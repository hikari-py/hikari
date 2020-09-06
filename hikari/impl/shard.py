# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
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
"""Single-shard implementation for the V6 and V7 event gateway for Discord."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["GatewayShardImpl"]

import asyncio
import contextlib
import http
import json
import logging
import typing
import urllib.parse
import zlib

import aiohttp

from hikari import errors
from hikari import intents as intents_
from hikari import presences
from hikari import snowflakes
from hikari import undefined
from hikari.api import shard
from hikari.impl import rate_limits
from hikari.utilities import constants
from hikari.utilities import data_binding
from hikari.utilities import date

if typing.TYPE_CHECKING:
    import datetime

    import aiohttp.http_websocket
    import aiohttp.typedefs

    from hikari import channels
    from hikari import config
    from hikari import guilds
    from hikari import users as users_

# Opcodes.
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
# If we disconnect within this period of time after starting, we should
# use an exponential backoff before restarting.
_BACKOFF_WINDOW: typing.Final[float] = 30.0
_BACKOFF_BASE: typing.Final[float] = 1.85
_BACKOFF_INCREMENT_START: typing.Final[int] = 2
_BACKOFF_CAP: typing.Final[float] = 600.0
# Ping-pong. Might disable this eventually.
_PING_PONG_HEARTBEAT_LATENCY: typing.Optional[float] = 20.0
# Discord seems to invalidate sessions if I send a 1xxx, which is useless
# for invalid session and reconnect messages where I want to be able to
# resume.
_RESUME_CLOSE_CODE: typing.Final[int] = 3_000
# Per-shard sending rate-limit
_TOTAL_RATELIMIT: typing.Final[typing.Tuple[float, int]] = (60.0, 120)
# Rate-limit for chunking requests (used to prevent saturating the entire
# ratelimit window).
_CHUNKING_RATELIMIT: typing.Final[typing.Tuple[float, int]] = (60.0, 60)


@typing.final
class _V6GatewayTransport(aiohttp.ClientWebSocketResponse):
    """Internal component to handle lower-level communication logic.

    This includes translating aiohttp error conditions to hikari ones,
    handling inbound zlib packets, creating the websocket and client session,
    and ensuring all resources are freed deterministically where possible.

    Payload logging is also performed here.
    """

    __slots__: typing.Sequence[str] = ("_zlib", "_logger", "_debug")

    # Initialized from `connect'
    _zlib: zlib._Decompress
    _logger: logging.Logger
    _debug: bool

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        self._zlib = zlib.decompressobj()

    def close(self, *, code: int = 1000, message: bytes = b"") -> typing.Coroutine[typing.Any, typing.Any, bool]:
        if not self._closed and not self._closing:
            self._logger.debug("sending close frame with code %s and message %s", int(code), message)
        return super().close(code=code, message=message)

    async def receive_json(
        self,
        *,
        loads: aiohttp.typedefs.JSONDecoder = json.loads,
        timeout: typing.Optional[float] = None,
    ) -> typing.Any:
        pl = await self._receive_and_check(timeout)
        self._log_debug_payload(pl, "received")
        return loads(pl)

    async def send_json(
        self,
        data: data_binding.JSONObject,
        compress: typing.Optional[int] = None,
        *,
        dumps: aiohttp.typedefs.JSONEncoder = json.dumps,
    ) -> None:
        pl = dumps(data)
        self._log_debug_payload(pl, "sending")
        await self.send_str(pl, compress)

    async def _receive_and_check(self, timeout: typing.Optional[float], /) -> str:
        buff = bytearray()

        while True:
            message = await self.receive(timeout)

            if message.type == aiohttp.WSMsgType.CLOSE:
                close_code = int(message.data)
                reason = message.extra
                self._logger.error("connection closed with code %s (%s)", close_code, reason)

                can_reconnect = close_code < 4000 or close_code in (
                    errors.ShardCloseCode.DECODE_ERROR,
                    errors.ShardCloseCode.INVALID_SEQ,
                    errors.ShardCloseCode.UNKNOWN_ERROR,
                    errors.ShardCloseCode.SESSION_TIMEOUT,
                    errors.ShardCloseCode.RATE_LIMITED,
                )

                # Assume we can always resume first.
                raise errors.GatewayServerClosedConnectionError(reason, close_code, can_reconnect)

            elif message.type == aiohttp.WSMsgType.CLOSING or message.type == aiohttp.WSMsgType.CLOSED:
                raise asyncio.CancelledError("Socket closed")

            elif message.type == aiohttp.WSMsgType.BINARY:
                buff += message.data

                if buff.endswith(b"\x00\x00\xff\xff"):
                    return self._zlib.decompress(buff).decode("utf-8")
            elif message.type == aiohttp.WSMsgType.TEXT:
                return message.data  # type: ignore
            else:
                # Assume exception for now.
                ex = self.exception()
                self._logger.warning(
                    "encountered unexpected error: %s",
                    ex,
                    exc_info=ex if self._logger.isEnabledFor(logging.DEBUG) else None,
                )
                raise errors.GatewayError("Unexpected websocket exception from gateway") from ex

    def _log_debug_payload(self, payload: str, message: str, /) -> None:
        if self._debug:
            self._logger.debug("%s payload with size %s\n\t\t%s", message, len(payload), payload)
        else:
            self._logger.debug("%s payload with size %s", message, len(payload))

    @classmethod
    @contextlib.asynccontextmanager
    async def connect(
        cls,
        *,
        debug: bool,
        http_config: config.HTTPSettings,
        logger: logging.Logger,
        proxy_config: config.ProxySettings,
        url: str,
    ) -> typing.AsyncGenerator[_V6GatewayTransport, None]:
        """Generate a single-use websocket connection.

        This uses a single connection in a TCP connector pool, with a one-use
        aiohttp client session.

        This also handles waiting for transports to be closed properly first,
        and keeps all of the nested boilerplate out of the way of the
        rest of the code, for the most part anyway.
        """
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(
                    enable_cleanup_closed=True,
                    force_close=True,
                    limit=1,
                    use_dns_cache=False,
                    verify_ssl=http_config.verify_ssl,
                ),
                raise_for_status=True,
                timeout=aiohttp.ClientTimeout(
                    total=http_config.timeouts.total,
                    connect=http_config.timeouts.acquire_and_connect,
                    sock_read=http_config.timeouts.request_socket_read,
                    sock_connect=http_config.timeouts.request_socket_connect,
                ),
                trust_env=proxy_config.trust_env,
                ws_response_class=cls,
            ) as cs:
                try:
                    async with cs.ws_connect(
                        heartbeat=_PING_PONG_HEARTBEAT_LATENCY,
                        max_msg_size=0,
                        proxy=proxy_config.url,
                        proxy_headers=proxy_config.headers,
                        url=url,
                    ) as ws:
                        raised = False
                        try:
                            assert isinstance(ws, cls)
                            ws._logger = logger
                            ws._debug = debug

                            yield ws
                        except errors.GatewayError:
                            raised = True
                            raise
                        except Exception as ex:
                            raised = True
                            raise errors.GatewayError(f"Unexpected {type(ex).__name__}: {ex}") from ex
                        finally:
                            if ws.closed:
                                return

                            if raised:
                                await ws.close(
                                    code=errors.ShardCloseCode.UNEXPECTED_CONDITION,
                                    message=b"unexpected fatal client error :-(",
                                )
                                return

                            if not ws._closing:
                                # We use a special close code here that prevents Discord
                                # randomly invalidating our session. Undocumented behaviour is
                                # nice like that...
                                await ws.close(
                                    code=_RESUME_CLOSE_CODE,
                                    message=b"client is shutting down",
                                )

                except aiohttp.ClientConnectionError as ex:
                    message = f"Failed to connect to Discord: {ex!r}"
                    raise errors.GatewayError(message) from ex

                except aiohttp.WSServerHandshakeError as ex:
                    if ex.status in http.HTTPStatus.__members__.values():
                        reason = str(http.HTTPStatus(ex.status))
                    else:
                        reason = "Unknown Reason"

                    message = (
                        f"Discord produced a {ex.status} {reason} response "
                        f"when attempting to upgrade to a websocket: {ex.message!r}"
                    )

                    raise errors.GatewayError(message) from ex
        finally:
            # We have to sleep to allow aiohttp time to close SSL transports...
            # https://github.com/aio-libs/aiohttp/issues/1925
            # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
            await asyncio.sleep(0.25)


@typing.final
class GatewayShardImpl(shard.GatewayShard):
    """Implementation of a V6 and V7 compatible gateway.

    Parameters
    ----------
    compression : typing.Optional[buitlins.str]
        Compression format to use for the shard. Only supported values are
        `"payload_zlib_stream"` or `builtins.None` to disable it.
    data_format : builtins.str
        Data format to use for inbound data. Only supported format is
        `"json"`.
    debug : builtins.bool
        If `builtins.True`, each sent and received payload is dumped to the
        logs. If `builtins.False`, only the fact that data has been
        sent/received will be logged.
    event_consumer
        A non-coroutine function consuming a `GatewayShardImpl`,
        a `builtins.str` event name, and a
        `hikari.utilities.data_binding.JSONObject` event object as parameters.
        This should return `builtins.None`, and will be called with each event
        that fires.
    http_settings : hikari.config.HTTPSettings
        The HTTP-related settings to use while negotiating a websocket.
    initial_activity : typing.Optional[hikari.presences.Activity]
        The initial activity to appear to have for this shard, or
        `builtins.None` if no activity should be set initially. This is the
        default.
    initial_idle_since : typing.Optional[datetime.datetime]
        The datetime to appear to be idle since, or `builtins.None` if the
        shard should not provide this. The default is `builtins.None`.
    initial_is_afk : bool
        Whether to appear to be AFK or not on login. Defaults to
        `builtins.False`.
    initial_status : hikari.presences.Status
        The initial status to set on login for the shard. Defaults to
        `hikari.presences.Status.ONLINE`.
    intents : typing.Optional[hikari.intents.Intents]
        Collection of intents to use, or `builtins.None` to not use intents at
        all.
    large_threshold : builtins.int
        The number of members to have in a guild for it to be considered large.
    proxy_settings : hikari.config.ProxySettings
        The proxy settings to use while negotiating a websocket.
    shard_id : builtins.int
        The shard ID.
    shard_count : builtins.int
        The shard count.
    token : builtins.str
        The bot token to use.
    url : builtins.str
        The gateway URL to use. This should not contain a query-string or
        fragments.
    version : builtins.int
        Gateway API version to use.

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
    """

    __slots__: typing.Sequence[str] = (
        "_activity",
        "_closed",
        "_closing",
        "_chunking_rate_limit",
        "_debug",
        "_event_consumer",
        "_handshake_completed",
        "_heartbeat_latency",
        "_http_settings",
        "_idle_since",
        "_intents",
        "_is_afk",
        "_large_threshold",
        "_last_heartbeat_ack_received",
        "_last_heartbeat_sent",
        "_logger",
        "_proxy_settings",
        "_run_task",
        "_seq",
        "_session_id",
        "_shard_count",
        "_shard_id",
        "_status",
        "_token",
        "_total_rate_limit",
        "_url",
        "_user_id",
        "_ws",
    )

    def __init__(
        self,
        *,
        compression: typing.Optional[str] = shard.GatewayCompression.PAYLOAD_ZLIB_STREAM,
        data_format: str = shard.GatewayDataFormat.JSON,
        debug: bool = False,
        event_consumer: typing.Callable[[shard.GatewayShard, str, data_binding.JSONObject], None],
        http_settings: config.HTTPSettings,
        initial_activity: typing.Optional[presences.Activity] = None,
        initial_idle_since: typing.Optional[datetime.datetime] = None,
        initial_is_afk: bool = False,
        initial_status: presences.Status = presences.Status.ONLINE,
        intents: typing.Optional[intents_.Intents] = None,
        large_threshold: int = 250,
        proxy_settings: config.ProxySettings,
        shard_id: int = 0,
        shard_count: int = 1,
        token: str,
        url: str,
        version: int = 6,
    ) -> None:

        if data_format != shard.GatewayDataFormat.JSON:
            raise NotImplementedError(f"Unsupported gateway data format: {data_format}")

        query = {"v": version, "encoding": data_format}

        if compression is not None:
            if compression == shard.GatewayCompression.PAYLOAD_ZLIB_STREAM:
                query["compress"] = "zlib-stream"
            else:
                raise NotImplementedError(f"Unsupported compression format {compression}")

        scheme, netloc, path, params, _, _ = urllib.parse.urlparse(url, allow_fragments=True)
        new_query = urllib.parse.urlencode(query)

        self._activity = initial_activity
        self._closing = asyncio.Event()
        self._closed = asyncio.Event()
        self._chunking_rate_limit = rate_limits.WindowedBurstRateLimiter(
            f"shard {shard_id} chunking rate limit",
            *_CHUNKING_RATELIMIT,
        )
        self._debug = debug
        self._event_consumer = event_consumer
        self._handshake_completed = asyncio.Event()
        self._heartbeat_latency = float("nan")
        self._http_settings = http_settings
        self._idle_since = initial_idle_since
        self._intents = intents
        self._is_afk = initial_is_afk
        self._large_threshold = large_threshold
        self._last_heartbeat_ack_received = float("nan")
        self._last_heartbeat_sent = float("nan")
        self._logger = logging.getLogger(f"hikari.gateway.{shard_id}")
        self._proxy_settings = proxy_settings
        self._run_task: typing.Optional[asyncio.Task[None]] = None
        self._seq: typing.Optional[int] = None
        self._session_id: typing.Optional[str] = None
        self._shard_count = shard_count
        self._shard_id = shard_id
        self._status = initial_status
        self._token = token
        self._total_rate_limit = rate_limits.WindowedBurstRateLimiter(
            f"shard {shard_id} total rate limit",
            *_TOTAL_RATELIMIT,
        )
        self._url = urllib.parse.urlunparse((scheme, netloc, path, params, new_query, ""))
        self._user_id: typing.Optional[snowflakes.Snowflake] = None
        self._ws: typing.Optional[_V6GatewayTransport] = None

    @property
    def heartbeat_latency(self) -> float:
        return self._heartbeat_latency

    @property
    def id(self) -> int:
        return self._shard_id

    @property
    def intents(self) -> typing.Optional[intents_.Intents]:
        return self._intents

    @property
    def is_alive(self) -> bool:
        return self._run_task is not None and not self._run_task.done()

    @property
    def shard_count(self) -> int:
        return self._shard_count

    async def close(self) -> None:
        if not self._closing.is_set():
            try:
                if self._ws is not None:
                    await self._ws.close(code=errors.ShardCloseCode.GOING_AWAY, message=b"shard disconnecting")
                self._closing.set()
            finally:
                self._chunking_rate_limit.close()
                self._total_rate_limit.close()

    async def get_user_id(self) -> snowflakes.Snowflake:
        await self._handshake_completed.wait()
        if self._user_id is None:
            raise RuntimeError("user_id was not known, this is probably a bug")
        return self._user_id

    async def join(self) -> None:
        """Wait for this shard to close, if running."""
        await self._closed.wait()

    async def request_guild_members(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        query: str = "",
        limit: int = 0,
        users: undefined.UndefinedOr[typing.Sequence[snowflakes.SnowflakeishOr[users_.User]]] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        if self._intents is not None:
            if not query and not limit and not self._intents & intents_.Intents.GUILD_MEMBERS:
                raise errors.MissingIntentError(intents_.Intents.GUILD_MEMBERS)

            if include_presences is not undefined.UNDEFINED and not self._intents & intents_.Intents.GUILD_PRESENCES:
                raise errors.MissingIntentError(intents_.Intents.GUILD_PRESENCES)

        if users is not undefined.UNDEFINED and (query or limit):
            raise ValueError("Cannot specify limit/query with users")

        if not 0 <= limit <= 100:
            raise ValueError("'limit' must be between 0 and 100, both inclusive")

        if users is not undefined.UNDEFINED and len(users) > 100:
            raise ValueError("'users' is limited to 100 users")

        if nonce is not undefined.UNDEFINED and len(bytes(nonce, "utf-8")) > 32:
            raise ValueError("'nonce' can be no longer than 32 byte characters long.")

        await self._chunking_rate_limit.acquire()
        message = "requesting guild members for guild %s"
        if include_presences:
            message += " with presences"
        self._logger.debug(message, int(guild))

        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("guild_id", guild)
        payload.put("presences", include_presences)
        payload.put("query", query)
        payload.put("limit", limit)
        payload.put_snowflake_array("user_ids", users)
        payload.put("nonce", nonce)

        await self._ws.send_json({"op": _REQUEST_GUILD_MEMBERS, "d": payload})  # type: ignore[union-attr]

    async def start(self) -> None:
        if self._run_task is not None:
            raise RuntimeError("Cannot run more than one instance of one shard concurrently")

        run_task = asyncio.create_task(self._run(), name=f"run shard {self._shard_id}")
        self._run_task = run_task
        waiter = asyncio.create_task(self._handshake_completed.wait(), name=f"wait for shard {self._shard_id} to start")
        done, _ = await asyncio.wait((waiter, run_task), return_when=asyncio.FIRST_COMPLETED)
        waiter.cancel()

        if done and waiter not in done:
            # This might throw an error, or it might not, depending on what we do with it.
            # This occurs if the run task finished before the handshake completion event,
            # which implies the shard died before it could become ready/resume...
            self._run_task = None
            run_task.result()
            raise asyncio.CancelledError(f"Shard {self._shard_id} was closed before it could start successfully")

    async def update_presence(
        self,
        *,
        idle_since: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        afk: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        activity: undefined.UndefinedNoneOr[presences.Activity] = undefined.UNDEFINED,
        status: undefined.UndefinedOr[presences.Status] = undefined.UNDEFINED,
    ) -> None:
        presence_payload = self._serialize_and_store_presence_payload(
            idle_since=idle_since,
            afk=afk,
            activity=activity,
            status=status,
        )
        payload: data_binding.JSONObject = {"op": _PRESENCE_UPDATE, "d": presence_payload}
        await self._ws.send_json(payload)  # type: ignore[union-attr]

    async def update_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: typing.Optional[snowflakes.SnowflakeishOr[channels.GuildVoiceChannel]],
        *,
        self_mute: bool = False,
        self_deaf: bool = False,
    ) -> None:
        await self._ws.send_json(  # type: ignore[union-attr]
            {
                "op": _VOICE_STATE_UPDATE,
                "d": {
                    "guild_id": str(int(guild)),
                    "channel_id": str(int(channel)) if channel is not None else None,
                    "mute": self_mute,
                    "deaf": self_deaf,
                },
            }
        )

    def _dispatch(self, name: str, seq: int, data: data_binding.JSONObject) -> None:
        # This is invoked a lot, and we don't need to explicitly await anything, so it should
        # not be a coroutine. Makes event dispatches much much faster under significant load.

        self._seq = seq

        if name == "READY":
            self._session_id = data["session_id"]
            user_pl = data["user"]
            user_id = user_pl["id"]
            self._user_id = snowflakes.Snowflake(user_id)
            tag = user_pl["username"] + "#" + user_pl["discriminator"]
            self._logger.info(
                "shard is ready [session:%s, user_id:%s, tag:%s]",
                self._session_id,
                user_id,
                tag,
            )
            self._handshake_completed.set()

        elif name == "RESUME":
            self._logger.info("shard has resumed [session:%s, seq:%s]", self._session_id, self._seq)
            self._handshake_completed.set()

        self._event_consumer(self, name, data)

    async def _identify(self) -> None:
        payload: data_binding.JSONObject = {
            "op": _IDENTIFY,
            "d": {
                "token": self._token,
                "compress": False,
                "large_threshold": self._large_threshold,
                "properties": {
                    "$os": constants.SYSTEM_TYPE,
                    "$browser": constants.AIOHTTP_VERSION,
                    "$device": constants.LIBRARY_VERSION,
                },
                "shard": [self._shard_id, self._shard_count],
            },
        }

        if self._intents is not None:
            payload["d"]["intents"] = self._intents

        payload["d"]["presence"] = self._serialize_and_store_presence_payload()

        await self._ws.send_json(payload)  # type: ignore[union-attr]

    async def _heartbeat(self, heartbeat_interval: float) -> bool:
        # Return True if zombied.
        # Prevent immediately zombie-ing.
        self._last_heartbeat_ack_received = date.monotonic()
        self._logger.debug("starting heartbeat with interval %ss", heartbeat_interval)

        while True:
            if self._last_heartbeat_ack_received <= self._last_heartbeat_sent:
                # Gateway is zombie
                return True

            self._logger.debug("preparing to send HEARTBEAT [s:%s, interval:%ss]", self._seq, heartbeat_interval)

            # TODO: Could this error, or can I just assume any other receiver will die first?
            await self._send_heartbeat()

            try:
                await asyncio.wait_for(self._closing.wait(), timeout=heartbeat_interval)
                # We are closing
                return False
            except asyncio.TimeoutError:
                # We should continue
                pass

    async def _resume(self) -> None:
        await self._ws.send_json(  # type: ignore[union-attr]
            {
                "op": _RESUME,
                "d": {"token": self._token, "seq": self._seq, "session_id": self._session_id},
            }
        )

    async def _run(self) -> None:
        self._closed.clear()
        last_started_at = -float("nan")

        backoff = rate_limits.ExponentialBackOff(
            base=_BACKOFF_BASE,
            maximum=_BACKOFF_CAP,
            initial_increment=_BACKOFF_INCREMENT_START,
        )

        try:
            while True:
                if date.monotonic() - last_started_at < _BACKOFF_WINDOW:
                    time = next(backoff)
                    self._logger.debug("backing off reconnecting for %.2fs to prevent spam", time)

                    try:
                        await asyncio.wait_for(self._closing.wait(), timeout=time)
                        # We were told to close.
                        return
                    except asyncio.TimeoutError:
                        # We are going to run once.
                        pass

                try:
                    if not await self._run_once():
                        self._logger.debug("shard has shut down")

                except errors.GatewayServerClosedConnectionError as ex:
                    if not ex.can_reconnect:
                        raise

                    self._logger.info(
                        "server has closed connection, will reconnect if possible [code:%s, reason:%s]",
                        ex.code,
                        ex.reason,
                    )

                except errors.GatewayError as ex:
                    self._logger.debug("encountered generic gateway error", exc_info=ex)
                    raise

                except Exception as ex:
                    self._logger.debug("encountered some unhandled error", exc_info=ex)
                    raise
        finally:
            self._closed.set()
            self._logger.info("shard %s has shut down permanently", self._shard_id)

    async def _run_once(self) -> bool:
        self._closing.clear()
        self._handshake_completed.clear()
        dispatch_disconnect = False
        try:
            async with _V6GatewayTransport.connect(
                debug=self._debug,
                http_config=self._http_settings,
                logger=self._logger,
                proxy_config=self._proxy_settings,
                url=self._url,
            ) as self._ws:
                # Dispatch CONNECTED synthetic event.
                self._event_consumer(self, "CONNECTED", {})
                dispatch_disconnect = True

                # Expect HELLO.
                payload = await self._ws.receive_json()
                if payload["op"] != _HELLO:
                    await self._ws.close(code=errors.ShardCloseCode.PROTOCOL_ERROR, message=b"Expected HELLO op")
                    raise errors.GatewayError(f"Expected opcode {_HELLO}, but received {payload['op']}")

                heartbeat_latency = float(payload["d"]["heartbeat_interval"]) / 1_000.0
                heartbeat_task = asyncio.create_task(self._heartbeat(heartbeat_latency))

                if self._closing.is_set():
                    await self._ws.close(code=errors.ShardCloseCode.GOING_AWAY, message=b"shard disconnecting")
                    return False

                try:
                    if self._seq is not None:
                        await self._resume()
                    else:
                        await self._identify()

                    if self._closing.is_set():
                        return False

                    # Event polling.
                    while not self._closing.is_set() and not heartbeat_task.done() and not heartbeat_task.cancelled():
                        payload = await self._ws.receive_json()
                        op = payload["op"]
                        d = payload["d"]

                        if op == _DISPATCH:
                            self._logger.debug("dispatching %s", payload["t"])
                            self._dispatch(payload["t"], payload["s"], d)
                        elif op == _HEARTBEAT:
                            await self._send_heartbeat_ack()
                            self._logger.debug("sent HEARTBEAT")
                        elif op == _HEARTBEAT_ACK:
                            now = date.monotonic()
                            self._last_heartbeat_ack_received = now
                            self._heartbeat_latency = now - self._last_heartbeat_sent
                            self._logger.debug("received HEARTBEAT ACK in %.1fms", self._heartbeat_latency * 1_000)
                        elif op == _RECONNECT:
                            # We should be able to resume...
                            self._logger.debug("received instruction to reconnect, will resume existing session")
                            return True
                        elif op == _INVALID_SESSION:
                            # We can resume if the payload was `true`.
                            if not d:
                                self._logger.debug("received invalid session, will need to start a new session")
                                self._seq = None
                                self._session_id = None
                            else:
                                self._logger.debug("received invalid session, will resume existing session")
                            return True
                        else:
                            self._logger.debug("unknown opcode %s received, it will be ignored...", op)

                    # If the heartbeat died due to an error, it should be raised here. We expect the heartbeat
                    # to always kill our connection if it dies.
                    # We return True if zombied
                    if await heartbeat_task:
                        now = date.monotonic()
                        self._logger.error(
                            "connection is a zombie, last heartbeat sent %ss ago",
                            now - self._last_heartbeat_sent,
                        )
                        return True
                    return False
                finally:

                    heartbeat_task.cancel()
        finally:
            self._ws = None
            if dispatch_disconnect:
                # If we managed to connect, we must always send the DISCONNECT event
                # afterwards.
                self._event_consumer(self, "DISCONNECTED", {})

    async def _send_heartbeat(self) -> None:
        await self._ws.send_json({"op": _HEARTBEAT, "d": self._seq})  # type: ignore[union-attr]
        self._last_heartbeat_sent = date.monotonic()

    async def _send_heartbeat_ack(self) -> None:
        await self._ws.send_json({"op": _HEARTBEAT_ACK, "d": None})  # type: ignore[union-attr]

    @staticmethod
    def _serialize_activity(activity: typing.Optional[presences.Activity]) -> data_binding.JSONish:
        if activity is None:
            return None

        return {"name": activity.name, "type": int(activity.type), "url": activity.url}

    def _serialize_and_store_presence_payload(
        self,
        idle_since: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        afk: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        status: undefined.UndefinedOr[presences.Status] = undefined.UNDEFINED,
        activity: undefined.UndefinedNoneOr[presences.Activity] = undefined.UNDEFINED,
    ) -> data_binding.JSONObject:
        payload = data_binding.JSONObjectBuilder()

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

        payload.put("since", idle_since, conversion=self._serialize_datetime)
        payload.put("afk", afk)
        payload.put("game", activity, conversion=self._serialize_activity)
        # Sending "offline" to the gateway wont do anything, we will have to
        # send "invisible" instead for this to work.
        if status is presences.Status.OFFLINE:
            payload.put("status", "invisible")
        else:
            payload.put("status", status)
        return payload

    @staticmethod
    def _serialize_datetime(dt: typing.Optional[datetime.datetime]) -> typing.Optional[int]:
        if dt is None:
            return None

        return int(dt.timestamp() * 1_000)
