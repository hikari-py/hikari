#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest
import asynctest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)

@pytest.mark.asyncio
async def test_list_guild_regions(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.list_voice_regions()
    http_client.request.assert_awaited_once_with("get", "/voice/regions")
