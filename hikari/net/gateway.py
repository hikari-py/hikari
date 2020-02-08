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
Single-threaded asyncio V6 Gateway implementation. Handles regular heartbeating in a background task
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
import enum
import json
import math
import time
import typing
import urllib.parse
import zlib

import aiohttp

from hikari.internal_utilities import loggers
from hikari.net import errors
from hikari.net import ratelimits
from hikari.net import user_agent

if typing.TYPE_CHECKING:
    from hikari.internal_utilities import type_hints


class GatewayIntent(enum.IntFlag):
    """
    Represents an intent on the gateway. This is a bitfield representation of all the categories of event
    that you wish to receive.

    Any events not in an intent category will be fired regardless of what intents you provide.

    Note:
        This will currently have no effect on the gateway until the solution is implemented on Discord's
        gateway. Discussion of proposed interface can be found at
        https://gist.github.com/msciotti/223272a6f976ce4fda22d271c23d72d9.
    """

    #: Subscribes to the following events:
    #:     - GUILD_CREATE
    #:     - GUILD_DELETE
    #:     - GUILD_ROLE_CREATE
    #:     - GUILD_ROLE_UPDATE
    #:     - GUILD_ROLE_DELETE
    #:     - CHANNEL_CREATE
    #:     - CHANNEL_UPDATE
    #:     - CHANNEL_DELETE
    #:     - CHANNEL_PINS_UPDATE
    GUILDS = 1 << 0

    #: Subscribes to the following events:
    #:     - GUILD_MEMBER_ADD
    #:     - GUILD_MEMBER_UPDATE
    #:     - GUILD_MEMBER_REMOVE
    GUILD_MEMBERS = 1 << 1

    #: Subscribes to the following events:
    #:     - GUILD_BAN_ADD
    #:     - GUILD_BAN_REMOVE
    GUILD_BANS = 1 << 2

    #: Subscribes to the following events:
    #:     - GUILD_EMOJIS_UPDATE
    GUILD_EMOJIS = 1 << 3

    #: Subscribes to the following events:
    #:     - GUILD_INTEGRATIONS_UPDATE
    GUILD_INTEGRATIONS = 1 << 4

    #: Subscribes to the following events:
    #:     - WEBHOOKS_UPDATE
    GUILD_WEBHOOKS = 1 << 5

    #: Subscribes to the following events:
    #:    - INVITE_CREATE
    #:    - INVITE_DELETE
    GUILD_INVITES = 1 << 6

    #: Subscribes to the following events:
    #:    - VOICE_STATE_UPDATE
    GUILD_VOICE_STATES = 1 << 7

    #: Subscribes to the following events:
    #:    - PRESENCE_UPDATE
    GUILD_PRESENCES = 1 << 8

    #: Subscribes to the following events:
    #:    - MESSAGE_CREATE
    #:    - MESSAGE_UPDATE
    #:    - MESSAGE_DELETE
    GUILD_MESSAGES = 1 << 9

    #: Subscribes to the following events:
    #:    - MESSAGE_REACTION_ADD
    #:    - MESSAGE_REACTION_REMOVE
    #:    - MESSAGE_REACTION_REMOVE_ALL
    #:    - MESSAGE_REACTION_REMOVE_EMOJI
    GUILD_MESSAGE_REACTIONS = 1 << 10

    #: Subscribes to the following events:
    #:    - TYPING_START
    GUILD_MESSAGE_TYPING = 1 << 11

    #: Subscribes to the following events:
    #:    - CHANNEL_CREATE
    #:    - MESSAGE_CREATE
    #:    - MESSAGE_UPDATE
    #:    - MESSAGE_DELETE
    DIRECT_MESSAGES = 1 << 12

    #: Subscribes to the following events:
    #:    - MESSAGE_REACTION_ADD
    #:    - MESSAGE_REACTION_REMOVE
    #:    - MESSAGE_REACTION_REMOVE_ALL
    DIRECT_MESSAGE_REACTIONS = 1 << 13

    #: Subscribes to the following events:
    #:    - TYPING_START
    DIRECT_MESSAGE_TYPING = 1 << 14


class GatewayStatus(str, enum.Enum):
    OFFLINE = "offline"
    CONNECTING = "connecting"
    WAITING_FOR_HELLO = "waiting for HELLO"
    IDENTIFYING = "identifying"
    RESUMING = "resuming"
    SHUTTING_DOWN = "shutting down"
    WAITING_FOR_MESSAGES = "waiting for messages"
    PROCESSING_NEW_MESSAGE = "processing message"


class GatewayClient:
    __slots__ = (
        "closed_event",
        "_compression",
        "_connected_at",
        "_connector",
        "_debug",
        "disconnect_count",
        "dispatch",
        "heartbeat_interval",
        "heartbeat_latency",
        "hello_event",
        "identify_event",
        "_intents",
        "_large_threshold",
        "_json_deserialize",
        "_json_serialize",
        "last_heartbeat_sent",
        "last_message_received",
        "_logger",
        "_presence",
        "_proxy_auth",
        "_proxy_headers",
        "_proxy_url",
        "_ratelimiter",
        "requesting_close_event",
        "_session",
        "session_id",
        "seq",
        "shard_id",
        "shard_count",
        "_ssl_context",
        "status",
        "_token",
        "_url",
        "_verify_ssl",
        "_ws",
        "_zlib",
    )

    def __init__(
        self,
        *,
        compression=True,
        connector=None,
        debug: bool = False,
        dispatch=lambda gw, e, p: None,
        initial_presence=None,
        intents: type_hints.Nullable[GatewayIntent] = None,
        json_deserialize=json.loads,
        json_serialize=json.dumps,
        large_threshold=250,
        proxy_auth=None,
        proxy_headers=None,
        proxy_url=None,
        session_id=None,
        seq=None,
        shard_id=0,
        shard_count=1,
        ssl_context=None,
        token,
        url,
        verify_ssl=True,
    ) -> None:
        self._compression = compression
        self.closed_event = asyncio.Event()
        self._connected_at = float("nan")
        self._connector = connector
        self._debug = debug
        self.disconnect_count = 0
        self.dispatch = dispatch
        self.heartbeat_interval = float("nan")
        self.heartbeat_latency = float("nan")
        self.hello_event = asyncio.Event()
        self.identify_event = asyncio.Event()
        self._intents = intents
        self._large_threshold = large_threshold
        self._json_deserialize = json_deserialize
        self._json_serialize = json_serialize
        self.last_heartbeat_sent = float("nan")
        self.last_message_received = float("nan")
        self._presence = initial_presence
        self._proxy_auth = proxy_auth
        self._proxy_headers = proxy_headers
        self._proxy_url = proxy_url
        self.requesting_close_event = asyncio.Event()
        self._session = None
        self.session_id = session_id
        self.seq = seq
        self.shard_id = shard_id if shard_id is not None and shard_count is not None else 0
        self.shard_count = shard_count if shard_id is not None and shard_count is not None else 1
        self._ssl_context = ssl_context
        self.status = GatewayStatus.OFFLINE
        self._token = token
        self._verify_ssl = verify_ssl
        self._ws: typing.Optional[aiohttp.ClientWebSocketResponse] = None
        self._zlib = None  # set this per connection or reconnecting can mess up.

        self._ratelimiter = ratelimits.WindowedBurstRateLimiter(
            f"gateway shard {self.shard_id}/{self.shard_count}", 60.0, 120,
        )

        self._logger = loggers.get_named_logger(self, self.shard_id)

        # Sanitise the URL...
        scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(url, allow_fragments=True)

        # We use JSON; I'm not having any of that erlang shit in my library!
        new_query = dict(v=6, encoding="json")
        if compression:
            new_query["compress"] = "zlib-stream"

        self._url = urllib.parse.urlunparse(
            (
                scheme,
                netloc,
                path,
                params,
                urllib.parse.urlencode(new_query),  # replace query with the correct one.
                "",  # no fragment
            )
        )

    @property
    def uptime(self) -> datetime.timedelta:
        delta = time.perf_counter() - self._connected_at
        return datetime.timedelta(seconds=0 if math.isnan(delta) else delta)

    @property
    def is_connected(self) -> bool:
        """
        Returns :class:`True` if this gateway client is actively connected to something, or
        :class:`False` if it is not running.
        """
        return not math.isnan(self._connected_at)

    @property
    def reconnect_count(self) -> int:
        # 0 disconnects + not is_connected => 0
        # 0 disconnects + is_connected => 0
        # 1 disconnects + not is_connected = 0
        # 1 disconnects + is_connected = 1
        # 2 disconnects + not is_connected = 1
        # 2 disconnects + is_connected = 2
        return max(0, self.disconnect_count - int(not self.is_connected))

    async def request_guild_members(
        self, guild_id, *guild_ids, **kwargs,
    ):
        guilds = [guild_id, *guild_ids]
        constraints = {}

        if "presences" in kwargs:
            constraints["presences"] = kwargs["presences"]

        if "user_ids" in kwargs:
            constraints["user_ids"] = kwargs["user_ids"]
        else:
            constraints["query"] = kwargs.get("query", "")
            constraints["limit"] = kwargs.get("limit", 0)

        self._logger.debug(
            "requesting guild members for guilds %s with constraints %s", guilds, constraints,
        )

        await self._send({"op": 8, "d": {"guild_id": guilds, **constraints}})

    async def update_status(self, presence) -> None:
        self._logger.debug("updating presence to %r", presence)
        await self._send(presence)
        self._presence = presence

    async def close(self, close_code: int = 1000):
        if not self.requesting_close_event.is_set():
            self.status = GatewayStatus.SHUTTING_DOWN
            self.requesting_close_event.set()
            # These will attribute error if they are not set; in this case we don't care, just ignore it.
            with contextlib.suppress(asyncio.TimeoutError, AttributeError):
                await asyncio.wait_for(asyncio.shield(self._ws.close(code=close_code)), timeout=2.0)
            with contextlib.suppress(asyncio.TimeoutError, AttributeError):
                await asyncio.wait_for(asyncio.shield(self._session.close()), timeout=2.0)
            self.closed_event.set()

    async def connect(self, client_session_type=aiohttp.ClientSession):
        if self.is_connected:
            raise RuntimeError("Already connected")

        self.closed_event.clear()
        self.hello_event.clear()
        self.identify_event.clear()
        self.requesting_close_event.clear()

        self._session = client_session_type(**self._cs_init_kwargs)
        close_code = 1006  # Abnormal closure

        try:
            self.status = GatewayStatus.CONNECTING
            self._ws = await self._session.ws_connect(**self._ws_connect_kwargs)
            self.status = GatewayStatus.WAITING_FOR_HELLO

            self._connected_at = time.perf_counter()
            self._zlib = zlib.decompressobj()
            self._logger.debug("expecting HELLO")
            pl = await self._receive()

            op = pl["op"]
            if op != 10:
                raise errors.GatewayError(f"Expected HELLO opcode 10 but received {op}")

            self.heartbeat_interval = pl["d"]["heartbeat_interval"] / 1_000.0

            self.hello_event.set()

            self.dispatch(self, "RECONNECT" if self.disconnect_count else "CONNECT", None)
            self._logger.info("received HELLO, interval is %ss", self.heartbeat_interval)

            completed, pending_tasks = await asyncio.wait(
                [self._heartbeat_keep_alive(self.heartbeat_interval), self._identify_or_resume_then_poll_events()],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Kill other running tasks now.
            for pending_task in pending_tasks:
                pending_task.cancel()

            ex = completed.pop().exception()

            if ex is None:
                # If no exception occurred, we must have exited non-exceptionally, indicating
                # the close event was set without an error causing that flag to be changed.
                ex = errors.GatewayClientClosedError()
            elif isinstance(ex, asyncio.TimeoutError):
                # If we get timeout errors receiving stuff, propagate as a zombied connection. This
                # is already done by the ping keepalive and heartbeat keepalive partially, but this
                # is a second edge case.
                ex = errors.GatewayZombiedError()

            if isinstance(ex, errors.GatewayError):
                close_code = ex.close_code

            raise ex
        finally:
            await self.close(close_code)
            self.closed_event.set()
            self.status = GatewayStatus.OFFLINE
            self._connected_at = float("nan")
            self.last_heartbeat_sent = float("nan")
            self.heartbeat_latency = float("nan")
            self.last_message_received = float("nan")
            self.disconnect_count += 1
            self._ws = None
            await self._session.close()
            self._session = None
            self.dispatch(self, "DISCONNECT", None)

    @property
    def _ws_connect_kwargs(self):
        return dict(
            url=self._url,
            compress=0,
            autoping=True,
            max_msg_size=0,
            proxy=self._proxy_url,
            proxy_auth=self._proxy_auth,
            proxy_headers=self._proxy_headers,
            verify_ssl=self._verify_ssl,
            ssl_context=self._ssl_context,
        )

    @property
    def _cs_init_kwargs(self):
        return dict(connector=self._connector)

    async def _identify_or_resume_then_poll_events(self):
        if self.session_id is None:
            self.status = GatewayStatus.IDENTIFYING
            self._logger.debug("sending IDENTIFY")
            pl = {
                "op": 2,
                "d": {
                    "token": self._token,
                    "compress": False,
                    "large_threshold": self._large_threshold,
                    "properties": {
                        "$os": user_agent.system_type(),
                        "$browser": user_agent.library_version(),
                        "$device": user_agent.python_version(),
                    },
                    "shard": [self.shard_id, self.shard_count],
                },
            }

            # Do not always add this option; if it is None, exclude it for now. According to Mason,
            # we can only use intents at the time of writing if our bot has less than 100 guilds.
            # This means we need to give the user the option to opt in to this rather than breaking their
            # bot with it if they have 100+ guilds. This restriction will be removed eventually.
            if self._intents is not None:
                pl["d"]["intents"] = self._intents

            if self._presence:
                pl["d"]["presence"] = self._presence
            await self._send(pl)
            self._logger.info("sent IDENTIFY, ready to listen to incoming events")
        else:
            self.status = GatewayStatus.RESUMING
            self._logger.debug("sending RESUME")
            pl = {
                "op": 6,
                "d": {"token": self._token, "seq": self.seq, "session_id": self.session_id},
            }
            await self._send(pl)
            self._logger.info("sent RESUME, ready to listen to incoming events")

        self.identify_event.set()
        await self._poll_events()

    async def _heartbeat_keep_alive(self, heartbeat_interval):
        while not self.requesting_close_event.is_set():
            if self.last_message_received < self.last_heartbeat_sent:
                raise asyncio.TimeoutError(
                    f"{self.shard_id}: connection is a zombie, haven't received HEARTBEAT ACK for too long"
                )
            self._logger.debug("sending heartbeat")
            await self._send({"op": 1, "d": self.seq})
            self.last_heartbeat_sent = time.perf_counter()
            try:
                await asyncio.wait_for(self.requesting_close_event.wait(), timeout=heartbeat_interval)
            except asyncio.TimeoutError:
                pass

    async def _poll_events(self):
        while not self.requesting_close_event.is_set():
            self.status = GatewayStatus.WAITING_FOR_MESSAGES
            next_pl = await self._receive()
            self.status = GatewayStatus.PROCESSING_NEW_MESSAGE

            op = next_pl["op"]
            d = next_pl["d"]

            if op == 0:
                self.seq = next_pl["s"]
                event_name = next_pl["t"]
                self.dispatch(self, event_name, d)
            elif op == 1:
                await self._send({"op": 11})
            elif op == 7:
                self._logger.debug("instructed by gateway server to restart connection")
                raise errors.GatewayMustReconnectError()
            elif op == 9:
                can_resume = bool(d)
                self._logger.info(
                    "instructed by gateway server to %s session", "resume" if can_resume else "restart",
                )
                raise errors.GatewayInvalidSessionError(can_resume)
            elif op == 11:
                now = time.perf_counter()
                self.heartbeat_latency = now - self.last_heartbeat_sent
                self._logger.debug("received HEARTBEAT ACK in %ss", self.heartbeat_latency)
            else:
                self._logger.debug("ignoring opcode %s with data %r", op, d)

    async def _receive(self):
        while True:
            message = await self._receive_one_packet()
            if message.type == aiohttp.WSMsgType.TEXT:
                obj = self._json_deserialize(message.data)

                if self._debug:
                    self._logger.debug("receive text payload %r", message.data)
                else:
                    self._logger.debug(
                        "receive text payload (op:%s, t:%s, s:%s, size:%s)",
                        obj.get("op"),
                        obj.get("t"),
                        obj.get("s"),
                        len(message.data),
                    )
                return obj
            elif message.type == aiohttp.WSMsgType.BINARY:
                buffer = bytearray(message.data)
                packets = 1
                while not buffer.endswith(b"\x00\x00\xff\xff"):
                    packets += 1
                    message = await self._receive_one_packet()
                    if message.type != aiohttp.WSMsgType.BINARY:
                        raise errors.GatewayError(f"Expected a binary message but got {message.type}")
                    buffer.extend(message.data)

                pl = self._zlib.decompress(buffer)
                obj = self._json_deserialize(pl)

                if self._debug:
                    self._logger.debug("receive %s zlib-encoded packets containing payload %r", packets, pl)
                else:
                    self._logger.debug(
                        "receive zlib payload (op:%s, t:%s, s:%s, size:%s, packets:%s)",
                        obj.get("op"),
                        obj.get("t"),
                        obj.get("s"),
                        len(pl),
                        packets,
                    )
                return obj
            elif message.type == aiohttp.WSMsgType.CLOSE:
                close_code = self._ws.close_code
                self._logger.debug("connection closed with code %s", close_code)
                if close_code == errors.GatewayCloseCode.AUTHENTICATION_FAILED:
                    raise errors.GatewayInvalidTokenError()
                elif close_code in (errors.GatewayCloseCode.SESSION_TIMEOUT, errors.GatewayCloseCode.INVALID_SEQ):
                    raise errors.GatewayInvalidSessionError(False)
                elif close_code == errors.GatewayCloseCode.SHARDING_REQUIRED:
                    raise errors.GatewayNeedsShardingError()
                else:
                    raise errors.GatewayConnectionClosedError(close_code)
            elif message.type in (aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSED):
                self._logger.debug("connection has been marked as closed")
                raise errors.GatewayClientClosedError()
            elif message.type == aiohttp.WSMsgType.ERROR:
                ex = self._ws.exception()
                self._logger.debug("connection encountered some error", exc_info=ex)
                raise errors.GatewayError("Unexpected exception occurred") from ex

    async def _receive_one_packet(self):
        packet = await self._ws.receive()
        self.last_message_received = time.perf_counter()
        return packet

    async def _send(self, payload):
        payload_str = self._json_serialize(payload)

        if len(payload_str) > 4096:
            raise errors.GatewayError(
                f"Tried to send a payload greater than 4096 bytes in size (was actually {len(payload_str)}"
            )

        await self._ratelimiter.acquire()
        await self._ws.send_str(payload_str)

        if self._debug:
            self._logger.debug("sent payload %s", payload_str)
        else:
            self._logger.debug("sent payload (op:%s, size:%s)", payload.get("op"), len(payload_str))

    def __str__(self):
        state = "Connected" if self.is_connected else "Disconnected"
        return f"{state} gateway connection to {self._url} at shard {self.shard_id}/{self.shard_count}"

    def __repr__(self):
        this_type = type(self).__name__
        major_attributes = ", ".join(
            (
                f"is_connected={self.is_connected!r}",
                f"heartbeat_latency={self.heartbeat_latency!r}",
                f"presence={self._presence!r}",
                f"shard_id={self.shard_id!r}",
                f"shard_count={self.shard_count!r}",
                f"seq={self.seq!r}",
                f"session_id={self.session_id!r}",
                f"uptime={self.uptime!r}",
                f"url={self._url!r}",
            )
        )

        return f"{this_type}({major_attributes})"

    def __bool__(self):
        return self.is_connected
