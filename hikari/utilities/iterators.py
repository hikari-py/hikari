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
"""Lazy iterators for data that requires repeated API calls to retrieve.

For consumers of this API, the only class you need to worry about is
`LazyIterator`. Everything else is internal detail only exposed for people who
wish to extend this API further!
"""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "LazyIterator",
    "FlatLazyIterator",
    "All",
    "AttrComparator",
    "BufferedLazyIterator",
    "ValueT",
    "AnotherValueT",
]

import abc
import asyncio
import typing

from hikari.utilities import spel

ValueT = typing.TypeVar("ValueT")
"""Type-hint of the type of the value returned by a lazy iterator."""
AnotherValueT = typing.TypeVar("AnotherValueT")
"""Type-hint of the type of a value by a mapped lazy iterator."""


class All(typing.Generic[ValueT]):
    """Helper that wraps predicates and invokes them together.

    Calling this object will pass the input item to each item, returning
    `builtins.True` only when all wrapped predicates return True when called
    with the given item.

    For example...

    ```py
    if w(foo) and x(foo) andy(foo) and z(foo):
        ...
    ```
    is equivalent to
    ```py
    condition = All([w, x, y, z])

    if condition(foo):
        ...
    ```

    This behaves like a lazy wrapper implementation of the `builtins.all` builtin.

    !!! note
        Like the rest of the standard library, this is a short-circuiting
        operation. This means that if a predicate returns `builtins.False`, no
        predicates after this are invoked, as the result is already known. In
        this sense, they are invoked in-order.

    !!! warning
        You should not generally need to use this outside of extending the
        iterators API in this library!

    Operators
    ---------
    * `this(value : ValueT) -> bool`:
        Return `builtins.True` if all conditions return `builtins.True` when
        invoked with the given value.
    * `~this`:
        Return a condition that, when invoked with the value, returns
        `builtins.False` if all conditions were `builtins.True` in this object.

    Parameters
    ----------
    *conditions : typing.Callable[[ValueT], builtins.bool]
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
    attr_name : builtins.str
        The attribute name. Can be prepended with a `.` optionally.
        If the attribute name ends with a `()`, then the call is invoked
        rather than treated as a property (useful for methods like
        `str.isupper`, for example).
    expected_value : typing.Any
        The expected value.
    cast : typing.Optional[typing.Callable[[ValueT], typing.Any]]
        Optional cast to perform on the input value when being called before
        comparing it to the expected value but after accessing the attribute.
    """

    __slots__: typing.Sequence[str] = ("attr_getter", "expected_value", "cast")

    def __init__(
        self,
        attr_name: str,
        expected_value: typing.Any,
        cast: typing.Optional[typing.Callable[[ValueT], typing.Any]] = None,
    ) -> None:
        self.expected_value = expected_value
        self.attr_getter: spel.AttrGetter[ValueT, typing.Any] = spel.AttrGetter(attr_name)
        self.cast = cast

    def __call__(self, item: ValueT) -> bool:
        real_item = self.cast(self.attr_getter(item)) if self.cast is not None else self.attr_getter(item)
        return bool(real_item == self.expected_value)


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

    Iterating across the items with indexes (like `builtins.enumerate` for normal
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

    def chunk(self, chunk_size: int) -> LazyIterator[typing.Sequence[ValueT]]:
        """Return results in chunks of up to `chunk_size` amount of entries.

        Parameters
        ----------
        chunk_size : int
            The limit for how many results should be returned in each chunk.

        Returns
        -------
        LazyIterator[typing.Sequence[ValueT]]
            `LazyIterator` that emits each chunked sequence.
        """
        return _ChunkedLazyIterator(self, chunk_size)

    def map(
        self, transformation: typing.Union[typing.Callable[[ValueT], AnotherValueT], str],
    ) -> LazyIterator[AnotherValueT]:
        """Map the values to a different value.

        Parameters
        ----------
        transformation : typing.Callable[[ValueT], builtins.bool] or builtins.str
            The function to use to map the attribute. This may alternatively
            be a string attribute name to replace the input value with. You
            can provide nested attributes using the `.` operator.

        Returns
        -------
        LazyIterator[AnotherValueT]
            `LazyIterator` that maps each value to another value.
        """
        if isinstance(transformation, str):
            transformation = typing.cast("spel.AttrGetter[ValueT, AnotherValueT]", spel.AttrGetter(transformation))

        return _MappingLazyIterator(self, transformation)

    async def for_each(self, consumer: typing.Callable[[ValueT], typing.Any]) -> None:
        """Pass each value to a given consumer immediately."""
        if asyncio.iscoroutinefunction(consumer):
            async for item in self:
                await consumer(item)
        else:
            async for item in self:
                consumer(item)

    def filter(
        self,
        *predicates: typing.Union[typing.Tuple[str, typing.Any], typing.Callable[[ValueT], bool]],
        **attrs: typing.Any,
    ) -> LazyIterator[ValueT]:
        """Filter the items by one or more conditions.

        Each condition is treated as a predicate, being called with each item
        that this iterator would return when it is requested.

        All conditions must evaluate to `builtins.True` for the item to be
        returned. If this is not met, then the item is discared and ignored,
        the next matching item will be returned instead, if there is one.

        Parameters
        ----------
        *predicates : typing.Callable[[ValueT], builtins.bool] or typing.Tuple[builtins.str, typing.Any]
            Predicates to invoke. These are functions that take a value and
            return `builtins.True` if it is of interest, or `builtins.False`
            otherwise. These may instead include 2-`builtins.tuple` objects
            consisting of a `builtins.str` attribute name (nested attributes
            are referred to using the `.` operator), and values to compare for
            equality. This allows you to specify conditions such as
            `members.filter(("user.bot", True))`.
        **attrs : typing.Any
            Alternative to passing 2-tuples. Cannot specify nested attributes
            using this method.

        Returns
        -------
        LazyIterator[ValueT]
            `LazyIterator` that only emits values where all conditions are
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
        *predicates : typing.Callable[[ValueT], builtins.bool] or typing.Tuple[builtins.str, typing.Any]
            Predicates to invoke. These are functions that take a value and
            return `builtins.True` if it is of interest, or `builtins.False`
            otherwise. These may instead include 2-`builtins.tuple` objects
            consisting of a `builtins.str` attribute name (nested attributes
            are referred to using the `.` operator), and values to compare for
            equality. This allows you to specify conditions such as
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
        *predicates : typing.Callable[[ValueT], builtins.bool] or typing.Tuple[builtins.str, typing.Any]
            Predicates to invoke. These are functions that take a value and
            return `builtins.True` if it is of interest, or `builtins.False`
            otherwise. These may instead include 2-`builtins.tuple` objects
            consisting of a `builtins.str` attribute name (nested attributes are
            referred to using the `.` operator), and values to compare for
            equality. This allows you to specify conditions such as
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
        *predicates : typing.Callable[[ValueT], builtins.bool] or typing.Tuple[builtins.str, typing.Any]
            Predicates to invoke. These are functions that take a value and
            return `builtins.True` if it is of interest, or `builtins.False`
            otherwise. These may instead include 2-`builtins.tuple` objects
            consisting of a `builtins.str` attribute name (nested attributes
            are referred to using the `.` operator), and values to compare for
            equality. This allows you to specify conditions such as
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
        conditions = self._map_predicates_and_attr_getters("skip_while", *predicates, **attrs)
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
        *predicates : typing.Callable[[ValueT], builtins.bool] or typing.Tuple[builtins.str, typing.Any]
            Predicates to invoke. These are functions that take a value and
            return `builtins.True` if it is of interest, or `builtins.False`
            otherwise. These may instead include 2-`builtins.tuple` objects
            consisting of a `builtins.str` attribute name (nested attributes are
            referred to using the `.` operator), and values to compare for
            equality. This allows you to specify conditions such as
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
        conditions = self._map_predicates_and_attr_getters("skip_until", *predicates, **attrs)
        return _DropWhileLazyIterator(self, ~conditions)

    def enumerate(self, *, start: int = 0) -> LazyIterator[typing.Tuple[int, ValueT]]:
        """Enumerate the paginated results lazily.

        This behaves as an asyncio-friendly version of `builtins.enumerate`
        which uses much less memory than collecting all the results first and
        calling `builtins.enumerate` across them.

        Parameters
        ----------
        start : builtins.int
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
        LazyIterator[typing.Tuple[builtins.int, T]]
            A paginated results view that asynchronously yields an increasing
            counter in a tuple with each result, lazily.
        """
        return _EnumeratedLazyIterator(self, start=start)

    def limit(self, limit: int) -> LazyIterator[ValueT]:
        """Limit the number of items you receive from this async iterator.

        Parameters
        ----------
        limit : builtins.int
            The number of items to get. This must be greater than zero.

        Examples
        --------
            >>> async for item in paginated_results.limit(3):
            ...     print(item)

        Returns
        -------
        LazyIterator[ValueT]
            A paginated results view that asynchronously yields a maximum
            of the given number of items before completing.
        """
        return _LimitedLazyIterator(self, limit)

    def skip(self, number: int) -> LazyIterator[ValueT]:
        """Drop the given number of items, then yield anything after.

        Parameters
        ----------
        number : builtins.int
            The max number of items to drop before any items are yielded.

        Returns
        -------
        LazyIterator[ValueT]
            A paginated results view that asynchronously yields all items
            AFTER the given number of items are discarded first.
        """
        return _DropCountLazyIterator(self, number)

    async def next(self) -> ValueT:
        """Return the next element of this iterator only.

        Returns
        -------
        ValueT
            The next result.

        Raises
        ------
        builtins.LookupError
            If no more results exist.
        """
        try:
            return await self.__anext__()
        except StopAsyncIteration:
            raise LookupError("No elements were found") from None

    async def last(self) -> ValueT:
        """Return the last element of this iterator only.

        Returns
        -------
        ValueT
            The last result.

        !!! note
            This method will consume the whole iterator if run.

        Raises
        ------
        builtins.LookupError
            If no result exists.
        """
        return await self.reversed().next()

    def reversed(self) -> LazyIterator[ValueT]:
        """Return a lazy iterator of the remainder of this iterator's values reversed.

        Returns
        -------
        LazyIterator[ValueT]
            The lazy iterator of this iterator's remaining values reversed.
        """
        return _ReversedLazyIterator(self)

    async def sort(self, *, key: typing.Any = None, reverse: bool = False) -> typing.Sequence[ValueT]:
        """Collect all results, then sort the collection before returning it."""
        return sorted(await self, key=key, reverse=reverse)

    async def collect(
        self, collector: typing.Callable[[typing.Sequence[ValueT]], typing.Collection[ValueT]]
    ) -> typing.Collection[ValueT]:
        """Collect the results into a given type and return it.

        Parameters
        ----------
        collector
            A function that consumes a sequence of values and returns a
            collection.
        """
        return collector(await self)

    async def count(self) -> int:
        """Count the number of results.

        Returns
        -------
        builtins.int
            Number of results found.
        """
        count = 0
        async for _ in self:
            count += 1

        return count

    def flat_map(self, flattener: _FlattenerT[ValueT, AnotherValueT]) -> LazyIterator[AnotherValueT]:
        r"""Perform a flat mapping operation.

        This will pass each item in the iterator to the given `function`
        parameter, expecting a new `typing.Iterable` or `typing.AsyncIterator`
        to be returned as the result. This means you can map to a new
        `LazyIterator`, `typing.AsyncIterator`, `typing.Iterable`,
        async generator, or generator.

        Remember that `typing.Iterator` implicitly provides `typing.Iterable`
        compatibility.

        This is used to provide lazy conversions, and can be used to implement
        reactive-like pipelines if desired.

        All results are combined into one large lazy iterator and yielded
        lazily.

        Parameters
        ----------
        flattener
            A function that returns either an async iterator or iterator of
            new values. Could be an attribute name instead.

        Example
        -------

        The following example generates a distinct collection of all mentioned
        users in the given channel from the past 500 messages.

        ```py
        def iter_mentioned_users(message: hikari.Message) -> typing.Iterable[Snowflake]:
            for match in re.findall(r"<@!?(\d+)>", message.content):
                yield Snowflake(match)

        mentioned_users = await (
            channel
            .history()
            .limit(500)
            .map(".content")
            .flat_map(iter_mentioned_users)
            .distinct()
        )
        ```

        Returns
        -------
        LazyIterator[AnotherValueT]
            The new lazy iterator to return.
        """
        return _FlatMapLazyIterator(self, flattener)

    def awaiting(self, window_size: int = 10) -> LazyIterator[ValueT]:
        """Await each item concurrently in a fixed size window.

        Parameters
        ----------
        window_size : int
            The window size of how many tasks to await at once. You can set this
            to `0` to await everything at once, but see the below warning.

        Returns
        -------
        LazyIterator[ValueT]
            The new lazy iterator to return.

        !!! warning
            Setting a large window size, or setting it to 0 to await everything
            is a dangerous thing to do if you are making API calls. Some
            endpoints will get ratelimited and cause a backup of waiting
            tasks, others may begin to spam global rate limits instead
            (the `fetch_user` endpoint seems to be notorious for doing this).

        !!! note
            This call assumes that the iterator contains awaitable values as
            input. MyPy cannot detect this nicely, so any cast is forced
            internally.

            If the item is not awaitable, you will receive a
            `builtins.TypeError` instead.

            You have been warned. You cannot escape the ways of the duck type
            young grasshopper.
        """
        # Not type safe. Can I make this type safe?
        return _AwaitingLazyIterator(typing.cast(LazyIterator[typing.Awaitable[ValueT]], self), window_size)

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
                comparator: AttrComparator[ValueT] = AttrComparator(p, True, bool)
                conditions.append(comparator)
            else:
                conditions.append(p)

        for name, value in attrs.items():
            attr_comparator: AttrComparator[ValueT] = AttrComparator(name, value)
            conditions.append(attr_comparator)

        return All(conditions)

    def _complete(self) -> typing.NoReturn:
        raise StopAsyncIteration("No more items exist in this iterator. It has been exhausted.") from None

    def __aiter__(self) -> LazyIterator[ValueT]:
        # We are our own async iterator.
        return self

    # noinspection PyTypeChecker
    def __iter__(self) -> LazyIterator[ValueT]:
        # This iterator is async only.
        cls = type(self)
        raise TypeError(f"{cls.__module__}.{cls.__qualname__} is an async-only iterator, did you mean 'async for'?")

    async def _fetch_all(self) -> typing.Sequence[ValueT]:
        return [item async for item in self]

    def __await__(self) -> typing.Generator[None, None, typing.Sequence[ValueT]]:
        return self._fetch_all().__await__()

    @abc.abstractmethod
    async def __anext__(self) -> ValueT:
        ...


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

    This `_next_chunk` should return `builtins.None` once the end of all items has been
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


class FlatLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT]):
    """A lazy iterator that has all items in-memory and ready.

    This can be iterated across as a normal iterator, or as an async iterator.
    """

    __slots__: typing.Sequence[str] = ("_iter",)

    def __init__(self, values: typing.Iterable[ValueT]) -> None:
        self._iter = iter(values)

    def __iter__(self) -> FlatLazyIterator[ValueT]:
        return self

    def __next__(self) -> ValueT:
        return next(self._iter)

    async def __anext__(self) -> ValueT:
        try:
            return next(self._iter)
        except StopIteration:
            self._complete()


class _EnumeratedLazyIterator(typing.Generic[ValueT], LazyIterator[typing.Tuple[int, ValueT]]):
    __slots__: typing.Sequence[str] = ("_i", "_iterator")

    def __init__(self, iterator: LazyIterator[ValueT], *, start: int) -> None:
        self._i = start
        self._iterator = iterator

    async def __anext__(self) -> typing.Tuple[int, ValueT]:
        pair = self._i, await self._iterator.__anext__()
        self._i += 1
        return pair


class _LimitedLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT]):
    __slots__: typing.Sequence[str] = ("_iterator", "_count", "_limit")

    def __init__(self, iterator: LazyIterator[ValueT], limit: int) -> None:
        if limit <= 0:
            raise ValueError("limit must be positive and non-zero")
        self._iterator = iterator
        self._count = 0
        self._limit = limit

    async def __anext__(self) -> ValueT:
        if self._count >= self._limit:
            self._complete()

        next_item = await self._iterator.__anext__()
        self._count += 1
        return next_item


class _DropCountLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT]):
    __slots__: typing.Sequence[str] = ("_iterator", "_count", "_number")

    def __init__(self, iterator: LazyIterator[ValueT], number: int) -> None:
        if number <= 0:
            raise ValueError("number must be positive and non-zero")
        self._iterator = iterator
        self._count = 0
        self._number = number

    async def __anext__(self) -> ValueT:
        while self._count < self._number:
            self._count += 1
            await self._iterator.__anext__()

        next_item = await self._iterator.__anext__()
        return next_item


class _FilteredLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT]):
    __slots__: typing.Sequence[str] = ("_iterator", "_predicate")

    def __init__(self, iterator: LazyIterator[ValueT], predicate: typing.Callable[[ValueT], bool]) -> None:
        self._iterator = iterator
        self._predicate = predicate

    async def __anext__(self) -> ValueT:
        async for item in self._iterator:
            if self._predicate(item):
                return item

        self._complete()


class _ChunkedLazyIterator(typing.Generic[ValueT], LazyIterator[typing.Sequence[ValueT]]):
    __slots__: typing.Sequence[str] = ("_iterator", "_chunk_size")

    def __init__(self, iterator: LazyIterator[ValueT], chunk_size: int) -> None:
        self._iterator = iterator
        self._chunk_size = chunk_size

    async def __anext__(self) -> typing.Sequence[ValueT]:
        chunk = []

        async for item in self._iterator:
            chunk.append(item)

            if len(chunk) == self._chunk_size:
                break

        if chunk:
            return chunk

        self._complete()


class _ReversedLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT]):
    __slots__: typing.Sequence[str] = ("_buffer", "_origin")

    def __init__(self, iterator: LazyIterator[ValueT]) -> None:
        self._buffer: typing.MutableSequence[ValueT] = []
        self._origin: typing.Optional[LazyIterator[ValueT]] = iterator

    async def __anext__(self) -> ValueT:
        if self._origin is not None:
            self._buffer.extend(await self._origin)
            self._origin = None

        try:
            return self._buffer.pop()
        except IndexError:
            self._complete()


class _MappingLazyIterator(typing.Generic[AnotherValueT, ValueT], LazyIterator[ValueT]):
    __slots__: typing.Sequence[str] = ("_iterator", "_transformation")

    def __init__(
        self, iterator: LazyIterator[AnotherValueT], transformation: typing.Callable[[AnotherValueT], ValueT],
    ) -> None:
        self._iterator = iterator
        self._transformation = transformation

    async def __anext__(self) -> ValueT:
        return self._transformation(await self._iterator.__anext__())


class _TakeWhileLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT]):
    __slots__: typing.Sequence[str] = ("_iterator", "_condition")

    def __init__(self, iterator: LazyIterator[ValueT], condition: typing.Callable[[ValueT], bool]) -> None:
        self._iterator = iterator
        self._condition = condition

    async def __anext__(self) -> ValueT:
        item = await self._iterator.__anext__()

        if self._condition(item):
            return item

        self._complete()


class _DropWhileLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT]):
    __slots__: typing.Sequence[str] = ("_iterator", "_condition", "_has_dropped")

    def __init__(self, iterator: LazyIterator[ValueT], condition: typing.Callable[[ValueT], bool]) -> None:
        self._iterator = iterator
        self._condition = condition
        self._has_dropped = False

    async def __anext__(self) -> ValueT:
        if not self._has_dropped:
            while not self._condition(item := await self._iterator.__anext__()):
                pass

            self._has_dropped = True
            return item

        return await self._iterator.__anext__()


_FlattenerResultT = typing.Union[typing.AsyncIterator[AnotherValueT], typing.Iterable[AnotherValueT]]

_FlattenerT = typing.Union[
    spel.AttrGetter[ValueT, _FlattenerResultT[AnotherValueT]],
    typing.Callable[[ValueT], _FlattenerResultT[AnotherValueT]],
]


class _FlatMapLazyIterator(typing.Generic[ValueT, AnotherValueT], LazyIterator[AnotherValueT]):
    __slots__: typing.Sequence[str] = ("_iterator", "_flattener", "_result_iterator")

    def __init__(self, iterator: LazyIterator[ValueT], flattener: _FlattenerT[ValueT, AnotherValueT]) -> None:
        self._iterator = iterator
        self._flattener = flattener
        self._result_iterator: typing.Optional[typing.AsyncIterator[AnotherValueT]] = None

    async def _generator(self) -> typing.AsyncIterator[AnotherValueT]:
        async for input_item in self._iterator:
            result_iterator = self._flattener(input_item)

            # Turns out that Iterator is also Iterable, interestingly.
            if isinstance(result_iterator, typing.Iterable):
                for output_item in result_iterator:
                    yield output_item
            else:
                async for output_item in result_iterator:
                    yield output_item

    async def __anext__(self) -> AnotherValueT:
        if self._result_iterator is None:
            self._result_iterator = self._generator()

        return await self._result_iterator.__anext__()


class _AwaitingLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT]):
    __slots__: typing.Sequence[str] = ("_iterator", "_window_size", "_buffer")

    def __init__(self, iterator: LazyIterator[typing.Awaitable[ValueT]], window_size: int) -> None:
        self._iterator = iterator
        self._window_size = float("inf") if window_size <= 0 else window_size
        self._buffer: typing.List[ValueT] = []

    async def __anext__(self) -> ValueT:
        if not self._buffer:
            coroutines: typing.List[typing.Awaitable[ValueT]] = []

            while len(coroutines) < self._window_size:
                try:
                    next_coroutine = await self._iterator.__anext__()
                    coroutines.append(next_coroutine)
                except StopAsyncIteration:
                    break

            if not coroutines:
                raise StopAsyncIteration

            self._buffer.extend(await asyncio.gather(*coroutines))

        return self._buffer.pop(0)
