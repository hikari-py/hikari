# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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

__all__: typing.Sequence[str] = ("GatewayBot",)

import asyncio
import datetime
import logging
import math
import sys
import types
import typing
import warnings

from hikari import applications
from hikari import errors
from hikari import intents as intents_
from hikari import presences
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari.impl import cache as cache_impl
from hikari.impl import config as config_impl
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import event_factory as event_factory_impl
from hikari.impl import event_manager as event_manager_impl
from hikari.impl import rest as rest_impl
from hikari.impl import shard as shard_impl
from hikari.impl import voice as voice_impl
from hikari.internal import aio
from hikari.internal import data_binding
from hikari.internal import signals
from hikari.internal import time
from hikari.internal import ux

if typing.TYPE_CHECKING:
    import concurrent.futures
    import os

    from hikari import channels
    from hikari import guilds
    from hikari import users as users_
    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import event_factory as event_factory_
    from hikari.api import event_manager as event_manager_
    from hikari.api import rest as rest_
    from hikari.api import shard as gateway_shard
    from hikari.api import voice as voice_
    from hikari.events import base_events

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.bot")


def _validate_activity(activity: undefined.UndefinedNoneOr[presences.Activity]) -> None:
    # This seems to cause confusion for a lot of people, so lets add some warnings into the mix.

    if not activity:
        return

    # If you ever change where this is called from, make sure to check the stacklevels are correct
    # or the code preview in the warning will be wrong...
    if activity.type is presences.ActivityType.STREAMING and activity.url is None:
        warnings.warn(
            "The STREAMING activity type requires a 'url' parameter pointing to a valid Twitch or YouTube video "
            "URL to be specified on the activity for the presence update to have any effect.",
            category=errors.HikariWarning,
            stacklevel=3,
        )


async def _close_resource(name: str, awaitable: typing.Awaitable[typing.Any]) -> None:
    future = asyncio.ensure_future(awaitable)

    try:
        await future
    except Exception as ex:
        asyncio.get_running_loop().call_exception_handler(
            {"message": f"{name} raised an exception during shut down", "future": future, "exception": ex}
        )


class GatewayBot(traits.GatewayBotAware):
    """Basic auto-sharding bot implementation.

    This is the class you will want to use to start, control, and build a bot
    with.

    !!! note
        Settings that control the gateway session are provided to the
        [`hikari.impl.gateway_bot.GatewayBot.run`][] and [`hikari.impl.gateway_bot.GatewayBot.start`][]
        functions in this class. This is done to allow you to contextually
        customise details such as sharding configuration without having to
        re-initialize the entire application each time.

    Parameters
    ----------
    token : str
        The bot token to sign in with.

    Other Parameters
    ----------------
    allow_color : bool
        Whether enable coloured console logs will be enabled on any platform that is a TTY.
        Setting a `"CLICOLOR"` environment variable to any **non `0`** value
        will override this setting.

        Users should consider this an advice to the application on whether it is
        safe to show colours if possible or not. Since some terminals can be
        awkward or not support features in a standard way, the option to
        explicitly disable this is provided. See `force_color` for an
        alternative.
    banner : typing.Optional[str]
        The package to search for a `banner.txt` in.

        Setting this to [`None`][] will disable the banner being shown.
    suppress_optimization_warning : bool
        By default, hikari warns you if you are not running
        your bot using optimizations (`-O` or `-OO`). If this is [`True`][], you won't
        receive these warnings, even if you are not running using optimizations.
    executor : typing.Optional[concurrent.futures.Executor]
        If non-[`None`][], then this executor
        is used instead of the [`concurrent.futures.ThreadPoolExecutor`][] attached
        to the [`asyncio.AbstractEventLoop`][] that the bot will run on. This
        executor is used primarily for file-IO.

        While mainly supporting the [`concurrent.futures.ThreadPoolExecutor`][]
        implementation in the standard lib, Hikari's file handling systems
        should also work with [`concurrent.futures.ProcessPoolExecutor`][], which
        relies on all objects used in IPC to be pickleable. Many third-party
        libraries will not support this fully though, so your mileage may vary
        on using ProcessPoolExecutor implementations with this parameter.
    force_color : bool
        If [`True`][], then this application
        will __force__ colour to be used in console-based output. Specifying a
        `"CLICOLOR_FORCE"` environment variable with a non-`"0"` value will
        override this setting.

        This will take precedence over `allow_color` if both are specified.
    cache_settings : typing.Optional[hikari.impl.config.CacheSettings]
        Optional cache settings. If unspecified, will use the defaults.
    http_settings : typing.Optional[hikari.impl.config.HTTPSettings]
        Optional custom HTTP configuration settings to use. Allows you to
        customise functionality such as whether SSL-verification is enabled,
        what timeouts [`aiohttp`][] should expect to use for requests, and behavior
        regarding HTTP-redirects.
    intents : hikari.intents.Intents
        This allows you
        to change which intents your application will use on the gateway. This
        can be used to control and change the types of events you will receive.
    auto_chunk_members : bool
        If [`False`][], then no member chunks will be requested automatically,
        even if there are reasons to do so.

        We only want to chunk if we both are allowed and need to:

        - Allowed?
            All the following must be true:
                1. `auto_chunk_members` is [`True`][] (the user wants us to).
                2. We have the necessary intents ([`hikari.intents.Intents.GUILD_MEMBERS`][]).
                3. The guild is marked as "large" or we do not have
                   [`hikari.intents.Intents.GUILD_PRESENCES`][] intent Discord will
                   only send every other member objects on the `GUILD_CREATE`
                   payload if presence intents are also declared, so if this
                   isn't the case then we also want to chunk small guilds.

        - Needed?
            One of the following must be true:
                1. We have a cache, and it requires it (it is enabled for
                   [`hikari.api.CacheComponents.MEMBERS`][]), but we are not limited
                   to only our own member (which is included in the `GUILD_CREATE`
                   payload).
                2. The user is waiting for the member chunks (there is an event
                   listener for it).
    logs : typing.Union[None, str, int, typing.Dict[str, typing.Any], os.PathLike]
        The flavour to set the logging to.

        This can be [`None`][] to not enable logging automatically.

        If you pass a [`str`][] or a [`int`][], it is interpreted as
        the global logging level to use, and should match one of `"DEBUG"`,
        `"INFO"`, `"WARNING"`, `"ERROR"` or `"CRITICAL"`.
        The configuration will be set up to use a `colorlog` coloured logger,
        and to use a sane logging format strategy. The output will be written
        to [`sys.stdout`][] using this configuration.

        If you pass a [`dict`][], it is treated as the mapping to pass to
        [`logging.config.dictConfig`][]. If the dict defines any handlers, default
        handlers will not be setup if `incremental` is not specified.

        If you pass a [`str`][] to an existing file or a [`os.PathLike`][], it is
        interpreted as the file to load config from using [`logging.config.fileConfig`][].

        Note that `"TRACE_HIKARI"` is a library-specific logging level
        which is expected to be more verbose than `"DEBUG"`.

    max_rate_limit : float
        The max number of seconds to backoff for when rate limited. Anything
        greater than this will instead raise an error.

        This defaults to five minutes if left to the default value. This is to
        stop potentially indefinitely waiting on an endpoint, which is almost
        never what you want to do if giving a response to a user.

        You can set this to `float("inf")` to disable this check entirely.

        Note that this only applies to the REST API component that communicates
        with Discord, and will not affect sharding or third party HTTP endpoints
        that may be in use.
    max_retries : typing.Optional[int]
        Maximum number of times a request will be retried if
        it fails with a `5xx` status.

        Will default to 3 if set to [`None`][].
    proxy_settings : typing.Optional[hikari.impl.config.ProxySettings]
        Custom proxy settings to use with network-layer logic
        in your application to get through an HTTP-proxy.
    dumps : hikari.internal.data_binding.JSONEncoder
        The JSON encoder this application should use.
    loads : hikari.internal.data_binding.JSONDecoder
        The JSON decoder this application should use.
    rest_url : typing.Optional[str]
        Defaults to the Discord REST API URL if [`None`][]. Can be
        overridden if you are attempting to point to an unofficial endpoint, or
        if you are attempting to mock/stub the Discord API for any reason.
        Generally you do not want to change this.

    Examples
    --------
    Simple logging setup:

    ```py
        hikari.GatewayBot("TOKEN", logs="INFO")  # Registered logging level
        # or
        hikari.GatewayBot("TOKEN", logs=20)  # Logging level as an int
    ```

    File config:

    ```py
        # See https://docs.python.org/3/library/logging.config.html#configuration-file-format for more info
        hikari.GatewayBot("TOKEN", logs="path/to/file.ini")
    ```

    Setting up logging through a dict config:

    ```py
        # See https://docs.python.org/3/library/logging.config.html#dictionary-schema-details for more info
        hikari.GatewayBot(
            "TOKEN",
            logs={
                "version": 1,
                "incremental": True,  # In incremental setups, the default stream handler will be setup
                "loggers": {
                    "hikari.gateway": {"level": "DEBUG"},
                    "hikari.ratelimits": {"level": "TRACE_HIKARI"},
                },
            }
        )
    ```
    """

    shards: typing.Mapping[int, gateway_shard.GatewayShard]
    """Mapping of shards in this application instance.

    Each shard ID is mapped to the corresponding shard instance.

    If the application has not started, it is acceptable to assume the
    result of this call will be an empty mapping.
    """

    __slots__: typing.Sequence[str] = (
        "_cache",
        "_closing_event",
        "_closed_event",
        "_entity_factory",
        "_event_manager",
        "_event_factory",
        "_executor",
        "_http_settings",
        "_intents",
        "_proxy_settings",
        "_rest",
        "_shards",
        "_token",
        "_voice",
        "_loads",
        "_dumps",
        "shards",
    )

    def __init__(
        self,
        token: str,
        *,
        allow_color: bool = True,
        banner: typing.Optional[str] = "hikari",
        suppress_optimization_warning: bool = False,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        force_color: bool = False,
        cache_settings: typing.Optional[config_impl.CacheSettings] = None,
        http_settings: typing.Optional[config_impl.HTTPSettings] = None,
        dumps: data_binding.JSONEncoder = data_binding.default_json_dumps,
        loads: data_binding.JSONDecoder = data_binding.default_json_loads,
        intents: intents_.Intents = intents_.Intents.ALL_UNPRIVILEGED,
        auto_chunk_members: bool = True,
        logs: typing.Union[None, str, int, typing.Dict[str, typing.Any], os.PathLike[str]] = "INFO",
        max_rate_limit: float = 300.0,
        max_retries: int = 3,
        proxy_settings: typing.Optional[config_impl.ProxySettings] = None,
        rest_url: typing.Optional[str] = None,
    ) -> None:
        # Beautification and logging
        ux.init_logging(logs, allow_color, force_color)
        self.print_banner(banner, allow_color, force_color)
        ux.warn_if_not_optimized(suppress_optimization_warning)

        # Settings and state
        self._closed_event: typing.Optional[asyncio.Event] = None
        self._closing_event: typing.Optional[asyncio.Event] = None
        self._executor = executor
        self._http_settings = http_settings if http_settings is not None else config_impl.HTTPSettings()
        self._intents = intents
        self._proxy_settings = proxy_settings if proxy_settings is not None else config_impl.ProxySettings()
        self._token = token.strip()
        self._dumps = dumps
        self._loads = loads

        # Caching
        cache_settings = cache_settings if cache_settings is not None else config_impl.CacheSettings()
        self._cache = cache_impl.CacheImpl(self, cache_settings)

        # Entity creation
        self._entity_factory = entity_factory_impl.EntityFactoryImpl(self)

        # Event creation
        self._event_factory = event_factory_impl.EventFactoryImpl(self)

        # Event handling
        self._event_manager = event_manager_impl.EventManagerImpl(
            self._entity_factory,
            self._event_factory,
            self._intents,
            auto_chunk_members=auto_chunk_members,
            cache=self._cache,
        )

        # Voice subsystem
        self._voice = voice_impl.VoiceComponentImpl(self)

        # RESTful API.
        self._rest = rest_impl.RESTClientImpl(
            cache=self._cache,
            entity_factory=self._entity_factory,
            executor=self._executor,
            http_settings=self._http_settings,
            max_rate_limit=max_rate_limit,
            proxy_settings=self._proxy_settings,
            dumps=dumps,
            loads=loads,
            rest_url=rest_url,
            max_retries=max_retries,
            token=token,
            token_type=applications.TokenType.BOT,
        )

        # We populate these on startup instead, as we need to possibly make some
        # HTTP requests to determine what to put in this mapping.
        self._shards: typing.Dict[int, gateway_shard.GatewayShard] = {}
        self.shards = types.MappingProxyType(self._shards)

    @property
    def cache(self) -> cache_.Cache:
        return self._cache

    @property
    def event_manager(self) -> event_manager_.EventManager:
        return self._event_manager

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
    def http_settings(self) -> config_impl.HTTPSettings:
        return self._http_settings

    @property
    def intents(self) -> intents_.Intents:
        return self._intents

    @property
    def proxy_settings(self) -> config_impl.ProxySettings:
        return self._proxy_settings

    @property
    def shard_count(self) -> int:
        return next(iter(self._shards.values())).shard_count if self._shards else 0

    @property
    def voice(self) -> voice_.VoiceComponent:
        return self._voice

    @property
    def rest(self) -> rest_.RESTClient:
        return self._rest

    @property
    def is_alive(self) -> bool:
        return self._closed_event is not None

    def _check_if_alive(self) -> None:
        if not self._closed_event:
            raise errors.ComponentStateConflictError("bot is not running so it cannot be interacted with")

    def get_me(self) -> typing.Optional[users_.OwnUser]:
        return self._cache.get_me()

    async def close(self) -> None:
        if not self._closed_event or not self._closing_event:
            raise errors.ComponentStateConflictError("Cannot close an inactive bot")

        if self._closing_event.is_set():
            await self.join()
            return

        _LOGGER.info("bot requested to shut down")
        self._closing_event.set()

        await self._event_manager.dispatch(self._event_factory.deserialize_stopping_event())
        _LOGGER.log(ux.TRACE, "StoppingEvent dispatch completed, now beginning termination")

        await _close_resource("voice handler", self._voice.close())

        shards = tuple(_close_resource(f"shard {s.id}", s.close()) for s in self._shards.values() if s.is_alive)

        for coro in asyncio.as_completed(shards):
            await coro

        await _close_resource("rest", self._rest.close())

        # Clear out cache and shard map
        self._cache.clear()
        self._shards.clear()

        await self._event_manager.dispatch(self._event_factory.deserialize_stopped_event())

        self._closed_event.set()
        self._closed_event = None
        self._closing_event = None

        _LOGGER.info("bot shut down successfully")

    def dispatch(self, event: base_events.Event) -> asyncio.Future[typing.Any]:
        """Dispatch an event.

        Parameters
        ----------
        event : hikari.events.base_events.Event
            The event to dispatch.

        Examples
        --------
        We can dispatch custom events by first defining a class that
        derives from [`hikari.events.base_events.Event`][].

        ```py
            import attrs

            from hikari.traits import RESTAware
            from hikari.events.base_events import Event
            from hikari.users import User
            from hikari.snowflakes import Snowflake

            @attrs.define()
            class EveryoneMentionedEvent(Event):
                app: RESTAware = attrs.field()

                author: User = attrs.field()
                '''The user who mentioned everyone.'''

                content: str = attrs.field()
                '''The message that was sent.'''

                message_id: Snowflake = attrs.field()
                '''The message ID.'''

                channel_id: Snowflake = attrs.field()
                '''The channel ID.'''
        ```

        We can then dispatch our event as we see fit.

        ```py
            from hikari.events.messages import MessageCreateEvent

            @bot.listen(MessageCreateEvent)
            async def on_message(event):
                if "@everyone" in event.content or "@here" in event.content:
                    event = EveryoneMentionedEvent(
                        author=event.author,
                        content=event.content,
                        message_id=event.id,
                        channel_id=event.channel_id,
                    )

                    bot.dispatch(event)
        ```

        This event can be listened to elsewhere by subscribing to it with
        [`hikari.impl.event_manager_base.EventManagerBase.subscribe`][].

        ```py
            @bot.listen(EveryoneMentionedEvent)
            async def on_everyone_mentioned(event):
                print(event.user, "just pinged everyone in", event.channel_id)
        ```

        Returns
        -------
        asyncio.Future[typing.Any]
            A future that can be optionally awaited. If awaited, the future
            will complete once all corresponding event listeners have been
            invoked. If not awaited, this will schedule the dispatch of the
            events in the background for later.

        See Also
        --------
        Listen : [`hikari.impl.gateway_bot.GatewayBot.listen`][].
        Stream : [`hikari.impl.gateway_bot.GatewayBot.stream`][].
        Subscribe : [`hikari.impl.gateway_bot.GatewayBot.subscribe`][].
        Unsubscribe : [`hikari.impl.gateway_bot.GatewayBot.unsubscribe`][].
        Wait_for : [`hikari.impl.gateway_bot.GatewayBot.wait_for`][].
        """
        return self._event_manager.dispatch(event)

    def get_listeners(
        self, event_type: typing.Type[base_events.EventT], /, *, polymorphic: bool = True
    ) -> typing.Collection[event_manager_.CallbackT[base_events.EventT]]:
        """Get the listeners for a given event type, if there are any.

        Parameters
        ----------
        event_type : typing.Type[EventT]
            The event type to look for.
            `EventT` must be a subclass of [`hikari.events.base_events.Event`][].
        polymorphic : bool
            If [`True`][], this will also return the listeners of the
            subclasses of the given event type. If [`False`][], then
            only listeners for this class specifically are returned.

        Returns
        -------
        typing.Collection[typing.Callable[[EventT], typing.Coroutine[typing.Any, typing.Any, None]]]
            A copy of the collection of listeners for the event. Will return
            an empty collection if nothing is registered.
        """
        return self._event_manager.get_listeners(event_type, polymorphic=polymorphic)

    async def join(self) -> None:
        if not self._closed_event:
            raise errors.ComponentStateConflictError("Cannot wait for an inactive bot to join")

        await aio.first_completed(self._closed_event.wait(), *(s.join() for s in self._shards.values()))

    def listen(
        self, *event_types: typing.Type[base_events.EventT]
    ) -> typing.Callable[[event_manager_.CallbackT[base_events.EventT]], event_manager_.CallbackT[base_events.EventT]]:
        """Generate a decorator to subscribe a callback to an event type.

        This is a second-order decorator.

        Parameters
        ----------
        *event_types : typing.Optional[typing.Type[EventT]]
            The event types to subscribe to. The implementation may allow this
            to be undefined. If this is the case, the event type will be inferred
            instead from the type hints on the function signature.

            `EventT` must be a subclass of [`hikari.events.base_events.Event`][].

        Returns
        -------
        typing.Callable[[EventT], EventT]
            A decorator for a coroutine function that passes it to
            [`hikari.impl.event_manager.EventManagerImpl.subscribe`][] before returning the function
            reference.

        See Also
        --------
        Dispatch : [`hikari.impl.gateway_bot.GatewayBot.dispatch`][].
        Stream : [`hikari.impl.gateway_bot.GatewayBot.stream`][].
        Subscribe : [`hikari.impl.gateway_bot.GatewayBot.subscribe`][].
        Unsubscribe : [`hikari.impl.gateway_bot.GatewayBot.unsubscribe`][].
        Wait_for : [`hikari.impl.gateway_bot.GatewayBot.wait_for`][].
        """
        return self._event_manager.listen(*event_types)

    @staticmethod
    def print_banner(
        banner: typing.Optional[str],
        allow_color: bool,
        force_color: bool,
        extra_args: typing.Optional[typing.Dict[str, str]] = None,
    ) -> None:
        """Print the banner.

        This allows library vendors to override this behaviour, or choose to
        inject their own "branding" on top of what hikari provides by default.

        Normal users should not need to invoke this function, and can simply
        change the `banner` argument passed to the constructor to manipulate
        what is displayed.

        Parameters
        ----------
        banner : typing.Optional[str]
            The package to find a `banner.txt` in.
        allow_color : bool
            A flag that allows advising whether to allow color if supported or
            not. Can be overridden by setting a `CLICOLOR` environment
            variable to a non-`"0"` string.
        force_color : bool
            A flag that allows forcing color to always be output, even if the
            terminal device may not support it. Setting the `CLICOLOR_FORCE`
            environment variable to a non-`"0"` string will override this.

            This will take precedence over `allow_color` if both are specified.
        extra_args : typing.Optional[typing.Dict[str, str]]
            If provided, extra $-substitutions to use when printing the banner.
            Default substitutions can not be overwritten.

        Raises
        ------
        ValueError
            If `extra_args` contains a default $-substitution.
        """
        ux.print_banner(banner, allow_color, force_color, extra_args=extra_args)

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
        enable_signal_handlers: typing.Optional[bool] = None,
        idle_since: typing.Optional[datetime.datetime] = None,
        ignore_session_start_limit: bool = False,
        large_threshold: int = 250,
        propagate_interrupts: bool = False,
        status: presences.Status = presences.Status.ONLINE,
        shard_ids: typing.Optional[typing.Sequence[int]] = None,
        shard_count: typing.Optional[int] = None,
    ) -> None:
        """Start the application and block until it's finished running.

        Other Parameters
        ----------------
        activity : typing.Optional[hikari.presences.Activity]
            The initial activity to display in the bot user presence, or
            [`None`][] (default) to not show any.
        afk : bool
            The initial AFK state to display in the bot user presence, or
            [`False`][] (default) to not show any.
        asyncio_debug : bool
            If [`True`][], then debugging is enabled for the asyncio event
            loop in use.
        check_for_updates : bool
            If [`True`][], will check for newer versions of hikari on PyPI
            and notify if available.
        close_passed_executor : bool
            If [`True`][], any custom [`concurrent.futures.Executor`][] passed
            to the constructor will be shut down when the application
            terminates. This does not affect the default executor associated
            with the event loop, and will not do anything if you do not
            provide a custom executor to the constructor.
        close_loop : bool
            If [`True`][], then once the bot enters a state where all components
            have shut down permanently during application shut down, then
            all asyncgens and background tasks will be destroyed, and the
            event loop will be shut down.

            This will wait until all hikari-owned [`aiohttp`][] connectors have
            had time to attempt to shut down correctly (around 250ms), and on
            Python 3.9 and newer, will also shut down the default event loop
            executor too.
        coroutine_tracking_depth : typing.Optional[int]
            If an integer value and supported by
            the interpreter, then this many nested coroutine calls will be
            tracked with their call origin state. This allows you to determine
            where non-awaited coroutines may originate from, but generally you
            do not want to leave this enabled for performance reasons.
        enable_signal_handlers : typing.Optional[bool]
            Defaults to [`True`][] if this is called in the main thread.

            If on a non-Windows OS with builtin support for kernel-level
            POSIX signals, then setting this to [`True`][] will allow
            treating keyboard interrupts and other OS signals to safely shut
            down the application as calls to shut down the application properly
            rather than just killing the process in a dirty state immediately.
            You should leave this enabled unless you plan to implement your own
            signal handling yourself.
        idle_since : typing.Optional[datetime.datetime]
            The [`datetime.datetime`][] the user should be marked as being idle
            since, or [`None`][] to not show this.
        ignore_session_start_limit : bool
            If [`False`][], then attempting to start more sessions than
            you are allowed in a 24 hour window will throw a [`RuntimeError`][]
            rather than going ahead and hitting the IDENTIFY limit, which
            may result in your token being reset. Setting to [`True`][]
            disables this behavior.
        large_threshold : int
            Threshold for members in a guild before it is treated as being
            "large" and no longer sending member details in the [GUILD CREATE][]
            event.
        propagate_interrupts : bool
            If [`True`][], then any internal [`hikari.errors.HikariInterrupt`][]
            that is raises as a result of catching an OS level signal will
            result in the exception being rethrown once the application has
            closed. This can allow you to use hikari signal handlers and
            still be able to determine what kind of interrupt the
            application received after it closes. When [`False`][], nothing
            is raised and the call will terminate cleanly and silently
            where possible instead.
        shard_ids : typing.Optional[typing.Sequence[int]]
            The shard IDs to create shards for. If not [`None`][], then
            a non-[`None`][] `shard_count` must ALSO be provided.

            Defaults to [`None`][], which means the Discord-recommended count
            is used for your application instead.

            Note that the sequence will be de-duplicated.
        shard_count : typing.Optional[int]
            The number of shards to use in the entire distributed application.

            Defaults to [`None`][] which results in the count being
            determined dynamically on startup.
        status : hikari.presences.Status
            The initial status to show for the user presence on startup.

        Raises
        ------
        hikari.errors.ComponentStateConflictError
            If bot is already running.
        TypeError
            If `shard_ids` is passed without `shard_count`.
        """
        if self._closed_event:
            raise errors.ComponentStateConflictError("bot is already running")

        if shard_ids is not None and shard_count is None:
            raise TypeError("'shard_ids' must be passed with 'shard_count'")

        loop = aio.get_or_make_loop()

        if asyncio_debug:
            loop.set_debug(True)

        if coroutine_tracking_depth is not None:
            try:
                # Provisionally defined in CPython, may be removed without notice.
                sys.set_coroutine_origin_tracking_depth(coroutine_tracking_depth)
            except AttributeError:
                _LOGGER.log(ux.TRACE, "cannot set coroutine tracking depth for sys, no functionality exists for this")

        with signals.handle_interrupts(
            enabled=enable_signal_handlers, loop=loop, propagate_interrupts=propagate_interrupts
        ):
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
                    if self._closing_event:
                        if self._closing_event.is_set():
                            loop.run_until_complete(self._closing_event.wait())
                        else:
                            loop.run_until_complete(self.close())

                    if close_passed_executor and self._executor is not None:
                        _LOGGER.debug("shutting down executor %s", self._executor)
                        self._executor.shutdown(wait=True)
                        self._executor = None

                    if close_loop:
                        aio.destroy_loop(loop, _LOGGER)

                    _LOGGER.info("successfully terminated")

                except errors.HikariInterrupt:
                    _LOGGER.warning("forcefully terminated")
                    raise

    async def start(
        self,
        *,
        activity: typing.Optional[presences.Activity] = None,
        afk: bool = False,
        check_for_updates: bool = True,
        idle_since: typing.Optional[datetime.datetime] = None,
        ignore_session_start_limit: bool = False,
        large_threshold: int = 250,
        shard_ids: typing.Optional[typing.Sequence[int]] = None,
        shard_count: typing.Optional[int] = None,
        status: presences.Status = presences.Status.ONLINE,
    ) -> None:
        """Start the bot, wait for all shards to become ready, and then return.

        Other Parameters
        ----------------
        activity : typing.Optional[hikari.presences.Activity]
            The initial activity to display in the bot user presence, or
            [`None`][] (default) to not show any.
        afk : bool
            The initial AFK state to display in the bot user presence, or
            [`False`][] (default) to not show any.
        check_for_updates : bool
            If [`True`][], will check for
            newer versions of `hikari` on PyPI and notify if available.
        idle_since : typing.Optional[datetime.datetime]
            The [`datetime.datetime`][] the user should be marked as being idle
            since, or [`None`][] (default) to not show this.
        ignore_session_start_limit : bool
            If [`False`][], then attempting to start more sessions than you
            are allowed in a 24 hour window will throw a [`RuntimeError`][]
            rather than going ahead and hitting the IDENTIFY limit,
            which may result in your token being reset. Setting to [`True`][]
            disables this behavior.
        large_threshold : int
            Threshold for members in a guild before it is treated as being
            "large" and no longer sending member details in the `GUILD CREATE`
            event.
        shard_ids : typing.Optional[typing.Sequence[int]]
            The shard IDs to create shards for. If not [`None`][], then
            a non-[`None`][] `shard_count` must ALSO be provided. Defaults to
            [`None`][], which means the Discord-recommended count is used
            for your application instead.

            Note that the sequence will be de-duplicated.
        shard_count : typing.Optional[int]
            The number of shards to use in the entire distributed application.

            Defaults to [`None`][] which results in the count being
            determined dynamically on startup.
        status : hikari.presences.Status
            The initial status to show for the user presence on startup.

        Raises
        ------
        TypeError
            If `shard_ids` is passed without `shard_count`.
        hikari.errors.ComponentStateConflictError
            If bot is already running.
        """
        if self._closed_event:
            raise errors.ComponentStateConflictError("bot is already running")

        if shard_ids is not None and shard_count is None:
            raise TypeError("'shard_ids' must be passed with 'shard_count'")

        _validate_activity(activity)

        start_time = time.monotonic()
        self._closed_event = asyncio.Event()
        self._closing_event = asyncio.Event()

        if check_for_updates:
            asyncio.create_task(
                ux.check_for_updates(self._http_settings, self._proxy_settings), name="check for package updates"
            )

        self._rest.start()
        self._voice.start()

        await self._event_manager.dispatch(self._event_factory.deserialize_starting_event())
        requirements = await self._rest.fetch_gateway_bot_info()

        if shard_count is None:
            shard_count = requirements.shard_count
        if shard_ids is None:
            shard_ids = tuple(range(shard_count))
        else:
            shard_ids = tuple(dict.fromkeys(shard_ids))

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
            raise RuntimeError("Attempted to start more sessions than were allowed in the given time-window")

        _LOGGER.info(
            "you can start %s session%s before the next window which starts at %s; planning to start %s session%s... ",
            requirements.session_start_limit.remaining,
            "s" if requirements.session_start_limit.remaining != 1 else "",
            requirements.session_start_limit.reset_at,
            len(shard_ids),
            "s" if len(shard_ids) != 1 else "",
        )

        max_concurrency = requirements.session_start_limit.max_concurrency
        while shard_ids:
            window = shard_ids[:max_concurrency]
            shard_ids = shard_ids[max_concurrency:]

            if self._shards:
                _LOGGER.info("the next startup window is in 5 seconds, please wait...")

                try:
                    await aio.first_completed(
                        self._closing_event.wait(), *(shard.join() for shard in self._shards.values()), timeout=5
                    )

                    if self._closing_event.is_set():
                        return

                    _LOGGER.critical("one or more shards closed while starting; shutting down")
                    raise RuntimeError("One or more shards closed while starting")
                except asyncio.TimeoutError:
                    # new window starts.
                    pass

            gather = asyncio.gather(
                *(
                    self._start_one_shard(
                        activity=activity,
                        afk=afk,
                        idle_since=idle_since,
                        status=status,
                        large_threshold=large_threshold,
                        shard_id=shard_id,
                        shard_count=shard_count,
                        url=requirements.url,
                    )
                    for shard_id in window
                )
            )

            await aio.first_completed(self._closing_event.wait(), gather)

        await self._event_manager.dispatch(self._event_factory.deserialize_started_event())

        _LOGGER.info("started successfully in approx %.2f seconds", time.monotonic() - start_time)

    def stream(
        self,
        event_type: typing.Type[base_events.EventT],
        /,
        timeout: typing.Union[float, int, None],
        limit: typing.Optional[int] = None,
    ) -> event_manager_.EventStream[base_events.EventT]:
        """Return a stream iterator for the given event and sub-events.

        !!! warning
            If you use `stream.open()` to start the stream then you must
            also close it with `stream.close()` otherwise it may queue
            events in memory indefinitely.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base_events.Event]
            The event type to listen for. This will listen for subclasses of
            this type additionally.
        timeout : typing.Optional[int, float]
            How long this streamer should wait for the next event before
            ending the iteration. If [`None`][] then this will continue
            until explicitly broken from.
        limit : typing.Optional[int]
            The limit for how many events this should queue at one time before
            dropping extra incoming events, leave this as [`None`][] for
            the cache size to be unlimited.

        Returns
        -------
        EventStream[hikari.events.base_events.Event]
            The async iterator to handle streamed events. This must be started
            with `with stream:` or `stream.open()` before
            asynchronously iterating over it.

        Examples
        --------
        ```py
            with bot.stream(events.ReactionAddEvent, timeout=30).filter(("message_id", message.id)) as stream:
                async for user_id in stream.map("user_id").limit(50):
                    ...
        ```

        or using `open()` and `close()`

        ```py
            stream = bot.stream(events.ReactionAddEvent, timeout=30).filter(("message_id", message.id))
            stream.open()

            async for user_id in stream.map("user_id").limit(50)
                ...

            stream.close()
        ```

        See Also
        --------
        Dispatch : [`hikari.impl.gateway_bot.GatewayBot.dispatch`][].
        Listen : [`hikari.impl.gateway_bot.GatewayBot.listen`][].
        Subscribe : [`hikari.impl.gateway_bot.GatewayBot.subscribe`][].
        Unsubscribe : [`hikari.impl.gateway_bot.GatewayBot.unsubscribe`][].
        Wait_for : [`hikari.impl.gateway_bot.GatewayBot.wait_for`][].
        """
        self._check_if_alive()
        return self._event_manager.stream(event_type, timeout=timeout, limit=limit)

    # Yes, this is not generic. The reason for this is MyPy complains about
    # using ABCs that are not concrete in generic types passed to functions.
    # For the sake of UX, I will check this at runtime instead and let the
    # user use a static type checker.
    def subscribe(self, event_type: typing.Type[typing.Any], callback: event_manager_.CallbackT[typing.Any]) -> None:
        """Subscribe a given callback to a given event type.

        Parameters
        ----------
        event_type : typing.Type[T]
            The event type to listen for. This will also listen for any
            subclasses of the given type.
            `T` must be a subclass of [`hikari.events.base_events.Event`][].
        callback
            Must be a coroutine function to invoke. This should
            consume an instance of the given event, or an instance of a valid
            subclass if one exists. Any result is discarded.

        Examples
        --------
        The following demonstrates subscribing a callback to message creation
        events.

        ```py
            from hikari.events.messages import MessageCreateEvent

            async def on_message(event):
                ...

            bot.subscribe(MessageCreateEvent, on_message)
        ```

        See Also
        --------
        Dispatch : [`hikari.impl.gateway_bot.GatewayBot.dispatch`][].
        Listen : [`hikari.impl.gateway_bot.GatewayBot.listen`][].
        Stream : [`hikari.impl.gateway_bot.GatewayBot.stream`][].
        Unsubscribe : [`hikari.impl.gateway_bot.GatewayBot.unsubscribe`][].
        Wait_for : [`hikari.impl.gateway_bot.GatewayBot.wait_for`][].
        """
        self._event_manager.subscribe(event_type, callback)

    # Yes, this is not generic. The reason for this is MyPy complains about
    # using ABCs that are not concrete in generic types passed to functions.
    # For the sake of UX, I will check this at runtime instead and let the
    # user use a static type checker.
    def unsubscribe(self, event_type: typing.Type[typing.Any], callback: event_manager_.CallbackT[typing.Any]) -> None:
        """Unsubscribe a given callback from a given event type, if present.

        Parameters
        ----------
        event_type : typing.Type[T]
            The event type to unsubscribe from. This must be the same exact
            type as was originally subscribed with to be removed correctly.
            `T` must derive from [`hikari.events.base_events.Event`][].
        callback
            The callback to unsubscribe.

        Examples
        --------
        The following demonstrates unsubscribing a callback from a message
        creation event.

        ```py
            from hikari.events.messages import MessageCreateEvent

            async def on_message(event):
                ...

            bot.unsubscribe(MessageCreateEvent, on_message)
        ```

        See Also
        --------
        Dispatch : [`hikari.impl.gateway_bot.GatewayBot.dispatch`][].
        Listen : [`hikari.impl.gateway_bot.GatewayBot.listen`][].
        Stream : [`hikari.impl.gateway_bot.GatewayBot.stream`][].
        Subscribe : [`hikari.impl.gateway_bot.GatewayBot.subscribe`][].
        Wait_for : [`hikari.impl.gateway_bot.GatewayBot.wait_for`][].
        """
        self._event_manager.unsubscribe(event_type, callback)

    async def wait_for(
        self,
        event_type: typing.Type[base_events.EventT],
        /,
        timeout: typing.Union[float, int, None],
        predicate: typing.Optional[event_manager_.PredicateT[base_events.EventT]] = None,
    ) -> base_events.EventT:
        """Wait for a given event to occur once, then return the event.

        !!! warning
            Async predicates are not supported.

        Parameters
        ----------
        event_type : typing.Type[hikari.events.base_events.Event]
            The event type to listen for. This will listen for subclasses of
            this type additionally.
        predicate
            A function taking the event as the single parameter.
            This should return [`True`][] if the event is one you want to
            return, or [`False`][] if the event should not be returned.
            If left as [`None`][] (the default), then the first matching event type
            that the bot receives (or any subtype) will be the one returned.
        timeout : typing.Union[float, int, None]
            The amount of time to wait before raising an [`asyncio.TimeoutError`][]
            and giving up instead. This is measured in seconds. If
            [`None`][], then no timeout will be waited for (no timeout can
            result in "leaking" of coroutines that never complete if called in
            an uncontrolled way, so is not recommended).

        Returns
        -------
        hikari.events.base_events.Event
            The event that was provided.

        Raises
        ------
        asyncio.TimeoutError
            If the timeout is not [`None`][] and is reached before an
            event is received that the predicate returns [`True`][] for.

        See Also
        --------
        Dispatch : [`hikari.impl.gateway_bot.GatewayBot.dispatch`][].
        Listen : [`hikari.impl.gateway_bot.GatewayBot.listen`][].
        Stream : [`hikari.impl.gateway_bot.GatewayBot.stream`][].
        Subscribe : [`hikari.impl.gateway_bot.GatewayBot.subscribe`][].
        Unsubscribe : [`hikari.impl.gateway_bot.GatewayBot.unsubscribe`][].
        """
        self._check_if_alive()
        return await self._event_manager.wait_for(event_type, timeout=timeout, predicate=predicate)

    def _get_shard(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> gateway_shard.GatewayShard:
        guild = snowflakes.Snowflake(guild)
        if shard := self._shards.get(snowflakes.calculate_shard_id(self.shard_count, guild)):
            return shard

        raise RuntimeError(f"Guild {guild} isn't covered by any of the shards in this client")

    async def update_presence(
        self,
        *,
        status: undefined.UndefinedOr[presences.Status] = undefined.UNDEFINED,
        idle_since: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        activity: undefined.UndefinedNoneOr[presences.Activity] = undefined.UNDEFINED,
        afk: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> None:
        self._check_if_alive()
        _validate_activity(activity)

        coros = [
            s.update_presence(status=status, activity=activity, idle_since=idle_since, afk=afk)
            for s in self._shards.values()
        ]

        await aio.all_of(*coros)

    async def update_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: typing.Optional[snowflakes.SnowflakeishOr[channels.GuildVoiceChannel]],
        *,
        self_mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        self_deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> None:
        self._check_if_alive()
        shard = self._get_shard(guild)
        await shard.update_voice_state(guild=guild, channel=channel, self_mute=self_mute, self_deaf=self_deaf)

    async def request_guild_members(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        query: str = "",
        limit: int = 0,
        users: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[users_.User]] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        self._check_if_alive()
        shard = self._get_shard(guild)
        await shard.request_guild_members(
            guild=guild, include_presences=include_presences, query=query, limit=limit, users=users, nonce=nonce
        )

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
    ) -> None:
        new_shard = shard_impl.GatewayShardImpl(
            http_settings=self._http_settings,
            proxy_settings=self._proxy_settings,
            event_manager=self._event_manager,
            event_factory=self._event_factory,
            intents=self._intents,
            dumps=self._dumps,
            loads=self._loads,
            initial_activity=activity,
            initial_is_afk=afk,
            initial_idle_since=idle_since,
            initial_status=status,
            large_threshold=large_threshold,
            shard_id=shard_id,
            shard_count=shard_count,
            token=self._token,
            url=url,
        )
        try:
            start = time.monotonic()
            await new_shard.start()
            end = time.monotonic()

            if new_shard.is_alive:
                _LOGGER.debug("shard %s started successfully in %.1fms", shard_id, (end - start) * 1_000)
                self._shards[shard_id] = new_shard
                return

            raise RuntimeError(f"shard {shard_id} shut down immediately when starting")

        except Exception:
            if new_shard.is_alive:
                await new_shard.close()

            raise
