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
    "AutocompleteChoiceBuilder",
    "ChannelSelectMenuBuilder",
    "CommandBuilder",
    "ContextMenuCommandBuilder",
    "GuildBuilder",
    "InteractionAutocompleteBuilder",
    "InteractionDeferredBuilder",
    "InteractionMessageBuilder",
    "InteractionModalBuilder",
    "InteractiveButtonBuilder",
    "LinkButtonBuilder",
    "MessageActionRowBuilder",
    "ModalActionRowBuilder",
    "PollAnswerBuilder",
    "PollBuilder",
    "SelectMenuBuilder",
    "SelectOptionBuilder",
    "SlashCommandBuilder",
    "TextInputBuilder",
    "TextSelectMenuBuilder",
    "TypingIndicator",
)

import asyncio
import typing

import attrs

from hikari import channels
from hikari import colors
from hikari import commands
from hikari import components as component_models
from hikari import emojis
from hikari import errors
from hikari import files
from hikari import iterators
from hikari import locales
from hikari import messages
from hikari import polls
from hikari import snowflakes
from hikari import undefined
from hikari.api import special_endpoints
from hikari.interactions import base_interactions
from hikari.internal import attrs_extensions
from hikari.internal import data_binding
from hikari.internal import mentions
from hikari.internal import routes
from hikari.internal import time

if not typing.TYPE_CHECKING:
    # This is insanely hacky, but it is needed for ruff to not complain until it gets type inference
    from hikari.internal import typing_extensions


if typing.TYPE_CHECKING:
    import concurrent.futures
    import types

    import typing_extensions  # noqa: TC004
    from typing_extensions import Self

    from hikari import applications
    from hikari import audit_logs
    from hikari import embeds as embeds_
    from hikari import guilds
    from hikari import permissions as permissions_
    from hikari import scheduled_events
    from hikari import users
    from hikari import voices
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import rest as rest_api

    _T = typing.TypeVar("_T")

    class _RequestCallSig(typing.Protocol):
        async def __call__(
            self,
            compiled_route: routes.CompiledRoute,
            *,
            query: data_binding.StringMapBuilder | None = None,
            form_builder: data_binding.URLEncodedFormBuilder | None = None,
            json: data_binding.JSONObjectBuilder | data_binding.JSONArray | None = None,
            reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
            auth: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        ) -> None | data_binding.JSONObject | data_binding.JSONArray: ...

    _GuildThreadChannelT_co = typing.TypeVar(
        "_GuildThreadChannelT_co", bound=channels.GuildThreadChannel, covariant=True
    )

    class _ThreadDeserializeSig(typing.Protocol[_GuildThreadChannelT_co]):
        def __call__(
            self,
            payload: data_binding.JSONObject,
            /,
            *,
            guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
            member: undefined.UndefinedNoneOr[channels.ThreadMember] = undefined.UNDEFINED,
        ) -> _GuildThreadChannelT_co:
            raise NotImplementedError


_ParentT = typing.TypeVar("_ParentT")
_GuildThreadChannelT = typing.TypeVar("_GuildThreadChannelT", bound=channels.GuildThreadChannel)


@typing.final
class TypingIndicator(special_endpoints.TypingIndicator):
    """Result type of [`hikari.api.rest.RESTClient.trigger_typing`][].

    This is an object that can either be awaited like a coroutine to trigger
    the typing indicator once, or an async context manager to keep triggering
    the typing indicator repeatedly until the context finishes.

    !!! note
        This is a helper class that is used by [`hikari.api.rest.RESTClient`][].
        You should only ever need to use instances of this class that are
        produced by that API.
    """

    __slots__: typing.Sequence[str] = ("_request_call", "_rest_close_event", "_route", "_task", "_task_name")

    def __init__(
        self,
        request_call: _RequestCallSig,
        channel: snowflakes.SnowflakeishOr[channels.TextableChannel],
        rest_close_event: asyncio.Event,
    ) -> None:
        self._route = routes.POST_CHANNEL_TYPING.compile(channel=channel)
        self._request_call = request_call
        self._task_name = f"repeatedly trigger typing in {channel}"
        self._task: asyncio.Task[None] | None = None
        self._rest_close_event = rest_close_event

    @typing_extensions.override
    def __await__(self) -> typing.Generator[typing.Any, typing.Any, typing.Any]:
        return self._request_call(self._route).__await__()

    @typing_extensions.override
    async def __aenter__(self) -> None:
        if self._task is not None:
            msg = "Cannot enter a typing indicator context more than once"
            raise TypeError(msg)
        self._task = asyncio.create_task(self._keep_typing(), name=self._task_name)

    @typing_extensions.override
    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None
    ) -> None:
        # This will always be true, but this keeps MyPy quiet.
        if self._task is not None:
            self._task.cancel()

    # These are only included at runtime in-order to avoid the model being typed as a synchronous context manager.
    if not typing.TYPE_CHECKING:

        def __enter__(self) -> typing.NoReturn:
            # This is async only.
            cls = type(self)
            msg = f"{cls.__module__}.{cls.__qualname__} is async-only, did you mean 'async with'?"
            raise TypeError(msg) from None

        def __exit__(
            self, exc_type: type[Exception] | None, exc_val: Exception | None, exc_tb: types.TracebackType | None
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
                except asyncio.TimeoutError:  # noqa: PERF203
                    pass

        except (asyncio.CancelledError, errors.ComponentStateConflictError):
            pass


class ChannelRepositioner(special_endpoints.ChannelRepositioner):
    __slots__: typing.Sequence[str] = ("_guild", "_request_call", "_channels")

    def __init__(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        request_call: _RequestCallSig,
        *,
        positions: typing.Mapping[int, snowflakes.SnowflakeishOr[channels.GuildChannel]] = {},
    ):
        self._guild = guild
        self._request_call = request_call
        self._channels = [RepositionChannelHelper(channel=channel, position=pos) for pos, channel in positions.items()]

    def reposition(
        self,
        position: int,
        channel: snowflakes.SnowflakeishOr[channels.GuildChannel],
        *,
        lock_permissions: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        parent: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels.GuildCategory]] = undefined.UNDEFINED,
    ) -> Self:
        self._channels.append(
            RepositionChannelHelper(
                channel=channel, position=position, lock_permissions=lock_permissions, parent=parent
            )
        )
        return self

    def __await__(self) -> typing.Generator[typing.Any, typing.Any, typing.Any]:
        route = routes.PATCH_GUILD_CHANNELS.compile(guild=self._guild)
        body = []
        for channel in self._channels:
            channel_payload = data_binding.JSONObjectBuilder()
            channel_payload.put_snowflake("id", channel.channel)
            channel_payload.put("position", channel.position)
            channel_payload.put("lock_permissions", channel.lock_permissions)
            channel_payload.put_snowflake("parent_id", channel.parent)
            body.append(channel_payload)
        return self._request_call(route, json=body).__await__()


@attrs.define(kw_only=True, weakref_slot=False)
class RepositionChannelHelper:
    channel: snowflakes.SnowflakeishOr[channels.GuildChannel] = attrs.field(repr=True)

    position: int = attrs.field(repr=True)

    lock_permissions: undefined.UndefinedOr[bool] = attrs.field(repr=True, default=undefined.UNDEFINED)

    parent: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels.GuildCategory]] = attrs.field(
        repr=True, default=undefined.UNDEFINED
    )


# As a note, slotting allows us to override the settable properties while staying within the interface's spec.
@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class GuildBuilder(special_endpoints.GuildBuilder):
    """Result type of [`hikari.api.rest.RESTClient.guild_builder`][].

    This is used to create a guild in a tidy way using the HTTP API, since
    the logic behind creating a guild on an API level is somewhat confusing
    and detailed.

    !!! note
        If you call [`hikari.api.special_endpoints.GuildBuilder.add_role`][], the default roles provided by Discord will
        be created. This also applies to the `add_` functions for
        text channels/voice channels/categories.

    !!! note
        Functions that return a [`hikari.snowflakes.Snowflake`][] do
        **not** provide the final ID that the object will have once the
        API call is made. The returned IDs are only able to be used to
        re-reference particular objects while building the guild format
        to allow for the creation of channels within categories,
        and to provide permission overwrites.

    Examples
    --------
    Creating an empty guild:

    ```py
    guild = await rest.guild_builder("My Server!").create()
    ```

    Creating a guild with an icon:

    ```py
    from hikari.files import WebResourceStream

    guild_builder = rest.guild_builder("My Server!")
    guild_builder.icon = WebResourceStream("cat.png", "http://...")
    guild = await guild_builder.create()
    ```

    Adding roles to your guild:

    ```py
    from hikari.permissions import Permissions

    guild_builder = rest.guild_builder("My Server!")

    everyone_role_id = guild_builder.add_role("@everyone")
    admin_role_id = guild_builder.add_role(
        "Admins", permissions=Permissions.ADMINISTRATOR
    )

    await guild_builder.create()
    ```

    !!! warning
        The first role must always be the `@everyone` role.

    Adding a text channel to your guild:

    ```py
    guild_builder = rest.guild_builder("My Server!")

    category_id = guild_builder.add_category("My safe place")
    channel_id = guild_builder.add_text_channel("general", parent_id=category_id)

    await guild_builder.create()
    ```
    """

    # Required arguments.
    _entity_factory: entity_factory_.EntityFactory = attrs.field(
        alias="entity_factory", metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    _executor: concurrent.futures.Executor | None = attrs.field(
        alias="executor", metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    _name: str = attrs.field(alias="name")
    _request_call: _RequestCallSig = attrs.field(alias="request_call", metadata={attrs_extensions.SKIP_DEEP_COPY: True})

    # Optional arguments.
    default_message_notifications: undefined.UndefinedOr[guilds.GuildMessageNotificationsLevel] = attrs.field(
        default=undefined.UNDEFINED
    )
    explicit_content_filter_level: undefined.UndefinedOr[guilds.GuildExplicitContentFilterLevel] = attrs.field(
        default=undefined.UNDEFINED
    )
    icon: undefined.UndefinedOr[files.Resourceish] = attrs.field(default=undefined.UNDEFINED)
    verification_level: undefined.UndefinedOr[guilds.GuildVerificationLevel | int] = attrs.field(
        default=undefined.UNDEFINED
    )

    # Non-arguments
    _channels: typing.MutableSequence[data_binding.JSONObject] = attrs.field(factory=list, init=False)
    _counter: int = attrs.field(default=0, init=False)
    _roles: typing.MutableSequence[data_binding.JSONObject] = attrs.field(factory=list, init=False)

    @property
    @typing_extensions.override
    def name(self) -> str:
        return self._name

    @typing_extensions.override
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

    @typing_extensions.override
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
            msg = "Cannot specify 'color' and 'colour' together."
            raise TypeError(msg)

        if len(self._roles) == 0:
            if name != "@everyone":
                msg = "First role must always be the '@everyone' role"
                raise ValueError(msg)
            if not undefined.all_undefined(color, colour, hoist, mentionable, position):
                msg = "Cannot pass 'color', 'colour', 'hoist', 'mentionable' nor 'position' to the '@everyone' role."
                raise ValueError(msg)

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

    @typing_extensions.override
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

    @typing_extensions.override
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

    @typing_extensions.override
    def add_voice_channel(
        self,
        name: str,
        /,
        *,
        parent_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        video_quality_mode: undefined.UndefinedOr[channels.VideoQualityMode | int] = undefined.UNDEFINED,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Collection[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        region: undefined.UndefinedNoneOr[voices.VoiceRegion | str],
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

    @typing_extensions.override
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
        region: undefined.UndefinedNoneOr[voices.VoiceRegion | str],
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

    __slots__: typing.Sequence[str] = ("_direction", "_entity_factory", "_first_id", "_request_call", "_route")

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

    @typing_extensions.override
    async def _next_chunk(self) -> typing.Generator[messages.Message, typing.Any, None] | None:
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

    __slots__: typing.Sequence[str] = ("_entity_factory", "_first_id", "_request_call", "_route")

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

    @typing_extensions.override
    async def _next_chunk(self) -> typing.Generator[users.User, typing.Any, None] | None:
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

    __slots__: typing.Sequence[str] = ("_entity_factory", "_first_id", "_newest_first", "_request_call", "_route")

    def __init__(
        self,
        entity_factory: entity_factory_.EntityFactory,
        request_call: _RequestCallSig,
        *,
        newest_first: bool,
        first_id: str,
    ) -> None:
        super().__init__()
        self._entity_factory = entity_factory
        self._newest_first = newest_first
        self._request_call = request_call
        self._first_id = first_id
        self._route = routes.GET_MY_GUILDS.compile()

    @typing_extensions.override
    async def _next_chunk(self) -> typing.Generator[applications.OwnGuild, typing.Any, None] | None:
        query = data_binding.StringMapBuilder()
        query.put("with_counts", True)
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
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
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

    @typing_extensions.override
    async def _next_chunk(self) -> typing.Generator[guilds.GuildBan, typing.Any, None] | None:
        query = data_binding.StringMapBuilder()
        query.put("before" if self._newest_first else "after", self._first_id)
        query.put("limit", 1000)

        chunk = await self._request_call(compiled_route=self._route, query=query)
        assert isinstance(chunk, list)

        if not chunk:
            return None

        if self._newest_first:
            # These are always returned in ascending order by [`.user.id`][].
            chunk.reverse()

        self._first_id = chunk[-1]["user"]["id"]
        return (self._entity_factory.deserialize_guild_member_ban(b) for b in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class MemberIterator(iterators.BufferedLazyIterator["guilds.Member"]):
    """Implementation of an iterator for retrieving members in a guild."""

    __slots__: typing.Sequence[str] = ("_entity_factory", "_first_id", "_guild_id", "_request_call", "_route")

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

    @typing_extensions.override
    async def _next_chunk(self) -> typing.Generator[guilds.Member, typing.Any, None] | None:
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
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        event: snowflakes.SnowflakeishOr[scheduled_events.ScheduledEvent],
        *,
        first_id: str,
        newest_first: bool,
    ) -> None:
        super().__init__()
        self._entity_factory = entity_factory
        self._first_id = first_id
        self._guild_id = snowflakes.Snowflake(guild)
        self._newest_first = newest_first
        self._request_call = request_call
        self._route = routes.GET_GUILD_SCHEDULED_EVENT_USERS.compile(guild=guild, scheduled_event=event)

    @typing_extensions.override
    async def _next_chunk(self) -> typing.Generator[scheduled_events.ScheduledEventUser, typing.Any, None] | None:
        query = data_binding.StringMapBuilder()
        query.put("before" if self._newest_first else "after", self._first_id)
        query.put("limit", 100)
        query.put("with_member", True)

        chunk = await self._request_call(compiled_route=self._route, query=query)
        assert isinstance(chunk, list)

        if not chunk:
            return None

        if self._newest_first:
            # These are always returned in ascending order by [`.user.id`][].
            chunk.reverse()

        self._first_id = chunk[-1]["user"]["id"]
        return (self._entity_factory.deserialize_scheduled_event_user(u, guild_id=self._guild_id) for u in chunk)


# We use an explicit forward reference for this, since this breaks potential
# circular import issues (once the file has executed, using those resources is
# not an issue for us).
class AuditLogIterator(iterators.LazyIterator["audit_logs.AuditLog"]):
    """Iterator implementation for an audit log."""

    __slots__: typing.Sequence[str] = (
        "_action_type",
        "_entity_factory",
        "_first_id",
        "_guild_id",
        "_request_call",
        "_route",
        "_user",
    )

    def __init__(
        self,
        entity_factory: entity_factory_.EntityFactory,
        request_call: _RequestCallSig,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        before: undefined.UndefinedOr[str],
        user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]],
        action_type: undefined.UndefinedOr[audit_logs.AuditLogEventType | int],
    ) -> None:
        self._action_type = action_type
        self._entity_factory = entity_factory
        self._first_id = before
        self._guild_id = snowflakes.Snowflake(guild)
        self._request_call = request_call
        self._route = routes.GET_GUILD_AUDIT_LOGS.compile(guild=guild)
        self._user = user

    @typing_extensions.override
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
        deserialize: _ThreadDeserializeSig[_GuildThreadChannelT],
        entity_factory: entity_factory_.EntityFactory,
        request_call: _RequestCallSig,
        route: routes.CompiledRoute,
        before: undefined.UndefinedOr[str],
        *,
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

    @typing_extensions.override
    async def _next_chunk(self) -> typing.Generator[_GuildThreadChannelT, typing.Any, None] | None:
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
    callback: typing.Callable[[data_binding.JSONObject], _T], data: data_binding.JSONObject | None
) -> _T | None:
    if data:
        return callback(data)

    return None


@attrs_extensions.with_copy
@attrs.define(kw_only=False, weakref_slot=False)
class AutocompleteChoiceBuilder(special_endpoints.AutocompleteChoiceBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.AutocompleteChoiceBuilder`][]."""

    _name: str = attrs.field(alias="name")
    _value: int | str | float = attrs.field(alias="value")

    @property
    @typing_extensions.override
    def name(self) -> str:
        return self._name

    @property
    @typing_extensions.override
    def value(self) -> int | str | float:
        return self._value

    @typing_extensions.override
    def set_name(self, name: str, /) -> Self:
        self._name = name
        return self

    @typing_extensions.override
    def set_value(self, value: float | str, /) -> Self:
        self._value = value
        return self

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {"name": self._name, "value": self._value}


@attrs_extensions.with_copy
@attrs.define(weakref_slot=False)
class InteractionAutocompleteBuilder(special_endpoints.InteractionAutocompleteBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.InteractionAutocompleteBuilder`][]."""

    _choices: typing.Sequence[special_endpoints.AutocompleteChoiceBuilder] = attrs.field(factory=tuple)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[base_interactions.ResponseType.AUTOCOMPLETE]:
        return base_interactions.ResponseType.AUTOCOMPLETE

    @property
    @typing_extensions.override
    def choices(self) -> typing.Sequence[special_endpoints.AutocompleteChoiceBuilder]:
        return self._choices

    @typing_extensions.override
    def set_choices(self, choices: typing.Sequence[special_endpoints.AutocompleteChoiceBuilder], /) -> Self:
        self._choices = choices
        return self

    @typing_extensions.override
    def build(
        self, _: entity_factory_.EntityFactory, /
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        return {"type": self.type, "data": {"choices": [choice.build() for choice in self._choices]}}, ()


@attrs_extensions.with_copy
@attrs.define(kw_only=False, weakref_slot=False)
class InteractionDeferredBuilder(special_endpoints.InteractionDeferredBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.InteractionDeferredBuilder`][].

    Parameters
    ----------
    type : hikari.interactions.base_interactions.DeferredResponseTypesT
        The type of interaction response this is.
    """

    # Required arguments.
    _type: base_interactions.DeferredResponseTypesT = attrs.field(
        alias="type",
        converter=base_interactions.ResponseType,
        validator=attrs.validators.in_(base_interactions.DEFERRED_RESPONSE_TYPES),
    )

    _flags: undefined.UndefinedType | int | messages.MessageFlag = attrs.field(
        alias="flags", default=undefined.UNDEFINED, kw_only=True
    )

    @property
    @typing_extensions.override
    def type(self) -> base_interactions.DeferredResponseTypesT:
        return self._type

    @property
    @typing_extensions.override
    def flags(self) -> undefined.UndefinedType | int | messages.MessageFlag:
        return self._flags

    @typing_extensions.override
    def set_flags(self, flags: undefined.UndefinedType | int | messages.MessageFlag, /) -> Self:
        self._flags = flags
        return self

    @typing_extensions.override
    def build(
        self, _: entity_factory_.EntityFactory, /
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        if self._flags is not undefined.UNDEFINED:
            return {"type": self._type, "data": {"flags": self._flags}}, ()

        return {"type": self._type}, ()


@attrs_extensions.with_copy
@attrs.define(kw_only=False, weakref_slot=False)
class InteractionMessageBuilder(special_endpoints.InteractionMessageBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.InteractionMessageBuilder`][].

    Parameters
    ----------
    type : hikari.interactions.base_interactions.MessageResponseTypesT
        The type of interaction response this is.
    content : hikari.undefined.UndefinedOr[str]
        The content of this response, if supplied. This follows the same rules
        as "content" on create message.
    """

    # Required arguments.
    _type: base_interactions.MessageResponseTypesT = attrs.field(
        alias="type",
        converter=base_interactions.ResponseType,
        validator=attrs.validators.in_(base_interactions.MESSAGE_RESPONSE_TYPES),
    )

    # Not-required arguments.
    _content: undefined.UndefinedNoneOr[str] = attrs.field(alias="content", default=undefined.UNDEFINED)

    # Key-word only not-required arguments.
    _flags: int | messages.MessageFlag | undefined.UndefinedType = attrs.field(
        alias="flags", default=undefined.UNDEFINED, kw_only=True
    )
    _is_tts: undefined.UndefinedOr[bool] = attrs.field(alias="is_tts", default=undefined.UNDEFINED, kw_only=True)
    _mentions_everyone: undefined.UndefinedOr[bool] = attrs.field(
        alias="mentions_everyone", default=undefined.UNDEFINED, kw_only=True
    )
    _role_mentions: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole] | bool] = attrs.field(
        alias="role_mentions", default=undefined.UNDEFINED, kw_only=True
    )
    _user_mentions: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[users.PartialUser] | bool] = attrs.field(
        alias="user_mentions", default=undefined.UNDEFINED, kw_only=True
    )
    _poll: undefined.UndefinedOr[special_endpoints.PollBuilder] = attrs.field(
        alias="poll", default=undefined.UNDEFINED, kw_only=True
    )
    _attachments: undefined.UndefinedNoneOr[list[files.Resourceish]] = attrs.field(
        alias="attachments", default=undefined.UNDEFINED, kw_only=True
    )
    _components: undefined.UndefinedNoneOr[list[special_endpoints.ComponentBuilder]] = attrs.field(
        alias="components", default=undefined.UNDEFINED, kw_only=True
    )
    _embeds: undefined.UndefinedNoneOr[list[embeds_.Embed]] = attrs.field(
        alias="embeds", default=undefined.UNDEFINED, kw_only=True
    )

    @property
    @typing_extensions.override
    def attachments(self) -> undefined.UndefinedNoneOr[typing.Sequence[files.Resourceish]]:
        return self._attachments.copy() if self._attachments else self._attachments

    @property
    @typing_extensions.override
    def content(self) -> undefined.UndefinedNoneOr[str]:
        return self._content

    @property
    @typing_extensions.override
    def components(self) -> undefined.UndefinedNoneOr[typing.Sequence[special_endpoints.ComponentBuilder]]:
        return self._components.copy() if self._components else self._components

    @property
    @typing_extensions.override
    def embeds(self) -> undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]]:
        return self._embeds.copy() if self._embeds else self._embeds

    @property
    @typing_extensions.override
    def flags(self) -> undefined.UndefinedType | int | messages.MessageFlag:
        return self._flags

    @property
    @typing_extensions.override
    def is_tts(self) -> undefined.UndefinedOr[bool]:
        return self._is_tts

    @property
    @typing_extensions.override
    def mentions_everyone(self) -> undefined.UndefinedOr[bool]:
        return self._mentions_everyone

    @property
    @typing_extensions.override
    def role_mentions(self) -> undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole] | bool]:
        return self._role_mentions

    @property
    @typing_extensions.override
    def type(self) -> base_interactions.MessageResponseTypesT:
        return self._type

    @property
    @typing_extensions.override
    def user_mentions(self) -> undefined.UndefinedOr[snowflakes.SnowflakeishSequence[users.PartialUser] | bool]:
        return self._user_mentions

    @property
    @typing_extensions.override
    def poll(self) -> undefined.UndefinedOr[special_endpoints.PollBuilder]:
        return self._poll

    @typing_extensions.override
    def add_attachment(self, attachment: files.Resourceish, /) -> Self:
        if not self._attachments:
            self._attachments = []

        self._attachments.append(attachment)
        return self

    @typing_extensions.override
    def clear_attachments(self, /) -> Self:
        self._attachments = None
        return self

    @typing_extensions.override
    def add_component(self, component: special_endpoints.ComponentBuilder, /) -> Self:
        if not self._components:
            self._components = []

        self._components.append(component)
        return self

    @typing_extensions.override
    def clear_components(self, /) -> Self:
        self._components = None
        return self

    @typing_extensions.override
    def add_embed(self, embed: embeds_.Embed, /) -> Self:
        if not self._embeds:
            self._embeds = []

        self._embeds.append(embed)
        return self

    @typing_extensions.override
    def clear_embeds(self, /) -> Self:
        self._embeds = None
        return self

    @typing_extensions.override
    def set_content(self, content: undefined.UndefinedOr[str], /) -> Self:
        self._content = str(content) if content is not undefined.UNDEFINED else undefined.UNDEFINED
        return self

    def clear_content(self, /) -> Self:
        self._content = None
        return self

    @typing_extensions.override
    def set_flags(self, flags: undefined.UndefinedType | int | messages.MessageFlag, /) -> Self:
        self._flags = flags
        return self

    @typing_extensions.override
    def set_tts(self, tts: undefined.UndefinedOr[bool], /) -> Self:
        self._is_tts = tts
        return self

    @typing_extensions.override
    def set_mentions_everyone(self, state: undefined.UndefinedOr[bool] = undefined.UNDEFINED, /) -> Self:
        self._mentions_everyone = state
        return self

    @typing_extensions.override
    def set_role_mentions(
        self,
        role_mentions: undefined.UndefinedOr[
            snowflakes.SnowflakeishSequence[guilds.PartialRole] | bool
        ] = undefined.UNDEFINED,
        /,
    ) -> Self:
        self._role_mentions = role_mentions
        return self

    @typing_extensions.override
    def set_user_mentions(
        self,
        user_mentions: undefined.UndefinedOr[
            snowflakes.SnowflakeishSequence[users.PartialUser] | bool
        ] = undefined.UNDEFINED,
        /,
    ) -> Self:
        self._user_mentions = user_mentions
        return self

    @typing_extensions.override
    def set_poll(self, poll: undefined.UndefinedOr[special_endpoints.PollBuilder], /) -> Self:
        self._poll = poll
        return self

    @typing_extensions.override
    def build(
        self, entity_factory: entity_factory_.EntityFactory, /
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
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

        if self._embeds:
            embeds: list[data_binding.JSONObject] = []
            for embed, attachments in map(entity_factory.serialize_embed, self._embeds):
                final_attachments.extend(attachments)
                embeds.append(embed)

            data["embeds"] = embeds
        elif self._embeds is None:
            data.put("embeds", None)

        if self._components:
            data.put_array("components", self._components, conversion=lambda component: component.build())
        elif self._components is None:
            data.put("components", None)

        data.put("flags", self.flags)
        data.put("tts", self.is_tts)
        data.put("poll", self.poll, conversion=lambda poll: poll.build())

        if (
            not undefined.all_undefined(self.mentions_everyone, self.user_mentions, self.role_mentions)
            or self.type is base_interactions.ResponseType.MESSAGE_CREATE
        ):
            data["allowed_mentions"] = mentions.generate_allowed_mentions(
                self.mentions_everyone, undefined.UNDEFINED, self.user_mentions, self.role_mentions
            )

        return {"type": self._type, "data": data}, final_attachments


@attrs.define(kw_only=False, weakref_slot=False)
class InteractionModalBuilder(special_endpoints.InteractionModalBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.InteractionModalBuilder`][]."""

    _title: str = attrs.field(alias="title")
    _custom_id: str = attrs.field(alias="custom_id")
    _components: list[special_endpoints.ComponentBuilder] = attrs.field(alias="components", factory=list)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[base_interactions.ResponseType.MODAL]:
        return base_interactions.ResponseType.MODAL

    @property
    @typing_extensions.override
    def title(self) -> str:
        return self._title

    @property
    @typing_extensions.override
    def custom_id(self) -> str:
        return self._custom_id

    @property
    @typing_extensions.override
    def components(self) -> typing.Sequence[special_endpoints.ComponentBuilder]:
        return self._components

    @typing_extensions.override
    def set_title(self, title: str, /) -> Self:
        self._title = title
        return self

    @typing_extensions.override
    def set_custom_id(self, custom_id: str, /) -> Self:
        self._custom_id = custom_id
        return self

    @typing_extensions.override
    def add_component(self, component: special_endpoints.ComponentBuilder, /) -> Self:
        self._components.append(component)
        return self

    @typing_extensions.override
    def build(
        self, entity_factory: entity_factory_.EntityFactory, /
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        data = data_binding.JSONObjectBuilder()
        data.put("title", self._title)
        data.put("custom_id", self._custom_id)
        data.put_array("components", self._components, conversion=lambda component: component.build())

        return {"type": self.type, "data": data}, ()


@attrs.define(kw_only=False, weakref_slot=False)
class InteractionPremiumRequiredBuilder(special_endpoints.InteractionPremiumRequiredBuilder):
    """Standard implementation of `hikari.api.special_endpoints.InteractionPremiumRequiredBuilder`."""

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[base_interactions.ResponseType.PREMIUM_REQUIRED]:
        return base_interactions.ResponseType.PREMIUM_REQUIRED

    @typing_extensions.override
    def build(
        self, entity_factory: entity_factory_.EntityFactory, /
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        return {"type": self.type}, ()


@attrs.define(kw_only=False, weakref_slot=False)
class CommandBuilder(special_endpoints.CommandBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.CommandBuilder`][]."""

    _name: str = attrs.field(alias="name")

    _id: undefined.UndefinedOr[snowflakes.Snowflake] = attrs.field(
        alias="id", default=undefined.UNDEFINED, kw_only=True
    )

    _default_member_permissions: undefined.UndefinedType | int | permissions_.Permissions = attrs.field(
        alias="default_member_permissions", default=undefined.UNDEFINED, kw_only=True
    )

    _is_nsfw: undefined.UndefinedOr[bool] = attrs.field(alias="is_nsfw", default=undefined.UNDEFINED, kw_only=True)

    _name_localizations: typing.Mapping[locales.Locale | str, str] = attrs.field(
        alias="name_localizations", factory=dict, kw_only=True
    )

    _integration_types: undefined.UndefinedOr[typing.Sequence[applications.ApplicationIntegrationType]] = attrs.field(
        alias="integration_types", default=undefined.UNDEFINED, kw_only=True
    )

    _context_types: undefined.UndefinedOr[typing.Sequence[applications.ApplicationContextType]] = attrs.field(
        alias="context_types", default=undefined.UNDEFINED, kw_only=True
    )

    @property
    @typing_extensions.override
    def id(self) -> undefined.UndefinedOr[snowflakes.Snowflake]:
        return self._id

    @property
    @typing_extensions.override
    def default_member_permissions(self) -> undefined.UndefinedType | permissions_.Permissions | int:
        return self._default_member_permissions

    @property
    @typing_extensions.override
    def is_nsfw(self) -> undefined.UndefinedOr[bool]:
        return self._is_nsfw

    @property
    @typing_extensions.override
    def name(self) -> str:
        return self._name

    @property
    @typing_extensions.override
    def integration_types(self) -> undefined.UndefinedOr[typing.Sequence[applications.ApplicationIntegrationType]]:
        return self._integration_types

    @property
    @typing_extensions.override
    def context_types(self) -> undefined.UndefinedOr[typing.Sequence[applications.ApplicationContextType]]:
        return self._context_types

    @property
    @typing_extensions.override
    def name_localizations(self) -> typing.Mapping[locales.Locale | str, str]:
        return self._name_localizations

    @typing_extensions.override
    def set_name(self, name: str, /) -> Self:
        self._name = name
        return self

    @typing_extensions.override
    def set_id(self, id_: undefined.UndefinedOr[snowflakes.Snowflakeish], /) -> Self:
        self._id = snowflakes.Snowflake(id_) if id_ is not undefined.UNDEFINED else undefined.UNDEFINED
        return self

    @typing_extensions.override
    def set_default_member_permissions(
        self, default_member_permissions: undefined.UndefinedType | int | permissions_.Permissions, /
    ) -> Self:
        self._default_member_permissions = default_member_permissions
        return self

    @typing_extensions.override
    def set_is_nsfw(self, state: undefined.UndefinedOr[bool], /) -> Self:
        self._is_nsfw = state
        return self

    @typing_extensions.override
    def set_integration_types(
        self, integration_types: undefined.UndefinedOr[typing.Sequence[applications.ApplicationIntegrationType]]
    ) -> Self:
        self._integration_types = integration_types
        return self

    @typing_extensions.override
    def set_context_types(
        self, context_types: undefined.UndefinedOr[typing.Sequence[applications.ApplicationContextType]]
    ) -> Self:
        self._context_types = context_types
        return self

    @typing_extensions.override
    def set_name_localizations(self, name_localizations: typing.Mapping[locales.Locale | str, str], /) -> Self:
        self._name_localizations = name_localizations
        return self

    @typing_extensions.override
    def build(self, _: entity_factory_.EntityFactory, /) -> typing.MutableMapping[str, typing.Any]:
        data = data_binding.JSONObjectBuilder()
        data["name"] = self._name
        data["type"] = self.type
        data.put_snowflake("id", self._id)
        data.put("name_localizations", self._name_localizations)
        data.put("nsfw", self._is_nsfw)
        data.put_array("integration_types", self._integration_types)
        data.put_array("contexts", self._context_types)

        # Discord considers 0 the same thing as ADMINISTRATORS, but we make it nicer to work with
        # by using it correctly.
        if self._default_member_permissions != 0:
            data.put("default_member_permissions", self._default_member_permissions)

        return data


@attrs_extensions.with_copy
@attrs.define(kw_only=False, weakref_slot=False)
class SlashCommandBuilder(CommandBuilder, special_endpoints.SlashCommandBuilder):
    """Builder class for slash commands."""

    _description: str = attrs.field(alias="description")
    _options: list[commands.CommandOption] = attrs.field(alias="options", factory=list, kw_only=True)
    _description_localizations: typing.Mapping[locales.Locale | str, str] = attrs.field(
        alias="description_localizations", factory=dict, kw_only=True
    )

    @property
    @typing_extensions.override
    def description(self) -> str:
        return self._description

    @property
    @typing_extensions.override
    def type(self) -> commands.CommandType:
        return commands.CommandType.SLASH

    @property
    @typing_extensions.override
    def options(self) -> typing.Sequence[commands.CommandOption]:
        return self._options.copy()

    @property
    @typing_extensions.override
    def description_localizations(self) -> typing.Mapping[locales.Locale | str, str]:
        return self._description_localizations

    @typing_extensions.override
    def set_description(self, description: str, /) -> Self:
        self._description = description
        return self

    @typing_extensions.override
    def set_description_localizations(
        self, description_localizations: typing.Mapping[locales.Locale | str, str], /
    ) -> Self:
        self._description_localizations = description_localizations
        return self

    @typing_extensions.override
    def add_option(self, option: commands.CommandOption) -> Self:
        self._options.append(option)
        return self

    @typing_extensions.override
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

    @typing_extensions.override
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
            nsfw=self._is_nsfw,
        )


@attrs_extensions.with_copy
@attrs.define(kw_only=False, weakref_slot=False)
class ContextMenuCommandBuilder(CommandBuilder, special_endpoints.ContextMenuCommandBuilder):
    """Builder class for context menu commands."""

    _type: commands.CommandType = attrs.field(alias="type")
    # name is redeclared here to ensure type is before it in the initializer's args.
    _name: str = attrs.field(alias="name")

    @property
    @typing_extensions.override
    def type(self) -> commands.CommandType:
        return self._type

    @typing_extensions.override
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
            nsfw=self.is_nsfw,
        )


def _build_emoji(
    emoji: snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType = undefined.UNDEFINED,
) -> tuple[undefined.UndefinedOr[str], undefined.UndefinedOr[str]]:
    """Build an emoji into the format accepted in buttons.

    Parameters
    ----------
    emoji
        The ID, object or raw string of an emoji to set on a component.

    Returns
    -------
    typing.Tuple[hikari.undefined.UndefinedOr[str], hikari.undefined.UndefinedOr[str]]
        A union of the custom emoji's id if defined (index 0) or the unicode
        emoji's string representation (index 1).
    """
    # Since these builder classes may be reused, this method should be called when the builder is being constructed.
    if emoji is not undefined.UNDEFINED:
        if isinstance(emoji, (int, emojis.CustomEmoji)):
            return str(int(emoji)), undefined.UNDEFINED

        return undefined.UNDEFINED, str(emoji)

    return undefined.UNDEFINED, undefined.UNDEFINED


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class _ButtonBuilder(special_endpoints.ButtonBuilder):
    _style: int | component_models.ButtonStyle = attrs.field(alias="style")
    _custom_id: undefined.UndefinedOr[str] = attrs.field()
    _url: undefined.UndefinedOr[str] = attrs.field()
    _emoji: snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType = attrs.field(
        alias="emoji", default=undefined.UNDEFINED
    )
    _emoji_id: undefined.UndefinedOr[str] = attrs.field(init=False, default=undefined.UNDEFINED)
    _emoji_name: undefined.UndefinedOr[str] = attrs.field(init=False, default=undefined.UNDEFINED)
    _label: undefined.UndefinedOr[str] = attrs.field(alias="label", default=undefined.UNDEFINED)
    _is_disabled: bool = attrs.field(alias="is_disabled", default=False)

    def __attrs_post_init__(self) -> None:
        self._emoji_id, self._emoji_name = _build_emoji(self._emoji)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[component_models.ComponentType.BUTTON]:
        return component_models.ComponentType.BUTTON

    @property
    @typing_extensions.override
    def style(self) -> int | component_models.ButtonStyle:
        return self._style

    @property
    @typing_extensions.override
    def emoji(self) -> snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType:
        return self._emoji

    @property
    @typing_extensions.override
    def label(self) -> undefined.UndefinedOr[str]:
        return self._label

    @property
    @typing_extensions.override
    def is_disabled(self) -> bool:
        return self._is_disabled

    @typing_extensions.override
    def set_emoji(self, emoji: snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType, /) -> Self:
        self._emoji_id, self._emoji_name = _build_emoji(emoji)
        self._emoji = emoji
        return self

    @typing_extensions.override
    def set_label(self, label: undefined.UndefinedOr[str], /) -> Self:
        self._label = label
        return self

    @typing_extensions.override
    def set_is_disabled(self, state: bool, /) -> Self:
        self._is_disabled = state
        return self

    @typing_extensions.override
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


@attrs.define(kw_only=True, weakref_slot=False)
class LinkButtonBuilder(_ButtonBuilder, special_endpoints.LinkButtonBuilder):
    """Builder class for link buttons."""

    _custom_id: undefined.UndefinedType = attrs.field(init=False, default=undefined.UNDEFINED)
    _style: typing.Literal[component_models.ButtonStyle.LINK] = attrs.field(
        init=False, default=component_models.ButtonStyle.LINK
    )
    _url: str = attrs.field(alias="url")

    @property
    @typing_extensions.override
    def url(self) -> str:
        return self._url


@attrs.define(kw_only=True, weakref_slot=False)
class InteractiveButtonBuilder(_ButtonBuilder, special_endpoints.InteractiveButtonBuilder):
    """Builder class for interactive buttons."""

    _custom_id: str = attrs.field(alias="custom_id")
    _url: undefined.UndefinedType = attrs.field(init=False, default=undefined.UNDEFINED)

    @property
    @typing_extensions.override
    def custom_id(self) -> str:
        return self._custom_id

    @typing_extensions.override
    def set_custom_id(self, custom_id: str, /) -> Self:
        self._custom_id = custom_id
        return self


@attrs_extensions.with_copy
@attrs.define(weakref_slot=False)
class SelectOptionBuilder(special_endpoints.SelectOptionBuilder):
    """Builder class for select menu options."""

    _label: str = attrs.field(alias="label")
    _value: str = attrs.field(alias="value")
    _description: undefined.UndefinedOr[str] = attrs.field(
        alias="description", default=undefined.UNDEFINED, kw_only=True
    )
    _emoji: snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType = attrs.field(
        alias="emoji", default=undefined.UNDEFINED, kw_only=True
    )
    _emoji_id: undefined.UndefinedOr[str] = attrs.field(init=False, default=undefined.UNDEFINED)
    _emoji_name: undefined.UndefinedOr[str] = attrs.field(init=False, default=undefined.UNDEFINED)
    _is_default: bool = attrs.field(alias="is_default", default=False, kw_only=True)

    def __attrs_post_init__(self) -> None:
        self._emoji_id, self._emoji_name = _build_emoji(self._emoji)

    @property
    @typing_extensions.override
    def label(self) -> str:
        return self._label

    @property
    @typing_extensions.override
    def value(self) -> str:
        return self._value

    @property
    @typing_extensions.override
    def description(self) -> undefined.UndefinedOr[str]:
        return self._description

    @property
    @typing_extensions.override
    def emoji(self) -> snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType:
        return self._emoji

    @property
    @typing_extensions.override
    def is_default(self) -> bool:
        return self._is_default

    @typing_extensions.override
    def set_label(self, label: str, /) -> Self:
        self._label = label
        return self

    @typing_extensions.override
    def set_value(self, value: str, /) -> Self:
        self._value = value
        return self

    @typing_extensions.override
    def set_description(self, value: undefined.UndefinedOr[str], /) -> Self:
        self._description = value
        return self

    @typing_extensions.override
    def set_emoji(self, emoji: snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType, /) -> Self:
        self._emoji_id, self._emoji_name = _build_emoji(emoji)
        self._emoji = emoji
        return self

    @typing_extensions.override
    def set_is_default(self, state: bool, /) -> Self:
        self._is_default = state
        return self

    @typing_extensions.override
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


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class SelectMenuBuilder(special_endpoints.SelectMenuBuilder):
    """Builder class for select menus."""

    _type: component_models.ComponentType | int = attrs.field(alias="type")
    _custom_id: str = attrs.field(alias="custom_id")
    _placeholder: undefined.UndefinedOr[str] = attrs.field(alias="placeholder", default=undefined.UNDEFINED)
    _min_values: int = attrs.field(alias="min_values", default=0)
    _max_values: int = attrs.field(alias="max_values", default=1)
    _is_disabled: bool = attrs.field(alias="is_disabled", default=False)

    @property
    @typing_extensions.override
    def type(self) -> int | component_models.ComponentType:
        return self._type

    @property
    @typing_extensions.override
    def custom_id(self) -> str:
        return self._custom_id

    @property
    @typing_extensions.override
    def is_disabled(self) -> bool:
        return self._is_disabled

    @property
    @typing_extensions.override
    def placeholder(self) -> undefined.UndefinedOr[str]:
        return self._placeholder

    @property
    @typing_extensions.override
    def min_values(self) -> int:
        return self._min_values

    @property
    @typing_extensions.override
    def max_values(self) -> int:
        return self._max_values

    @typing_extensions.override
    def set_custom_id(self, custom_id: str, /) -> Self:
        self._custom_id = custom_id
        return self

    @typing_extensions.override
    def set_is_disabled(self, state: bool, /) -> Self:
        self._is_disabled = state
        return self

    @typing_extensions.override
    def set_placeholder(self, value: undefined.UndefinedOr[str], /) -> Self:
        self._placeholder = value
        return self

    @typing_extensions.override
    def set_min_values(self, value: int, /) -> Self:
        self._min_values = value
        return self

    @typing_extensions.override
    def set_max_values(self, value: int, /) -> Self:
        self._max_values = value
        return self

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        data = data_binding.JSONObjectBuilder()

        data["type"] = self._type
        data["custom_id"] = self._custom_id
        data.put("placeholder", self._placeholder)
        data.put("min_values", self._min_values)
        data.put("max_values", self._max_values)
        data.put("disabled", self._is_disabled)
        return data


@attrs.define(init=False, weakref_slot=False)
class TextSelectMenuBuilder(SelectMenuBuilder, special_endpoints.TextSelectMenuBuilder[_ParentT]):
    """Builder class for text select menus."""

    _options: list[special_endpoints.SelectOptionBuilder] = attrs.field()
    _parent: _ParentT | None = attrs.field()
    _type: typing.Literal[component_models.ComponentType.TEXT_SELECT_MENU] = attrs.field()

    if not typing.TYPE_CHECKING:
        # This will not work with the generated for attrs copy methods.
        __copy__ = None
        __deepcopy__ = None

    @typing.overload
    def __init__(
        self,
        *,
        custom_id: str,
        parent: _ParentT,
        options: typing.Sequence[special_endpoints.SelectOptionBuilder] = (),
        placeholder: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        min_values: int = 0,
        max_values: int = 1,
        is_disabled: bool = False,
    ) -> None: ...

    @typing.overload
    def __init__(
        self: TextSelectMenuBuilder[typing.NoReturn],
        *,
        custom_id: str,
        options: typing.Sequence[special_endpoints.SelectOptionBuilder] = (),
        placeholder: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        min_values: int = 0,
        max_values: int = 1,
        is_disabled: bool = False,
    ) -> None: ...

    def __init__(
        self,
        *,
        custom_id: str,
        parent: _ParentT | None = None,
        options: typing.Sequence[special_endpoints.SelectOptionBuilder] = (),
        placeholder: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        min_values: int = 0,
        max_values: int = 1,
        is_disabled: bool = False,
    ) -> None:
        super().__init__(
            type=component_models.ComponentType.TEXT_SELECT_MENU,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            is_disabled=is_disabled,
        )
        self._options = list(options)
        self._parent = parent

    @property
    @typing_extensions.override
    def parent(self) -> _ParentT:
        if self._parent is None:
            msg = "This menu has no parent"
            raise RuntimeError(msg)

        return self._parent

    @property
    @typing_extensions.override
    def options(self) -> typing.Sequence[special_endpoints.SelectOptionBuilder]:
        return self._options.copy()

    @typing_extensions.override
    def add_option(
        self,
        label: str,
        value: str,
        /,
        *,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        emoji: snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType = undefined.UNDEFINED,
        is_default: bool = False,
    ) -> Self:
        return self.add_raw_option(
            SelectOptionBuilder(label=label, value=value, description=description, emoji=emoji, is_default=is_default)
        )

    def add_raw_option(self, option: special_endpoints.SelectOptionBuilder, /) -> Self:
        self._options.append(option)
        return self

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        data = super().build()

        data["options"] = [option.build() for option in self._options]
        return data


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ChannelSelectMenuBuilder(SelectMenuBuilder, special_endpoints.ChannelSelectMenuBuilder):
    """Builder class for channel select menus."""

    _channel_types: typing.Sequence[channels.ChannelType] = attrs.field(alias="channel_types", factory=list)
    _type: typing.Literal[component_models.ComponentType.CHANNEL_SELECT_MENU] = attrs.field(
        default=component_models.ComponentType.CHANNEL_SELECT_MENU, init=False
    )

    @property
    @typing_extensions.override
    def channel_types(self) -> typing.Sequence[channels.ChannelType]:
        return self._channel_types

    @typing_extensions.override
    def set_channel_types(self, value: typing.Sequence[channels.ChannelType], /) -> Self:
        self._channel_types = value
        return self

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        data = super().build()

        data["channel_types"] = self._channel_types
        return data


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class TextInputBuilder(special_endpoints.TextInputBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.TextInputBuilder`][]."""

    _custom_id: str = attrs.field(alias="custom_id")
    _label: str = attrs.field(alias="label")

    _style: component_models.TextInputStyle = attrs.field(alias="style", default=component_models.TextInputStyle.SHORT)
    _placeholder: undefined.UndefinedOr[str] = attrs.field(
        alias="placeholder", default=undefined.UNDEFINED, kw_only=True
    )
    _value: undefined.UndefinedOr[str] = attrs.field(alias="value", default=undefined.UNDEFINED, kw_only=True)
    _required: bool = attrs.field(alias="required", default=True, kw_only=True)
    _min_length: int = attrs.field(alias="min_length", default=0, kw_only=True)
    _max_length: int = attrs.field(alias="max_length", default=4000, kw_only=True)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[component_models.ComponentType.TEXT_INPUT]:
        return component_models.ComponentType.TEXT_INPUT

    @property
    @typing_extensions.override
    def custom_id(self) -> str:
        return self._custom_id

    @property
    @typing_extensions.override
    def label(self) -> str:
        return self._label

    @property
    @typing_extensions.override
    def style(self) -> component_models.TextInputStyle:
        return self._style

    @property
    @typing_extensions.override
    def placeholder(self) -> undefined.UndefinedOr[str]:
        return self._placeholder

    @property
    @typing_extensions.override
    def value(self) -> undefined.UndefinedOr[str]:
        return self._value

    @property
    @typing_extensions.override
    def is_required(self) -> bool:
        return self._required

    @property
    @typing_extensions.override
    def min_length(self) -> int:
        return self._min_length

    @property
    @typing_extensions.override
    def max_length(self) -> int:
        return self._max_length

    @typing_extensions.override
    def set_style(self, style: component_models.TextInputStyle | int, /) -> Self:
        self._style = component_models.TextInputStyle(style)
        return self

    @typing_extensions.override
    def set_custom_id(self, custom_id: str, /) -> Self:
        self._custom_id = custom_id
        return self

    @typing_extensions.override
    def set_label(self, label: str, /) -> Self:
        self._label = label
        return self

    @typing_extensions.override
    def set_placeholder(self, placeholder: undefined.UndefinedOr[str], /) -> Self:
        self._placeholder = placeholder
        return self

    @typing_extensions.override
    def set_value(self, value: undefined.UndefinedOr[str], /) -> Self:
        self._value = value
        return self

    @typing_extensions.override
    def set_required(self, required: bool, /) -> Self:
        self._required = required
        return self

    @typing_extensions.override
    def set_min_length(self, min_length: int, /) -> Self:
        self._min_length = min_length
        return self

    @typing_extensions.override
    def set_max_length(self, max_length: int, /) -> Self:
        self._max_length = max_length
        return self

    @typing_extensions.override
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


@attrs.define(kw_only=True, weakref_slot=False)
class MessageActionRowBuilder(special_endpoints.MessageActionRowBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.MessageActionRowBuilder`][]."""

    _components: list[special_endpoints.ComponentBuilder] = attrs.field(alias="components", factory=list)
    _stored_type: int | None = attrs.field(default=None, init=False)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[component_models.ComponentType.ACTION_ROW]:
        return component_models.ComponentType.ACTION_ROW

    @property
    @typing_extensions.override
    def components(self) -> typing.Sequence[special_endpoints.ComponentBuilder]:
        return self._components.copy()

    def _assert_can_add_type(self, type_: component_models.ComponentType | int, /) -> None:
        if self._stored_type is not None and self._stored_type != type_:
            msg = f"{type_} component type cannot be added to a container which already holds {self._stored_type}"
            raise ValueError(msg)

        self._stored_type = type_

    @typing_extensions.override
    def add_component(self, component: special_endpoints.ComponentBuilder, /) -> Self:
        self._assert_can_add_type(component.type)
        self._components.append(component)
        return self

    @typing_extensions.override
    def add_interactive_button(
        self,
        style: component_models.InteractiveButtonTypesT,
        custom_id: str,
        /,
        *,
        emoji: snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType = undefined.UNDEFINED,
        label: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        is_disabled: bool = False,
    ) -> Self:
        return self.add_component(
            InteractiveButtonBuilder(
                style=style, custom_id=custom_id, emoji=emoji, label=label, is_disabled=is_disabled
            )
        )

    @typing_extensions.override
    def add_link_button(
        self,
        url: str,
        /,
        *,
        emoji: snowflakes.Snowflakeish | emojis.Emoji | str | undefined.UndefinedType = undefined.UNDEFINED,
        label: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        is_disabled: bool = False,
    ) -> Self:
        return self.add_component(LinkButtonBuilder(url=url, label=label, emoji=emoji, is_disabled=is_disabled))

    @typing_extensions.override
    def add_select_menu(
        self,
        type_: component_models.ComponentType | int,
        custom_id: str,
        /,
        *,
        placeholder: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        min_values: int = 0,
        max_values: int = 1,
        is_disabled: bool = False,
    ) -> Self:
        return self.add_component(
            SelectMenuBuilder(
                type=type_,
                custom_id=custom_id,
                placeholder=placeholder,
                min_values=min_values,
                max_values=max_values,
                is_disabled=is_disabled,
            )
        )

    @typing_extensions.override
    def add_channel_menu(
        self,
        custom_id: str,
        /,
        *,
        channel_types: typing.Sequence[channels.ChannelType] = (),
        placeholder: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        min_values: int = 0,
        max_values: int = 1,
        is_disabled: bool = False,
    ) -> Self:
        return self.add_component(
            ChannelSelectMenuBuilder(
                custom_id=custom_id,
                placeholder=placeholder,
                channel_types=channel_types,
                min_values=min_values,
                max_values=max_values,
                is_disabled=is_disabled,
            )
        )

    @typing_extensions.override
    def add_text_menu(
        self,
        custom_id: str,
        /,
        *,
        placeholder: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        min_values: int = 0,
        max_values: int = 1,
        is_disabled: bool = False,
    ) -> special_endpoints.TextSelectMenuBuilder[Self]:
        component = TextSelectMenuBuilder(
            custom_id=custom_id,
            parent=self,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            is_disabled=is_disabled,
        )
        self.add_component(component)
        return component

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {
            "type": component_models.ComponentType.ACTION_ROW,
            "components": [component.build() for component in self._components],
        }


@attrs.define(kw_only=True, weakref_slot=False)
class ModalActionRowBuilder(special_endpoints.ModalActionRowBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.ModalActionRowBuilder`][]."""

    _components: list[special_endpoints.ComponentBuilder] = attrs.field(alias="components", factory=list)
    _stored_type: int | None = attrs.field(init=False, default=None)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[component_models.ComponentType.ACTION_ROW]:
        return component_models.ComponentType.ACTION_ROW

    @property
    @typing_extensions.override
    def components(self) -> typing.Sequence[special_endpoints.ComponentBuilder]:
        return self._components.copy()

    def _assert_can_add_type(self, type_: component_models.ComponentType | int, /) -> None:
        if self._stored_type is not None and self._stored_type != type_:
            msg = f"{type_} component type cannot be added to a container which already holds {self._stored_type}"
            raise ValueError(msg)

        self._stored_type = type_

    @typing_extensions.override
    def add_component(self, component: special_endpoints.ComponentBuilder, /) -> Self:
        self._assert_can_add_type(component.type)
        self._components.append(component)
        return self

    @typing_extensions.override
    def add_text_input(
        self,
        custom_id: str,
        label: str,
        /,
        *,
        style: component_models.TextInputStyle = component_models.TextInputStyle.SHORT,
        placeholder: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        value: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        required: bool = True,
        min_length: int = 0,
        max_length: int = 4000,
    ) -> Self:
        return self.add_component(
            TextInputBuilder(
                custom_id=custom_id,
                label=label,
                style=style,
                placeholder=placeholder,
                value=value,
                required=required,
                min_length=min_length,
                max_length=max_length,
            )
        )

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {
            "type": component_models.ComponentType.ACTION_ROW,
            "components": [component.build() for component in self._components],
        }


@attrs.define(kw_only=True, weakref_slot=False)
class PollBuilder(special_endpoints.PollBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.PollBuilder`][]."""

    _question_text: str = attrs.field(alias="question_text")
    _answers: list[special_endpoints.PollAnswerBuilder] = attrs.field(alias="answers", factory=list)
    _duration: undefined.UndefinedOr[int] = attrs.field(alias="duration", default=undefined.UNDEFINED)
    _allow_multiselect: bool = attrs.field(alias="allow_multiselect")
    _layout_type: undefined.UndefinedOr[polls.PollLayoutType] = attrs.field(
        alias="layout_type", default=undefined.UNDEFINED
    )

    @property
    @typing_extensions.override
    def question_text(self) -> str:
        return self._question_text

    @property
    @typing_extensions.override
    def answers(self) -> typing.Sequence[special_endpoints.PollAnswerBuilder]:
        return self._answers

    @property
    @typing_extensions.override
    def duration(self) -> undefined.UndefinedOr[int]:
        return self._duration

    @property
    @typing_extensions.override
    def allow_multiselect(self) -> bool:
        return self._allow_multiselect

    @property
    @typing_extensions.override
    def layout_type(self) -> undefined.UndefinedOr[polls.PollLayoutType]:
        return self._layout_type

    @typing_extensions.override
    def add_answer(
        self,
        *,
        text: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        emoji: undefined.UndefinedOr[emojis.Emoji] = undefined.UNDEFINED,
    ) -> Self:
        answer = PollAnswerBuilder(text=text, emoji=emoji)
        self._answers.append(answer)
        return self

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        payload = data_binding.JSONObjectBuilder()

        payload.put("question", {"text": self._question_text})
        payload.put("answers", [answer.build() for answer in self._answers])
        payload.put("duration", self._duration)
        payload.put("allow_multiselect", self._allow_multiselect)
        payload.put("layout_type", self._layout_type)

        return payload


@attrs.define(kw_only=True, weakref_slot=False)
class PollAnswerBuilder(special_endpoints.PollAnswerBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.PollAnswerBuilder`][]."""

    _text: undefined.UndefinedOr[str] = attrs.field(alias="text", default=undefined.UNDEFINED)
    _emoji: undefined.UndefinedOr[emojis.Emoji] = attrs.field(alias="emoji", default=undefined.UNDEFINED)

    @property
    @typing_extensions.override
    def text(self) -> undefined.UndefinedOr[str]:
        return self._text

    @property
    @typing_extensions.override
    def emoji(self) -> undefined.UndefinedOr[emojis.Emoji]:
        return self._emoji

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        payload = data_binding.JSONObjectBuilder()

        payload.put("text", self._text)

        if self._emoji is not undefined.UNDEFINED:
            emoji_id, emoji_name = _build_emoji(self._emoji)

            if emoji_id is not undefined.UNDEFINED:
                payload["emoji"] = {"id": emoji_id}

            elif emoji_name is not undefined.UNDEFINED:
                payload["emoji"] = {"name": emoji_name}

        return {"poll_media": payload}
