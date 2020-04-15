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
"""Defines a facade around :obj:`~hikari.clients.shard_clients.ShardClient`.

This provides functionality such as keeping multiple shards alive
"""

__all__ = ["GatewayManager"]

import asyncio
import datetime
import math
import time
import typing

from hikari import events
from hikari import gateway_entities
from hikari import guilds
from hikari.clients import configs
from hikari.clients import runnable
from hikari.clients import shard_clients
from hikari.internal import conversions
from hikari.internal import more_logging
from hikari.state import event_dispatchers
from hikari.state import raw_event_consumers

ShardT = typing.TypeVar("ShardT", bound=shard_clients.ShardClient)


class GatewayManager(typing.Generic[ShardT], runnable.RunnableClient):
    """Provides a management layer for multiple-sharded bots.

    This also provides additional conduit used to connect up shards to the
    rest of this framework to enable management of dispatched events, etc.
    """

    def __init__(
        self,
        *,
        shard_ids: typing.Sequence[int],
        shard_count: int,
        config: configs.WebsocketConfig,
        url: str,
        raw_event_consumer_impl: raw_event_consumers.RawEventConsumer,
        shard_type: typing.Type[ShardT] = shard_clients.ShardClient,
        dispatcher: typing.Optional[event_dispatchers.EventDispatcher] = None,
    ) -> None:
        super().__init__(more_logging.get_named_logger(self, conversions.pluralize(shard_count, "shard")))
        self._is_running = False
        self.config = config
        self.raw_event_consumer = raw_event_consumer_impl
        self._dispatcher = dispatcher
        self.shards: typing.Dict[int, ShardT] = {
            shard_id: shard_type(shard_id, shard_count, config, raw_event_consumer_impl, url) for shard_id in shard_ids
        }
        self.shard_ids = shard_ids

    @property
    def latency(self) -> float:
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
            if not math.isnan(shard.latency):
                latencies.append(shard.latency)

        return sum(latencies) / len(latencies) if latencies else float("nan")

    async def start(self) -> None:
        """Start all shards.

        This safely starts all shards at the correct rate to prevent invalid
        session spam. This involves starting each shard sequentially with a
        5 second pause between each.
        """
        if self._is_running:
            raise RuntimeError("Cannot start a client twice.")

        if self._dispatcher is not None:
            await self._dispatcher.dispatch_event(events.StartingEvent())

        self._is_running = True
        self.logger.info("starting %s shard(s)", len(self.shards))
        start_time = time.perf_counter()
        for i, shard_id in enumerate(self.shard_ids):
            if i > 0:
                await asyncio.sleep(5)

            shard_obj = self.shards[shard_id]
            await shard_obj.start()
        finish_time = time.perf_counter()

        self.logger.info("started %s shard(s) in approx %.2fs", len(self.shards), finish_time - start_time)

        if self._dispatcher is not None:
            await self._dispatcher.dispatch_event(events.StartedEvent())

    async def join(self) -> None:
        """Wait for all shards to finish executing, then return."""
        await asyncio.gather(*(shard_obj.join() for shard_obj in self.shards.values()))

    async def close(self) -> None:
        """Close all shards.

        Waits for all shards to shut down before returning.
        """
        if self._is_running:
            self.logger.info("stopping %s shard(s)", len(self.shards))
            start_time = time.perf_counter()
            try:
                if self._dispatcher is not None:
                    await self._dispatcher.dispatch_event(events.StoppingEvent())
                await asyncio.gather(*(shard_obj.close() for shard_obj in self.shards.values()))
            finally:
                finish_time = time.perf_counter()
                self.logger.info("stopped %s shard(s) in approx %.2fs", len(self.shards), finish_time - start_time)
                self._is_running = False
                if self._dispatcher is not None:
                    await self._dispatcher.dispatch_event(events.StoppedEvent())

    async def update_presence(
        self,
        *,
        status: guilds.PresenceStatus = ...,
        activity: typing.Optional[gateway_entities.GatewayActivity] = ...,
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
                shard.update_presence(status=status, activity=activity, idle_since=idle_since, is_afk=is_afk)
                for shard in self.shards.values()
                if shard.connection_state
                in (shard_clients.ShardState.WAITING_FOR_READY, shard_clients.ShardState.READY)
            )
        )
