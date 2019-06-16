FROM       python:3.6-alpine
VOLUME     ["/hikari", "/hikari_tests"]
COPY       requirements.txt .
COPY       tox.ini          .
RUN        apk add git && pip install -Ur requirements.txt
