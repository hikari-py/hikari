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
import logging
import math
import platform
import time
import typing
import zlib

import aiohttp

from hikari.net import errors
from hikari.net import ratelimits
from hikari.internal_utilities import meta

if typing.TYPE_CHECKING:
    from hikari.internal_utilities import type_hints


@meta.incubating()
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


class GatewayClient:
    __slots__ = (
        "closed_event",
        "compression",
        "connected_at",
        "connector",
        "debug",
        "dispatch",
        "intents",
        "large_threshold",
        "json_deserialize",
        "json_serialize",
        "last_heartbeat_sent",
        "last_heartbeat_ack_received",
        "last_ping_sent",
        "last_pong_received",
        "logger",
        "presence",
        "proxy_auth",
        "proxy_headers",
        "proxy_url",
        "ratelimiter",
        "receive_timeout",
        "reconnect_count",
        "session",
        "session_id",
        "seq",
        "shard_id",
        "shard_count",
        "ssl_context",
        "token",
        "url",
        "verify_ssl",
        "ws",
        "zlib",
    )

    def __init__(
        self,
        *,
        compression=True,
        connector=None,
        debug: bool = False,
        dispatch=lambda gw, e, p: None,
        initial_presence=None,
        intents: type_hints.NotRequired[GatewayIntent] = None,
        json_deserialize=json.loads,
        json_serialize=json.dumps,
        large_threshold=1_000,
        proxy_auth=None,
        proxy_headers=None,
        proxy_url=None,
        receive_timeout=10.0,
        session_id=None,
        seq=None,
        shard_id=0,
        shard_count=1,
        ssl_context=None,
        token,
        url,
        verify_ssl=True,
    ):
        self.closed_event = asyncio.Event()
        self.compression = compression
        self.connected_at = float("nan")
        self.connector = connector
        self.debug = debug
        self.dispatch = dispatch
        self.intents = intents
        self.large_threshold = large_threshold
        self.json_deserialize = json_deserialize
        self.json_serialize = json_serialize
        self.last_heartbeat_sent = float("nan")
        self.last_heartbeat_ack_received = float("nan")
        self.last_ping_sent = float("nan")
        self.last_pong_received = float("nan")
        self.presence = initial_presence
        self.proxy_auth = proxy_auth
        self.proxy_headers = proxy_headers
        self.proxy_url = proxy_url
        self.receive_timeout = receive_timeout
        self.reconnect_count = 0
        self.session = None
        self.session_id = session_id
        self.seq = seq
        self.shard_id = shard_id if shard_id is not None and shard_count is not None else 0
        self.shard_count = shard_count if shard_id is not None and shard_count is not None else 1
        self.ssl_context = ssl_context
        self.token = token
        self.verify_ssl = verify_ssl
        self.ws = None
        self.zlib = None  # set this per connection or reconnecting can mess up.

        name = f"hikari.{type(self).__name__}"
        if shard_count > 1:
            name += f"{shard_id}"
        self.logger = logging.getLogger(name)

        url = f"{url}?v=6&encoding=json"
        if compression:
            url += "&compress=zlib-stream"
        self.url = url

        self.ratelimiter = ratelimits.WindowedBurstRateLimiter(f"gateway shard {shard_id}/{shard_count}", 60.0, 120)

    @property
    def latency(self):
        return self.last_pong_received - self.last_ping_sent

    @property
    def heartbeat_latency(self):
        return self.last_heartbeat_ack_received - self.last_heartbeat_sent

    @property
    def uptime(self):
        delta = time.perf_counter() - self.connected_at
        return datetime.timedelta(seconds=0 if math.isnan(delta) else delta)

    @property
    def is_connected(self):
        return not math.isnan(self.connected_at)

    async def connect(self):
        try:
            self.session = aiohttp.ClientSession(connector=self.connector)
            self.ws = await self.session.ws_connect(
                self.url,
                receive_timeout=self.receive_timeout,
                compress=0,
                autoping=False,
                max_msg_size=0,
                proxy=self.proxy_url,
                proxy_auth=self.proxy_auth,
                proxy_headers=self.proxy_headers,
                verify_ssl=self.verify_ssl,
                ssl_context=self.ssl_context,
                timeout=self.receive_timeout,
            )

            self.zlib = zlib.decompressobj()

            self.connected_at = time.perf_counter()
            self.last_pong_received = self.connected_at
            self.last_heartbeat_ack_received = self.connected_at

            # Parse HELLO
            self.logger.debug("expecting HELLO")
            pl = await self.receive()
            op = pl["op"]
            if op != 10:
                raise errors.GatewayError(f"Expected HELLO opcode 10 but received {op}")
            hb_interval = pl["d"]["heartbeat_interval"] / 1_000.0

            self.dispatch(self, "RECONNECT" if self.reconnect_count else "CONNECT", None)
            self.logger.info("received HELLO, interval is %ss", hb_interval)

            completed, pending_tasks = await asyncio.wait(
                [self.ping_keep_alive(), self.heartbeat_keep_alive(hb_interval), self.handshake_and_poll_events()],
                return_when=asyncio.FIRST_COMPLETED
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

            raise ex

        finally:
            self.logger.debug("closing websocket")
            with contextlib.suppress(AttributeError):
                await self.ws.close()
            self.logger.debug("closing session")
            with contextlib.suppress(AttributeError):
                await self.session.close()
            self.connected_at = float("nan")
            self.last_ping_sent = float("nan")
            self.last_pong_received = float("nan")
            self.last_heartbeat_sent = float("nan")
            self.last_heartbeat_ack_received = float("nan")
            self.reconnect_count += 1
            self.closed_event.clear()
            self.dispatch(self, "DISCONNECT", None)

    async def handshake_and_poll_events(self):
        if self.session_id is None:
            await self.identify()
            self.logger.info("sent IDENTIFY, ready to listen to incoming events")
        else:
            await self.resume()
            self.logger.info("sent RESUME, ready to listen to incoming events")
        await self.poll_events()

    def identify(self):
        self.logger.debug("sending IDENTIFY")
        pl = {
            "op": 2,
            "d": {
                "token": self.token,
                "compress": False,
                "large_threshold": self.large_threshold,
                "properties": {
                    "$os": " ".join((platform.system(), platform.release(),)),
                    "$browser": "hikari/1.0.0a1",
                    "$device": " ".join(
                        (platform.python_implementation(), platform.python_revision(), platform.python_version(),)
                    ),
                },
                "shard": [self.shard_id, self.shard_count],
            },
        }

        # Do not always add this option; if it is None, exclude it for now. According to Mason,
        # we can only use intents at the time of writing if our bot has less than 100 guilds.
        # This means we need to give the user the option to opt in to this rather than breaking their
        # bot with it if they have 100+ guilds. This restriction will be removed eventually.
        if self.intents is not None:
            pl["d"]["intents"] = self.intents

        if self.presence:
            pl["d"]["presence"] = self.presence
        return self.send(pl)

    def resume(self):
        self.logger.debug("sending RESUME")
        pl = {
            "op": 6,
            "d": {"token": self.token, "seq": self.seq, "session_id": self.session_id,},
        }
        return self.send(pl)

    async def ping_keep_alive(self):
        while not self.closed_event.is_set():
            if self.last_pong_received < self.last_ping_sent:
                raise errors.GatewayZombiedError()
            self.logger.debug("sending ping")
            await self.ws.ping()
            self.last_ping_sent = time.perf_counter()
            try:
                await asyncio.wait_for(self.closed_event.wait(), timeout=0.75 * self.receive_timeout)
            except asyncio.TimeoutError:
                pass

    async def heartbeat_keep_alive(self, heartbeat_interval):
        while not self.closed_event.is_set():
            if self.last_heartbeat_ack_received < self.last_heartbeat_sent:
                raise errors.GatewayZombiedError()
            self.logger.debug("sending heartbeat")
            await self.send({"op": 1, "d": self.seq})
            self.last_heartbeat_sent = time.perf_counter()
            try:
                await asyncio.wait_for(self.closed_event.wait(), timeout=heartbeat_interval)
            except asyncio.TimeoutError:
                pass

    async def poll_events(self):
        while True:
            next_pl = await self.receive()

            op = next_pl["op"]
            d = next_pl["d"]

            if op == 0:
                self.seq = next_pl["s"]
                event_name = next_pl["t"]
                self.dispatch(self, event_name, d)
            elif op == 1:
                await self.send({"op": 11})
            elif op == 7:
                self.logger.debug("instructed by gateway server to restart connection")
                raise errors.GatewayMustReconnectError()
            elif op == 9:
                resumable = bool(d)
                self.logger.debug(
                    "instructed by gateway server to %s session", "resume" if resumable else "restart",
                )
                raise errors.GatewayInvalidSessionError(resumable)
            elif op == 11:
                self.last_heartbeat_ack_received = time.perf_counter()
                ack_wait = self.last_heartbeat_ack_received - self.last_heartbeat_sent
                self.logger.debug("received HEARTBEAT ACK in %ss", ack_wait)
            else:
                self.logger.debug("ignoring opcode %s with data %r", op, d)

    async def close(self):
        if not self.closed_event.is_set():
            self.closed_event.set()
        if self.ws is not None:
            await self.ws.close()

    async def receive(self):
        while True:
            message = await self.ws.receive()
            if message.type == aiohttp.WSMsgType.TEXT:
                obj = self.json_deserialize(message.data)

                if self.debug:
                    self.logger.debug("receive text payload %r", message.data)
                else:
                    self.logger.debug(
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
                    message = await self.ws.receive()
                    if message.type != aiohttp.WSMsgType.BINARY:
                        raise errors.GatewayError(f"Expected a binary message but got {message.type}")
                    buffer.extend(message.data)

                pl = self.zlib.decompress(buffer)
                obj = self.json_deserialize(pl)

                if self.debug:
                    self.logger.debug("receive %s zlib-encoded packets containing payload %r", packets, pl)
                else:
                    self.logger.debug(
                        "receive zlib payload (op:%s, t:%s, s:%s, size:%s, packets:%s)",
                        obj.get("op"),
                        obj.get("t"),
                        obj.get("s"),
                        len(pl),
                        packets,
                    )
                return obj
            elif message.type == aiohttp.WSMsgType.PING:
                self.logger.debug("receive ping")
                await self.ws.pong()
                self.logger.debug("sent pong")
            elif message.type == aiohttp.WSMsgType.PONG:
                self.last_pong_received = time.perf_counter()
                self.logger.debug("receive pong after %ss", self.last_pong_received - self.last_ping_sent)
            elif message.type == aiohttp.WSMsgType.CLOSE:
                close_code = self.ws.close_code
                self.logger.debug("connection closed with code %s", close_code)
                if close_code == errors.GatewayCloseCode.AUTHENTICATION_FAILED:
                    raise errors.GatewayInvalidTokenError()
                elif close_code in (errors.GatewayCloseCode.SESSION_TIMEOUT, errors.GatewayCloseCode.INVALID_SEQ):
                    raise errors.GatewayInvalidSessionError(False)
                elif close_code == errors.GatewayCloseCode.SHARDING_REQUIRED:
                    raise errors.GatewayNeedsShardingError()
                else:
                    raise errors.GatewayConnectionClosedError(close_code)
            elif message.type in (aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSED):
                self.logger.debug("connection has already closed, so giving up")
                raise errors.GatewayClientClosedError()
            elif message.type == aiohttp.WSMsgType.ERROR:
                ex = self.ws.exception()
                self.logger.debug("connection encountered some error", exc_info=ex)
                raise errors.GatewayError("Unexpected exception occurred") from ex

    async def send(self, payload):
        payload_str = self.json_serialize(payload)

        if len(payload_str) > 4096:
            raise errors.GatewayError(
                f"Tried to send a payload greater than 4096 bytes in size (was actually {len(payload_str)}"
            )

        await self.ratelimiter.acquire()
        await self.ws.send_str(payload_str)

        if self.debug:
            self.logger.debug("sent payload %s", payload_str)
        else:
            self.logger.debug("sent payload (op:%s, size:%s)", payload.get("op"), len(payload_str))

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

        self.logger.debug(
            "requesting guild members for guilds %s with constraints %s", guilds, constraints,
        )

        await self.send({"op": 8, "d": {"guild_id": guilds, **constraints,}})

    async def update_status(self, presence) -> None:
        self.logger.debug("updating presence to %r", presence)
        await self.send(presence)
        self.presence = presence

    def __str__(self):
        state = "Connected" if self.is_connected else "Disconnected"
        return f"{state} gateway connection to {self.url} at shard {self.shard_id}/{self.shard_count}"

    def __repr__(self):
        this_type = type(self).__name__
        major_attributes = ", ".join(
            (
                f"is_connected={self.is_connected!r}",
                f"latency={self.latency!r}",
                f"heartbeat_latency={self.heartbeat_latency!r}",
                f"presence={self.presence!r}",
                f"shard_id={self.shard_id!r}",
                f"shard_count={self.shard_count!r}",
                f"seq={self.seq!r}",
                f"session_id={self.session_id!r}",
                f"uptime={self.uptime!r}",
                f"url={self.url!r}",
            )
        )

        return f"{this_type}({major_attributes})"

    def __bool__(self):
        return self.is_connected
