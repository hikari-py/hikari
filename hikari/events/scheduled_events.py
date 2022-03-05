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

__all__: typing.Sequence[str] = [
    "ScheduledEventEvent",
    "ScheduledEventCreateEvent",
    "ScheduledEventDeleteEvent",
    "ScheduledEventUpdateEvent",
    "ScheduledEventUserAddEvent",
    "ScheduledEventUserRemoveEvent",
]

import abc
import typing

import attr

from hikari import intents
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import scheduled_events
    from hikari import snowflakes
    from hikari import traits
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(intents.Intents.GUILD_SCHEDULED_EVENTS)
class ScheduledEventEvent(shard_events.ShardEvent, abc.ABC):

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def event_id(self) -> snowflakes.Snowflake:
        ...


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS)
class ScheduledEventCreateEvent(ScheduledEventEvent):
    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    event: scheduled_events.ScheduledEvent = attr.field()

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.event.app

    @property
    def event_id(self) -> snowflakes.Snowflake:
        return self.event.id


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS)
class ScheduledEventDeleteEvent(ScheduledEventEvent):
    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    event: scheduled_events.ScheduledEvent = attr.field()

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.event.app

    @property
    def event_id(self) -> snowflakes.Snowflake:
        return self.event.id


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS)
class ScheduledEventUpdateEvent(ScheduledEventEvent):
    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    event: scheduled_events.ScheduledEvent = attr.field()

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.event.app

    @property
    def event_id(self) -> snowflakes.Snowflake:
        return self.event.id


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS)
class ScheduledEventUserAddEvent(ScheduledEventEvent):
    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    event_id: snowflakes.Snowflake = attr.field()
    user_id: snowflakes.Snowflake = attr.field()
    guild_id: snowflakes.Snowflake = attr.field()


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS)
class ScheduledEventUserRemoveEvent(ScheduledEventEvent):
    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    event_id: snowflakes.Snowflake = attr.field()
    user_id: snowflakes.Snowflake = attr.field()
    guild_id: snowflakes.Snowflake = attr.field()
