#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_delete_pinned_channel_message(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.delete_pinned_channel_message("12345", "54321")
    http_client.request.assert_awaited_once_with(
        "delete", "/channels/{channel_id}/pins/{message_id}", channel_id="12345", message_id="54321"
    )
