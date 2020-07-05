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
"""Various custom data structures."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["IDMap", "IDTable"]

import array
import bisect
import reprlib
import typing

import immutables

from hikari.utilities import snowflake

_VT = typing.TypeVar("_VT")


class IDMap(typing.MutableMapping[snowflake.Snowflake, _VT], typing.Generic[_VT]):
    """A hash array mapped trie of snowflakes mapping to a value type."""

    __slots__ = ("_data",)

    def __init__(self) -> None:
        self._data = immutables.Map()

    def __getitem__(self, key: snowflake.Snowflake) -> _VT:
        return self._data[key]

    def __setitem__(self, key: snowflake.Snowflake, value: _VT) -> None:
        self._data = self._data.set(key, value)

    def __delitem__(self, key: snowflake.Snowflake) -> None:
        self._data = self._data.delete(key)

    set = __setitem__
    delete = __delitem__

    def set_many(self, pairs: typing.Iterable[typing.Tuple[snowflake.Snowflake, _VT]]) -> None:
        mutation = self._data.mutate()
        for key, value in pairs:
            mutation[key] = value

        self._data = mutation.finish()

    def delete_many(self, keys: typing.Iterable[int]) -> None:
        mutation = self._data.mutate()

        for key in keys:
            del mutation[key]

        self._data = mutation.finish()

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> typing.Iterator[snowflake.Snowflake]:
        return iter((snowflake.Snowflake(i) for i in self._data))

    def __repr__(self) -> str:
        return "SnowflakeMapping(" + reprlib.repr(dict(self._data)) + ")"


class IDTable(typing.MutableSet[snowflake.Snowflake]):
    """Compact 64-bit integer bisected-array-set of snowflakes."""

    __slots__ = ("_ids",)

    def __init__(self) -> None:
        self._ids = array.array("Q")

    def add(self, sf: snowflake.Snowflake) -> None:
        index = bisect.bisect_right(self._ids, sf)
        if self._ids[index] != sf:
            self._ids.insert(index, sf)

    def discard(self, sf: snowflake.Snowflake) -> None:
        index = self._index_of(sf)
        if index != -1:
            del self._ids[index]

    def _index_of(self, sf: int) -> int:
        bottom, top = 0, len(self._ids) - 1

        while top - bottom:
            pos = (bottom + top) // 2
            item = self._ids[pos]
            if item == sf:
                return pos

            if item < sf:
                bottom = pos
            else:
                top = pos

        return -1

    def __contains__(self, value: typing.Any) -> bool:
        if not isinstance(value, int):
            return False
        return self._index_of(value) != -1

    def __len__(self) -> int:
        return len(self._ids)

    def __iter__(self) -> typing.Iterator[snowflake.Snowflake]:
        return iter((snowflake.Snowflake(i) for i in self._ids))

    def __repr__(self) -> str:
        return "SnowflakeTable" + reprlib.repr(self._ids)[5:]
