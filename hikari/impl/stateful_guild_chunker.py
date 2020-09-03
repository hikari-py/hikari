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

__all__: typing.Final[typing.List[str]] = ["StatefulGuildChunkerImpl", "ChunkStream"]

import asyncio
import base64
import copy
import random
import time
import typing

import attr

from hikari import intents as intents_
from hikari import snowflakes
from hikari import undefined
from hikari.api import chunker
from hikari.events import shard_events
from hikari.utilities import attr_extensions
from hikari.utilities import date
from hikari.utilities import event_stream
from hikari.utilities import mapping

if typing.TYPE_CHECKING:
    import datetime

    from hikari import guilds
    from hikari import traits
    from hikari import users as users_
    from hikari.api import shard as gateway_shard


EXPIRY_TIME: typing.Final[int] = 5000
"""How long a chunk event should wait until it's considered expired in miliseconds."""


def _random_nonce() -> str:
    head = time.perf_counter_ns().to_bytes(8, "big")
    tail = random.getrandbits(92).to_bytes(12, "big")
    return base64.b64encode(head + tail).decode("ascii")


class ChunkStream(event_stream.EventStream[shard_events.MemberChunkEvent]):
    """A specialised event stream used for triggering and streaming chunk events.

    See Also
    --------
    Event Stream: `hikari.utilities.event_stream.EventStream`
    """

    __slots__: typing.Sequence[str] = (
        "_guild_id",
        "_include_presences",
        "_limit",
        "_missing_chunks",
        "_nonce",
        "_query",
        "_users",
    )

    def __init__(
        self,
        app: traits.BotAware,
        guild_id: snowflakes.Snowflake,
        *,
        timeout: typing.Union[int, float, None],
        limit: typing.Optional[int] = None,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        query_limit: int = 0,
        query: str = "",
        users: undefined.UndefinedOr[typing.Sequence[snowflakes.SnowflakeishOr[users_.User]]] = undefined.UNDEFINED,
    ) -> None:
        super().__init__(app=app, event_type=shard_events.MemberChunkEvent, limit=limit, timeout=timeout)
        self._guild_id = guild_id
        self._include_presences = include_presences
        self._limit = query_limit
        self._missing_chunks: typing.Optional[typing.MutableSequence[int]] = None
        self._nonce = date.uuid()
        self._query = query
        self._users = users
        self.filter(lambda event: event.nonce == self._nonce)

    async def _listener(self, event: shard_events.MemberChunkEvent) -> None:
        if not self._filters(event):
            return

        if self._missing_chunks is None:
            self._missing_chunks = list(range(event.chunk_count))

        self._missing_chunks.remove(event.chunk_index)

        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            pass

        if not self._missing_chunks:
            # While it is tempting to just close the stream here, that'd lead to a type error being
            # raised the next time they try to iterate over it.
            assert self._registered_listener is not None
            self._app.dispatcher.unsubscribe(shard_events.MemberChunkEvent, self._registered_listener)

    async def __anext__(self) -> shard_events.MemberChunkEvent:
        if not self._active:
            raise TypeError("stream must be started with `await with` before entering it")

        if self._queue.empty() and not self._missing_chunks and self._missing_chunks is not None:
            raise StopAsyncIteration from None

        try:
            return await asyncio.wait_for(self._queue.get(), timeout=self._timeout)
        except asyncio.TimeoutError:
            raise StopAsyncIteration from None

    async def open(self) -> None:
        # as super().open will possibly flip self.started, we want to have its state when this was originally called.
        started = self._active
        await super().open()

        if not started:
            shard_id = snowflakes.calculate_shard_id(self._app, self._guild_id)
            await self._app.shards[shard_id].request_guild_members(
                guild=self._guild_id,
                include_presences=self._include_presences,
                query=self._query,
                limit=self._limit,
                users=self._users,
                nonce=self._nonce,
            )


@attr.s(init=True, kw_only=True, hash=False, eq=True, slots=True, weakref_slot=False)
class _TrackedRequests:
    """`hikari.api.chunker.RequestInformation` implementation."""

    __slots__: typing.Sequence[str]

    average_chunk_size: typing.Optional[int] = attr.ib(default=None)
    chunk_count: typing.Optional[int] = attr.ib(default=None)
    guild_id: snowflakes.Snowflake = attr.ib()
    last_received: typing.Optional[datetime.datetime] = attr.ib(default=None)
    _mono_last_received: typing.Optional[int] = attr.ib(default=None)
    missing_chunk_indexes: typing.Optional[typing.MutableSequence[int]] = attr.ib(default=None)
    nonce: str = attr.ib()
    not_found_ids: typing.MutableSequence[snowflakes.Snowflake] = attr.ib(factory=list)

    def __copy__(self) -> _TrackedRequests:
        chunks = attr_extensions.copy_attrs(self)
        chunks.missing_chunk_indexes = (
            list(self.missing_chunk_indexes) if self.missing_chunk_indexes is not None else None
        )
        chunks.not_found_ids = list(self.not_found_ids)
        return chunks

    @property
    def is_complete(self) -> bool:
        if self.received_chunks == self.chunk_count:
            return True

        return self._mono_last_received is not None and time.monotonic_ns() - self._mono_last_received > EXPIRY_TIME

    @property
    def received_chunks(self) -> int:
        if self.chunk_count is None or self.missing_chunk_indexes is None:
            return 0

        return self.chunk_count - len(self.missing_chunk_indexes)

    def update(self, event: shard_events.MemberChunkEvent) -> None:
        if self.missing_chunk_indexes is None:
            self.average_chunk_size = len(event.members)
            self.chunk_count = event.chunk_count
            self.missing_chunk_indexes = list(range(event.chunk_count))

        self.not_found_ids.extend(event.not_found)
        self.missing_chunk_indexes.remove(event.chunk_index)
        self._mono_last_received = time.monotonic_ns()
        self.last_received = date.utc_datetime()


class StatefulGuildChunkerImpl(chunker.GuildChunker):
    """Guild chunker implementation.

    Parameters
    ----------
    app : hikari.traits.BotAware
        The object of the bot aware app this is bound to.
    limit : builtins.int
        The maximum amount of requests that this chunker should store information
        about for each shard.
    """

    __slots__: typing.Sequence[str] = ("_app", "_limit", "_tracked")

    def __init__(self, app: traits.BotAware, limit: int = 200) -> None:
        self._app = app
        self._limit = limit
        self._tracked: typing.MutableMapping[int, mapping.CMRIMutableMapping[str, _TrackedRequests]] = {}

    def _default_include_presences(
        self, guild_id: snowflakes.Snowflake, include_presences: undefined.UndefinedOr[bool]
    ) -> bool:
        if include_presences is not undefined.UNDEFINED:
            return include_presences

        shard_id = snowflakes.calculate_shard_id(self._app, guild_id)
        shard = self._app.shards[shard_id]
        return shard.intents is None or bool(shard.intents & intents_.Intents.GUILD_PRESENCES)

    def fetch_members_for_guild(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.GatewayGuild],
        *,
        timeout: typing.Union[int, float, None],
        limit: typing.Optional[int],
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        query_limit: int = 0,
        query: str = "",
        users: undefined.UndefinedOr[typing.Sequence[snowflakes.SnowflakeishOr[users_.User]]] = undefined.UNDEFINED,
    ) -> event_stream.Streamer[shard_events.MemberChunkEvent]:
        guild_id = snowflakes.Snowflake(guild)
        return ChunkStream(
            app=self._app,
            guild_id=guild_id,
            timeout=timeout,
            limit=limit,
            include_presences=self._default_include_presences(guild_id, include_presences),
            query_limit=query_limit,
            query=query,
            users=users,
        )

    async def get_request_status(self, nonce: str, /) -> typing.Optional[chunker.RequestInformation]:
        try:
            shard_id = int(nonce.split(".", 1)[0])
        except ValueError:
            return None
        else:
            return copy.copy(self._tracked[shard_id].get(nonce)) if shard_id in self._tracked else None

    async def list_requests_for_shard(
        self, shard: typing.Union[gateway_shard.GatewayShard, int], /
    ) -> typing.Sequence[chunker.RequestInformation]:
        shard_id = shard if isinstance(shard, int) else shard.id

        if shard_id not in self._tracked:
            return ()

        return tuple(copy.copy(chunk) for chunk in self._tracked[shard_id].copy().values())

    async def list_requests_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.GatewayGuild], /
    ) -> typing.Sequence[chunker.RequestInformation]:
        guild_id = snowflakes.Snowflake(guild)
        shard_id = snowflakes.calculate_shard_id(self._app, guild_id)
        if shard_id not in self._tracked:
            return ()

        return tuple(copy.copy(event) for event in self._tracked[shard_id].values() if event.guild_id == guild_id)

    async def consume_chunk_event(self, event: shard_events.MemberChunkEvent, /) -> None:
        if (
            event.shard.id not in self._tracked
            or event.nonce is None
            or event.nonce not in self._tracked[event.shard.id]
        ):
            return

        self._tracked[event.shard.id][event.nonce].update(event)

    async def request_guild_members(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.GatewayGuild],
        /,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        limit: int = 0,
        query: str = "",
        users: undefined.UndefinedOr[typing.Sequence[snowflakes.SnowflakeishOr[users_.User]]] = undefined.UNDEFINED,
    ) -> str:
        guild_id = snowflakes.Snowflake(guild)
        shard_id = snowflakes.calculate_shard_id(self._app, guild_id)
        nonce = f"{shard_id}.{_random_nonce()}"
        if shard_id not in self._tracked:
            self._tracked[shard_id] = mapping.CMRIMutableMapping(limit=self._limit)

        tracker = _TrackedRequests(guild_id=guild_id, nonce=nonce)
        self._tracked[shard_id][nonce] = tracker
        await self._app.shards[shard_id].request_guild_members(
            guild=guild_id,
            include_presences=self._default_include_presences(guild_id, include_presences),
            limit=limit,
            nonce=nonce,
            query=query,
            users=users,
        )
        return nonce

    async def close(self) -> None:
        return None
