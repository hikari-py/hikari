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

        # This is a little hacky workaround to boost performance. We force

        self._gather_task = None
        self._request_close_event = asyncio.Event()
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
        self._tasks = {}

    @property
    def gateway_shards(self) -> typing.Mapping[int, gateway.Gateway]:
        return self._shards

    @property
    def shard_count(self) -> int:
        return self._shard_count

    async def start(self) -> None:
        self._tasks.clear()
        self._gather_task = None

        self._request_close_event.clear()
        self.logger.info("starting %s", conversions.pluralize(len(self._shards), "shard"))

        start_time = time.perf_counter()

        try:
            for i, shard_id in enumerate(self._shards):
                if self._request_close_event.is_set():
                    break

                if i > 0:
                    self.logger.info("waiting for 5 seconds until next shard can start")

                    completed, _ = await asyncio.wait(
                        self._tasks.values(), timeout=5, return_when=asyncio.FIRST_COMPLETED
                    )

                    if completed:
                        raise completed.pop().exception()

                shard_obj = self._shards[shard_id]
                self._tasks[shard_id] = await shard_obj.start()
        finally:
            if len(self._tasks) != len(self._shards):
                self.logger.warning(
                    "application aborted midway through initialization, will begin shutting down %s shard(s)",
                    len(self._tasks),
                )
                await self._abort()
                return

        finish_time = time.perf_counter()
        self._gather_task = asyncio.create_task(
            self._gather(), name=f"shard zookeeper for {len(self._shards)} shard(s)"
        )
        self.logger.info("started %s shard(s) in approx %.2fs", len(self._shards), finish_time - start_time)

        if hasattr(self, "event_dispatcher") and isinstance(self.event_dispatcher, event_dispatcher.IEventDispatcher):
            await self.event_dispatcher.dispatch(other.StartedEvent())

    async def join(self) -> None:
        if self._gather_task is not None:
            await self._gather_task

    async def _abort(self):
        for shard_id in self._tasks:
            await self._shards[shard_id].close()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)

    async def _gather(self):
        try:
            await asyncio.gather(*self._tasks.values())
        finally:
            self.logger.debug("gather failed, shutting down shard(s)")
            await self.close()

    async def close(self) -> None:
        if self._tasks:
            # This way if we cancel the stopping task, we still shut down properly.
            self._request_close_event.set()

            self.logger.info("stopping %s shard(s)", len(self._tasks))

            has_event_dispatcher = hasattr(self, "event_dispatcher") and isinstance(
                self.event_dispatcher, event_dispatcher.IEventDispatcher
            )

            try:
                if has_event_dispatcher:
                    # noinspection PyUnresolvedReferences
                    await self.event_dispatcher.dispatch(other.StoppingEvent())

                await self._abort()
            finally:
                self._tasks.clear()

                if has_event_dispatcher:
                    # noinspection PyUnresolvedReferences
                    await self.event_dispatcher.dispatch(other.StoppedEvent())

    async def _run(self):
        await self.start()
        await self.join()

    def run(self):
        loop = asyncio.get_event_loop()

        def sigterm_handler(*_):
            loop.create_task(self.close())

        try:
            with contextlib.suppress(NotImplementedError):
                # Not implemented on Windows
                loop.add_signal_handler(signal.SIGTERM, sigterm_handler)

            loop.run_until_complete(self._run())

        except KeyboardInterrupt:
            self.logger.info("received signal to shut down client")
            raise
        finally:
            loop.run_until_complete(self.close())
            with contextlib.suppress(NotImplementedError):
                # Not implemented on Windows
                loop.remove_signal_handler(signal.SIGTERM)
            self.logger.info("client has shut down")

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
