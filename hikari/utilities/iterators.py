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
"""Lazy iterators for data that requires repeated API calls to retrieve.

For consumers of this API, the only class you need to worry about is
`LazyIterator`. Everything else is internal detail only exposed for people who
wish to extend this API further!
"""
from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = [
    "LazyIterator",
    "All",
    "AttrComparator",
    "BufferedLazyIterator",
]

import abc
import typing

from hikari.utilities import spel

ValueT = typing.TypeVar("ValueT")
AnotherValueT = typing.TypeVar("AnotherValueT")


class All(typing.Generic[ValueT]):
    """Helper that wraps predicates and invokes them together.

    Calling this object will pass the input item to each item, returning
    `True` only when all wrapped predicates return True when called with the
    given item.

    For example...

    ```py
    if w(foo) and x(foo) and y(foo) and z(foo):
        ...
    ```
    is equivalent to
    ```py
    condition = All([w, x, y, z])

    if condition(foo):
        ...
    ```

    This behaves like a lazy wrapper implementation of the `all` builtin.

    !!! note
        Like the rest of the standard library, this is a short-circuiting
        operation. This means that if a predicate returns `False`, no predicates
        after this are invoked, as the result is already known. In this sense,
        they are invoked in-order.

    !!! warning
        You shouldn't generally need to use this outside of extending the
        iterators API in this library!

    Operators
    ---------
    * `this(value : T) -> bool`:
        Return `True` if all conditions return `True` when invoked with the
        given value.
    * `~this`:
        Return a condition that, when invoked with the value, returns `False`
        if all conditions were `True` in this object.

    Parameters
    ----------
    *conditions : typing.Callable[[T], bool]
        The predicates to wrap.
    """

    __slots__: typing.Sequence[str] = ("conditions",)

    def __init__(self, conditions: typing.Collection[typing.Callable[[ValueT], bool]]) -> None:
        self.conditions = conditions

    def __call__(self, item: ValueT) -> bool:
        return all(condition(item) for condition in self.conditions)

    def __invert__(self) -> typing.Callable[[ValueT], bool]:
        return lambda item: not self(item)


class AttrComparator(typing.Generic[ValueT]):
    """A comparator that compares the result of a call with something else.

    This uses the `spel` module internally.

    Parameters
    ----------
    attr_name : str
        The attribute name. Can be prepended with a `.` optionally.
        If the attribute name ends with a `()`, then the call is invoked
        rather than treated as a property (useful for methods like
        `str.isupper`, for example).
    expected_value : T
        The expected value.
    """

    __slots__: typing.Sequence[str] = ("attr_getter", "expected_value")

    def __init__(self, attr_name: str, expected_value: typing.Any) -> None:
        self.expected_value = expected_value
        self.attr_getter: spel.AttrGetter[ValueT, typing.Any] = spel.AttrGetter(attr_name)

    def __call__(self, item: ValueT) -> bool:
        return bool(self.attr_getter(item))


class LazyIterator(typing.Generic[ValueT], abc.ABC):
    """A set of results that are fetched asynchronously from the API as needed.

    This is a `typing.AsyncIterable` and `typing.AsyncIterator` with several
    additional helpful methods provided for convenience.

    Examples
    --------
    You can use this in multiple ways.

    As an async iterable:

    ```py
    >>> async for item in paginated_results:
    ...    process(item)
    ```

    As an eagerly retrieved set of results (performs all API calls at once,
    which may be slow for large sets of data):

    ```py
    >>> results = await paginated_results
    >>> # ... which is equivalent to this...
    >>> results = [item async for item in paginated_results]
    ```

    As an async iterator (not recommended):

    ```py
    >>> try:
    ...    while True:
    ...        process(await paginated_results.__anext__())
    ... except StopAsyncIteration:
    ...    pass
    ```

    Additionally, you can make use of some of the provided helper methods
    on this class to perform basic operations easily.

    Iterating across the items with indexes (like `enumerate` for normal
    iterables):

    ```py
    >>> async for i, item in paginated_results.enumerate():
    ...    print(i, item)
    (0, foo)
    (1, bar)
    (2, baz)
    ```

    Limiting the number of results you iterate across:

    ```py
    >>> async for item in paginated_results.limit(3):
    ...    process(item)
    ```
    """

    __slots__: typing.Sequence[str] = ()

    def map(
        self, transformation: typing.Union[typing.Callable[[ValueT], AnotherValueT], str],
    ) -> LazyIterator[AnotherValueT]:
        """Map the values to a different value.

        Parameters
        ----------
        transformation : typing.Callable[[ValueT], bool] or str
            The function to use to map the attribute. This may alternatively
            be a string attribute name to replace the input value with. You
            can provide nested attributes using the `.` operator.

        Returns
        -------
        LazyIterator[AnotherValueT]
            LazyIterator that maps each value to another value.
        """
        if isinstance(transformation, str):
            transformation = typing.cast("spel.AttrGetter[ValueT, AnotherValueT]", spel.AttrGetter(transformation))

        return _MappingLazyIterator(self, transformation)

    def filter(
        self,
        *predicates: typing.Union[typing.Tuple[str, typing.Any], typing.Callable[[ValueT], bool]],
        **attrs: typing.Any,
    ) -> LazyIterator[ValueT]:
        """Filter the items by one or more conditions that must all be `True`.

        Parameters
        ----------
        *predicates : typing.Callable[[ValueT], bool] or typing.Tuple[str, typing.Any]
            Predicates to invoke. These are functions that take a value and
            return `True` if it is of interest, or `False` otherwise. These
            may instead include 2-`tuple` objects consisting of a `str`
            attribute name (nested attributes are referred to using the `.`
            operator), and values to compare for equality. This allows you
            to specify conditions such as `members.filter(("user.bot", True))`.
        **attrs : typing.Any
            Alternative to passing 2-tuples. Cannot specify nested attributes
            using this method.

        Returns
        -------
        LazyIterator[ValueT]
            LazyIterator that only emits values where all conditions are
            matched.
        """
        conditions = self._map_predicates_and_attr_getters("filter", *predicates, **attrs)
        return _FilteredLazyIterator(self, conditions)

    def take_while(
        self,
        *predicates: typing.Union[typing.Tuple[str, typing.Any], typing.Callable[[ValueT], bool]],
        **attrs: typing.Any,
    ) -> LazyIterator[ValueT]:
        """Return each item until any conditions fail or the end is reached.

        Parameters
        ----------
        *predicates : typing.Callable[[ValueT], bool] or typing.Tuple[str, typing.Any]
            Predicates to invoke. These are functions that take a value and
            return `True` if it is of interest, or `False` otherwise. These
            may instead include 2-`tuple` objects consisting of a `str`
            attribute name (nested attributes are referred to using the `.`
            operator), and values to compare for equality. This allows you
            to specify conditions such as
            `members.take_while(("user.bot", True))`.
        **attrs : typing.Any
            Alternative to passing 2-tuples. Cannot specify nested attributes
            using this method.

        Returns
        -------
        LazyIterator[ValueT]
            LazyIterator that only emits values until any conditions are not
            matched.
        """
        conditions = self._map_predicates_and_attr_getters("take_while", *predicates, **attrs)
        return _TakeWhileLazyIterator(self, conditions)

    def take_until(
        self,
        *predicates: typing.Union[typing.Tuple[str, typing.Any], typing.Callable[[ValueT], bool]],
        **attrs: typing.Any,
    ) -> LazyIterator[ValueT]:
        """Return each item until any conditions pass or the end is reached.

        Parameters
        ----------
        *predicates : typing.Callable[[ValueT], bool] or typing.Tuple[str, typing.Any]
            Predicates to invoke. These are functions that take a value and
            return `True` if it is of interest, or `False` otherwise. These
            may instead include 2-`tuple` objects consisting of a `str`
            attribute name (nested attributes are referred to using the `.`
            operator), and values to compare for equality. This allows you
            to specify conditions such as
            `members.take_until(("user.bot", True))`.
        **attrs : typing.Any
            Alternative to passing 2-tuples. Cannot specify nested attributes
            using this method.

        Returns
        -------
        LazyIterator[ValueT]
            LazyIterator that only emits values until any conditions are
            matched.
        """
        conditions = self._map_predicates_and_attr_getters("take_until", *predicates, **attrs)
        return _TakeWhileLazyIterator(self, ~conditions)

    def skip_while(
        self,
        *predicates: typing.Union[typing.Tuple[str, typing.Any], typing.Callable[[ValueT], bool]],
        **attrs: typing.Any,
    ) -> LazyIterator[ValueT]:
        """Discard items while all conditions are True.

        Items after this will be yielded as normal.

        Parameters
        ----------
        *predicates : typing.Callable[[ValueT], bool] or typing.Tuple[str, typing.Any]
            Predicates to invoke. These are functions that take a value and
            return `True` if it is of interest, or `False` otherwise. These
            may instead include 2-`tuple` objects consisting of a `str`
            attribute name (nested attributes are referred to using the `.`
            operator), and values to compare for equality. This allows you
            to specify conditions such as
            `members.skip_while(("user.bot", True))`.
        **attrs : typing.Any
            Alternative to passing 2-tuples. Cannot specify nested attributes
            using this method.

        Returns
        -------
        LazyIterator[ValueT]
            LazyIterator that only emits values once a condition has been met.
            All items before this are discarded.
        """
        conditions = self._map_predicates_and_attr_getters("drop_while", *predicates, **attrs)
        return _DropWhileLazyIterator(self, conditions)

    def skip_until(
        self,
        *predicates: typing.Union[typing.Tuple[str, typing.Any], typing.Callable[[ValueT], bool]],
        **attrs: typing.Any,
    ) -> LazyIterator[ValueT]:
        """Discard items while all conditions are False.

        Items after this will be yielded as normal.

        Parameters
        ----------
        *predicates : typing.Callable[[ValueT], bool] or typing.Tuple[str, typing.Any]
            Predicates to invoke. These are functions that take a value and
            return `True` if it is of interest, or `False` otherwise. These
            may instead include 2-`tuple` objects consisting of a `str`
            attribute name (nested attributes are referred to using the `.`
            operator), and values to compare for equality. This allows you
            to specify conditions such as
            `members.skip_until(("user.bot", True))`.
        **attrs : typing.Any
            Alternative to passing 2-tuples. Cannot specify nested attributes
            using this method.

        Returns
        -------
        LazyIterator[ValueT]
            LazyIterator that only emits values once a condition has failed.
            All items before this are discarded.
        """
        conditions = self._map_predicates_and_attr_getters("drop_while", *predicates, **attrs)
        return _DropWhileLazyIterator(self, ~conditions)

    def enumerate(self, *, start: int = 0) -> LazyIterator[typing.Tuple[int, ValueT]]:
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
        LazyIterator[typing.Tuple[int, T]]
            A paginated results view that asynchronously yields an increasing
            counter in a tuple with each result, lazily.
        """
        return _EnumeratedLazyIterator(self, start=start)

    def limit(self, limit: int) -> LazyIterator[ValueT]:
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
        LazyIterator[T]
            A paginated results view that asynchronously yields a maximum
            of the given number of items before completing.
        """
        return _LimitedLazyIterator(self, limit)

    def skip(self, number: int) -> LazyIterator[ValueT]:
        """Drop the given number of items, then yield anything after.

        Parameters
        ----------
        number : int
            The max number of items to drop before any items are yielded.

        Returns
        -------
        LazyIterator[T]
            A paginated results view that asynchronously yields all items
            AFTER the given number of items are discarded first.
        """
        return _DropCountLazyIterator(self, number)

    async def first(self) -> ValueT:
        """Return the first element of this iterator only."""
        return await self.__anext__()

    @staticmethod
    def _map_predicates_and_attr_getters(
        alg_name: str,
        *predicates: typing.Union[str, typing.Tuple[str, typing.Any], typing.Callable[[ValueT], bool]],
        **attrs: typing.Any,
    ) -> All[ValueT]:
        if not predicates and not attrs:
            raise TypeError(f"You should provide at least one predicate to {alg_name}()")

        conditions: typing.List[typing.Callable[[ValueT], bool]] = []

        for p in predicates:
            if isinstance(p, tuple):
                name, value = p
                tuple_comparator: AttrComparator[ValueT] = AttrComparator(name, value)
                conditions.append(tuple_comparator)
            elif isinstance(p, str):
                comparator: AttrComparator[ValueT] = AttrComparator(p, bool)
                conditions.append(comparator)
            else:
                conditions.append(p)

        for name, value in attrs.items():
            attr_comparator: AttrComparator[ValueT] = AttrComparator(name, value)
            conditions.append(attr_comparator)

        return All(conditions)

    def _complete(self) -> typing.NoReturn:
        raise StopAsyncIteration("No more items exist in this paginator. It has been exhausted.") from None

    def __aiter__(self) -> LazyIterator[ValueT]:
        # We are our own iterator.
        return self

    async def _fetch_all(self) -> typing.Sequence[ValueT]:
        return [item async for item in self]

    def __await__(self) -> typing.Generator[None, None, typing.Sequence[ValueT]]:
        return self._fetch_all().__await__()

    @abc.abstractmethod
    async def __anext__(self) -> ValueT:
        ...


class _EnumeratedLazyIterator(typing.Generic[ValueT], LazyIterator[typing.Tuple[int, ValueT]]):
    __slots__: typing.Sequence[str] = ("_i", "_paginator")

    def __init__(self, paginator: LazyIterator[ValueT], *, start: int) -> None:
        self._i = start
        self._paginator = paginator

    async def __anext__(self) -> typing.Tuple[int, ValueT]:
        pair = self._i, await self._paginator.__anext__()
        self._i += 1
        return pair


class _LimitedLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT]):
    __slots__: typing.Sequence[str] = ("_paginator", "_count", "_limit")

    def __init__(self, paginator: LazyIterator[ValueT], limit: int) -> None:
        if limit <= 0:
            raise ValueError("limit must be positive and non-zero")
        self._paginator = paginator
        self._count = 0
        self._limit = limit

    async def __anext__(self) -> ValueT:
        if self._count >= self._limit:
            self._complete()

        next_item = await self._paginator.__anext__()
        self._count += 1
        return next_item


class _DropCountLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT]):
    __slots__: typing.Sequence[str] = ("_paginator", "_count", "_number")

    def __init__(self, paginator: LazyIterator[ValueT], number: int) -> None:
        if number <= 0:
            raise ValueError("number must be positive and non-zero")
        self._paginator = paginator
        self._count = 0
        self._number = number

    async def __anext__(self) -> ValueT:
        while self._count < self._number:
            self._count += 1
            await self._paginator.__anext__()

        next_item = await self._paginator.__anext__()
        return next_item


class _FilteredLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT]):
    __slots__: typing.Sequence[str] = ("_paginator", "_predicate")

    def __init__(self, paginator: LazyIterator[ValueT], predicate: typing.Callable[[ValueT], bool]) -> None:
        self._paginator = paginator
        self._predicate = predicate

    async def __anext__(self) -> ValueT:
        async for item in self._paginator:
            if self._predicate(item):
                return item
        raise StopAsyncIteration


class _MappingLazyIterator(typing.Generic[AnotherValueT, ValueT], LazyIterator[ValueT]):
    __slots__: typing.Sequence[str] = ("_paginator", "_transformation")

    def __init__(
        self, paginator: LazyIterator[AnotherValueT], transformation: typing.Callable[[AnotherValueT], ValueT],
    ) -> None:
        self._paginator = paginator
        self._transformation = transformation

    async def __anext__(self) -> ValueT:
        return self._transformation(await self._paginator.__anext__())


class _TakeWhileLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT]):
    __slots__: typing.Sequence[str] = ("_paginator", "_condition")

    def __init__(self, paginator: LazyIterator[ValueT], condition: typing.Callable[[ValueT], bool],) -> None:
        self._paginator = paginator
        self._condition = condition

    async def __anext__(self) -> ValueT:
        item = await self._paginator.__anext__()

        if self._condition(item):
            return item

        self._complete()


class _DropWhileLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT]):
    __slots__: typing.Sequence[str] = ("_paginator", "_condition", "_has_dropped")

    def __init__(self, paginator: LazyIterator[ValueT], condition: typing.Callable[[ValueT], bool],) -> None:
        self._paginator = paginator
        self._condition = condition
        self._has_dropped = False

    async def __anext__(self) -> ValueT:
        if not self._has_dropped:
            while not self._condition(item := await self._paginator.__anext__()):
                pass

            self._has_dropped = True
            return item

        return await self._paginator.__anext__()


class BufferedLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT], abc.ABC):
    """A special kind of lazy iterator that is used by internal components.

    The purpose of this is to provide an interface to lazily deserialize
    collections of payloads received from paginated API endpoints such as
    `GET /channels/{channel_id}/messages`, which will return a certain number
    of messages at a time on a low level. This class provides the base interface
    for handling lazily decoding each item in those responses and returning them
    in the expected format when iterating across this object.

    Implementations are expected to provide a `_next_chunk` private method
    which when awaited returns a lazy generator of each deserialized object
    to later yield. This will be iterated across lazily by this implementation,
    thus reducing the amount of work needed if only a few objects out of, say,
    100, need to be deserialized.

    This `_next_chunk` should return `None` once the end of all items has been
    reached.

    An example would look like the following:

    ```py
    async def some_http_call(i):
        ...


    class SomeEndpointLazyIterator(BufferedLazyIterator[SomeObject]):
        def __init__(self):
            super().__init__()
            self._i = 0


        def _next_chunk(self) -> typing.Optional[typing.Generator[ValueT, None, None]]:
            raw_items = await some_http_call(self._i)
            self._i += 1

            if not raw_items:
                return None

            generator = (SomeObject(raw_item) for raw_item in raw_items)
            return generator
    ```
    """

    __slots__: typing.Sequence[str] = ("_buffer",)

    def __init__(self) -> None:
        empty_genexp = typing.cast(typing.Generator[ValueT, None, None], (_ for _ in ()))
        self._buffer: typing.Optional[typing.Generator[ValueT, None, None]] = empty_genexp

    @abc.abstractmethod
    async def _next_chunk(self) -> typing.Optional[typing.Generator[ValueT, None, None]]:
        ...

    async def __anext__(self) -> ValueT:
        # This sneaky snippet of code lets us use generators rather than lists.
        # This is important, as we can use this to make generators that
        # deserialize loads of items lazy. If we only want 10 messages of
        # history, we can use the same code and prefetch 100 without any
        # performance hit from it other than the JSON string response.
        try:
            if self._buffer is not None:
                return next(self._buffer)
        except StopIteration:
            self._buffer = await self._next_chunk()
            if self._buffer is not None:
                return next(self._buffer)
        self._complete()
