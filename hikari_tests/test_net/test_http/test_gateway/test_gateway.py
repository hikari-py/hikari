#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_get_gateway(http_client):
    http_client.request = asynctest.CoroutineMock(return_value={"url": "http://somehost.com"})
    url = await http_client.get_gateway()
    http_client.request.assert_awaited_once_with("get", "/gateway")
    assert url == "http://somehost.com"


@pytest.mark.asyncio
async def test_get_gateway_bot(http_client):
    payload = {
        "url": "http://somehost.com",
        "shards": 123,
        "session_start_limit": {"total": 1000, "remaining": 999, "reset_after": 14400000},
    }
    http_client.request = asynctest.CoroutineMock(return_value=payload)
    obj = await http_client.get_gateway_bot()
    http_client.request.assert_awaited_once_with("get", "/gateway/bot")
    assert obj == payload
