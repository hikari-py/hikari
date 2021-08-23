# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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

__all__: typing.List[str] = [
    "completed_future",
    "get_or_make_loop",
    "is_async_iterator",
    "is_async_iterable",
    "first_completed",
    "all_of",
]

import asyncio
import inspect
import typing

if typing.TYPE_CHECKING:
    # typing_extensions is a dependency of mypy, and pyright vendors it.
    from typing_extensions import TypeGuard

T_co = typing.TypeVar("T_co", covariant=True)
T_inv = typing.TypeVar("T_inv")


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

    Raises
    ------
    RuntimeError
        When called in an environment with no running event loop.
    """
    future = asyncio.get_running_loop().create_future()
    future.set_result(result)
    return future


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


def is_async_iterator(obj: typing.Any) -> TypeGuard[typing.AsyncIterator[object]]:
    """Determine if the object is an async iterator or not."""
    return asyncio.iscoroutinefunction(getattr(obj, "__anext__", None))


def is_async_iterable(obj: typing.Any) -> TypeGuard[typing.AsyncIterable[object]]:
    """Determine if the object is an async iterable or not."""
    attr = getattr(obj, "__aiter__", None)
    return inspect.isfunction(attr) or inspect.ismethod(attr)


async def first_completed(
    *aws: typing.Awaitable[typing.Any],
    timeout: typing.Optional[float] = None,
) -> None:
    """Wait for the first awaitable to complete.

    The awaitables that don't complete first will be cancelled.

    Completion is defined as having a result or an exception set. Thus,
    cancelling any of the awaitables will also result in the others being
    cancelled.

    If the first awaitable raises an exception, then that exception will be
    propagated.

    Parameters
    ----------
    *aws : typing.Awaitable[typing.Any]
        Awaitables to wait for.
    timeout : typing.Optional[float]
        Optional timeout to wait for, or `builtins.None` to not use one.
        If the timeout is reached, all awaitables are cancelled immediately.

    !!! note
        If more than one awaitable is completed before entering this call, then
        the first future is always returned.
    """
    fs = list(map(asyncio.ensure_future, aws))
    iterator = asyncio.as_completed(fs, timeout=timeout)
    try:
        await next(iterator)
    except asyncio.CancelledError:
        raise asyncio.CancelledError("first_completed gatherer cancelled") from None
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError("first_completed gatherer timed out") from None
    finally:
        for f in fs:
            if not f.done() and not f.cancelled():
                f.cancel()
                # Asyncio gathering futures complain if not awaited after cancellation
                try:
                    await f
                except asyncio.CancelledError:
                    pass


async def all_of(
    *aws: typing.Awaitable[T_co],
    timeout: typing.Optional[float] = None,
) -> typing.Sequence[T_co]:
    """Await the completion of all the given awaitable items.

    If any fail or time out, then they are all cancelled.

    Parameters
    ----------
    *aws : typing.Awaitable[T_co]
        Awaitables to wait for.
    timeout : typing.Optional[float]
        Optional timeout to wait for, or `builtins.None` to not use one.
        If the timeout is reached, all awaitables are cancelled immediately.

    Returns
    -------
    typing.Sequence[T_co]
        The results of each awaitable in the order they were provided invoked
        in.
    """
    fs = list(map(asyncio.ensure_future, aws))
    gatherer = asyncio.gather(*fs)

    try:
        return await asyncio.wait_for(gatherer, timeout=timeout)
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError("all_of gatherer timed out") from None
    except asyncio.CancelledError:
        raise asyncio.CancelledError("all_of gatherer cancelled") from None
    finally:
        for f in fs:
            if not f.done() and not f.cancelled():
                f.cancel()
                # Asyncio gathering futures complain if not awaited after cancellation
                try:
                    await f
                except asyncio.CancelledError:
                    pass

        gatherer.cancel()
        try:
            # coverage.py will complain that this is not fully covered, as the
            # "except" block will always be hit. This is intentional.
            await gatherer  # pragma: no cover
        except asyncio.CancelledError:
            pass


def get_or_make_loop() -> asyncio.AbstractEventLoop:
    """Get the current usable event loop or create a new one.

    Returns
    -------
    asyncio.AbstractEventLoop
    """
    # get_event_loop will error under oddly specific cases such as if set_event_loop has been called before even
    # if it was just called with None or if it's called on a thread which isn't the main Thread.
    try:
        loop = asyncio.get_event_loop_policy().get_event_loop()

        # Closed loops cannot be re-used.
        if not loop.is_closed():
            return loop

    except RuntimeError:
        pass

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop
