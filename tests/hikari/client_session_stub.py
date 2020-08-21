# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import annotations

import asyncio

import aiohttp
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
        self.connector = mock.Mock(spec_set=aiohttp.BaseConnector)
        self.cookie_jar = mock.Mock(spec_set=aiohttp.CookieJar)
        self.version = aiohttp.HttpVersion11

        self.response_stub = mock.Mock(spec_set=aiohttp.ClientResponse)
        self.websocket_stub = mock.Mock(spec_set=aiohttp.ClientWebSocketResponse)

        self.request_context_stub = RequestContextStub(lambda: self.response_stub)
        self.ws_connect_stub = RequestContextStub(lambda: self.websocket_stub)

        self.request = mock.Mock(wraps=lambda *args, **kwargs: self.request_context_stub)
        self.ws_connect = mock.Mock(wraps=lambda *args, **kwargs: self.ws_connect_stub)

        for method in "get put patch post delete head options".split():
            self._make_method(method)

    def _make_method(self, method) -> None:
        shim = mock.Mock(wraps=lambda *a, **k: self.request(method, *a, **k))
        setattr(self, method, shim)

    @property
    def loop(self):
        return asyncio.current_task().get_loop()

    async def __aenter__(self) -> ClientSessionStub:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
