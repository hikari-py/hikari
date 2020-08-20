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

__all__: typing.Final[typing.List[str]] = ["BotApp"]

import asyncio
import contextlib
import datetime
import logging
import math
import signal
import sys
import time
import typing
import warnings

from hikari import config
from hikari import errors
from hikari import intents as intents_
from hikari import presences
from hikari import traits
from hikari import undefined
from hikari.api import event_dispatcher
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
from hikari.utilities import art
from hikari.utilities import constants
from hikari.utilities import date
from hikari.utilities import version_sniffer

if typing.TYPE_CHECKING:
    import concurrent.futures

    from hikari import users
    from hikari.api import cache as cache_
    from hikari.api import chunker as guild_chunker_
    from hikari.events import base_events
    from hikari.impl import event_manager_base

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari")


class BotApp(
    traits.DispatcherAware,
    traits.EventFactoryAware,
    traits.RESTAware,
    traits.ShardAware,
    event_dispatcher.EventDispatcher,
):
    """Implementation of an auto-sharded single-instance bot application.

    Parameters
    ----------
    banner_package : typing.Optional[builtins.str]
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
    http_settings : typing.Optional[hikari.config.HTTPSettings]
        The HTTP-related settings to use.
    initial_activity : typing.Optional[hikari.presences.Activity]
        The initial activity to have on each shard. Defaults to `builtins.None`.
    initial_status : hikari.presences.Status
        The initial status to have on each shard. Defaults to
        `hikari.presences.Status.ONLINE`.
    initial_idle_since : typing.Optional[datetime.datetime]
        The initial time to show as being idle since, or `builtins.None` if not
        idle, for each shard. Defaults to `builtins.None`.
    initial_is_afk : builtins.bool
        If `builtins.True`, each shard will appear as being AFK on startup. If `builtins.False`,
        each shard will appear as _not_ being AFK. Defaults to `builtins.False`
    intents : typing.Optional[hikari.intents.Intents]
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
    logging_level : typing.Optional[builtins.str or builtins.int]
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
    proxy_settings : typing.Optional[hikari.config.ProxySettings]
        Settings to use for the proxy.
    rest_version : int
        The version of the HTTP API to connect to. At the time of writing,
        only version `6` and version `7` (undocumented development release)
        are supported. This defaults to v6.
    shard_ids : typing.Optional[typing.AbstractSet[builtins.int]]
        A set of every shard ID that should be created and started on startup.
        If left to `builtins.None` along with `shard_count`, then auto-sharding
        is used instead, which is the default.
    shard_count : typing.Optional[builtins.int]
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
        "_stateless",
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
        initial_activity: typing.Optional[presences.Activity] = None,
        initial_idle_since: typing.Optional[datetime.datetime] = None,
        initial_is_afk: bool = False,
        initial_status: presences.Status = presences.Status.ONLINE,
        intents: typing.Optional[intents_.Intents] = intents_.Intents.ALL_UNPRIVILEGED,
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

        self._connector_factory = rest_client_impl.BasicLazyCachedTCPConnectorFactory()
        self._debug = debug
        self._entity_factory = entity_factory_impl.EntityFactoryImpl(app=self)
        self._event_factory = event_factory_impl.EventFactoryImpl(app=self)
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
            connector_factory=self._connector_factory,
            connector_owner=False,
            debug=debug,
            entity_factory=self._entity_factory,
            executor=self._executor,
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
        self._shards: typing.Dict[int, gateway_shard.GatewayShard] = {}
        self._started_at_monotonic: typing.Optional[float] = None
        self._started_at_timestamp: typing.Optional[datetime.datetime] = None
        self._tasks: typing.Dict[int, asyncio.Task[typing.Any]] = {}
        self._token = token
        self._version = gateway_version
        # This should always be last so that we don't get an extra error when failed to initialize
        self._start_count: int = 0

        self._cache: cache_.MutableCache
        self._guild_chunker: guild_chunker_.GuildChunker
        self._event_manager: event_manager_base.EventManagerBase

        self._stateless = stateless
        if stateless:
            self._cache = stateless_cache_impl.StatelessCacheImpl()
            self._guild_chunker = stateless_guild_chunker_impl.StatelessGuildChunkerImpl()
            self._event_manager = stateless_event_manager.StatelessEventManagerImpl(app=self, intents=intents)
            _LOGGER.info("this application is stateless, cache-based operations will not be available")
        else:
            self._cache = cache_impl.StatefulCacheImpl(app=self, intents=intents)
            self._guild_chunker = guild_chunker_impl.StatefulGuildChunkerImpl(app=self, intents=intents)
            self._event_manager = stateful_event_manager.StatefulEventManagerImpl(
                app=self, cache=self._cache, intents=intents
            )

        self._voice = voice.VoiceComponentImpl(self, self._event_manager)

    def __del__(self) -> None:
        # If something goes wrong while initializing the bot, `_start_count` might not be there.
        if hasattr(self, "_start_count") and self._start_count == 0:
            # TODO: may remove this as it causes issues with tests. Provisionally implemented only.
            warnings.warn(
                "Looks like your bot never started. Make sure you called bot.run() after you set the bot object up.",
                category=errors.HikariWarning,
            )

    @property
    def cache(self) -> cache_.Cache:
        # <<inherited docstring from traits.CacheAware>>
        return self._cache

    @property
    def chunker(self) -> guild_chunker_.GuildChunker:
        # <<inherited docstring from traits.ChunkerAware>>
        return self._guild_chunker

    @property
    def dispatcher(self) -> event_dispatcher.EventDispatcher:
        # <<inherited docstring from traits.DispatcherAware>>
        return self._event_manager

    @property
    def entity_factory(self) -> entity_factory_impl.EntityFactoryImpl:
        # <<inherited docstring from traits.EntityFactoryAware>>
        return self._entity_factory

    @property
    def event_factory(self) -> event_factory_impl.EventFactoryImpl:
        # <<inherited docstring from traits.EventFactoryAware>>
        return self._event_factory

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        # <<inherited docstring from traits.ExecutorAware>>
        return self._executor

    @property
    def heartbeat_latencies(self) -> typing.Mapping[int, float]:
        # <<inherited docstring from traits.ShardAware>>
        return {shard_id: shard.heartbeat_latency for shard_id, shard in self._shards.items()}

    @property
    def heartbeat_latency(self) -> float:
        # <<inherited docstring from traits.ShardAware>>
        started_shards = [
            shard.heartbeat_latency for shard in self._shards.values() if not math.isnan(shard.heartbeat_latency)
        ]

        if not started_shards:
            return float("nan")

        return sum(started_shards) / len(started_shards)

    @property
    def http_settings(self) -> config.HTTPSettings:
        # <<inherited docstring from traits.NetworkSettingsAware>>
        return self._http_settings

    @property
    def intents(self) -> typing.Optional[intents_.Intents]:
        # <<inherited docstring from traits.ShardAware>>
        return self._intents

    @property
    def is_debug_enabled(self) -> bool:
        """Return `builtins.True` if debugging is enabled.

        Returns
        -------
        builtins.bool
            `builtins.True` if debugging is enabled, `builtins.False` otherwise.

        """
        return self._debug

    @property
    def is_stateless(self) -> bool:
        # <<inherited docstring from traits.CacheAware>>
        return self._stateless

    @property
    def me(self) -> typing.Optional[users.OwnUser]:
        # <<inherited docstring from traits.ShardAware>>
        return self._cache.get_me()

    @property
    def proxy_settings(self) -> config.ProxySettings:
        # <<inherited docstring from traits.NetworkSettingsAware>>
        return self._proxy_settings

    @property
    def rest(self) -> rest_client_impl.RESTClientImpl:
        # <<inherited docstring from traits.RESTAware>>
        return self._rest

    @property
    def shards(self) -> typing.Mapping[int, gateway_shard.GatewayShard]:
        # <<inherited docstring from traits.ShardAware>>
        return self._shards

    @property
    def shard_count(self) -> int:
        # <<inherited docstring from traits.ShardAware>>
        return self._shard_count

    @property
    def voice(self) -> voice.VoiceComponentImpl:
        # <<inherited docstring from traits.VoiceAware>>
        return self._voice

    @property
    def started_at(self) -> typing.Optional[datetime.datetime]:
        """Return the datetime when the bot first connected.

        Returns
        -------
        typing.Optional[datetime.datetime]
            The datetime that the bot connected at for the first time, or
            `builtins.None` if it has not yet connected.
        """
        return self._started_at_timestamp

    @property
    def uptime(self) -> float:
        """Return the number of seconds that the bot has been up.

        This is a monotonic time. To get the physical startup date, see
        `BotApp.started_at` instead.

        Returns
        -------
        builtins.float
            The number of seconds the application has been running for.
            If not started, then this will return `0.0`.
        """
        return date.monotonic() - self._started_at_monotonic if self._started_at_monotonic else 0.0

    async def start(self) -> None:
        """Determine sharding settings if needed, and start all shards.

        This method will first log if any library updates are available.

        The bot user info and sharding settings will be fetched from the REST
        API. If no explicit shard count/shard IDs have been provided to the
        constructor of this class, then the recommended shard count that
        Discord recommends will be used instead.

        The first shard will be started individually first. This ensures that
        we do not spam IDENTIFY payloads on multiple shards in large
        applications if the application will be unable to start.

        After this, each remaining shard will be started, respecting the API's
        max concurrency that Discord specifies.

        This will return once all shards that are to be started have
        fired their READY event. Any exceptions that are raised before this
        will be propagated, and all existing connections will be closed again.

        To wait for the bot to close indefinitely, you should call `BotApp.join`
        immediately after this call returns, else this will attempt to
        keep-alive in the background.
        """
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
                    _LOGGER.info("backing off for 5 seconds")
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
                await self._abort_shards()

                # We know an error occurred if this condition is met, so re-raise it.
                raise

            finish_time = date.monotonic()
            self._shard_gather_task = asyncio.create_task(
                self._gather_shard_lifecycles(), name=f"zookeeper for {len(self._shards)} shard(s)"
            )

            # Don't bother logging this if we are single sharded. It is useless information.
            if len(self._shard_ids) > 1:
                _LOGGER.info("started %s shard(s) in approx %.2fs", len(self._shards), finish_time - start_time)

            await self.dispatch(lifetime_events.StartedEvent(app=self))

    def listen(
        self, event_type: typing.Optional[typing.Type[event_dispatcher.EventT_co]] = None,
    ) -> typing.Callable[
        [event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co]],
        event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co],
    ]:
        # <<inherited docstring from event_dispatcher.EventDispatcher>>
        return self.dispatcher.listen(event_type)

    def get_listeners(
        self, event_type: typing.Type[event_dispatcher.EventT_co], *, polymorphic: bool = True,
    ) -> typing.Collection[event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co]]:
        # <<inherited docstring from event_dispatcher.EventDispatcher>>
        return self.dispatcher.get_listeners(event_type, polymorphic=polymorphic)

    def subscribe(
        self,
        event_type: typing.Type[event_dispatcher.EventT_co],
        callback: event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co],
    ) -> event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co]:
        # <<inherited docstring from event_dispatcher.EventDispatcher>>
        return self.dispatcher.subscribe(event_type, callback)

    def unsubscribe(
        self,
        event_type: typing.Type[event_dispatcher.EventT_co],
        callback: event_dispatcher.AsyncCallbackT[event_dispatcher.EventT_co],
    ) -> None:
        # <<inherited docstring from event_dispatcher.EventDispatcher>>
        return self.dispatcher.unsubscribe(event_type, callback)

    async def wait_for(
        self,
        event_type: typing.Type[event_dispatcher.EventT_co],
        /,
        timeout: typing.Union[float, int, None],
        predicate: typing.Optional[event_dispatcher.PredicateT[event_dispatcher.EventT_co]] = None,
    ) -> event_dispatcher.EventT_co:
        # <<inherited docstring from event_dispatcher.EventDispatcher>>
        return await self.dispatcher.wait_for(event_type, predicate=predicate, timeout=timeout)

    def dispatch(self, event: base_events.Event) -> asyncio.Future[typing.Any]:
        # <<inherited docstring from event_dispatcher.EventDispatcher>>
        return self.dispatcher.dispatch(event)

    async def close(self) -> None:
        """Request that all shards disconnect and the application shuts down.

        This will close all shards that are running, and then close any
        REST components and connectors.
        """
        self._guild_chunker.close()

        try:
            if self._tasks:
                # This way if we cancel the stopping task, we still shut down properly.
                self._request_close_event.set()

                _LOGGER.info("stopping %s shard(s)", len(self._tasks))

                try:
                    await self.dispatch(lifetime_events.StoppingEvent(app=self))
                    await self._abort_shards()
                finally:
                    self._tasks.clear()
                    await self.dispatch(lifetime_events.StoppedEvent(app=self))
        finally:
            await self._rest.close()
            await self._connector_factory.close()
            self._global_ratelimit.close()

    def run(self, *, close_loop: bool = True) -> None:
        """Run this application on the current thread in an event loop.

        This will use the event loop that is set for the current thread, or
        it will create one if it does not already exist.

        This call will **block** the current thread until the application
        has closed. Additionally, it will hook into any OS signals to
        detect external interrupts to request the process terminates.

        All hooks will be removed again on shutdown. Any fatal exceptions
        that may have occurred during the startup or execution of the
        application will be propagated.

        The application is always guaranteed to be shut down before this
        function completes or propagates any exception.

        Parameters
        ----------
        close_loop : builtins.bool
            If `builtins.True` (per the default), then the event loop will
            be explicitly closed once the application has closed. If
            `builtins.False`, this behaviour will not occur.

            Setting this to `builtins.False` may be desirable if you wish
            to continue using the event loop after the application has closed.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            _LOGGER.debug("no event loop registered on this thread; now creating one...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            self._map_signal_handlers(
                loop.add_signal_handler,
                lambda *_: loop.create_task(self.close(), name="signal interrupt shutting down application"),
            )
            loop.run_until_complete(self._shard_management_lifecycle())

        except KeyboardInterrupt as ex:
            _LOGGER.info("received OS signal to shut down client")
            if self._debug:
                raise
            # The user will not care where this gets raised from, unless we are
            # debugging. It just causes a lot of confusing spam.
            raise ex.with_traceback(None) from None

        except errors.GatewayClientClosedError:
            _LOGGER.info("client shut itself down")

        finally:
            self._map_signal_handlers(loop.remove_signal_handler)
            if close_loop and not loop.is_closed():
                _LOGGER.info("closing event loop")
                loop.close()

    async def join(self) -> None:
        """Wait for the application to finish running.

        If the application has not started, then calling this will return
        immediately.

        Any exceptions that are raised by the application that go unhandled
        will be propagated.
        """
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
        """Update the presence on all shards.

        This call will patch the presence on each shard. This means that
        unless you explicitly specify a parameter, the previous value will be
        retained. This means you do not have to track the global presence
        in your code.

        Parameters
        ----------
        status : hikari.undefined.UndefinedOr[hikari.presences.Status]
            The status to set all shards to. If undefined, no statuses are
            changed.
        activity : hikari.undefined.UndefinedNoneOr[hikari.presences.Activity]
            The activity to set. May be `builtins.None` if the activity should
            be cleared. If undefined, no activities are changed.
        idle_since : hikari.undefined.UndefinedNoneOr[datetime.datetime]
            The datetime to appear to be idle since. If `builtins.None`, then
            this is not sent (this does not need to be specified to set the
            bot's status to idle). If undefined, the idle timestamp is not
            changed.
        afk : hikari.undefined.UndefinedOr[builtins.bool]
            If `builtins.True`, then the bot is marked as being AFK. If
            `builtins.False`, the bot is marked as not being AFK. If
            unspecified, this is not changed.

        !!! note
            This will only send the update payloads to shards that are alive.
            Any shards that are not alive will cache the new presence for
            when they do start.

        !!! note
            If you want to set presences per shard, access the shard you wish
            to update (e.g. by using `BotApp.shards`), and call
            `hikari.api.shard.IGatewayShard.update_presence` on that shard.

            This method is simply a facade to make performing this in bulk
            simpler.
        """
        coros = [
            s.update_presence(status=status, activity=activity, idle_since=idle_since, afk=afk)
            for s in self._shards.values()
        ]

        await asyncio.gather(*coros)

    async def _init(self) -> None:
        gw_recs, bot_user = await asyncio.gather(self.rest.fetch_gateway_bot(), self.rest.fetch_my_user())

        self._cache.set_me(bot_user)

        self._shard_count = self._shard_count if self._shard_count else gw_recs.shard_count
        self._shard_ids = self._shard_ids if self._shard_ids else set(range(self._shard_count))
        self._max_concurrency = gw_recs.session_start_limit.max_concurrency
        url = gw_recs.url

        reset_at = gw_recs.session_start_limit.reset_at.strftime("%d/%m/%y %H:%M:%S %Z").rstrip()

        shard_clients: typing.Dict[int, gateway_shard.GatewayShard] = {}
        for shard_id in self._shard_ids:
            # TODO: allow custom connector factory?
            shard = gateway_shard_impl.GatewayShardImpl(
                compression=gateway_shard.GatewayCompression.PAYLOAD_ZLIB_STREAM,
                data_format=gateway_shard.GatewayDataFormat.JSON,
                debug=self._debug,
                event_consumer=self._event_manager.consume_raw_event,
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
                "will connect %s/%s shards with a max concurrency of %s -- "
                "you have started %s/%s sessions prior to connecting (resets at %s)",
                len(self._shard_ids),
                self._shard_count,
                self._max_concurrency,
                gw_recs.session_start_limit.used,
                gw_recs.session_start_limit.total,
                reset_at,
            )

    def _max_concurrency_chunker(self) -> typing.Iterator[typing.Iterator[int]]:
        """Yield generators of shard IDs.

        Each yielded generator will yield every shard ID that can be started
        at the same time.

        You should then wait 5 seconds between each window.

        The first window will always contain a single shard.
        The reasoning behind this is to ensure we are able to successfully
        connect on one shard before spamming the gateway with failed
        connections on large applications, as this can exhaust the daily
        identify limit.
        """
        n = 0
        is_first = True

        while n < self._shard_count:
            next_window = [i for i in range(n, n + self._max_concurrency) if i in self._shard_ids]
            # Don't yield anything if no IDs are in the given window.
            if is_first:
                is_first = False
                first, next_window = next_window[0], next_window[1:]
                yield iter((first,))

            if next_window:
                yield iter(next_window)

            n += self._max_concurrency

    async def _abort_shards(self) -> None:
        """Close all shards and wait for them to terminate."""
        for shard_id in self._tasks:
            if self._shards[shard_id].is_alive:
                _LOGGER.debug("stopping shard %s", shard_id)
                await self._shards[shard_id].close()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)

    async def _gather_shard_lifecycles(self) -> None:
        """Await all shards.

        Ensure shards are requested to close before the coroutine function
        completes.
        """
        try:
            _LOGGER.debug("gathering shards")
            await asyncio.gather(*self._tasks.values())
        finally:
            _LOGGER.debug("gather terminated, shutting down shard(s)")
            await asyncio.shield(self.close())

    async def _shard_management_lifecycle(self) -> None:
        """Start all shards and then wait for them to finish."""
        await self.start()
        await self.join()

    @staticmethod
    def _map_signal_handlers(
        mapping_function: typing.Callable[..., None], *args: typing.Callable[[], typing.Any]
    ) -> None:
        """Register/deregister a given signal handler to all signals."""
        valid_interrupts = signal.valid_signals()
        # We must getattr on these, or we risk an exception occurring on Windows.
        for interrupt_name in ("SIGQUIT", "SIGTERM"):
            interrupt = getattr(signal, interrupt_name, None)
            if interrupt in valid_interrupts:
                with contextlib.suppress(NotImplementedError):
                    mapping_function(interrupt, *args)

    @staticmethod
    def _dump_banner(banner_package: str) -> None:
        """Dump the banner art and wait for it to flush before continuing."""
        sys.stdout.write(art.get_banner(banner_package) + "\n")
        sys.stdout.flush()
        # Give the TTY time to flush properly.
        time.sleep(0.05)
