FROM python:3.11-slim-bookworm

RUN apt-get update -y && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/anontex

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN python -m pip install -U pip poetry
RUN poetry config virtualenvs.create false

COPY pyproject.toml /usr/src/anontex/
COPY poetry.lock /usr/src/anontex/

RUN poetry lock --no-update
RUN poetry install --no-interaction --no-ansi --no-root --without dev

COPY ./anontex /anontex

EXPOSE 8000

CMD uvicorn anontex.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS:-1}
