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
"""Events fired for guild scheduled event related changes."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "ScheduledEventEvent",
    "ScheduledEventCreateEvent",
    "ScheduledEventDeleteEvent",
    "ScheduledEventUpdateEvent",
    "ScheduledEventUserAddEvent",
    "ScheduledEventUserRemoveEvent",
)

import abc
import typing

import attrs

from hikari import intents
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import attrs_extensions

if typing.TYPE_CHECKING:
    from hikari import scheduled_events
    from hikari import snowflakes
    from hikari import traits
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(intents.Intents.GUILD_SCHEDULED_EVENTS)
class ScheduledEventEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any scheduled event related events."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def event_id(self) -> snowflakes.Snowflake:
        """ID of the scheduled event."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_SCHEDULED_EVENTS)
class ScheduledEventCreateEvent(ScheduledEventEvent):
    """Event fired when a guild scheduled event is created."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    event: scheduled_events.ScheduledEvent = attrs.field()
    """The scheduled event that was created."""

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.event.app

    @property
    def event_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ScheduledEventEvent>>.
        return self.event.id


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_SCHEDULED_EVENTS)
class ScheduledEventDeleteEvent(ScheduledEventEvent):
    """Event fired when a guild scheduled event is deleted."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    event: scheduled_events.ScheduledEvent = attrs.field()
    """The scheduled event that was deleted."""

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.event.app

    @property
    def event_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ScheduledEventEvent>>.
        return self.event.id


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_SCHEDULED_EVENTS)
class ScheduledEventUpdateEvent(ScheduledEventEvent):
    """Event fired when a guild scheduled event is updated."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    event: scheduled_events.ScheduledEvent = attrs.field()
    """The scheduled event that was updated."""

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.event.app

    @property
    def event_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ScheduledEventEvent>>.
        return self.event.id


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_SCHEDULED_EVENTS)
class ScheduledEventUserAddEvent(ScheduledEventEvent):
    """Event fired when a user subscribes to a guild scheduled event."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    event_id: snowflakes.Snowflake = attrs.field()
    """ID of the scheduled event that the user was added to."""

    user_id: snowflakes.Snowflake = attrs.field()
    """ID of the user that was added to the scheduled event."""

    guild_id: snowflakes.Snowflake = attrs.field()
    """ID of the guild that the scheduled event belongs to."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_SCHEDULED_EVENTS)
class ScheduledEventUserRemoveEvent(ScheduledEventEvent):
    """Event fired when a user unsubscribes from a guild scheduled event."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    event_id: snowflakes.Snowflake = attrs.field()
    """ID of the scheduled event that the user was removed from."""

    user_id: snowflakes.Snowflake = attrs.field()
    """ID of the user that was removed from the scheduled event."""

    guild_id: snowflakes.Snowflake = attrs.field()
    """ID of the guild that the scheduled event belongs to."""
