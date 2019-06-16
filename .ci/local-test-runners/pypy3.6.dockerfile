FROM       pypy:3.6-slim
VOLUME     ["/hikari", "/hikari_tests"]
COPY       requirements.txt .
COPY       tox.ini          .
RUN        apt update && apt install git -y && pip install -Ur requirements.txt
