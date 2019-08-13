#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""
A very basic low level bot that only has a HTTP client and a websocket. No other state is maintained.
"""
import asyncio
import logging
import os
import time

from hikari.core.net import gateway, http_client


class Bot:
    def __init__(self):
        self.http: http_client.HTTPClient = ...
        self.ws: gateway.GatewayClient = ...

    async def init(self):
        token = os.environ["TOKEN"]
        self.http = http_client.HTTPClient(token=token)
        host = await self.http.get_gateway()
        self.ws = gateway.GatewayClient(host=host, token=token, dispatch=self.on_event)

    async def run(self):
        await self.ws.run()

    async def close(self):
        await self.ws.close(True)
        await self.http.close()

    async def on_event(self, name, payload):
        if name == "MESSAGE_CREATE" and not payload["author"].get("bot", False):
            await self.on_message_create(payload)

    async def on_message_create(self, message):
        if message["content"] == "h.ping":
            start = time.perf_counter()
            message = await self.http.create_message(message["channel_id"], content="Pong!")
            http_latency = time.perf_counter() - start
            gateway_latency = self.ws.heartbeat_latency
            logging.info("Ping... Pong! %s http/%s gateway", http_latency, gateway_latency)
            await self.http.edit_message(
                message["channel_id"], message["id"],
                content=f"Pong! HTTP: {http_latency * 1_000:.0f}ms, WS: {gateway_latency * 1_000:.0f}ms"
            )


async def main():
    logging.basicConfig(level="INFO")
    bot = Bot()
    await bot.init()
    try:
        await bot.run()
    finally:
        await bot.close()


asyncio.run(main())
