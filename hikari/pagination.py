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
"""Async iterator extensions for paginated data."""
from __future__ import annotations

import abc
import datetime
import typing

from hikari import bases
from hikari.internal import assertions
from hikari.internal import more_collections

_T = typing.TypeVar("_T")


class PaginatedResults(typing.Generic[_T], abc.ABC):
    """A set of results that are fetched asynchronously from the API as needed.

    This is a `typing.AsyncIterable` and `typing.AsyncIterator` with several
    additional helpful methods provided for convenience.

    Examples
    --------
    You can use this in multiple ways.

    As an async iterable:

        >>> async for item in paginated_results:
        ...    process(item)

    As an eagerly retrieved set of results (performs all API calls at once,
    which may be slow for large sets of data):

        >>> results = await paginated_results
        >>> # ... which is equivalent to this...
        >>> results = [item async for item in paginated_results]

    As an async iterator (not recommended):

        >>> try:
        ...    while True:
        ...        process(await paginated_results.__anext__())
        ... except StopAsyncIteration:
        ...    pass

    Additionally, you can make use of some of the provided helper methods
    on this class to perform basic operations easily.

    Iterating across the items with indexes (like `enumerate` for normal
    iterables):

        >>> async for i, item in paginated_results.enumerate():
        ...    print(i, item)
        (0, foo)
        (1, bar)
        (2, baz)

    Limiting the number of results you iterate across:

        >>> async for item in paginated_results.limit(3):
        ...    process(item)
    """

    __slots__ = ()

    def enumerate(self, *, start: int = 0) -> PaginatedResults[typing.Tuple[int, _T]]:
        """Enumerate the paginated results lazily.

        This behaves as an asyncio-friendly version of `builtins.enumerate`
        which uses much less memory than collecting all the results first and
        calling `enumerate` across them.

        Parameters
        ----------
        start : int
            Optional int to start at. If omitted, this is `0`.

        Examples
        --------
            >>> async for i, item in paginated_results.enumerate():
            ...    print(i, item)
            (0, foo)
            (1, bar)
            (2, baz)
            (3, bork)
            (4, qux)

            >>> async for i, item in paginated_results.enumerate(start=9):
            ...    print(i, item)
            (9, foo)
            (10, bar)
            (11, baz)
            (12, bork)
            (13, qux)

            >>> async for i, item in paginated_results.enumerate(start=9).limit(3):
            ...    print(i, item)
            (9, foo)
            (10, bar)
            (11, baz)

        Returns
        -------
        PaginatedResults[typing.Tuple[int, T]]
            A paginated results view that asynchronously yields an increasing
            counter in a tuple with each result, lazily.
        """
        return _EnumeratedPaginatedResults(self, start=start)

    def limit(self, limit: int) -> PaginatedResults[_T]:
        """Limit the number of items you receive from this async iterator.

        Parameters
        ----------
        limit : int
            The number of items to get. This must be greater than zero.

        Examples
        --------
            >>> async for item in paginated_results.limit(3):
            ...     print(item)


        Returns
        -------
        PaginatedResults[T]
            A paginated results view that asynchronously yields a maximum
            of the given number of items before completing.
        """
        return _LimitedPaginatedResults(self, limit)

    def _complete(self) -> typing.NoReturn:
        raise StopAsyncIteration("No more items exist in this paginator. It has been exhausted.") from None

    def __aiter__(self) -> PaginatedResults[_T]:
        # We are our own iterator.
        return self

    async def _fetch_all(self) -> typing.Sequence[_T]:
        return [item async for item in self]

    @staticmethod
    def _prepare_first_id(value, if_none=bases.Snowflake.min()) -> str:
        """Prepare the given first ID type passed by the user.

        Given an object with an ID, a datetime, an int, a snowflake, or a string
        type, convert the element to the string ID snowflake it represents
        that can be passed to the underlying REST API safely.

        Parameters
        ----------
        value
            The element to prepare.
        if_none
            The value to use if the `value` is `None`. Defaults to a snowflake
            of `0`.

        Returns
        -------
        str
            The string ID.
        """
        if value is None:
            value = if_none

        if isinstance(value, datetime.datetime):
            value = str(int(bases.Snowflake.from_datetime(value)))

        if isinstance(value, (int, bases.Snowflake)):
            return str(value)
        if isinstance(value, bases.Unique):
            return str(value.id)
        if isinstance(value, str):
            return value

        raise TypeError("expected object with ID, datetime, snowflake, or None")

    def __await__(self):
        return self._fetch_all().__await__()

    @abc.abstractmethod
    async def __anext__(self) -> _T:
        ...


_EnumeratedT = typing.Tuple[int, _T]


class _EnumeratedPaginatedResults(typing.Generic[_T], PaginatedResults[_EnumeratedT]):
    __slots__ = ("_i", "_paginator")

    def __init__(self, paginator: PaginatedResults[_T], *, start: int) -> None:
        self._i = start
        self._paginator = paginator

    async def __anext__(self) -> typing.Tuple[int, _T]:
        pair = self._i, await self._paginator.__anext__()
        self._i += 1
        return pair


class _LimitedPaginatedResults(typing.Generic[_T], PaginatedResults[_T]):
    __slots__ = ("_paginator", "_count", "_limit")

    def __init__(self, paginator: PaginatedResults[_T], limit: int) -> None:
        assertions.assert_that(limit > 0, "limit must be positive and non-zero")
        self._paginator = paginator
        self._count = 0
        self._limit = limit

    async def __anext__(self) -> _T:
        if self._count >= self._limit:
            self._complete()

        next_item = await self._paginator.__anext__()
        self._count += 1
        return next_item


class BufferedPaginatedResults(typing.Generic[_T], PaginatedResults[_T]):
    """A buffered paginator implementation that handles chunked responses."""

    __slots__ = ("_buffer",)

    def __init__(self) -> None:
        # Start with an empty generator to force the paginator to get the next item.
        self._buffer = more_collections.EMPTY_GENERATOR_EXPRESSION

    @abc.abstractmethod
    async def _next_chunk(self) -> typing.Optional[typing.Generator[typing.Any, None, _T]]:
        # Return `None` when exhausted.
        ...

    async def __anext__(self) -> _T:
        # This sneaky snippet of code lets us use generators rather than lists.
        # This is important, as we can use this to make generators that
        # deserialize loads of items lazy. If we only want 10 messages of
        # history, we can use the same code and prefetch 100 without any
        # performance hit from it other than the JSON string response.
        try:
            return next(self._buffer)
        except StopIteration:
            self._buffer = await self._next_chunk()
            if self._buffer is None:
                self._complete()
            else:
                return next(self._buffer)
