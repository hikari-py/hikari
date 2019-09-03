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

import abc
import dataclasses
import datetime
import inspect

from hikari.core.utils import assertions
from hikari.core.utils import dateutils


def dataclass(**kwargs):
    """
    Wraps the dataclasses' dataclass decorator and injects some default behaviour, such as injecting `__hash__` into
    any member that supplies the `id` member.

    Args:
        **kwargs:
            Any arguments to pass to dataclasses' dataclass decorator.

    Returns:
        A decorator for a new data class.
    """

    def decorator(cls):
        kwargs.pop("init", "__init__" not in cls.__dict__)

        # noinspection PyArgumentList
        dataclass_cls = dataclasses.dataclass(**kwargs)(cls)

        # Dataclasses usually don't allow inheritance of hash codes properly due to internal constraints but
        # we force the hash of our types to be inheritable by extra implementation.
        # Hashcode gets derived from object normally, but we can usually see this by seeing if the reference
        # is a slot or an actual function. If it is a slot, we should assume it is not redefined elsewhere, I guess.
        if not inspect.isfunction(cls.__hash__):
            # mro [0] is always the implementation class, mro[-1] is always object() which has a __hash__ that is
            # useless to us.
            for base in cls.mro()[1:-1]:
                if "__hash__" in base.__dict__:
                    dataclass_cls.__hash__ = lambda self: base.__hash__(self)
                    break

        return dataclass_cls

    return decorator


@assertions.assert_is_mixin
@assertions.assert_is_slotted
class Snowflake(abc.ABC):
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

    def __hash__(self):
        return hash(self.id)

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
class Messageable(abc.ABC):
    async def send(self, *args, **kwargs):
        raise NotImplementedError("Not yet implemented.")


__all__ = ("Snowflake", "NamedEnum", "Messageable")
