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

test_data_kwargs = [
    ("position", 10),
    ("topic", "eating donkey"),
    ("nsfw", True),
    ("rate_limit_per_user", 420),
    ("bitrate", 69_000),
    ("user_limit", 69),
    ("permission_overwrites", [{"id": "919191", "allow": 0, "deny": 180}, {"id": "191919", "allow": 10, "deny": 19}]),
    ("parent_id", "999999"),
]


@pytest.fixture()
async def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_modify_channel_no_kwargs(http_client):
    # Not sure if this is even valid TODO: verify
    http_client.request = asynctest.CoroutineMock()
    await http_client.modify_channel("12345")
    http_client.request.assert_awaited_once_with(
        "patch", "/channels/{channel_id}", channel_id="12345", json={}, reason=utils.UNSPECIFIED
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(["name", "value"], test_data_kwargs)
async def test_modify_channel_with_one_kwarg(http_client, name, value):
    http_client.request = asynctest.CoroutineMock()
    await http_client.modify_channel("12345", **{name: value})
    http_client.request.assert_awaited_once_with(
        "patch", "/channels/{channel_id}", channel_id="12345", json={name: value}, reason=utils.UNSPECIFIED
    )


@pytest.mark.asyncio
async def test_modify_channel_with_many_kwargs(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.modify_channel("12345", **{name: value for name, value in test_data_kwargs})
    http_client.request.assert_awaited_once_with(
        "patch",
        "/channels/{channel_id}",
        channel_id="12345",
        json={name: value for name, value in test_data_kwargs},
        reason=utils.UNSPECIFIED,
    )


@pytest.mark.asyncio
async def test_modify_channel_return_value(http_client):
    http_client.request = asynctest.CoroutineMock(return_value={"...": "..."})
    result = await http_client.modify_channel("12345")
    assert result == {"...": "..."}


@pytest.mark.asyncio
async def test_with_optional_reason(http_client):
    http_client.request = asynctest.CoroutineMock()
    await http_client.modify_channel("696969", reason="because i can")
    args, kwargs = http_client.request.call_args
    assert kwargs["reason"] == "because i can"
