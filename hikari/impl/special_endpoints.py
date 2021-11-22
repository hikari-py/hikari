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

__all__: typing.List[str] = [
    "ActionRowBuilder",
    "CommandBuilder",
    "TypingIndicator",
    "GuildBuilder",
    "InteractionDeferredBuilder",
    "InteractionMessageBuilder",
    "InteractiveButtonBuilder",
    "LinkButtonBuilder",
    "SelectMenuBuilder",
]

import asyncio
import typing

import attr

from hikari import channels
from hikari import commands
from hikari import emojis
from hikari import errors
from hikari import files
from hikari import iterators
from hikari import messages
from hikari import snowflakes
from hikari import undefined
from hikari.api import special_endpoints
from hikari.interactions import base_interactions
from hikari.internal import attr_extensions
from hikari.internal import data_binding
from hikari.internal import mentions
from hikari.internal import routes
from hikari.internal import time

if typing.TYPE_CHECKING:
    import concurrent.futures
    import types

    from hikari import applications
    from hikari import audit_logs
    from hikari import colors
    from hikari import embeds as embeds_
    from hikari import guilds
    from hikari import permissions as permissions_
    from hikari import users
    from hikari import voices
    from hikari.api import entity_factory as entity_factory_

    _T = typing.TypeVar("_T")
    _CommandBuilderT = typing.TypeVar("_CommandBuilderT", bound="CommandBuilder")
    _InteractionMessageBuilderT = typing.TypeVar("_InteractionMessageBuilderT", bound="InteractionMessageBuilder")
    _InteractionDeferredBuilderT = typing.TypeVar("_InteractionDeferredBuilderT", bound="InteractionDeferredBuilder")
    _ActionRowBuilderT = typing.TypeVar("_ActionRowBuilderT", bound="ActionRowBuilder")
    _ButtonBuilderT = typing.TypeVar("_ButtonBuilderT", bound="_ButtonBuilder[typing.Any]")
    _SelectOptionBuilderT = typing.TypeVar("_SelectOptionBuilderT", bound="_SelectOptionBuilder[typing.Any]")
    _SelectMenuBuilderT = typing.TypeVar("_SelectMenuBuilderT", bound="SelectMenuBuilder[typing.Any]")

    # Hack around used to avoid recursive generic types leading to type checker issues in builders
    class _ContainerProto(typing.Protocol):
        def add_component(self: _T, component: special_endpoints.ComponentBuilder, /) -> _T:
            raise NotImplementedError


_ContainerProtoT = typing.TypeVar("_ContainerProtoT", bound="_ContainerProto")


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
        channel: snowflakes.SnowflakeishOr[channels.TextableChannel],
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
            raise TypeError("Cannot enter a typing indicator context more than once")
        self._task = asyncio.create_task(self._keep_typing(), name=self._task_name)

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        # This will always be true, but this keeps MyPy quiet.
        if self._task is not None:
            self._task.cancel()

    # These are only included at runtime in-order to avoid the model being typed as a synchronous context manager.
    if not typing.TYPE_CHECKING:

        def __enter__(self) -> typing.NoReturn:
            # This is async only.
            cls = type(self)
            raise TypeError(f"{cls.__module__}.{cls.__qualname__} is async-only, did you mean 'async with'?") from None

        def __exit__(
            self,
            exc_type: typing.Optional[typing.Type[Exception]],
            exc_val: typing.Optional[Exception],
            exc_tb: typing.Optional[types.TracebackType],
        ) -> None:
            return None

    async def _keep_typing(self) -> None:
        # Cancelled error will occur when the context manager is requested to
        # stop.
        try:
            # If the REST API closes while typing, just stop.
            while not self._rest_close_event.is_set():
                # Use slightly less than 10s to ensure latency does not
                # cause the typing indicator to stop showing for a split
                # second if the request is slow to execute.
                try:
                    await asyncio.gather(self, asyncio.wait_for(self._rest_close_event.wait(), timeout=9.0))
                except asyncio.TimeoutError:
                    pass

        except (asyncio.CancelledError, errors.ComponentStateConflictError):
            pass


# As a note, slotting allows us to override the settable properties while staying within the interface's spec.
@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
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
    _entity_factory: entity_factory_.EntityFactory = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    _executor: typing.Optional[concurrent.futures.Executor] = attr.field(
        metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    _name: str = attr.field()
    _request_call: typing.Callable[
        ..., typing.Coroutine[None, None, typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]]
    ] = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})

    # Optional arguments.
    default_message_notifications: undefined.UndefinedOr[guilds.GuildMessageNotificationsLevel] = attr.field(
        default=undefined.UNDEFINED
    )
    explicit_content_filter_level: undefined.UndefinedOr[guilds.GuildExplicitContentFilterLevel] = attr.field(
        default=undefined.UNDEFINED
    )
    icon: undefined.UndefinedOr[files.Resourceish] = attr.field(default=undefined.UNDEFINED)
    verification_level: undefined.UndefinedOr[typing.Union[guilds.GuildVerificationLevel, int]] = attr.field(
        default=undefined.UNDEFINED
    )

    # Non-arguments
    _channels: typing.MutableSequence[data_binding.JSONObject] = attr.field(factory=list, init=False)
    _counter: int = attr.field(default=0, init=False)
    _roles: typing.MutableSequence[data_binding.JSONObject] = attr.field(factory=list, init=False)

    @property
    def name(self) -> str:
        return self._name

    async def create(self) -> guilds.RESTGuild:
        route = routes.POST_GUILDS.compile()
        payload = data_binding.JSONObjectBuilder()
        payload.put("name", self.name)
        payload.put_array("roles", self._roles if self._roles else undefined.UNDEFINED)
        payload.put_array("channels", self._channels if self._channels else undefined.UNDEFINED)
        payload.put("verification_level", self.verification_level)
        payload.put("default_message_notifications", self.default_message_notifications)
        payload.put("explicit_content_filter", self.explicit_content_filter_level)

        if self.icon is not undefined.UNDEFINED:
            icon = files.ensure_resource(self.icon)

            async with icon.stream(executor=self._executor) as stream:
                data_uri = await stream.data_uri()
                payload.put("icon", data_uri)

        response = await self._request_call(route, json=payload)
        assert isinstance(response, dict)
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
        if not undefined.any_undefined(color, colour):
            raise TypeError("Cannot specify 'color' and 'colour' together.")

        if len(self._roles) == 0:
            if name != "@everyone":
                raise ValueError("First role must always be the '@everyone' role")
            if not undefined.all_undefined(color, colour, hoist, mentionable, position):
                raise ValueError(
                    "Cannot pass 'color', 'colour', 'hoist', 'mentionable' nor 'position' to the '@everyone' role."
                )

        snowflake_id = self._new_snowflake()
        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("id", snowflake_id)
        payload.put("name", name)
        payload.put("color", color, conversion=colors.Color.of)
        payload.put("color", colour, conversion=colors.Color.of)
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
        video_quality_mode: undefined.UndefinedOr[typing.Union[channels.VideoQualityMode, int]] = undefined.UNDEFINED,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Collection[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        region: undefined.UndefinedNoneOr[typing.Union[voices.VoiceRegion, str]],
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> snowflakes.Snowflake:
        snowflake_id = self._new_snowflake()
        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("id", snowflake_id)
        payload.put("name", name)
        payload.put("type", channels.ChannelType.GUILD_VOICE)
        payload.put("video_quality_mode", video_quality_mode)
        payload.put("bitrate", bitrate)
        payload.put("position", position)
        payload.put("user_limit", user_limit)
        payload.put_snowflake("parent_id", parent_id)
        payload.put("rtc_region", region, conversion=str)

        payload.put_array(
            "permission_overwrites",
            permission_overwrites,
            conversion=self._entity_factory.serialize_permission_overwrite,
        )

        self._channels.append(payload)
        return snowflake_id

    def add_stage_channel(
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
        region: undefined.UndefinedNoneOr[typing.Union[voices.VoiceRegion, str]],
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> snowflakes.Snowflake:
        snowflake_id = self._new_snowflake()
        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("id", snowflake_id)
        payload.put("name", name)
        payload.put("type", channels.ChannelType.GUILD_STAGE)
        payload.put("bitrate", bitrate)
        payload.put("position", position)
        payload.put("user_limit", user_limit)
        payload.put_snowflake("parent_id", parent_id)
        payload.put("rtc_region", region, conversion=str)

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
        return snowflakes.Snowflake.from_data(time.utc_datetime(), 0, 0, value)


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
        channel: snowflakes.SnowflakeishOr[channels.TextableChannel],
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

        chunk = await self._request_call(compiled_route=self._route, query=query)
        assert isinstance(chunk, list)

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
        channel: snowflakes.SnowflakeishOr[channels.TextableChannel],
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

        chunk = await self._request_call(compiled_route=self._route, query=query)
        assert isinstance(chunk, list)

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
        # We rely on Discord's default for the limit here since for this endpoint this has always scaled
        # along side the maximum page size limit to match the maximum amount of guilds a user can be in.

        chunk = await self._request_call(compiled_route=self._route, query=query)
        assert isinstance(chunk, list)

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

        chunk = await self._request_call(compiled_route=self._route, query=query)
        assert isinstance(chunk, list)

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
        action_type: undefined.UndefinedOr[typing.Union["audit_logs.AuditLogEventType", int]],
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
        query.put("action_type", self._action_type, conversion=int)
        query.put("before", self._first_id)

        response = await self._request_call(compiled_route=self._route, query=query)
        assert isinstance(response, dict)

        audit_log_entries = response["audit_log_entries"]
        if not audit_log_entries:
            raise StopAsyncIteration

        log = self._entity_factory.deserialize_audit_log(response)
        # Since deserialize_audit_log may skip entries it doesn't recognise,
        # first_id has to be calculated based on the raw payload as log.entries
        # may be missing entries.
        self._first_id = str(min(entry["id"] for entry in audit_log_entries))
        return log


@attr_extensions.with_copy
@attr.define(kw_only=False, weakref_slot=False)
class InteractionDeferredBuilder(special_endpoints.InteractionDeferredBuilder):
    """Standard implementation of `hikari.api.special_endpoints.InteractionDeferredBuilder`.

    Parameters
    ----------
    type : hikari.interactions.base_interactions.DeferredResponseTypesT
        The type of interaction response this is.
    """

    # Required arguments.
    _type: base_interactions.DeferredResponseTypesT = attr.field(
        converter=base_interactions.ResponseType,
        validator=attr.validators.in_(base_interactions.DEFERRED_RESPONSE_TYPES),
    )

    _flags: typing.Union[undefined.UndefinedType, int, messages.MessageFlag] = attr.field(
        default=undefined.UNDEFINED, kw_only=True
    )

    @property
    def type(self) -> base_interactions.DeferredResponseTypesT:
        return self._type

    @property
    def flags(self) -> typing.Union[undefined.UndefinedType, int, messages.MessageFlag]:
        return self._flags

    def set_flags(
        self: _InteractionDeferredBuilderT, flags: typing.Union[undefined.UndefinedType, int, messages.MessageFlag], /
    ) -> _InteractionDeferredBuilderT:
        self._flags = flags
        return self

    def build(self, _: entity_factory_.EntityFactory, /) -> data_binding.JSONObject:
        if self._flags is not undefined.UNDEFINED:
            return {"type": self._type, "data": {"flags": self._flags}}

        return {"type": self._type}


@attr_extensions.with_copy
@attr.define(kw_only=False, weakref_slot=False)
class InteractionMessageBuilder(special_endpoints.InteractionMessageBuilder):
    """Standard implementation of `hikari.api.special_endpoints.InteractionMessageBuilder`.

    Parameters
    ----------
    type : hikari.interactions.base_interactions.MessageResponseTypesT
        The type of interaction response this is.

    Other Parameters
    ----------------
    content : hikari.undefined.UndefinedOr[builtins.str]
        The content of this response, if supplied. This follows the same rules
        as "content" on create message.
    """

    # Required arguments.
    _type: base_interactions.MessageResponseTypesT = attr.field(
        converter=base_interactions.ResponseType,
        validator=attr.validators.in_(base_interactions.MESSAGE_RESPONSE_TYPES),
    )

    # Not-required arguments.
    _content: undefined.UndefinedOr[str] = attr.field(default=undefined.UNDEFINED)

    # Key-word only not-required arguments.
    _flags: typing.Union[int, messages.MessageFlag, undefined.UndefinedType] = attr.field(
        default=undefined.UNDEFINED, kw_only=True
    )
    _is_tts: undefined.UndefinedOr[bool] = attr.field(default=undefined.UNDEFINED, kw_only=True)
    _mentions_everyone: undefined.UndefinedOr[bool] = attr.field(default=undefined.UNDEFINED, kw_only=True)
    _role_mentions: undefined.UndefinedOr[
        typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
    ] = attr.field(default=undefined.UNDEFINED, kw_only=True)
    _user_mentions: undefined.UndefinedOr[
        typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
    ] = attr.field(default=undefined.UNDEFINED, kw_only=True)
    _components: typing.List[special_endpoints.ComponentBuilder] = attr.field(factory=list, kw_only=True)
    _embeds: typing.List[embeds_.Embed] = attr.field(factory=list, kw_only=True)

    @property
    def content(self) -> undefined.UndefinedOr[str]:
        return self._content

    @property
    def components(self) -> typing.Sequence[special_endpoints.ComponentBuilder]:
        return self._components.copy()

    @property
    def embeds(self) -> typing.Sequence[embeds_.Embed]:
        return self._embeds.copy()

    @property
    def flags(self) -> typing.Union[undefined.UndefinedType, int, messages.MessageFlag]:
        return self._flags

    @property
    def is_tts(self) -> undefined.UndefinedOr[bool]:
        return self._is_tts

    @property
    def mentions_everyone(self) -> undefined.UndefinedOr[bool]:
        return self._mentions_everyone

    @property
    def role_mentions(
        self,
    ) -> undefined.UndefinedOr[typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]]:
        return self._role_mentions

    @property
    def type(self) -> base_interactions.MessageResponseTypesT:
        return self._type

    @property
    def user_mentions(
        self,
    ) -> undefined.UndefinedOr[typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]]:
        return self._user_mentions

    def add_component(
        self: _InteractionMessageBuilderT, component: special_endpoints.ComponentBuilder, /
    ) -> _InteractionMessageBuilderT:
        self._components.append(component)
        return self

    def add_embed(self: _InteractionMessageBuilderT, embed: embeds_.Embed, /) -> _InteractionMessageBuilderT:
        self._embeds.append(embed)
        return self

    def set_content(
        self: _InteractionMessageBuilderT, content: undefined.UndefinedOr[str], /
    ) -> _InteractionMessageBuilderT:
        self._content = str(content) if content is not undefined.UNDEFINED else undefined.UNDEFINED
        return self

    def set_flags(
        self: _InteractionMessageBuilderT, flags: typing.Union[undefined.UndefinedType, int, messages.MessageFlag], /
    ) -> _InteractionMessageBuilderT:
        self._flags = flags
        return self

    def set_tts(self: _InteractionMessageBuilderT, tts: undefined.UndefinedOr[bool], /) -> _InteractionMessageBuilderT:
        self._is_tts = tts
        return self

    def set_mentions_everyone(
        self: _InteractionMessageBuilderT, state: undefined.UndefinedOr[bool] = undefined.UNDEFINED, /
    ) -> _InteractionMessageBuilderT:
        self._mentions_everyone = state
        return self

    def set_role_mentions(
        self: _InteractionMessageBuilderT,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
        /,
    ) -> _InteractionMessageBuilderT:
        self._role_mentions = role_mentions
        return self

    def set_user_mentions(
        self: _InteractionMessageBuilderT,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        /,
    ) -> _InteractionMessageBuilderT:
        self._user_mentions = user_mentions
        return self

    def build(self, entity_factory: entity_factory_.EntityFactory, /) -> data_binding.JSONObject:
        data = data_binding.JSONObjectBuilder()
        data.put("content", self.content)
        if self._embeds:
            embeds: typing.List[data_binding.JSONObject] = []
            for embed, attachments in map(entity_factory.serialize_embed, self._embeds):
                if attachments:
                    raise ValueError("Cannot send an embed with attachments in a slash command's initial response")

                embeds.append(embed)

            data["embeds"] = embeds

        data.put_array("components", self._components, conversion=lambda component: component.build())
        data.put("flags", self.flags)
        data.put("tts", self.is_tts)

        if not undefined.all_undefined(self.mentions_everyone, self.user_mentions, self.role_mentions):
            data["allowed_mentions"] = mentions.generate_allowed_mentions(
                self.mentions_everyone, undefined.UNDEFINED, self.user_mentions, self.role_mentions
            )

        return {"type": self._type, "data": data}


@attr_extensions.with_copy
@attr.define(kw_only=False, weakref_slot=False)
class CommandBuilder(special_endpoints.CommandBuilder):
    """Standard implementation of `hikari.api.special_endpoints.CommandBuilder`."""

    # Required arguments.
    _name: str = attr.field()
    _description: str = attr.field()

    # Key-word only not-required arguments.
    _id: undefined.UndefinedOr[snowflakes.Snowflake] = attr.field(default=undefined.UNDEFINED, kw_only=True)
    _default_permission: undefined.UndefinedOr[bool] = attr.field(default=undefined.UNDEFINED, kw_only=True)

    # Non-arguments.
    _options: typing.List[commands.CommandOption] = attr.field(factory=list)

    @property
    def description(self) -> str:
        return self._description

    @property
    def id(self) -> undefined.UndefinedOr[snowflakes.Snowflake]:
        return self._id

    @property
    def default_permission(self) -> undefined.UndefinedOr[bool]:
        return self._default_permission

    @property
    def options(self) -> typing.Sequence[commands.CommandOption]:
        return self._options.copy()

    @property
    def name(self) -> str:
        return self._name

    def add_option(self: _CommandBuilderT, option: commands.CommandOption) -> _CommandBuilderT:
        self._options.append(option)
        return self

    def set_id(self: _CommandBuilderT, id_: undefined.UndefinedOr[snowflakes.Snowflakeish], /) -> _CommandBuilderT:
        self._id = snowflakes.Snowflake(id_) if id_ is not undefined.UNDEFINED else undefined.UNDEFINED
        return self

    def set_default_permission(self: _CommandBuilderT, state: undefined.UndefinedOr[bool], /) -> _CommandBuilderT:
        self._default_permission = state
        return self

    def build(self, entity_factory: entity_factory_.EntityFactory, /) -> data_binding.JSONObject:
        data = data_binding.JSONObjectBuilder()
        data["name"] = self._name
        data["description"] = self._description
        data.put_array("options", self._options, conversion=entity_factory.serialize_command_option)
        data.put_snowflake("id", self._id)
        data.put("default_permission", self._default_permission)
        return data


def _build_emoji(
    emoji: typing.Union[snowflakes.Snowflakeish, emojis.Emoji, str, undefined.UndefinedType] = undefined.UNDEFINED
) -> typing.Tuple[undefined.UndefinedOr[str], undefined.UndefinedOr[str]]:
    """Build an emoji into the format accepted in buttons.

    Parameters
    ----------
    emoji : typing.Union[hikari.snowflakes.Snowflakeish, hikari.emojis.Emoji, builtins.str, hikari.undefined.UndefinedType]
        The ID, object or raw string of an emoji to set on a component.

    Returns
    -------
    typing.Tuple[hikari.undefined.UndefinedOr[builtins.str], hikari.undefined.UndefinedOr[builtins.str]]
        A union of the custom emoji's id if defined (index 0) or the unicode
        emoji's string representation (index 1).
    """  # noqa E501 - Line too long
    # Since these builder classes may be re-used, this method should be called when the builder is being constructed.
    if emoji is not undefined.UNDEFINED:
        if isinstance(emoji, (int, emojis.CustomEmoji)):
            return str(int(emoji)), undefined.UNDEFINED

        return undefined.UNDEFINED, str(emoji)

    return undefined.UNDEFINED, undefined.UNDEFINED


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class _ButtonBuilder(special_endpoints.ButtonBuilder[_ContainerProtoT]):
    _container: _ContainerProtoT = attr.field()
    _style: typing.Union[int, messages.ButtonStyle] = attr.field()
    _custom_id: undefined.UndefinedOr[str] = attr.field(default=undefined.UNDEFINED)
    _url: undefined.UndefinedOr[str] = attr.field(default=undefined.UNDEFINED)
    _emoji: typing.Union[snowflakes.Snowflakeish, emojis.Emoji, str, undefined.UndefinedType] = attr.field(
        default=undefined.UNDEFINED
    )
    _emoji_id: undefined.UndefinedOr[str] = attr.field(default=undefined.UNDEFINED)
    _emoji_name: undefined.UndefinedOr[str] = attr.field(default=undefined.UNDEFINED)
    _label: undefined.UndefinedOr[str] = attr.field(default=undefined.UNDEFINED)
    _is_disabled: bool = attr.field(default=False)

    @property
    def style(self) -> typing.Union[int, messages.ButtonStyle]:
        return self._style

    @property
    def emoji(self) -> typing.Union[snowflakes.Snowflakeish, emojis.Emoji, str, undefined.UndefinedType]:
        return self._emoji

    @property
    def label(self) -> undefined.UndefinedOr[str]:
        return self._label

    @property
    def is_disabled(self) -> bool:
        return self._is_disabled

    def set_emoji(
        self: _ButtonBuilderT,
        emoji: typing.Union[snowflakes.Snowflakeish, emojis.Emoji, str, undefined.UndefinedType],
        /,
    ) -> _ButtonBuilderT:
        self._emoji_id, self._emoji_name = _build_emoji(emoji)
        self._emoji = emoji
        return self

    def set_label(self: _ButtonBuilderT, label: undefined.UndefinedOr[str], /) -> _ButtonBuilderT:
        self._label = label
        return self

    def set_is_disabled(self: _ButtonBuilderT, state: bool, /) -> _ButtonBuilderT:
        self._is_disabled = state
        return self

    def add_to_container(self) -> _ContainerProtoT:
        self._container.add_component(self)
        return self._container

    def build(self) -> data_binding.JSONObject:
        data = data_binding.JSONObjectBuilder()

        data["type"] = messages.ComponentType.BUTTON
        data["style"] = self._style
        data["disabled"] = self._is_disabled
        data.put("label", self._label)

        if self._emoji_id is not undefined.UNDEFINED:
            data["emoji"] = {"id": self._emoji_id}

        elif self._emoji_name is not undefined.UNDEFINED:
            data["emoji"] = {"name": self._emoji_name}

        data.put("custom_id", self._custom_id)
        data.put("url", self._url)

        return data


@attr.define(kw_only=True, weakref_slot=False)
class LinkButtonBuilder(_ButtonBuilder[_ContainerProtoT], special_endpoints.LinkButtonBuilder[_ContainerProtoT]):
    """Builder class for link buttons."""

    _url: str = attr.field()

    @property
    def url(self) -> str:
        return self._url


@attr.define(kw_only=True, weakref_slot=False)
class InteractiveButtonBuilder(
    _ButtonBuilder[_ContainerProtoT], special_endpoints.InteractiveButtonBuilder[_ContainerProtoT]
):
    """Builder class for interactive buttons."""

    _custom_id: str = attr.field()

    @property
    def custom_id(self) -> str:
        return self._custom_id


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class _SelectOptionBuilder(special_endpoints.SelectOptionBuilder["_SelectMenuBuilderT"]):
    """Builder class for select menu options."""

    _menu: _SelectMenuBuilderT = attr.field()
    _label: str = attr.field()
    _value: str = attr.field()
    _description: undefined.UndefinedOr[str] = attr.field(default=undefined.UNDEFINED)
    _emoji: typing.Union[snowflakes.Snowflakeish, emojis.Emoji, str, undefined.UndefinedType] = attr.field(
        default=undefined.UNDEFINED
    )
    _emoji_id: undefined.UndefinedOr[str] = attr.field(default=undefined.UNDEFINED)
    _emoji_name: undefined.UndefinedOr[str] = attr.field(default=undefined.UNDEFINED)
    _is_default: bool = attr.field(default=False)

    @property
    def label(self) -> str:
        return self._label

    @property
    def value(self) -> str:
        return self._value

    @property
    def description(self) -> undefined.UndefinedOr[str]:
        return self._description

    @property
    def emoji(self) -> typing.Union[snowflakes.Snowflakeish, emojis.Emoji, str, undefined.UndefinedType]:
        return self._emoji

    @property
    def is_default(self) -> bool:
        return self._is_default

    def set_description(self: _SelectOptionBuilderT, value: undefined.UndefinedOr[str], /) -> _SelectOptionBuilderT:
        self._description = value
        return self

    def set_emoji(
        self: _SelectOptionBuilderT,
        emoji: typing.Union[snowflakes.Snowflakeish, emojis.Emoji, str, undefined.UndefinedType],
        /,
    ) -> _SelectOptionBuilderT:
        self._emoji_id, self._emoji_name = _build_emoji(emoji)
        self._emoji = emoji
        return self

    def set_is_default(self: _SelectOptionBuilderT, state: bool, /) -> _SelectOptionBuilderT:
        self._is_default = state
        return self

    def add_to_menu(self) -> _SelectMenuBuilderT:
        self._menu.add_raw_option(self)
        return self._menu

    def build(self) -> data_binding.JSONObject:
        data = data_binding.JSONObjectBuilder()

        data["label"] = self._label
        data["value"] = self._value
        data["default"] = self._is_default
        data.put("description", self._description)

        if self._emoji_id is not undefined.UNDEFINED:
            data["emoji"] = {"id": self._emoji_id}

        elif self._emoji_name is not undefined.UNDEFINED:
            data["emoji"] = {"name": self._emoji_name}

        return data


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class SelectMenuBuilder(special_endpoints.SelectMenuBuilder[_ContainerProtoT]):
    """Builder class for select menus."""

    _container: _ContainerProtoT = attr.field()
    _custom_id: str = attr.field()
    # Any has to be used here as we can't access Self type in this context
    _options: typing.List[special_endpoints.SelectOptionBuilder[typing.Any]] = attr.field(factory=list)
    _placeholder: undefined.UndefinedOr[str] = attr.field(default=undefined.UNDEFINED)
    _min_values: int = attr.field(default=0)
    _max_values: int = attr.field(default=1)
    _is_disabled: bool = attr.field(default=False)

    @property
    def custom_id(self) -> str:
        return self._custom_id

    @property
    def is_disabled(self) -> bool:
        return self._is_disabled

    @property
    def options(
        self: _SelectMenuBuilderT,
    ) -> typing.Sequence[special_endpoints.SelectOptionBuilder[_SelectMenuBuilderT]]:
        return self._options.copy()

    @property
    def placeholder(self) -> undefined.UndefinedOr[str]:
        return self._placeholder

    @property
    def min_values(self) -> int:
        return self._min_values

    @property
    def max_values(self) -> int:
        return self._max_values

    def add_option(
        self: _SelectMenuBuilderT, label: str, value: str, /
    ) -> special_endpoints.SelectOptionBuilder[_SelectMenuBuilderT]:
        return _SelectOptionBuilder(menu=self, label=label, value=value)

    def add_raw_option(
        self: _SelectMenuBuilderT, option: special_endpoints.SelectOptionBuilder[_SelectMenuBuilderT], /
    ) -> _SelectMenuBuilderT:
        self._options.append(option)
        return self

    def set_is_disabled(self: _SelectMenuBuilderT, state: bool, /) -> _SelectMenuBuilderT:
        self._is_disabled = state
        return self

    def set_placeholder(self: _SelectMenuBuilderT, value: undefined.UndefinedOr[str], /) -> _SelectMenuBuilderT:
        self._placeholder = value
        return self

    def set_min_values(self: _SelectMenuBuilderT, value: int, /) -> _SelectMenuBuilderT:
        self._min_values = value
        return self

    def set_max_values(self: _SelectMenuBuilderT, value: int, /) -> _SelectMenuBuilderT:
        self._max_values = value
        return self

    def add_to_container(self) -> _ContainerProtoT:
        self._container.add_component(self)
        return self._container

    def build(self) -> data_binding.JSONObject:
        data = data_binding.JSONObjectBuilder()

        data["type"] = messages.ComponentType.SELECT_MENU
        data["custom_id"] = self._custom_id
        data["options"] = [option.build() for option in self._options]
        data.put("placeholder", self._placeholder)
        data.put("min_values", self._min_values)
        data.put("max_values", self._max_values)
        data.put("disabled", self._is_disabled)
        return data


@attr.define(kw_only=True, weakref_slot=False)
class ActionRowBuilder(special_endpoints.ActionRowBuilder):
    """Standard implementation of `hikari.api.special_endpoints.ActionRowBuilder`."""

    _components: typing.List[special_endpoints.ComponentBuilder] = attr.field(factory=list)
    _stored_type: typing.Optional[messages.ComponentType] = attr.field(default=None)

    @property
    def components(self) -> typing.Sequence[special_endpoints.ComponentBuilder]:
        return self._components.copy()

    def _assert_can_add_type(self, type_: messages.ComponentType, /) -> None:
        if self._stored_type is not None and self._stored_type != type_:
            raise ValueError(
                f"{type_} component type cannot be added to a container which already holds {self._stored_type}"
            )

        self._stored_type = type_

    def add_component(self: _ActionRowBuilderT, component: special_endpoints.ComponentBuilder, /) -> _ActionRowBuilderT:
        self._components.append(component)
        return self

    @typing.overload
    def add_button(
        self: _ActionRowBuilderT, style: messages.InteractiveButtonTypesT, custom_id: str, /
    ) -> special_endpoints.InteractiveButtonBuilder[_ActionRowBuilderT]:
        ...

    @typing.overload
    def add_button(
        self: _ActionRowBuilderT,
        style: typing.Union[typing.Literal[messages.ButtonStyle.LINK], typing.Literal[5]],
        url: str,
        /,
    ) -> special_endpoints.LinkButtonBuilder[_ActionRowBuilderT]:
        ...

    def add_button(
        self: _ActionRowBuilderT, style: typing.Union[int, messages.ButtonStyle], url_or_custom_id: str, /
    ) -> special_endpoints.ButtonBuilder[_ActionRowBuilderT]:
        self._assert_can_add_type(messages.ComponentType.BUTTON)
        if style in messages.InteractiveButtonTypes:
            return InteractiveButtonBuilder(container=self, style=style, custom_id=url_or_custom_id)

        return LinkButtonBuilder(container=self, style=style, url=url_or_custom_id)

    def add_select_menu(
        self: _ActionRowBuilderT, custom_id: str, /
    ) -> special_endpoints.SelectMenuBuilder[_ActionRowBuilderT]:
        self._assert_can_add_type(messages.ComponentType.SELECT_MENU)
        return SelectMenuBuilder(container=self, custom_id=custom_id)

    def build(self) -> data_binding.JSONObject:
        return {
            "type": messages.ComponentType.ACTION_ROW,
            "components": [component.build() for component in self._components],
        }
