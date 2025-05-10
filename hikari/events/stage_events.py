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
"""Events that fire when stage instances are created/updated/deleted."""

from __future__ import annotations

import abc
import typing

import attrs

from hikari import intents
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import attrs_extensions
from hikari.internal import typing_extensions

if typing.TYPE_CHECKING:
    from hikari import traits
    from hikari.api import shard as gateway_shard
    from hikari.stage_instances import StageInstance


@base_events.requires_intents(intents.Intents.GUILDS)
class StageInstanceEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any event that involves stage instances."""

    __slots__: typing.Sequence[str] = ()

    @property
    @typing_extensions.override
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.stage_instance.app

    @property
    @abc.abstractmethod
    def stage_instance(self) -> StageInstance:
        """Stage instance that this event relates to."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILDS)
class StageInstanceCreateEvent(StageInstanceEvent):
    """Event fired when a stage instance is created."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    stage_instance: StageInstance = attrs.field()
    """The stage instance that was created."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILDS)
class StageInstanceUpdateEvent(StageInstanceEvent):
    """Event fired when a stage instance is updated."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    stage_instance: StageInstance = attrs.field()
    """The stage instance that was updated."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILDS)
class StageInstanceDeleteEvent(StageInstanceEvent):
    """Event fired when a stage instance is deleted."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    stage_instance: StageInstance = attrs.field()
    """The stage instance that was deleted."""
