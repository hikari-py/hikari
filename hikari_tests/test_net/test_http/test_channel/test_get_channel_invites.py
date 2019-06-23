#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_get_channel_invites(http_client):
    http_client.request = asynctest.CoroutineMock(return_value={"...": "..."})
    result = await http_client.get_channel_invites("123456")
    http_client.request.assert_awaited_once_with("get", "/channels/{channel_id}/invites", channel_id="123456")
    assert result == {"...": "..."}
