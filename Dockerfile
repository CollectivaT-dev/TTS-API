FROM python:3.7.9-slim-buster

# Project setup

ENV VIRTUAL_ENV=/opt/venv

RUN apt-get update \
    && apt-get install gcc g++ mecab libmecab-dev mecab-ipadic-utf8 libsndfile1 -y \
    && apt-get install libasound2 libc6 libgcc1 libstdc++6 -y \
    && apt-get clean

RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install  --quiet --upgrade pip && \
    pip install  --quiet pip-tools

COPY . /app

RUN pip install -r /app/requirements.txt \
    && rm -rf /root/.cache/pip

WORKDIR /app

ENV PYTHONUNBUFFERED=1
