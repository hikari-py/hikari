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
Custom data structures and constant values.
"""
import types
import typing

from hikari.core.utils import assertions

# If more than one empty-definition is used in the same context, the type checker will probably whinge, so we have
# to keep separate types...
_A = typing.TypeVar("_A")
_B = typing.TypeVar("_B", bound=typing.Hashable)
_C = typing.TypeVar("_C")
_D = typing.TypeVar("_D", bound=typing.Hashable)
_E = typing.TypeVar("_E")

_K = typing.TypeVar("_K", bound=typing.Hashable)
_V = typing.TypeVar("_V")

_DiscordType = typing.Union[bool, float, int, None, str, typing.List["_DiscordType"], "_DiscordObject"]
_DiscordObject = typing.Dict[str, "_DiscordType"]

#: Any type that Discord may return from the API.
DiscordType = typing.NewType("DiscordType", _DiscordType)

#: Type hint for a Discord-compatible object.
#:
#: This is a :class:`builtins.dict` of :class:`builtins.str` keys that map to any value. Since the :mod:`hikari.net`
#: module does not enforce concrete models for values sent and received, mappings are passed around to represent request
#: and response data. This allows an implementation to use this layer as desired.
DiscordObject = typing.NewType("DiscordObject", _DiscordObject)


class ObjectProxy(typing.Dict[str, typing.Any]):
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

    def __getattr__(self, key: str) -> typing.Any:
        return self[key]

    def __setattr__(self, key: str, value: typing.Any) -> None:
        self[key] = value

    def __delattr__(self, key: str) -> None:
        del self[key]


class LRUDict(typing.MutableMapping[_K, _V]):
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

    def __getitem__(self, key: _K) -> _V:
        return self._data[key]

    def __setitem__(self, key: _K, value: _V) -> None:
        while len(self._data) >= self._lru_size:
            self._data.popitem()
        self._data[key] = value

    def __delitem__(self, key: _K) -> None:
        del self._data[key]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> typing.Iterator[_K]:
        yield from self._data


#: An immutable indexable container of elements with zero size.
EMPTY_SEQUENCE: typing.Sequence[_A] = tuple()
#: An immutable unordered container of elements with zero size.
EMPTY_SET: typing.AbstractSet[_B] = frozenset()
#: An immutable container of elements with zero size.
EMPTY_COLLECTION: typing.Collection[_C] = EMPTY_SEQUENCE
#: An immutable ordered mapping of key elements to value elements with zero size.
EMPTY_DICT: typing.Mapping[_D, _E] = types.MappingProxyType({})

__all__ = ("DiscordObject", "ObjectProxy", "LRUDict", "EMPTY_SEQUENCE", "EMPTY_SET", "EMPTY_COLLECTION", "EMPTY_DICT")
