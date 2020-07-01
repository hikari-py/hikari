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
"""Special endpoint implementations.

You should never need to make any of these objects manually.
"""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["TypingIndicator", "GuildBuilder"]

import asyncio
import contextlib
import datetime
import typing

import attr

from hikari.api import special_endpoints
from hikari.impl import routes
from hikari.utilities import data_binding
from hikari.utilities import date
from hikari.utilities import iterators
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import types

    from hikari.api import rest_app
    from hikari.models import applications
    from hikari.models import audit_logs
    from hikari.models import channels
    from hikari.models import colors
    from hikari.models import guilds
    from hikari.models import messages
    from hikari.models import permissions as permissions_
    from hikari.models import users
    from hikari.utilities import snowflake


@typing.final
class TypingIndicator(special_endpoints.TypingIndicator):
    """Result type of `hiarki.net.rest.trigger_typing`.

    This is an object that can either be awaited like a coroutine to trigger
    the typing indicator once, or an async context manager to keep triggering
    the typing indicator repeatedly until the context finishes.
    """

    __slots__: typing.Sequence[str] = ("_channel", "_request_call", "_task")

    def __init__(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
    ) -> None:
        self._channel = channel
        self._request_call = request_call
        self._task: typing.Optional[asyncio.Task[None]] = None

    def __await__(self) -> typing.Generator[None, typing.Any, None]:
        route = routes.POST_CHANNEL_TYPING.compile(channel=self._channel)
        yield from self._request_call(route).__await__()

    async def __aenter__(self) -> None:
        if self._task is not None:
            raise TypeError("cannot enter a typing indicator context more than once.")
        self._task = asyncio.create_task(self._keep_typing(), name=f"repeatedly trigger typing in {self._channel}")

    async def __aexit__(self, ex_t: typing.Type[Exception], ex_v: Exception, exc_tb: types.TracebackType) -> None:
        # This will always be true, but this keeps MyPy quiet.
        if self._task is not None:
            self._task.cancel()
            # Prevent reusing this object by not setting it back to None.
            self._task = NotImplemented

    async def _keep_typing(self) -> None:
        with contextlib.suppress(asyncio.CancelledError):
            while True:
                # Use slightly less than 10s to ensure latency does not
                # cause the typing indicator to stop showing for a split
                # second if the request is slow to execute.
                await asyncio.gather(self, asyncio.sleep(9))


@attr.s(auto_attribs=True, kw_only=True, slots=True)
class GuildBuilder(special_endpoints.GuildBuilder):
    """A helper class used to construct a prototype for a guild.

    This is used to create a guild in a tidy way using the HTTP API, since
    the logic behind creating a guild on an API level is somewhat confusing
    and detailed.
    """

    # Required arguments.
    _app: rest_app.IRESTApp
    _name: str

    # Optional args that we kept hidden.
    _channels: typing.MutableSequence[data_binding.JSONObject] = attr.ib(factory=list)
    _counter: int = 0
    _request_call: typing.Callable[
        ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
    ]
    _roles: typing.MutableSequence[data_binding.JSONObject] = attr.ib(factory=list)

    @property
    def name(self) -> str:
        return self._name

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

        if self.icon is not undefined.UNDEFINED:
            async with self.icon.stream(executor=self._app.executor) as stream:
                data_uri = await stream.data_uri()
                payload.put("icon", data_uri)

        raw_response = await self._request_call(route, body=payload)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._app.entity_factory.deserialize_guild(response)

    def add_role(
        self,
        name: str,
        /,
        *,
        color: typing.Union[undefined.UndefinedType, colors.Color] = undefined.UNDEFINED,
        colour: typing.Union[undefined.UndefinedType, colors.Color] = undefined.UNDEFINED,
        hoisted: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        mentionable: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        permissions: typing.Union[undefined.UndefinedType, permissions_.Permission] = undefined.UNDEFINED,
        position: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
    ) -> snowflake.Snowflake:
        if len(self._roles) == 0 and name != "@everyone":
            raise ValueError("First role must always be the @everyone role")

        if not undefined.count(color, colour):
            raise TypeError("Cannot specify 'color' and 'colour' together.")

        snowflake_id = self._new_snowflake()
        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("id", snowflake_id)
        payload.put("name", name)
        payload.put("color", color)
        payload.put("color", colour)
        payload.put("hoisted", hoisted)
        payload.put("mentionable", mentionable)
        payload.put("permissions", permissions)
        payload.put("position", position)
        self._roles.append(payload)
        return snowflake_id

    def add_category(
        self,
        name: str,
        /,
        *,
        position: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        permission_overwrites: typing.Union[
            undefined.UndefinedType, typing.Collection[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        nsfw: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
    ) -> snowflake.Snowflake:
        snowflake_id = self._new_snowflake()
        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("id", snowflake_id)
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
        return snowflake_id

    def add_text_channel(
        self,
        name: str,
        /,
        *,
        parent_id: typing.Union[undefined.UndefinedType, snowflake.Snowflake] = undefined.UNDEFINED,
        topic: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        rate_limit_per_user: typing.Union[undefined.UndefinedType, date.TimeSpan] = undefined.UNDEFINED,
        position: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        permission_overwrites: typing.Union[
            undefined.UndefinedType, typing.Collection[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        nsfw: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
    ) -> snowflake.Snowflake:
        snowflake_id = self._new_snowflake()
        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("id", snowflake_id)
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
        return snowflake_id

    def add_voice_channel(
        self,
        name: str,
        /,
        *,
        parent_id: typing.Union[undefined.UndefinedType, snowflake.Snowflake] = undefined.UNDEFINED,
        bitrate: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        position: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        permission_overwrites: typing.Union[
            undefined.UndefinedType, typing.Collection[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        nsfw: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        user_limit: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
    ) -> snowflake.Snowflake:
        snowflake_id = self._new_snowflake()
        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("id", snowflake_id)
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
        return snowflake_id

    def _new_snowflake(self) -> snowflake.Snowflake:
        value = self._counter
        self._counter += 1
        return snowflake.Snowflake.from_data(datetime.datetime.now(tz=datetime.timezone.utc), 0, 0, value,)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class MessageIterator(iterators.BufferedLazyIterator["messages.Message"]):
    """Implementation of an iterator for message history."""

    __slots__: typing.Sequence[str] = ("_app", "_request_call", "_direction", "_first_id", "_route")

    def __init__(
        self,
        app: rest_app.IRESTApp,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        channel_id: str,
        direction: str,
        first_id: typing.Union[str, undefined.UndefinedType],
    ) -> None:
        super().__init__()
        self._app = app
        self._request_call = request_call
        self._direction = direction
        self._first_id = first_id
        self._route = routes.GET_CHANNEL_MESSAGES.compile(channel=channel_id)

    async def _next_chunk(self) -> typing.Optional[typing.Generator[messages.Message, typing.Any, None]]:
        query = data_binding.StringMapBuilder()
        query.put(self._direction, self._first_id)
        query.put("limit", 100)

        raw_chunk = await self._request_call(compiled_route=self._route, query=query)
        chunk = typing.cast(data_binding.JSONArray, raw_chunk)

        if not chunk:
            return None
        if self._direction == "after":
            chunk.reverse()

        self._first_id = chunk[-1]["id"]
        return (self._app.entity_factory.deserialize_message(m) for m in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class ReactorIterator(iterators.BufferedLazyIterator["users.User"]):
    """Implementation of an iterator for message reactions."""

    __slots__: typing.Sequence[str] = ("_app", "_first_id", "_route", "_request_call")

    def __init__(
        self,
        app: rest_app.IRESTApp,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        channel_id: str,
        message_id: str,
        emoji: str,
    ) -> None:
        super().__init__()
        self._app = app
        self._request_call = request_call
        self._first_id = undefined.UNDEFINED
        self._route = routes.GET_REACTIONS.compile(channel=channel_id, message=message_id, emoji=emoji)

    async def _next_chunk(self) -> typing.Optional[typing.Generator[users.User, typing.Any, None]]:
        query = data_binding.StringMapBuilder()
        query.put("after", self._first_id)
        query.put("limit", 100)

        raw_chunk = await self._request_call(compiled_route=self._route, query=query)
        chunk = typing.cast(data_binding.JSONArray, raw_chunk)

        if not chunk:
            return None

        self._first_id = chunk[-1]["id"]
        return (self._app.entity_factory.deserialize_user(u) for u in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class OwnGuildIterator(iterators.BufferedLazyIterator["applications.OwnGuild"]):
    """Implementation of an iterator for retrieving guilds you are in."""

    __slots__: typing.Sequence[str] = ("_app", "_request_call", "_route", "_newest_first", "_first_id")

    def __init__(
        self,
        app: rest_app.IRESTApp,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
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
        query = data_binding.StringMapBuilder()
        query.put("before" if self._newest_first else "after", self._first_id)
        query.put("limit", 100)

        raw_chunk = await self._request_call(compiled_route=self._route, query=query)
        chunk = typing.cast(data_binding.JSONArray, raw_chunk)

        if not chunk:
            return None

        self._first_id = chunk[-1]["id"]
        return (self._app.entity_factory.deserialize_own_guild(g) for g in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class MemberIterator(iterators.BufferedLazyIterator["guilds.Member"]):
    """Implementation of an iterator for retrieving members in a guild."""

    __slots__: typing.Sequence[str] = ("_app", "_request_call", "_route", "_first_id")

    def __init__(
        self,
        app: rest_app.IRESTApp,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        guild_id: str,
    ) -> None:
        super().__init__()
        self._route = routes.GET_GUILD_MEMBERS.compile(guild=guild_id)
        self._request_call = request_call
        self._app = app
        # This starts at the default provided by discord instead of the max snowflake
        # because that caused discord to take about 2 seconds more to return the first response.
        self._first_id = undefined.UNDEFINED

    async def _next_chunk(self) -> typing.Optional[typing.Generator[guilds.Member, typing.Any, None]]:
        query = data_binding.StringMapBuilder()
        query.put("after", self._first_id)
        query.put("limit", 100)

        raw_chunk = await self._request_call(compiled_route=self._route, query=query)
        chunk = typing.cast(data_binding.JSONArray, raw_chunk)

        if not chunk:
            return None

        # noinspection PyTypeChecker
        self._first_id = chunk[-1]["user"]["id"]

        return (self._app.entity_factory.deserialize_member(m) for m in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class AuditLogIterator(iterators.LazyIterator["audit_logs.AuditLog"]):
    """Iterator implementation for an audit log."""

    def __init__(
        self,
        app: rest_app.IRESTApp,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        guild_id: str,
        before: typing.Union[str, undefined.UndefinedType],
        user_id: typing.Union[str, undefined.UndefinedType],
        action_type: typing.Union[int, undefined.UndefinedType],
    ) -> None:
        self._action_type = action_type
        self._app = app
        self._first_id = before
        self._request_call = request_call
        self._route = routes.GET_GUILD_AUDIT_LOGS.compile(guild=guild_id)
        self._user_id = user_id

    async def __anext__(self) -> audit_logs.AuditLog:
        query = data_binding.StringMapBuilder()
        query.put("limit", 100)
        query.put("user_id", self._user_id)
        query.put("event_type", self._action_type)
        query.put("before", self._first_id)

        raw_response = await self._request_call(compiled_route=self._route, query=query)
        response = typing.cast(data_binding.JSONObject, raw_response)

        if not response["entries"]:
            raise StopAsyncIteration

        log = self._app.entity_factory.deserialize_audit_log(response)
        self._first_id = str(min(log.entries.keys()))
        return log
