# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Basic implementation the components for a single-process bot."""

from __future__ import annotations

import asyncio
import concurrent.futures
import datetime
import logging
import math
import signal
import sys
import types
import typing

from hikari import config
from hikari import errors
from hikari import intents as intents_
from hikari import presences
from hikari import traits
from hikari import users
from hikari.api import cache as cache_
from hikari.api import chunker as chunker_
from hikari.api import entity_factory as entity_factory_
from hikari.api import event_dispatcher
from hikari.api import event_factory as event_factory_
from hikari.api import shard as gateway_shard
from hikari.api import voice as voice_
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import event_factory as event_factory_impl
from hikari.impl import rest as rest_impl
from hikari.impl import shard as shard_impl
from hikari.impl import voice as voice_impl
from hikari.utilities import aio
from hikari.utilities import constants
from hikari.utilities import date
from hikari.utilities import ux

if typing.TYPE_CHECKING:
    from hikari.api import cache
    from hikari.api import chunker
    from hikari.api import rest as rest_
    from hikari.api import shard
    from hikari.impl import event_manager_base

LoggerLevel = typing.Union[
    typing.Literal["DEBUG"],
    typing.Literal["INFO"],
    typing.Literal["WARNING"],
    typing.Literal["ERROR"],
    typing.Literal["CRITICAL"],
]
"""Type-hint for a valid logging level."""


_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari")


class BotApp(traits.BotAware):
    def __init__(
        self,
        token: str,
        *,
        allow_color: bool = True,
        banner: typing.Optional[str] = "hikari",
        chunking_limit: int = 200,
        debug: bool = False,
        enable_cache: bool = True,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        force_color: bool = False,
        http_settings: typing.Optional[config.HTTPSettings] = None,
        intents: intents_.Intents = intents_.Intents.ALL_UNPRIVILEGED,
        logs: typing.Union[None, LoggerLevel, typing.Dict[str, typing.Any]] = "INFO",
        proxy_settings: typing.Optional[config.ProxySettings] = None,
        rest_url: str = constants.REST_API_URL,
    ) -> None:
        # Beautification and logging
        ux.init_logging(logs, allow_color, force_color)
        ux.print_banner(banner, allow_color, force_color)

        # Settings and state
        self._banner = banner
        self._closing_event = asyncio.Event()
        self._debug = debug
        self._executor = executor
        self._http_settings = http_settings if http_settings is not None else config.HTTPSettings()
        self._intents = intents
        self._proxy_settings = proxy_settings if proxy_settings is not None else config.ProxySettings()
        self._token = token

        # Caching, chunking, and event subsystems.
        self._cache: cache.Cache
        self._chunker: chunker.GuildChunker
        self._events: event_dispatcher.EventDispatcher
        events_obj: event_manager_base.EventManagerBase

        if enable_cache:
            from hikari.impl import stateful_cache
            from hikari.impl import stateful_event_manager
            from hikari.impl import stateful_guild_chunker

            cache_obj = stateful_cache.StatefulCacheImpl(self, intents)
            self._cache = cache_obj
            self._chunker = stateful_guild_chunker.StatefulGuildChunkerImpl(self, chunking_limit)

            events_obj = stateful_event_manager.StatefulEventManagerImpl(self, cache_obj, intents)
            self._raw_event_consumer = events_obj.consume_raw_event
            self._events = events_obj
        else:
            from hikari.impl import stateless_cache
            from hikari.impl import stateless_event_manager
            from hikari.impl import stateless_guild_chunker

            self._cache = stateless_cache.StatelessCacheImpl()
            self._chunker = stateless_guild_chunker.StatelessGuildChunkerImpl()

            events_obj = stateless_event_manager.StatelessEventManagerImpl(self, intents)
            self._raw_event_consumer = events_obj.consume_raw_event
            self._events = events_obj

        # Entity creation
        self._entity_factory = entity_factory_impl.EntityFactoryImpl(self)

        # Event creation
        self._event_factory = event_factory_impl.EventFactoryImpl(self)

        # Voice subsystem
        self._voice = voice_impl.VoiceComponentImpl(self, self._debug, self._events)

        # RESTful API.
        self._rest = rest_impl.RESTClientImpl(   # noqa: S106 hardcoded password false positive.
            debug=debug,
            connector_factory=rest_impl.BasicLazyCachedTCPConnectorFactory(),
            connector_owner=True,
            entity_factory=self._entity_factory,
            executor=self._executor,
            http_settings=self._http_settings,
            proxy_settings=self._proxy_settings,
            rest_url=rest_url,
            token=token,
            token_type="Bot",
            version=6,
        )

        # We populate these on startup instead, as we need to possibly make some
        # HTTP requests to determine what to put in this mapping.
        self._shards: typing.Dict[int, shard.GatewayShard] = {}

    @property
    def cache(self) -> cache_.Cache:
        return self._cache

    @property
    def chunker(self) -> chunker_.GuildChunker:
        return self._chunker

    @property
    def dispatcher(self) -> event_dispatcher.EventDispatcher:
        return self._events

    @property
    def entity_factory(self) -> entity_factory_.EntityFactory:
        return self._entity_factory

    @property
    def event_factory(self) -> event_factory_.EventFactory:
        return self._event_factory

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        return self._executor

    @property
    def heartbeat_latencies(self) -> typing.Mapping[int, float]:
        return {s.id: s.heartbeat_latency for s in self._shards.values()}

    @property
    def heartbeat_latency(self) -> float:
        latencies = [s.heartbeat_latency for s in self._shards.values() if not math.isnan(s.heartbeat_latency)]
        return sum(latencies) if latencies else float("nan")

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

    @property
    def intents(self) -> typing.Optional[intents_.Intents]:
        return self._intents

    @property
    def me(self) -> typing.Optional[users.OwnUser]:
        return self._cache.get_me()

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._proxy_settings

    @property
    def shards(self) -> typing.Mapping[int, gateway_shard.GatewayShard]:
        return types.MappingProxyType(self._shards)

    @property
    def shard_count(self) -> int:
        if self._shards:
            return next(iter(self._shards.values())).shard_count
        return 0

    @property
    def voice(self) -> voice_.VoiceComponent:
        return self._voice

    @property
    def rest(self) -> rest_.RESTClient:
        return self._rest

    async def close(self, wait: bool = False) -> None:
        self._closing_event.set()

        _LOGGER.debug("BotApp#close(%s) invoked", wait)

        if wait:
            try:
                await self.join()
            finally:
                # Discard any exception that occurred from shutting down.
                return

    async def join(self, until_close: bool = True) -> None:
        awaitables: typing.List[typing.Awaitable[typing.Any]] = list(self._shards.values())
        if until_close:
            awaitables.append(self._closing_event.wait())

        await aio.first_completed(*awaitables)

    # TODO: implement fully, this is just a stub for testing only.
    def run(
        self,
        *,
        asyncio_debug: typing.Optional[bool] = None,
        activity: typing.Optional[presences.Activity] = None,
        afk: bool = False,
        close_executor: bool = False,
        close_loop: bool = True,
        coroutine_tracking_depth: typing.Optional[int] = None,
        enable_signal_handlers: bool = True,
        idle_since: typing.Optional[datetime.datetime] = None,
        shard_ids: typing.Optional[typing.Set[int]] = None,
        shard_count: typing.Optional[int] = None,
        status: presences.Status = presences.Status.ONLINE,
    ) -> None:
        loop = asyncio.get_event_loop()
        signals = ("SIGINT", "SIGQUIT", "SIGTERM")

        if asyncio_debug:
            loop.set_debug(True)

        if coroutine_tracking_depth is not None:
            try:
                # Provisionally defined in CPython, may be removed without notice.
                loop.set_coroutine_tracking_depth(coroutine_tracking_depth)  # type: ignore[attr-defined]
            except AttributeError:
                _LOGGER.warning("Cannot set coroutine tracking depth for %s")

        def signal_handler(signum: int) -> None:
            raise errors.HikariInterrupt(signum, signal.strsignal(signum))

        if enable_signal_handlers:
            for sig in signals:
                try:
                    signum = getattr(signal, sig)
                    loop.add_signal_handler(signum, signal_handler, signum)
                except (NotImplementedError, AttributeError):
                    # Windows doesn't use signals (NotImplementedError);
                    # Some OSs may decide to not implement some signals either...
                    pass

        try:
            loop.run_until_complete(
                self.start(
                    activity=activity,
                    afk=afk,
                    idle_since=idle_since,
                    shard_ids=shard_ids,
                    shard_count=shard_count,
                    status=status,
                )
            )

            try:
                loop.run_until_complete(self.join(until_close=False))
            finally:
                try:
                    loop.run_until_complete(self.terminate(close_executor=close_executor))
                finally:
                    if enable_signal_handlers:
                        for sig in signals:
                            try:
                                signum = getattr(signal, sig)
                                loop.remove_signal_handler(signum)
                            except (NotImplementedError, AttributeError):
                                # Windows doesn't use signals (NotImplementedError);
                                # Some OSs may decide to not implement some signals either...
                                pass

                    if close_loop:
                        self._destroy_loop(loop)

        except errors.HikariInterrupt as interrupt:
            _LOGGER.info(
                "bot has shut down after receiving %s (%s)",
                interrupt.description or str(interrupt.signum),
                interrupt.signum,
            )

    async def start(
        self,
        *,
        activity: typing.Optional[presences.Activity] = None,
        afk: bool = False,
        idle_since: typing.Optional[datetime.datetime] = None,
        shard_ids: typing.Optional[typing.Set[int]] = None,
        shard_count: typing.Optional[int] = None,
        status: presences.Status = presences.Status.ONLINE,
    ) -> None:
        asyncio.create_task(ux.check_for_updates())

        if shard_ids is not None and shard_count is None:
            raise TypeError("Must pass shard_count if specifying shard_ids manually")

        requirements = await self._rest.fetch_gateway_bot()

        if shard_count is None:
            shard_count = requirements.shard_count
        if shard_ids is None:
            shard_ids = set(range(shard_count))

        _LOGGER.info(
            "planning to start %s session%s... you can start %s session%s before the next window starts at %s",
            len(shard_ids),
            "s" if len(shard_ids) != 1 else "",
            requirements.session_start_limit.remaining,
            "s" if requirements.session_start_limit.remaining != 1 else "",
            requirements.session_start_limit.reset_at,
        )

        for window_start in range(0, shard_count, requirements.session_start_limit.max_concurrency):
            window = [
                candidate_shard_id
                for candidate_shard_id in range(
                    window_start, window_start + requirements.session_start_limit.max_concurrency
                )
                if candidate_shard_id in shard_ids
            ]

            if not window:
                continue
            if self._shards:
                close_waiter = asyncio.create_task(self._closing_event.wait())
                shard_joiners = map(asyncio.create_task, self._shards.values())
                try:
                    await aio.all_of(close_waiter, *shard_joiners, timeout=5)
                    if close_waiter:
                        _LOGGER.info("requested to shut down during startup of shards")
                    else:
                        _LOGGER.critical("one or more shards shut down unexpectedly during bot startup")

                    await self.terminate()
                    return
                except asyncio.TimeoutError:
                    # new window starts.
                    pass
                except Exception as ex:
                    _LOGGER.critical("an exception occurred in one of the started shards during bot startup: %r", ex)
                    await self.terminate()
                    raise

            started_shards = await aio.all_of(
                *(
                    self._start_one_shard(
                        activity=activity,
                        afk=afk,
                        idle_since=idle_since,
                        shard_id=candidate_shard_id,
                        shard_count=shard_count,
                        status=status,
                        url=requirements.url,
                    )
                    for candidate_shard_id in window
                    if candidate_shard_id in shard_ids
                )
            )

            for started_shard in started_shards:
                self._shards[started_shard.id] = started_shard

    async def terminate(self, close_executor: bool = False) -> None:
        async def handle(name: str, awaitable: typing.Awaitable[typing.Any]) -> None:
            future = asyncio.ensure_future(awaitable)

            try:
                await future
            except Exception as ex:
                loop = asyncio.get_running_loop()

                loop.call_exception_handler(
                    {
                        "message": f"{name} raised an exception during shutdown",
                        "future": future,
                        "exception": ex,
                    }
                )

        calls = [
            ("rest", self._rest.close()),
            ("chunker", self._chunker.close()),
            ("voice handler", self._voice.close()),
            *((f"shard {s.id}", s.close()) for s in self._shards.values()),
        ]

        for coro in asyncio.as_completed([handle(*pair) for pair in calls]):
            await coro

        if close_executor and self._executor is not None:
            _LOGGER.debug("shutting down executor %s", self._executor)
            self._executor.shutdown(wait=True)
            self._executor = None

    async def _start_one_shard(
        self,
        activity: typing.Optional[presences.Activity],
        afk: bool,
        idle_since: typing.Optional[datetime.datetime],
        shard_id: int,
        shard_count: int,
        status: presences.Status,
        url: str,
    ) -> shard_impl.GatewayShardImpl:
        new_shard = shard_impl.GatewayShardImpl(
            debug=self._debug,
            event_consumer=self._raw_event_consumer,
            http_settings=self._http_settings,
            initial_activity=activity,
            initial_is_afk=afk,
            initial_idle_since=idle_since,
            initial_status=status,
            intents=self._intents,
            proxy_settings=self._proxy_settings,
            shard_id=shard_id,
            shard_count=shard_count,
            token=self._token,
            url=url,
        )

        start = date.monotonic()
        await new_shard.start()
        end = date.monotonic()

        if new_shard.is_alive:
            _LOGGER.info("Shard %s started successfully in %.1fms", shard_id, (end - start) * 1_000)
            return new_shard

        raise errors.GatewayError(f"Shard {shard_id} shut down immediately when starting")

    @staticmethod
    def _destroy_loop(loop: asyncio.AbstractEventLoop) -> None:
        async def murder(future: asyncio.Future[typing.Any]) -> None:
            # These include _GatheringFuture which must be awaited if the children
            # throw an asyncio.CancelledError, otherwise it will spam logs with warnings
            # about exceptions not being retrieved before GC.
            try:
                future.cancel()
                await future
            except asyncio.CancelledError:
                pass
            except Exception as ex:
                loop.call_exception_handler(
                    {
                        "message": "Future raised unexpected exception after requesting cancellation",
                        "exception": ex,
                        "future": future,
                    }
                )

        remaining_tasks = [t for t in asyncio.all_tasks(loop) if not t.cancelled() and not t.done()]

        if remaining_tasks:
            _LOGGER.debug("terminating %s remaining tasks forcefully", len(remaining_tasks))
            loop.run_until_complete(asyncio.gather(*(murder(task) for task in remaining_tasks)))
        else:
            _LOGGER.debug("No remaining tasks exist, good job!")

        if sys.version_info >= (3, 9):
            _LOGGER.debug("shutting down default executor")
            loop.run_until_complete(loop.shutdown_default_executor())

        _LOGGER.debug("shutting down asyncgens")
        loop.run_until_complete(loop.shutdown_asyncgens())

        _LOGGER.debug("closing event loop")
        loop.close()
