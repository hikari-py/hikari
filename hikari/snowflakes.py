#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
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
"""A representation of the Discord Snowflake datatype.

Each Snowflake integer used to uniquely identify entities
on the server.
"""

__all__ = ["Snowflake", "UniqueEntity", "HashableT"]

import datetime
import functools
import typing

import attr

from hikari.internal import conversions
from hikari.internal import marshaller
from hikari import entities


@functools.total_ordering
class Snowflake(entities.HikariEntity, typing.SupportsInt):
    """A concrete representation of a unique identifier for an object on Discord.

    This object can be treated as a regular :obj:`~int` for most purposes.
    """

    __slots__ = ("_value",)

    #: The integer value of this ID.
    #:
    #: :type: :obj:`~int`
    _value: int

    # noinspection PyMissingConstructor
    def __init__(self, value: typing.Union[int, str]) -> None:  # pylint:disable=super-init-not-called
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

    def __hash__(self):
        return hash(self._value)

    def __int__(self):
        return self._value

    def __repr__(self):
        return repr(self._value)

    def __str__(self):
        return str(self._value)

    def __eq__(self, other):
        return isinstance(other, typing.SupportsInt) and int(other) == self._value

    def __lt__(self, other):
        return self._value < int(other)

    def serialize(self) -> str:
        """Generate a JSON-friendly representation of this object."""
        return str(self._value)

    @classmethod
    def deserialize(cls, value: str) -> "Snowflake":
        """Take a :obj:`~str` ID and convert it into a Snowflake object."""
        return cls(value)

    @classmethod
    def from_datetime(cls, date: datetime.datetime) -> "Snowflake":
        """Get a snowflake object from a datetime object."""
        return cls.from_timestamp(date.timestamp())

    @classmethod
    def from_timestamp(cls, timestamp: float) -> "Snowflake":
        """Get a snowflake object from a seconds timestamp."""
        return cls(int(timestamp - conversions.DISCORD_EPOCH) * 1000 << 22)


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class UniqueEntity(entities.HikariEntity, typing.SupportsInt):
    """An entity that has an integer ID of some sort."""

    #: The ID of this entity.
    #:
    #: :type: :obj:`~Snowflake`
    id: Snowflake = marshaller.attrib(hash=True, eq=True, repr=True, deserializer=Snowflake, serializer=str)

    def __int__(self):
        return int(self.id)


T = typing.TypeVar("T", bound=UniqueEntity)
HashableT = typing.Union[Snowflake, int, T]
