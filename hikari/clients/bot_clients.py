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
__all__ = ["BotBase", "StatelessBot"]

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
from hikari.clients import rest_clients
from hikari.clients import runnable
from hikari.clients import shard_clients
from hikari.internal import conversions
from hikari.internal import more_collections
from hikari.internal import more_typing
from hikari.state import event_dispatchers
from hikari.state import event_managers
from hikari.state import stateless_event_managers

ShardClientT = typing.TypeVar("ShardClientT", bound=shard_clients.ShardClient)
EventManagerT = typing.TypeVar("EventManagerT", bound=event_managers.EventManager)
RESTClientT = typing.TypeVar("RESTClientT", bound=rest_clients.RESTClient)
BotConfigT = typing.TypeVar("BotConfigT", bound=configs.BotConfig)


class BotBase(
    typing.Generic[ShardClientT, RESTClientT, EventManagerT, BotConfigT],
    runnable.RunnableClient,
    event_dispatchers.EventDispatcher,
    abc.ABC,
):
    """An abstract base class for a bot implementation.

    This takes several generic parameter types in the following order:
    - ``ShardClientT`` - the implementation of
        :obj:`~hikari.clients.shard_clients.ShardClient` to use for shards.
    - ``RESTClientT`` - the implementation of
        :obj:`~hikari.clients.rest_clients.RESTClient` to use for API calls.
    - ``EventManagerT`` - the implementation of
        :obj:`~hikari.state.event_managers.EventManager` to use for
        event management, translation, and dispatching.
    - ``BotConfigT`` - the implementation of
        :obj:`~hikari.clients.configs.BotConfig` to read component-specific
        details from.

    Parameters
    ----------
    config : :obj:`~hikari.clients.configs.BotConfig`
        The config object to use.
    """

    #: The config for this bot.
    #:
    #: :type: :obj:`~hikari.clients.configs.BotConfig`
    _config: BotConfigT

    #: The event manager for this bot.
    #:
    #: :type: an implementation instance of :obj:`~hikari.state.event_managers.EventManager`
    event_manager: EventManagerT

    #: The logger to use for this bot.
    #:
    #: :type: :obj:`~logging.Logger`
    logger: logging.Logger

    #: The REST HTTP client to use for this bot.
    #:
    #: :type: :obj:`~hikari.clients.rest_clients.RESTClient`
    rest: RESTClientT

    #: Shards registered to this bot.
    #:
    #: These will be created once the bot has started execution.
    #:
    #: :type: :obj:`~typing.Mapping` [ :obj:`~int`, ? extends :obj:`~hikari.clients.shard_client.ShardClient` ]
    shards: typing.Mapping[int, ShardClientT]

    @abc.abstractmethod
    def __init__(self, config: configs.BotConfig) -> None:
        super().__init__(logging.getLogger(f"hikari.{type(self).__qualname__}"))
        self._config = config
        self.event_manager = self._create_event_manager()
        self.rest = self._create_rest(config)
        self.shards = more_collections.EMPTY_DICT

    @property
    def heartbeat_latency(self) -> float:
        """Average heartbeat latency for all valid shards.

        This will return a mean of all the heartbeat intervals for all shards
        with a valid heartbeat latency that are in the
        :obj:`~hikari.clients.shard_clients.ShardState.READY` state.

        If no shards are in this state, this will return ``float('nan')``
        instead.

        Returns
        -------
        :obj:`~float`
            The mean latency for all ``READY`` shards that have sent at least
            one acknowledged ``HEARTBEAT`` payload. If there is not at least
            one shard that meets this criteria, this will instead return
            ``float('nan')``.
        """
        latencies = []
        for shard in self.shards.values():
            if not math.isnan(shard.heartbeat_latency):
                latencies.append(shard.heartbeat_latency)

        return sum(latencies) / len(latencies) if latencies else float("nan")

    @property
    def total_disconnect_count(self) -> int:
        """Total number of times any shard has disconnected.

        Returns
        -------
        :obj:`int`
            Total disconnect count.
        """
        return sum(s.disconnect_count for s in self.shards.values())

    @property
    def total_reconnect_count(self) -> int:
        """Total number of times any shard has reconnected.

        Returns
        -------
        :obj:`int`
            Total reconnect count.
        """
        return sum(s.reconnect_count for s in self.shards.values())

    @property
    def intents(self) -> typing.Optional[intents.Intent]:
        """Intent values that any shard connections will be using.

        Returns
        -------
        :obj:`~hikari.intents.Intent`, optional
            A :obj:`~enum.IntFlag` enum containing each intent that is set. If
            intents are not being used at all, then this will return
            :obj:`~None` instead.
        """
        return self._config.intents

    @property
    def version(self) -> float:
        """Version being used for the gateway API.

        Returns
        -------
        :obj:`~int`
            The API version being used.
        """
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

        shards = {}
        for shard_id in shard_ids:
            shard = self._create_shard(shard_id, shard_count, url, self._config, self.event_manager)
            shards[shard_id] = shard

        self.shards = shards

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
        self, event_type: typing.Type[event_dispatchers.EventT], callback: event_dispatchers.EventCallbackT
    ) -> event_dispatchers.EventCallbackT:
        return self.event_manager.event_dispatcher.add_listener(event_type, callback)

    def remove_listener(
        self, event_type: typing.Type[event_dispatchers.EventT], callback: event_dispatchers.EventCallbackT
    ) -> event_dispatchers.EventCallbackT:
        return self.event_manager.event_dispatcher.remove_listener(event_type, callback)

    def wait_for(
        self,
        event_type: typing.Type[event_dispatchers.EventT],
        *,
        timeout: typing.Optional[float],
        predicate: event_dispatchers.PredicateT,
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

        Warning
        -------
        This will only apply to connected shards.

        Notes
        -----
        If you wish to update a presence for a specific shard, you can do this
        by using the ``shards`` :obj:`~typing.Mapping` to find the shard you
        wish to update.

        Parameters
        ----------
        status : :obj:`~hikari.guilds.PresenceStatus`
            If specified, the new status to set.
        activity : :obj:`~hikari.gateway_entities.GatewayActivity`, optional
            If specified, the new activity to set.
        idle_since : :obj:`~datetime.datetime`, optional
            If specified, the time to show up as being idle since,
            or :obj:`~None` if not applicable.
        is_afk : :obj:`~bool`
            If specified, :obj:`~True` if the user should be marked as AFK,
            or :obj:`~False` otherwise.
        """
        await asyncio.gather(
            *(
                s.update_presence(status=status, activity=activity, idle_since=idle_since, is_afk=is_afk)
                for s in self.shards.values()
                if s.connection_state in (shard_clients.ShardState.WAITING_FOR_READY, shard_clients.ShardState.READY)
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
        shard_id : :obj:`~int`
            The shard ID to use.
        shard_count : :obj:`~int`
            The shard count to use.
        url : :obj:`~str`
            The gateway URL to connect to.
        config : :obj:`~hikari.clients.configs.BotConfig`
            The bot config to use.
        event_manager :obj:`~hikari.state.event_managers.EventManager`
            The event manager to use.

        Returns
        -------
        :obj:`~hikari.clients.shard_clients.ShardClient`
            The shard client implementation to use for the given shard ID.

        Notes
        -----
        The ``shard_id`` and ``shard_count`` may be set within the ``config``
        object passed, but any conforming implementations are expected to
        use the value passed in the ``shard_id` and ``shard_count`` parameters
        regardless. Failure to do so may result in an invalid sharding
        configuration being used.

        """

    @classmethod
    @abc.abstractmethod
    def _create_rest(cls, config: BotConfigT) -> RESTClientT:
        """Return a new REST client from the given configuration.

        Parameters
        ----------
        config : :obj:`~hikari.clients.configs.BotConfig`
            The bot config to use.

        Returns
        -------
        :obj:`~hikari.clients.rest_clients.RESTClient`
            The REST client to use.

        """

    @classmethod
    @abc.abstractmethod
    def _create_event_manager(cls):
        """Return a new instance of an event manager implementation.

        Returns
        -------
        :obj:`~hikari.state.event_managers.EventManager`
            The event manager to use internally.
        """


class StatelessBot(
    BotBase[
        shard_clients.ShardClientImpl,
        rest_clients.RESTClient,
        stateless_event_managers.StatelessEventManagerImpl,
        configs.BotConfig,
    ]
):
    """Bot client without any state internals."""

    def __init__(self, config=configs.BotConfig) -> None:
        super().__init__(config)

    @classmethod
    def _create_shard(
        cls,
        shard_id: int,
        shard_count: int,
        url: str,
        config: configs.BotConfig,
        event_manager: stateless_event_managers.StatelessEventManagerImpl,
    ) -> shard_clients.ShardClientImpl:
        return shard_clients.ShardClientImpl(
            shard_id=shard_id,
            shard_count=shard_count,
            config=config,
            raw_event_consumer_impl=event_manager,
            url=url,
            dispatcher=event_manager.event_dispatcher,
        )

    @classmethod
    def _create_rest(cls, config: BotConfigT) -> rest_clients.RESTClient:
        return rest_clients.RESTClient(config)

    @classmethod
    def _create_event_manager(cls) -> EventManagerT:
        return stateless_event_managers.StatelessEventManagerImpl()
