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
Model ABCs and mixins.
"""
from __future__ import annotations

import copy
import datetime
import typing

from hikari.core.utils import assertions
from hikari.core.utils import custom_types
from hikari.core.utils import date_utils


@assertions.assert_is_mixin
@assertions.assert_is_slotted
class NamedEnum:
    """
    A mixin for an enum that is produced from a string by Discord. This ensures that the key can be looked up from a
    lowercase value that discord provides and use a Pythonic key name that is in upper case.
    """

    __slots__ = ()

    @classmethod
    def from_discord_name(cls, name: str):
        """
        Consume a string as described on the Discord API documentation and return a member of this enum, or
        raise a :class:`KeyError` if the name is invalid.
        """
        return cls[name.upper()]

    def __str__(self):
        return self.name

    __repr__ = __str__


@assertions.assert_is_mixin
@assertions.assert_is_slotted
class Snowflake:
    """
    Base for any type that specifies an ID. The implementation is expected to implement that field.

    Warning:
        Due to constraints by the dataclasses library, one must ensure to define
        `__hash__` on any object expected to be hashable explicitly. It will not
        be inherited correctly.
    """

    __slots__ = ()

    #: The ID of this object.
    #:
    #: :type: :class:`int`
    id: int

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        epoch = self.id >> 22
        return date_utils.discord_epoch_to_datetime(epoch)

    @property
    def internal_worker_id(self) -> int:
        """The internal worker ID that created this object on Discord."""
        return (self.id & 0x3E0_000) >> 17

    @property
    def internal_process_id(self) -> int:
        """The internal process ID that created this object on Discord."""
        return (self.id & 0x1F_000) >> 12

    @property
    def increment(self) -> int:
        """The increment of Discord's system when this object was made."""
        return self.id & 0xFFF

    def __lt__(self, other) -> bool:
        if not isinstance(other, Snowflake):
            raise TypeError(
                f"Cannot compare a Snowflake type {type(self).__name__} to a non-snowflake type {type(other).__name__}"
            )
        return self.id < other.id

    def __le__(self, other) -> bool:
        return self < other or self == other

    def __gt__(self, other) -> bool:
        if not isinstance(other, Snowflake):
            raise TypeError(
                f"Cannot compare a Snowflake type {type(self).__name__} to a non-snowflake type {type(other).__name__}"
            )
        return self.id > other.id

    def __ge__(self, other) -> bool:
        return self > other or self == other


_T = typing.TypeVar("_T", bound="HikariModel")


@assertions.assert_is_mixin
@assertions.assert_is_slotted
class HikariModel:
    """
    Marks a class that is allowed to have its state periodically updated, rather than being recreated.

    Any classes with this as a subclass should not be assumed to have consistent state between awaiting other elements.

    If you need some fields to be copied across by reference regardless of being requested to produce a new copy, you
    should specify their names in the `__copy_byref__` class var. This will prevent :func:`copy.copy` being
    invoked on them when duplicating the object to produce a before and after view when a change is made.
    """

    __slots__ = ()
    __copy_by_ref__: typing.ClassVar[typing.Tuple] = ()

    def update_state(self, payload: custom_types.DiscordObject) -> None:
        """
        Updates the internal state of an existing instance of this object from a raw Discord payload.
        """
        raise NotImplementedError

    def copy(self: _T) -> _T:
        """
        Create a copy of this object.

        Return:
            the copy of this object.
        """
        # Make a new instance without the internal attributes.
        # noinspection PyArgumentList
        reconstructor, (cls, base, state), data = self.__reduce__()
        new_instance = reconstructor(cls, base, state)

        for k, v in data.items():
            if k in self.__copy_by_ref__:
                setattr(new_instance, k, v)
            else:
                setattr(new_instance, k, copy.copy(v))

        return new_instance

    def __copy__(self):
        return self.copy()


__all__ = ("Snowflake", "NamedEnum", "HikariModel")
