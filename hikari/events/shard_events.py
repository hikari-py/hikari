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
"""Events relating to specific shards events."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "ShardEvent",
    "ShardPayloadEvent",
    "ShardStateEvent",
    "ShardConnectedEvent",
    "ShardDisconnectedEvent",
    "ShardReadyEvent",
    "ShardResumedEvent",
    "MemberChunkEvent",
)

import abc
import typing

import attrs

from hikari.events import base_events
from hikari.internal import attrs_extensions
from hikari.internal import collections

if typing.TYPE_CHECKING:
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

    nonce: typing.Optional[str] = attrs.field(repr=True)
    """String nonce used to identify the request member chunks are associated with.

    This is the nonce value passed while requesting member chunks or [`None`][]
    if there was no nonce passed.
    """

    @typing.overload
    def __getitem__(self, index_or_slice: int, /) -> guilds.Member: ...

    @typing.overload
    def __getitem__(self, index_or_slice: slice, /) -> typing.Sequence[guilds.Member]: ...

    def __getitem__(
        self, index_or_slice: typing.Union[int, slice], /
    ) -> typing.Union[guilds.Member, typing.Sequence[guilds.Member]]:
        return collections.get_index_or_slice(self.members, index_or_slice)

    def __iter__(self) -> typing.Iterator[guilds.Member]:
        return iter(self.members.values())

    def __len__(self) -> int:
        return len(self.members)
