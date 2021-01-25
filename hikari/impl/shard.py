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
"""Single-shard implementation for the V8 event gateway for Discord."""

from __future__ import annotations

__all__: typing.List[str] = ["GatewayShardImpl"]

import asyncio
import contextlib
import json
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
from hikari.api import shard
from hikari.impl import rate_limits
from hikari.internal import data_binding
from hikari.internal import net
from hikari.internal import time
from hikari.internal import ux

if typing.TYPE_CHECKING:
    import datetime

    import aiohttp.http_websocket
    import aiohttp.typedefs

    from hikari import channels
    from hikari import config
    from hikari import guilds
    from hikari import users as users_
    from hikari.api import event_factory as event_factory_
    from hikari.api import event_manager as event_manager_

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
# If we disconnect within this period of time after starting, we should
# use an exponential backoff before restarting.
_BACKOFF_WINDOW: typing.Final[float] = 30.0
_BACKOFF_BASE: typing.Final[float] = 1.85
_BACKOFF_INCREMENT_START: typing.Final[int] = 2
_BACKOFF_CAP: typing.Final[float] = 60.0
# Discord seems to invalidate sessions if I send a 1xxx, which is useless
# for invalid session and reconnect messages where I want to be able to
# resume.
_RESUME_CLOSE_CODE: typing.Final[int] = 3_000
# Per-shard sending rate-limit
_TOTAL_RATELIMIT: typing.Final[typing.Tuple[float, int]] = (60.0, 120)
# Rate-limit for chunking requests (used to prevent saturating the entire
# ratelimit window).
_CHUNKING_RATELIMIT: typing.Final[typing.Tuple[float, int]] = (60.0, 60)
# Supported gateway version
_VERSION: int = 8


def _log_filterer(token: str) -> typing.Callable[[str], str]:
    def filterer(entry: str) -> str:
        return entry.replace(token, "**REDACTED TOKEN**")

    return filterer


if typing.TYPE_CHECKING:
    # noinspection PyProtectedMember,PyUnresolvedReferences
    _ZlibDecompressor = zlib._Decompress


@typing.final
class _GatewayTransport(aiohttp.ClientWebSocketResponse):
    """Internal component to handle lower-level communication logic.

    This includes translating aiohttp error conditions to hikari ones,
    handling inbound zlib packets, creating the websocket and client session,
    and ensuring all resources are freed deterministically where possible.

    Payload logging is also performed here.
    """

    __slots__: typing.Sequence[str] = ("zlib", "logger", "log_filterer", "sent_close")

    # Initialized from `connect'
    zlib: _ZlibDecompressor
    logger: logging.Logger
    log_filterer: typing.Callable[[str], str]
    sent_close: bool

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        self.zlib = zlib.decompressobj()
        self.sent_close = False

    async def send_close(self, *, code: int = 1000, message: bytes = b"") -> bool:
        # aiohttp may close the socket by invoking close() internally. By giving
        # a different name, we can ensure aiohttp won't invoke this method.
        # We can then guarantee any call to this method was made by us, as
        # opposed to, for example, Windows injecting a spurious EOF when
        # something disconnects, which makes aiohttp just shut down as if we
        # did it.
        if not self.sent_close:
            self.sent_close = True
            self.logger.debug("sending close frame with code %s and message %s", int(code), message)
            try:
                return await asyncio.wait_for(super().close(code=code, message=message), timeout=5)
            except asyncio.TimeoutError:
                self.logger.debug("failed to send close frame in time, probably connection issues")
        return False

    async def receive_json(
        self,
        *,
        loads: aiohttp.typedefs.JSONDecoder = json.loads,
        timeout: typing.Optional[float] = None,
    ) -> typing.Any:
        pl = await self._receive_and_check(timeout)
        if self.logger.isEnabledFor(ux.TRACE):
            filtered = self.log_filterer(pl)  # type: ignore
            self.logger.log(ux.TRACE, "received payload with size %s\n    %s", len(pl), filtered)
        return loads(pl)

    async def send_json(
        self,
        data: data_binding.JSONObject,
        compress: typing.Optional[int] = None,
        *,
        dumps: aiohttp.typedefs.JSONEncoder = json.dumps,
    ) -> None:
        pl = dumps(data)
        if self.logger.isEnabledFor(ux.TRACE):
            filtered = self.log_filterer(pl)  # type: ignore
            self.logger.log(ux.TRACE, "sending payload with size %s\n    %s", len(pl), filtered)
        await self.send_str(pl, compress)

    async def _receive_and_check(self, timeout: typing.Optional[float], /) -> str:
        buff = bytearray()

        while True:
            message = await self.receive(timeout)

            if message.type == aiohttp.WSMsgType.CLOSE:
                close_code = int(message.data)
                reason = message.extra
                self.logger.error("connection closed with code %s (%s)", close_code, reason)

                can_reconnect = close_code < 4000 or close_code in (
                    errors.ShardCloseCode.UNKNOWN_ERROR,
                    errors.ShardCloseCode.DECODE_ERROR,
                    errors.ShardCloseCode.INVALID_SEQ,
                    errors.ShardCloseCode.SESSION_TIMEOUT,
                    errors.ShardCloseCode.RATE_LIMITED,
                )

                raise errors.GatewayServerClosedConnectionError(reason, close_code, can_reconnect)

            elif message.type == aiohttp.WSMsgType.CLOSING or message.type == aiohttp.WSMsgType.CLOSED:
                # May be caused by the server shutting us down.
                # May be caused by Windows injecting an EOF if something disconnects, as some
                # network drivers appear to do this.
                raise errors.GatewayConnectionError("Socket has closed")

            elif len(buff) != 0 and message.type != aiohttp.WSMsgType.BINARY:
                raise errors.GatewayError(f"Unexpected message type received {message.type.name}, expected BINARY")

            elif message.type == aiohttp.WSMsgType.BINARY:
                buff.extend(message.data)

                if buff.endswith(b"\x00\x00\xff\xff"):
                    return self.zlib.decompress(buff).decode("utf-8")

            elif message.type == aiohttp.WSMsgType.TEXT:
                return message.data  # type: ignore

            else:
                # Assume exception for now.
                ex = self.exception()
                self.logger.warning(
                    "encountered unexpected error: %s",
                    ex,
                    exc_info=ex if self.logger.isEnabledFor(logging.DEBUG) else None,
                )
                raise errors.GatewayError("Unexpected websocket exception from gateway") from ex

    @classmethod
    @contextlib.asynccontextmanager
    async def connect(
        cls,
        *,
        http_settings: config.HTTPSettings,
        logger: logging.Logger,
        proxy_settings: config.ProxySettings,
        log_filterer: typing.Callable[[str], str],
        url: str,
    ) -> typing.AsyncGenerator[_GatewayTransport, None]:
        """Generate a single-use websocket connection.

        This uses a single connection in a TCP connector pool, with a one-use
        aiohttp client session.

        This also handles waiting for transports to be closed properly first,
        and keeps all of the nested boilerplate out of the way of the
        rest of the code, for the most part anyway.
        """
        exit_stack = contextlib.AsyncExitStack()

        try:
            connector = net.create_tcp_connector(http_settings, dns_cache=False, limit=1)
            client_session = await exit_stack.enter_async_context(
                net.create_client_session(connector, True, http_settings, True, proxy_settings.trust_env, cls)
            )

            web_socket = await exit_stack.enter_async_context(
                client_session.ws_connect(
                    max_msg_size=0,
                    proxy=proxy_settings.url,
                    proxy_headers=proxy_settings.headers,
                    url=url,
                )
            )

            assert isinstance(web_socket, cls)

            raised = False
            try:
                web_socket.logger = logger
                # We store this so we can remove it from debug logs
                # which enables people to send me logs in issues safely.
                # Also MyPy raises a false positive about this...
                web_socket.log_filterer = log_filterer  # type: ignore

                yield web_socket
            except errors.GatewayError:
                raised = True
                raise
            except Exception as ex:
                raised = True
                raise errors.GatewayError(f"Unexpected {type(ex).__name__}: {ex}") from ex
            finally:
                if web_socket.closed:
                    logger.log(ux.TRACE, "ws was already closed")

                elif raised:
                    await web_socket.send_close(
                        code=errors.ShardCloseCode.UNEXPECTED_CONDITION,
                        message=b"unexpected fatal client error :-(",
                    )

                elif not web_socket._closing:
                    # We use a special close code here that prevents Discord
                    # randomly invalidating our session. Undocumented behaviour is
                    # nice like that...
                    await web_socket.send_close(
                        code=_RESUME_CLOSE_CODE,
                        message=b"client is shutting down",
                    )

        except (aiohttp.ClientOSError, aiohttp.ClientConnectionError, aiohttp.WSServerHandshakeError) as ex:
            # Windows will sometimes raise an aiohttp.ClientOSError
            # If we cannot do DNS lookup, this will fail with a ClientConnectionError
            # usually.
            #
            # aiohttp.WSServerHandshakeError has a really bad str, so we use the repr instead.
            if isinstance(ex, aiohttp.WSServerHandshakeError):
                reason = repr(ex)
            else:
                reason = str(ex)

            raise errors.GatewayConnectionError(reason) from None

        finally:
            await exit_stack.aclose()

            # We have to sleep to allow aiohttp time to close SSL transports...
            # https://github.com/aio-libs/aiohttp/issues/1925
            # https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
            await asyncio.sleep(0.25)


@typing.final
class GatewayShardImpl(shard.GatewayShard):
    """Implementation of a V8 compatible gateway.

    Parameters
    ----------
    token : builtins.str
        The bot token to use.
    url : builtins.str
        The gateway URL to use. This should not contain a query-string or
        fragments.
    event_manager : hikari.api.event_manager.EventManager
        The event manager this shard should make calls to.
    event_factory : hikari.api.event_factory.EventFactory
        The event factory this shard should use.

    Other Parameters
    ----------------
    compression : typing.Optional[buitlins.str]
        Compression format to use for the shard. Only supported values are
        `"payload_zlib_stream"` or `builtins.None` to disable it.
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
    intents : hikari.intents.Intents
        Collection of intents to use.
    large_threshold : builtins.int
        The number of members to have in a guild for it to be considered large.
    shard_id : builtins.int
        The shard ID.
    shard_count : builtins.int
        The shard count.
    http_settings : hikari.config.HTTPSettings
        The HTTP-related settings to use while negotiating a websocket.
    proxy_settings : hikari.config.ProxySettings
        The proxy settings to use while negotiating a websocket.
    data_format : builtins.str
        Data format to use for inbound data. Only supported format is
        `"json"`.

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
        "_event_manager",
        "_event_factory",
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

        query = {"v": _VERSION, "encoding": str(data_format)}

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
        self._event_manager = event_manager
        self._event_factory = event_factory
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
        return self._run_task is not None and not self._run_task.done()

    @property
    def shard_count(self) -> int:
        return self._shard_count

    async def close(self) -> None:
        if not self._closing.is_set():
            try:
                if self._ws is not None:
                    self._logger.debug(
                        "shard.close() was called and the websocket was still alive -- "
                        "disconnecting immediately with GOING AWAY"
                    )
                    await self._ws.send_close(code=errors.ShardCloseCode.GOING_AWAY, message=b"shard disconnecting")
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

    async def _send_json(
        self,
        data: data_binding.JSONObject,
        compress: typing.Optional[int] = None,
        *,
        dumps: aiohttp.typedefs.JSONEncoder = json.dumps,
    ) -> None:
        await self._total_rate_limit.acquire()

        await self._ws.send_json(data=data, compress=compress, dumps=dumps)  # type: ignore[union-attr]

    def _check_if_alive(self) -> None:
        if not self.is_alive:
            raise errors.ComponentNotRunningError(
                f"shard {self._shard_id} is not running so it cannot be interacted with"
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
        self._check_if_alive()
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

        await self._chunking_rate_limit.acquire()

        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("guild_id", guild)
        payload.put("presences", include_presences)
        payload.put("query", query)
        payload.put("limit", limit)
        payload.put_snowflake_array("user_ids", users)
        payload.put("nonce", nonce)

        await self._send_json({_OP: _REQUEST_GUILD_MEMBERS, _D: payload})

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
            raise asyncio.CancelledError(f"shard {self._shard_id} was closed before it could start successfully")

    async def update_presence(
        self,
        *,
        idle_since: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        afk: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        activity: undefined.UndefinedNoneOr[presences.Activity] = undefined.UNDEFINED,
        status: undefined.UndefinedOr[presences.Status] = undefined.UNDEFINED,
    ) -> None:
        self._check_if_alive()
        presence_payload = self._serialize_and_store_presence_payload(
            idle_since=idle_since,
            afk=afk,
            activity=activity,
            status=status,
        )
        payload: data_binding.JSONObject = {_OP: _PRESENCE_UPDATE, _D: presence_payload}
        await self._send_json(payload)

    async def update_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: typing.Optional[snowflakes.SnowflakeishOr[channels.GuildVoiceChannel]],
        *,  # TODO: make default to undefined
        self_mute: bool = False,
        self_deaf: bool = False,
    ) -> None:
        self._check_if_alive()
        await self._send_json(
            {
                _OP: _VOICE_STATE_UPDATE,
                _D: {
                    "guild_id": str(int(guild)),
                    "channel_id": str(int(channel)) if channel is not None else None,
                    "self_mute": self_mute,
                    "self_deaf": self_deaf,
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
            unavailable_guild_count = len(data["guilds"])
            version = data["v"]
            self._logger.info(
                "shard is ready: %s guilds, %s (%s), session %r on v%s gateway",
                unavailable_guild_count,
                tag,
                user_id,
                self._session_id,
                version,
            )
            self._handshake_completed.set()

        elif name == "RESUME":
            self._logger.info("shard has resumed [session:%s, seq:%s]", self._session_id, self._seq)
            self._handshake_completed.set()

        try:
            self._event_manager.consume_raw_event(name, self, data)
        except LookupError:
            self._logger.debug("ignoring unknown event %s:\n    %r", name, data)

    async def _identify(self) -> None:
        payload: data_binding.JSONObject = {
            _OP: _IDENTIFY,
            _D: {
                "token": self._token,
                "compress": False,
                "large_threshold": self._large_threshold,
                "properties": {
                    "$os": f"{platform.system()} {platform.architecture()[0]}",
                    "$browser": f"aiohttp {aiohttp.__version__}",
                    "$device": f"hikari {about.__version__}",
                },
                "shard": [self._shard_id, self._shard_count],
            },
        }

        payload[_D]["intents"] = self._intents

        payload[_D]["presence"] = self._serialize_and_store_presence_payload()

        await self._send_json(payload)

    async def _heartbeat(self, heartbeat_interval: float) -> bool:
        # Return True if zombied or should reconnect, false if time to die forever.
        # Prevent immediately zombie-ing.
        self._last_heartbeat_ack_received = time.monotonic()
        self._logger.debug("starting heartbeat with interval %ss", heartbeat_interval)

        while not self._closing.is_set() and not self._closed.is_set():
            if self._last_heartbeat_ack_received <= self._last_heartbeat_sent:
                # Gateway is zombie, close and request reconnect.
                self._logger.warning(
                    "connection has not received a HEARTBEAT_ACK for approx %.1fs and is being disconnected, "
                    "expect a reconnect shortly",
                    time.monotonic() - self._last_heartbeat_ack_received,
                )
                return True

            self._logger.log(
                ux.TRACE, "preparing to send HEARTBEAT [s:%s, interval:%ss]", self._seq, heartbeat_interval
            )

            await self._send_heartbeat()

            try:
                await asyncio.wait_for(self._closing.wait(), timeout=heartbeat_interval)
                # We are closing
                break
            except asyncio.TimeoutError:
                # We should continue
                continue

        self._logger.debug("heartbeat task is finishing now")
        return False

    async def _poll_events(self) -> typing.Optional[bool]:
        payload = await self._ws.receive_json(timeout=5)  # type: ignore[union-attr]

        op = payload[_OP]  # opcode int
        d = payload[_D]  # data/payload. Usually a dict or a bool for INVALID_SESSION

        if op == _DISPATCH:
            t = payload[_T]  # event name str
            s = payload[_S]  # seq int
            self._logger.log(ux.TRACE, "dispatching %s with seq %s", t, s)
            self._dispatch(t, s, d)
        elif op == _HEARTBEAT:
            await self._send_heartbeat_ack()
            self._logger.log(ux.TRACE, "sent HEARTBEAT")
        elif op == _HEARTBEAT_ACK:
            now = time.monotonic()
            self._last_heartbeat_ack_received = now
            self._heartbeat_latency = now - self._last_heartbeat_sent
            self._logger.log(ux.TRACE, "received HEARTBEAT ACK in %.1fms", self._heartbeat_latency * 1_000)
        elif op == _RECONNECT:
            # We should be able to resume...
            self._logger.info("received instruction to reconnect, will resume existing session")
            return True
        elif op == _INVALID_SESSION:
            # We can resume if the payload was `true`.
            if not d:
                self._logger.info("received invalid session, will need to start a new session")
                self._seq = None
                self._session_id = None
            else:
                self._logger.info("received invalid session, will resume existing session")
            return True
        else:
            self._logger.log(ux.TRACE, "unknown opcode %s received, it will be ignored...", op)

        return None

    async def _resume(self) -> None:
        await self._send_json(
            {
                _OP: _RESUME,
                _D: {"token": self._token, "seq": self._seq, "session_id": self._session_id},
            }
        )

    async def _run(self) -> None:
        self._closed.clear()
        self._closing.clear()
        last_started_at = -float("inf")

        backoff = rate_limits.ExponentialBackOff(
            base=_BACKOFF_BASE,
            maximum=_BACKOFF_CAP,
            initial_increment=_BACKOFF_INCREMENT_START,
        )

        try:
            while not self._closing.is_set() and not self._closed.is_set():
                if time.monotonic() - last_started_at < _BACKOFF_WINDOW:
                    backoff_time = next(backoff)
                    self._logger.info("backing off reconnecting for %.2fs", backoff_time)

                    try:
                        await asyncio.wait_for(self._closing.wait(), timeout=backoff_time)
                        # We were told to close.
                        return
                    except asyncio.TimeoutError:
                        # We are going to run once.
                        pass

                try:
                    last_started_at = time.monotonic()
                    should_restart = await self._run_once()

                    if not should_restart:
                        self._logger.info("shard has disconnected and shut down normally")
                        return

                except errors.GatewayConnectionError as ex:
                    self._logger.error(
                        "failed to communicate with server, reason was: %r. Will retry shortly", ex.reason
                    )

                except errors.GatewayServerClosedConnectionError as ex:
                    if not ex.can_reconnect:
                        raise

                    self._logger.info(
                        "server has closed connection, will reconnect if possible [code:%s, reason:%s]",
                        ex.code,
                        ex.reason,
                    )

                    # We don't want to back off from this. If Discord keep closing the connection, it is their issue.
                    # If we back off here, we'll find a mass outage will prevent shards from becoming healthy on
                    # reconnect in large sharded bots for a very long period of time.
                    backoff.reset()

                except errors.GatewayError as ex:
                    self._logger.error("encountered generic gateway error", exc_info=ex)
                    raise

                except Exception as ex:
                    self._logger.error("encountered some unhandled error", exc_info=ex)
                    raise
        finally:
            self._closing.set()
            self._closed.set()

    async def _run_once(self) -> bool:
        self._handshake_completed.clear()
        dispatch_disconnect = False
        exception = None

        exit_stack = contextlib.AsyncExitStack()

        self._ws = await exit_stack.enter_async_context(
            _GatewayTransport.connect(
                http_settings=self._http_settings,
                log_filterer=_log_filterer(self._token),
                logger=self._logger,
                proxy_settings=self._proxy_settings,
                url=self._url,
            )
        )

        try:
            # Dispatch CONNECTED synthetic event.
            self._event_manager.dispatch(self._event_factory.deserialize_connected_event(self))
            dispatch_disconnect = True

            heartbeat_task = await self._wait_for_hello()

            try:
                if self._seq is not None:
                    self._logger.debug("resuming session %s", self._session_id)
                    await self._resume()
                else:
                    self._logger.debug("identifying with new session")
                    await self._identify()

                if self._closing.is_set():
                    self._logger.debug(
                        "closing flag was set during handshake, disconnecting with GOING AWAY "
                        "(_run_once => do not reconnect)"
                    )
                    await self._ws.send_close(  # type: ignore[union-attr]
                        code=errors.ShardCloseCode.GOING_AWAY, message=b"shard disconnecting"
                    )
                    return False

                # Event polling.
                while not self._closing.is_set() and not heartbeat_task.done() and not heartbeat_task.cancelled():
                    try:
                        result = await self._poll_events()

                        if result is not None:
                            return result
                    except asyncio.TimeoutError:
                        # We should check if the shard is still alive and then poll again after.
                        pass

                # If the heartbeat died due to an error, it should be raised here.
                # This will currently allow us to try to resume if that happens
                # We return True if zombied.
                if await heartbeat_task:
                    now = time.monotonic()
                    self._logger.error(
                        "connection is a zombie, last heartbeat sent %.2fs ago",
                        now - self._last_heartbeat_sent,
                    )
                    self._logger.debug("will attempt to reconnect (_run_once => reconnect)")
                    return True

                self._logger.debug(
                    "shard has requested graceful termination, so will not attempt to reconnect "
                    "(_run_once => do not reconnect)"
                )
                await self._ws.send_close(  # type: ignore[union-attr]
                    code=errors.ShardCloseCode.GOING_AWAY,
                    message=b"shard disconnecting",
                )
                return False

            finally:
                heartbeat_task.cancel()

        except Exception as ex:
            exception = ex
            raise

        finally:
            ws = self._ws
            self._ws = None
            await exit_stack.aclose()
            if dispatch_disconnect:
                # If we managed to connect, we must always send the DISCONNECT event
                # afterwards.
                self._event_manager.dispatch(self._event_factory.deserialize_disconnected_event(self))

            # Ignore errors if we are closing
            if self._closing.is_set() or self._closed.is_set():
                return False

            # Check if we made the socket close or handled it. If we didn't, we should always try to
            # reconnect, as aiohttp is probably closing it internally without telling us properly.
            if exception is None and not ws.sent_close:  # type: ignore[union-attr]
                return True

    async def _send_heartbeat(self) -> None:
        await self._send_json({_OP: _HEARTBEAT, _D: self._seq})
        self._last_heartbeat_sent = time.monotonic()

    async def _send_heartbeat_ack(self) -> None:
        await self._send_json({_OP: _HEARTBEAT_ACK, _D: None})

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

    async def _wait_for_hello(self) -> asyncio.Task[bool]:
        # Expect HELLO.
        payload = await self._ws.receive_json()  # type: ignore[union-attr]
        if payload[_OP] != _HELLO:
            self._logger.debug(
                "expected HELLO opcode, received %s which makes no sense, closing with PROTOCOL ERROR ",
                "(_run_once => raise and do not reconnect)",
                payload[_OP],
            )
            await self._ws.send_close(  # type: ignore[union-attr]
                code=errors.ShardCloseCode.PROTOCOL_ERROR,
                message=b"Expected HELLO op",
            )
            raise errors.GatewayError(f"Expected opcode {_HELLO}, but received {payload[_OP]}")

        if self._closing.is_set():
            self._logger.debug(
                "closing flag was set before we could handshake, disconnecting with GOING AWAY "
                "(_run_once => do not reconnect)"
            )
            await self._ws.send_close(  # type: ignore[union-attr]
                code=errors.ShardCloseCode.GOING_AWAY,
                message=b"shard disconnecting",
            )
            raise asyncio.CancelledError("closing flag was set before we could handshake")

        heartbeat_interval = float(payload[_D]["heartbeat_interval"]) / 1_000.0
        heartbeat_task = asyncio.create_task(self._heartbeat(heartbeat_interval))
        return heartbeat_task
