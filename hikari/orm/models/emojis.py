#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
# GNU Lesser General Public License for more details.7
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""
Types of emoji.
"""
from __future__ import annotations

import abc
import typing

from hikari.internal_utilities import containers
from hikari.internal_utilities import reprs
from hikari.orm import fabric
from hikari.orm.models import guilds
from hikari.orm.models import bases


class Emoji(bases.BaseModel, abc.ABC):
    """Base for any emoji type."""

    __slots__ = ()

    __init__ = NotImplemented

    @property
    @abc.abstractmethod
    def is_unicode(self) -> bool:
        """True if the emoji is a unicode emoji, false otherwise."""


class UnicodeEmoji(Emoji):
    """
    An emoji that consists of one or more unicode characters. This is just a string with some extra pieces of
    information included.
    """

    __slots__ = ("value",)

    #: The unicode string value for the emoji.
    #:
    #: :type: :class:`str`
    value: str

    __repr__ = reprs.repr_of("value")

    @property
    def is_unicode(self) -> bool:
        return True

    def __init__(self, payload: containers.DiscordObjectT) -> None:
        self.value = payload["name"]

    def __eq__(self, other):
        if isinstance(other, Emoji):
            return other.value == self.value
        return other == self.value

    def __ne__(self, other):
        return not (self.value == other)

    def __str__(self):
        return self.value


class UnknownEmoji(Emoji, bases.SnowflakeMixin):
    """
    A custom emoji that we do not know anything about other than the ID and name. These usually occur as a result
    of messages being sent by Nitro users, emojis from public emoji servers, and as reactions to a message by nitro
    users.
    """

    __slots__ = ("id", "name")

    #: The snowflake ID of the emoji.
    #:
    #: :type: :class:`int`.
    id: int

    #: The name of the emoji.
    #:
    #: :type: :class:`str`
    name: str

    __repr__ = reprs.repr_of("id", "name")

    def __init__(self, payload: containers.DiscordObjectT) -> None:
        self.id = int(payload["id"])
        self.name = payload["name"]

    @property
    def is_unicode(self) -> bool:
        return False


class GuildEmoji(UnknownEmoji, bases.BaseModelWithFabric):
    """
    Represents an emoji in a guild that the user is a member of.
    """

    __slots__ = (
        "_fabric",
        "_role_ids",
        "_guild_id",
        "is_requiring_colons",
        "is_managed",
        "is_animated",
        "user",
        "__weakref__",
    )

    _role_ids: typing.Sequence[int]
    _guild_id: typing.Optional[int]

    #: `True` if the emoji requires colons to be mentioned; `False` otherwise.
    #:
    #: :type: :class:`bool`
    is_requiring_colons: bool

    #: The user who made the object, if available.
    #:
    #: :type: :class:`hikari.orm.models.users.User` or `None`
    user: typing.Optional[user.User]

    #: `True` if the emoji is managed as part of an integration with Twitch, `False` otherwise.
    #:
    #: :type: :class:`bool`
    is_managed: bool

    #: `True` if the emoji is animated; `False` otherwise.
    #:
    #: :type: :class:`bool`
    is_animated: bool

    __repr__ = reprs.repr_of("id", "name", "is_animated")

    def __init__(self, fabric_obj: fabric.Fabric, payload: containers.DiscordObjectT, guild_id: int) -> None:
        super().__init__(payload)
        self._fabric = fabric_obj
        self._guild_id = guild_id
        self.user = fabric_obj.state_registry.parse_user(payload.get("user")) if "user" in payload else None
        self.is_requiring_colons = payload.get("require_colons", True)
        self.is_animated = payload.get("animated", False)
        self.is_managed = payload.get("managed", False)
        self._role_ids = [int(r) for r in payload.get("roles", containers.EMPTY_SEQUENCE)]

    @property
    def guild(self) -> guilds.Guild:
        return self._fabric.state_registry.get_guild_by_id(self._guild_id)


def is_payload_guild_emoji_candidate(payload: containers.DiscordObjectT) -> bool:
    """
    Returns True if the given dict represents an emoji that is from a guild we actively reside in.

    Warning:
        This is only used internally, you do not have any reason to call this from your code. You should use
        `isinstance` instead on actual emoji instances.
    """
    return "id" in payload and "animated" in payload


def parse_emoji(
    fabric_obj: fabric.Fabric, payload: containers.DiscordObjectT, guild_id: typing.Optional[int] = None
) -> typing.Union[UnicodeEmoji, UnknownEmoji, GuildEmoji]:
    """
    Parse the given emoji payload into an appropriate implementation of Emoji.

    Args:
        fabric_obj:
            The global fabric.
        payload:
            the payload to parse.
        guild_id:
            the owning guild of the emoji if known and appropriate, otherwise `None`.

    Returns:
        One of :class:`UnicodeEmoji`, :class:`UnknownEmoji`, :class:`GuildEmoji`.
    """
    if is_payload_guild_emoji_candidate(payload) and guild_id is not None:
        return GuildEmoji(fabric_obj, payload, guild_id)
    elif payload.get("id") is not None:
        return UnknownEmoji(payload)
    else:
        return UnicodeEmoji(payload)


#: The type of a known emoji.
KnownEmojiT = typing.Union[UnicodeEmoji, GuildEmoji]

#: A :class:`GuildEmoji`, or an :class:`int`/:class:`str` ID of one.
GuildEmojiLikeT = typing.Union[bases.RawSnowflakeT, GuildEmoji]

#: A :class:`GuildEmoji`, an :class:`int` ID of one, a :class:`UnicodeEmoji`, or a :class:`str` representation of one.
KnownEmojiLikeT = typing.Union[int, str, KnownEmojiT]


__all__ = ["Emoji", "UnicodeEmoji", "UnknownEmoji", "GuildEmoji", "KnownEmojiT", "GuildEmojiLikeT", "KnownEmojiLikeT"]
