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

from hikari.api import event_dispatcher as event_dispatcher_
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from concurrent import futures
    import datetime

    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import event_consumer as event_consumer_
    from hikari.models import presences
    from hikari.net import http_settings as http_settings_
    from hikari.net import gateway
    from hikari.net import rest as rest_


class IApp(abc.ABC):
    """The base for any type of Hikari application object.

    All types of Hikari-based application should derive from this type in order
    to provide a consistent interface that is compatible with models and events
    that make reference to it.

    Following this pattern allows you to extend this library in pretty much
    any direction you can think of without having to rewrite major piece of
    this code base.

    Example
    -------
    A quick and dirty theoretical concrete implementation may look like the
    following.

    ```py
    class MyApp(IApp):
        def __init__(self):
            self._logger = logging.getLogger(__name__)
            self._cache = MyCacheImplementation(self)
            self._entity_factory = MyEntityFactoryImplementation(self)
            self._thread_pool = concurrent.futures.ThreadPoolExecutor()

        logger = property(lambda self: self._logger)
        cache = property(lambda self: self._cache)
        entity_factory = property(lambda self: self._entity_factory)
        thread_pool = property(lambda self: self._thread_pool)

        async def close(self):
            self._thread_pool.shutdown()
    ```

    If you are in any doubt, check out the `hikari.RESTApp` and `hikari.Bot`
    implementations to see how they are pieced together!
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def logger(self) -> logging.Logger:
        """Logger for logging messages.

        Returns
        -------
        logging.Logger
            The application-level logger.
        """

    @property
    @abc.abstractmethod
    def cache(self) -> cache_.ICache:
        """Entity cache.

        Returns
        -------
        hikari.api.cache.ICache
            The cache implementation used in this application.
        """

    @property
    @abc.abstractmethod
    def entity_factory(self) -> entity_factory_.IEntityFactory:
        """Entity creator and updater facility.

        Returns
        -------
        hikari.api.entity_factory.IEntityFactory
            The factory object used to produce and update Python entities.
        """

    @property
    @abc.abstractmethod
    def thread_pool(self) -> typing.Optional[futures.ThreadPoolExecutor]:
        """Thread-pool to utilise for file IO within the library, if set.

        Returns
        -------
        concurrent.futures.ThreadPoolExecutor or None
            The custom thread-pool being used for blocking IO. If the
            default event loop thread-pool is being used, then this will
            return `None` instead.
        """

    @abc.abstractmethod
    async def close(self) -> None:
        """Safely shut down all resources."""


class IRESTApp(IApp, abc.ABC):
    """Component specialization that is used for REST-only applications.

    Examples may include web dashboards, or applications where no gateway
    connection is required. As a result, no event conduit is provided by
    these implementations. They do however provide a REST client, and the
    general components defined in `IApp`
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def rest(self) -> rest_.REST:
        """REST API Client.

        Use this to make calls to Discord's REST API over HTTPS.

        Returns
        -------
        hikari.net.rest.REST
            The REST API client.
        """


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
        """Raw event consumer.

        This should be passed raw event payloads from your gateway
        websocket implementation.

        Returns
        -------
        hikari.api.event_consumer.IEventConsumer
            The event consumer implementation in-use.
        """


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

    ```py

    # We can now do this...

    >>> @bot.listen()
    >>> async def on_message(event: hikari.MessageCreateEvent) -> None: ...

    # ...instead of having to do this...

    >>> @bot.listen(hikari.MessageCreateEvent)
    >>> async def on_message(event: hikari.MessageCreateEvent) -> None: ...
    ```

    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def event_dispatcher(self) -> event_dispatcher_.IEventDispatcher:
        """Event dispatcher and subscription manager.

        This stores every event you subscribe to in your application, and
        manages invoking those subscribed callbacks when the corresponding
        event occurs.

        Event dispatchers also provide a `wait_for` functionality that can be
        used to wait for a one-off event that matches a certain criteria. This
        is useful if waiting for user feedback for a specific procedure being
        performed.

        Users may create their own events and trigger them using this as well,
        thus providing a simple in-process event bus that can easily be extended
        with a little work to span multiple applications in a distributed
        cluster.

        Returns
        -------
        hikari.api.event_dispatcher.IEventDispatcher
            The event dispatcher in use.
        """

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

        !!! note
            "Non-sharded" bots should expect one value to be in this mapping
            under the shard ID `0`.

                >>> bot.gateway_shards[0].heartbeat_latency
                0.145612141

        Returns
        -------
        typing.Mapping[int, hikari.net.gateway.Gateway]
            The mapping of shard IDs to gateway connections for the
            corresponding shard. These shard IDs are 0-indexed.
        """

    @property
    @abc.abstractmethod
    def gateway_shard_count(self) -> int:
        """Count the number of shards in the entire distributed application.

        If the shards have not started, and auto-sharding is in-place, then it
        is acceptable for this to return `0`. When the application is running,
        this should always be a non-zero natural number that is greater than the
        maximum ID in `gateway_shards`.

        Returns
        -------
        int
            The number of shards in the entire application.
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
        status: typing.Union[undefined.Undefined, presences.PresenceStatus] = undefined.Undefined(),
        activity: typing.Union[undefined.Undefined, presences.OwnActivity, None] = undefined.Undefined(),
        idle_since: typing.Union[undefined.Undefined, datetime.datetime, None] = undefined.Undefined(),
        is_afk: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
    ) -> None:
        """Update the presence of the user for all shards.

        This will only update arguments that you explicitly specify a value for.
        Any arguments that you do not explicitly provide some value for will
        not be changed (these values will default to be `undefined`).

        !!! warning
            This will only apply to connected shards.

        !!! note
            If you wish to update a presence for a specific shard, you can do
            this by using the `gateway_shards` `typing.Mapping` to find the
            shard you wish to update.

        Parameters
        ----------
        status : hikari.models.presences.PresenceStatus or hikari.utilities.undefined.Undefined
            If defined, the new status to set.
        activity : hikari.models.presences.OwnActivity or None or hikari.utilities.undefined.Undefined
            If defined, the new activity to set.
        idle_since : datetime.datetime or None or hikari.utilities.undefined.Undefined
            If defined, the time to show up as being idle since, or `None` if
            not applicable. If undefined, then it is not changed.
        is_afk : bool or hikari.utilities.undefined.Undefined
            If defined, `True` if the user should be marked as AFK,
            or `False` if not AFK.
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
    """Base for bot applications.

    Bots are components that have access to a REST API, an event dispatcher,
    and an event consumer.

    Additionally, bots will contain a collection of Gateway client objects.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def http_settings(self) -> http_settings_.HTTPSettings:
        """HTTP settings to use for the shards when they get created.

        !!! info
            This is stored only for bots, since shards are generated lazily on
            start-up once sharding information has been retrieved from the REST
            API. To do this, an event loop has to be running first.

        Returns
        -------
        hikari.net.http_settings.HTTPSettings
            The HTTP settings to use.
        """
