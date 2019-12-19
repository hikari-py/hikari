#!/usr/bin/env python3
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
#
# Big text is from: http://patorjk.com/software/taag/#p=display&f=Big&t=Gateway
# Adding new categories? Keep it consistent, bud.

import aiohttp
import asyncmock as mock
import pytest

from hikari.net import ws


@pytest.mark.parametrize("input", ["hello", b"hello"])
@pytest.mark.gateway
def test__promote_to_bytes(input):
    assert ws._promote_to_bytes(input) == b"hello"


@pytest.mark.gateway
def test_WebSocketClosure___init__():
    ex = ws.WebSocketClosure(69, "nice")
    assert ex.code == 69
    assert ex.reason == "nice"


@pytest.mark.gateway
class TestWebSocketClientSession:
    def test___init___specifies_response_class(self):
        with mock.patch("aiohttp.ClientSession.__init__") as __init__:
            ws.WebSocketClientSession()
            __init__.assert_called_with(ws_response_class=ws.WebSocketClientResponse)

    def test_ws_connect(self):
        with mock.patch("aiohttp.ClientSession.__init__"), mock.patch("aiohttp.ClientSession.ws_connect") as ws_connect:
            session = ws.WebSocketClientSession()
            session.ws_connect("http://localhost")
            aiohttp.ClientSession.ws_connect.assert_called_with(
                "http://localhost", autoclose=False, max_msg_size=0, autoping=True
            )


@pytest.mark.gateway
class TestWebSocketResponse:
    @pytest.mark.asyncio
    async def test_close(self):
        with mock.patch("aiohttp.ClientWebSocketResponse.__init__", return_value=None) as __init__:
            with mock.patch("aiohttp.ClientWebSocketResponse.close", new=mock.AsyncMock()) as close:
                websocket = ws.WebSocketClientResponse()
                await websocket.close(code=420, reason="yeet")
                close.assert_called_with(code=420, message=b"yeet")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["message_type", "expect_error"],
        [
            (aiohttp.WSMsgType.BINARY, False),
            (aiohttp.WSMsgType.TEXT, False),
            (aiohttp.WSMsgType.CLOSED, True),
            (aiohttp.WSMsgType.PING, True),
            (aiohttp.WSMsgType.PONG, True),
            (aiohttp.WSMsgType.CONTINUATION, True),
            (aiohttp.WSMsgType.ERROR, True),
            (aiohttp.WSMsgType.CLOSING, True),
        ],
    )
    async def test_receive_any_str(self, message_type, expect_error):
        response = mock.MagicMock(spec_set=aiohttp.WSMessage)
        response.data = "blah"
        response.type = message_type

        with mock.patch("aiohttp.ClientWebSocketResponse.__init__", return_value=None) as __init__:
            with mock.patch("aiohttp.ClientWebSocketResponse.receive", new=mock.AsyncMock(return_value=response)):
                websocket = ws.WebSocketClientResponse()
                if expect_error:
                    try:
                        await websocket.receive_any_str()
                        assert False, "no error"
                    except TypeError:
                        # traceback.print_exc()
                        assert True, "type error as expected"
                else:
                    assert isinstance(await websocket.receive_any_str(), (str, bytes))

    @pytest.mark.asyncio
    async def test_receive_on_normal_message(self):
        with mock.patch("aiohttp.ClientWebSocketResponse.__init__", return_value=None) as __init__:
            websocket = ws.WebSocketClientResponse()
            response = mock.MagicMock(spec_set=aiohttp.WSMessage)
            response.data = "blah"
            response.type = aiohttp.WSMsgType.TEXT
            aiohttp.ClientWebSocketResponse.receive = mock.AsyncMock(return_value=response)

            response = await websocket.receive()
            assert response.data == "blah"
            assert response.type == aiohttp.WSMsgType.TEXT

    @pytest.mark.asyncio
    async def test_receive_on_known_close_message(self):
        response = mock.MagicMock(spec_set=aiohttp.WSMessage)
        response.type = aiohttp.WSMsgType.CLOSE
        with mock.patch("aiohttp.ClientWebSocketResponse.__init__", return_value=None) as __init__:
            with mock.patch("aiohttp.ClientWebSocketResponse.close", new=mock.AsyncMock()):
                with mock.patch("aiohttp.ClientWebSocketResponse.receive", new=mock.AsyncMock(return_value=response)):

                    websocket = ws.WebSocketClientResponse()
                    websocket._close_code = 1000

                    try:
                        response = await websocket.receive()
                        assert False, f"expected exception, got {response!r}"
                    except ws.WebSocketClosure as ex:
                        assert ex.reason == "NORMAL_CLOSURE"
                        assert ex.code == 1000

    @pytest.mark.asyncio
    async def test_receive_on_unknown_close_message(self):
        response = mock.MagicMock(spec_set=aiohttp.WSMessage)
        response.type = aiohttp.WSMsgType.CLOSE
        with mock.patch("aiohttp.ClientWebSocketResponse.__init__", return_value=None) as __init__:
            with mock.patch("aiohttp.ClientWebSocketResponse.close", new=mock.AsyncMock()):
                with mock.patch("aiohttp.ClientWebSocketResponse.receive", new=mock.AsyncMock(return_value=response)):
                    websocket = ws.WebSocketClientResponse()
                    websocket._close_code = 69

                    try:
                        response = await websocket.receive()
                        assert False, f"expected exception, got {response!r}"
                    except ws.WebSocketClosure as ex:
                        assert ex.reason == "no reason"
                        assert ex.code == 69
