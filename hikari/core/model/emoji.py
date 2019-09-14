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
import dataclasses
import typing

from hikari.core.model import base
from hikari.core.model import model_cache
from hikari.core.utils import types


class Emoji(abc.ABC):
    """Base for any emoji type."""

    __slots__ = ()


@dataclasses.dataclass()
class UnicodeEmoji(Emoji):
    """
    An emoji that consists of one or more unicode characters. This is just a string with some extra pieces of
    information included.
    """

    __slots__ = ("value",)

    value: str

    def __init__(self, payload: types.DiscordObject) -> None:
        self.value = payload["name"]

    def __eq__(self, other):
        return self.value == other

    def __ne__(self, other):
        return not (self.value == other)

    def __str__(self):
        return self.value


@dataclasses.dataclass()
class UnknownEmoji(Emoji, base.Snowflake):
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

    def __init__(self, payload: types.DiscordObject) -> None:
        self.id = int(payload["id"])
        self.name = payload["name"]


@dataclasses.dataclass()
class GuildEmoji(UnknownEmoji):
    __slots__ = ("_state", "_role_ids", "_guild_id", "require_colons", "managed", "animated", "user", "__weakref__")

    _state: model_cache.AbstractModelCache
    _role_ids: typing.List[int]
    _guild_id: typing.Optional[int]

    #: `True` if the emoji requires colons to be mentioned; `False` otherwise.
    #:
    #: :type: :class:`bool`
    require_colons: bool

    #: The user who made the object, if available.
    #:
    #: :type: :class:`hikari.core.model.user.User` or `None`
    user: typing.Optional[user.User]

    #: `True` if the emoji is managed as part of an integration with Twitch, `False` otherwise.
    #:
    #: :type: :class:`bool`
    managed: bool

    #: `True` if the emoji is animated; `False` otherwise.
    #:
    #: :type: :class:`bool
    animated: bool

    def __init__(
        self, global_state: model_cache.AbstractModelCache, payload: types.DiscordObject, guild_id: int
    ) -> None:
        super().__init__(payload)
        self._state = global_state
        self._role_ids = [int(r) for r in payload.get("roles", [])]
        self._guild_id = guild_id
        self.require_colons = payload.get("require_colons", True)
        self.animated = payload.get("animated", False)
        self.managed = payload.get("managed", False)
        self.user = global_state.parse_user(payload.get("user")) if "user" in payload else None


def emoji_from_dict(
    global_state: model_cache.AbstractModelCache, payload: types.DiscordObject, guild_id: typing.Optional[int] = None
) -> typing.Union[UnicodeEmoji, UnknownEmoji, GuildEmoji]:
    if payload.get("id") is None:
        return UnicodeEmoji(payload)
    elif payload.get("animated") is None:
        return UnknownEmoji(payload)
    else:
        return GuildEmoji(global_state, payload, guild_id)


__all__ = ["UnicodeEmoji", "UnknownEmoji", "GuildEmoji"]
