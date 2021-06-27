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
"""Standard implementations of a Interaction based REST-only bot."""
from __future__ import annotations

__all__: typing.Sequence[str] = ["RESTBot"]

import asyncio
import typing

from hikari import applications
from hikari import config
from hikari import snowflakes
from hikari import traits
from hikari.api import interaction_server as interaction_server_
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import event_factory as event_factory_impl
from hikari.impl import interaction_server as interaction_server_impl
from hikari.impl import rest as rest_impl
from hikari.internal import ux

if typing.TYPE_CHECKING:
    import concurrent.futures
    import socket as socket_
    import ssl

    from hikari import guilds
    from hikari import interactions
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import event_factory as event_factory_
    from hikari.api import rest as rest_


# TODO: implement token strategy in rest client for Oauth2
class RESTBot(traits.InteractionServerAware, interaction_server_.InteractionServer):
    """Basic implementation of an interaction based REST-only bot.

    Parameters
    ----------
    token : builtins.str
        The bot or application token to use.
    token_type : typing.Union[hikari.applications.TokenType, str]
        The type of token being passed, this may be "Bot" or "Bearer".

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
    application : typing.Optional[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]]
        Object or ID of the application this bot instance should be associated
        with. If left as `builtins.None` then the client will try to work this
        value out based on `token`.
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
    http_settings : typing.Optional[hikari.config.HTTPSettings]
        Optional custom HTTP configuration settings to use. Allows you to
        customise functionality such as whether SSL-verification is enabled,
        what timeouts `aiohttp` should expect to use for requests, and behavior
        regarding HTTP-redirects.
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
    public_key : typing.Union[builtins.str, builtins.bytes, builtins.None]
        The public key to use to verify received interaction requests.
        This may be a hex encoded `builtins.str` or the raw `builtins.bytes`.
        If left as `builtins.None` then the client will try to work this value
        out based on `token`.
    rest_url : typing.Optional[builtins.str]
        Defaults to the Discord REST API URL if `builtins.None`. Can be
        overridden if you are attempting to point to an unofficial endpoint, or
        if you are attempting to mock/stub the Discord API for any reason.
        Generally you do not want to change this.

    !!! note
        `force_color` will always take precedence over `allow_color`.
    """

    __slots__: typing.Sequence[str] = (
        "_banner",
        "_executor",
        "_http_settings",
        "_proxy_settings",
        "_entity_factory",
        "_event_factory",
        "_rest",
        "_server",
    )

    def __init__(  # noqa: S106,S107 - Possible hardcoded password: 'Bot'
        self,
        token: str,
        # TODO: can we be more smart about this default for token_type?
        token_type: typing.Union[applications.TokenType, str],
        public_key: typing.Union[bytes, str, None] = None,
        *,
        allow_color: bool = True,
        application: typing.Optional[snowflakes.SnowflakeishOr[guilds.PartialApplication]] = None,
        banner: typing.Optional[str] = "hikari",
        executor: typing.Optional[concurrent.futures.Executor] = None,
        force_color: bool = False,
        http_settings: typing.Optional[config.HTTPSettings] = None,
        logs: typing.Union[None, int, str, typing.Dict[str, typing.Any]] = "INFO",
        max_rate_limit: float = 300,
        proxy_settings: typing.Optional[config.ProxySettings] = None,
        rest_url: typing.Optional[str] = None,
    ) -> None:
        if isinstance(public_key, str):
            public_key = bytes.fromhex(public_key)

        # TODO: raise if public_key's length isn't right when bytes

        if application is not None:
            application = snowflakes.Snowflake(application)

        elif token_type == applications.TokenType.BOT:
            try:
                application = applications.get_token_id(token)

            except ValueError:
                pass

        # Beautification and logging
        ux.init_logging(logs, allow_color, force_color)
        self.print_banner(banner, allow_color, force_color)

        # Settings and state
        self._banner = banner
        self._executor = executor
        self._http_settings = http_settings if http_settings is not None else config.HTTPSettings()
        self._proxy_settings = proxy_settings if proxy_settings is not None else config.ProxySettings()

        # Entity creation
        self._entity_factory = entity_factory_impl.EntityFactoryImpl(self)

        # Event creation
        self._event_factory = event_factory_impl.EventFactoryImpl(self)

        # RESTful API.
        self._rest = rest_impl.RESTClientImpl(
            application=application,
            connector_factory=rest_impl.BasicLazyCachedTCPConnectorFactory(self._http_settings),
            connector_owner=True,
            entity_factory=self._entity_factory,
            executor=self._executor,
            http_settings=self._http_settings,
            max_rate_limit=max_rate_limit,
            proxy_settings=self._proxy_settings,
            rest_url=rest_url,
            token=token,
            token_type=token_type,
        )

        # IntegrationServer
        self._server = interaction_server_impl.InteractionServer(
            application_id=application,
            entity_factory=self._entity_factory,
            event_factory=self._event_factory,
            public_key=public_key,
            rest_client=self._rest,
        )

    @property
    def is_alive(self) -> bool:
        return self._server.is_alive

    @property
    def listeners(
        self,
    ) -> interaction_server_.ListenerMapT[interactions.PartialInteraction]:
        return self._server.listeners

    @property
    def interaction_server(self) -> interaction_server_.InteractionServer:
        return self._server

    @property
    def rest(self) -> rest_.RESTClient:
        return self._rest

    @property
    def entity_factory(self) -> entity_factory_.EntityFactory:
        return self._entity_factory

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._proxy_settings

    @property
    def executor(self) -> typing.Optional[concurrent.futures.Executor]:
        return self._executor

    @property
    def event_factory(self) -> event_factory_.EventFactory:
        return self._event_factory

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

    async def close(self) -> None:
        await self._server.close()

    async def join(self) -> None:
        await self._server.join()

    async def on_interaction(self, body: bytes, signature: bytes, timestamp: bytes) -> interaction_server_.Response:
        return await self._server.on_interaction(body, signature, timestamp)

    def run(
        self,
        asyncio_debug: typing.Optional[bool] = None,
        backlog: int = 128,
        check_for_updates: bool = True,
        close_loop: bool = True,
        close_passed_executor: bool = False,
        coroutine_tracking_depth: typing.Optional[int] = None,
        enable_signal_handlers: bool = True,
        host: typing.Optional[typing.Union[str, typing.Sequence[str]]] = None,
        path: typing.Optional[str] = None,
        port: typing.Optional[int] = None,
        reuse_address: typing.Optional[bool] = None,
        reuse_port: typing.Optional[bool] = None,
        shutdown_timeout: float = 60.0,
        socket: typing.Optional[socket_.socket] = None,
        ssl_context: typing.Optional[ssl.SSLContext] = None,
    ) -> None:
        """Open this REST server and block until it closes.

        Other Parameters
        ----------------
        asyncio_debug : builtins.bool
            Defaults to `builtins.False`. If `builtins.True`, then debugging is
            enabled for the asyncio event loop in use.
        backlog : int
            The number of unaccepted connections that the system will allow before
            refusing new connections.
        check_for_updates : builtins.bool
            Defaults to `builtins.True`. If `builtins.True`, will check for
            newer versions of `hikari` on PyPI and notify if available.
        close_loop : builtins.bool
            Defaults to `builtins.True`. If `builtins.True`, then once the bot
            enters a state where all components have shut down permanently
            during application shutdown, then all asyngens and background tasks
            will be destroyed, and the event loop will be shut down.

            This will wait until all `hikari`-owned `aiohttp` connectors have
            had time to attempt to shut down correctly (around 250ms), and on
            Python 3.9 and newer, will also shut down the default event loop
            executor too.
        close_passed_executor : builtins.bool
            Defaults to `builtins.False`. If `builtins.True`, any custom
            `concurrent.futures.Executor` passed to the constructor will be
            shut down when the application terminates. This does not affect the
            default executor associated with the event loop, and will not
            do anything if you do not provide a custom executor to the
            constructor.
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
        host : typing.Optional[typing.Union[builtins.str, aiohttp.web.HostSequence]]
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
            A delay to wait for graceful server shutdown before forcefully
            disconnecting all open client sockets. This defaults to 60 seconds.
        ssl_context : typing.Optional[ssl.SSLContext]
            SSL context for HTTPS servers.
        """
        if check_for_updates:
            asyncio.get_event_loop().create_task(
                ux.check_for_updates(self._http_settings, self._proxy_settings),
                name="check for package updates",
            )

        self._server.run(
            asyncio_debug=asyncio_debug,
            backlog=backlog,
            close_loop=close_loop,
            coroutine_tracking_depth=coroutine_tracking_depth,
            enable_signal_handlers=enable_signal_handlers,
            host=host,
            port=port,
            path=path,
            reuse_address=reuse_address,
            reuse_port=reuse_port,
            socket=socket,
            shutdown_timeout=shutdown_timeout,
            ssl_context=ssl_context,
        )

        if close_passed_executor and self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

    async def start(
        self,
        backlog: int = 128,
        check_for_updates: bool = True,
        enable_signal_handlers: bool = True,
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

        Other Parameters
        ----------------
        backlog : int
            The number of unaccepted connections that the system will allow before
            refusing new connections.
        check_for_updates : builtins.bool
            Defaults to `builtins.True`. If `builtins.True`, will check for
            newer versions of `hikari` on PyPI and notify if available.
        enable_signal_handlers : builtins.bool
            Defaults to `builtins.True`. If on a __non-Windows__ OS with builtin
            support for kernel-level POSIX signals, then setting this to
            `builtins.True` will allow treating keyboard interrupts and other
            OS signals to safely shut down the application as calls to
            shut down the application properly rather than just killing the
            process in a dirty state immediately. You should leave this disabled
            unless you plan to implement your own signal handling yourself.
        host : typing.Optional[typing.Union[builtins.str, aiohttp.web.HostSequence]]
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
            A delay to wait for graceful server shutdown before forcefully
            disconnecting all open client sockets. This defaults to 60 seconds.
        ssl_context : typing.Optional[ssl.SSLContext]
            SSL context for HTTPS servers.

        !!! note
            For more information on the other parameters such as defaults see
            AIOHTTP's documentation.
        """
        if check_for_updates:
            asyncio.create_task(
                ux.check_for_updates(self._http_settings, self._proxy_settings),
                name="check for package updates",
            )

        await self._server.start(
            backlog=backlog,
            enable_signal_handlers=enable_signal_handlers,
            host=host,
            port=port,
            path=path,
            reuse_address=reuse_address,
            reuse_port=reuse_port,
            socket=socket,
            shutdown_timeout=shutdown_timeout,
            ssl_context=ssl_context,
        )

    def set_listener(
        self,
        interaction_type: typing.Type[interaction_server_.InteractionT],
        listener: typing.Optional[interaction_server_.MainListenerT[interaction_server_.InteractionT]],
        /,
        *,
        replace: bool = False,
    ) -> None:
        self._server.set_listener(interaction_type, listener, replace=replace)
