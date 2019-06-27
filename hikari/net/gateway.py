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
__all__ = ("GatewayClient",)

import datetime
import json
import logging
import time
import zlib

import websockets

from hikari import errors
from hikari.compat import asyncio
from hikari.compat import contextlib
from hikari.compat import typing
from hikari.net import opcodes
from hikari.net import rates
from hikari import _utils
from hikari._utils import DispatchHandler
from hikari._utils import DiscordObject


class _ResumeConnection(websockets.ConnectionClosed):
    """Request to restart the client connection using a resume. This is only used internally."""

    __slots__ = ()


class _RestartConnection(websockets.ConnectionClosed):
    """Request by the gateway to completely reconnect using a fresh connection. This is only used internally."""

    __slots__ = ()


class GatewayClient:
    """
    Implementation of the gateway communication layer. This is single threaded and can represent the connection for
    an un-sharded bot, or for a specific gateway shard. This does not implement voice activity.

    Args:
        connector:
            the method used to create a websockets connection. You usually don't want to change this.
        dispatch:
            A coroutine function that consumes a string event name and a JSON dispatch event payload consumed
            from the gateway to call each time a dispatch occurs. This payload will be a dict as described on the
            Gateway documentation. If it is not a coroutine function, it will get cast to a coroutine function first.
        host:
            the host to connect to, in the format `wss://gateway.net` or `wss://gateway.net:port` without a query
            fragment.
        initial_presence:
            A JSON-serializable dict containing the initial presence to set, or `None` to just appear
            `online`. See https://discordapp.com/developers/docs/topics/gateway#update-status for a description
            of this `update-status` payload object.
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
        shard_count:
            the shard count to use, or `None` if sharding is to be disabled (default).
        shard_id:
            the shard ID to use, or `None` if sharding is to be disabled (default).
        token:
            the token to use to authenticate with the gateway.

    Warning:
        It is highly recommended to not alter any attributes of this object whilst the gateway is running unless clearly
        specified otherwise. Any change to internal state may result in undefined behaviour or effects. This is designed
        to be a low-level interface to the gateway, and not a general-use object.
    """

    __slots__ = [
        "dispatch",
        "_connector",
        "_in_buffer",
        "_zlib_decompressor",
        "shard_count",
        "shard_id",
        "heartbeat_interval",
        "closed_event",
        "heartbeat_latency",
        "in_cid",
        "initial_presence",
        "large_threshold",
        "last_ack_received",
        "last_heartbeat_sent",
        "logger",
        "loop",
        "max_persistent_buffer_size",
        "out_cid",
        "rate_limit",
        "seq",
        "session_id",
        "started_at",
        "trace",
        "token",
        "uri",
        "ws",
        "version",
    ]

    #: The API version we should request the use of.
    _REQUESTED_VERSION = 7
    _NEVER_RECONNECT_CODES = (
        opcodes.GatewayClosure.AUTHENTICATION_FAILED,
        opcodes.GatewayClosure.INVALID_SHARD,
        opcodes.GatewayClosure.SHARDING_REQUIRED,
    )

    def __init__(
        self,
        host: str,
        *,
        connector=websockets.connect,
        dispatch: DispatchHandler = lambda t, d: None,
        initial_presence: typing.Optional[DiscordObject] = None,
        large_threshold: int = 50,
        loop: asyncio.AbstractEventLoop,
        max_persistent_buffer_size: int = 3 * 1024 ** 2,
        shard_id: typing.Optional[int] = None,
        shard_count: typing.Optional[int] = None,
        token: str,
    ) -> None:
        loop = _utils.assert_not_none(loop, "loop")

        #: The coroutine function to dispatch any events to.
        self.dispatch = asyncio.coroutine(dispatch)

        self._connector = connector
        self._in_buffer: bytearray = bytearray()
        self._zlib_decompressor: typing.Any = zlib.decompressobj()

        #: Number of shards in use, or `None` if not sharded.
        self.shard_count = shard_count
        #: Current shard ID, or `None` if not sharded.
        self.shard_id = shard_id

        #: The heartbeat interval. This is `float('nan')` until the gateway provides us a value to use on startup.
        self.heartbeat_interval = float("nan")
        #: An :class:`asyncio.Event` that will be triggered whenever the gateway disconnects.
        self.closed_event = asyncio.Event(loop=loop)
        #: The time period in seconds that the last heartbeat we sent took to be acknowledged by the gateway. This
        #: will be `float('inf')` until the first heartbeat is performed and acknowledged.
        self.heartbeat_latency = float("inf")
        #: Number of packets that have been received since startup.
        self.in_cid = 0
        #: The initial presence to use for the bot status once IDENTIFYing with the shard.
        self.initial_presence = initial_presence
        #: What we regard to be a large guild in member numbers.
        self.large_threshold = large_threshold
        #: The :func:`time.perf_counter` that the last heartbeat was acknowledged at. Is `float('nan')` until then.
        self.last_ack_received = float("nan")
        #: The :func:`time.perf_counter` that the last heartbeat was sent at. Is `float('nan')` until then.
        self.last_heartbeat_sent = float("nan")
        #: Logger adapter used to dump information to the console.
        self.logger = logging.getLogger(type(self).__name__)
        #: The event loop to use.
        self.loop: asyncio.AbstractEventLoop = loop
        #: What we consider to be a large size for the internal buffer. Any packet over this size results in the buffer
        #: being completely recreated.
        self.max_persistent_buffer_size = max_persistent_buffer_size
        #: Number of packets that have been sent since startup.
        self.out_cid = 0
        #: Rate limit bucket for the gateway.
        self.rate_limit = rates.TimedTokenBucket(120, 60, loop)
        #: The `seq` flag value, if there is one set.
        self.seq = None
        #: The session ID in use, if there is one set.
        self.session_id = None
        #: When the gateway connection was started
        self.started_at: typing.Optional[int] = None
        #: A list of gateway servers that are connected to, once connected.
        self.trace: typing.List[str] = []
        #: Token used to authenticate with the gateway.
        self.token = token.strip()
        #: The URI being connected to.
        self.uri = f"{host}?v={self._REQUESTED_VERSION}&encoding=json&compression=zlib-stream"
        #: The :class:`websockets.WebSocketClientProtocol` handling the low-level connection logic. Populated only while
        #: connected.
        self.ws: typing.Optional[websockets.WebSocketClientProtocol] = None
        #: Gateway protocol version. Starts as the requested version, updated once ready with the actual version being
        #: used.
        self.version = self._REQUESTED_VERSION

    @property
    def up_time(self) -> datetime.timedelta:
        """The length of time the gateway has been connected for, or 0 seconds if the client has not yet started."""
        if self.started_at is None:
            return datetime.timedelta(seconds=0)
        else:
            return datetime.timedelta(seconds=time.perf_counter() - self.started_at)

    @property
    def is_shard(self) -> bool:
        """True if this is considered a shard, false otherwise."""
        return self.shard_id is not None and self.shard_count is not None

    async def _trigger_resume(self, code: int, reason: str) -> "typing.NoReturn":
        """Trigger a `RESUME` operation. This will raise a :class:`ResumableConnectionClosed` exception."""
        await self.ws.close(code=code, reason=reason)
        raise _ResumeConnection(code=code, reason=reason)

    async def _trigger_identify(self, code: int, reason: str) -> "typing.NoReturn":
        """Trigger a re-`IDENTIFY` operation. This will raise a :class:`GatewayRequestedReconnection` exception."""
        await self.ws.close(code=code, reason=reason)
        raise _RestartConnection(code=code, reason=reason)

    async def _send_json(self, payload, skip_rate_limit) -> None:
        self.logger.debug(
            "sending payload %s and %s rate limit", payload, "skipping" if skip_rate_limit else "not skipping"
        )

        if not skip_rate_limit:
            await self.rate_limit.acquire(self._warn_about_internal_rate_limit)

        raw = json.dumps(payload)
        if len(raw) > 4096:
            self._handle_payload_oversize(payload)
        else:
            self.out_cid += 1
            await self.ws.send(raw)

    async def _receive_json(self) -> DiscordObject:
        msg = await self.ws.recv()

        if isinstance(msg, (bytes, bytearray)):
            self._in_buffer.extend(msg)
            while not self._in_buffer.endswith(b"\x00\x00\xff\xff"):
                msg = await self.ws.recv()
                self._in_buffer.extend(msg)

            msg = self._zlib_decompressor.decompress(self._in_buffer).decode("utf-8")

            # Prevent large packets persisting a massive buffer we never utilise.
            if len(self._in_buffer) > self.max_persistent_buffer_size:
                self._in_buffer = bytearray()
            else:
                self._in_buffer.clear()

        payload = json.loads(msg)

        if not isinstance(payload, dict):
            return await self._trigger_identify(code=opcodes.GatewayClosure.TYPE_ERROR, reason="Expected JSON object.")

        self.logger.debug("received payload %s", payload)
        self.in_cid += 1

        return payload

    def _warn_about_internal_rate_limit(self):
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
        while not self.closed_event.is_set():
            try:
                now = time.perf_counter()
                if self.last_heartbeat_sent + self.heartbeat_interval < now:
                    last_sent = now - self.last_heartbeat_sent
                    msg = f"Failed to receive an acknowledgement from the previous heartbeat sent ~{last_sent}s ago"
                    await self._trigger_resume(code=opcodes.GatewayClosure.PROTOCOL_VIOLATION, reason=msg)

                await asyncio.wait_for(self.closed_event.wait(), timeout=self.heartbeat_interval)
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
        self._dispatch("HELLO", d)

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
                "properties": {
                    "$os": _utils.system_type(),
                    "$browser": _utils.library_version(),
                    "$device": _utils.python_version(),
                },
            },
        }

        if self.initial_presence is not None:
            payload["d"]["status"] = self.initial_presence

        if self.is_shard:
            # noinspection PyTypeChecker
            payload["d"]["shard"] = [self.shard_id, self.shard_count]

        self.logger.info("sent IDENTIFY")
        await self._send_json(payload, False)

    async def _handle_dispatch(self, event: str, payload: DiscordObject) -> None:
        event == "READY" and await self._handle_ready(payload)
        event == "RESUMED" and await self._handle_resumed(payload)
        self.logger.debug("DISPATCH %s", event)
        self._dispatch(event, payload)

    async def _handle_ready(self, ready: DiscordObject) -> None:
        self.trace = ready["_trace"]
        self.session_id = ready["session_id"]
        self.version = ready["v"]
        self.logger.info("session %s is READY", self.session_id)
        self.logger.debug("trace for session %s is %s", self.session_id, self.trace)

    async def _handle_resumed(self, resumed: DiscordObject) -> None:
        self.trace = resumed["_trace"]
        self.logger.info("RESUMED successfully")
        self._dispatch("RESUME", None)

    async def _process_events(self) -> None:
        """Polls the gateway for new packets and handles dispatching the results."""
        while not self.closed_event.is_set():
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
            await self._trigger_identify(
                code=opcodes.GatewayClosure.NORMAL_CLOSURE, reason="you requested me to reconnect"
            )
        elif op == opcodes.GatewayOpcode.INVALID_SESSION:
            if d is True:
                self.logger.warning("will try to disconnect and RESUME")
                await self._trigger_resume(
                    code=opcodes.GatewayClosure.NORMAL_CLOSURE, reason="invalid session id so will resume"
                )
            else:
                self.logger.warning("will try to re-IDENTIFY")
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
            Results will be dispatched as events in chunks of 1000 members per guild.
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
        self, idle_since: typing.Optional[int], game: typing.Optional[DiscordObject], status: str, afk: bool
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
            :class:`errors.DiscordGatewayError`:
                if the token provided is invalidated.
            :class:`websockets.exceptions.ConnectionClosed`:
                if the connection is unexpectedly closed before we can start processing.
        """
        while not self.closed_event.is_set():
            await self.run_once()

    async def run_once(self, **kwargs) -> None:
        """
        Run the gateway once, then finish regardless of the closure reason.

        Args:
            **kwargs:
                Other arguments to pass to the websockets connect method.

        Raises:
            :class:`errors.DiscordGatewayError`:
                if the token provided is invalidated.
            :class:`websockets.exceptions.ConnectionClosed`:
                if the connection is unexpectedly closed before we can start processing.

        Note:
             By default, if the `uri`, `loop`, or `compression` options were not specified, then they default to
             the `uri` and `loop` stored in this object, and `None` for compression. Specifying these flags will allow
             you to override this behaviour if you need to, although you should not usually need to manipulate this.
        """
        kwargs.setdefault("uri", self.uri)
        kwargs.setdefault("loop", self.loop)
        kwargs.setdefault("compression", None)

        try:
            self.started_at = time.perf_counter()

            async with self._connector(**kwargs) as self.ws:
                try:
                    await self._receive_hello()
                    is_resume = self.seq is not None and self.session_id is not None
                    await (self._send_resume() if is_resume else self._send_identify())
                    await asyncio.gather(self._keep_alive(), self._process_events())
                except (_RestartConnection, _ResumeConnection, websockets.ConnectionClosed) as ex:
                    code, reason = opcodes.GatewayClosure(ex.code), ex.reason or "no reason"

                    if ex.code in self._NEVER_RECONNECT_CODES:
                        self.logger.critical("disconnected after %s [%s]. Please rectify issue manually", reason, code)
                        raise errors.GatewayError(code, reason) from ex

                    else:
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
        self.closed_event.set()
        block and await self.ws.wait_closed()

    def _dispatch(self, event_name: str, payload: typing.Optional[_utils.DiscordObject]) -> None:
        # This prevents us blocking any task such as the READY handler.
        self.loop.create_task(self.dispatch(event_name, payload))
