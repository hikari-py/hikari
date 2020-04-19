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
"""Asyncio extensions and utilities.

|internal|
"""
from __future__ import annotations

__all__ = ["completed_future"]

import asyncio
import typing

from hikari.internal import more_typing


@typing.overload
def completed_future() -> more_typing.Future[None]:
    """Return a completed future with no result."""


@typing.overload
def completed_future(result: more_typing.T_contra, /) -> more_typing.Future[more_typing.T_contra]:
    """Return a completed future with the given value as the result."""


def completed_future(result=None, /):
    """Create a future on the current running loop that is completed, then return it.

    Parameters
    ----------
    result : :obj:`~typing.Any`
        The value to set for the result of the future.

    Returns
    -------
    :obj:`~asyncio.Future`
        The completed future.
    """
    future = asyncio.get_event_loop().create_future()
    future.set_result(result)
    return future


def wait(
    aws: typing.Union[more_typing.Coroutine, typing.Awaitable], *, timeout=None, return_when=asyncio.ALL_COMPLETED
) -> more_typing.Coroutine[typing.Tuple[typing.Set[more_typing.Future], typing.Set[more_typing.Future]]]:
    """Run awaitable objects in the aws set concurrently.

    This blocks until the condition specified by `return_value`.

    Returns
    -------
    :obj:`~typing.Tuple` with two :obj:`~typing.Set` of futures.
        The coroutine returned by :obj:`~asyncio.wait` of two sets of
        Tasks/Futures (done, pending).
    """
    # noinspection PyTypeChecker
    return asyncio.wait([asyncio.ensure_future(f) for f in aws], timeout=timeout, return_when=return_when)
