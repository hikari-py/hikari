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
"""Asyncio extensions and utilities."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "completed_future",
    "is_async_iterator",
    "is_async_iterable",
    "first_completed",
]

import asyncio
import inspect
import logging
import typing

T_co = typing.TypeVar("T_co", covariant=True)
T_inv = typing.TypeVar("T_inv")
U_co = typing.TypeVar("U_co", covariant=True)

_LOGGER: typing.Final[logging.Logger] = logging.getLogger(__name__)


def completed_future(result: typing.Optional[T_inv] = None, /) -> asyncio.Future[typing.Optional[T_inv]]:
    """Create a future on the current running loop that is completed, then return it.

    Parameters
    ----------
    result : T
        The value to set for the result of the future.
        `T` is a generic type placeholder for the type that
        the future will have set as the result. `T` may be `builtins.None`, in
        which case, this will return `asyncio.Future[builtins.None]`.

    Returns
    -------
    asyncio.Future[T]
        The completed future.
    """
    future = asyncio.get_event_loop().create_future()
    future.set_result(result)
    # MyPy pretends this type hint is valid when it is not. Probably should be
    # in the standard lib but whatever.
    return typing.cast("asyncio.Future[typing.Optional[T_inv]]", future)


# On Python3.8.2, there appears to be a bug with the typing module:

# >>> class Aiterable:
# ...     async def __aiter__(self):  # noqa: E800
# ...         yield ...
# >>> isinstance(Aiterable(), typing.AsyncIterable)
# True

# >>> class Aiterator:
# ...     async def __anext__(self):  # noqa: E800
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


async def first_completed(
    f1: asyncio.Future[typing.Any],
    f2: asyncio.Future[typing.Any],
    *fs: asyncio.Future[typing.Any],
    timeout: typing.Optional[float] = None,
) -> None:
    """Wait for the first of two or more futures to complete.

    The futures that don't complete first will be cancelled.

    Completion is defined as having a result or an exception set. Thus,
    cancelling any of the futures will also result in the others being
    cancelled.

    If the first future raises an exception, then that exception will be
    propagated.

    Parameters
    ----------
    f1 : asyncio.Future[typing.Any]
        The first future to wait for.
    f2 : asyncio.Future[typing.Any]
        The second future to wait for.
    *fs : asyncio.Future[typing.Any]
        Additional futures to wait for.
    timeout : typing.Optional[float]
        Optional timeout to wait for, or `builtins.None` to not use one.
        If the timeout is reached, all futures are cancelled immediately.

    !!! note
        If more than one future is completed before entering this call, then
        the first future is always returned.
    """
    iterator = asyncio.as_completed([f1, f2, *fs], timeout=timeout)
    try:
        await next(iterator)
    finally:
        for f in [f1, f2, *fs]:
            if not f.done() and not f.cancelled():
                f.cancel()
                # Asyncio Gathering Futures complain if not awaited after cancellation
                try:
                    await f
                except asyncio.CancelledError:
                    pass
