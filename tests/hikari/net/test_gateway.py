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
import time
import urllib.parse
from unittest import mock

import aiohttp
import async_timeout
import pytest

from hikari.internal_utilities import containers
from hikari.net import errors
from hikari.net import gateway
from hikari.net import user_agent
from hikari.net import versions
from tests.hikari import _helpers


class MockWS:
    def __init__(self):
        self.args = None
        self.kwargs = None
        self.aenter = 0
        self.aexit = 0

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self

    async def __aenter__(self):
        self.aenter += 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.aexit += 1
        return self


class MockClientSession:
    def __init__(self):
        self.args = None
        self.kwargs = None
        self.aenter = 0
        self.aexit = 0
        self.ws = MockWS()
        self.close = mock.AsyncMock()

    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self

    async def __aenter__(self):
        self.aenter += 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.aexit += 1

    async def ws_connect(self, *args, **kwargs):
        return self.ws(*args, **kwargs)


@pytest.mark.asyncio
class TestGatewayClientConstructor:
    async def test_init_sets_shard_numbers_correctly(self,):
        input_shard_id, input_shard_count, expected_shard_id, expected_shard_count = 1, 2, 1, 2
        client = gateway.GatewayClient(shard_id=input_shard_id, shard_count=input_shard_count, token="xxx", url="yyy")
        assert client.shard_id == expected_shard_id
        assert client.shard_count == expected_shard_count

    async def test_dispatch_is_callable(self):
        client = gateway.GatewayClient(token="xxx", url="yyy")
        client.dispatch(client, "ping", "pong")

    @pytest.mark.parametrize(
        ["compression", "expected_url_query"],
        [
            (True, dict(v=["6"], encoding=["json"], compress=["zlib-stream"])),
            (False, dict(v=["6"], encoding=["json"])),
        ],
    )
    async def test_compression(self, compression, expected_url_query):
        url = "ws://baka-im-not-a-http-url:49620/locate/the/bloody/websocket?ayyyyy=lmao"
        client = gateway.GatewayClient(token="xxx", url=url, compression=compression)
        scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(client._url)
        assert scheme == "ws"
        assert netloc == "baka-im-not-a-http-url:49620"
        assert path == "/locate/the/bloody/websocket"
        assert params == ""
        actual_query_dict = urllib.parse.parse_qs(query)
        assert actual_query_dict == expected_url_query
        assert fragment == ""

    async def test_init_hearbeat_defaults_before_startup(self):
        client = gateway.GatewayClient(token="xxx", url="yyy")
        assert math.isnan(client.last_heartbeat_sent)
        assert math.isnan(client.heartbeat_latency)
        assert math.isnan(client.last_message_received)

    async def test_init_connected_at_is_nan(self):
        client = gateway.GatewayClient(token="xxx", url="yyy")
        assert math.isnan(client._connected_at)


@pytest.mark.asyncio
class TestGatewayClientUptimeProperty:
    @pytest.mark.parametrize(
        ["connected_at", "now", "expected_uptime"],
        [(float("nan"), 31.0, datetime.timedelta(seconds=0)), (10.0, 31.0, datetime.timedelta(seconds=21.0)),],
    )
    async def test_uptime(self, connected_at, now, expected_uptime):
        with mock.patch("time.perf_counter", return_value=now):
            client = gateway.GatewayClient(token="xxx", url="yyy")
            client._connected_at = connected_at
            assert client.uptime == expected_uptime


@pytest.mark.asyncio
class TestGatewayClientIsConnectedProperty:
    @pytest.mark.parametrize(["connected_at", "is_connected"], [(float("nan"), False), (15, True), (2500.0, True),])
    async def test_is_connected(self, connected_at, is_connected):
        client = gateway.GatewayClient(token="xxx", url="yyy")
        client._connected_at = connected_at
        assert client.is_connected is is_connected


@pytest.mark.asyncio
class TestGatewayReconnectCountProperty:
    @pytest.mark.parametrize(
        ["disconnect_count", "is_connected", "expected_reconnect_count"],
        [
            (0, False, 0),
            (0, True, 0),
            (1, False, 0),
            (1, True, 1),
            (2, False, 1),
            (2, True, 2),
            (3, False, 2),
            (3, True, 3),
        ],
    )
    async def test_value(self, disconnect_count, is_connected, expected_reconnect_count):
        client = gateway.GatewayClient(token="xxx", url="yyy")
        client.disconnect_count = disconnect_count
        client._connected_at = 420 if is_connected else float("nan")
        assert client.reconnect_count == expected_reconnect_count


@pytest.mark.asyncio
class TestGatewayClientAiohttpClientSessionKwargsProperty:
    async def test_right_stuff_is_included(self):
        connector = mock.MagicMock()

        client = gateway.GatewayClient(url="...", token="...", connector=connector,)

        assert client._cs_init_kwargs == dict(connector=connector)


@pytest.mark.asyncio
class TestGatewayClientWebSocketKwargsProperty:
    async def test_right_stuff_is_included(self):
        url = "http://localhost.lan/discord"
        proxy_url = "http://localhost.lan/some_proxy"
        proxy_auth = mock.MagicMock()
        proxy_headers = mock.MagicMock()
        verify_ssl = True
        ssl_context = mock.MagicMock()

        client = gateway.GatewayClient(
            url=url,
            token="...",
            proxy_url=proxy_url,
            proxy_auth=proxy_auth,
            proxy_headers=proxy_headers,
            verify_ssl=verify_ssl,
            ssl_context=ssl_context,
            version=versions.GatewayVersion.STABLE,
        )

        scheme, netloc, url, params, query, fragment = urllib.parse.urlparse(client._url)
        query = urllib.parse.parse_qs(query)
        assert query["v"] == [str(versions.GatewayVersion.STABLE.value)]

        client._url = url

        assert client._ws_connect_kwargs == dict(
            url=url,
            compress=0,
            autoping=True,
            max_msg_size=0,
            proxy=proxy_url,
            proxy_auth=proxy_auth,
            proxy_headers=proxy_headers,
            verify_ssl=verify_ssl,
            ssl_context=ssl_context,
        )


@pytest.mark.asyncio
class TestGatewayConnect:
    @pytest.fixture
    def client_session_t(self):
        return MockClientSession()

    @property
    def hello_payload(self):
        return {"op": 10, "d": {"heartbeat_interval": 30_000,}}

    @property
    def non_hello_payload(self):
        return {"op": 69, "d": "yeet"}

    @pytest.fixture
    def client(self, event_loop):
        asyncio.set_event_loop(event_loop)
        client = _helpers.unslot_class(gateway.GatewayClient)(url="ws://localhost", token="xxx")
        client = _helpers.mock_methods_on(client, except_=("connect",))
        client._receive = mock.AsyncMock(return_value=self.hello_payload)
        return client

    @contextlib.contextmanager
    def suppress_closure(self):
        with contextlib.suppress(errors.GatewayClientClosedError):
            yield

    async def test_RuntimeError_if_already_connected(self, client):
        client._connected_at = 22.4  # makes client expect to be connected

        try:
            with self.suppress_closure():
                await client.connect()
            assert False
        except RuntimeError:
            pass

        assert client._ws is None
        client._identify_or_resume_then_poll_events.assert_not_called()
        client._heartbeat_keep_alive.assert_not_called()

    @_helpers.timeout_after(10.0)
    async def test_closed_event_unset_on_open(self, client, client_session_t):
        client.closed_event.set()
        with self.suppress_closure():
            task = asyncio.create_task(client.connect(client_session_t))
            await client.hello_event.wait()
            assert not client.closed_event.is_set()
            await task
        assert client.closed_event.is_set()

    @_helpers.timeout_after(10.0)
    async def test_session_opened_with_expected_kwargs(self, client, client_session_t):
        with self.suppress_closure():
            await client.connect(client_session_t)
        assert client_session_t.args == ()
        assert client_session_t.kwargs == client._cs_init_kwargs

    @_helpers.timeout_after(10.0)
    async def test_ws_opened_with_expected_kwargs(self, client, client_session_t):
        with self.suppress_closure():
            await client.connect(client_session_t)
        assert client_session_t.ws.args == ()
        assert client_session_t.ws.kwargs == client._ws_connect_kwargs

    @_helpers.timeout_after(10.0)
    async def test_ws_closed_afterwards(self, client, client_session_t):
        with self.suppress_closure():
            await client.connect(client_session_t)
        client.close.assert_awaited_with(1000)

    @_helpers.timeout_after(10.0)
    async def test_disconnecting_unsets_connected_at(self, client, client_session_t):
        assert math.isnan(client._connected_at)

        with mock.patch("time.perf_counter", return_value=420):
            with self.suppress_closure():
                await client.connect(client_session_t)
            assert math.isnan(client._connected_at)

    @_helpers.timeout_after(10.0)
    async def test_disconnecting_unsets_last_message_received(self, client, client_session_t):
        assert math.isnan(client.last_message_received)

        with mock.patch("time.perf_counter", return_value=420):
            with self.suppress_closure():
                await client.connect(client_session_t)
        assert math.isnan(client.last_message_received)

    @_helpers.timeout_after(10.0)
    async def test_disconnecting_unsets_last_heartbeat_sent(self, client, client_session_t):
        with self.suppress_closure():
            await client.connect(client_session_t)
        assert math.isnan(client.last_heartbeat_sent)

    @_helpers.timeout_after(10.0)
    async def test_disconnecting_drops_reference_to_session(self, client, client_session_t):
        with self.suppress_closure():
            await client.connect(client_session_t)
        assert client._session is None

    @_helpers.timeout_after(10.0)
    async def test_disconnecting_drops_reference_to_ws(self, client, client_session_t):
        with self.suppress_closure():
            await client.connect(client_session_t)
        assert client._ws is None

    @_helpers.timeout_after(10.0)
    async def test_disconnecting_increments_disconnect_count(self, client, client_session_t):
        client.disconnect_count = 69
        with self.suppress_closure():
            await client.connect(client_session_t)
        assert client.disconnect_count == 70

    @_helpers.timeout_after(10.0)
    async def test_disconnecting_dispatches_DISCONNECT(self, client, client_session_t):
        client.dispatch = mock.MagicMock()
        with self.suppress_closure():
            await client.connect(client_session_t)
        client.dispatch.assert_called_with(client, "DISCONNECT", containers.EMPTY_DICT)

    @_helpers.timeout_after(10.0)
    async def test_new_zlib_each_time(self, client, client_session_t):
        assert client._zlib is None
        previous_zlib = None

        for i in range(20):
            with self.suppress_closure():
                await client.connect(client_session_t)
            assert client._zlib is not None
            assert previous_zlib is not client._zlib
            previous_zlib = client._zlib
            client._connected_at = float("nan")

    @_helpers.timeout_after(10.0)
    async def test_hello(self, client, client_session_t):
        with self.suppress_closure():
            await client.connect(client_session_t)

        client._receive.assert_awaited_once()

    @_helpers.timeout_after(10.0)
    @_helpers.assert_raises(type_=errors.GatewayError)
    async def test_no_hello_throws_RuntimeError(self, client, client_session_t):
        client._receive = mock.AsyncMock(return_value=self.non_hello_payload)
        await client.connect(client_session_t)

    @_helpers.timeout_after(10.0)
    async def test_heartbeat_keep_alive_correctly_started(self, client, client_session_t):
        with self.suppress_closure():
            await client.connect(client_session_t)

        client._heartbeat_keep_alive.assert_called_with(self.hello_payload["d"]["heartbeat_interval"] / 1_000.0)

    @_helpers.timeout_after(10.0)
    async def test_identify_or_resume_then_poll_events_started(self, client, client_session_t):
        with self.suppress_closure():
            await client.connect(client_session_t)

        client._identify_or_resume_then_poll_events.assert_called_once()

    @_helpers.timeout_after(10.0)
    async def test_waits_indefinitely_if_everything_is_working(self, client, client_session_t):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        client._heartbeat_keep_alive = deadlock
        client._identify_or_resume_then_poll_events = deadlock

        try:
            await asyncio.wait_for(client.connect(client_session_t), timeout=2.5)
            assert False
        except asyncio.TimeoutError:
            pass

    @_helpers.timeout_after(10.0)
    async def test_waits_for_identify_or_resume_then_poll_events_then_throws_that_exception(
        self, client, client_session_t
    ):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        class ExceptionThing(Exception):
            pass

        async def identify_or_resume_then_poll_events():
            raise ExceptionThing()

        client._heartbeat_keep_alive = deadlock
        client._identify_or_resume_then_poll_events = identify_or_resume_then_poll_events

        try:
            await client.connect(client_session_t)
            assert False
        except ExceptionThing:
            pass

    async def test_waits_for_heartbeat_keep_alive_to_return_then_throws_GatewayClientClosedError(
        self, client, client_session_t
    ):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        async def heartbeat_keep_alive(_):
            pass

        client._heartbeat_keep_alive = heartbeat_keep_alive
        client._identify_or_resume_then_poll_events = deadlock

        try:
            await client.connect(client_session_t)
            assert False
        except errors.GatewayClientClosedError:
            pass

    async def test_waits_for_identify_or_resume_then_poll_events_to_return_throws_GatewayClientClosedError(
        self, client, client_session_t
    ):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        async def identify_or_resume_then_poll_events():
            pass

        client._heartbeat_keep_alive = deadlock
        client._identify_or_resume_then_poll_events = identify_or_resume_then_poll_events

        try:
            await client.connect(client_session_t)
            assert False
        except errors.GatewayClientClosedError:
            pass

    async def test_TimeoutError_on_heartbeat_keep_alive_raises_GatewayZombiedError(self, client, client_session_t):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        async def heartbeat_keep_alive(_):
            raise asyncio.TimeoutError("reee")

        client._heartbeat_keep_alive = heartbeat_keep_alive
        client._identify_or_resume_then_poll_events = deadlock

        try:
            await client.connect(client_session_t)
            assert False
        except errors.GatewayZombiedError:
            pass

    async def test_TimeoutError_on_identify_or_resume_then_poll_events_raises_GatewayZombiedError(
        self, client, client_session_t
    ):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        async def identify_or_resume_then_poll_events():
            raise asyncio.TimeoutError("reee")

        client._heartbeat_keep_alive = deadlock
        client._identify_or_resume_then_poll_events = identify_or_resume_then_poll_events

        try:
            await client.connect(client_session_t)
            assert False
        except errors.GatewayZombiedError:
            pass


@pytest.mark.asyncio
class TestGatewayClientIdentifyOrResumeThenPollEvents:
    @pytest.fixture
    def client(self):
        client = _helpers.unslot_class(gateway.GatewayClient)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("_identify_or_resume_then_poll_events",))

        def send(_):
            client.send_time = time.perf_counter()

        def poll_events():
            client.poll_events_time = time.perf_counter()

        client._send = mock.AsyncMock(wraps=send)
        client._poll_events = mock.AsyncMock(spec=gateway.GatewayClient._send, wraps=poll_events)
        return client

    async def test_no_session_id_sends_identify_then_polls_events(self, client):
        client.session_id = None
        await client._identify_or_resume_then_poll_events()

        client._send.assert_awaited_once()
        args, kwargs = client._send.call_args
        assert len(args) == 1
        payload = args[0]
        assert payload["op"] == 2  # IDENTIFY
        client._poll_events.assert_awaited_once()
        assert client.send_time <= client.poll_events_time

    async def test_session_id_sends_resume_then_polls_events(self, client):
        client.session_id = 69420
        await client._identify_or_resume_then_poll_events()

        client._send.assert_awaited_once()
        args, kwargs = client._send.call_args
        assert len(args) == 1
        payload = args[0]
        assert payload["op"] == 6  # RESUME
        client._poll_events.assert_awaited_once()
        assert client.send_time <= client.poll_events_time

    async def test_identify_payload_no_intents_no_presence(self, client):
        client._presence = None
        client._intents = None
        client.session_id = None
        client._token = "aaaa"
        client._large_threshold = 420
        client.shard_id = 69
        client.shard_count = 96

        await client._identify_or_resume_then_poll_events()

        client._send.assert_awaited_once_with(
            {
                "op": 2,
                "d": {
                    "token": "aaaa",
                    "compress": False,
                    "large_threshold": 420,
                    "properties": {
                        "$os": user_agent.system_type(),
                        "$browser": user_agent.library_version(),
                        "$device": user_agent.python_version(),
                    },
                    "shard": [69, 96],
                },
            }
        )

    async def test_identify_payload_with_presence(self, client):
        presence = {"aaa": "bbb"}
        client._presence = presence
        client._intents = None
        client.session_id = None
        client._token = "aaaa"
        client._large_threshold = 420
        client.shard_id = 69
        client.shard_count = 96

        await client._identify_or_resume_then_poll_events()

        client._send.assert_awaited_once_with(
            {
                "op": 2,
                "d": {
                    "token": "aaaa",
                    "compress": False,
                    "large_threshold": 420,
                    "properties": {
                        "$os": user_agent.system_type(),
                        "$browser": user_agent.library_version(),
                        "$device": user_agent.python_version(),
                    },
                    "shard": [69, 96],
                    "presence": presence,
                },
            }
        )

    async def test_identify_payload_with_intents(self, client):
        intents = 629 | 139
        client._presence = None
        client._intents = intents
        client.session_id = None
        client._token = "aaaa"
        client._large_threshold = 420
        client.shard_id = 69
        client.shard_count = 96

        await client._identify_or_resume_then_poll_events()

        client._send.assert_awaited_once_with(
            {
                "op": 2,
                "d": {
                    "token": "aaaa",
                    "compress": False,
                    "large_threshold": 420,
                    "properties": {
                        "$os": user_agent.system_type(),
                        "$browser": user_agent.library_version(),
                        "$device": user_agent.python_version(),
                    },
                    "shard": [69, 96],
                    "intents": intents,
                },
            }
        )

    async def test_identify_payload_with_intents_and_presence(self, client):
        intents = 629 | 139
        presence = {"aaa": "bbb"}
        client._presence = presence
        client._intents = intents
        client.session_id = None
        client._token = "aaaa"
        client._large_threshold = 420
        client.shard_id = 69
        client.shard_count = 96

        await client._identify_or_resume_then_poll_events()

        client._send.assert_awaited_once_with(
            {
                "op": 2,
                "d": {
                    "token": "aaaa",
                    "compress": False,
                    "large_threshold": 420,
                    "properties": {
                        "$os": user_agent.system_type(),
                        "$browser": user_agent.library_version(),
                        "$device": user_agent.python_version(),
                    },
                    "shard": [69, 96],
                    "intents": intents,
                    "presence": presence,
                },
            }
        )

    @_helpers.timeout_after(10.0)
    @pytest.mark.parametrize("seq", [None, 999])
    async def test_resume_payload(self, client, seq):
        client.session_id = 69420
        client.seq = seq
        client.token = "reee"

        await client._identify_or_resume_then_poll_events()

        client._send.assert_awaited_once_with({"op": 6, "d": {"token": "1234", "session_id": 69420, "seq": seq,}})


@pytest.mark.asyncio
class TestHeartbeatKeepAlive:
    @pytest.fixture
    def client(self, event_loop):
        asyncio.set_event_loop(event_loop)
        client = _helpers.unslot_class(gateway.GatewayClient)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("_heartbeat_keep_alive",))
        client._send = mock.AsyncMock()
        # This won't get set on the right event loop if we are not careful
        client.closed_event = asyncio.Event()
        client.last_heartbeat_ack_received = time.perf_counter()
        return client

    @_helpers.timeout_after(10.0)
    async def test_loops_indefinitely_until_requesting_close_event_set(self, client, event_loop):
        def send(_):
            client.last_heartbeat_ack_received = time.perf_counter() + 3

        client._send = mock.AsyncMock(wraps=send)

        task: asyncio.Future = event_loop.create_task(client._heartbeat_keep_alive(0.01))
        await asyncio.sleep(2)

        if task.done():
            raise task.exception()

        client.requesting_close_event.set()
        await asyncio.sleep(2)
        assert task.done()

        assert client._send.await_count > 2  # arbitrary number to imply a lot of calls.

    @_helpers.timeout_after(10.0)
    async def test_heartbeat_interval_is_waited_on_heartbeat_sent_until_requesting_close_event_set(
        self, client, event_loop
    ):
        task: asyncio.Future = event_loop.create_task(client._heartbeat_keep_alive(100_000))
        await asyncio.sleep(2)
        client.requesting_close_event.set()
        await asyncio.sleep(0.1)
        assert task.done()

    @_helpers.timeout_after(1.0)
    @_helpers.assert_raises(type_=asyncio.TimeoutError)
    async def test_last_heartbeat_ack_received_less_than_last_heartbeat_sent_raises_TimeoutError(self, client):
        client.last_heartbeat_sent = 220
        client.last_message_received = 20

        await client._heartbeat_keep_alive(0.25)

    @pytest.mark.parametrize("seq", [None, 0, 259])
    async def test_heartbeat_payload(self, client, seq):
        client.seq = seq
        with contextlib.suppress(asyncio.TimeoutError):
            with async_timeout.timeout(1.0):
                await client._heartbeat_keep_alive(1.0)

        client._send.assert_awaited_once_with({"op": 1, "d": seq})


@pytest.mark.asyncio
class TestClose:
    @pytest.fixture
    def client(self, event_loop):
        asyncio.set_event_loop(event_loop)
        client = _helpers.unslot_class(gateway.GatewayClient)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("close",))
        client.ws = _helpers.create_autospec(aiohttp.ClientWebSocketResponse)
        client.session = _helpers.create_autospec(aiohttp.ClientSession)
        client.closed_event = asyncio.Event()
        return client

    @_helpers.timeout_after(1.0)
    async def test_closing_already_closing_websocket_does_nothing(self, client):
        client.requesting_close_event.set()
        client.requesting_close_event.set = mock.MagicMock()
        await client.close()
        client.requesting_close_event.set.assert_not_called()

    @_helpers.timeout_after(1.0)
    async def test_closing_first_time_sets_closed_event(self, client):
        client.closed_event.clear()
        await client.close()
        assert client.closed_event.is_set()

    @_helpers.timeout_after(3.0)
    async def test_closing_ws_first_time_only_waits_2s(self, client):
        client.closed_event.clear()

        async def close(_):
            await asyncio.sleep(10.0)

        client.ws.close = close
        client.session.close = mock.AsyncMock()
        await client.close()

    @_helpers.timeout_after(3.0)
    async def test_closing_session_first_time_only_waits_2s(self, client):
        client.closed_event.clear()

        async def close():
            await asyncio.sleep(10.0)

        client.ws.close = mock.AsyncMock()
        client.session.close = close
        await client.close()

    @_helpers.timeout_after(3.0)
    async def test_closing_ws_first_time_only_waits_2s(self, client):
        client.closed_event.clear()

        async def close(code):
            await asyncio.sleep(10.0)

        client.ws.close = close
        client.session.close = mock.AsyncMock()
        await client.close()

    @_helpers.timeout_after(5.0)
    async def test_closing_ws_and_session_first_time_only_waits_4s(self, client):
        client.closed_event.clear()

        async def close(code=...):
            await asyncio.sleep(10.0)

        client.ws.close = close
        client.session.close = close
        await client.close()


@pytest.mark.asyncio
class TestPollEvents:
    @pytest.fixture
    def client(self, event_loop):
        asyncio.set_event_loop(event_loop)
        client = _helpers.unslot_class(gateway.GatewayClient)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("_poll_events",))
        return client

    @_helpers.timeout_after(5.0)
    async def test_opcode_0(self, client):
        def receive():
            client.requesting_close_event.set()
            return {"op": 0, "d": {"content": "whatever"}, "t": "MESSAGE_CREATE", "s": 123}

        client._receive = mock.AsyncMock(wraps=receive)

        await client._poll_events()

        client.dispatch.assert_called_with(client, "MESSAGE_CREATE", {"content": "whatever"})


@pytest.mark.asyncio
class TestRequestGuildMembers:
    @pytest.fixture
    def client(self, event_loop):
        asyncio.set_event_loop(event_loop)
        client = _helpers.unslot_class(gateway.GatewayClient)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("request_guild_members",))
        return client

    async def test_no_kwargs(self, client):
        await client.request_guild_members("1234", "5678")
        client._send.assert_awaited_once_with({"op": 8, "d": {"guild_id": ["1234", "5678"], "query": "", "limit": 0}})

    @pytest.mark.parametrize(
        ["kwargs", "expected_limit", "expected_query"],
        [({"limit": 22}, 22, ""), ({"query": "lol"}, 0, "lol"), ({"limit": 22, "query": "lol"}, 22, "lol"),],
    )
    async def test_limit_and_query(self, client, kwargs, expected_limit, expected_query):
        await client.request_guild_members("1234", "5678", **kwargs)
        client._send.assert_awaited_once_with(
            {"op": 8, "d": {"guild_id": ["1234", "5678"], "query": expected_query, "limit": expected_limit,}}
        )

    async def test_user_ids(self, client):
        await client.request_guild_members("1234", "5678", user_ids=["9", "18", "27"])
        client._send.assert_awaited_once_with(
            {"op": 8, "d": {"guild_id": ["1234", "5678"], "user_ids": ["9", "18", "27"]}}
        )

    @pytest.mark.parametrize("presences", [True, False])
    async def test_presences(self, client, presences):
        await client.request_guild_members("1234", "5678", presences=presences)
        client._send.assert_awaited_once_with(
            {"op": 8, "d": {"guild_id": ["1234", "5678"], "query": "", "limit": 0, "presences": presences}}
        )


@pytest.mark.asyncio
class TestUpdatePresence:
    @pytest.fixture
    def client(self, event_loop):
        asyncio.set_event_loop(event_loop)
        client = _helpers.unslot_class(gateway.GatewayClient)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("update_presence",))
        return client

    async def test_sends_payload(self, client):
        await client.update_presence({"foo": "bar"})
        client._send.assert_awaited_once_with({"op": 3, "d": {"foo": "bar"}})

    async def test_caches_payload_for_later(self, client):
        client._presence = {"baz": "bork"}
        await client.update_presence({"foo": "bar"})
        assert client._presence == {"foo": "bar"}
