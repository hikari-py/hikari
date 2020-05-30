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

__all__ = ["Entity", "Snowflake", "Unique"]

import abc
import typing

import attr

from hikari.utilities import date as date_

if typing.TYPE_CHECKING:
    import datetime

    from hikari import app as app_


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=False)
class Entity(abc.ABC):
    """The base for any entity used in this API."""

    _app: typing.Optional[app_.IApp] = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    def set_app(self, app: app_.IApp) -> None:
        if hasattr(self, "_app"):
            raise AttributeError("Protected attribute '_app' cannot be overwritten.")
        self._app = app


class Snowflake(int):
    """A concrete representation of a unique identifier for an object on Discord.

    This object can be treated as a regular `int` for most purposes.
    """

    __slots__ = ()

    ___MIN___: Snowflake
    ___MAX___: Snowflake

    @staticmethod
    def __new__(cls, value: typing.Union[int, str]) -> Snowflake:
        return super(Snowflake, cls).__new__(cls, value)

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        epoch = self >> 22
        return date_.discord_epoch_to_datetime(epoch)

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
    def from_datetime(cls, date: datetime.datetime) -> Snowflake:
        """Get a snowflake object from a datetime object."""
        return cls.from_data(date, 0, 0, 0)

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
            (date_.datetime_to_discord_epoch(timestamp) << 22) | (worker_id << 17) | (process_id << 12) | increment
        )


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=False)
class Unique(typing.SupportsInt):
    """A base for an entity that has an integer ID of some sort.

    Casting an object of this type to an `int` will produce the
    integer ID of the object.
    """

    id: Snowflake = attr.ib(converter=Snowflake, hash=True, eq=True, repr=True)
    """The ID of this entity."""

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        return self.id.created_at

    def __int__(self) -> int:
        return int(self.id)


UniqueObject = typing.Union[Unique, Snowflake, int, str]
"""A unique object."""
