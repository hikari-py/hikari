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
import types
import typing

import attr

from hikari import rest_app
from hikari.internal import conversions
from hikari.models import bases
from hikari.models import colors
from hikari.models import files
from hikari.models import guilds
from hikari.models import permissions as permissions_
from hikari.models import unset
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


class DummyID(int):
    __slots__ = ()


@attr.s(auto_attribs=True, kw_only=True, slots=True)
class GuildBuilder:
    _app: rest_app.IRESTApp
    _channels: typing.MutableSequence[more_typing.JSONObject] = attr.ib(factory=list)
    _counter: int = 0
    _name: typing.Union[unset.Unset, str]
    _request_call: typing.Callable[..., more_typing.Coroutine[more_typing.JSONObject]]
    _roles: typing.MutableSequence[more_typing.JSONObject] = attr.ib(factory=list)
    default_message_notifications: typing.Union[unset.Unset, guilds.GuildMessageNotificationsLevel] = unset.UNSET
    explicit_content_filter_level: typing.Union[unset.Unset, guilds.GuildExplicitContentFilterLevel] = unset.UNSET
    icon: typing.Union[unset.Unset, files.BaseStream] = unset.UNSET
    region: typing.Union[unset.Unset, str] = unset.UNSET
    verification_level: typing.Union[unset.Unset, guilds.GuildVerificationLevel] = unset.UNSET

    @property
    def name(self) -> str:
        # Read-only!
        return self._name

    def __await__(self) -> typing.Generator[guilds.Guild, None, typing.Any]:
        yield from self.create().__await__()

    async def create(self) -> guilds.Guild:
        route = routes.POST_GUILDS.compile()
        payload = {
            "name": self.name,
            "icon": None if unset.is_unset(self.icon) else await self.icon.read(),
            "roles": self._roles,
            "channels": self._channels,
        }
        conversions.put_if_specified(payload, "region", self.region)
        conversions.put_if_specified(payload, "verification_level", self.verification_level)
        conversions.put_if_specified(payload, "default_message_notifications", self.default_message_notifications)
        conversions.put_if_specified(payload, "explicit_content_filter", self.explicit_content_filter_level)

        response = await self._request_call(route, body=payload)
        return self._app.entity_factory.deserialize_guild(response)

    def add_role(
        self,
        name: str,
        /,
        *,
        color: typing.Union[unset.Unset, colors.Color] = unset.UNSET,
        colour: typing.Union[unset.Unset, colors.Color] = unset.UNSET,
        hoisted: typing.Union[unset.Unset, bool] = unset.UNSET,
        mentionable: typing.Union[unset.Unset, bool] = unset.UNSET,
        permissions: typing.Union[unset.Unset, permissions_.Permission] = unset.UNSET,
        position: typing.Union[unset.Unset, int] = unset.UNSET,
    ) -> bases.Snowflake:
        snowflake = self._new_snowflake()
        payload = {"id": str(snowflake), "name": name}
        conversions.put_if_specified(payload, "color", color)
        conversions.put_if_specified(payload, "color", colour)
        conversions.put_if_specified(payload, "hoisted", hoisted)
        conversions.put_if_specified(payload, "mentionable", mentionable)
        conversions.put_if_specified(payload, "permissions", permissions)
        conversions.put_if_specified(payload, "position", position)
        self._roles.append(payload)
        return snowflake

    def add_category(
        self,
        name: str,
        /,
        *,
        position: typing.Union[unset.Unset, int] = unset.UNSET,
        permission_overwrites: typing.Union[unset.Unset, typing.Collection[channels.PermissionOverwrite]] = unset.UNSET,
        nsfw: typing.Union[unset.Unset, bool] = unset.UNSET,
    ) -> bases.Snowflake:
        snowflake = self._new_snowflake()
        payload = {"id": str(snowflake), "type": channels.ChannelType.GUILD_CATEGORY, "name": name}
        conversions.put_if_specified(payload, "position", position)
        conversions.put_if_specified(payload, "nsfw", nsfw)

        if not unset.is_unset(permission_overwrites):
            overwrites = [self._app.entity_factory.serialize_permission_overwrite(o) for o in permission_overwrites]
            payload["permission_overwrites"] = overwrites

        self._channels.append(payload)
        return snowflake

    def add_text_channel(
        self,
        name: str,
        /,
        *,
        parent_id: bases.Snowflake = unset.UNSET,
        topic: typing.Union[unset.Unset, str] = unset.UNSET,
        rate_limit_per_user: typing.Union[unset.Unset, more_typing.TimeSpanT] = unset.UNSET,
        position: typing.Union[unset.Unset, int] = unset.UNSET,
        permission_overwrites: typing.Union[unset.Unset, typing.Collection[channels.PermissionOverwrite]] = unset.UNSET,
        nsfw: typing.Union[unset.Unset, bool] = unset.UNSET,
    ) -> bases.Snowflake:
        snowflake = self._new_snowflake()
        payload = {"id": str(snowflake), "type": channels.ChannelType.GUILD_TEXT, "name": name}
        conversions.put_if_specified(payload, "topic", topic)
        conversions.put_if_specified(payload, "rate_limit_per_user", rate_limit_per_user, conversions.timespan_to_int)
        conversions.put_if_specified(payload, "position", position)
        conversions.put_if_specified(payload, "nsfw", nsfw)
        conversions.put_if_specified(payload, "parent_id", parent_id, str)

        if not unset.is_unset(permission_overwrites):
            overwrites = [self._app.entity_factory.serialize_permission_overwrite(o) for o in permission_overwrites]
            payload["permission_overwrites"] = overwrites

        self._channels.append(payload)
        return snowflake

    def add_voice_channel(
        self,
        name: str,
        /,
        *,
        parent_id: bases.Snowflake = unset.UNSET,
        bitrate: typing.Union[unset.Unset, int] = unset.UNSET,
        position: typing.Union[unset.Unset, int] = unset.UNSET,
        permission_overwrites: typing.Union[unset.Unset, typing.Collection[channels.PermissionOverwrite]] = unset.UNSET,
        nsfw: typing.Union[unset.Unset, bool] = unset.UNSET,
        user_limit: typing.Union[unset.Unset, int] = unset.UNSET,
    ) -> bases.Snowflake:
        snowflake = self._new_snowflake()
        payload = {"id": str(snowflake), "type": channels.ChannelType.GUILD_VOICE, "name": name}
        conversions.put_if_specified(payload, "bitrate", bitrate)
        conversions.put_if_specified(payload, "position", position)
        conversions.put_if_specified(payload, "nsfw", nsfw)
        conversions.put_if_specified(payload, "user_limit", user_limit)
        conversions.put_if_specified(payload, "parent_id", parent_id, str)

        if not unset.is_unset(permission_overwrites):
            overwrites = [self._app.entity_factory.serialize_permission_overwrite(o) for o in permission_overwrites]
            payload["permission_overwrites"] = overwrites

        self._channels.append(payload)
        return snowflake

    def _new_snowflake(self) -> bases.Snowflake:
        value = self._counter
        self._counter += 1
        return bases.Snowflake.from_data(datetime.datetime.now(tz=datetime.timezone.utc), 0, 0, value,)
