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
"""Component that provides the ability manage guild chunking."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["GuildChunker"]

import abc
import typing

from hikari import undefined

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import iterators
    from hikari import snowflakes
    from hikari import users as users_
    from hikari.events import shard_events


class ChunkInformation(typing.Protocol):
    """Information about a member request that's being tracked."""

    @property
    def average_chunk_size(self) -> typing.Optional[int]:
        """Average amount of members that are being received per chunk."""

    @property
    def chunk_count(self) -> typing.Optional[int]:
        """Amount of chunks that are expected for this request."""

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        """Snowflake ID of the guild this chunk request is for."""

    @property
    def is_complete(self) -> bool:
        """Whether this chunk event is finished or not.

        A chunk event may be considered finished after all chunks have been received
        or after it's timed out.
        """

    @property
    def last_received(self) -> typing.Optional[int]:
        """Monotonic time of when we last received a chunk for this event in ms."""

    @property
    def missing_chunks(self) -> typing.Optional[typing.Sequence[int]]:
        """Sequence of the indexes of chunks we haven't received yet.

        If this is `builtins.None` then we haven't received the initial chunk.
        """

    @property
    def nonce(self) -> str:
        """Automatically generated unique identifier of the this chunk's event."""

    @property
    def not_found(self) -> typing.Sequence[snowflakes.Snowflake]:
        """Sequence of the snowflakes that were request in this event that weren't found."""

    @property
    def received_chunks(self) -> int:
        """Count of how many chunks have been received so far."""


class GuildChunker(abc.ABC):
    """Component specialization that is used to manage guild chunking."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def fetch_members_for_guild(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.GatewayGuild],
        *,
        timeout: int,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        limit: int = 0,
        query: str = "",
        users: undefined.UndefinedOr[typing.Sequence[snowflakes.SnowflakeishOr[users_.User]]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[shard_events.MemberChunkEvent]:
        ...

    @abc.abstractmethod
    async def get_chunk_status(self, nonce: str) -> typing.Optional[ChunkInformation]:
        ...

    @abc.abstractmethod
    async def list_chunk_statuses_for_shard(self, shard_id: int) -> typing.Sequence[ChunkInformation]:
        ...

    @abc.abstractmethod
    async def list_chunk_statuses_for_guild(self, guild_id: snowflakes.Snowflake) -> typing.Sequence[ChunkInformation]:
        ...

    @abc.abstractmethod
    async def on_chunk_event(self, event: shard_events.MemberChunkEvent, /) -> None:
        ...

    @abc.abstractmethod
    async def request_guild_members(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.GatewayGuild],
        /,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        limit: int = 0,
        query: str = "",
        users: undefined.UndefinedOr[typing.Sequence[snowflakes.SnowflakeishOr[users_.User]]] = undefined.UNDEFINED,
    ) -> str:
        """Request for a guild chunk.

        Parameters
        ----------
        guild: hikari.guilds.Guild
            The guild to request chunk for.
        """

    async def close(self) -> None:
        """Close the guild chunker."""
