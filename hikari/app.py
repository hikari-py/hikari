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
"""Core interfaces for types of Hikari application."""

from __future__ import annotations

__all__ = ["IApp", "IRESTApp", "IGatewayConsumer", "IGatewayDispatcher", "IGatewayZookeeper", "IBot"]

import abc
import functools
import logging
import typing

from hikari import event_dispatcher as event_dispatcher_
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from concurrent import futures
    import datetime

    from hikari import cache as cache_
    from hikari import entity_factory as entity_factory_
    from hikari import event_consumer as event_consumer_
    from hikari.models import presences
    from hikari import http_settings as http_settings_
    from hikari.net import gateway
    from hikari.net import rest as rest_


class IApp(abc.ABC):
    """Core components that any Hikari-based application will usually need."""

    __slots__ = ()

    @property
    @abc.abstractmethod
    def logger(self) -> logging.Logger:
        """Logger for logging messages."""

    @property
    @abc.abstractmethod
    def cache(self) -> cache_.ICache:
        """Entity cache."""

    @property
    @abc.abstractmethod
    def entity_factory(self) -> entity_factory_.IEntityFactory:
        """Entity creator and updater facility."""

    @property
    @abc.abstractmethod
    def thread_pool(self) -> typing.Optional[futures.ThreadPoolExecutor]:
        """Thread-pool to utilise for file IO within the library, if set."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Safely shut down all resources."""


class IRESTApp(IApp, abc.ABC):
    """Component specialization that is used for REST-only applications.

    Examples may include web dashboards, or applications where no gateway
    connection is required. As a result, no event conduit is provided by
    these implementations.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def rest(self) -> rest_.REST:
        """REST API."""


class IGatewayConsumer(IApp, abc.ABC):
    """Component specialization that supports consumption of raw events.

    This may be combined with `IGatewayZookeeper` for most single-process
    bots, or may be a specific component for large distributed applications
    that consume events from a message queue, for example.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def event_consumer(self) -> event_consumer_.IEventConsumer:
        """Raw event consumer."""


class IGatewayDispatcher(IApp, abc.ABC):
    """Component specialization that supports dispatching of events.

    These events are expected to be instances of
    `hikari.events.base.HikariEvent`.

    This may be combined with `IGatewayZookeeper` for most single-process
    bots, or may be a specific component for large distributed applications
    that consume events from a message queue, for example.

    This purposely also implements some calls found in
    `hikari.event_dispatcher.IEventDispatcher` with defaulting delegated calls
    to the event dispatcher. This provides a more intuitive syntax for
    applications.

        # We can now do this...

        >>> @bot.listen()
        >>> async def on_message(event: hikari.MessageCreateEvent) -> None: ...

        # ...instead of having to do this...

        >>> @bot.listen(hikari.MessageCreateEvent)
        >>> async def on_message(event: hikari.MessageCreateEvent) -> None: ...

    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def event_dispatcher(self) -> event_dispatcher_.IEventDispatcher:
        """Event dispatcher and waiter."""

    # Do not add type hints to me! I delegate to a documented method elsewhere!
    @functools.wraps(event_dispatcher_.IEventDispatcher.listen)
    def listen(self, event_type=undefined.Undefined()):
        ...

    # Do not add type hints to me! I delegate to a documented method elsewhere!
    @functools.wraps(event_dispatcher_.IEventDispatcher.subscribe)
    def subscribe(self, event_type, callback):
        ...

    # Do not add type hints to me! I delegate to a documented method elsewhere!
    @functools.wraps(event_dispatcher_.IEventDispatcher.unsubscribe)
    def unsubscribe(self, event_type, callback):
        ...

    # Do not add type hints to me! I delegate to a documented method elsewhere!
    @functools.wraps(event_dispatcher_.IEventDispatcher.wait_for)
    async def wait_for(self, event_type, predicate, timeout):
        ...

    # Do not add type hints to me! I delegate to a documented method elsewhere!
    @functools.wraps(event_dispatcher_.IEventDispatcher.dispatch)
    def dispatch(self, event):
        ...


class IGatewayZookeeper(IGatewayConsumer, abc.ABC):
    """Component specialization that looks after a set of shards.

    These events will be produced by a low-level gateway implementation, and
    will produce `list` and `dict` types only.

    This may be combined with `IGatewayDispatcher` for most single-process
    bots, or may be a specific component for large distributed applications
    that feed new events into a message queue, for example.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def gateway_shards(self) -> typing.Mapping[int, gateway.Gateway]:
        """Map of each shard ID to the corresponding client for it.

        If the shards have not started, and auto=sharding is in-place, then it
        is acceptable for this to return an empty mapping.
        """

    @property
    @abc.abstractmethod
    def gateway_shard_count(self) -> int:
        """Amount of shards in the entire distributed application.

        If the shards have not started, and auto=sharding is in-place, then it
        is acceptable for this to return `0`.
        """

    @abc.abstractmethod
    async def start(self) -> None:
        """Start all shards and wait for them to be READY."""

    @abc.abstractmethod
    async def join(self) -> None:
        """Wait for all shards to shut down."""

    @abc.abstractmethod
    async def update_presence(
        self,
        *,
        status: presences.PresenceStatus = ...,
        activity: typing.Optional[presences.OwnActivity] = ...,
        idle_since: typing.Optional[datetime.datetime] = ...,
        is_afk: bool = ...,
    ) -> None:
        """Update the presence of the user for all shards.

        This will only update arguments that you explicitly specify a value for.
        Any arguments that you do not explicitly provide some value for will
        not be changed.

        !!! warning
            This will only apply to connected shards.

        !!! note
            If you wish to update a presence for a specific shard, you can do
            this by using the `gateway_shards` `typing.Mapping` to find the
            shard you wish to update.

        Parameters
        ----------
        status : hikari.models.presences.PresenceStatus
            If specified, the new status to set.
        activity : hikari.models.presences.OwnActivity | None
            If specified, the new activity to set.
        idle_since : datetime.datetime | None
            If specified, the time to show up as being idle since,
            or `None` if not applicable.
        is_afk : bool
            If specified, `True` if the user should be marked as AFK,
            or `False` otherwise.
        """

    @abc.abstractmethod
    def run(self) -> None:
        """Execute this component on an event loop.

        Performs the same job as `RunnableClient.start`, but provides additional
        preparation such as registering OS signal handlers for interrupts,
        and preparing the initial event loop.

        This enables the client to be run immediately without having to
        set up the `asyncio` event loop manually first.
        """


class IBot(IRESTApp, IGatewayZookeeper, IGatewayDispatcher, abc.ABC):
    """Component for single-process bots.

    Bots are components that have access to a REST API, an event dispatcher,
    and an event consumer.

    Additionally, bots will contain a collection of Gateway client objects.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def http_settings(self) -> http_settings_.HTTPSettings:
        """The HTTP settings to use."""
