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
"""Events that fire when channels are modified.

This does not include message events, nor reaction events.
"""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "ChannelEvent",
    "GuildChannelEvent",
    "PrivateChannelEvent",
    "ChannelCreateEvent",
    "GuildChannelCreateEvent",
    "PrivateChannelCreateEvent",
    "ChannelUpdateEvent",
    "GuildChannelUpdateEvent",
    "PrivateChannelUpdateEvent",
    "ChannelDeleteEvent",
    "GuildChannelDeleteEvent",
    "PrivateChannelDeleteEvent",
    "PinsUpdateEvent",
    "GuildPinsUpdateEvent",
    "PrivatePinsUpdateEvent",
    "InviteCreateEvent",
    "InviteDeleteEvent",
    "WebhookUpdateEvent",
]

import abc
import typing

import attr

from hikari import intents
from hikari import traits
from hikari.events import base_events
from hikari.events import shard_events
from hikari.utilities import attr_extensions

if typing.TYPE_CHECKING:
    import datetime

    from hikari import channels
    from hikari import invites
    from hikari import snowflakes
    from hikari import webhooks
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(intents.Intents.GUILDS, intents.Intents.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ChannelEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any channel-bound event in guilds or private messages."""

    @property
    @abc.abstractmethod
    def channel_id(self) -> snowflakes.Snowflake:
        """ID of the channel the event relates to.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the channel this event relates to.
        """

    async def fetch_channel(self) -> channels.PartialChannel:
        """Perform an API call to fetch the details about this channel.

        !!! note
            For `ChannelDeleteEvent`-derived events, this will always raise
            an exception, since the channel will have already been removed.

        Returns
        -------
        hikari.channels.PartialChannel
            A derivative of `hikari.channels.PartialChannel`. The actual
            type will vary depending on the type of channel this event
            concerns.
        """
        return await self.app.rest.fetch_channel(self.channel_id)


@base_events.requires_intents(intents.Intents.GUILDS)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class GuildChannelEvent(ChannelEvent, abc.ABC):
    """Event base for any channel-bound event in guilds."""

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflakes.Snowflake:
        """ID of the guild that this event relates to.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the guild that relates to this event.
        """

    if typing.TYPE_CHECKING:

        async def fetch_channel(self) -> channels.GuildChannel:
            ...


@attr.s(kw_only=True, slots=True, weakref_slot=False)
class PrivateChannelEvent(ChannelEvent, abc.ABC):
    """Event base for any channel-bound event in private messages."""

    if typing.TYPE_CHECKING:

        async def fetch_channel(self) -> channels.PrivateChannel:
            ...


@base_events.requires_intents(intents.Intents.GUILDS, intents.Intents.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ChannelCreateEvent(ChannelEvent, abc.ABC):
    """Base event for any channel being created."""

    @property
    @abc.abstractmethod
    def channel(self) -> channels.PartialChannel:
        """Channel this event represents.

        Returns
        -------
        hikari.channels.PartialChannel
            The channel that was created.
        """

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ChannelEvent>>.
        return self.channel.id


@base_events.requires_intents(intents.Intents.GUILDS)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class GuildChannelCreateEvent(GuildChannelEvent, ChannelCreateEvent):
    """Event fired when a guild channel is created."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel: channels.GuildChannel = attr.ib(repr=True)
    """Guild channel that this event represents.

    Returns
    -------
    hikari.channels.GuildChannel
        The guild channel that was created.
    """

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildChannelEvent>>.
        return self.channel.guild_id


@base_events.requires_intents(intents.Intents.PRIVATE_MESSAGES)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class PrivateChannelCreateEvent(PrivateChannelEvent, ChannelCreateEvent):
    """Event fired when a private channel is created."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel: channels.PrivateChannel = attr.ib(repr=True)
    """Private channel that this event represents.

    Returns
    -------
    hikari.channels.PrivateChannel
        The guild channel that was created.
    """


@base_events.requires_intents(intents.Intents.GUILDS, intents.Intents.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ChannelUpdateEvent(ChannelEvent, abc.ABC):
    """Base event for any channel being updated."""

    @property
    @abc.abstractmethod
    def channel(self) -> channels.PartialChannel:
        """Channel this event represents.

        Returns
        -------
        hikari.channels.PartialChannel
            The channel that was updated.
        """

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ChannelEvent>>.
        return self.channel.id


@base_events.requires_intents(intents.Intents.GUILDS)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class GuildChannelUpdateEvent(GuildChannelEvent, ChannelUpdateEvent):
    """Event fired when a guild channel is edited."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel: channels.GuildChannel = attr.ib(repr=True)
    """Guild channel that this event represents.

    Returns
    -------
    hikari.channels.GuildChannel
        The guild channel that was updated.
    """

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildChannelEvent>>.
        return self.channel.guild_id


@base_events.requires_intents(intents.Intents.PRIVATE_MESSAGES)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class PrivateChannelUpdateEvent(PrivateChannelEvent, ChannelUpdateEvent):
    """Event fired when a private channel is edited."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel: channels.PrivateChannel = attr.ib(repr=True)
    """Private channel that this event represents.

    Returns
    -------
    hikari.channels.PrivateChannel
        The private channel that was updated.
    """


@base_events.requires_intents(intents.Intents.GUILDS, intents.Intents.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class ChannelDeleteEvent(ChannelEvent, abc.ABC):
    """Base event for any channel being deleted."""

    @property
    @abc.abstractmethod
    def channel(self) -> channels.PartialChannel:
        """Channel this event represents.

        Returns
        -------
        hikari.channels.PartialChannel
            The channel that was deleted.
        """

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ChannelEvent>>.
        return self.channel.id

    if typing.TYPE_CHECKING:
        # Channel will never be found.
        async def fetch_channel(self) -> typing.NoReturn:
            ...


@base_events.requires_intents(intents.Intents.GUILDS)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class GuildChannelDeleteEvent(GuildChannelEvent, ChannelDeleteEvent):
    """Event fired when a guild channel is deleted."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel: channels.GuildChannel = attr.ib(repr=True)
    """Guild channel that this event represents.

    Returns
    -------
    hikari.channels.GuildChannel
        The guild channel that was deleted.
    """

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildChannelEvent>>.
        return self.channel.guild_id

    if typing.TYPE_CHECKING:
        # Channel will never be found.
        async def fetch_channel(self) -> typing.NoReturn:
            ...


# TODO: can this actually ever get fired?
@base_events.requires_intents(intents.Intents.PRIVATE_MESSAGES)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class PrivateChannelDeleteEvent(PrivateChannelEvent, ChannelDeleteEvent):
    """Event fired when a private channel is deleted."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring>>.

    channel: channels.PrivateChannel = attr.ib(repr=True)
    """Private channel that this event represents.

    Returns
    -------
    hikari.channels.PrivateChannel
        The private channel that was deleted.
    """

    if typing.TYPE_CHECKING:
        # Channel will never be found.
        async def fetch_channel(self) -> typing.NoReturn:
            ...


# TODO: find out what private message intents are needed.
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class PinsUpdateEvent(ChannelEvent, abc.ABC):
    """Base event fired when a message is pinned/unpinned in a channel."""

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

    if typing.TYPE_CHECKING:

        async def fetch_channel(self) -> channels.TextChannel:
            ...


@base_events.requires_intents(intents.Intents.GUILDS)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class GuildPinsUpdateEvent(PinsUpdateEvent, GuildChannelEvent):
    """Event fired when a message is pinned/unpinned in a guild channel."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.ib()
    # <<inherited docstring from ChannelEvent>>.

    guild_id: snowflakes.Snowflake = attr.ib()
    # <<inherited docstring from GuildChannelEvent>>.

    last_pin_timestamp: typing.Optional[datetime.datetime] = attr.ib(repr=True)
    # <<inherited docstring from ChannelPinsUpdateEvent>>.

    if typing.TYPE_CHECKING:

        async def fetch_channel(self) -> channels.GuildTextChannel:
            ...


# TODO: This is not documented as having an intent, is this right? The guild version requires GUILDS intent.
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class PrivatePinsUpdateEvent(PinsUpdateEvent, PrivateChannelEvent):
    """Event fired when a message is pinned/unpinned in a private channel."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.ib()
    # <<inherited docstring from ChannelEvent>>.

    last_pin_timestamp: typing.Optional[datetime.datetime] = attr.ib(repr=True)
    # <<inherited docstring from ChannelPinsUpdateEvent>>.

    if typing.TYPE_CHECKING:

        async def fetch_channel(self) -> channels.PrivateTextChannel:
            ...


@base_events.requires_intents(intents.Intents.GUILD_INVITES)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class InviteEvent(GuildChannelEvent, abc.ABC):
    """Base event type for guild invite updates."""

    @property
    @abc.abstractmethod
    def code(self) -> str:
        """Code that is used in the URL for the invite.

        Returns
        -------
        builtins.str
            The invite code.
        """

    if typing.TYPE_CHECKING:

        async def fetch_channel(self) -> channels.GuildTextChannel:
            ...

    async def fetch_invite(self) -> invites.Invite:
        """Perform an API call to retrieve an up-to-date image of this invite.

        Returns
        -------
        hikari.invites.Invite
            The invite object.
        """
        return await self.app.rest.fetch_invite(self.code)


@base_events.requires_intents(intents.Intents.GUILD_INVITES)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class InviteCreateEvent(InviteEvent):
    """Event fired when an invite is created in a channel."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    invite: invites.InviteWithMetadata = attr.ib()
    """Invite that was created.

    Returns
    -------
    hikari.invites.InviteWithMetaData
        The created invite object.
    """

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ChannelEvent>>.
        return self.invite.channel_id

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildChannelEvent>>.
        # This will always be non-None for guild channel invites.
        assert self.invite.guild_id is not None
        return self.invite.guild_id

    @property
    def code(self) -> str:
        # <<inherited docstring from InviteEvent>>.
        return self.invite.code


@base_events.requires_intents(intents.Intents.GUILD_INVITES)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class InviteDeleteEvent(InviteEvent):
    """Event fired when an invite is deleted from a channel."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.ib()
    # <<inherited docstring from ChannelEvent>>.

    guild_id: snowflakes.Snowflake = attr.ib()
    # <<inherited docstring from GuildChannelEvent>>.

    code: str = attr.ib()
    # <<inherited docstring from InviteEvent>>.

    if typing.TYPE_CHECKING:
        # Invite will never be found.
        async def fetch_invite(self) -> typing.NoReturn:
            ...


@base_events.requires_intents(intents.Intents.GUILD_WEBHOOKS)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class WebhookUpdateEvent(GuildChannelEvent):
    """Event fired when a webhook is created/updated/deleted in a channel.

    Unfortunately, Discord does not provide any information on what webhook
    actually changed, nor specifically whether it was created/updated/deleted,
    so this event is pretty useless unless you keep track of the webhooks in
    the channel manually beforehand.
    """

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.ib()
    # <<inherited docstring from ChannelEvent>>.

    guild_id: snowflakes.Snowflake = attr.ib()
    # <<inherited docstring from GuildChannelEvent>>.

    async def fetch_channel_webhooks(self) -> typing.Sequence[webhooks.Webhook]:
        """Perform an API call to fetch the webhooks for this channel.

        Returns
        -------
        typing.Sequence[hikari.webhooks.Webhook]
            The webhooks in this channel.
        """
        return await self.app.rest.fetch_channel_webhooks(self.channel_id)

    async def fetch_guild_webhooks(self) -> typing.Sequence[webhooks.Webhook]:
        """Perform an API call to fetch the webhooks for this guild.

        Returns
        -------
        typing.Sequence[hikari.webhooks.Webhook]
            The webhooks in this guild.
        """
        return await self.app.rest.fetch_guild_webhooks(self.guild_id)

    if typing.TYPE_CHECKING:

        async def fetch_channel(self) -> channels.GuildTextChannel:
            ...
