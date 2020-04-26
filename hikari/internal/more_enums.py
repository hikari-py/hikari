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
"""Mixin utilities for defining enums."""

from __future__ import annotations

__all__ = ["Enum", "IntFlag", "must_be_unique", "generated_value"]

import enum
import typing


class Enum(enum.Enum):
    """A non-flag enum type.

    This gives a more meaningful `__str__` implementation than what is defined
    in the `enum` module by default.
    """

    __slots__ = ()

    name: str
    """The name of the enum member."""

    def __str__(self) -> str:
        return self.name


class IntFlag(enum.IntFlag):
    """Base for an integer flag enum type.

    This gives a more meaningful `__str__` implementation than what is defined
    in the `enum` module by default.
    """

    __slots__ = ()

    name: str
    """The name of the enum member."""

    def __str__(self) -> str:
        return ", ".join(flag.name for flag in typing.cast(typing.Iterable, type(self)) if flag & self)


must_be_unique = enum.unique
generated_value = enum.auto
