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
import datetime
import functools
import typing

import attr

from hikari.internal_utilities import dates

RawEntityT = typing.Union[
    None, bool, int, float, str, bytes, typing.Sequence[typing.Any], typing.Mapping[str, typing.Any]
]

T_conta = typing.TypeVar("T_contra", contravariant=True)


# DO NOT ADD ATTRIBUTES TO THIS CLASS.
@attr.s(slots=True)
class HikariEntity:
    __slots__ = ()


# DO NOT ADD ATTRIBUTES TO THIS CLASS.
@attr.s(slots=True)
class Deserializable:
    @classmethod
    def deserialize(cls: typing.Type[T_conta], payload: RawEntityT) -> T_conta:
        raise NotImplementedError()


@functools.total_ordering
class Snowflake(HikariEntity, typing.SupportsInt):
    """A concrete representation of a unique identifier for an object on
    Discord.
    """

    __slots__ = ("value",)

    def __init__(self, value: typing.Union[int, str]) -> None:
        self.value = int(value)

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        epoch = self.value >> 22
        return dates.discord_epoch_to_datetime(epoch)

    @property
    def internal_worker_id(self) -> int:
        """The internal worker ID that created this object on Discord."""
        return (self.value & 0x3E0_000) >> 17

    @property
    def internal_process_id(self) -> int:
        """The internal process ID that created this object on Discord."""
        return (self.value & 0x1F_000) >> 12

    @property
    def increment(self) -> int:
        """The increment of Discord's system when this object was made."""
        return self.value & 0xFFF

    def __int__(self):
        return self.value

    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return isinstance(other, (int, typing.SupportsInt)) and int(other) == self.value

    def __lt__(self, other):
        return self.value < int(other)

    def serialize(self) -> str:
        return str(self.value)


@attr.s(slots=True)
class UniqueEntity(HikariEntity):
    """An entity that has an integer ID of some sort."""

    id: Snowflake = attr.ib(hash=True, eq=True, repr=True)
