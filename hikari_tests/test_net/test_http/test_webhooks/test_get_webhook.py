#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_get_webhook(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_webhook("424242")
    http_client.request.assert_awaited_once_with("get", "/webhooks/{webhook_id}", webhook_id="424242")
