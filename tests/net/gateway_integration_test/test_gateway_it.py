#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import functools
import inspect
import logging

import pytest
import async_timeout

from hikari.net import gateway
from tests.net.gateway_integration_test import gateway_mock


def timeout_after(time: float):
    def decorator(coro):
        if inspect.iscoroutinefunction(coro):
            @functools.wraps(coro)
            async def call(*args, **kwargs):
                async with async_timeout.timeout(time):
                    return await coro(*args, **kwargs)
        else:
            raise TypeError('Need async')

        return call

    return decorator


HOST, PORT = "localhost", 9876
URI = f"ws://{HOST}:{PORT}/api/v7/gateway"
LOGGER = logging.getLogger("GatewayTest")
VALID_TOKEN = "test_token"


@pytest.fixture
async def server(event_loop):
    LOGGER.info("creating mock server at %s:%s", HOST, PORT)
    server = gateway_mock.MockGatewayServerV7(event_loop, VALID_TOKEN)
    await server.start(HOST, PORT)
    LOGGER.info("mock server is ready")
    yield server
    LOGGER.info("requesting server to shut down")
    await server.stop()
    LOGGER.info("server stopped")


@timeout_after(15)
@pytest.mark.asyncio
async def test_client_attempts_to_identify_once_connected(event_loop, server):
    gw = gateway.GatewayConnection(
        host=URI, loop=event_loop, token=VALID_TOKEN
    )
    asyncio.create_task(gw.run())
    await server.connection_made.wait()
    await server.send_hello()
    identify = await server.wait_for(lambda p: p["op"] == server.IDENTIFY_OP)

    assert identify['op'] == 2

    d = identify['d']
    assert d['token'] == VALID_TOKEN
    assert d['compress'] is False
    assert isinstance(d['large_threshold'], int)
    assert 0 <= d['large_threshold'] <= 200

    properties = d['properties']
    assert '$os' in properties
    assert '$browser' in properties
    assert '$device' in properties

    await gw.close(True)


@timeout_after(30)
@pytest.mark.asyncio
async def test_client_starts_heartbeating(event_loop, server):
    gw = gateway.GatewayConnection(
        host=URI, loop=event_loop, token=VALID_TOKEN
    )
    asyncio.create_task(gw.run())

    # Really short interval just for testing sanity...
    server.heartbeat_interval = 2_500
    await server.connection_made.wait()
    await server.send_hello()

    for i in range(3):
        await server.wait_for(lambda p: p["op"] == server.HEARTBEAT_OP)

    await gw.close(True)


@timeout_after(30)
@pytest.mark.asyncio
async def test_client_acknowledges_heart_beat(event_loop, server):
    gw = gateway.GatewayConnection(
        host=URI, loop=event_loop, token=VALID_TOKEN
    )
    asyncio.create_task(gw.run())
    server.heartbeat_interval = 40_000
    await server.connection_made.wait()
    await server.send_hello()

    for i in range(3):
        w = asyncio.create_task(
            server.wait_for(lambda p: p["op"] == server.HEARTBEAT_ACK_OP)
        )
        await server.send_heartbeat()
        await w
        await asyncio.sleep(1)

    await gw.close(True)


@timeout_after(30)
@pytest.mark.asyncio
async def test_client_acknowledges_heart_beat(event_loop, server):
    gw = gateway.GatewayConnection(
        host=URI, loop=event_loop, token=VALID_TOKEN
    )
    asyncio.create_task(gw.run())
    server.heartbeat_interval = 40_000
    await server.connection_made.wait()
    await server.send_hello()

    for i in range(3):
        w = asyncio.create_task(
            server.wait_for(lambda p: p["op"] == server.HEARTBEAT_ACK_OP)
        )
        await server.send_heartbeat()
        await w
        await asyncio.sleep(1)

    await gw.close(True)


@timeout_after(30)
@pytest.mark.asyncio
async def test_client_can_resume(event_loop, server):
    gw = gateway.GatewayConnection(host=URI, loop=event_loop, token=VALID_TOKEN)

    seq = 123
    session_id = 12345

    # Will reidentify
    gw._seq = seq
    gw._session_id = session_id
    server.seq = seq
    server.session_id = session_id

    asyncio.create_task(gw.run())
    await server.connection_made.wait()
    await server.send_hello()
    resume = await server.wait_for(lambda p: p["op"] == server.RESUME_OP)

    assert resume['op'] == 6

    d = resume['d']
    assert d['token'] == VALID_TOKEN
    assert d['seq'] == seq
    assert d['session_id'] == session_id

    await gw.close(True)


@timeout_after(15)
@pytest.mark.asyncio
async def test_client_understands_small_zlib_payloads(event_loop, server):
    # Try sending a zlib-compressed "hello" payload. Our logic should decode this properly.
    gw = gateway.GatewayConnection(host=URI, loop=event_loop, token=VALID_TOKEN)
    asyncio.create_task(gw.run())
    await server.connection_made.wait()

    hello_payload = server.make_payload(
        server.HELLO_OP,
        {"heartbeat_interval": server.heartbeat_interval, "_trace": server.trace},
    )

    await server.send_compressed_json(hello_payload)
    identify = await server.wait_for(lambda p: p["op"] == server.IDENTIFY_OP)

    assert identify['op'] == 2

    d = identify['d']
    assert d['token'] == VALID_TOKEN
    assert d['compress'] is False
    assert isinstance(d['large_threshold'], int)
    assert 0 <= d['large_threshold'] <= 200

    properties = d['properties']
    assert '$os' in properties
    assert '$browser' in properties
    assert '$device' in properties

    await gw.close(True)
