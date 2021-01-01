# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Special endpoint implementations.

You should never need to make any of these objects manually.
"""
from __future__ import annotations

__all__: typing.List[str] = ["TypingIndicator", "GuildBuilder"]

import asyncio
import contextlib
import datetime
import typing

import attr

from hikari import channels
from hikari import errors
from hikari import files
from hikari import iterators
from hikari import snowflakes
from hikari import undefined
from hikari.api import special_endpoints
from hikari.internal import attr_extensions
from hikari.internal import data_binding
from hikari.internal import routes
from hikari.internal import time

if typing.TYPE_CHECKING:
    import concurrent.futures
    import types

    from hikari import applications
    from hikari import audit_logs
    from hikari import colors
    from hikari import guilds
    from hikari import messages
    from hikari import permissions as permissions_
    from hikari import users
    from hikari.api import entity_factory as entity_factory_


@typing.final
class TypingIndicator(special_endpoints.TypingIndicator):
    """Result type of `hikari.api.rest.RESTClient.trigger_typing`.

    This is an object that can either be awaited like a coroutine to trigger
    the typing indicator once, or an async context manager to keep triggering
    the typing indicator repeatedly until the context finishes.

    !!! note
        This is a helper class that is used by `hikari.api.rest.RESTClient`.
        You should only ever need to use instances of this class that are
        produced by that API.
    """

    __slots__: typing.Sequence[str] = ("_route", "_request_call", "_task", "_rest_close_event", "_task_name")

    def __init__(
        self,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        rest_closed_event: asyncio.Event,
    ) -> None:
        self._route = routes.POST_CHANNEL_TYPING.compile(channel=channel)
        self._request_call = request_call
        self._task_name = f"repeatedly trigger typing in {channel}"
        self._task: typing.Optional[asyncio.Task[None]] = None
        self._rest_close_event = rest_closed_event

    def __await__(self) -> typing.Generator[typing.Any, typing.Any, typing.Any]:
        return self._request_call(self._route).__await__()

    async def __aenter__(self) -> None:
        if self._task is not None:
            raise TypeError("cannot enter a typing indicator context more than once.")
        self._task = asyncio.create_task(self._keep_typing(), name=self._task_name)

    async def __aexit__(
        self,
        exception_type: typing.Type[BaseException],
        exception: BaseException,
        exception_traceback: types.TracebackType,
    ) -> None:
        # This will always be true, but this keeps MyPy quiet.
        if self._task is not None:
            self._task.cancel()

    def __enter__(self) -> typing.NoReturn:
        # This is async only.
        cls = type(self)
        raise TypeError(f"{cls.__module__}.{cls.__qualname__} is async-only, did you mean 'async with'?") from None

    def __exit__(self, exc_type: typing.Type[Exception], exc_val: Exception, exc_tb: types.TracebackType) -> None:
        return None

    async def _keep_typing(self) -> None:
        # Cancelled error will occur when the context manager is requested to
        # stop.
        with contextlib.suppress(asyncio.CancelledError, errors.HTTPClientClosedError):
            # If the REST API closes while typing, just stop.
            while not self._rest_close_event.is_set():
                # Use slightly less than 10s to ensure latency does not
                # cause the typing indicator to stop showing for a split
                # second if the request is slow to execute.
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.gather(self, asyncio.wait_for(self._rest_close_event.wait(), timeout=9.0))


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class GuildBuilder(special_endpoints.GuildBuilder):
    """Result type of `hikari.api.rest.RESTClient.guild_builder`.

    This is used to create a guild in a tidy way using the HTTP API, since
    the logic behind creating a guild on an API level is somewhat confusing
    and detailed.

    !!! note
        This is a helper class that is used by `hikari.api.rest.RESTClient`.
        You should only ever need to use instances of this class that are
        produced by that API, thus, any details about the constructor are
        omitted from the following examples for brevity.

    Examples
    --------
    Creating an empty guild.

    ```py
    guild = await rest.guild_builder("My Server!").create()
    ```

    Creating a guild with an icon

    ```py
    from hikari.files import WebResourceStream

    guild_builder = rest.guild_builder("My Server!")
    guild_builder.icon = WebResourceStream("cat.png", "http://...")
    guild = await guild_builder.create()
    ```

    Adding roles to your guild.

    ```py
    from hikari.permissions import Permissions

    guild_builder = rest.guild_builder("My Server!")

    everyone_role_id = guild_builder.add_role("@everyone")
    admin_role_id = guild_builder.add_role("Admins", permissions=Permissions.ADMINISTRATOR)

    await guild_builder.create()
    ```

    !!! warning
        The first role must always be the `@everyone` role.

    !!! note
        If you call `add_role`, the default roles provided by discord will
        be created. This also applies to the `add_` functions for
        text channels/voice channels/categories.

    !!! note
        Functions that return a `hikari.snowflakes.Snowflake` do
        **not** provide the final ID that the object will have once the
        API call is made. The returned IDs are only able to be used to
        re-reference particular objects while building the guild format.

        This is provided to allow creation of channels within categories,
        and to provide permission overwrites.

    Adding a text channel to your guild.

    ```py
    guild_builder = rest.guild_builder("My Server!")

    category_id = guild_builder.add_category("My safe place")
    channel_id = guild_builder.add_text_channel("general", parent_id=category_id)

    await guild_builder.create()
    ```
    """

    # Required arguments.
    _entity_factory: entity_factory_.EntityFactory = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    _executor: typing.Optional[concurrent.futures.Executor] = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    _name: str = attr.ib()

    # Optional args that we kept hidden.
    _channels: typing.MutableSequence[data_binding.JSONObject] = attr.ib(factory=list, init=False)
    _counter: int = attr.ib(default=0, init=False)
    _request_call: typing.Callable[
        ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
    ] = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    _roles: typing.MutableSequence[data_binding.JSONObject] = attr.ib(factory=list, init=False)

    @property
    def name(self) -> str:
        return self._name

    async def create(self) -> guilds.RESTGuild:
        route = routes.POST_GUILDS.compile()
        payload = data_binding.JSONObjectBuilder()
        payload.put("name", self.name)
        payload.put_array("roles", self._roles if self._roles else undefined.UNDEFINED)
        payload.put_array("channels", self._channels if self._channels else undefined.UNDEFINED)
        payload.put("region", self.region)
        payload.put("verification_level", self.verification_level)
        payload.put("default_message_notifications", self.default_message_notifications)
        payload.put("explicit_content_filter", self.explicit_content_filter_level)

        if self.icon is not undefined.UNDEFINED:
            icon = files.ensure_resource(self.icon)

            async with icon.stream(executor=self._executor) as stream:
                data_uri = await stream.data_uri()
                payload.put("icon", data_uri)

        raw_response = await self._request_call(route, json=payload)
        response = typing.cast(data_binding.JSONObject, raw_response)
        return self._entity_factory.deserialize_rest_guild(response)

    def add_role(
        self,
        name: str,
        /,
        *,
        color: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        colour: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        hoist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentionable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        permissions: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> snowflakes.Snowflake:
        if not undefined.count(color, colour):
            raise TypeError("Cannot specify 'color' and 'colour' together.")

        if len(self._roles) == 0:
            if name != "@everyone":
                raise ValueError("First role must always be the '@everyone' role")
            if undefined.count(color, colour, hoist, mentionable, position) != 5:
                raise ValueError(
                    "Cannot pass 'color', 'colour', 'hoist', 'mentionable' nor 'position' to the '@everyone' role."
                )

        snowflake_id = self._new_snowflake()
        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("id", snowflake_id)
        payload.put("name", name)
        payload.put("color", color)
        payload.put("color", colour)
        payload.put("hoist", hoist)
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
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Collection[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> snowflakes.Snowflake:
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
            conversion=self._entity_factory.serialize_permission_overwrite,
        )

        self._channels.append(payload)
        return snowflake_id

    def add_text_channel(
        self,
        name: str,
        /,
        *,
        parent_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Collection[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> snowflakes.Snowflake:
        snowflake_id = self._new_snowflake()
        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("id", snowflake_id)
        payload.put("name", name)
        payload.put("type", channels.ChannelType.GUILD_TEXT)
        payload.put("topic", topic)
        payload.put("rate_limit_per_user", rate_limit_per_user, conversion=time.timespan_to_int)
        payload.put("position", position)
        payload.put("nsfw", nsfw)
        payload.put_snowflake("parent_id", parent_id)

        payload.put_array(
            "permission_overwrites",
            permission_overwrites,
            conversion=self._entity_factory.serialize_permission_overwrite,
        )

        self._channels.append(payload)
        return snowflake_id

    def add_voice_channel(
        self,
        name: str,
        /,
        *,
        parent_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Collection[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> snowflakes.Snowflake:
        snowflake_id = self._new_snowflake()
        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("id", snowflake_id)
        payload.put("name", name)
        payload.put("type", channels.ChannelType.GUILD_VOICE)
        payload.put("bitrate", bitrate)
        payload.put("position", position)
        payload.put("user_limit", user_limit)
        payload.put_snowflake("parent_id", parent_id)

        payload.put_array(
            "permission_overwrites",
            permission_overwrites,
            conversion=self._entity_factory.serialize_permission_overwrite,
        )

        self._channels.append(payload)
        return snowflake_id

    def _new_snowflake(self) -> snowflakes.Snowflake:
        value = self._counter
        self._counter += 1
        return snowflakes.Snowflake.from_data(
            datetime.datetime.now(tz=datetime.timezone.utc),
            0,
            0,
            value,
        )


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class MessageIterator(iterators.BufferedLazyIterator["messages.Message"]):
    """Implementation of an iterator for message history."""

    __slots__: typing.Sequence[str] = ("_entity_factory", "_request_call", "_direction", "_first_id", "_route")

    def __init__(
        self,
        entity_factory: entity_factory_.EntityFactory,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        direction: str,
        first_id: undefined.UndefinedOr[str],
    ) -> None:
        super().__init__()
        self._entity_factory = entity_factory
        self._request_call = request_call
        self._direction = direction
        self._first_id = first_id
        self._route = routes.GET_CHANNEL_MESSAGES.compile(channel=channel)

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
        return (self._entity_factory.deserialize_message(m) for m in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class ReactorIterator(iterators.BufferedLazyIterator["users.User"]):
    """Implementation of an iterator for message reactions."""

    __slots__: typing.Sequence[str] = ("_entity_factory", "_first_id", "_route", "_request_call")

    def __init__(
        self,
        entity_factory: entity_factory_.EntityFactory,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        channel: snowflakes.SnowflakeishOr[channels.TextChannel],
        message: snowflakes.SnowflakeishOr[messages.PartialMessage],
        emoji: str,
    ) -> None:
        super().__init__()
        self._entity_factory = entity_factory
        self._request_call = request_call
        self._first_id = undefined.UNDEFINED
        self._route = routes.GET_REACTIONS.compile(channel=channel, message=message, emoji=emoji)

    async def _next_chunk(self) -> typing.Optional[typing.Generator[users.User, typing.Any, None]]:
        query = data_binding.StringMapBuilder()
        query.put("after", self._first_id)
        query.put("limit", 100)

        raw_chunk = await self._request_call(compiled_route=self._route, query=query)
        chunk = typing.cast(data_binding.JSONArray, raw_chunk)

        if not chunk:
            return None

        self._first_id = chunk[-1]["id"]
        return (self._entity_factory.deserialize_user(u) for u in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class OwnGuildIterator(iterators.BufferedLazyIterator["applications.OwnGuild"]):
    """Implementation of an iterator for retrieving guilds you are in."""

    __slots__: typing.Sequence[str] = ("_entity_factory", "_request_call", "_route", "_newest_first", "_first_id")

    def __init__(
        self,
        entity_factory: entity_factory_.EntityFactory,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        newest_first: bool,
        first_id: str,
    ) -> None:
        super().__init__()
        self._entity_factory = entity_factory
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
        return (self._entity_factory.deserialize_own_guild(g) for g in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class MemberIterator(iterators.BufferedLazyIterator["guilds.Member"]):
    """Implementation of an iterator for retrieving members in a guild."""

    __slots__: typing.Sequence[str] = ("_entity_factory", "_guild_id", "_request_call", "_route", "_first_id")

    def __init__(
        self,
        entity_factory: entity_factory_.EntityFactory,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> None:
        super().__init__()
        self._guild_id = snowflakes.Snowflake(str(int(guild)))
        self._route = routes.GET_GUILD_MEMBERS.compile(guild=guild)
        self._request_call = request_call
        self._entity_factory = entity_factory
        # This starts at the default provided by discord instead of the max snowflake
        # because that caused discord to take about 2 seconds more to return the first response.
        self._first_id = undefined.UNDEFINED

    async def _next_chunk(self) -> typing.Optional[typing.Generator[guilds.Member, typing.Any, None]]:
        query = data_binding.StringMapBuilder()
        query.put("after", self._first_id)
        query.put("limit", 1000)

        raw_chunk = await self._request_call(compiled_route=self._route, query=query)
        chunk = typing.cast(data_binding.JSONArray, raw_chunk)

        if not chunk:
            return None

        self._first_id = chunk[-1]["user"]["id"]

        return (self._entity_factory.deserialize_member(m, guild_id=self._guild_id) for m in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class AuditLogIterator(iterators.LazyIterator["audit_logs.AuditLog"]):
    """Iterator implementation for an audit log."""

    __slots__: typing.Sequence[str] = (
        "_entity_factory",
        "_action_type",
        "_request_call",
        "_route",
        "_first_id",
        "_user",
    )

    def __init__(
        self,
        entity_factory: entity_factory_.EntityFactory,
        request_call: typing.Callable[
            ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
        ],
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        before: undefined.UndefinedOr[str],
        user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]],
        action_type: undefined.UndefinedOr[int],
    ) -> None:
        self._action_type = action_type
        self._entity_factory = entity_factory
        self._first_id = before
        self._request_call = request_call
        self._route = routes.GET_GUILD_AUDIT_LOGS.compile(guild=guild)
        self._user = user

    async def __anext__(self) -> audit_logs.AuditLog:
        query = data_binding.StringMapBuilder()
        query.put("limit", 100)
        query.put("user_id", self._user)
        query.put("event_type", self._action_type)
        query.put("before", self._first_id)

        raw_response = await self._request_call(compiled_route=self._route, query=query)
        response = typing.cast(data_binding.JSONObject, raw_response)

        if not response["audit_log_entries"]:
            raise StopAsyncIteration

        log = self._entity_factory.deserialize_audit_log(response)
        self._first_id = str(min(log.entries.keys()))
        return log
