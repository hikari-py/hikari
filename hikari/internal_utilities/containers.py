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
"""Custom data structures and constant values."""
__all__ = [
    "EMPTY_SEQUENCE",
    "EMPTY_SET",
    "EMPTY_COLLECTION",
    "EMPTY_DICT",
]

import types
import typing

# If more than one empty-definition is used in the same context, the type checker will probably whinge, so we have
# to keep separate types...
HashableT = typing.TypeVar("HashableT", bound=typing.Hashable)
ValueT = typing.TypeVar("ValueT")

#: An immutable indexable container of elements with zero size.
EMPTY_SEQUENCE: typing.Sequence = tuple()
#: An immutable unordered container of elements with zero size.
EMPTY_SET: typing.AbstractSet = frozenset()
#: An immutable container of elements with zero size.
EMPTY_COLLECTION: typing.Collection = tuple()
#: An immutable ordered mapping of key elements to value elements with zero size.
EMPTY_DICT: typing.Mapping = types.MappingProxyType({})
