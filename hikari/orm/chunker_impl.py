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
"""
Basic implementation of a chunker.
"""
from __future__ import annotations

import itertools
import typing

from hikari.internal_utilities import data_structures
from hikari.internal_utilities import logging_helpers
from hikari.orm import chunker
from hikari.orm import fabric
from hikari.orm.models import guilds


class ChunkerImpl(chunker.IChunker):
    """
    A simple chunker that does not allow waiting for chunks to be received, but will process members
    and presences received with the given fabric's state registry.
    """

    __slots__ = ("logger", "fabric")

    def __init__(self, fabric_obj: fabric.Fabric):
        self.fabric = fabric_obj
        self.logger = logging_helpers.get_named_logger(self)

    def load_members_for(
        self,
        guild_obj: guilds.Guild,
        *guild_objs: guilds.Guild,
        limit: int = 0,
        presences: bool = True,
        query: str = None,
        user_ids: typing.Optional[typing.Sequence[int]] = None,
    ) -> None:
        if user_ids is not None:
            if query is not None:
                raise RuntimeError("you may not specify both a query and user_ids when requesting member chunks")
            user_ids = list(map(str, user_ids))

        # We should request the guild info on the shard the guild is using, so aggregate the guilds by the shard id.
        for shard_id, guild_objs in itertools.groupby((guild_obj, *guild_objs), lambda g: g.shard_id):
            self.fabric.gateways[shard_id].request_guild_members(
                *map(lambda g: str(g.id), guild_objs), limit=limit, presences=presences, query=query, user_ids=user_ids,
            )

    async def handle_next_chunk(self, chunk_payload: data_structures.DiscordObjectT, shard_id: int) -> None:
        guild_id = int(chunk_payload["guild_id"])
        guild_obj = self.fabric.state_registry.get_guild_by_id(guild_id)

        if guild_obj is None:
            self.logger.warning("ignoring members chunk for unknown guild %s", guild_id)
            return

        members = chunk_payload["members"]
        presences = chunk_payload.get("presences", data_structures.EMPTY_SEQUENCE)

        # Dealloc presences sequence and make a lookup table instead.
        # noinspection PyTypeChecker
        presences = {int(presence_payload["user"]["id"]): presence_payload for presence_payload in presences}

        self.logger.info("received a chunk of %s members for guild %s from shard %s", len(members), guild_id, shard_id)

        for member_payload in members:
            member_obj = self.fabric.state_registry.parse_member(member_payload, guild_obj)
            presence_payload = presences.get(member_obj.id)
            if presence_payload is not None:
                self.fabric.state_registry.parse_presence(member_obj, presence_payload)

    async def close(self):
        pass
