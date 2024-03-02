# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Implementation of a Snowflake type."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "Snowflake",
    "Unique",
    "calculate_shard_id",
    "Snowflakeish",
    "SearchableSnowflakeish",
    "SnowflakeishOr",
    "SearchableSnowflakeishOr",
    "SnowflakeishIterable",
    "SnowflakeishSequence",
)

import abc
import typing

from hikari.internal import time

if typing.TYPE_CHECKING:
    import datetime

    from hikari import guilds
    from hikari import traits


@typing.final
class Snowflake(int):
    """A concrete representation of a unique ID for an entity on Discord.

    This object can be treated as a regular [int][] for most purposes.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        epoch = self >> 22
        return time.discord_epoch_to_datetime(epoch)

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
        """Minimum value for a snowflakes."""
        return cls(0)

    @classmethod
    def max(cls) -> Snowflake:
        """Maximum value for a snowflakes."""
        return cls((1 << 63) - 1)

    @classmethod
    def from_data(cls, timestamp: datetime.datetime, worker_id: int, process_id: int, increment: int) -> Snowflake:
        """Convert the pieces of info that comprise an ID into a Snowflake."""
        return cls(
            (time.datetime_to_discord_epoch(timestamp) << 22) | (worker_id << 17) | (process_id << 12) | increment
        )


class Unique(abc.ABC):
    """Mixin for a class that enforces uniqueness by a snowflake ID."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def id(self) -> Snowflake:
        """ID of this entity."""

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        return self.id.created_at

    @typing.final
    def __index__(self) -> int:
        return int(self.id)

    @typing.final
    def __int__(self) -> int:
        return int(self.id)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: typing.Any) -> bool:
        return type(self) is type(other) and self.id == other.id


def calculate_shard_id(
    app_or_count: typing.Union[traits.ShardAware, int], guild: SnowflakeishOr[guilds.PartialGuild]
) -> int:
    """Calculate the shard ID for a guild based on it's shard aware app or shard count.

    Parameters
    ----------
    app_or_count : typing.Union[hikari.traits.ShardAware, int]
        The shard aware app of the current application or the integer count of
        the current app's shards.
    guild : SnowflakeishOr[hikari.guilds.PartialGuild]
        The object or ID of the guild to get the shard ID of.

    Returns
    -------
    int
        The zero-indexed integer ID of the shard that should cover this guild.
    """
    shard_count = app_or_count if isinstance(app_or_count, int) else app_or_count.shard_count
    return (int(guild) >> 22) % shard_count


Snowflakeish = typing.Union[Snowflake, int]
"""Type hint for a value that resembles a [hikari.snowflakes.Snowflake][] object functionally.

This is a value that is [hikari.snowflakes.Snowflake][]-ish.

A value is [hikari.snowflakes.Snowflake][]-ish if casting it to an [int][] allows it to be cast to
a [hikari.snowflakes.Snowflake][].

The valid types for this type hint are:

- [int][]
- [hikari.snowflakes.Snowflake][]
"""

SearchableSnowflakeish = typing.Union[Snowflakeish, "datetime.datetime"]
"""Type hint for a snowflakeish that can be searched for in history.

This is just a [hikari.snowflakes.Snowflakeish][] that can alternatively be some form of
[datetime.datetime][] instance.

The valid types for this type hint are:

- [str][] containing digits.
- [int][]
- [hikari.snowflakes.Snowflake][]
- [datetime.datetime][]
"""

T = typing.TypeVar("T", covariant=True, bound=Unique)

SnowflakeishOr = typing.Union[T, Snowflakeish]
"""Type hint representing a unique object entity.

This is a value that is [hikari.snowflakes.Snowflake][]-ish or a specific type covariant.

If you see `SnowflakeishOr[Foo]` anywhere as a type hint, it means the value
may be a `Foo` instance, a [hikari.snowflakes.Snowflake][], an [int][] or a [str][]
with numeric digits only.

Essentially this represents any concrete object, or ID of that object. It is
used across Hikari's API to allow use of functions when information is only
partially available (due to Discord inconsistencies, edge case behaviour, or
use of intents).

The valid types for this type hint are:

- [int][]
- [hikari.snowflakes.Snowflake][]
"""

SearchableSnowflakeishOr = typing.Union[T, SearchableSnowflakeish]
"""Type hint for a unique object entity that can be searched for.

This is a variant of [hikari.snowflakes.SnowflakeishOr][] that also allows an alternative value
of a [datetime.datetime][] to be specified.

Essentially this represents any concrete object, or ID of that object. It is
used across Hikari's API to allow use of functions when information is only
partially available (due to Discord inconsistencies, edge case behaviour, or
use of intents).

The valid types for this type hint are:

- [int][]
- [hikari.snowflakes.Snowflake][]
- [datetime.datetime][]
"""

SnowflakeishIterable = typing.Iterable[SnowflakeishOr[T]]
"""Type hint representing an iterable of unique object entities."""


SnowflakeishSequence = typing.Sequence[SnowflakeishOr[T]]
"""Type hint representing a collection of unique object entities."""
