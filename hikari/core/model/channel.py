#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
import dataclasses
import typing

from hikari.core.model import base
from hikari.core.model import guild as _guild
from hikari.core.model import overwrite
from hikari.core.model import user
from hikari.core.utils import transform

_channel_type_to_class = {}


@dataclasses.dataclass()
class Channel(base.Snowflake, abc.ABC):
    """
    A generic type of channel.
    """

    __slots__ = ("_state", "id")

    _state: typing.Any

    #: True if the implementation is a DM channel, or False otherwise.
    #:
    #: :type: :class:`bool`
    is_dm: typing.ClassVar[bool]

    #: The ID of the channel.
    #:
    #: :type: :class:`int`
    id: int

    def __init__(self, global_state, payload):
        self._state = global_state
        self.id = int(payload["id"])

    def __init_subclass__(cls, **kwargs):
        if "type" in kwargs:
            _channel_type_to_class[kwargs.pop("type")] = cls
        cls.is_dm = "guild" not in cls.__qualname__.lower()


@dataclasses.dataclass()
class GuildChannel(Channel, abc.ABC):
    """
    A channel that belongs to a guild.
    """

    __slots__ = ("_guild_id", "position", "permission_overwrites", "name", "_parent_id")

    _guild_id: int
    _parent_id: typing.Optional[int]

    #: The position of the channel in the channel list.
    #:
    #: :type: :class:`int`
    position: int

    #: A list of permission overwrites for this channel.
    #:
    #: :type: :class:`list` of :attr:`hikari.core.model.overwrite.Overwrite`
    permission_overwrites: typing.List[overwrite.Overwrite]

    #: The name of the channel.
    #:
    #: :type: :class:`str`
    name: str

    def __init__(self, global_state, payload):
        super().__init__(global_state, payload)
        self._guild_id = int(payload["guild_id"])
        self.position = int(payload["position"])

        overwrites = []
        for raw_overwrite in payload["permission_overwrites"]:
            overwrite_obj = overwrite.Overwrite(raw_overwrite)
            overwrites.append(overwrite_obj)

        self.permission_overwrites = overwrites
        self.name = payload["name"]
        self._parent_id = transform.nullable_cast(payload.get("parent_id"), int)

    @property
    def guild(self) -> _guild.Guild:
        return self._state.get_guild_by_id(self._guild_id)

    @property
    def parent(self) -> typing.Optional[GuildCategory]:
        return self.guild.channels[self._parent_id] if self._parent_id is not None else None


@dataclasses.dataclass()
class GuildTextChannel(GuildChannel, type=0):
    """
    A text channel.
    """

    __slots__ = ("topic", "rate_limit_per_user", "last_message_id", "nsfw")

    _parent_id: typing.Optional[int]

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
    nsfw: bool

    # noinspection PyMissingConstructor
    def __init__(self, global_state, payload):
        super().__init__(global_state, payload)
        self.nsfw = payload.get("nsfw", False)
        self.topic = payload.get("topic")
        self.rate_limit_per_user = payload.get("rate_limit_per_user", 0)
        self.last_message_id = transform.nullable_cast(payload.get("last_message_id"), int)


@dataclasses.dataclass()
class DMChannel(Channel, type=1):
    """
    A DM channel between users.
    """

    __slots__ = ("last_message_id", "recipients")

    #: The optional ID of the last message to be sent.
    #:
    #: :type: :class:`int` or `None`
    last_message_id: typing.Optional[int]

    #: List of recipients in the DM chat.
    #:
    #: :type: :class:`list` of :class:`hikari.core.model.user.User`
    recipients: typing.List[user.User]

    # noinspection PyMissingConstructor
    def __init__(self, global_state, payload):
        super().__init__(global_state, payload)
        self.last_message_id = transform.nullable_cast(payload.get("last_message_id"), int)
        self.recipients = [global_state.parse_user(u) for u in payload.get("recipients", ())]


@dataclasses.dataclass()
class GuildVoiceChannel(GuildChannel, type=2):
    """
    A voice channel within a guild.
    """

    __slots__ = ("bitrate", "user_limit")

    _parent_id: typing.Optional[int]

    #: Bit-rate of the voice channel.
    #:
    #: :type: :class:`int`
    bitrate: int

    #: The max number of users in the voice channel, or None if there is no limit.
    #:
    #: :type: :class:`int` or `None`
    user_limit: typing.Optional[int]

    # noinspection PyMissingConstructor
    def __init__(self, global_state, payload):
        super().__init__(global_state, payload)
        self.bitrate = payload.get("bitrate") or None
        self.user_limit = payload.get("user_limit") or None


@dataclasses.dataclass()
class GroupDMChannel(DMChannel, type=3):
    """
    A DM group chat.
    """

    __slots__ = ("icon_hash", "name", "_owner_id", "owner_application_id")

    _owner_id: int

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

    # noinspection PyMissingConstructor
    def __init__(self, global_state, payload):
        super().__init__(global_state, payload)
        self.icon_hash = payload.get("icon")
        self.name = payload.get("name")
        self.owner_application_id = transform.nullable_cast(payload.get("application_id"), int)
        self._owner_id = transform.nullable_cast(payload.get("owner_id"), int)


@dataclasses.dataclass(init=False)
class GuildCategory(GuildChannel, type=4):
    """
    A category within a guild.
    """

    __slots__ = ()


@dataclasses.dataclass()
class GuildNewsChannel(GuildChannel, type=5):
    """
    A channel for news topics within a guild.
    """

    __slots__ = ("topic", "last_message_id", "nsfw")

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
    nsfw: bool

    # noinspection PyMissingConstructor
    def __init__(self, global_state, payload):
        super().__init__(global_state, payload)
        self.nsfw = payload.get("nsfw", False)
        self.topic = payload.get("topic")
        self.last_message_id = transform.nullable_cast(payload.get("last_message_id"), int)


@dataclasses.dataclass(init=False)
class GuildStoreChannel(GuildChannel, type=6):
    """
    A store channel for selling of games within a guild.
    """

    __slots__ = ()


def channel_from_dict(
    global_state, payload
) -> typing.Union[
    GuildTextChannel, DMChannel, GuildVoiceChannel, GroupDMChannel, GuildCategory, GuildNewsChannel, GuildStoreChannel
]:
    """
    Parse a channel from a channel payload from an API call.

    This returns an instance of the class that corresponds to the given channel type in the payload.
    """
    channel_type = payload.get("type")

    if channel_type in _channel_type_to_class:
        channel_type = _channel_type_to_class[channel_type]
        channel = channel_type(global_state, payload)
        return channel
    else:
        raise TypeError(f"Invalid channel type {channel_type}") from None


__all__ = (
    "Channel",
    "GuildChannel",
    "GuildTextChannel",
    "DMChannel",
    "GuildVoiceChannel",
    "GroupDMChannel",
    "GuildCategory",
    "GuildNewsChannel",
    "GuildStoreChannel",
)
