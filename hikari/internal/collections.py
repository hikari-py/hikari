# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
"""Custom data structures used within Hikari's core implementation."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "ExtendedMapT",
    "KeyT",
    "ValueT",
    "SnowflakeSet",
    "ExtendedMutableMapping",
    "FreezableDict",
    "LimitedCapacityCacheMap",
    "get_index_or_slice",
)

import abc
import array
import bisect
import itertools
import sys
import typing

from hikari import snowflakes

ExtendedMapT = typing.TypeVar("ExtendedMapT", bound="ExtendedMutableMapping[typing.Any, typing.Any]")
"""Type-hint A type hint used for mapped collection objects."""
KeyT = typing.TypeVar("KeyT", bound=typing.Hashable)
"""Type-hint A type hint used for the type of a mapping's key."""
ValueT = typing.TypeVar("ValueT")
"""Type-hint A type hint used for the type of a mapping's value."""

_LONG_LONG_UNSIGNED: typing.Final[str] = sys.intern("Q")


class ExtendedMutableMapping(typing.MutableMapping[KeyT, ValueT], abc.ABC):
    """The abstract class of mutable mappings used within Hikari.

    These are mutable mappings that have a couple of extra methods to allow
    for further optimised copy operations, as well as the ability to freeze
    the implementation of a mapping to make it read-only.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def copy(self: ExtendedMapT) -> ExtendedMapT:
        """Return a copy of this mapped collection.

        Unlike simply doing `dict(mapping)`, this may rely on internal detail
        around how the data is being stored to allow for a more efficient copy.
        This may look like calling `dict.copy` and wrapping the result in a
        mapped collection.

        .. note::
            Any removal policy on this mapped collection will be copied over.

        Returns
        -------
        MapT[KeyT, ValueT]
            A copy of this mapped collection.
        """

    @abc.abstractmethod
    def freeze(self) -> typing.MutableMapping[KeyT, ValueT]:
        """Return a frozen mapping view of the items in this mapped collection.

        Unlike simply doing `dict(mapping)`, this may rely on internal detail
        around how the data is being stored to allow for a more efficient copy.
        This may look like calling `dict.copy`.

        .. note::
            Unlike `ExtendedMutableMapping.copy`, this should return a pure
            mapping with no removal policy at all.

        Returns
        -------
        typing.MutableMapping[KeyT, ValueT]
            A frozen mapping view of the items in this mapped collection.
        """


class FreezableDict(ExtendedMutableMapping[KeyT, ValueT]):
    """A mapping that wraps a dict, but can also be frozen."""

    __slots__: typing.Sequence[str] = ("_data",)

    def __init__(self, source: typing.Optional[typing.Dict[KeyT, ValueT]] = None, /) -> None:
        self._data = source or {}

    def clear(self) -> None:
        self._data.clear()

    def copy(self) -> FreezableDict[KeyT, ValueT]:
        return FreezableDict(self._data.copy())

    # TODO: name this something different if it is not physically frozen.
    def freeze(self) -> typing.Dict[KeyT, ValueT]:
        return self._data.copy()

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


class LimitedCapacityCacheMap(ExtendedMutableMapping[KeyT, ValueT]):
    """Implementation of a capacity-limited most-recently-inserted mapping.

    This will start removing the oldest entries after it's maximum capacity is
    reached as new entries are added.

    Parameters
    ----------
    source : typing.Optional[typing.Dict[KeyT, ValueT]]
        A source dictionary of keys to values to create this from.
    limit : int
        The limit for how many objects should be stored by this mapping before
        it starts removing the oldest entries.
    on_expire : typing.Optional[typing.Callable[[ValueT], None]]
        A function to call each time an item is garbage collected from this
        map. This should take one positional argument of the same type stored
        in this mapping as the value and should return `None`.

        This will always be called after the entry has been removed.
    """

    __slots__: typing.Sequence[str] = ("_data", "_limit", "_on_expire")

    def __init__(
        self,
        source: typing.Optional[typing.Dict[KeyT, ValueT]] = None,
        /,
        *,
        limit: int,
        on_expire: typing.Optional[typing.Callable[[ValueT], None]] = None,
    ) -> None:
        self._data: typing.Dict[KeyT, ValueT] = source or {}
        self._limit = limit
        self._on_expire = on_expire
        self._garbage_collect()

    def clear(self) -> None:
        self._data.clear()

    def copy(self) -> LimitedCapacityCacheMap[KeyT, ValueT]:
        return LimitedCapacityCacheMap(self._data.copy(), limit=self._limit, on_expire=self._on_expire)

    def freeze(self) -> typing.Dict[KeyT, ValueT]:
        return self._data.copy()

    def _garbage_collect(self) -> None:
        while len(self._data) > self._limit:
            value = self._data.pop(next(iter(self._data)))

            if self._on_expire:
                self._on_expire(value)

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


# TODO: can this be immutable?
class SnowflakeSet(typing.MutableSet[snowflakes.Snowflake]):
    r"""Set of `hikari.snowflakes.Snowflake` objects.

    This internally uses a sorted bisect-array of 64 bit integers to represent
    the information. This reduces the space needed to store these objects
    significantly down to the size of 8 bytes per item.

    In contrast, a regular list would take generally 8 bytes per item just to
    store the memory address, and then a further 28 bytes or more to physically
    store the integral value if it does not get interned by the Python
    implementation you are using. A regular set would consume even more
    space, being a hashtable internally.

    The detail of this implementation has the side effect that searches
    will take $$ \mathcal{O} \left( \log n \right) $$ operations in the worst
    case, and $$ \Omega \left (k \right) $$ in the best case. Average case
    will be $$ \mathcal{O} \left( \log n \right) $$

    Insertions and removals will take $$ \mathcal{O} \left( \log n \right) $$
    operations in the worst case, due to `bisect` using a binary insertion sort
    algorithm internally. Average case will be
    $$ \mathcal{O} \left( \log n \right) $$ and best case will be
    $$ \Omega \left\( k \right) $$

    .. warning::
        This is not thread-safe and must not be iterated across whilst being
        concurrently modified.

    Other Parameters
    ----------------
    *ids : int
        The IDs to fill this table with.
    """

    __slots__: typing.Sequence[str] = ("_ids",)

    def __init__(self, *ids: int) -> None:
        self._ids: typing.MutableSequence[int] = array.array(_LONG_LONG_UNSIGNED)

        if ids:
            self.add_all(ids)

    def add(self, value: int, /) -> None:
        """Add a snowflake to this set."""
        # Always append the first item, as we cannot compare with nothing.
        index = bisect.bisect_left(self._ids, value)
        if index == len(self._ids):
            self._ids.append(value)
        elif self._ids[index] != value:
            self._ids.insert(index, value)

    def add_all(self, sfs: typing.Iterable[int], /) -> None:
        """Add a collection of snowflakes to this set."""
        if not sfs:
            return

        for sf in sfs:
            # Yes, this is repeated code, but we want insertions to be as fast
            # as possible for caching purposes, so reduce the number of function
            # calls as much as possible and reimplement the logic for `add`
            # here.
            index = bisect.bisect_left(self._ids, sf)
            if index == len(self._ids):
                self._ids.append(sf)
            elif self._ids[index] != sf:
                self._ids.insert(index, sf)

    def clear(self) -> None:
        """Clear all items from this collection."""
        # Arrays lack a "clear" method.
        self._ids = array.array(_LONG_LONG_UNSIGNED)

    def discard(self, value: int, /) -> None:
        """Remove a snowflake from this set if it's present."""
        if not self._ids:
            return

        index = bisect.bisect_left(self._ids, value)

        if index < len(self) and self._ids[index] == value:
            del self._ids[index]

    def __contains__(self, value: typing.Any) -> bool:
        if not isinstance(value, int):
            return False

        index = bisect.bisect_left(self._ids, value)

        if index < len(self._ids):
            return self._ids[index] == value
        return False

    def __iter__(self) -> typing.Iterator[snowflakes.Snowflake]:
        return map(snowflakes.Snowflake, self._ids)

    def __len__(self) -> int:
        return len(self._ids)

    def __repr__(self) -> str:
        return type(self).__name__ + "(" + ", ".join(map(repr, self._ids)) + ")"

    def __sizeof__(self) -> int:
        return super().__sizeof__() + sys.getsizeof(self._ids)

    def __str__(self) -> str:
        return "{" + ", ".join(map(repr, self._ids)) + "}"


def get_index_or_slice(
    mapping: typing.Mapping[KeyT, ValueT], index_or_slice: typing.Union[int, slice]
) -> typing.Union[ValueT, typing.Sequence[ValueT]]:
    """Get a mapping's entry at a given index as if it's a sequence of it's values.

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
    IndexError
        If `index_or_slice` is an int and is outside the range of the mapping's
        contents.
    """
    if isinstance(index_or_slice, slice):
        return tuple(itertools.islice(mapping.values(), index_or_slice.start, index_or_slice.stop, index_or_slice.step))

    try:
        return next(itertools.islice(mapping.values(), index_or_slice, None))
    except StopIteration:
        raise IndexError(index_or_slice) from None
