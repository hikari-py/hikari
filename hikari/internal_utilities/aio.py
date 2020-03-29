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
__all__ = [
    "CoroutineFunctionT",
    "PartialCoroutineProtocolT",
    "completed_future",
]

import asyncio
import typing

ReturnT = typing.TypeVar("ReturnT", covariant=True)
CoroutineFunctionT = typing.Callable[..., typing.Coroutine[typing.Any, typing.Any, ReturnT]]


class PartialCoroutineProtocolT(typing.Protocol[ReturnT]):
    """Represents the type of a :obj:`functools.partial` wrapping an :mod:`asyncio` coroutine."""

    def __call__(self, *args, **kwargs) -> typing.Coroutine[None, None, ReturnT]:
        ...

    def __await__(self):
        ...


def completed_future(result: typing.Any = None) -> asyncio.Future:
    """Create a future on the current running loop that is completed, then return it.

    Parameters
    ---------
    result : :obj:`typing.Any`
        The value to set for the result of the future.

    Returns
    -------
    :obj:`asyncio.Future`
        The completed future.
    """
    future = asyncio.get_event_loop().create_future()
    future.set_result(result)
    return future
