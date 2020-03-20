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
"""Assertions of things. 
These are functions that validate a value, expected to return the value on success but error
on any failure.
"""
__all__ = [
    "assert_that",
    "assert_not_none",
    "assert_in_range",
]

import typing

ValueT = typing.TypeVar("ValueT")
BaseTypeInstanceT = typing.TypeVar("BaseTypeInstanceT")


def assert_that(condition: bool, message: str = None, error_type: type = ValueError) -> None:
    """Raises a :obj:`ValueError` with the optional description if the given condition is falsified."""
    if not condition:
        raise error_type(message or "condition must not be False")


def assert_not_none(value: ValueT, message: typing.Optional[str] = None) -> ValueT:
    """Raises a :obj:`ValueError` with the optional description if the given value is ``None``."""
    if value is None:
        raise ValueError(message or "value must not be None")
    return value


def assert_in_range(value, min_inclusive, max_inclusive, name: str = None):
    """Raise a value error if a value is not in the range [min, max]"""
    if not (min_inclusive <= value <= max_inclusive):
        name = name or "The value"
        raise ValueError(f"{name} must be in the inclusive range of {min_inclusive} and {max_inclusive}")
