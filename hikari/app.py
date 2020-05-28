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
"""Core interfaces for a Hikari application."""
from __future__ import annotations

__all__ = ["IApp"]

import abc
import logging
import typing

from concurrent import futures

if typing.TYPE_CHECKING:
    import datetime

    from hikari import cache as cache_
    from hikari import entity_factory as entity_factory_
    from hikari import event_consumer as event_consumer_
    from hikari import event_dispatcher as event_dispatcher_
    from hikari.models import guilds
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
        """The optional library-wide thread-pool to utilise for file IO."""

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
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def event_dispatcher(self) -> event_dispatcher_.IEventDispatcher:
        """Event dispatcher and waiter."""


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
        """Mapping of each shard ID to the corresponding client for it."""

    @property
    @abc.abstractmethod
    def gateway_shard_count(self) -> int:
        """The number of shards in the entire distributed application."""

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
        status: guilds.PresenceStatus = ...,
        activity: typing.Optional[gateway.Activity] = ...,
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
        status : hikari.models.guilds.PresenceStatus
            If specified, the new status to set.
        activity : hikari.models.gateway.Activity | None
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
