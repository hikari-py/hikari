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
import contextlib
import logging
import typing

from hikari import intents as intents_
from hikari.api import chunker
from hikari.events import lifetime_events
from hikari.events import shard_events
from hikari.impl import rate_limits
from hikari.utilities import date

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import traits

_LOGGER = logging.getLogger("hikari.guild_chunker")


class StatefulGuildChunkerImpl(chunker.GuildChunker):
    """Guild chunker implementation."""

    __slots__: typing.Sequence[str] = (
        "_app",
        "_presences",
        "_queues",
        "_chunkers",
        "_expected_chunks",
        "_dispatch_task",
    )

    def __init__(self, app: traits.BotAware, intents: typing.Optional[intents_.Intents]) -> None:
        self._app = app
        self._presences: bool = intents is None or bool(intents & intents_.Intents.GUILD_PRESENCES)
        self._queues: typing.Dict[int, typing.List[int]] = {}
        self._chunkers: typing.Dict[int, asyncio.Task[None]] = {}
        self._expected_chunks: typing.Dict[str, typing.Tuple[int, int]] = {}
        self._dispatch_task: typing.Optional[asyncio.Task[None]] = None

    async def request_guild_chunk(self, guild: guilds.GatewayGuild) -> None:
        if self._dispatch_task is None:
            self._dispatch_task = asyncio.create_task(self._dispatch_state_ready(), name="dispatch StateReadyEvent")

        if (shard_id := guild.shard_id) is not None:
            if shard_id not in self._queues:
                self._queues[shard_id] = []

            self._queues[shard_id].append(guild.id)

            if shard_id not in self._chunkers:
                task = asyncio.create_task(self._request_chunk(shard_id))
                self._chunkers[shard_id] = task
        else:
            raise RuntimeError("Guild did not have sharding information available")

    async def handle_guild_chunk(self, event: shard_events.MemberChunkEvent) -> None:
        # We need to distinguish events we triggered internally
        # and the ones the user triggered. The `nonce` is how we
        # achive this.
        if event.nonce is None or (info := self._expected_chunks.get(event.nonce)) is None:
            return

        expected = None
        if event.index != info[0]:
            expected = info[0]

        index = event.index + 1
        if expected is not None:
            _LOGGER.warning(
                "received chunk with index %s for guild with ID %s, but expecting index %s. %s chunk(s) lost!",
                index,
                event.guild_id,
                expected,
                index - expected,
            )
        else:
            _LOGGER.debug("received chunk %s/%s for guild with ID %s", index, event.count, event.guild_id)

        if index == event.count:
            del self._expected_chunks[event.nonce]
        else:
            self._expected_chunks[event.nonce] = (index, event.count)

    async def _request_chunk(self, shard_id: int) -> None:
        # Since this is not an endpoint but a request, we dont get the ratelimit info
        # to go off from. This will allow 60 requests per 60 seconds, which should be
        # a reasonable ratelimit. This will also leave 60 more requests per 60 seconds
        # for other shard requests if this were to be exausted.
        with rate_limits.WindowedBurstRateLimiter(f"chunking guilds on shard {shard_id}", 60, 60) as limit:
            while len(self._queues[shard_id]) != 0:
                await limit.acquire()
                guild_id = self._queues[shard_id].pop()
                nonce = date.uuid()
                message = "requesting guild members for guild %s on shard %s"
                if self._presences:
                    message = f"{message} with presences"
                message = f"{message} [nonce: %s]"
                _LOGGER.debug(message, guild_id, shard_id, nonce)

                await self._app.shards[shard_id].request_guild_members(
                    guild_id, include_presences=self._presences, nonce=nonce
                )
                self._expected_chunks[nonce] = (0, 0)

            del self._chunkers[shard_id]

    async def _dispatch_state_ready(self) -> None:
        with contextlib.suppress(asyncio.CancelledError):
            while True:
                try:
                    await self._app.dispatcher.wait_for(shard_events.MemberChunkEvent, timeout=5)
                except asyncio.TimeoutError:
                    if self._expected_chunks:
                        _LOGGER.warning(
                            "no member chunk received in 5 seconds but still expecting for %s guild chunk(s), discarting",
                            len(self._expected_chunks),
                        )
                    else:
                        _LOGGER.debug("no member chunk received in 5 seconds, dispatching StateReadyEvent")

                    await self._app.dispatcher.dispatch(lifetime_events.StateReadyEvent(app=self._app))
                    self._expected_chunks.clear()
                    break

    def close(self) -> None:
        if self._dispatch_task is not None:
            self._dispatch_task.cancel()

        while self._chunkers:
            _, future = self._chunkers.popitem()
            future.cancel()
