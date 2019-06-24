#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_create_guild_emoji(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_guild_emoji("424242", "asdf", b"", [])
    http_client.request.assert_awaited_once_with(
        "post", "/guilds/{guild_id}/emojis", guild_id="424242", json={"name": "asdf", "image": b"", "roles": []}
    )
