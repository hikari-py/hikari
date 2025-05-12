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
    "AutoModBlockMemberInteractionActionBuilder",
    "AutoModBlockMessageActionBuilder",
    "AutoModKeywordPresetTriggerBuilder",
    "AutoModKeywordTriggerBuilder",
    "AutoModMemberProfileTriggerBuilder",
    "AutoModMentionSpamTriggerBuilder",
    "AutoModSendAlertMessageActionBuilder",
    "AutoModSpamTriggerBuilder",
    "AutoModTimeoutActionBuilder",
    "AutocompleteChoiceBuilder",
    "ChannelSelectMenuBuilder",
    "CommandBuilder",
    "ContainerComponentBuilder",
    "ContextMenuCommandBuilder",
    "FileComponentBuilder",
    "InteractionAutocompleteBuilder",
    "InteractionDeferredBuilder",
    "InteractionMessageBuilder",
    "InteractionModalBuilder",
    "InteractiveButtonBuilder",
    "LinkButtonBuilder",
    "MediaGalleryComponentBuilder",
    "MediaGalleryItemBuilder",
    "MessageActionRowBuilder",
    "ModalActionRowBuilder",
    "PollAnswerBuilder",
    "PollBuilder",
    "SectionComponentBuilder",
    "SelectMenuBuilder",
    "SelectOptionBuilder",
    "SeparatorComponentBuilder",
    "SlashCommandBuilder",
    "TextDisplayComponentBuilder",
    "TextInputBuilder",
    "TextSelectMenuBuilder",
    "ThumbnailComponentBuilder",
    "TypingIndicator",
)

import abc
import asyncio
import typing

import attrs

from hikari import auto_mod
from hikari import channels
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
    import types

    import typing_extensions  # noqa: TC004
    from typing_extensions import Self

    from hikari import applications
    from hikari import audit_logs
    from hikari import colors
    from hikari import embeds as embeds_
    from hikari import guilds
    from hikari import permissions as permissions_
    from hikari import scheduled_events
    from hikari import users
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
class _ButtonBuilder(special_endpoints.ButtonBuilder, abc.ABC):
    _id: undefined.UndefinedOr[int] = attrs.field(alias="id", default=undefined.UNDEFINED)
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
    def id(self) -> undefined.UndefinedOr[int]:
        return self._id

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
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        data = data_binding.JSONObjectBuilder()

        data["type"] = component_models.ComponentType.BUTTON
        data["style"] = self.style
        data["disabled"] = self._is_disabled
        data.put("id", self._id)
        data.put("label", self._label)

        if self._emoji_id is not undefined.UNDEFINED:
            data["emoji"] = {"id": self._emoji_id}

        elif self._emoji_name is not undefined.UNDEFINED:
            data["emoji"] = {"name": self._emoji_name}

        return data, []


@attrs.define(kw_only=True, weakref_slot=False)
class LinkButtonBuilder(_ButtonBuilder, special_endpoints.LinkButtonBuilder):
    """Builder class for link buttons."""

    _custom_id: undefined.UndefinedType = attrs.field(init=False, default=undefined.UNDEFINED)
    _url: str = attrs.field(alias="url")

    @property
    @typing_extensions.override
    def url(self) -> str:
        return self._url

    @property
    @typing_extensions.override
    def style(self) -> typing.Literal[component_models.ButtonStyle.LINK]:
        return component_models.ButtonStyle.LINK

    @typing_extensions.override
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        data, attachments = super().build()

        data["url"] = self._url

        return data, attachments


@attrs.define(kw_only=True, weakref_slot=False)
class InteractiveButtonBuilder(_ButtonBuilder, special_endpoints.InteractiveButtonBuilder):
    """Builder class for interactive buttons."""

    _style: int | component_models.ButtonStyle = attrs.field(alias="style")
    _custom_id: str = attrs.field(alias="custom_id")

    @property
    @typing_extensions.override
    def style(self) -> int | component_models.ButtonStyle:
        return self._style

    @property
    @typing_extensions.override
    def custom_id(self) -> str:
        return self._custom_id

    @typing_extensions.override
    def set_custom_id(self, custom_id: str, /) -> Self:
        self._custom_id = custom_id
        return self

    @typing_extensions.override
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        data, attachments = super().build()

        data["custom_id"] = self._custom_id

        return data, attachments


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

    _id: undefined.UndefinedOr[int] = attrs.field(alias="id", default=undefined.UNDEFINED)
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
    def id(self) -> undefined.UndefinedOr[int]:
        return self._id

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
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        data = data_binding.JSONObjectBuilder()

        data["type"] = self._type
        data["custom_id"] = self._custom_id
        data.put("id", self._id)
        data.put("placeholder", self._placeholder)
        data.put("min_values", self._min_values)
        data.put("max_values", self._max_values)
        data.put("disabled", self._is_disabled)
        return data, []


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
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
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
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
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
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
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
            id=id,
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
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        payload, attachments = super().build()

        payload["options"] = [option.build() for option in self._options]
        return payload, attachments


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
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        payload, attachments = super().build()

        payload["channel_types"] = self._channel_types
        return payload, attachments


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class TextInputBuilder(special_endpoints.TextInputBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.TextInputBuilder`][]."""

    _id: undefined.UndefinedOr[int] = attrs.field(alias="id", default=undefined.UNDEFINED)
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
    def id(self) -> undefined.UndefinedOr[int]:
        return self._id

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
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        data = data_binding.JSONObjectBuilder()

        data["type"] = component_models.ComponentType.TEXT_INPUT
        data["style"] = self._style
        data["custom_id"] = self._custom_id
        data["label"] = self._label
        data.put("id", self._id)
        data.put("placeholder", self._placeholder)
        data.put("value", self._value)
        data.put("required", self._required)
        data.put("min_length", self._min_length)
        data.put("max_length", self._max_length)

        return data, []


@attrs.define(kw_only=True, weakref_slot=False)
class MessageActionRowBuilder(special_endpoints.MessageActionRowBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.MessageActionRowBuilder`][]."""

    _id: undefined.UndefinedOr[int] = attrs.field(alias="id", default=undefined.UNDEFINED)
    _components: list[special_endpoints.MessageActionRowBuilderComponentsT] = attrs.field(
        alias="components", factory=list
    )
    _stored_type: int | None = attrs.field(default=None, init=False)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[component_models.ComponentType.ACTION_ROW]:
        return component_models.ComponentType.ACTION_ROW

    @property
    @typing_extensions.override
    def id(self) -> undefined.UndefinedOr[int]:
        return self._id

    @property
    @typing_extensions.override
    def components(self) -> typing.Sequence[special_endpoints.MessageActionRowBuilderComponentsT]:
        return self._components.copy()

    def _assert_can_add_type(self, type_: component_models.ComponentType | int, /) -> None:
        if self._stored_type is not None and self._stored_type != type_:
            msg = f"{type_} component type cannot be added to a container which already holds {self._stored_type}"
            raise ValueError(msg)

        self._stored_type = type_

    @typing_extensions.override
    def add_component(self, component: special_endpoints.MessageActionRowBuilderComponentsT, /) -> Self:
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
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> Self:
        return self.add_component(
            InteractiveButtonBuilder(
                id=id, style=style, custom_id=custom_id, emoji=emoji, label=label, is_disabled=is_disabled
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
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> Self:
        return self.add_component(LinkButtonBuilder(id=id, url=url, label=label, emoji=emoji, is_disabled=is_disabled))

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
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> Self:
        return self.add_component(
            SelectMenuBuilder(
                type=type_,
                id=id,
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
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> Self:
        return self.add_component(
            ChannelSelectMenuBuilder(
                id=id,
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
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> special_endpoints.TextSelectMenuBuilder[Self]:
        component = TextSelectMenuBuilder(
            id=id,
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
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        payload = data_binding.JSONObjectBuilder()

        payload.put("id", self._id)
        payload.put("type", component_models.ComponentType.ACTION_ROW)

        components_payload: typing.MutableSequence[typing.Any] = []
        attachments: typing.MutableSequence[files.Resource[files.AsyncReader]] = []
        for component in self.components:
            component_payload, component_attachments = component.build()
            components_payload.append(component_payload)
            attachments.extend(component_attachments)

        payload.put_array("components", components_payload)

        return payload, attachments


@attrs.define(kw_only=True, weakref_slot=False)
class ModalActionRowBuilder(special_endpoints.ModalActionRowBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.ModalActionRowBuilder`][]."""

    _id: undefined.UndefinedOr[int] = attrs.field(alias="id", default=undefined.UNDEFINED)
    _components: list[special_endpoints.ModalActionRowBuilderComponentsT] = attrs.field(
        alias="components", factory=list
    )
    _stored_type: int | None = attrs.field(init=False, default=None)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[component_models.ComponentType.ACTION_ROW]:
        return component_models.ComponentType.ACTION_ROW

    @property
    @typing_extensions.override
    def id(self) -> undefined.UndefinedOr[int]:
        return self._id

    @property
    @typing_extensions.override
    def components(self) -> typing.Sequence[special_endpoints.ModalActionRowBuilderComponentsT]:
        return self._components.copy()

    def _assert_can_add_type(self, type_: component_models.ComponentType | int, /) -> None:
        if self._stored_type is not None and self._stored_type != type_:
            msg = f"{type_} component type cannot be added to a container which already holds {self._stored_type}"
            raise ValueError(msg)

        self._stored_type = type_

    @typing_extensions.override
    def add_component(self, component: special_endpoints.ModalActionRowBuilderComponentsT, /) -> Self:
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
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        component_payloads: list[typing.MutableMapping[str, typing.Any]] = []
        attachments: list[files.Resource[files.AsyncReader]] = []

        for component in self.components:
            component_payload, component_attachments = component.build()
            component_payloads.append(component_payload)
            attachments.extend(component_attachments)

        payload = data_binding.JSONObjectBuilder()
        payload["type"] = self.type
        payload["components"] = component_payloads
        payload.put("id", self._id)

        return payload, attachments


def _build_media_resource(resource: files.Resource[files.AsyncReader]) -> dict[str, typing.Any]:
    return {"url": resource.url}


@attrs.define(kw_only=True, weakref_slot=False)
class SectionComponentBuilder(special_endpoints.SectionComponentBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.SectionComponentBuilder`][]."""

    _id: undefined.UndefinedOr[int] = attrs.field(alias="id", default=undefined.UNDEFINED)
    _components: list[special_endpoints.SectionBuilderComponentsT] = attrs.field(alias="components", factory=list)
    _accessory: special_endpoints.SectionBuilderAccessoriesT = attrs.field(alias="accessory")

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[component_models.ComponentType.SECTION]:
        return component_models.ComponentType.SECTION

    @property
    @typing_extensions.override
    def id(self) -> undefined.UndefinedOr[int]:
        return self._id

    @property
    @typing_extensions.override
    def components(self) -> typing.Sequence[special_endpoints.SectionBuilderComponentsT]:
        return self._components.copy()

    @property
    @typing_extensions.override
    def accessory(self) -> special_endpoints.SectionBuilderAccessoriesT:
        return self._accessory

    @typing_extensions.override
    def add_component(self, component: special_endpoints.SectionBuilderComponentsT) -> Self:
        self._components.append(component)
        return self

    @typing_extensions.override
    def add_text_display(self, content: str, *, id: undefined.UndefinedOr[int] = undefined.UNDEFINED) -> Self:
        component = TextDisplayComponentBuilder(id=id, content=content)
        self.add_component(component)
        return self

    @typing_extensions.override
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        payload = data_binding.JSONObjectBuilder()
        payload["type"] = self.type
        payload.put("id", self._id)

        accessory_payload, accessory_attachments = self.accessory.build()

        attachments: list[files.Resource[files.AsyncReader]] = list(accessory_attachments)
        components_payload: list[typing.Mapping[str, typing.Any]] = []
        for component in self.components:
            component_payload, component_attachments = component.build()

            components_payload.append(component_payload)
            attachments.extend(component_attachments)

        payload["components"] = components_payload
        payload["accessory"] = accessory_payload

        return payload, attachments


@attrs.define(kw_only=True, weakref_slot=False)
class TextDisplayComponentBuilder(special_endpoints.TextDisplayComponentBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.TextDisplayComponentBuilder`][]."""

    _id: undefined.UndefinedOr[int] = attrs.field(alias="id", default=undefined.UNDEFINED)
    _content: str = attrs.field(alias="content")

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[component_models.ComponentType.TEXT_DISPLAY]:
        return component_models.ComponentType.TEXT_DISPLAY

    @property
    @typing_extensions.override
    def id(self) -> undefined.UndefinedOr[int]:
        return self._id

    @property
    @typing_extensions.override
    def content(self) -> str:
        return self._content

    @typing_extensions.override
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        payload = data_binding.JSONObjectBuilder()
        payload["type"] = self.type
        payload["content"] = self._content

        payload.put("id", self._id)

        return payload, ()


@attrs.define(kw_only=True, weakref_slot=False)
class ThumbnailComponentBuilder(special_endpoints.ThumbnailComponentBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.ThumbnailComponentBuilder`][]."""

    _id: undefined.UndefinedOr[int] = attrs.field(alias="id", default=undefined.UNDEFINED)
    _media: files.Resourceish = attrs.field(alias="media")
    _description: undefined.UndefinedOr[str] = attrs.field(alias="description", default=undefined.UNDEFINED)
    _spoiler: bool = attrs.field(alias="spoiler", default=False)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[component_models.ComponentType.THUMBNAIL]:
        return component_models.ComponentType.THUMBNAIL

    @property
    @typing_extensions.override
    def id(self) -> undefined.UndefinedOr[int]:
        return self._id

    @property
    @typing_extensions.override
    def media(self) -> files.Resourceish:
        return self._media

    @property
    @typing_extensions.override
    def description(self) -> undefined.UndefinedOr[str]:
        return self._description

    @property
    @typing_extensions.override
    def is_spoiler(self) -> bool:
        return self._spoiler

    @typing_extensions.override
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        media_resource = files.ensure_resource(self._media)

        payload = data_binding.JSONObjectBuilder()
        payload["type"] = self.type
        payload["media"] = _build_media_resource(media_resource)
        payload["spoiler"] = self._spoiler

        payload.put("id", self._id)
        payload.put("description", self._description)

        return payload, (media_resource,)


@attrs.define(kw_only=True, weakref_slot=False)
class MediaGalleryComponentBuilder(special_endpoints.MediaGalleryComponentBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.MediaGalleryComponentBuilder`][]."""

    _id: undefined.UndefinedOr[int] = attrs.field(alias="id", default=undefined.UNDEFINED)
    _items: list[special_endpoints.MediaGalleryItemBuilder] = attrs.field(alias="items", factory=list)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[component_models.ComponentType.MEDIA_GALLERY]:
        return component_models.ComponentType.MEDIA_GALLERY

    @property
    @typing_extensions.override
    def id(self) -> undefined.UndefinedOr[int]:
        return self._id

    @property
    @typing_extensions.override
    def items(self) -> typing.Sequence[special_endpoints.MediaGalleryItemBuilder]:
        return self._items.copy()

    @typing_extensions.override
    def add_item(self, item: special_endpoints.MediaGalleryItemBuilder) -> Self:
        self._items.append(item)
        return self

    @typing_extensions.override
    def add_media_gallery_item(
        self,
        media: files.Resourceish,
        *,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        spoiler: bool = False,
    ) -> Self:
        self.add_item(MediaGalleryItemBuilder(media=media, description=description, spoiler=spoiler))
        return self

    @typing_extensions.override
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        items_payload: list[typing.MutableMapping[str, typing.Any]] = []
        attachments: list[files.Resource[files.AsyncReader]] = []
        for item in self.items:
            item_payload, item_attachments = item.build()
            items_payload.append(item_payload)
            attachments.extend(item_attachments)

        payload = data_binding.JSONObjectBuilder()
        payload["type"] = self.type
        payload["items"] = items_payload
        payload.put("id", self._id)

        return payload, attachments


@attrs.define(kw_only=True, weakref_slot=False)
class MediaGalleryItemBuilder(special_endpoints.MediaGalleryItemBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.MediaGalleryItemBuilder`][]."""

    _media: files.Resourceish = attrs.field(alias="media")
    _description: undefined.UndefinedOr[str] = attrs.field(alias="description", default=undefined.UNDEFINED)
    _spoiler: bool = attrs.field(alias="spoiler", default=False)

    @property
    @typing_extensions.override
    def media(self) -> files.Resourceish:
        return self._media

    @property
    @typing_extensions.override
    def description(self) -> undefined.UndefinedOr[str]:
        return self._description

    @property
    @typing_extensions.override
    def is_spoiler(self) -> bool:
        return self._spoiler

    @typing_extensions.override
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        media_resource = files.ensure_resource(self._media)

        payload = data_binding.JSONObjectBuilder()
        payload["media"] = _build_media_resource(media_resource)
        payload["spoiler"] = self._spoiler
        payload.put("description", self._description)

        return payload, (media_resource,)


@attrs.define(kw_only=True, weakref_slot=False)
class SeparatorComponentBuilder(special_endpoints.SeparatorComponentBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.SeparatorComponentBuilder`][]."""

    _id: undefined.UndefinedOr[int] = attrs.field(alias="id", default=undefined.UNDEFINED)
    _spacing: undefined.UndefinedOr[component_models.SpacingType] = attrs.field(
        alias="spacing", default=undefined.UNDEFINED
    )
    _divider: undefined.UndefinedOr[bool] = attrs.field(alias="divider", default=undefined.UNDEFINED)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[component_models.ComponentType.SEPARATOR]:
        return component_models.ComponentType.SEPARATOR

    @property
    @typing_extensions.override
    def id(self) -> undefined.UndefinedOr[int]:
        return self._id

    @property
    @typing_extensions.override
    def spacing(self) -> undefined.UndefinedOr[component_models.SpacingType]:
        return self._spacing

    @property
    @typing_extensions.override
    def divider(self) -> undefined.UndefinedOr[bool]:
        return self._divider

    @typing_extensions.override
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        payload = data_binding.JSONObjectBuilder()
        payload["type"] = self.type
        payload.put("id", self._id)
        payload.put("spacing", self._spacing)
        payload.put("divider", self._divider)

        return payload, ()


@attrs.define(kw_only=True, weakref_slot=False)
class FileComponentBuilder(special_endpoints.FileComponentBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.FileComponentBuilder`][]."""

    _id: undefined.UndefinedOr[int] = attrs.field(alias="id", default=undefined.UNDEFINED)
    _file: files.Resourceish = attrs.field(alias="file")
    _spoiler: bool = attrs.field(alias="spoiler", default=False)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[component_models.ComponentType.FILE]:
        return component_models.ComponentType.FILE

    @property
    @typing_extensions.override
    def id(self) -> undefined.UndefinedOr[int]:
        return self._id

    @property
    @typing_extensions.override
    def file(self) -> files.Resourceish:
        return self._file

    @property
    @typing_extensions.override
    def is_spoiler(self) -> bool:
        return self._spoiler

    @typing_extensions.override
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        file_resource = files.ensure_resource(self._file)

        payload = data_binding.JSONObjectBuilder()
        payload["type"] = self.type
        payload["spoiler"] = self._spoiler
        payload["file"] = _build_media_resource(file_resource)
        payload.put("id", self._id)

        return payload, (file_resource,)


@attrs.define(kw_only=True, weakref_slot=False)
class ContainerComponentBuilder(special_endpoints.ContainerComponentBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.ContainerComponentBuilder`][]."""

    _id: undefined.UndefinedOr[int] = attrs.field(alias="id", default=undefined.UNDEFINED)
    _accent_color: undefined.UndefinedOr[colors.Color] = attrs.field(alias="accent_color", default=undefined.UNDEFINED)
    _spoiler: bool = attrs.field(alias="spoiler", default=False)

    _components: list[special_endpoints.ContainerBuilderComponentsT] = attrs.field(alias="components", factory=list)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[component_models.ComponentType.CONTAINER]:
        return component_models.ComponentType.CONTAINER

    @property
    @typing_extensions.override
    def id(self) -> undefined.UndefinedOr[int]:
        return self._id

    @property
    @typing_extensions.override
    def accent_color(self) -> undefined.UndefinedOr[colors.Color]:
        return self._accent_color

    @property
    @typing_extensions.override
    def is_spoiler(self) -> bool:
        return self._spoiler

    @property
    @typing_extensions.override
    def components(self) -> typing.Sequence[special_endpoints.ContainerBuilderComponentsT]:
        return self._components.copy()

    @typing_extensions.override
    def add_component(self, component: special_endpoints.ContainerBuilderComponentsT) -> Self:
        self._components.append(component)
        return self

    @typing_extensions.override
    def add_action_row(
        self,
        components: typing.Sequence[special_endpoints.MessageActionRowBuilderComponentsT],
        *,
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> Self:
        component = MessageActionRowBuilder(id=id, components=list(components))
        self.add_component(component)
        return self

    @typing_extensions.override
    def add_text_display(self, content: str, *, id: undefined.UndefinedOr[int] = undefined.UNDEFINED) -> Self:
        component = TextDisplayComponentBuilder(id=id, content=content)
        self.add_component(component)
        return self

    @typing_extensions.override
    def add_media_gallery(
        self,
        items: typing.Sequence[special_endpoints.MediaGalleryItemBuilder],
        *,
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> Self:
        component = MediaGalleryComponentBuilder(id=id, items=list(items))
        self.add_component(component)
        return self

    @typing_extensions.override
    def add_separator(
        self,
        *,
        spacing: undefined.UndefinedOr[component_models.SpacingType] = undefined.UNDEFINED,
        divider: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        id: undefined.UndefinedOr[int] = undefined.UNDEFINED,
    ) -> Self:
        component = SeparatorComponentBuilder(id=id, spacing=spacing, divider=divider)
        self.add_component(component)
        return self

    @typing_extensions.override
    def add_file(
        self, file: files.Resourceish, *, spoiler: bool = False, id: undefined.UndefinedOr[int] = undefined.UNDEFINED
    ) -> Self:
        component = FileComponentBuilder(id=id, file=file, spoiler=spoiler)
        self.add_component(component)
        return self

    @typing_extensions.override
    def build(
        self,
    ) -> tuple[typing.MutableMapping[str, typing.Any], typing.Sequence[files.Resource[files.AsyncReader]]]:
        payload = data_binding.JSONObjectBuilder()
        payload["type"] = self.type
        payload["spoiler"] = self._spoiler
        payload.put("id", self._id)
        payload.put("accent_color", self._accent_color)

        components_payload: typing.MutableSequence[typing.MutableMapping[str, typing.Any]] = []
        attachments: typing.MutableSequence[files.Resource[files.AsyncReader]] = []
        for component in self.components:
            component_payload, component_attachments = component.build()
            components_payload.append(component_payload)
            attachments.extend(component_attachments)

        payload.put_array("components", components_payload)

        return payload, attachments


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


@attrs.define(kw_only=True, weakref_slot=False)
class AutoModBlockMessageActionBuilder(special_endpoints.AutoModBlockMessageActionBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.AutoModBlockMessageActionBuilder`][]."""

    _custom_message: str | None = attrs.field(alias="custom_message", default=None)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModActionType.BLOCK_MESSAGE]:
        return auto_mod.AutoModActionType.BLOCK_MESSAGE

    @property
    @typing_extensions.override
    def custom_message(self) -> str | None:
        return self._custom_message

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {"type": self.type, "metadata": {"custom_message": self.custom_message}}


@attrs.define(kw_only=True, weakref_slot=False)
class AutoModSendAlertMessageActionBuilder(special_endpoints.AutoModSendAlertMessageActionBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.AutoModSendAlertMessageActionBuilder`][]."""

    _channel_id: snowflakes.Snowflake = attrs.field(alias="channel_id")

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModActionType.SEND_ALERT_MESSAGE]:
        return auto_mod.AutoModActionType.SEND_ALERT_MESSAGE

    @property
    @typing_extensions.override
    def channel_id(self) -> snowflakes.Snowflake:
        return self._channel_id

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {"type": self.type, "metadata": {"channel_id": self.channel_id}}


@attrs.define(kw_only=True, weakref_slot=False)
class AutoModTimeoutActionBuilder(special_endpoints.AutoModTimeoutActionBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.AutoModTimeoutActionBuilder`][]."""

    _duration_seconds: int = attrs.field(alias="duration_seconds")

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModActionType.TIMEOUT]:
        return auto_mod.AutoModActionType.TIMEOUT

    @property
    @typing_extensions.override
    def duration_seconds(self) -> int:
        return self._duration_seconds

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {"type": self.type, "metadata": {"duration_seconds": self.duration_seconds}}


@attrs.define(kw_only=True, weakref_slot=False)
class AutoModBlockMemberInteractionActionBuilder(special_endpoints.AutoModBlockMemberInteractionActionBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.AutoModBlockMemberInteractionActionBuilder`][]."""

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModActionType.BLOCK_MEMBER_INTERACTION]:
        return auto_mod.AutoModActionType.BLOCK_MEMBER_INTERACTION

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {"type": self.type, "metadata": {}}


@attrs.define(kw_only=True, weakref_slot=False)
class AutoModKeywordTriggerBuilder(special_endpoints.AutoModKeywordTriggerBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.AutoModKeywordTriggerBuilder`][]."""

    _keyword_filter: list[str] = attrs.field(alias="keyword_filter", factory=list)

    _regex_patterns: list[str] = attrs.field(alias="regex_patterns", factory=list)

    _allow_list: list[str] = attrs.field(alias="allow_list", factory=list)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModTriggerType.KEYWORD]:
        return auto_mod.AutoModTriggerType.KEYWORD

    @property
    @typing_extensions.override
    def keyword_filter(self) -> typing.Sequence[str]:
        return self._keyword_filter

    @property
    @typing_extensions.override
    def regex_patterns(self) -> typing.Sequence[str]:
        return self._regex_patterns

    @property
    @typing_extensions.override
    def allow_list(self) -> typing.Sequence[str]:
        return self._allow_list

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {
            "keyword_filter": self.keyword_filter,
            "regex_patterns": self.regex_patterns,
            "allow_list": self.allow_list,
        }


@attrs.define(kw_only=True, weakref_slot=False)
class AutoModSpamTriggerBuilder(special_endpoints.AutoModSpamTriggerBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.AutoModSpamTriggerBuilder`][]."""

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModTriggerType.SPAM]:
        return auto_mod.AutoModTriggerType.SPAM

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {}


@attrs.define(kw_only=True, weakref_slot=False)
class AutoModKeywordPresetTriggerBuilder(special_endpoints.AutoModKeywordPresetTriggerBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.AutoModKeywordPresetTriggerBuilder`][]."""

    _presets: list[auto_mod.AutoModKeywordPresetType] = attrs.field(alias="presets", factory=list)

    _allow_list: list[str] = attrs.field(alias="allow_list", factory=list)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModTriggerType.KEYWORD_PRESET]:
        return auto_mod.AutoModTriggerType.KEYWORD_PRESET

    @property
    @typing_extensions.override
    def presets(self) -> typing.Sequence[auto_mod.AutoModKeywordPresetType]:
        return self._presets

    @property
    @typing_extensions.override
    def allow_list(self) -> typing.Sequence[str]:
        return self._allow_list

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {"presets": self.presets, "allow_list": self.allow_list}


@attrs.define(kw_only=True, weakref_slot=False)
class AutoModMentionSpamTriggerBuilder(special_endpoints.AutoModMentionSpamTriggerBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.AutoModSpamTriggerBuilder`][]."""

    _mention_total_limit: int = attrs.field(alias="mention_total_limit")

    _mention_raid_protection_enabled: bool = attrs.field(alias="mention_raid_protection_enabled")

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModTriggerType.MENTION_SPAM]:
        return auto_mod.AutoModTriggerType.MENTION_SPAM

    @property
    @typing_extensions.override
    def mention_total_limit(self) -> int:
        return self._mention_total_limit

    @property
    @typing_extensions.override
    def mention_raid_protection_enabled(self) -> bool:
        return self._mention_raid_protection_enabled

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {
            "mention_total_limit": self.mention_total_limit,
            "mention_raid_protection_enabled": self.mention_raid_protection_enabled,
        }


@attrs.define(kw_only=True, weakref_slot=False)
class AutoModMemberProfileTriggerBuilder(special_endpoints.AutoModMemberProfileTriggerBuilder):
    """Standard implementation of [`hikari.api.special_endpoints.AutoModMemberProfileTriggerBuilder`][]."""

    _keyword_filter: list[str] = attrs.field(alias="keyword_filter", factory=list)

    _regex_patterns: list[str] = attrs.field(alias="regex_patterns", factory=list)

    _allow_list: list[str] = attrs.field(alias="allow_list", factory=list)

    @property
    @typing_extensions.override
    def type(self) -> typing.Literal[auto_mod.AutoModTriggerType.MEMBER_PROFILE]:
        return auto_mod.AutoModTriggerType.MEMBER_PROFILE

    @property
    @typing_extensions.override
    def keyword_filter(self) -> typing.Sequence[str]:
        return self._keyword_filter

    @property
    @typing_extensions.override
    def regex_patterns(self) -> typing.Sequence[str]:
        return self._regex_patterns

    @property
    @typing_extensions.override
    def allow_list(self) -> typing.Sequence[str]:
        return self._allow_list

    @typing_extensions.override
    def build(self) -> typing.MutableMapping[str, typing.Any]:
        return {
            "keyword_filter": self.keyword_filter,
            "regex_patterns": self.regex_patterns,
            "allow_list": self.allow_list,
        }
