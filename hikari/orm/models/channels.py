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
"""
Channel models.
"""
from __future__ import annotations

import abc
import enum
import typing

from hikari.internal_utilities import assertions
from hikari.internal_utilities import auto_repr
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import transformations
from hikari.orm import fabric
from hikari.orm.models import guilds as _guild
from hikari.orm.models import interfaces
from hikari.orm.models import overwrites
from hikari.orm.models import users


class ChannelType(interfaces.BestEffortEnumMixin, enum.IntEnum):
    """
    The types of channels returned by the api.
    """

    #: A text channel in a guild.
    GUILD_TEXT = 0

    #: A direct channel between two users.
    DM = 1

    #: A voice channel in a guild.
    GUILD_VOICE = 2

    #: A direct channel between multiple users.
    GROUP_DM = 3

    #: An category used for organizing channels in a guild.
    GUILD_CATEGORY = 4

    #: A channel that can be followed and can crosspost.
    GUILD_ANNOUNCEMENT = 5

    #: A channel that show's a game's store page.
    GUILD_STORE = 6


class Channel(abc.ABC, interfaces.ISnowflake, interfaces.IStatefulModel):
    """
    A generic type of channel.

    Note:
        As part of the contract for this class being volatile, once initialized, the `update_state` method will be
        invoked, thus one should set any dependent fields in the constructor BEFORE invoking super where possible
        or the fields will not be initialized when accessed.
    """

    __slots__ = ("_fabric", "id", "__weakref__")

    #: Channel implementations provided.
    _channel_implementations: typing.ClassVar[typing.Dict[int, typing.Type[Channel]]] = {}

    #: True if the class is a DM channel class, False otherwise.
    #:
    #: :type: :class:`bool`
    is_dm: typing.ClassVar[bool]

    #: The type of the class.
    #:
    #: :type: :class:`ChannelType`
    type: typing.ClassVar[ChannelType]

    #: The ID of the channel.
    #:
    #: :type: :class:`int`
    id: int

    @abc.abstractmethod
    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        self._fabric = fabric_obj
        self.id = int(payload["id"])
        self.update_state(payload)

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if "type" in kwargs:
            cls.type = kwargs.pop("type")
            existing_type = cls._channel_implementations.get(cls.type)
            assertions.assert_that(
                existing_type is None, f"Channel type {cls.type} is already registered to {existing_type}"
            )
            cls._channel_implementations[cls.type] = cls
        cls.is_dm = kwargs.pop("is_dm", NotImplemented)

    @classmethod
    def get_channel_class_from_type(cls, type: typing.Union[ChannelType, int]) -> typing.Optional[typing.Type[Channel]]:
        return cls._channel_implementations.get(type)


class PartialChannel(Channel):
    """
    A generic partial Channel object used when we only know a channel's name and type.
    """

    __slots__ = ("name", "type")

    #: The name of the channel.
    #:
    #: :type: :class:`str`
    name: str

    #: The type of channel this represents.
    #:
    #: :type: :class:`ChannelType` or :class:`int`
    type: typing.Union[ChannelType, int]

    __repr__ = auto_repr.repr_of("id", "name", "type")

    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        self.name = payload["name"]
        self.type = ChannelType.get_best_effort_from_value(payload["type"])
        super().__init__(fabric_obj, payload)


class TextChannel(Channel, abc.ABC):
    """
    Any class that can have messages sent to it.

    This class itself will not behave as a dataclass, and is a trait for Channels that have the ability to
    send and receive messages to implement as a basic interface.
    """

    __slots__ = ()

    #: The optional ID of the last message to be sent.
    #:
    #: :type: :class:`int` or `None`
    last_message_id: typing.Optional[int]


class GuildChannel(Channel, is_dm=False):
    """
    A channel that belongs to a guild.
    """

    __slots__ = ("guild_id", "position", "permission_overwrites", "name", "parent_id")

    #: The guild's ID.
    #:
    #: :type: :class:`int`
    guild_id: int

    #: The parent channel ID.
    #:
    #: :type: :class:`int` or :class:`None`
    parent_id: typing.Optional[int]

    #: The position of the channel in the channel list.
    #:
    #: :type: :class:`int`
    position: int

    #: A sequence t of permission overwrites for this channel.
    #:
    #: :type: :class:`typing.Sequence` of :attr:`hikari.orm.models.overwrites.Overwrite`
    permission_overwrites: typing.Sequence[overwrites.Overwrite]

    #: The name of the channel.
    #:
    #: :type: :class:`str`
    name: str

    @abc.abstractmethod
    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        self.guild_id = int(payload["guild_id"])
        super().__init__(fabric_obj, payload)

    def update_state(self, payload: data_structures.DiscordObjectT) -> None:
        self.position = int(payload["position"])

        overwrite_objs = []

        for raw_overwrite in payload["permission_overwrites"]:
            overwrite_obj = overwrites.Overwrite(raw_overwrite)
            overwrite_objs.append(overwrite_obj)

        self.permission_overwrites = overwrite_objs
        self.name = payload["name"]
        self.parent_id = transformations.nullable_cast(payload.get("parent_id"), int)

    @property
    def guild(self) -> _guild.Guild:
        return self._fabric.state_registry.get_guild_by_id(self.guild_id)

    @property
    def parent(self) -> typing.Optional[GuildCategory]:
        return self.guild.channels[self.parent_id] if self.parent_id is not None else None


class GuildTextChannel(GuildChannel, TextChannel, type=ChannelType.GUILD_TEXT, is_dm=False):
    """
    A text channel.
    """

    __slots__ = ("topic", "rate_limit_per_user", "last_message_id", "is_nsfw")

    #: The channel topic.
    #:
    #: :type: :class:`str` or `None`
    topic: typing.Optional[str]

    #: How many seconds a user has to wait before sending consecutive messages.
    #:
    #: :type: :class:`int`
    rate_limit_per_user: int

    #: The optional ID of the last message to be sent.
    #:
    #: :type: :class:`int` or `None`
    last_message_id: typing.Optional[int]

    #: Whether the channel is NSFW or not
    #:
    #: :type: :class:`bool`
    is_nsfw: bool

    __repr__ = auto_repr.repr_of("id", "name", "guild.name", "is_nsfw")

    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        super().__init__(fabric_obj, payload)

    def update_state(self, payload: data_structures.DiscordObjectT) -> None:
        super().update_state(payload)
        self.is_nsfw = payload.get("nsfw", False)
        self.topic = payload.get("topic")
        self.rate_limit_per_user = payload.get("rate_limit_per_user", 0)
        self.last_message_id = transformations.nullable_cast(payload.get("last_message_id"), int)


class DMChannel(TextChannel, type=ChannelType.DM, is_dm=True):
    """
    A DM channel between users.
    """

    __slots__ = ("last_message_id", "recipients")

    #: The optional ID of the last message to be sent.
    #:
    #: :type: :class:`int` or `None`
    last_message_id: typing.Optional[int]

    #: Sequence of recipients in the DM chat.
    #:
    #: :type: :class:`typing.Sequence` of :class:`hikari.orm.models.users.User`
    recipients: typing.Sequence[users.User]

    __repr__ = auto_repr.repr_of("id")

    # noinspection PyMissingConstructor
    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        super().__init__(fabric_obj, payload)

    def update_state(self, payload: data_structures.DiscordObjectT) -> None:
        super().update_state(payload)
        self.last_message_id = transformations.nullable_cast(payload.get("last_message_id"), int)
        self.recipients = [self._state.parse_user(u) for u in payload.get("recipients", data_structures.EMPTY_SEQUENCE)]


class GuildVoiceChannel(GuildChannel, type=ChannelType.GUILD_VOICE, is_dm=False):
    """
    A voice channel within a guild.
    """

    __slots__ = ("bitrate", "user_limit")

    #: Bit-rate of the voice channel.
    #:
    #: :type: :class:`int`
    bitrate: int

    #: The max number of users in the voice channel, or None if there is no limit.
    #:
    #: :type: :class:`int` or `None`
    user_limit: typing.Optional[int]

    __repr__ = auto_repr.repr_of("id", "name", "guild.name", "bitrate", "user_limit")

    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        super().__init__(fabric_obj, payload)

    def update_state(self, payload: data_structures.DiscordObjectT) -> None:
        super().update_state(payload)
        self.bitrate = payload.get("bitrate") or None
        self.user_limit = payload.get("user_limit") or None


class GroupDMChannel(DMChannel, type=ChannelType.GROUP_DM, is_dm=True):
    """
    A DM group chat.
    """

    __slots__ = ("icon_hash", "name", "owner_id", "owner_application_id")

    #: The ID of the person or application that owns this channel currently.
    #:
    #: :type: :class:`int`
    owner_id: int

    #: Hash of the icon for the chat, if there is one.
    #:
    #: :type: :class:`str` or `None`
    icon_hash: typing.Optional[str]

    #: Name for the chat, if there is one.
    #:
    #: :type: :class:`str` or `None`
    name: typing.Optional[str]

    #: If the chat was made by a bot, this will be the application ID of the bot that made it. For all other cases it
    #: will be `None`.
    #:
    #: :type: :class:`int` or `None`
    owner_application_id: typing.Optional[int]

    __repr__ = auto_repr.repr_of("id", "name")

    # noinspection PyMissingConstructor
    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        super().__init__(fabric_obj, payload)

    def update_state(self, payload: data_structures.DiscordObjectT) -> None:
        super().update_state(payload)
        self.icon_hash = payload.get("icon")
        self.name = payload.get("name")
        self.owner_application_id = transformations.nullable_cast(payload.get("application_id"), int)
        self.owner_id = transformations.nullable_cast(payload.get("owner_id"), int)


class GuildCategory(GuildChannel, type=ChannelType.GUILD_CATEGORY, is_dm=False):
    """
    A category within a guild.
    """

    __slots__ = ()

    __repr__ = auto_repr.repr_of("id", "name", "guild.name")

    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        super().__init__(fabric_obj, payload)


class GuildAnnouncementChannel(GuildChannel, type=ChannelType.GUILD_ANNOUNCEMENT, is_dm=False):
    """
    A channel for announcement topics within a guild.

    Note:
        This channel type may also be known as a `news channel` internally. However, this was
        announced to be renamed on August 22nd, 2019 by
        this changelog entry: https://discordapp.com/developers/docs/change-log#august-22-2019
    """

    __slots__ = ("topic", "last_message_id", "is_nsfw")

    #: The channel topic.
    #:
    #: :type: :class:`str` or `None`
    topic: typing.Optional[str]

    #: The optional ID of the last message to be sent.
    #:
    #: :type: :class:`int` or `None`
    last_message_id: typing.Optional[int]

    #: Whether the channel is NSFW or not
    #:
    #: :type: :class:`bool`
    is_nsfw: bool

    __repr__ = auto_repr.repr_of("id", "name", "guild.name", "is_nsfw")

    # noinspection PyMissingConstructor
    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        super().__init__(fabric_obj, payload)

    def update_state(self, payload: data_structures.DiscordObjectT) -> None:
        super().update_state(payload)
        self.is_nsfw = payload.get("nsfw", False)
        self.topic = payload.get("topic")
        self.last_message_id = transformations.nullable_cast(payload.get("last_message_id"), int)


class GuildStoreChannel(GuildChannel, type=ChannelType.GUILD_STORE, is_dm=False):
    """
    A store channel for selling of games within a guild.
    """

    __slots__ = ()

    __repr__ = auto_repr.repr_of("id", "name", "guild.name")

    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        super().__init__(fabric_obj, payload)


# noinspection PyProtectedMember
def is_channel_type_dm(channel_type: int) -> bool:
    """
    Returns True if a raw channel type is for a DM. If a channel type is given that is not recognised, then it returns
    `False` regardless.

    This is only used internally, there is no other reason for you to use this outside of framework-internal code.
    """
    return getattr(Channel._channel_implementations.get(channel_type), "is_dm", False)


# noinspection PyProtectedMember
def parse_channel(fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> Channel:
    """
    Parse a channel from a channel payload from an API call.

    Args:
        fabric_obj:
            the global fabric.
        payload:
            the payload to parse.

    Returns:
        A subclass of :class:`Channel` as appropriate for the given payload provided.
    """
    channel_type = payload.get("type")

    if channel_type in Channel._channel_implementations:
        channel_type = Channel._channel_implementations[channel_type]
        channel = channel_type(fabric_obj, payload)
        return channel
    else:
        raise TypeError(f"Invalid channel type {channel_type}") from None


__all__ = (
    "ChannelType",
    "Channel",
    "PartialChannel",
    "GuildChannel",
    "GuildTextChannel",
    "DMChannel",
    "GuildVoiceChannel",
    "GroupDMChannel",
    "GuildCategory",
    "GuildAnnouncementChannel",
    "GuildStoreChannel",
)
