#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
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
import asyncio
import logging

import cymock as mock
import pytest

from hikari.net import gateway as _gateway
from hikari.orm import fabric
from hikari.orm.gateway import basic_chunker_impl
from hikari.orm.models import guilds
from hikari.orm.models import members
from hikari.orm.state import base_registry
from tests.hikari import _helpers


@pytest.fixture
def fabric_obj():
    def make_gateway():
        gw = _helpers.create_autospec(_gateway.GatewayClient)
        gw.request_guild_members = mock.AsyncMock()
        return gw

    fabric_obj = fabric.Fabric()
    fabric_obj.state_registry = _helpers.create_autospec(base_registry.BaseRegistry)
    fabric_obj.gateways = {
        # We'd never have None and shard ids together, but this doesn't matter for this test.
        None: make_gateway(),
        0: make_gateway(),
        1: make_gateway(),
        2: make_gateway(),
        3: make_gateway(),
        4: make_gateway(),
    }
    fabric_obj.chunker = _helpers.unslot_class(basic_chunker_impl.BasicChunkerImpl)(fabric_obj)
    return fabric_obj


@pytest.fixture
def guild_chunk_payload_no_presences(member_payload):
    return {"guild_id": "1", "members": [member_payload]}


@pytest.fixture
def guild_chunk_payload_presences(member_payload, presence_payload):
    return {"guild_id": "1", "members": [member_payload], "presences": [presence_payload]}


@pytest.fixture
def member_payload():
    return {"user": {"id": "1234", "username": "blah", "discriminator": "6969", "avatar": None}}


@pytest.fixture
def presence_payload():
    return {
        "user": {"id": "1234"},
        "status": "online",
        "game": None,
        "client_status": {"desktop": "online"},
        "activities": [],
        "roles": ["123", "456", "789"],
        "guild_id": "1",
    }


@_helpers.assert_raises(type_=RuntimeError)
@pytest.mark.asyncio
async def test_load_members_for_does_not_allow_both_user_ids_and_query(fabric_obj):
    guild_obj1 = _helpers.mock_model(guilds.Guild, id=1234)
    guild_obj2 = _helpers.mock_model(guilds.Guild, id=3456)

    await fabric_obj.chunker.load_members_for(guild_obj1, guild_obj2, query="a string", user_ids=[9, 18, 27, 36])


@_helpers.assert_raises(type_=RuntimeError)
@pytest.mark.asyncio
async def test_load_members_for_does_not_allow_both_user_ids_and_limit(fabric_obj):
    guild_obj1 = _helpers.mock_model(guilds.Guild, id=1234)
    guild_obj2 = _helpers.mock_model(guilds.Guild, id=3456)

    await fabric_obj.chunker.load_members_for(guild_obj1, guild_obj2, limit=69, user_ids=[9, 18, 27, 36])


@pytest.mark.asyncio
async def test_load_members_for_when_user_ids_provided(fabric_obj):
    guild_obj1 = _helpers.mock_model(guilds.Guild, id=1234, shard_id=0)
    guild_obj2 = _helpers.mock_model(guilds.Guild, id=3456, shard_id=0)

    with mock.patch("asyncio.create_task"):
        await fabric_obj.chunker.load_members_for(guild_obj1, guild_obj2, user_ids=[9, 18, 27], presences=False)

    assert fabric_obj.chunker.queues[0].get_nowait() == [1234, {"presences": False, "user_ids": ["9", "18", "27"]}]
    assert fabric_obj.chunker.queues[0].get_nowait() == [3456, {"presences": False, "user_ids": ["9", "18", "27"]}]
    assert fabric_obj.chunker.queues[0].empty()


@pytest.mark.asyncio
async def test_load_members_for_when_no_filter_provided(fabric_obj):
    guild_obj1 = _helpers.mock_model(guilds.Guild, id=1234, shard_id=0)
    guild_obj2 = _helpers.mock_model(guilds.Guild, id=3456, shard_id=0)

    with mock.patch("asyncio.create_task"):
        await fabric_obj.chunker.load_members_for(guild_obj1, guild_obj2, presences=False, limit=69)

    assert fabric_obj.chunker.queues[0].get_nowait() == [1234, {"presences": False, "query": "", "limit": 69}]
    assert fabric_obj.chunker.queues[0].get_nowait() == [3456, {"presences": False, "query": "", "limit": 69}]
    assert fabric_obj.chunker.queues[0].empty()


@pytest.mark.asyncio
async def test_load_members_for_with_shards(fabric_obj):
    guild_obj1 = _helpers.mock_model(guilds.Guild, id=1, shard_id=1)
    guild_obj2 = _helpers.mock_model(guilds.Guild, id=2, shard_id=1)
    guild_obj3 = _helpers.mock_model(guilds.Guild, id=3, shard_id=2)
    guild_obj4 = _helpers.mock_model(guilds.Guild, id=4, shard_id=2)
    guild_obj5 = _helpers.mock_model(guilds.Guild, id=5, shard_id=2)
    guild_obj6 = _helpers.mock_model(guilds.Guild, id=6, shard_id=2)
    guild_obj7 = _helpers.mock_model(guilds.Guild, id=7, shard_id=3)
    guild_obj8 = _helpers.mock_model(guilds.Guild, id=8, shard_id=3)
    guild_obj9 = _helpers.mock_model(guilds.Guild, id=9, shard_id=4)

    await fabric_obj.chunker.load_members_for(
        guild_obj1,
        guild_obj2,
        guild_obj3,
        guild_obj4,
        guild_obj5,
        guild_obj6,
        guild_obj7,
        guild_obj8,
        guild_obj9,
        **{"user_ids": [9, 18, 27, 36]},
    )

    assert fabric_obj.chunker.queues[1].get_nowait() == [1, {"presences": True, "user_ids": ["9", "18", "27", "36"]}]
    assert fabric_obj.chunker.queues[1].get_nowait() == [2, {"presences": True, "user_ids": ["9", "18", "27", "36"]}]
    assert fabric_obj.chunker.queues[1].empty()

    assert fabric_obj.chunker.queues[2].get_nowait() == [3, {"presences": True, "user_ids": ["9", "18", "27", "36"]}]
    assert fabric_obj.chunker.queues[2].get_nowait() == [4, {"presences": True, "user_ids": ["9", "18", "27", "36"]}]
    assert fabric_obj.chunker.queues[2].get_nowait() == [5, {"presences": True, "user_ids": ["9", "18", "27", "36"]}]
    assert fabric_obj.chunker.queues[2].get_nowait() == [6, {"presences": True, "user_ids": ["9", "18", "27", "36"]}]
    assert fabric_obj.chunker.queues[2].empty()

    assert fabric_obj.chunker.queues[3].get_nowait() == [7, {"presences": True, "user_ids": ["9", "18", "27", "36"]}]
    assert fabric_obj.chunker.queues[3].get_nowait() == [8, {"presences": True, "user_ids": ["9", "18", "27", "36"]}]
    assert fabric_obj.chunker.queues[3].empty()

    assert fabric_obj.chunker.queues[4].get_nowait() == [9, {"presences": True, "user_ids": ["9", "18", "27", "36"]}]
    assert fabric_obj.chunker.queues[4].empty()


@pytest.mark.asyncio
async def test_load_members_for_creates_queue_for_shard_if_non_existent(fabric_obj):
    guild_obj = _helpers.mock_model(guilds.Guild, id=1, shard_id=0)
    fabric_obj.chunker.queues = {}

    await fabric_obj.chunker.load_members_for(guild_obj)

    assert fabric_obj.chunker.queues[0].get_nowait() == [1, {"presences": True, "query": "", "limit": 0}]
    assert fabric_obj.chunker.queues[0].empty()


@pytest.mark.asyncio
async def test_load_members_for_creates_task_for_shard_if_non_existent(fabric_obj):
    guild_obj = _helpers.mock_model(guilds.Guild, id=1, shard_id=0)
    fabric_obj.chunker.shard_chunkers = {}
    fabric_obj.chunker._do_chunk_for_shard = mock.MagicMock()

    with mock.patch("asyncio.create_task") as create_task:
        await fabric_obj.chunker.load_members_for(guild_obj)

        create_task.assert_called_once_with(fabric_obj.chunker._do_chunk_for_shard(0))


@pytest.mark.asyncio
async def test__do_chunk_for_shard_goes_through_all_the_queue_and_then_selfdestroys(fabric_obj):
    queue = asyncio.Queue()
    await queue.put([123, {"presences": True}])

    fabric_obj.chunker.queues = {0: queue}
    fabric_obj.chunker.shard_chunkers = {0: None}

    await fabric_obj.chunker._do_chunk_for_shard(0)

    fabric_obj.gateways[0].request_guild_members.assert_called_with(123, presences=True)
    assert fabric_obj.chunker.shard_chunkers == {}


@pytest.mark.asyncio
async def test_handle_next_chunk_for_unknown_guild_does_nothing(fabric_obj, guild_chunk_payload_no_presences):
    fabric_obj.chunker.logger = _helpers.create_autospec(logging.Logger)
    fabric_obj.state_registry.get_guild_by_id = mock.MagicMock(
        spec_set=fabric_obj.state_registry.get_guild_by_id, return_value=None
    )

    await fabric_obj.chunker.handle_next_chunk(guild_chunk_payload_no_presences, 1)

    fabric_obj.state_registry.get_guild_by_id.assert_called_with(1)
    fabric_obj.chunker.logger.warning.assert_called_once()


@pytest.mark.asyncio
async def test_handle_next_chunk_for_members_without_presences(
    fabric_obj, guild_chunk_payload_no_presences, member_payload
):
    guild_obj = _helpers.mock_model(guilds.Guild, id=1, shard_id=1)
    member_obj = _helpers.mock_model(members.Member, id=1234)
    fabric_obj.state_registry.parse_member = mock.MagicMock(
        spec_set=fabric_obj.state_registry.parse_member, return_value=member_obj
    )
    fabric_obj.state_registry.get_guild_by_id = mock.MagicMock(
        spec_set=fabric_obj.state_registry.get_guild_by_id, return_value=guild_obj
    )

    await fabric_obj.chunker.handle_next_chunk(guild_chunk_payload_no_presences, 1)

    fabric_obj.state_registry.parse_member.assert_called_with(member_payload, guild_obj)
    fabric_obj.state_registry.parse_presence.assert_not_called()


@pytest.mark.asyncio
async def test_handle_next_chunk_for_members_with_presences(
    fabric_obj, guild_chunk_payload_presences, member_payload, presence_payload
):
    guild_obj = _helpers.mock_model(guilds.Guild, id=1, shard_id=1)
    member_obj = _helpers.mock_model(members.Member, id=1234)
    fabric_obj.state_registry.parse_member = mock.MagicMock(
        spec_set=fabric_obj.state_registry.parse_member, return_value=member_obj
    )
    fabric_obj.state_registry.get_guild_by_id = mock.MagicMock(
        spec_set=fabric_obj.state_registry.get_guild_by_id, return_value=guild_obj
    )
    fabric_obj.chunker.logger = _helpers.create_autospec(logging.Logger)

    await fabric_obj.chunker.handle_next_chunk(guild_chunk_payload_presences, 1)

    fabric_obj.state_registry.parse_member.assert_called_with(member_payload, guild_obj)
    fabric_obj.state_registry.parse_presence.assert_called_with(member_obj, presence_payload)


def test_close_cancels_all_shard_tasks(event_loop, fabric_obj):
    task1 = event_loop.create_future()
    task2 = event_loop.create_future()

    fabric_obj.chunker.shard_chunkers = {0: task1, 1: task2}

    fabric_obj.chunker.close()

    assert task1.cancelled()
    assert task2.cancelled()
