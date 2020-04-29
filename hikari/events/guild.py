#!/usr/bin/env python3
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
"""Components and entities that are used to describe Discord gateway guild events."""

from __future__ import annotations

__all__ = [
    "GuildCreateEvent",
    "GuildUpdateEvent",
    "GuildLeaveEvent",
    "GuildUnavailableEvent",
    "BaseGuildBanEvent",
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

from hikari import bases
from hikari import emojis as _emojis
from hikari import guilds
from hikari import intents
from hikari import unset
from hikari import users
from hikari.internal import conversions
from hikari.internal import marshaller
from hikari.events import base

if typing.TYPE_CHECKING:
    import datetime


@base.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildCreateEvent(base.HikariEvent, guilds.Guild):
    """Used to represent Guild Create gateway events.

    Will be received when the bot joins a guild, and when a guild becomes
    available to a guild (either due to outage or at startup).
    """


@base.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildUpdateEvent(base.HikariEvent, guilds.Guild):
    """Used to represent Guild Update gateway events."""


@base.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildLeaveEvent(base.HikariEvent, bases.UniqueEntity, marshaller.Deserializable):
    """Fired when the current user leaves the guild or is kicked/banned from it.

    !!! note
        This is fired based on Discord's Guild Delete gateway event.
    """


@base.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildUnavailableEvent(base.HikariEvent, bases.UniqueEntity, marshaller.Deserializable):
    """Fired when a guild becomes temporarily unavailable due to an outage.

    !!! note
        This is fired based on Discord's Guild Delete gateway event.
    """


@base.requires_intents(intents.Intent.GUILD_BANS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class BaseGuildBanEvent(base.HikariEvent, marshaller.Deserializable, abc.ABC):
    """A base object that guild ban events will inherit from."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild this ban is in."""

    user: users.User = marshaller.attrib(deserializer=users.User.deserialize)
    """The object of the user this ban targets."""


@base.requires_intents(intents.Intent.GUILD_BANS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildBanAddEvent(BaseGuildBanEvent):
    """Used to represent a Guild Ban Add gateway event."""


@base.requires_intents(intents.Intent.GUILD_BANS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildBanRemoveEvent(BaseGuildBanEvent):
    """Used to represent a Guild Ban Remove gateway event."""


@base.requires_intents(intents.Intent.GUILD_EMOJIS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildEmojisUpdateEvent(base.HikariEvent, marshaller.Deserializable):
    """Represents a Guild Emoji Update gateway event."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild this emoji was updated in."""

    emojis: typing.Mapping[bases.Snowflake, _emojis.GuildEmoji] = marshaller.attrib(
        deserializer=lambda ems: {emoji.id: emoji for emoji in map(_emojis.GuildEmoji.deserialize, ems)}
    )
    """The updated mapping of emojis by their ID."""


@base.requires_intents(intents.Intent.GUILD_INTEGRATIONS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildIntegrationsUpdateEvent(base.HikariEvent, marshaller.Deserializable):
    """Used to represent Guild Integration Update gateway events."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild the integration was updated in."""


@base.requires_intents(intents.Intent.GUILD_MEMBERS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildMemberAddEvent(base.HikariEvent, guilds.GuildMember):
    """Used to represent a Guild Member Add gateway event."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild where this member was added."""


@base.requires_intents(intents.Intent.GUILD_MEMBERS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildMemberUpdateEvent(base.HikariEvent, marshaller.Deserializable):
    """Used to represent a Guild Member Update gateway event.

    Sent when a guild member or their inner user object is updated.
    """

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild this member was updated in."""

    role_ids: typing.Sequence[bases.Snowflake] = marshaller.attrib(
        raw_name="roles", deserializer=lambda role_ids: [bases.Snowflake.deserialize(rid) for rid in role_ids],
    )
    """A sequence of the IDs of the member's current roles."""

    user: users.User = marshaller.attrib(deserializer=users.User.deserialize)
    """The object of the user who was updated."""

    nickname: typing.Union[None, str, unset.Unset] = marshaller.attrib(
        raw_name="nick", deserializer=str, if_none=None, if_undefined=unset.Unset, default=unset.UNSET
    )
    """This member's nickname.

    When set to `None`, this has been removed and when set to
    `hikari.unset.UNSET` this hasn't been acted on.
    """

    premium_since: typing.Union[None, datetime.datetime, unset.Unset] = marshaller.attrib(
        deserializer=conversions.parse_iso_8601_ts, if_none=None, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The datetime of when this member started "boosting" this guild.

    Will be `None` if they aren't boosting.
    """


@base.requires_intents(intents.Intent.GUILD_MEMBERS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildMemberRemoveEvent(base.HikariEvent, marshaller.Deserializable):
    """Used to represent Guild Member Remove gateway events.

    Sent when a member is kicked, banned or leaves a guild.
    """

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild this user was removed from."""

    user: users.User = marshaller.attrib(deserializer=users.User.deserialize)
    """The object of the user who was removed from this guild."""


@base.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildRoleCreateEvent(base.HikariEvent, marshaller.Deserializable):
    """Used to represent a Guild Role Create gateway event."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild where this role was created."""

    role: guilds.GuildRole = marshaller.attrib(deserializer=guilds.GuildRole.deserialize)
    """The object of the role that was created."""


@base.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildRoleUpdateEvent(base.HikariEvent, marshaller.Deserializable):
    """Used to represent a Guild Role Create gateway event."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild where this role was updated."""

    role: guilds.GuildRole = marshaller.attrib(deserializer=guilds.GuildRole.deserialize)
    """The updated role object."""


@base.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildRoleDeleteEvent(base.HikariEvent, marshaller.Deserializable):
    """Represents a gateway Guild Role Delete Event."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild where this role is being deleted."""

    role_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the role being deleted."""


@base.requires_intents(intents.Intent.GUILD_PRESENCES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class PresenceUpdateEvent(base.HikariEvent, guilds.GuildMemberPresence):
    """Used to represent Presence Update gateway events.

    Sent when a guild member changes their presence.
    """
