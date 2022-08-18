FROM python:3.7.9-slim-buster

# Project setup

ENV VIRTUAL_ENV=/opt/venv

RUN apt-get update \
    && apt-get install gcc g++ mecab libmecab-dev mecab-ipadic-utf8 libsndfile1 -y \
    && apt-get clean

RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install  --quiet --upgrade pip && \
    pip install  --quiet pip-tools

RUN pip install --no-deps TTS==0.7.1

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt \
    && rm -rf /root/.cache/pip

COPY . /app
WORKDIR /app

