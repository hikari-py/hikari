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
"""Internal utilities used by the REST API.

You should never need to make any of these objects manually.
"""
from __future__ import annotations

# Do not document anything in here.
__all__ = []

import asyncio
import contextlib
import types
import typing

from hikari.internal import conversions
from hikari.models import bases
from hikari.net import routes

if typing.TYPE_CHECKING:
    from hikari.internal import more_typing
    from hikari.models import channels


class TypingIndicator:
    """Result type of `hiarki.net.rest.trigger_typing`.

    This is an object that can either be awaited like a coroutine to trigger
    the typing indicator once, or an async context manager to keep triggering
    the typing indicator repeatedly until the context finishes.
    """

    __slots__ = ("_channel", "_request_call", "_task")

    def __init__(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        request_call: typing.Callable[..., more_typing.Coroutine[more_typing.JSONObject]],
    ) -> None:
        self._channel = conversions.value_to_snowflake(channel)
        self._request_call = request_call
        self._task = None

    def __await__(self) -> typing.Generator[None, typing.Any, None]:
        route = routes.POST_CHANNEL_TYPING.compile(channel=self._channel)
        yield from self._request_call(route).__await__()

    async def __aenter__(self) -> None:
        if self._task is not None:
            raise TypeError("cannot enter a typing indicator context more than once.")
        self._task = asyncio.create_task(self._keep_typing(), name=f"repeatedly trigger typing in {self._channel}")

    async def __aexit__(self, ex_t: typing.Type[Exception], ex_v: Exception, exc_tb: types.TracebackType) -> None:
        self._task.cancel()
        # Prevent reusing this object by not setting it back to None.
        self._task = NotImplemented

    async def _keep_typing(self) -> None:
        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(self, asyncio.sleep(9.9), return_exceptions=True)
