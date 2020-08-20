# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Basic implementation of a guild chunker."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["StatefulGuildChunkerImpl"]

import asyncio
import logging
import typing

from hikari import intents as intents_
from hikari.api import chunker
from hikari.impl import rate_limits

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import traits

_LOGGER = logging.getLogger("hikari.guild_chunker")


class StatefulGuildChunkerImpl(chunker.GuildChunker):
    """Guild chunker implementation."""

    __slots__: typing.Sequence[str] = ("_app", "_presences", "_queues", "_chunkers")

    def __init__(self, app: traits.ShardAware, intents: typing.Optional[intents_.Intents]):
        self._app = app
        self._presences: bool = intents is None or bool(intents & intents_.Intents.GUILD_PRESENCES)
        self._queues: typing.Dict[int, typing.List[int]] = {}
        self._chunkers: typing.Dict[int, asyncio.Task[None]] = {}

    async def request_guild_chunk(self, guild: guilds.GatewayGuild) -> None:
        if (shard_id := guild.shard_id) is not None:
            if shard_id not in self._queues:
                self._queues[shard_id] = []

            self._queues[shard_id].append(guild.id)

            if shard_id not in self._chunkers:
                task = asyncio.create_task(self._request_chunk(shard_id))
                self._chunkers[shard_id] = task
        else:
            raise RuntimeError("Guild did not have sharding information available")

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
                await self._app.shards[shard_id].request_guild_members(guild_id, include_presences=self._presences)

            del self._chunkers[shard_id]

    def close(self) -> None:
        while self._chunkers:
            _, future = self._chunkers.popitem()
            future.cancel()
