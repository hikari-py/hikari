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
"""Events that fire when channels are modified.

This does not include message events, nor reaction events.
"""

from __future__ import annotations

__all__: typing.List[str] = [
    "ChannelEvent",
    "GuildChannelEvent",
    "DMChannelEvent",
    "GuildChannelCreateEvent",
    "GuildChannelUpdateEvent",
    "GuildChannelDeleteEvent",
    "PinsUpdateEvent",
    "GuildPinsUpdateEvent",
    "DMPinsUpdateEvent",
    "InviteCreateEvent",
    "InviteDeleteEvent",
    "WebhookUpdateEvent",
]

import abc
import typing

import attr

from hikari import channels
from hikari import intents
from hikari import traits
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    import datetime

    from hikari import guilds
    from hikari import invites
    from hikari import messages
    from hikari import snowflakes
    from hikari import webhooks
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(intents.Intents.GUILDS, intents.Intents.DM_MESSAGES)
class ChannelEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any channel-bound event in guilds or private messages."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def channel_id(self) -> snowflakes.Snowflake:
        """ID of the channel the event relates to.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the channel this event relates to.
        """

    @abc.abstractmethod
    async def fetch_channel(self) -> channels.PartialChannel:
        """Perform an API call to fetch the details about this channel.

        !!! note
            For `GuildChannelDeleteEvent` events, this will always raise
            an exception, since the channel will have already been removed.

        Returns
        -------
        hikari.channels.PartialChannel
            A derivative of `hikari.channels.PartialChannel`. The actual
            type will vary depending on the type of channel this event
            concerns.

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


@base_events.requires_intents(intents.Intents.GUILDS)
class GuildChannelEvent(ChannelEvent, abc.ABC):
    """Event base for any channel-bound event in guilds."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflakes.Snowflake:
        """ID of the guild that this event relates to.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the guild that relates to this event.
        """

    def get_guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the cached guild that this event relates to, if known.

        If not, return `builtins.None`.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The gateway guild this event relates to, if known. Otherwise
            this will return `builtins.None`.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_available_guild(self.guild_id) or self.app.cache.get_unavailable_guild(self.guild_id)

    async def fetch_guild(self) -> guilds.RESTGuild:
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
        return await self.app.rest.fetch_guild(self.guild_id)

    def get_channel(self) -> typing.Optional[channels.GuildChannel]:
        """Get the cached channel that this event relates to, if known.

        If not, return `builtins.None`.

        Returns
        -------
        typing.Optional[hikari.channels.GuildChannel]
            The cached channel this event relates to. If not known, this
            will return `builtins.None` instead.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_guild_channel(self.channel_id)

    async def fetch_channel(self) -> channels.GuildChannel:
        """Perform an API call to fetch the details about this channel.

        !!! note
            For `GuildChannelDeleteEvent` events, this will always raise
            an exception, since the channel will have already been removed.

        Returns
        -------
        hikari.channels.GuildChannel
            A derivative of `hikari.channels.GuildChannel`. The actual
            type will vary depending on the type of channel this event
            concerns.

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
        assert isinstance(channel, channels.GuildChannel)
        return channel


class DMChannelEvent(ChannelEvent, abc.ABC):
    """Event base for any channel-bound event in private messages."""

    __slots__: typing.Sequence[str] = ()

    async def fetch_channel(self) -> channels.PrivateChannel:
        """Perform an API call to fetch the details about this channel.

        !!! note
            For `GuildChannelDeleteEvent` events, this will always raise
            an exception, since the channel will have already been removed.

        Returns
        -------
        hikari.channels.PrivateChannel
            A derivative of `hikari.channels.PrivateChannel`. The actual
            type will vary depending on the type of channel this event
            concerns.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `VIEW_CHANNEL` permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
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
        assert isinstance(channel, channels.PrivateChannel)
        return channel


@base_events.requires_intents(intents.Intents.GUILDS)
@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class GuildChannelCreateEvent(GuildChannelEvent):
    """Event fired when a guild channel is created."""

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel: channels.GuildChannel = attr.field(repr=True)
    """Guild channel that this event represents.

    Returns
    -------
    hikari.channels.GuildChannel
        The guild channel that was created.
    """

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.channel.app

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ChannelEvent>>.
        return self.channel.id

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildChannelEvent>>.
        return self.channel.guild_id


@base_events.requires_intents(intents.Intents.GUILDS)
@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class GuildChannelUpdateEvent(GuildChannelEvent):
    """Event fired when a guild channel is edited."""

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    old_channel: typing.Optional[channels.GuildChannel] = attr.field(repr=True)
    """The old guild channel object.

    This will be `builtins.None` if the channel missing from the cache.
    """

    channel: channels.GuildChannel = attr.field(repr=True)
    """Guild channel that this event represents.

    Returns
    -------
    hikari.channels.GuildChannel
        The guild channel that was updated.
    """

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.channel.app

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ChannelEvent>>.
        return self.channel.id

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildChannelEvent>>.
        return self.channel.guild_id


@base_events.requires_intents(intents.Intents.GUILDS)
@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class GuildChannelDeleteEvent(GuildChannelEvent):
    """Event fired when a guild channel is deleted."""

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel: channels.GuildChannel = attr.field(repr=True)
    """Guild channel that this event represents.

    Returns
    -------
    hikari.channels.GuildChannel
        The guild channel that was deleted.
    """

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.channel.app

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ChannelEvent>>.
        return self.channel.id

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildChannelEvent>>.
        return self.channel.guild_id

    if typing.TYPE_CHECKING:
        # Channel will never be found.
        async def fetch_channel(self) -> typing.NoReturn:
            ...


@base_events.requires_intents(intents.Intents.DM_MESSAGES, intents.Intents.GUILDS)
class PinsUpdateEvent(ChannelEvent, abc.ABC):
    """Base event fired when a message is pinned/unpinned in a channel."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def last_pin_timestamp(self) -> typing.Optional[datetime.datetime]:
        """Datetime of when the most recent message was pinned in the channel.

        Will be `builtins.None` if nothing is pinned or the information is
        unavailable.

        Returns
        -------
        typing.Optional[datetime.datetime]
            The datetime of the most recent pinned message in the channel,
            or `builtins.None` if no pins are available.
        """

    @abc.abstractmethod
    async def fetch_channel(self) -> channels.TextableChannel:
        """Perform an API call to fetch the details about this channel.

        Returns
        -------
        hikari.channels.TextableChannel
            A derivative of `hikari.channels.TextableChannel`. The actual
            type will vary depending on the type of channel this event
            concerns.
        """

    async def fetch_pins(self) -> typing.Sequence[messages.Message]:
        """Perform an API call to fetch the pinned messages in this channel.

        Returns
        -------
        typing.Sequence[hikari.messages.Message]
            The pinned messages in this channel.
        """
        return await self.app.rest.fetch_pins(self.channel_id)


@base_events.requires_intents(intents.Intents.GUILDS)
@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class GuildPinsUpdateEvent(PinsUpdateEvent, GuildChannelEvent):
    """Event fired when a message is pinned/unpinned in a guild channel."""

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ChannelEvent>>.

    guild_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from GuildChannelEvent>>.

    last_pin_timestamp: typing.Optional[datetime.datetime] = attr.field(repr=True)
    # <<inherited docstring from ChannelPinsUpdateEvent>>.

    def get_channel(self) -> typing.Optional[channels.TextableGuildChannel]:
        """Get the cached channel that this event relates to, if known.

        If not, return `builtins.None`.

        Returns
        -------
        typing.Optional[hikari.channels.TextableGuildChannel]
            The cached channel this event relates to. If not known, this
            will return `builtins.None` instead.
        """
        channel = super().get_channel()
        assert channel is None or isinstance(channel, channels.TextableGuildChannel)
        return channel

    async def fetch_channel(self) -> channels.TextableGuildChannel:
        """Perform an API call to fetch the details about this channel.

        Returns
        -------
        hikari.channels.TextableGuildChannel
            A derivative of `hikari.channels.TextableGuildChannel`. The actual
            type will vary depending on the type of channel this event
            concerns.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `VIEW_CHANNEL` permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
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
        assert isinstance(channel, channels.GuildTextChannel)
        return channel


@base_events.requires_intents(intents.Intents.DM_MESSAGES)
@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class DMPinsUpdateEvent(PinsUpdateEvent, DMChannelEvent):
    """Event fired when a message is pinned/unpinned in a private channel."""

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ChannelEvent>>.

    last_pin_timestamp: typing.Optional[datetime.datetime] = attr.field(repr=True)
    # <<inherited docstring from ChannelPinsUpdateEvent>>.

    async def fetch_channel(self) -> channels.DMChannel:
        """Perform an API call to fetch the details about this channel.

        Returns
        -------
        hikari.channels.DMChannel
            A derivative of `hikari.channels.DMChannel`. The actual
            type will vary depending on the type of channel this event
            concerns.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
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
        assert isinstance(channel, channels.DMChannel)
        return channel


@base_events.requires_intents(intents.Intents.GUILD_INVITES)
class InviteEvent(GuildChannelEvent, abc.ABC):
    """Base event type for guild invite updates."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def code(self) -> str:
        """Code that is used in the URL for the invite.

        Returns
        -------
        builtins.str
            The invite code.
        """

    async def fetch_invite(self) -> invites.Invite:
        """Perform an API call to retrieve an up-to-date image of this invite.

        Returns
        -------
        hikari.invites.Invite
            The invite object.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the invite is not found.
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
        return await self.app.rest.fetch_invite(self.code)


@base_events.requires_intents(intents.Intents.GUILD_INVITES)
@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class InviteCreateEvent(InviteEvent):
    """Event fired when an invite is created in a channel."""

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    invite: invites.InviteWithMetadata = attr.field()
    """Invite that was created.

    Returns
    -------
    hikari.invites.InviteWithMetadata
        The created invite object.
    """

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.invite.app

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ChannelEvent>>.
        return self.invite.channel_id

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildChannelEvent>>.
        # This will never be None for guild channel invites.
        assert self.invite.guild_id is not None
        return self.invite.guild_id

    @property
    def code(self) -> str:
        # <<inherited docstring from InviteEvent>>.
        return self.invite.code


@base_events.requires_intents(intents.Intents.GUILD_INVITES)
@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class InviteDeleteEvent(InviteEvent):
    """Event fired when an invite is deleted from a channel."""

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ChannelEvent>>.

    guild_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from GuildChannelEvent>>.

    code: str = attr.field()
    # <<inherited docstring from InviteEvent>>.

    old_invite: typing.Optional[invites.InviteWithMetadata] = attr.field()
    """Object of the old cached invite.

    This will be `builtins.None` if the invite is missing from the cache.
    """

    if typing.TYPE_CHECKING:
        # Invite will never be found.
        async def fetch_invite(self) -> typing.NoReturn:
            ...


@base_events.requires_intents(intents.Intents.GUILD_WEBHOOKS)
@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class WebhookUpdateEvent(GuildChannelEvent):
    """Event fired when a webhook is created/updated/deleted in a channel.

    Unfortunately, Discord does not provide any information on what webhook
    actually changed, nor specifically whether it was created/updated/deleted,
    so this event is pretty useless unless you keep track of the webhooks in
    the channel manually beforehand.
    """

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ChannelEvent>>.

    guild_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from GuildChannelEvent>>.

    async def fetch_channel_webhooks(self) -> typing.Sequence[webhooks.PartialWebhook]:
        """Perform an API call to fetch the webhooks for this channel.

        Returns
        -------
        typing.Sequence[hikari.webhooks.PartialWebhook]
            The webhooks in this channel.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_WEBHOOKS` permission.
        hikari.errors.NotFoundError
            If the channel is not found.
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
        return await self.app.rest.fetch_channel_webhooks(self.channel_id)

    async def fetch_guild_webhooks(self) -> typing.Sequence[webhooks.PartialWebhook]:
        """Perform an API call to fetch the webhooks for this guild.

        Returns
        -------
        typing.Sequence[hikari.webhooks.PartialWebhook]
            The webhooks in this guild.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_WEBHOOKS` permission.
        hikari.errors.NotFoundError
            If the guild is not found.
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
        return await self.app.rest.fetch_guild_webhooks(self.guild_id)
