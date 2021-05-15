# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
"""Events fired when users begin typing in channels."""
from __future__ import annotations

__all__: typing.List[str] = [
    "TypingEvent",
    "GuildTypingEvent",
    "DMTypingEvent",
]

import abc
import typing

import attr

from hikari import channels
from hikari import intents
from hikari import traits
from hikari.api import special_endpoints
from hikari.events import base_events
from hikari.events import shard_events

if typing.TYPE_CHECKING:
    import datetime

    from hikari import guilds
    from hikari import snowflakes
    from hikari import users
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_TYPING, intents.Intents.DM_MESSAGE_TYPING)
class TypingEvent(shard_events.ShardEvent, abc.ABC):
    """Base event fired when a user begins typing in a channel."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def channel_id(self) -> snowflakes.Snowflake:
        """ID of the channel that this event concerns.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the channel that this event concerns.
        """

    @property
    @abc.abstractmethod
    def user_id(self) -> snowflakes.Snowflake:
        """ID of the user who triggered this typing event.

        Returns
        -------
        hikari.snowflakes.Snowflake
            ID of the user who is typing.
        """

    @property
    @abc.abstractmethod
    def timestamp(self) -> datetime.datetime:
        """Timestamp of when this typing event started.

        Returns
        -------
        datetime.datetime
            UTC timestamp of when the user started typing.
        """

    @property
    @abc.abstractmethod
    def user(self) -> typing.Optional[users.User]:
        """Get the cached user that is typing, if known.

        Returns
        -------
        typing.Optional[hikari.users.User]
            The user, if known.
        """

    @abc.abstractmethod
    async def fetch_channel(self) -> channels.TextChannel:
        """Perform an API call to fetch an up-to-date image of this channel.

        Returns
        -------
        hikari.channels.TextChannel
            The channel.
        """

    @abc.abstractmethod
    async def fetch_user(self) -> users.User:
        """Perform an API call to fetch an up-to-date image of this user.

        Returns
        -------
        hikari.users.User
            The user.
        """

    def trigger_typing(self) -> special_endpoints.TypingIndicator:
        """Return a typing indicator for this channel that can be awaited.

        Returns
        -------
        hikari.api.special_endpoints.TypingIndicator
            A typing indicator context manager and awaitable to trigger typing
            in a channel with.
        """
        return self.app.rest.trigger_typing(self.channel_id)


@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_TYPING)
@attr.define(frozen=True, kw_only=True, weakref_slot=False)
class GuildTypingEvent(TypingEvent):
    """Event fired when a user starts typing in a guild channel."""

    app: traits.RESTAware = attr.field()
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field()
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from TypingEvent>>.

    timestamp: datetime.datetime = attr.field(repr=False)
    # <<inherited docstring from TypingEvent>>.

    guild_id: snowflakes.Snowflake = attr.field()
    """ID of the guild that this event relates to.

    Returns
    -------
    hikari.snowflakes.Snowflake
        The ID of the guild that relates to this event.
    """

    user: guilds.Member = attr.field(repr=False)
    """Member object of the user who triggered this typing event.

    Unlike on `PrivateTypingEvent` instances, Discord will always send
    this field in any payload.

    Returns
    -------
    hikari.guilds.Member
        Member of the user who triggered this typing event.
    """

    @property
    def channel(self) -> typing.Union[channels.GuildTextChannel, channels.GuildNewsChannel, None]:
        """Get the cached channel object this typing event occurred in.

        Returns
        -------
        typing.Union[hikari.channels.GuildTextChannel, hikari.channels.GuildNewsChannel, builtins.None]
            The channel.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        channel = self.app.cache.get_guild_channel(self.channel_id)
        assert channel is None or isinstance(
            channel, (channels.GuildTextChannel, channels.GuildNewsChannel)
        ), f"expected GuildTextChannel or GuildNewsChannel from cache, got {channel}"
        return channel

    @property
    def guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the cached object of the guild this typing event occurred in.

        If the guild is not found then this will return `builtins.None`.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The object of the gateway guild if found else `builtins.None`.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_available_guild(self.guild_id) or self.app.cache.get_unavailable_guild(self.guild_id)

    @property
    def user_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from TypingEvent>>.
        return self.user.id

    async def fetch_channel(self) -> typing.Union[channels.GuildTextChannel, channels.GuildNewsChannel]:
        """Perform an API call to fetch an up-to-date image of this channel.

        Returns
        -------
        typing.Union[hikari.channels.GuildTextChannel, hikari.channels.GuildNewsChannel]
            The channel.
        """
        channel = await self.app.rest.fetch_channel(self.channel_id)
        assert isinstance(
            channel, (channels.GuildTextChannel, channels.GuildNewsChannel)
        ), f"expected GuildTextChannel or GuildNewsChannel from API, got {channel}"
        return channel

    async def fetch_guild(self) -> guilds.Guild:
        """Perform an API call to fetch an up-to-date image of this guild.

        Returns
        -------
        hikari.guilds.Guild
            The guild.
        """
        return await self.app.rest.fetch_guild(self.guild_id)

    async def fetch_guild_preview(self) -> guilds.GuildPreview:
        """Perform an API call to fetch an up-to-date preview of this guild.

        Returns
        -------
        hikari.guilds.GuildPreview
            The guild.
        """
        return await self.app.rest.fetch_guild_preview(self.guild_id)

    async def fetch_user(self) -> guilds.Member:
        """Perform an API call to fetch an up-to-date image of this member.

        Returns
        -------
        hikari.guilds.Member
            The member.
        """
        return await self.app.rest.fetch_member(self.guild_id, self.user_id)


@base_events.requires_intents(intents.Intents.DM_MESSAGES)
@attr.define(frozen=True, kw_only=True, weakref_slot=False)
class DMTypingEvent(TypingEvent):
    """Event fired when a user starts typing in a guild channel."""

    app: traits.RESTAware = attr.field()
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field()
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from TypingEvent>>.

    user_id: snowflakes.Snowflake = attr.field(repr=True)
    # <<inherited docstring from TypingEvent>>.

    timestamp: datetime.datetime = attr.field(repr=False)
    # <<inherited docstring from TypingEvent>>.

    @property
    def user(self) -> typing.Optional[users.User]:
        # <<inherited docstring from TypingEvent>>.
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_user(self.user_id)

    async def fetch_channel(self) -> channels.DMChannel:
        """Perform an API call to fetch an up-to-date image of this channel.

        Returns
        -------
        hikari.channels.DMChannel
            The channel.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `READ_MESSAGES` permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        channel = await self.app.rest.fetch_channel(self.channel_id)
        assert isinstance(channel, channels.DMChannel), f"expected DMChannel from API, got {channel}"
        return channel

    async def fetch_user(self) -> users.User:
        """Perform an API call to fetch an up-to-date image of the user.

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
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_user(self.user_id)
