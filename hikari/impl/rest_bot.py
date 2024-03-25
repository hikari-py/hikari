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
"""Standard implementations of a Interaction based REST-only bot."""
from __future__ import annotations

__all__: typing.Sequence[str] = ("RESTBot",)

import asyncio
import logging
import sys
import typing

from hikari import applications
from hikari import errors
from hikari import traits
from hikari.api import interaction_server as interaction_server_
from hikari.impl import config as config_impl
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import interaction_server as interaction_server_impl
from hikari.impl import rest as rest_impl
from hikari.internal import aio
from hikari.internal import signals
from hikari.internal import ux

if typing.TYPE_CHECKING:
    import concurrent.futures
    import os
    import socket as socket_
    import ssl

    from hikari.api import entity_factory as entity_factory_api
    from hikari.api import rest as rest_api
    from hikari.api import special_endpoints
    from hikari.interactions import base_interactions
    from hikari.interactions import command_interactions
    from hikari.interactions import component_interactions
    from hikari.interactions import modal_interactions

    _InteractionT_co = typing.TypeVar("_InteractionT_co", bound=base_interactions.PartialInteraction, covariant=True)
    _MessageResponseBuilderT = typing.Union[
        special_endpoints.InteractionDeferredBuilder, special_endpoints.InteractionMessageBuilder
    ]
    _ModalOrMessageResponseBuilderT = typing.Union[_MessageResponseBuilderT, special_endpoints.InteractionModalBuilder]

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.rest_bot")


class RESTBot(traits.RESTBotAware, interaction_server_.InteractionServer):
    """Basic implementation of an interaction based REST-only bot.

    Parameters
    ----------
    token : typing.Union[str, hikari.api.rest.TokenStrategy]
        The bot or bearer token.
    token_type : typing.Union[str, hikari.applications.TokenType, None]
        The type of token in use. This should only be passed when [`str`][]
        is passed for `token`, can be `"Bot"` or `"Bearer"` and defaults
        to `"Bot".

        This should be left as [`None`][] when [`hikari.api.rest.TokenStrategy`][]
        is passed for [`token`][].

    Other Parameters
    ----------------
    allow_color : bool
        Whether to enable coloured console logs on any platform that is a TTY.
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
        By default, Hikari warns you if you are not running your bot using
        optimizations (`-O` or `-OO`). If this is [`True`][], you won't receive
        these warnings, even if you are not running using optimizations.
    executor : typing.Optional[concurrent.futures.Executor]
        If non-[`None`][], then this executor is used instead of the
        [`concurrent.futures.ThreadPoolExecutor`][] attached to the
        [`asyncio.AbstractEventLoop`][] that the bot will run on. This
        executor is used primarily for file-IO.

        While mainly supporting the [`concurrent.futures.ThreadPoolExecutor`][]
        implementation in the standard lib, hikari's file handling systems
        should also work with [`concurrent.futures.ProcessPoolExecutor`][], which
        relies on all objects used in IPC to be pickleable. Many third-party
        libraries will not support this fully though, so your mileage may vary
        on using ProcessPoolExecutor implementations with this parameter.
    force_color : bool
        If [`True`][], then this application will __force__ colour to be
        used in console-based output. Specifying a `"CLICOLOR_FORCE"`
        environment variable with a non-`"0"` value will
        override this setting.

        This will take precedence over `allow_color` if both are specified.
    http_settings : typing.Optional[hikari.config.HTTPSettings]
        Optional custom HTTP configuration settings to use. Allows you to
        customise functionality such as whether SSL-verification is enabled,
        what timeouts [`aiohttp`][] should expect to use for requests, and behavior
        regarding HTTP-redirects.
    logs : typing.Union[None, int, str, typing.Dict[str, typing.Any], os.PathLike[str]]
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

        Defaults to 3 if set to [`None`][].
    proxy_settings : typing.Optional[hikari.impl.config.ProxySettings]
        Custom proxy settings to use with network-layer logic
        in your application to get through an HTTP-proxy.
    public_key : typing.Union[str, bytes, None]
        The public key to use to verify received interaction requests.
        This may be a hex encoded [`str`][] or the raw [`bytes`][].
        If left as [`None`][] then the client will try to work this value
        out based on [`token`][].
    rest_url : typing.Optional[str]
        Defaults to the Discord REST API URL if [`None`][]. Can be
        overridden if you are attempting to point to an unofficial endpoint, or
        if you are attempting to mock/stub the Discord API for any reason.
        Generally you do not want to change this.

    Raises
    ------
    ValueError
        * If `token_type` is provided when a token strategy is passed for `token`.
        * if `token_type` is left as [`None`][] when a string is passed for `token`.

    Examples
    --------
    Simple logging setup:

    ```py
        hikari.RESTBot("TOKEN", logs="INFO")  # Registered logging level
        # or
        hikari.RESTBot("TOKEN", logs=20)  # Logging level as an int
    ```

    File config:

    ```py
        # See https://docs.python.org/3/library/logging.config.html#configuration-file-format for more info
        hikari.RESTBot("TOKEN", logs="path/to/file.ini")
    ```

    Setting up logging through a dict config:

    ```py
        # See https://docs.python.org/3/library/logging.config.html#dictionary-schema-details for more info
        hikari.RESTBot(
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

    __slots__: typing.Sequence[str] = (
        "_close_event",
        "_entity_factory",
        "_executor",
        "_http_settings",
        "_is_closing",
        "_on_shutdown",
        "_on_startup",
        "_proxy_settings",
        "_rest",
        "_server",
    )

    @typing.overload
    def __init__(
        self,
        token: rest_api.TokenStrategy,
        *,
        public_key: typing.Union[bytes, str, None] = None,
        allow_color: bool = True,
        banner: typing.Optional[str] = "hikari",
        suppress_optimization_warning: bool = False,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        force_color: bool = False,
        http_settings: typing.Optional[config_impl.HTTPSettings] = None,
        logs: typing.Union[None, str, int, typing.Dict[str, typing.Any], os.PathLike[str]] = "INFO",
        max_rate_limit: float = 300.0,
        max_retries: int = 3,
        proxy_settings: typing.Optional[config_impl.ProxySettings] = None,
        rest_url: typing.Optional[str] = None,
    ) -> None: ...

    @typing.overload
    def __init__(
        self,
        token: str,
        token_type: typing.Union[str, applications.TokenType] = applications.TokenType.BOT,
        public_key: typing.Union[bytes, str, None] = None,
        *,
        allow_color: bool = True,
        banner: typing.Optional[str] = "hikari",
        suppress_optimization_warning: bool = False,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        force_color: bool = False,
        http_settings: typing.Optional[config_impl.HTTPSettings] = None,
        logs: typing.Union[None, str, int, typing.Dict[str, typing.Any], os.PathLike[str]] = "INFO",
        max_rate_limit: float = 300.0,
        max_retries: int = 3,
        proxy_settings: typing.Optional[config_impl.ProxySettings] = None,
        rest_url: typing.Optional[str] = None,
    ) -> None: ...

    def __init__(
        self,
        token: typing.Union[str, rest_api.TokenStrategy],
        token_type: typing.Union[applications.TokenType, str, None] = None,
        public_key: typing.Union[bytes, str, None] = None,
        *,
        allow_color: bool = True,
        banner: typing.Optional[str] = "hikari",
        suppress_optimization_warning: bool = False,
        executor: typing.Optional[concurrent.futures.Executor] = None,
        force_color: bool = False,
        http_settings: typing.Optional[config_impl.HTTPSettings] = None,
        logs: typing.Union[None, str, int, typing.Dict[str, typing.Any], os.PathLike[str]] = "INFO",
        max_rate_limit: float = 300.0,
        max_retries: int = 3,
        proxy_settings: typing.Optional[config_impl.ProxySettings] = None,
        rest_url: typing.Optional[str] = None,
    ) -> None:
        if isinstance(public_key, str):
            public_key = bytes.fromhex(public_key)

        if isinstance(token, str):
            token = token.strip()

            if token_type is None:
                token_type = applications.TokenType.BOT

        # Beautification and logging
        ux.init_logging(logs, allow_color, force_color)
        self.print_banner(banner, allow_color, force_color)
        ux.warn_if_not_optimized(suppress_optimization_warning)

        # Settings and state
        self._close_event: typing.Optional[asyncio.Event] = None
        self._executor = executor
        self._http_settings = http_settings if http_settings is not None else config_impl.HTTPSettings()
        self._is_closing = False
        self._on_shutdown: typing.List[typing.Callable[[RESTBot], typing.Coroutine[typing.Any, typing.Any, None]]] = []
        self._on_startup: typing.List[typing.Callable[[RESTBot], typing.Coroutine[typing.Any, typing.Any, None]]] = []
        self._proxy_settings = proxy_settings if proxy_settings is not None else config_impl.ProxySettings()

        # Entity creation
        self._entity_factory = entity_factory_impl.EntityFactoryImpl(self)

        # RESTful API.
        self._rest = rest_impl.RESTClientImpl(
            cache=None,
            entity_factory=self._entity_factory,
            executor=self._executor,
            http_settings=self._http_settings,
            max_rate_limit=max_rate_limit,
            max_retries=max_retries,
            proxy_settings=self._proxy_settings,
            rest_url=rest_url,
            token=token,
            token_type=token_type,
        )

        # InteractionServer
        self._server = interaction_server_impl.InteractionServer(
            entity_factory=self._entity_factory, public_key=public_key, rest_client=self._rest
        )

    @property
    def is_alive(self) -> bool:
        return self._close_event is not None

    @property
    def interaction_server(self) -> interaction_server_.InteractionServer:
        return self._server

    @property
    def on_shutdown(
        self,
    ) -> typing.Sequence[typing.Callable[[RESTBot], typing.Coroutine[typing.Any, typing.Any, None]]]:
        return self._on_shutdown.copy()

    @property
    def on_startup(self) -> typing.Sequence[typing.Callable[[RESTBot], typing.Coroutine[typing.Any, typing.Any, None]]]:
        return self._on_startup.copy()

    @property
    def rest(self) -> rest_api.RESTClient:
        return self._rest

    @property
    def entity_factory(self) -> entity_factory_api.EntityFactory:
        return self._entity_factory

    @property
    def http_settings(self) -> config_impl.HTTPSettings:
        return self._http_settings

    @property
    def proxy_settings(self) -> config_impl.ProxySettings:
        return self._proxy_settings

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        return self._executor

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

    def add_shutdown_callback(
        self, callback: typing.Callable[[RESTBot], typing.Coroutine[typing.Any, typing.Any, None]], /
    ) -> None:
        self._on_shutdown.append(callback)

    def remove_shutdown_callback(
        self, callback: typing.Callable[[RESTBot], typing.Coroutine[typing.Any, typing.Any, None]], /
    ) -> None:
        self._on_shutdown.remove(callback)

    def add_startup_callback(
        self, callback: typing.Callable[[RESTBot], typing.Coroutine[typing.Any, typing.Any, None]], /
    ) -> None:
        self._on_startup.append(callback)

    def remove_startup_callback(
        self, callback: typing.Callable[[RESTBot], typing.Coroutine[typing.Any, typing.Any, None]], /
    ) -> None:
        self._on_startup.remove(callback)

    async def close(self) -> None:
        if not self._close_event:
            raise errors.ComponentStateConflictError("Cannot close an inactive bot")

        if self._is_closing:
            await self.join()
            return

        _LOGGER.info("bot requested to shut down")

        self._is_closing = True
        await self._server.close()

        try:
            for callback in self._on_shutdown:
                await callback(self)

        finally:
            await self._rest.close()
            self._close_event.set()
            self._close_event = None
            self._is_closing = False

            _LOGGER.info("bot shut down")

    async def join(self) -> None:
        if not self._close_event:
            raise errors.ComponentStateConflictError("Cannot wait for an inactive bot to join")

        await self._close_event.wait()

    async def on_interaction(self, body: bytes, signature: bytes, timestamp: bytes) -> interaction_server_.Response:
        return await self._server.on_interaction(body, signature, timestamp)

    def run(
        self,
        asyncio_debug: bool = False,
        backlog: int = 128,
        check_for_updates: bool = True,
        close_loop: bool = True,
        close_passed_executor: bool = False,
        coroutine_tracking_depth: typing.Optional[int] = None,
        enable_signal_handlers: typing.Optional[bool] = None,
        host: typing.Optional[typing.Union[str, typing.Sequence[str]]] = None,
        path: typing.Optional[str] = None,
        port: typing.Optional[int] = None,
        propagate_interrupts: bool = False,
        reuse_address: typing.Optional[bool] = None,
        reuse_port: typing.Optional[bool] = None,
        shutdown_timeout: float = 60.0,
        socket: typing.Optional[socket_.socket] = None,
        ssl_context: typing.Optional[ssl.SSLContext] = None,
    ) -> None:
        """Open this REST server and block until it closes.

        Other Parameters
        ----------------
        asyncio_debug : bool
            If [`True`][], then debugging is enabled for the asyncio event loop in use.
        backlog : int
            The number of unaccepted connections that the system will allow before
            refusing new connections.
        check_for_updates : bool
            If [`True`][], will check for newer versions of hikari on
            PyPI and notify if available.
        close_loop : bool
            If [`True`][], then once the bot enters a state where all components
            have shut down permanently during application shut down, then all
            asyncgens and background tasks will be destroyed, and the event
            loop will be shut down.

            This will wait until all hikari-owned [`aiohttp`][] connectors have
            had time to attempt to shut down correctly (around 250ms), and on
            Python 3.9 and newer, will also shut down the default event loop
            executor too.
        close_passed_executor : bool
            If [`True`][], any custom [`concurrent.futures.Executor`][] passed
            to the constructor will be shut down when the application
            terminates. This does not affect the default executor associated
            with the event loop, and will not do anything if you do not
            provide a custom executor to the constructor.
        coroutine_tracking_depth : typing.Optional[int]
            If an integer value and supported by the interpreter, then this
            many nested coroutine calls will be tracked with their call
            origin state. This allows you to determine where non-awaited
            coroutines may originate from, but generally you
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
        host : typing.Optional[typing.Union[str, aiohttp.web.HostSequence]]
            TCP/IP host or a sequence of hosts for the HTTP server.
        port : typing.Optional[int]
            TCP/IP port for the HTTP server.
        path : typing.Optional[str]
            File system path for HTTP server unix domain socket.
        reuse_address : typing.Optional[bool]
            Tells the kernel to reuse a local socket in TIME_WAIT state, without
            waiting for its natural timeout to expire.
        reuse_port : typing.Optional[bool]
            Tells the kernel to allow this endpoint to be bound to the same port
            as other existing endpoints are also bound to.
        socket : typing.Optional[socket.socket]
            A pre-existing socket object to accept connections on.
        shutdown_timeout : float
            A delay, in seconds, to wait for graceful server shut down before forcefully
            disconnecting all open client sockets.
        ssl_context : typing.Optional[ssl.SSLContext]
            SSL context for HTTPS servers.
        """
        if self.is_alive:
            raise errors.ComponentStateConflictError("Cannot start a bot that's already active")

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
                        backlog=backlog,
                        check_for_updates=check_for_updates,
                        host=host,
                        port=port,
                        path=path,
                        reuse_address=reuse_address,
                        reuse_port=reuse_port,
                        socket=socket,
                        shutdown_timeout=shutdown_timeout,
                        ssl_context=ssl_context,
                    )
                )
                loop.run_until_complete(self.join())

            finally:
                try:
                    if self._close_event:
                        if self._is_closing:
                            loop.run_until_complete(self._close_event.wait())
                        else:
                            loop.run_until_complete(self.close())

                    if close_passed_executor and self._executor:
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
        backlog: int = 128,
        check_for_updates: bool = True,
        host: typing.Optional[typing.Union[str, typing.Sequence[str]]] = None,
        port: typing.Optional[int] = None,
        path: typing.Optional[str] = None,
        reuse_address: typing.Optional[bool] = None,
        reuse_port: typing.Optional[bool] = None,
        socket: typing.Optional[socket_.socket] = None,
        shutdown_timeout: float = 60.0,
        ssl_context: typing.Optional[ssl.SSLContext] = None,
    ) -> None:
        """Start the bot and wait for the internal server to startup then return.

        !!! note
            For more information on the other parameters such as defaults see
            AIOHTTP's documentation.

        Other Parameters
        ----------------
        backlog : int
            The number of unaccepted connections that the system will allow before
            refusing new connections.
        check_for_updates : bool
            If [`True`][], will check for newer versions of hikari on PyPI
            and notify if available.
        host : typing.Optional[typing.Union[str, aiohttp.web.HostSequence]]
            TCP/IP host or a sequence of hosts for the HTTP server.
        port : typing.Optional[int]
            TCP/IP port for the HTTP server.
        path : typing.Optional[str]
            File system path for HTTP server unix domain socket.
        reuse_address : typing.Optional[bool]
            Tells the kernel to reuse a local socket in TIME_WAIT state, without
            waiting for its natural timeout to expire.
        reuse_port : typing.Optional[bool]
            Tells the kernel to allow this endpoint to be bound to the same port
            as other existing endpoints are also bound to.
        socket : typing.Optional[socket.socket]
            A pre-existing socket object to accept connections on.
        shutdown_timeout : float
            A delay, in seconds, to wait for graceful server shut down before forcefully
            disconnecting all open client sockets.
        ssl_context : typing.Optional[ssl.SSLContext]
            SSL context for HTTPS servers.
        """
        if self.is_alive:
            raise errors.ComponentStateConflictError("Cannot start an already active interaction server")

        self._is_closing = False
        self._close_event = asyncio.Event()

        if check_for_updates:
            asyncio.create_task(
                ux.check_for_updates(self._http_settings, self._proxy_settings), name="check for package updates"
            )

        self._rest.start()
        try:
            for callback in self._on_startup:
                await callback(self)

        except Exception:
            await self._rest.close()
            raise

        await self._server.start(
            backlog=backlog,
            host=host,
            port=port,
            path=path,
            reuse_address=reuse_address,
            reuse_port=reuse_port,
            socket=socket,
            shutdown_timeout=shutdown_timeout,
            ssl_context=ssl_context,
        )

    @typing.overload
    def get_listener(
        self, interaction_type: typing.Type[command_interactions.CommandInteraction], /
    ) -> typing.Optional[
        interaction_server_.ListenerT[command_interactions.CommandInteraction, _ModalOrMessageResponseBuilderT]
    ]: ...

    @typing.overload
    def get_listener(
        self, interaction_type: typing.Type[component_interactions.ComponentInteraction], /
    ) -> typing.Optional[
        interaction_server_.ListenerT[component_interactions.ComponentInteraction, _ModalOrMessageResponseBuilderT]
    ]: ...

    @typing.overload
    def get_listener(
        self, interaction_type: typing.Type[command_interactions.AutocompleteInteraction], /
    ) -> typing.Optional[
        interaction_server_.ListenerT[
            command_interactions.AutocompleteInteraction, special_endpoints.InteractionAutocompleteBuilder
        ]
    ]: ...

    @typing.overload
    def get_listener(
        self, interaction_type: typing.Type[modal_interactions.ModalInteraction], /
    ) -> typing.Optional[
        interaction_server_.ListenerT[modal_interactions.ModalInteraction, _MessageResponseBuilderT]
    ]: ...

    @typing.overload
    def get_listener(
        self, interaction_type: typing.Type[_InteractionT_co], /
    ) -> typing.Optional[
        interaction_server_.ListenerT[_InteractionT_co, special_endpoints.InteractionResponseBuilder]
    ]: ...

    def get_listener(
        self, interaction_type: typing.Type[_InteractionT_co], /
    ) -> typing.Optional[interaction_server_.ListenerT[_InteractionT_co, special_endpoints.InteractionResponseBuilder]]:
        return self._server.get_listener(interaction_type)

    @typing.overload
    def set_listener(
        self,
        interaction_type: typing.Type[command_interactions.CommandInteraction],
        listener: typing.Optional[
            interaction_server_.ListenerT[command_interactions.CommandInteraction, _ModalOrMessageResponseBuilderT]
        ],
        /,
        *,
        replace: bool = False,
    ) -> None: ...

    @typing.overload
    def set_listener(
        self,
        interaction_type: typing.Type[component_interactions.ComponentInteraction],
        listener: typing.Optional[
            interaction_server_.ListenerT[component_interactions.ComponentInteraction, _ModalOrMessageResponseBuilderT]
        ],
        /,
        *,
        replace: bool = False,
    ) -> None: ...

    @typing.overload
    def set_listener(
        self,
        interaction_type: typing.Type[command_interactions.AutocompleteInteraction],
        listener: typing.Optional[
            interaction_server_.ListenerT[
                command_interactions.AutocompleteInteraction, special_endpoints.InteractionAutocompleteBuilder
            ]
        ],
        /,
        *,
        replace: bool = False,
    ) -> None: ...

    @typing.overload
    def set_listener(
        self,
        interaction_type: typing.Type[modal_interactions.ModalInteraction],
        listener: typing.Optional[
            interaction_server_.ListenerT[modal_interactions.ModalInteraction, _MessageResponseBuilderT]
        ],
        /,
        *,
        replace: bool = False,
    ) -> None: ...

    def set_listener(
        self,
        interaction_type: typing.Type[_InteractionT_co],
        listener: typing.Optional[
            interaction_server_.ListenerT[_InteractionT_co, special_endpoints.InteractionResponseBuilder]
        ],
        /,
        *,
        replace: bool = False,
    ) -> None:
        self._server.set_listener(interaction_type, listener, replace=replace)  # type: ignore
