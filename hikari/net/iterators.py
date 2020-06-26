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
"""Lazy iterators for data that requires repeated API calls to retrieve."""
from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = ["LazyIterator"]

import abc
import operator
import typing

from hikari.net import routes
from hikari.utilities import data_binding
from hikari.utilities import snowflake
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.api import rest

    from hikari.models import applications
    from hikari.models import audit_logs
    from hikari.models import guilds
    from hikari.models import messages
    from hikari.models import users

ValueT = typing.TypeVar("ValueT")
AnotherValueT = typing.TypeVar("AnotherValueT")


class _AllConditions(typing.Generic[ValueT]):
    __slots__: typing.Sequence[str] = ("conditions",)

    def __init__(self, conditions: typing.Collection[typing.Callable[[ValueT], bool]]) -> None:
        self.conditions = conditions

    def __call__(self, item: ValueT) -> bool:
        return all(condition(item) for condition in self.conditions)


class _AttrComparator(typing.Generic[ValueT]):
    __slots__: typing.Sequence[str] = ("getter", "expected_value")

    def __init__(self, attr_name: str, expected_value: typing.Any) -> None:
        if attr_name.startswith("."):
            attr_name = attr_name[1:]
        self.getter = operator.attrgetter(attr_name)
        self.expected_value = expected_value

    def __call__(self, item: ValueT) -> bool:
        return bool(self.getter(item) == self.expected_value)


class LazyIterator(typing.Generic[ValueT], abc.ABC):
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
            if transformation.startswith("."):
                transformation = transformation[1:]
            transformation = operator.attrgetter(transformation)
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
        if not predicates and not attrs:
            raise TypeError("You should provide at least one predicate to filter()")

        conditions: typing.List[typing.Callable[[ValueT], bool]] = []

        for p in predicates:
            if isinstance(p, tuple):
                name, value = p
                tuple_comparator: _AttrComparator[ValueT] = _AttrComparator(name, value)
                conditions.append(tuple_comparator)
            else:
                conditions.append(p)

        for name, value in attrs.items():
            attr_comparator: _AttrComparator[ValueT] = _AttrComparator(name, value)
            conditions.append(attr_comparator)

        if len(conditions) > 1:
            return _FilteredLazyIterator(self, _AllConditions(conditions))
        else:
            return _FilteredLazyIterator(self, conditions[0])

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


class _BufferedLazyIterator(typing.Generic[ValueT], LazyIterator[ValueT]):
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


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class MessageIterator(_BufferedLazyIterator["messages.Message"]):
    """Implementation of an iterator for message history."""

    __slots__: typing.Sequence[str] = ("_app", "_request_call", "_direction", "_first_id", "_route")

    def __init__(
        self,
        app: rest.IRESTClient,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        channel_id: str,
        direction: str,
        first_id: str,
    ) -> None:
        super().__init__()
        self._app = app
        self._request_call = request_call
        self._direction = direction
        self._first_id = first_id
        self._route = routes.GET_CHANNEL_MESSAGES.compile(channel=channel_id)

    async def _next_chunk(self) -> typing.Optional[typing.Generator[messages.Message, typing.Any, None]]:
        query = data_binding.StringMapBuilder()
        query.put(self._direction, self._first_id)
        query.put("limit", 100)

        raw_chunk = await self._request_call(compiled_route=self._route, query=query)
        chunk = typing.cast(data_binding.JSONArray, raw_chunk)

        if not chunk:
            return None
        if self._direction == "after":
            chunk.reverse()

        self._first_id = chunk[-1]["id"]
        return (self._app.entity_factory.deserialize_message(m) for m in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class ReactorIterator(_BufferedLazyIterator["users.User"]):
    """Implementation of an iterator for message reactions."""

    __slots__: typing.Sequence[str] = ("_app", "_first_id", "_route", "_request_call")

    def __init__(
        self,
        app: rest.IRESTClient,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        channel_id: str,
        message_id: str,
        emoji: str,
    ) -> None:
        super().__init__()
        self._app = app
        self._request_call = request_call
        self._first_id = snowflake.Snowflake.min()
        self._route = routes.GET_REACTIONS.compile(channel=channel_id, message=message_id, emoji=emoji)

    async def _next_chunk(self) -> typing.Optional[typing.Generator[users.User, typing.Any, None]]:
        query = data_binding.StringMapBuilder()
        query.put("after", self._first_id)
        query.put("limit", 100)

        raw_chunk = await self._request_call(compiled_route=self._route, query=query)
        chunk = typing.cast(data_binding.JSONArray, raw_chunk)

        if not chunk:
            return None

        self._first_id = chunk[-1]["id"]
        return (self._app.entity_factory.deserialize_user(u) for u in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class OwnGuildIterator(_BufferedLazyIterator["applications.OwnGuild"]):
    """Implementation of an iterator for retrieving guilds you are in."""

    __slots__: typing.Sequence[str] = ("_app", "_request_call", "_route", "_newest_first", "_first_id")

    def __init__(
        self,
        app: rest.IRESTClient,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        newest_first: bool,
        first_id: str,
    ) -> None:
        super().__init__()
        self._app = app
        self._newest_first = newest_first
        self._request_call = request_call
        self._first_id = first_id
        self._route = routes.GET_MY_GUILDS.compile()

    async def _next_chunk(self) -> typing.Optional[typing.Generator[applications.OwnGuild, typing.Any, None]]:
        query = data_binding.StringMapBuilder()
        query.put("before" if self._newest_first else "after", self._first_id)
        query.put("limit", 100)

        raw_chunk = await self._request_call(compiled_route=self._route, query=query)
        chunk = typing.cast(data_binding.JSONArray, raw_chunk)

        if not chunk:
            return None

        self._first_id = chunk[-1]["id"]
        return (self._app.entity_factory.deserialize_own_guild(g) for g in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class MemberIterator(_BufferedLazyIterator["guilds.Member"]):
    """Implementation of an iterator for retrieving members in a guild."""

    __slots__: typing.Sequence[str] = ("_app", "_request_call", "_route", "_first_id")

    def __init__(
        self,
        app: rest.IRESTClient,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        guild_id: str,
    ) -> None:
        super().__init__()
        self._route = routes.GET_GUILD_MEMBERS.compile(guild=guild_id)
        self._request_call = request_call
        self._app = app
        self._first_id = snowflake.Snowflake.min()

    async def _next_chunk(self) -> typing.Optional[typing.Generator[guilds.Member, typing.Any, None]]:
        query = data_binding.StringMapBuilder()
        query.put("after", self._first_id)
        query.put("limit", 100)

        raw_chunk = await self._request_call(compiled_route=self._route, query=query)
        chunk = typing.cast(data_binding.JSONArray, raw_chunk)

        if not chunk:
            return None

        # noinspection PyTypeChecker
        self._first_id = chunk[-1]["user"]["id"]

        return (self._app.entity_factory.deserialize_member(m) for m in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class AuditLogIterator(LazyIterator["audit_logs.AuditLog"]):
    """Iterator implementation for an audit log."""

    def __init__(
        self,
        app: rest.IRESTClient,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        guild_id: str,
        before: str,
        user_id: typing.Union[str, undefined.UndefinedType],
        action_type: typing.Union[int, undefined.UndefinedType],
    ) -> None:
        self._action_type = action_type
        self._app = app
        self._first_id = str(before)
        self._request_call = request_call
        self._route = routes.GET_GUILD_AUDIT_LOGS.compile(guild=guild_id)
        self._user_id = user_id

    async def __anext__(self) -> audit_logs.AuditLog:
        query = data_binding.StringMapBuilder()
        query.put("limit", 100)
        query.put("user_id", self._user_id)
        query.put("event_type", self._action_type)

        raw_response = await self._request_call(compiled_route=self._route, query=query)
        response = typing.cast(data_binding.JSONObject, raw_response)

        if not response["entries"]:
            raise StopAsyncIteration

        log = self._app.entity_factory.deserialize_audit_log(response)
        self._first_id = str(min(log.entries.keys()))
        return log
