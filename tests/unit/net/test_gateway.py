#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import json
import math
import urllib.parse as urlparse
import zlib

import async_timeout
import asynctest
import pytest

from hikari.net import gateway



class MockGateway(gateway.GatewayConnection):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.ws = asynctest.MagicMock()
        self.ws.close = asynctest.CoroutineMock()
        self.ws.send = asynctest.CoroutineMock()
        self.ws.recv = asynctest.CoroutineMock()
        self.ws.wait_closed = self._wait_closed

    async def _wait_closed(self):
        await asyncio.sleep(0.1)


def teardown_function(event_loop):
    asynctest.helpers.exhaust_callbacks(event_loop)


async def duff_consumer_coro(*_, **__):
    pass


@pytest.mark.asyncio
async def test_init_produces_valid_url(event_loop):
    """GatewayConnection.__init__ should produce a valid query fragment for the URL."""
    gw = gateway.GatewayConnection(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234')
    bits: urlparse.ParseResult = urlparse.urlparse(gw.uri)

    assert bits.scheme == 'wss'
    assert bits.hostname == 'gateway.discord.gg'
    assert bits.port == 4949
    assert bits.query == 'v=7&encoding=json&compression=zlib-stream'
    assert not bits.fragment


@pytest.mark.asyncio
async def test__do_resume_triggers_correct_signals(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234')

    try:
        await gw._do_resume(69, 'boom')
        assert False, 'No exception raised'
    except gateway.ResumeConnection:
        gw.ws.close.assert_awaited_once_with(code=69, reason='boom')


@pytest.mark.asyncio
async def test__do_reidentify_triggers_correct_signals(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234')

    try:
        await gw._do_reidentify(69, 'boom')
        assert False, 'No exception raised'
    except gateway.RestartConnection:
        gw.ws.close.assert_awaited_once_with(code=69, reason='boom')


@pytest.mark.asyncio
async def test__send_json_async_calls__send_json_asynchronously(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234')

    gw._send_json = asynctest.CoroutineMock()
    await gw._send_json_async({})

    gw._send_json.assert_awaited_once_with({})


@pytest.mark.asyncio
async def test__send_json_calls_websocket(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw._logger = asynctest.MagicMock()

    # pretend to sleep only
    with asynctest.patch('asyncio.sleep', new=duff_consumer_coro):
        await gw._send_json({})

    gw.ws.send.assert_awaited_once_with('{}')

    # Ensure we didn't get ratelimited on a single call.
    gw._logger.debug.assert_not_called()


@pytest.mark.asyncio
async def test__send_json_eventually_gets_ratelimited(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw._logger = asynctest.MagicMock()
    gw.RATELIMIT_COOLDOWN = 0.1

    futures = []

    for i in range(130):
        futures.append(gw._send_json({}))

    await asyncio.gather(*futures)

    gw._logger.debug.assert_called_with('Shard %s: now being rate-limited', None)


@pytest.mark.asyncio
async def test__send_json_wont_send_massive_payloads(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw._logger = asynctest.MagicMock()

    payload = {
        'some_item': 'lol' * 4096
    }

    # pretend to sleep only
    with asynctest.patch('asyncio.sleep', new=duff_consumer_coro):
        await gw._send_json(payload)

    gw.ws.send.assert_not_called()
    gw._logger.error.assert_called_with("Shard %s: Failed to send payload as it was too large. Sending this would "
                                        "result in a disconnect. Payload was: %s", None, payload)


@pytest.mark.asyncio
async def test__receive_json_calls_recv_at_least_once(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw.ws.recv = asynctest.CoroutineMock(return_value='{}')
    await gw._receive_json()
    gw.ws.recv.assert_any_call()


@pytest.mark.asyncio
async def test__receive_json_tries_to_reidentify_if_payload_was_not_a_dict(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw._do_reidentify = asynctest.CoroutineMock()
    gw.ws.recv = asynctest.CoroutineMock(return_value='[]')
    await gw._receive_json()
    gw.ws.recv.assert_any_call()
    gw._do_reidentify.assert_awaited_once_with(code=1007, reason="Expected JSON object.")


@pytest.mark.asyncio
async def test__receive_json_when_receiving_string_decodes_immediately(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)

    with asynctest.patch('json.loads', new=asynctest.MagicMock(return_value={})):
        recv_value = ('{'
                      '  "foo": "bar",'
                      '  "baz": "bork",'
                      '  "qux": ["q", "u", "x", "x"]'
                      '}')
        gw.ws.recv = asynctest.CoroutineMock(return_value=recv_value)
        await gw._receive_json()
        json.loads.assert_called_with(recv_value, encoding='utf-8')


@pytest.mark.asyncio
async def test__receive_json_when_receiving_zlib_payloads_collects_before_decoding(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)

    with asynctest.patch('json.loads', new=asynctest.MagicMock(return_value={})):
        recv_value = ('{'
                      '  "foo": "bar",'
                      '  "baz": "bork",'
                      '  "qux": ["q", "u", "x", "x"]'
                      '}').encode("utf-8")

        payload = zlib.compress(recv_value) + b"\x00\x00\xff\xff"

        chunk_size = 16
        chunks = [payload[i: i + chunk_size] for i in range(0, len(payload), chunk_size)]

        gw.ws.recv = asynctest.CoroutineMock(side_effect=chunks)
        await gw._receive_json()
        json.loads.assert_called_with(recv_value.decode('utf-8'), encoding='utf-8')


@pytest.mark.asyncio
async def test_small_zlib_payloads_leave_buffer_alone(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)

    with asynctest.patch('json.loads', new=asynctest.MagicMock(return_value={})):
        recv_value = ('{'
                      '  "foo": "bar",'
                      '  "baz": "bork",'
                      '  "qux": ["q", "u", "x", "x"]'
                      '}').encode("utf-8")

        payload = zlib.compress(recv_value) + b"\x00\x00\xff\xff"

        chunk_size = 16
        chunks = [payload[i: i + chunk_size] for i in range(0, len(payload), chunk_size)]

        first_array = gw._in_buffer
        gw.ws.recv = asynctest.CoroutineMock(side_effect=chunks)
        await gw._receive_json()
        assert gw._in_buffer is first_array


@pytest.mark.asyncio
async def test_massive_zlib_payloads_cause_buffer_replacement(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)

    with asynctest.patch('json.loads', new=asynctest.MagicMock(return_value={})):
        recv_value = ('{'
                      '  "foo": "bar",'
                      '  "baz": "bork",'
                      '  "qux": ["q", "u", "x", "x"]'
                      '}').encode("utf-8")

        payload = zlib.compress(recv_value) + b"\x00\x00\xff\xff"

        chunk_size = 16
        chunks = [payload[i: i + chunk_size] for i in range(0, len(payload), chunk_size)]

        first_array = gw._in_buffer
        gw.max_persistent_buffer_size = 3
        gw.ws.recv = asynctest.CoroutineMock(side_effect=chunks)
        await gw._receive_json()
        assert gw._in_buffer is not first_array


@pytest.mark.asyncio
async def test_heartbeat_beats_at_interval(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw._heartbeat_interval = 0.05

    task = asyncio.create_task(gw._keep_alive())
    try:
        await asyncio.sleep(0.2)
    finally:
        task.cancel()
        gw.ws.send.assert_awaited_with('{"op": 1, "d": null}')


@pytest.mark.asyncio
async def test_heartbeat_shuts_down_when_closure_request(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw._heartbeat_interval = 0.05

    with async_timeout.timeout(5):
        task = asyncio.create_task(gw._keep_alive())
        try:
            await asyncio.sleep(0.2)
        finally:
            await gw.close(True)
            await task


@pytest.mark.asyncio
async def test_heartbeat_if_not_acknowledged_in_time_closes_connection_with_resume(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw._last_heartbeat_sent = -float('inf')
    gw._heartbeat_interval = 0

    task = asyncio.create_task(gw._keep_alive())

    with async_timeout.timeout(0.1):
        await asyncio.sleep(0)

    task.cancel()
    gw.ws.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_slow_loop_produces_warning(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw._heartbeat_interval = 0
    gw.heartbeat_latency = 0
    gw._logger = asynctest.MagicMock()
    task = asyncio.create_task(gw._keep_alive())

    with async_timeout.timeout(0.1):
        await asyncio.sleep(0)

    task.cancel()
    gw._logger.warning.assert_called_once()


@pytest.mark.asyncio
async def test__send_heartbeat(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw._send_json_async = asynctest.MagicMock()
    await gw._send_heartbeat()
    gw._send_json_async.assert_called_with({"op": 1, "d": None})


@pytest.mark.asyncio
async def test__send_ack(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw._send_json_async = asynctest.MagicMock()
    await gw._send_ack()
    gw._send_json_async.assert_called_with({"op": 11})


@pytest.mark.asyncio
async def test__handle_ack(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw._last_heartbeat_sent = 0
    await gw._handle_ack()
    assert not math.isnan(gw.heartbeat_latency) and not math.isinf(gw.heartbeat_latency)


@pytest.mark.asyncio
async def test__recv_hello_when_is_hello(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw._receive_json = asynctest.CoroutineMock(
        return_value={"op": 10, "d": {"heartbeat_interval": 12345, "_trace": ["foo"]}})
    await gw._recv_hello()

    assert gw.trace == ['foo']
    assert gw._heartbeat_interval == 12.345


@pytest.mark.asyncio
async def test__recv_hello_when_is_not_hello_causes_resume(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw._receive_json = asynctest.CoroutineMock(
        return_value={"op": 9, "d": {"heartbeat_interval": 12345, "_trace": ["foo"]}})

    gw._do_resume = asynctest.CoroutineMock()
    await gw._recv_hello()
    gw._do_resume.assert_awaited()


@pytest.mark.asyncio
async def test__send_resume(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None)
    gw._session_id = 1234321
    gw._seq = 69_420
    gw._send_json_async = asynctest.MagicMock()
    await gw._send_resume()
    gw._send_json_async.assert_called_with({
        "op": 6,
        "d": {
            "token": '1234',
            "session_id": 1234321,
            "seq": 69_420
        }
    })


@pytest.mark.asyncio
async def test__send_identify_when_not_redacted_default_behaviour(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None,
                     large_threshold=69, incognito=False)
    gw._session_id = 1234321
    gw._seq = 69_420
    gw._send_json_async = asynctest.MagicMock()

    with asynctest.patch("hikari.net.gateway.python_version", new=lambda: "python3"), \
         asynctest.patch("hikari.net.gateway.library_version", new=lambda: "vx.y.z"), \
         asynctest.patch("platform.system", new=lambda: "leenuks"):
        await gw._send_identify()
        gw._send_json_async.assert_called_with({
            "op": 2,
            "d": {
                "token": '1234',
                "compress": False,
                "large_threshold": 69,
                "properties": {
                    "$os": "leenuks",
                    "$browser": "vx.y.z",
                    "$device": "python3"
                }
            }
        })


@pytest.mark.asyncio
async def test__send_identify_when_redacted(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=None,
                     large_threshold=69, incognito=True)
    gw._session_id = 1234321
    gw._seq = 69_420
    gw._send_json_async = asynctest.MagicMock()

    with asynctest.patch("hikari.net.gateway.python_version", new=lambda: "python3"), \
         asynctest.patch("hikari.net.gateway.library_version", new=lambda: "vx.y.z"), \
         asynctest.patch("platform.system", new=lambda: "leenuks"):
        await gw._send_identify()
        gw._send_json_async.assert_called_with({
            "op": 2,
            "d": {
                "token": '1234',
                "compress": False,
                "large_threshold": 69,
                "properties": {
                    "$os": "redacted",
                    "$browser": "redacted",
                    "$device": "redacted"
                }
            }
        })


@pytest.mark.asyncio
async def test__send_identify_includes_sharding_info_if_present(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=917,
                     shard_count=1234, large_threshold=69, incognito=False)
    gw._send_json_async = asynctest.MagicMock()

    await gw._send_identify()
    payload = gw._send_json_async.call_args[0][0]

    assert 'd' in payload
    assert 'shard' in payload['d']
    assert payload['d']['shard'] == [917, 1234]


@pytest.mark.asyncio
async def test__send_identify_includes_status_info_if_present(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=917,
                     shard_count=1234, large_threshold=69, incognito=False, initial_presence={'foo': 'bar'})
    gw._send_json_async = asynctest.MagicMock()

    await gw._send_identify()
    payload = gw._send_json_async.call_args[0][0]

    assert 'd' in payload
    assert 'status' in payload['d']
    assert payload['d']['status'] == {'foo': 'bar'}


@pytest.mark.asyncio
async def test__process_events_halts_if_closed_event_is_set(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=917,
                     shard_count=1234, large_threshold=69, incognito=False)
    gw._receive_json = asynctest.CoroutineMock()
    gw.closed_event.set()
    await gw._process_events()
    gw._receive_json.assert_not_awaited()


@pytest.mark.asyncio
async def test__process_events_updates_seq_if_provided_from_payload(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=917,
                     shard_count=1234, large_threshold=69, incognito=False)
    gw._receive_json = asynctest.CoroutineMock(return_value={'op': 0, 'd': {}, 's': 69})
    t = asyncio.create_task(gw._process_events())
    await asyncio.sleep(0.1)
    await gw.close(block=True)
    t.cancel()
    assert gw._seq == 69


@pytest.mark.asyncio
async def test__process_events_does_not_update_seq_if_not_provided_from_payload(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=917,
                     shard_count=1234, large_threshold=69, incognito=False)

    gw._seq = 123
    gw._receive_json = asynctest.CoroutineMock(return_value={'op': 0, 'd': {}})
    t = asyncio.create_task(gw._process_events())
    await asyncio.sleep(0.1)
    await gw.close(block=True)
    await t
    assert gw._seq == 123


@pytest.mark.asyncio
async def test__process_events_on_dispatch_opcode(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=917,
                     shard_count=1234, large_threshold=69, incognito=False)
    gw._receive_json = asynctest.CoroutineMock(return_value={'op': 0, 'd': {}, 't': 'explosion'})
    gw.dispatch = asynctest.CoroutineMock()
    t = asyncio.create_task(gw._process_events())
    await asyncio.sleep(0.1)
    await gw.close(block=True)
    await t
    gw.dispatch.assert_awaited_with('explosion', {})


@pytest.mark.asyncio
async def test__process_events_on_heartbeat_opcode(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=917,
                     shard_count=1234, large_threshold=69, incognito=False)
    gw._receive_json = asynctest.CoroutineMock(return_value={'op': 1, 'd': {}})
    gw._send_ack = asynctest.CoroutineMock()
    t = asyncio.create_task(gw._process_events())
    await asyncio.sleep(0.1)
    await gw.close(block=True)
    await t
    gw._send_ack.assert_any_await()


@pytest.mark.asyncio
async def test__process_events_on_heartbeat_ack_opcode(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=917,
                     shard_count=1234, large_threshold=69, incognito=False)
    gw._receive_json = asynctest.CoroutineMock(return_value={'op': 11, 'd': {}})
    gw._handle_ack = asynctest.CoroutineMock()
    t = asyncio.create_task(gw._process_events())
    await asyncio.sleep(0.1)
    await gw.close(block=True)
    await t
    gw._handle_ack.assert_any_await()


@pytest.mark.asyncio
async def test__process_events_on_reconnect_opcode(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=917,
                     shard_count=1234, large_threshold=69, incognito=False)
    gw._receive_json = asynctest.CoroutineMock(return_value={'op': 7, 'd': {}})

    try:
        with async_timeout.timeout(1):
            await gw._process_events()
        assert False, 'No error raised'
    except gateway.RestartConnection as ex:
        assert ex.code == 1003
        assert ex.reason.startswith('Reconnect opcode was received')


@pytest.mark.asyncio
async def test__process_events_on_resumable_invalid_session_opcode(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=917,
                     shard_count=1234, large_threshold=69, incognito=False)
    gw._receive_json = asynctest.CoroutineMock(return_value={'op': 9, 'd': True})

    try:
        with async_timeout.timeout(1):
            await gw._process_events()
        assert False, 'No error raised'
    except gateway.ResumeConnection as ex:
        assert ex.code == 1003


@pytest.mark.asyncio
async def test__process_events_on_non_resumable_invalid_session_opcode(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=917,
                     shard_count=1234, large_threshold=69, incognito=False)
    gw._receive_json = asynctest.CoroutineMock(return_value={'op': 69, 'd': 'lmao'})

    try:
        with async_timeout.timeout(1):
            await gw._process_events()
        assert False, 'Unknown opcodes should not cause the loop to stop'
    except asyncio.TimeoutError:
        assert True, 'Expected happy path'


@pytest.mark.asyncio
async def test_request_guild_members(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=917,
                     shard_count=1234, large_threshold=69, incognito=False)
    gw._send_json_async = asynctest.MagicMock()
    await gw.request_guild_members(1234)
    gw._send_json_async.assert_called_with({
        'op': 8,
        "d": {
            "guild_id": "1234",
            "query": "",
            "limit": 0,
        }
    })


@pytest.mark.asyncio
async def test_update_status(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=917,
                     shard_count=1234, large_threshold=69, incognito=False)
    gw._send_json_async = asynctest.MagicMock()
    await gw.update_status(1234, {'name': 'boom'}, 'dead', True)
    gw._send_json_async.assert_called_with({
        'op': 3,
        "d": {
            "idle": 1234,
            "game": {
                "name": "boom"
            },
            "status": "dead",
            "afk": True,
        }
    })


@pytest.mark.asyncio
async def test_update_voice_state(event_loop):
    gw = MockGateway(host="wss://gateway.discord.gg:4949/", loop=event_loop, token='1234', shard_id=917,
                     shard_count=1234, large_threshold=69, incognito=False)
    gw._send_json_async = asynctest.MagicMock()
    await gw.update_voice_state(1234, 5678, False, True)
    gw._send_json_async.assert_called_with({
        'op': 4,
        "d": {
            "guild_id": "1234",
            "channel_id": "5678",
            "self_mute": False,
            "self_deaf": True,
        }
    })
