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
Emojis.
"""
from __future__ import annotations

import abc
import dataclasses
import typing
import unicodedata

from hikari.core.model import base
from hikari.core.model import model_cache


class BaseEmoji(abc.ABC):
    """
    ABC for any emoji that Discord may present to us.
    """
    __slots__ = ()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """The friendly name of the emoji."""

    @property
    @abc.abstractmethod
    def value(self) -> str:
        """The raw value of the emoji. This is the raw string representation."""


class UnicodeEmoji(BaseEmoji, str):
    """
    Represents a standard emoji that is part of unicode.

    Examples include \N{OK HAND SIGN} and \N{AUBERGINE}, both of which are one unicode character.

    Other cases include combined characters such as \N{REGIONAL INDICATOR SYMBOL LETTER G} and
    \N{REGIONAL INDICATOR SYMBOL LETTER B} which combine to make a UK flag emoji on Discord:
    \N{REGIONAL INDICATOR SYMBOL LETTER G}\N{REGIONAL INDICATOR SYMBOL LETTER B}.
    """
    __slots__ = ()

    @property
    def name(self) -> str:
        """The official name of the unicode character sequence."""
        return unicodedata.name(self).lower()

    @property
    def value(self) -> str:
        """The actual character string representation of the emoji."""
        return self

    @property
    def code_points(self) -> typing.List[int]:
        """
        A list of code points. This will be the same length as the length of the emoji with `len()`,
        and each value will correspond to the ordinal value of the character. This mechanism exists to handle
        composite characters such as flags and keycapped numbers (`flag_gb` and `nine`, as examples)
        """
        return [ord(c) for c in self]

    def __repr__(self):
        return f"{type(self).__qualname__}(name={self.name!r})"

    def __str__(self):
        return self


@dataclasses.dataclass()
class CustomEmoji(BaseEmoji, base.Snowflake):
    """
    A custom emoji which may or may not contain guild-specific additional information, depending on whether the
    authorized user is a member in the guild the emoji belongs to or not.
    """
    __slots__ = ("id", "_name", "animated", "guild_details")

    _name: str
    animated: bool
    #: Details about the emoji from the guild it is defined in, if the authorized user is in that guild.
    #:
    #: :type: :class:`EmojiGuildDetails` if we are in the same guild, or `None` otherwise.
    guild_details: typing.Optional[EmojiGuildDetails]

    @property
    def name(self) -> str:
        """The name of the emoji only."""
        return self._name

    @property
    def value(self) -> str:
        """The raw emoji mention."""
        return "<{0}:{1}:{2}>".format("a" if self.animated else "", self._name, self.id)

    @property
    def require_colons(self) -> bool:
        # All custom emojis need colons as far as we know.
        return True

    def __str__(self):
        return self.value

    def __repr__(self):
        return (
            f"{type(self).__qualname__}" 
            f"(name={self.name!r}, animated={self.animated}, guild_details={self.guild_details})"
        )


@dataclasses.dataclass()
class EmojiGuildDetails:
    __slots__ = ("_state", "_guild_id", "_creator_id", "managed")
    _state: model_cache.AbstractModelCache
    _guild_id: int
    _creator_id: int
    managed: bool


__all__ = [
    "BaseEmoji", "UnicodeEmoji", "CustomEmoji", "EmojiGuildDetails"
]
