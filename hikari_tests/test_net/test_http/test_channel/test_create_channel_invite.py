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

from hikari import _utils


@pytest.fixture()
async def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_without_optional_args_has_empty_payload(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_channel_invite("696969")
    http_client.request.assert_awaited_once_with(
        "post", "/channels/{channel_id}/invites", channel_id="696969", json={}, reason=_utils.unspecified
    )


@pytest.mark.asyncio
async def test_with_max_age(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_channel_invite("696969", max_age=10)
    http_client.request.assert_awaited_once_with(
        "post", "/channels/{channel_id}/invites", channel_id="696969", json={"max_age": 10}, reason=_utils.unspecified
    )


@pytest.mark.asyncio
async def test_with_max_uses(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_channel_invite("696969", max_uses=10)
    http_client.request.assert_awaited_once_with(
        "post", "/channels/{channel_id}/invites", channel_id="696969", json={"max_uses": 10}, reason=_utils.unspecified
    )


@pytest.mark.asyncio
async def test_with_temporary(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_channel_invite("696969", temporary=True)
    http_client.request.assert_awaited_once_with(
        "post",
        "/channels/{channel_id}/invites",
        channel_id="696969",
        json={"temporary": True},
        reason=_utils.unspecified,
    )


@pytest.mark.asyncio
async def test_with_unique(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_channel_invite("696969", unique=True)
    http_client.request.assert_awaited_once_with(
        "post", "/channels/{channel_id}/invites", channel_id="696969", json={"unique": True}, reason=_utils.unspecified
    )


@pytest.mark.asyncio
async def test_optional_reason(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_channel_invite("696969", reason="because i can")
    args, kwargs = http_client.request.call_args
    assert kwargs["reason"] == "because i can"
