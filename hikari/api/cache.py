# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Core interface for a cache implementation."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["ICacheView", "ICacheComponent"]

import abc
import typing

from hikari.api import component
from hikari.utilities import iterators

if typing.TYPE_CHECKING:
    from hikari.utilities import snowflake


_T = typing.TypeVar("_T", bound="snowflake.Unique")
_T_co = typing.TypeVar("_T_co", bound="snowflake.Unique")
_U = typing.TypeVar("_U")


class ICacheView(typing.Mapping["snowflake.Snowflake", _T], abc.ABC):
    """Interface describing an immutable snapshot view of part of a cache."""

    @abc.abstractmethod
    def get_item_at(self, index: int) -> _T:
        ...

    @abc.abstractmethod
    def iterator(self) -> iterators.LazyIterator[_T_co]:
        ...


class ICacheComponent(component.IComponent, abc.ABC):
    """Interface describing the operations a cache component should provide.

    This will be used by the gateway and HTTP API to cache specific types of
    objects that the application should attempt to remember for later, depending
    on how this is implemented. The requirement for this stems from the
    assumption by Discord that bot applications will maintain some form of
    "memory" of the events that occur.

    The implementation may choose to use a simple in-memory collection of
    objects, or may decide to use a distributed system such as a Redis cache
    for cross-process bots.
    """

    __slots__: typing.Sequence[str] = ()

    # TODO: interface :)
