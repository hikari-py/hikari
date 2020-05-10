#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""Basic single-application weaving manager."""

from __future__ import annotations

__all__ = ["raw_event_mapper", "EventManager"]

import inspect
import logging
import typing

from hikari.internal import assertions
from hikari.events import dispatchers, consumers

if typing.TYPE_CHECKING:
    from hikari.clients import components as _components
    from hikari.clients import shards

EVENT_MARKER_ATTR: typing.Final[str] = "___event_name___"

EventConsumerT = typing.Callable[[str, typing.Mapping[str, str]], typing.Awaitable[None]]


def raw_event_mapper(name: str) -> typing.Callable[[EventConsumerT], EventConsumerT]:
    """Create a decorator for a coroutine function to register it as an event handler.

    Parameters
    ----------
    name: str
        The case sensitive name of the event to associate the annotated method
        with.

    Returns
    -------
    decorator(T) -> T
        A decorator for a method.

    """

    def decorator(callable: EventConsumerT) -> EventConsumerT:
        assertions.assert_that(inspect.iscoroutinefunction(callable), "Annotated element must be a coroutine function")
        event_set = getattr(callable, EVENT_MARKER_ATTR, set())
        event_set.add(name)
        setattr(callable, EVENT_MARKER_ATTR, event_set)
        return callable

    return decorator


def _has_event_marker(obj: typing.Any) -> bool:
    return hasattr(obj, EVENT_MARKER_ATTR)


def _get_event_marker(obj: typing.Any) -> typing.Set[str]:
    return getattr(obj, EVENT_MARKER_ATTR)


EventDispatcherT = typing.TypeVar("EventDispatcherT", bound=dispatchers.EventDispatcher)


class EventManager(typing.Generic[EventDispatcherT], consumers.RawEventConsumer):
    """Abstract definition of the components for an event system for a bot.

    The class itself inherits from
    `hikari.state.consumers.RawEventConsumer` (which allows it to provide the
    ability to transform a raw payload into an event object).

    This is designed as a basis to enable transformation of raw incoming events
    from the websocket into more usable native Python objects, and to then
    dispatch them to a given event dispatcher. It does not provide the logic for
    how to specifically parse each event however.

    Parameters
    ----------
    components: hikari.clients.components.Components
        The client components that this event manager should be bound to.
        Includes the event dispatcher that will store individual events and
        manage dispatching them after this object creates them.

    !!! note
        This object will detect internal event mapper functions by looking for
        coroutine functions wrapped with `raw_event_mapper`.

        These methods are expected to have the following parameters:

        * shard_obj : `hikari.clients.shards.ShardClient`

            The shard client that emitted the event.

        * payload : `typing.Any`

            The received payload. This is expected to be a JSON-compatible type.

        For example, if you want to provide an implementation that can consume
        and handle `MESSAGE_CREATE` events, you can do the following.

            class MyMappingEventConsumer(MappingEventConsumer):
                @event_mapper("MESSAGE_CREATE")
                def _process_message_create(self, shard, payload) -> MessageCreateEvent:
                    return MessageCreateEvent.deserialize(payload)

        The decorator can be stacked if you wish to provide one mapper

        ... it is pretty simple. This is exposed in this way to enable you to
        write code that may use a distributed system instead of a single-process
        bot.

        Writing to a message queue is pretty simple using this mechanism, as you
        can choose when and how to place the event on a queue to be consumed by
        other application components.

        For the sake of simplicity, Hikari only provides implementations for
        single process bots, since most of what you will need will be fairly
        bespoke if you want to implement anything more complicated; regardless,
        the tools are here for you to use as you see fit.

    !!! warning
        This class provides the scaffold for making an event consumer, but doe
        not physically implement the logic to deserialize and process specific
        events.

        To provide this, use one of the provided implementations of this class,
        or create your own as needed.
    """

    def __init__(self, components: _components.Components) -> None:
        self.logger = logging.getLogger(type(self).__qualname__)
        self._components = components
        self.raw_event_mappers = {}

        # Look for events and register them.
        for _, member in inspect.getmembers(self, _has_event_marker):
            event_names = _get_event_marker(member)
            for event_name in event_names:
                self.raw_event_mappers[event_name] = member

    async def process_raw_event(
        self, shard_client_obj: shards.ShardClient, name: str, payload: typing.Mapping[str, typing.Any],
    ) -> None:
        """Process a low level event.

        This will update the internal weaving, perform processing where necessary,
        and then dispatch the event to any listeners.

        Parameters
        ----------
        shard_client_obj : hikari.clients.shards.ShardClient
            The shard that triggered this event.
        name : str
            The raw event name.
        payload : dict
            The payload that was sent.
        """
        try:
            handler = self.raw_event_mappers[name]
        except KeyError:
            self.logger.debug("no handler for event %s is registered", name)
            return

        try:
            await handler(shard_client_obj, payload)
        except Exception as ex:
            self.logger.exception(
                "Failed to unmarshal %r event payload. This is likely a bug in the library itself.", exc_info=ex,
            )
