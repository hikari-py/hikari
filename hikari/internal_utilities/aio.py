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
import functools
import asyncio

import typing

from hikari.internal_utilities import compat


ReturnT = typing.TypeVar("ReturnT")


def optional_await(
    description: str = None,
    shield: bool = False
) -> typing.Callable[
     [typing.Callable[..., typing.Coroutine[typing.Any, typing.Any, ReturnT]]],
     typing.Callable[..., typing.Awaitable[ReturnT]]
]:
    """
    Optional await decorator factory for async functions so that they can be called without await and
    scheduled on the event loop lazily.

    Args:
        description:
            the optional name to give the dispatched task.
        shield:
            defaults to False. If `True`, the coroutine will be wrapped in a :function:`asyncio.shield`
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
            return compat.asyncio.create_task(coro, name=description)

        return wrapper

    return decorator


class PartialCoroutineProtocolT(compat.typing.Protocol[ReturnT]):
    """Represents the type of a :class:`functools.partial` wrapping an :mod:`asyncio` coroutine."""

    def __call__(self) -> typing.Coroutine[None, None, ReturnT]:
        ...


__all__ = ["optional_await", "PartialCoroutineProtocolT"]
