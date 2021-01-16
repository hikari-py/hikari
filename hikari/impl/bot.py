# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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

__all__: typing.List[str] = ["BotApp"]

import asyncio
import contextlib
import datetime
import logging
import math
import signal
import sys
import threading
import traceback
import types
import typing
import warnings

from hikari import config
from hikari import errors
from hikari import intents as intents_
from hikari import presences
from hikari import traits
from hikari import undefined
from hikari.api import event_manager as event_manager_
from hikari.impl import cache as cache_impl
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import event_factory as event_factory_impl
from hikari.impl import event_manager as event_manager_impl
from hikari.impl import rest as rest_impl
from hikari.impl import shard as shard_impl
from hikari.impl import voice as voice_impl
from hikari.internal import aio
from hikari.internal import time
from hikari.internal import ux

if typing.TYPE_CHECKING:
    import concurrent.futures

    from hikari import event_stream
    from hikari import users
    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import event_factory as event_factory_
    from hikari.api import rest as rest_
    from hikari.api import shard as gateway_shard
    from hikari.api import voice as voice_
    from hikari.internal import data_binding

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari")


class BotApp(traits.BotAware, event_manager_.EventManager):
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
    cache_settings : typing.Optional[hikari.config.CacheSettings]
        Optional cache settings. If unspecified, will use the defaults.
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

        As a side note, you can always opt to leave this on the default value
        and then use an incremental `logging.config.dictConfig` that applies
        any additional changes on top of the base configuration, if you prefer.
        An example of can be found in the `Example` section.

        Note that `"TRACE_HIKARI"` is a library-specific logging level
        which is expected to be more verbose than `"DEBUG"`.
    max_rate_limit : builtins.float
        The max number of seconds to backoff for when rate limited. Anything
        greater than this will instead raise an error.

        This defaults to five minutes if left to the default value. This is to
        stop potentially indefinitely waiting on an endpoint, which is almost
        never what you want to do if giving a response to a user.

        You can set this to `float("inf")` to disable this check entirely.

        Note that this only applies to the REST API component that communicates
        with Discord, and will not affect sharding or third party HTTP endpoints
        that may be in use.
    proxy_settings : typing.Optional[config.ProxySettings]
        Custom proxy settings to use with network-layer logic
        in your application to get through an HTTP-proxy.
    rest_url : typing.Optional[builtins.str]
        Defaults to the Discord REST API URL if `builtins.None`. Can be
        overridden if you are attempting to point to an unofficial endpoint, or
        if you are attempting to mock/stub the Discord API for any reason.
        Generally you do not want to change this.

    !!! note
        `force_color` will always take precedence over `allow_color`.

    !!! note
        Settings that control the gateway session are provided to the
        `BotApp.run` and `BotApp.start` functions in this class. This is done
        to allow you to contextually customise details such as sharding
        configuration without having to re-initialize the entire application
        each time.

    Example
    -------
    Setting up logging using a dictionary configuration:

    ```py
    import os

    import hikari

    # We want to make gateway logs output as DEBUG, and TRACE for all ratelimit content.
    bot = hikari.Bot(
        token=os.environ["BOT_TOKEN"],
        logs={
            "version": 1,
            "incremental": True,
            "loggers": {
                "hikari.gateway": {"level": "DEBUG"},
                "hikari.ratelimits": {"level": "TRACE_HIKARI"},
            },
        },
    )
    ```
    """

    __slots__: typing.Sequence[str] = (
        "_cache",
        "_closing_event",
        "_closed",
        "_entity_factory",
        "_events",
        "_event_factory",
        "_executor",
        "_http_settings",
        "_intents",
        "_is_alive",
        "_proxy_settings",
        "_rest",
        "_shards",
        "_token",
        "_voice",
        "shards",
    )

    def __init__(
        self,
        token: str,
        *,
        allow_color: bool = True,
        banner: typing.Optional[str] = "hikari",
        executor: typing.Optional[concurrent.futures.Executor] = None,
        force_color: bool = False,
        cache_settings: typing.Optional[config.CacheSettings] = None,
        http_settings: typing.Optional[config.HTTPSettings] = None,
        intents: intents_.Intents = intents_.Intents.ALL_UNPRIVILEGED,
        logs: typing.Union[None, int, str, typing.Dict[str, typing.Any]] = "INFO",
        max_rate_limit: float = 300,
        proxy_settings: typing.Optional[config.ProxySettings] = None,
        rest_url: typing.Optional[str] = None,
    ) -> None:
        # Beautification and logging
        ux.init_logging(logs, allow_color, force_color)
        self.print_banner(banner, allow_color, force_color)

        # Settings and state
        self._closing_event = asyncio.Event()
        self._closed = False
        self._is_alive = False
        self._executor = executor
        self._http_settings = http_settings if http_settings is not None else config.HTTPSettings()
        self._intents = intents
        self._proxy_settings = proxy_settings if proxy_settings is not None else config.ProxySettings()
        self._token = token

        # Caching
        cache_settings = cache_settings if cache_settings is not None else config.CacheSettings()
        self._cache = cache_impl.CacheImpl(self, cache_settings)

        # Event handling
        self._events = event_manager_impl.EventManagerImpl(self, cache=self._cache)

        # Entity creation
        self._entity_factory = entity_factory_impl.EntityFactoryImpl(self)

        # Event creation
        self._event_factory = event_factory_impl.EventFactoryImpl(self)

        # Voice subsystem
        self._voice = voice_impl.VoiceComponentImpl(self)

        # RESTful API.
        self._rest = rest_impl.RESTClientImpl(
            connector_factory=rest_impl.BasicLazyCachedTCPConnectorFactory(self._http_settings),
            connector_owner=True,
            entity_factory=self._entity_factory,
            executor=self._executor,
            http_settings=self._http_settings,
            max_rate_limit=max_rate_limit,
            proxy_settings=self._proxy_settings,
            rest_url=rest_url,
            token=token,
        )

        # We populate these on startup instead, as we need to possibly make some
        # HTTP requests to determine what to put in this mapping.
        self._shards: typing.Dict[int, gateway_shard.GatewayShard] = {}
        self.shards: typing.Mapping[int, gateway_shard.GatewayShard] = types.MappingProxyType(self._shards)

    @property
    def cache(self) -> cache_.Cache:
        return self._cache

    @property
    def event_manager(self) -> event_manager_.EventManager:
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
        return sum(latencies) / len(latencies) if latencies else float("nan")

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

    @property
    def intents(self) -> intents_.Intents:
        return self._intents

    @property
    def me(self) -> typing.Optional[users.OwnUser]:
        return self._cache.get_me()

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._proxy_settings

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

    @property
    def is_alive(self) -> bool:
        return self._is_alive

    def add_raw_consumer(self, name: str, consumer: event_manager_.ConsumerT, /) -> None:
        self._events.add_raw_consumer(name, consumer)

    def get_raw_consumers(self, name: str, /) -> typing.Sequence[event_manager_.ConsumerT]:
        return self._events.get_raw_consumers(name)

    def remove_raw_consumer(self, name: str, consumer: event_manager_.ConsumerT, /) -> None:
        self._events.remove_raw_consumer(name, consumer)

    def consume_raw_event(
        self, shard: gateway_shard.GatewayShard, event_name: str, payload: data_binding.JSONObject
    ) -> None:
        self._events.consume_raw_event(shard, event_name, payload)

    async def close(self, force: bool = True) -> None:
        """Kill the application by shutting all components down."""
        if not self._closing_event.is_set():
            _LOGGER.debug("bot requested to shutdown [force:%s]", force)

        self._closing_event.set()

        if self._closed or not force:
            return

        self._closed = True

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

        await self.dispatch(self.event_factory.deserialize_stopping_event())

        _LOGGER.log(ux.TRACE, "StoppingEvent dispatch completed, now beginning termination")

        calls = [
            ("rest", self._rest.close()),
            ("voice handler", self._voice.close()),
            *((f"shard {s.id}", s.close()) for s in self._shards.values()),
        ]

        for coro in asyncio.as_completed([handle(*pair) for pair in calls]):
            await coro

        # Join any shards until they finish
        await aio.all_of(*(s.join() for s in self._shards.values()), timeout=len(self._shards))

        # Clear out cache and shard map
        self._cache.clear()
        self._shards.clear()
        self._is_alive = False

        await self.dispatch(self.event_factory.deserialize_stopped_event())

    def dispatch(self, event: event_manager_.EventT_inv) -> asyncio.Future[typing.Any]:
        return self._events.dispatch(event)

    def get_listeners(
        self, event_type: typing.Type[event_manager_.EventT_co], *, polymorphic: bool = True
    ) -> typing.Collection[event_manager_.CallbackT[event_manager_.EventT_co]]:
        return self._events.get_listeners(event_type, polymorphic=polymorphic)

    async def join(self, until_close: bool = True) -> None:
        awaitables: typing.List[typing.Awaitable[typing.Any]] = [s.join() for s in self._shards.values()]
        if until_close:
            awaitables.append(self._closing_event.wait())

        await aio.first_completed(*awaitables)

    def listen(
        self, event_type: typing.Optional[typing.Type[event_manager_.EventT_co]] = None
    ) -> typing.Callable[
        [event_manager_.CallbackT[event_manager_.EventT_co]], event_manager_.CallbackT[event_manager_.EventT_co]
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
        check_for_updates: bool = True,
        close_passed_executor: bool = False,
        close_loop: bool = True,
        coroutine_tracking_depth: typing.Optional[int] = None,
        enable_signal_handlers: bool = True,
        idle_since: typing.Optional[datetime.datetime] = None,
        ignore_session_start_limit: bool = False,
        large_threshold: int = 250,
        propagate_interrupts: bool = False,
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
        check_for_updates : builtins.bool
            Defaults to `builtins.True`. If `builtins.True`, will check for
            newer versions of `hikari` on PyPI and notify if available.
        close_passed_executor : builtins.bool
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
        propagate_interrupts : builtins.bool
            Defaults to `builtins.False`. If set to `builtins.True`, then any
            internal `hikari.errors.HikariInterrupt` that is raises as a
            result of catching an OS level signal will result in the
            exception being rethrown once the application has closed. This can
            allow you to use hikari signal handlers and still be able to
            determine what kind of interrupt the application received after
            it closes. When `builtins.False`, nothing is raised and the call
            will terminate cleanly and silently where possible instead.
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
            raise TypeError("'shard_ids' must be passed with 'shard_count'")

        loop = asyncio.get_event_loop()
        signals = ("SIGINT", "SIGTERM")

        if asyncio_debug:
            loop.set_debug(True)

        if coroutine_tracking_depth is not None:
            try:
                # Provisionally defined in CPython, may be removed without notice.
                loop.set_coroutine_tracking_depth(coroutine_tracking_depth)  # type: ignore[attr-defined]
            except AttributeError:
                _LOGGER.log(
                    ux.TRACE, "cannot set coroutine tracking depth for %s, no functionality exists for this", loop
                )

        # Throwing this in the handler will lead to lots of fun OS specific shenanigans. So, lets just
        # cache it for later, I guess.
        interrupt: typing.Optional[errors.HikariInterrupt] = None
        loop_thread_id = threading.get_native_id()

        def handle_os_interrupt(signum: int, frame: types.FrameType) -> None:
            # If we use a POSIX system, then raising an exception in here works perfectly and shuts the loop down
            # with an exception, which is good.
            # Windows, however, is special on this front. On Windows, the exception is caught by whatever was
            # currently running on the event loop at the time, which is annoying for us, as this could be fired into
            # the task for an event dispatch, for example, which is a guarded call that is never waited for by design.

            # We can't always safely intercept this either, as Windows does not allow us to use asyncio loop
            # signal listeners (since Windows doesn't have kernel-level signals, only emulated system calls
            # for a remote few standard C signal types). Thus, the best solution here is to set the close bit
            # instead, which will let the bot start to clean itself up as if the user closed it manually via a call
            # to `bot.close()`.
            nonlocal interrupt
            signame = signal.strsignal(signum)
            assert signame is not None  # Will always be True

            interrupt = errors.HikariInterrupt(signum, signame)
            # The loop may or may not be running, depending on the state of the application when this occurs.
            # Signals on POSIX only occur on the main thread usually, too, so we need to ensure this is
            # threadsafe if we want the user's application to still shut down if on a separate thread.
            # We log native thread IDs purely for debugging purposes.
            if _LOGGER.isEnabledFor(ux.TRACE):
                _LOGGER.log(
                    ux.TRACE,
                    "interrupt %s occurred on thread %s, bot on thread %s will be notified to shut down shortly\n"
                    "Stacktrace for developer sanity:\n%s",
                    signum,
                    threading.get_native_id(),
                    loop_thread_id,
                    "".join(traceback.format_stack(frame)),
                )

            asyncio.run_coroutine_threadsafe(self._set_close_flag(signame, signum), loop)

        if enable_signal_handlers:
            for sig in signals:
                try:
                    signum = getattr(signal, sig)
                    signal.signal(signum, handle_os_interrupt)
                except AttributeError:
                    _LOGGER.log(ux.TRACE, "signal %s is not implemented on your platform", sig)

        try:
            loop.run_until_complete(
                self.start(
                    activity=activity,
                    afk=afk,
                    check_for_updates=check_for_updates,
                    idle_since=idle_since,
                    ignore_session_start_limit=ignore_session_start_limit,
                    large_threshold=large_threshold,
                    shard_ids=shard_ids,
                    shard_count=shard_count,
                    status=status,
                )
            )

            loop.run_until_complete(self.join())

        finally:
            try:
                loop.run_until_complete(self.close())

                if close_passed_executor and self._executor is not None:
                    _LOGGER.debug("shutting down executor %s", self._executor)
                    self._executor.shutdown(wait=True)
                    self._executor = None
            finally:
                if enable_signal_handlers:
                    for sig in signals:
                        try:
                            signum = getattr(signal, sig)
                            signal.signal(signum, signal.SIG_DFL)
                        except AttributeError:
                            # Signal not implemented probably. We should have logged this earlier.
                            pass

                if close_loop:
                    self._destroy_loop(loop)

                _LOGGER.info("application has successfully terminated")

                if propagate_interrupts and interrupt is not None:
                    raise interrupt

    async def start(
        self,
        *,
        activity: typing.Optional[presences.Activity] = None,
        afk: bool = False,
        check_for_updates: bool = True,
        idle_since: typing.Optional[datetime.datetime] = None,
        ignore_session_start_limit: bool = False,
        large_threshold: int = 250,
        shard_ids: typing.Optional[typing.AbstractSet[int]] = None,
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
        check_for_updates : builtins.bool
            Defaults to `builtins.True`. If `builtins.True`, will check for
            newer versions of `hikari` on PyPI and notify if available.
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

        self._validate_activity(activity)

        # Dispatch the update checker, the sharding requirements checker, and dispatch
        # the starting event together to save a little time on startup.
        start_time = time.monotonic()

        if check_for_updates:
            asyncio.create_task(
                ux.check_for_updates(self._http_settings, self._proxy_settings),
                name="check for package updates",
            )

        requirements_task = asyncio.create_task(self._rest.fetch_gateway_bot(), name="fetch gateway sharding settings")
        await self.dispatch(self.event_factory.deserialize_starting_event())
        requirements = await requirements_task

        if shard_count is None:
            shard_count = requirements.shard_count
        if shard_ids is None:
            shard_ids = set(range(shard_count))

        if requirements.session_start_limit.remaining < len(shard_ids) and not ignore_session_start_limit:
            _LOGGER.critical(
                "would have started %s session%s, but you only have %s session%s remaining until %s. Starting more "
                "sessions than you are allowed to start may result in your token being reset. To skip this message, "
                "use bot.run(..., ignore_session_start_limit=True) or bot.start(..., ignore_session_start_limit=True)",
                len(shard_ids),
                "s" if len(shard_ids) != 1 else "",
                requirements.session_start_limit.remaining,
                "s" if requirements.session_start_limit.remaining != 1 else "",
                requirements.session_start_limit.reset_at,
            )
            raise errors.GatewayError("Attempted to start more sessions than were allowed in the given time-window")

        self._is_alive = True
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
                shard_joiners = [s.join() for s in self._shards.values()]

                try:
                    # Attempt to wait for all started shards, for 5 seconds, along with the close
                    # waiter.
                    # If the close flag is set (i.e. user invoked bot.close), or one or more shards
                    # die in this time, we shut down immediately.
                    # If we time out, the joining tasks get discarded and we spin up the next
                    # block of shards, if applicable.
                    _LOGGER.info("the next startup window is in 5 seconds, please wait...")
                    await aio.first_completed(aio.all_of(*shard_joiners, timeout=5), close_waiter)

                    if not close_waiter.cancelled():
                        _LOGGER.info("requested to shut down during startup of shards")
                    else:
                        _LOGGER.critical("one or more shards shut down unexpectedly during bot startup")
                    return

                except asyncio.TimeoutError:
                    # If any shards stopped silently, we should close.
                    if any(not s.is_alive for s in self._shards.values()):
                        _LOGGER.warning("one of the shards has been manually shut down (no error), will now shut down")
                        await self.close()
                        return
                    # new window starts.

                except Exception as ex:
                    _LOGGER.critical("an exception occurred in one of the started shards during bot startup: %r", ex)
                    raise

            await aio.all_of(
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

        await self.dispatch(self.event_factory.deserialize_started_event())

        _LOGGER.info("application started successfully in approx %.2f seconds", time.monotonic() - start_time)

    def _check_if_alive(self) -> None:
        if not self._is_alive:
            raise errors.ComponentNotRunningError("bot is not running so it cannot be interacted with")

    def stream(
        self,
        event_type: typing.Type[event_manager_.EventT_co],
        /,
        timeout: typing.Union[float, int, None],
        limit: typing.Optional[int] = None,
    ) -> event_stream.Streamer[event_manager_.EventT_co]:
        self._check_if_alive()
        return self._events.stream(event_type, timeout=timeout, limit=limit)

    def subscribe(
        self, event_type: typing.Type[typing.Any], callback: event_manager_.CallbackT[typing.Any]
    ) -> event_manager_.CallbackT[typing.Any]:
        return self._events.subscribe(event_type, callback)

    def unsubscribe(self, event_type: typing.Type[typing.Any], callback: event_manager_.CallbackT[typing.Any]) -> None:
        self._events.unsubscribe(event_type, callback)

    async def wait_for(
        self,
        event_type: typing.Type[event_manager_.EventT_co],
        /,
        timeout: typing.Union[float, int, None],
        predicate: typing.Optional[event_manager_.PredicateT[event_manager_.EventT_co]] = None,
    ) -> event_manager_.EventT_co:
        self._check_if_alive()
        return await self._events.wait_for(event_type, timeout=timeout, predicate=predicate)

    async def update_presence(
        self,
        *,
        status: undefined.UndefinedOr[presences.Status] = undefined.UNDEFINED,
        idle_since: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        activity: undefined.UndefinedNoneOr[presences.Activity] = undefined.UNDEFINED,
        afk: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> None:
        self._check_if_alive()
        self._validate_activity(activity)

        coros = [
            s.update_presence(status=status, activity=activity, idle_since=idle_since, afk=afk)
            for s in self._shards.values()
        ]

        await aio.all_of(*coros)

    # TODO: Update voice state
    # TODO: Request guild chunk

    async def _set_close_flag(self, signame: str, signum: int) -> None:
        # This needs to be a coroutine, as the closing event is not threadsafe, so we have no way to set this
        # from a Unix system call handler if we are running on a thread that isn't the main application thread
        # without getting undefined behaviour. We do however have `asyncio.run_coroutine_threadsafe` which can
        # run a coroutine function on the event loop from a completely different thread, so this is the safest
        # solution.
        _LOGGER.debug("received interrupt %s (%s), will start shutting down shortly", signame, signum)

        await self.close(force=False)

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
            event_manager=self._events,
            event_factory=self._event_factory,
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
        self._shards[new_shard.id] = new_shard

        start = time.monotonic()
        await aio.first_completed(new_shard.start(), self._closing_event.wait())
        end = time.monotonic()

        if new_shard.is_alive:
            _LOGGER.debug("Shard %s started successfully in %.1fms", shard_id, (end - start) * 1_000)
            return new_shard

        raise errors.GatewayError(f"shard {shard_id} shut down immediately when starting")

    @staticmethod
    def _destroy_loop(loop: asyncio.AbstractEventLoop) -> None:
        async def murder(future: asyncio.Future[typing.Any]) -> None:
            # These include _GatheringFuture which must be awaited if the children
            # throw an asyncio.CancelledError, otherwise it will spam logs with warnings
            # about exceptions not being retrieved before GC.
            try:
                _LOGGER.log(ux.TRACE, "killing %s", future)
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
            with contextlib.suppress(NotImplementedError):
                # This seems to raise a NotImplementedError when running with uvloop.
                loop.run_until_complete(loop.shutdown_default_executor())

        _LOGGER.debug("shutting down asyncgens")
        loop.run_until_complete(loop.shutdown_asyncgens())

        _LOGGER.debug("closing event loop")
        loop.close()

    @staticmethod
    def _validate_activity(activity: undefined.UndefinedNoneOr[presences.Activity]) -> None:
        # This seems to cause confusion for a lot of people, so lets add some warnings into the mix.

        if activity is undefined.UNDEFINED or activity is None:
            return

        # If you ever change where this is called from, make sure to check the stacklevels are correct
        # or the code preview in the warning will be wrong...
        if activity.type is presences.ActivityType.CUSTOM:
            warnings.warn(
                "The CUSTOM activity type is not supported by bots at the time of writing, and may therefore not have "
                "any effect if used.",
                category=errors.HikariWarning,
                stacklevel=3,
            )
        elif activity.type is presences.ActivityType.STREAMING and activity.url is None:
            warnings.warn(
                "The STREAMING activity type requires a 'url' parameter pointing to a valid Twitch or YouTube video "
                "URL to be specified on the activity for the presence update to have any effect.",
                category=errors.HikariWarning,
                stacklevel=3,
            )
