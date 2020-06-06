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
import datetime
import typing

import attr

from hikari.net import routes
from hikari.utilities import data_binding
from hikari.utilities import date
from hikari.utilities import snowflake as snowflake_
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import types

    from hikari.api import app as app_
    from hikari.models import bases
    from hikari.models import channels
    from hikari.models import colors
    from hikari.models import files
    from hikari.models import guilds
    from hikari.models import permissions as permissions_


class TypingIndicator:
    """Result type of `hiarki.net.rest.trigger_typing`.

    This is an object that can either be awaited like a coroutine to trigger
    the typing indicator once, or an async context manager to keep triggering
    the typing indicator repeatedly until the context finishes.
    """

    __slots__ = ("_channel", "_request_call", "_task")

    def __init__(
        self,
        channel: typing.Union[channels.TextChannel, bases.UniqueObject],
        request_call: typing.Callable[..., typing.Coroutine[None, typing.Any, data_binding.JSONObject]],
    ) -> None:
        self._channel = channel
        self._request_call = request_call
        self._task = None

    def __await__(self) -> typing.Generator[None, typing.Any, None]:
        route = routes.POST_CHANNEL_TYPING.compile(channel=self._channel)
        yield from self._request_call(route).__await__()

    def __enter__(self) -> typing.NoReturn:
        raise TypeError("Use 'async with' rather than 'with' when triggering the typing indicator.")

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
            while True:
                await asyncio.gather(self, asyncio.sleep(9.9), return_exceptions=True)


@attr.s(auto_attribs=True, kw_only=True, slots=True)
class GuildBuilder:
    _app: app_.IRESTApp
    _channels: typing.MutableSequence[data_binding.JSONObject] = attr.ib(factory=list)
    _counter: int = 0
    _name: typing.Union[undefined.Undefined, str]
    _request_call: typing.Callable[..., typing.Coroutine[None, typing.Any, data_binding.JSONObject]]
    _roles: typing.MutableSequence[data_binding.JSONObject] = attr.ib(factory=list)
    default_message_notifications: typing.Union[
        undefined.Undefined, guilds.GuildMessageNotificationsLevel
    ] = undefined.Undefined()
    explicit_content_filter_level: typing.Union[
        undefined.Undefined, guilds.GuildExplicitContentFilterLevel
    ] = undefined.Undefined()
    icon: typing.Union[undefined.Undefined, files.BaseStream] = undefined.Undefined()
    region: typing.Union[undefined.Undefined, str] = undefined.Undefined()
    verification_level: typing.Union[undefined.Undefined, guilds.GuildVerificationLevel] = undefined.Undefined()

    @property
    def name(self) -> str:
        # Read-only!
        return self._name

    def __await__(self) -> typing.Generator[guilds.Guild, None, typing.Any]:
        yield from self.create().__await__()

    async def create(self) -> guilds.Guild:
        route = routes.POST_GUILDS.compile()
        payload = data_binding.JSONObjectBuilder()
        payload.put("name", self.name)
        payload.put_array("roles", self._roles)
        payload.put_array("channels", self._channels)
        payload.put("region", self.region)
        payload.put("verification_level", self.verification_level)
        payload.put("default_message_notifications", self.default_message_notifications)
        payload.put("explicit_content_filter", self.explicit_content_filter_level)

        if not isinstance(self.icon, undefined.Undefined):
            payload.put("icon", await self.icon.fetch_data_uri())

        response = await self._request_call(route, body=payload)
        return self._app.entity_factory.deserialize_guild(response)

    def add_role(
        self,
        name: str,
        /,
        *,
        color: typing.Union[undefined.Undefined, colors.Color] = undefined.Undefined(),
        colour: typing.Union[undefined.Undefined, colors.Color] = undefined.Undefined(),
        hoisted: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        mentionable: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        permissions: typing.Union[undefined.Undefined, permissions_.Permission] = undefined.Undefined(),
        position: typing.Union[undefined.Undefined, int] = undefined.Undefined(),
    ) -> snowflake_.Snowflake:
        if len(self._roles) == 0 and name != "@everyone":
            raise ValueError("First role must always be the @everyone role")

        if not undefined.Undefined.count(color, colour):
            raise TypeError("Cannot specify 'color' and 'colour' together.")

        snowflake = self._new_snowflake()
        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("id", snowflake)
        payload.put("name", name)
        payload.put("color", color)
        payload.put("color", colour)
        payload.put("hoisted", hoisted)
        payload.put("mentionable", mentionable)
        payload.put("permissions", permissions)
        payload.put("position", position)
        self._roles.append(payload)
        return snowflake

    def add_category(
        self,
        name: str,
        /,
        *,
        position: typing.Union[undefined.Undefined, int] = undefined.Undefined(),
        permission_overwrites: typing.Union[
            undefined.Undefined, typing.Collection[channels.PermissionOverwrite]
        ] = undefined.Undefined(),
        nsfw: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
    ) -> snowflake_.Snowflake:
        snowflake = self._new_snowflake()
        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("id", snowflake)
        payload.put("name", name)
        payload.put("type", channels.ChannelType.GUILD_CATEGORY)
        payload.put("position", position)
        payload.put("nsfw", nsfw)

        payload.put_array(
            "permission_overwrites",
            permission_overwrites,
            conversion=self._app.entity_factory.serialize_permission_overwrite,
        )

        self._channels.append(payload)
        return snowflake

    def add_text_channel(
        self,
        name: str,
        /,
        *,
        parent_id: snowflake_.Snowflake = undefined.Undefined(),
        topic: typing.Union[undefined.Undefined, str] = undefined.Undefined(),
        rate_limit_per_user: typing.Union[undefined.Undefined, date.TimeSpan] = undefined.Undefined(),
        position: typing.Union[undefined.Undefined, int] = undefined.Undefined(),
        permission_overwrites: typing.Union[
            undefined.Undefined, typing.Collection[channels.PermissionOverwrite]
        ] = undefined.Undefined(),
        nsfw: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
    ) -> snowflake_.Snowflake:
        snowflake = self._new_snowflake()
        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("id", snowflake)
        payload.put("name", name)
        payload.put("type", channels.ChannelType.GUILD_TEXT)
        payload.put("topic", topic)
        payload.put("rate_limit_per_user", rate_limit_per_user, conversion=date.timespan_to_int)
        payload.put("position", position)
        payload.put("nsfw", nsfw)
        payload.put_snowflake("parent_id", parent_id)

        payload.put_array(
            "permission_overwrites",
            permission_overwrites,
            conversion=self._app.entity_factory.serialize_permission_overwrite,
        )

        self._channels.append(payload)
        return snowflake

    def add_voice_channel(
        self,
        name: str,
        /,
        *,
        parent_id: snowflake_.Snowflake = undefined.Undefined(),
        bitrate: typing.Union[undefined.Undefined, int] = undefined.Undefined(),
        position: typing.Union[undefined.Undefined, int] = undefined.Undefined(),
        permission_overwrites: typing.Union[
            undefined.Undefined, typing.Collection[channels.PermissionOverwrite]
        ] = undefined.Undefined(),
        nsfw: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        user_limit: typing.Union[undefined.Undefined, int] = undefined.Undefined(),
    ) -> snowflake_.Snowflake:
        snowflake = self._new_snowflake()
        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("id", snowflake)
        payload.put("name", name)
        payload.put("type", channels.ChannelType.GUILD_VOICE)
        payload.put("bitrate", bitrate)
        payload.put("position", position)
        payload.put("nsfw", nsfw)
        payload.put("user_limit", user_limit)
        payload.put_snowflake("parent_id", parent_id)

        payload.put_array(
            "permission_overwrites",
            permission_overwrites,
            conversion=self._app.entity_factory.serialize_permission_overwrite,
        )

        self._channels.append(payload)
        return snowflake

    def _new_snowflake(self) -> snowflake_.Snowflake:
        value = self._counter
        self._counter += 1
        return snowflake_.Snowflake.from_data(datetime.datetime.now(tz=datetime.timezone.utc), 0, 0, value,)
