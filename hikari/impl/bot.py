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

__all__: typing.Final[typing.List[str]] = ["BotAppImpl"]

import asyncio
import contextlib
import datetime
import logging
import reprlib
import signal
import sys
import time
import typing
import warnings

from hikari import config
from hikari import errors
from hikari.api import bot
from hikari.api import shard as gateway_shard
from hikari.events import lifetime_events
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import event_factory as event_factory_impl
from hikari.impl import rate_limits
from hikari.impl import rest as rest_client_impl
from hikari.impl import shard as gateway_shard_impl
from hikari.impl import stateful_cache as cache_impl
from hikari.impl import stateful_event_manager
from hikari.impl import stateful_guild_chunker as guild_chunker_impl
from hikari.impl import stateless_cache as stateless_cache_impl
from hikari.impl import stateless_event_manager
from hikari.impl import stateless_guild_chunker as stateless_guild_chunker_impl
from hikari.impl import voice
from hikari.models import intents as intents_
from hikari.models import presences
from hikari.utilities import art
from hikari.utilities import constants
from hikari.utilities import date
from hikari.utilities import undefined
from hikari.utilities import version_sniffer

if typing.TYPE_CHECKING:
    import concurrent.futures

    from hikari.api import cache as cache_
    from hikari.api import event_consumer as event_consumer_
    from hikari.api import event_dispatcher as event_dispatcher_
    from hikari.api import guild_chunker as guild_chunker_
    from hikari.events import base_events
    from hikari.impl import event_manager_base
    from hikari.models import users

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari")


class BotAppImpl(bot.IBotApp):
    """Implementation of an auto-sharded single-instance bot application.

    Parameters
    ----------
    banner_package : builtins.str or builtins.None
        The package to look for a `banner.txt` in. Will default to Hikari's
        banner if unspecified. If you set this to `builtins.None`, then no
        banner will be displayed.
    debug : builtins.bool
        Defaulting to `builtins.False`, if `builtins.True`, then each payload sent and received
        on the gateway will be dumped to debug logs, and every HTTP API request
        and response will also be dumped to logs. This will provide useful
        debugging context at the cost of performance. Generally you do not
        need to enable this.
    gateway_version : builtins.int
        The version of the gateway to connect to. At the time of writing,
        only version `6` and version `7` (undocumented development release)
        are supported. This defaults to using v6.
    http_settings : hikari.config.HTTPSettings or builtins.None
        The HTTP-related settings to use.
    initial_activity : hikari.utilities.undefined.UndefinedNoneOr[hikari.models.presences.Activity]
        The initial activity to have on each shard.
    initial_status : hikari.utilities.undefined.UndefinedOr[hikari.models.presences.Status]
        The initial status to have on each shard.
    initial_idle_since : hikari.utilities.undefined.UndefinedNoneOr[datetime.datetime]
        The initial time to show as being idle since, or `builtins.None` if not
        idle, for each shard.
    initial_is_afk : hikari.utilities.undefined.UndefinedOr[builtins.bool]
        If `builtins.True`, each shard will appear as being AFK on startup. If `builtins.False`,
        each shard will appear as _not_ being AFK.
    intents : hikari.models.intents.Intent or builtins.None
        The intents to use for each shard. If `builtins.None`, then no intents
        are passed. Note that on the version `7` gateway, this will cause an
        immediate connection close with an error code.

        The default for this is to enable all intents that do not require
        privileges.

        !!! warning
            Enabling privileged intents without enabling the intent
            in the Discord developer dashboard will result in shards immediately
            being disconnected on startup and the application raising an
            exception.
    large_threshold : builtins.int
        The number of members that need to be in a guild for the guild to be
        considered large. Defaults to the maximum, which is `250`.
    logging_level : builtins.str or builtins.int or builtins.None
        If not `builtins.None`, then this will be the logging level set if you
        have not enabled logging already. In this case, it should be a valid
        `logging` level that can be passed to `logging.basicConfig`. If you have
        already initialized logging, then this is irrelevant and this
        parameter can be safely ignored. If you set this to `builtins.None`,
        then no logging will initialize if you have a reason to not use any
        logging or simply wish to initialize it in your own time instead.

        !!! note
            Initializing logging means already have a handler in the root
            logger. This is usually achieved by calling `logging.basicConfig`
            or adding the handler manually.
    proxy_settings : hikari.config.ProxySettings or builtins.None
        Settings to use for the proxy.
    rest_version : int
        The version of the HTTP API to connect to. At the time of writing,
        only version `6` and version `7` (undocumented development release)
        are supported. This defaults to v6.
    shard_ids : typing.AbstractSet[builtins.int] or builtins.None
        A set of every shard ID that should be created and started on startup.
        If left to `builtins.None` along with `shard_count`, then auto-sharding
        is used instead, which is the default.
    shard_count : builtins.int or builtins.None
        The number of shards in the entire application. If left to
        `builtins.None` along with `shard_ids`, then auto-sharding is used
        instead, which is the default.
    stateless : builtins.bool
        If `builtins.True`, the bot will not implement a cache, and will be
        considered stateless. If `builtins.False`, then a cache will be used.

        While the cache components are a WIP, this will default to
        `builtins.True`. This should be expected to be changed to
        `builtins.False` before the first non-development release is made.
    token : builtins.str
        The bot token to use. This should not start with a prefix such as
        `Bot `, but instead only contain the token itself.

    !!! note
        The default parameters for `shard_ids` and `shard_count` are marked as
        undefined. When both of these are left to the default value, the
        application will use the Discord-provided recommendation for the number
        of shards to start.

        If only one of these two parameters are specified, expect a
        `builtins.TypeError` to be raised.

        Likewise, all shard_ids must be greater-than or equal-to `0`, and
        less than `shard_count` to be valid. Failing to provide valid
        values will result in a `builtins.ValueError` being raised.

    !!! note
        If all four of `initial_activity`, `initial_idle_since`,
        `initial_is_afk`, and `initial_status` are not defined and left to their
        default values, then the presence will not be _updated_ on startup
        at all.

    !!! note
        To disable auto-sharding, you should explicitly specify how many shards
        you wish to use. For non-sharded applications, this can be done by
        passing `shard_count` as `1` in the constructor.

    Raises
    ------
    builtins.TypeError
        If sharding information is not specified correctly.
    builtins.ValueError
        If sharding information is provided, but is unfeasible or invalid.
    """

    __slots__: typing.Sequence[str] = (
        "_cache",
        "_guild_chunker",
        "_connector_factory",
        "_debug",
        "_entity_factory",
        "_event_manager",
        "_event_factory",
        "_executor",
        "_global_ratelimit",
        "_http_settings",
        "_initial_activity",
        "_initial_idle_since",
        "_initial_is_afk",
        "_initial_status",
        "_intents",
        "_large_threshold",
        "_max_concurrency",
        "_proxy_settings",
        "_request_close_event",
        "_rest",
        "_shard_count",
        "_shard_gather_task",
        "_shard_ids",
        "_shards",
        "_started_at_monotonic",
        "_started_at_timestamp",
        "_tasks",
        "_token",
        "_version",
        "_voice",
        "_start_count",
    )

    def __init__(
        self,
        *,
        banner_package: typing.Optional[str] = "hikari",
        debug: bool = False,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        gateway_version: int = 6,
        http_settings: typing.Optional[config.HTTPSettings] = None,
        initial_activity: undefined.UndefinedNoneOr[presences.Activity] = undefined.UNDEFINED,
        initial_idle_since: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        initial_is_afk: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        initial_status: undefined.UndefinedOr[presences.Status] = undefined.UNDEFINED,
        intents: typing.Optional[intents_.Intent] = intents_.Intent.ALL_UNPRIVILEGED,
        large_threshold: int = 250,
        logging_level: typing.Union[str, int, None] = "INFO",
        proxy_settings: typing.Optional[config.ProxySettings] = None,
        rest_version: int = 6,
        rest_url: typing.Optional[str] = None,
        shard_ids: typing.Optional[typing.AbstractSet[int]] = None,
        shard_count: typing.Optional[int] = None,
        stateless: bool = True,
        token: str,
    ) -> None:
        if undefined.count(shard_ids, shard_count) == 1:
            raise TypeError("You must provide values for both shard_ids and shard_count, or neither.")

        if logging_level is not None and not _LOGGER.hasHandlers():
            logging.captureWarnings(True)
            logging.basicConfig(format=art.get_default_logging_format())
            logging.root.setLevel(logging_level)

        if banner_package is not None:
            self._dump_banner(banner_package)

        self._cache: cache_.IMutableCacheComponent
        self._event_manager: event_manager_base.EventManagerComponentBase
        self._guild_chunker: guild_chunker_.IGuildChunkerComponent

        if stateless:
            self._cache = stateless_cache_impl.StatelessCacheImpl(app=self)
            self._guild_chunker = stateless_guild_chunker_impl.StatelessGuildChunkerImpl(app=self)
            self._event_manager = stateless_event_manager.StatelessEventManagerImpl(
                app=self, mutable_cache=self._cache, intents=intents,
            )
            _LOGGER.info("this application is stateless, cache-based operations will not be available")
        else:
            self._cache = cache_impl.StatefulCacheImpl(app=self, intents=intents)
            self._guild_chunker = guild_chunker_impl.StatefulGuildChunkerImpl(app=self, intents=intents)
            self._event_manager = stateful_event_manager.StatefulEventManagerImpl(
                app=self, intents=intents, mutable_cache=self._cache,
            )

        self._connector_factory = rest_client_impl.BasicLazyCachedTCPConnectorFactory()
        self._debug = debug
        self._entity_factory = entity_factory_impl.EntityFactoryComponentImpl(app=self)
        self._event_factory = event_factory_impl.EventFactoryComponentImpl(app=self)
        self._executor = executor
        self._global_ratelimit = rate_limits.ManualRateLimiter()
        self._http_settings = config.HTTPSettings() if http_settings is None else http_settings
        self._initial_activity = initial_activity
        self._initial_idle_since = initial_idle_since
        self._initial_is_afk = initial_is_afk
        self._initial_status = initial_status
        self._intents = intents
        self._large_threshold = large_threshold
        self._max_concurrency = 1
        self._proxy_settings = config.ProxySettings() if proxy_settings is None else proxy_settings
        self._request_close_event = asyncio.Event()
        self._rest = rest_client_impl.RESTClientImpl(  # noqa: S106 - Possible hardcoded password
            app=self,
            connector_factory=self._connector_factory,
            connector_owner=False,
            debug=debug,
            http_settings=self._http_settings,
            proxy_settings=self._proxy_settings,
            token=token,
            token_type=constants.BOT_TOKEN,  # nosec
            rest_url=rest_url,
            version=rest_version,
        )
        self._shard_count: int = shard_count if shard_count is not None else 0
        self._shard_gather_task: typing.Optional[asyncio.Task[None]] = None
        self._shard_ids: typing.AbstractSet[int] = set() if shard_ids is None else shard_ids
        self._shards: typing.Dict[int, gateway_shard.IGatewayShard] = {}
        self._started_at_monotonic: typing.Optional[float] = None
        self._started_at_timestamp: typing.Optional[datetime.datetime] = None
        self._tasks: typing.Dict[int, asyncio.Task[typing.Any]] = {}
        self._token = token
        self._version = gateway_version
        self._voice = voice.VoiceComponentImpl(self, self._event_manager)
        # This should always be last so that we don't get an extra error when failed to initialize
        self._start_count: int = 0

    def __del__(self) -> None:
        # If something goes wrong while initializing the bot, `_start_count` might not be there.
        if hasattr(self, "_start_count") and self._start_count == 0:
            # TODO: may remove this as it causes issues with tests. Provisionally implemented only.
            warnings.warn(
                "Looks like your bot never started. Make sure you called bot.run() after you set the bot object up.",
                category=errors.HikariWarning,
            )

    @property
    def cache(self) -> cache_.ICacheComponent:
        return self._cache

    @property
    def guild_chunker(self) -> guild_chunker_.IGuildChunkerComponent:
        return self._guild_chunker

    @property
    def is_debug_enabled(self) -> bool:
        return self._debug

    @property
    def entity_factory(self) -> entity_factory_impl.EntityFactoryComponentImpl:
        return self._entity_factory

    @property
    def event_consumer(self) -> event_consumer_.IEventConsumerComponent:
        return self._event_manager

    @property
    def event_dispatcher(self) -> event_dispatcher_.IEventDispatcherComponent:
        return self._event_manager

    @property
    def event_factory(self) -> event_factory_impl.EventFactoryComponentImpl:
        return self._event_factory

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        return self._executor

    @property
    def heartbeat_latencies(self) -> typing.Mapping[int, typing.Optional[datetime.timedelta]]:
        return {shard_id: shard.heartbeat_latency for shard_id, shard in self._shards.items()}

    @property
    def heartbeat_latency(self) -> typing.Optional[datetime.timedelta]:
        started_shards = [
            shard.heartbeat_latency.total_seconds()
            for shard in self._shards.values()
            if shard.heartbeat_latency is not None
        ]

        if not started_shards:
            return None

        raw = sum(started_shards) / len(started_shards)
        return datetime.timedelta(seconds=raw)

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

    @property
    def intents(self) -> typing.Optional[intents_.Intent]:
        return self._intents

    @property
    def me(self) -> typing.Optional[users.OwnUser]:
        return self._cache.get_me()

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._proxy_settings

    @property
    def rest(self) -> rest_client_impl.RESTClientImpl:
        return self._rest

    @property
    def shards(self) -> typing.Mapping[int, gateway_shard.IGatewayShard]:
        return self._shards

    @property
    def shard_count(self) -> int:
        return self._shard_count

    @property
    def voice(self) -> voice.VoiceComponentImpl:
        return self._voice

    @property
    def started_at(self) -> typing.Optional[datetime.datetime]:
        return self._started_at_timestamp

    @property
    def uptime(self) -> datetime.timedelta:
        if self._started_at_monotonic:
            raw_uptime = date.monotonic() - self._started_at_monotonic
        else:
            raw_uptime = 0.0
        return datetime.timedelta(seconds=raw_uptime)

    async def start(self) -> None:
        asyncio.create_task(version_sniffer.log_available_updates(_LOGGER), name="check for hikari library updates")

        self._start_count += 1
        self._started_at_monotonic = date.monotonic()
        self._started_at_timestamp = date.local_datetime()

        if self._debug is True:
            _LOGGER.warning("debug mode is enabled, performance may be affected")

            # If possible, set the coroutine origin tracking depth to a larger value.
            # This feature is provisional, so don't hold your breath if it doesn't
            # exist.
            with contextlib.suppress(AttributeError, NameError):
                # noinspection PyUnresolvedReferences
                sys.set_coroutine_origin_tracking_depth(40)  # type: ignore[attr-defined]

            # Set debugging on the event loop.
            asyncio.get_event_loop().set_debug(True)

        self._tasks.clear()
        self._shard_gather_task = None

        await self._init()

        self._request_close_event.clear()

        await self.dispatch(lifetime_events.StartingEvent(app=self))

        start_time = date.monotonic()

        try:
            for i, shard_ids in enumerate(self._max_concurrency_chunker()):
                if self._request_close_event.is_set():
                    break

                if i > 0:
                    _LOGGER.info("waiting for 5 seconds until next shard can start")

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
                _LOGGER.warning(
                    "application aborted midway through initialization, will begin shutting down %s shard(s)",
                    len(self._tasks),
                )
                await self._abort()

                # We know an error occurred if this condition is met, so re-raise it.
                raise

            finish_time = date.monotonic()
            self._shard_gather_task = asyncio.create_task(
                self._gather(), name=f"zookeeper for {len(self._shards)} shard(s)"
            )

            # Don't bother logging this if we are single sharded. It is useless information.
            if len(self._shard_ids) > 1:
                _LOGGER.info("started %s shard(s) in approx %.2fs", len(self._shards), finish_time - start_time)

            await self.dispatch(lifetime_events.StartedEvent(app=self))

    def listen(
        self, event_type: typing.Optional[typing.Type[event_dispatcher_.EventT_co]] = None,
    ) -> typing.Callable[
        [event_dispatcher_.AsyncCallbackT[event_dispatcher_.EventT_co]],
        event_dispatcher_.AsyncCallbackT[event_dispatcher_.EventT_co],
    ]:
        return self.event_dispatcher.listen(event_type)

    def get_listeners(
        self, event_type: typing.Type[event_dispatcher_.EventT_co], *, polymorphic: bool = True,
    ) -> typing.Collection[event_dispatcher_.AsyncCallbackT[event_dispatcher_.EventT_co]]:
        return self.event_dispatcher.get_listeners(event_type, polymorphic=polymorphic)

    def has_listener(
        self,
        event_type: typing.Type[event_dispatcher_.EventT_co],
        callback: event_dispatcher_.AsyncCallbackT[event_dispatcher_.EventT_co],
        *,
        polymorphic: bool = True,
    ) -> bool:
        return self.event_dispatcher.has_listener(event_type, callback, polymorphic=polymorphic)

    def subscribe(
        self,
        event_type: typing.Type[event_dispatcher_.EventT_co],
        callback: event_dispatcher_.AsyncCallbackT[event_dispatcher_.EventT_co],
    ) -> event_dispatcher_.AsyncCallbackT[event_dispatcher_.EventT_co]:
        return self.event_dispatcher.subscribe(event_type, callback)

    def unsubscribe(
        self,
        event_type: typing.Type[event_dispatcher_.EventT_co],
        callback: event_dispatcher_.AsyncCallbackT[event_dispatcher_.EventT_co],
    ) -> None:
        return self.event_dispatcher.unsubscribe(event_type, callback)

    async def wait_for(
        self,
        event_type: typing.Type[event_dispatcher_.EventT_co],
        /,
        timeout: typing.Union[float, int, None],
        predicate: typing.Optional[event_dispatcher_.PredicateT[event_dispatcher_.EventT_co]] = None,
    ) -> event_dispatcher_.EventT_co:
        return await self.event_dispatcher.wait_for(event_type, predicate=predicate, timeout=timeout)

    def dispatch(self, event: base_events.Event) -> asyncio.Future[typing.Any]:
        return self.event_dispatcher.dispatch(event)

    async def close(self) -> None:
        await self._rest.close()
        await self._connector_factory.close()
        self._guild_chunker.close()
        self._global_ratelimit.close()

        if self._tasks:
            # This way if we cancel the stopping task, we still shut down properly.
            self._request_close_event.set()

            _LOGGER.info("stopping %s shard(s)", len(self._tasks))

            try:
                await self.dispatch(lifetime_events.StoppingEvent(app=self))
                await self._abort()
            finally:
                self._tasks.clear()
                await self.dispatch(lifetime_events.StoppedEvent(app=self))

    def run(self) -> None:
        loop = asyncio.get_event_loop()

        def on_interrupt() -> None:
            loop.create_task(self.close(), name="signal interrupt shutting down application")

        try:
            self._map_signal_handlers(loop.add_signal_handler, on_interrupt)
            loop.run_until_complete(self._run())
        except KeyboardInterrupt as ex:
            _LOGGER.info("received signal to shut down client")
            if self._debug:
                raise
            else:
                # The user will not care where this gets raised from, unless we are
                # debugging. It just causes a lot of confusing spam.
                raise ex.with_traceback(None)  # noqa: R100 raise in except handler without from
        finally:
            self._map_signal_handlers(loop.remove_signal_handler)
            _LOGGER.info("client has shut down")

    async def join(self) -> None:
        if self._shard_gather_task is not None:
            await self._shard_gather_task

    async def update_presence(
        self,
        *,
        status: undefined.UndefinedOr[presences.Status] = undefined.UNDEFINED,
        activity: undefined.UndefinedNoneOr[presences.Activity] = undefined.UNDEFINED,
        idle_since: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        afk: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> None:
        await asyncio.gather(
            *(
                s.update_presence(status=status, activity=activity, idle_since=idle_since, afk=afk)
                for s in self._shards.values()
                if s.is_alive
            )
        )

    async def _init(self) -> None:
        gw_recs, bot_user = await asyncio.gather(self.rest.fetch_gateway_bot(), self.rest.fetch_my_user())

        self._cache.set_me(bot_user)

        self._shard_count = self._shard_count if self._shard_count else gw_recs.shard_count
        self._shard_ids = self._shard_ids if self._shard_ids else set(range(self._shard_count))
        self._max_concurrency = gw_recs.session_start_limit.max_concurrency
        url = gw_recs.url

        reset_at = gw_recs.session_start_limit.reset_at.strftime("%d/%m/%y %H:%M:%S %Z").rstrip()

        shard_clients: typing.Dict[int, gateway_shard.IGatewayShard] = {}
        for shard_id in self._shard_ids:
            shard = gateway_shard_impl.GatewayShardImpl(
                app=self,
                compression=gateway_shard.GatewayCompression.PAYLOAD_ZLIB_STREAM,
                data_format=gateway_shard.GatewayDataFormat.JSON,
                debug=self._debug,
                http_settings=self._http_settings,
                initial_activity=self._initial_activity,
                initial_idle_since=self._initial_idle_since,
                initial_is_afk=self._initial_is_afk,
                initial_status=self._initial_status,
                intents=self._intents,
                large_threshold=self._large_threshold,
                proxy_settings=self._proxy_settings,
                shard_id=shard_id,
                shard_count=self._shard_count,
                token=self._token,
                url=url,
                version=self._version,
            )
            shard_clients[shard_id] = shard

        self._shards = shard_clients

        if len(self._shard_ids) == 1 and self._shard_ids == {0}:
            _LOGGER.info(
                "single-sharded configuration -- you have started %s/%s sessions prior to connecting (resets at %s)",
                gw_recs.session_start_limit.used,
                gw_recs.session_start_limit.total,
                reset_at,
            )
        else:
            _LOGGER.info(
                "max_concurrency: %s (contact Discord for an increase) -- "
                "will connect %s shards %s; the distributed application should have %s shards in total -- "
                "you have started %s/%s sessions prior to connecting (resets at %s)",
                gw_recs.session_start_limit.max_concurrency,
                len(self._shard_ids),
                reprlib.repr(sorted(self._shard_ids)),
                self._shard_count,
                gw_recs.session_start_limit.used,
                gw_recs.session_start_limit.total,
                reset_at,
            )

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
            _LOGGER.debug("gather failed, shutting down shard(s)")
            await self.close()

    async def _run(self) -> None:
        try:
            await self.start()
            await self.join()
        finally:
            await asyncio.shield(self.close())

    @staticmethod
    def _map_signal_handlers(
        mapping_function: typing.Callable[..., None], *args: typing.Callable[[], typing.Any]
    ) -> None:
        valid_interrupts = signal.valid_signals()
        # We must getattr on these, or we risk an exception occurring on Windows.
        for interrupt_name in ("SIGQUIT", "SIGTERM"):
            interrupt = getattr(signal, interrupt_name, None)
            if interrupt in valid_interrupts:
                with contextlib.suppress(NotImplementedError):
                    mapping_function(interrupt, *args)

    @staticmethod
    def _dump_banner(banner_package: str) -> None:
        sys.stdout.write(art.get_banner(banner_package) + "\n")
        sys.stdout.flush()
        # Give the TTY time to flush properly.
        time.sleep(0.05)
