FROM nekokatt/stackless-python-hikari:3.8.0-rc
COPY . .
RUN  pip install nox
