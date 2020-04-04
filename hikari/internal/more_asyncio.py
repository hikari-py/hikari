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

__all__ = ["Future", "Task", "completed_future"]

import asyncio
import contextvars
import typing

T = typing.TypeVar("T")
T_co = typing.TypeVar("T_co")

try:
    raise Exception
except Exception as ex:  # pylint:disable=broad-except
    tb = ex.__traceback__
    StackFrameType = type(tb.tb_frame)


# pylint:disable=unused-variable
@typing.runtime_checkable
class Future(typing.Protocol[T]):
    """Typed protocol representation of an :obj:`asyncio.Future`.

    You should consult the documentation for :obj:`asyncio.Future` for usage.
    """

    def result(self) -> T:
        """See :meth:`asyncio.Future.result`."""

    def set_result(self, result: T, /) -> None:
        """See :meth:`asyncio.Future.set_result`."""

    def set_exception(self, exception: Exception, /) -> None:
        """See :meth:`asyncio.Future.set_exception`."""

    def done(self) -> bool:
        """See :meth:`asyncio.Future.done`."""

    def cancelled(self) -> bool:
        """See :meth:`asyncio.Future.cancelled`."""

    def add_done_callback(
        self, callback: typing.Callable[[Future[T]], None], /, *, context: typing.Optional[contextvars.Context],
    ) -> None:
        """See :meth:`asyncio.Future.add_done_callback`."""

    def remove_done_callback(self, callback: typing.Callable[[Future[T]], None], /) -> None:
        """See :meth:`asyncio.Future.remove_done_callback`."""

    def cancel(self) -> bool:
        """See :meth:`asyncio.Future.cancel`."""

    def exception(self) -> typing.Optional[Exception]:
        """See :meth:`asyncio.Future.exception`."""

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """See :meth:`asyncio.Future.get_loop`."""

    def __await__(self) -> typing.Coroutine[None, None, T]:
        ...


# pylint:enable=unused-variable


# pylint:disable=unused-variable
class Task(Future[T]):
    """Typed protocol representation of an :obj:`asyncio.Task`.

    You should consult the documentation for :obj:`asyncio.Task` for usage.
    """

    def get_stack(self, *, limit: typing.Optional[int] = None) -> typing.Sequence[StackFrameType]:
        """See :meth:`asyncio.Task.get_stack`."""

    def print_stack(self, *, limit: typing.Optional[int] = None, file: typing.Optional[typing.IO] = None) -> None:
        """See :meth:`asyncio.Task.print_stack`."""

    def get_name(self) -> str:
        """See :meth:`asyncio.Task.get_name`."""

    def set_name(self, value: str, /) -> None:
        """See :meth:`asyncio.Task.set_name`."""


# pylint:enable=unused-variable


@typing.overload
def completed_future() -> Future[None]:
    """Return a completed future with no result."""


@typing.overload
def completed_future(result: T, /) -> Future[T]:
    """Return a completed future with the given value as the result."""


def completed_future(result=None, /):
    """Create a future on the current running loop that is completed, then return it.

    Parameters
    ----------
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
