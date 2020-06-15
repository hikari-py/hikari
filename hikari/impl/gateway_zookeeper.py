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

__all__: typing.Final[typing.List[str]] = ["AbstractGatewayZookeeper"]

import abc
import asyncio
import contextlib
import datetime
import signal
import time
import typing

from hikari.api import event_dispatcher
from hikari.api import gateway_zookeeper
from hikari.events import other
from hikari.net import gateway
from hikari.utilities import aio
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.events import base as base_events
    from hikari.net import http_settings
    from hikari.models import gateway as gateway_models
    from hikari.models import intents as intents_
    from hikari.models import presences


class AbstractGatewayZookeeper(gateway_zookeeper.IGatewayZookeeperApp, abc.ABC):
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
    config : hikari.utilities.undefined.UndefinedType or hikari.net.http_settings.HTTPSettings
        Optional aiohttp settings to apply to the created shards.
    debug : bool
        Defaulting to `False`, if `True`, then each payload sent and received
        on the gateway will be dumped to debug logs. This will provide useful
        debugging context at the cost of performance. Generally you do not
        need to enable this.
    initial_activity : hikari.models.presences.Activity or None or hikari.utilities.undefined.UndefinedType
        The initial activity to have on each shard.
    initial_activity : hikari.models.presences.Status or hikari.utilities.undefined.UndefinedType
        The initial status to have on each shard.
    initial_idle_since : datetime.datetime or None or hikari.utilities.undefined.UndefinedType
        The initial time to show as being idle since, or `None` if not idle,
        for each shard.
    initial_idle_since : bool or hikari.utilities.undefined.UndefinedType
        If `True`, each shard will appear as being AFK on startup. If `False`,
        each shard will appear as _not_ being AFK.
    intents : hikari.models.intents.Intent or None
        The intents to use for each shard. If `None`, then no intents are
        passed. Note that on the version `7` gateway, this will cause an
        immediate connection close with an error code.
    large_threshold : int
        The number of members that need to be in a guild for the guild to be
        considered large. Defaults to the maximum, which is `250`.
    shard_ids : typing.Set[int] or undefined.UndefinedType
        A set of every shard ID that should be created and started on startup.
        If left undefined along with `shard_count`, then auto-sharding is used
        instead, which is the default.
    shard_count : int or undefined.UndefinedType
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

    # We do not bother with SIGINT here, since we can catch it as a KeyboardInterrupt
    # instead and provide tidier handling of the stacktrace as a result.
    _SIGNALS: typing.Final[typing.ClassVar[typing.Sequence[str]]] = ("SIGQUIT", "SIGTERM")

    def __init__(
        self,
        *,
        compression: bool,
        config: http_settings.HTTPSettings,
        debug: bool,
        initial_activity: typing.Union[undefined.UndefinedType, presences.Activity, None] = undefined.UNDEFINED,
        initial_idle_since: typing.Union[undefined.UndefinedType, datetime.datetime, None] = undefined.UNDEFINED,
        initial_is_afk: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        initial_status: typing.Union[undefined.UndefinedType, presences.Status] = undefined.UNDEFINED,
        intents: typing.Optional[intents_.Intent],
        large_threshold: int,
        shard_ids: typing.Union[typing.Set[int], undefined.UndefinedType] = undefined.UNDEFINED,
        shard_count: typing.Union[int, undefined.UndefinedType] = undefined.UNDEFINED,
        token: str,
        version: int,
    ) -> None:
        if undefined.count(shard_ids, shard_count) == 1:
            raise TypeError("You must provide values for both shard_ids and shard_count, or neither.")
        if shard_ids is not undefined.UNDEFINED:
            if not shard_ids:
                raise ValueError("At least one shard ID must be specified if provided.")
            if not all(shard_id >= 0 for shard_id in shard_ids):
                raise ValueError("shard_ids must be greater than or equal to 0.")
            if shard_count is not undefined.UNDEFINED and not all(shard_id < shard_count for shard_id in shard_ids):
                raise ValueError("shard_ids must be less than the total shard_count.")

        self._aiohttp_config = config
        self._debug = debug
        self._gather_task: typing.Optional[asyncio.Task[None]] = None
        self._initial_activity = initial_activity
        self._initial_idle_since = initial_idle_since
        self._initial_is_afk = initial_is_afk
        self._initial_status = initial_status
        self._intents = intents
        self._large_threshold = large_threshold
        self._max_concurrency = 1
        self._request_close_event = asyncio.Event()
        self._shard_count = shard_count if shard_count is not undefined.UNDEFINED else 0
        self._shard_ids = set() if shard_ids is undefined.UNDEFINED else shard_ids
        self._shards: typing.Dict[int, gateway.Gateway] = {}
        self._tasks: typing.Dict[int, asyncio.Task[typing.Any]] = {}
        self._token = token
        self._use_compression = compression
        self._version = version

    @property
    def shards(self) -> typing.Mapping[int, gateway.Gateway]:
        return self._shards

    @property
    def shard_count(self) -> int:
        return self._shard_count

    def run(self) -> None:
        loop = asyncio.get_event_loop()

        def on_interrupt() -> None:
            loop.create_task(self.close(), name="signal interrupt shutting down application")

        try:
            self._map_signal_handlers(loop.add_signal_handler, on_interrupt)
            loop.run_until_complete(self._run())
        except KeyboardInterrupt as ex:
            self.logger.info("received signal to shut down client")
            if self._debug:
                raise
            else:
                # The user won't care where this gets raised from, unless we are
                # debugging. It just causes a lot of confusing spam.
                raise ex.with_traceback(None)
        finally:
            self._map_signal_handlers(loop.remove_signal_handler)
            self.logger.info("client has shut down")

    async def start(self) -> None:
        self._tasks.clear()
        self._gather_task = None

        await self._init()

        self._request_close_event.clear()

        await self._maybe_dispatch(other.StartingEvent())

        if self._shard_count > 1:
            self.logger.info("starting %s shard(s)", len(self._shards))
        else:
            self.logger.info("this application will be single-sharded")

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

                    while completed:
                        if (ex := completed.pop().exception()) is not None:
                            raise ex

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
            self._gather_task = asyncio.create_task(self._gather(), name=f"zookeeper for {len(self._shards)} shard(s)")
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

            try:
                await self._maybe_dispatch(other.StoppingEvent())
                await self._abort()
            finally:
                self._tasks.clear()
                await self._maybe_dispatch(other.StoppedEvent())

    async def update_presence(
        self,
        *,
        status: typing.Union[undefined.UndefinedType, presences.Status] = undefined.UNDEFINED,
        activity: typing.Union[undefined.UndefinedType, presences.Activity, None] = undefined.UNDEFINED,
        idle_since: typing.Union[undefined.UndefinedType, datetime.datetime, None] = undefined.UNDEFINED,
        is_afk: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
    ) -> None:
        await asyncio.gather(
            *(
                s.update_presence(status=status, activity=activity, idle_since=idle_since, is_afk=is_afk)
                for s in self._shards.values()
                if s.is_alive
            )
        )

    @abc.abstractmethod
    async def fetch_sharding_settings(self) -> gateway_models.GatewayBot:
        """Fetch the recommended sharding settings and gateway URL from Discord.

        Returns
        -------
        hikari.models.gateway.GatewayBot
            The recommended sharding settings and configuration for the
            bot account.
        """

    async def _init(self) -> None:
        gw_recs = await self.fetch_sharding_settings()

        self.logger.info(
            "you have opened %s session(s) recently, you can open %s more before %s",
            gw_recs.session_start_limit.total - gw_recs.session_start_limit.remaining,
            gw_recs.session_start_limit.remaining if gw_recs.session_start_limit.remaining > 0 else "no",
            (datetime.datetime.now() + gw_recs.session_start_limit.reset_after).strftime("%c"),
        )

        self._shard_count = self._shard_count if self._shard_count else gw_recs.shard_count
        self._shard_ids = self._shard_ids if self._shard_ids else set(range(self._shard_count))
        self._max_concurrency = gw_recs.session_start_limit.max_concurrency
        url = gw_recs.url

        self.logger.info(
            "will connect shards to %s at a rate of %s shard(s) per 5 seconds (contact Discord to increase this rate)",
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

    async def _abort(self) -> None:
        for shard_id in self._tasks:
            if self._shards[shard_id].is_alive:
                await self._shards[shard_id].close()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)

    async def _gather(self) -> None:
        try:
            await asyncio.gather(*self._tasks.values())
        finally:
            self.logger.debug("gather failed, shutting down shard(s)")
            await self.close()

    async def _run(self) -> None:
        try:
            await self.start()
            await self.join()
        finally:
            await self.close()

    def _maybe_dispatch(self, event: base_events.Event) -> typing.Awaitable[typing.Any]:
        if isinstance(self, event_dispatcher.IEventDispatcherApp):
            return self.event_dispatcher.dispatch(event)
        else:
            return aio.completed_future()

    def _map_signal_handlers(
        self, mapping_function: typing.Callable[..., None], *args: typing.Callable[[], typing.Any],
    ) -> None:
        valid_interrupts = signal.valid_signals()
        for interrupt in self._SIGNALS:
            if (code := getattr(signal, interrupt, None)) in valid_interrupts:
                with contextlib.suppress(NotImplementedError):
                    mapping_function(code, *args)
