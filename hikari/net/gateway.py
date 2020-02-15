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

Can be used as the main gateway connection for a single-sharded bot, or the gateway connection for a
specific shard in a swarm of shards making up a larger bot.

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
import ssl
import time
import typing
import urllib.parse
import zlib

import aiohttp.typedefs

from hikari.internal_utilities import containers
from hikari.internal_utilities import loggers
from hikari.internal_utilities import type_hints
from hikari.net import errors
from hikari.net import ratelimits
from hikari.net import user_agent
from hikari.net import versions

if typing.TYPE_CHECKING:
    import logging


class GatewayIntent(enum.IntFlag):
    """
    Represents an intent on the gateway. This is a bitfield representation of all the categories of event
    that you wish to receive.

    Any events not in an intent category will be fired regardless of what intents you provide.


    Warning:
        If you are using the V7 Gateway, you will be REQUIRED to provide some form of intent value when
        you connect. Failure to do so may result in immediate termination of the session server-side.
    """

    #: Subscribes to the following events:
    #: * GUILD_CREATE
    #: * GUILD_DELETE
    #: * GUILD_ROLE_CREATE
    #: * GUILD_ROLE_UPDATE
    #: * GUILD_ROLE_DELETE
    #: * CHANNEL_CREATE
    #: * CHANNEL_UPDATE
    #: * CHANNEL_DELETE
    #: * CHANNEL_PINS_UPDATE
    GUILDS = 1 << 0

    #: Subscribes to the following events:
    #: * GUILD_MEMBER_ADD
    #: * GUILD_MEMBER_UPDATE
    #: * GUILD_MEMBER_REMOVE
    GUILD_MEMBERS = 1 << 1

    #: Subscribes to the following events:
    #: * GUILD_BAN_ADD
    #: * GUILD_BAN_REMOVE
    GUILD_BANS = 1 << 2

    #: Subscribes to the following events:
    #: * GUILD_EMOJIS_UPDATE
    GUILD_EMOJIS = 1 << 3

    #: Subscribes to the following events:
    #: * GUILD_INTEGRATIONS_UPDATE
    GUILD_INTEGRATIONS = 1 << 4

    #: Subscribes to the following events:
    #: * WEBHOOKS_UPDATE
    GUILD_WEBHOOKS = 1 << 5

    #: Subscribes to the following events:
    #: * INVITE_CREATE
    #: * INVITE_DELETE
    GUILD_INVITES = 1 << 6

    #: Subscribes to the following events:
    #: * VOICE_STATE_UPDATE
    GUILD_VOICE_STATES = 1 << 7

    #: Subscribes to the following events:
    #: * PRESENCE_UPDATE
    GUILD_PRESENCES = 1 << 8

    #: Subscribes to the following events:
    #: * MESSAGE_CREATE
    #: * MESSAGE_UPDATE
    #: * MESSAGE_DELETE
    GUILD_MESSAGES = 1 << 9

    #: Subscribes to the following events:
    #: * MESSAGE_REACTION_ADD
    #: * MESSAGE_REACTION_REMOVE
    #: * MESSAGE_REACTION_REMOVE_ALL
    #: * MESSAGE_REACTION_REMOVE_EMOJI
    GUILD_MESSAGE_REACTIONS = 1 << 10

    #: Subscribes to the following events:
    #: * TYPING_START
    GUILD_MESSAGE_TYPING = 1 << 11

    #: Subscribes to the following events:
    #: * CHANNEL_CREATE
    #: * MESSAGE_CREATE
    #: * MESSAGE_UPDATE
    #: * MESSAGE_DELETE
    DIRECT_MESSAGES = 1 << 12

    #: Subscribes to the following events:
    #: * MESSAGE_REACTION_ADD
    #: * MESSAGE_REACTION_REMOVE
    #: * MESSAGE_REACTION_REMOVE_ALL
    DIRECT_MESSAGE_REACTIONS = 1 << 13

    #: Subscribes to the following events
    #: * TYPING_START
    DIRECT_MESSAGE_TYPING = 1 << 14


class GatewayStatus(str, enum.Enum):
    """
    Various states that a gateway connection can be in.
    """

    OFFLINE = "offline"
    CONNECTING = "connecting"
    WAITING_FOR_HELLO = "waiting for HELLO"
    IDENTIFYING = "identifying"
    RESUMING = "resuming"
    SHUTTING_DOWN = "shutting down"
    WAITING_FOR_MESSAGES = "waiting for messages"
    PROCESSING_NEW_MESSAGE = "processing message"


#: The signature for an event dispatch callback.
DispatchT = typing.Callable[["GatewayClient", str, type_hints.JSONObject], None]


class GatewayClient:
    """
    Implementation of a client for the Discord Gateway. This is a websocket connection to Discord that
    is used to inform your application of events that occur, and to allow you to change your presence,
    amongst other real-time applications.

    Each :class:`GatewayClient` represents a single shard.

    Expected events that may be passed to the event dispatcher are documented in the
    `gateway event reference <https://discordapp.com/developers/docs/topics/gateway#commands-and-events>`_.
    No normalization of the gateway event names occurs, and no transformation of . In addition to this,
    a few internal events can also be triggered to notify you of changes to the connection state.
    * `CONNECT` - fired on initial connection to Discord.
    * `RECONNECT` - fired if we have previously been connected to Discord but are making a new
        connection on an existing :class:`GatewayClient` instance.
    * `DISCONNECT` - fired when the connection is closed for any reason.

    Args:
        compression:
            If True, then payload compression is enabled on the connection. If False, no payloads
            are compressed. You usually want to keep this enabled.
        connector:
            The :class:`aiohttp.BaseConnector` to use for the HTTP session that gets upgraded to a
            websocket connection. You can use this to customise connection pooling, etc.
        debug:
            If True, the client is configured to provide extra contextual information to use when
            debugging this library or extending it. This includes logging every payload that is
            sent or received to the logger as debug entries. Generally it is best to keep this
            disabled.
        dispatch:
            The method to invoke with any dispatched events. This must not be a coroutine function, 
            and must take three arguments only. The first is the reference to this 
            :class:`GatewayClient` The second is the event name.
        initial_presence:
            A raw JSON object as a :class:`dict` that should be set as the initial presence of the
            bot user once online. If or `None`, then it will be set to the default, which is
            showing up as online without a custom status message.
        intents:
            Bitfield of intents to use. If you use the V7 API, this is mandatory. This field will
            determine what events you will receive.
        json_deserialize:
            A custom JSON deserializer function to use. Defaults to :func:`json.loads`.
        json_serialize:
            A custom JSON serializer function to use. Defaults to :func:`json.dumps`.
        large_threshold:
            The number of members that have to be in a guild for it to be considered to be "large".
            Large guilds will not have member information sent automatically, and must manually
            request that member chunks be sent using :meth:`request_member_chunks`.
        proxy_auth:
            Optional :class:`aiohttp.BasicAuth` object that can be provided to allow authenticating
            with a proxy if you use one. Leave or `None` to ignore.
        proxy_headers:
            Optional :class:`aiohttp.typedefs.LooseHeaders` to provide as headers to allow the 
            connection through a proxy if you use one. Leave or `None` to ignore.
        proxy_url:
            Optional :class:`str` to use for a proxy server. If or `None`, then it is ignored.
        session_id:
            The session ID to use. If specified along with a `seq`, then the gateway client
            will attempt to RESUME an existing session rather than re-IDENTIFY. Otherwise, it
            will be ignored.
        seq:
            The sequence number to use. If specified along with a `session_id`, then the gateway
            client will attempt to RESUME an existing session rather than re-IDENTIFY. Otherwise,
            it will be ignored.
        shard_id:
            The shard ID of this gateway client. Defaults to 0.
        shard_count:
            The number of shards on this gateway. Defaults to 1, which implies no sharding is
            taking place.
        ssl_context:
            An optional custom :class:`ssl.SSLContext` to provide to customise how SSL works.
        token:
            The mandatory bot token for the bot account to use, minus the "Bot" authentication
            prefix used elsewhere.
        url:
            The websocket URL to use.
        verify_ssl:
            If True, SSL verification is enabled, which is generally what you want. If you get
            SSL issues, you can try turning this off at your own risk.
        version:
            The version of the gateway API to use. Defaults to the most recent stable documented
            version.
            
    """

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
        "logger",
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
        "version",
        "_ws",
        "_zlib",
    )

    def __init__(
        self,
        *,
        compression: bool = True,
        connector: type_hints.Nullable[aiohttp.BaseConnector] = None,
        debug: bool = False,
        dispatch: DispatchT = lambda gw, e, p: None,
        initial_presence: type_hints.Nullable[type_hints.JSONObject] = None,
        intents: type_hints.Nullable[GatewayIntent] = None,
        json_deserialize: typing.Callable[[typing.AnyStr], type_hints.JSONObject] = json.loads,
        json_serialize: typing.Callable[[type_hints.JSONObject], typing.AnyStr] = json.dumps,
        large_threshold: int = 250,
        proxy_auth: type_hints.Nullable[aiohttp.BasicAuth] = None,
        proxy_headers: type_hints.Nullable[aiohttp.typedefs.LooseHeaders] = None,
        proxy_url: type_hints.Nullable[str] = None,
        session_id: type_hints.Nullable[str] = None,
        seq: type_hints.Nullable[int] = None,
        shard_id: int = 0,
        shard_count: int = 1,
        ssl_context: type_hints.Nullable[ssl.SSLContext] = None,
        token: str,
        url: str,
        verify_ssl: bool = True,
        version: versions.GatewayVersion = versions.GatewayVersion.STABLE,
    ) -> None:
        # Sanitise the URL...
        scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(url, allow_fragments=True)

        new_query = dict(v=int(version), encoding="json")
        if compression:
            # payload compression
            new_query["compress"] = "zlib-stream"

        new_query = urllib.parse.urlencode(new_query)

        url = urllib.parse.urlunparse((scheme, netloc, path, params, new_query, ""))

        self._compression: bool = compression
        self._connected_at: float = float("nan")
        self._connector: type_hints.Nullable[aiohttp.BaseConnector] = connector
        self._debug: bool = debug
        self._intents: type_hints.Nullable[GatewayIntent] = intents
        self._large_threshold: int = large_threshold
        self._json_deserialize: typing.Callable[[typing.AnyStr], type_hints.JSONObject] = json_deserialize
        self._json_serialize: typing.Callable[[type_hints.JSONObject], typing.AnyStr] = json_serialize
        self._presence: type_hints.Nullable[type_hints.JSONObject] = initial_presence
        self._proxy_auth: type_hints.Nullable[aiohttp.BasicAuth] = proxy_auth
        self._proxy_headers: type_hints.Nullable[aiohttp.typedefs.LooseHeaders] = proxy_headers
        self._proxy_url: type_hints.Nullable[str] = proxy_url
        self._ratelimiter: ratelimits.WindowedBurstRateLimiter = ratelimits.WindowedBurstRateLimiter(
            f"gateway shard {shard_id}/{shard_count}", 60.0, 120
        )
        self._session: type_hints.Nullable[aiohttp.ClientSession] = None
        self._ssl_context: type_hints.Nullable[ssl.SSLContext] = ssl_context
        self._token: str = token
        self._url: str = url
        self._verify_ssl: bool = verify_ssl
        self._ws: type_hints.Nullable[aiohttp.ClientWebSocketResponse] = None
        self._zlib: type_hints.Nullable[zlib.decompressobj] = None

        #: An event that is set when the connection closes.
        #:
        #: :type: :class:`asyncio.Event`
        self.closed_event: asyncio.Event = asyncio.Event()

        #: The number of times we have disconnected from the gateway on this client instance.
        #:
        #: :type: :class:`int`
        self.disconnect_count: int = 0

        #: The dispatch method to call when dispatching a new event. This is
        #: the method passed in the constructor.
        self.dispatch: DispatchT = dispatch

        #: The heartbeat interval Discord instructed the client to beat at. This is `nan` until
        #: this information is received.
        #:
        #: :type: :class:`float`
        self.heartbeat_interval: float = float("nan")

        #: The most recent heartbeat latency measurement in seconds. This is `nan` until
        #: this information is available. The latency is calculated as the time between sending
        #: a `HEARTBEAT` payload and receiving a `HEARTBEAT_ACK` response.
        #:
        #: :type: :class:`float`
        self.heartbeat_latency: float = float("nan")

        #: An event that is set when Discord sends a `HELLO` payload. This indicates some sort of
        #: connection has successfully been made.
        #:
        #: :type: :class:`asyncio.Event`
        self.hello_event: asyncio.Event = asyncio.Event()

        #: An event that is set when the client has successfully `IDENTIFY`ed or `RESUMED` with the
        #: gateway. This indicates regular communication can now take place on the connection and
        #: events can be expected to be received.
        #:
        #: :type: :class:`asyncio.Event`
        self.identify_event: asyncio.Event = asyncio.Event()

        #: The monotonic timestamp that the last `HEARTBEAT` was sent at, or `nan` if no
        #: `HEARTBEAT` has yet been sent.
        #:
        #: :type: :class:`float`
        self.last_heartbeat_sent: float = float("nan")

        #: The monotonic timestamp at which the last payload was received from Discord. If this
        #: was more than the :attr:`heartbeat_interval` from the current time, then the connection
        #: is assumed to be zombied and is shut down. If no messages have been received yet, this
        #: is `nan`.
        #:
        #: :type: :class:`float`
        self.last_message_received: float = float("nan")

        #: The logger used for dumping information about what this client is doing.
        #:
        #: :type: :class:`logging.Logger`
        self.logger: logging.Logger = loggers.get_named_logger(self, shard_id)

        #: An event that is set when something requests that the connection should close somewhere.
        #:
        #: :type: :class:`asyncio.Event`
        self.requesting_close_event: asyncio.Event = asyncio.Event()

        #: The current session ID, if known.
        #:
        #: :type: :class:`str` or or `None`
        self.session_id: type_hints.Nullable[str] = session_id

        #: The current sequence number for state synchronization with the API, if known.
        #:
        #: :type: :class:`int` or `None`.
        self.seq: type_hints.Nullable[int] = seq

        #: The shard ID.
        #:
        #: :type: :class:`int`
        self.shard_id: int = shard_id

        #: The number of shards in use for the bot.
        #:
        #: :type: :class:`int`
        self.shard_count: int = shard_count

        #: The current status of the gateway. This can be used to print out informative context for large sharded
        #: bots.
        #:
        #: :type: :class:`GatewayStatus`
        self.status: GatewayStatus = GatewayStatus.OFFLINE

        #: The API version to use on Discord.
        #:
        #: :type: :class:`hikari.net.versions.GatewayVersion`
        self.version: versions.GatewayVersion = version

        self.logger.debug("using Gateway version %s", int(version))

    @property
    def uptime(self) -> datetime.timedelta:
        """
        Returns:
            The amount of time the connection has been running for. If it isn't running, this will
            always return 0 seconds.
        """
        delta = time.perf_counter() - self._connected_at
        return datetime.timedelta(seconds=0 if math.isnan(delta) else delta)

    @property
    def is_connected(self) -> bool:
        """
        Returns:
             `True` if this gateway client is actively connected to something, or
             `False` if it is not running.
        """
        return not math.isnan(self._connected_at)

    @property
    def reconnect_count(self) -> int:
        """
        Returns:
            The number of times this client has been reconnected since it was initialized. This can be used as a
            debugging context, but is also used internally for exception management.
        """
        # 0 disconnects + not is_connected => 0
        # 0 disconnects + is_connected => 0
        # 1 disconnects + not is_connected = 0
        # 1 disconnects + is_connected = 1
        # 2 disconnects + not is_connected = 1
        # 2 disconnects + is_connected = 2
        return max(0, self.disconnect_count - int(not self.is_connected))

    @typing.overload
    async def request_guild_members(self, guild_id: str, *guild_ids: str, limit: int = 0, query: str = "") -> None:
        ...

    @typing.overload
    async def request_guild_members(self, guild_id: str, *guild_ids: str, user_ids: typing.Collection[str]) -> None:
        ...

    async def request_guild_members(self, guild_id, *guild_ids, **kwargs):
        """
        Requests the guild members for a guild or set of guilds. These guilds must be
        being served by this shard, and the results will be provided with `GUILD_MEMBER_CHUNK`
        events.

        Args:
            guild_id : str
                The first guild to request members for.
            *guild_ids : str
                Additional guilds to request members for.
            **kwargs :
                Optional arguments.

        Keyword Args:
            limit : int
                Limit for the number of members to respond with. Set to 0 to be unlimited.
            query : str
                An optional string to filter members with. If specified, only members who have a
                username starting with this string will be returned.
            user_ids : `list` [`str`]
                 An optional list of user IDs to return member info about.

        Note:
            You may not specify `user_ids` at the same time as `limit` and `query`. Likewise,
            if you specify one of `limit` or `query`, the other must also be included. The default
            if no optional arguments are specified is to use a `limit` of `0` and a `query` of
            `""` (empty-string).

        """
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

        await self._send({"op": 8, "d": {"guild_id": guilds, **constraints}})

    async def update_status(self, presence: type_hints.JSONObject) -> None:
        """
        Change the presence of the bot user for this shard.

        Args:
            presence : dict
                The new presence payload to set.
        """
        self.logger.debug("updating presence to %r", presence)
        await self._send(presence)
        self._presence = presence

    async def close(self, close_code: int = 1000) -> None:
        """
        Request this gateway connection closes.

        Args:
            close_code : int
                The close code to use. Defaults to `1000` (normal closure).
        """
        if not self.requesting_close_event.is_set():
            self.status = GatewayStatus.SHUTTING_DOWN
            self.requesting_close_event.set()
            # These will attribute error if they are not set; in this case we don't care, just ignore it.
            with contextlib.suppress(asyncio.TimeoutError, AttributeError):
                await asyncio.wait_for(asyncio.shield(self._ws.close(code=close_code)), timeout=2.0)
            with contextlib.suppress(asyncio.TimeoutError, AttributeError):
                await asyncio.wait_for(asyncio.shield(self._session.close()), timeout=2.0)
            self.closed_event.set()

    async def connect(self, client_session_type=aiohttp.ClientSession) -> None:
        """
        Connect to the gateway and return if it closes.

        # todo: finish
        """
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
            self.logger.debug("expecting HELLO")
            pl = await self._receive()

            op = pl["op"]
            if op != 10:
                raise errors.GatewayError(f"Expected HELLO opcode 10 but received {op}")

            self.heartbeat_interval = pl["d"]["heartbeat_interval"] / 1_000.0

            self.hello_event.set()

            self.dispatch(
                self,
                "RECONNECT" if self.disconnect_count else "CONNECT",
                typing.cast(type_hints.JSONObject, containers.EMPTY_DICT),
            )
            self.logger.info("received HELLO, interval is %ss", self.heartbeat_interval)

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
            self.dispatch(self, "DISCONNECT", typing.cast(type_hints.JSONObject, containers.EMPTY_DICT))

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
            self.logger.debug("sending IDENTIFY")
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
            self.logger.info("sent IDENTIFY, ready to listen to incoming events")
        else:
            self.status = GatewayStatus.RESUMING
            self.logger.debug("sending RESUME")
            pl = {
                "op": 6,
                "d": {"token": self._token, "seq": self.seq, "session_id": self.session_id},
            }
            await self._send(pl)
            self.logger.info("sent RESUME, ready to listen to incoming events")

        self.identify_event.set()
        await self._poll_events()

    async def _heartbeat_keep_alive(self, heartbeat_interval):
        while not self.requesting_close_event.is_set():
            if self.last_message_received < self.last_heartbeat_sent:
                raise asyncio.TimeoutError(
                    f"{self.shard_id}: connection is a zombie, haven't received HEARTBEAT ACK for too long"
                )
            self.logger.debug("sending heartbeat")
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
                self.logger.debug("instructed by gateway server to restart connection")
                raise errors.GatewayMustReconnectError()
            elif op == 9:
                can_resume = bool(d)
                self.logger.info(
                    "instructed by gateway server to %s session", "resume" if can_resume else "restart",
                )
                raise errors.GatewayInvalidSessionError(can_resume)
            elif op == 11:
                now = time.perf_counter()
                self.heartbeat_latency = now - self.last_heartbeat_sent
                self.logger.debug("received HEARTBEAT ACK in %ss", self.heartbeat_latency)
            else:
                self.logger.debug("ignoring opcode %s with data %r", op, d)

    async def _receive(self):
        while True:
            message = await self._receive_one_packet()
            if message.type == aiohttp.WSMsgType.TEXT:
                obj = self._json_deserialize(message.data)

                if self._debug:
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
                    message = await self._receive_one_packet()
                    if message.type != aiohttp.WSMsgType.BINARY:
                        raise errors.GatewayError(f"Expected a binary message but got {message.type}")
                    buffer.extend(message.data)

                pl = self._zlib.decompress(buffer)
                obj = self._json_deserialize(pl)

                if self._debug:
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
            elif message.type == aiohttp.WSMsgType.CLOSE:
                close_code = self._ws.close_code
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
                self.logger.debug("connection has been marked as closed")
                raise errors.GatewayClientClosedError()
            elif message.type == aiohttp.WSMsgType.ERROR:
                ex = self._ws.exception()
                self.logger.debug("connection encountered some error", exc_info=ex)
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
            self.logger.debug("sent payload %s", payload_str)
        else:
            self.logger.debug("sent payload (op:%s, size:%s)", payload.get("op"), len(payload_str))

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
