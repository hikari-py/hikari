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
"""Events fired for interaction related changes."""
from __future__ import annotations

__all__: typing.Sequence[str] = [
    "CommandEvent",
    "CommandCreateEvent",
    "CommandUpdateEvent",
    "CommandDeleteEvent",
    "InteractionCreateEvent",
]

import abc
import typing

import attr

from hikari.events import shard_events
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import traits
    from hikari.api import shard as gateway_shard
    from hikari.interactions import bases as interaction_bases
    from hikari.interactions import commands


class CommandEvent(shard_events.ShardEvent, abc.ABC):
    """Base class of events fired for changes to application commands."""

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.command.app

    @property
    @abc.abstractmethod
    def command(self) -> commands.Command:
        """Object of the command this event is for.

        Returns
        -------
        hikari.interactions.commands.Command
            The command this event is for.
        """


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class CommandCreateEvent(CommandEvent):
    """Event fired when a command is created relevant to the current bot.

    !!! note
        This includes applications created by other bots which share a guild
        with the current bot.
    """

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.

    command: commands.Command = attr.field(repr=True)
    # <<inherited docstring from CommandEvent>>.


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class CommandUpdateEvent(CommandEvent):
    """Event fired when a command is updated relevant to the current bot.

    !!! note
        This includes applications created by other bots which share a guild
        with the current bot.
    """

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.

    command: commands.Command = attr.field(repr=True)
    # <<inherited docstring from CommandEvent>>.


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class CommandDeleteEvent(CommandEvent):
    """Event fired when a command is deleted relevant to the current bot.

    !!! note
        This includes applications created by other bots which share a guild
        with the current bot.
    """

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.

    command: commands.Command = attr.field(repr=True)
    # <<inherited docstring from CommandEvent>>.


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
class InteractionCreateEvent(shard_events.ShardEvent):
    """Event fired when an interaction is created."""

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    """Shard that received this event."""

    interaction: interaction_bases.PartialInteraction = attr.field(repr=True)
    """Interaction that this event is related to.

    Returns
    -------
    hikari.interactions.bases.PartialInteraction
        Object of the interaction that this event is related to.
    """

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.interaction.app
