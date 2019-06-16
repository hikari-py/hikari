#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest

from hikari.models.audit import action_type


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_audit_log_request_layout(http_client):
    http_client.request = asynctest.CoroutineMock(return_value=(..., ..., {}))

    result = await http_client.get_guild_audit_log(
        1234, user_id=5678, action=action_type.ActionType.MEMBER_KICK, limit=18
    )

    http_client.request.assert_awaited_once_with(
        "get",
        "/guilds/{guild_id}/audit-logs",
        params={"guild_id": 1234},
        query={"user_id": 5678, "action_type": action_type.ActionType.MEMBER_KICK.value, "limit": 18},
    )

    assert result == {}


@pytest.mark.asyncio
async def test_audit_log_request_default_args(http_client):
    http_client.request = asynctest.CoroutineMock(return_value=(..., ..., {}))

    result = await http_client.get_guild_audit_log(1234)

    http_client.request.assert_awaited_once_with(
        "get", "/guilds/{guild_id}/audit-logs", params={"guild_id": 1234}, query={}
    )

    assert result == {}


@pytest.mark.asyncio
async def test_audit_log_request_with_bad_limit(http_client):
    http_client.request = asynctest.CoroutineMock(return_value=(..., ..., {}))

    try:
        await http_client.get_guild_audit_log(1234, limit=-17)
        assert False
    except ValueError:
        assert True
