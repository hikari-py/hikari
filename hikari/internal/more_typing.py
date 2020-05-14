#!/usr/bin/env python3
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
"""Various reusable type-hints for this library."""
# pylint:disable=unused-variable

from __future__ import annotations

__all__ = [
    "JSONType",
    "NullableJSONArray",
    "JSONObject",
    "NullableJSONObject",
    "JSONArray",
    "NullableJSONType",
    "Headers",
    "Coroutine",
    "Future",
    "Task",
]

# Hide any imports; this encourages any uses of this to use the typing module
# for regular stuff rather than relying on it being in here as well.
# pylint: disable=ungrouped-imports
from typing import Any as _Any
from typing import AnyStr as _AnyStr
from typing import Coroutine as _Coroutine
from typing import Mapping as _Mapping
from typing import Optional as _Optional
from typing import Protocol as _Protocol
from typing import runtime_checkable as runtime_checkable
from typing import Sequence as _Sequence
from typing import TYPE_CHECKING as _TYPE_CHECKING
from typing import TypeVar as _TypeVar
from typing import Union as _Union

if _TYPE_CHECKING:
    from types import FrameType as _FrameType
    from typing import Callable as _Callable
    from typing import IO as _IO
    import asyncio
    import contextvars
# pylint: enable=ungrouped-imports

T_contra = _TypeVar("T_contra", contravariant=True)
# noinspection PyShadowingBuiltins
T_co = _TypeVar("T_co", covariant=True)

##########################
# HTTP TYPE HINT HELPERS #
##########################

JSONType = _Union[
    _Mapping[str, "NullableJSONType"], _Sequence["NullableJSONType"], _AnyStr, int, float, bool,
]
"""Any JSON type."""

NullableJSONType = _Optional[JSONType]
"""Any JSON type, including `null`."""

JSONObject = _Mapping[str, NullableJSONType]
"""A mapping produced from a JSON object."""

NullableJSONObject = _Optional[JSONObject]
"""A mapping produced from a JSON object that may or may not be present."""

JSONArray = _Sequence[NullableJSONType]
"""A sequence produced from a JSON array."""

NullableJSONArray = _Optional[JSONArray]
"""A sequence produced from a JSON array that may or may not be present."""

Headers = _Mapping[str, _Union[_Sequence[str], str]]
"""HTTP headers."""

#############################
# ASYNCIO TYPE HINT HELPERS #
#############################

Coroutine = _Coroutine[_Any, _Any, T_co]
"""A coroutine object.

This is awaitable but MUST be awaited somewhere to be completed correctly.
"""


@runtime_checkable
class Future(_Protocol[T_contra]):
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
        self, callback: _Callable[[Future[T_contra]], None], /, *, context: _Optional[contextvars.Context],
    ) -> None:
        """See `asyncio.Future.add_done_callback`."""

    def remove_done_callback(self, callback: _Callable[[Future[T_contra]], None], /) -> None:
        """See `asyncio.Future.remove_done_callback`."""

    def cancel(self) -> bool:
        """See `asyncio.Future.cancel`."""

    def exception(self) -> _Optional[Exception]:
        """See `asyncio.Future.exception`."""

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """See `asyncio.Future.get_loop`."""

    def __await__(self) -> Coroutine[T_contra]:
        ...


@runtime_checkable
class Task(_Protocol[T_contra]):
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
        self, callback: _Callable[[Future[T_contra]], None], /, *, context: _Optional[contextvars.Context],
    ) -> None:
        """See `asyncio.Future.add_done_callback`."""

    def remove_done_callback(self, callback: _Callable[[Future[T_contra]], None], /) -> None:
        """See `asyncio.Future.remove_done_callback`."""

    def cancel(self) -> bool:
        """See `asyncio.Future.cancel`."""

    def exception(self) -> _Optional[Exception]:
        """See `asyncio.Future.exception`."""

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """See `asyncio.Future.get_loop`."""

    def get_stack(self, *, limit: _Optional[int] = None) -> _Sequence[_FrameType]:
        """See `asyncio.Task.get_stack`."""

    def print_stack(self, *, limit: _Optional[int] = None, file: _Optional[_IO] = None) -> None:
        """See `asyncio.Task.print_stack`."""

    def get_name(self) -> str:
        """See `asyncio.Task.get_name`."""

    def set_name(self, value: str, /) -> None:
        """See `asyncio.Task.set_name`."""

    def __await__(self) -> Coroutine[T_contra]:
        ...


# pylint:enable=unused-variable
