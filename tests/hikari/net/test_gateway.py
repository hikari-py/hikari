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
import json
import math
import platform
import time
import urllib.parse as urlparse
import zlib

import asynctest
import pytest

from hikari import errors
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import user_agent
from hikari.net import gateway
from hikari.net import opcodes
from hikari.net import ws
from tests.hikari import _helpers


def teardown_function():
    _helpers.purge_loop()


class Context:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class MockSession(ws.WebSocketClientSession):
    def __init__(self, ws):
        self.ws = ws
        self._closed = False
        self.ws_connect = asynctest.MagicMock(wraps=self.ws_connect, spec_set=self.ws_connect)

    async def __aenter__(self):
        return

    async def __aexit__(self, *_, **__):
        self._closed = True

    def __del__(self):
        pass

    @property
    def closed(self):
        return self._closed

    def ws_connect(self, url: str, **kwargs):
        return self


class MockGateway(gateway.GatewayClientV7):
    def __init__(self, **kwargs):
        ws = Context()
        gateway.GatewayClientV7.__init__(self, **kwargs)
        self.ws = ws
        self.ws.close = asynctest.CoroutineMock()
        self.ws.send = asynctest.CoroutineMock()
        self.ws.receive_any_str = asynctest.CoroutineMock()
        self.ws.wait_closed = self._wait_closed
        self.client_session.close()
        self.client_session = MockSession(self.ws)

    @staticmethod
    async def _wait_closed():
        await asyncio.sleep(0.5)


def mock_run_once_parts(timeout=10):
    def decorator(coro):
        async def wrapper(*args, **kwargs):
            gw = MockGateway(
                uri="wss://gateway.discord.gg:4949/",
                loop=asyncio.get_event_loop(),
                token="1234",
                shard_id=917,
                shard_count=1234,
                large_threshold=69,
            )
            gw._receive_hello = asynctest.CoroutineMock(spec_set=gw._receive_hello)
            gw._send_resume = asynctest.CoroutineMock(spec_set=gw._send_resume)
            gw._send_heartbeat = asynctest.CoroutineMock(spec_set=gw._send_heartbeat)
            gw._send_identify = asynctest.CoroutineMock(spec_set=gw._send_identify)
            gw._keep_alive = asynctest.CoroutineMock(spec_set=gw._keep_alive)
            gw._process_events = asynctest.CoroutineMock(spec_set=gw._process_events)

            await coro(*args, **kwargs, gw=gw)

        wrapper.__name__ = coro.__name__
        wrapper.__qualname__ = coro.__qualname__
        return wrapper

    return decorator


# noinspection PyProtectedMember,SpellCheckingInspection,PyUnresolvedReferences
@pytest.mark.asyncio
@pytest.mark.gateway
@pytest.mark.slow
@pytest.mark.trylast
class TestGateway:
    async def test_init_produces_valid_url(self, event_loop):
        """GatewayConnection.__init__ should produce a valid query fragment for the URL."""
        # noinspection PyTypeChecker
        gw = gateway.GatewayClientV7(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234")
        bits: urlparse.ParseResult = urlparse.urlparse(gw.uri)

        assert bits.scheme == "wss"
        assert bits.hostname == "gateway.discord.gg"
        assert bits.port == 4949
        assert bits.query == "v=7&encoding=json&compression=zlib-stream"
        assert not bits.fragment

    async def test_do_resume_triggers_correct_signals(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234")

        try:
            await gw._trigger_resume(69, "boom")
            assert False, "No exception raised"
        except gateway._ResumeConnection:
            gw.ws.close.assert_awaited_once_with(code=69, reason="boom")

    async def test_do_reidentify_triggers_correct_signals(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234")

        try:
            await gw._trigger_identify(69, "boom")
            assert False, "No exception raised"
        except gateway._RestartConnection:
            gw.ws.close.assert_awaited_once_with(code=69, reason="boom")

    async def test_send_json_calls_websocket(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._logger = asynctest.MagicMock()

        # pretend to sleep only
        async def fake_sleep(*_):
            pass

        with _helpers.mock_patch(asyncio.sleep, new=fake_sleep):
            await gw._send_json({}, False)

        gw.ws.send.assert_awaited_once_with("{}")

    async def test_ratelimiting_on_send(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._warn_about_internal_rate_limit = asynctest.MagicMock(wraps=gw._warn_about_internal_rate_limit)
        gw.rate_limit._per = 1.5
        gw.rate_limit.reset_at = time.perf_counter() + 1.5

        for i in range(121):
            await gw._send_json({}, False)

        gw._warn_about_internal_rate_limit.assert_called()

    async def test_ratelimiting_on_send_can_be_overridden(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._warn_about_internal_rate_limit = asynctest.MagicMock(wraps=gw._warn_about_internal_rate_limit)
        gw.rate_limit._per = 3
        gw.rate_limit.reset_at = time.perf_counter() + 3

        for i in range(121):
            await gw._send_json({}, True)

        gw._warn_about_internal_rate_limit.assert_not_called()

    async def test_send_json_wont_send_massive_payloads(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._handle_payload_oversize = asynctest.MagicMock(wraps=gw._handle_payload_oversize)
        pl = {"d": {"lolololilolo": "lol" * 4096}, "op": "1", "blah": 2}
        await gw._send_json(pl, False)
        gw._handle_payload_oversize.assert_called_once_with(pl)

    async def test_receive_json_calls_receive_any_str_at_least_once(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw.ws.receive_any_str = asynctest.CoroutineMock(return_value="{}")
        await gw._receive_json()
        gw.ws.receive_any_str.assert_any_call()

    async def test_receive_json_closes_connection_if_payload_was_not_a_dict(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._trigger_identify = asynctest.CoroutineMock()
        gw.ws.receive_any_str = asynctest.CoroutineMock(return_value="[]")
        await gw._receive_json()
        gw.ws.receive_any_str.assert_any_call()
        gw._trigger_identify.assert_awaited_once_with(
            code=opcodes.GatewayClosure.TYPE_ERROR, reason="Expected JSON object."
        )

    async def test_receive_json_when_receiving_string_decodes_immediately(self, event_loop):
        with asynctest.patch("json.loads", new=asynctest.MagicMock(return_value={})) as json_loads:
            gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
            receive_any_str_value = "{" '  "foo": "bar",' '  "baz": "bork",' '  "qux": ["q", "u", "x", "x"]' "}"
            gw.ws.receive_any_str = asynctest.CoroutineMock(return_value=receive_any_str_value)
            await gw._receive_json()
            # noinspection PyUnresolvedReferences
            json_loads.assert_called_with(receive_any_str_value, object_hook=data_structures.ObjectProxy)

    async def test_receive_json_when_receiving_zlib_payloads_collects_before_decoding(self, event_loop):
        with asynctest.patch("json.loads", new=asynctest.MagicMock(return_value={})) as json_loads:
            gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
            receive_any_str_value = (
                "{" '  "foo": "bar",' '  "baz": "bork",' '  "qux": ["q", "u", "x", "x"]' "}".encode("utf-8")
            )

            payload = zlib.compress(receive_any_str_value) + b"\x00\x00\xff\xff"

            chunk_size = 16
            chunks = [payload[i : i + chunk_size] for i in range(0, len(payload), chunk_size)]

            gw.ws.receive_any_str = asynctest.CoroutineMock(side_effect=chunks)
            await gw._receive_json()
            # noinspection PyUnresolvedReferences
            json_loads.assert_called_with(
                receive_any_str_value.decode("utf-8"), object_hook=data_structures.ObjectProxy
            )

    async def test_small_zlib_payloads_leave_buffer_alone(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)

        with _helpers.mock_patch(json.loads, new=asynctest.MagicMock(return_value={})):
            receive_any_str_value = (
                "{" '  "foo": "bar",' '  "baz": "bork",' '  "qux": ["q", "u", "x", "x"]' "}".encode("utf-8")
            )

            payload = zlib.compress(receive_any_str_value) + b"\x00\x00\xff\xff"

            chunk_size = 16
            chunks = [payload[i : i + chunk_size] for i in range(0, len(payload), chunk_size)]

            first_array = gw._in_buffer
            gw.ws.receive_any_str = asynctest.CoroutineMock(side_effect=chunks)
            await gw._receive_json()
            assert gw._in_buffer is first_array

    async def test_massive_zlib_payloads_cause_buffer_replacement(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)

        with _helpers.mock_patch(json.loads, new=asynctest.MagicMock(return_value={})):
            receive_any_str_value = (
                "{" '  "foo": "bar",' '  "baz": "bork",' '  "qux": ["q", "u", "x", "x"]' "}".encode("utf-8")
            )

            payload = zlib.compress(receive_any_str_value) + b"\x00\x00\xff\xff"

            chunk_size = 16
            chunks = [payload[i : i + chunk_size] for i in range(0, len(payload), chunk_size)]

            first_array = gw._in_buffer
            gw.max_persistent_buffer_size = 3
            gw.ws.receive_any_str = asynctest.CoroutineMock(side_effect=chunks)
            await gw._receive_json()
            assert gw._in_buffer is not first_array

    async def test_heartbeat_beats_at_interval(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw.heartbeat_interval = 0.01

        task = asyncio.create_task(gw._keep_alive())
        try:
            await asyncio.sleep(0.5)
        finally:
            task.cancel()
            gw.ws.send.assert_awaited_with('{"op": 1, "d": null}')

    async def test_heartbeat_shuts_down_when_closure_request(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw.heartbeat_interval = 0.01

        task = asyncio.create_task(gw._keep_alive())
        try:
            await asyncio.sleep(0.5)
        finally:
            await gw.close(True)
            await task

    async def test_heartbeat_if_not_acknowledged_in_time_closes_connection_with_resume(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw.last_heartbeat_sent = -float("inf")
        gw.heartbeat_interval = 0

        task = asyncio.create_task(gw._keep_alive())

        await asyncio.sleep(0.5)

        task.cancel()
        gw.ws.close.assert_awaited_once()

    async def test_slow_loop_produces_warning(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw.heartbeat_interval = 0
        gw.heartbeat_latency = 0
        gw._handle_slow_client = asynctest.MagicMock(wraps=gw._handle_slow_client)
        task = asyncio.create_task(gw._keep_alive())

        await asyncio.sleep(0.5)

        task.cancel()
        gw._handle_slow_client.assert_called_once()

    async def test_send_heartbeat(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._send_json = asynctest.CoroutineMock()
        await gw._send_heartbeat()
        gw._send_json.assert_called_with({"op": 1, "d": None}, True)

    async def test_send_ack(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._send_json = asynctest.CoroutineMock()
        await gw._send_ack()
        gw._send_json.assert_called_with({"op": 11}, True)

    async def test_handle_ack(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw.last_heartbeat_sent = 0
        await gw._handle_ack()
        assert not math.isnan(gw.heartbeat_latency) and not math.isinf(gw.heartbeat_latency)

    async def test_receive_any_str_hello_when_is_hello(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._receive_json = asynctest.CoroutineMock(
            return_value={"op": 10, "d": {"heartbeat_interval": 12345, "_trace": ["foo"]}}
        )
        await gw._receive_hello()

        assert gw.trace == ["foo"]
        assert gw.heartbeat_interval == 12.345

    async def test_receive_any_str_hello_when_is_not_hello_causes_resume(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._receive_json = asynctest.CoroutineMock(
            return_value={"op": 9, "d": {"heartbeat_interval": 12345, "_trace": ["foo"]}}
        )

        gw._trigger_resume = asynctest.CoroutineMock()
        await gw._receive_hello()
        gw._trigger_resume.assert_awaited()

    async def test_send_resume(self, event_loop):
        gw = MockGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw.session_id = 1234321
        gw.seq = 69_420
        gw._send_json = asynctest.CoroutineMock()
        await gw._send_resume()
        gw._send_json.assert_called_with({"op": 6, "d": {"token": "1234", "session_id": 1234321, "seq": 69_420}}, False)

    async def test_send_identify(self, event_loop):
        with contextlib.ExitStack() as stack:
            stack.enter_context(_helpers.mock_patch(user_agent.python_version, new=lambda: "python3"))
            stack.enter_context(_helpers.mock_patch(user_agent.library_version, new=lambda: "vx.y.z"))
            stack.enter_context(_helpers.mock_patch(platform.system, new=lambda: "leenuks"))

            gw = MockGateway(
                uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None, large_threshold=69
            )
            gw.session_id = 1234321
            gw.seq = 69_420
            gw._send_json = asynctest.CoroutineMock()

            await gw._send_identify()
            gw._send_json.assert_called_with(
                {
                    "op": 2,
                    "d": {
                        "token": "1234",
                        "compress": False,
                        "large_threshold": 69,
                        "properties": {"$os": "leenuks", "$browser": "vx.y.z", "$device": "python3"},
                    },
                },
                False,
            )

    async def test_send_identify_includes_sharding_info_if_present(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._send_json = asynctest.CoroutineMock()

        await gw._send_identify()
        payload = gw._send_json.call_args[0][0]

        assert "d" in payload
        assert "shard" in payload["d"]
        assert payload["d"]["shard"] == [917, 1234]

    async def test_send_identify_includes_status_info_if_present(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
            initial_presence={"foo": "bar"},
        )
        gw._send_json = asynctest.CoroutineMock()

        await gw._send_identify()
        payload = gw._send_json.call_args[0][0]

        assert "d" in payload
        assert "status" in payload["d"]
        assert payload["d"]["status"] == {"foo": "bar"}

    async def test_process_events_halts_if_closed_event_is_set(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._process_one_event = asynctest.CoroutineMock()
        gw._closed_event.set()
        await gw._process_events()
        gw._process_one_event.assert_not_awaited()

    async def test_process_one_event_updates_seq_if_provided_from_payload(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._receive_json = asynctest.CoroutineMock(return_value={"op": 0, "d": {}, "s": 69})
        await gw._process_one_event()
        assert gw.seq == 69

    async def test_process_events_does_not_update_seq_if_not_provided_from_payload(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        gw.seq = 123
        gw._receive_json = asynctest.CoroutineMock(return_value={"op": 0, "d": {}})
        await gw._process_one_event()
        assert gw.seq == 123

    async def test_process_events_on_dispatch_opcode(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        async def flag_death_on_call():
            gw._closed_event.set()
            return {"op": 0, "d": {}, "t": "explosion"}

        gw._receive_json = flag_death_on_call

        gw._dispatch = asynctest.MagicMock()
        await gw._process_one_event()
        gw._dispatch.assert_called_with("explosion", {})

    async def test_process_events_on_heartbeat_opcode(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        async def flag_death_on_call():
            gw._closed_event.set()
            return {"op": 1, "d": {}}

        gw._receive_json = flag_death_on_call

        gw._send_ack = asynctest.CoroutineMock()
        await gw._process_one_event()
        gw._send_ack.assert_any_await()

    async def test_process_events_on_heartbeat_ack_opcode(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        async def flag_death_on_call():
            gw._closed_event.set()
            return {"op": 11, "d": {}}

        gw._receive_json = flag_death_on_call

        gw._handle_ack = asynctest.CoroutineMock()
        await gw._process_one_event()
        gw._handle_ack.assert_any_await()

    async def test_process_events_on_reconnect_opcode(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        async def flag_death_on_call():
            gw._closed_event.set()
            return {"op": 7, "d": {}}

        gw._receive_json = flag_death_on_call

        with contextlib.suppress(gateway._RestartConnection):
            await gw._process_one_event()
            assert False, "No error raised"

    async def test_process_events_on_resumable_invalid_session_opcode(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        async def flag_death_on_call():
            gw._closed_event.set()
            return {"op": 9, "d": True}

        gw._receive_json = flag_death_on_call

        with contextlib.suppress(gateway._ResumeConnection):
            await gw._process_one_event()
            assert False, "No error raised"

    async def test_process_events_on_non_resumable_invalid_session_opcode(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        async def flag_death_on_call():
            gw._closed_event.set()
            return {"op": 9, "d": False}

        gw._receive_json = flag_death_on_call

        with contextlib.suppress(gateway._RestartConnection):
            await gw._process_one_event()
            assert False, "No error raised"

    async def test_process_events_on_unrecognised_opcode_passes_silently(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        async def flag_death_on_call():
            gw._closed_event.set()
            return {"op": -1, "d": False}

        gw._receive_json = flag_death_on_call
        await gw._process_one_event()

    async def test_request_guild_members(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._send_json = asynctest.CoroutineMock()
        await gw.request_guild_members("1234")
        gw._send_json.assert_called_with({"op": 8, "d": {"guild_id": "1234", "query": "", "limit": 0}}, False)

    async def test_update_status(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._send_json = asynctest.CoroutineMock()
        await gw.update_status(1234, {"name": "boom"}, "dead", True)
        gw._send_json.assert_called_with(
            {"op": 3, "d": {"idle": 1234, "game": {"name": "boom"}, "status": "dead", "afk": True}}, False
        )

    async def test_update_voice_state(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._send_json = asynctest.CoroutineMock()
        await gw.update_voice_state("1234", 5678, False, True)
        gw._send_json.assert_called_with(
            {"op": 4, "d": {"guild_id": "1234", "channel_id": "5678", "self_mute": False, "self_deaf": True}}, False
        )

    async def test_no_blocking_close(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw.ws.wait_closed = asynctest.CoroutineMock()
        await gw.close(False)
        assert gw._closed_event.is_set()
        gw.ws.wait_closed.assert_not_awaited()

    async def test_blocking_close(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw.ws.wait_closed = asynctest.CoroutineMock()
        await gw.close(True)
        assert gw._closed_event.is_set()
        gw.ws.wait_closed.assert_awaited()

    async def test_shut_down_run_does_not_loop(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._receive_json = asynctest.CoroutineMock()
        gw._closed_event.set()
        await gw.run()

    async def test_invalid_session_when_cannot_resume_does_not_resume(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._trigger_resume = asynctest.CoroutineMock(wraps=gw._trigger_resume)
        gw._trigger_identify = asynctest.CoroutineMock(wraps=gw._trigger_identify)
        pl = {"op": opcodes.GatewayOpcode.INVALID_SESSION.value, "d": False}
        gw._receive_json = asynctest.CoroutineMock(return_value=pl)

        with contextlib.suppress(gateway._RestartConnection):
            await gw._process_one_event()
            assert False, "No exception raised"

        gw._trigger_identify.assert_awaited_once()
        gw._trigger_resume.assert_not_awaited()

    async def test_invalid_session_when_can_resume_does_resume(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._trigger_resume = asynctest.CoroutineMock(wraps=gw._trigger_resume)
        gw._trigger_identify = asynctest.CoroutineMock(wraps=gw._trigger_identify)
        pl = {"op": opcodes.GatewayOpcode.INVALID_SESSION.value, "d": True}
        gw._receive_json = asynctest.CoroutineMock(return_value=pl)

        with contextlib.suppress(gateway._ResumeConnection):
            await gw._process_one_event()
            assert False, "No exception raised"

        gw._trigger_resume.assert_awaited_once()
        gw._trigger_identify.assert_not_awaited()

    async def test_dispatch_ready(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        #  *sweats furiously*
        pl = {
            "op": 0,
            "t": "READY",
            "d": {
                # https://discordapp.com/developers/docs/topics/gateway#ready-ready-event-fields
                "v": 69,
                "_trace": ["potato.com", "tomato.net"],
                "shard": [9, 18],
                "session_id": "69420lmaolmao",
                "guilds": [{"id": "9182736455463", "unavailable": True}, {"id": "72819099110270", "unavailable": True}],
                "private_channels": [],  # always empty /shrug
                "user": {
                    "id": "81624",
                    "username": "Ben_Dover",
                    "discriminator": 9921,
                    "avatar": "a_d41d8cd98f00b204e9800998ecf8427e",
                    "bot": bool("of course i am"),
                    "mfa_enabled": True,
                    "locale": "en_gb",
                    "verified": False,
                    "email": "chestylaroo@boing.biz",
                    "flags": 69,
                    "premimum_type": 0,
                },
            },
        }
        gw._receive_json = asynctest.CoroutineMock(return_value=pl)
        gw._handle_ready = asynctest.CoroutineMock()
        await gw._process_one_event()
        gw._handle_ready.assert_awaited_once_with(pl["d"])

    async def test_dispatch_resume(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        pl = {"op": 0, "t": "RESUMED", "d": {"_trace": ["potato.com", "tomato.net"]}}

        gw._receive_json = asynctest.CoroutineMock(return_value=pl)
        gw._handle_resumed = asynctest.CoroutineMock()
        await gw._process_one_event()
        gw._handle_resumed.assert_awaited_once_with(pl["d"])

    async def test_handle_ready(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        #  *sweats furiously*
        pl = {
            "op": 0,
            "t": "READY",
            "d": {
                # https://discordapp.com/developers/docs/topics/gateway#ready-ready-event-fields
                "v": 69,
                "_trace": ["potato.com", "tomato.net"],
                "shard": [9, 18],
                "session_id": "69420lmaolmao",
                "guilds": [{"id": "9182736455463", "unavailable": True}, {"id": "72819099110270", "unavailable": True}],
                "private_channels": [],  # always empty /shrug
                "user": {
                    "id": "81624",
                    "username": "Ben_Dover",
                    "discriminator": 9921,
                    "avatar": "a_d41d8cd98f00b204e9800998ecf8427e",
                    "bot": bool("of course i am"),
                    "mfa_enabled": True,
                    "locale": "en_gb",
                    "verified": False,
                    "email": "chestylaroo@boing.biz",
                    "flags": 69,
                    "premimum_type": 0,
                },
            },
        }
        await gw._handle_ready(pl["d"])

    async def test_handle_resume(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        pl = {"op": 0, "t": "RESUMED", "d": {"_trace": ["potato.com", "tomato.net"]}}
        await gw._handle_resumed(pl["d"])

    async def test_process_events_calls_process_one_event(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        async def side_effect(*_, **__):
            gw._closed_event.set()

        gw._process_one_event = asynctest.CoroutineMock(side_effect=side_effect)
        await gw._process_events()
        gw._process_one_event.assert_awaited_once()

    async def test_run_calls_run_once(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        async def side_effect(*_, **__):
            gw._closed_event.set()

        gw.run_once = asynctest.CoroutineMock(side_effect=side_effect)
        await gw.run()
        gw.run_once.assert_awaited_once()

    @mock_run_once_parts()
    async def test_run_once_opens_connection(_, gw):
        # Stop the ws going further than the hello part.
        gw._receive_hello = asynctest.CoroutineMock(side_effect=ws.WebSocketClosure(1000, "idk"))
        gw.uri = "ws://uri"
        await gw.run_once()
        gw.client_session.ws_connect.assert_called_once_with(
            gw.uri, compress=0, proxy=None, proxy_auth=None, proxy_headers=None, ssl_context=None, verify_ssl=True,
        )

    @mock_run_once_parts()
    async def test_run_once_waits_for_hello(_, gw):
        # Stop the WS going further than the hello part.
        gw._receive_hello = asynctest.CoroutineMock(side_effect=ws.WebSocketClosure(1000, "idk"))
        gw.uri = "ws://uri"
        await gw.run_once()
        gw._receive_hello.assert_awaited_once()

    @mock_run_once_parts()
    async def test_run_once_heart_beats_before_keep_alive_but_after_send_identify(_, gw):
        send_identify_time = -float("inf")
        heartbeat_time = -float("inf")
        keep_alive_time = -float("inf")

        async def _send_identify():
            nonlocal send_identify_time
            send_identify_time = time.perf_counter()

        async def _send_heartbeat():
            nonlocal heartbeat_time
            heartbeat_time = time.perf_counter()

        async def _keep_alive():
            nonlocal keep_alive_time
            keep_alive_time = time.perf_counter()

        gw._send_identify = _send_identify
        gw._send_heartbeat = _send_heartbeat
        gw._keep_alive = _keep_alive

        await gw.run_once()

        # Sanity check
        assert -float("inf") == -float("inf")

        assert send_identify_time != -float("inf")
        assert heartbeat_time != -float("inf")
        assert keep_alive_time != -float("inf")
        assert send_identify_time < heartbeat_time < keep_alive_time

    @mock_run_once_parts()
    async def test_run_once_identifies_normally(_, gw):
        await gw.run_once()
        gw._send_identify.assert_awaited_once()
        gw._send_resume.assert_not_awaited()

    @mock_run_once_parts()
    async def test_run_once_resumes_when_seq_and_session_id_set(_, gw):
        gw.seq = 59
        gw.session_id = 1234
        await gw.run_once()
        gw._send_resume.assert_awaited_once()
        gw._send_identify.assert_not_awaited()

    @mock_run_once_parts()
    async def test_run_once_spins_up_heartbeat_keep_alive_task(_, gw):
        await gw.run_once()
        gw._keep_alive.assert_awaited()

    @mock_run_once_parts()
    async def test_run_once_spins_up_event_processing_task(_, gw):
        await gw.run_once()
        gw._process_events.assert_awaited()

    @mock_run_once_parts()
    async def test_run_once_never_reconnect_is_raised_via_RestartConnection(_, gw):
        gw._process_events = asynctest.CoroutineMock(
            side_effect=gateway._RestartConnection(gw._NEVER_RECONNECT_CODES[0], "some lazy message")
        )
        try:
            await gw.run_once()
            assert False, "no runtime error raised"
        except errors.GatewayError as ex:
            assert isinstance(ex.__cause__, gateway._RestartConnection)

    @mock_run_once_parts()
    async def test_run_once_never_reconnect_is_raised_via_ResumeConnection(_, gw):
        gw._process_events = asynctest.CoroutineMock(
            side_effect=gateway._ResumeConnection(gw._NEVER_RECONNECT_CODES[0], "some lazy message")
        )
        try:
            await gw.run_once()
            assert False, "no runtime error raised"
        except errors.GatewayError as ex:
            assert isinstance(ex.__cause__, gateway._ResumeConnection)

    @mock_run_once_parts()
    async def test_run_once_RestartConnection(_, gw):
        gw._process_events = asynctest.CoroutineMock(
            side_effect=gateway._RestartConnection(opcodes.GatewayClosure.INVALID_SEQ, "some lazy message")
        )
        start = 1, 2, ["foo"]
        gw.seq, gw.session_id, gw.trace = start
        # Speed up the test by mocking asyncio.sleep
        await gw.run_once()

        assert gw.seq is None, "seq was not reset"
        assert gw.session_id is None, "session_id was not reset"
        assert gw.trace == [], "trace was not cleared"

    @mock_run_once_parts()
    async def test_run_once_ResumeConnection(_, gw):
        gw._process_events = asynctest.CoroutineMock(
            side_effect=gateway._ResumeConnection(opcodes.GatewayClosure.RATE_LIMITED, "some lazy message")
        )
        start = 1, 2, ["foo"]
        gw._seq, gw._session_id, gw.trace = start
        await gw.run_once()
        assert gw._seq == 1, "seq was reset"
        assert gw._session_id == 2, "session_id was reset"
        assert gw.trace == ["foo"], "trace was cleared"

    async def test_up_time_when_not_running(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        assert gw.up_time.total_seconds() == 0

    async def test_up_time_when_running(self, event_loop):
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        gw.started_at = time.perf_counter() - 15

        assert gw.up_time.total_seconds() > 15

    async def test_dispatch_invokes_dispatcher_as_task(self, event_loop):
        callback_invoked_at = float("nan")

        async def callback(*_, **__):
            nonlocal callback_invoked_at
            callback_invoked_at = time.perf_counter()

        dispatch = asynctest.CoroutineMock(wraps=callback)
        gw = MockGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
            dispatch=dispatch,
        )

        gw._dispatch("explosion", {"brains collected": 55})
        dispatch_task_created_at = time.perf_counter()

        await asyncio.sleep(0.1)

        dispatch.assert_called_once_with(gw, "explosion", {"brains collected": 55})

        # This implies the task wasn't directly awaited immediately
        assert dispatch_task_created_at < callback_invoked_at
