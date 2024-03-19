# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
"""Single-shard implementation for the V10 event gateway for Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("GatewayShardImpl",)

import asyncio
import contextlib
import logging
import platform
import sys
import typing
import urllib.parse
import zlib

import aiohttp

from hikari import _about as about
from hikari import errors
from hikari import intents as intents_
from hikari import presences
from hikari import snowflakes
from hikari import undefined
from hikari import urls
from hikari.api import shard
from hikari.impl import rate_limits
from hikari.internal import aio
from hikari.internal import data_binding
from hikari.internal import net
from hikari.internal import time
from hikari.internal import ux

if typing.TYPE_CHECKING:
    import datetime

    import aiohttp.http_websocket
    import aiohttp.typedefs

    from hikari import channels
    from hikari import guilds
    from hikari import users as users_
    from hikari.api import event_factory as event_factory_
    from hikari.api import event_manager as event_manager_
    from hikari.impl import config

# Important attributes
_D: typing.Final[str] = sys.intern("d")
_T: typing.Final[str] = sys.intern("t")
_S: typing.Final[str] = sys.intern("s")
_OP: typing.Final[str] = sys.intern("op")

# Opcodes
_DISPATCH: typing.Final[int] = 0
_HEARTBEAT: typing.Final[int] = 1
_IDENTIFY: typing.Final[int] = 2
_PRESENCE_UPDATE: typing.Final[int] = 3
_VOICE_STATE_UPDATE: typing.Final[int] = 4
_RESUME: typing.Final[int] = 6
_RECONNECT: typing.Final[int] = 7
_REQUEST_GUILD_MEMBERS: typing.Final[int] = 8
_INVALID_SESSION: typing.Final[int] = 9
_HELLO: typing.Final[int] = 10
_HEARTBEAT_ACK: typing.Final[int] = 11
# Special dispatches
_READY: typing.Final[str] = sys.intern("READY")
_RESUMED: typing.Final[str] = sys.intern("RESUMED")
# If we disconnect within this period of time after starting, we should
# use an exponential backoff before restarting.
_BACKOFF_WINDOW: typing.Final[float] = 30.0
_BACKOFF_BASE: typing.Final[float] = 1.85
_BACKOFF_CAP: typing.Final[float] = 60.0
# Discord seems to invalidate sessions if I send a 1xxx, which is useless
# for invalid session and reconnect messages where I want to be able to
# resume.
_RESUME_CLOSE_CODE: typing.Final[int] = 3_000
# Per-shard sending rate-limit
_TOTAL_RATELIMIT: typing.Final[typing.Tuple[float, int]] = (60.0, 120)
# Rate-limit for non-priority packages.
# This is done to always allow for HEARTBEAT packages
# to get around (leaving 3 slots for it).
_NON_PRIORITY_RATELIMIT: typing.Final[typing.Tuple[float, int]] = (60.0, 117)
# Used to identify the end of a ZLIB payload
_ZLIB_SUFFIX: typing.Final[bytes] = b"\x00\x00\xff\xff"
# Close codes which don't invalidate the current session.
_RECONNECTABLE_CLOSE_CODES: typing.FrozenSet[errors.ShardCloseCode] = frozenset(
    (
        errors.ShardCloseCode.UNKNOWN_ERROR,
        errors.ShardCloseCode.DECODE_ERROR,
        errors.ShardCloseCode.INVALID_SEQ,
        errors.ShardCloseCode.SESSION_TIMEOUT,
        errors.ShardCloseCode.RATE_LIMITED,
    )
)
# Default value used by the client
_CUSTOM_STATUS_NAME = "Custom Status"


def _log_filterer(token: str) -> typing.Callable[[str], str]:
    def filterer(entry: str) -> str:
        return entry.replace(token, "**REDACTED TOKEN**")

    return filterer


@typing.final
class _GatewayTransport:
    """Internal component to handle lower-level communication logic.

    This includes translating aiohttp error conditions to hikari ones,
    handling inbound zlib packets, creating the websocket and client session,
    and ensuring all resources are freed deterministically where possible.

    Payload logging is also performed here.
    """

    __slots__ = (
        "_zlib",
        "_sent_close",
        "_logger",
        "_exit_stack",
        "_log_filterer",
        "_ws",
        "_receive_and_check",
        "_loads",
        "_dumps",
    )

    def __init__(
        self,
        ws: aiohttp.ClientWebSocketResponse,
        transport_compression: bool,
        exit_stack: contextlib.AsyncExitStack,
        logger: logging.Logger,
        log_filterer: typing.Callable[[str], str],
        dumps: data_binding.JSONEncoder,
        loads: data_binding.JSONDecoder,
    ) -> None:
        self._logger = logger
        self._log_filterer = log_filterer
        self._exit_stack = exit_stack
        self._sent_close = False
        self._ws = ws
        self._zlib = zlib.decompressobj()
        self._loads = loads
        self._dumps = dumps

        if transport_compression:
            self._receive_and_check = self._receive_and_check_zlib
        else:
            self._receive_and_check = self._receive_and_check_text

    async def send_close(self, *, code: int, message: bytes) -> None:
        if self._sent_close:
            return

        self._sent_close = True
        self._logger.debug("sending close frame with code %s and message %s", code, message)
        try:
            await asyncio.wait_for(self._ws.close(code=code, message=message), timeout=5)

        except asyncio.TimeoutError:
            self._logger.debug("failed to send close frame in time, probably connection issues")

        finally:
            await self._exit_stack.aclose()

            # We have to sleep to allow aiohttp time to close SSL transports...
            # This code can be removed in aiohttp v4.0.0
            # https://github.com/aio-libs/aiohttp/issues/1925
            # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
            await asyncio.sleep(0.25)

    async def receive_json(self) -> typing.Any:
        pl = await self._receive_and_check()
        if self._logger.isEnabledFor(ux.TRACE):
            filtered = self._log_filterer(pl)
            self._logger.log(ux.TRACE, "received payload with size %s\n    %s", len(pl), filtered)

        return self._loads(pl)

    async def send_json(self, data: data_binding.JSONObject) -> None:
        pl = self._dumps(data)
        if self._logger.isEnabledFor(ux.TRACE):
            filtered = self._log_filterer(pl.decode("utf-8"))
            self._logger.log(ux.TRACE, "sending payload with size %s\n    %s", len(pl), filtered)

        await self._ws.send_bytes(pl)

    def _handle_other_message(self, message: aiohttp.WSMessage, /) -> typing.NoReturn:
        if message.type == aiohttp.WSMsgType.TEXT:
            raise errors.GatewayError("Unexpected message type received TEXT, expected BINARY")

        if message.type == aiohttp.WSMsgType.BINARY:
            raise errors.GatewayError("Unexpected message type received BINARY, expected TEXT")

        if message.type == aiohttp.WSMsgType.CLOSE:
            close_code = int(message.data)

            can_reconnect = close_code < 4000 or close_code in _RECONNECTABLE_CLOSE_CODES
            # str(message.extra) is used to cast the possible None to a string
            raise errors.GatewayServerClosedConnectionError(str(message.extra), close_code, can_reconnect)

        if message.type == aiohttp.WSMsgType.CLOSING or message.type == aiohttp.WSMsgType.CLOSED:
            # May be caused by the server shutting us down.
            # May be caused by Windows injecting an EOF if something disconnects, as some
            # network drivers appear to do this.
            raise errors.GatewayConnectionError("Socket has closed")

        # Assume exception for now.
        raise errors.GatewayError("Unexpected websocket exception from gateway") from self._ws.exception()

    async def _receive_and_check_text(self) -> str:
        message = await self._ws.receive()

        if message.type == aiohttp.WSMsgType.TEXT:
            assert isinstance(message.data, str)
            return message.data

        self._handle_other_message(message)

    async def _receive_and_check_zlib(self) -> str:
        message = await self._ws.receive()

        if message.type == aiohttp.WSMsgType.BINARY:
            if message.data.endswith(_ZLIB_SUFFIX):
                return self._zlib.decompress(message.data).decode("utf-8")

            return await self._receive_and_check_complete_zlib_package(message.data)

        self._handle_other_message(message)

    async def _receive_and_check_complete_zlib_package(self, initial_data: bytes, /) -> str:
        buff = bytearray(initial_data)

        while not buff.endswith(_ZLIB_SUFFIX):
            message = await self._ws.receive()

            if message.type == aiohttp.WSMsgType.BINARY:
                buff.extend(message.data)
                continue

            self._handle_other_message(message)

        return self._zlib.decompress(buff).decode("utf-8")

    @classmethod
    async def connect(
        cls,
        *,
        http_settings: config.HTTPSettings,
        logger: logging.Logger,
        proxy_settings: config.ProxySettings,
        log_filterer: typing.Callable[[str], str],
        dumps: data_binding.JSONEncoder,
        loads: data_binding.JSONDecoder,
        transport_compression: bool,
        url: str,
    ) -> _GatewayTransport:
        """Generate a single-use websocket connection.

        This uses a single connection in a TCP connector pool, with a one-use
        aiohttp client session.
        """
        exit_stack = contextlib.AsyncExitStack()

        try:
            try:
                connector = net.create_tcp_connector(http_settings=http_settings, dns_cache=False, limit=1)
                client_session = await exit_stack.enter_async_context(
                    net.create_client_session(
                        connector=connector,
                        connector_owner=True,
                        http_settings=http_settings,
                        raise_for_status=True,
                        trust_env=proxy_settings.trust_env,
                    )
                )

                web_socket = await exit_stack.enter_async_context(
                    client_session.ws_connect(
                        max_msg_size=0,
                        proxy=proxy_settings.url,
                        proxy_headers=proxy_settings.headers,
                        url=url,
                        # We manage this ourselves
                        autoclose=False,
                    )
                )

                return cls(
                    ws=web_socket,
                    transport_compression=transport_compression,
                    exit_stack=exit_stack,
                    logger=logger,
                    log_filterer=log_filterer,
                    loads=loads,
                    dumps=dumps,
                )

            except (aiohttp.ClientConnectionError, aiohttp.ClientResponseError, asyncio.TimeoutError) as ex:
                # If we cannot do DNS lookup, this will fail with an aiohttp.ClientConnectionError
                # usually, but it might also fail with asyncio.TimeoutError if its gets stuck in a weird way
                #
                # aiohttp.ClientResponseError has a really bad str, so we use the repr instead
                if isinstance(ex, aiohttp.ClientResponseError):
                    reason = repr(ex)
                elif isinstance(ex, asyncio.TimeoutError):
                    reason = "Timeout exceeded"
                else:
                    reason = str(ex)
                raise errors.GatewayConnectionError(reason) from None

        except Exception:
            await exit_stack.aclose()

            # We have to sleep to allow aiohttp time to close SSL transports...
            # This code can be removed in aiohttp v4.0.0
            # https://github.com/aio-libs/aiohttp/issues/1925
            # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
            await asyncio.sleep(0.25)

            raise


def _serialize_datetime(dt: typing.Optional[datetime.datetime]) -> typing.Optional[int]:
    if dt is None:
        return None

    return int(dt.timestamp() * 1_000)


def _serialize_activity(activity: typing.Optional[presences.Activity]) -> data_binding.JSONish:
    if activity is None:
        return None

    # Syntactic sugar, treat `name` as state if using `CUSTOM` and `state` is not passed.
    state: typing.Optional[str]
    if activity.type is presences.ActivityType.CUSTOM and activity.name and not activity.state:
        name = _CUSTOM_STATUS_NAME
        state = activity.name
    else:
        name = activity.name
        state = activity.state

    payload = {"name": name, "state": state, "type": int(activity.type), "url": activity.url}
    return payload


class GatewayShardImpl(shard.GatewayShard):
    """Implementation of a V10 compatible gateway.

    !!! note
        If all four of `initial_activity`, `initial_idle_since`,
        `initial_is_afk`, and `initial_status` are not defined and left to their
        default values, then the presence will not be _updated_ on startup
        at all.
        If any of these _are_ specified, then any that are not specified will
        be set to sane defaults, which may change the previous status. This will
        only occur during startup, and is an artifact of how Discord manages
        these updates internally. All other calls to update the status of
        the shard will support partial updates.

    Parameters
    ----------
    token : str
        The bot token to use.
    url : str
        The gateway URL to use. This should not contain a query-string or
        fragments.
    event_manager : hikari.api.event_manager.EventManager
        The event manager this shard should make calls to.
    event_factory : hikari.api.event_factory.EventFactory
        The event factory this shard should use.

    Other Parameters
    ----------------
    compression : typing.Optional[str]
        Compression format to use for the shard. Only supported values are
        `"transport_zlib_stream"` or [`None`][] to disable it.
    dumps : hikari.internal.data_binding.JSONEncoder
        The JSON encoder this application should use.
    loads : hikari.internal.data_binding.JSONDecoder
        The JSON decoder this application should use.
    initial_activity : typing.Optional[hikari.presences.Activity]
        The initial activity to appear to have for this shard, or
        [`None`][] if no activity should be set initially. This is the
        default.
    initial_idle_since : typing.Optional[datetime.datetime]
        The datetime to appear to be idle since, or [`None`][] if the
        shard should not provide this. The default is [`None`][].
    initial_is_afk : bool
        Whether to appear to be AFK or not on login.
    initial_status : hikari.presences.Status
        The initial status to set on login for the shard.
    intents : hikari.intents.Intents
        Collection of intents to use.
    large_threshold : int
        The number of members to have in a guild for it to be considered large.
    shard_id : int
        The shard ID.
    shard_count : int
        The shard count.
    http_settings : hikari.impl.config.HTTPSettings
        The HTTP-related settings to use while negotiating a websocket.
    proxy_settings : hikari.impl.config.ProxySettings
        The proxy settings to use while negotiating a websocket.
    data_format : str
        Data format to use for inbound data. Only supported format is `"json"`.
    """

    __slots__: typing.Sequence[str] = (
        "_activity",
        "_dumps",
        "_event_manager",
        "_event_factory",
        "_gateway_url",
        "_handshake_event",
        "_heartbeat_latency",
        "_http_settings",
        "_idle_since",
        "_intents",
        "_is_afk",
        "_is_closing",
        "_keep_alive_task",
        "_large_threshold",
        "_last_heartbeat_ack_received",
        "_last_heartbeat_sent",
        "_loads",
        "_logger",
        "_non_priority_rate_limit",
        "_proxy_settings",
        "_resume_gateway_url",
        "_seq",
        "_session_id",
        "_shard_count",
        "_shard_id",
        "_status",
        "_token",
        "_total_rate_limit",
        "_transport_compression",
        "_user_id",
        "_ws",
    )

    def __init__(
        self,
        *,
        compression: typing.Optional[str] = shard.GatewayCompression.TRANSPORT_ZLIB_STREAM,
        dumps: data_binding.JSONEncoder = data_binding.default_json_dumps,
        loads: data_binding.JSONDecoder = data_binding.default_json_loads,
        initial_activity: typing.Optional[presences.Activity] = None,
        initial_idle_since: typing.Optional[datetime.datetime] = None,
        initial_is_afk: bool = False,
        initial_status: presences.Status = presences.Status.ONLINE,
        intents: intents_.Intents,
        large_threshold: int = 250,
        shard_id: int = 0,
        shard_count: int = 1,
        http_settings: config.HTTPSettings,
        proxy_settings: config.ProxySettings,
        data_format: str = shard.GatewayDataFormat.JSON,
        event_manager: event_manager_.EventManager,
        event_factory: event_factory_.EventFactory,
        token: str,
        url: str,
    ) -> None:
        if data_format != shard.GatewayDataFormat.JSON:
            raise NotImplementedError(f"Unsupported gateway data format: {data_format}")

        if compression and compression != shard.GatewayCompression.TRANSPORT_ZLIB_STREAM:
            raise NotImplementedError(f"Unsupported compression format {compression}")

        self._activity = initial_activity
        self._event_manager = event_manager
        self._event_factory = event_factory
        self._gateway_url = url
        self._handshake_event: typing.Optional[asyncio.Event] = None
        self._heartbeat_latency = float("nan")
        self._http_settings = http_settings
        self._idle_since = initial_idle_since
        self._intents = intents
        self._is_afk = initial_is_afk
        self._is_closing = False
        self._keep_alive_task: typing.Optional[asyncio.Task[None]] = None
        self._large_threshold = large_threshold
        self._last_heartbeat_ack_received = float("nan")
        self._last_heartbeat_sent = float("nan")
        self._logger = logging.getLogger(f"hikari.gateway.{shard_id}")
        self._non_priority_rate_limit = rate_limits.WindowedBurstRateLimiter(
            f"shard {shard_id} non-priority rate limit", *_NON_PRIORITY_RATELIMIT
        )
        self._proxy_settings = proxy_settings
        self._resume_gateway_url: typing.Optional[str] = None
        self._seq: typing.Optional[int] = None
        self._session_id: typing.Optional[str] = None
        self._shard_count = shard_count
        self._shard_id = shard_id
        self._status = initial_status
        self._token = token
        self._total_rate_limit = rate_limits.WindowedBurstRateLimiter(
            f"shard {shard_id} total rate limit", *_TOTAL_RATELIMIT
        )
        self._transport_compression = compression is not None
        self._dumps = dumps
        self._loads = loads
        self._user_id: typing.Optional[snowflakes.Snowflake] = None
        self._ws: typing.Optional[_GatewayTransport] = None

    @property
    def heartbeat_latency(self) -> float:
        return self._heartbeat_latency

    @property
    def id(self) -> int:
        return self._shard_id

    @property
    def intents(self) -> intents_.Intents:
        return self._intents

    @property
    def is_alive(self) -> bool:
        return self._keep_alive_task is not None

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and self._handshake_event is not None and self._handshake_event.is_set()

    @property
    def shard_count(self) -> int:
        return self._shard_count

    async def close(self) -> None:
        if not self._keep_alive_task:
            raise errors.ComponentStateConflictError("Cannot close an inactive shard")

        if self._is_closing:
            await self.join()
            return

        self._logger.info("shard has been requested to shutdown")
        self._is_closing = True

        self._keep_alive_task.cancel()
        try:
            await self._keep_alive_task
        except asyncio.CancelledError:
            pass

        self._keep_alive_task = None
        self._non_priority_rate_limit.close()
        self._total_rate_limit.close()
        self._is_closing = False
        self._logger.info("shard shutdown successfully")

    def get_user_id(self) -> snowflakes.Snowflake:
        self._check_if_connected()
        assert self._user_id is not None, "user_id was not known, this is probably a bug"
        return self._user_id

    async def join(self) -> None:
        if not self._keep_alive_task:
            raise errors.ComponentStateConflictError("Cannot join an inactive shard")

        await asyncio.wait_for(asyncio.shield(self._keep_alive_task), timeout=None)

    async def _send_json(self, data: data_binding.JSONObject, /, priority: bool = False) -> None:
        if not priority:
            await self._non_priority_rate_limit.acquire()

        await self._total_rate_limit.acquire()

        assert self._ws is not None
        await self._ws.send_json(data)

    def _check_if_connected(self) -> None:
        if not self.is_connected:
            raise errors.ComponentStateConflictError(
                f"shard {self._shard_id} is not connected so it cannot be interacted with"
            )

    async def request_guild_members(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        query: str = "",
        limit: int = 0,
        users: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[users_.User]] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        self._check_if_connected()
        if not query and not limit and not self._intents & intents_.Intents.GUILD_MEMBERS:
            raise errors.MissingIntentError(intents_.Intents.GUILD_MEMBERS)

        if include_presences and not self._intents & intents_.Intents.GUILD_PRESENCES:
            raise errors.MissingIntentError(intents_.Intents.GUILD_PRESENCES)

        if users is not undefined.UNDEFINED and (query or limit):
            raise ValueError("Cannot specify limit/query with users")

        if not 0 <= limit <= 100:
            raise ValueError("'limit' must be between 0 and 100, both inclusive")

        if users is not undefined.UNDEFINED and len(users) > 100:
            raise ValueError("'users' is limited to 100 users")

        if nonce is not undefined.UNDEFINED and len(bytes(nonce, "utf-8")) > 32:
            raise ValueError("'nonce' can be no longer than 32 byte characters long.")

        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("guild_id", guild)
        payload.put("presences", include_presences)
        payload.put("query", query)
        payload.put("limit", limit)
        payload.put_snowflake_array("user_ids", users)
        payload.put("nonce", nonce)

        await self._send_json({_OP: _REQUEST_GUILD_MEMBERS, _D: payload})

    async def start(self) -> None:
        if self._keep_alive_task or self._handshake_event:
            raise errors.ComponentStateConflictError("Cannot run more than one instance of one shard concurrently")

        self._handshake_event = asyncio.Event()
        keep_alive_task = asyncio.create_task(self._keep_alive(), name=f"keep alive (shard {self._shard_id})")

        await aio.first_completed(self._handshake_event.wait(), asyncio.shield(keep_alive_task))

        if not self._handshake_event.is_set():
            # This might throw an error, or it might not, depending on what we do with it.
            # This occurs if the run task finished before the handshake completion event,
            # which implies the shard died before it could become ready/resume...
            keep_alive_task.result()
            raise RuntimeError(f"shard {self._shard_id} was closed before it could start successfully")

        self._keep_alive_task = keep_alive_task

    async def update_presence(
        self,
        *,
        idle_since: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        afk: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        activity: undefined.UndefinedNoneOr[presences.Activity] = undefined.UNDEFINED,
        status: undefined.UndefinedOr[presences.Status] = undefined.UNDEFINED,
    ) -> None:
        self._check_if_connected()
        presence_payload = self._serialize_and_store_presence_payload(
            idle_since=idle_since, afk=afk, activity=activity, status=status
        )
        await self._send_json({_OP: _PRESENCE_UPDATE, _D: presence_payload})

    async def update_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: typing.Optional[snowflakes.SnowflakeishOr[channels.GuildVoiceChannel]],
        *,
        self_mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        self_deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> None:
        self._check_if_connected()

        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("guild_id", guild)
        payload.put_snowflake("channel_id", channel)
        payload.put("self_mute", self_mute)
        payload.put("self_deaf", self_deaf)

        await self._send_json({_OP: _VOICE_STATE_UPDATE, _D: payload})

    async def _send_heartbeat(self) -> None:
        self._logger.log(ux.TRACE, "sending HEARTBEAT [s:%s]", self._seq)
        await self._send_json({_OP: _HEARTBEAT, _D: self._seq}, priority=True)
        self._last_heartbeat_sent = time.monotonic()

    async def _heartbeat(self, heartbeat_interval: float) -> None:
        # Prevent immediately zombie-ing.
        self._last_heartbeat_ack_received = time.monotonic()
        self._logger.debug("starting heartbeat with interval %ss", heartbeat_interval)

        while True:
            if self._last_heartbeat_ack_received <= self._last_heartbeat_sent:
                # Gateway is zombie, close and request reconnect.
                self._logger.error(
                    "connection has not received a HEARTBEAT_ACK for approx %.1fs and is being disconnected; "
                    "will attempt to reconnect",
                    time.monotonic() - self._last_heartbeat_ack_received,
                )
                return

            await self._send_heartbeat()

            await asyncio.sleep(heartbeat_interval)

    async def _poll_events(self) -> None:
        assert self._ws is not None
        assert self._handshake_event is not None

        while True:
            payload = await self._ws.receive_json()

            op = payload[_OP]

            if op == _DISPATCH:
                name = payload[_T]
                data = payload[_D]
                self._seq = payload[_S]

                self._logger.log(ux.TRACE, "dispatching %s with seq %s", name, self._seq)

                if name == _READY:
                    self._session_id = data["session_id"]
                    self._resume_gateway_url = data["resume_gateway_url"]
                    user_pl = data["user"]
                    self._user_id = snowflakes.Snowflake(user_pl["id"])

                    # TODO: Remove when rollout finishes
                    user = user_pl["username"] + (
                        "#" + user_pl["discriminator"] if user_pl["discriminator"] != "0" else ""
                    )
                    self._logger.info(
                        "shard is ready: %s guilds, %s (%s), session %r on v%s gateway",
                        len(data["guilds"]),
                        user,
                        self._user_id,
                        self._session_id,
                        data["v"],
                    )
                    self._handshake_event.set()

                elif name == _RESUMED:
                    self._logger.info("resumed session [session:%s, seq:%s]", self._session_id, self._seq)
                    self._handshake_event.set()

                try:
                    self._event_manager.consume_raw_event(name, self, data)
                except LookupError:
                    self._logger.debug("ignoring unknown event %s:\n    %r", name, data)

            elif op == _HEARTBEAT_ACK:
                now = time.monotonic()
                self._last_heartbeat_ack_received = now
                self._heartbeat_latency = now - self._last_heartbeat_sent
                self._logger.log(ux.TRACE, "received HEARTBEAT ACK in %.1fms", self._heartbeat_latency * 1_000)

            elif op == _HEARTBEAT:
                self._logger.log(ux.TRACE, "sending heartbeat as requested by gateway")
                await self._send_heartbeat()

            elif op == _RECONNECT:
                self._logger.info("received instruction to reconnect, will resume existing session")
                return

            elif op == _INVALID_SESSION:
                can_reconnect = payload[_D]  # We can resume if the payload data is [`true`][].
                if not can_reconnect:
                    self._logger.info("received invalid session, will need to start a new session")
                    self._seq = None
                    self._resume_gateway_url = None
                    self._session_id = None
                else:
                    self._logger.info("received invalid session, will resume existing session")

                return

            else:
                self._logger.log(ux.TRACE, "unknown opcode %s received, it will be ignored...", op)

    async def _connect(self) -> typing.Tuple[asyncio.Task[None], ...]:
        if self._ws is not None:
            raise errors.ComponentStateConflictError("Attempting to connect an already connected shard")

        assert self._handshake_event is not None

        url_parts = urllib.parse.urlparse(self._resume_gateway_url or self._gateway_url, allow_fragments=True)

        query = dict(urllib.parse.parse_qsl(url_parts.query))
        query["v"] = str(urls.VERSION)
        query["encoding"] = "json"

        if self._transport_compression:
            query["compress"] = "zlib-stream"

        url = urllib.parse.urlunparse(
            (url_parts.scheme, url_parts.netloc, url_parts.path, url_parts.params, urllib.parse.urlencode(query), "")
        )

        self._ws = await _GatewayTransport.connect(
            http_settings=self._http_settings,
            log_filterer=_log_filterer(self._token),
            logger=self._logger,
            proxy_settings=self._proxy_settings,
            transport_compression=self._transport_compression,
            loads=self._loads,
            dumps=self._dumps,
            url=url,
        )

        # Expect initial HELLO
        hello_payload = await self._ws.receive_json()
        if hello_payload[_OP] != _HELLO:
            self._logger.debug(
                "expected %s (HELLO) opcode, received %s which makes no sense, closing with PROTOCOL ERROR",
                _HELLO,
                hello_payload[_OP],
            )
            await self._ws.send_close(code=errors.ShardCloseCode.PROTOCOL_ERROR, message=b"Expected HELLO op")
            raise errors.GatewayError(f"Expected opcode {_HELLO} (HELLO), but received {hello_payload[_OP]}")

        # Spawn lifetime tasks
        heartbeat_interval = float(hello_payload[_D]["heartbeat_interval"]) / 1_000.0
        heartbeat_task = asyncio.create_task(
            self._heartbeat(heartbeat_interval), name=f"heartbeat (shard {self._shard_id})"
        )
        poll_events_task = asyncio.create_task(self._poll_events(), name=f"poll events (shard {self._shard_id})")

        # Rate-limits are imposed per websocket connection
        self._total_rate_limit.close()
        self._non_priority_rate_limit.close()

        # Perform handshake
        if self._seq is None:
            self._logger.info("identifying with new session")
            await self._send_json(
                {
                    _OP: _IDENTIFY,
                    _D: {
                        "token": self._token,
                        "compress": False,
                        "large_threshold": self._large_threshold,
                        "properties": {
                            "os": f"{platform.system()} {platform.architecture()[0]}",
                            "browser": f"hikari ({about.__version__}, aiohttp {aiohttp.__version__})",
                            "device": f"hikari {about.__version__}",
                        },
                        "shard": [self._shard_id, self._shard_count],
                        "intents": self._intents,
                        "presence": self._serialize_and_store_presence_payload(),
                    },
                }
            )
        else:
            self._logger.info("resuming session %s", self._session_id)
            await self._send_json(
                {_OP: _RESUME, _D: {"token": self._token, "seq": self._seq, "session_id": self._session_id}}
            )

        lifetime_tasks = (heartbeat_task, poll_events_task)

        await aio.first_completed(self._handshake_event.wait(), *(asyncio.shield(t) for t in lifetime_tasks))

        return lifetime_tasks

    async def _keep_alive(self) -> None:
        assert self._handshake_event is not None

        lifetime_tasks: typing.Tuple[asyncio.Task[None], ...] = ()
        last_started_at = -float("inf")
        backoff = rate_limits.ExponentialBackOff(base=_BACKOFF_BASE, maximum=_BACKOFF_CAP)

        while True:
            self._handshake_event.clear()

            if time.monotonic() - last_started_at < _BACKOFF_WINDOW:
                backoff_time = next(backoff)
                self._logger.info("backing off reconnecting for %.2fs", backoff_time)
                await asyncio.sleep(backoff_time)

            try:
                last_started_at = time.monotonic()
                lifetime_tasks = await self._connect()

                if not self._handshake_event.is_set():
                    continue

                await self._event_manager.dispatch(self._event_factory.deserialize_connected_event(self))
                await aio.first_completed(*lifetime_tasks)

                # Since nothing went wrong, we can reset the backoff and try again
                backoff.reset()

            except ConnectionResetError:
                self._logger.warning("connection got reset by server. Will retry shortly")

            except errors.GatewayConnectionError as ex:
                self._logger.warning("failed to communicate with server, reason was: %r. Will retry shortly", ex.reason)

            except errors.GatewayServerClosedConnectionError as ex:
                if not ex.can_reconnect:
                    self._logger.info(
                        "server has closed the connection permanently [code:%s, reason:%s]", ex.code, ex.reason
                    )
                    raise

                self._logger.info(
                    "server has closed the connection, will attempt to reconnect [code:%s, reason:%s]",
                    ex.code,
                    ex.reason,
                )

                # We don't want to back off from this. If Discord keep closing the connection, it is their issue.
                # If we back off here, we'll find a mass outage will prevent shards from becoming healthy on
                # reconnect in large sharded bots for a very long period of time.
                backoff.reset()

            except errors.GatewayError as ex:
                self._logger.error("encountered gateway error", exc_info=ex)
                raise

            except asyncio.CancelledError:
                self._is_closing = True
                return

            except Exception as ex:
                self._logger.error("encountered some unhandled error", exc_info=ex)
                raise

            finally:
                # Cancel any left-over tasks
                for task in lifetime_tasks:
                    if not task.done() and not task.cancelled():
                        task.cancel()

                        try:
                            await task
                        except asyncio.CancelledError:
                            pass

                # Close the ws
                if self._ws:
                    ws = self._ws
                    self._ws = None

                    if self._is_closing:
                        await ws.send_close(
                            code=errors.ShardCloseCode.GOING_AWAY, message=b"shard disconnecting permanently"
                        )
                    else:
                        await ws.send_close(code=_RESUME_CLOSE_CODE, message=b"shard disconnecting temporarily")

                    if self._handshake_event.is_set():
                        # We dispatched the connected event, so we can dispatch the disconnected one too
                        await self._event_manager.dispatch(self._event_factory.deserialize_disconnected_event(self))

    def _serialize_and_store_presence_payload(
        self,
        idle_since: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        afk: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        status: undefined.UndefinedOr[presences.Status] = undefined.UNDEFINED,
        activity: undefined.UndefinedNoneOr[presences.Activity] = undefined.UNDEFINED,
    ) -> data_binding.JSONObject:
        if activity is undefined.UNDEFINED:
            activity = self._activity
        else:
            self._activity = activity

        if status is undefined.UNDEFINED:
            status = self._status
        else:
            self._status = status

        if idle_since is undefined.UNDEFINED:
            idle_since = self._idle_since
        else:
            self._idle_since = idle_since

        if afk is undefined.UNDEFINED:
            afk = self._is_afk
        else:
            self._is_afk = afk

        payload = data_binding.JSONObjectBuilder()
        payload.put("since", idle_since, conversion=_serialize_datetime)
        payload.put("afk", afk)
        payload.put("game", activity, conversion=_serialize_activity)
        # Sending "offline" to the gateway won't do anything, we will have to
        # send "invisible" instead for this to work.
        payload.put("status", "invisible" if status is presences.Status.OFFLINE else status)
        return payload
