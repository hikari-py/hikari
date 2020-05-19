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
from __future__ import annotations

import abc
import asyncio
import time
import typing

from hikari.api import event_dispatcher
from hikari.api import gateway_zookeeper
from hikari.events import other
from hikari import gateway
from hikari.internal import conversions

if typing.TYPE_CHECKING:
    import datetime

    from hikari import http_settings
    from hikari.models import gateway
    from hikari.models import guilds
    from hikari.models import intents as intents_


class AbstractGatewayZookeeper(gateway_zookeeper.IGatewayZookeeper, abc.ABC):
    def __init__(
        self,
        *,
        config: http_settings.HTTPSettings,
        debug: bool,
        initial_activity: typing.Optional[gateway.Activity],
        initial_idle_since: typing.Optional[datetime.datetime],
        initial_is_afk: bool,
        initial_status: guilds.PresenceStatus,
        intents: typing.Optional[intents_.Intent],
        large_threshold: int,
        shard_ids: typing.Set[int],
        shard_count: int,
        token: str,
        url: str,
        use_compression: bool,
        version: int,
    ) -> None:
        self._aiohttp_config = config
        self._url = url
        self._shard_count = shard_count
        self._shards = {
            shard_id: gateway.Gateway(
                config=config,
                debug=debug,
                dispatch=self.event_consumer.consume_raw_event,
                initial_activity=initial_activity,
                initial_idle_since=initial_idle_since,
                initial_is_afk=initial_is_afk,
                initial_status=initial_status,
                intents=intents,
                large_threshold=large_threshold,
                shard_id=shard_id,
                shard_count=shard_count,
                token=token,
                url=url,
                use_compression=use_compression,
                version=version,
            )
            for shard_id in shard_ids
        }

    @property
    def gateway_shards(self) -> typing.Mapping[int, gateway.Gateway]:
        return self._shards

    @property
    def shard_count(self) -> int:
        return self._shard_count

    async def start(self) -> None:
        self.logger.info("starting %s", conversions.pluralize(len(self._shards), "shard"))

        start_time = time.perf_counter()

        for i, shard_id in enumerate(self._shards):
            if i > 0:
                self.logger.info("idling for 5 seconds to avoid an invalid session")
                await asyncio.sleep(5)

            shard_obj = self._shards[shard_id]
            await shard_obj.run()

        finish_time = time.perf_counter()

        self.logger.info("started %s shard(s) in approx %.2fs", len(self._shards), finish_time - start_time)

        if hasattr(self, "event_dispatcher") and isinstance(self.event_dispatcher, event_dispatcher.IEventDispatcher):
            await self.event_dispatcher.dispatch(other.StartedEvent())

    async def join(self) -> None:
        await asyncio.gather(*(shard_obj.join() for shard_obj in self._shards.values()))

    async def close(self) -> None:
        self.logger.info("stopping %s shard(s)", len(self._shards))
        start_time = time.perf_counter()

        has_event_dispatcher = hasattr(self, "event_dispatcher") and isinstance(
            self.event_dispatcher, event_dispatcher.IEventDispatcher
        )

        try:
            if has_event_dispatcher:
                # noinspection PyUnresolvedReferences
                await self.event_dispatcher.dispatch(other.StoppingEvent())

            await asyncio.gather(*(shard_obj.close() for shard_obj in self._shards.values()))
        finally:
            finish_time = time.perf_counter()
            self.logger.info("stopped %s shard(s) in approx %.2fs", len(self._shards), finish_time - start_time)

            if has_event_dispatcher:
                # noinspection PyUnresolvedReferences
                await self.event_dispatcher.dispatch(other.StoppedEvent())

    async def update_presence(
        self,
        *,
        status: guilds.PresenceStatus = ...,
        activity: typing.Optional[gateway.Activity] = ...,
        idle_since: typing.Optional[datetime.datetime] = ...,
        is_afk: bool = ...,
    ) -> None:
        await asyncio.gather(
            *(
                s.update_presence(status=status, activity=activity, idle_since=idle_since, is_afk=is_afk)
                for s in self._shards.values()
                if s.connection_state in (status.ShardState.WAITING_FOR_READY, status.ShardState.READY)
            )
        )
