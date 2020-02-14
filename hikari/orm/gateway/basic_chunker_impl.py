#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""
Basic implementation of a chunker.
"""
from __future__ import annotations

import asyncio
import typing

import hikari.internal_utilities.type_hints
from hikari.internal_utilities import containers
from hikari.internal_utilities import loggers
from hikari.net import ratelimits
from hikari.orm.gateway import base_chunker

if typing.TYPE_CHECKING:
    from hikari.internal_utilities import type_hints
    from hikari.orm import fabric
    from hikari.orm.models import guilds


class BasicChunkerImpl(base_chunker.BaseChunker):
    """
    A simple chunker that does not allow waiting for chunks to be received, but will process members
    and presences received with the given fabric's state registry.
    """

    __slots__ = ("logger", "fabric", "queues", "shard_chunkers")

    def __init__(self, fabric_obj: fabric.Fabric, presences: bool = True) -> None:
        self.fabric = fabric_obj
        self.logger = loggers.get_named_logger(self)
        self.queues: typing.Dict[int, asyncio.Queue] = {}
        self.shard_chunkers: typing.Dict[int, asyncio.Task] = {}

    async def load_members_for(
        self,
        guild_obj: guilds.Guild,
        *guild_objs: guilds.Guild,
        limit: int = 0,
        presences: bool = True,
        query: type_hints.Nullable[str] = None,
        user_ids: type_hints.Nullable[typing.Sequence[int]] = None,
    ) -> None:
        kwargs = {"presences": presences}
        if user_ids:
            if query or limit:
                raise RuntimeError("you may not specify both a query/limit and user_ids when requesting member chunks")
            kwargs["user_ids"] = list(map(str, user_ids))
        else:
            kwargs["query"] = query if query else ""
            kwargs["limit"] = limit

        for guild in (guild_obj, *guild_objs):
            shard_id = guild.shard_id
            if shard_id not in self.queues:
                self.queues[shard_id] = asyncio.Queue()

            await self.queues[shard_id].put([guild.id, kwargs])

            if shard_id not in self.shard_chunkers:
                task = asyncio.create_task(self._do_chunk_for_shard(shard_id))
                self.shard_chunkers[shard_id] = task

    async def _do_chunk_for_shard(self, shard_id: int) -> None:
        with ratelimits.WindowedBurstRateLimiter(f"chunking guilds on shard {shard_id}", 60, 60) as limit:
            while not self.queues[shard_id].empty():
                guild_id, request_kwargs = self.queues[shard_id].get_nowait()
                await limit.acquire()
                await self.fabric.gateways[shard_id].request_guild_members(guild_id, **request_kwargs)

            del self.shard_chunkers[shard_id]

    async def handle_next_chunk(
        self, chunk_payload: hikari.internal_utilities.type_hints.JSONObject, shard_id: int
    ) -> None:
        guild_id = int(chunk_payload["guild_id"])
        guild_obj = self.fabric.state_registry.get_guild_by_id(guild_id)

        if guild_obj is None:
            self.logger.warning("ignoring members chunk for unknown guild %s", guild_id)
            return

        members = chunk_payload["members"]
        presences = chunk_payload.get("presences", containers.EMPTY_SEQUENCE)

        # Dealloc presences sequence and make a lookup table instead.
        # noinspection PyTypeChecker
        presences = {int(presence_payload["user"]["id"]): presence_payload for presence_payload in presences}

        self.logger.info("received a chunk of %s members for guild %s from shard %s", len(members), guild_id, shard_id)

        for member_payload in members:
            member_obj = self.fabric.state_registry.parse_member(member_payload, guild_obj)
            presence_payload = presences.get(member_obj.id)
            if presence_payload is not None:
                self.fabric.state_registry.parse_presence(member_obj, presence_payload)

    def close(self) -> None:
        while self.shard_chunkers:
            _, future = self.shard_chunkers.popitem()
            future.cancel()
