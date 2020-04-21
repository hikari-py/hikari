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
"""A bot client might go here... eventually..."""
__all__ = ["BotBase"]

import abc
import asyncio
import datetime
import logging
import math
import time
import typing

from hikari import events
from hikari import gateway_entities
from hikari import guilds
from hikari import intents
from hikari.clients import configs
from hikari.clients import rest
from hikari.clients import runnable
from hikari.clients import shards
from hikari.internal import conversions
from hikari.internal import more_collections
from hikari.internal import more_typing
from hikari.state import dispatchers
from hikari.state import event_managers

ShardClientT = typing.TypeVar("ShardClientT", bound=shards.ShardClient)
EventManagerT = typing.TypeVar("EventManagerT", bound=event_managers.EventManager)
EventDispatcherT = typing.TypeVar("EventDispatcherT", bound=dispatchers.EventDispatcher)
RESTClientT = typing.TypeVar("RESTClientT", bound=rest.RESTClient)
BotConfigT = typing.TypeVar("BotConfigT", bound=configs.BotConfig)


class BotBase(
    typing.Generic[ShardClientT, RESTClientT, EventDispatcherT, EventManagerT, BotConfigT],
    runnable.RunnableClient,
    dispatchers.EventDispatcher,
    abc.ABC,
):
    """An abstract base class for a bot implementation.

    This takes several generic parameter types in the following order:

    * `ShardClientT` - the implementation of
        `hikari.clients.shards.ShardClient` to use for shards.
    * `RESTClientT` - the implementation of
        `hikari.clients.rest.RESTClient` to use for API calls.
    * `EventDispatcherT` - the implementation of
        `hikari.state.dispatchers.EventDispatcher` to use for
        dispatching events. This class will then delegate any calls inherited
        from `hikari.state.dispatchers.EventDispatcher` to that
        implementation when provided.
    * `EventManagerT` - the implementation of
        `hikari.state.event_managers.EventManager` to use for
        event management, translation, and dispatching.
    * `BotConfigT` - the implementation of
        `hikari.clients.configs.BotConfig` to read component-specific
        details from.

    Parameters
    ----------
    config : hikari.clients.configs.BotConfig
        The config object to use.
    """

    _config: BotConfigT
    """The config for this bot."""

    event_dispatcher: EventDispatcherT
    """The event dispatcher for this bot."""

    event_manager: EventManagerT
    """The event manager for this bot."""

    logger: logging.Logger
    """The logger to use for this bot."""

    rest: RESTClientT
    """The REST HTTP client to use for this bot."""

    shards: typing.Mapping[int, ShardClientT]
    """Shards registered to this bot.

    These will be created once the bot has started execution.
    """

    def __init__(self, config: configs.BotConfig) -> None:
        super().__init__(logging.getLogger(f"hikari.{type(self).__qualname__}"))
        self._config = config
        self.event_dispatcher = self._create_event_dispatcher(config)
        self.event_manager = self._create_event_manager(config, self.event_dispatcher)
        self.rest = self._create_rest(config)
        self.shards = more_collections.EMPTY_DICT

    @property
    def heartbeat_latency(self) -> float:
        """Average heartbeat latency for all valid shards.

        This will return a mean of all the heartbeat intervals for all shards
        with a valid heartbeat latency that are in the
        `hikari.clients.shards.ShardState.READY` state.

        If no shards are in this state, this will return `float("nan")`
        instead.

        Returns
        -------
        float
            The mean latency for all `READY` shards that have sent at least
            one acknowledged `HEARTBEAT` payload. If there is not at least
            one shard that meets this criteria, this will instead return
            `float("nan")`.
        """
        latencies = []
        for shard in self.shards.values():
            if not math.isnan(shard.heartbeat_latency):
                latencies.append(shard.heartbeat_latency)

        return sum(latencies) / len(latencies) if latencies else float("nan")

    @property
    def total_disconnect_count(self) -> int:
        """Total number of times any shard has disconnected."""
        return sum(s.disconnect_count for s in self.shards.values())

    @property
    def total_reconnect_count(self) -> int:
        """Total number of times any shard has reconnected."""
        return sum(s.reconnect_count for s in self.shards.values())

    @property
    def intents(self) -> typing.Optional[intents.Intent]:  # noqa: D401
        """Intents that are in use for the connection.

        If intents are not being used at all, then this will be `None` instead.
        """
        return self._config.intents

    @property
    def version(self) -> float:
        """Version being used for the gateway API."""
        return self._config.gateway_version

    async def start(self):
        if self.shards:
            raise RuntimeError("Bot is already running.")

        gateway_bot = await self.rest.fetch_gateway_bot()

        self.logger.info(
            "you have sent an IDENTIFY %s time(s) before now, and have %s remaining. This will reset at %s.",
            gateway_bot.session_start_limit.total - gateway_bot.session_start_limit.remaining,
            gateway_bot.session_start_limit.remaining,
            datetime.datetime.now() + gateway_bot.session_start_limit.reset_after,
        )

        shard_count = self._config.shard_count if self._config.shard_count else gateway_bot.shard_count
        shard_ids = self._config.shard_ids if self._config.shard_ids else [*range(shard_count)]
        url = gateway_bot.url

        self.logger.info("will connect shards to %s", url)

        shard_clients = {}
        for shard_id in shard_ids:
            shard = self._create_shard(shard_id, shard_count, url, self._config, self.event_manager)
            shard_clients[shard_id] = shard

        self.shards = shard_clients

        self.logger.info("starting %s", conversions.pluralize(len(self.shards), "shard"))

        start_time = time.perf_counter()

        for i, shard_id in enumerate(self.shards):
            if i > 0:
                self.logger.info("idling for 5 seconds to avoid an invalid session")
                await asyncio.sleep(5)

            shard_obj = self.shards[shard_id]
            await shard_obj.start()

        finish_time = time.perf_counter()

        self.logger.info("started %s shard(s) in approx %.2fs", len(self.shards), finish_time - start_time)

        if self.event_manager is not None:
            await self.dispatch_event(events.StartedEvent())

    async def close(self) -> None:
        try:
            if self.shards:
                self.logger.info("stopping %s shard(s)", len(self.shards))
                start_time = time.perf_counter()
                try:
                    await self.dispatch_event(events.StoppingEvent())
                    await asyncio.gather(*(shard_obj.close() for shard_obj in self.shards.values()))
                finally:
                    finish_time = time.perf_counter()
                    self.logger.info("stopped %s shard(s) in approx %.2fs", len(self.shards), finish_time - start_time)
                    await self.dispatch_event(events.StoppedEvent())
        finally:
            await self.rest.close()

    async def join(self) -> None:
        await asyncio.gather(*(shard_obj.join() for shard_obj in self.shards.values()))

    def add_listener(
        self, event_type: typing.Type[dispatchers.EventT], callback: dispatchers.EventCallbackT, **kwargs
    ) -> dispatchers.EventCallbackT:
        return self.event_manager.event_dispatcher.add_listener(event_type, callback, _stack_level=4)

    def remove_listener(
        self, event_type: typing.Type[dispatchers.EventT], callback: dispatchers.EventCallbackT
    ) -> dispatchers.EventCallbackT:
        return self.event_manager.event_dispatcher.remove_listener(event_type, callback)

    def wait_for(
        self,
        event_type: typing.Type[dispatchers.EventT],
        *,
        timeout: typing.Optional[float],
        predicate: dispatchers.PredicateT,
    ) -> more_typing.Future:
        return self.event_manager.event_dispatcher.wait_for(event_type, timeout=timeout, predicate=predicate)

    def dispatch_event(self, event: events.HikariEvent) -> more_typing.Future[typing.Any]:
        return self.event_manager.event_dispatcher.dispatch_event(event)

    async def update_presence(
        self,
        *,
        status: guilds.PresenceStatus = ...,
        activity: typing.Optional[gateway_entities.Activity] = ...,
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
            If you wish to update a presence for a specific shard, you can do this
            by using the `shards` `typing.Mapping` to find the shard you wish to
            update.

        Parameters
        ----------
        status : hikari.guilds.PresenceStatus
            If specified, the new status to set.
        activity : hikari.gateway_entities.Activity, optional
            If specified, the new activity to set.
        idle_since : datetime.datetime, optional
            If specified, the time to show up as being idle since,
            or `None` if not applicable.
        is_afk : bool
            If specified, `True` if the user should be marked as AFK,
            or `False` otherwise.
        """
        await asyncio.gather(
            *(
                s.update_presence(status=status, activity=activity, idle_since=idle_since, is_afk=is_afk)
                for s in self.shards.values()
                if s.connection_state in (shards.ShardState.WAITING_FOR_READY, shards.ShardState.READY)
            )
        )

    @classmethod
    @abc.abstractmethod
    def _create_shard(
        cls, shard_id: int, shard_count: int, url: str, config: BotConfigT, event_manager: EventManagerT,
    ) -> ShardClientT:
        """Return a new shard for the given parameters.

        Parameters
        ----------
        shard_id : int
            The shard ID to use.
        shard_count : int
            The shard count to use.
        url : str
            The gateway URL to connect to.
        config : hikari.clients.configs.BotConfig
            The bot config to use.
        event_manager hikari.state.event_managers.EventManager
            The event manager to use.

        Returns
        -------
        hikari.clients.shards.ShardClient
            The shard client implementation to use for the given shard ID.

        !!! note
            The `shard_id` and `shard_count` may be set within the `config`
            object passed, but any conforming implementations are expected to
            use the value passed in the `shard_id` and `shard_count` parameters
            regardless. Failure to do so may result in an invalid sharding
            configuration being used.
        """

    @classmethod
    @abc.abstractmethod
    def _create_rest(cls, config: BotConfigT) -> RESTClientT:
        """Return a new REST client from the given configuration.

        Parameters
        ----------
        config : hikari.clients.configs.BotConfig
            The bot config to use.

        Returns
        -------
        hikari.clients.rest.RESTClient
            The REST client to use.

        """

    @classmethod
    @abc.abstractmethod
    def _create_event_manager(cls, config: BotConfigT, dispatcher: EventDispatcherT) -> EventManagerT:
        """Return a new instance of an event manager implementation.

        Parameters
        ----------
        config : hikari.clients.configs.BotConfig
            The bot config to use.

        Returns
        -------
        hikari.state.event_managers.EventManager
            The event manager to use internally.

        """

    @classmethod
    @abc.abstractmethod
    def _create_event_dispatcher(cls, config: BotConfigT) -> EventDispatcherT:
        """Return a new instance of an event dispatcher implementation.

        Parameters
        ----------
        config : hikari.clients.configs.BotConfig`
            The bot config to use.

        Returns
        -------
        hikari.state.dispatchers.EventDispatcher
        """
