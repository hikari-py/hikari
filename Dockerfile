FROM       python:3
RUN        pip install --pre hikari>=1.0.0
ENTRYPOINT python -m hikari.clients.gateway_runner
