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
import asyncio
import contextlib
import datetime
import math
import urllib.parse
from unittest import mock

import pytest

from hikari.net import errors
from hikari.net import gateway
from tests.hikari import _helpers


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["input_shard_id", "input_shard_count", "expected_shard_id", "expected_shard_count"],
    [(None, None, 0, 1), (1, 2, 1, 2), (None, 5, 0, 1), (0, None, 0, 1),],
)
async def test_init_sets_shard_numbers_correctly(
    input_shard_id, input_shard_count, expected_shard_id, expected_shard_count,
):
    client = gateway.GatewayClient(shard_id=input_shard_id, shard_count=input_shard_count, token="xxx", url="yyy")
    assert client.shard_id == expected_shard_id
    assert client.shard_count == expected_shard_count


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["compression", "expected_url_query"],
    [(True, dict(v=["6"], encoding=["json"], compress=["zlib-stream"])), (False, dict(v=["6"], encoding=["json"])),],
)
async def test_compression(compression, expected_url_query):
    url = "ws://baka-im-not-a-http-url:49620/locate/the/bloody/websocket?ayyyyy=lmao"
    client = gateway.GatewayClient(token="xxx", url=url, compression=compression)
    scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(client.url)
    assert scheme == "ws"
    assert netloc == "baka-im-not-a-http-url:49620"
    assert path == "/locate/the/bloody/websocket"
    assert params == ""
    actual_query_dict = urllib.parse.parse_qs(query)
    assert actual_query_dict == expected_url_query
    assert fragment == ""


@pytest.mark.asyncio
async def test_init_ping_defaults_before_startup():
    client = gateway.GatewayClient(token="xxx", url="yyy")
    assert math.isnan(client.last_ping_sent)
    assert math.isnan(client.last_pong_received)


@pytest.mark.asyncio
async def test_init_hearbeat_defaults_before_startup():
    client = gateway.GatewayClient(token="xxx", url="yyy")
    assert math.isnan(client.last_heartbeat_sent)
    assert math.isnan(client.last_heartbeat_ack_received)


@pytest.mark.asyncio
async def test_init_connected_at_is_nan():
    client = gateway.GatewayClient(token="xxx", url="yyy")
    assert math.isnan(client.connected_at)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["sent", "received", "predicate"],
    [(float("nan"), float("nan"), math.isnan), (10.0, float("nan"), math.isnan), (10.0, 31.0, 21.0 .__eq__),],
)
async def test_latency(sent, received, predicate):
    client = gateway.GatewayClient(token="xxx", url="yyy")
    client.last_ping_sent = sent
    client.last_pong_received = received
    assert predicate(client.latency)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["sent", "received", "predicate"],
    [(float("nan"), float("nan"), math.isnan), (10.0, float("nan"), math.isnan), (10.0, 31.0, 21.0 .__eq__),],
)
async def test_heart7beat_latency(sent, received, predicate):
    client = gateway.GatewayClient(token="xxx", url="yyy")
    client.last_heartbeat_sent = sent
    client.last_heartbeat_ack_received = received
    assert predicate(client.heartbeat_latency)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["connected_at", "now", "expected_uptime"],
    [(float("nan"), 31.0, datetime.timedelta(seconds=0)), (10.0, 31.0, datetime.timedelta(seconds=21.0)),],
)
async def test_uptime(connected_at, now, expected_uptime):
    with mock.patch("time.perf_counter", return_value=now):
        client = gateway.GatewayClient(token="xxx", url="yyy")
        client.connected_at = connected_at
        assert client.uptime == expected_uptime


@pytest.mark.asyncio
@pytest.mark.parametrize(["connected_at", "is_connected"], [(float("nan"), False), (15, True), (2500.0, True),])
async def test_is_connected(connected_at, is_connected):
    client = gateway.GatewayClient(token="xxx", url="yyy")
    client.connected_at = connected_at
    assert client.is_connected is is_connected


@pytest.mark.asyncio
async def test_ws_connect_kwargs_contain_right_stuff():
    url = "foobarbaz"
    receive_timeout = 33
    proxy_url = "http://localhost.lan"
    proxy_auth = mock.MagicMock()
    proxy_headers = mock.MagicMock()
    verify_ssl = True
    ssl_context = mock.MagicMock()
    timeout = receive_timeout

    client = gateway.GatewayClient(
        url="...",
        token="...",
        receive_timeout=receive_timeout,
        proxy_url=proxy_url,
        proxy_auth=proxy_auth,
        proxy_headers=proxy_headers,
        verify_ssl=verify_ssl,
        ssl_context=ssl_context,
    )
    client.url = url

    assert client._ws_connect_kwargs == dict(
        url=url,
        receive_timeout=receive_timeout,
        compress=0,
        autoping=False,
        max_msg_size=0,
        proxy=proxy_url,
        proxy_auth=proxy_auth,
        proxy_headers=proxy_headers,
        verify_ssl=verify_ssl,
        ssl_context=ssl_context,
        timeout=receive_timeout,
    )


@pytest.mark.asyncio
class TestGatewayOpenWebsocket:
    pass


@pytest.mark.asyncio
class TestGatewayConnect:
    @property
    def hello_payload(self):
        return {"op": 10, "d": {"heartbeat_interval": 30_000,}}

    @pytest.fixture()
    def client(self):
        client = _helpers.unslot_class(gateway.GatewayClient)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("connect",))
        client._receive = mock.AsyncMock(return_value=self.hello_payload)
        client._open_websocket = _helpers.AsyncContextManagerMock()

        return client

    @contextlib.contextmanager
    def suppress_closure(self):
        with contextlib.suppress(errors.GatewayClientClosedError):
            yield

    async def test_RuntimeError_if_already_connected(self, client):
        client.connected_at = 22.4  # makes client expect to be connected

        try:
            await client.connect()
            assert False
        except RuntimeError:
            pass

        assert client.ws is None
        client._identify_or_resume_then_poll_events.assert_not_called()
        client._ping_keep_alive.assert_not_called()
        client._heartbeat_keep_alive.assert_not_called()

    async def test_open_websocket_is_called(self, client):
        with self.suppress_closure():
            await client.connect()

        assert client._open_websocket.awaited_aenter
        assert client._open_websocket.awaited_aexit

    async def test_new_zlib_each_time(self, client):
        assert client.zlib is None
        previous_zlib = None

        for i in range(20):
            with self.suppress_closure():
                await client.connect()
            assert client.zlib is not None
            assert previous_zlib is not client.zlib
            previous_zlib = client.zlib
            client.connected_at = float("nan")

    async def test_heartbeat_keep_alive_correctly_started(self, client):
        with self.suppress_closure():
            await client.connect()

        client._heartbeat_keep_alive.assert_called_with(self.hello_payload["d"]["heartbeat_interval"] / 1_000.0)

    async def test_ping_keep_alive_started(self, client):
        with self.suppress_closure():
            await client.connect()

        client._ping_keep_alive.assert_called_once()

    async def test_identify_or_resume_then_poll_events_started(self, client):
        with self.suppress_closure():
            await client.connect()

        client._identify_or_resume_then_poll_events.assert_called_once()

    async def test_waits_for_ping_keep_alive_to_die_then_throws_that_exception(self, client):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        class ExceptionThing(Exception):
            pass

        async def ping_keep_alive():
            raise ExceptionThing()

        client._ping_keep_alive = ping_keep_alive
        client._heartbeat_keep_alive = deadlock
        client._identify_or_resume_then_poll_events = deadlock

        try:
            await client.connect()
            assert False
        except ExceptionThing:
            pass

    async def test_waits_for_heartbeat_keep_alive_to_die_then_throws_that_exception(self, client):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        class ExceptionThing(Exception):
            pass

        async def heartbeat_keep_alive(_):
            raise ExceptionThing()

        client._ping_keep_alive = deadlock
        client._heartbeat_keep_alive = heartbeat_keep_alive
        client._identify_or_resume_then_poll_events = deadlock

        try:
            await client.connect()
            assert False
        except ExceptionThing:
            pass

    async def test_waits_for_identify_or_resume_then_poll_events_then_throws_that_exception(self, client):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        class ExceptionThing(Exception):
            pass

        async def identify_or_resume_then_poll_events():
            raise ExceptionThing()

        client._ping_keep_alive = deadlock
        client._heartbeat_keep_alive = deadlock
        client._identify_or_resume_then_poll_events = identify_or_resume_then_poll_events

        try:
            await client.connect()
            assert False
        except ExceptionThing:
            pass

    async def test_waits_for_ping_keep_alive_to_return_then_throws_GatewayClientClosedError(self, client):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        async def ping_keep_alive():
            pass

        client._ping_keep_alive = ping_keep_alive
        client._heartbeat_keep_alive = deadlock
        client._identify_or_resume_then_poll_events = deadlock

        try:
            await client.connect()
            assert False
        except errors.GatewayClientClosedError:
            pass

    async def test_waits_for_heartbeat_keep_alive_to_return_then_throws_GatewayClientClosedError(self, client):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        async def heartbeat_keep_alive(_):
            pass

        client._ping_keep_alive = deadlock
        client._heartbeat_keep_alive = heartbeat_keep_alive
        client._identify_or_resume_then_poll_events = deadlock

        try:
            await client.connect()
            assert False
        except errors.GatewayClientClosedError:
            pass

    async def test_waits_for_identify_or_resume_then_poll_events_to_return_throws_GatewayClientClosedError(
        self, client
    ):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        async def identify_or_resume_then_poll_events():
            pass

        client._ping_keep_alive = deadlock
        client._heartbeat_keep_alive = deadlock
        client._identify_or_resume_then_poll_events = identify_or_resume_then_poll_events

        try:
            await client.connect()
            assert False
        except errors.GatewayClientClosedError:
            pass

    async def test_waits_indefinitely(self, client):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        client._ping_keep_alive = deadlock
        client._heartbeat_keep_alive = deadlock
        client._identify_or_resume_then_poll_events = deadlock

        try:
            await asyncio.wait_for(client.connect(), timeout=2)
            assert False
        except asyncio.TimeoutError:
            pass
