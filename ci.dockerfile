FROM python:3.8.3
COPY . .
RUN pip install nox
RUN nox
