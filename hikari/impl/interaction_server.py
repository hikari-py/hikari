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

__all__: typing.List[str] = ["InteractionServer"]

import asyncio
import logging
import typing

import aiohttp.web
import aiohttp.web_runner

from hikari import applications
from hikari import errors
from hikari.api import interaction_server
from hikari.api import special_endpoints
from hikari.interactions import base_interactions
from hikari.internal import data_binding
from hikari.internal import ed25519

if typing.TYPE_CHECKING:
    import socket as socket_
    import ssl

    import aiohttp.typedefs

    from hikari.api import entity_factory as entity_factory_api
    from hikari.api import rest as rest_api
    from hikari.interactions import command_interactions
    from hikari.interactions import component_interactions

    _InteractionT_co = typing.TypeVar("_InteractionT_co", bound=base_interactions.PartialInteraction, covariant=True)
    _ResponseT_co = typing.TypeVar("_ResponseT_co", bound=special_endpoints.InteractionResponseBuilder, covariant=True)
    _MessageResponseBuilderT = typing.Union[
        special_endpoints.InteractionDeferredBuilder, special_endpoints.InteractionMessageBuilder
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
_NOT_IMPLEMENTED: typing.Final[int] = 501

_UTF_8_CHARSET: typing.Final[str] = "UTF-8"

# Header keys and values
_X_SIGNATURE_ED25519_HEADER: typing.Final[str] = "X-Signature-Ed25519"
_X_SIGNATURE_TIMESTAMP_HEADER: typing.Final[str] = "X-Signature-Timestamp"
_CONTENT_TYPE_KEY: typing.Final[str] = "Content-Type"
_USER_AGENT_KEY: typing.Final[str] = "User-Agent"
_JSON_CONTENT_TYPE: typing.Final[str] = "application/json"
_JSON_TYPE_WITH_CHARSET: typing.Final[str] = f"{_JSON_CONTENT_TYPE}; charset={_UTF_8_CHARSET}"
_TEXT_CONTENT_TYPE: typing.Final[str] = "text/plain"
_TEXT_TYPE_WITH_CHARSET: typing.Final[str] = f"{_TEXT_CONTENT_TYPE}; charset={_UTF_8_CHARSET}"


class _Response:
    __slots__: typing.Sequence[str] = ("_headers", "_payload", "_status_code")

    def __init__(
        self,
        status_code: int,
        payload: typing.Optional[bytes] = None,
        *,
        content_type: typing.Optional[str] = None,
    ) -> None:
        self._headers = None
        if payload or content_type:
            self._headers = {_CONTENT_TYPE_KEY: content_type or _TEXT_TYPE_WITH_CHARSET}

        self._payload = payload
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


# Constant response
_PONG_RESPONSE: typing.Final[_Response] = _Response(
    _OK_STATUS, data_binding.dump_json({"type": _PONG_RESPONSE_TYPE}).encode(), content_type=_JSON_TYPE_WITH_CHARSET
)


class InteractionServer(interaction_server.InteractionServer):
    """Standard implementation of `hikari.api.interaction_server.InteractionServer`.

    Parameters
    ----------
    entity_factory : hikari.api.entity_factory.EntityFactory
        The entity factory instance this server should use.

    Other Parameters
    ----------------
    dumps : aiohttp.typedefs.JSONEncoder
        The JSON encoder this server should use. Defaults to `json.dumps`.
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
        "_close_event",
        "_dumps",
        "_entity_factory",
        "_is_closing",
        "_listeners",
        "_loads",
        "_rest_client",
        "_server",
        "_verify",
    )

    def __init__(
        self,
        *,
        dumps: aiohttp.typedefs.JSONEncoder = data_binding.dump_json,
        entity_factory: entity_factory_api.EntityFactory,
        loads: aiohttp.typedefs.JSONDecoder = data_binding.load_json,
        rest_client: rest_api.RESTClient,
        public_key: typing.Optional[bytes] = None,
    ) -> None:
        # Building asyncio.Lock when there isn't a running loop may lead to runtime errors.
        self._application_fetch_lock: typing.Optional[asyncio.Lock] = None
        # Building asyncio.Event when there isn't a running loop may lead to runtime errors.
        self._close_event: typing.Optional[asyncio.Event] = None
        self._dumps = dumps
        self._entity_factory = entity_factory
        self._is_closing = False
        self._listeners: typing.Dict[typing.Type[base_interactions.PartialInteraction], typing.Any] = {}
        self._loads = loads
        self._rest_client = rest_client
        self._server: typing.Optional[aiohttp.web_runner.AppRunner] = None
        self._verify = ed25519.build_ed25519_verifier(public_key) if public_key is not None else None

    @property
    def is_alive(self) -> bool:
        """Whether this interaction server is active.

        Returns
        -------
        builtins.bool
            Whether this interaction server is active
        """
        return self._server is not None

    async def _fetch_public_key(self) -> ed25519.VerifierT:
        if self._application_fetch_lock is None:
            self._application_fetch_lock = asyncio.Lock()

        application: typing.Union[applications.Application, applications.AuthorizationApplication]
        async with self._application_fetch_lock:
            if self._verify:
                return self._verify

            if self._rest_client.token_type == applications.TokenType.BOT:
                application = await self._rest_client.fetch_application()

            else:
                application = (await self._rest_client.fetch_authorization()).application

            self._verify = ed25519.build_ed25519_verifier(application.public_key)
            return self._verify

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
            _LOGGER.debug("Payload with invalid media type %r received", request.content_type)
            return aiohttp.web.Response(
                status=_UNSUPPORTED_MEDIA_TYPE_STATUS,
                body=b"Unsupported Media Type",
                content_type=_TEXT_CONTENT_TYPE,
                charset=_UTF_8_CHARSET,
            )

        try:
            signature_header = bytes.fromhex(request.headers[_X_SIGNATURE_ED25519_HEADER])
            timestamp_header = request.headers[_X_SIGNATURE_TIMESTAMP_HEADER].encode()

        except (KeyError, ValueError):
            user_agent = request.headers.get(_USER_AGENT_KEY, "NONE")
            _LOGGER.debug("Received a request with a missing or invalid signature header (UA %r)", user_agent)
            return aiohttp.web.Response(
                status=_BAD_REQUEST_STATUS,
                body=b"Missing or invalid required request signature header(s)",
                content_type=_TEXT_CONTENT_TYPE,
                charset=_UTF_8_CHARSET,
            )

        try:
            body = await request.read()

        except aiohttp.web.HTTPRequestEntityTooLarge:
            _LOGGER.debug("Received a request with a payload that's too large to process")
            return aiohttp.web.Response(
                status=_PAYLOAD_TOO_LARGE_STATUS,
                body=b"Payload too large",
                content_type=_TEXT_CONTENT_TYPE,
                charset=_UTF_8_CHARSET,
            )

        if not body:
            user_agent = request.headers.get(_USER_AGENT_KEY, "NONE")
            _LOGGER.debug("Received a body-less request (UA %r)", user_agent)
            return aiohttp.web.Response(
                status=_BAD_REQUEST_STATUS,
                body=b"POST request must have a body",
                content_type=_TEXT_CONTENT_TYPE,
                charset=_UTF_8_CHARSET,
            )

        response = await self.on_interaction(body=body, signature=signature_header, timestamp=timestamp_header)
        return aiohttp.web.Response(status=response.status_code, headers=response.headers, body=response.payload)

    async def close(self) -> None:
        """Gracefully close the server and any open connections."""
        if not self._server or not self._close_event:
            raise errors.ComponentStateConflictError("Cannot close an inactive interaction server")

        if self._is_closing:
            await self.join()
            return

        self._is_closing = True
        self._application_fetch_lock = None
        # This shutdown then cleanup ordering matters.
        await self._server.shutdown()
        await self._server.cleanup()
        self._close_event.set()
        self._close_event = None
        self._server = None

    async def join(self) -> None:
        """Wait for the process to halt before continuing."""
        if not self._close_event:
            raise errors.ComponentStateConflictError("Cannot wait for an inactive interaction server to join")

        await self._close_event.wait()

    async def on_interaction(self, body: bytes, signature: bytes, timestamp: bytes) -> interaction_server.Response:
        """Handle an interaction received from Discord as a REST server.

        !!! note
            If this server instance is alive then this will be called internally
            by the server but if the instance isn't alive then this may still be
            called externally to trigger interaction dispatch.

        Parameters
        ----------
        body : builtins.bytes
            The interaction payload.
        signature : builtins.bytes
            Value of the `"X-Signature-Ed25519"` header used to verify the body.
        timestamp : builtins.bytes
            Value of the `"X-Signature-Timestamp"` header used to verify the body.

        Returns
        -------
        hikari.api.interaction_server.Response
            Instructions on how the REST server calling this should respond to
            the interaction request.
        """
        verify = self._verify or await self._fetch_public_key()

        if not verify(body, signature, timestamp):
            _LOGGER.error("Received a request with an invalid signature")
            return _Response(_BAD_REQUEST_STATUS, b"Invalid request signature")

        try:
            payload = self._loads(body.decode("utf-8"))
            interaction_type = int(payload["type"])

        except (data_binding.JSONDecodeError, ValueError, TypeError) as exc:
            _LOGGER.error("Received a request with an invalid JSON body", exc_info=exc)
            return _Response(_BAD_REQUEST_STATUS, b"Invalid JSON body")

        except KeyError as exc:
            _LOGGER.error("Missing 'type' field in received JSON payload", exc_info=exc)
            return _Response(_BAD_REQUEST_STATUS, b"Missing required 'type' field in payload")

        if interaction_type == _PING_INTERACTION_TYPE:
            _LOGGER.debug("Responding to ping interaction")
            return _PONG_RESPONSE

        try:
            interaction = self._entity_factory.deserialize_interaction(payload)

        except errors.UnrecognisedEntityError:
            _LOGGER.debug("Ignoring unknown interaction type %s", interaction_type)
            return _Response(_NOT_IMPLEMENTED, b"Interaction type not implemented")

        except Exception as exc:
            asyncio.get_running_loop().call_exception_handler(
                {"message": "Exception occurred during interaction deserialization", "exception": exc}
            )
            return _Response(_INTERNAL_SERVER_ERROR_STATUS, b"Exception occurred during interaction deserialization")

        if listener := self._listeners.get(type(interaction)):
            _LOGGER.debug("Dispatching interaction %s", interaction.id)
            try:
                result = await listener(interaction)
                payload = self._dumps(result.build(self._entity_factory))

            except Exception as exc:
                asyncio.get_running_loop().call_exception_handler(
                    {"message": "Exception occurred during interaction dispatch", "exception": exc}
                )
                return _Response(_INTERNAL_SERVER_ERROR_STATUS, b"Exception occurred during interaction dispatch")

            return _Response(_OK_STATUS, payload.encode(), content_type=_JSON_TYPE_WITH_CHARSET)

        _LOGGER.debug(
            "Ignoring interaction %s of type %s without registered listener", interaction.id, interaction.type
        )
        return _Response(_NOT_IMPLEMENTED, b"Handler not set for this interaction type")

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
        if self._server:
            raise errors.ComponentStateConflictError("Cannot start an already active interaction server")

        self._close_event = asyncio.Event()
        self._is_closing = False
        aio_app = aiohttp.web.Application()
        aio_app.add_routes([aiohttp.web.post("/", self.aiohttp_hook)])
        self._server = aiohttp.web_runner.AppRunner(aio_app, handle_signals=enable_signal_handlers, access_log=_LOGGER)
        await self._server.setup()
        sites: typing.List[aiohttp.web.BaseSite] = []

        if host is not None:
            if isinstance(host, str):
                host = [host]

            for h in host:
                sites.append(
                    aiohttp.web.TCPSite(
                        self._server,
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
                    self._server,
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
                    self._server, path, shutdown_timeout=shutdown_timeout, ssl_context=ssl_context, backlog=backlog
                )
            )

        if socket is not None:
            sites.append(
                aiohttp.web.SockSite(
                    self._server, socket, shutdown_timeout=shutdown_timeout, ssl_context=ssl_context, backlog=backlog
                )
            )

        for site in sites:
            _LOGGER.info("Starting site on %s", site.name)
            await site.start()

    @typing.overload
    def get_listener(
        self, interaction_type: typing.Type[command_interactions.CommandInteraction], /
    ) -> typing.Optional[
        interaction_server.ListenerT[command_interactions.CommandInteraction, _MessageResponseBuilderT]
    ]:
        ...

    @typing.overload
    def get_listener(
        self, interaction_type: typing.Type[component_interactions.ComponentInteraction], /
    ) -> typing.Optional[
        interaction_server.ListenerT[component_interactions.ComponentInteraction, _MessageResponseBuilderT]
    ]:
        ...

    def get_listener(
        self, interaction_type: typing.Type[_InteractionT_co], /
    ) -> typing.Optional[interaction_server.ListenerT[_InteractionT_co, special_endpoints.InteractionResponseBuilder]]:
        return self._listeners.get(interaction_type)

    @typing.overload
    def set_listener(
        self,
        interaction_type: typing.Type[command_interactions.CommandInteraction],
        listener: typing.Optional[
            interaction_server.ListenerT[command_interactions.CommandInteraction, _MessageResponseBuilderT]
        ],
        /,
        *,
        replace: bool = False,
    ) -> None:
        ...

    @typing.overload
    def set_listener(
        self,
        interaction_type: typing.Type[component_interactions.ComponentInteraction],
        listener: typing.Optional[
            interaction_server.ListenerT[component_interactions.ComponentInteraction, _MessageResponseBuilderT]
        ],
        /,
        *,
        replace: bool = False,
    ) -> None:
        ...

    def set_listener(
        self,
        interaction_type: typing.Type[_InteractionT_co],
        listener: typing.Optional[
            interaction_server.ListenerT[_InteractionT_co, special_endpoints.InteractionResponseBuilder]
        ],
        /,
        *,
        replace: bool = False,
    ) -> None:
        if listener:
            if not replace and interaction_type in self._listeners:
                raise TypeError(f"Listener already set for {interaction_type.__name__}")

            self._listeners[interaction_type] = listener

        else:
            self._listeners.pop(interaction_type, None)
