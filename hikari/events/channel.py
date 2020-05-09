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
"""Components and entities that are used to describe Discord gateway channel events."""
from __future__ import annotations

__all__ = [
    "BaseChannelEvent",
    "ChannelCreateEvent",
    "ChannelUpdateEvent",
    "ChannelDeleteEvent",
    "ChannelPinUpdateEvent",
    "WebhookUpdateEvent",
    "TypingStartEvent",
    "InviteCreateEvent",
    "InviteDeleteEvent",
    "VoiceStateUpdateEvent",
    "VoiceServerUpdateEvent",
]

import abc
import datetime
import typing

import attr

from hikari import bases as base_entities
from hikari import channels
from hikari import guilds
from hikari import intents
from hikari import invites
from hikari import users
from hikari import voices
from hikari.events import base as base_events
from hikari.internal import conversions
from hikari.internal import marshaller

if typing.TYPE_CHECKING:
    from hikari.internal import more_typing


def _overwrite_deserializer(
    payload: more_typing.JSONArray, **kwargs: typing.Any
) -> typing.Mapping[base_entities.Snowflake, channels.PermissionOverwrite]:
    return {
        base_entities.Snowflake(overwrite["id"]): channels.PermissionOverwrite.deserialize(overwrite, **kwargs)
        for overwrite in payload
    }


def _rate_limit_per_user_deserializer(seconds: int) -> datetime.timedelta:
    return datetime.timedelta(seconds=seconds)


def _recipients_deserializer(
    payload: more_typing.JSONArray, **kwargs: typing.Any
) -> typing.Mapping[base_entities.Snowflake, users.User]:
    return {base_entities.Snowflake(user["id"]): users.User.deserialize(user, **kwargs) for user in payload}


@base_events.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class BaseChannelEvent(base_events.HikariEvent, base_entities.Unique, marshaller.Deserializable, abc.ABC):
    """A base object that Channel events will inherit from."""

    type: channels.ChannelType = marshaller.attrib(deserializer=channels.ChannelType, repr=True)
    """The channel's type."""

    guild_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=None, default=None, repr=True
    )
    """The ID of the guild this channel is in, will be `None` for DMs."""

    position: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None, default=None)
    """The sorting position of this channel.

    This will be relative to the `BaseChannelEvent.parent_id` if set.
    """

    permission_overwrites: typing.Optional[
        typing.Mapping[base_entities.Snowflake, channels.PermissionOverwrite]
    ] = marshaller.attrib(deserializer=_overwrite_deserializer, if_undefined=None, default=None, inherit_kwargs=True)
    """An mapping of the set permission overwrites for this channel, if applicable."""

    name: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, default=None, repr=True)
    """The name of this channel, if applicable."""

    topic: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, if_none=None, default=None)
    """The topic of this channel, if applicable and set."""

    is_nsfw: typing.Optional[bool] = marshaller.attrib(
        raw_name="nsfw", deserializer=bool, if_undefined=None, default=None
    )
    """Whether this channel is nsfw, will be `None` if not applicable."""

    last_message_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_none=None, if_undefined=None, default=None
    )
    """The ID of the last message sent, if it's a text type channel."""

    bitrate: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None, default=None)
    """The bitrate (in bits) of this channel, if it's a guild voice channel."""

    user_limit: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None, default=None)
    """The user limit for this channel if it's a guild voice channel."""

    rate_limit_per_user: typing.Optional[datetime.timedelta] = marshaller.attrib(
        deserializer=_rate_limit_per_user_deserializer, if_undefined=None, default=None
    )
    """How long a user has to wait before sending another message in this channel.

    This is only applicable to a guild text like channel.
    """

    recipients: typing.Optional[typing.Mapping[base_entities.Snowflake, users.User]] = marshaller.attrib(
        deserializer=_recipients_deserializer, if_undefined=None, default=None, inherit_kwargs=True,
    )
    """A mapping of this channel's recipient users, if it's a DM or group DM."""

    icon_hash: typing.Optional[str] = marshaller.attrib(
        raw_name="icon", deserializer=str, if_undefined=None, if_none=None, default=None
    )
    """The hash of this channel's icon, if it's a group DM channel and is set."""

    owner_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=None, default=None
    )
    """The ID of this channel's creator, if it's a DM channel."""

    application_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=None, default=None
    )
    """The ID of the application that created the group DM.

    This is only applicable to bot based group DMs.
    """

    parent_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=None, if_none=None, default=None
    )
    """The ID of this channels's parent category within guild, if set."""

    last_pin_timestamp: typing.Optional[datetime.datetime] = marshaller.attrib(
        deserializer=conversions.parse_iso_8601_ts, if_undefined=None, default=None
    )
    """The datetime of when the last message was pinned in this channel."""


@base_events.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class ChannelCreateEvent(BaseChannelEvent):
    """Represents Channel Create gateway events.

    Will be sent when a guild channel is created and before all Create Message
    events that originate from a DM channel.
    """


@base_events.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class ChannelUpdateEvent(BaseChannelEvent):
    """Represents Channel Update gateway events."""


@base_events.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class ChannelDeleteEvent(BaseChannelEvent):
    """Represents Channel Delete gateway events."""


@base_events.requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class ChannelPinUpdateEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent the Channel Pins Update gateway event.

    Sent when a message is pinned or unpinned in a channel but not
    when a pinned message is deleted.
    """

    guild_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=None, default=None, repr=True
    )
    """The ID of the guild where this event happened.

    Will be `None` if this happened in a DM channel.
    """

    channel_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the channel where the message was pinned or unpinned."""

    last_pin_timestamp: typing.Optional[datetime.datetime] = marshaller.attrib(
        deserializer=conversions.parse_iso_8601_ts, if_undefined=None, default=None, repr=True
    )
    """The datetime of when the most recent message was pinned in this channel.

    Will be `None` if there are no messages pinned after this change.
    """


@base_events.requires_intents(intents.Intent.GUILD_WEBHOOKS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class WebhookUpdateEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent webhook update gateway events.

    Sent when a webhook is updated, created or deleted in a guild.
    """

    guild_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the guild this webhook is being updated in."""

    channel_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the channel this webhook is being updated in."""


def _timestamp_deserializer(date: str) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(date, datetime.timezone.utc)


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_TYPING, intents.Intent.DIRECT_MESSAGE_TYPING)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class TypingStartEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent typing start gateway events.

    Received when a user or bot starts "typing" in a channel.
    """

    channel_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the channel this typing event is occurring in."""

    guild_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=None, default=None, repr=True
    )
    """The ID of the guild this typing event is occurring in.

    Will be `None` if this event is happening in a DM channel.
    """

    user_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the user who triggered this typing event."""

    timestamp: datetime.datetime = marshaller.attrib(deserializer=_timestamp_deserializer)
    """The datetime of when this typing event started."""

    member: typing.Optional[guilds.GuildMember] = marshaller.attrib(
        deserializer=guilds.GuildMember.deserialize, if_undefined=None, default=None
    )
    """The member object of the user who triggered this typing event.

    Will be `None` if this was triggered in a DM.
    """


def _max_age_deserializer(age: int) -> typing.Optional[datetime.datetime]:
    return datetime.timedelta(seconds=age) if age > 0 else None


def _max_uses_deserializer(count: int) -> typing.Union[int, float]:
    return count or float("inf")


@base_events.requires_intents(intents.Intent.GUILD_INVITES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class InviteCreateEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Represents a gateway Invite Create event."""

    channel_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the channel this invite targets."""

    code: str = marshaller.attrib(deserializer=str, repr=True)
    """The code that identifies this invite."""

    created_at: datetime.datetime = marshaller.attrib(deserializer=conversions.parse_iso_8601_ts)
    """The datetime of when this invite was created."""

    guild_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=None, default=None, repr=True
    )
    """The ID of the guild this invite was created in, if applicable.

    Will be `None` for group DM invites.
    """

    inviter: typing.Optional[users.User] = marshaller.attrib(
        deserializer=users.User.deserialize, if_undefined=None, default=None, inherit_kwargs=True
    )
    """The object of the user who created this invite, if applicable."""

    max_age: typing.Optional[datetime.timedelta] = marshaller.attrib(deserializer=_max_age_deserializer,)
    """The timedelta of how long this invite will be valid for.

    If set to `None` then this is unlimited.
    """

    max_uses: typing.Union[int, float] = marshaller.attrib(deserializer=_max_uses_deserializer)
    """The limit for how many times this invite can be used before it expires.

    If set to infinity (`float("inf")`) then this is unlimited.
    """

    target_user: typing.Optional[users.User] = marshaller.attrib(
        deserializer=users.User.deserialize, if_undefined=None, default=None, inherit_kwargs=True
    )
    """The object of the user who this invite targets, if set."""

    target_user_type: typing.Optional[invites.TargetUserType] = marshaller.attrib(
        deserializer=invites.TargetUserType, if_undefined=None, default=None
    )
    """The type of user target this invite is, if applicable."""

    is_temporary: bool = marshaller.attrib(raw_name="temporary", deserializer=bool)
    """Whether this invite grants temporary membership."""

    uses: int = marshaller.attrib(deserializer=int)
    """The amount of times this invite has been used."""


@base_events.requires_intents(intents.Intent.GUILD_INVITES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class InviteDeleteEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent Invite Delete gateway events.

    Sent when an invite is deleted for a channel we can access.
    """

    channel_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the channel this ID was attached to."""

    # TODO: move common fields with InviteCreateEvent into base class.
    code: str = marshaller.attrib(deserializer=str, repr=True)
    """The code of this invite."""

    guild_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=None, default=None, repr=True
    )
    """The ID of the guild this invite was deleted in.

    This will be `None` if this invite belonged to a DM channel.
    """


@base_events.requires_intents(intents.Intent.GUILD_VOICE_STATES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class VoiceStateUpdateEvent(base_events.HikariEvent, voices.VoiceState):
    """Used to represent voice state update gateway events.

    Sent when a user joins, leaves or moves voice channel(s).
    """


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class VoiceServerUpdateEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent voice server update gateway events.

    Sent when initially connecting to voice and when the current voice instance
    falls over to a new server.
    """

    token: str = marshaller.attrib(deserializer=str)
    """The voice connection's string token."""

    guild_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the guild this voice server update is for."""

    endpoint: str = marshaller.attrib(deserializer=str, repr=True)
    """The uri for this voice server host."""
