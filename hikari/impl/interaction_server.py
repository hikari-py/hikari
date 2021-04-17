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
"""Standard implementation of a REST based interactions server."""
from __future__ import annotations

__all__: typing.Sequence[str] = ["InteractionServer"]

import asyncio
import hashlib
import logging
import sys
import typing

import aiohttp.web
import aiohttp.web_runner

from hikari import errors
from hikari import interactions
from hikari.api import interaction_server
from hikari.api import special_endpoints
from hikari.internal import data_binding
from hikari.internal import ed25519
from hikari.internal import ux

if typing.TYPE_CHECKING:
    import socket as socket_
    import ssl

    import aiohttp.typedefs

    from hikari import applications
    from hikari import snowflakes
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import event_factory as event_factory_
    from hikari.api import event_manager as event_manager_
    from hikari.api import rest as rest_client_

    ListenerDictT = typing.Dict[
        typing.Type[interaction_server.InteractionT],
        interaction_server.MainListenerT[interaction_server.InteractionT],
    ]


_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.interaction_server")

# Internal interaction and interaction response types.
_PING_INTERACTION_TYPE: typing.Final[int] = 1
_PONG_RESPONSE_TYPE: typing.Final[int] = 1

# HTTP status codes.
_OK_STATUS: typing.Final[int] = 200
_BAD_REQUEST_STATUS: typing.Final[int] = 400
_PAYLOAD_TOO_LARGE_STATUS: typing.Final[int] = 413
_UNSUPPORTED_MEDIA_TYPE_STATUS: typing.Final[int] = 415
_INTERNAL_SERVER_ERROR_STATUS: typing.Final[int] = 500

# Header keys and values
_X_SIGNATURE_ED25519_HEADER: typing.Final[str] = "X-Signature-Ed25519"
_X_SIGNATURE_TIMESTAMP_HEADER: typing.Final[str] = "X-Signature-Timestamp"
_CONTENT_TYPE_KEY: typing.Final[str] = "Content-Type"
_USER_AGENT_KEY: typing.Final[str] = "User-Agent"
_JSON_CONTENT_TYPE: typing.Final[str] = "application/json"
_TEXT_CONTENT_TYPE: typing.Final[str] = "text/plain"

# Constant response payloads
_ACK_PAYLOAD: typing.Final[str] = data_binding.dump_json({"type": interactions.InteractionResponseType.ACKNOWLEDGE})
_PONG_PAYLOAD: typing.Final[str] = data_binding.dump_json({"type": _PONG_RESPONSE_TYPE})


class _Response:
    __slots__: typing.Sequence[str] = ("_headers", "_payload", "_status_code")

    def __init__(
        self,
        status_code: int,
        payload: typing.Optional[str] = None,
        *,
        content_type: typing.Optional[str] = None,
        headers: typing.Optional[typing.MutableMapping[str, str]] = None,
    ) -> None:
        if payload or content_type:
            if not headers:
                headers = {}

            headers[_CONTENT_TYPE_KEY] = content_type or _TEXT_CONTENT_TYPE

        self._headers = headers
        self._payload = payload.encode() if payload is not None else None
        self._status_code = status_code

    @property
    def headers(self) -> typing.Optional[typing.Mapping[str, str]]:
        return self._headers

    @property
    def payload(self) -> typing.Optional[bytes]:
        return self._payload

    @property
    def status_code(self) -> int:
        return self._status_code


class InteractionServer(interaction_server.InteractionServer):
    """Standard implementation of `hikari.api.interaction_server.InteractionServer`.

    Parameters
    ----------
    entity_factory : hikari.api.entity_factory.EntityFactory
        The entity factory instance this server should use.
    event_factory : hikari.api.event_factory.EventFactory
        The event factory instance this server should use.

    Other Parameters
    ----------------
    dumps : aiohttp.typedefs.JSONEncoder
        The JSON encoder this server should use. Defaults to `json.dumps`.
    events : typing.Optional[hikari.api.event_manager.EventManager]
        The event manager this server should dispatch all valid received events
        to along side the single dispatch listener. If left as `builtins.None`
        then this will still call the relevant `InteractionServer.listeners`
        callback.
    loads : aiohttp.typedefs.JSONDecoder
        The JSON decoder this server should use. Defaults to `json.loads`.
    public_key : builtins.bytes
        The public key this server should use for verifying request payloads from
        Discord. If left as `builtins.None` then the client will try to work this
        out using `rest_client`.
    rest_client : hikari.api.rest.RESTClient
        The client this should use for making REST requests.
    """

    __slots__: typing.Sequence[str] = (
        "_application_fetch_lock",
        "_dumps",
        "_entity_factory",
        "_event_factory",
        "_events",
        "_future",
        "_hashes",
        "_listeners",
        "_loads",
        "_rest_client",
        "_runner",
        "_server",
        "_verify",
    )

    def __init__(
        self,
        *,
        de_duplicate: bool = True,
        dumps: aiohttp.typedefs.JSONEncoder = data_binding.dump_json,
        entity_factory: entity_factory_.EntityFactory,
        event_factory: event_factory_.EventFactory,
        loads: aiohttp.typedefs.JSONDecoder = data_binding.load_json,
        rest_client: rest_client_.RESTClient,
        event_manager: typing.Optional[event_manager_.EventManager] = None,
        public_key: typing.Optional[bytes] = None,
    ) -> None:
        self._application_fetch_lock = asyncio.Lock()
        self._dumps = dumps
        self._entity_factory = entity_factory
        self._event_factory = event_factory
        self._events = event_manager
        self._future: asyncio.Future[None] = asyncio.Future()
        self._hashes: typing.Optional[typing.List[bytes]] = [] if de_duplicate else None
        self._listeners: ListenerDictT[interactions.PartialInteraction] = {}
        self._loads = loads
        self._rest_client = rest_client
        self._runner: typing.Optional[aiohttp.web_runner.AppRunner] = None
        self._server = aiohttp.web.Application()
        self._server.add_routes([aiohttp.web.post("/", self.aiohttp_hook)])
        self._server.on_cleanup.append(self._on_cleanup)
        self._server.on_shutdown.append(self._on_shutdown)
        self._server.on_startup.append(self._on_startup)
        self._verify = ed25519.build_ed25519_verifier(public_key) if public_key is not None else None

    @property
    def is_alive(self) -> bool:
        return self._runner is not None

    @property
    def listeners(
        self,
    ) -> interaction_server.ListenerMapT[interactions.PartialInteraction]:
        return self._listeners.copy()

    def _check_duplication(self, body: bytes) -> bool:
        if self._hashes is not None:
            if (current_hash := hashlib.md5(body).digest()) in self._hashes:  # noqa: 303 Use of insecure hash function.
                return True

            self._hashes.append(current_hash)
            if len(self._hashes) > 300:
                self._hashes.pop(0)

        return False

    async def _fetch_public_key(self) -> ed25519.VerifierT:
        application: typing.Union[applications.Application, applications.AuthorizationApplication]
        async with self._application_fetch_lock:
            if self._verify:
                return self._verify

            try:
                application = (await self._rest_client.fetch_authorization()).application

            except errors.UnauthorizedError:
                application = await self._rest_client.fetch_application()

            self._verify = ed25519.build_ed25519_verifier(application.public_key)
            return self._verify

    async def _on_cleanup(self, _: aiohttp.web.Application, /) -> None:
        if self._events:
            await self._events.dispatch(self._event_factory.deserialize_stopped_event())

    async def _on_shutdown(self, _: aiohttp.web.Application, /) -> None:
        if self._events:
            await self._events.dispatch(self._event_factory.deserialize_stopping_event())

    async def _on_startup(self, _: aiohttp.web.Application, /) -> None:
        if self._events:
            await self._events.dispatch(self._event_factory.deserialize_starting_event())
            await self._events.dispatch(self._event_factory.deserialize_started_event())

    async def aiohttp_hook(self, request: aiohttp.web.Request) -> aiohttp.web.Response:
        """Handle an AIOHTTP interaction request.

        This method handles aiohttp specific detail before calling
        `InteractionServer.on_interaction` with the data extracted from the
        request if it can and handles building an aiohttp response.

        Parameters
        ----------
        request : aiohttp.web.Request
            The received request.

        Returns
        -------
        aiohtttp.web.Response
            The aiohttp response.
        """
        if request.content_type.lower() != _JSON_CONTENT_TYPE:
            return aiohttp.web.Response(
                status=_UNSUPPORTED_MEDIA_TYPE_STATUS, body="Unsupported Media Type", content_type=_TEXT_CONTENT_TYPE
            )

        try:
            signature_header = bytes.fromhex(request.headers[_X_SIGNATURE_ED25519_HEADER])
            timestamp_header = request.headers[_X_SIGNATURE_TIMESTAMP_HEADER].encode()

        except (KeyError, ValueError):
            user_agent = request.headers.get(_USER_AGENT_KEY, "NONE")
            _LOGGER.info("Received a request with a missing or invalid ed25519 header (UA %r)", user_agent)
            return aiohttp.web.Response(
                status=_BAD_REQUEST_STATUS,
                body="Missing or invalid required request signature header(s)",
                content_type=_TEXT_CONTENT_TYPE,
            )

        try:
            body = await request.read()

        except aiohttp.web.HTTPRequestEntityTooLarge:
            return aiohttp.web.Response(
                status=_PAYLOAD_TOO_LARGE_STATUS, body="Payload too large", content_type=_TEXT_CONTENT_TYPE
            )

        if not body:
            user_agent = request.headers.get(_USER_AGENT_KEY, "NONE")
            _LOGGER.info("Received a body-less request (UA %r)", user_agent)
            return aiohttp.web.Response(
                status=_BAD_REQUEST_STATUS, body="POST request must have a body", content_type=_TEXT_CONTENT_TYPE
            )

        response = await self.on_interaction(body=body, signature=signature_header, timestamp=timestamp_header)
        return aiohttp.web.Response(status=response.status_code, headers=response.headers, body=response.payload)

    async def close(self) -> None:
        if not self._runner:
            raise TypeError("Cannot close an inactive interaction server")

        runner = self._runner
        future = self._future
        self._runner = None
        await runner.shutdown()
        await runner.cleanup()
        future.set_result(None)

    async def join(self) -> None:
        if not self._runner:
            raise TypeError("Cannot wait for an inactive interaction server to join")

        await self._future

    async def on_interaction(self, body: bytes, signature: bytes, timestamp: bytes) -> interaction_server.Response:
        verify = self._verify or await self._fetch_public_key()

        if not verify(body, signature, timestamp):
            _LOGGER.info("Received a request with an invalid signature")
            return _Response(_BAD_REQUEST_STATUS, "Invalid request signature")

        if self._check_duplication(body):
            _LOGGER.warning("Ignoring duplicated interaction request\n  %r", body)  # TODO: not a warning
            return _Response(_OK_STATUS, _ACK_PAYLOAD, content_type=_JSON_CONTENT_TYPE)

        try:
            payload = self._loads(body.decode("utf-8"))
            interaction_type = int(payload["type"])

        except (data_binding.JSONDecodeError, ValueError) as exc:
            _LOGGER.info("Received a request with an invalid JSON body", exc_info=exc)
            return _Response(_BAD_REQUEST_STATUS, "Invalid JSON body")

        except (KeyError, TypeError) as exc:
            _LOGGER.info("Invalid or missing 'type' field in received JSON payload", exc_info=exc)
            return _Response(_BAD_REQUEST_STATUS, "Invalid or missing 'type' field in payload")

        if interaction_type == _PING_INTERACTION_TYPE:
            _LOGGER.debug("Responding to ping interaction")
            return _Response(_OK_STATUS, _PONG_PAYLOAD, content_type=_JSON_CONTENT_TYPE)

        try:
            event = self._event_factory.deserialize_interaction_create_event(None, payload)

        except Exception as exc:
            asyncio.get_running_loop().call_exception_handler(
                {"message": "Exception occurred during interaction deserialization", "exception": exc}
            )
            return _Response(_INTERNAL_SERVER_ERROR_STATUS, "Exception occurred during interaction deserialization")

        _LOGGER.debug("Dispatching interaction %s", event.interaction.id)

        if self._events:
            asyncio.create_task(
                self._events.dispatch(event), name=f"{event.interaction.id} interaction request dispatch"
            )

        result: typing.Optional[special_endpoints.InteractionResponseBuilder] = None
        if listener := self._listeners.get(type(event.interaction)):
            try:
                result = await listener(event.interaction)

            except Exception as exc:
                asyncio.get_running_loop().call_exception_handler(
                    {"message": "Exception occurred during interaction dispatch", "exception": exc}
                )
                return _Response(_INTERNAL_SERVER_ERROR_STATUS, "Exception occurred during interaction dispatch")

        payload = self._dumps(result.build(self._entity_factory)) if result else _ACK_PAYLOAD
        return _Response(_OK_STATUS, payload, content_type=_JSON_CONTENT_TYPE)

    def run(
        self,
        asyncio_debug: typing.Optional[bool] = None,
        backlog: int = 128,
        close_loop: bool = True,
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
        backlog : builtins.int
            The number of unaccepted connections that the system will allow before
            refusing new connections.
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
        host : typing.Optional[typing.Union[builtins.str, aiohttp.web.HostSequence]]
            TCP/IP host or a sequence of hosts for the HTTP server.
        port : typing.Optional[builtins.int]
            TCP/IP port for the HTTP server.
        path : typing.Optional[builtins.str]
            File system path for HTTP server unix domain socket.
        reuse_address : typing.Optional[builtins.bool]
            Tells the kernel to reuse a local socket in TIME_WAIT state, without
            waiting for its natural timeout to expire.
        reuse_port : typing.Optional[builtins.bool]
            Tells the kernel to allow this endpoint to be bound to the same port
            as other existing endpoints are also bound to.
        socket : typing.Optional[socket.socket]
            A pre-existing socket object to accept connections on.
        shutdown_timeout : builtins.float
            A delay to wait for graceful server shutdown before forcefully
            disconnecting all open client sockets. This defaults to 60 seconds.
        ssl_context : typing.Optional[ssl.SSLContext]
            SSL context for HTTPS servers.
        """
        if self._runner:
            raise TypeError("Cannot start an already active interaction server")

        loop = asyncio.get_event_loop()

        if asyncio_debug:
            loop.set_debug(True)

        if coroutine_tracking_depth is not None:
            try:
                # Provisionally defined in CPython, may be removed without notice.
                sys.set_coroutine_origin_tracking_depth(coroutine_tracking_depth)  # type: ignore[attr-defined]
            except AttributeError:
                _LOGGER.log(ux.TRACE, "cannot set coroutine tracking depth for sys, no functionality exists for this")

        loop.run_until_complete(
            self.start(
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
        )
        loop.run_until_complete(self.join())

        if close_loop:
            loop.close()

    async def start(
        self,
        backlog: int = 128,
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
        backlog : builtins.int
            The number of unaccepted connections that the system will allow before
            refusing new connections.
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
        port : typing.Optional[builtins.int]
            TCP/IP port for the HTTP server.
        path : typing.Optional[builtins.str]
            File system path for HTTP server unix domain socket.
        reuse_address : typing.Optional[builtins.bool]
            Tells the kernel to reuse a local socket in TIME_WAIT state, without
            waiting for its natural timeout to expire.
        reuse_port : typing.Optional[builtins.bool]
            Tells the kernel to allow this endpoint to be bound to the same port
            as other existing endpoints are also bound to.
        socket : typing.Optional[socket.socket]
            A pre-existing socket object to accept connections on.
        shutdown_timeout : builtins.float
            A delay to wait for graceful server shutdown before forcefully
            disconnecting all open client sockets. This defaults to 60 seconds.
        ssl_context : typing.Optional[ssl.SSLContext]
            SSL context for HTTPS servers.

        !!! note
            For more information on the other parameters such as defaults see
            AIOHTTP's documentation.
        """
        if self._runner:
            raise TypeError("Cannot start an already active interaction server")

        self._future = asyncio.futures.Future()
        self._runner = aiohttp.web_runner.AppRunner(
            self._server, handle_signals=enable_signal_handlers, access_log=_LOGGER
        )
        await self._runner.setup()
        sites: typing.List[aiohttp.web.BaseSite] = []

        if host is not None:
            if isinstance(host, str):
                host = [host]

            for h in host:
                sites.append(
                    aiohttp.web.TCPSite(
                        self._runner,
                        h,
                        port,
                        shutdown_timeout=shutdown_timeout,
                        ssl_context=ssl_context,
                        backlog=backlog,
                        reuse_address=reuse_address,
                        reuse_port=reuse_port,
                    )
                )

        elif path is None and socket is None or port is None:
            sites.append(
                aiohttp.web.TCPSite(
                    self._runner,
                    port=port,
                    shutdown_timeout=shutdown_timeout,
                    ssl_context=ssl_context,
                    backlog=backlog,
                    reuse_address=reuse_address,
                    reuse_port=reuse_port,
                )
            )

        if path is not None:
            sites.append(
                aiohttp.web.UnixSite(
                    self._runner, path, shutdown_timeout=shutdown_timeout, ssl_context=ssl_context, backlog=backlog
                )
            )

        if socket is not None:
            sites.append(
                aiohttp.web.SockSite(
                    self._runner, socket, shutdown_timeout=shutdown_timeout, ssl_context=ssl_context, backlog=backlog
                )
            )

        for site in sites:
            _LOGGER.info("Starting site on %s", site.name)
            await site.start()

    def set_listener(
        self,
        interaction_type: typing.Type[interaction_server.InteractionT],
        listener: typing.Optional[interaction_server.MainListenerT[interaction_server.InteractionT]],
        /,
        *,
        replace: bool = False,
    ) -> None:
        if not replace and interaction_type in self._listeners:
            raise TypeError(f"Listener already set for {interaction_type!r}")

        self._listeners[interaction_type] = listener  # type: ignore[assignment]
