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
"""Components and entities that are used to describe both DMs and guild channels on Discord."""

from __future__ import annotations

__all__ = [
    "ChannelType",
    "PermissionOverwrite",
    "PermissionOverwriteType",
    "PartialChannel",
    "DMChannel",
    "GroupDMChannel",
    "GuildCategory",
    "GuildChannel",
    "GuildTextChannel",
    "GuildNewsChannel",
    "GuildStoreChannel",
    "GuildVoiceChannel",
    "GuildChannelBuilder",
]

import datetime
import typing

import attr

from hikari import bases
from hikari import permissions
from hikari import users
from hikari.internal import conversions
from hikari.internal import marshaller
from hikari.internal import more_collections
from hikari.internal import more_enums

if typing.TYPE_CHECKING:
    from hikari.internal import more_typing


@more_enums.must_be_unique
class ChannelType(int, more_enums.Enum):
    """The known channel types that are exposed to us by the API."""

    GUILD_TEXT = 0
    """A text channel in a guild."""

    DM = 1
    """A direct channel between two users."""

    GUILD_VOICE = 2
    """A voice channel in a guild."""

    GROUP_DM = 3
    """A direct channel between multiple users."""

    GUILD_CATEGORY = 4
    """An category used for organizing channels in a guild."""

    GUILD_NEWS = 5
    """A channel that can be followed and can crosspost."""

    GUILD_STORE = 6
    """A channel that show's a game's store page."""


@more_enums.must_be_unique
class PermissionOverwriteType(str, more_enums.Enum):
    """The type of entity a Permission Overwrite targets."""

    ROLE = "role"
    """A permission overwrite that targets all the members with a specific role."""

    MEMBER = "member"
    """A permission overwrite that targets a specific guild member."""

    def __str__(self) -> str:
        return self.value


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class PermissionOverwrite(bases.Unique, marshaller.Deserializable, marshaller.Serializable):
    """Represents permission overwrites for a channel or role in a channel."""

    type: PermissionOverwriteType = marshaller.attrib(deserializer=PermissionOverwriteType, serializer=str)
    """The type of entity this overwrite targets."""

    allow: permissions.Permission = marshaller.attrib(
        deserializer=permissions.Permission, serializer=int, default=permissions.Permission(0)
    )
    """The permissions this overwrite allows."""

    deny: permissions.Permission = marshaller.attrib(
        deserializer=permissions.Permission, serializer=int, default=permissions.Permission(0)
    )
    """The permissions this overwrite denies."""

    @property
    def unset(self) -> permissions.Permission:
        """Bitfield of all permissions not explicitly allowed or denied by this overwrite."""
        return typing.cast(permissions.Permission, (self.allow | self.deny))


def register_channel_type(
    type_: ChannelType,
) -> typing.Callable[[typing.Type[PartialChannel]], typing.Type[PartialChannel]]:
    """Generate a decorator for channel classes defined in this library.

    This allows them to associate themselves with a given channel type.

    Parameters
    ----------
    type_ : ChannelType
        The channel type to associate with.

    Returns
    -------
    decorator(T) -> T
        The decorator to decorate the class with.
    """

    def decorator(cls):
        mapping = getattr(register_channel_type, "types", {})
        mapping[type_] = cls
        setattr(register_channel_type, "types", mapping)
        return cls

    return decorator


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class PartialChannel(bases.Unique, marshaller.Deserializable):
    """Represents a channel where we've only received it's basic information.

    This is commonly received in REST responses.
    """

    name: typing.Optional[str] = marshaller.attrib(
        deserializer=str, repr=True, default=None, if_undefined=None, if_none=None
    )
    """The channel's name. This will be missing for DM channels."""

    type: ChannelType = marshaller.attrib(deserializer=ChannelType, repr=True)
    """The channel's type."""


def _deserialize_recipients(payload: more_typing.JSONArray, **kwargs: typing.Any) -> typing.Sequence[users.User]:
    return {bases.Snowflake(user["id"]): users.User.deserialize(user, **kwargs) for user in payload}


@register_channel_type(ChannelType.DM)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class DMChannel(PartialChannel):
    """Represents a DM channel."""

    last_message_id: typing.Optional[bases.Snowflake] = marshaller.attrib(deserializer=bases.Snowflake, if_none=None)
    """The ID of the last message sent in this channel.

    !!! note
        This might point to an invalid or deleted message.
    """

    recipients: typing.Mapping[bases.Snowflake, users.User] = marshaller.attrib(
        deserializer=_deserialize_recipients, inherit_kwargs=True,
    )
    """The recipients of the DM."""


@register_channel_type(ChannelType.GROUP_DM)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GroupDMChannel(DMChannel):
    """Represents a DM group channel."""

    owner_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake, repr=True)
    """The ID of the owner of the group."""

    icon_hash: typing.Optional[str] = marshaller.attrib(raw_name="icon", deserializer=str, if_none=None)
    """The hash of the icon of the group."""

    application_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake, if_undefined=None, default=None
    )
    """The ID of the application that created the group DM, if it's a bot based group DM."""


def _deserialize_overwrites(
    payload: more_typing.JSONArray, **kwargs: typing.Any
) -> typing.Mapping[bases.Snowflake, PermissionOverwrite]:
    return {
        bases.Snowflake(overwrite["id"]): PermissionOverwrite.deserialize(overwrite, **kwargs) for overwrite in payload
    }


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildChannel(PartialChannel):
    """The base for anything that is a guild channel."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake, if_undefined=None, default=None, repr=True
    )
    """The ID of the guild the channel belongs to.

    This will be `None` when received over the gateway in certain events (e.g.
    Guild Create).
    """

    position: int = marshaller.attrib(deserializer=int)
    """The sorting position of the channel."""

    permission_overwrites: PermissionOverwrite = marshaller.attrib(
        deserializer=_deserialize_overwrites, inherit_kwargs=True
    )
    """The permission overwrites for the channel."""

    is_nsfw: typing.Optional[bool] = marshaller.attrib(
        raw_name="nsfw", deserializer=bool, if_undefined=None, default=None
    )
    """Whether the channel is marked as NSFW.

    This will be `None` when received over the gateway in certain events (e.g
    Guild Create).
    """

    parent_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake, if_none=None, if_undefined=None, repr=True
    )
    """The ID of the parent category the channel belongs to."""


@register_channel_type(ChannelType.GUILD_CATEGORY)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildCategory(GuildChannel):
    """Represents a guild category."""


def _deserialize_rate_limit_per_user(payload: int) -> datetime.timedelta:
    return datetime.timedelta(seconds=payload)


@register_channel_type(ChannelType.GUILD_TEXT)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildTextChannel(GuildChannel):
    """Represents a guild text channel."""

    topic: typing.Optional[str] = marshaller.attrib(deserializer=str, if_none=None)
    """The topic of the channel."""

    last_message_id: typing.Optional[bases.Snowflake] = marshaller.attrib(deserializer=bases.Snowflake, if_none=None)
    """The ID of the last message sent in this channel.

    !!! note
        This might point to an invalid or deleted message.
    """

    rate_limit_per_user: datetime.timedelta = marshaller.attrib(deserializer=_deserialize_rate_limit_per_user)
    """The delay (in seconds) between a user can send a message to this channel.

    !!! note
        Bots, as well as users with `MANAGE_MESSAGES` or `MANAGE_CHANNEL`,
        are not affected by this.
    """

    last_pin_timestamp: typing.Optional[datetime.datetime] = marshaller.attrib(
        deserializer=conversions.parse_iso_8601_ts, if_none=None, if_undefined=None
    )
    """The timestamp of the last-pinned message.

    This may be `None` in several cases (currently undocumented clearly by
    Discord).
    """


@register_channel_type(ChannelType.GUILD_NEWS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildNewsChannel(GuildChannel):
    """Represents an news channel."""

    topic: str = marshaller.attrib(deserializer=str, if_none=None)
    """The topic of the channel."""

    last_message_id: typing.Optional[bases.Snowflake] = marshaller.attrib(deserializer=bases.Snowflake, if_none=None)
    """The ID of the last message sent in this channel.

    !!! note
        This might point to an invalid or deleted message.
    """

    last_pin_timestamp: typing.Optional[datetime.datetime] = marshaller.attrib(
        deserializer=conversions.parse_iso_8601_ts, if_none=None, if_undefined=None
    )
    """The timestamp of the last-pinned message.

    This may be `None` in several cases (currently undocumented clearly by
    Discord).
    """


@register_channel_type(ChannelType.GUILD_STORE)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildStoreChannel(GuildChannel):
    """Represents a store channel."""


@register_channel_type(ChannelType.GUILD_VOICE)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class GuildVoiceChannel(GuildChannel):
    """Represents an voice channel."""

    bitrate: int = marshaller.attrib(deserializer=int, repr=True)
    """The bitrate for the voice channel (in bits)."""

    user_limit: int = marshaller.attrib(deserializer=int, repr=True)
    """The user limit for the voice channel."""


class GuildChannelBuilder(marshaller.Serializable):
    """Used to create channel objects to send in guild create requests.

    Parameters
    ----------
    channel_name : str
        The name to set for the channel.
    channel_type : ChannelType
        The type of channel this should build.

    Examples
    --------
        channel_obj = (
            channels.GuildChannelBuilder("Catgirl-appreciation", channels.ChannelType.GUILD_TEXT)
            .is_nsfw(True)
            .with_topic("Here we men of culture appreciate the way of the neko.")
            .with_rate_limit_per_user(datetime.timedelta(seconds=5))
            .with_permission_overwrites([overwrite_obj])
            .with_id(1)
        )
    """

    __slots__ = ("_payload",)

    def __init__(self, channel_name: str, channel_type: ChannelType) -> None:
        self._payload: typing.Dict[str, typing.Any] = {
            "type": channel_type,
            "name": channel_name,
        }

    def serialize(self: GuildChannelBuilder) -> typing.Mapping[str, typing.Any]:
        """Serialize this instance into a payload to send to Discord."""
        return self._payload

    def is_nsfw(self) -> GuildChannelBuilder:
        """Mark this channel as NSFW."""
        self._payload["nsfw"] = True
        return self

    def with_permission_overwrites(self, overwrites: typing.Sequence[PermissionOverwrite]) -> GuildChannelBuilder:
        """Set the permission overwrites for this channel.

        Parameters
        ----------
        overwrites : typing.Sequence[PermissionOverwrite]
            A sequence of overwrite objects to add, where the first overwrite
            object

        !!! note
            Calling this multiple times will overwrite any previously added
            overwrites.
        """
        self._payload["permission_overwrites"] = [o.serialize() for o in overwrites]
        return self

    def with_topic(self, topic: str) -> GuildChannelBuilder:
        """Set the topic for this channel.

        Parameters
        ----------
        topic : str
            The string topic to set.
        """
        self._payload["topic"] = topic
        return self

    def with_bitrate(self, bitrate: int) -> GuildChannelBuilder:
        """Set the bitrate for this channel.

        Parameters
        ----------
        bitrate : int
            The bitrate to set in bits.
        """
        self._payload["bitrate"] = int(bitrate)
        return self

    def with_user_limit(self, user_limit: int) -> GuildChannelBuilder:
        """Set the limit for how many users can be in this channel at once.

        Parameters
        ----------
        user_limit : int
            The user limit to set.
        """
        self._payload["user_limit"] = int(user_limit)
        return self

    def with_rate_limit_per_user(
        self, rate_limit_per_user: typing.Union[datetime.timedelta, int]
    ) -> GuildChannelBuilder:
        """Set the rate limit for users sending messages in this channel.

        Parameters
        ----------
        rate_limit_per_user : typing.Union[datetime.timedelta, int]
            The amount of seconds users will have to wait before sending another
            message in the channel to set.
        """
        self._payload["rate_limit_per_user"] = int(
            rate_limit_per_user.total_seconds()
            if isinstance(rate_limit_per_user, datetime.timedelta)
            else rate_limit_per_user
        )
        return self

    def with_parent_category(self, category: typing.Union[bases.Snowflake, int]) -> GuildChannelBuilder:
        """Set the parent category for this channel.

        Parameters
        ----------
        category : typing.Union[hikari.bases.Snowflake, int]
            The placeholder ID of the category channel that should be this
            channel's parent.
        """
        self._payload["parent_id"] = str(int(category))
        return self

    def with_id(self, channel_id: typing.Union[bases.Snowflake, int]) -> GuildChannelBuilder:
        """Set the placeholder ID for this channel.

        Parameters
        ----------
        channel_id : typing.Union[hikari.bases.Snowflake, int]
            The placeholder ID to use.

        !!! note
            This ID is purely a place holder used for setting parent category
            channels and will have no effect on the created channel's ID.
        """
        self._payload["id"] = str(int(channel_id))
        return self


def deserialize_channel(payload: more_typing.JSONObject, **kwargs: typing.Any) -> typing.Union[GuildChannel, DMChannel]:
    """Deserialize a channel object into the corresponding class.

    !!! warning
        This can only be used to deserialize full channel objects. To
        deserialize a partial object, use `PartialChannel.deserialize`.
    """
    type_id = payload["type"]
    types = getattr(register_channel_type, "types", more_collections.EMPTY_DICT)
    channel_type = types[type_id]
    return channel_type.deserialize(payload, **kwargs)
