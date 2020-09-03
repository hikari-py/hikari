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

__all__: typing.Final[typing.List[str]] = ["GuildChunker", "RequestInformation"]

import abc
import typing

from hikari import undefined

if typing.TYPE_CHECKING:
    import datetime

    from hikari import guilds
    from hikari import snowflakes
    from hikari import users as users_
    from hikari.api import shard as gateway_shard
    from hikari.events import shard_events
    from hikari.utilities import event_stream


class RequestInformation(typing.Protocol):
    """Information about a member request that's being tracked.

    This protocol defines the fields that should be exported by a `GuildChunker`
    implementation when getting the tracked information about a request.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def average_chunk_size(self) -> typing.Optional[int]:
        """Average amount of members that are being received per chunk.

        Returns
        -------
        typing.Optional[builtins.int]
            The `builtins.int` average size of each chunk for this request
            or `builtins.None` if we haven't received a response to pull
            information from yet.
        """

    @property
    def chunk_count(self) -> typing.Optional[int]:
        """Amount of chunks that are expected for this request.

        Returns
        -------
        typing.Optional[builtins.int]
            The `builtins.int` count of how many chunk events should be received
            for this request or `builtins.None` if we haven't received a
            response to pull information from yet.
        """

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        """Snowflake ID of the guild this chunk request is for.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the guild this request is for.
        """

    @property
    def is_complete(self) -> bool:
        """Whether this chunk request is finished or not.

        A chunk request may be considered finished after all chunks have been
        received or after it's timed out.

        Returns
        -------
        builtins.bool
            Whether this chunk request is considered to be finished or not yet.
        """

    @property
    def last_received(self) -> typing.Optional[datetime.datetime]:
        """Datetime of when we last received a chunk for this event.

        Returns
        -------
        typing.Optional[datetime.datetime]
            A datetime object of when we last received a chunk event for this
            request or `builtins.None` if we haven't received any chunk events
            in response to this request yet.
        """

    @property
    def missing_chunk_indexes(self) -> typing.Optional[typing.Sequence[int]]:
        """Sequence of the indexes of chunks we haven't received yet.

        Returns
        -------
        typing.Optional[typing.Sequence[builtins.int]]
            A sequence of `builtins.int` indexes of the chunk events we haven't
            received for this request or `builtins.None` if we haven't received
            a response to pull information from yet.
        """

    @property
    def nonce(self) -> str:
        """Automatically generated unique identifier of the this chunk's event.

        Returns
        -------
        builtins.str
            The unique nonce that was generated for this request.
        """

    @property
    def not_found_ids(self) -> typing.Sequence[snowflakes.Snowflake]:
        """Sequence of the snowflakes that were requested but not found.

        !!! note
            If no IDs were requested then this will be empty.

        typing.Sequence[hikari.snowflakes.Snowflake]
            A sequence of the snowflake IDs that were explicitly requested but
            weren't found.
        """

    @property
    def received_chunks(self) -> int:
        """Count of how many chunks have been received so far.

        Returns
        -------
        builtins.int
            The `builtins.int` count of how many chunks events we've received in
            response to this request so far.
        """


class GuildChunker(abc.ABC):
    """Component specialization that is used to manage guild chunking."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
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
        """Request for a guild chunk.

        Parameters
        ----------
        guild : hikari.guilds.Guild
            The guild to request chunk for.
        timeout : typing.Union[builtins.int, builtins.float, builtins.None]
            The maximum amount of time the returned stream should spend waiting
            for the next chunk event to be received before ending the iteration.
            If `builtins.None` then this will never timeout between events.
        limit : typing.Optional[builtins.int]
            The limit for how many events the streamer should queue before
            dropping extra received events. Leave as `builtins.None` for this to
            be unlimited.
        include_presences : hikari.undefined.UndefinedOr[builtins.bool]
            If specified, whether to request presences.
        query : builtins.str
            If not `""`, request the members which username starts with the string.
        query_limit : builtins.int
            Maximum number of members to send matching the query.
        users : hikari.undefined.UndefinedOr[typing.Sequence[hikari.snowflakes.SnowflakeishOr[hikari.users.User]]]
            If specified, the users to request for.

        !!! note
            To request the full list of members, set `query` to `""` (empty
            string) and `limit` to `0`.

        !!! note
            The chunk request will not be sent off until the returned stream is
            opened.

        !!! warning
            Validation errors like `builtins.ValueError` and
            `hikari.errors.MissingIntentError` will be delayed until you open
            the returned stream.

        Returns
        -------
        hikari.utilities.event_stream.Streamer[hikari.events.shard_events.MemberChunkEvent]
            A stream of chunk events for the generated request.
        """

    @abc.abstractmethod
    async def get_request_status(self, nonce: str, /) -> typing.Optional[RequestInformation]:
        """Return the status of a request.

        Parameters
        ----------
        nonce : str
            The unique identifier for the tracked request to get.

        Returns
        -------
        typing.Optional[RequestInformation]
            Information about the request if found, else `builtins.None`.
        """

    @abc.abstractmethod
    async def list_requests_for_shard(
        self, shard: typing.Union[gateway_shard.GatewayShard, int], /
    ) -> typing.Sequence[RequestInformation]:
        """List the statuses of requests made for a specific shard.

        Parameters
        ----------
        shard : typing.Union[hikari.api.shard.GatewayShard, builtins.int]
            The object or ID of the shard to get the tracked requests for.

        Returns
        -------
        typing.Sequence[RequestInformation]
            A sequence of data objects of information about the tracked requests
            for the given shard.
        """

    @abc.abstractmethod
    async def list_requests_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.GatewayGuild], /
    ) -> typing.Sequence[RequestInformation]:
        """List the statuses of requests made for a specific guild.

        Parameters
        ----------
        guild: hikari.snowflakes.SnowflakeishOr[hikari.guilds.GatewayGuild]
            The object or ID of the guild to get the tracked requests for.

        Returns
        -------
        typing.Sequence[RequestInformation]
            A sequence of data objects of information about the tracked requests
            for the given guild.
        """

    @abc.abstractmethod
    async def consume_chunk_event(self, event: shard_events.MemberChunkEvent, /) -> None:
        """Listen to chunk events.

        Parameters
        ----------
        event : hikari.events.shard_events.MemberChunkEvent
            The object of the chunk event that's being consumed.
        """

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

        !!! note
            For the chunker to track a request the request may need to be made
            using this method rather than using
            `hikari.api.shard.GatewayShard.request_guild_members`.

        Parameters
        ----------
        guild : hikari.guilds.Guild
            The guild to request chunk for.
        include_presences : hikari.undefined.UndefinedOr[builtins.bool]
            If specified, whether to request presences.
        query : builtins.str
            If not `""`, request the members which username starts with the string.
        limit : builtins.int
            Maximum number of members to send matching the query.
        users : hikari.undefined.UndefinedOr[typing.Sequence[hikari.snowflakes.SnowflakeishOr[hikari.users.User]]]
            If specified, the users to request for.

        !!! note
            To request the full list of members, set `query` to `""` (empty
            string) and `limit` to `0`.

        Returns
        -------
        builtins.str
            The generated unique nonce used for tracking this request.

        Raises
        ------
        ValueError
            When trying to specify `users` with `query`/`limit`, if `limit` is not between
            0 and 100, both inclusive or if `users` length is over 100.
        hikari.errors.MissingIntentError
            When trying to request presences without the `GUILD_MEMBERS` or when trying to
            request the full list of members without `GUILD_PRESENCES`.
        """

    async def close(self) -> None:
        """Close the guild chunker."""
