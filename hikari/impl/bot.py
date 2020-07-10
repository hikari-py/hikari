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
"""Basic implementation the components for a single-process bot."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["BotAppImpl"]

import asyncio
import contextlib
import datetime
import logging
import math
import os
import reprlib
import signal
import sys
import time
import typing

from hikari import config
from hikari.api import bot
from hikari.api.gateway import shard as gateway_shard
from hikari.events import other as other_events
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import rate_limits
from hikari.impl.cache import in_memory as cache_impl
from hikari.impl.cache import stateless as stateless_cache_impl
from hikari.impl.gateway import manager
from hikari.impl.gateway import shard as gateway_shard_impl
from hikari.impl.rest import client as rest_client_impl
from hikari.impl.voice import voice_component
from hikari.models import presences
from hikari.utilities import constants
from hikari.utilities import date
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import concurrent.futures

    from hikari.api import cache as cache_
    from hikari.api.gateway import dispatcher as event_dispatcher_
    from hikari.events import base as base_events
    from hikari.models import gateway as gateway_models
    from hikari.models import intents as intents_

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari")


class BotAppImpl(bot.IBotApp):
    """Implementation of an auto-sharded bot application.

    Parameters
    ----------
    debug : builtins.bool
        Defaulting to `builtins.False`, if `builtins.True`, then each payload sent and received
        on the gateway will be dumped to debug logs, and every HTTP API request
        and response will also be dumped to logs. This will provide useful
        debugging context at the cost of performance. Generally you do not
        need to enable this.
    gateway_compression : builtins.bool
        Defaulting to `builtins.True`, if `builtins.True`, then zlib transport
        compression is usedfor each shard connection. If `builtins.False`, no
        compression is used.
    gateway_version : builtins.int
        The version of the gateway to connect to. At the time of writing,
        only version `6` and version `7` (undocumented development release)
        are supported. This defaults to using v6.
    http_settings : hikari.config.HTTPSettings or builtins.None
        The HTTP-related settings to use.
    initial_activity : hikari.models.presences.Activity or builtins.None or hikari.utilities.undefined.UndefinedType
        The initial activity to have on each shard.
    initial_activity : hikari.models.presences.Status or hikari.utilities.undefined.UndefinedType
        The initial status to have on each shard.
    initial_idle_since : datetime.datetime or builtins.None or hikari.utilities.undefined.UndefinedType
        The initial time to show as being idle since, or `builtins.None` if not
        idle, for each shard.
    initial_idle_since : builtins.bool or hikari.utilities.undefined.UndefinedType
        If `builtins.True`, each shard will appear as being AFK on startup. If `builtins.False`,
        each shard will appear as _not_ being AFK.
    intents : hikari.models.intents.Intent or builtins.None
        The intents to use for each shard. If `builtins.None`, then no intents
        are passed. Note that on the version `7` gateway, this will cause an
        immediate connection close with an error code.
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
    shard_ids : typing.Set[builtins.int] or builtins.None
        A set of every shard ID that should be created and started on startup.
        If left to `builtins.None` along with `shard_count`, then auto-sharding
        is used instead, which is the default.
    shard_count : builtins.int or builtins.None
        The number of shards in the entire application. If left to
        `builtins.None` along with `shard_ids`, then auto-sharding is used
        instead, which is the default.
    stateless : builtins.bool
        If `builtins.True`, the bot will not implement a cache, and will be
        considered stateless. If `builtins.False`, then a cache will be used
        (this is the default).
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

    Raises
    ------
    builtins.TypeError
        If sharding information is not specified correctly.
    builtins.ValueError
        If sharding information is provided, but is unfeasible or invalid.
    """

    def __init__(
        self,
        *,
        debug: bool = False,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        gateway_compression: bool = True,
        gateway_version: int = 6,
        http_settings: typing.Optional[config.HTTPSettings] = None,
        initial_activity: typing.Union[undefined.UndefinedType, presences.Activity, None] = undefined.UNDEFINED,
        initial_idle_since: typing.Union[undefined.UndefinedType, datetime.datetime, None] = undefined.UNDEFINED,
        initial_is_afk: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        initial_status: typing.Union[undefined.UndefinedType, presences.Status] = undefined.UNDEFINED,
        intents: typing.Optional[intents_.Intent] = None,
        large_threshold: int = 250,
        logging_level: typing.Union[str, int, None] = "INFO",
        proxy_settings: typing.Optional[config.ProxySettings] = None,
        rest_version: int = 6,
        rest_url: typing.Optional[str] = None,
        shard_ids: typing.Optional[typing.Set[int]] = None,
        shard_count: typing.Optional[int] = None,
        stateless: bool = False,
        token: str,
    ) -> None:
        if logging_level is not None and not _LOGGER.hasHandlers():
            logging.captureWarnings(True)
            logging.basicConfig(format=self._determine_default_logging_format())
            _LOGGER.setLevel(logging_level)

        self._dump_banner()

        if stateless:
            self._cache = stateless_cache_impl.StatelessCacheImpl()
            _LOGGER.info("this application is stateless, cache-based operations will not be available")
        else:
            self._cache = cache_impl.InMemoryCacheComponentImpl(app=self)

        self._event_manager = manager.EventManagerImpl(app=self, intents_=intents)
        self._entity_factory = entity_factory_impl.EntityFactoryComponentImpl(app=self)
        self._global_ratelimit = rate_limits.ManualRateLimiter()
        self._voice = voice_component.VoiceComponentImpl(self, self._event_manager)

        self._started_at_monotonic: typing.Optional[float] = None
        self._started_at_timestamp: typing.Optional[datetime.datetime] = None

        self._executor = executor

        http_settings = config.HTTPSettings() if http_settings is None else http_settings
        proxy_settings = config.ProxySettings() if proxy_settings is None else proxy_settings

        if undefined.count(shard_ids, shard_count) == 1:
            raise TypeError("You must provide values for both shard_ids and shard_count, or neither.")

        self._debug = debug
        self._gather_task: typing.Optional[asyncio.Task[None]] = None
        self._http_settings = http_settings
        self._initial_activity = initial_activity
        self._initial_idle_since = initial_idle_since
        self._initial_is_afk = initial_is_afk
        self._initial_status = initial_status
        self._intents = intents
        self._large_threshold = large_threshold
        self._max_concurrency = 1
        self._proxy_settings = proxy_settings
        self._request_close_event = asyncio.Event()
        self._shard_count: int = shard_count if shard_count is not None else 0
        self._shard_ids: typing.Set[int] = set() if shard_ids is None else shard_ids
        self._shards: typing.Dict[int, gateway_shard.IGatewayShard] = {}
        self._tasks: typing.Dict[int, asyncio.Task[typing.Any]] = {}
        self._token = token
        self._use_compression = gateway_compression
        self._version = gateway_version

        self._rest = rest_client_impl.RESTClientImpl(  # noqa: S106 - Possible hardcoded password
            app=self,
            connector=None,
            connector_owner=True,
            debug=debug,
            http_settings=self._http_settings,
            global_ratelimit=self._global_ratelimit,
            proxy_settings=self._proxy_settings,
            token=token,
            token_type=constants.BOT_TOKEN,  # nosec
            rest_url=rest_url,
            version=rest_version,
        )

    @property
    def cache(self) -> cache_.ICacheComponent:
        return self._cache

    @property
    def entity_factory(self) -> entity_factory_impl.EntityFactoryComponentImpl:
        return self._entity_factory

    @property
    def event_consumer(self) -> manager.EventManagerImpl:
        return self._event_manager

    @property
    def event_dispatcher(self) -> manager.EventManagerImpl:
        return self._event_manager

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        return self._executor

    @property
    def heartbeat_latencies(self) -> typing.Mapping[int, typing.Optional[float]]:
        return {
            shard_id: None if math.isnan(shard.heartbeat_latency) else shard.heartbeat_latency
            for shard_id, shard in self._shards.items()
        }

    @property
    def heartbeat_latency(self) -> typing.Optional[float]:
        started_shards = [shard for shard in self._shards.values() if not math.isnan(shard.heartbeat_latency)]
        if not started_shards:
            return None

        return sum(shard.heartbeat_latency for shard in started_shards) / len(started_shards)

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

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

    def voice(self) -> voice_component.VoiceComponentImpl:
        return self._voice

    @property
    def started_at(self) -> typing.Optional[datetime.datetime]:
        return self._started_at_timestamp

    @property
    def uptime(self) -> datetime.timedelta:
        raw_uptime = time.perf_counter() - self._started_at_monotonic if self._started_at_monotonic is not None else 0.0
        return datetime.timedelta(seconds=raw_uptime)

    async def start(self) -> None:
        self._started_at_monotonic = time.perf_counter()
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
        self._gather_task = None

        await self._init()

        self._request_close_event.clear()

        await self.dispatch(other_events.StartingEvent())

        start_time = time.perf_counter()

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

            finish_time = time.perf_counter()
            self._gather_task = asyncio.create_task(self._gather(), name=f"zookeeper for {len(self._shards)} shard(s)")

            # Don't bother logging this if we are single sharded. It is useless information.
            if len(self._shard_ids) > 1:
                _LOGGER.info("started %s shard(s) in approx %.2fs", len(self._shards), finish_time - start_time)

            await self.dispatch(other_events.StartedEvent())

    def listen(
        self,
        event_type: typing.Union[
            undefined.UndefinedType, typing.Type[event_dispatcher_.EventT_co]
        ] = undefined.UNDEFINED,
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
        self._global_ratelimit.close()

        if self._tasks:
            # This way if we cancel the stopping task, we still shut down properly.
            self._request_close_event.set()

            _LOGGER.info("stopping %s shard(s)", len(self._tasks))

            try:
                await self.dispatch(other_events.StoppingEvent())
                await self._abort()
            finally:
                self._tasks.clear()
                await self.dispatch(other_events.StoppedEvent())

    async def fetch_sharding_settings(self) -> gateway_models.GatewayBot:
        return await self.rest.fetch_gateway_bot()

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
                # The user won't care where this gets raised from, unless we are
                # debugging. It just causes a lot of confusing spam.
                raise ex.with_traceback(None)  # noqa: R100 raise in except handler without from
        finally:
            self._map_signal_handlers(loop.remove_signal_handler)
            _LOGGER.info("client has shut down")

    async def join(self) -> None:
        if self._gather_task is not None:
            await self._gather_task

    async def update_presence(
        self,
        *,
        status: typing.Union[undefined.UndefinedType, presences.Status] = undefined.UNDEFINED,
        activity: typing.Union[undefined.UndefinedType, presences.Activity, None] = undefined.UNDEFINED,
        idle_since: typing.Union[undefined.UndefinedType, datetime.datetime, None] = undefined.UNDEFINED,
        afk: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
    ) -> None:
        await asyncio.gather(
            *(
                s.update_presence(status=status, activity=activity, idle_since=idle_since, afk=afk)
                for s in self._shards.values()
                if s.is_alive
            )
        )

    async def _init(self) -> None:
        gw_recs = await self.fetch_sharding_settings()

        self._shard_count = self._shard_count if self._shard_count else gw_recs.shard_count
        self._shard_ids = self._shard_ids if self._shard_ids else set(range(self._shard_count))
        self._max_concurrency = gw_recs.session_start_limit.max_concurrency
        url = gw_recs.url

        reset_at = gw_recs.session_start_limit.reset_at.strftime("%d/%m/%y %H:%M:%S %Z").rstrip()

        shard_clients: typing.Dict[int, gateway_shard.IGatewayShard] = {}
        for shard_id in self._shard_ids:
            shard = gateway_shard_impl.GatewayShardImpl(
                app=self,
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
                use_compression=self._use_compression,
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
            await self.close()

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

    def _dump_banner(self) -> None:
        from importlib import resources
        import platform
        import string

        import aiohttp
        import attr

        from hikari import _about

        args = {
            # Colours:
            ""
            # Hikari stuff.
            "hikari_version": _about.__version__,
            "hikari_copyright": _about.__copyright__,
            "hikari_license": _about.__license__,
            "hikari_install_location": os.path.abspath(os.path.dirname(_about.__file__)),
            "hikari_documentation_url": _about.__docs__,
            "hikari_discord_invite": _about.__discord_invite__,
            "hikari_source_url": _about.__url__,
            # Python stuff.
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "python_build": " ".join(platform.python_build()),
            "python_branch": platform.python_branch(),
            "python_compiler": platform.python_compiler(),
            # Platform specific stuff I might remove later.
            "libc_version": " ".join(platform.libc_ver()),
            # System stuff.
            "platform_system": platform.system(),
            "platform_architecture": " ".join(platform.architecture()),
            # Dependencies.
            "aiohttp_version": aiohttp.__version__,
            "attrs_version": attr.__version__,
        }

        args.update(self._determine_console_colour_palette())

        with resources.open_text("hikari.impl", "banner.txt") as banner_fp:
            banner = string.Template(banner_fp.read()).safe_substitute(args)

        sys.stdout.write(banner + "\n")
        sys.stdout.flush()
        # Give the TTY time to flush properly.
        time.sleep(0.2)

    def _determine_default_logging_format(self) -> str:
        format_str = (
            "{red}%(levelname)-1.1s{default} {yellow}%(asctime)23.23s"  # noqa: FS003 f-string missing prefix
            "{default} {bright}{green}%(name)20.20s: {default}{cyan}%(message)s{default}"  # noqa: FS003
        )

        return format_str.format(**self._determine_console_colour_palette())

    @staticmethod
    def _determine_console_colour_palette() -> typing.Dict[str, str]:
        # Modified from
        # https://github.com/django/django/blob/master/django/core/management/color.py

        plat = sys.platform
        supports_color = False

        # isatty is not always implemented, https://code.djangoproject.com/ticket/6223
        is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

        if plat != "Pocket PC":
            if plat == "win32":
                supports_color |= os.getenv("TERM_PROGRAM", None) == "mintty"
                supports_color |= "ANSICON" in os.environ
                supports_color |= is_a_tty
            else:
                supports_color = is_a_tty

            supports_color |= bool(os.getenv("PYCHARM_HOSTED", ""))

        palette = {
            "default": "\033[0m",
            "bright": "\033[1m",
            "underline": "\033[4m",
            "invert": "\033[7m",
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
            "white": "\033[37m",
            "bright_red": "\033[91m",
            "bright_green": "\033[92m",
            "bright_yellow": "\033[93m",
            "bright_blue": "\033[94m",
            "bright_magenta": "\033[95m",
            "bright_cyan": "\033[96m",
            "bright_white": "\033[97m",
            "framed": "\033[51m",
            "dim": "\033[2m",
        }

        if not supports_color:
            for key in list(palette.keys()):
                palette[key] = ""

        return palette
