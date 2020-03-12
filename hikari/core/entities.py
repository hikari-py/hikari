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

import cattr

import attr
import typing

from hikari.internal_utilities import dates


class HikariConverter(cattr.Converter):
    pass


class Entity:
    """A model entity."""

    __slots__ = ()
    _converter = HikariConverter()

    @classmethod
    def __init_class__(cls, converter: cattr.Converter):
        ...

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        cls.__init_class__(cls._converter)

    def serialize(self):
        """
        Returns
        -------

        A JSON-compatible representation of this object.
        """
        return self._converter.unstructure(self)

    @classmethod
    def deserialize(cls, payload):
        """
        Parameters
        ----------
        payload:
            The payload to deserialize.

        Returns
        -------
        The structured object.
        """
        return cls._converter.structure(payload, cls)


@functools.total_ordering
class Snowflake(Entity, typing.SupportsInt):
    """A concrete representation of a unique identifier for an object on
    Discord.
    """

    __slots__ = ("value",)

    def __init__(self, value: typing.Union[int, str]) -> None:
        self.value = int(value)

    @classmethod
    def __init_class__(cls, converter):
        converter.register_structure_hook(cls, lambda data, t: t(data))
        converter.register_unstructure_hook(cls, str)
        ...

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


@attr.s(slots=True)
class Hashable(Entity):
    """An entity that has an integer ID of some sort."""

    id: Snowflake = attr.ib(hash=True, eq=True, repr=True)
