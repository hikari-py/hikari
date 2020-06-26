# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""Application and entities that are used to describe Discord gateway channel events."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = [
    "BaseChannelEvent",
    "ChannelCreateEvent",
    "ChannelUpdateEvent",
    "ChannelDeleteEvent",
    "ChannelPinsUpdateEvent",
    "WebhookUpdateEvent",
    "TypingStartEvent",
    "InviteCreateEvent",
    "InviteDeleteEvent",
]

import abc
import datetime
import typing

import attr

from hikari.events import base as base_events
from hikari.models import intents
from hikari.utilities import snowflake

if typing.TYPE_CHECKING:
    from hikari.api import rest
    from hikari.models import channels
    from hikari.models import guilds
    from hikari.models import invites


@base_events.requires_intents(intents.Intent.GUILDS)  # TODO: this intent doesn't account for DM channels.
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class BaseChannelEvent(base_events.Event, abc.ABC):
    """A base object that Channel events will inherit from."""

    channel: channels.PartialChannel = attr.ib(repr=True)
    """The object of the channel this event involved."""


@base_events.requires_intents(intents.Intent.GUILDS)  # TODO: this intent doesn't account for DM channels.
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class ChannelCreateEvent(BaseChannelEvent):
    """Represents Channel Create gateway events.

    Will be sent when a guild channel is created and before all Create Message
    events that originate from a DM channel.
    """


@base_events.requires_intents(intents.Intent.GUILDS)  # TODO: this intent doesn't account for DM channels.
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class ChannelUpdateEvent(BaseChannelEvent):
    """Represents Channel Update gateway events."""


@base_events.requires_intents(intents.Intent.GUILDS)  # TODO: this intent doesn't account for DM channels.
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class ChannelDeleteEvent(BaseChannelEvent):
    """Represents Channel Delete gateway events."""


@base_events.requires_intents(intents.Intent.GUILDS)  # TODO: this intent doesn't account for DM channels.
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class ChannelPinsUpdateEvent(base_events.Event):
    """Used to represent the Channel Pins Update gateway event.

    Sent when a message is pinned or unpinned in a channel but not
    when a pinned message is deleted.
    """

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(repr=True)
    """The ID of the guild where this event happened.

    Will be `None` if this happened in a DM channel.
    """

    channel_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the channel where the message was pinned or unpinned."""

    last_pin_timestamp: typing.Optional[datetime.datetime] = attr.ib(repr=True)
    """The datetime of when the most recent message was pinned in this channel.

    Will be `None` if there are no messages pinned after this change.
    """


@base_events.requires_intents(intents.Intent.GUILD_WEBHOOKS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class WebhookUpdateEvent(base_events.Event):
    """Used to represent webhook update gateway events.

    Sent when a webhook is updated, created or deleted in a guild.
    """

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    guild_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the guild this webhook is being updated in."""

    channel_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the channel this webhook is being updated in."""


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_TYPING, intents.Intent.DIRECT_MESSAGE_TYPING)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class TypingStartEvent(base_events.Event):
    """Used to represent typing start gateway events.

    Received when a user or bot starts "typing" in a channel.
    """

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    channel_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the channel this typing event is occurring in."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(repr=True)
    """The ID of the guild this typing event is occurring in.

    Will be `None` if this event is happening in a DM channel.
    """

    user_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the user who triggered this typing event."""

    timestamp: datetime.datetime = attr.ib(repr=False)
    """The datetime of when this typing event started."""

    member: typing.Optional[guilds.Member] = attr.ib(repr=False)
    """The member object of the user who triggered this typing event.

    Will be `None` if this was triggered in a DM.
    """


@base_events.requires_intents(intents.Intent.GUILD_INVITES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class InviteCreateEvent(base_events.Event):
    """Represents a gateway Invite Create event."""

    invite: invites.InviteWithMetadata = attr.ib(repr=True)
    """The object of the invite being created."""


@base_events.requires_intents(intents.Intent.GUILD_INVITES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class InviteDeleteEvent(base_events.Event):
    """Used to represent Invite Delete gateway events.

    Sent when an invite is deleted for a channel we can access.
    """

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    channel_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the channel this ID was attached to."""

    code: str = attr.ib(repr=True)
    """The code of this invite."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(repr=True)
    """The ID of the guild this invite was deleted in.

    This will be `None` if this invite belonged to a DM channel.
    """
