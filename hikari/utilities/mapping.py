# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Limited mapping implementations used by hikari."""
from __future__ import annotations

__all__: typing.Sequence[str] = [
    "KeyT",
    "ValueT",
    "MRUMutableMapping",
    "get_index_or_slice",
]

import datetime
import itertools
import time
import typing

KeyT = typing.TypeVar("KeyT", bound=typing.Hashable)
"""Type-hint A type hint used for the type of a mapping's key."""
ValueT = typing.TypeVar("ValueT")
"""Type-hint A type hint used for the type of a mapping's value."""


class MRUMutableMapping(typing.MutableMapping[KeyT, ValueT]):
    """A most recently used mutable mapping implementation.

    This will remove entries

    Parameters
    ----------
    expiry : datetime.timedelta
        The timedelta of how long entries should be stored for before removal.
    """

    __slots__ = ("_data", "_expiry")

    def __init__(self, expiry: datetime.timedelta) -> None:
        if expiry <= datetime.timedelta():
            raise ValueError("expiry time must be greater than 0 microseconds.")

        self._expiry: float = expiry.total_seconds()
        self._data: typing.Dict[KeyT, typing.Tuple[float, ValueT]] = {}

    def _garbage_collect(self) -> None:
        current_time = time.perf_counter()
        for key, value in tuple(self._data.items()):
            if current_time - value[0] < self._expiry:
                break

            del self._data[key]

    def __delitem__(self, key: KeyT) -> None:
        del self._data[key]
        self._garbage_collect()

    def __getitem__(self, key: KeyT) -> ValueT:
        return self._data[key][1]

    def __iter__(self) -> typing.Iterator[KeyT]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __setitem__(self, key: KeyT, value: ValueT) -> None:
        #  Seeing as we rely on insertion order in _garbage_collect, we have to make sure that each item is added to
        #  the end of the dict.
        if key in self:
            del self[key]

        self._data[key] = (time.perf_counter(), value)
        self._garbage_collect()


class CMRIMutableMapping(typing.MutableMapping[KeyT, ValueT]):
    """Implementation of a capacity most recently used mutable mapping.

    This will start removing the oldest entries after it's maximum capacity is
    meet as new entries are added.

    Parameters
    ----------
    limit : int
        The limit for how many objects should be stored by this cache before it
        starts removing the oldest entries.
    """

    __slots__ = ("_data", "_limit")

    def __init__(self, limit: int) -> None:
        self._data: typing.Dict[KeyT, ValueT] = {}
        self._limit = limit

    def _garbage_collect(self) -> None:
        while len(self._data) > self._limit:
            self._data.pop(next(iter(self._data)))

    def __delitem__(self, key: KeyT) -> None:
        del self._data[key]

    def __getitem__(self, key: KeyT) -> ValueT:
        return self._data[key]

    def __iter__(self) -> typing.Iterator[KeyT]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __setitem__(self, key: KeyT, value: ValueT) -> None:
        self._data[key] = value
        self._garbage_collect()


def get_index_or_slice(
    mapping: typing.Mapping[KeyT, ValueT], index_or_slice: typing.Union[int, slice]
) -> typing.Union[ValueT, typing.Sequence[ValueT]]:
    """Get a dict entry at a given index as if it's a sequence of it's values.

    Parameters
    ----------
    mapping : typing.Mapping[KeyT, ValueT]
        The mapping of entries to treat as a sequence.
    index_or_slice : typing.Sequence[KeyT, ValueT]
        The index to get an entry to get or slice of multiple entries to get.

    Returns
    -------
    ValueT or typing.Sequence[ValueT]
        The value found at the given integer index or a sequence of the values
        found based on the given slice's rules.

    Raises
    ------
    TypeError
        If `index_or_slice` isn't a `buildings.slice` or `builtins.int`.
    IndexError
        If `index_or_slice` is an int and is outside the range of the mapping's
        contents.
    """
    if isinstance(index_or_slice, slice):
        return tuple(itertools.islice(mapping.values(), index_or_slice.start, index_or_slice.stop, index_or_slice.step))
    elif isinstance(index_or_slice, int):
        try:
            return next(itertools.islice(mapping.values(), index_or_slice, None))
        except StopIteration:
            raise IndexError(index_or_slice) from None
    else:
        raise TypeError(f"sequence indices must be integers or slices, not {type(index_or_slice).__name__}")
