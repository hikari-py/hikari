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
async def test_modify_webhook(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.modify_webhook("424242", "asdf", b"", "696969")
    http_client.request.assert_awaited_once_with(
        "patch",
        "/webhooks/{webhook_id}",
        webhook_id="424242",
        json={"name": "asdf", "avatar": b"", "channel_id": "696969"},
        reason=_utils.unspecified,
    )


@pytest.mark.asyncio
async def test_with_optional_reason(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.modify_webhook("696969", "123456", b"", "1234", reason="because i can")
    args, kwargs = http_client.request.call_args
    assert kwargs["reason"] == "because i can"
