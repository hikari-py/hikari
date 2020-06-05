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
"""Asyncio extensions and utilities."""

from __future__ import annotations

__all__ = ["completed_future", "is_async_iterator", "is_async_iterable", "Future", "Task"]

import asyncio
import inspect
import typing

if typing.TYPE_CHECKING:
    import contextvars
    import types

T_contra = typing.TypeVar("T_contra", contravariant=True)


def completed_future(result: typing.Optional[T_contra] = None, /) -> Future[typing.Optional[T_contra]]:
    """Create a future on the current running loop that is completed, then return it.

    Parameters
    ----------
    result : T_contra or None
        The value to set for the result of the future.
        `T_contra` is a generic type placeholder for the type that
        the future will have set as the result.

    Returns
    -------
    Future[T_contra or None]
        The completed future.
    """
    future = asyncio.get_event_loop().create_future()
    future.set_result(result)
    return future


# On Python3.8.2, there appears to be a bug with the typing module:

# >>> class Aiterable:
# ...     async def __aiter__(self):
# ...         yield ...
# >>> isinstance(Aiterable(), typing.AsyncIterable)
# True

# >>> class Aiterator:
# ...     async def __anext__(self):
# ...         return ...
# >>> isinstance(Aiterator(), typing.AsyncIterator)
# False

# ... so I guess I will have to determine this some other way.


def is_async_iterator(obj: typing.Any) -> bool:
    """Determine if the object is an async iterator or not."""
    return asyncio.iscoroutinefunction(getattr(obj, "__anext__", None))


def is_async_iterable(obj: typing.Any) -> bool:
    """Determine if the object is an async iterable or not."""
    attr = getattr(obj, "__aiter__", None)
    return inspect.isfunction(attr) or inspect.ismethod(attr)


@typing.runtime_checkable
class Future(typing.Protocol[T_contra]):
    """Typed protocol representation of an `asyncio.Future`.

    You should consult the documentation for `asyncio.Future` for usage.
    """

    def result(self) -> T_contra:
        """See `asyncio.Future.result`."""

    def set_result(self, result: T_contra, /) -> None:
        """See `asyncio.Future.set_result`."""

    def set_exception(self, exception: Exception, /) -> None:
        """See `asyncio.Future.set_exception`."""

    def done(self) -> bool:
        """See `asyncio.Future.done`."""

    def cancelled(self) -> bool:
        """See `asyncio.Future.cancelled`."""

    def add_done_callback(
        self, callback: typing.Callable[[Future[T_contra]], None], /, *, context: typing.Optional[contextvars.Context],
    ) -> None:
        """See `asyncio.Future.add_done_callback`."""

    def remove_done_callback(self, callback: typing.Callable[[Future[T_contra]], None], /) -> None:
        """See `asyncio.Future.remove_done_callback`."""

    def cancel(self) -> bool:
        """See `asyncio.Future.cancel`."""

    def exception(self) -> typing.Optional[Exception]:
        """See `asyncio.Future.exception`."""

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """See `asyncio.Future.get_loop`."""

    def __await__(self) -> typing.Generator[T_contra, None, typing.Any]:
        ...


@typing.runtime_checkable
class Task(typing.Protocol[T_contra]):
    """Typed protocol representation of an `asyncio.Task`.

    You should consult the documentation for `asyncio.Task` for usage.
    """

    def result(self) -> T_contra:
        """See`asyncio.Future.result`."""

    def set_result(self, result: T_contra, /) -> None:
        """See `asyncio.Future.set_result`."""

    def set_exception(self, exception: Exception, /) -> None:
        """See `asyncio.Future.set_exception`."""

    def done(self) -> bool:
        """See `asyncio.Future.done`."""

    def cancelled(self) -> bool:
        """See `asyncio.Future.cancelled`."""

    def add_done_callback(
        self, callback: typing.Callable[[Future[T_contra]], None], /, *, context: typing.Optional[contextvars.Context],
    ) -> None:
        """See `asyncio.Future.add_done_callback`."""

    def remove_done_callback(self, callback: typing.Callable[[Future[T_contra]], None], /) -> None:
        """See `asyncio.Future.remove_done_callback`."""

    def cancel(self) -> bool:
        """See `asyncio.Future.cancel`."""

    def exception(self) -> typing.Optional[Exception]:
        """See `asyncio.Future.exception`."""

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """See `asyncio.Future.get_loop`."""

    def get_stack(self, *, limit: typing.Optional[int] = None) -> typing.Sequence[types.FrameType]:
        """See `asyncio.Task.get_stack`."""

    def print_stack(self, *, limit: typing.Optional[int] = None, file: typing.Optional[typing.IO] = None) -> None:
        """See `asyncio.Task.print_stack`."""

    def get_name(self) -> str:
        """See `asyncio.Task.get_name`."""

    def set_name(self, value: str, /) -> None:
        """See `asyncio.Task.set_name`."""

    def __await__(self) -> typing.Generator[T_contra, None, typing.Any]:
        ...
