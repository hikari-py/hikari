#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
import datetime
import json
import ssl
import time
import typing
import zlib

import aiohttp.typedefs

from hikari import errors
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import logging_helpers
from hikari.internal_utilities import user_agent
from hikari.net import extra_gateway_events
from hikari.net import opcodes
from hikari.net import rates
from hikari.net import ws


class _ResumeConnection(ws.WebSocketClosure):
    """Request to restart the client connection using a resume. This is only used internally."""

    __slots__ = ()


class _RestartConnection(ws.WebSocketClosure):
    """Request by the gateway to completely reconnect using a fresh connection. This is only used internally."""

    __slots__ = ()


#: The signature of an event dispatcher function. Consumes three arguments. The first is the gateway that triggered
#: the event. The second is an event name from the gateway, the third is the payload which is assumed to always be a
#: :class:`dict` with :class:`str` keys. This should be a coroutine function.
DispatchHandler = typing.Callable[["GatewayClient", str, typing.Any], typing.Awaitable[None]]

# Version of the gateway in use.
_IMPL_VERSION = 7


async def _default_dispatch(gateway, event, payload) -> None:
    ...


class GatewayClientV7:
    """
    Implementation of the gateway communication layer. This is single threaded and can represent the connection for
    an un-sharded bot, or for a specific gateway shard. This does not implement voice activity.
    
    This implementation targets v7 of the gateway. 

    Args:
        client_session:
            **Required**. The :class:`hikari.net.ws.WebSocketClientSession` to use to make the websocket connection.

            Note:
                this must be closed manually.
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
        dispatch:
            A coroutine function that consumes a string event name and a JSON dispatch event payload consumed
            from the gateway to call each time a dispatch occurs. The payload will vary between events.
            If unspecified, this will default to an empty callback that does nothing.
        initial_presence:
            A JSON-serializable dict containing the initial presence to set, or `None` to just appear
            `online`. See https://discordapp.com/developers/docs/topics/gateway#update-status for a description
            of this `update-status` payload object.
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
        shard_count:
            the shard count to use, or `None` if sharding is to be disabled (default).
        shard_id:
            the shard ID to use, or `None` if sharding is to be disabled (default).
        ssl_context:
            optional SSL context to use.
        verify_ssl:
            defaulting to True, setting this to false will disable SSL verification.
        timeout:
            optional timeout to apply to individual HTTP requests.

    Warning:
        It is highly recommended to not alter any attributes of this object whilst the gateway is running unless clearly
        specified otherwise. Any change to internal state may result in undefined behaviour or effects. This is designed
        to be a low-level interface to the gateway, and not a general-use object.

    Events
    ~~~~~~

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
        "_in_buffer",
        "_closed_event",
        "client_session",
        "dispatch",
        "fingerprint",
        "heartbeat_interval",
        "heartbeat_latency",
        "in_count",
        "initial_presence",
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
        "seq",
        "session_id",
        "shard_count",
        "shard_id",
        "ssl_context",
        "started_at",
        "timeout",
        "token",
        "trace",
        "uri",
        "verify_ssl",
        "version",
        "ws",
        "zlib_decompressor",
    )

    #: The API version we should request the use of.
    _REQUESTED_VERSION = _IMPL_VERSION
    _NEVER_RECONNECT_CODES = (
        opcodes.GatewayClosure.AUTHENTICATION_FAILED,
        opcodes.GatewayClosure.INVALID_SHARD,
        opcodes.GatewayClosure.SHARDING_REQUIRED,
    )

    def __init__(
        self,
        *,
        # required args:
        uri: str,
        token: str,
        # optional args:
        json_unmarshaller: typing.Callable = None,
        json_unmarshaller_object_hook: typing.Type[dict] = None,
        json_marshaller: typing.Callable = None,
        dispatch: DispatchHandler = None,
        initial_presence: typing.Optional[data_structures.DiscordObjectT] = None,
        large_threshold: int = 50,
        loop: asyncio.AbstractEventLoop = None,
        max_persistent_buffer_size: int = 3 * 1024 ** 2,
        shard_id: typing.Optional[int] = None,
        shard_count: typing.Optional[int] = None,
        connector: aiohttp.BaseConnector = None,
        proxy_headers: aiohttp.typedefs.LooseHeaders = None,
        proxy_auth: aiohttp.BasicAuth = None,
        proxy_url: str = None,
        ssl_context: ssl.SSLContext = None,
        verify_ssl: bool = True,
        timeout: float = None,
    ) -> None:
        #: Raw buffer that gets filled by messages. You should not interfere with this field ever.
        #:
        #:
        self._in_buffer: bytearray = bytearray()

        #: An :class:`asyncio.Event` that will be triggered whenever the gateway disconnects.
        #: This is only used internally.
        self._closed_event = asyncio.Event()

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
        self.json_unmarshaller_object_hook = json_unmarshaller_object_hook or data_structures.ObjectProxy

        logger_args = (self, shard_id, shard_count) if shard_id is not None and shard_count is not None else (self,)

        #: Logger used to dump information to the console.
        #:
        #: :type: :class:`logging.Logger`
        self.logger = logging_helpers.get_named_logger(*logger_args)

        #: The coroutine function to dispatch any events to.
        #:
        #: :type: :class:`hikari.net.gateway.DispatchHandler`
        self.dispatch: DispatchHandler = dispatch or _default_dispatch

        loop = loop or asyncio.get_running_loop()

        #: The event loop to use.
        #:
        #: :type: :class:`asyncio.AbstractEventLoop`
        self.loop: asyncio.AbstractEventLoop = loop

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

        #: Client session to make the websocket connection from.
        #:
        #: :type: :class:`hikari.net.ws.WebSocketClientSession`
        self.client_session = ws.WebSocketClientSession(
            connector=connector, loop=self.loop, json_serialize=json_marshaller, version=aiohttp.HttpVersion11,
        )

        #: Number of shards in use, or `None` if not sharded.
        #:
        #: :type: :class:`int` or :class:`None`
        self.shard_count = shard_count

        #: Current shard ID, or `None` if not sharded.
        #:
        #: :type: :class:`int` or :class:`None`
        self.shard_id = shard_id

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
        self.uri = f"{uri}?v={self._REQUESTED_VERSION}&encoding=json&compression=zlib-stream"

        #: The active websocket connection handling the low-level connection logic. Populated only while
        #: connected.
        #:
        #: :type: :class:`aiohttp.ClientWebSocketResponse` or :class:`None`
        self.ws: typing.Optional[ws.WebSocketClientResponse] = None

        #: Gateway protocol version. Starts as the requested version, updated once ready with the actual version being
        #: used.
        #:
        #: :type: :class:`int`
        self.version = self._REQUESTED_VERSION

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
        self.timeout = timeout

    @property
    def up_time(self) -> datetime.timedelta:
        """The length of time the gateway has been connected for, or 0 seconds if the client has not yet started."""
        if self.started_at is None:
            return datetime.timedelta(seconds=0)
        return datetime.timedelta(seconds=time.perf_counter() - self.started_at)

    @property
    def is_shard(self) -> bool:
        """True if this is considered a shard, false otherwise."""
        return self.shard_id is not None and self.shard_count is not None

    async def _trigger_resume(self, code: int, reason: str) -> typing.NoReturn:
        """Trigger a `RESUME` operation. This will raise a :class:`ResumableConnectionClosed` exception."""
        await self.ws.close(code=code, reason=reason)
        raise _ResumeConnection(code=code, reason=reason)

    async def _trigger_identify(self, code: int, reason: str) -> typing.NoReturn:
        """Trigger a re-`IDENTIFY` operation. This will raise a :class:`GatewayRequestedReconnection` exception."""
        await self.ws.close(code=code, reason=reason)
        raise _RestartConnection(code=code, reason=reason)

    async def _send_json(self, payload, skip_rate_limit) -> None:
        self.logger.debug(
            "sending payload %s and %s rate limit", payload, "skipping" if skip_rate_limit else "not skipping"
        )

        if not skip_rate_limit:
            await self.rate_limit.acquire(self._warn_about_internal_rate_limit)

        raw = self.json_marshaller(payload)
        if len(raw) > 4096:
            self._handle_payload_oversize(payload)
        else:
            self.out_count += 1
            await self.ws.send_str(raw)

    async def _receive_json(self) -> data_structures.DiscordObjectT:
        msg = await self.ws.receive_any_str()

        if isinstance(msg, (bytes, bytearray)):
            self._in_buffer.extend(msg)
            while not self._in_buffer.endswith(b"\x00\x00\xff\xff"):
                msg = await self.ws.receive_any_str()
                self._in_buffer.extend(msg)

            msg = self.zlib_decompressor.decompress(self._in_buffer).decode("utf-8")

            # Prevent large packets persisting a massive buffer we never utilise.
            if len(self._in_buffer) > self.max_persistent_buffer_size:
                self._in_buffer = bytearray()
            else:
                self._in_buffer.clear()

        payload = self.json_unmarshaller(msg, object_hook=self.json_unmarshaller_object_hook)

        if not isinstance(payload, dict):
            return await self._trigger_identify(code=opcodes.GatewayClosure.TYPE_ERROR, reason="Expected JSON object.")

        self.logger.debug("received payload %s", payload)
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
            time_taken * 1_000,
        )

    async def _send_heartbeat(self) -> None:
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

    async def _keep_alive(self) -> None:
        # Send first heartbeat immediately so we know the latency.
        while not self._closed_event.is_set():
            try:
                now = time.perf_counter()
                if self.last_heartbeat_sent + self.heartbeat_interval < now:
                    last_sent = now - self.last_heartbeat_sent
                    msg = f"Failed to receive an acknowledgement from the previous heartbeat sent ~{last_sent}s ago"
                    await self._trigger_resume(code=opcodes.GatewayClosure.PROTOCOL_VIOLATION, reason=msg)

                await asyncio.wait_for(self._closed_event.wait(), timeout=self.heartbeat_interval)
            except asyncio.TimeoutError:
                start = time.perf_counter()
                await self._send_heartbeat()
                time_taken = time.perf_counter() - start

                if time_taken > 0.15 * self.heartbeat_latency:
                    self._handle_slow_client(time_taken)
            finally:
                # Yield to the event loop for a little while. Prevents some buggy behaviour with PyPy, and prevents
                # any mutation of the heartbeat interval immediately tanking the CPU, so may as well keep it here.
                await asyncio.sleep(1)

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
        self.heartbeat_interval = hb / 1_000.0
        self.logger.info("received HELLO. heartbeat interval is %sms", hb)
        self._dispatch(extra_gateway_events.CONNECT)

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
            },
        }

        if self.initial_presence is not None:
            payload["d"]["status"] = self.initial_presence

        if self.is_shard:
            # noinspection PyTypeChecker
            payload["d"]["shard"] = [self.shard_id, self.shard_count]

        self.logger.info("sent IDENTIFY")
        await self._send_json(payload, False)

    async def _handle_dispatch(self, event: str, payload: data_structures.DiscordObjectT) -> None:
        if event == "READY":
            await self._handle_ready(payload)
        if event == "RESUMED":
            await self._handle_resumed(payload)
        self.logger.debug("DISPATCH %s", event)
        self._dispatch(event, payload)

    async def _handle_ready(self, ready_payload: data_structures.DiscordObjectT) -> None:
        self.trace = ready_payload["_trace"]
        self.session_id = ready_payload["session_id"]
        self.version = ready_payload["v"]
        self.logger.info("session %s is READY", self.session_id)
        self.logger.debug("trace for session %s is %s", self.session_id, self.trace)

    async def _handle_resumed(self, resume_payload: data_structures.DiscordObjectT) -> None:
        self.trace = resume_payload["_trace"]
        self.logger.info("RESUMED successfully")
        self._dispatch(extra_gateway_events.RESUMED)

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
            self.logger.warning("instructed to disconnect and RECONNECT with gateway")
            self._dispatch(extra_gateway_events.RECONNECT)
            await self._trigger_identify(
                code=opcodes.GatewayClosure.NORMAL_CLOSURE, reason="you requested me to reconnect"
            )
        elif op == opcodes.GatewayOpcode.INVALID_SESSION:
            if d is True:
                self.logger.warning("will try to disconnect and RESUME")
                self._dispatch(extra_gateway_events.INVALID_SESSION, True)
                await self._trigger_resume(
                    code=opcodes.GatewayClosure.NORMAL_CLOSURE, reason="invalid session id so will resume"
                )
            else:
                self.logger.warning("will try to re-IDENTIFY")
                self._dispatch(extra_gateway_events.INVALID_SESSION, False)
                await self._trigger_identify(
                    code=opcodes.GatewayClosure.NORMAL_CLOSURE, reason="invalid session id so will close"
                )
        else:
            self.logger.warning("received unrecognised opcode %s", op)

    async def request_guild_members(self, guild_id: str, query: str = "", limit: int = 0) -> None:
        """
        Requests guild members from the given Guild ID. This can be used to retrieve all members available in a guild.

        Args:
            guild_id: the guild ID to request members from.
            query: member names to search for, or empty string to remove the constraint.
            limit: max number of members to retrieve, or zero to remove the constraint.

        Warning:
            Results will be dispatched as events in chunks of 1000 members per guild using the
            :attr:`hikari.events.GUILD_MEMBERS_CHUNK` event. You will need to listen to these yourself and decode them
            in case more than one occurs at once.
        """
        self.logger.debug("requesting members for guild %r with query %r and limit %r", guild_id, query, limit)
        await self._send_json(
            {
                "op": opcodes.GatewayOpcode.REQUEST_GUILD_MEMBERS,
                "d": {"guild_id": guild_id, "query": query, "limit": limit},
            },
            False,
        )

    async def update_status(
        self,
        idle_since: typing.Optional[int],
        game: typing.Optional[data_structures.DiscordObjectT],
        status: str,
        afk: bool,
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
            :class:`hikari.core.errors.DiscordGatewayError`:
                if the token provided is invalidated.
            :class:`websockets.exceptions.ConnectionClosed`:
                if the connection is unexpectedly closed before we can start processing.
        """
        while not self._closed_event.is_set():
            await self.run_once()

    async def run_once(self) -> None:
        """
        Run the gateway once, then finish regardless of the closure reason.

        Raises:
            :class:`hikari.errors.GatewayError`:
                if the token provided is invalidated.
            :class:`hikari.net.ws.WebSocketClosure`:
                if the connection is unexpectedly closed before we can start processing.
        """
        kwargs = dict(
            proxy=self.proxy_url,
            proxy_auth=self.proxy_auth,
            proxy_headers=self.proxy_headers,
            verify_ssl=self.verify_ssl,
            ssl_context=self.ssl_context,
            compress=0,
        )

        try:
            self.started_at = time.perf_counter()

            async with self.client_session.ws_connect(self.uri, **kwargs) as self.ws:
                try:
                    await self._receive_hello()
                    is_resume = self.seq is not None and self.session_id is not None
                    await (self._send_resume() if is_resume else self._send_identify())
                    await self._send_heartbeat()
                    await asyncio.gather(self._keep_alive(), self._process_events())
                    self._dispatch(extra_gateway_events.SHUTDOWN)
                except ws.WebSocketClosure as ex:
                    code, reason = opcodes.GatewayClosure(ex.code), ex.reason or "no reason"

                    self._dispatch(extra_gateway_events.DISCONNECT, {"code": code, "reason": reason})

                    if ex.code in self._NEVER_RECONNECT_CODES:
                        self.logger.critical("disconnected after %s [%s]. Please rectify issue manually", reason, code)
                        raise errors.GatewayError(code, reason) from ex

                    self.logger.warning("reconnecting after %s [%s]", reason, code)
                    if isinstance(ex, _RestartConnection):
                        self.seq, self.session_id, self.trace = None, None, []

        finally:
            self.logger.info("gateway client shutting down")

    async def close(self, block=True) -> None:
        """
        Request that the gateway gracefully shuts down. Once this has occurred, you should not reuse this object. Doing
        so will result in undefined behaviour.

        Args:
            block: await the closure of the websocket connection. Defaults to `True`. If `False`, then nothing is
                waited for.
        """
        self._closed_event.set()
        if block:
            await self.ws.wait_closed()

    def _dispatch(self, event_name: str, payload=None) -> None:
        # This prevents us blocking any task such as the READY handler.
        self.loop.create_task(self.dispatch(self, event_name, payload))


__all__ = ["GatewayClientV7"]
