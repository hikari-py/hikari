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

from hikari import utils


test_args = {
    "topic": "I like trains.",
    "bitrate": 64000,
    "user_limit": 10,
    "rate_limit_per_user": 100,
    "position": 2,
    "permission_overwrites": [{"id": "404101", "type": "role", "allow": 666, "deny": 911}],
    "parent_id": 404,
    "nsfw": True,
}


@pytest.fixture()
async def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_create_guild_channel_no_kwars(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_guild_channel("424242", "asdf")
    http_client.request.assert_awaited_once_with(
        "post", "/guilds/{guild_id}/channels", guild_id="424242", json={"name": "asdf"}, reason=utils.UNSPECIFIED
    )


@pytest.mark.asyncio
async def test_create_guild_channel_all_kwars(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_guild_channel("424242", "asdf", type_=1, **test_args)
    http_client.request.assert_awaited_once_with(
        "post",
        "/guilds/{guild_id}/channels",
        guild_id="424242",
        json=dict(name="asdf", type=1, **test_args),
        reason=utils.UNSPECIFIED,
    )


@pytest.mark.asyncio
async def test_with_optional_reason(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.create_guild_channel("424242", "asdf", reason="baz")
    args, kwargs = http_client.request.call_args
    assert kwargs["reason"] == "baz"
