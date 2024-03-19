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
"""Events fired when users begin typing in channels."""
from __future__ import annotations

__all__: typing.Sequence[str] = ("TypingEvent", "GuildTypingEvent", "DMTypingEvent")

import abc
import typing

import attrs

from hikari import channels
from hikari import intents
from hikari import traits
from hikari.api import special_endpoints
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import attrs_extensions

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
        """ID of the channel that this event concerns."""

    @property
    @abc.abstractmethod
    def user_id(self) -> snowflakes.Snowflake:
        """ID of the user who triggered this typing event."""

    @property
    @abc.abstractmethod
    def timestamp(self) -> datetime.datetime:
        """Timestamp of when this typing event started."""

    async def fetch_channel(self) -> channels.TextableChannel:
        """Perform an API call to fetch an up-to-date image of this channel.

        Returns
        -------
        hikari.channels.TextableChannel
            The channel.
        """
        channel = await self.app.rest.fetch_channel(self.channel_id)
        assert isinstance(channel, channels.TextableChannel)
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
@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class GuildTypingEvent(TypingEvent):
    """Event fired when a user starts typing in a guild channel."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from TypingEvent>>.

    timestamp: datetime.datetime = attrs.field(repr=False)
    # <<inherited docstring from TypingEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field()
    """ID of the guild that this event relates to."""

    member: guilds.Member = attrs.field(repr=False)
    """Object of the member who triggered this typing event."""

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.member.app

    @property
    def user_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from TypingEvent>>.
        return self.member.id

    async def fetch_channel(self) -> channels.TextableGuildChannel:
        """Perform an API call to fetch an up-to-date image of this channel.

        Returns
        -------
        hikari.channels.TextableGuildChannel
            The channel.
        """
        channel = await super().fetch_channel()
        assert isinstance(
            channel, channels.TextableGuildChannel
        ), f"expected TextableGuildChannel from API, got {channel}"
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

    async def fetch_member(self) -> guilds.Member:
        """Perform an API call to fetch an up-to-date image of this event's member.

        Returns
        -------
        hikari.guilds.Member
            The member.
        """
        return await self.app.rest.fetch_member(self.guild_id, self.user_id)

    def get_channel(self) -> typing.Optional[channels.TextableGuildChannel]:
        """Get the cached channel object this typing event occurred in.

        Returns
        -------
        typing.Optional[hikari.channels.TextableGuildChannel]
            The channel.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        channel = self.app.cache.get_guild_channel(self.channel_id)
        assert channel is None or isinstance(
            channel, channels.TextableGuildChannel
        ), f"expected TextableGuildChannel from cache, got {channel}"
        return channel

    def get_guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the cached object of the guild this typing event occurred in.

        If the guild is not found then this will return [`None`][].

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The object of the gateway guild if found else [`None`][].
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_available_guild(self.guild_id) or self.app.cache.get_unavailable_guild(self.guild_id)


@base_events.requires_intents(intents.Intents.DM_MESSAGES)
@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class DMTypingEvent(TypingEvent):
    """Event fired when a user starts typing in a guild channel."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from TypingEvent>>.

    user_id: snowflakes.Snowflake = attrs.field(repr=True)
    # <<inherited docstring from TypingEvent>>.

    timestamp: datetime.datetime = attrs.field(repr=False)
    # <<inherited docstring from TypingEvent>>.

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
            If you are missing the [`hikari.permissions.Permissions.VIEW_CHANNEL`][] permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        channel = await super().fetch_channel()
        assert isinstance(channel, channels.DMChannel), f"expected DMChannel from API, got {channel}"
        return channel
