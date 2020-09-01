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

__all__: typing.Final[typing.List[str]] = ["StatelessGuildChunkerImpl"]

import typing

from hikari import undefined
from hikari.api import chunker
from hikari.utilities import event_stream

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import snowflakes
    from hikari import users as users_
    from hikari.api import shard as gateway_shard
    from hikari.events import shard_events


class _EmptyStream(event_stream.Streamer["shard_events.MemberChunkEvent"]):
    """An empty stream implementation used by the stateless chunker."""

    async def close(self) -> None:
        return None

    async def open(self) -> None:
        return None

    async def __anext__(self) -> typing.NoReturn:
        raise StopAsyncIteration


class StatelessGuildChunkerImpl(chunker.GuildChunker):
    """Stateless guild chunker.

    A stateless guild chunker implementation that implements dummy operations
    for each of the required attributes of a functional guild chunker
    implementation. Any methods will always raise `builtins.NotImplemented`
    when being invoked.
    """

    __slots__: typing.Sequence[str] = ()

    def fetch_members_for_guild(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.GatewayGuild],
        *,
        timeout: typing.Union[int, float, None],
        limit: typing.Optional[int] = None,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        query_limit: int = 0,
        query: str = "",
        users: undefined.UndefinedOr[typing.Sequence[snowflakes.SnowflakeishOr[users_.User]]] = undefined.UNDEFINED,
    ) -> event_stream.Streamer[shard_events.MemberChunkEvent]:
        return _EmptyStream()

    async def get_request_status(self, nonce: str, /) -> typing.Optional[chunker.RequestInformation]:
        return None

    async def list_requests_for_shard(
        self, shard: typing.Union[gateway_shard.GatewayShard, int], /
    ) -> typing.Sequence[chunker.RequestInformation]:
        return ()

    async def list_requests_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.GatewayGuild], /
    ) -> typing.Sequence[chunker.RequestInformation]:
        return ()

    async def consume_chunk_event(self, event: shard_events.MemberChunkEvent, /) -> typing.NoReturn:
        raise NotImplementedError("This application is stateless, guild chunking operations are not implemented.")

    async def request_guild_members(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.GatewayGuild],
        /,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        limit: int = 0,
        query: str = "",
        users: undefined.UndefinedOr[typing.Sequence[snowflakes.SnowflakeishOr[users_.User]]] = undefined.UNDEFINED,
    ) -> typing.NoReturn:
        raise NotImplementedError("This application is stateless, guild chunking operations are not implemented.")

    async def close(self) -> None:
        return None
