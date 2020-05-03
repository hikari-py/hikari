FROM python:3.8.2
COPY . .
RUN pip install nox 'virtualenv<20.0.19'
RUN nox
