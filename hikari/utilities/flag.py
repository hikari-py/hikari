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
"""Stuff to make working with enum flags a bit easier."""
from __future__ import annotations

__all__: typing.List[str] = ["Flag"]

import enum
import math
import typing


FlagT = typing.TypeVar("FlagT", bound="Flag")


class Flag(enum.IntFlag):
    """Base type for an enum integer flag in Hikari.

    Provides a consistent way of producing human-readable strings, and
    utilities for exploding bitfields into individual member values.

    Example
    -------

    ```py
    >>> class Permission(Flag):
    ...     CREATE = enum.auto()
    ...     READ = enum.auto()
    ...     UPDATE = enum.auto()
    ...     DELETE = enum.auto()

    >>> perms = Permission.CREATE | Permission.READ
    >>> print(perms.split())
    [Permission.CREATE, Permission.READ]
    """

    def split(self: FlagT) -> typing.Sequence[FlagT]:
        """Return a list of all atomic values for this flag."""
        members: typing.List[FlagT] = []

        for member in type(self).__members__.values():
            # Don't show `NONE` values, it breaks stuff and makes no sense here.
            if not member.value:
                continue

            # If it isn't a combined value, and it is contained in the bitfield:
            if math.log2(member.value).is_integer() and member & self:
                members.append(member)

        return sorted(members, key=lambda m: m.name)

    def __str__(self) -> str:
        if hasattr(self, "name") and self.name is not None:
            return self.name
        return " | ".join(m.name for m in self.split())
