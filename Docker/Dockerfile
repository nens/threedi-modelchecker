FROM python:3.5

RUN apt-get update \
    && apt-get install -y \
        sqlite3 \
        libsqlite3-mod-spatialite

WORKDIR /code

COPY requirements.txt .
COPY requirements-dev.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt
