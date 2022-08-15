import json
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Body
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
    print(short)
    print(links)
    if short in links:
        return RedirectResponse(links[short])
    else:
        return HTMLResponse('404', status_code=404)


@app.get('/')
def get():
    return FileResponse('index.html')


@app.put('/')
def put(name: str | None = None, body: str = Body()):
    global last_id

    # Generate name
    while not name:
        last_id += 1
        name = encode(last_id)
        if name in links:
            name = None

    # Put name
    links[name] = body
    store()

    return PlainTextResponse(f'/{name}')


if __name__ == '__main__':
    load()
    uvicorn.run(app)

