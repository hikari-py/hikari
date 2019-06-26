#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest

from hikari import _utils


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_delete_close_channel(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.delete_close_channel("12345")
    http_client.request.assert_awaited_once_with(
        "delete", "/channels/{channel_id}", channel_id="12345", reason=_utils.unspecified
    )


@pytest.mark.asyncio
async def test_with_optional_reason(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.delete_close_channel("696969", reason="because i can")
    args, kwargs = http_client.request.call_args
    assert kwargs["reason"] == "because i can"
