#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_without_optional_args_has_empty_payload(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_channel_invite("696969")
    http_client.request.assert_awaited_once_with("post", "/channels/{channel_id}/invites", channel_id="696969", json={})


@pytest.mark.asyncio
async def test_with_max_age(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_channel_invite("696969", max_age=10)
    http_client.request.assert_awaited_once_with(
        "post", "/channels/{channel_id}/invites", channel_id="696969", json={"max_age": 10}
    )


@pytest.mark.asyncio
async def test_with_max_uses(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_channel_invite("696969", max_uses=10)
    http_client.request.assert_awaited_once_with(
        "post", "/channels/{channel_id}/invites", channel_id="696969", json={"max_uses": 10}
    )


@pytest.mark.asyncio
async def test_with_temporary(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_channel_invite("696969", temporary=True)
    http_client.request.assert_awaited_once_with(
        "post", "/channels/{channel_id}/invites", channel_id="696969", json={"temporary": True}
    )


@pytest.mark.asyncio
async def test_with_unique(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_channel_invite("696969", unique=True)
    http_client.request.assert_awaited_once_with(
        "post", "/channels/{channel_id}/invites", channel_id="696969", json={"unique": True}
    )
