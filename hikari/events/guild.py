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

from hikari import bases as base_entities
from hikari import emojis as _emojis
from hikari import guilds
from hikari import intents
from hikari import unset
from hikari import users
from hikari.events import base as base_events
from hikari.internal import conversions
from hikari.internal import marshaller

if typing.TYPE_CHECKING:
    import datetime

    from hikari.internal import more_typing


@base_events.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildCreateEvent(base_events.HikariEvent, guilds.Guild):
    """Used to represent Guild Create gateway events.

    Will be received when the bot joins a guild, and when a guild becomes
    available to a guild (either due to outage or at startup).
    """


@base_events.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildUpdateEvent(base_events.HikariEvent, guilds.Guild):
    """Used to represent Guild Update gateway events."""


@base_events.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildLeaveEvent(base_events.HikariEvent, base_entities.Unique, marshaller.Deserializable):
    """Fired when the current user leaves the guild or is kicked/banned from it.

    !!! note
        This is fired based on Discord's Guild Delete gateway event.
    """


@base_events.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildUnavailableEvent(base_events.HikariEvent, base_entities.Unique, marshaller.Deserializable):
    """Fired when a guild becomes temporarily unavailable due to an outage.

    !!! note
        This is fired based on Discord's Guild Delete gateway event.
    """


@base_events.requires_intents(intents.Intent.GUILD_BANS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class BaseGuildBanEvent(base_events.HikariEvent, marshaller.Deserializable, abc.ABC):
    """A base object that guild ban events will inherit from."""

    guild_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the guild this ban is in."""

    user: users.User = marshaller.attrib(deserializer=users.User.deserialize, inherit_kwargs=True, repr=True)
    """The object of the user this ban targets."""


@base_events.requires_intents(intents.Intent.GUILD_BANS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildBanAddEvent(BaseGuildBanEvent):
    """Used to represent a Guild Ban Add gateway event."""


@base_events.requires_intents(intents.Intent.GUILD_BANS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildBanRemoveEvent(BaseGuildBanEvent):
    """Used to represent a Guild Ban Remove gateway event."""


def _deserialize_emojis(
    payload: more_typing.JSONArray, **kwargs: typing.Any
) -> typing.Mapping[base_entities.Snowflake, _emojis.GuildEmoji]:
    return {base_entities.Snowflake(emoji["id"]): _emojis.GuildEmoji.deserialize(emoji, **kwargs) for emoji in payload}


@base_events.requires_intents(intents.Intent.GUILD_EMOJIS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildEmojisUpdateEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Represents a Guild Emoji Update gateway event."""

    guild_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake)
    """The ID of the guild this emoji was updated in."""

    emojis: typing.Mapping[base_entities.Snowflake, _emojis.GuildEmoji] = marshaller.attrib(
        deserializer=_deserialize_emojis, inherit_kwargs=True, repr=True
    )
    """The updated mapping of emojis by their ID."""


@base_events.requires_intents(intents.Intent.GUILD_INTEGRATIONS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildIntegrationsUpdateEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent Guild Integration Update gateway events."""

    guild_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the guild the integration was updated in."""


@base_events.requires_intents(intents.Intent.GUILD_MEMBERS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildMemberAddEvent(base_events.HikariEvent, guilds.GuildMember):
    """Used to represent a Guild Member Add gateway event."""

    guild_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the guild where this member was added."""


def _deserialize_role_ids(payload: more_typing.JSONArray) -> typing.Sequence[base_entities.Snowflake]:
    return [base_entities.Snowflake(role_id) for role_id in payload]


@base_events.requires_intents(intents.Intent.GUILD_MEMBERS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildMemberUpdateEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent a Guild Member Update gateway event.

    Sent when a guild member or their inner user object is updated.
    """

    guild_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the guild this member was updated in."""

    role_ids: typing.Sequence[base_entities.Snowflake] = marshaller.attrib(
        raw_name="roles", deserializer=_deserialize_role_ids,
    )
    """A sequence of the IDs of the member's current roles."""

    user: users.User = marshaller.attrib(deserializer=users.User.deserialize, inherit_kwargs=True, repr=True)
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


@base_events.requires_intents(intents.Intent.GUILD_MEMBERS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildMemberRemoveEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent Guild Member Remove gateway events.

    Sent when a member is kicked, banned or leaves a guild.
    """

    # TODO: make GuildMember event into common base class.
    guild_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the guild this user was removed from."""

    user: users.User = marshaller.attrib(deserializer=users.User.deserialize, inherit_kwargs=True, repr=True)
    """The object of the user who was removed from this guild."""


@base_events.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildRoleCreateEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent a Guild Role Create gateway event."""

    guild_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the guild where this role was created."""

    role: guilds.GuildRole = marshaller.attrib(deserializer=guilds.GuildRole.deserialize, inherit_kwargs=True)
    """The object of the role that was created."""


@base_events.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildRoleUpdateEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent a Guild Role Create gateway event."""

    # TODO: make any event with a guild ID into a custom base event.
    # https://pypi.org/project/stupid/ could this work around the multiple inheritance problem?
    guild_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the guild where this role was updated."""

    role: guilds.GuildRole = marshaller.attrib(
        deserializer=guilds.GuildRole.deserialize, inherit_kwargs=True, repr=True
    )
    """The updated role object."""


@base_events.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildRoleDeleteEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Represents a gateway Guild Role Delete Event."""

    guild_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the guild where this role is being deleted."""

    role_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the role being deleted."""


@base_events.requires_intents(intents.Intent.GUILD_PRESENCES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class PresenceUpdateEvent(base_events.HikariEvent, guilds.GuildMemberPresence):
    """Used to represent Presence Update gateway events.

    Sent when a guild member changes their presence.
    """
