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
"""Events fired for interaction related changes."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "AutocompleteInteractionCreateEvent",
    "CommandInteractionCreateEvent",
    "ComponentInteractionCreateEvent",
    "InteractionCreateEvent",
    "ModalInteractionCreateEvent",
)

import typing

import attrs

from hikari.events import shard_events
from hikari.internal import attrs_extensions
from hikari.internal import typing_extensions

if typing.TYPE_CHECKING:
    from hikari import traits
    from hikari.api import shard as gateway_shard
    from hikari.interactions import base_interactions
    from hikari.interactions import command_interactions
    from hikari.interactions import component_interactions
    from hikari.interactions import modal_interactions


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class InteractionCreateEvent(shard_events.ShardEvent):
    """Event fired when an interaction is created."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    """Shard that received this event."""

    interaction: base_interactions.PartialInteraction = attrs.field(repr=True)
    """Interaction that this event is related to."""

    @property
    @typing_extensions.override
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.interaction.app


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class CommandInteractionCreateEvent(InteractionCreateEvent):
    """Event fired when a command interaction is created."""

    interaction: command_interactions.CommandInteraction = attrs.field(repr=True)
    """Interaction that this event is related to."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ComponentInteractionCreateEvent(InteractionCreateEvent):
    """Event fired when a component interaction is created."""

    interaction: component_interactions.ComponentInteraction = attrs.field(repr=True)
    """Interaction that this event is related to."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class AutocompleteInteractionCreateEvent(InteractionCreateEvent):
    """Event fired when an autocomplete interaction is created."""

    interaction: command_interactions.AutocompleteInteraction = attrs.field(repr=True)
    """Interaction that this event is related to."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class ModalInteractionCreateEvent(InteractionCreateEvent):
    """Event fired when a modal interaction is created."""

    interaction: modal_interactions.ModalInteraction = attrs.field(repr=True)
    """Interaction that this event is related to."""
