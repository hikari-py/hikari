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
"""
Asyncio extensions and utilities.
"""
from __future__ import annotations

import asyncio
import functools
import typing

from hikari.internal_utilities import assertions


ReturnT = typing.TypeVar("ReturnT", covariant=True)
CoroutineFunctionT = typing.Callable[..., typing.Coroutine[typing.Any, typing.Any, ReturnT]]


def optional_await(
    description: str = None, shield: bool = False
) -> typing.Callable[
    [typing.Callable[..., typing.Coroutine[typing.Any, typing.Any, ReturnT]]],
    typing.Callable[..., typing.Awaitable[ReturnT]],
]:
    """
    Optional await decorator factory for async functions so that they can be called without await and
    scheduled on the event loop lazily.

    Args:
        description:
            the optional name to give the dispatched task.
        shield:
            defaults to False. If `True`, the coroutine will be wrapped in a :func:`asyncio.shield`
            to prevent it being cancelled.

    Returns:
        A decorator for a coroutine function.
    """

    def decorator(
        coro_fn: typing.Callable[..., typing.Coroutine[typing.Any, typing.Any, ReturnT]]
    ) -> typing.Callable[..., typing.Awaitable[ReturnT]]:
        @functools.wraps(coro_fn)
        def wrapper(*args, **kwargs) -> typing.Awaitable[ReturnT]:
            coro = asyncio.shield(coro_fn(*args, **kwargs)) if shield else coro_fn(*args, **kwargs)
            return asyncio.create_task(coro, name=description)

        return wrapper

    return decorator


class PartialCoroutineProtocolT(typing.Protocol[ReturnT]):
    """Represents the type of a :class:`functools.partial` wrapping an :mod:`asyncio` coroutine."""

    def __call__(self, *args, **kwargs) -> typing.Coroutine[None, None, ReturnT]:
        ...

    def __await__(self):
        ...


class EventDelegate:
    """
    A multiplexing map. This is essentially an event delegation mapoing that stores callbacks for various events
    that may be triggered, and acts as the mechanism for storing and calling event handlers when they need to be
    invoked.
    """
    def __init__(self) -> None:
        self._muxes = {}

    def add(self, name: str, coroutine_function: CoroutineFunctionT) -> None:
        """
        Register a new event callback to a given event name.

        Args:
            name:
                The name of the event to register to.
            coroutine_function:
                The event callback to invoke when this event is fired.
        """
        assertions.assert_that(
            asyncio.iscoroutinefunction(coroutine_function), "You must subscribe a coroutine function only", TypeError
        )
        if name not in self._muxes:
            self._muxes[name] = []
        self._muxes[name].append(coroutine_function)

    def remove(self, name: str, coroutine_function: CoroutineFunctionT) -> None:
        """
        Remove the given coroutine function from the handlers for the given event. The name is mandatory to enable
        supporting registering the same event callback for multiple event types.

        Args:
            name:
                The event to remove from.
            coroutine_function:
                The event callback to remove.
        """
        if name in self._muxes and coroutine_function in self._muxes[name]:
            if len(self._muxes[name]) - 1 == 0:
                del self._muxes[name]
            else:
                self._muxes[name].remove(coroutine_function)

    def dispatch(self, name: str, *args) -> asyncio.Future:
        """
        Dispatch a given event.

        Args:
            name:
                The name of the event to dispatch.
            *args:
                The parameters to pass to the event callback.

        Returns:
            A future. This may be a gathering future of the callbacks to invoke, or it may be
            a completed future object. Regardless, this result will be scheduled on the event loop
            automatically, and does not need to be awaited. Awaiting this future will await
            completion of all invoked event handlers.
        """
        if name in self._muxes:
            return asyncio.gather(*(callback(*args) for callback in self._muxes[name]))
        return completed_future()


def completed_future(result: typing.Any = None) -> asyncio.Future:
    """
    Create a future on the current running loop that is completed, then return it.

    Args:
        result:
            The value to set for the result of the future.

    Returns:
        The completed future.
    """
    future = asyncio.get_event_loop().create_future()
    future.set_result(result)
    return future


__all__ = ["optional_await", "CoroutineFunctionT", "PartialCoroutineProtocolT", "EventDelegate", "completed_future"]
