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
"""Application and entities that are used to describe Discord gateway guild events."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = [
    "GuildEvent",
    "GuildCreateEvent",
    "GuildUpdateEvent",
    "GuildLeaveEvent",
    "GuildUnavailableEvent",
    "GuildBanEvent",
    "GuildBanAddEvent",
    "GuildBanRemoveEvent",
    "GuildEmojisUpdateEvent",
    "GuildIntegrationsUpdateEvent",
    "GuildMemberAddEvent",
    "GuildMemberUpdateEvent",
    "GuildMemberRemoveEvent",
    "GuildRoleCreateEvent",
    "GuildRoleUpdateEvent",
    "GuildRoleDeleteEvent",
    "PresenceUpdateEvent",
]

import abc
import typing

import attr

from hikari.events import base as base_events
from hikari.models import intents
from hikari.utilities import snowflake

if typing.TYPE_CHECKING:
    from hikari.api import rest
    from hikari.models import emojis as emojis_models
    from hikari.models import guilds
    from hikari.models import presences
    from hikari.models import users


@base_events.requires_intents(intents.Intent.GUILDS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildEvent(base_events.Event):
    """A base object that all guild events will inherit from."""


@base_events.requires_intents(intents.Intent.GUILDS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildCreateEvent(GuildEvent):
    """Used to represent Guild Create gateway events.

    Will be received when the bot joins a guild, and when a guild becomes
    available to a guild (either due to outage or at startup).
    """

    guild: guilds.Guild = attr.ib(repr=True)
    """The object of the guild that's being created."""


@base_events.requires_intents(intents.Intent.GUILDS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildUpdateEvent(GuildEvent):
    """Used to represent Guild Update gateway events."""

    guild: guilds.Guild = attr.ib(repr=True)
    """The object of the guild that's being updated."""


@base_events.requires_intents(intents.Intent.GUILDS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildLeaveEvent(GuildEvent, snowflake.Unique):
    """Fired when the current user leaves the guild or is kicked/banned from it.

    !!! note
        This is fired based on Discord's Guild Delete gateway event.
    """

    id: snowflake.Snowflake = attr.ib(
        converter=snowflake.Snowflake, eq=True, hash=True, repr=True, factory=snowflake.Snowflake,
    )
    """The ID of this entity."""


@base_events.requires_intents(intents.Intent.GUILDS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildUnavailableEvent(GuildEvent, snowflake.Unique):
    """Fired when a guild becomes temporarily unavailable due to an outage.

    !!! note
        This is fired based on Discord's Guild Delete gateway event.
    """

    id: snowflake.Snowflake = attr.ib(
        converter=snowflake.Snowflake, eq=True, hash=True, repr=True, factory=snowflake.Snowflake,
    )
    """The ID of this entity."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""


@base_events.requires_intents(intents.Intent.GUILD_BANS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildBanEvent(GuildEvent, abc.ABC):
    """A base object that guild ban events will inherit from."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    guild_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the guild this ban is in."""

    user: users.User = attr.ib(repr=True)
    """The object of the user this ban targets."""


@base_events.requires_intents(intents.Intent.GUILD_BANS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildBanAddEvent(GuildBanEvent):
    """Used to represent a Guild Ban Add gateway event."""


@base_events.requires_intents(intents.Intent.GUILD_BANS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildBanRemoveEvent(GuildBanEvent):
    """Used to represent a Guild Ban Remove gateway event."""


@base_events.requires_intents(intents.Intent.GUILD_EMOJIS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildEmojisUpdateEvent(GuildEvent):
    """Represents a Guild Emoji Update gateway event."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    guild_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the guild this emoji was updated in."""

    emojis: typing.Mapping[snowflake.Snowflake, emojis_models.KnownCustomEmoji] = attr.ib(repr=True)
    """The updated mapping of emojis by their ID."""


@base_events.requires_intents(intents.Intent.GUILD_INTEGRATIONS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildIntegrationsUpdateEvent(GuildEvent):
    """Used to represent Guild Integration Update gateway events."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    guild_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the guild the integration was updated in."""


@base_events.requires_intents(intents.Intent.GUILD_MEMBERS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildMemberEvent(GuildEvent):
    """A base class that all guild member events will inherit from."""


@base_events.requires_intents(intents.Intent.GUILD_MEMBERS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildMemberAddEvent(GuildMemberEvent):
    """Used to represent a Guild Member Add gateway event."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    guild_id: snowflake.Snowflake = attr.ib(repr=True)  # TODO: do we want to have guild_id on all members?
    """The ID of the guild where this member was added."""

    member: guilds.Member = attr.ib(repr=True)
    """The object of the member who's being added."""


@base_events.requires_intents(intents.Intent.GUILD_MEMBERS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildMemberUpdateEvent(GuildMemberEvent):
    """Used to represent a Guild Member Update gateway event.

    Sent when a guild member or their inner user object is updated.
    """

    member: guilds.Member = attr.ib(repr=True)


@base_events.requires_intents(intents.Intent.GUILD_MEMBERS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildMemberRemoveEvent(GuildMemberEvent):
    """Used to represent Guild Member Remove gateway events.

    Sent when a member is kicked, banned or leaves a guild.
    """

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    # TODO: make GuildMember event into common base class.
    guild_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the guild this user was removed from."""

    user: users.User = attr.ib(repr=True)
    """The object of the user who was removed from this guild."""


@base_events.requires_intents(intents.Intent.GUILDS)
class GuildRoleEvent(GuildEvent):
    """A base class that all guild role events will inherit from."""


@base_events.requires_intents(intents.Intent.GUILDS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildRoleCreateEvent(GuildRoleEvent):
    """Used to represent a Guild Role Create gateway event."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    guild_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the guild where this role was created."""

    role: guilds.Role = attr.ib(repr=True)
    """The object of the role that was created."""


@base_events.requires_intents(intents.Intent.GUILDS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildRoleUpdateEvent(GuildRoleEvent):
    """Used to represent a Guild Role Create gateway event."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    # TODO: make any event with a guild ID into a custom base event.
    # https://pypi.org/project/stupid/ could this work around the multiple inheritance problem?
    guild_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the guild where this role was updated."""

    role: guilds.Role = attr.ib(repr=True)
    """The updated role object."""


@base_events.requires_intents(intents.Intent.GUILDS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class GuildRoleDeleteEvent(GuildRoleEvent):
    """Represents a gateway Guild Role Delete Event."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    guild_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the guild where this role is being deleted."""

    role_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the role being deleted."""


@base_events.requires_intents(intents.Intent.GUILD_PRESENCES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class PresenceUpdateEvent(GuildEvent):
    """Used to represent Presence Update gateway events.

    Sent when a guild member changes their presence.
    """

    presence: presences.MemberPresence = attr.ib(repr=True)
    """The object of the presence being updated."""
