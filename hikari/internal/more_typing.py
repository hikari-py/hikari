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

# Don't export anything.
__all__ = []

import asyncio
import contextvars

# Hide any imports; this encourages any uses of this to use the typing module
# for regular stuff rather than relying on it being in here as well.
from types import FrameType as _FrameType
from typing import Any as _Any
from typing import AnyStr as _AnyStr
from typing import Callable as _Callable
from typing import Coroutine as _Coroutine
from typing import IO as _IO
from typing import Mapping as _Mapping
from typing import Optional as _Optional
from typing import Protocol as _Protocol
from typing import runtime_checkable as _runtime_checkable
from typing import Sequence as _Sequence
from typing import TypeVar as _TypeVar
from typing import Union as _Union

T_contra = _TypeVar("T_contra", contravariant=True)
# noinspection PyShadowingBuiltins
T_co = _TypeVar("T_co", covariant=True)

##########################
# HTTP TYPE HINT HELPERS #
##########################

#: Any JSON type.
JSONType = _Union[
    _Mapping[str, "NullableJSONType"], _Sequence["NullableJSONType"], _AnyStr, int, float, bool,
]

#: Any JSON type, including ``null``.
NullableJSONType = _Optional[JSONType]

#: A mapping produced from a JSON object.
JSONObject = _Mapping[str, NullableJSONType]

#: A mapping produced from a JSON object that may or may not be present.
NullableJSONObject = _Optional[JSONObject]

#: A sequence produced from a JSON array.
JSONArray = _Sequence[NullableJSONType]

#: A sequence produced from a JSON array that may or may not be present.
NullableJSONArray = _Optional[JSONArray]

#: HTTP headers.
Headers = _Mapping[str, _Union[_Sequence[str], str]]

#############################
# ASYNCIO TYPE HINT HELPERS #
#############################

#: A coroutine object.
#:
#: This is awaitable but MUST be awaited somewhere to be
#: completed correctly.
Coroutine = _Coroutine[_Any, _Any, T_co]


@_runtime_checkable
class Future(_Protocol[T_contra]):
    """Typed protocol representation of an :obj:`~asyncio.Future`.

    You should consult the documentation for :obj:`~asyncio.Future` for usage.
    """

    def result(self) -> T_contra:
        """See :meth:`asyncio.Future.result`."""

    def set_result(self, result: T_contra, /) -> None:
        """See :meth:`asyncio.Future.set_result`."""

    def set_exception(self, exception: Exception, /) -> None:
        """See :meth:`asyncio.Future.set_exception`."""

    def done(self) -> bool:
        """See :meth:`asyncio.Future.done`."""

    def cancelled(self) -> bool:
        """See :meth:`asyncio.Future.cancelled`."""

    def add_done_callback(
        self, callback: _Callable[[Future[T_contra]], None], /, *, context: _Optional[contextvars.Context],
    ) -> None:
        """See :meth:`asyncio.Future.add_done_callback`."""

    def remove_done_callback(self, callback: _Callable[[Future[T_contra]], None], /) -> None:
        """See :meth:`asyncio.Future.remove_done_callback`."""

    def cancel(self) -> bool:
        """See :meth:`asyncio.Future.cancel`."""

    def exception(self) -> _Optional[Exception]:
        """See :meth:`asyncio.Future.exception`."""

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """See :meth:`asyncio.Future.get_loop`."""

    def __await__(self) -> Coroutine[T_contra]:
        ...


@_runtime_checkable
class Task(_Protocol[T_contra]):
    """Typed protocol representation of an :obj:`~asyncio.Task`.

    You should consult the documentation for :obj:`~asyncio.Task` for usage.
    """

    def result(self) -> T_contra:
        """See :meth:`asyncio.Future.result`."""

    def set_result(self, result: T_contra, /) -> None:
        """See :meth:`asyncio.Future.set_result`."""

    def set_exception(self, exception: Exception, /) -> None:
        """See :meth:`asyncio.Future.set_exception`."""

    def done(self) -> bool:
        """See :meth:`asyncio.Future.done`."""

    def cancelled(self) -> bool:
        """See :meth:`asyncio.Future.cancelled`."""

    def add_done_callback(
        self, callback: _Callable[[Future[T_contra]], None], /, *, context: _Optional[contextvars.Context],
    ) -> None:
        """See :meth:`asyncio.Future.add_done_callback`."""

    def remove_done_callback(self, callback: _Callable[[Future[T_contra]], None], /) -> None:
        """See :meth:`asyncio.Future.remove_done_callback`."""

    def cancel(self) -> bool:
        """See :meth:`asyncio.Future.cancel`."""

    def exception(self) -> _Optional[Exception]:
        """See :meth:`asyncio.Future.exception`."""

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """See :meth:`asyncio.Future.get_loop`."""

    def get_stack(self, *, limit: _Optional[int] = None) -> _Sequence[_FrameType]:
        """See :meth:`asyncio.Task.get_stack`."""

    def print_stack(self, *, limit: _Optional[int] = None, file: _Optional[_IO] = None) -> None:
        """See :meth:`asyncio.Task.print_stack`."""

    def get_name(self) -> str:
        """See :meth:`asyncio.Task.get_name`."""

    def set_name(self, value: str, /) -> None:
        """See :meth:`asyncio.Task.set_name`."""

    def __await__(self) -> Coroutine[T_contra]:
        ...


# pylint:enable=unused-variable
