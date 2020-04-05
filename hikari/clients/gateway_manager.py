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
"""Defines a facade around :obj:`hikari.clients.shard_client.ShardClient`.

This provides functionality such as keeping multiple shards alive
"""

__all__ = ["GatewayManager"]

import asyncio
import time
import typing

from hikari.clients import configs
from hikari.clients import runnable
from hikari.internal import conversions
from hikari.internal import more_logging
from hikari.clients import shard_client
from hikari.state import raw_event_consumers

ShardT = typing.TypeVar("ShardT", bound=shard_client.ShardClient)


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
        shard_type: typing.Type[ShardT] = shard_client.ShardClient,
    ) -> None:
        super().__init__(more_logging.get_named_logger(self, conversions.pluralize(shard_count, "shard")))
        self._is_running = False
        self.config = config
        self.raw_event_consumer = raw_event_consumer_impl
        self.shards: typing.Dict[int, ShardT] = {
            shard_id: shard_type(shard_id, shard_count, config, raw_event_consumer_impl, url) for shard_id in shard_ids
        }
        self.shard_ids = shard_ids

    async def start(self) -> None:
        """Start all shards.

        This safely starts all shards at the correct rate to prevent invalid
        session spam. This involves starting each shard sequentially with a
        5 second pause between each.
        """
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

    async def join(self) -> None:
        """Wait for all shards to finish executing, then return."""
        await asyncio.gather(*(shard_obj.join() for shard_obj in self.shards.values()))

    async def close(self, wait: bool = True) -> None:
        """Close all shards.

        Parameters
        ----------
        wait : :obj:`bool`
            If ``True`` (the default), then once called, this will wait until
            all shards have shut down before returning. If ``False``, it will
            only send the signal to shut down, but will return immediately.
        """
        if self._is_running:
            self.logger.info("stopping %s shard(s)", len(self.shards))
            start_time = time.perf_counter()
            try:
                await asyncio.gather(*(shard_obj.close(wait) for shard_obj in self.shards.values()))
            finally:
                finish_time = time.perf_counter()
                self.logger.info("stopped %s shard(s) in approx %.2fs", len(self.shards), finish_time - start_time)
                self._is_running = False
