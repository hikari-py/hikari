# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Implementation of a Snowflake type."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "Snowflake",
    "Unique",
    "Snowflakeish",
    "SearchableSnowflakeish",
    "SnowflakeishOr",
    "SearchableSnowflakeishOr",
]

import abc
import datetime

# noinspection PyUnresolvedReferences
import typing

from hikari.utilities import date


@typing.final
class Snowflake(int):
    """A concrete representation of a unique ID for an entity on Discord.

    This object can be treated as a regular `builtins.int` for most purposes.
    """

    __slots__: typing.Sequence[str] = ()

    ___MIN___: Snowflake
    ___MAX___: Snowflake

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        epoch = self >> 22
        return date.discord_epoch_to_datetime(epoch)

    @property
    def internal_worker_id(self) -> int:
        """ID of the worker that created this snowflake on Discord's systems."""
        return (self & 0x3E0_000) >> 17

    @property
    def internal_process_id(self) -> int:
        """ID of the process that created this snowflake on Discord's systems."""
        return (self & 0x1F_000) >> 12

    @property
    def increment(self) -> int:
        """Increment of Discord's system when this object was made."""
        return self & 0xFFF

    @classmethod
    def from_datetime(cls, timestamp: datetime.datetime) -> Snowflake:
        """Get a snowflake object from a datetime object."""
        return cls.from_data(timestamp, 0, 0, 0)

    @classmethod
    def min(cls) -> Snowflake:
        """Minimum value for a snowflake."""
        if not hasattr(cls, "___MIN___"):
            cls.___MIN___ = Snowflake(0)
        return cls.___MIN___

    @classmethod
    def max(cls) -> Snowflake:
        """Maximum value for a snowflake."""
        if not hasattr(cls, "___MAX___"):
            cls.___MAX___ = Snowflake((1 << 63) - 1)
        return cls.___MAX___

    @classmethod
    def from_data(cls, timestamp: datetime.datetime, worker_id: int, process_id: int, increment: int) -> Snowflake:
        """Convert the pieces of info that comprise an ID into a Snowflake."""
        return cls(
            (date.datetime_to_discord_epoch(timestamp) << 22) | (worker_id << 17) | (process_id << 12) | increment
        )


class Unique(abc.ABC):
    """Mixin for a class that enforces uniqueness by a snowflake ID."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def id(self) -> Snowflake:
        """Return the ID of this entity.

        Returns
        -------
        Snowflake
            The snowflake ID of this object.
        """

    # TODO: make immutable interface, as this is a major risk to consistent hash codes.
    @id.setter
    def id(self, value: Snowflake) -> None:
        """Set the ID on this entity."""

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        return self.id.created_at

    @typing.final
    def __int__(self) -> int:
        return int(self.id)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: typing.Any) -> bool:
        return type(self) is type(other) and self.id == other.id


Snowflakeish = typing.Union[Snowflake, int, str]
"""Type hint for a value that resembles a `Snowflake` object functionally.

This is a value that is `Snowflake`-ish.

A value is `Snowflake`-ish if casting it to an `int` allows it to be cast to
a `Snowflake`.

The valid types for this type hint are:

- `builtins.str` containing digits.
- `builtins.int`
- `Snowflake`
"""

SearchableSnowflakeish = typing.Union[Snowflakeish, datetime.datetime]
"""Type hint for a snowflakeish that can be searched for in history.

This is just a `Snowflakeish` that can alternatively be some form of
`datetime.datetime` instance.

The valid types for this type hint are:

- `builtins.str` containing digits.
- `builtins.int`
- `Snowflake`
- `datetime.datetime`
"""

T = typing.TypeVar("T", covariant=True)

SnowflakeishOr = typing.Union[T, Snowflakeish]
"""Type hint representing a unique object entity.

This is a value that is `Snowflake`-ish or a specific type covariant.

If you see `SnowflakeishOr[Foo]` anywhere as a type hint, it means the value
may be a `Foo` instance, a `Snowflake`, a `builtins.int` or a `builtins.str`
with numeric digits only.

Essentially this represents any concrete object, or ID of that object. It is
used across Hikari's API to allow use of functions when information is only
partially available (due to Discord inconsistencies, edge case behaviour, or
use of intents).

The valid types for this type hint are:

- `T` - the generic type parameter in the expression
    `SearchableSnowflakeishOr[T]`
- `builtins.str` containing digits.
- `buitlins.int`
- `Snowflake`
"""

SearchableSnowflakeishOr = typing.Union[T, SearchableSnowflakeish]
"""Type hint for a unique object entity that can be searched for.

This is a variant of `SnowflakeishOr` that also allows an alternative value
of a `datetime.datetime` to be specified.

Essentially this represents any concrete object, or ID of that object. It is
used across Hikari's API to allow use of functions when information is only
partially available (due to Discord inconsistencies, edge case behaviour, or
use of intents).

The valid types for this type hint are:

- `T` - the generic type parameter in the expression
    `SearchableSnowflakeishOr[T]`
- `builtins.str` containing digits.
- `buitlins.int`
- `Snowflake`
- `datetime.datetime`
"""
