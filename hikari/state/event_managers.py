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
__all__ = ["raw_event_mapper", "EventManager"]

import inspect

import typing

from hikari.clients import shard_client
from hikari.state import event_dispatchers
from hikari import entities
from hikari.state import raw_event_consumers
from hikari.internal import assertions
from hikari.internal import more_logging

EVENT_MARKER_ATTR = "___event_name___"

EventConsumerT = typing.Callable[[str, entities.RawEntityT], typing.Awaitable[None]]


def raw_event_mapper(name: str) -> typing.Callable[[EventConsumerT], EventConsumerT]:
    """Create a decorator for a coroutine function to register it as an event handler.

    Parameters
    ----------
    name: str
        The case sensitive name of the event to associate the annotated method
        with.

    Returns
    -------
    ``decorator(callable) -> callable``
        A decorator for a method.

    """

    def decorator(callable_item: EventConsumerT) -> EventConsumerT:
        assertions.assert_that(inspect.isfunction(callable_item), "Annotated element must be a function")
        event_set = getattr(callable_item, EVENT_MARKER_ATTR, set())
        event_set.add(name)
        setattr(callable_item, EVENT_MARKER_ATTR, event_set)
        return callable_item

    return decorator


def _has_event_marker(obj: typing.Any) -> bool:
    return hasattr(obj, EVENT_MARKER_ATTR)


def _get_event_marker(obj: typing.Any) -> typing.Set[str]:
    return getattr(obj, EVENT_MARKER_ATTR)


EventDispatcherT = typing.TypeVar("EventDispatcherT", bound=event_dispatchers.EventDispatcher)


class EventManager(typing.Generic[EventDispatcherT], raw_event_consumers.RawEventConsumer):
    """Abstract definition of the components for an event system for a bot.

    The class itself inherits from
    :obj:`hikari.state.raw_event_consumer.RawEventConsumer` (which allows
    it to provide the ability to transform a raw payload into an event object).

    This is designed as a basis to enable transformation of raw incoming events
    from the websocket into more usable native Python objects, and to then
    dispatch them to a given event dispatcher. It does not provide the logic for
    how to specifically parse each event however.

    Parameters
    ----------
    event_dispatcher_impl: :obj:`hikari.state.event_dispatcher.EventDispatcher`, optional
        An implementation of event dispatcher that will store individual events
        and manage dispatching them after this object creates them. If ``None``,
        then a default implementation is chosen.

    Notes
    -----
    This object will detect internal event mapper functions by looking for
    coroutine functions wrapped with :obj:`raw_event_mapper`.

    These methods are expected to have the following parameters:

        shard_obj: :obj:`hikari.clients.shard_client.ShardClient`
            The shard client that emitted the event.
        payload: :obj:`typing.Any`
            The received payload. This is expected to be a JSON-compatible type.

    For example, if you want to provide an implementation that can consume
    and handle ``MESSAGE_CREATE`` events, you can do the following.

    .. code-block:: python

        class MyMappingEventConsumer(MappingEventConsumer):
            @event_mapper("MESSAGE_CREATE")
            def _process_message_create(self, shard, payload) -> MessageCreateEvent:
                return MessageCreateEvent.deserialize(payload)

    The decorator can be stacked if you wish to provide one mapper

    ... it is pretty simple. This is exposed in this way to enable you to write
    code that may use a distributed system instead of a single-process bot.

    Writing to a message queue is pretty simple using this mechanism, as you can
    choose when and how to place the event on a queue to be consumed by other
    application components.

    For the sake of simplicity, Hikari only provides implementations for single
    process bots, since most of what you will need will be fairly bespoke if you
    want to implement anything more complicated; regardless, the tools are here
    for you to use as you see fit.

    Warnings
    --------
    This class provides the scaffold for making an event consumer, but does not
    physically implement the logic to deserialize and process specific events.

    To provide this, use one of the provided implementations of this class, or
    create your own as needed.
    """

    def __init__(self, event_dispatcher_impl: typing.Optional[EventDispatcherT] = None) -> None:
        if event_dispatcher_impl is None:
            event_dispatcher_impl = event_dispatchers.EventDispatcherImpl()

        self.logger = more_logging.get_named_logger(self)
        self.event_dispatcher = event_dispatcher_impl
        self.raw_event_mappers = {}

        # Look for events and register them.
        for _, member in inspect.getmembers(self, _has_event_marker):
            event_names = _get_event_marker(member)
            for event_name in event_names:
                self.raw_event_mappers[event_name] = member

    def process_raw_event(
        self, shard_client_obj: shard_client.ShardClient, name: str, payload: entities.RawEntityT,
    ) -> None:
        """Process a low level event.

        This will update the internal weaving, perform processing where necessary,
        and then dispatch the event to any listeners.

        Parameters
        ----------
        shard_client_obj: :obj:`hikari.clients.shard_client.ShardClient`
            The shard that triggered this event.
        name : :obj:`str`
            The raw event name.
        payload : :obj:`dict`
            The payload that was sent.
        """
        try:
            handler = self.raw_event_mappers[name]
        except KeyError:
            self.logger.debug("No handler for event %s is registered", name)
        else:
            event = handler(shard_client_obj, payload)
            self.event_dispatcher.dispatch_event(event)


class StatelessEventManagerImpl(EventManager[event_dispatchers.EventDispatcher]):
    """Stateless event manager implementation for stateless bots.

    This is an implementation that does not rely on querying prior information to
    operate. The implementation details of this are much simpler than a stateful
    version, and are not immediately affected by the use of intents.
    """
