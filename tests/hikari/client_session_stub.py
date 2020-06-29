# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
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
import aiohttp
import asyncio
import mock


class RequestContextStub:
    def __init__(self, response_getter) -> None:
        self.response_getter = response_getter
        self.await_count = 0

    async def __aenter__(self) -> None:
        return self.response_getter()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def __await__(self) -> aiohttp.ClientResponse:
        # noinspection PyUnreachableCode
        if False:
            yield  # Turns this into a generator.
        self.await_count += 1
        return self.response_getter()

    def assert_awaited_once(self):
        assert self.await_count == 1


class ClientSessionStub:
    def __init__(self) -> None:
        self.close = mock.AsyncMock()
        self.closed = mock.PropertyMock()
        self.connector = mock.create_autospec(aiohttp.BaseConnector)
        self.cookie_jar = mock.create_autospec(aiohttp.CookieJar)
        self.version = aiohttp.HttpVersion11

        self.response_stub = mock.create_autospec(aiohttp.ClientResponse)
        self.websocket_stub = mock.create_autospec(aiohttp.ClientWebSocketResponse)

        self.request_context_stub = RequestContextStub(lambda: self.response_stub)
        self.ws_connect_stub = RequestContextStub(lambda: self.websocket_stub)

        self.request = mock.MagicMock(wraps=lambda *args, **kwargs: self.request_context_stub)
        self.ws_connect = mock.MagicMock(wraps=lambda *args, **kwargs: self.ws_connect_stub)

    @property
    def loop(self):
        return asyncio.current_task().get_loop()
