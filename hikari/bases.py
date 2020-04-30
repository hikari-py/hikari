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
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""Datastructure bases."""

from __future__ import annotations

__all__ = ["HikariEntity", "LARGEST_SNOWFLAKE", "Snowflake", "UniqueEntity"]

import abc
import functools
import typing

import attr

from hikari.internal import conversions
from hikari.internal import marshaller

if typing.TYPE_CHECKING:
    import datetime

    from hikari.clients import components


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True, init=False)
class HikariEntity(abc.ABC):
    """The base for any entity used in this API."""

    _components: typing.Optional[components.Components] = attr.attrib(default=None, repr=False, eq=False, hash=False)
    """The client components that models may use for procedures."""


@functools.total_ordering
class Snowflake(HikariEntity, typing.SupportsInt):
    """A concrete representation of a unique identifier for an object on Discord.

    This object can be treated as a regular `int` for most purposes.
    """

    __slots__ = ("_value",)

    _value: int
    """The integer value of this ID."""

    def __init__(self, value: typing.Union[int, str]) -> None:
        super().__init__()
        self._value = int(value)

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        epoch = self._value >> 22
        return conversions.discord_epoch_to_datetime(epoch)

    @property
    def internal_worker_id(self) -> int:
        """ID of the worker that created this snowflake on Discord's systems."""
        return (self._value & 0x3E0_000) >> 17

    @property
    def internal_process_id(self) -> int:
        """ID of the process that created this snowflake on Discord's systems."""
        return (self._value & 0x1F_000) >> 12

    @property
    def increment(self) -> int:
        """Increment of Discord's system when this object was made."""
        return self._value & 0xFFF

    def __hash__(self) -> int:
        return hash(self._value)

    def __int__(self) -> int:
        return self._value

    def __repr__(self) -> str:
        return repr(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __eq__(self, other: typing.Any) -> bool:
        return isinstance(other, typing.SupportsInt) and int(other) == self._value

    def __lt__(self, other: "Snowflake") -> bool:
        return self._value < int(other)

    def serialize(self) -> str:
        """Generate a JSON-friendly representation of this object."""
        return str(self._value)

    @classmethod
    def deserialize(cls, value: str) -> Snowflake:
        """Take a `str` ID and convert it into a Snowflake object."""
        return cls(value)

    @classmethod
    def from_datetime(cls, date: datetime.datetime) -> Snowflake:
        """Get a snowflake object from a datetime object."""
        return cls.from_timestamp(date.timestamp())

    @classmethod
    def from_timestamp(cls, timestamp: float) -> Snowflake:
        """Get a snowflake object from a seconds timestamp."""
        return cls(int(timestamp - conversions.DISCORD_EPOCH) * 1000 << 22)


LARGEST_SNOWFLAKE: typing.Final[Snowflake] = Snowflake((1 << 63) - 1)


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class UniqueEntity(HikariEntity, typing.SupportsInt, abc.ABC):
    """A base for an entity that has an integer ID of some sort.

    Casting an object of this type to an `int` will produce the
    integer ID of the object.
    """

    id: Snowflake = marshaller.attrib(hash=True, eq=True, repr=True, deserializer=Snowflake, serializer=str)
    """The ID of this entity."""

    def __int__(self) -> int:
        return int(self.id)


T = typing.TypeVar("T", bound=UniqueEntity)
Hashable = typing.Union[Snowflake, int, T]
