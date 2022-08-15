#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Body
from pysafebrowsing import SafeBrowsing
from starlette.requests import Request
from starlette.responses import RedirectResponse, HTMLResponse, FileResponse, PlainTextResponse

app = FastAPI()


links: dict[str, str]
last_id: int

data_path = Path('data')
links_path = data_path / 'short-links.json'
last_id_path = data_path / 'last_id.txt'

# Removed lower l
chars = 'abcdefghijkmnopqrstuvwxyz'
base = len(chars)

# URL checks
re_url = re.compile(r"""^https?://(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:[a-z\u00a1-\uffff]{2,}))\.?)(?::\d{2,5})?(?:[/?#]\S*)?$""")
safe_browsing = SafeBrowsing(os.environ['GOOGLE_API_KEY'])

blacklist = {'docs', 'favicon'}


def store():
    data_path.mkdir(parents=True, exist_ok=True)
    links_path.write_text(json.dumps(links))
    last_id_path.write_text(str(last_id))


def load():
    global links
    global last_id
    links = json.loads(links_path.read_text()) if links_path.is_file() else {}
    last_id = int(last_id_path.read_text()) if last_id_path.is_file() else 1000


def encode(plain: int) -> str:
    cipher = ''
    while plain != 0:
        digit = int(plain % base)
        cipher += chars[digit]
        plain = (plain - digit) // base
    return cipher


def decode(s: str) -> int:
    total = 0
    for i, token in enumerate(s):
        digit = chars.index(token)
        assert digit != -1, f'Unknown char: {token}'
        total += digit * int(base ** i)
    return total


@app.get('/{short}')
def expand(short: str):
    if short == 'favicon.ico':
        return FileResponse('favicon.ico')
    if short in links:
        return RedirectResponse(links[short])
    else:
        return HTMLResponse('404', status_code=404)


@app.get('/')
def index():
    return FileResponse('index.html')


@app.put('/')
def put(request: Request, name: str | None = None, body: str = Body()):
    try:
        global last_id

        ip = request.headers.get('X-Real-IP') or request.client.host

        print(f'New PUT request from {ip}')
        print(f'> URL: {body.replace("https://", "").replace("http://", "")}')

        # Check valid html
        assert re_url.match(body), 'Invalid HTML'
        sb = safe_browsing.lookup_url(body)
        print(f'> SafeBrowsing Result: {sb}')
        assert not sb['malicious'], f'Link is malicious ({",".join(sb["threats"]).lower()})'

        # Generate name
        while not name:
            last_id += 1
            name = encode(last_id)
            if name in links or name in blacklist:
                name = None

        # Put name
        links[name] = body
        print(f'> Added link: {name}')
        store()

        return PlainTextResponse(f'/{name}')

    except AssertionError as e:
        print(f'> Rejected. {e}')
        return PlainTextResponse(f'Error: {e}', status_code=400)

if __name__ == '__main__':
    load()
    uvicorn.run(app, host='0.0.0.0', port=8000)

