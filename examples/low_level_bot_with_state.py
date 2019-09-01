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
A very basic low level bot that only has a HTTP client and a websocket providing data to a state object for
state caching and object marshalling purposes.
"""

import asyncio
import logging
import os

from hikari.core.net import gateway, http_client
from hikari.core.state import cache
from hikari.core.state import network_mediator


class Bot:
    def __init__(self):
        self.http: http_client.HTTPClient = ...
        self.ws: gateway.GatewayClient = ...
        self.state: network_mediator.BasicNetworkMediator = ...
        self.cache = cache.InMemoryCache()

    async def init(self):
        self.state = network_mediator.BasicNetworkMediator(self.cache, self.on_event)
        token = os.environ["TOKEN"]
        self.http = http_client.HTTPClient(token=token)
        host = await self.http.get_gateway()
        self.ws = gateway.GatewayClient(host=host, token=token, dispatch=self.state.consume_raw_event)

    async def run(self):
        await self.ws.run()

    async def close(self):
        await self.ws.close(True)
        await self.http.close()

    def on_event(self, name, *args):
        print(name, args)


async def main():
    logging.basicConfig(level="DEBUG")
    bot = Bot()
    await bot.init()
    try:
        await bot.run()
    finally:
        await bot.close()


asyncio.run(main())
