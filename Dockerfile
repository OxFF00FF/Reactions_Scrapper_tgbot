FROM python:3.9-alpine

ENV PYTHONFAULTHANDLER=1 \
     PYTHONUNBUFFERED=1 \
     PYTHONDONTWRITEBYTECODE=1 \
     PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

COPY Bot ./Bot
COPY main.py .env requirements.txt ./
COPY sessions ./sessions

RUN pip install -r requirements.txt

CMD ["python", "main.py"]