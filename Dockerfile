FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/anontex

RUN apt-get update -y && apt-get install -y gcc && \
    python -m pip install -U pip poetry && \
    apt-get remove -y gcc && apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock LICENSE ./

RUN poetry lock && poetry install --no-interaction --no-ansi --no-root --no-cache

COPY ./anontex /anontex

EXPOSE 8000

CMD uvicorn anontex.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-1}
