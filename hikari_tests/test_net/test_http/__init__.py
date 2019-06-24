#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest

from hikari.net.http import client


class ClientMock(client.HTTPClient):
    def __init__(self, *args, **kwargs):
        with asynctest.patch("aiohttp.ClientSession", new=asynctest.MagicMock()):
            super().__init__(*args, **kwargs)

    async def request(self, method, path, params=None, **kwargs):
        pass
