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

You should never need to refer to this documentation directly.
"""
from __future__ import annotations

# Do not document anything in here.
__all__ = []

import asyncio
import contextlib
import types
import typing

from hikari import pagination
from hikari.internal import conversions
from hikari.models import applications
from hikari.models import bases
from hikari.models import channels
from hikari.models import messages
from hikari.models import users
from hikari.net import routes

if typing.TYPE_CHECKING:
    from hikari import base_app
    from hikari.internal import more_typing


class MessagePaginator(pagination.BufferedLazyIterator[messages.Message]):
    __slots__ = ("_app", "_request_call", "_direction", "_first_id", "_route")

    def __init__(
        self,
        app: base_app.IBaseApp,
        request_call: typing.Callable[..., more_typing.Coroutine[more_typing.JSONArray]],
        channel_id: str,
        direction: str,
        first_id: str,
    ) -> None:
        super().__init__()
        self._app = app
        self._request_call = request_call
        self._direction = direction
        self._first_id = first_id
        self._route = routes.GET_CHANNEL_MESSAGES.compile(channel=channel_id)

    async def _next_chunk(self) -> typing.Optional[typing.Generator[messages.Message, typing.Any, None]]:
        chunk = await self._request_call(self._route, query={self._direction: self._first_id, "limit": 100})

        if not chunk:
            return None
        if self._direction == "after":
            chunk.reverse()

        self._first_id = chunk[-1]["id"]
        return (self._app.entity_factory.deserialize_message(m) for m in chunk)


class ReactorPaginator(pagination.BufferedLazyIterator[users.User]):
    __slots__ = ("_app", "_first_id", "_route", "_request_call")

    def __init__(
        self,
        app: base_app.IBaseApp,
        request_call: typing.Callable[..., more_typing.Coroutine[more_typing.JSONArray]],
        channel_id: str,
        message_id: str,
        emoji: str,
    ) -> None:
        super().__init__()
        self._app = app
        self._request_call = request_call
        self._first_id = bases.Snowflake.min()
        self._route = routes.GET_REACTIONS.compile(channel_id=channel_id, message_id=message_id, emoji=emoji)

    async def _next_chunk(self) -> typing.Optional[typing.Generator[users.User, typing.Any, None]]:
        chunk = await self._request_call(self._route, query={"after": self._first_id, "limit": 100})

        if not chunk:
            return None

        self._first_id = chunk[-1]["id"]
        return (self._app.entity_factory.deserialize_user(u) for u in chunk)


class OwnGuildPaginator(pagination.BufferedLazyIterator[applications.OwnGuild]):
    __slots__ = ("_app", "_request_call", "_route", "_newest_first", "_first_id")

    def __init__(
        self,
        app: base_app.IBaseApp,
        request_call: typing.Callable[..., more_typing.Coroutine[more_typing.JSONArray]],
        newest_first: bool,
        first_id: str,
    ) -> None:
        super().__init__()
        self._app = app
        self._newest_first = newest_first
        self._request_call = request_call
        self._first_id = first_id
        self._route = routes.GET_MY_GUILDS.compile()

    async def _next_chunk(self) -> typing.Optional[typing.Generator[applications.OwnGuild, typing.Any, None]]:
        kwargs = {"before" if self._newest_first else "after": self._first_id, "limit": 100}

        chunk = await self._request_call(self._route, query=kwargs)

        if not chunk:
            return None

        self._first_id = chunk[-1]["id"]
        return (self._app.entity_factory.deserialize_own_guild(g) for g in chunk)


class TypingIndicator:
    __slots__ = ("_channel", "_request_call", "_task")

    def __init__(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObjectT],
        request_call: typing.Callable[..., more_typing.Coroutine[more_typing.JSONObject]],
    ) -> None:
        self._channel = conversions.cast_to_str_id(channel)
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
