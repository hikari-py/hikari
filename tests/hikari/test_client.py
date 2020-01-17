#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
import datetime
import math
import signal

import pytest

import asyncmock as mock

from hikari import client as _client
from hikari import client_options as _client_options
from hikari.net import gateway
from hikari.net import http_api
from hikari.orm import fabric as _fabric
from hikari.orm.gateway import basic_chunker_impl
from hikari.orm.gateway import dispatching_event_adapter_impl
from hikari.orm.http import http_adapter_impl
from hikari.orm.models import gateway_bot
from hikari.orm.state import state_registry_impl
from tests.hikari import _helpers


class TestClient:
    # Lets us prevent "unclosed session" warnings, etc.
    @pytest.fixture()
    def patched_client_session_class(self):
        with mock.patch("aiohttp.ClientSession") as cs:
            yield cs

    @pytest.mark.asyncio
    async def test_dispatch(self):
        client = _client.Client("token")
        client._event_dispatcher.dispatch = mock.MagicMock()

        client.dispatch("message_create", "foo", 1, True)

        client._event_dispatcher.dispatch.assert_called_with("message_create", "foo", 1, True)

    @pytest.mark.asyncio
    async def test_add_event(self):
        async def foo():
            ...

        client = _client.Client("token")
        client._event_dispatcher.add = mock.MagicMock()

        client.add_event("message_create", foo)

        client._event_dispatcher.add.assert_called_with("message_create", foo)

    @pytest.mark.asyncio
    async def test_remove_event(self):
        async def foo():
            ...

        client = _client.Client("token")
        client._event_dispatcher.remove = mock.MagicMock()

        client.remove_event("message_create", foo)

        client._event_dispatcher.remove.assert_called_with("message_create", foo)

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=RuntimeError)
    async def test_event_when_name_is_not_str_nor_None_raises(self):
        client = _client.Client("token")

        @client.event(True)
        async def on_message_create():
            ...

    @pytest.mark.asyncio
    async def test_event_without_name_and_starts_with_on(self):
        client = _client.Client("token")

        with mock.patch("hikari.client.Client.add_event") as add_event:

            @client.event()
            async def on_message_create():
                ...

            add_event.assert_called_with("message_create", on_message_create)

    @pytest.mark.asyncio
    async def test_event_without_name_and_doesnt_start_with_on(self):
        client = _client.Client("token")

        with mock.patch("hikari.client.Client.add_event") as add_event:

            @client.event()
            async def message_create():
                ...

            add_event.assert_called_with("message_create", message_create)

    @pytest.mark.asyncio
    async def test_event_with_name(self):
        client = _client.Client("token")

        with mock.patch("hikari.client.Client.add_event") as add_event:

            @client.event("message_create")
            async def foo():
                ...

            add_event.assert_called_with("message_create", foo)

    @pytest.mark.asyncio
    async def test_heartbeat_latency_when_bot_not_started_is_nan(self):
        client = _client.Client("token")
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {}

        assert math.isnan(client.heartbeat_latency)

    @pytest.mark.asyncio
    async def test_heartbeat_latency_when_bot_started(self):
        def gw(id, latency):
            gw = mock.MagicMock()
            gw.shard_id = id
            gw.heartbeat_latency = latency
            return gw

        client = _client.Client("token")
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {0: gw(0, 1), 1: gw(1, 2)}

        assert client.heartbeat_latency == 1.5

    @pytest.mark.asyncio
    async def test_hearbeat_latencies_when_bot_not_started(self):
        client = _client.Client("token")
        client._fabric = None

        assert client.heartbeat_latencies == {}

    @pytest.mark.asyncio
    async def test_hearbeat_latencies(self):
        def gw(id, latency):
            gw = mock.MagicMock()
            gw.shard_id = id
            gw.heartbeat_latency = latency
            return gw

        client = _client.Client("token")
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {0: gw(0, 0.1), 1: gw(1, 0.2)}

        assert client.heartbeat_latencies == {0: 0.1, 1: 0.2}
