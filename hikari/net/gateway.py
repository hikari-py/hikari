#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""
Single-threaded asyncio V7 Gateway implementation. Handles regular heartbeating in a background task
on the same event loop. Implements zlib transport compression only.

Can be used as the main gateway connection for a single-sharded bot, or the gateway connection for a specific shard
in a swarm of shards making up a larger bot.

References:
    - IANA WS closure code standards: https://www.iana.org/assignments/websocket/websocket.xhtml
    - Gateway documentation: https://discordapp.com/developers/docs/topics/gateway
    - Opcode documentation: https://discordapp.com/developers/docs/topics/opcodes-and-status-codes
"""
from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import datetime
import functools
import json
import operator
import random
import ssl
import time
import typing
import zlib

import aiohttp.typedefs

from hikari import errors
from hikari.internal_utilities import compat
from hikari.internal_utilities import containers
from hikari.internal_utilities import loggers
from hikari.internal_utilities import meta
from hikari.net import rates
from hikari.net import user_agent


@dataclasses.dataclass(frozen=True)
class _RestartableClosure(RuntimeError):
    """
    Raised when the server shuts down the connection unexpectedly or we have triggered a closure
    because the server did something we didn't expect.

    These closures always result in us retrying one way or another, we do not just exit.
    """

    __slots__ = ("code", "reason")

    #: The closure code provided.
    code: int
    #: The message provided.
    reason: str


class _ResumeConnection(_RestartableClosure):
    """Request to restart the client connection using a resume. This is only used internally."""

    __slots__ = ()


class _RestartConnection(_RestartableClosure):
    """Request by the gateway to completely reconnect using a fresh connection. This is only used internally."""

    __slots__ = ()


class _ConnectionShutDownByUser(RuntimeError):
    """
    Raised internally when a connection has shut down.
    """

    __slots__ = ()


#: The signature of an event dispatcher function. Consumes three arguments. The first is the gateway that triggered
#: the event. The second is an event name from the gateway, the third is the payload which is assumed to always be a
#: :class:`dict` with :class:`str` keys. This should be a coroutine function.
DispatchHandler = typing.Callable[["GatewayClient", str, typing.Any], typing.Awaitable[None]]


async def _default_dispatch(_gateway, _event, _payload) -> None:
    ...


class Backoff:
    """
    Simple exponential backoff with maximum backoff cap and random jitter. If the backoff reaches
    the max backoff, a RuntimeError is raised.
    """

    __slots__ = ("max_backoff", "retry_count")

    def __init__(self, max_backoff: float):
        self.max_backoff = max_backoff
        self.retry_count = 0

    def __iter__(self):
        return self

    def __next__(self):
        backoff = (2 ** self.retry_count) + random.random()  # nosec
        if backoff < self.max_backoff:
            self.retry_count += 1
        else:
            raise RuntimeError("maximum backoff was reached.")
        return backoff

    def reset(self):
        self.retry_count = 0


class GatewayClient:
    """
    Implementation of the gateway communication layer. This is single threaded and can represent the connection for
    an un-sharded bot, or for a specific gateway shard. This does not implement voice activity.
    
    This implementation targets v7 of the gateway. 

    Args:
        token:
            the token to use to authenticate with the gateway.
        uri:
            the host to connect to, in the format `wss://gateway.net` or `wss://gateway.net:port`.

            Warning:
                This must NOT contain a query or a fragment!

    Optional args:
        connector:
            the :class:`aiohttp.BaseConnector` to use for the client session, or `None` if you wish to use the
            default instead.
        enable_guild_subscription_events:
            Defaulting to `True`, this will make the gateway emit events for changes to presence in guilds, and
            for any user-typing events. If you set this to `False`, those events will be ignored and will not
            be sent by Discord, reducing overall load on the bot significantly in large numbers of guilds.
        gateway_event_dispatcher:
            Consumer of any DISPATCH payloads that are received.

            A coroutine function that consumes this gateway client object, a string event name, and a JSON dispatch
            event payload consumed from the gateway to call each time a dispatch occurs.  The payload will vary between
            events. If unspecified, this will default to an empty callback that does nothing. This will only consume
            events that originate from the Discord gateway.

            See https://discordapp.com/developers/docs/topics/gateway#commands-and-events for the types of event that
            can be fired to this dispatcher.

            See :class:`hikari.net.opcodes.GatewayEvent` for the types of known event that can be fired to this
            dispatcher. If the event is in this list, an instance of this enum will be passed as the event name.
            If the event is unknown, a raw string will be passed instead.
        http_timeout:
            optional timeout to apply to individual HTTP requests.
        initial_presence:
            A JSON-serializable dict containing the initial presence to set, or `None` to just appear
            `online`. See https://discordapp.com/developers/docs/topics/gateway#update-status for a description
            of this `update-status` payload object.
        intents:
            A bitfield combination of every :class:`hikari.net.opcodes.GatewayIntent` you wish to receive events for.

            Warning:
                This feature is currently incubating and is not yet supported by the V7 gateway, so will not yet
                have any effect.

                See https://gist.github.com/msciotti/223272a6f976ce4fda22d271c23d72d9 for a discussion of the
                proposed implementation. This functionality exists purely as a placeholder for the time being, and
                will not filter anything out.

            If unspecified, this defaults to requesting all events possible.
        internal_event_dispatcher:
            Consumer of internal notable events.

            A coroutine function that consumes this gateway client object, a string event name and a JSON object
            containing event information to call each time a dispatch occurs. The payload will vary between events.
            If unspecified, this will default to an empty callback that does nothing. This will only consume events
            that originate internally, such as when a connection is made, closed, or when an invalid session occurs,
            etc.

            This exists separately to allow you to filter out non-API compliant events if you desire. If you wish to
            handle these in the same way as the gateway DISPATCH events, you can just pass the same dispatcher as
            for `gateway_event_dispatcher`.

            See :class:`hikari.net.opcodes.GatewayInternalEvent` for the types of event that can be fired to this
            dispatcher, if you wish to use "constant" values in your implementation to represent events.
        json_marshaller:
            a callable that consumes a Python object and returns a JSON-encoded string.
            This defaults to :func:`json.dumps`.
        json_unmarshaller:
            a callable that consumes a JSON-encoded string and returns a Python object.
            This defaults to :func:`json.loads`.
        json_unmarshaller_object_hook:
            the object hook to use to parse a JSON object into a Python object. Defaults to
            :class:`hikari.internal_utilities.data_structures.ObjectProxy`. This means that you can use any
            received dict as a regular dict, or use "JavaScript"-like dot-notation to access members.

            .. code-block:: python

                d = ObjectProxy(...)
                assert d.foo[1].bar == d["foo"][1]["bar"]
        large_threshold:
            the large threshold limit. Defaults to 50.
        loop:
            the event loop to run on. Required.
        max_persistent_buffer_size:
            Max size to allow the zlib buffer to grow to before recreating it. This defaults to
            3MiB. A larger value favours a slight (most likely unnoticeable) overall performance increase, at the cost
            of memory usage, since the gateway can send payloads tens of megabytes in size potentially. Without
            truncating, the payload will remain at the largest allocated size even when no longer required to provide
            that capacity.
        proxy_auth:
            optional proxy authentication to use.
        proxy_headers:
            optional proxy headers to pass.
        proxy_url:
            optional proxy URL to use.
        receive_timeout:
            the time to wait to receive any form of message before considering the connection to be dead.
        shard_count:
            the shard count to use, or `None` if sharding is to be disabled (default).
        shard_id:
            the shard ID to use, or `None` if sharding is to be disabled (default).
        ssl_context:
            optional SSL context to use.
        verify_ssl:
            defaulting to True, setting this to false will disable SSL verification.

    Warning:
        It is highly recommended to not alter any attributes of this object whilst the gateway is running unless clearly
        specified otherwise. Any change to internal state may result in undefined behaviour or effects. This is designed
        to be a low-level interface to the gateway, and not a general-use object.

    Warning:
        This must be initialized within a coroutine while an event loop is active
        and registered to the current thread.

    **Events**

    All events are dispatched with at least two arguments. These are always the first two to be provided, and will
    always be in the same order.

    Mandatory arguments:
        gateway:
            The gateway client that emitted this event. This is provided to allow event adapters to consolidate
            many shards into one common handler if required.
        event_name:
            The string name of the event. For internal events, these will always be in lowercase. Discord will provide
            events in UPPERCASE instead, so it is useful to call :meth:`str.lower` before processing it.

    As well as any events provided by the Discord API (as described at
    https://discordapp.com/developers/docs/topics/gateway#commands-and-events), this implementation will provide
    several other internal event types. These are defined specifically in :mod:`hikari.net.extra_gateway_events`.
    """

    __slots__ = (
        "_backoff",
        "_client_session_factory",
        "_closed_event",
        "_enable_guild_subscription_events",
        "_in_buffer",
        "_intents",
        "fingerprint",
        "gateway_event_dispatcher",
        "heartbeat_interval",
        "heartbeat_latency",
        "http_timeout",
        "in_count",
        "is_running",
        "initial_presence",
        "internal_event_dispatcher",
        "json_marshaller",
        "json_unmarshaller",
        "json_unmarshaller_object_hook",
        "large_threshold",
        "last_ack_received",
        "last_heartbeat_sent",
        "logger",
        "loop",
        "proxy_auth",
        "proxy_headers",
        "proxy_url",
        "max_persistent_buffer_size",
        "out_count",
        "rate_limit",
        "ready_event",
        "seq",
        "session_id",
        "shard_count",
        "shard_id",
        "ssl_context",
        "started_at",
        "token",
        "trace",
        "url",
        "verify_ssl",
        "ws",
        "zlib_decompressor",
    )

    # Closure codes that are unrecoverable from. This generally means the authentication is wrong or the bot
    # is not sharded correctly. The user has to fix these themselves, we cannot do it.
    _NEVER_RECONNECT_CODES = (
        opcodes.GatewayClosure.AUTHENTICATION_FAILED,
        opcodes.GatewayClosure.INVALID_SHARD,
        opcodes.GatewayClosure.SHARDING_REQUIRED,
    )

    # Closure codes from the gateway where we should never attempt to resume with and should always restart
    # the socket with a fresh session.
    _DO_NOT_RESUME_CLOSURE_CODES = (opcodes.GatewayClosure.UNKNOWN_OPCODE,)

    # How often to ping.
    _AUTOPING_PERIOD = 10

    # How much lag to find acceptable in general operations.
    _LAG_TOLERANCE_PERCENTAGE = 0.15

    def __init__(
        self,
        *,
        # required args:
        token: str,
        uri: str,
        # optional args:
        connector: aiohttp.BaseConnector = None,
        enable_guild_subscription_events=True,
        gateway_event_dispatcher: DispatchHandler = None,
        http_timeout: float = None,
        initial_presence: typing.Optional[containers.JSONObject] = None,
        intents: opcodes.GatewayIntent = functools.reduce(operator.or_, opcodes.GatewayIntent.__iter__()),
        internal_event_dispatcher: DispatchHandler = None,
        json_marshaller: typing.Callable = None,
        json_unmarshaller: typing.Callable = None,
        json_unmarshaller_object_hook: typing.Type[dict] = None,
        large_threshold: int = 50,
        loop: asyncio.AbstractEventLoop = None,
        max_persistent_buffer_size: int = 3 * 1024 ** 2,
        proxy_auth: aiohttp.BasicAuth = None,
        proxy_headers: aiohttp.typedefs.LooseHeaders = None,
        proxy_url: str = None,
        shard_count: typing.Optional[int] = None,
        shard_id: typing.Optional[int] = None,
        ssl_context: ssl.SSLContext = None,
        verify_ssl: bool = True,
    ) -> None:
        loop = loop or asyncio.get_running_loop()

        #: The event loop to use.
        #:
        #: :type: :class:`asyncio.AbstractEventLoop`
        self.loop: asyncio.AbstractEventLoop = loop

        #: Raw buffer that gets filled by messages. You should not interfere with this field ever.
        self._in_buffer: bytearray = bytearray()

        #: Holds the backoff to use. We max at 64 seconds.
        self._backoff = Backoff(64)

        #: An :class:`asyncio.Event` that will be triggered whenever the gateway disconnects.
        #: This is only used internally.
        self._closed_event = asyncio.Event()

        #: True if we want the guild to send events for presence changes and typing events. This is
        #: private as it cannot be adjusted once initially set without re-identifying.
        self._enable_guild_subscription_events = enable_guild_subscription_events

        #: The gateway intent to use. This is a bitfield combination of each category of event you wish to
        #: receive DISPATCH payloads for. See :class:`hikari.net.opcodes.GatewayIntent` for more information.
        #: This is private as it only applies while we identify.
        self._intents = intents

        #: Partial that can be used to generate new client sessions when we need them...
        self._client_session_factory = functools.partial(
            aiohttp.ClientSession,
            connector=connector,
            loop=self.loop,
            json_serialize=json_marshaller,
            version=aiohttp.HttpVersion11,
        )

        #: Callable used to marshal (serialize) payloads into JSON-encoded strings from native Python objects.
        #:
        #: Defaults to :func:`json.dumps`. You may want to override this if you choose to use a different
        #: JSON library, such as one that is compiled.
        self.json_marshaller = json_marshaller or json.dumps

        #: Callable used to unmarshal (deserialize) JSON-encoded payloads into native Python objects.
        #:
        #: Defaults to :func:`json.loads`. You may want to override this if you choose to use a different
        #: JSON library, such as one that is compiled.
        self.json_unmarshaller = json_unmarshaller or json.loads

        #: Dict-derived type to use for unmarshalled JSON objects.
        #:
        #: For convenience, this defaults to :class:`hikari.internal_utilities.data_structures.ObjectProxy`, since
        #: this provides a benefit of allowing you to use dicts as if they were normal python objects. If you wish
        #: to use another implementation, or just default to :class:`dict` instead, it is worth changing this
        #: attribute.
        self.json_unmarshaller_object_hook = json_unmarshaller_object_hook or containers.ObjectProxy

        logger_args = (self, shard_id, shard_count) if shard_id is not None and shard_count is not None else (self,)

        #: Logger used to dump information to the console.
        #:
        #: :type: :class:`logging.Logger`
        self.logger = loggers.get_named_logger(*logger_args)

        #: The coroutine function to dispatch any gateway DISPATCH events to.
        #:
        #: :type: :class:`hikari.net.gateway.DispatchHandler`
        self.gateway_event_dispatcher: DispatchHandler = gateway_event_dispatcher or _default_dispatch

        #: The coroutine function to dispatch any connection-related events to.
        #:
        #: :type: :class:`hikari.net.gateway.DispatchHandler`
        self.internal_event_dispatcher: DispatchHandler = internal_event_dispatcher or _default_dispatch

        #: The fingerprint payload used to identify this connection to the gateway.
        #:
        #: :type: :class:`dict`
        self.fingerprint = {
            "$os": user_agent.system_type(),
            "$browser": user_agent.library_version(),
            "$device": user_agent.python_version(),
        }

        #: ZLIB decompression context.
        #:
        #: :type: :class:`zlib.decompressobj`
        self.zlib_decompressor: typing.Any = zlib.decompressobj()

        #: Number of shards in use, or `None` if not sharded.
        #:
        #: :type: :class:`int` or :class:`None`
        self.shard_count = shard_count

        #: Current shard ID, or `None` if not sharded.
        #:
        #: :type: :class:`int` or :class:`None`
        self.shard_id = shard_id

        #: A boolean that represents whether the client is running or not.
        #:
        #: :type: :class:`bool`
        self.is_running = False

        #: The heartbeat interval. This is `float('nan')` until the gateway provides us a value to use on startup.
        #:
        #: :type: :class:`float`
        self.heartbeat_interval = float("nan")

        #: The time period in seconds that the last heartbeat we sent took to be acknowledged by the gateway. This
        #: will be `float('inf')` until the first heartbeat is performed and acknowledged.
        #:
        #: :type: :class:`float`
        self.heartbeat_latency = float("inf")

        #: Number of packets that have been received since startup.
        #:
        #: :type: :class:`int`
        self.in_count = 0

        #: The initial presence to use for the bot status once IDENTIFYing with the shard.
        #:
        #: :type: :class:`dict` or :class:`None`
        self.initial_presence = initial_presence

        #: What we regard to be a large guild in member numbers.
        #:
        #: :type: :class:`int`
        self.large_threshold = large_threshold

        #: The :func:`time.perf_counter` that the last heartbeat was acknowledged at. Is `float('nan')` until then.
        #:
        #: :type: :class:`float`
        self.last_ack_received = float("nan")

        #: The :func:`time.perf_counter` that the last heartbeat was sent at. Is `float('nan')` until then.
        #:
        #: :type: :class:`float`
        self.last_heartbeat_sent = float("nan")

        #: What we consider to be a large size for the internal buffer. Any packet over this size results in the buffer
        #: being completely recreated.
        #:
        #: :type: :class:`int`
        self.max_persistent_buffer_size = max_persistent_buffer_size

        #: Number of packets that have been sent since startup.
        #:
        #: :type: :class:`int`
        self.out_count = 0

        #: Rate limit bucket for the gateway.
        #:
        #: :type: :class:`hikari.net.rates.TimedTokenBucket`
        self.rate_limit = rates.TimedTokenBucket(120, 60, loop)

        #: The `seq` flag value, if there is one set.
        #:
        #: :type: :class:`int` or :class:`None`
        self.seq = None

        #: The session ID in use, if there is one set.
        #:
        #: :type: :class:`int` or :class:`None`
        self.session_id = None

        #: When the gateway connection was started, as a unix timestamp.
        #:
        #: :type: :class:`int` or :class:`None`
        self.started_at: typing.Optional[int] = None

        #: A list of gateway servers that are connected to, once connected.
        #:
        #: :type: :class`list` of :class:`str`
        self.trace: typing.List[str] = []

        #: Token used to authenticate with the gateway.
        #:
        #: :type: :class:`str`
        self.token = token.strip()

        #: The URI being connected to.
        #:
        #: :type: :class:`str`
        self.url = f"{uri}?v={self.version}&encoding=json&compress=zlib-stream"

        #: The active websocket connection handling the low-level connection logic. Populated only while
        #: connected.
        #:
        #: :type: :class:`aiohttp.ClientWebSocketResponse` or :class:`None`
        self.ws: typing.Optional[aiohttp.ClientWebSocketResponse] = None

        #: Optional SSL context to use.
        #:
        #: :type: :class:`ssl.SSLContext`
        self.ssl_context: ssl.SSLContext = ssl_context

        #: Optional proxy URL to use for HTTP requests.
        #:
        #: :type: :class:`str`
        self.proxy_url = proxy_url

        #: Optional authorization to use if using a proxy.
        #:
        #: :type: :class:`aiohttp.BasicAuth`
        self.proxy_auth = proxy_auth

        #: Optional proxy headers to pass.
        #:
        #: :type: :class:`aiohttp.typedefs.LooseHeaders`
        self.proxy_headers = proxy_headers

        #: If `true`, this will enforce SSL signed certificate verification, otherwise it will
        #: ignore potentially malicious SSL certificates.
        #:
        #: :type: :class:`bool`
        self.verify_ssl = verify_ssl

        #: Optional timeout for the initial HTTP request.
        #:
        #: :type: :class:`float`
        self.http_timeout = http_timeout

        #: An event you can wait for to determine when the bot receives the
        #: READY payload. We use this to indicate we are connected correctly.
        self.ready_event = asyncio.Event()

    @property
    def version(self) -> int:
        """The version of the gateway being used."""
        return 7

    @property
    def up_time(self) -> datetime.timedelta:
        """The length of time the gateway has been connected for, or 0 seconds if the client has not yet started."""
        if self.started_at is None:
            return datetime.timedelta(seconds=0)
        return datetime.timedelta(seconds=time.perf_counter() - self.started_at)

    @property
    def is_shard(self) -> bool:
        """True if this is considered a shard, false if the bot is running with a single gateway connection."""
        return self.shard_id is not None and self.shard_count is not None

    async def _trigger_resume(self, code: int, reason: str, cause=None) -> typing.NoReturn:
        """Trigger a `RESUME` operation. This will raise a :class:`ResumableConnectionClosed` exception."""
        raise _ResumeConnection(code=code, reason=reason) from cause

    async def _trigger_identify(self, code: int, reason: str, cause=None) -> typing.NoReturn:
        """Trigger a re-`IDENTIFY` operation. This will raise a :class:`GatewayRequestedReconnection` exception."""
        raise _RestartConnection(code=code, reason=reason) from cause

    async def _receive(self):
        # Repeat if we ping or pong just to keep that transparently out the way...
        while True:
            try:
                response = await self.ws.receive()
                self.logger.debug("< [%s] %s", response.type.name, response.data)
            except asyncio.TimeoutError:
                await self._trigger_resume(opcodes.GatewayClosure.INTERNAL_ERROR, "websocket connection timed out")
            else:
                if response.type in (aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY):
                    return response.data
                elif response.type == aiohttp.WSMsgType.PING:
                    self.logger.debug("received ping")
                    await self.ws.pong()
                elif response.type == aiohttp.WSMsgType.PONG:
                    self.logger.debug("received pong")
                elif response.type == aiohttp.WSMsgType.CLOSE:
                    await self.ws.close()
                    raise _RestartableClosure(self.ws.close_code, "gateway closed the connection")
                elif response.type in (aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSED):
                    raise _ConnectionShutDownByUser()
                elif response.type == aiohttp.WSMsgType.ERROR:
                    raise self.ws.exception()
                else:
                    raise TypeError(f"Expected TEXT or BINARY message on websocket but received {response.type}")

    async def _send_json(self, payload, skip_rate_limit) -> None:
        if not skip_rate_limit:
            await self.rate_limit.acquire(self._warn_about_internal_rate_limit)

        raw = self.json_marshaller(payload)
        if len(raw) > 4096:
            self._handle_payload_oversize(payload)
        else:
            self.out_count += 1
            await self.ws.send_str(raw)
            self.logger.debug("> %s", raw)

    async def _receive_json(self) -> containers.JSONObject:
        msg = await self._receive()

        if isinstance(msg, (bytes, bytearray)):
            self._in_buffer.extend(msg)
            while not self._in_buffer.endswith(b"\x00\x00\xff\xff"):
                msg = await self._receive()
                self._in_buffer.extend(msg)

            msg = self.zlib_decompressor.decompress(self._in_buffer).decode("utf-8")

            # Prevent large packets persisting a massive buffer we never utilise.
            # TODO: tune this size to get best performance?
            if len(self._in_buffer) > self.max_persistent_buffer_size:
                self._in_buffer = bytearray()
            else:
                self._in_buffer.clear()

        payload = self.json_unmarshaller(msg, object_hook=self.json_unmarshaller_object_hook)

        if not isinstance(payload, dict):
            return await self._trigger_identify(code=opcodes.GatewayClosure.TYPE_ERROR, reason="Expected JSON object.")

        self.in_count += 1

        return payload

    def _warn_about_internal_rate_limit(self) -> None:
        delta = self.rate_limit.reset_at - time.perf_counter()
        self.logger.warning(
            "you are being rate limited internally to prevent the gateway from disconnecting you. "
            "The current rate limit ends in %.2f seconds",
            delta,
        )

    def _handle_payload_oversize(self, payload) -> None:
        self.logger.error(
            "refusing to send payload as it is too large and sending this would result in a disconnect. "
            "Payload was: %s",
            payload,
        )

    def _handle_slow_client(self, time_taken) -> None:
        self.logger.warning(
            "took %sms to send HEARTBEAT, which is more than 15%% of the heartbeat interval. "
            "Your connection may be poor or the event loop may be blocked or under excessive load",
            time_taken * 1000,
        )

    async def _send_heartbeat(self) -> None:
        now = time.perf_counter()
        if self.last_ack_received < self.last_heartbeat_sent:
            last_sent = now - self.last_heartbeat_sent
            msg = f"failed to receive an acknowledgement from the previous heartbeat sent ~{last_sent}s ago"
            await self._trigger_resume(code=opcodes.GatewayClosure.PROTOCOL_VIOLATION, reason=msg)
        await self._send_json({"op": opcodes.GatewayOpcode.HEARTBEAT, "d": self.seq}, True)
        self.logger.debug("sent HEARTBEAT")
        self.last_heartbeat_sent = time.perf_counter()

    async def _send_ack(self) -> None:
        await self._send_json({"op": opcodes.GatewayOpcode.HEARTBEAT_ACK}, True)
        self.logger.debug("sent HEARTBEAT_ACK")

    async def _handle_ack(self) -> None:
        self.last_ack_received = time.perf_counter()
        self.heartbeat_latency = self.last_ack_received - self.last_heartbeat_sent
        self.logger.debug("received HEARTBEAT_ACK after %sms", round(self.heartbeat_latency * 1000))

    async def _ping_runner(self):
        # We keep pinging to expect pongs. This allows us to keep our timeout a little more reasonable.
        while not self._closed_event.is_set():
            await self.ws.ping()
            await asyncio.sleep(self._AUTOPING_PERIOD)

    async def _heartbeat_runner(self) -> None:
        # Send first heartbeat immediately so we know the latency.
        while not self._closed_event.is_set():
            try:
                await asyncio.wait_for(self._closed_event.wait(), timeout=self.heartbeat_interval)
            except asyncio.TimeoutError:
                # If we cannot send a heartbeat in around 45 seconds, we are blocked, and we cannot continue to
                # function as a normal bot.
                try:
                    start = time.perf_counter()
                    await asyncio.wait_for(self._send_heartbeat(), timeout=self.heartbeat_interval)
                    time_taken = time.perf_counter() - start

                    if time_taken > self._LAG_TOLERANCE_PERCENTAGE * self.heartbeat_latency:
                        self._handle_slow_client(time_taken)
                except asyncio.TimeoutError as ex:
                    await self._trigger_resume(
                        opcodes.GatewayClosure.INTERNAL_ERROR,
                        f"bot was unable to send a heartbeat in ~{self.heartbeat_latency}s successfully",
                        ex,
                    )

    async def _receive_hello(self) -> None:
        hello = await self._receive_json()
        op = hello["op"]
        if op != opcodes.GatewayOpcode.HELLO:
            return await self._trigger_resume(
                code=opcodes.GatewayClosure.PROTOCOL_VIOLATION, reason=f"Expected HELLO but got {op}"
            )

        d = hello["d"]
        self.trace = d["_trace"]
        hb = d["heartbeat_interval"]
        self.heartbeat_interval = hb / 1000.0
        self._dispatch_new_event(opcodes.GatewayInternalEvent.CONNECT, None, True)
        self._dispatch_new_event(opcodes.GatewayEvent.HELLO, d, False)
        self.logger.info("received HELLO. heartbeat interval is %sms", hb)

    async def _send_resume(self) -> None:
        payload = {
            "op": opcodes.GatewayOpcode.RESUME,
            "d": {"token": self.token, "session_id": self.session_id, "seq": self.seq},
        }
        await self._send_json(payload, False)
        self.logger.info("sent RESUME")

    async def _send_identify(self) -> None:
        payload = {
            "op": opcodes.GatewayOpcode.IDENTIFY,
            "d": {
                "token": self.token,
                "compress": False,
                "large_threshold": self.large_threshold,
                "properties": self.fingerprint,
                "guild_subscriptions": self._enable_guild_subscription_events,
                # Do not uncomment this, it will trigger a 4012 shutdown, which is undocumented
                # behaviour according to the closure codes list at the time of writing
                # see https://github.com/discordapp/discord-api-docs/issues/1266
                # "intents": int(self._intents),
            },
        }

        if self.initial_presence is not None:
            payload["d"]["presence"] = self.initial_presence

        if self.is_shard:
            # noinspection PyTypeChecker
            payload["d"]["shard"] = [self.shard_id, self.shard_count]

        self.logger.info(
            "sent IDENTIFY, guild subscriptions are %s",
            "enabled" if self._enable_guild_subscription_events else "disabled",
        )
        await self._send_json(payload, False)

    async def _handle_dispatch(self, event: str, payload: containers.JSONObject) -> None:
        if event == opcodes.GatewayEvent.READY:
            await self._handle_ready(payload)
        elif event == opcodes.GatewayEvent.RESUMED:
            await self._handle_resumed(payload)
        else:
            self.logger.debug("DISPATCH %s", event)
            try:
                event = opcodes.GatewayEvent(event)
            except ValueError:
                pass
            self._dispatch_new_event(event, payload, False)

    async def _handle_ready(self, ready_payload: containers.JSONObject) -> None:
        self.trace = ready_payload["_trace"]
        self.session_id = ready_payload["session_id"]
        shard = ready_payload.get("shard")

        if shard is not None:
            self.shard_id, self.shard_count = shard

        self.ready_event.set()
        self._dispatch_new_event(opcodes.GatewayEvent.READY, ready_payload, False)

        self.logger.info("session %s has completed handshake, initial connection is READY", self.session_id)
        self.logger.debug("trace for session %s is %s", self.session_id, self.trace)

    async def _handle_resumed(self, resume_payload: containers.JSONObject) -> None:
        self.trace = resume_payload["_trace"]
        self.session_id = resume_payload["session_id"]
        self.seq = resume_payload["seq"]
        self.logger.info("RESUMED successfully")
        # This is a gateway event, we don't want to capture it with the internal events, so it is
        # not enumerated.
        self._dispatch_new_event(opcodes.GatewayEvent.RESUMED, resume_payload, False)

    async def _process_events(self) -> None:
        """Polls the gateway for new packets and handles dispatching the results."""
        while not self._closed_event.is_set():
            await self._process_one_event()

    async def _process_one_event(self) -> None:
        message = await self._receive_json()
        op = message["op"]
        d = message["d"]
        seq = message.get("s", None)
        t = message.get("t", None)

        with contextlib.suppress(ValueError):
            op = opcodes.GatewayOpcode(op)

        if seq is not None:
            self.seq = seq
        if op == opcodes.GatewayOpcode.DISPATCH:
            await self._handle_dispatch(t, d)
        elif op == opcodes.GatewayOpcode.HEARTBEAT:
            await self._send_ack()
        elif op == opcodes.GatewayOpcode.HEARTBEAT_ACK:
            await self._handle_ack()
        elif op == opcodes.GatewayOpcode.RECONNECT:
            self.logger.warning("received RECONNECT, will reconnect with a new session")
            self._dispatch_new_event(opcodes.GatewayEvent.RECONNECT, d, False)
            await self._trigger_identify(
                code=opcodes.GatewayClosure.NORMAL_CLOSURE, reason="you requested me to reconnect"
            )
        elif op == opcodes.GatewayOpcode.INVALID_SESSION:
            self._dispatch_new_event(opcodes.GatewayEvent.INVALID_SESSION, d, False)
            if d is True:
                self.logger.warning("received INVALID_SESSION, will try to disconnect and RESUME")
                await self._trigger_resume(
                    code=opcodes.GatewayClosure.NORMAL_CLOSURE, reason="invalid session id so will resume"
                )
            else:
                self.logger.warning("received INVALID_SESSION, will try to re-IDENTIFY")
                await self._trigger_identify(
                    code=opcodes.GatewayClosure.NORMAL_CLOSURE, reason="invalid session id so will close"
                )
        else:
            self.logger.warning("received unrecognised opcode %s", op)

    def request_guild_members(
        self,
        guild_id: str,
        *guild_ids: str,
        limit: int = 0,
        query: str = None,
        presences: bool = True,
        user_ids: typing.Sequence[str] = None,
    ) -> None:
        """
        Requests guild members from the given Guild ID. This can be used to retrieve all members available in a guild.

        Args:
            guild_id:
                the first guild ID to request members from.
            *guild_ids:
                zero or more additional guild IDs to request members from.
            query:
                member names to search for, or empty string to remove the constraint.
            limit:
                max number of members to retrieve, or zero to remove the constraint. This will be
                ignored unless a non-empty `query` is specified.
            presences:
                `True` to return presences, `False` otherwise.
            user_ids:
                An optional sequence of user IDs to get the details for.

        Warning:
            Results will be dispatched as events in chunks of 1000 members per guild using the
            `GUILD_MEMBERS_CHUNK` event. You will need to listen to these yourself and decode
            them in case more than one occurs at once.

        Warning:
            You may not specify both `query` and `user_ids` in this call.
        """
        payload = {"guild_id": [guild_id, *guild_ids], "presences": presences}

        if user_ids is not None:
            if query is not None:
                raise RuntimeError("Cannot specify both user_ids and query together")
            payload["user_ids"] = [*user_ids]
        else:
            payload["query"] = query if query is not None else ""
            payload["limit"] = limit

        self.logger.debug("requesting members with constraints %s", payload)
        compat.asyncio.create_task(
            self._send_json({"op": opcodes.GatewayOpcode.REQUEST_GUILD_MEMBERS, "d": payload}, False,),
            name=f"send REQUEST_GUILD_MEMBERS (shard {self.shard_id}/{self.shard_count})",
        )

    @meta.incubating(message="This is not currently documented.")
    def request_guild_sync(self, guild_id1: str, *guild_ids: str) -> None:
        """
        Request that the gateway re-syncs any guilds provided.

        Args:
            guild_id1:
                the first guild ID to consider.
            guild_ids:
                any additional guild IDs to consider.
        """
        guilds = [guild_id1, *guild_ids]
        self.logger.debug("requesting a guild sync for guilds %s", guilds)
        compat.asyncio.create_task(
            self._send_json({"op": opcodes.GatewayOpcode.GUILD_SYNC, "d": guilds}, False),
            name=f"send GUILD_SYNC (shard {self.shard_id}/{self.shard_count})",
        )

    async def update_status(
        self, idle_since: typing.Optional[int], game: typing.Optional[containers.JSONObject], status: str, afk: bool,
    ) -> None:
        """
        Updates the bot user's status in this shard.

        Args:
            idle_since: unix timestamp in milliseconds that the user has been idle for, or `None` if not idle.
            game: an activity object representing the activity, or `None` if no activity is set.
            status: the status string to set.
            afk: True if the client is AFK, false otherwise.
        See:
            - Activity objects: https://discordapp.com/developers/docs/topics/gateway#activity-object
            - Valid statuses: https://discordapp.com/developers/docs/topics/gateway#update-status-status-types
        """
        d = {"idle": idle_since, "game": game, "status": status, "afk": afk}

        self.logger.debug(
            "updating status to idle since %r with game %r with status %r and afk %r", idle_since, game, status, afk
        )
        await self._send_json({"op": opcodes.GatewayOpcode.STATUS_UPDATE, "d": d}, False)

    async def update_voice_state(
        self, guild_id: str, channel_id: typing.Optional[int], self_mute: bool, self_deaf: bool
    ) -> None:
        """
        Updates the given shard's voice state (used to connect to/disconnect from/move between voice channels.

        Args:
            guild_id: the guild ID.
            channel_id: the channel ID, or `None` if you wish to disconnect.
            self_mute: if `True`, mute the bot, else if `False` keep the bot unmuted.
            self_deaf: if `True`, deafen the bot, else if `False`, keep the bot listening.
        """
        d = {"guild_id": str(guild_id), "channel_id": str(channel_id), "self_mute": self_mute, "self_deaf": self_deaf}

        self.logger.debug("updating voice state %s", d)
        await self._send_json({"op": opcodes.GatewayOpcode.VOICE_STATE_UPDATE, "d": d}, False)

    async def run(self) -> None:
        """
        Run the gateway and attempt to keep it alive for as long as possible using restarts and resumes if needed.

        Raises:
            :class:`hikari.errors.GatewayError`:
                if the token provided is invalidated.
            :class:`websockets.exceptions.ConnectionClosed`:
                if the connection is unexpectedly closed before we can start processing.
        """
        websocket_kwargs = dict(
            autoping=False,
            proxy=self.proxy_url,
            proxy_auth=self.proxy_auth,
            proxy_headers=self.proxy_headers,
            verify_ssl=self.verify_ssl,
            ssl_context=self.ssl_context,
            compress=0,
            max_msg_size=0,  # fixes #149, due to Discord's iffy message sizes.
            receive_timeout=2 * self._AUTOPING_PERIOD,
        )

        self._backoff.reset()
        session = None

        while not self._closed_event.is_set():
            try:
                session = self._client_session_factory()
                self.logger.debug("creating websocket connection to %s", self.url)

                self.started_at = time.perf_counter()
                self.ws = await session.ws_connect(self.url, **websocket_kwargs)
                try:
                    self.is_running = True
                    await self._run_once()
                finally:
                    self.is_running = False
                    compat.asyncio.create_task(self.ws.close(), name=f"close shard {self.shard_id}")
            except _ConnectionShutDownByUser:
                # The user asked us to stop, so don't throw anything. We will just exit on the loop gracefully.
                self.logger.warning("shard has been shut down by user")
                self._closed_event.set()
            except _RestartableClosure:
                # Something occurred where we want to automatically resume or restart, so reconnect without
                # exiting, but take the course of the backoff first.
                next_backoff = next(self._backoff)
                self.logger.warning("shard has shut down and will retry after a %ss backoff", next_backoff)
                await asyncio.sleep(next_backoff)
            except aiohttp.ClientConnectionError as ex:
                self.logger.error("failed to connect to gateway for initial HTTP upgrade: %s", str(ex))
                raise ex
            finally:
                await session.close()

    async def _run_once(self):
        """
        Manages keeping the websocket that is already assumed to be alive running until the first
        exception is raised. The callee is expected to manage shutting down any other resources.
        """
        try:
            await self._receive_hello()
            is_resume = self.seq is not None and self.session_id is not None
            await (self._send_resume() if is_resume else self._send_identify())
            await self._send_heartbeat()
            await asyncio.gather(self._heartbeat_runner(), self._process_events(), self._ping_runner())
            self._dispatch_new_event(opcodes.GatewayInternalEvent.MANUAL_SHUTDOWN, None, True)
        except _RestartableClosure as ex:
            code, reason = opcodes.GatewayClosure(ex.code), ex.reason or "no reason"

            self._dispatch_new_event(opcodes.GatewayInternalEvent.DISCONNECT, {"code": code, "reason": reason}, True)

            if ex.code in self._NEVER_RECONNECT_CODES:
                self.logger.critical("disconnected after %s [%s]. Please rectify", reason, code)
                raise errors.GatewayError(code, reason) from ex

            self.logger.warning("reconnecting after %s [%s]", reason, code)
            if isinstance(ex, _RestartConnection) or code in self._DO_NOT_RESUME_CLOSURE_CODES:
                self.seq, self.session_id, self.trace = None, None, []

            # Now we are tidy, reraise.
            raise ex
        finally:
            self.ready_event.clear()

    def _dispatch_new_event(self, event_name: str, payload, is_internal_event) -> None:
        # This prevents us blocking any task such as the READY handler.
        dispatcher = self.internal_event_dispatcher if is_internal_event else self.gateway_event_dispatcher
        compat.asyncio.create_task(
            dispatcher(self, event_name, payload),
            name=f"dispatching {event_name} event (shard {self.shard_id}/{self.shard_count})",
        )

    async def close(self) -> None:
        """
        Request that the gateway gracefully shuts down.
        """
        if not self.ws.closed:
            self._closed_event.set()
            await self.ws.close()


__all__ = ["GatewayClient"]
