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
"""
Custom data structures and constant values.
"""
import types
import typing

from hikari.internal_utilities import assertions
from hikari.internal_utilities import compat

# If more than one empty-definition is used in the same context, the type checker will probably whinge, so we have
# to keep separate types...
HashableT = typing.TypeVar("HashableT", bound=typing.Hashable)
ValueT = typing.TypeVar("ValueT")

#: General scalar JSON-compatible type.
ScalarT = typing.Union[dict, list, int, float, str, bool, None]

#: Type hint for a Discord-compatible object.
#:
#: This is a :class:`builtins.dict` of :class:`builtins.str` keys that map to any value. Since the
#: :mod:`hikari.net` module does not enforce concrete models for values sent and received, mappings are passed
#: around to represent request and response data. This allows an implementation to use this layer as desired.
DiscordObjectT = typing.Dict[str, ScalarT]


class ObjectProxy(typing.Generic[ValueT], typing.Dict[str, ValueT]):
    """
    A wrapper for a dict that enables accession, mutation, and deletion of valid key names as if they were attributes.

    Example:
        >>> o = ObjectProxy({"foo": 10, "bar": 20})
        >>> print(o["foo"], o.bar)  # 10 20
        >>> del o["foo"]
        >>> o["bar"] = 69
        >>> print(o)  # {"bar": 69}
    """

    __slots__ = ()

    def __getattr__(self, key: str) -> ValueT:
        return self[key]

    def __setattr__(self, key: str, value: ValueT) -> None:
        self[key] = value

    def __delattr__(self, key: str) -> None:
        del self[key]


class LRUDict(typing.MutableMapping[HashableT, ValueT]):
    """
    A dict that stores a maximum number of items before the oldest is purged.
    """

    # This will not function correctly on non-CPython implementations of Python3.6, and any implementation of
    # Python3.5 or older, as it makes the assumption that all dictionaries are ordered by default.

    __slots__ = ("_lru_size", "_data")

    def __init__(self, lru_size: int, dict_factory=dict) -> None:
        assertions.assert_is_natural(lru_size)
        self._data = dict_factory()
        self._lru_size = lru_size

    def __getitem__(self, key: HashableT) -> ValueT:
        return self._data[key]

    def __setitem__(self, key: HashableT, value: ValueT) -> None:
        while len(self._data) >= self._lru_size:
            self._data.popitem()
        self._data[key] = value

    def __delitem__(self, key: HashableT) -> None:
        del self._data[key]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> typing.Iterator[ValueT]:
        yield from self._data


class DefaultImmutableMapping(typing.Mapping[HashableT, ValueT]):
    """
    A special type of immutable mapping that wraps a mapping of some sort and provides
    an interface allowing either a stored or default value to be returned depending on
    whether the query exists as a key or not.
    """

    __slots__ = ("_data", "_default")

    def __init__(self, data: typing.Mapping[HashableT, ValueT], default: typing.Any):
        self._data = types.MappingProxyType(data)
        self._default = default

    def __getitem__(self, item):
        try:
            return self._data[item]
        except KeyError:
            return self._default

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> typing.Iterator[HashableT]:
        return iter(self._data)



#: An immutable indexable container of elements with zero size.
EMPTY_SEQUENCE: typing.Sequence = tuple()
#: An immutable unordered container of elements with zero size.
EMPTY_SET: typing.AbstractSet = frozenset()
#: An immutable container of elements with zero size.
EMPTY_COLLECTION: typing.Collection = tuple()
#: An immutable ordered mapping of key elements to value elements with zero size.
EMPTY_DICT: typing.Mapping = types.MappingProxyType({})

DictImplT = typing.TypeVar("DictImplT", typing.Dict, dict)
DictFactoryT = typing.Union[typing.Type[DictImplT], typing.Callable[[], DictImplT]]

__all__ = (
    "ScalarT",
    "DiscordObjectT",
    "ObjectProxy",
    "LRUDict",
    "EMPTY_SEQUENCE",
    "EMPTY_SET",
    "EMPTY_COLLECTION",
    "EMPTY_DICT",
    "DictImplT",
    "DictFactoryT",
)
