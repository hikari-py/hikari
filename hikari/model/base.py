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
Model ABCs.
"""
from __future__ import annotations

import copy

__all__ = ("StatefulModel", "Snowflake", "PartialObject", "NamedEnum")

import abc
import dataclasses
import datetime
import enum
import typing

from hikari import utils

T = typing.TypeVar("T")


class Model(abc.ABC):
    """
    Core base model for any Hikari model.
    """

    __slots__ = ()

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, payload: utils.DiscordObject, state=NotImplemented):
        """
        Consume a Discord payload and produce an instance of this class.

        The state may not be required by the model. If it is not required, then it is not necessary to specify it.
        Unless the object implements StatefulModel, then it is not to store the state explicitly.
        """
        return NotImplemented


@dataclasses.dataclass(repr=False)
class StatefulModel(Model):
    """
    Base for every model we can use in this API which needs access to the global state.
    """

    __slots__ = ("_state",)

    #: Internal API state.
    _state: typing.Any


# noinspection PyUnresolvedReferences,PyAbstractClass
@dataclasses.dataclass()
class Snowflake(StatefulModel):
    """
    Abstract base for every model in this API that provides an ID attribute. This should also store the state internally
    by default.

    Warning:
        Due to constraints by the dataclasses library, one must ensure to define
        `__hash__` on any object expected to be hashable explicitly. It will not
        be inherited correctly.
    """

    __slots__ = ("id",)

    #: ID of the object.
    id: int

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        stamp = ((self.id >> 22) / 1_000) + utils.DISCORD_EPOCH
        return datetime.datetime.utcfromtimestamp(stamp)

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


@dataclasses.dataclass()
class PartialObject(Snowflake):
    """
    Representation of a partially constructed object. This may be returned by some components instead of a correctly
    initialized object if information is not available.
    """

    __slots__ = ("_other_attrs",)

    _other_attrs: typing.Dict[str, typing.Any]

    @classmethod
    def from_dict(cls: PartialObject, payload: utils.DiscordObject, state=NotImplemented) -> PartialObject:
        payload = copy.copy(payload)
        return cls(_state=state, id=int(payload.pop("id")), _other_attrs=payload)

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
