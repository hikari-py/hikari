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


test_all_kwargs = {
    "name": "asdf",
    "region": "eu-west",
    "verification_level": 1,
    "default_message_notifications": 1,
    "explicit_content_filter": 1,
    "afk_channel_id": "404101",
    "afk_timeout": 10,
    "icon": b"",
    "owner_id": "696969",
    "splash": b"",
    "system_channel_id": "112",
}


@pytest.fixture()
async def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_modify_guild_no_kwargs(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.modify_guild("424242")
    http_client.request.assert_awaited_once_with(
        "patch", "/guilds/{guild_id}", guild_id="424242", json={}, reason=utils.UNSPECIFIED
    )


@pytest.mark.asyncio
async def test_modify_guild_all_kwargs(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.modify_guild("424242", **test_all_kwargs)
    http_client.request.assert_awaited_once_with(
        "patch", "/guilds/{guild_id}", guild_id="424242", json=test_all_kwargs, reason=utils.UNSPECIFIED
    )


@pytest.mark.asyncio
async def test_with_optional_reason(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.modify_guild("424242", reason="baz")
    args, kwargs = http_client.request.call_args
    assert kwargs["reason"] == "baz"
