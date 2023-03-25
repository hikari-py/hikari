# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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

__all__: typing.Sequence[str] = (
    "CommandBuilder",
    "SlashCommandBuilder",
    "ContextMenuCommandBuilder",
    "TypingIndicator",
    "GuildBuilder",
    "InteractionAutocompleteBuilder",
    "InteractionDeferredBuilder",
    "InteractionMessageBuilder",
    "InteractiveButtonBuilder",
    "LinkButtonBuilder",
    "SelectMenuBuilder",
    "ChannelSelectMenuBuilder",
    "TextSelectMenuBuilder",
    "TextInputBuilder",
    "InteractionModalBuilder",
    "MessageActionRowBuilder",
    "ModalActionRowBuilder",
)

import asyncio
import typing

import attr

from hikari import channels
from hikari import commands
from hikari import components as component_models
from hikari import emojis
from hikari import errors
from hikari import files
from hikari import iterators
from hikari import locales
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

    from typing_extensions import Self

    from hikari import applications
    from hikari import audit_logs
    from hikari import colors
    from hikari import embeds as embeds_
    from hikari import guilds
    from hikari import permissions as permissions_
    from hikari import scheduled_events
    from hikari import users
    from hikari import voices
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import rest as rest_api

    _T = typing.TypeVar("_T")
    _TextSelectMenuBuilderT = typing.TypeVar("_TextSelectMenuBuilderT", bound="TextSelectMenuBuilder[typing.Any]")

    class _RequestCallSig(typing.Protocol):
        async def __call__(
            self,
            compiled_route: routes.CompiledRoute,
            *,
            query: typing.Optional[data_binding.StringMapBuilder] = None,
            form_builder: typing.Optional[data_binding.URLEncodedFormBuilder] = None,
            json: typing.Union[data_binding.JSONObjectBuilder, data_binding.JSONArray, None] = None,
            reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
            auth: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        ) -> typing.Union[None, data_binding.JSONObject, data_binding.JSONArray]:
            ...

    class _ThreadDeserializeSig(typing.Protocol["_GuildThreadChannelCovT"]):
        def __call__(
            self,
            payload: data_binding.JSONObject,
            /,
            *,
            guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
            member: undefined.UndefinedNoneOr[channels.ThreadMember] = undefined.UNDEFINED,
        ) -> _GuildThreadChannelCovT:
            raise NotImplementedError

    # Hack around used to avoid recursive generic types leading to type checker issues in builders
    class _ContainerProto(typing.Protocol):
        def add_component(self, component: special_endpoints.ComponentBuilder, /) -> Self:
            raise NotImplementedError


_ContainerProtoT = typing.TypeVar("_ContainerProtoT", bound="_ContainerProto")
_GuildThreadChannelT = typing.TypeVar("_GuildThreadChannelT", bound=channels.GuildThreadChannel)
_GuildThreadChannelCovT = typing.TypeVar("_GuildThreadChannelCovT", bound=channels.GuildThreadChannel, covariant=True)


@typing.final
class TypingIndicator(special_endpoints.TypingIndicator):
    """Result type of `hikari.api.rest.RESTClient.trigger_typing`.

    This is an object that can either be awaited like a coroutine to trigger
    the typing indicator once, or an async context manager to keep triggering
    the typing indicator repeatedly until the context finishes.

    .. note::
        This is a helper class that is used by `hikari.api.rest.RESTClient`.
        You should only ever need to use instances of this class that are
        produced by that API.
    """

    __slots__: typing.Sequence[str] = ("_route", "_request_call", "_task", "_rest_close_event", "_task_name")

    def __init__(
        self,
        request_call: _RequestCallSig,
        channel: snowflakes.SnowflakeishOr[channels.TextableChannel],
        rest_close_event: asyncio.Event,
    ) -> None:
        self._route = routes.POST_CHANNEL_TYPING.compile(channel=channel)
        self._request_call = request_call
        self._task_name = f"repeatedly trigger typing in {channel}"
        self._task: typing.Optional[asyncio.Task[None]] = None
        self._rest_close_event = rest_close_event

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

    .. note::
        If you call `add_role`, the default roles provided by Discord will
        be created. This also applies to the `add_` functions for
        text channels/voice channels/categories.

    .. note::
        Functions that return a `hikari.snowflakes.Snowflake` do
        **not** provide the final ID that the object will have once the
        API call is made. The returned IDs are only able to be used to
        re-reference particular objects while building the guild format
        to allow for the creation of channels within categories,
        and to provide permission overwrites.

    Examples
    --------
    Creating an empty guild:

    .. code-block:: python

        guild = await rest.guild_builder("My Server!").create()

    Creating a guild with an icon:

    .. code-block:: python

        from hikari.files import WebResourceStream

        guild_builder = rest.guild_builder("My Server!")
        guild_builder.icon = WebResourceStream("cat.png", "http://...")
        guild = await guild_builder.create()

    Adding roles to your guild:

    .. code-block:: python

        from hikari.permissions import Permissions

        guild_builder = rest.guild_builder("My Server!")

        everyone_role_id = guild_builder.add_role("@everyone")
        admin_role_id = guild_builder.add_role("Admins", permissions=Permissions.ADMINISTRATOR)

        await guild_builder.create()

    .. warning::
        The first role must always be the `@everyone` role.

    Adding a text channel to your guild:

    .. code-block:: python

        guild_builder = rest.guild_builder("My Server!")

        category_id = guild_builder.add_category("My safe place")
        channel_id = guild_builder.add_text_channel("general", parent_id=category_id)

        await guild_builder.create()
    """

    # Required arguments.
    _entity_factory: entity_factory_.EntityFactory = attr.field(
        alias="entity_factory", metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    _executor: typing.Optional[concurrent.futures.Executor] = attr.field(
        alias="executor", metadata={attr_extensions.SKIP_DEEP_COPY: True}
    )
    _name: str = attr.field(alias="name")
    _request_call: _RequestCallSig = attr.field(alias="request_call", metadata={attr_extensions.SKIP_DEEP_COPY: True})

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
        request_call: _RequestCallSig,
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
        request_call: _RequestCallSig,
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
        request_call: _RequestCallSig,
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

        if self._newest_first:
            chunk.reverse()

        self._first_id = chunk[-1]["id"]
        return (self._entity_factory.deserialize_own_guild(g) for g in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class GuildBanIterator(iterators.BufferedLazyIterator["guilds.GuildBan"]):
    """Iterator implementation for retrieving guild bans."""

    __slots__: typing.Sequence[str] = (
        "_entity_factory",
        "_guild_id",
        "_request_call",
        "_route",
        "_first_id",
        "_newest_first",
    )

    def __init__(
        self,
        entity_factory: entity_factory_.EntityFactory,
        request_call: _RequestCallSig,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        newest_first: bool,
        first_id: str,
    ) -> None:
        super().__init__()
        self._guild_id = snowflakes.Snowflake(str(int(guild)))
        self._route = routes.GET_GUILD_BANS.compile(guild=guild)
        self._request_call = request_call
        self._entity_factory = entity_factory
        self._first_id = first_id
        self._newest_first = newest_first

    async def _next_chunk(self) -> typing.Optional[typing.Generator[guilds.GuildBan, typing.Any, None]]:
        query = data_binding.StringMapBuilder()
        query.put("before" if self._newest_first else "after", self._first_id)
        query.put("limit", 1000)

        chunk = await self._request_call(compiled_route=self._route, query=query)
        assert isinstance(chunk, list)

        if not chunk:
            return None

        if self._newest_first:
            # These are always returned in ascending order by `.user.id`.
            chunk.reverse()

        self._first_id = chunk[-1]["user"]["id"]
        return (self._entity_factory.deserialize_guild_member_ban(b) for b in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class MemberIterator(iterators.BufferedLazyIterator["guilds.Member"]):
    """Implementation of an iterator for retrieving members in a guild."""

    __slots__: typing.Sequence[str] = ("_entity_factory", "_guild_id", "_request_call", "_route", "_first_id")

    def __init__(
        self,
        entity_factory: entity_factory_.EntityFactory,
        request_call: _RequestCallSig,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> None:
        super().__init__()
        self._guild_id = snowflakes.Snowflake(str(int(guild)))
        self._route = routes.GET_GUILD_MEMBERS.compile(guild=guild)
        self._request_call = request_call
        self._entity_factory = entity_factory
        # This starts at the default provided by Discord instead of the max snowflake
        # because that caused Discord to take about 2 seconds more to return the first response.
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
class ScheduledEventUserIterator(iterators.BufferedLazyIterator["scheduled_events.ScheduledEventUser"]):
    """Implementation of an iterator for retrieving the users subscribed to a scheduled event."""

    __slots__: typing.Sequence[str] = (
        "_entity_factory",
        "_first_id",
        "_guild_id",
        "_newest_first",
        "_request_call",
        "_route",
    )

    def __init__(
        self,
        entity_factory: entity_factory_.EntityFactory,
        request_call: _RequestCallSig,
        newest_first: bool,
        first_id: str,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        event: snowflakes.SnowflakeishOr[scheduled_events.ScheduledEvent],
    ) -> None:
        super().__init__()
        self._entity_factory = entity_factory
        self._first_id = first_id
        self._guild_id = snowflakes.Snowflake(guild)
        self._newest_first = newest_first
        self._request_call = request_call
        self._route = routes.GET_GUILD_SCHEDULED_EVENT_USERS.compile(guild=guild, scheduled_event=event)

    async def _next_chunk(
        self,
    ) -> typing.Optional[typing.Generator[scheduled_events.ScheduledEventUser, typing.Any, None]]:
        query = data_binding.StringMapBuilder()
        query.put("before" if self._newest_first else "after", self._first_id)
        query.put("limit", 100)
        query.put("with_member", True)

        chunk = await self._request_call(compiled_route=self._route, query=query)
        assert isinstance(chunk, list)

        if not chunk:
            return None

        if self._newest_first:
            # These are always returned in ascending order by `.user.id`.
            chunk.reverse()

        self._first_id = chunk[-1]["user"]["id"]
        return (self._entity_factory.deserialize_scheduled_event_user(u, guild_id=self._guild_id) for u in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class AuditLogIterator(iterators.LazyIterator["audit_logs.AuditLog"]):
    """Iterator implementation for an audit log."""

    __slots__: typing.Sequence[str] = (
        "_entity_factory",
        "_action_type",
        "_guild_id",
        "_request_call",
        "_route",
        "_first_id",
        "_user",
    )

    def __init__(
        self,
        entity_factory: entity_factory_.EntityFactory,
        request_call: _RequestCallSig,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        before: undefined.UndefinedOr[str],
        user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]],
        action_type: undefined.UndefinedOr[typing.Union["audit_logs.AuditLogEventType", int]],
    ) -> None:
        self._action_type = action_type
        self._entity_factory = entity_factory
        self._first_id = before
        self._guild_id = snowflakes.Snowflake(guild)
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

        log = self._entity_factory.deserialize_audit_log(response, guild_id=self._guild_id)
        # Since deserialize_audit_log may skip entries it doesn't recognise,
        # first_id has to be calculated based on the raw payload as log.entries
        # may be missing entries.
        self._first_id = str(min(entry["id"] for entry in audit_log_entries))
        return log


class GuildThreadIterator(iterators.BufferedLazyIterator[_GuildThreadChannelT]):
    """Iterator implemented for guild thread endpoints."""

    __slots__: typing.Sequence[str] = (
        "_before_is_timestamp",
        "_deserialize",
        "_entity_factory",
        "_has_more",
        "_next_before",
        "_request_call",
        "_route",
    )

    def __init__(
        self,
        deserialize: _ThreadDeserializeSig[_GuildThreadChannelCovT],
        entity_factory: entity_factory_.EntityFactory,
        request_call: _RequestCallSig,
        route: routes.CompiledRoute,
        before: undefined.UndefinedOr[str],
        before_is_timestamp: bool,
    ) -> None:
        super().__init__()
        self._before_is_timestamp = before_is_timestamp
        self._deserialize = deserialize
        self._entity_factory = entity_factory
        self._has_more = True
        self._next_before = before
        self._request_call = request_call
        self._route = route

    async def _next_chunk(self) -> typing.Optional[typing.Generator[_GuildThreadChannelCovT, typing.Any, None]]:
        if not self._has_more:
            return None

        query = data_binding.StringMapBuilder()
        query.put("limit", 100)
        query.put("before", self._next_before)

        response = await self._request_call(compiled_route=self._route, query=query)
        assert isinstance(response, dict)

        if not (threads := response["threads"]):
            # Since GET is idempotent, has_more should always be false if there
            # are no threads in the current response.
            self._has_more = False
            return None

        self._has_more = response["has_more"]
        members = {int(member["id"]): member for member in response["members"]}
        if self._before_is_timestamp:
            self._next_before = (
                time.iso8601_datetime_string_to_datetime(threads[-1]["thread_metadata"]["archive_timestamp"])
            ).isoformat()

        else:
            self._next_before = str(int(threads[-1]["id"]))

        return (
            self._deserialize(
                payload,
                member=_maybe_cast(self._entity_factory.deserialize_thread_member, members.get(int(payload["id"]))),
            )
            for payload in threads
        )


def _maybe_cast(
    callback: typing.Callable[[data_binding.JSONObject], _T], data: typing.Optional[data_binding.JSONObject]
) -> typing.Optional[_T]:
    if data:
        return callback(data)

    return None


@attr_extensions.with_copy
@attr.define(kw_only=False, weakref_slot=False)
class InteractionAutocompleteBuilder(special_endpoints.InteractionAutocompleteBuilder):
    """Standard implementation of `hikari.api.special_endpoints.InteractionAutocompleteBuilder`."""

    _choices: typing.Sequence[commands.CommandChoice] = attr.field(alias="choices", factory=list)

    @property
    def type(self) -> typing.Literal[base_interactions.ResponseType.AUTOCOMPLETE]:
        return base_interactions.ResponseType.AUTOCOMPLETE

    @property
    def choices(self) -> typing.Sequence[commands.CommandChoice]:
        return self._choices

    def set_choices(self, choices: typing.Sequence[commands.CommandChoice], /) -> Self:
        """Set autocomplete choices.

        Returns
        -------
        InteractionAutocompleteBuilder
            Object of this builder.
        """
        self._choices = choices
        return self

    def build(
        self, _: entity_factory_.EntityFactory, /
    ) -> typing.Tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        data = {"choices": [{"name": choice.name, "value": choice.value} for choice in self._choices]}
        return {"type": self.type, "data": data}, ()


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
        alias="type",
        converter=base_interactions.ResponseType,
        validator=attr.validators.in_(base_interactions.DEFERRED_RESPONSE_TYPES),
    )

    _flags: typing.Union[undefined.UndefinedType, int, messages.MessageFlag] = attr.field(
        alias="flags", default=undefined.UNDEFINED, kw_only=True
    )

    @property
    def type(self) -> base_interactions.DeferredResponseTypesT:
        return self._type

    @property
    def flags(self) -> typing.Union[undefined.UndefinedType, int, messages.MessageFlag]:
        return self._flags

    def set_flags(self, flags: typing.Union[undefined.UndefinedType, int, messages.MessageFlag], /) -> Self:
        self._flags = flags
        return self

    def build(
        self, _: entity_factory_.EntityFactory, /
    ) -> typing.Tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        if self._flags is not undefined.UNDEFINED:
            return {"type": self._type, "data": {"flags": self._flags}}, ()

        return {"type": self._type}, ()


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
    content : hikari.undefined.UndefinedOr[str]
        The content of this response, if supplied. This follows the same rules
        as "content" on create message.
    """

    # Required arguments.
    _type: base_interactions.MessageResponseTypesT = attr.field(
        alias="type",
        converter=base_interactions.ResponseType,
        validator=attr.validators.in_(base_interactions.MESSAGE_RESPONSE_TYPES),
    )

    # Not-required arguments.
    _content: undefined.UndefinedOr[str] = attr.field(alias="content", default=undefined.UNDEFINED)

    # Key-word only not-required arguments.
    _flags: typing.Union[int, messages.MessageFlag, undefined.UndefinedType] = attr.field(
        alias="flags", default=undefined.UNDEFINED, kw_only=True
    )
    _is_tts: undefined.UndefinedOr[bool] = attr.field(alias="is_tts", default=undefined.UNDEFINED, kw_only=True)
    _mentions_everyone: undefined.UndefinedOr[bool] = attr.field(
        alias="mentions_everyone", default=undefined.UNDEFINED, kw_only=True
    )
    _role_mentions: undefined.UndefinedOr[
        typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
    ] = attr.field(alias="role_mentions", default=undefined.UNDEFINED, kw_only=True)
    _user_mentions: undefined.UndefinedOr[
        typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
    ] = attr.field(alias="user_mentions", default=undefined.UNDEFINED, kw_only=True)
    _attachments: undefined.UndefinedNoneOr[typing.List[files.Resourceish]] = attr.field(
        alias="attachments", default=undefined.UNDEFINED, kw_only=True
    )
    _components: undefined.UndefinedOr[typing.List[special_endpoints.ComponentBuilder]] = attr.field(
        alias="components", default=undefined.UNDEFINED, kw_only=True
    )
    _embeds: undefined.UndefinedOr[typing.List[embeds_.Embed]] = attr.field(
        alias="embeds", default=undefined.UNDEFINED, kw_only=True
    )

    @property
    def attachments(self) -> undefined.UndefinedNoneOr[typing.Sequence[files.Resourceish]]:
        return self._attachments.copy() if self._attachments else self._attachments

    @property
    def content(self) -> undefined.UndefinedOr[str]:
        return self._content

    @property
    def components(self) -> undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]]:
        return self._components.copy() if self._components is not undefined.UNDEFINED else undefined.UNDEFINED

    @property
    def embeds(self) -> undefined.UndefinedOr[typing.Sequence[embeds_.Embed]]:
        return self._embeds.copy() if self._embeds is not undefined.UNDEFINED else undefined.UNDEFINED

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

    def clear_attachments(self, /) -> Self:
        self._attachments = None
        return self

    def add_attachment(self, attachment: files.Resourceish, /) -> Self:
        if not self._attachments:
            self._attachments = []

        self._attachments.append(attachment)
        return self

    def add_component(self, component: special_endpoints.ComponentBuilder, /) -> Self:
        if self._components is undefined.UNDEFINED:
            self._components = []

        self._components.append(component)
        return self

    def add_embed(self, embed: embeds_.Embed, /) -> Self:
        if self._embeds is undefined.UNDEFINED:
            self._embeds = []

        self._embeds.append(embed)
        return self

    def set_content(self, content: undefined.UndefinedOr[str], /) -> Self:
        self._content = str(content) if content is not undefined.UNDEFINED else undefined.UNDEFINED
        return self

    def set_flags(self, flags: typing.Union[undefined.UndefinedType, int, messages.MessageFlag], /) -> Self:
        self._flags = flags
        return self

    def set_tts(self, tts: undefined.UndefinedOr[bool], /) -> Self:
        self._is_tts = tts
        return self

    def set_mentions_everyone(self, state: undefined.UndefinedOr[bool] = undefined.UNDEFINED, /) -> Self:
        self._mentions_everyone = state
        return self

    def set_role_mentions(
        self,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
        /,
    ) -> Self:
        self._role_mentions = role_mentions
        return self

    def set_user_mentions(
        self,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        /,
    ) -> Self:
        self._user_mentions = user_mentions
        return self

    def build(
        self, entity_factory: entity_factory_.EntityFactory, /
    ) -> typing.Tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        data = data_binding.JSONObjectBuilder()
        data.put("content", self.content)

        final_attachments = []
        if self._attachments:
            attachments_payload = []

            for f in self._attachments:
                if isinstance(f, messages.Attachment):
                    attachments_payload.append({"id": f.id, "filename": f.filename})
                    continue

                final_attachments.append(files.ensure_resource(f))

            if attachments_payload:
                data.put("attachments", attachments_payload)

        elif self._attachments is None:
            data.put("attachments", None)

        if self._embeds is not undefined.UNDEFINED:
            embeds: typing.List[data_binding.JSONObject] = []
            for embed, attachments in map(entity_factory.serialize_embed, self._embeds):
                final_attachments.extend(attachments)
                embeds.append(embed)

            data["embeds"] = embeds

        data.put_array("components", self._components, conversion=lambda component: component.build())
        data.put("flags", self.flags)
        data.put("tts", self.is_tts)

        if (
            not undefined.all_undefined(self.mentions_everyone, self.user_mentions, self.role_mentions)
            or self.type is base_interactions.ResponseType.MESSAGE_CREATE
        ):
            data["allowed_mentions"] = mentions.generate_allowed_mentions(
                self.mentions_everyone, undefined.UNDEFINED, self.user_mentions, self.role_mentions
            )

        return {"type": self._type, "data": data}, final_attachments


@attr.define(kw_only=False, weakref_slot=False)
class InteractionModalBuilder(special_endpoints.InteractionModalBuilder):
    """Standard implementation of `hikari.api.special_endpoints.InteractionModalBuilder`."""

    _title: str = attr.field(alias="title")
    _custom_id: str = attr.field(alias="custom_id")
    _components: typing.List[special_endpoints.ComponentBuilder] = attr.field(alias="components", factory=list)

    @property
    def type(self) -> typing.Literal[base_interactions.ResponseType.MODAL]:
        return base_interactions.ResponseType.MODAL

    @property
    def title(self) -> str:
        return self._title

    @property
    def custom_id(self) -> str:
        return self._custom_id

    @property
    def components(self) -> typing.Sequence[special_endpoints.ComponentBuilder]:
        return self._components

    def set_title(self, title: str, /) -> Self:
        self._title = title
        return self

    def set_custom_id(self, custom_id: str, /) -> Self:
        self._custom_id = custom_id
        return self

    def add_component(self, component: special_endpoints.ComponentBuilder, /) -> Self:
        self._components.append(component)
        return self

    def build(
        self, entity_factory: entity_factory_.EntityFactory, /
    ) -> typing.Tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        data = data_binding.JSONObjectBuilder()
        data.put("title", self._title)
        data.put("custom_id", self._custom_id)
        data.put_array("components", self._components, conversion=lambda component: component.build())

        return {"type": self.type, "data": data}, ()


@attr.define(kw_only=False, weakref_slot=False)
class CommandBuilder(special_endpoints.CommandBuilder):
    """Standard implementation of `hikari.api.special_endpoints.CommandBuilder`."""

    _name: str = attr.field(alias="name")

    _id: undefined.UndefinedOr[snowflakes.Snowflake] = attr.field(alias="id", default=undefined.UNDEFINED, kw_only=True)
    _default_member_permissions: typing.Union[undefined.UndefinedType, int, permissions_.Permissions] = attr.field(
        alias="default_member_permissions", default=undefined.UNDEFINED, kw_only=True
    )
    _is_dm_enabled: undefined.UndefinedOr[bool] = attr.field(
        alias="is_dm_enabled", default=undefined.UNDEFINED, kw_only=True
    )
    _is_nsfw: undefined.UndefinedOr[bool] = attr.field(alias="is_nsfw", default=undefined.UNDEFINED, kw_only=True)

    _name_localizations: typing.Mapping[typing.Union[locales.Locale, str], str] = attr.field(
        alias="name_localizations", factory=dict, kw_only=True
    )

    @property
    def id(self) -> undefined.UndefinedOr[snowflakes.Snowflake]:
        return self._id

    @property
    def default_member_permissions(self) -> typing.Union[undefined.UndefinedType, permissions_.Permissions, int]:
        return self._default_member_permissions

    @property
    def is_dm_enabled(self) -> undefined.UndefinedOr[bool]:
        return self._is_dm_enabled

    @property
    def is_nsfw(self) -> undefined.UndefinedOr[bool]:
        return self._is_nsfw

    @property
    def name(self) -> str:
        return self._name

    def set_id(self, id_: undefined.UndefinedOr[snowflakes.Snowflakeish], /) -> Self:
        self._id = snowflakes.Snowflake(id_) if id_ is not undefined.UNDEFINED else undefined.UNDEFINED
        return self

    def set_default_member_permissions(
        self,
        default_member_permissions: typing.Union[undefined.UndefinedType, int, permissions_.Permissions],
        /,
    ) -> Self:
        self._default_member_permissions = default_member_permissions
        return self

    def set_is_dm_enabled(self, state: undefined.UndefinedOr[bool], /) -> Self:
        self._is_dm_enabled = state
        return self

    def set_is_nsfw(self, state: undefined.UndefinedOr[bool], /) -> Self:
        self._is_nsfw = state
        return self

    @property
    def name_localizations(self) -> typing.Mapping[typing.Union[locales.Locale, str], str]:
        return self._name_localizations

    def set_name_localizations(
        self,
        name_localizations: typing.Mapping[typing.Union[locales.Locale, str], str],
        /,
    ) -> Self:
        self._name_localizations = name_localizations
        return self

    def build(self, _: entity_factory_.EntityFactory, /) -> typing.MutableMapping[str, typing.Any]:
        data = data_binding.JSONObjectBuilder()
        data["name"] = self._name
        data["type"] = self.type
        data.put_snowflake("id", self._id)
        data.put("name_localizations", self._name_localizations)
        data.put("dm_permission", self._is_dm_enabled)
        data.put("nsfw", self._is_nsfw)

        # Discord considers 0 the same thing as ADMINISTRATORS, but we make it nicer to work with
        # by using it correctly.
        if self._default_member_permissions != 0:
            data.put("default_member_permissions", self._default_member_permissions)

        return data


@attr_extensions.with_copy
@attr.define(kw_only=False, weakref_slot=False)
class SlashCommandBuilder(CommandBuilder, special_endpoints.SlashCommandBuilder):
    """Builder class for slash commands."""

    _description: str = attr.field(alias="description")
    _options: typing.List[commands.CommandOption] = attr.field(alias="options", factory=list, kw_only=True)
    _description_localizations: typing.Mapping[typing.Union[locales.Locale, str], str] = attr.field(
        alias="description_localizations", factory=dict, kw_only=True
    )

    @property
    def description(self) -> str:
        return self._description

    @property
    def type(self) -> commands.CommandType:
        return commands.CommandType.SLASH

    def add_option(self, option: commands.CommandOption) -> Self:
        self._options.append(option)
        return self

    @property
    def options(self) -> typing.Sequence[commands.CommandOption]:
        return self._options.copy()

    @property
    def description_localizations(
        self,
    ) -> typing.Mapping[typing.Union[locales.Locale, str], str]:
        return self._description_localizations

    def set_description_localizations(
        self,
        description_localizations: typing.Mapping[typing.Union[locales.Locale, str], str],
        /,
    ) -> Self:
        self._description_localizations = description_localizations
        return self

    def build(self, entity_factory: entity_factory_.EntityFactory, /) -> typing.MutableMapping[str, typing.Any]:
        data = super().build(entity_factory)
        # Under this context we know this'll always be a JSONObjectBuilder but
        # the return types need to be kept as MutableMapping to avoid exposing an
        # internal type on the public API.
        assert isinstance(data, data_binding.JSONObjectBuilder)
        data.put("description", self._description)
        data.put_array("options", self._options, conversion=entity_factory.serialize_command_option)
        data.put("description_localizations", self._description_localizations)
        return data

    async def create(
        self,
        rest: rest_api.RESTClient,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        /,
        *,
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> commands.SlashCommand:
        return await rest.create_slash_command(
            application,
            self._name,
            self._description,
            guild=guild,
            options=self._options,
            name_localizations=self._name_localizations,
            description_localizations=self._description_localizations,
            default_member_permissions=self._default_member_permissions,
            dm_enabled=self._is_dm_enabled,
            nsfw=self._is_nsfw,
        )


@attr_extensions.with_copy
@attr.define(kw_only=False, weakref_slot=False)
class ContextMenuCommandBuilder(CommandBuilder, special_endpoints.ContextMenuCommandBuilder):
    """Builder class for context menu commands."""

    _type: commands.CommandType = attr.field(alias="type")
    # name is re-declared here to ensure type is before it in the initializer's args.
    _name: str = attr.field(alias="name")

    @property
    def type(self) -> commands.CommandType:
        return self._type

    async def create(
        self,
        rest: rest_api.RESTClient,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        /,
        *,
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> commands.ContextMenuCommand:
        return await rest.create_context_menu_command(
            application,
            self._type,
            self._name,
            guild=guild,
            name_localizations=self._name_localizations,
            default_member_permissions=self._default_member_permissions,
            dm_enabled=self._is_dm_enabled,
            nsfw=self.is_nsfw,
        )


def _build_emoji(
    emoji: typing.Union[snowflakes.Snowflakeish, emojis.Emoji, str, undefined.UndefinedType] = undefined.UNDEFINED
) -> typing.Tuple[undefined.UndefinedOr[str], undefined.UndefinedOr[str]]:
    """Build an emoji into the format accepted in buttons.

    Parameters
    ----------
    emoji : typing.Union[hikari.snowflakes.Snowflakeish, hikari.emojis.Emoji, str, hikari.undefined.UndefinedType]
        The ID, object or raw string of an emoji to set on a component.

    Returns
    -------
    typing.Tuple[hikari.undefined.UndefinedOr[str], hikari.undefined.UndefinedOr[str]]
        A union of the custom emoji's id if defined (index 0) or the unicode
        emoji's string representation (index 1).
    """
    # Since these builder classes may be re-used, this method should be called when the builder is being constructed.
    if emoji is not undefined.UNDEFINED:
        if isinstance(emoji, (int, emojis.CustomEmoji)):
            return str(int(emoji)), undefined.UNDEFINED

        return undefined.UNDEFINED, str(emoji)

    return undefined.UNDEFINED, undefined.UNDEFINED


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class _ButtonBuilder(special_endpoints.ButtonBuilder[_ContainerProtoT]):
    _container: _ContainerProtoT = attr.field(alias="container")
    _style: typing.Union[int, component_models.ButtonStyle] = attr.field(alias="style")
    _custom_id: undefined.UndefinedOr[str] = attr.field(alias="custom_id", default=undefined.UNDEFINED)
    _url: undefined.UndefinedOr[str] = attr.field(alias="url", default=undefined.UNDEFINED)
    _emoji: typing.Union[snowflakes.Snowflakeish, emojis.Emoji, str, undefined.UndefinedType] = attr.field(
        default=undefined.UNDEFINED
    )
    _emoji_id: undefined.UndefinedOr[str] = attr.field(alias="emoji_id", default=undefined.UNDEFINED)
    _emoji_name: undefined.UndefinedOr[str] = attr.field(alias="emoji_name", default=undefined.UNDEFINED)
    _label: undefined.UndefinedOr[str] = attr.field(alias="label", default=undefined.UNDEFINED)
    _is_disabled: bool = attr.field(alias="is_disabled", default=False)

    @property
    def type(self) -> typing.Literal[component_models.ComponentType.BUTTON]:
        return component_models.ComponentType.BUTTON

    @property
    def style(self) -> typing.Union[int, component_models.ButtonStyle]:
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
        self,
        emoji: typing.Union[snowflakes.Snowflakeish, emojis.Emoji, str, undefined.UndefinedType],
        /,
    ) -> Self:
        self._emoji_id, self._emoji_name = _build_emoji(emoji)
        self._emoji = emoji
        return self

    def set_label(self, label: undefined.UndefinedOr[str], /) -> Self:
        self._label = label
        return self

    def set_is_disabled(self, state: bool, /) -> Self:
        self._is_disabled = state
        return self

    def add_to_container(self) -> _ContainerProtoT:
        self._container.add_component(self)
        return self._container

    def build(self) -> typing.MutableMapping[str, typing.Any]:
        data = data_binding.JSONObjectBuilder()

        data["type"] = component_models.ComponentType.BUTTON
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

    _url: str = attr.field(alias="url")

    @property
    def url(self) -> str:
        return self._url


@attr.define(kw_only=True, weakref_slot=False)
class InteractiveButtonBuilder(
    _ButtonBuilder[_ContainerProtoT], special_endpoints.InteractiveButtonBuilder[_ContainerProtoT]
):
    """Builder class for interactive buttons."""

    _custom_id: str = attr.field(alias="custom_id")

    @property
    def custom_id(self) -> str:
        return self._custom_id


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class _SelectOptionBuilder(special_endpoints.SelectOptionBuilder["_TextSelectMenuBuilderT"]):
    """Builder class for select menu options."""

    _menu: _TextSelectMenuBuilderT = attr.field(alias="menu")
    _label: str = attr.field(alias="label")
    _value: str = attr.field(alias="value")
    _description: undefined.UndefinedOr[str] = attr.field(alias="description", default=undefined.UNDEFINED)
    _emoji: typing.Union[snowflakes.Snowflakeish, emojis.Emoji, str, undefined.UndefinedType] = attr.field(
        alias="emoji", default=undefined.UNDEFINED
    )
    _emoji_id: undefined.UndefinedOr[str] = attr.field(alias="emoji_id", default=undefined.UNDEFINED)
    _emoji_name: undefined.UndefinedOr[str] = attr.field(alias="emoji_name", default=undefined.UNDEFINED)
    _is_default: bool = attr.field(alias="is_default", default=False)

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

    def set_description(self, value: undefined.UndefinedOr[str], /) -> Self:
        self._description = value
        return self

    def set_emoji(
        self,
        emoji: typing.Union[snowflakes.Snowflakeish, emojis.Emoji, str, undefined.UndefinedType],
        /,
    ) -> Self:
        self._emoji_id, self._emoji_name = _build_emoji(emoji)
        self._emoji = emoji
        return self

    def set_is_default(self, state: bool, /) -> Self:
        self._is_default = state
        return self

    def add_to_menu(self) -> _TextSelectMenuBuilderT:
        self._menu.add_raw_option(self)
        return self._menu

    def build(self) -> typing.MutableMapping[str, typing.Any]:
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

    _container: _ContainerProtoT = attr.field(alias="container")
    _type: typing.Union[component_models.ComponentType, int] = attr.field(alias="type")
    _custom_id: str = attr.field(alias="custom_id")
    _placeholder: undefined.UndefinedOr[str] = attr.field(alias="placeholder", default=undefined.UNDEFINED)
    _min_values: int = attr.field(alias="min_values", default=0)
    _max_values: int = attr.field(alias="max_values", default=1)
    _is_disabled: bool = attr.field(alias="is_disabled", default=False)

    @property
    def type(self) -> typing.Union[int, component_models.ComponentType]:
        return self._type

    @property
    def custom_id(self) -> str:
        return self._custom_id

    @property
    def is_disabled(self) -> bool:
        return self._is_disabled

    @property
    def placeholder(self) -> undefined.UndefinedOr[str]:
        return self._placeholder

    @property
    def min_values(self) -> int:
        return self._min_values

    @property
    def max_values(self) -> int:
        return self._max_values

    def set_is_disabled(self, state: bool, /) -> Self:
        self._is_disabled = state
        return self

    def set_placeholder(self, value: undefined.UndefinedOr[str], /) -> Self:
        self._placeholder = value
        return self

    def set_min_values(self, value: int, /) -> Self:
        self._min_values = value
        return self

    def set_max_values(self, value: int, /) -> Self:
        self._max_values = value
        return self

    def add_to_container(self) -> _ContainerProtoT:
        self._container.add_component(self)
        return self._container

    def build(self) -> typing.MutableMapping[str, typing.Any]:
        data = data_binding.JSONObjectBuilder()

        data["type"] = self._type
        data["custom_id"] = self._custom_id
        data.put("placeholder", self._placeholder)
        data.put("min_values", self._min_values)
        data.put("max_values", self._max_values)
        data.put("disabled", self._is_disabled)
        return data


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class TextSelectMenuBuilder(
    SelectMenuBuilder[_ContainerProtoT], special_endpoints.TextSelectMenuBuilder[_ContainerProtoT]
):
    """Builder class for text select menus."""

    _type: typing.Literal[component_models.ComponentType.TEXT_SELECT_MENU] = attr.field(
        default=component_models.ComponentType.TEXT_SELECT_MENU, init=False
    )
    # Any has to be used here as we can't access Self type in this context
    _options: typing.List[special_endpoints.SelectOptionBuilder[typing.Any]] = attr.field(alias="options", factory=list)

    @property
    def options(
        self,
    ) -> typing.Sequence[special_endpoints.SelectOptionBuilder[Self]]:
        return self._options.copy()

    def add_option(self, label: str, value: str, /) -> special_endpoints.SelectOptionBuilder[Self]:
        return _SelectOptionBuilder(menu=self, label=label, value=value)

    def add_raw_option(self, option: special_endpoints.SelectOptionBuilder[Self], /) -> Self:
        self._options.append(option)
        return self

    def build(self) -> typing.MutableMapping[str, typing.Any]:
        data = super().build()

        data["options"] = [option.build() for option in self._options]
        return data


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class ChannelSelectMenuBuilder(
    SelectMenuBuilder[_ContainerProtoT], special_endpoints.ChannelSelectMenuBuilder[_ContainerProtoT]
):
    """Builder class for channel select menus."""

    _channel_types: typing.Sequence[channels.ChannelType] = attr.field(alias="channel_types", factory=list)
    _type: typing.Literal[component_models.ComponentType.CHANNEL_SELECT_MENU] = attr.field(
        default=component_models.ComponentType.CHANNEL_SELECT_MENU, init=False
    )

    @property
    def channel_types(self) -> typing.Sequence[channels.ChannelType]:
        return self._channel_types

    def set_channel_types(self, value: typing.Sequence[channels.ChannelType], /) -> Self:
        self._channel_types = value
        return self

    def build(self) -> typing.MutableMapping[str, typing.Any]:
        data = super().build()

        data["channel_types"] = self._channel_types
        return data


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class TextInputBuilder(special_endpoints.TextInputBuilder[_ContainerProtoT]):
    """Standard implementation of `hikari.api.special_endpoints.TextInputBuilder`."""

    _container: _ContainerProtoT = attr.field(alias="container")
    _custom_id: str = attr.field(alias="custom_id")
    _label: str = attr.field(alias="label")

    _style: component_models.TextInputStyle = attr.field(alias="style", default=component_models.TextInputStyle.SHORT)
    _placeholder: undefined.UndefinedOr[str] = attr.field(
        alias="placeholder", default=undefined.UNDEFINED, kw_only=True
    )
    _value: undefined.UndefinedOr[str] = attr.field(alias="value", default=undefined.UNDEFINED, kw_only=True)
    _required: undefined.UndefinedOr[bool] = attr.field(alias="required", default=undefined.UNDEFINED, kw_only=True)
    _min_length: undefined.UndefinedOr[int] = attr.field(alias="min_length", default=undefined.UNDEFINED, kw_only=True)
    _max_length: undefined.UndefinedOr[int] = attr.field(alias="max_length", default=undefined.UNDEFINED, kw_only=True)

    @property
    def type(self) -> typing.Literal[component_models.ComponentType.TEXT_INPUT]:
        return component_models.ComponentType.TEXT_INPUT

    @property
    def custom_id(self) -> str:
        return self._custom_id

    @property
    def label(self) -> str:
        return self._label

    @property
    def style(self) -> component_models.TextInputStyle:
        return self._style

    @property
    def placeholder(self) -> undefined.UndefinedOr[str]:
        return self._placeholder

    @property
    def value(self) -> undefined.UndefinedOr[str]:
        return self._value

    @property
    def required(self) -> undefined.UndefinedOr[bool]:
        return self._required

    @property
    def min_length(self) -> undefined.UndefinedOr[int]:
        return self._min_length

    @property
    def max_length(self) -> undefined.UndefinedOr[int]:
        return self._max_length

    def set_style(self, style: typing.Union[component_models.TextInputStyle, int], /) -> Self:
        self._style = component_models.TextInputStyle(style)
        return self

    def set_custom_id(self, custom_id: str, /) -> Self:
        self._custom_id = custom_id
        return self

    def set_label(self, label: str, /) -> Self:
        self._label = label
        return self

    def set_placeholder(self, placeholder: str, /) -> Self:
        self._placeholder = placeholder
        return self

    def set_value(self, value: str, /) -> Self:
        self._value = value
        return self

    def set_required(self, required: bool, /) -> Self:
        self._required = required
        return self

    def set_min_length(self, min_length: int, /) -> Self:
        self._min_length = min_length
        return self

    def set_max_length(self, max_length: int, /) -> Self:
        self._max_length = max_length
        return self

    def add_to_container(self) -> _ContainerProtoT:
        self._container.add_component(self)
        return self._container

    def build(self) -> typing.MutableMapping[str, typing.Any]:
        data = data_binding.JSONObjectBuilder()

        data["type"] = component_models.ComponentType.TEXT_INPUT
        data["style"] = self._style
        data["custom_id"] = self._custom_id
        data["label"] = self._label
        data.put("placeholder", self._placeholder)
        data.put("value", self._value)
        data.put("required", self._required)
        data.put("min_length", self._min_length)
        data.put("max_length", self._max_length)

        return data


@attr.define(kw_only=True, weakref_slot=False)
class MessageActionRowBuilder(special_endpoints.MessageActionRowBuilder):
    """Standard implementation of `hikari.api.special_endpoints.ActionRowBuilder`."""

    _components: typing.List[special_endpoints.ComponentBuilder] = attr.field(alias="components", factory=list)
    _stored_type: typing.Optional[component_models.ComponentType] = attr.field(default=None, init=False)

    @property
    def type(self) -> typing.Literal[component_models.ComponentType.ACTION_ROW]:
        return component_models.ComponentType.ACTION_ROW

    @property
    def components(self) -> typing.Sequence[special_endpoints.ComponentBuilder]:
        return self._components.copy()

    def _assert_can_add_type(self, type_: typing.Union[component_models.ComponentType, int], /) -> None:
        type_ = component_models.ComponentType(type_)
        if self._stored_type is not None and self._stored_type != type_:
            raise ValueError(
                f"{type_} component type cannot be added to a container which already holds {self._stored_type}"
            )

        self._stored_type = type_

    def add_component(self, component: special_endpoints.ComponentBuilder, /) -> Self:
        self._components.append(component)
        return self

    @typing.overload
    def add_button(
        self, style: component_models.InteractiveButtonTypesT, custom_id: str, /
    ) -> special_endpoints.InteractiveButtonBuilder[Self]:
        ...

    @typing.overload
    def add_button(
        self,
        style: typing.Literal[component_models.ButtonStyle.LINK, 5],
        url: str,
        /,
    ) -> special_endpoints.LinkButtonBuilder[Self]:
        ...

    @typing.overload
    def add_button(
        self,
        style: typing.Union[int, component_models.ButtonStyle],
        url_or_custom_id: str,
        /,
    ) -> typing.Union[special_endpoints.LinkButtonBuilder[Self], special_endpoints.InteractiveButtonBuilder[Self],]:
        ...

    def add_button(
        self,
        style: typing.Union[int, component_models.ButtonStyle],
        url_or_custom_id: str,
        /,
    ) -> typing.Union[special_endpoints.LinkButtonBuilder[Self], special_endpoints.InteractiveButtonBuilder[Self],]:
        self._assert_can_add_type(component_models.ComponentType.BUTTON)
        if style in component_models.InteractiveButtonTypes:
            return InteractiveButtonBuilder(container=self, style=style, custom_id=url_or_custom_id)

        return LinkButtonBuilder(container=self, style=style, url=url_or_custom_id)

    @typing.overload
    def add_select_menu(
        self,
        type_: typing.Literal[component_models.ComponentType.TEXT_SELECT_MENU, 3],
        custom_id: str,
        /,
    ) -> special_endpoints.TextSelectMenuBuilder[Self]:
        ...

    @typing.overload
    def add_select_menu(
        self,
        type_: typing.Literal[component_models.ComponentType.CHANNEL_SELECT_MENU, 8],
        custom_id: str,
        /,
    ) -> special_endpoints.ChannelSelectMenuBuilder[Self]:
        ...

    def add_select_menu(
        self,
        type_: typing.Union[component_models.ComponentType, int],
        custom_id: str,
        /,
    ) -> special_endpoints.SelectMenuBuilder[Self]:
        if type_ not in component_models.SelectMenuTypes:
            raise ValueError(f"{type_!r} is an invalid type option")

        self._assert_can_add_type(type_)

        if type_ == component_models.ComponentType.TEXT_SELECT_MENU:
            return TextSelectMenuBuilder(container=self, custom_id=custom_id)
        if type_ == component_models.ComponentType.CHANNEL_SELECT_MENU:
            return ChannelSelectMenuBuilder(container=self, custom_id=custom_id)

        return SelectMenuBuilder(container=self, type=type_, custom_id=custom_id)

    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {
            "type": component_models.ComponentType.ACTION_ROW,
            "components": [component.build() for component in self._components],
        }


@attr.define(kw_only=True, weakref_slot=False)
class ModalActionRowBuilder(special_endpoints.ModalActionRowBuilder):
    """Standard implementation of `hikari.api.special_endpoints.ActionRowBuilder`."""

    _components: typing.List[special_endpoints.ComponentBuilder] = attr.field(alias="components", factory=list)
    _stored_type: typing.Optional[component_models.ComponentType] = attr.field(
        alias="stored_type", init=False, default=None
    )

    @property
    def type(self) -> typing.Literal[component_models.ComponentType.ACTION_ROW]:
        return component_models.ComponentType.ACTION_ROW

    @property
    def components(self) -> typing.Sequence[special_endpoints.ComponentBuilder]:
        return self._components.copy()

    def _assert_can_add_type(self, type_: component_models.ComponentType, /) -> None:
        if self._stored_type is not None and self._stored_type != type_:
            raise ValueError(
                f"{type_} component type cannot be added to a container which already holds {self._stored_type}"
            )

        self._stored_type = type_

    def add_component(self, component: special_endpoints.ComponentBuilder, /) -> Self:
        self._components.append(component)
        return self

    def add_text_input(
        self,
        custom_id: str,
        label: str,
    ) -> special_endpoints.TextInputBuilder[Self]:
        self._assert_can_add_type(component_models.ComponentType.TEXT_INPUT)
        return TextInputBuilder(container=self, custom_id=custom_id, label=label)

    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {
            "type": component_models.ComponentType.ACTION_ROW,
            "components": [component.build() for component in self._components],
        }
