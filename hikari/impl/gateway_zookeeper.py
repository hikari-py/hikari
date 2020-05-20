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
import contextlib
import signal
import time
import typing

from hikari import event_dispatcher
from hikari import gateway_zookeeper
from hikari.events import other
from hikari.internal import conversions
from hikari.net import gateway

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
        self._request_close_event = asyncio.Event()
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
        self._running = False

    @property
    def gateway_shards(self) -> typing.Mapping[int, gateway.Gateway]:
        return self._shards

    @property
    def shard_count(self) -> int:
        return self._shard_count

    async def start(self) -> None:
        self._running = True
        self._request_close_event.clear()
        self.logger.info("starting %s", conversions.pluralize(len(self._shards), "shard"))

        start_time = time.perf_counter()

        for i, shard_id in enumerate(self._shards):
            if i > 0:
                self.logger.info("waiting for 5 seconds until next shard can start")

                try:
                    await asyncio.wait_for(self._request_close_event.wait(), timeout=5)
                    # If this passes, the bot got shut down while sharding.
                    return
                except asyncio.TimeoutError:
                    # Continue, no close occurred.
                    pass

            shard_obj = self._shards[shard_id]
            await shard_obj.start()

        finish_time = time.perf_counter()

        self.logger.info("started %s shard(s) in approx %.2fs", len(self._shards), finish_time - start_time)

        if hasattr(self, "event_dispatcher") and isinstance(self.event_dispatcher, event_dispatcher.IEventDispatcher):
            await self.event_dispatcher.dispatch(other.StartedEvent())

    async def join(self) -> None:
        if self._running:
            await asyncio.gather(*(shard_obj.join() for shard_obj in self._shards.values()))

    async def close(self) -> None:
        if self._running:
            # This way if we cancel the stopping task, we still shut down properly.
            self._request_close_event.set()
            self._running = False
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

    def run(self):
        loop = asyncio.get_event_loop()

        def sigterm_handler(*_):
            raise KeyboardInterrupt()

        try:
            with contextlib.suppress(NotImplementedError):
                # Not implemented on Windows
                loop.add_signal_handler(signal.SIGTERM, sigterm_handler)

            loop.run_until_complete(self.start())
            loop.run_until_complete(self.join())

            self.logger.info("client has shut down")

        except KeyboardInterrupt:
            self.logger.info("received signal to shut down client")
            loop.run_until_complete(self.close())
            # Apparently you have to alias except clauses or you get an
            # UnboundLocalError.
            raise
        finally:
            loop.run_until_complete(self.close())
            with contextlib.suppress(NotImplementedError):
                # Not implemented on Windows
                loop.remove_signal_handler(signal.SIGTERM)

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
                if s.is_alive
            )
        )
