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
"""Abstract zookeeper implementation for multiple-sharded applications."""

from __future__ import annotations

__all__ = ["AbstractGatewayZookeeper"]

import abc
import asyncio
import contextlib
import datetime
import signal
import time
import typing

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
    """Provides keep-alive logic for orchestrating multiple shards.

    This provides the logic needed to keep multiple shards alive at once, and
    correctly orchestrate their startup and shutdown. Applications that are
    multi-sharded or auto-sharded can extend this functionality to acquire the
    ability to manage sharding.

    !!! note
        This does not provide REST API functionality.

    Parameters
    ----------
    compression : bool
        Defaulting to `True`, if `True`, then zlib transport compression is used
        for each shard connection. If `False`, no compression is used.
    config : hikari.utilities.undefined.Undefined or hikari.net.http_settings.HTTPSettings
        Optional aiohttp settings to apply to the created shards.
    debug : bool
        Defaulting to `False`, if `True`, then each payload sent and received
        on the gateway will be dumped to debug logs. This will provide useful
        debugging context at the cost of performance. Generally you do not
        need to enable this.
    initial_activity : hikari.models.presences.OwnActivity or None or hikari.utilities.undefined.Undefined
        The initial activity to have on each shard.
    initial_activity : hikari.models.presences.PresenceStatus or hikari.utilities.undefined.Undefined
        The initial status to have on each shard.
    initial_idle_since : datetime.datetime or None or hikari.utilities.undefined.Undefined
        The initial time to show as being idle since, or `None` if not idle,
        for each shard.
    initial_idle_since : bool or hikari.utilities.undefined.Undefined
        If `True`, each shard will appear as being AFK on startup. If `False`,
        each shard will appear as _not_ being AFK.
    intents : hikari.models.intents.Intent or None
        The intents to use for each shard. If `None`, then no intents are
        passed. Note that on the version `7` gateway, this will cause an
        immediate connection close with an error code.
    large_threshold : int
        The number of members that need to be in a guild for the guild to be
        considered large. Defaults to the maximum, which is `250`.
    shard_ids : typing.Set[int] or undefined.Undefined
        A set of every shard ID that should be created and started on startup.
        If left undefined along with `shard_count`, then auto-sharding is used
        instead, which is the default.
    shard_count : int or undefined.Undefined
        The number of shards in the entire application. If left undefined along
        with `shard_ids`, then auto-sharding is used instead, which is the
        default.
    token : str
        The bot token to use. This should not start with a prefix such as
        `Bot `, but instead only contain the token itself.
    version : int
        The version of the gateway to connect to. At the time of writing,
        only version `6` and version `7` (undocumented development release)
        are supported. This defaults to using v6.

    !!! note
        The default parameters for `shard_ids` and `shard_count` are marked as
        undefined. When both of these are left to the default value, the
        application will use the Discord-provided recommendation for the number
        of shards to start.

        If only one of these two parameters are specified, expect a `TypeError`
        to be raised.

        Likewise, all shard_ids must be greater-than or equal-to `0`, and
        less than `shard_count` to be valid. Failing to provide valid
        values will result in a `ValueError` being raised.

    !!! note
        If all four of `initial_activity`, `initial_idle_since`,
        `initial_is_afk`, and `initial_status` are not defined and left to their
        default values, then the presence will not be _updated_ on startup
        at all.

    Raises
    ------
    ValueError
        If sharding information is provided, but is unfeasible or invalid.
    TypeError
        If sharding information is not specified correctly.
    """

    def __init__(
        self,
        *,
        compression: bool,
        config: http_settings.HTTPSettings,
        debug: bool,
        initial_activity: typing.Union[undefined.Undefined, presences.OwnActivity, None] = undefined.Undefined(),
        initial_idle_since: typing.Union[undefined.Undefined, datetime.datetime, None] = undefined.Undefined(),
        initial_is_afk: typing.Union[undefined.Undefined, bool] = undefined.Undefined(),
        initial_status: typing.Union[undefined.Undefined, presences.PresenceStatus] = undefined.Undefined(),
        intents: typing.Optional[intents_.Intent],
        large_threshold: int,
        shard_ids: typing.Set[int],
        shard_count: int,
        token: str,
        version: int,
    ) -> None:
        if undefined.Undefined.count(shard_ids, shard_count) == 1:
            raise TypeError("You must provide values for both shard_ids and shard_count, or neither.")
        if not isinstance(shard_ids, undefined.Undefined):
            if not shard_ids:
                raise ValueError("At least one shard ID must be specified if provided.")
            if not all(shard_id >= 0 for shard_id in shard_ids):
                raise ValueError("shard_ids must be greater than or equal to 0.")
            if not all(shard_id < shard_count for shard_id in shard_ids):
                raise ValueError("shard_ids must be less than the total shard_count.")

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
        self._use_compression = compression
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
