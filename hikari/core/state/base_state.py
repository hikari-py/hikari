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
"""Definition of the interface a compliant state implementation should provide.

State object handle decoding events and managing application state.
"""
__all__ = ["BaseState"]

import abc
import asyncio
import inspect
import typing

from hikari.core import entities
from hikari.core import events
from hikari.core.clients import shard_client
from hikari.internal import assertions
from hikari.internal import more_logging

EVENT_MARKER_ATTR = "___event_name___"

EventConsumerT = typing.Callable[[str, entities.RawEntityT], typing.Awaitable[None]]


def register_state_event_handler(name: str) -> typing.Callable[[EventConsumerT], EventConsumerT]:
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
        setattr(callable_item, EVENT_MARKER_ATTR, name)
        return callable_item

    return decorator


def _has_event_marker(obj: typing.Any) -> bool:
    return hasattr(obj, EVENT_MARKER_ATTR)


def _get_event_marker(obj: typing.Any) -> str:
    return getattr(obj, EVENT_MARKER_ATTR)


class BaseState(abc.ABC):
    """Abstract definition of a state manager.

    This is designed to manage any state-related operations in an application by
    consuming raw events from a low level gateway connection, transforming them
    to object-based event types, and tracking overall application state.

    Any methods marked with the :obj:`register_state_event_handler` decorator
    will be detected and registered as event handlers by the constructor.
    """

    @abc.abstractmethod
    def __init__(self):
        self.logger = more_logging.get_named_logger(self)
        self._event_mapping = {}

        # Look for events and register them.
        for _, member in inspect.getmembers(self, _has_event_marker):
            event = _get_event_marker(member)
            self._event_mapping[event] = member

    async def process_raw_event(
        self, shard_client_obj: shard_client.ShardClient, name: str, payload: entities.RawEntityT,
    ) -> None:
        """Process a low level event.

        This will update the internal state, perform processing where necessary,
        and then dispatch the event to any listeners.

        Parameters
        ----------
        shard_client_obj: :obj:`hikari.core.clients.shard_client.ShardClient`
            The shard that triggered this event.
        name : :obj:`str`
            The raw event name.
        payload : :obj:`dict`
            The payload that was sent.
        """
        try:
            handler = self._event_mapping[name]
        except KeyError:
            self.logger.debug("No handler for event %s is registered", name)
        else:
            event = await handler(shard_client_obj, payload)
            self.dispatch(event)

    @abc.abstractmethod
    def dispatch(self, event: events.HikariEvent) -> None:
        """Dispatch the given event somewhere."""
