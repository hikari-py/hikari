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

__all__ = ["completed_future", "wait", "is_async_iterator", "is_async_iterable"]

import asyncio
import inspect
import typing

if typing.TYPE_CHECKING:
    from hikari.internal import more_typing

    _T_contra = typing.TypeVar("_T_contra", contravariant=True)


def completed_future(result: _T_contra = None, /) -> more_typing.Future[_T_contra]:
    """Create a future on the current running loop that is completed, then return it.

    Parameters
    ----------
    result : typing.Any
        The value to set for the result of the future.

    Returns
    -------
    asyncio.Future
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
    return inspect.isfunction(obj.__aiter__) or inspect.ismethod(getattr(obj, "__aiter__", None))
