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
import dataclasses
import json
import math
import time
import typing
import urllib.parse as urlparse
import zlib

import aiohttp
import asyncmock as mock
import pytest

from hikari import errors
from hikari.internal_utilities import containers
from hikari.net import gateway
from hikari.net import opcodes
from hikari.net import rates
from tests.hikari import _helpers


def teardown_function():
    _helpers.purge_loop()


@dataclasses.dataclass
class StubMessage:
    data: typing.AnyStr
    type: aiohttp.WSMsgType = aiohttp.WSMsgType.TEXT


class StubClientWebSocketResponse(aiohttp.ClientWebSocketResponse):
    def __init__(self):
        self.close = mock.AsyncMock(wraps=lambda: setattr(self, "_closed", True))
        self.receive = mock.AsyncMock(return_value=StubMessage("{}"))
        self.send_str = mock.AsyncMock()
        self._closed = False

    def __init_subclass__(cls, **kwargs):
        # suppresses warnings
        pass


def stub_client_web_socket_response():
    ws_conn = mock.MagicMock(spec_set=aiohttp.ClientWebSocketResponse)
    ws_conn.close = mock.AsyncMock()
    ws_conn.closed = False
    ws_conn.receive = mock.AsyncMock(return_value=StubMessage("{}"))
    ws_conn.send_str = mock.AsyncMock()
    return ws_conn


def stub_client_session(ws_conn):
    session = mock.MagicMock(spec_set=aiohttp.ClientSession)
    session.close = mock.AsyncMock()
    session.closed = False
    session.ws_connect = mock.AsyncMock(return_value=ws_conn)
    return session


class StubLowLevelGateway(gateway.GatewayClient):
    def __init__(self, **kwargs):
        # noinspection PyShadowingNames
        gateway.GatewayClient.__init__(self, **kwargs)
        self.ws = stub_client_web_socket_response()
        self._mock_session = stub_client_session(self.ws)
        self._client_session_factory = lambda: self._mock_session


@pytest.fixture
def low_level_gateway_mock(event_loop):
    return StubLowLevelGateway(token="foobar", uri="wss://localhost:4949", loop=event_loop)


# noinspection PyProtectedMember
@pytest.mark.asyncio
@pytest.mark.gateway
@pytest.mark.slow
@pytest.mark.trylast
class TestGateway:
    async def test_init_produces_valid_url(self, event_loop):
        """GatewayConnection.__init__ should produce a valid query fragment for the URL."""
        # noinspection PyTypeChecker
        gw = gateway.GatewayClient(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234")
        bits: urlparse.ParseResult = urlparse.urlparse(gw.url)

        assert bits.scheme == "wss"
        assert bits.hostname == "gateway.discord.gg"
        assert bits.port == 4949
        assert bits.query == "v=7&encoding=json&compression=zlib-stream"
        assert not bits.fragment

    async def test_do_resume_triggers_correct_signals(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234")

        try:
            await gw._trigger_resume(69, "boom")
            assert False, "No exception raised"
        except gateway._ResumeConnection:
            gw.ws.close.assert_called_once_with(code=69)

    async def test_do_reidentify_triggers_correct_signals(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234")

        try:
            await gw._trigger_identify(69, "boom")
            assert False, "No exception raised"
        except gateway._RestartConnection:
            gw.ws.close.assert_called_once_with(code=69)

    async def test_send_json_calls_websocket(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._logger = mock.MagicMock()

        # pretend to sleep only
        async def fake_sleep(*_):
            pass

        with _helpers.mock_patch(asyncio.sleep, new=fake_sleep):
            await gw._send_json({}, False)

        gw.ws.send_str.assert_called_once_with("{}")

    async def test_ratelimiting_on_send(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._warn_about_internal_rate_limit = mock.MagicMock(wraps=gw._warn_about_internal_rate_limit)

        gw.rate_limit = rates.TimedTokenBucket(10, 0.1, event_loop)
        gw.rate_limit.reset_at = time.perf_counter() + gw.rate_limit._per

        for i in range(20):
            await gw._send_json({}, False)

        gw._warn_about_internal_rate_limit.assert_called()

    async def test_ratelimiting_on_send_can_be_overridden(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._warn_about_internal_rate_limit = mock.MagicMock(wraps=gw._warn_about_internal_rate_limit)
        gw.rate_limit._per = 0.1
        gw.rate_limit.reset_at = time.perf_counter() + gw.rate_limit._per

        for i in range(20):
            await gw._send_json({}, True)

        gw._warn_about_internal_rate_limit.assert_not_called()

    async def test_send_json_wont_send_massive_payloads(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._handle_payload_oversize = mock.MagicMock(wraps=gw._handle_payload_oversize)
        pl = {"d": {"lolololilolo": "lol" * 4096}, "op": "1", "blah": 2}
        await gw._send_json(pl, False)
        gw._handle_payload_oversize.assert_called_once_with(pl)

    async def test_receive_json_calls__receive_at_least_once(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._receive = mock.AsyncMock(return_value="{}")
        await gw._receive_json()
        gw._receive.assert_any_call()

    async def test_receive_json_closes_connection_if_payload_was_not_a_dict(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._trigger_identify = mock.AsyncMock()
        gw._receive = mock.AsyncMock(return_value="[]")
        await gw._receive_json()
        gw._trigger_identify.assert_called_once_with(
            code=opcodes.GatewayClosure.TYPE_ERROR, reason="Expected JSON object."
        )

    async def test_receive_json_when_receiving_string_decodes_immediately(self, event_loop):
        with mock.patch("json.loads", new=mock.MagicMock(return_value={})) as json_loads:
            gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
            receive_call_result = '{"foo":"bar","baz":"bork","qux":["q", "u", "x", "x"]}'
            gw._receive = mock.AsyncMock(return_value=receive_call_result)
            await gw._receive_json()
            json_loads.assert_called_with(receive_call_result, object_hook=containers.ObjectProxy)

    async def test_receive_json_when_receiving_zlib_payloads_collects_before_decoding(self, event_loop):
        with mock.patch("json.loads", new=mock.MagicMock(return_value={})) as json_loads:
            gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
            receive_call_result = '{"foo": "bar","baz": "bork","qux": ["q", "u", "x", "x"]}'.encode("utf-8")

            payload = zlib.compress(receive_call_result) + b"\x00\x00\xff\xff"

            chunk_size = 16
            chunk_slices = (slice(i, i + chunk_size) for i in range(0, len(payload), chunk_size))
            chunks = [payload[chunk_slice] for chunk_slice in chunk_slices]

            gw._receive = mock.AsyncMock(side_effect=chunks)
            await gw._receive_json()
            # noinspection PyUnresolvedReferences
            json_loads.assert_called_with(receive_call_result.decode("utf-8"), object_hook=containers.ObjectProxy)

    async def test_small_zlib_payloads_leave_buffer_alone(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)

        with _helpers.mock_patch(json.loads, new=mock.MagicMock(return_value={})):
            receive_call_result = '{"foo": "bar","baz": "bork","qux": ["q", "u", "x", "x"]}'.encode("utf-8")

            payload = zlib.compress(receive_call_result) + b"\x00\x00\xff\xff"

            chunk_size = 16
            chunk_slices = (slice(i, i + chunk_size) for i in range(0, len(payload), chunk_size))
            chunks = [payload[chunk_slice] for chunk_slice in chunk_slices]

            first_array = gw._in_buffer
            gw._receive = mock.AsyncMock(side_effect=chunks)
            await gw._receive_json()
            assert gw._in_buffer is first_array

    async def test_massive_zlib_payloads_cause_buffer_replacement(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)

        with _helpers.mock_patch(json.loads, new=mock.MagicMock(return_value={})):
            receive_call_result = '{"foo": "bar","baz": "bork","qux": ["q", "u", "x", "x"]}'.encode("utf-8")

            payload = zlib.compress(receive_call_result) + b"\x00\x00\xff\xff"

            chunk_size = 16
            chunk_slices = (slice(i, i + chunk_size) for i in range(0, len(payload), chunk_size))
            chunks = [payload[chunk_slice] for chunk_slice in chunk_slices]

            gw._in_buffer = bytearray()
            first_array = gw._in_buffer
            gw.max_persistent_buffer_size = 3
            gw._receive = mock.AsyncMock(side_effect=chunks)
            await gw._receive_json()
            assert gw._in_buffer is not first_array

    async def test_heartbeat_beats_at_interval(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw.heartbeat_interval = 0.01

        task = asyncio.create_task(gw._keep_alive())
        try:
            await asyncio.sleep(0.1)
        finally:
            task.cancel()
            gw.ws.send_str.assert_called_with('{"op": 1, "d": null}')

    async def test_heartbeat_shuts_down_when_closure_request(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw.heartbeat_interval = 10

        task = asyncio.create_task(gw._keep_alive())
        try:
            await asyncio.sleep(0.1)
        finally:
            await gw.close()
            await task

    async def test_heartbeat_if_not_acknowledged_in_time_closes_connection_with_resume(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw.last_heartbeat_sent = -float("inf")
        gw.heartbeat_interval = 0

        task = asyncio.create_task(gw._keep_alive())

        await asyncio.sleep(0.1)

        task.cancel()
        gw.ws.close.assert_called_once()

    async def test_slow_loop_produces_warning(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw.heartbeat_interval = 0
        # will always make the latency appear slow.
        gw.heartbeat_latency = 0
        gw._handle_slow_client = mock.MagicMock(wraps=gw._handle_slow_client)
        task = asyncio.create_task(gw._keep_alive())

        await asyncio.sleep(0.1)

        task.cancel()
        gw._handle_slow_client.assert_called_once()

    async def test_send_heartbeat(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._send_json = mock.AsyncMock()
        await gw._send_heartbeat()
        gw._send_json.assert_called_with({"op": 1, "d": None}, True)

    async def test_send_ack(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._send_json = mock.AsyncMock()
        await gw._send_ack()
        gw._send_json.assert_called_with({"op": 11}, True)

    async def test_handle_ack(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw.last_heartbeat_sent = 0
        await gw._handle_ack()
        assert not math.isnan(gw.heartbeat_latency) and not math.isinf(gw.heartbeat_latency)

    async def test__receive_hello_when_is_hello(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._receive_json = mock.AsyncMock(
            return_value={"op": 10, "d": {"heartbeat_interval": 12345, "_trace": ["foo"]}}
        )
        await gw._receive_hello()

        assert gw.trace == ["foo"]
        assert gw.heartbeat_interval == 12.345

    async def test_receive_hello_dispatches_connect(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        payload = {"op": 10, "d": {"heartbeat_interval": 12345, "_trace": ["foo"]}}
        gw._receive_json = mock.AsyncMock(return_value=payload)
        gw._dispatch_new_event = mock.MagicMock(spec_set=gw._dispatch_new_event)

        await gw._receive_hello()

        gw._dispatch_new_event.assert_any_call(opcodes.GatewayInternalEvent.CONNECT, None, is_internal_event=True)
        gw._dispatch_new_event.assert_any_call(opcodes.GatewayEvent.HELLO, payload["d"], is_internal_event=False)

    async def test__receive_hello_when_is_not_hello_causes_resume(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw._receive_json = mock.AsyncMock(return_value={"op": 9, "d": {"heartbeat_interval": 12345, "_trace": ["foo"]}})

        gw._trigger_resume = mock.AsyncMock()
        await gw._receive_hello()
        gw._trigger_resume.assert_called()

    async def test_send_resume(self, event_loop):
        gw = StubLowLevelGateway(uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", shard_id=None)
        gw.session_id = 1_234_321
        gw.seq = 69420
        gw._send_json = mock.AsyncMock()
        await gw._send_resume()
        gw._send_json.assert_called_with(
            {"op": 6, "d": {"token": "1234", "session_id": 1_234_321, "seq": 69420}}, False
        )

    @pytest.mark.parametrize("guild_subscriptions", [True, False])
    async def test_send_identify(self, event_loop, guild_subscriptions):
        with contextlib.ExitStack() as stack:
            stack.enter_context(
                mock.patch("hikari.net.user_agent.python_version", new=lambda: "python3")
            )
            stack.enter_context(
                mock.patch("hikari.net.user_agent.library_version", new=lambda: "vx.y.z")
            )
            stack.enter_context(mock.patch("hikari.net.user_agent.system_type", new=lambda: "leenuks"))

            gw = StubLowLevelGateway(
                uri="wss://gateway.discord.gg:4949/",
                loop=event_loop,
                token="1234",
                shard_id=None,
                large_threshold=69,
                intents=opcodes.GatewayIntent.GUILD_BANS | opcodes.GatewayIntent.GUILDS,
            )
            gw.session_id = 1_234_321
            gw.seq = 69420
            gw._send_json = mock.AsyncMock()
            gw._enable_guild_subscription_events = guild_subscriptions

            await gw._send_identify()
            gw._send_json.assert_called_with(
                {
                    "op": opcodes.GatewayOpcode.IDENTIFY,
                    "d": {
                        "token": "1234",
                        "compress": False,
                        "large_threshold": 69,
                        "properties": {"$os": "leenuks", "$browser": "vx.y.z", "$device": "python3"},
                        "guild_subscriptions": guild_subscriptions,
                        # Disabled until intents get implemented: specifying these currently on the actual
                        # gateway will trigger a 4012 shutdown, which is undocumented
                        # behaviour according to the closure codes list at the time of writing
                        # see https://github.com/discordapp/discord-api-docs/issues/1266
                        # "intents": 0x5,
                    },
                },
                False,
            )

    async def test_send_identify_includes_sharding_info_if_present(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._send_json = mock.AsyncMock()

        await gw._send_identify()
        payload = gw._send_json.call_args[0][0]

        assert "d" in payload
        assert "shard" in payload["d"]
        assert payload["d"]["shard"] == [917, 1234]

    @pytest.mark.parametrize("is_present", [True, False])
    async def test_send_identify_includes_presence_info_if_present(self, event_loop, is_present):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
            initial_presence={"foo": "bar"} if is_present else None,
        )
        gw._send_json = mock.AsyncMock()

        await gw._send_identify()
        payload = gw._send_json.call_args[0][0]

        assert "d" in payload
        if is_present:
            assert "presence" in payload["d"]
            assert payload["d"]["presence"] == {"foo": "bar"}
        else:
            assert "presence" not in payload["d"]

    async def test_process_events_halts_if_closed_event_is_set(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._process_one_event = mock.AsyncMock()
        gw._closed_event.set()
        await gw._process_events()
        gw._process_one_event.assert_not_called()

    async def test_process_one_event_updates_seq_if_provided_from_payload(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._receive_json = mock.AsyncMock(return_value={"op": 0, "t": "SOMETHING", "d": {}, "s": 69})
        await gw._process_one_event()
        assert gw.seq == 69

    async def test_process_events_does_not_update_seq_if_not_provided_from_payload(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        gw.seq = 123
        gw._receive_json = mock.AsyncMock(return_value={"op": 0, "t": "SOMETHING", "d": {}})
        await gw._process_one_event()
        assert gw.seq == 123

    async def test_process_events_on_dispatch_opcode(self, event_loop):
        gw = StubLowLevelGateway(
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

        gw._dispatch_new_event = mock.MagicMock()
        await gw._process_one_event()
        gw._dispatch_new_event.assert_called_with("explosion", {}, False)

    async def test_process_events_on_heartbeat_opcode(self, event_loop):
        gw = StubLowLevelGateway(
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

        gw._send_ack = mock.AsyncMock()
        await gw._process_one_event()
        gw._send_ack.assert_any_call()

    async def test_process_events_on_heartbeat_ack_opcode(self, event_loop):
        gw = StubLowLevelGateway(
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

        gw._handle_ack = mock.AsyncMock()
        await gw._process_one_event()
        gw._handle_ack.assert_any_call()

    async def test_process_events_on_reconnect_opcode(self, event_loop):
        gw = StubLowLevelGateway(
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
        gw = StubLowLevelGateway(
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
        gw = StubLowLevelGateway(
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
        gw = StubLowLevelGateway(
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

    @pytest.mark.parametrize("guild_ids", [["123"], ["1234", "5678"], ["1234", "5678", "9101112"]])
    @pytest.mark.parametrize(
        "user_ids", [[], ["9"], ["9", "17", "25"], ["9", "17", "25", "9", "9"], ("9", "17", "25", "9", "9")]
    )
    async def test_request_guild_members_with_user_ids(self, event_loop, user_ids, guild_ids):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        # Mock coroutines so we don't have to fight with testing `create_task` being called properly with
        # a coroutine, and so that we don't have to ensure a coro gets called in the implementation
        coro = mock.MagicMock()
        gw._send_json = mock.MagicMock(return_value=coro)
        with mock.patch("hikari.internal_utilities.compat.asyncio.create_task") as create_task:
            gw.request_guild_members(*guild_ids, limit=69, user_ids=user_ids, presences=True)
            gw._send_json.assert_called_with(
                # No query param, so no limit passed.
                {"op": 8, "d": {"guild_id": guild_ids, "user_ids": list(user_ids), "presences": True}},
                False,
            )
            create_task.assert_called_with(
                coro, name=f"send REQUEST_GUILD_MEMBERS (shard 917/1234)",
            )

    @pytest.mark.parametrize("guild_ids", [["123"], ["1234", "5678"], ["1234", "5678", "9101112"]])
    @pytest.mark.parametrize("query", ["", " ", "   ", "\0", "ayy lmao"])
    async def test_request_guild_members_with_query(self, event_loop, query, guild_ids):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        # Mock coroutines so we don't have to fight with testing `create_task` being called properly with
        # a coroutine, and so that we don't have to ensure a coro gets called in the implementation
        coro = mock.MagicMock()
        gw._send_json = mock.MagicMock(return_value=coro)
        with mock.patch("hikari.internal_utilities.compat.asyncio.create_task") as create_task:
            gw.request_guild_members(*guild_ids, limit=69, query=query, presences=True)
            gw._send_json.assert_called_with(
                {"op": 8, "d": {"guild_id": guild_ids, "query": query, "limit": 69, "presences": True}}, False
            )
            create_task.assert_called_with(
                coro, name=f"send REQUEST_GUILD_MEMBERS (shard 917/1234)",
            )

    @pytest.mark.parametrize("guild_ids", [["123"], ["1234", "5678"]])
    @pytest.mark.parametrize("user_ids", [[], ["9"], ["9", "17", "25"], ("9", "17", "25", "9", "9")])
    @pytest.mark.parametrize("query", ["", " ", "that_guy123"])
    async def test_request_guild_members_with_query_and_user_ids_should_error(
        self, event_loop, query, user_ids, guild_ids
    ):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        # Who cares.
        gw._send_json = mock.AsyncMock()
        try:
            # noinspection PyArgumentList
            await gw.request_guild_members(*guild_ids, limit=69, query=query, presences=True, user_ids=user_ids)
            assert False, "No error"
        except RuntimeError:
            pass  # we expect this to error to pass this test.

    @pytest.mark.parametrize("guild_ids", [["123"], ["1234", "5678"]])
    async def test_request_guild_members_with_no_filter(self, event_loop, guild_ids):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        # Mock coroutines so we don't have to fight with testing `create_task` being called properly with
        # a coroutine, and so that we don't have to ensure a coro gets called in the implementation
        coro = mock.MagicMock()
        gw._send_json = mock.MagicMock(return_value=coro)
        with mock.patch("hikari.internal_utilities.compat.asyncio.create_task") as create_task:
            gw.request_guild_members(*guild_ids, limit=69, user_ids=None, query=None, presences=True)
            gw._send_json.assert_called_with(
                # We don't pass a query, but no user_ids is passed, so we expect query and thus limit to be sent.
                # If we didn't sent query and limit in this case, we'd have the session revoked as being invalid.
                {"op": 8, "d": {"guild_id": guild_ids, "presences": True, "query": "", "limit": 69}},
                False,
            )
            create_task.assert_called_with(
                coro, name=f"send REQUEST_GUILD_MEMBERS (shard 917/1234)",
            )

    async def test_update_status(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._send_json = mock.AsyncMock()
        await gw.update_status(1234, {"name": "boom"}, "dead", True)
        gw._send_json.assert_called_with(
            {"op": 3, "d": {"idle": 1234, "game": {"name": "boom"}, "status": "dead", "afk": True}}, False
        )

    async def test_update_voice_state(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._send_json = mock.AsyncMock()
        await gw.update_voice_state("1234", 5678, False, True)
        gw._send_json.assert_called_with(
            {"op": 4, "d": {"guild_id": "1234", "channel_id": "5678", "self_mute": False, "self_deaf": True}}, False
        )

    async def test__close_when_running(self, low_level_gateway_mock):
        low_level_gateway_mock.ws.closed = False
        await low_level_gateway_mock.close()
        assert low_level_gateway_mock._closed_event.is_set()
        low_level_gateway_mock.ws.close.assert_called_once()

    async def test__close_when_closed(self, low_level_gateway_mock):
        low_level_gateway_mock.ws.closed = True
        await low_level_gateway_mock.close()
        low_level_gateway_mock.ws.close.assert_not_called()

    async def test_shut_down_run_does_not_loop(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._receive_json = mock.AsyncMock()
        gw._closed_event.set()
        await gw.run()

    async def test_invalid_session_when_cannot_resume_does_not_resume(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._trigger_resume = mock.MagicMock(wraps=gw._trigger_resume)
        gw._trigger_identify = mock.MagicMock(wraps=gw._trigger_identify)
        pl = {"op": opcodes.GatewayOpcode.INVALID_SESSION.value, "d": False}
        gw._receive_json = mock.AsyncMock(return_value=pl)

        with contextlib.suppress(gateway._RestartConnection):
            await gw._process_one_event()
            assert False, "No exception raised"

        gw._trigger_identify.assert_called_once_with(
            code=opcodes.GatewayClosure.NORMAL_CLOSURE, reason="invalid session id so will close"
        )
        gw._trigger_resume.assert_not_called()

    async def test_invalid_session_when_can_resume_does_resume(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        gw._trigger_resume = mock.MagicMock(wraps=gw._trigger_resume)
        gw._trigger_identify = mock.MagicMock(wraps=gw._trigger_identify)
        pl = {"op": opcodes.GatewayOpcode.INVALID_SESSION.value, "d": True}
        gw._receive_json = mock.AsyncMock(return_value=pl)

        with contextlib.suppress(gateway._ResumeConnection):
            await gw._process_one_event()
            assert False, "No exception raised"

        gw._trigger_resume.assert_called_once_with(
            code=opcodes.GatewayClosure.NORMAL_CLOSURE, reason="invalid session id so will resume"
        )
        gw._trigger_identify.assert_not_called()

    async def test_dispatch_ready(self, event_loop):
        gw = StubLowLevelGateway(
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
                # always empty:
                # https://discordapp.com/developers/docs/change-log#documentation-fix-list-of-open-dms-in-certain-payloads
                "private_channels": [],
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
        gw._receive_json = mock.AsyncMock(return_value=pl)
        gw._handle_ready = mock.AsyncMock()
        await gw._process_one_event()
        gw._handle_ready.assert_called_once_with(pl["d"])

    async def test_dispatch_resume(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )
        pl = {"op": 0, "t": "RESUMED", "d": {"_trace": ["potato.com", "tomato.net"]}}

        gw._receive_json = mock.AsyncMock(return_value=pl)
        gw._handle_resumed = mock.AsyncMock()
        await gw._process_one_event()
        gw._handle_resumed.assert_called_once_with(pl["d"])

    async def test_handle_ready_for_sharded_gateway_sets_shard_info(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", large_threshold=69
        )
        gw.shard_id = None
        gw.shard_count = None

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

        assert gw.trace == pl["d"]["_trace"]
        assert gw.shard_id == pl["d"]["shard"][0]
        assert gw.shard_count == pl["d"]["shard"][1]

    async def test_handle_ready_for_unsharded_gateway_does_not_set_shard_info(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", large_threshold=69
        )
        gw.shard_id = None
        gw.shard_count = None

        #  *sweats furiously again*
        pl = {
            "op": 0,
            "t": "READY",
            "d": {
                # https://discordapp.com/developers/docs/topics/gateway#ready-ready-event-fields
                "v": 69,
                "_trace": ["potato.com", "tomato.net"],
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

        assert gw.trace == pl["d"]["_trace"]
        assert gw.shard_id is None
        assert gw.shard_count is None

    async def test_handle_ready_dispatches_READY_event(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", large_threshold=69
        )
        gw._dispatch_new_event = mock.MagicMock(spec_set=gw._dispatch_new_event)
        gw.shard_id = None
        gw.shard_count = None

        #  *sweats furiously again*
        pl = {
            "op": 0,
            "t": "READY",
            "d": {
                # https://discordapp.com/developers/docs/topics/gateway#ready-ready-event-fields
                "v": 69,
                "_trace": ["potato.com", "tomato.net"],
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

        gw._dispatch_new_event.assert_called_with("READY", pl["d"], is_internal_event=False)

    async def test_handle_resumed_dispatches_RESUMED(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/", loop=event_loop, token="1234", large_threshold=69,
        )
        gw._dispatch_new_event = mock.MagicMock(spec_set=gw._dispatch_new_event)
        gw.shard_id = 9
        gw.shard_count = 18
        pl = {
            "op": 0,
            "t": "RESUMED",
            "d": {"_trace": ["potato.com", "tomato.net"], "seq": 192, "session_id": "168ayylmao"},
        }

        await gw._handle_resumed(pl["d"])
        gw._dispatch_new_event.assert_called_with("RESUMED", pl["d"], is_internal_event=False)

    async def test_process_events_calls_process_one_event(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        def _process_one_event():
            gw._closed_event.set()

        gw._process_one_event = mock.AsyncMock(wraps=_process_one_event)
        await gw._process_events()
        gw._process_one_event.assert_any_call()

    async def test_run_calls_run_once(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        def side_effect(*_, **__):
            gw._closed_event.set()

        gw.run_once = mock.AsyncMock(wraps=side_effect)
        await gw.run()
        gw.run_once.assert_called_once()

    async def test_run_once_opens_connection(self, low_level_gateway_mock):
        # Stop the ws going further than the hello part.
        low_level_gateway_mock._receive_hello = mock.AsyncMock(side_effect=gateway._WebSocketClosure(1000, "idk"))
        await low_level_gateway_mock.run_once()
        low_level_gateway_mock._mock_session.ws_connect.assert_called_once_with(
            "wss://localhost:4949?v=7&encoding=json&compression=zlib-stream",
            compress=0,
            proxy=None,
            proxy_auth=None,
            proxy_headers=None,
            ssl_context=None,
            verify_ssl=True,
        )

    async def test_run_once_catches_exception(self, low_level_gateway_mock):
        # Mock to prevent 10s sleep during test and to spy
        with mock.patch("asyncio.sleep", new=mock.AsyncMock()) as sleep:
            low_level_gateway_mock._client_session_factory = mock.MagicMock(side_effect=ConnectionRefusedError)
            await low_level_gateway_mock.run_once()
            sleep.assert_called_once()

    async def test__run_once_waits_for_hello(self, stub_for__run_once):
        # Stop the WS going further than the hello part.
        stub_for__run_once._receive_hello = mock.AsyncMock(side_effect=gateway._WebSocketClosure(1000, "idk"))
        stub_for__run_once.uri = "ws://uri"
        await stub_for__run_once._run_once()
        stub_for__run_once._receive_hello.assert_called_once()

    @pytest.fixture
    def stub_for__run_once(self, low_level_gateway_mock):
        return _helpers.mock_methods_on(low_level_gateway_mock, except_=("_run_once",))

    async def test__run_once_heart_beats_before_keep_alive_but_after_send_identify(self, stub_for__run_once):
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

        stub_for__run_once._send_identify = _send_identify
        stub_for__run_once._send_heartbeat = _send_heartbeat
        stub_for__run_once._keep_alive = _keep_alive

        await stub_for__run_once._run_once()

        # Sanity check
        assert -float("inf") == -float("inf")

        assert send_identify_time != -float("inf")
        assert heartbeat_time != -float("inf")
        assert keep_alive_time != -float("inf")
        assert send_identify_time < heartbeat_time < keep_alive_time

    async def test__run_once_identifies_normally(self, stub_for__run_once):
        await stub_for__run_once._run_once()
        stub_for__run_once._send_identify.assert_called_once()
        stub_for__run_once._send_resume.assert_not_called()

    async def test__run_once_resumes_when_seq_and_session_id_set(self, stub_for__run_once):
        stub_for__run_once.seq = 59
        stub_for__run_once.session_id = 1234
        await stub_for__run_once._run_once()
        stub_for__run_once._send_resume.assert_called_once()
        stub_for__run_once._send_identify.assert_not_called()

    async def test__run_once_spins_up_heartbeat_keep_alive_task(self, stub_for__run_once):
        await stub_for__run_once._run_once()
        stub_for__run_once._keep_alive.assert_called()

    async def test__run_once_spins_up_event_processing_task(self, stub_for__run_once):
        await stub_for__run_once._run_once()
        stub_for__run_once._process_events.assert_called()

    async def test__run_once_never_reconnect_is_raised_via_RestartConnection(self, stub_for__run_once):
        stub_for__run_once._process_events = mock.AsyncMock(
            side_effect=gateway._RestartConnection(stub_for__run_once._NEVER_RECONNECT_CODES[0], "some lazy message")
        )
        try:
            await stub_for__run_once._run_once()
            assert False, "no runtime error raised"
        except errors.GatewayError as ex:
            assert isinstance(ex.__cause__, gateway._RestartConnection)

    async def test__run_once_never_reconnect_is_raised_via_ResumeConnection(self, stub_for__run_once):
        stub_for__run_once._process_events = mock.AsyncMock(
            side_effect=gateway._ResumeConnection(stub_for__run_once._NEVER_RECONNECT_CODES[0], "some lazy message")
        )
        try:
            await stub_for__run_once._run_once()
            assert False, "no runtime error raised"
        except errors.GatewayError as ex:
            assert isinstance(ex.__cause__, gateway._ResumeConnection)

    async def test__run_once_RestartConnection(self, stub_for__run_once):
        stub_for__run_once._process_events = mock.AsyncMock(
            side_effect=gateway._RestartConnection(opcodes.GatewayClosure.INVALID_SEQ, "some lazy message")
        )
        start = 1, 2, ["foo"]
        stub_for__run_once.seq, stub_for__run_once.session_id, stub_for__run_once.trace = start
        await stub_for__run_once._run_once()

        assert stub_for__run_once.seq is None, "seq was not reset"
        assert stub_for__run_once.session_id is None, "session_id was not reset"
        assert stub_for__run_once.trace == [], "trace was not cleared"

    async def test__run_once_ResumeConnection(self, stub_for__run_once):
        stub_for__run_once._process_events = mock.AsyncMock(
            side_effect=gateway._ResumeConnection(opcodes.GatewayClosure.RATE_LIMITED, "some lazy message")
        )
        start = 1, 2, ["foo"]
        stub_for__run_once._seq, stub_for__run_once._session_id, stub_for__run_once.trace = start
        await stub_for__run_once._run_once()
        assert stub_for__run_once._seq == 1, "seq was reset"
        assert stub_for__run_once._session_id == 2, "session_id was reset"
        assert stub_for__run_once.trace == ["foo"], "trace was cleared"

    async def test_up_time_when_not_running(self, event_loop):
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
        )

        assert gw.up_time.total_seconds() == 0

    async def test_up_time_when_running(self, event_loop):
        gw = StubLowLevelGateway(
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
        dispatch_gateway_coro = mock.MagicMock()
        dispatch_internal_coro = mock.MagicMock()
        dispatch_gateway_event = mock.MagicMock(return_value=dispatch_gateway_coro)
        dispatch_internal_event = mock.MagicMock(return_value=dispatch_internal_coro)
        gw = StubLowLevelGateway(
            uri="wss://gateway.discord.gg:4949/",
            loop=event_loop,
            token="1234",
            shard_id=917,
            shard_count=1234,
            large_threshold=69,
            gateway_event_dispatcher=dispatch_gateway_event,
            internal_event_dispatcher=dispatch_internal_event,
        )

        with mock.patch("hikari.internal_utilities.compat.asyncio.create_task") as create_task:
            gw._dispatch_new_event("explosion", {"brains collected": 55}, is_internal_event=False)
            create_task.assert_called_once_with(
                dispatch_gateway_coro, name="dispatching explosion event (shard 917/1234)"
            )
        with mock.patch("hikari.internal_utilities.compat.asyncio.create_task") as create_task:
            gw._dispatch_new_event("client_on_fire", {"it burns!": 100}, is_internal_event=True)
            create_task.assert_called_once_with(
                dispatch_internal_coro, name="dispatching client_on_fire event (shard 917/1234)"
            )

    @pytest.mark.parametrize("type_", [aiohttp.WSMsgType.BINARY, aiohttp.WSMsgType.TEXT])
    async def test__receive_when_valid_payload(self, low_level_gateway_mock, type_):
        low_level_gateway_mock.ws.receive = mock.AsyncMock(return_value=StubMessage("hello", type_))
        result = await low_level_gateway_mock._receive()
        assert result == "hello"

    @_helpers.assert_raises(
        type_=gateway._WebSocketClosure,
        checks=[lambda ex: ex.code == 1234, lambda ex: ex.reason == "gateway closed the connection"],
    )
    async def test__receive_when_close(self, low_level_gateway_mock):
        low_level_gateway_mock.ws.receive = mock.AsyncMock(return_value=StubMessage("xxx", aiohttp.WSMsgType.CLOSE))
        low_level_gateway_mock.ws.close_code = 1234
        await low_level_gateway_mock._receive()

    @_helpers.assert_raises(type_=TypeError, checks=[lambda ex: "Expected TEXT or BINARY message" in str(ex)])
    async def test__receive_for_anything_else_raises_TypeError(self, low_level_gateway_mock):
        low_level_gateway_mock.ws.receive = mock.AsyncMock(
            return_value=StubMessage("xxx", aiohttp.WSMsgType.CONTINUATION)
        )
        await low_level_gateway_mock._receive()

    async def test_request_guild_sync(self, low_level_gateway_mock):
        guilds = ["9", "18", "27", "36"]
        send_json_coro = mock.MagicMock()
        low_level_gateway_mock._send_json = mock.MagicMock(return_value=send_json_coro)

        with mock.patch("hikari.internal_utilities.compat.asyncio.create_task") as create_task:
            low_level_gateway_mock.request_guild_sync(*guilds)

            low_level_gateway_mock._send_json.assert_called_once_with(
                {"op": opcodes.GatewayOpcode.GUILD_SYNC, "d": guilds},
                False
            )
            create_task.assert_called_once_with(
                send_json_coro,
                name=f"send GUILD_SYNC (shard {low_level_gateway_mock.shard_id}/{low_level_gateway_mock.shard_count})"
            )