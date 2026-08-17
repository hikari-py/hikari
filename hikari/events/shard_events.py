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
"""Events relating to specific shards events."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "ChannelInfo",
    "ChannelInfoEvent",
    "MemberChunkEvent",
    "RequestGuildMembersRateLimitedEvent",
    "ShardConnectedEvent",
    "ShardDisconnectedEvent",
    "ShardEvent",
    "ShardPayloadEvent",
    "ShardRateLimitedEvent",
    "ShardReadyEvent",
    "ShardResumedEvent",
    "ShardStateEvent",
)

import abc
import typing

import attrs

from hikari.events import base_events
from hikari.internal import attrs_extensions
from hikari.internal import collections
from hikari.internal import typing_extensions

if typing.TYPE_CHECKING:
    import datetime

    from hikari import applications
    from hikari import guilds
    from hikari import presences as presences_
    from hikari import snowflakes
    from hikari import traits
    from hikari import users
    from hikari.api import shard as gateway_shard


class ShardEvent(base_events.Event, abc.ABC):
    """Base class for any event that was shard-specific."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def shard(self) -> gateway_shard.GatewayShard:
        """Shard that received this event."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ShardPayloadEvent(ShardEvent):
    """Event fired for most shard events with their raw payload.

    !!! note
        This will only be dispatched for real dispatch events received from
        Discord and not artificial events like the [`hikari.events.shard_events.ShardStateEvent`][] events.
    """

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.

    name: str = attrs.field()
    """Name of the received event."""

    payload: typing.Mapping[str, typing.Any] = attrs.field()
    """The raw payload for this event."""


class ShardStateEvent(ShardEvent, abc.ABC):
    """Base class for any event concerning the state/connectivity of a shard.

    This currently wraps connection/disconnection/ready/resumed events only.
    """

    __slots__: typing.Sequence[str] = ()


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ShardConnectedEvent(ShardStateEvent):
    """Event fired when a shard successfully connects."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ShardDisconnectedEvent(ShardStateEvent):
    """Event fired when a shard disconnects."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ShardReadyEvent(ShardStateEvent):
    """Event fired when a shard declares it is ready."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.

    actual_gateway_version: int = attrs.field(repr=True)
    """Actual gateway version being used."""

    resume_gateway_url: str = attrs.field(repr=False)
    """The URL to use to when reconnecting to the gateway."""

    session_id: str = attrs.field(repr=True)
    """ID for this session."""

    my_user: users.OwnUser = attrs.field(repr=True)
    """User for the current bot account this connection is authenticated with."""

    unavailable_guilds: typing.Sequence[snowflakes.Snowflake] = attrs.field(repr=False)
    """Sequence of the IDs for all guilds this bot is currently in.

    All guilds will start off "unavailable" and should become available after
    a few seconds of connecting one-by-one.
    """

    application_id: snowflakes.Snowflake = attrs.field(repr=True)
    """ID of the application this ready event is for."""

    application_flags: applications.ApplicationFlags = attrs.field(repr=True)
    """Flags of the application this ready event is for."""

    @property
    @typing_extensions.override
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.my_user.app


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ShardResumedEvent(ShardStateEvent):
    """Event fired when a shard resumes an existing session."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ShardRateLimitedEvent(ShardEvent):
    """Event fired when a gateway operation is rate limited on a shard."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.

    opcode: int = attrs.field(repr=True)
    """Opcode of the gateway operation that was rate limited."""

    retry_after: float = attrs.field(repr=True)
    """How many seconds to wait before the operation can be retried."""

    meta: typing.Mapping[str, typing.Any] = attrs.field(repr=True)
    """The raw metadata for the operation that was rate limited."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class RequestGuildMembersRateLimitedEvent(ShardRateLimitedEvent):
    """Event fired when requesting guild members is rate limited on a shard."""

    guild_id: snowflakes.Snowflake = attrs.field(repr=True)
    """ID of the guild members were requested for."""

    nonce: str | None = attrs.field(repr=True)
    """The nonce sent in the request that was rate limited, if any."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class MemberChunkEvent(ShardEvent, typing.Sequence["guilds.Member"]):
    """Event fired when a member chunk payload is received on a gateway shard."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field(repr=True)
    # <<docstring inherited from ShardEvent>>.

    members: typing.Mapping[snowflakes.Snowflake, guilds.Member] = attrs.field(repr=False)
    """Mapping of user IDs to the objects of the members in this chunk."""

    chunk_index: int = attrs.field(repr=True)
    """Zero-indexed position of this within the queued up chunks for this request."""

    chunk_count: int = attrs.field(repr=True)
    """Total number of expected chunks for the request this is associated with."""

    not_found: typing.Sequence[snowflakes.Snowflake] = attrs.field(repr=True)
    """Sequence of the snowflakes that were not found while making this request.

    This is only applicable when user IDs are specified while making the
    member request the chunk is associated with.
    """

    presences: typing.Mapping[snowflakes.Snowflake, presences_.MemberPresence] = attrs.field(repr=False)
    """Mapping of user IDs to found member presence objects.

    This will be empty if no presences are found or
    [`include_presences`][hikari.api.shard.GatewayShard.request_guild_members] is
    not passed as [`True`][] while requesting the member chunks.
    """

    nonce: str | None = attrs.field(repr=True)
    """String nonce used to identify the request member chunks are associated with.

    This is the nonce value passed while requesting member chunks or [`None`][]
    if there was no nonce passed.
    """

    @typing.overload
    def __getitem__(self, index_or_slice: int, /) -> guilds.Member: ...

    @typing.overload
    def __getitem__(self, index_or_slice: slice, /) -> typing.Sequence[guilds.Member]: ...

    @typing_extensions.override
    def __getitem__(self, index_or_slice: int | slice, /) -> guilds.Member | typing.Sequence[guilds.Member]:
        return collections.get_index_or_slice(self.members, index_or_slice)

    @typing_extensions.override
    def __iter__(self) -> typing.Iterator[guilds.Member]:
        return iter(self.members.values())

    @typing_extensions.override
    def __len__(self) -> int:
        return len(self.members)


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ChannelInfo:
    """Ephemeral information for a channel in a guild.

    This is sent as part of a [`hikari.events.shard_events.ChannelInfoEvent`][].
    """

    channel_id: snowflakes.Snowflake = attrs.field(repr=True)
    """ID of the channel this information is for."""

    status: str | None = attrs.field(repr=True)
    """The voice channel status.

    This will be [`None`][] if no status is set or the field was not
    requested.
    """

    voice_start_time: datetime.datetime | None = attrs.field(repr=True)
    """When the ongoing voice session started.

    This will be [`None`][] if there is no ongoing voice session or the
    field was not requested.
    """


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ChannelInfoEvent(ShardEvent):
    """Event fired when a channel info payload is received on a gateway shard.

    This is sent in response to
    [`hikari.api.shard.GatewayShard.request_channel_info`][].
    """

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field(repr=True)
    """ID of the guild this event is for."""

    channels: typing.Mapping[snowflakes.Snowflake, ChannelInfo] = attrs.field(repr=False)
    """Mapping of channel IDs to the ephemeral information of the guild's channels."""
