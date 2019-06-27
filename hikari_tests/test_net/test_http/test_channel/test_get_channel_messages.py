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
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_no_kwargs(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_channel_messages("696969")
    http_client.request.assert_awaited_once_with("get", "/channels/{channel_id}/messages", channel_id="696969", json={})


@pytest.mark.asyncio
async def test_with_limit(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_channel_messages("696969", limit=12)
    http_client.request.assert_awaited_once_with(
        "get", "/channels/{channel_id}/messages", channel_id="696969", json={"limit": 12}
    )


@pytest.mark.asyncio
async def test_with_before(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_channel_messages("696969", before="12")
    http_client.request.assert_awaited_once_with(
        "get", "/channels/{channel_id}/messages", channel_id="696969", json={"before": "12"}
    )


@pytest.mark.asyncio
async def test_with_after(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_channel_messages("696969", after="12")
    http_client.request.assert_awaited_once_with(
        "get", "/channels/{channel_id}/messages", channel_id="696969", json={"after": "12"}
    )


@pytest.mark.asyncio
async def test_with_around(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_channel_messages("696969", around="12")
    http_client.request.assert_awaited_once_with(
        "get", "/channels/{channel_id}/messages", channel_id="696969", json={"around": "12"}
    )


@pytest.mark.asyncio
async def test_with_before_and_limit(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_channel_messages("696969", before="12", limit=12)
    http_client.request.assert_awaited_once_with(
        "get", "/channels/{channel_id}/messages", channel_id="696969", json={"before": "12", "limit": 12}
    )


@pytest.mark.asyncio
async def test_with_after_and_limit(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_channel_messages("696969", after="12", limit=12)
    http_client.request.assert_awaited_once_with(
        "get", "/channels/{channel_id}/messages", channel_id="696969", json={"after": "12", "limit": 12}
    )


@pytest.mark.asyncio
async def test_with_around_and_limit(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.get_channel_messages("696969", around="12", limit=12)
    http_client.request.assert_awaited_once_with(
        "get", "/channels/{channel_id}/messages", channel_id="696969", json={"around": "12", "limit": 12}
    )
