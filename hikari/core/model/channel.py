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

import typing

from hikari.core.model import base
from hikari.core.model import guild as _guild
from hikari.core.model import overwrite
from hikari.core.model import user
from hikari.core.utils import transform

_channel_type_to_class = {}


@base.dataclass()
class Channel(base.Snowflake, abc.ABC):
    """
    A generic type of channel.
    """

    __slots__ = ("_state", "id")

    _state: typing.Any

    #: The ID of the channel.
    #:
    #: :type: :class:`int`
    id: int

    def __init_subclass__(cls, **kwargs):
        if "type" in kwargs:
            _channel_type_to_class[kwargs.pop("type")] = cls

    @staticmethod
    @abc.abstractmethod
    def from_dict(payload, state):
        """Convert the given payload and state into an object instance."""

    @property
    @abc.abstractmethod
    def is_dm(self) -> bool:
        """Return True if this is a DM."""
        ...


@base.dataclass()
class GuildChannel(Channel, abc.ABC):
    """
    A channel that belongs to a guild.
    """

    __slots__ = ("_guild_id", "position", "permission_overwrites", "name")

    _guild_id: int

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

    @property
    def is_dm(self) -> bool:
        return False

    @property
    def guild(self) -> _guild.Guild:
        return self._state.get_guild_by_id(self._guild_id)

    @property
    def parent(self) -> typing.Optional[GuildCategory]:
        parent_id = getattr(self, "_parent_id", None)
        if parent_id is not None:
            return self.guild.channels.get(parent_id)
        return None


@base.dataclass()
class GuildTextChannel(GuildChannel, type=0):
    """
    A text channel.
    """

    __slots__ = ("topic", "rate_limit_per_user", "last_message_id", "nsfw", "_parent_id")

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

    # noinspection PyMethodOverriding
    @staticmethod
    def from_dict(global_state, payload):
        return GuildTextChannel(
            _state=global_state,
            id=transform.get_cast(payload, "id", int),
            _guild_id=transform.get_cast(payload, "guild_id", int),
            position=payload.get("position"),
            permission_overwrites=transform.get_sequence(payload, "permission_overwrites", overwrite.Overwrite),
            name=payload.get("name"),
            nsfw=payload.get("nsfw", False),
            _parent_id=transform.get_cast(payload, "parent_id", int),
            topic=payload.get("topic"),
            rate_limit_per_user=payload.get("rate_limit_per_user"),
            last_message_id=transform.get_cast(payload, "last_message_id", int),
        )


@base.dataclass()
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

    @staticmethod
    def from_dict(global_state, payload):
        return DMChannel(
            _state=global_state,
            id=transform.get_cast(payload, "id", int),
            last_message_id=transform.get_cast(payload, "last_message_id", int),
            recipients=transform.get_sequence(payload, "recipients", global_state.parse_user),
        )

    @property
    def is_dm(self) -> bool:
        return True


@base.dataclass()
class GuildVoiceChannel(GuildChannel, type=2):
    """
    A voice channel within a guild.
    """

    __slots__ = ("bitrate", "user_limit", "_parent_id")

    _parent_id: typing.Optional[int]

    #: Bit-rate of the voice channel.
    #:
    #: :type: :class:`int`
    bitrate: int

    #: The max number of users in the voice channel, or None if there is no limit.
    #:
    #: :type: :class:`int` or `None`
    user_limit: typing.Optional[int]

    @staticmethod
    def from_dict(global_state, payload):
        return GuildVoiceChannel(
            _state=global_state,
            id=transform.get_cast(payload, "id", int),
            _guild_id=transform.get_cast(payload, "guild_id", int),
            position=payload.get("position"),
            permission_overwrites=transform.get_sequence(payload, "permission_overwrites", overwrite.Overwrite),
            name=payload.get("name"),
            bitrate=payload.get("bitrate"),
            user_limit=payload.get("user_limit") or None,
            _parent_id=transform.get_cast(payload, "parent_id", int),
        )


@base.dataclass()
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

    @staticmethod
    def from_dict(global_state, payload):
        return GroupDMChannel(
            global_state,
            id=transform.get_cast(payload, "id", int),
            last_message_id=transform.get_cast(payload, "last_message_id", int),
            recipients=transform.get_sequence(payload, "recipients", repr),  # TODO: implement
            icon_hash=payload.get("icon"),
            name=payload.get("name"),
            owner_application_id=transform.get_cast(payload, "owner_application_id", int),
            _owner_id=transform.get_cast(payload, "owner_id", int),
        )


@base.dataclass()
class GuildCategory(GuildChannel, type=4):
    """
    A category within a guild.
    """

    __slots__ = ()

    @staticmethod
    def from_dict(global_state, payload):
        return GuildCategory(
            _state=global_state,
            id=transform.get_cast(payload, "id", int),
            _guild_id=transform.get_cast(payload, "guild_id", int),
            position=transform.get_cast(payload, "position", int),
            permission_overwrites=transform.get_sequence(payload, "permission_overwrites", overwrite.Overwrite),
            name=payload.get("name"),
        )


@base.dataclass()
class GuildNewsChannel(GuildChannel, type=5):
    """
    A channel for news topics within a guild.
    """

    __slots__ = ("topic", "last_message_id", "_parent_id", "nsfw")

    _parent_id: typing.Optional[int]

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

    # noinspection PyMethodOverriding
    @staticmethod
    def from_dict(global_state, payload):
        return GuildNewsChannel(
            _state=global_state,
            id=transform.get_cast(payload, "id", int),
            _guild_id=transform.get_cast(payload, "guild_id", int),
            position=transform.get_cast(payload, "position", int),
            permission_overwrites=transform.get_sequence(payload, "permission_overwrites", overwrite.Overwrite),
            name=payload.get("name"),
            nsfw=payload.get("nsfw", False),
            _parent_id=transform.get_cast(payload, "parent_id", int),
            topic=payload.get("topic"),
            last_message_id=transform.get_cast(payload, "last_message_id", int),
        )


@base.dataclass()
class GuildStoreChannel(GuildChannel, type=6):
    """
    A store channel for selling of games within a guild.
    """

    __slots__ = ("_parent_id",)

    _parent_id: typing.Optional[int]

    @staticmethod
    def from_dict(global_state, payload):
        return GuildStoreChannel(
            _state=global_state,
            id=transform.get_cast(payload, "id", int),
            _guild_id=transform.get_cast(payload, "guild_id", int),
            position=transform.get_cast(payload, "position", int),
            permission_overwrites=transform.get_sequence(payload, "permission_overwrites", overwrite.Overwrite),
            name=payload.get("name"),
            _parent_id=transform.get_cast(payload, "parent_id", int),
        )


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

    try:
        return _channel_type_to_class[channel_type].from_dict(global_state, payload)
    except KeyError:
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
