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
__all__ = ["EnumMixin", "FlagMixin"]

import typing


class EnumMixin:
    """Mixin for a non-flag enum type.

    This gives a more meaningful ``__str__`` implementation.

    The class should inherit this mixin before any type defined in :mod:`~enum`.
    """

    __slots__ = ()

    #: The name of the enum member.
    #:
    #: :obj:`~str`
    name: str

    def __str__(self) -> str:
        return self.name


class FlagMixin:
    """Mixin for a flag enum type.

    This gives a more meaningful ``__str__`` implementation.

    The class should inherit this mixin before any type defined in :mod:`~enum`.
    """

    __slots__ = ()

    #: The name of the enum member.
    #:
    #: :obj:`~str`
    name: str

    def __str__(self) -> str:
        return ", ".join(flag.name for flag in typing.cast(typing.Iterable, type(self)) if flag & self)
