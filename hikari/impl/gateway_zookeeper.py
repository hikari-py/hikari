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

__all__ = ["AbstractGatewayZookeeper"]

import abc
import asyncio
import contextlib
import datetime
import inspect
import os
import platform
import signal
import time
import typing

from hikari import _about
from hikari.api import app as app_
from hikari.api import event_dispatcher
from hikari.events import other
from hikari.net import gateway
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.net import http_settings
    from hikari.models import gateway as gateway_models
    from hikari.models import intents as intents_
    from hikari.models import presences


class AbstractGatewayZookeeper(app_.IGatewayZookeeper, abc.ABC):
    def __init__(
        self,
        *,
        config: http_settings.HTTPSettings,
        debug: bool,
        initial_activity: typing.Optional[presences.OwnActivity],
        initial_idle_since: typing.Optional[datetime.datetime],
        initial_is_afk: bool,
        initial_status: presences.PresenceStatus,
        intents: typing.Optional[intents_.Intent],
        large_threshold: int,
        shard_ids: typing.Set[int],
        shard_count: int,
        token: str,
        use_compression: bool,
        version: int,
    ) -> None:
        self._aiohttp_config = config
        self._debug = debug
        self._gather_task = None
        self._initial_activity = initial_activity
        self._initial_idle_since = initial_idle_since
        self._initial_is_afk = initial_is_afk
        self._initial_status = initial_status
        self._intents = intents
        self._large_threshold = large_threshold
        self._max_concurrency = 1
        self._request_close_event = asyncio.Event()
        self._shard_count = shard_count
        self._shard_ids = shard_ids
        self._shards = {}
        self._tasks = {}
        self._token = token
        self._use_compression = use_compression
        self._version = version

    @property
    def gateway_shards(self) -> typing.Mapping[int, gateway.Gateway]:
        return self._shards

    @property
    def gateway_shard_count(self) -> int:
        return self._shard_count

    async def start(self) -> None:
        self._tasks.clear()
        self._gather_task = None

        await self._init()

        self._request_close_event.clear()

        await self._maybe_dispatch(other.StartingEvent())

        self.logger.info("starting %s shard(s)", len(self._shards))

        start_time = time.perf_counter()

        try:
            for i, shard_ids in enumerate(self._max_concurrency_chunker()):
                if self._request_close_event.is_set():
                    break

                if i > 0:
                    self.logger.info("waiting for 5 seconds until next shard can start")

                    completed, _ = await asyncio.wait(
                        self._tasks.values(), timeout=5, return_when=asyncio.FIRST_COMPLETED
                    )

                    if completed:
                        raise completed.pop().exception()

                window = {}
                for shard_id in shard_ids:
                    shard_obj = self._shards[shard_id]
                    window[shard_id] = asyncio.create_task(shard_obj.start(), name=f"start gateway shard {shard_id}")

                # Wait for the group to start.
                await asyncio.gather(*window.values())

                # Store the keep-alive tasks and continue.
                for shard_id, start_task in window.items():
                    self._tasks[shard_id] = start_task.result()

        finally:
            if len(self._tasks) != len(self._shards):
                self.logger.warning(
                    "application aborted midway through initialization, will begin shutting down %s shard(s)",
                    len(self._tasks),
                )
                await self._abort()

                # We know an error occurred if this condition is met, so re-raise it.
                raise

            finish_time = time.perf_counter()
            self._gather_task = asyncio.create_task(
                self._gather(), name=f"shard zookeeper for {len(self._shards)} shard(s)"
            )
            self.logger.info("started %s shard(s) in approx %.2fs", len(self._shards), finish_time - start_time)

            await self._maybe_dispatch(other.StartedEvent())

    async def join(self) -> None:
        if self._gather_task is not None:
            await self._gather_task

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

    def run(self) -> None:
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
        status: typing.Union[undefined.Undefined, presences.PresenceStatus] = undefined.Undefined(),
        activity: typing.Union[undefined.Undefined, presences.OwnActivity, None] = undefined.Undefined(),
        idle_since: typing.Union[undefined.Undefined, datetime.datetime] = undefined.Undefined(),
        is_afk: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
    ) -> None:
        await asyncio.gather(
            *(
                s.update_presence(status=status, activity=activity, idle_since=idle_since, is_afk=is_afk)
                for s in self._shards.values()
                if s.is_alive
            )
        )

    async def _init(self):
        version = _about.__version__
        # noinspection PyTypeChecker
        path = os.path.abspath(os.path.dirname(inspect.getsourcefile(_about)))
        py_impl = platform.python_implementation()
        py_ver = platform.python_version()
        py_compiler = platform.python_compiler()
        self.logger.info(
            "hikari v%s (installed in %s) (%s %s %s)", version, path, py_impl, py_ver, py_compiler,
        )

        gw_recs = await self._fetch_gateway_recommendations()

        self.logger.info(
            "you have sent an IDENTIFY %s time(s) before now, and have %s remaining. This will reset at %s.",
            gw_recs.session_start_limit.total - gw_recs.session_start_limit.remaining,
            gw_recs.session_start_limit.remaining,
            datetime.datetime.now() + gw_recs.session_start_limit.reset_after,
        )

        self._shard_count = self._shard_count if self._shard_count else gw_recs.shard_count
        self._shard_ids = self._shard_ids if self._shard_ids else range(self._shard_count)
        self._max_concurrency = gw_recs.session_start_limit.max_concurrency
        url = gw_recs.url

        self.logger.info(
            "will connect shards to %s. max_concurrency while connecting is %s, contact Discord to get this increased",
            url,
            self._max_concurrency,
        )

        shard_clients: typing.Dict[int, gateway.Gateway] = {}
        for shard_id in self._shard_ids:
            shard = gateway.Gateway(
                app=self,
                config=self._aiohttp_config,
                debug=self._debug,
                initial_activity=self._initial_activity,
                initial_idle_since=self._initial_idle_since,
                initial_is_afk=self._initial_is_afk,
                initial_status=self._initial_status,
                intents=self._intents,
                large_threshold=self._large_threshold,
                shard_id=shard_id,
                shard_count=self._shard_count,
                token=self._token,
                url=url,
                use_compression=self._use_compression,
                version=self._version,
            )
            shard_clients[shard_id] = shard

        self._shards = shard_clients  # pylint: disable=attribute-defined-outside-init

    def _max_concurrency_chunker(self) -> typing.Iterator[typing.Iterator[int]]:
        """Yield generators of shard IDs.

        Each yielded generator will yield every shard ID that can be started
        at the same time.

        You should then wait 5 seconds between each window.
        """
        n = 0
        while n < self._shard_count:
            next_window = [i for i in range(n, n + self._max_concurrency) if i in self._shard_ids]
            # Don't yield anything if no IDs are in the given window.
            if next_window:
                yield iter(next_window)
            n += self._max_concurrency

    @abc.abstractmethod
    async def _fetch_gateway_recommendations(self) -> gateway_models.GatewayBot:
        ...

    async def _abort(self) -> None:
        for shard_id in self._tasks:
            await self._shards[shard_id].close()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)

    async def _gather(self) -> None:
        try:
            await asyncio.gather(*self._tasks.values())
        finally:
            self.logger.debug("gather failed, shutting down shard(s)")
            await self.close()

    async def _run(self) -> None:
        await self.start()
        await self.join()

    async def _maybe_dispatch(self, event) -> None:
        if hasattr(self, "event_dispatcher"):
            # noinspection PyUnresolvedReferences
            await self.event_dispatcher.dispatch(event)
