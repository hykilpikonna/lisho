FROM python:3.10-alpine

WORKDIR /app

COPY requirements.txt req
RUN pip3 install -r req

COPY . .
CMD ["python3", "api.py"]
