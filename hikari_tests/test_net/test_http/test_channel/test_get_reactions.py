#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.

import asynctest
import pytest


@pytest.fixture()
async def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_no_kwargs(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_reactions("12345", "54321", "99887766")
    http_client.request.assert_awaited_once_with(
        "get",
        "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
        channel_id="12345",
        message_id="54321",
        emoji="99887766",
        json={},
    )


@pytest.mark.asyncio
async def test_before(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_reactions("12345", "54321", "99887766", before="707")
    http_client.request.assert_awaited_once_with(
        "get",
        "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
        channel_id="12345",
        message_id="54321",
        emoji="99887766",
        json={"before": "707"},
    )


@pytest.mark.asyncio
async def test_after(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_reactions("12345", "54321", "99887766", after="707")
    http_client.request.assert_awaited_once_with(
        "get",
        "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
        channel_id="12345",
        message_id="54321",
        emoji="99887766",
        json={"after": "707"},
    )


@pytest.mark.asyncio
async def test_limit(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_reactions("12345", "54321", "99887766", limit=10)
    http_client.request.assert_awaited_once_with(
        "get",
        "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
        channel_id="12345",
        message_id="54321",
        emoji="99887766",
        json={"limit": 10},
    )


@pytest.mark.asyncio
async def test_limit_and_before(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_reactions("12345", "54321", "99887766", limit=10, before="707")
    http_client.request.assert_awaited_once_with(
        "get",
        "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
        channel_id="12345",
        message_id="54321",
        emoji="99887766",
        json={"limit": 10, "before": "707"},
    )


@pytest.mark.asyncio
async def test_limit_and_after(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_reactions("12345", "54321", "99887766", limit=10, after="707")
    http_client.request.assert_awaited_once_with(
        "get",
        "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
        channel_id="12345",
        message_id="54321",
        emoji="99887766",
        json={"limit": 10, "after": "707"},
    )
