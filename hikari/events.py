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
"""Components and entities that are used to describe Discord gateway events."""

__all__ = [
    "HikariEvent",
    "ExceptionEvent",
    "ConnectedEvent",
    "DisconnectedEvent",
    "StartingEvent",
    "StartedEvent",
    "StoppingEvent",
    "StoppedEvent",
    "ReadyEvent",
    "ResumedEvent",
    "BaseChannelEvent",
    "ChannelCreateEvent",
    "ChannelUpdateEvent",
    "ChannelDeleteEvent",
    "ChannelPinUpdateEvent",
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
    "InviteCreateEvent",
    "InviteDeleteEvent",
    "MessageCreateEvent",
    "MessageUpdateEvent",
    "MessageDeleteEvent",
    "MessageDeleteBulkEvent",
    "MessageReactionAddEvent",
    "MessageReactionRemoveEvent",
    "MessageReactionRemoveAllEvent",
    "MessageReactionRemoveEmojiEvent",
    "PresenceUpdateEvent",
    "TypingStartEvent",
    "UserUpdateEvent",
    "VoiceStateUpdateEvent",
    "VoiceServerUpdateEvent",
    "WebhookUpdateEvent",
]

import abc
import datetime
import typing

import attr

from hikari import applications
from hikari import bases
from hikari import channels
from hikari import embeds as _embeds
from hikari import emojis as _emojis
from hikari import guilds
from hikari import intents
from hikari import invites
from hikari import messages
from hikari import unset
from hikari import users
from hikari import voices
from hikari.clients import shards
from hikari.internal import conversions
from hikari.internal import marshaller
from hikari.internal import more_collections

T_contra = typing.TypeVar("T_contra", contravariant=True)


# Base event, is not deserialized
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class HikariEvent(bases.HikariEntity, abc.ABC):
    """The base class that all events inherit from."""


_HikariEventT = typing.TypeVar("_HikariEventT", contravariant=True)

_REQUIRED_INTENTS_ATTR: typing.Final[str] = "___required_intents___"


def get_required_intents_for(event_type: typing.Type[HikariEvent]) -> typing.Collection[intents.Intent]:
    """Retrieve the intents that are required to listen to an event type.

    Parameters
    ----------
    event_type : typing.Type [ HikariEvent ]
        The event type to get required intents for.

    Returns
    -------
    typing.Collection [ hikari.intents.Intent ]
        Collection of acceptable subset combinations of intent needed to
        be able to receive the given event type.
    """
    return getattr(event_type, _REQUIRED_INTENTS_ATTR, more_collections.EMPTY_COLLECTION)


def requires_intents(
    first: intents.Intent, *rest: intents.Intent
) -> typing.Callable[[typing.Type[_HikariEventT]], typing.Type[_HikariEventT]]:
    """Decorate an event type to define what intents it requires.

    Parameters
    ----------
    first : hikari.intents.Intent
        First combination of intents that are acceptable in order to receive
        the decorated event type.
    *rest : hikari.intents.Intent
        Zero or more additional combinations of intents to require for this
        event to be subscribed to.

    """

    def decorator(cls: typing.Type[_HikariEventT]) -> typing.Type[_HikariEventT]:
        cls.___required_intents___ = [first, *rest]
        return cls

    return decorator


# Synthetic event, is not deserialized, and is produced by the dispatcher.
@attr.s(slots=True, auto_attribs=True)
class ExceptionEvent(HikariEvent):
    """Descriptor for an exception thrown while processing an event."""

    exception: Exception
    """The exception that was raised."""

    event: HikariEvent
    """The event that was being invoked when the exception occurred."""

    callback: typing.Callable[[HikariEvent], typing.Awaitable[None]]
    """The event that was being invoked when the exception occurred."""


# Synthetic event, is not deserialized
@attr.s(slots=True, auto_attribs=True)
class StartingEvent(HikariEvent):
    """Event that is fired before the gateway client starts all shards."""


# Synthetic event, is not deserialized
@attr.s(slots=True, auto_attribs=True)
class StartedEvent(HikariEvent):
    """Event that is fired when the gateway client starts all shards."""


# Synthetic event, is not deserialized
@attr.s(slots=True, auto_attribs=True)
class StoppingEvent(HikariEvent):
    """Event that is fired when the gateway client is instructed to disconnect all shards."""


# Synthetic event, is not deserialized
@attr.s(slots=True, auto_attribs=True)
class StoppedEvent(HikariEvent):
    """Event that is fired when the gateway client has finished disconnecting all shards."""


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class ConnectedEvent(HikariEvent, marshaller.Deserializable):
    """Event invoked each time a shard connects."""

    shard: shards.ShardClient
    """The shard that connected."""


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class DisconnectedEvent(HikariEvent, marshaller.Deserializable):
    """Event invoked each time a shard disconnects."""

    shard: shards.ShardClient
    """The shard that disconnected."""


@attr.s(slots=True, kw_only=True, auto_attribs=True)
class ResumedEvent(HikariEvent):
    """Represents a gateway Resume event."""

    shard: shards.ShardClient
    """The shard that reconnected."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class ReadyEvent(HikariEvent, marshaller.Deserializable):
    """Represents the gateway Ready event.

    This is received only when IDENTIFYing with the gateway.
    """

    gateway_version: int = marshaller.attrib(raw_name="v", deserializer=int)
    """The gateway version this is currently connected to."""

    my_user: users.MyUser = marshaller.attrib(raw_name="user", deserializer=users.MyUser.deserialize)
    """The object of the current bot account this connection is for."""

    unavailable_guilds: typing.Mapping[bases.Snowflake, guilds.UnavailableGuild] = marshaller.attrib(
        raw_name="guilds",
        deserializer=lambda guilds_objs: {g.id: g for g in map(guilds.UnavailableGuild.deserialize, guilds_objs)},
    )
    """A mapping of the guilds this bot is currently in.

    All guilds will start off "unavailable".
    """

    session_id: str = marshaller.attrib(deserializer=str)
    """The id of the current gateway session, used for reconnecting."""

    _shard_information: typing.Optional[typing.Tuple[int, int]] = marshaller.attrib(
        raw_name="shard", deserializer=tuple, if_undefined=None, default=None
    )
    """Information about the current shard, only provided when IDENTIFYing."""

    @property
    def shard_id(self) -> typing.Optional[int]:
        """Zero-indexed ID of the current shard.

        This is only available if this ready event was received while IDENTIFYing.
        """
        return self._shard_information[0] if self._shard_information else None

    @property
    def shard_count(self) -> typing.Optional[int]:
        """Total shard count for this bot.

        This is only available if this ready event was received while IDENTIFYing.
        """
        return self._shard_information[1] if self._shard_information else None


@requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class BaseChannelEvent(HikariEvent, bases.UniqueEntity, marshaller.Deserializable, abc.ABC):
    """A base object that Channel events will inherit from."""

    type: channels.ChannelType = marshaller.attrib(deserializer=channels.ChannelType)
    """The channel's type."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild this channel is in, will be `None` for DMs."""

    position: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None, default=None)
    """The sorting position of this channel.

    This will be relative to the `BaseChannelEvent.parent_id` if set.
    """

    permission_overwrites: typing.Optional[
        typing.Mapping[bases.Snowflake, channels.PermissionOverwrite]
    ] = marshaller.attrib(
        deserializer=lambda overwrites: {o.id: o for o in map(channels.PermissionOverwrite.deserialize, overwrites)},
        if_undefined=None,
        default=None,
    )
    """An mapping of the set permission overwrites for this channel, if applicable."""

    name: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, default=None)
    """The name of this channel, if applicable."""

    topic: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, if_none=None, default=None)
    """The topic of this channel, if applicable and set."""

    is_nsfw: typing.Optional[bool] = marshaller.attrib(
        raw_name="nsfw", deserializer=bool, if_undefined=None, default=None
    )
    """Whether this channel is nsfw, will be `None` if not applicable."""

    last_message_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_none=None, if_undefined=None, default=None
    )
    """The ID of the last message sent, if it's a text type channel."""

    bitrate: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None, default=None)
    """The bitrate (in bits) of this channel, if it's a guild voice channel."""

    user_limit: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None, default=None)
    """The user limit for this channel if it's a guild voice channel."""

    rate_limit_per_user: typing.Optional[datetime.timedelta] = marshaller.attrib(
        deserializer=lambda delta: datetime.timedelta(seconds=delta), if_undefined=None, default=None
    )
    """How long a user has to wait before sending another message in this channel.

    This is only applicable to a guild text like channel.
    """

    recipients: typing.Optional[typing.Mapping[bases.Snowflake, users.User]] = marshaller.attrib(
        deserializer=lambda recipients: {user.id: user for user in map(users.User.deserialize, recipients)},
        if_undefined=None,
        default=None,
    )
    """A mapping of this channel's recipient users, if it's a DM or group DM."""

    icon_hash: typing.Optional[str] = marshaller.attrib(
        raw_name="icon", deserializer=str, if_undefined=None, if_none=None, default=None
    )
    """The hash of this channel's icon, if it's a group DM channel and is set."""

    owner_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of this channel's creator, if it's a DM channel."""

    application_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the application that created the group DM.

    This is only applicable to bot based group DMs.
    """

    parent_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, if_none=None, default=None
    )
    """The ID of this channels's parent category within guild, if set."""

    last_pin_timestamp: typing.Optional[datetime.datetime] = marshaller.attrib(
        deserializer=conversions.parse_iso_8601_ts, if_undefined=None, default=None
    )
    """The datetime of when the last message was pinned in this channel."""


@requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class ChannelCreateEvent(BaseChannelEvent):
    """Represents Channel Create gateway events.

    Will be sent when a guild channel is created and before all Create Message
    events that originate from a DM channel.
    """


@requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class ChannelUpdateEvent(BaseChannelEvent):
    """Represents Channel Update gateway events."""


@requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class ChannelDeleteEvent(BaseChannelEvent):
    """Represents Channel Delete gateway events."""


@requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class ChannelPinUpdateEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent the Channel Pins Update gateway event.

    Sent when a message is pinned or unpinned in a channel but not
    when a pinned message is deleted.
    """

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild where this event happened.

    Will be `None` if this happened in a DM channel.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel where the message was pinned or unpinned."""

    last_pin_timestamp: typing.Optional[datetime.datetime] = marshaller.attrib(
        deserializer=conversions.parse_iso_8601_ts, if_undefined=None, default=None
    )
    """The datetime of when the most recent message was pinned in this channel.

    Will be `None` if there are no messages pinned after this change.
    """


@requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildCreateEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent Guild Create gateway events.

    Will be received when the bot joins a guild, and when a guild becomes
    available to a guild (either due to outage or at startup).
    """


@requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildUpdateEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent Guild Update gateway events."""


@requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildLeaveEvent(HikariEvent, bases.UniqueEntity, marshaller.Deserializable):
    """Fired when the current user leaves the guild or is kicked/banned from it.

    !!! note
        This is fired based on Discord's Guild Delete gateway event.
    """


@requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildUnavailableEvent(HikariEvent, bases.UniqueEntity, marshaller.Deserializable):
    """Fired when a guild becomes temporarily unavailable due to an outage.

    !!! note
        This is fired based on Discord's Guild Delete gateway event.
    """


@requires_intents(intents.Intent.GUILD_BANS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class BaseGuildBanEvent(HikariEvent, marshaller.Deserializable, abc.ABC):
    """A base object that guild ban events will inherit from."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild this ban is in."""

    user: users.User = marshaller.attrib(deserializer=users.User.deserialize)
    """The object of the user this ban targets."""


@requires_intents(intents.Intent.GUILD_BANS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildBanAddEvent(BaseGuildBanEvent):
    """Used to represent a Guild Ban Add gateway event."""


@requires_intents(intents.Intent.GUILD_BANS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildBanRemoveEvent(BaseGuildBanEvent):
    """Used to represent a Guild Ban Remove gateway event."""


@requires_intents(intents.Intent.GUILD_EMOJIS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildEmojisUpdateEvent(HikariEvent, marshaller.Deserializable):
    """Represents a Guild Emoji Update gateway event."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild this emoji was updated in."""

    emojis: typing.Mapping[bases.Snowflake, _emojis.GuildEmoji] = marshaller.attrib(
        deserializer=lambda ems: {emoji.id: emoji for emoji in map(_emojis.GuildEmoji.deserialize, ems)}
    )
    """The updated mapping of emojis by their ID."""


@requires_intents(intents.Intent.GUILD_INTEGRATIONS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildIntegrationsUpdateEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent Guild Integration Update gateway events."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild the integration was updated in."""


@requires_intents(intents.Intent.GUILD_MEMBERS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildMemberAddEvent(HikariEvent, guilds.GuildMember):
    """Used to represent a Guild Member Add gateway event."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild where this member was added."""


@requires_intents(intents.Intent.GUILD_MEMBERS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildMemberUpdateEvent(HikariEvent, marshaller.Deserializable):
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


@requires_intents(intents.Intent.GUILD_MEMBERS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildMemberRemoveEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent Guild Member Remove gateway events.

    Sent when a member is kicked, banned or leaves a guild.
    """

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild this user was removed from."""

    user: users.User = marshaller.attrib(deserializer=users.User.deserialize)
    """The object of the user who was removed from this guild."""


@requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildRoleCreateEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent a Guild Role Create gateway event."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild where this role was created."""

    role: guilds.GuildRole = marshaller.attrib(deserializer=guilds.GuildRole.deserialize)
    """The object of the role that was created."""


@requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildRoleUpdateEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent a Guild Role Create gateway event."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild where this role was updated."""

    role: guilds.GuildRole = marshaller.attrib(deserializer=guilds.GuildRole.deserialize)
    """The updated role object."""


@requires_intents(intents.Intent.GUILDS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildRoleDeleteEvent(HikariEvent, marshaller.Deserializable):
    """Represents a gateway Guild Role Delete Event."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild where this role is being deleted."""

    role_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the role being deleted."""


@requires_intents(intents.Intent.GUILD_INVITES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class InviteCreateEvent(HikariEvent, marshaller.Deserializable):
    """Represents a gateway Invite Create event."""

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel this invite targets."""

    code: str = marshaller.attrib(deserializer=str)
    """The code that identifies this invite."""

    created_at: datetime.datetime = marshaller.attrib(deserializer=conversions.parse_iso_8601_ts)
    """The datetime of when this invite was created."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild this invite was created in, if applicable.

    Will be `None` for group DM invites.
    """

    inviter: typing.Optional[users.User] = marshaller.attrib(
        deserializer=users.User.deserialize, if_undefined=None, default=None
    )
    """The object of the user who created this invite, if applicable."""

    max_age: typing.Optional[datetime.timedelta] = marshaller.attrib(
        deserializer=lambda age: datetime.timedelta(seconds=age) if age > 0 else None,
    )
    """The timedelta of how long this invite will be valid for.

    If set to `None` then this is unlimited.
    """

    max_uses: typing.Union[int, float] = marshaller.attrib(deserializer=lambda count: count or float("inf"))
    """The limit for how many times this invite can be used before it expires.

    If set to infinity (`float("inf")`) then this is unlimited.
    """

    target_user: typing.Optional[users.User] = marshaller.attrib(
        deserializer=users.User.deserialize, if_undefined=None, default=None
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


@requires_intents(intents.Intent.GUILD_INVITES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class InviteDeleteEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent Invite Delete gateway events.

    Sent when an invite is deleted for a channel we can access.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel this ID was attached to."""

    code: str = marshaller.attrib(deserializer=str)
    """The code of this invite."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild this invite was deleted in.

    This will be `None` if this invite belonged to a DM channel.
    """


@requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.DIRECT_MESSAGES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageCreateEvent(HikariEvent, messages.Message):
    """Used to represent Message Create gateway events."""


# This is an arbitrarily partial version of `messages.Message`
@requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.DIRECT_MESSAGES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageUpdateEvent(HikariEvent, bases.UniqueEntity, marshaller.Deserializable):
    """Represents Message Update gateway events.

    !!! note
        All fields on this model except `MessageUpdateEvent.channel_id` and
        `MessageUpdateEvent.id` may be set to `hikari.unset.UNSET` (a singleton)
        we have not received information about their state from Discord
        alongside field nullability.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel that the message was sent in."""

    guild_id: typing.Union[bases.Snowflake, unset.Unset] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The ID of the guild that the message was sent in."""

    author: typing.Union[users.User, unset.Unset] = marshaller.attrib(
        deserializer=users.User.deserialize, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The author of this message."""

    member: typing.Union[guilds.GuildMember, unset.Unset] = marshaller.attrib(
        deserializer=guilds.GuildMember.deserialize, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The member properties for the message's author."""

    content: typing.Union[str, unset.Unset] = marshaller.attrib(
        deserializer=str, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The content of the message."""

    timestamp: typing.Union[datetime.datetime, unset.Unset] = marshaller.attrib(
        deserializer=conversions.parse_iso_8601_ts, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The timestamp that the message was sent at."""

    edited_timestamp: typing.Union[datetime.datetime, unset.Unset, None] = marshaller.attrib(
        deserializer=conversions.parse_iso_8601_ts, if_none=None, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The timestamp that the message was last edited at.

    Will be `None` if the message wasn't ever edited.
    """

    is_tts: typing.Union[bool, unset.Unset] = marshaller.attrib(
        raw_name="tts", deserializer=bool, if_undefined=unset.Unset, default=unset.UNSET
    )
    """Whether the message is a TTS message."""

    is_mentioning_everyone: typing.Union[bool, unset.Unset] = marshaller.attrib(
        raw_name="mention_everyone", deserializer=bool, if_undefined=unset.Unset, default=unset.UNSET
    )
    """Whether the message mentions `@everyone` or `@here`."""

    user_mentions: typing.Union[typing.Set[bases.Snowflake], unset.Unset] = marshaller.attrib(
        raw_name="mentions",
        deserializer=lambda user_mentions: {bases.Snowflake.deserialize(u["id"]) for u in user_mentions},
        if_undefined=unset.Unset,
        default=unset.UNSET,
    )
    """The users the message mentions."""

    role_mentions: typing.Union[typing.Set[bases.Snowflake], unset.Unset] = marshaller.attrib(
        raw_name="mention_roles",
        deserializer=lambda role_mentions: {bases.Snowflake.deserialize(r) for r in role_mentions},
        if_undefined=unset.Unset,
        default=unset.UNSET,
    )
    """The roles the message mentions."""

    channel_mentions: typing.Union[typing.Set[bases.Snowflake], unset.Unset] = marshaller.attrib(
        raw_name="mention_channels",
        deserializer=lambda channel_mentions: {bases.Snowflake.deserialize(c["id"]) for c in channel_mentions},
        if_undefined=unset.Unset,
        default=unset.UNSET,
    )
    """The channels the message mentions."""

    attachments: typing.Union[typing.Sequence[messages.Attachment], unset.Unset] = marshaller.attrib(
        deserializer=lambda attachments: [messages.Attachment.deserialize(a) for a in attachments],
        if_undefined=unset.Unset,
        default=unset.UNSET,
    )
    """The message attachments."""

    embeds: typing.Union[typing.Sequence[_embeds.Embed], unset.Unset] = marshaller.attrib(
        deserializer=lambda embed_objs: [_embeds.Embed.deserialize(e) for e in embed_objs],
        if_undefined=unset.Unset,
        default=unset.UNSET,
    )
    """The message's embeds."""

    reactions: typing.Union[typing.Sequence[messages.Reaction], unset.Unset] = marshaller.attrib(
        deserializer=lambda reactions: [messages.Reaction.deserialize(r) for r in reactions],
        if_undefined=unset.Unset,
        default=unset.UNSET,
    )
    """The message's reactions."""

    is_pinned: typing.Union[bool, unset.Unset] = marshaller.attrib(
        raw_name="pinned", deserializer=bool, if_undefined=unset.Unset, default=unset.UNSET
    )
    """Whether the message is pinned."""

    webhook_id: typing.Union[bases.Snowflake, unset.Unset] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=unset.Unset, default=unset.UNSET
    )
    """If the message was generated by a webhook, the webhook's ID."""

    type: typing.Union[messages.MessageType, unset.Unset] = marshaller.attrib(
        deserializer=messages.MessageType, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The message's type."""

    activity: typing.Union[messages.MessageActivity, unset.Unset] = marshaller.attrib(
        deserializer=messages.MessageActivity.deserialize, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The message's activity."""

    application: typing.Optional[applications.Application] = marshaller.attrib(
        deserializer=applications.Application.deserialize, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The message's application."""

    message_reference: typing.Union[messages.MessageCrosspost, unset.Unset] = marshaller.attrib(
        deserializer=messages.MessageCrosspost.deserialize, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The message's cross-posted reference data."""

    flags: typing.Union[messages.MessageFlag, unset.Unset] = marshaller.attrib(
        deserializer=messages.MessageFlag, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The message's flags."""

    nonce: typing.Union[str, unset.Unset] = marshaller.attrib(
        deserializer=str, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The message nonce.

    This is a string used for validating a message was sent.
    """


@requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.DIRECT_MESSAGES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageDeleteEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent Message Delete gateway events.

    Sent when a message is deleted in a channel we have access to.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel where this message was deleted."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild where this message was deleted.

    This will be `None` if this message was deleted in a DM channel.
    """

    message_id: bases.Snowflake = marshaller.attrib(raw_name="id", deserializer=bases.Snowflake.deserialize)
    """The ID of the message that was deleted."""


@requires_intents(intents.Intent.GUILD_MESSAGES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageDeleteBulkEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent Message Bulk Delete gateway events.

    Sent when multiple messages are deleted in a channel at once.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel these messages have been deleted in."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_none=None
    )
    """The ID of the channel these messages have been deleted in.

    This will be `None` if these messages were bulk deleted in a DM channel.
    """

    message_ids: typing.Set[bases.Snowflake] = marshaller.attrib(
        raw_name="ids", deserializer=lambda msgs: {bases.Snowflake.deserialize(m) for m in msgs}
    )
    """A collection of the IDs of the messages that were deleted."""


@requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageReactionAddEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent Message Reaction Add gateway events."""

    user_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the user adding the reaction."""

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel where this reaction is being added."""

    message_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the message this reaction is being added to."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild where this reaction is being added.

    This will be `None` if this is happening in a DM channel.
    """

    member: typing.Optional[guilds.GuildMember] = marshaller.attrib(
        deserializer=guilds.GuildMember.deserialize, if_undefined=None, default=None
    )
    """The member object of the user who's adding this reaction.

    This will be `None` if this is happening in a DM channel.
    """

    emoji: typing.Union[_emojis.UnknownEmoji, _emojis.UnicodeEmoji] = marshaller.attrib(
        deserializer=_emojis.deserialize_reaction_emoji,
    )
    """The object of the emoji being added."""


@requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageReactionRemoveEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent Message Reaction Remove gateway events."""

    user_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the user who is removing their reaction."""

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel where this reaction is being removed."""

    message_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the message this reaction is being removed from."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild where this reaction is being removed

    This will be `None` if this event is happening in a DM channel.
    """

    emoji: typing.Union[_emojis.UnicodeEmoji, _emojis.UnknownEmoji] = marshaller.attrib(
        deserializer=_emojis.deserialize_reaction_emoji,
    )
    """The object of the emoji being removed."""


@requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageReactionRemoveAllEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent Message Reaction Remove All gateway events.

    Sent when all the reactions are removed from a message, regardless of emoji.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel where the targeted message is."""

    message_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the message all reactions are being removed from."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild where the targeted message is, if applicable."""


@requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageReactionRemoveEmojiEvent(HikariEvent, marshaller.Deserializable):
    """Represents Message Reaction Remove Emoji events.

    Sent when all the reactions for a single emoji are removed from a message.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel where the targeted message is."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild where the targeted message is, if applicable."""

    message_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the message the reactions are being removed from."""

    emoji: typing.Union[_emojis.UnicodeEmoji, _emojis.UnknownEmoji] = marshaller.attrib(
        deserializer=_emojis.deserialize_reaction_emoji,
    )
    """The object of the emoji that's being removed."""


@requires_intents(intents.Intent.GUILD_PRESENCES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class PresenceUpdateEvent(HikariEvent, guilds.GuildMemberPresence):
    """Used to represent Presence Update gateway events.

    Sent when a guild member changes their presence.
    """


@requires_intents(intents.Intent.GUILD_MESSAGE_TYPING, intents.Intent.DIRECT_MESSAGE_TYPING)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class TypingStartEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent typing start gateway events.

    Received when a user or bot starts "typing" in a channel.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel this typing event is occurring in."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild this typing event is occurring in.

    Will be `None` if this event is happening in a DM channel.
    """

    user_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the user who triggered this typing event."""

    timestamp: datetime.datetime = marshaller.attrib(
        deserializer=lambda date: datetime.datetime.fromtimestamp(date, datetime.timezone.utc)
    )
    """The datetime of when this typing event started."""

    member: typing.Optional[guilds.GuildMember] = marshaller.attrib(
        deserializer=guilds.GuildMember.deserialize, if_undefined=None, default=None
    )
    """The member object of the user who triggered this typing event.

    Will be `None` if this was triggered in a DM.
    """


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class UserUpdateEvent(HikariEvent, users.MyUser):
    """Used to represent User Update gateway events.

    Sent when the current user is updated.
    """


@requires_intents(intents.Intent.GUILD_VOICE_STATES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class VoiceStateUpdateEvent(HikariEvent, voices.VoiceState):
    """Used to represent voice state update gateway events.

    Sent when a user joins, leaves or moves voice channel(s).
    """


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class VoiceServerUpdateEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent voice server update gateway events.

    Sent when initially connecting to voice and when the current voice instance
    falls over to a new server.
    """

    token: str = marshaller.attrib(deserializer=str)
    """The voice connection's string token."""

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild this voice server update is for."""

    endpoint: str = marshaller.attrib(deserializer=str)
    """The uri for this voice server host."""


@requires_intents(intents.Intent.GUILD_WEBHOOKS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class WebhookUpdateEvent(HikariEvent, marshaller.Deserializable):
    """Used to represent webhook update gateway events.

    Sent when a webhook is updated, created or deleted in a guild.
    """

    guild_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the guild this webhook is being updated in."""

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel this webhook is being updated in."""
