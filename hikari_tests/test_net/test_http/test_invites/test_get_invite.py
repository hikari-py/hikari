#!/usr/bin/env python3
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_get_invite_without_counts(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_invite("424242")
    http_client.request.assert_awaited_once_with("get", "/invites/{invite_code}", invite_code="424242", query={})


@pytest.mark.asyncio
async def test_get_invite_with_counts(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_invite("424242", with_counts=True)
    http_client.request.assert_awaited_once_with(
        "get", "/invites/{invite_code}", invite_code="424242", query={"with_counts": True}
    )
