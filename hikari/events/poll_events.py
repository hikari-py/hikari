# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
"""Events related to polls."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("PollVoteCreateEvent", "PollVoteDeleteEvent")

import typing

import attrs

from hikari import undefined
from hikari.events import shard_events
from hikari.internal import attrs_extensions

if typing.TYPE_CHECKING:
    from hikari import channels
    from hikari import guilds
    from hikari import snowflakes
    from hikari import traits
    from hikari import users
    from hikari.api import shard as gateway_shard


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class BasePollVoteEvent(shard_events.ShardEvent):
    """Event base for any event that involves a user voting on a poll."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    user_id: snowflakes.Snowflake = attrs.field()
    """ID of the user that added their vote to the poll."""

    channel_id: snowflakes.Snowflake = attrs.field()
    """ID of the channel that the poll is in."""

    message_id: snowflakes.Snowflake = attrs.field()
    """ID of the message that the poll is in."""

    guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = attrs.field()
    """ID of the guild that the poll is in.

    This will be [hikari.undefined.UNDEFINED][] if the poll is in a DM channel.
    """

    answer_id: int = attrs.field()
    """ID of the answer that the user voted for."""

    def get_guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the cached guild that this event relates to, if known.

        If not, return [`None`][].

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The gateway guild this event relates to, if known. Otherwise,
            this will return [`None`][].
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        if isinstance(self.guild_id, undefined.UndefinedType):
            return None

        return self.app.cache.get_available_guild(self.guild_id) or self.app.cache.get_unavailable_guild(self.guild_id)

    async def fetch_guild(self) -> typing.Optional[guilds.RESTGuild]:
        """Perform an API call to fetch the guild that this event relates to.

        Returns
        -------
        hikari.guilds.RESTGuild
            The guild that this event occurred in.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        if isinstance(self.guild_id, undefined.UndefinedType):
            return None

        return await self.app.rest.fetch_guild(self.guild_id)

    def get_channel(self) -> typing.Optional[channels.PermissibleGuildChannel]:
        """Get the cached channel that this event relates to, if known.

        If not, return [`None`][].

        Returns
        -------
        typing.Optional[hikari.channels.GuildChannel]
            The cached channel this event relates to. If not known, this
            will return [`None`][] instead.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_guild_channel(self.channel_id)

    async def fetch_channel(self) -> channels.GuildChannel:
        """Perform an API call to fetch the details about this channel.

        !!! note
            For [`hikari.events.channel_events.GuildChannelDeleteEvent`][] events, this will always raise
            an exception, since the channel will have already been removed.

        Returns
        -------
        hikari.channels.GuildChannel
            A derivative of [`hikari.channels.GuildChannel`][]. The
            actual type will vary depending on the type of channel this event
            concerns.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.VIEW_CHANNEL`][] permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        channel = await self.app.rest.fetch_channel(self.channel_id)
        assert isinstance(channel, channels.GuildChannel)
        return channel

    def get_user(self) -> typing.Optional[users.User]:
        """Get the cached user that is typing, if known.

        Returns
        -------
        typing.Optional[hikari.users.User]
            The user, if known.
        """
        if isinstance(self.app, traits.CacheAware):
            return self.app.cache.get_user(self.user_id)

        return None

    async def fetch_user(self) -> users.User:
        """Perform an API call to fetch an up-to-date image of this user.

        Returns
        -------
        hikari.users.User
            The user.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the user is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_user(self.user_id)


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class PollVoteCreateEvent(BasePollVoteEvent):
    """Event that is fired when a user add their vote to a poll.

    If the poll allows multiple selection, one event will be fired for each vote.
    """


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class PollVoteDeleteEvent(BasePollVoteEvent):
    """Event that is fired when a user remove their vote to a poll.

    If the poll allows multiple selection, one event will be fired for each vote.
    """
