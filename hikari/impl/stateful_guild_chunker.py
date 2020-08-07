# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Basic implementation of a guild chunker."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["StatefulGuildChunkerImpl"]

import asyncio
import logging
import typing

from hikari.api import guild_chunker
from hikari.impl import rate_limits
from hikari.models import intents as intents_

if typing.TYPE_CHECKING:
    from hikari.api import bot
    from hikari.models import guilds

_LOGGER = logging.getLogger("hikari.guild_chunker")


class StatefulGuildChunkerImpl(guild_chunker.IGuildChunkerComponent):
    """Guild chunker implementation."""

    __slots__: typing.Sequence[str] = ("_app", "_presences", "_queues", "_chunkers")

    def __init__(self, app: bot.IBotApp, intents: typing.Optional[intents_.Intent]):
        self._app = app
        self._presences: bool = intents is None or bool(intents & intents_.Intent.GUILD_PRESENCES)
        self._queues: typing.Dict[int, typing.List[int]] = {}
        self._chunkers: typing.Dict[int, asyncio.Task[None]] = {}

    @property
    @typing.final
    def app(self) -> bot.IBotApp:
        return self._app

    async def request_guild_chunk(self, guild: guilds.Guild, shard_id: int) -> None:
        if shard_id not in self._queues:
            self._queues[shard_id] = []

        self._queues[shard_id].append(guild.id)

        if shard_id not in self._chunkers:
            task = asyncio.create_task(self._request_chunk(shard_id))
            self._chunkers[shard_id] = task

    async def _request_chunk(self, shard_id: int) -> None:
        # Since this is not an endpoint but a request, we dont get the ratelimit info
        # to go off from. This will allow 60 requests per 60 seconds, which should be
        # a reasonable ratelimit. This will also leave 60 more requests per 60 seconds
        # for other shard requests if this were to be exausted.
        with rate_limits.WindowedBurstRateLimiter(f"chunking guilds on shard {shard_id}", 60, 60) as limit:
            while len(self._queues[shard_id]) != 0:
                await limit.acquire()
                guild_id = self._queues[shard_id].pop()
                message = "requesting guild members for guild %s on shard %s"
                if self._presences:
                    message = f"{message} with presences"
                _LOGGER.debug(message, guild_id, shard_id)
                await self._app.shards[shard_id].request_guild_members(guild_id, presences=self._presences)

            del self._chunkers[shard_id]

    def close(self) -> None:
        while self._chunkers:
            _, future = self._chunkers.popitem()
            future.cancel()
