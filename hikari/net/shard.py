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
"""Single-threaded asyncio Gateway implementation.

Handles regular heartbeating in a background task
on the same event loop. Implements zlib transport compression only.

Can be used as the main gateway connection for a single-sharded bot, or the gateway connection for a
specific shard in a swarm of shards making up a larger bot.

See Also
--------
* IANA WS closure code standards: https://www.iana.org/assignments/websocket/websocket.xhtml
* Gateway documentation: https://discordapp.com/developers/docs/topics/gateway
* Opcode documentation: https://discordapp.com/developers/docs/topics/opcodes-and-status-codes
"""
__all__ = ["ShardConnection"]

import asyncio
import contextlib
import datetime
import json
import logging
import math
import ssl
import time
import typing
import urllib.parse
import zlib

import aiohttp.typedefs

from hikari import errors
from hikari.internal import more_logging
from hikari.net import codes
from hikari.net import ratelimits
from hikari.net import user_agent
from hikari.net import versions

#: The signature for an event dispatch callback.
DispatchT = typing.Callable[["ShardConnection", str, typing.Dict], None]


class ShardConnection:
    """Implementation of a client for the Discord Gateway.

    This is a websocket connection to Discord that is used to inform your
    application of events that occur, and to allow you to change your presence,
    amongst other real-time applications.

    Each :obj:`ShardConnection` represents a single shard.

    Expected events that may be passed to the event dispatcher are documented in the
    `gateway event reference <https://discordapp.com/developers/docs/topics/gateway#commands-and-events>`_.
    No normalization of the gateway event names occurs. In addition to this,
    some internal events can also be triggered to notify you of changes to
    the connection state.

    * ``CONNECTED`` - fired on initial connection to Discord.
    * ``DISCONNECTED`` - fired when the connection is closed for any reason.

    Parameters
    ----------
    compression: :obj:`bool`
        If True, then payload compression is enabled on the connection.
        If False, no payloads are compressed. You usually want to keep this
        enabled.
    connector: :obj:`aiohttp.BaseConnector`, optional
        The :obj:`aiohttp.BaseConnector` to use for the HTTP session that
        gets upgraded to a websocket connection. You can use this to customise
        connection pooling, etc.
    debug: :obj:`bool`
        If True, the client is configured to provide extra contextual
        information to use when debugging this library or extending it. This
        includes logging every payload that is sent or received to the logger
        as debug entries. Generally it is best to keep this disabled.
    dispatch: dispatch function
        The function to invoke with any dispatched events. This must not be a
        coroutine function, and must take three arguments only. The first is
        the reference to this :obj:`ShardConnection` The second is the
        event name.
    initial_presence: :obj:`typing.Dict`, optional
        A raw JSON object as a :obj:`typing.Dict` that should be set as the initial
        presence of the bot user once online. If ``None``, then it will be set to
        the default, which is showing up as online without a custom status
        message.
    intents: :obj:`hikari.net.codes.GatewayIntent`, optional
        Bitfield of intents to use. If you use the V7 API, this is mandatory.
        This field will determine what events you will receive.
    json_deserialize: deserialization function
        A custom JSON deserializer function to use. Defaults to
        :func:`json.loads`.
    json_serialize: serialization function
        A custom JSON serializer function to use. Defaults to
        :func:`json.dumps`.
    large_threshold: :obj:`int`
        The number of members that have to be in a guild for it to be
        considered to be "large". Large guilds will not have member information
        sent automatically, and must manually request that member chunks be
        sent using :meth:`request_member_chunks`.
    proxy_auth: :obj:`aiohttp.BasicAuth`, optional
        Optional :obj:`aiohttp.BasicAuth` object that can be provided to
        allow authenticating with a proxy if you use one. Leave ``None`` to
        ignore.
    proxy_headers: :obj:`aiohttp.typedefs.LooseHeaders`, optional
        Optional :obj:`aiohttp.typedefs.LooseHeaders` to provide as headers
        to allow the connection through a proxy if you use one. Leave ``None``
        to ignore.
    proxy_url: :obj:`str`, optional
        Optional :obj:`str` to use for a proxy server. If ``None``, then it
        is ignored.
    session_id: :obj:`str`, optional
        The session ID to use. If specified along with ``seq``, then the
        gateway client will attempt to ``RESUME`` an existing session rather than
        re-``IDENTIFY``. Otherwise, it will be ignored.
    seq: :obj:`int`, optional
        The sequence number to use. If specified along with ``session_id``, then
        the gateway client will attempt to ``RESUME`` an existing session rather
        than re-``IDENTIFY``. Otherwise, it will be ignored.
    shard_id: :obj:`int`
        The shard ID of this gateway client. Defaults to ``0``.
    shard_count: :obj:`int`
        The number of shards on this gateway. Defaults to ``1``, which implies no
        sharding is taking place.
    ssl_context: :obj:`ssl.SSLContext`, optional
        An optional custom :obj:`ssl.SSLContext` to provide to customise how
        SSL works.
    token: :obj:`str`
        The mandatory bot token for the bot account to use, minus the "Bot"
        authentication prefix used elsewhere.
    url: :obj:`str`
        The websocket URL to use.
    verify_ssl: :obj:`bool`
        If ``True``, SSL verification is enabled, which is generally what you want.
        If you get SSL issues, you can try turning this off at your own risk.
    version: :obj:`hikari.net.versions.GatewayVersion`
        The version of the gateway API to use. Defaults to the most recent
        stable documented version.
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
        "ready_event",
        "resumed_event",
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

    #: An event that is set when the connection closes.
    #:
    #: :type: :obj:`asyncio.Event`
    closed_event: asyncio.Event

    #: The number of times we have disconnected from the gateway on this
    #: client instance.
    #:
    #: :type: :obj:`int`
    disconnect_count: int

    #: The dispatch method to call when dispatching a new event. This is
    #: the method passed in the constructor.
    dispatch: DispatchT

    #: The heartbeat interval Discord instructed the client to beat at.
    #: This is ``nan`` until this information is received.
    #:
    #: :type: :obj:`float`
    heartbeat_interval: float

    #: The most recent heartbeat latency measurement in seconds. This is
    #: ``nan`` until this information is available. The latency is calculated
    #: as the time between sending a ``HEARTBEAT`` payload and receiving a
    #: ``HEARTBEAT_ACK`` response.
    #:
    #: :type: :obj:`float`
    heartbeat_latency: float

    #: An event that is set when Discord sends a ``HELLO`` payload. This
    #: indicates some sort of connection has successfully been made.
    #:
    #: :type: :obj:`asyncio.Event`
    hello_event: asyncio.Event

    #: An event that is set when the client has successfully ``IDENTIFY``ed
    #: or ``RESUMED`` with the gateway. This indicates regular communication
    #: can now take place on the connection and events can be expected to
    #: be received.
    #:
    #: :type: :obj:`asyncio.Event`
    identify_event: asyncio.Event

    #: The monotonic timestamp that the last ``HEARTBEAT`` was sent at, or
    #: ``nan`` if no ``HEARTBEAT`` has yet been sent.
    #:
    #: :type: :obj:`float`
    last_heartbeat_sent: float

    #: The monotonic timestamp at which the last payload was received from
    #: Discord. If this was more than the ``heartbeat_interval`` from
    #: the current time, then the connection is assumed to be zombied and
    #: is shut down. If no messages have been received yet, this is ``nan``.
    #:
    #: :type: :obj:`float`
    last_message_received: float

    #: The logger used for dumping information about what this client is doing.
    #:
    #: :type: :obj:`logging.Logger`
    logger: logging.Logger

    #: An event that is triggered when a ``READY`` payload is received for the
    #: shard. This indicates that it successfully started up and had a correct
    #: sharding configuration. This is more appropriate to wait for than
    #: :attr:`identify_event` since the former will still fire if starting
    #: shards too closely together, for example. This would still lead to an
    #: immediate invalid session being fired afterwards.
    #
    #: It is worth noting that this event is only set for the first ``READY``
    #: event after connecting with a fresh connection. For all other purposes,
    #: you should wait for the event to be fired in the ``dispatch`` function
    #: you provide.
    #:
    #: :type: :obj:`asyncio.Event`
    ready_event: asyncio.Event

    #: An event that is triggered when a resume has succeeded on the gateway.
    #:
    #: :type: :obj:`asyncio.Event`
    resumed_event: asyncio.Event

    #: An event that is set when something requests that the connection
    #: should close somewhere.
    #:
    #: :type: :obj:`asyncio.Event`
    requesting_close_event: asyncio.Event

    #: The current session ID, if known.
    #:
    #: :type: :obj:`str`, optional
    session_id: typing.Optional[str]

    #: The current sequence number for state synchronization with the API,
    #: if known.
    #:
    #: :type: :obj:`int`, optional.
    seq: typing.Optional[int]

    #: The shard ID.
    #:
    #: :type: :obj:`int`
    shard_id: int

    #: The number of shards in use for the bot.
    #:
    #: :type: :obj:`int`
    shard_count: int

    #: The API version to use on Discord.
    #:
    #: :type: :obj:`int`
    version: int

    def __init__(
        self,
        *,
        compression: bool = True,
        connector: typing.Optional[aiohttp.BaseConnector] = None,
        debug: bool = False,
        dispatch: DispatchT = lambda gw, e, p: None,
        initial_presence: typing.Optional[typing.Dict] = None,
        intents: typing.Optional[codes.GatewayIntent] = None,
        json_deserialize: typing.Callable[[typing.AnyStr], typing.Dict] = json.loads,
        json_serialize: typing.Callable[[typing.Dict], typing.AnyStr] = json.dumps,
        large_threshold: int = 250,
        proxy_auth: typing.Optional[aiohttp.BasicAuth] = None,
        proxy_headers: typing.Optional[aiohttp.typedefs.LooseHeaders] = None,
        proxy_url: typing.Optional[str] = None,
        session_id: typing.Optional[str] = None,
        seq: typing.Optional[int] = None,
        shard_id: int = 0,
        shard_count: int = 1,
        ssl_context: typing.Optional[ssl.SSLContext] = None,
        token: str,
        url: str,
        verify_ssl: bool = True,
        version: typing.Union[int, versions.GatewayVersion] = versions.GatewayVersion.STABLE,
    ) -> None:
        # Sanitise the URL...
        scheme, netloc, path, params, _, _ = urllib.parse.urlparse(url, allow_fragments=True)

        new_query = dict(v=int(version), encoding="json")
        if compression:
            # payload compression
            new_query["compress"] = "zlib-stream"

        new_query = urllib.parse.urlencode(new_query)

        url = urllib.parse.urlunparse((scheme, netloc, path, params, new_query, ""))

        self._compression: bool = compression
        self._connected_at: float = float("nan")
        self._connector: typing.Optional[aiohttp.BaseConnector] = connector
        self._debug: bool = debug
        self._intents: typing.Optional[intents.GatewayIntent] = intents
        self._large_threshold: int = large_threshold
        self._json_deserialize: typing.Callable[[typing.AnyStr], typing.Dict] = json_deserialize
        self._json_serialize: typing.Callable[[typing.Dict], typing.AnyStr] = json_serialize
        self._presence: typing.Optional[typing.Dict] = initial_presence
        self._proxy_auth: typing.Optional[aiohttp.BasicAuth] = proxy_auth
        self._proxy_headers: typing.Optional[aiohttp.typedefs.LooseHeaders] = proxy_headers
        self._proxy_url: typing.Optional[str] = proxy_url
        self._ratelimiter: ratelimits.WindowedBurstRateLimiter = ratelimits.WindowedBurstRateLimiter(
            f"gateway shard {shard_id}/{shard_count}", 60.0, 120
        )
        self._session: typing.Optional[aiohttp.ClientSession] = None
        self._ssl_context: typing.Optional[ssl.SSLContext] = ssl_context
        self._token: str = token
        self._url: str = url
        self._verify_ssl: bool = verify_ssl
        self._ws: typing.Optional[aiohttp.ClientWebSocketResponse] = None
        self._zlib: typing.Optional[zlib.decompressobj] = None
        self.closed_event: asyncio.Event = asyncio.Event()
        self.disconnect_count: int = 0
        self.dispatch: DispatchT = dispatch
        self.heartbeat_interval: float = float("nan")
        self.heartbeat_latency: float = float("nan")
        self.hello_event: asyncio.Event = asyncio.Event()
        self.identify_event: asyncio.Event = asyncio.Event()
        self.last_heartbeat_sent: float = float("nan")
        self.last_message_received: float = float("nan")
        self.requesting_close_event: asyncio.Event = asyncio.Event()
        self.ready_event: asyncio.Event = asyncio.Event()
        self.resumed_event: asyncio.Event = asyncio.Event()
        self.session_id = session_id
        self.seq: typing.Optional[int] = seq
        self.shard_id: int = shard_id
        self.shard_count: int = shard_count
        self.version: int = int(version)

        self.logger: logging.Logger = more_logging.get_named_logger(self, f"#{shard_id}", f"v{self.version}")

    @property
    def uptime(self) -> datetime.timedelta:
        """Amount of time the connection has been running for.

        Returns
        -------
        :obj:`datetime.timedelta`
            The amount of time the connection has been running for. If it isn't
            running, this will always return ``0`` seconds.
        """
        delta = time.perf_counter() - self._connected_at
        return datetime.timedelta(seconds=0 if math.isnan(delta) else delta)

    @property
    def is_connected(self) -> bool:
        """Whether the gateway is connecter or not.

        Returns
        -------
        :obj:`bool`
            True if this gateway client is actively connected to something, or
            False if it is not running.
        """
        return not math.isnan(self._connected_at)

    @property
    def intents(self) -> typing.Optional[codes.GatewayIntent]:
        """Intents being used.

        If this is ``None``, no intent usage was being
        used on this shard. On V6 this would be regular usage as prior to
        the intents change in January 2020. If on V7, you just won't be
        able to connect at all to the gateway.

        Returns
        -------
        :obj:`hikari.net.codes.GatewayIntent`, optional
            The intents being used.
        """
        return self._intents

    @property
    def reconnect_count(self) -> int:
        """Reconnection count for this shard connection instance.

        This can be used as a debugging context, but is also used internally
        for exception management.

        Returns
        -------
        :obj:`int`
            The amount of times the gateway has reconnected since initialization.
        """
        # 0 disconnects + not is_connected => 0
        # 0 disconnects + is_connected => 0
        # 1 disconnects + not is_connected = 0
        # 1 disconnects + is_connected = 1
        # 2 disconnects + not is_connected = 1
        # 2 disconnects + is_connected = 2
        return max(0, self.disconnect_count - int(not self.is_connected))

    # Ignore docstring not starting in an imperative mood
    @property
    def current_presence(self) -> typing.Dict:  # noqa: D401
        """Current presence for the gateway.

        Returns
        -------
        :obj:`typing.Dict`
            The current presence for the gateway.
        """
        # Make a shallow copy to prevent mutation.
        return dict(self._presence or {})

    @typing.overload
    async def request_guild_members(self, guild_id: str, *guild_ids: str, limit: int = 0, query: str = "") -> None:
        """Request guild members in the given guilds using a query string and an optional limit."""

    @typing.overload
    async def request_guild_members(self, guild_id: str, *guild_ids: str, user_ids: typing.Sequence[str]) -> None:
        """Request guild members in the given guilds using a set of user IDs to resolve."""

    async def request_guild_members(self, guild_id, *guild_ids, **kwargs):
        """Request the guild members for a guild or set of guilds.

        These guilds must be being served by this shard, and the results will be
        provided to the dispatcher with ``GUILD_MEMBER_CHUNK`` events.

        Parameters
        ----------
        guild_id : :obj:`str`
            The first guild to request members for.
        *guild_ids : :obj:`str`
            Additional guilds to request members for.
        **kwargs
            Optional arguments.

        Keyword Args
        ------------
        limit : :obj:`int`
            Limit for the number of members to respond with. Set to ``0`` to be
            unlimited.
        query : :obj:`str`
            An optional string to filter members with. If specified, only
            members who have a username starting with this string will be
            returned.
        user_ids : :obj:`typing.Sequence` [ :obj:`str` ]
            An optional list of user IDs to return member info about.

        Note
        ----
        You may not specify ``user_ids`` at the same time as ``limit`` and
        ``query``. Likewise, if you specify one of ``limit`` or ``query``,
        the other must also be included. The default, if no optional arguments
        are specified, is to use a ``limit = 0`` and a ``query = ""`` (empty-string).
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

        await self._send({"op": codes.GatewayOpcode.REQUEST_GUILD_MEMBERS, "d": {"guild_id": guilds, **constraints}})

    async def update_presence(self, presence: typing.Dict) -> None:
        """Change the presence of the bot user for this shard.

        Parameters
        ----------
        presence : :obj:`typing.Dict`
            The new presence payload to set.
        """
        presence.setdefault("since", None)
        presence.setdefault("game", None)
        presence.setdefault("status", "online")
        presence.setdefault("afk", False)

        self.logger.debug("updating presence to %r", presence)
        await self._send({"op": codes.GatewayOpcode.PRESENCE_UPDATE, "d": presence})
        self._presence = presence

    async def close(self, close_code: int = 1000) -> None:
        """Request this gateway connection closes.

        Parameters
        ----------
        close_code : :obj:`int`
            The close code to use. Defaults to ``1000`` (normal closure).
        """
        if not self.requesting_close_event.is_set():
            self.requesting_close_event.set()
            # These will attribute error if they are not set; in this case we don't care, just ignore it.
            with contextlib.suppress(asyncio.TimeoutError, AttributeError):
                await asyncio.wait_for(asyncio.shield(self._ws.close(code=close_code)), timeout=2.0)
            with contextlib.suppress(asyncio.TimeoutError, AttributeError):
                await asyncio.wait_for(asyncio.shield(self._session.close()), timeout=2.0)
            self.closed_event.set()

    async def connect(self, client_session_type=aiohttp.ClientSession) -> None:
        """Connect to the gateway and return when it closes.

        Parameters
        ----------
        client_session_type
            The client session implementation to use. You generally do not want
            to change this from the default, which is :obj:`aiohttp.ClientSession`.
        """
        if self.is_connected:
            raise RuntimeError("Already connected")

        self.closed_event.clear()
        self.hello_event.clear()
        self.identify_event.clear()
        self.ready_event.clear()
        self.requesting_close_event.clear()
        self.resumed_event.clear()

        self._session = client_session_type(**self._cs_init_kwargs)
        close_code = codes.GatewayCloseCode.ABNORMAL_CLOSURE

        try:
            self._ws = await self._session.ws_connect(**self._ws_connect_kwargs)

            self._connected_at = time.perf_counter()
            self._zlib = zlib.decompressobj()
            self.logger.debug("expecting HELLO")
            pl = await self._receive()

            op = pl["op"]
            if op != 10:
                raise errors.GatewayError(f"Expected HELLO opcode 10 but received {op}")

            self.heartbeat_interval = pl["d"]["heartbeat_interval"] / 1_000.0

            self.hello_event.set()

            self.dispatch(self, "CONNECTED", {})
            self.logger.debug("received HELLO (interval:%ss)", self.heartbeat_interval)

            completed, pending_tasks = await asyncio.wait(
                [self._heartbeat_keep_alive(self.heartbeat_interval), self._identify_or_resume_then_poll_events()],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Kill other running tasks now.
            for pending_task in pending_tasks:
                pending_task.cancel()
                with contextlib.suppress(Exception):
                    # Clear any pending exception to prevent a nasty console message.
                    pending_task.result()

            # If the heartbeat call closes normally, then we want to get the exception
            # raised by the identify call if it raises anything. This prevents spammy
            # exceptions being thrown if the client shuts down during the handshake,
            # which becomes more and more likely when we consider bots may have many
            # shards running, each taking min of 5s to start up after the first.
            ex = None
            while len(completed) > 0 and ex is None:
                ex = completed.pop().exception()

            if ex is None:
                # If no exception occurred, we must have exited non-exceptionally, indicating
                # the close event was set without an error causing that flag to be changed.
                ex = errors.GatewayClientClosedError()
                close_code = codes.GatewayCloseCode.NORMAL_CLOSURE
            elif isinstance(ex, asyncio.TimeoutError):
                # If we get timeout errors receiving stuff, propagate as a zombied connection. This
                # is already done by the ping keepalive and heartbeat keepalive partially, but this
                # is a second edge case.
                ex = errors.GatewayZombiedError()

            if hasattr(ex, "close_code"):
                close_code = ex.close_code

            raise ex
        finally:
            await self.close(close_code)
            self.closed_event.set()
            self._connected_at = float("nan")
            self.last_heartbeat_sent = float("nan")
            self.heartbeat_latency = float("nan")
            self.last_message_received = float("nan")
            self.disconnect_count += 1
            self._ws = None
            await self._session.close()
            self._session = None
            self.dispatch(self, "DISCONNECTED", {})

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
            self.logger.debug("preparing to send IDENTIFY")

            pl = {
                "op": codes.GatewayOpcode.IDENTIFY,
                "d": {
                    "token": self._token,
                    "compress": False,
                    "large_threshold": self._large_threshold,
                    "properties": user_agent.UserAgent().websocket_triplet,
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
                # noinspection PyTypeChecker
                pl["d"]["presence"] = self._presence
            await self._send(pl)
            self.logger.debug("sent IDENTIFY, now listening to incoming events")
        else:
            self.logger.debug("preparing to send RESUME")
            pl = {
                "op": codes.GatewayOpcode.RESUME,
                "d": {"token": self._token, "seq": self.seq, "session_id": self.session_id},
            }
            await self._send(pl)
            self.logger.debug("sent RESUME, now listening to incoming events")

        self.identify_event.set()
        await self._poll_events()

    async def _heartbeat_keep_alive(self, heartbeat_interval):
        while not self.requesting_close_event.is_set():
            if self.last_message_received < self.last_heartbeat_sent:
                raise asyncio.TimeoutError(
                    f"{self.shard_id}: connection is a zombie, haven't received HEARTBEAT ACK for too long"
                )
            self.logger.debug("preparing to send HEARTBEAT (s:%s, interval:%ss)", self.seq, self.heartbeat_interval)
            await self._send({"op": codes.GatewayOpcode.HEARTBEAT, "d": self.seq})
            self.last_heartbeat_sent = time.perf_counter()
            try:
                await asyncio.wait_for(self.requesting_close_event.wait(), timeout=heartbeat_interval)
            except asyncio.TimeoutError:
                pass

    async def _poll_events(self):
        while not self.requesting_close_event.is_set():
            next_pl = await self._receive()

            op = next_pl["op"]
            d = next_pl["d"]

            if op == codes.GatewayOpcode.DISPATCH:
                self.seq = next_pl["s"]
                event_name = next_pl["t"]

                if event_name == "READY":
                    self.session_id = d["session_id"]
                    version = d["v"]

                    self.logger.debug(
                        "connection is READY (session:%s, version:%s)", self.session_id, version,
                    )

                    self.ready_event.set()

                elif event_name == "RESUMED":
                    self.resumed_event.set()

                    self.logger.debug("connection has RESUMED (session:%s, s:%s)", self.session_id, self.seq)

                self.dispatch(self, event_name, d)
            elif op == codes.GatewayOpcode.HEARTBEAT:
                self.logger.debug("received HEARTBEAT, preparing to send HEARTBEAT ACK to server in response")
                await self._send({"op": codes.GatewayOpcode.HEARTBEAT_ACK})
            elif op == codes.GatewayOpcode.RECONNECT:
                self.logger.debug("instructed by gateway server to restart connection")
                raise errors.GatewayMustReconnectError()
            elif op == codes.GatewayOpcode.INVALID_SESSION:
                can_resume = bool(d)
                self.logger.debug(
                    "instructed by gateway server to %s session", "resume" if can_resume else "restart",
                )
                raise errors.GatewayInvalidSessionError(can_resume)
            elif op == codes.GatewayOpcode.HEARTBEAT_ACK:
                now = time.perf_counter()
                self.heartbeat_latency = now - self.last_heartbeat_sent
                self.logger.debug("received HEARTBEAT ACK (latency:%ss)", self.heartbeat_latency)
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

            if message.type == aiohttp.WSMsgType.CLOSE:
                close_code = self._ws.close_code
                try:
                    close_code = codes.GatewayCloseCode(close_code)
                except ValueError:
                    pass

                self.logger.debug("connection closed with code %s", close_code)
                if close_code == codes.GatewayCloseCode.AUTHENTICATION_FAILED:
                    raise errors.GatewayInvalidTokenError()
                if close_code in (codes.GatewayCloseCode.SESSION_TIMEOUT, codes.GatewayCloseCode.INVALID_SEQ):
                    raise errors.GatewayInvalidSessionError(False)
                if close_code == codes.GatewayCloseCode.SHARDING_REQUIRED:
                    raise errors.GatewayNeedsShardingError()

                raise errors.GatewayServerClosedConnectionError(close_code)

            if message.type in (aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSED):
                self.logger.debug("connection has been marked as closed")
                raise errors.GatewayClientClosedError()

            if message.type == aiohttp.WSMsgType.ERROR:
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
