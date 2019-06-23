#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_create_reaction(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_channel_message("696969", "12")
    http_client.request.assert_awaited_once_with(
        "get", "/channels/{channel_id}/messages/{message_id}", channel_id="696969", message_id="12"
    )
