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

import aiohttp
import async_timeout
import mock
import pytest

from hikari import errors
from hikari.gateway import connection
from hikari.internal import codes
from hikari.internal import more_collections
from hikari.internal import user_agents
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
class TestShardConstructor:
    async def test_init_sets_shard_numbers_correctly(self):
        input_shard_id, input_shard_count, expected_shard_id, expected_shard_count = 1, 2, 1, 2
        client = connection.Shard(shard_id=input_shard_id, shard_count=input_shard_count, token="xxx", url="yyy")
        assert client.shard_id == expected_shard_id
        assert client.shard_count == expected_shard_count

    async def test_dispatch_is_callable(self):
        client = connection.Shard(token="xxx", url="yyy")
        client.dispatcher(client, "ping", "pong")

    @pytest.mark.parametrize(
        ["compression", "expected_url_query"],
        [
            (True, dict(v=["6"], encoding=["json"], compress=["zlib-stream"])),
            (False, dict(v=["6"], encoding=["json"])),
        ],
    )
    async def test_compression(self, compression, expected_url_query):
        url = "ws://baka-im-not-a-http-url:49620/locate/the/bloody/websocket?ayyyyy=lmao"
        client = connection.Shard(token="xxx", url=url, compression=compression)
        scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(client.url)
        assert scheme == "ws"
        assert netloc == "baka-im-not-a-http-url:49620"
        assert path == "/locate/the/bloody/websocket"
        assert params == ""
        actual_query_dict = urllib.parse.parse_qs(query)
        assert actual_query_dict == expected_url_query
        assert fragment == ""

    async def test_init_hearbeat_defaults_before_startup(self):
        client = connection.Shard(token="xxx", url="yyy")
        assert math.isnan(client.last_heartbeat_sent)
        assert math.isnan(client.heartbeat_latency)
        assert math.isnan(client.last_message_received)

    async def test_init_connected_at_is_nan(self):
        client = connection.Shard(token="xxx", url="yyy")
        assert math.isnan(client.connected_at)


@pytest.mark.asyncio
class TestShardUptimeProperty:
    @pytest.mark.parametrize(
        ["connected_at", "now", "expected_uptime"],
        [(float("nan"), 31.0, datetime.timedelta(seconds=0)), (10.0, 31.0, datetime.timedelta(seconds=21.0)),],
    )
    async def test_uptime(self, connected_at, now, expected_uptime):
        with mock.patch("time.perf_counter", return_value=now):
            client = connection.Shard(token="xxx", url="yyy")
            client.connected_at = connected_at
            assert client.up_time == expected_uptime


@pytest.mark.asyncio
class TestShardIsConnectedProperty:
    @pytest.mark.parametrize(["connected_at", "is_connected"], [(float("nan"), False), (15, True), (2500.0, True),])
    async def test_is_connected(self, connected_at, is_connected):
        client = connection.Shard(token="xxx", url="yyy")
        client.connected_at = connected_at
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
        client = connection.Shard(token="xxx", url="yyy")
        client.disconnect_count = disconnect_count
        client.connected_at = 420 if is_connected else float("nan")
        assert client.reconnect_count == expected_reconnect_count


@pytest.mark.asyncio
class TestGatewayCurrentPresenceProperty:
    async def test_returns_presence(self):
        client = connection.Shard(token="xxx", url="yyy")
        client._presence = {"foo": "bar"}
        assert client.current_presence == {"foo": "bar"}

    async def test_returns_copy(self):
        client = connection.Shard(token="xxx", url="yyy")
        client._presence = {"foo": "bar"}
        assert client.current_presence is not client._presence


@pytest.mark.asyncio
class TestConnect:
    @property
    def hello_payload(self):
        return {"op": 10, "d": {"heartbeat_interval": 30_000}}

    @property
    def non_hello_payload(self):
        return {"op": 69, "d": "yeet"}

    @pytest.fixture
    def client(self, event_loop):
        asyncio.set_event_loop(event_loop)
        client = _helpers.unslot_class(connection.Shard)(url="ws://localhost", token="xxx")
        client = _helpers.mock_methods_on(client, except_=("connect",))
        client._receive = mock.AsyncMock(return_value=self.hello_payload)
        return client

    @contextlib.contextmanager
    def suppress_closure(self):
        with contextlib.suppress(errors.GatewayClientClosedError):
            yield

    async def test_RuntimeError_if_already_connected(self, client):
        client.connected_at = 22.4  # makes client expect to be connected

        try:
            with self.suppress_closure():
                await client.connect()
            assert False
        except RuntimeError:
            pass

        assert client._ws is None
        client._run.assert_not_called()
        client._heartbeat_keep_alive.assert_not_called()

    @pytest.mark.parametrize(
        "event_attr", ["closed_event", "handshake_event", "ready_event", "requesting_close_event", "resumed_event"]
    )
    @_helpers.timeout_after(10.0)
    async def test_events_unset_on_open(self, client, event_attr):
        getattr(client, event_attr).set()
        with self.suppress_closure():
            task = asyncio.create_task(client.connect())
            # Wait until the first main event object is set. By then we expect
            # the event we are testing to have been unset again if it is
            # working properly.
            await client.hello_event.wait()
            assert not getattr(client, event_attr).is_set()
            await task

    async def test_hello_event_unset_on_open(self, client):
        client.hello_event = mock.MagicMock()

        with self.suppress_closure():
            await client.connect()

        client.hello_event.clear.assert_called_once()
        client.hello_event.set.assert_called_once()

    @_helpers.timeout_after(10.0)
    async def test_closed_event_set_on_connect_terminate(self, client):
        with self.suppress_closure():
            await asyncio.create_task(client.connect())

        assert client.closed_event.is_set()

    @_helpers.timeout_after(10.0)
    async def test_session_opened_with_expected_kwargs(self, client):
        with self.suppress_closure():
            await client.connect()
        client._create_ws.assert_awaited_once_with(client.url, compress=0, auto_ping=True, max_msg_size=0)

    @_helpers.timeout_after(10.0)
    async def test_ws_closed_afterwards(self, client):
        with self.suppress_closure():
            await client.connect()
        client.close.assert_awaited_with(1000)

    @_helpers.timeout_after(10.0)
    async def test_disconnecting_unsets_connected_at(self, client):
        assert math.isnan(client.connected_at)

        with mock.patch("time.perf_counter", return_value=420):
            with self.suppress_closure():
                await client.connect()
            assert math.isnan(client.connected_at)

    @_helpers.timeout_after(10.0)
    async def test_disconnecting_unsets_last_message_received(self, client):
        assert math.isnan(client.last_message_received)

        with mock.patch("time.perf_counter", return_value=420):
            with self.suppress_closure():
                await client.connect()
        assert math.isnan(client.last_message_received)

    @_helpers.timeout_after(10.0)
    async def test_disconnecting_unsets_last_heartbeat_sent(
        self, client,
    ):
        with self.suppress_closure():
            await client.connect()
        assert math.isnan(client.last_heartbeat_sent)

    @_helpers.timeout_after(10.0)
    async def test_disconnecting_drops_reference_to_ws(self, client):
        with self.suppress_closure():
            await client.connect()
        assert client._ws is None

    @_helpers.timeout_after(10.0)
    async def test_disconnecting_increments_disconnect_count(self, client):
        client.disconnect_count = 69
        with self.suppress_closure():
            await client.connect()
        assert client.disconnect_count == 70

    @_helpers.timeout_after(10.0)
    async def test_connecting_dispatches_CONNECTED(self, client):
        with self.suppress_closure():
            task = asyncio.create_task(client.connect())
            await client.hello_event.wait()
            # sanity check for the DISCONNECTED test
            assert mock.call("CONNECTED", more_collections.EMPTY_DICT) in client.do_dispatch.call_args_list
            client.do_dispatch.assert_called_with("CONNECTED", more_collections.EMPTY_DICT)
            await task

    @_helpers.timeout_after(10.0)
    async def test_disconnecting_dispatches_DISCONNECTED(self, client):
        with self.suppress_closure():
            task = asyncio.create_task(client.connect())
            await client.hello_event.wait()
            assert mock.call("DISCONNECTED", more_collections.EMPTY_DICT) not in client.do_dispatch.call_args_list
            await task
        client.do_dispatch.assert_called_with("DISCONNECTED", more_collections.EMPTY_DICT)

    @_helpers.timeout_after(10.0)
    async def test_new_zlib_each_time(self, client):
        assert client._zlib is None
        previous_zlib = None

        for i in range(20):
            with self.suppress_closure():
                await client.connect()
            assert client._zlib is not None
            assert previous_zlib is not client._zlib
            previous_zlib = client._zlib
            client.connected_at = float("nan")

    @_helpers.timeout_after(10.0)
    async def test_hello(self, client):
        with self.suppress_closure():
            await client.connect()

        client._receive.assert_awaited_once()

    @_helpers.timeout_after(10.0)
    @_helpers.assert_raises(type_=errors.GatewayError)
    async def test_no_hello_throws_GatewayError(self, client):
        client._receive = mock.AsyncMock(return_value=self.non_hello_payload)
        await client.connect()

    @_helpers.timeout_after(10.0)
    async def test_heartbeat_keep_alive_correctly_started(self, client):
        with self.suppress_closure():
            await client.connect()

        client._heartbeat_keep_alive.assert_called_with(self.hello_payload["d"]["heartbeat_interval"] / 1_000.0)

    @_helpers.timeout_after(10.0)
    async def test_identify_or_resume_then_poll_events_started(self, client):
        with self.suppress_closure():
            await client.connect()

        client._run.assert_called_once()

    @_helpers.timeout_after(10.0)
    async def test_waits_indefinitely_if_everything_is_working(self, client):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        client._heartbeat_keep_alive = deadlock
        client._run = deadlock

        try:
            await asyncio.wait_for(client.connect(), timeout=2.5)
            assert False
        except asyncio.TimeoutError:
            pass

    @_helpers.timeout_after(10.0)
    async def test_waits_for_run_then_throws_that_exception(self, client):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        class ExceptionThing(Exception):
            pass

        async def run():
            raise ExceptionThing()

        client._heartbeat_keep_alive = deadlock
        client._run = run

        try:
            await client.connect()
            assert False
        except ExceptionThing:
            pass

    async def test_waits_for_heartbeat_keep_alive_to_return_then_throws_GatewayClientClosedError(self, client):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        async def heartbeat_keep_alive(_):
            pass

        client._heartbeat_keep_alive = heartbeat_keep_alive
        client._run = deadlock

        try:
            await client.connect()
            assert False
        except errors.GatewayClientClosedError:
            pass

    async def test_waits_for_identify_or_resume_then_poll_events_to_return_throws_GatewayClientClosedError(
        self, client,
    ):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        async def run():
            pass

        client._heartbeat_keep_alive = deadlock
        client._run = run

        try:
            await client.connect()
            assert False
        except errors.GatewayClientClosedError:
            pass

    async def test_TimeoutError_on_heartbeat_keep_alive_raises_GatewayZombiedError(self, client):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        async def heartbeat_keep_alive(_):
            raise asyncio.TimeoutError("reee")

        client._heartbeat_keep_alive = heartbeat_keep_alive
        client._run = deadlock

        try:
            await client.connect()
            assert False
        except errors.GatewayZombiedError:
            pass

    async def test_TimeoutError_on_identify_or_resume_then_poll_events_raises_GatewayZombiedError(self, client):
        async def deadlock(*_, **__):
            await asyncio.get_running_loop().create_future()

        async def run():
            raise asyncio.TimeoutError("reee")

        client._heartbeat_keep_alive = deadlock
        client._run = run

        try:
            await client.connect()
            assert False
        except errors.GatewayZombiedError:
            pass


@pytest.mark.asyncio
class TestShardRun:
    @pytest.fixture
    def client(self, event_loop):
        asyncio.set_event_loop(event_loop)
        client = _helpers.unslot_class(connection.Shard)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("_run",))

        def receive():
            client.recv_time = time.perf_counter()

        def identify():
            client.identify_time = time.perf_counter()

        def resume():
            client.resume_time = time.perf_counter()

        client._identify = mock.AsyncMock(spec=connection.Shard._identify, wraps=identify)
        client._resume = mock.AsyncMock(spec=connection.Shard._resume, wraps=resume)
        client._receive = mock.AsyncMock(spec=connection.Shard._receive, wraps=receive)
        return client

    async def test_no_session_id_sends_identify_then_polls_events(self, client):
        client.session_id = None
        task = asyncio.create_task(client._run())
        await asyncio.sleep(0.25)
        try:
            client._identify.assert_awaited_once()
            client._receive.assert_awaited_once()
            client._resume.assert_not_called()
            assert client.identify_time <= client.recv_time
        finally:
            task.cancel()

    async def test_session_id_sends_resume_then_polls_events(self, client):
        client.session_id = 69420
        task = asyncio.create_task(client._run())
        await asyncio.sleep(0.25)
        try:
            client._resume.assert_awaited_once()
            client._receive.assert_awaited_once()
            client._identify.assert_not_called()
            assert client.resume_time <= client.recv_time
        finally:
            task.cancel()


@pytest.mark.asyncio
class TestIdentify:
    @pytest.fixture
    def client(self, event_loop):
        asyncio.set_event_loop(event_loop)
        client = _helpers.unslot_class(connection.Shard)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("_identify",))
        return client

    async def test_identify_payload_no_intents_no_presence(self, client):
        client._presence = None
        client._intents = None
        client.session_id = None
        client._token = "aaaa"
        client.large_threshold = 420
        client.shard_id = 69
        client.shard_count = 96

        await client._identify()

        client._send.assert_awaited_once_with(
            {
                "op": 2,
                "d": {
                    "token": "aaaa",
                    "compress": False,
                    "large_threshold": 420,
                    "properties": user_agents.UserAgent().websocket_triplet,
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
        client.large_threshold = 420
        client.shard_id = 69
        client.shard_count = 96

        await client._identify()

        client._send.assert_awaited_once_with(
            {
                "op": 2,
                "d": {
                    "token": "aaaa",
                    "compress": False,
                    "large_threshold": 420,
                    "properties": user_agents.UserAgent().websocket_triplet,
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
        client.large_threshold = 420
        client.shard_id = 69
        client.shard_count = 96

        await client._identify()

        client._send.assert_awaited_once_with(
            {
                "op": 2,
                "d": {
                    "token": "aaaa",
                    "compress": False,
                    "large_threshold": 420,
                    "properties": user_agents.UserAgent().websocket_triplet,
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
        client.large_threshold = 420
        client.shard_id = 69
        client.shard_count = 96

        await client._identify()

        client._send.assert_awaited_once_with(
            {
                "op": 2,
                "d": {
                    "token": "aaaa",
                    "compress": False,
                    "large_threshold": 420,
                    "properties": user_agents.UserAgent().websocket_triplet,
                    "shard": [69, 96],
                    "intents": intents,
                    "presence": presence,
                },
            }
        )


@pytest.mark.asyncio
class TestResume:
    @pytest.fixture
    def client(self, event_loop):
        asyncio.set_event_loop(event_loop)
        client = _helpers.unslot_class(connection.Shard)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("_resume",))
        return client

    @_helpers.timeout_after(10.0)
    @pytest.mark.parametrize("seq", [None, 999])
    async def test_resume_payload(self, client, seq):
        client.session_id = 69420
        client.seq = seq
        client._token = "reee"

        await client._resume()

        client._send.assert_awaited_once_with(
            {"op": codes.GatewayOpcode.RESUME, "d": {"token": "reee", "session_id": 69420, "seq": seq}}
        )


@pytest.mark.asyncio
class TestHeartbeatKeepAlive:
    @pytest.fixture
    def client(self, event_loop):
        asyncio.set_event_loop(event_loop)
        client = _helpers.unslot_class(connection.Shard)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("_heartbeat_keep_alive", "_zombie_detector"))
        client._send = mock.AsyncMock()
        # This won't get set on the right event loop if we are not careful
        client.closed_event = asyncio.Event()
        client.last_heartbeat_ack_received = time.perf_counter()
        return client

    @_helpers.timeout_after(10.0)
    async def test_loops_indefinitely_until_requesting_close_event_set(self, client, event_loop):
        async def recv():
            await asyncio.sleep(0.1)
            client.last_heartbeat_ack_received = time.perf_counter()
            client.last_message_received = client.last_heartbeat_ack_receied

        client._send = mock.AsyncMock(wraps=lambda *_: asyncio.create_task(recv()))

        task: asyncio.Future = event_loop.create_task(client._heartbeat_keep_alive(0.5))
        await asyncio.sleep(1.5)

        if task.done():
            raise task.exception()

        client.requesting_close_event.set()
        await asyncio.sleep(1.5)
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
        client.last_message_received = time.perf_counter() - 1

        await client._heartbeat_keep_alive(0.25)

    @pytest.mark.parametrize("seq", [None, 0, 259])
    async def test_heartbeat_payload(self, client, seq):
        client.seq = seq
        with contextlib.suppress(asyncio.TimeoutError):
            with async_timeout.timeout(0.5):
                await client._heartbeat_keep_alive(1)

        client._send.assert_awaited_once_with({"op": 1, "d": seq})

    @_helpers.assert_does_not_raise(type_=asyncio.TimeoutError)
    async def test_zombie_detector_not_a_zombie(self):
        client = mock.MagicMock()
        client.last_message_received = time.perf_counter() - 5
        heartbeat_interval = 41.25
        connection.Shard._zombie_detector(client, heartbeat_interval)

    @_helpers.assert_raises(type_=asyncio.TimeoutError)
    async def test_zombie_detector_is_a_zombie(self):
        client = mock.MagicMock()
        client.last_message_received = time.perf_counter() - 500000
        heartbeat_interval = 41.25
        connection.Shard._zombie_detector(client, heartbeat_interval)


@pytest.mark.asyncio
class TestClose:
    @pytest.fixture
    def client(self, event_loop):
        asyncio.set_event_loop(event_loop)
        client = _helpers.unslot_class(connection.Shard)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("close",))
        client.ws = mock.MagicMock(aiohttp.ClientWebSocketResponse)
        client.session = mock.MagicMock(aiohttp.ClientSession)
        client.closed_event = asyncio.Event()
        client._presence = {}
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
        client = _helpers.unslot_class(connection.Shard)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("_run",))
        return client

    @_helpers.timeout_after(5.0)
    async def test_opcode_0(self, client):
        def receive():
            client.requesting_close_event.set()
            return {"op": 0, "d": {"content": "whatever"}, "t": "MESSAGE_CREATE", "s": 123}

        client._receive = mock.AsyncMock(wraps=receive)

        await client._run()

        client.do_dispatch.assert_called_with("MESSAGE_CREATE", {"content": "whatever"})

    @_helpers.timeout_after(5.0)
    async def test_opcode_0_resume_sets_session_id(self, client):
        client.seq = None
        client.session_id = None

        def receive():
            client.requesting_close_event.set()
            return {"op": 0, "d": {"v": 69, "session_id": "1a2b3c4d"}, "t": "READY", "s": 123}

        client._receive = mock.AsyncMock(wraps=receive)

        await client._run()

        client.do_dispatch.assert_called_with("READY", {"v": 69, "session_id": "1a2b3c4d"})

        assert client.session_id == "1a2b3c4d"
        assert client.seq == 123


@pytest.mark.asyncio
class TestRequestGuildMembers:
    @pytest.fixture
    def client(self, event_loop):
        asyncio.set_event_loop(event_loop)
        client = _helpers.unslot_class(connection.Shard)(token="1234", url="xxx")
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
        client = _helpers.unslot_class(connection.Shard)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("update_presence",))
        return client

    async def test_sends_payload(self, client):
        await client.update_presence({"afk": True, "game": {"name": "69", "type": 1}, "since": 69, "status": "dnd"})
        client._send.assert_awaited_once_with(
            {"op": 3, "d": {"afk": True, "game": {"name": "69", "type": 1}, "since": 69, "status": "dnd"}}
        )

    async def test_caches_payload_for_later(self, client):
        client._presence = {"baz": "bork"}
        await client.update_presence({"afk": True, "game": {"name": "69", "type": 1}, "since": 69, "status": "dnd"})
        assert client._presence == {"afk": True, "game": {"name": "69", "type": 1}, "since": 69, "status": "dnd"}

    async def test_injects_default_fields(self, client):
        await client.update_presence({"foo": "bar"})
        for k in ("foo", "afk", "game", "since", "status"):
            assert k in client._presence


@pytest.mark.asyncio
class TestUpdateVoiceState:
    @pytest.fixture
    def client(self, event_loop):
        asyncio.set_event_loop(event_loop)
        client = _helpers.unslot_class(connection.Shard)(token="1234", url="xxx")
        client = _helpers.mock_methods_on(client, except_=("update_voice_state",))
        return client

    @pytest.mark.parametrize("channel", ["1234", None])
    async def test_sends_payload(self, client, channel_id):
        await client.update_voice_state("9987", channel_id, True, False)
        client._send.assert_awaited_once_with(
            {
                "op": codes.GatewayOpcode.VOICE_STATE_UPDATE,
                "d": {"guild_id": "9987", "channel": channel_id, "self_mute": True, "self_deaf": False,},
            }
        )
