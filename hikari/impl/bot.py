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

__all__: typing.Final[typing.List[str]] = ["BotApp", "LoggerLevelT"]

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
from hikari.events import lifetime_events
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import event_factory as event_factory_impl
from hikari.impl import rest as rest_impl
from hikari.impl import shard as shard_impl
from hikari.impl import voice as voice_impl
from hikari.utilities import aio
from hikari.utilities import constants
from hikari.utilities import date
from hikari.utilities import event_stream
from hikari.utilities import ux

if typing.TYPE_CHECKING:
    from hikari.api import cache
    from hikari.api import chunker
    from hikari.api import rest as rest_
    from hikari.api import shard
    from hikari.impl import event_manager_base

LoggerLevelT = typing.Union[
    int,
    typing.Literal["DEBUG"],
    typing.Literal["INFO"],
    typing.Literal["WARNING"],
    typing.Literal["ERROR"],
    typing.Literal["CRITICAL"],
]
"""Type-hint for a valid logging level.

This may be an `int` logging level (e.g. `logging.DEBUG`, `logging.CRITICAL`),
or a capitalized string that matches one of `"DEBUG"`, `"INFO"`, `"WARNING"`,
`"ERROR"`, or `"CRITICAL"`.
"""

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari")


class BotApp(traits.BotAware, event_dispatcher.EventDispatcher):
    """Basic auto-sharding bot implementation.

    This is the class you will want to use to start, control, and build a bot
    with.

    Parameters
    ----------
    token : builtins.str
        The bot token to sign in with.

    Other Parameters
    ----------------
    allow_color : builtins.bool
        Defaulting to `builtins.True`, this will enable coloured console logs
        on any platform that is a TTY.
        Setting a `"CLICOLOR"` environment variable to any **non `0`** value
        will override this setting.

        Users should consider this an advice to the application on whether it is
        safe to show colours if possible or not. Since some terminals can be
        awkward or not support features in a standard way, the option to
        explicitly disable this is provided. See `force_color` for an
        alternative.
    banner : typing.Optional[builtins.str]
        The package to search for a `banner.txt` in. Defaults to `"hikari"` for
        the `"hikari/banner.txt"` banner.
        Setting this to `builtins.None` will disable the banner being shown.
    chunking_limit : typing.Optional[builtins.int]
        Defaults to `200`. The maximum amount of requests that this chunker
        should store information about for each shard.
    debug : builtins.bool
        Defaults to `builtins.False`. If `builtins.True`, then the contents
        of each payload sent and received over the REST API and any websockets.
        This may incur a noticeable performance penalty for large applications.
    enable_cache : builtins.bool
        Defaults to `builtins.True`. If `builtins.False`, the application is
        configured to be mostly stateless. This means almost all cache calls
        will yield an empty or `builtins.None` value, and you will be left to
        rely on the `REST` API only.

        This can be a viable alternative if you are providing a custom cache
        implementation, or simply do not want the overhead of maintaining a
        state in your application.
    executor : typing.Optional[concurrent.futures.Executor]
        Defaults to `builtins.None`. If non-`builtins.None`, then this executor
        is used instead of the `concurrent.futures.ThreadPoolExecutor` attached
        to the `asyncio.AbstractEventLoop` that the bot will run on. This
        executor is used primarily for file-IO.

        While mainly supporting the `concurrent.futures.ThreadPoolExecutor`
        implementation in the standard lib, Hikari's file handling systems
        should also work with `concurrent.futures.ProcessPoolExecutor`, which
        relies on all objects used in IPC to be `pickle`able. Many third-party
        libraries will not support this fully though, so your mileage may vary
        on using ProcessPoolExecutor implementations with this parameter.
    force_color : builtins.bool
        Defaults to `builtins.False`. If `builtins.True`, then this application
        will __force__ colour to be used in console-based output. Specifying a
        `"CLICOLOR_FORCE"` environment variable with a non-`"0"` value will
        override this setting.
    http_settings : typing.Optional[hikari.config.HTTPSettings]
        Optional custom HTTP configuration settings to use. Allows you to
        customise functionality such as whether SSL-verification is enabled,
        what timeouts `aiohttp` should expect to use for requests, and behavior
        regarding HTTP-redirects.
    intents : hikari.intents.Intents
        Defaults to `hikari.intents.Intents.ALL_UNPRIVILEGED`. This allows you
        to change which intents your application will use on the gateway. This
        can be used to control and change the types of events you will receive.
    logs : typing.Union[builtins.None, LoggerLevel, typing.Dict[str, typing.Any]]
        Defaults to `"INFO"`.

        If `builtins.None`, then the Python logging system is left uninitialized
        on startup, and you will need to configure it manually to view most
        logs that are output by components of this library.

        If one of the valid values in a `LoggerLevel`, then this will match a
        call to `colorlog.basicConfig` (a facade for `logging.basicConfig` with
        additional conduit for enabling coloured logging levels) with the
        `level` kwarg matching this value.

        If a `typing.Dict[str, typing.Any]` equivalent, then this value is
        passed to `logging.config.dictConfig` to allow the user to provide a
        specialized logging configuration of their choice.
    proxy_settings : typing.Optional[config.ProxySettings]
        If specified, custom proxy settings to use with network-layer logic
        in your application to get through an HTTP-proxy.
    rest_url : builtins.str
        Defaults to the Discord REST API URL. Can be overridden if you are
        attempting to point to an unofficial endpoint, or if you are attempting
        to mock/stub the Discord API for any reason. Generally you do not want
        to change this.

    !!! note
        `force_color` will always take precedence over `allow_color`.

    !!! note
        Settings that control the gateway session are provided to the
        `BotApp.run` and `BotApp.start` functions in this class. This is done
        to allow you to contextually customise details such as sharding
        configuration without having to re-initialize the entire application
        each time.
    """

    __slots__: typing.Sequence[str] = (
        "_banner",
        "_cache",
        "_chunker",
        "_closing_event",
        "_debug",
        "_entity_factory",
        "_events",
        "_event_factory",
        "_executor",
        "_http_settings",
        "_intents",
        "_proxy_settings",
        "_raw_event_consumer",
        "_rest",
        "_shards",
        "_token",
        "_voice",
    )

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
        logs: typing.Union[None, LoggerLevelT, typing.Dict[str, typing.Any]] = "INFO",
        proxy_settings: typing.Optional[config.ProxySettings] = None,
        rest_url: str = constants.REST_API_URL,
    ) -> None:
        # Beautification and logging
        ux.init_logging(logs, allow_color, force_color)
        self.print_banner(banner, allow_color, force_color)

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
        self._rest = rest_impl.RESTClientImpl(
            debug=debug,
            connector_factory=rest_impl.BasicLazyCachedTCPConnectorFactory(),
            connector_owner=True,
            entity_factory=self._entity_factory,
            executor=self._executor,
            http_settings=self._http_settings,
            proxy_settings=self._proxy_settings,
            rest_url=rest_url,
            token=token,
            token_type=constants.BOT_TOKEN_PREFIX,
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

    def dispatch(self, event: event_dispatcher.EventT_inv) -> asyncio.Future[typing.Any]:
        return self._events.dispatch(event)

    def get_listeners(
        self, event_type: typing.Type[event_dispatcher.EventT_co], *, polymorphic: bool = True
    ) -> typing.Collection[event_dispatcher.CallbackT[event_dispatcher.EventT_co]]:
        return self._events.get_listeners(event_type, polymorphic=polymorphic)

    async def join(self, until_close: bool = True) -> None:
        """Wait indefinitely until the application closes.

        This can be placed in a task and cancelled without affecting the
        application runtime itself. Any exceptions raised by shards will be
        propagated to here.

        Other Parameters
        ----------------
        until_close : builtins.bool
            Defaults to `builtins.True`. If set, the waiter will stop as soon as
            a request for shut down is processed. This can allow you to break
            and begin closing your own resources.

            If `builtins.False`, then this will wait until all shards' tasks
            have died.
        """
        awaitables: typing.List[typing.Awaitable[typing.Any]] = [s.join() for s in self._shards.values()]
        if until_close:
            awaitables.append(self._closing_event.wait())

        await aio.first_completed(*awaitables)

    def listen(
        self, event_type: typing.Optional[typing.Type[event_dispatcher.EventT_co]] = None
    ) -> typing.Callable[
        [event_dispatcher.CallbackT[event_dispatcher.EventT_co]], event_dispatcher.CallbackT[event_dispatcher.EventT_co]
    ]:
        return self._events.listen(event_type)

    @staticmethod
    def print_banner(banner: typing.Optional[str], allow_color: bool, force_color: bool) -> None:
        """Print the banner.

        This allows library vendors to override this behaviour, or choose to
        inject their own "branding" on top of what hikari provides by default.

        Normal users should not need to invoke this function, and can simply
        change the `banner` argument passed to the constructor to manipulate
        what is displayed.

        Parameters
        ----------
        banner : typing.Optional[builtins.str]
            The package to find a `banner.txt` in.
        allow_color : builtins.bool
            A flag that allows advising whether to allow color if supported or
            not. Can be overridden by setting a `"CLICOLOR"` environment
            variable to a non-`"0"` string.
        force_color : builtins.bool
            A flag that allows forcing color to always be output, even if the
            terminal device may not support it. Setting the `"CLICOLOR_FORCE"`
            environment variable to a non-`"0"` string will override this.

        !!! note
            `force_color` will always take precedence over `allow_color`.
        """
        ux.print_banner(banner, allow_color, force_color)

    def run(
        self,
        *,
        activity: typing.Optional[presences.Activity] = None,
        afk: bool = False,
        asyncio_debug: typing.Optional[bool] = None,
        close_executor: bool = False,
        close_loop: bool = True,
        coroutine_tracking_depth: typing.Optional[int] = None,
        enable_signal_handlers: bool = True,
        idle_since: typing.Optional[datetime.datetime] = None,
        ignore_session_start_limit: bool = False,
        large_threshold: int = 250,
        status: presences.Status = presences.Status.ONLINE,
        shard_ids: typing.Optional[typing.Set[int]] = None,
        shard_count: typing.Optional[int] = None,
    ) -> None:
        """Start the bot, wait for all shards to become ready, and then return.

        Other Parameters
        ----------------
        activity : typing.Optional[hikari.presences.Activity]
            The initial activity to display in the bot user presence, or
            `builtins.None` (default) to not show any.
        afk : builtins.bool
            The initial AFK state to display in the bot user presence, or
            `builtins.False` (default) to not show any.
        asyncio_debug : builtins.bool
            Defaults to `builtins.False`. If `builtins.True`, then debugging is
            enabled for the asyncio event loop in use.
        close_executor : builtins.bool
            Defaults to `builtins.False`. If `builtins.True`, any custom
            `concurrent.futures.Executor` passed to the constructor will be
            shut down when the application terminates. This does not affect the
            default executor associated with the event loop, and will not
            do anything if you do not provide a custom executor to the
            constructor.
        close_loop : builtins.bool
            Defaults to `builtins.True`. If `builtins.True`, then once the bot
            enters a state where all components have shut down permanently
            during application shutdown, then all asyngens and background tasks
            will be destroyed, and the event loop will be shut down.

            This will wait until all `hikari`-owned `aiohttp` connectors have
            had time to attempt to shut down correctly (around 250ms), and on
            Python 3.9 and newer, will also shut down the default event loop
            executor too.
        coroutine_tracking_depth : typing.Optional[builtins.int]
            Defaults to `builtins.None`. If an integer value and supported by
            the interpreter, then this many nested coroutine calls will be
            tracked with their call origin state. This allows you to determine
            where non-awaited coroutines may originate from, but generally you
            do not want to leave this enabled for performance reasons.
        enable_signal_handlers : builtins.bool
            Defaults to `builtins.True`. If on a __non-Windows__ OS with builtin
            support for kernel-level POSIX signals, then setting this to
            `builtins.True` will allow treating keyboard interrupts and other
            OS signals to safely shut down the application as calls to
            shut down the application properly rather than just killing the
            process in a dirty state immediately. You should leave this disabled
            unless you plan to implement your own signal handling yourself.
        idle_since : typing.Optional[datetime.datetime]
            The `datetime.datetime` the user should be marked as being idle
            since, or `builtins.None` (default) to not show this.
        ignore_session_start_limit : builtins.bool
            Defaults to `builtins.False`. If `builtins.False`, then attempting
            to start more sessions than you are allowed in a 24 hour window
            will throw a `hikari.errors.GatewayError` rather than going ahead
            and hitting the IDENTIFY limit, which may result in your token
            being reset. Setting to `builtins.True` disables this behavior.
        large_threshold : builtins.int
            Threshold for members in a guild before it is treated as being
            "large" and no longer sending member details in the `GUILD CREATE`
            event. Defaults to `250`.
        shard_ids : typing.Optional[typing.Set[builtins.int]]
            The shard IDs to create shards for. If not `builtins.None`, then
            a non-`None` `shard_count` must ALSO be provided. Defaults to
            `builtins.None`, which means the Discord-recommended count is used
            for your application instead.
        shard_count : typing.Optional[builtins.int]
            The number of shards to use in the entire distributed application.
            Defaults to `builtins.None` which results in the count being
            determined dynamically on startup.
        status : hikari.presences.Status
            The initial status to show for the user presence on startup.
            Defaults to `hikari.presences.Status.ONLINE`.
        """
        loop = asyncio.get_event_loop()
        signals = ("SIGINT", "SIGQUIT", "SIGTERM")

        if asyncio_debug:
            loop.set_debug(True)

        if coroutine_tracking_depth is not None:
            try:
                # Provisionally defined in CPython, may be removed without notice.
                loop.set_coroutine_tracking_depth(coroutine_tracking_depth)  # type: ignore[attr-defined]
            except AttributeError:
                _LOGGER.debug("cannot set coroutine tracking depth for %s, no functionality exists for this", loop)

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
                    ignore_session_start_limit=ignore_session_start_limit,
                    large_threshold=large_threshold,
                    shard_ids=shard_ids,
                    shard_count=shard_count,
                    status=status,
                )
            )

            loop.run_until_complete(self.join(until_close=False))

        except errors.HikariInterrupt as interrupt:
            _LOGGER.info(
                "received %s (%s), will proceed to shut down",
                interrupt.description or str(interrupt.signum),
                interrupt.signum,
            )

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

                _LOGGER.info("application has successfully terminated")

    async def start(
        self,
        *,
        activity: typing.Optional[presences.Activity] = None,
        afk: bool = False,
        idle_since: typing.Optional[datetime.datetime] = None,
        ignore_session_start_limit: bool = False,
        large_threshold: int = 250,
        shard_ids: typing.Optional[typing.Set[int]] = None,
        shard_count: typing.Optional[int] = None,
        status: presences.Status = presences.Status.ONLINE,
    ) -> None:
        """Start the bot, wait for all shards to become ready, and then return.

        Other Parameters
        ----------------
        activity : typing.Optional[hikari.presences.Activity]
            The initial activity to display in the bot user presence, or
            `builtins.None` (default) to not show any.
        afk : builtins.bool
            The initial AFK state to display in the bot user presence, or
            `builtins.False` (default) to not show any.
        idle_since : typing.Optional[datetime.datetime]
            The `datetime.datetime` the user should be marked as being idle
            since, or `builtins.None` (default) to not show this.
        ignore_session_start_limit : builtins.bool
            Defaults to `builtins.False`. If `builtins.False`, then attempting
            to start more sessions than you are allowed in a 24 hour window
            will throw a `hikari.errors.GatewayError` rather than going ahead
            and hitting the IDENTIFY limit, which may result in your token
            being reset. Setting to `builtins.True` disables this behavior.
        large_threshold : builtins.int
            Threshold for members in a guild before it is treated as being
            "large" and no longer sending member details in the `GUILD CREATE`
            event. Defaults to `250`.
        shard_ids : typing.Optional[typing.Set[builtins.int]]
            The shard IDs to create shards for. If not `builtins.None`, then
            a non-`None` `shard_count` must ALSO be provided. Defaults to
            `builtins.None`, which means the Discord-recommended count is used
            for your application instead.
        shard_count : typing.Optional[builtins.int]
            The number of shards to use in the entire distributed application.
            Defaults to `builtins.None` which results in the count being
            determined dynamically on startup.
        status : hikari.presences.Status
            The initial status to show for the user presence on startup.
            Defaults to `hikari.presences.Status.ONLINE`.
        """
        if shard_ids is not None and shard_count is None:
            raise TypeError("Must pass shard_count if specifying shard_ids manually")

        # Dispatch the update checker, the sharding requirements checker, and dispatch
        # the starting event together to save a little time on startup.
        asyncio.create_task(ux.check_for_updates(), name="check for package updates")
        requirements_task = asyncio.create_task(self._rest.fetch_gateway_bot(), name="fetch gateway sharding settings")
        await self.dispatch(lifetime_events.StartingEvent(app=self))
        requirements = await requirements_task

        if shard_count is None:
            shard_count = requirements.shard_count
        if shard_ids is None:
            shard_ids = set(range(shard_count))

        if requirements.session_start_limit.remaining < len(shard_ids) and not ignore_session_start_limit:
            _LOGGER.critical(
                "would have started %s session(s), but you only have %s remaining until %s. Starting more sessions "
                "than you are allowed to start may result in your token being reset. To skip this message, "
                "use bot.run(..., ignore_session_start_limit=True) or bot.start(..., ignore_session_start_limit=True)"
            )
            raise errors.GatewayError("Attempted to start more sessions than were allowed in the given time-window")

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
                shard_joiners = [asyncio.ensure_future(s.join()) for s in self._shards.values()]

                try:
                    # Attempt to wait for all started shards, for 5 seconds, along with the close
                    # waiter.
                    # If the close flag is set (i.e. user invoked bot.close), or one or more shards
                    # die in this time, we shut down immediately.
                    # If we time out, the joining tasks get discarded and we spin up the next
                    # block of shards, if applicable.
                    await aio.all_of(close_waiter, *shard_joiners, timeout=5)
                    if close_waiter:
                        _LOGGER.info("requested to shut down during startup of shards")
                    else:
                        _LOGGER.critical("one or more shards shut down unexpectedly during bot startup")
                    return

                except asyncio.TimeoutError:
                    # new window starts.
                    pass

                except Exception as ex:
                    _LOGGER.critical("an exception occurred in one of the started shards during bot startup: %r", ex)
                    raise

            started_shards = await aio.all_of(
                *(
                    self._start_one_shard(
                        activity=activity,
                        afk=afk,
                        idle_since=idle_since,
                        status=status,
                        large_threshold=large_threshold,
                        shard_id=candidate_shard_id,
                        shard_count=shard_count,
                        url=requirements.url,
                    )
                    for candidate_shard_id in window
                    if candidate_shard_id in shard_ids
                )
            )

            for started_shard in started_shards:
                self._shards[started_shard.id] = started_shard

        await self.dispatch(lifetime_events.StartedEvent(app=self))

    def stream(
        self,
        event_type: typing.Type[event_dispatcher.EventT_co],
        /,
        timeout: typing.Union[float, int, None],
        limit: typing.Optional[int] = None,
    ) -> event_stream.Streamer[event_dispatcher.EventT_co]:
        return self._events.stream(event_type, timeout=timeout, limit=limit)

    async def terminate(self, close_executor: bool = False) -> None:
        """Kill the application by shutting all components down.

        Other Parameters
        ----------------
        close_executor : builtins.bool
            Defaults to `builtins.False`. If `builtins.True`, any custom
            `concurrent.futures.Executor` passed to the constructor will be
            shut down when the application terminates. This does not affect the
            default executor associated with the event loop, and will not
            do anything if you do not provide a custom executor to the
            constructor.
        """

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

        await self.dispatch(lifetime_events.StoppingEvent(app=self))

        calls = [
            ("rest", self._rest.close()),
            ("chunker", self._chunker.close()),
            ("voice handler", self._voice.close()),
            *((f"shard {s.id}", s.close()) for s in self._shards.values()),
        ]

        for coro in asyncio.as_completed([handle(*pair) for pair in calls]):
            await coro

        # Users may still require use of an executor once shut down, so we
        # should do that after we do this.
        await self.dispatch(lifetime_events.StoppedEvent(app=self))

        if close_executor and self._executor is not None:
            _LOGGER.debug("shutting down executor %s", self._executor)
            self._executor.shutdown(wait=True)
            self._executor = None

    def subscribe(
        self, event_type: typing.Type[typing.Any], callback: event_dispatcher.CallbackT[typing.Any]
    ) -> event_dispatcher.CallbackT[typing.Any]:
        return self._events.subscribe(event_type, callback)

    def unsubscribe(
        self, event_type: typing.Type[typing.Any], callback: event_dispatcher.CallbackT[typing.Any]
    ) -> None:
        self._events.unsubscribe(event_type, callback)

    async def wait_for(
        self,
        event_type: typing.Type[event_dispatcher.EventT_co],
        /,
        timeout: typing.Union[float, int, None],
        predicate: typing.Optional[event_dispatcher.PredicateT[event_dispatcher.EventT_co]] = None,
    ) -> event_dispatcher.EventT_co:
        return await self._events.wait_for(event_type, timeout=timeout, predicate=predicate)

    async def _start_one_shard(
        self,
        activity: typing.Optional[presences.Activity],
        afk: bool,
        idle_since: typing.Optional[datetime.datetime],
        status: presences.Status,
        large_threshold: int,
        shard_id: int,
        shard_count: int,
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
            large_threshold=large_threshold,
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
