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

CoroutineFunctionT = typing.Callable[..., typing.Coroutine[typing.Any, typing.Any, typing.Any]]
ReturnT = typing.TypeVar("ReturnT", covariant=True)


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

    def __call__(self) -> typing.Coroutine[None, None, ReturnT]:
        ...

    def __await__(self):
        ...


class MuxMap:
    def __init__(self):
        self._muxes = {}

    def add(self, name: str, coroutine_function: CoroutineFunctionT) -> None:
        assertions.assert_that(
            asyncio.iscoroutinefunction(coroutine_function), "You must subscribe a coroutine function only", TypeError
        )
        if name not in self._muxes:
            self._muxes[name] = []
        self._muxes[name].append(coroutine_function)

    def remove(self, name: str, coroutine_function: CoroutineFunctionT) -> None:
        if name in self._muxes and coroutine_function in self._muxes[name]:
            if len(self._muxes[name]) - 1 == 0:
                del self._muxes[name]
            else:
                self._muxes[name].remove(coroutine_function)

    def dispatch(self, name: str, *args) -> asyncio.Future:
        if name in self._muxes:
            return asyncio.gather(*(callback(*args) for callback in self._muxes[name]))


__all__ = ["optional_await", "CoroutineFunctionT", "PartialCoroutineProtocolT", "MuxMap"]
