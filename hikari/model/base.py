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
__all__ = ("SnowflakeMixin", "PartialObject", "NamedEnum")

import copy
import dataclasses
import datetime
import enum
import typing

from hikari.utils import assertions, dateutils


@assertions.assert_is_mixin
@assertions.assert_is_slotted
class SnowflakeMixin:
    """
    Base for any type that specifies an ID. The implementation is expected to implement that field.

    Warning:
        Due to constraints by the dataclasses library, one must ensure to define
        `__hash__` on any object expected to be hashable explicitly. It will not
        be inherited correctly.
    """

    __slots__ = ()

    #: The ID of this object.
    id: int

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        epoch = self.id >> 22
        return dateutils.discord_epoch_to_datetime(epoch)

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
        if not isinstance(other, SnowflakeMixin):
            raise TypeError(
                f"Cannot compare a Snowflake type {type(self).__name__} to a non-snowflake type {type(other).__name__}"
            )
        return self.id < other.id

    def __le__(self, other) -> bool:
        return self < other or self == other

    def __gt__(self, other) -> bool:
        if not isinstance(other, SnowflakeMixin):
            raise TypeError(
                f"Cannot compare a Snowflake type {type(self).__name__} to a non-snowflake type {type(other).__name__}"
            )
        return self.id > other.id

    def __ge__(self, other) -> bool:
        return self > other or self == other


@dataclasses.dataclass()
class PartialObject(SnowflakeMixin):
    """
    Representation of a partially constructed object. This may be returned by some components instead of a correctly
    initialized object if information is not available.

    Any other attributes that were provided with this object are accessible by using dot-notation as normal, but will
    not be documented here and should not be relied on. Your mileage may vary.
    """

    __slots__ = ("id", "_other_attrs")

    #: The ID of this object.
    id: int
    _other_attrs: typing.Dict[str, typing.Any]

    @staticmethod
    def from_dict(payload):
        payload = copy.copy(payload)
        return PartialObject(id=int(payload.pop("id")), _other_attrs=payload)

    def __getattr__(self, item):
        return self._other_attrs[item]


class NamedEnum(enum.Enum):
    """
    An enum that is produced from a string by Discord. This ensures that the key can be looked up from a lowercase
    value that discord provides and use a Pythonic key name that is in upper case.
    """

    @classmethod
    def from_discord_name(cls, name: str):
        """
        Consume a string as described on the Discord API documentation and return a member of this enum, or
        raise a :class:`KeyError` if the name is invalid.
        """
        return cls[name.upper()]
