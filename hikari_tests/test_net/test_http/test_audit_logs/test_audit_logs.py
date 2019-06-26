#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_audit_log_request_layout(http_client):
    http_client.request = asynctest.CoroutineMock(return_value={"foo": "bar"})

    result = await http_client.get_guild_audit_log("1234", user_id="5678", action_type=20, limit=18)

    http_client.request.assert_awaited_once_with(
        "get",
        "/guilds/{guild_id}/audit-logs",
        query={"user_id": "5678", "action_type": 20, "limit": 18},
        guild_id="1234",
    )

    assert result == {"foo": "bar"}


@pytest.mark.asyncio
async def test_audit_log_request_default_args(http_client):
    http_client.request = asynctest.CoroutineMock(return_value={"foo": "bar"})

    result = await http_client.get_guild_audit_log("1234")

    http_client.request.assert_awaited_once_with("get", "/guilds/{guild_id}/audit-logs", guild_id="1234", query={})

    assert result == {"foo": "bar"}
