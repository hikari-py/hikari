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

from hikari.state import state_registry
from hikari.state.models import interfaces
from hikari.state.models import guilds
from hikari.internal_utilities import auto_repr
from hikari.internal_utilities import data_structures


class Emoji(interfaces.IStateful, abc.ABC):
    """Base for any emoji type."""

    __slots__ = ()

    @abc.abstractmethod
    def __init__(self):
        ...

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

    __repr__ = auto_repr.repr_of("value")

    @property
    def is_unicode(self) -> bool:
        return True

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.value = payload["name"]

    def __eq__(self, other):
        if isinstance(other, Emoji):
            return other.value == self.value
        return other == self.value

    def __ne__(self, other):
        return not (self.value == other)

    def __str__(self):
        return self.value


class UnknownEmoji(Emoji, interfaces.ISnowflake):
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

    __repr__ = auto_repr.repr_of("id", "name")

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.id = int(payload["id"])
        self.name = payload["name"]

    @property
    def is_unicode(self) -> bool:
        return False


class GuildEmoji(UnknownEmoji):
    """
    Represents an AbstractEmoji in a guild that the user is a member of.
    """

    __slots__ = ("_state", "_role_ids", "_guild_id", "require_colons", "managed", "animated", "user", "__weakref__")

    _state: state_registry.IStateRegistry
    _role_ids: typing.Sequence[int]
    _guild_id: typing.Optional[int]

    #: `True` if the emoji requires colons to be mentioned; `False` otherwise.
    #:
    #: :type: :class:`bool`
    require_colons: bool

    #: The user who made the object, if available.
    #:
    #: :type: :class:`hikari.core.models.users.User` or `None`
    user: typing.Optional[user.User]

    #: `True` if the emoji is managed as part of an integration with Twitch, `False` otherwise.
    #:
    #: :type: :class:`bool`
    managed: bool

    #: `True` if the emoji is animated; `False` otherwise.
    #:
    #: :type: :class:`bool
    animated: bool

    __repr__ = auto_repr.repr_of("id", "name", "animated")

    def __init__(
        self, global_state: state_registry.IStateRegistry, payload: data_structures.DiscordObjectT, guild_id: int
    ) -> None:
        super().__init__(payload)
        self._state = global_state
        self._guild_id = guild_id
        self.user = global_state.parse_user(payload.get("user")) if "user" in payload else None
        self.require_colons = payload.get("require_colons", True)
        self.animated = payload.get("animated", False)
        self.managed = payload.get("managed", False)
        self._role_ids = [int(r) for r in payload.get("roles", data_structures.EMPTY_SEQUENCE)]

    @property
    def guild(self) -> guilds.Guild:
        return self._state.get_guild_by_id(self._guild_id)


def is_payload_guild_emoji_candidate(payload: data_structures.DiscordObjectT) -> bool:
    """
    Returns True if the given dict represents an emoji that is from a guild we actively reside in.

    Warning:
        This is only used internally, you do not have any reason to call this from your code. You should use
        `isinstance` instead on actual emoji instances.
    """
    return "id" in payload and "animated" in payload


def parse_emoji(
    global_state: state_registry.IStateRegistry,
    payload: data_structures.DiscordObjectT,
    guild_id: typing.Optional[int] = None,
) -> typing.Union[UnicodeEmoji, UnknownEmoji, GuildEmoji]:
    """
    Parse the given emoji payload into an appropriate implementation of Emoji.

    Args:
        global_state:
            The global state object.
        payload:
            the payload to parse.
        guild_id:
            the owning guild of the emoji if known and appropriate, otherwise `None`.

    Returns:
        One of :class:`UnicodeEmoji`, :class:`UnknownEmoji`, :class:`GuildEmoji`.
    """
    if is_payload_guild_emoji_candidate(payload) and guild_id is not None:
        return GuildEmoji(global_state, payload, guild_id)
    elif payload.get("id") is not None:
        return UnknownEmoji(payload)
    else:
        return UnicodeEmoji(payload)


__all__ = ["Emoji", "UnicodeEmoji", "UnknownEmoji", "GuildEmoji"]
