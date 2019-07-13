#!/usr/bin/env python
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
Model ABCs.
"""
__all__ = ("Model", "Snowflake", "NamedEnum")

import abc
import dataclasses
import datetime
import enum
import typing

from hikari import utils


T = typing.TypeVar("T")


# noinspection PyMethodMayBeStatic,PyUnusedLocal
@dataclasses.dataclass(eq=False, order=False, unsafe_hash=False, repr=False)
class Model(abc.ABC):
    """
    Base for every model we can use in this API.
    """

    __slots__ = ("_state",)

    #: Internal API state.
    _state: typing.Any

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, payload: utils.DiscordObject, state):
        """Consume a Discord payload and produce an instance of this class."""
        return NotImplemented

    def to_dict(self) -> utils.DiscordObject:
        """
        Consume this class instance and produce a Discord payload.

        Classes are not required to implement this method unless it is required internally.
        """
        return NotImplemented


# noinspection PyUnresolvedReferences
@dataclasses.dataclass()
class Snowflake(Model, abc.ABC):
    """
    Base for every model in this API that provides an ID attribute.
    """

    __slots__ = ("id",)

    #: ID of the object.
    id: int

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        stamp = ((self.id >> 22) / 1_000) + utils.DISCORD_EPOCH
        return datetime.datetime.fromtimestamp(stamp)

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

    def __eq__(self, other):
        return isinstance(other, Snowflake) and self.id == other.id

    def __lt__(self, other):
        if not isinstance(other, Snowflake):
            raise TypeError(
                f"Cannot compare a Snowflake type {type(self).__name__} to a non-snowflake type {type(other).__name__}"
            )
        return self.id < other.id


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
