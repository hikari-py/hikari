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
    "MapT",
    "KeyT",
    "ValueT",
    "MappedCollection",
    "DictionaryCollection",
    "MRIMutableMapping",
    "CMRIMutableMapping",
    "get_index_or_slice",
    "copy_mapping",
]

import abc
import datetime
import itertools
import time
import typing

MapT = typing.TypeVar("MapT", bound="MappedCollection[typing.Any, typing.Any]")
"""Type-hint A type hint used for mapped collection objects."""
KeyT = typing.TypeVar("KeyT", bound=typing.Hashable)
"""Type-hint A type hint used for the type of a mapping's key."""
ValueT = typing.TypeVar("ValueT")
"""Type-hint A type hint used for the type of a mapping's value."""


class MappedCollection(typing.MutableMapping[KeyT, ValueT], abc.ABC):
    """The abstract class of mutable mappings used within hikari.

    This extends `typing.MutableMapping` with "copy" and "freeze" methods.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def copy(self: MapT) -> MapT:
        """Return a copy of this mapped collection.

        Unlike simply doing `dict(mapping)`, this may rely on internal detail
        around how the data is being stored to allow for a more efficient copy.
        This may look like calling `dict.copy` and wrapping the result in a
        mapped collection.

        !!! note
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

        !!! note
            Unlike `MappedCollection.copy`, this should return a pure mapping
            with no removal policy at all.

        Returns
        -------
        typing.MutableMapping[KeyT, ValueT]
            A frozen mapping view of the items in this mapped collection.
        """


class DictionaryCollection(MappedCollection[KeyT, ValueT]):
    """A basic mapped collection that acts like a dictionary."""

    __slots__ = ("_data",)

    def __init__(self, source: typing.Optional[typing.Dict[KeyT, ValueT]] = None, /) -> None:
        self._data = source or {}

    def copy(self) -> DictionaryCollection[KeyT, ValueT]:
        return DictionaryCollection(self._data.copy())

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


class _FrozenMRIMapping(typing.MutableMapping[KeyT, ValueT]):
    __slots__ = ("_source",)

    def __init__(self, source: typing.Dict[KeyT, typing.Tuple[float, ValueT]], /) -> None:
        self._source = source

    def __getitem__(self, key: KeyT) -> ValueT:
        return self._source[key][1]

    def __iter__(self) -> typing.Iterator[KeyT]:
        return iter(self._source)

    def __len__(self) -> int:
        return len(self._source)

    def __delitem__(self, key: KeyT) -> None:
        del self._source[key]

    def __setitem__(self, key: KeyT, value: ValueT) -> None:
        self._source[key] = (0.0, value)


class MRIMutableMapping(MappedCollection[KeyT, ValueT]):
    """A most-recently-inserted limited mutable mapping implementation.

    This will remove entries on modification as as they pass the expiry limit.

    Parameters
    ----------
    expiry : datetime.timedelta
        The timedelta of how long entries should be stored for before removal.
    source : typing.Optional[typing.Dict[KeyT, typing.Tuple[builtins.float, ValueT]]
        A source dictionary of keys to tuples of float timestamps and values to
        create this from.
    """

    __slots__ = ("_data", "_expiry")

    def __init__(
        self,
        source: typing.Optional[typing.Dict[KeyT, typing.Tuple[float, ValueT]]] = None,
        /,
        *,
        expiry: datetime.timedelta,
    ) -> None:
        if expiry <= datetime.timedelta():
            raise ValueError("expiry time must be greater than 0 microseconds.")

        self._expiry: float = expiry.total_seconds()
        self._data = source or {}
        self._garbage_collect()

    def copy(self) -> MRIMutableMapping[KeyT, ValueT]:
        return MRIMutableMapping(self._data.copy(), expiry=datetime.timedelta(seconds=self._expiry))

    def freeze(self) -> typing.MutableMapping[KeyT, ValueT]:
        return _FrozenMRIMapping(self._data.copy())

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


class CMRIMutableMapping(MappedCollection[KeyT, ValueT]):
    """Implementation of a capacity-limited most-recently-inserted mapping.

    This will start removing the oldest entries after it's maximum capacity is
    reached as new entries are added.

    Parameters
    ----------
    limit : int
        The limit for how many objects should be stored by this mapping before
        it starts removing the oldest entries.
    source : typing.Optional[typing.Dict[KeyT, ValueT]]
        A source dictionary of keys to values to create this from.
    """

    __slots__ = ("_data", "_limit")

    def __init__(self, source: typing.Optional[typing.Dict[KeyT, ValueT]] = None, /, *, limit: int) -> None:
        self._data: typing.Dict[KeyT, ValueT] = source or {}
        self._limit = limit
        self._garbage_collect()

    def copy(self) -> CMRIMutableMapping[KeyT, ValueT]:
        return CMRIMutableMapping(self._data.copy(), limit=self._limit)

    def freeze(self) -> typing.Dict[KeyT, ValueT]:
        return self._data.copy()

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
    TypeError
        If `index_or_slice` isn't a `builtins.slice` or `builtins.int`.
    IndexError
        If `index_or_slice` is an int and is outside the range of the mapping's
        contents.
    """
    if isinstance(index_or_slice, slice):
        return tuple(itertools.islice(mapping.values(), index_or_slice.start, index_or_slice.stop, index_or_slice.step))

    if isinstance(index_or_slice, int):
        try:
            return next(itertools.islice(mapping.values(), index_or_slice, None))
        except StopIteration:
            raise IndexError(index_or_slice) from None

    raise TypeError(f"sequence indices must be integers or slices, not {type(index_or_slice).__name__}")


def copy_mapping(mapping: typing.Mapping[KeyT, ValueT]) -> typing.MutableMapping[KeyT, ValueT]:
    """Logic for copying mappings that targets implementation specific copy impls (e.g. dict.copy).

    .. deprecated::
        `MappedCollection` should be preferred over this.
    """
    # dict.copy ranges from between roughly 2 times to 5 times more efficient than casting to a dict so we want to
    # try to use this where possible.
    try:
        return mapping.copy()  # type: ignore[attr-defined, no-any-return]
    except (AttributeError, TypeError):
        raise NotImplementedError("provided mapping doesn't implement a copy method") from None
