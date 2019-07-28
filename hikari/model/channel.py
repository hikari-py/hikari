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

__all__ = (
    "Channel", "GuildChannel", "GuildTextChannel", "DMChannel", "GuildVoiceChannel",
    "GroupDMChannel", "GuildCategory", "GuildNewsChannel", "GuildStoreChannel",
)

import abc
import dataclasses

import abc
import typing

from hikari.model import base, overwrite, user
from hikari.utils import maps


@dataclasses.dataclass()
class Channel(base.SnowflakeMixin, abc.ABC):
    """
    A generic type of channel.
    """

    __slots__ = ("_state", "id")

    _state: typing.Any
    #: The ID of the channel.
    id: int

    @staticmethod
    @abc.abstractmethod
    def from_dict(payload, state):
        """Convert the given payload and state into an object instance."""


@dataclasses.dataclass()
class GuildChannel(Channel, abc.ABC):
    """
    A channel that belongs to a guild.
    """

    __slots__ = ("guild_id", "position", "permission_overwrites", "name")

    #: ID of the guild that owns this channel.
    guild_id: int
    #: The position of the channel in the channel list.
    position: int
    #: A list of permission overwrites for this channel.
    permission_overwrites: typing.List[overwrite.Overwrite]
    #: The name of the channel.
    name: str


@dataclasses.dataclass()
class GuildTextChannel(GuildChannel):
    """
    A text channel.
    """

    __slots__ = ("topic", "rate_limit_per_user", "last_message_id", "nsfw", "parent_id")

    #: The channel topic.
    topic: typing.Optional[str]
    #: How many seconds a user has to wait before sending consecutive messages.
    rate_limit_per_user: int
    #: The optional ID of the last message to be sent.
    last_message_id: typing.Optional[int]
    #: Whether the channel is NSFW or not
    nsfw: bool
    #: The parent ID of the channel, if there is one
    parent_id: typing.Optional[int]

    # noinspection PyMethodOverriding
    @staticmethod
    def from_dict(payload, state):
        return GuildTextChannel(
            _state=state,
            id=maps.get_from_map_as(payload, "id", int),
            guild_id=maps.get_from_map_as(payload, "guild_id", int),
            position=payload["position"],
            permission_overwrites=[NotImplemented for _ in payload["permission_overwrites"]],  # TODO
            name=payload["name"],
            nsfw=payload.get("nsfw", False),
            parent_id=maps.get_from_map_as(payload, "parent_id", int),
            topic=payload.get("topic"),
            rate_limit_per_user=payload.get("rate_limit_per_user"),
            last_message_id=maps.get_from_map_as(payload, "last_message_id", int),
        )


@dataclasses.dataclass()
class DMChannel(Channel):
    """
    A DM channel between users.
    """

    __slots__ = ("last_message_id", "recipients")

    #: The optional ID of the last message to be sent.
    last_message_id: typing.Optional[int]
    #: List of recipients in the DM chat.
    recipients: typing.List[user.User]

    @staticmethod
    def from_dict(payload, state):
        return DMChannel(
            _state=state,
            id=int(payload["id"]),
            last_message_id=maps.get_from_map_as(payload, "last_message_id", int),
            recipients=[NotImplemented for _ in payload["recipients"]],  # TODO
        )


@dataclasses.dataclass()
class GuildVoiceChannel(GuildChannel):
    """
    A voice channel within a guild.
    """

    __slots__ = ("bitrate", "user_limit", "parent_id")

    #: Bit-rate of the voice channel.
    bitrate: int
    #: The max number of users in the voice channel, or None if there is no limit.
    user_limit: typing.Optional[int]
    #: The parent ID of the channel
    parent_id: typing.Optional[int]

    @staticmethod
    def from_dict(payload, state):
        return GuildVoiceChannel(
            _state=state,
            id=maps.get_from_map_as(payload, "id", int),
            guild_id=maps.get_from_map_as(payload, "guild_id", int),
            position=payload["position"],
            permission_overwrites=[NotImplemented for _ in payload["permission_overwrites"]],  # TODO
            name=payload["name"],
            bitrate=payload["bitrate"],
            user_limit=payload["user_limit"] or None,
            parent_id=maps.get_from_map_as(payload, "parent_id", int),
        )


@dataclasses.dataclass()
class GroupDMChannel(DMChannel):
    """
    A DM group chat.
    """

    __slots__ = ("icon_hash", "name", "owner_id", "owner_application_id")

    #: Hash of the icon for the chat, if there is one.
    icon_hash: typing.Optional[str]
    #: Name for the chat, if there is one.
    name: typing.Optional[str]
    #: ID of the owner of the chat.
    owner_id: int
    #: If the chat was made by a bot, this will be the application ID of the bot that made it. For all other cases it
    #: will be `None`.
    owner_application_id: typing.Optional[int]

    @staticmethod
    def from_dict(payload, state):
        return GroupDMChannel(
            state,
            id=maps.get_from_map_as(payload, "id", int),
            last_message_id=payload["last_message_id"],
            recipients=[NotImplemented for _ in payload["recipients"]],  # TODO
            icon_hash=payload.get("icon") if payload["icon"] else None,
            name=payload.get("name"),
            owner_application_id=maps.get_from_map_as(payload, "owner_application_id", int),
            owner_id=maps.get_from_map_as(payload, "owner_id", int),
        )


@dataclasses.dataclass()
class GuildCategory(GuildChannel):
    """
    A category within a guild.
    """
    __slots__ = ()

    @staticmethod
    def from_dict(payload, state):
        return GuildCategory(
            _state=state,
            id=int(payload["id"]),
            guild_id=int(payload["guild_id"]),
            position=payload["position"],
            permission_overwrites=[NotImplemented for _ in payload["permission_overwrites"]],  # TODO
            name=payload["name"],
        )


@dataclasses.dataclass()
class GuildNewsChannel(GuildChannel):
    """
    A channel for news topics within a guild.
    """

    __slots__ = ("topic", "last_message_id", "parent_id", "nsfw")

    #: The channel topic.
    topic: typing.Optional[str]
    #: The optional ID of the last message to be sent.
    last_message_id: typing.Optional[int]
    #: Parent of the channel
    parent_id: typing.Optional[int]
    #: Whether the channel is NSFW or not
    nsfw: bool

    # noinspection PyMethodOverriding
    @staticmethod
    def from_dict(payload, state):
        return GuildNewsChannel(
            _state=state,
            id=maps.get_from_map_as(payload, "id", int),
            guild_id=maps.get_from_map_as(payload, "guild_id", int),
            position=payload["position"],
            permission_overwrites=[NotImplemented for _ in payload["permission_overwrites"]],  # TODO
            name=payload["name"],
            nsfw=payload.get("nsfw", False),
            parent_id=maps.get_from_map_as(payload, "parent_id", int),
            topic=payload.get("topic"),
            last_message_id=maps.get_from_map_as(payload, "last_message_id", int),
        )


@dataclasses.dataclass()
class GuildStoreChannel(GuildChannel):
    """
    A store channel for selling of games within a guild.
    """
    __slots__ = ("parent_id",)
    #: The parent category ID if there is one.
    parent_id: typing.Optional[int]

    @staticmethod
    def from_dict(payload, state):
        return GuildStoreChannel(
            _state=state,
            id=maps.get_from_map_as(payload, "id", int),
            guild_id=maps.get_from_map_as(payload, "guild_id", int),
            position=payload["position"],
            permission_overwrites=[NotImplemented for _ in payload["permission_overwrites"]],  # TODO
            name=payload["name"],
            parent_id=maps.get_from_map_as(payload, "parent_id", int),
        )


def channel_from_dict(payload, state):
    channel_types = [
        GuildTextChannel,
        DMChannel,
        GuildVoiceChannel,
        GroupDMChannel,
        GuildCategory,
        GuildNewsChannel,
        GuildStoreChannel,
    ]

    channel_type = payload["type"]

    try:
        return channel_types[channel_type].from_dict(payload, state)
    except IndexError:
        raise TypeError(f"Invalid channel type {channel_type}") from None
