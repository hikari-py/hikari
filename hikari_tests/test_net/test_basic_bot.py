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
import asyncio
import contextlib

import asynctest
import pytest

from hikari.net import basic_bot
from hikari.net import http


def test_initialise_bot_stores_http_and_loop_but_not_gateway():
    bot = basic_bot.BasicBot("12345", asynctest.CoroutineMock())
    assert bot.loop is not None
    assert isinstance(bot.http, http.HTTPClient)
    assert bot.gateway is None


@pytest.mark.asyncio
async def test_start_initializes_gateway():
    with contextlib.ExitStack() as stack:
        mock_gateway = asynctest.MagicMock()
        mock_gateway.run = asynctest.CoroutineMock()
        mock_http = asynctest.CoroutineMock()
        mock_http.get_gateway = asynctest.CoroutineMock(return_value="http://somebody.com")
        get_debug_data = asynctest.CoroutineMock()

        stack.enter_context(asynctest.patch("hikari.net.gateway.GatewayClient", new=lambda *_, **__: mock_gateway))
        stack.enter_context(asynctest.patch("hikari.net.debug.get_debug_data", new=get_debug_data))
        stack.enter_context(asynctest.patch("hikari.net.http.HTTPClient", new=lambda *_, **__: mock_http))

        bot = basic_bot.BasicBot("12345", asynctest.CoroutineMock())
        await bot.start()

        get_debug_data.assert_awaited()
        mock_http.get_gateway.assert_awaited()
        mock_gateway.run.assert_awaited_once()


def test_run_awaits_start():
    bot = basic_bot.BasicBot("12345", asynctest.CoroutineMock())
    bot.start = asynctest.CoroutineMock()

    bot.run(foo="foo", bar="bar")

    bot.start.assert_awaited_with(foo="foo", bar="bar")


@pytest.mark.asyncio
async def test_gateway_dispatch_awaits_our_dispatch(event_loop):
    dispatch = asynctest.CoroutineMock()

    with contextlib.ExitStack() as stack:
        bot = basic_bot.BasicBot("12345", dispatch, loop=event_loop)
        bot._init_gateway("http://foo.com")
        bot.gateway._dispatch("ping", {"response": "pong"})
        await asyncio.sleep(0.2)
        dispatch.assert_awaited_with("ping", {"response": "pong"})


@pytest.mark.asyncio
async def test_gateway_dispatch_catches_our_exception(event_loop):
    class YourCodeSucksException(RuntimeError):
        pass

    async def erroring_dispatch(*_, **__):
        raise YourCodeSucksException

    dispatch = asynctest.CoroutineMock(wraps=erroring_dispatch)

    with contextlib.ExitStack() as stack:
        bot = basic_bot.BasicBot("12345", dispatch, loop=event_loop)
        bot._init_gateway("http://foo.com")
        bot.gateway._dispatch("ping", {"response": "pong"})
        await asyncio.sleep(0.2)
        dispatch.assert_awaited_with("ping", {"response": "pong"})
