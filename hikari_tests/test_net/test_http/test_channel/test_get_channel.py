#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_get_channel(http_client):
    http_client.request = asynctest.CoroutineMock(return_value={"id": "696969", "name": "bobs and v"})
    channel = await http_client.get_channel("696969")
    http_client.request.assert_awaited_once_with("get", "/channels/{channel_id}", channel_id="696969")
    assert channel == {"id": "696969", "name": "bobs and v"}
