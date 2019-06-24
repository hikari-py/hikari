#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_bulk_delete_messages(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.bulk_delete_messages("69", ["192", "168", "0", "1"])
    http_client.request.assert_awaited_once_with(
        "post",
        "/channels/{channel_id}/messages/bulk-delete",
        channel_id="69",
        json={"messages": ["192", "168", "0", "1"]},
    )
