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
async def test_edit_channel_permissions(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.edit_channel_permissions("69", "420", allow=192, deny=168, type_="member")
    http_client.request.assert_awaited_once_with(
        "put",
        "/channels/{channel_id}/permissions/{overwrite_id}",
        channel_id="69",
        overwrite_id="420",
        json={"allow": 192, "deny": 168, "type": "member"},
        reason=_utils.unspecified,
    )


@pytest.mark.asyncio
async def test_with_optional_reason(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.edit_channel_permissions(
        "696969", "123456", allow=123, deny=456, type_="me", reason="because i can"
    )
    args, kwargs = http_client.request.call_args
    assert kwargs["reason"] == "because i can"
