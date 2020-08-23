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
import copy
import time
import typing

import attr

from hikari import intents as intents_
from hikari import iterators
from hikari import snowflakes
from hikari import undefined
from hikari.api import chunker
from hikari.events import shard_events
from hikari.utilities import attr_extensions
from hikari.utilities import date
from hikari.utilities import mapping

if typing.TYPE_CHECKING:
    import types

    from hikari import guilds
    from hikari import traits
    from hikari import users
    from hikari.api import shard as gateway_shard


EXPIRY_TIME = 5000
"""How long a chunk event should wait until it's considered expired in miliseconds."""


def _get_shard_id(app: traits.ShardAware, guild_id: snowflakes.Snowflake) -> int:
    return (guild_id >> 22) % app.shard_count


class ChunkStream(iterators.LazyIterator[shard_events.MemberChunkEvent]):
    """A lazy iterator used for requesting guild members and collecting the results."""

    __slots__: typing.Sequence[str] = (
        "_app",
        "_queue",
        "_guild_id",
        "_include_presences",
        "_limit",
        "_missing_chunks",
        "_nonce",
        "_query",
        "_requested",
        "_timeout",
        "_user_ids",
    )

    def __init__(
        self,
        app: traits.BotAware,
        guild_id: snowflakes.Snowflake,
        *,
        timeout: int,
        buffer_limit: int = 0,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        query_limit: int = 0,
        query: str = "",
        user_ids: undefined.UndefinedOr[typing.Sequence[snowflakes.SnowflakeishOr[users.User]]] = undefined.UNDEFINED,
    ) -> None:
        self._app = app
        self._guild_id = guild_id
        self._include_presences = include_presences
        self._limit = query_limit
        self._missing_chunks: typing.Optional[typing.MutableSequence[int]] = None
        self._nonce = date.uuid()
        self._query = query
        self._queue: asyncio.Queue[shard_events.MemberChunkEvent] = asyncio.Queue(buffer_limit)
        self._requested = False
        self._timeout = timeout
        self._user_ids = user_ids

    async def _listen_for_chunks(self, event: shard_events.MemberChunkEvent) -> None:
        if event.nonce != self._nonce:
            return

        if self._missing_chunks is None:
            self._missing_chunks = list(range(event.chunk_count))

        self._missing_chunks.remove(event.chunk_index)

        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            pass

        if not self._missing_chunks:
            self._app.dispatcher.unsubscribe(shard_events.MemberChunkEvent, self._listen_for_chunks)

    async def _request(self) -> None:
        await self._app.shards[_get_shard_id(self._app, self._guild_id)].request_guild_members(
            guild=self._guild_id,
            include_presences=self._include_presences,
            query=self._query,
            limit=self._limit,
            user_ids=self._user_ids,
            nonce=self._nonce,
        )
        self._requested = True

    async def __anext__(self) -> shard_events.MemberChunkEvent:
        if not self._requested:
            raise TypeError("stream must be started with `await with` before entering it")

        if self._queue.empty() and not self._missing_chunks and self._missing_chunks is not None:
            raise StopAsyncIteration from None

        try:
            return await asyncio.wait_for(self._queue.get(), timeout=self._timeout)
        except asyncio.TimeoutError:
            raise StopAsyncIteration from None

    async def __aenter__(self) -> ChunkStream:
        if not self._requested:
            await self.open()

        return self

    def __enter__(self) -> typing.NoReturn:
        # This is async only.
        cls = type(self)
        raise TypeError(f"{cls.__module__}.{cls.__qualname__} is async-only, did you mean 'async with'?") from None

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        self.close()

    async def _await_all(self) -> typing.Sequence[shard_events.MemberChunkEvent]:
        if not self._requested:
            await self.open()

        result = [event async for event in self]
        self.close()
        return result

    def __await__(self) -> typing.Generator[None, None, typing.Sequence[shard_events.MemberChunkEvent]]:
        return self._await_all().__await__()

    def close(self) -> None:
        try:
            self._app.dispatcher.unsubscribe(shard_events.MemberChunkEvent, self._listen_for_chunks)
        except ValueError:
            pass

    async def open(self) -> None:
        await self._request()
        self._app.dispatcher.subscribe(shard_events.MemberChunkEvent, self._listen_for_chunks)


@attr.s(init=True, kw_only=True, hash=False, eq=True, slots=True, weakref_slot=False)
class _TrackedChunks:
    average_chunk_size: typing.Optional[int] = attr.ib(default=None)
    chunk_count: typing.Optional[int] = attr.ib(default=None)
    guild_id: snowflakes.Snowflake = attr.ib()
    last_received: typing.Optional[int] = attr.ib(default=None)
    missing_chunks: typing.Optional[typing.MutableSequence[int]] = attr.ib(default=None)
    nonce: str = attr.ib()
    not_found: typing.MutableSequence[snowflakes.Snowflake] = attr.ib(factory=list)

    def __copy__(self) -> _TrackedChunks:
        chunks = attr_extensions.copy_attrs(self)
        chunks.missing_chunks = list(chunks.missing_chunks) if chunks.missing_chunks is not None else None
        chunks.not_found = list(chunks.not_found)
        return chunks

    @property
    def is_complete(self) -> bool:
        if self.received_chunks == self.chunk_count:
            return True

        return self.last_received is not None and time.monotonic_ns() - self.last_received > EXPIRY_TIME

    @property
    def received_chunks(self) -> int:
        if self.chunk_count is None or self.missing_chunks is None:
            return 0

        return self.chunk_count - len(self.missing_chunks)


class StatefulGuildChunkerImpl(chunker.GuildChunker):
    """Guild chunker implementation."""

    __slots__: typing.Sequence[str] = ("_app", "_tracked")

    def __init__(self, app: traits.BotAware, limit: int = 200) -> None:
        self._app = app
        self._tracked: typing.MutableMapping[int, typing.Dict[str, _TrackedChunks]] = mapping.CMRIMutableMapping(limit)

    def _verify_include_presences(
        self, guild_id: snowflakes.Snowflake, include_presences: undefined.UndefinedOr[bool]
    ) -> undefined.UndefinedOr[bool]:
        shard = self._app.shards[_get_shard_id(self._app, guild_id)]

        if (
            include_presences is False
            or shard.intents is None
            or bool(shard.intents & intents_.Intents.GUILD_PRESENCES)
        ):
            return include_presences

        raise ValueError(f"cannot include presences with current intents declared {shard.intents}") from None

    def fetch_members_for_guild(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.GatewayGuild],
        *,
        timeout: int,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        limit: int = 0,
        query: str = "",
        user_ids: undefined.UndefinedOr[typing.Sequence[snowflakes.SnowflakeishOr[users.User]]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[shard_events.MemberChunkEvent]:
        guild_id = snowflakes.Snowflake(guild)
        return ChunkStream(
            app=self._app,
            guild_id=guild_id,
            timeout=timeout,
            include_presences=self._verify_include_presences(guild_id, include_presences),
            query_limit=limit,
            query=query,
            user_ids=user_ids,
        )

    async def get_chunk_status(self, shard_id: int, nonce: str) -> typing.Optional[chunker.ChunkInformation]:
        return copy.copy(self._tracked[shard_id].get(nonce)) if shard_id in self._tracked else None

    async def list_chunk_statuses_for_shard(
        self, shard: typing.Union[gateway_shard.GatewayShard, int]
    ) -> typing.Sequence[chunker.ChunkInformation]:
        shard_id = shard if isinstance(shard, int) else shard.id

        if shard_id in self._tracked:
            return tuple(copy.copy(chunk) for chunk in tuple(self._tracked[shard_id].values()))

        return ()

    async def list_chunk_statuses_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.GatewayGuild]
    ) -> typing.Sequence[chunker.ChunkInformation]:
        guild_id = snowflakes.Snowflake(guild)
        shard_id = _get_shard_id(self._app, guild_id)
        if shard_id not in self._tracked:
            return ()

        return tuple(copy.copy(event) for event in self._tracked[shard_id].values() if event.guild_id == guild_id)

    async def on_chunk_event(self, event: shard_events.MemberChunkEvent, /) -> None:
        if event.shard.id not in self._tracked or event.nonce not in self._tracked[event.shard.id]:
            return

        event_tracker = self._tracked[event.shard.id][event.nonce]

        if event_tracker.missing_chunks is None:
            event_tracker.average_chunk_size = len(event.members)
            event_tracker.chunk_count = event.chunk_count
            event_tracker.missing_chunks = list(range(event.chunk_count))

        event_tracker.not_found.extend(event.not_found)
        event_tracker.missing_chunks.remove(event.chunk_index)
        event_tracker.last_received = time.monotonic_ns()

    async def request_guild_chunk(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.GatewayGuild],
        /,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        limit: int = 0,
        query: str = "",
        user_ids: undefined.UndefinedOr[typing.Sequence[snowflakes.SnowflakeishOr[users.User]]] = undefined.UNDEFINED,
    ) -> str:
        guild_id = snowflakes.Snowflake(guild)
        shard_id = _get_shard_id(self._app, guild_id)
        nonce = date.uuid()
        if shard_id not in self._tracked:
            self._tracked[shard_id] = {}

        tracker = _TrackedChunks(guild_id=guild_id, nonce=nonce)
        self._tracked[shard_id][nonce] = tracker
        await self._app.shards[shard_id].request_guild_members(
            guild=guild_id,
            include_presences=self._verify_include_presences(guild_id, include_presences),
            limit=limit,
            nonce=nonce,
            query=query,
            user_ids=user_ids,
        )
        return nonce

    async def close(self) -> None:
        return None
