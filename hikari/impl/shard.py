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

__all__: typing.Final[typing.List[str]] = [
    "GatewayShardImplV6",
    "GatewayShardImpl",
]

import asyncio
import datetime
import enum
import logging
import random
import typing
import urllib.parse
import zlib

import aiohttp
import attr

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
    from hikari import channels
    from hikari import config
    from hikari import guilds
    from hikari import users


@typing.final
class GatewayShardImplV6(shard.GatewayShard):
    """Implementation of a V6 and V7 compatible gateway.

    Parameters
    ----------
    compression : buitlins.str or buitlins.None
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
        A coroutine function consuming a `GatewayShardImplV6`,
        a `builtins.str` event name, and a
        `hikari.utilities.data_binding.JSONObject` event object as parameters.
        This should return `builtins.None`, and will be called asynchronously
        with each event that fires.
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
        "_backoff",
        "_compression",
        "_connected_at",
        "_data_format",
        "_debug",
        "_event_consumer",
        "_handshake_event",
        "_heartbeat_interval",
        "_heartbeat_latency",
        "_http_settings",
        "_idle_since",
        "_intents",
        "_is_afk",
        "_large_threshold",
        "_last_heartbeat_sent",
        "_last_message_received",
        "_last_run_started_at",
        "_logger",
        "_proxy_settings",
        "_ratelimiter",
        "_request_close_event",
        "_seq",
        "_session_id",
        "_session_started_at",
        "_shard_id",
        "_shard_count",
        "_status",
        "_token",
        "_user_id",
        "_version",
        "_ws",
        "_zlib",
        "_zombied",
        "url",
    )

    @enum.unique
    @typing.final
    class _Opcode(enum.IntEnum):
        DISPATCH = 0
        HEARTBEAT = 1
        IDENTIFY = 2
        PRESENCE_UPDATE = 3
        VOICE_STATE_UPDATE = 4
        RESUME = 6
        RECONNECT = 7
        REQUEST_GUILD_MEMBERS = 8
        INVALID_SESSION = 9
        HELLO = 10
        HEARTBEAT_ACK = 11

    @attr.s(slots=True, repr=False, weakref_slot=False)
    @typing.final
    class _Reconnect(RuntimeError):
        pass

    @attr.s(slots=True, repr=False, weakref_slot=False)
    @typing.final
    class _SocketClosed(RuntimeError):
        pass

    @attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
    @typing.final
    class _InvalidSession(RuntimeError):
        can_resume: bool = attr.ib(default=False)

    _RESTART_RATELIMIT_WINDOW: typing.Final[typing.ClassVar[float]] = 30.0
    """If the shard restarts more than once within this period of time, then
    exponentially back-off to prevent spamming the gateway or tanking the CPU.

    This is potentially important if the internet connection turns off, as the
    bot will simply attempt to reconnect repeatedly until the connection
    resumes.
    """

    _NO_SESSION_INVALIDATION_CLOSE_CODE: typing.Final[typing.ClassVar[int]] = 3000
    """Discord seems to invalidate sessions if I send a 1xxx, which is useless
    for invalid session and reconnect messages where I want to be able to
    resume.
    """

    def __init__(
        self,
        *,
        compression: typing.Optional[str] = shard.GatewayCompression.PAYLOAD_ZLIB_STREAM,
        data_format: str = shard.GatewayDataFormat.JSON,
        debug: bool = False,
        event_consumer: typing.Callable[
            [shard.GatewayShard, str, data_binding.JSONObject], typing.Coroutine[None, None, None]
        ],
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
        self._activity: undefined.UndefinedNoneOr[presences.Activity] = initial_activity
        self._backoff = rate_limits.ExponentialBackOff(base=1.85, maximum=600, initial_increment=2)
        self._compression = compression.lower() if compression is not None else None
        self._connected_at: typing.Optional[float] = None
        self._data_format = data_format.lower()
        self._debug = debug
        self._event_consumer = event_consumer
        self._handshake_event = asyncio.Event()
        self._heartbeat_interval = float("nan")
        self._heartbeat_latency = float("nan")
        self._http_settings = http_settings
        self._idle_since: typing.Optional[datetime.datetime] = initial_idle_since
        self._intents: typing.Optional[intents_.Intents] = intents
        self._is_afk: undefined.UndefinedOr[bool] = initial_is_afk
        self._large_threshold = large_threshold
        self._last_heartbeat_sent = float("nan")
        self._last_message_received = float("nan")
        self._last_run_started_at = float("nan")
        self._logger = logging.getLogger(f"hikari.gateway.{shard_id}")
        self._proxy_settings = proxy_settings
        self._ratelimiter = rate_limits.WindowedBurstRateLimiter(str(shard_id), 60.0, 120)
        self._request_close_event = asyncio.Event()
        self._seq: typing.Optional[int] = None
        self._session_id: typing.Optional[str] = None
        self._session_started_at: typing.Optional[float] = None
        self._shard_id: int = shard_id
        self._shard_count: int = shard_count
        self._status: undefined.UndefinedOr[presences.Status] = initial_status
        self._token = token
        self._user_id: typing.Optional[snowflakes.Snowflake] = None
        self._version = version
        self._ws: typing.Optional[aiohttp.ClientWebSocketResponse] = None
        self._zlib: typing.Any = None  # No typeshed/stub.
        self._zombied = False

        scheme, netloc, path, params, _, _ = urllib.parse.urlparse(url, allow_fragments=True)

        if self._data_format != shard.GatewayDataFormat.JSON:
            raise NotImplementedError(f"Unsupported gateway data format: {self._data_format}")

        new_query = dict(v=int(version), encoding=self._data_format)

        if self._compression is not None:
            if self._compression == shard.GatewayCompression.PAYLOAD_ZLIB_STREAM:
                new_query["compress"] = "zlib-stream"
            else:
                raise NotImplementedError(f"Unsupported compression format {self._compression}")

        new_query = urllib.parse.urlencode(new_query)
        self.url = urllib.parse.urlunparse((scheme, netloc, path, params, new_query, ""))

    @property
    def compression(self) -> typing.Optional[str]:
        return self._compression

    @property
    def connection_uptime(self) -> float:
        return date.monotonic() - self._connected_at if self._connected_at is not None else 0

    @property
    def data_format(self) -> str:
        return self._data_format

    @property
    def heartbeat_interval(self) -> float:
        return self._heartbeat_interval

    @property
    def heartbeat_latency(self) -> float:
        return self._heartbeat_latency

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

    @property
    def id(self) -> int:
        return self._shard_id

    @property
    def intents(self) -> typing.Optional[intents_.Intents]:
        return self._intents

    @property
    def is_alive(self) -> bool:
        return self._connected_at is not None

    @property
    def proxy_settings(self) -> config.ProxySettings:
        return self._proxy_settings

    @property
    def sequence(self) -> typing.Optional[int]:
        return self._seq

    @property
    def session_id(self) -> typing.Optional[str]:
        return self._session_id

    @property
    def session_uptime(self) -> float:
        return date.monotonic() - self._session_started_at if self._session_started_at is not None else 0

    @property
    def shard_count(self) -> int:
        return self._shard_count

    @property
    def version(self) -> int:
        return self._version

    async def get_user_id(self) -> snowflakes.Snowflake:
        await self._handshake_event.wait()
        if self._user_id is None:
            raise RuntimeError("user_id was not known, this is probably a bug")
        return self._user_id

    async def start(self) -> asyncio.Task[None]:
        run_task = asyncio.create_task(self._run(), name=f"shard {self._shard_id} keep-alive")
        handshake_future = asyncio.ensure_future(self._handshake_event.wait())
        await asyncio.wait([run_task, handshake_future], return_when=asyncio.FIRST_COMPLETED)  # type: ignore

        # Ensure we propagate a startup error without joining the run task first.
        # We should not need to kill the handshake event, that should be done for us.
        if run_task.done() and (exception := run_task.exception()) is not None:
            raise exception

        return run_task

    async def close(self) -> None:
        """Close the websocket."""
        if not self._request_close_event.is_set():
            if self.is_alive:
                self._logger.info("received request to shut down shard")
            else:
                self._logger.debug("shard marked as closed when it was not running")
            self._request_close_event.set()

            if self._ws is not None:
                self._logger.warning("gateway client closed, will not attempt to restart")
                await self._close_ws(errors.ShardCloseCode.NORMAL_CLOSURE, "client shut down")

    async def update_presence(
        self,
        *,
        idle_since: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        afk: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        activity: undefined.UndefinedNoneOr[presences.Activity] = undefined.UNDEFINED,
        status: undefined.UndefinedOr[presences.Status] = undefined.UNDEFINED,
    ) -> None:
        presence_payload = self._serialize_and_store_presence_payload(
            idle_since=idle_since, afk=afk, activity=activity, status=status,
        )
        payload: data_binding.JSONObject = {"op": self._Opcode.PRESENCE_UPDATE, "d": presence_payload}

        if self.is_alive:
            await self._send_json(payload)
        else:
            self._logger.debug("not sending presence update, I am not alive")

    async def update_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: typing.Optional[snowflakes.SnowflakeishOr[channels.GuildVoiceChannel]],
        *,
        self_mute: bool = False,
        self_deaf: bool = False,
    ) -> None:
        await self._send_json(
            {
                "op": self._Opcode.VOICE_STATE_UPDATE,
                "d": {
                    "guild_id": str(int(guild)),
                    "channel_id": str(int(channel)) if channel is not None else None,
                    "mute": self_mute,
                    "deaf": self_deaf,
                },
            }
        )

    async def request_guild_members(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        include_presences: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        query: str = "",
        limit: int = 0,
        user_ids: undefined.UndefinedOr[typing.Sequence[snowflakes.SnowflakeishOr[users.User]]] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        if self._intents is not None:
            if not query and not limit and not self._intents & intents_.Intents.GUILD_MEMBERS:
                raise errors.MissingIntentError(intents_.Intents.GUILD_MEMBERS)

            if include_presences is not undefined.UNDEFINED and not self._intents & intents_.Intents.GUILD_PRESENCES:
                raise errors.MissingIntentError(intents_.Intents.GUILD_PRESENCES)

        if user_ids is not undefined.UNDEFINED and (query or limit):
            raise ValueError("Cannot specify limit/query with users")

        if not 0 <= limit <= 100:
            raise ValueError("'limit' must be between 0 and 100, both inclusive")

        if user_ids is not undefined.UNDEFINED and len(user_ids) > 100:
            raise ValueError("'users' is limited to 100 users")

        payload = data_binding.JSONObjectBuilder()
        payload.put_snowflake("guild_id", guild)
        payload.put("include_presences", include_presences)
        payload.put("query", query)
        payload.put("limit", limit)
        payload.put_snowflake_array("user_ids", user_ids)
        payload.put("nonce", nonce)

        await self._send_json({"op": self._Opcode.REQUEST_GUILD_MEMBERS, "d": payload})

    async def _run(self) -> None:
        """Start the shard and wait for it to shut down."""
        async with aiohttp.ClientSession(
            connector_owner=True,
            connector=aiohttp.TCPConnector(
                verify_ssl=self._http_settings.verify_ssl,
                # We are never going to want more than one connection. This will be spammy on
                # big sharded bots and waste a lot of time, so theres no reason to bother.
                limit=1,
                limit_per_host=1,
            ),
            version=aiohttp.HttpVersion11,
            timeout=aiohttp.ClientTimeout(
                total=self._http_settings.timeouts.total,
                connect=self._http_settings.timeouts.acquire_and_connect,
                sock_read=self._http_settings.timeouts.request_socket_read,
                sock_connect=self._http_settings.timeouts.request_socket_connect,
            ),
            trust_env=self._proxy_settings.trust_env,
        ) as client_session:
            try:
                # This may be set if we are stuck in a reconnect loop.
                while not self._request_close_event.is_set() and await self._run_once_shielded(client_session):
                    pass

                # Allow zookeepers to stop gathering tasks for each shard.
                raise errors.GatewayClientClosedError
            finally:
                # This is set to ensure that the `start' waiter does not deadlock if
                # we cannot connect successfully. It is a hack, but it works.
                self._handshake_event.set()

    async def _run_once_shielded(self, client_session: aiohttp.ClientSession) -> bool:
        # Returns `builtins.True` if we can reconnect, or `builtins.False` otherwise.
        # Wraps the runner logic in the standard exception handling mechanisms.
        try:
            await self._run_once(client_session)
            return False

        except aiohttp.ClientConnectorError as ex:
            # TODO: will I need to reset the session_id and seq ever here? I don't think I do, but I should check
            self._logger.error(
                "failed to connect to Discord because %s.%s: %s", type(ex).__module__, type(ex).__qualname__, str(ex),
            )

        except self._InvalidSession as ex:
            if ex.can_resume:
                self._logger.warning("invalid session, so will attempt to resume session %s now", self._session_id)
                await self._close_ws(self._NO_SESSION_INVALIDATION_CLOSE_CODE, "invalid session (resume)")
                self._backoff.reset()
            else:
                self._logger.warning("invalid session, so will attempt to reconnect with new session in a few seconds")
                await self._close_ws(errors.ShardCloseCode.NORMAL_CLOSURE, "invalid session (no resume)")
                self._seq = None
                self._session_id = None
                self._session_started_at = None

        except self._Reconnect:
            self._logger.warning("instructed by Discord to reconnect and resume session %s", self._session_id)
            self._backoff.reset()
            await self._close_ws(self._NO_SESSION_INVALIDATION_CLOSE_CODE, "reconnecting")

        except self._SocketClosed:
            # The socket has already closed, so no need to close it again.
            if self._zombied:
                self._backoff.reset()

            if not self._request_close_event.is_set():
                self._logger.warning("unexpected socket closure, will attempt to resume")
            else:
                self._session_started_at = None

            return not self._request_close_event.is_set()

        except errors.GatewayServerClosedConnectionError as ex:
            if ex.can_reconnect:
                self._logger.warning(
                    "server closed the connection with %s (%s), will attempt to reconnect", ex.code, ex.reason,
                )
            else:
                self._seq = None
                self._session_id = None
                self._session_started_at = None
                self._backoff.reset()
                self._request_close_event.set()
                raise

        except Exception as ex:
            self._logger.error("unexpected exception occurred, shard will now die", exc_info=ex)
            self._seq = None
            self._session_id = None
            self._session_started_at = None
            await self._close_ws(errors.ShardCloseCode.UNEXPECTED_CONDITION, "unexpected error occurred")
            raise

        return True

    async def _run_once(self, client_session: aiohttp.ClientSession) -> None:
        # Physical runner logic without error handling.
        self._request_close_event.clear()

        self._zombied = False

        if date.monotonic() - self._last_run_started_at < self._RESTART_RATELIMIT_WINDOW:
            # Interrupt sleep immediately if a request to close is fired.
            wait_task = asyncio.create_task(
                self._request_close_event.wait(), name=f"gateway shard {self._shard_id} backing off"
            )
            try:
                backoff = next(self._backoff)
                self._logger.debug("backing off for %ss", backoff)
                await asyncio.wait_for(wait_task, timeout=backoff)

                # If this line gets reached, the wait didn't time out, meaning
                # the user told the client to shut down gracefully before the
                # backoff completed.
                return
            except asyncio.TimeoutError:
                pass

        # Do this after. It prevents backing off on the first try.
        self._last_run_started_at = date.monotonic()

        self._logger.debug("creating websocket connection to %s", self.url)
        self._ws = await client_session.ws_connect(
            url=self.url,
            autoping=True,
            autoclose=True,
            proxy=self._proxy_settings.url,
            proxy_headers=self._proxy_settings.all_headers,
            verify_ssl=self._http_settings.verify_ssl,
            # Discord can send massive messages that lead us to being disconnected
            # without this. It is a bit shit that there is no guarantee of the size
            # of these messages, but there is not much we can do about this one.
            max_msg_size=0,
        )

        self._connected_at = date.monotonic()

        # Technically we are connected after the hello, but this ensures we can send and receive
        # before firing that event.
        self._dispatch("CONNECTED", {})

        try:

            self._zlib = zlib.decompressobj()

            self._handshake_event.clear()
            self._request_close_event.clear()

            await self._handshake()

            # We should ideally set this after HELLO, but it should be fine
            # here as well. If we don't heartbeat in time, something probably
            # went majorly wrong anyway.
            heartbeat = asyncio.create_task(
                self._heartbeat_keepalive(), name=f"gateway shard {self._shard_id} heartbeat"
            )

            try:
                await self._poll_events()
            finally:
                heartbeat.cancel()
        finally:
            self._dispatch("DISCONNECTED", {})
            self._connected_at = None

    async def _close_ws(self, code: int, message: str) -> None:
        self._logger.debug("sending close frame with code %s and message %r", int(code), message)
        # None if the websocket error'ed on initialization.
        if self._ws is not None:
            await self._ws.close(code=code, message=bytes(message, "utf-8"))

    async def _handshake(self) -> None:
        hello = await self._expect_opcode(self._Opcode.HELLO)
        self._heartbeat_interval = hello["heartbeat_interval"] / 1_000.0
        self._logger.info("received HELLO, heartbeat interval is %ss", self._heartbeat_interval)

        if self._session_id is not None:
            await self._send_json(
                {
                    "op": self._Opcode.RESUME,
                    "d": {"token": self._token, "seq": self._seq, "session_id": self._session_id},
                }
            )
        else:
            payload: data_binding.JSONObject = {
                "op": self._Opcode.IDENTIFY,
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

            await self._send_json(payload)

    async def _heartbeat_keepalive(self) -> None:
        # Wait a random offset between 0ms and <heartbeat_interval>ms before
        # sending the first heartbeat. This helps not overload the gateway
        # after recovering from an outage.
        #
        # S311 - Dont use random for security/cryptographic purposes
        offset = random.random() * self._heartbeat_interval  # noqa: S311
        await asyncio.sleep(offset)

        try:
            while not self._request_close_event.is_set():
                now = date.monotonic()
                time_since_message = now - self._last_message_received
                time_since_heartbeat_sent = now - self._last_heartbeat_sent

                if self._heartbeat_interval < time_since_message:
                    self._logger.error(
                        "connection is a zombie, haven't received any message for %ss, last heartbeat sent %ss ago",
                        time_since_message,
                        time_since_heartbeat_sent,
                    )
                    await self._close_zombie()
                    return

                self._logger.debug(
                    "preparing to send HEARTBEAT [s:%s, interval:%ss]", self._seq, self._heartbeat_interval
                )
                await self._send_json({"op": self._Opcode.HEARTBEAT, "d": self._seq})
                self._last_heartbeat_sent = date.monotonic()

                try:
                    await asyncio.wait_for(self._request_close_event.wait(), timeout=self._heartbeat_interval)
                except asyncio.TimeoutError:
                    pass

        except asyncio.CancelledError:
            # This happens if the poll task has stopped. It is not a problem we need to report.
            pass

    async def _close_zombie(self) -> None:
        # https://gitlab.com/nekokatt/hikari/-/issues/462
        #
        # aiohttp has a little "race condition" where it will try to wait for the close frame to be
        # sent before it physically proceeds to close the aiohttp.ClientResponse. This is a bit
        # annoying for us, since when we are zombied, this frame will probably never be able to be
        # sent (if the network went down). However, to feed a socket closure message into the
        # message receive loop, we need to make this call.
        #
        # Thus, the best solution here is to make a task to perform this call in the background,
        # and await for a short amount of time to let it feed the close message before it proceeds.
        # After this, we manually close the internal aiohttp ClientResponse to force that close frame
        # to fail to send immediately, before proceeding to await the original close task from then
        # on.
        #
        # Probably should file a bug report at some point... if I remember.
        self._zombied = True
        close_task = asyncio.create_task(
            self._close_ws(code=errors.ShardCloseCode.PROTOCOL_ERROR, message="heartbeat timeout")
        )
        await asyncio.sleep(0.1)
        # noinspection PyProtectedMember
        self._ws._response.close()  # type: ignore[union-attr]
        try:
            await close_task
        finally:
            # Discard any exception, I don't care, as this is broken anyway.
            return

    async def _poll_events(self) -> None:
        while not self._request_close_event.is_set():
            message = await self._receive_json()

            op = message["op"]
            data = message["d"]

            if op == self._Opcode.DISPATCH:
                event = message["t"]
                self._seq = message["s"]

                if event == "READY":
                    self._session_id = data["session_id"]
                    user_pl = data["user"]
                    user_id = user_pl["id"]
                    self._user_id = snowflakes.Snowflake(user_id)
                    tag = user_pl["username"] + "#" + user_pl["discriminator"]
                    self._logger.info(
                        "shard is ready [session:%s, user_id:%s, tag:%s]", self._session_id, user_id, tag,
                    )
                    self._handshake_event.set()
                    self._session_started_at = date.monotonic()

                elif event == "RESUME":
                    self._logger.info("shard has resumed [session:%s, seq:%s]", self._session_id, self._seq)
                    self._handshake_event.set()

                self._dispatch(event, data)

            elif op == self._Opcode.HEARTBEAT:
                self._logger.debug("received HEARTBEAT; sending HEARTBEAT ACK")
                await self._send_json({"op": self._Opcode.HEARTBEAT_ACK})

            elif op == self._Opcode.HEARTBEAT_ACK:
                self._heartbeat_latency = date.monotonic() - self._last_heartbeat_sent
                self._logger.debug("received HEARTBEAT ACK [latency:%ss]", self._heartbeat_latency)

            elif op == self._Opcode.RECONNECT:
                self._logger.debug("RECONNECT")
                raise self._Reconnect

            elif op == self._Opcode.INVALID_SESSION:
                self._logger.debug("INVALID SESSION [resume:%s]", data)
                raise self._InvalidSession(data)

            else:
                self._logger.debug("ignoring unrecognised opcode %s", op)

    async def _expect_opcode(self, opcode: _Opcode) -> data_binding.JSONObject:
        message = await self._receive_json()
        op = message["op"]

        if op == opcode:
            return typing.cast("data_binding.JSONObject", message["d"])

        error_message = f"Unexpected opcode {op} received, expected {opcode}"
        await self._close_ws(errors.ShardCloseCode.PROTOCOL_ERROR, error_message)
        raise errors.GatewayError(error_message)

    async def _receive_json(self) -> data_binding.JSONObject:
        message = await self._receive_raw()

        payload: data_binding.JSONObject

        if message.type == aiohttp.WSMsgType.BINARY:
            n, string = await self._receive_zlib_message(message.data)
            payload = data_binding.load_json(string)  # type: ignore[assignment]
            self._log_debug_payload(
                string, "received %s zlib encoded packets [t:%s, op:%s]", n, payload.get("t"), payload.get("op"),
            )
            return payload

        if message.type == aiohttp.WSMsgType.TEXT:
            string = message.data
            payload = data_binding.load_json(string)  # type: ignore[assignment]
            self._log_debug_payload(string, "received text payload [t:%s, op:%s]", payload.get("t"), payload.get("op"))
            return payload

        # This should NEVER occur unless we broke this badly.
        raise TypeError("Unexpected message type " + message.type)

    async def _receive_zlib_message(self, first_packet: bytes) -> typing.Tuple[int, str]:
        # Alloc new array each time; this prevents consuming a large amount of
        # unused memory because of Discord sending massive payloads on connect
        # initially before the payloads shrink in size. Python may not shrink
        # this dynamically if not...
        buff = bytearray(first_packet)

        packets = 1

        while not buff.endswith(b"\x00\x00\xff\xff"):
            message = await self._receive_raw()
            if message.type != aiohttp.WSMsgType.BINARY:
                raise errors.GatewayError(f"Expected a binary message but got {message.type}")
            buff.append(message.data)
            packets += 1

        return packets, self._zlib.decompress(buff).decode("utf-8")

    async def _receive_raw(self) -> aiohttp.WSMessage:
        message: aiohttp.WSMessage = await self._ws.receive()  # type: ignore[union-attr]
        self._last_message_received = date.monotonic()

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

        if message.type == aiohttp.WSMsgType.CLOSING or message.type == aiohttp.WSMsgType.CLOSED:
            raise self._SocketClosed

        if message.type == aiohttp.WSMsgType.ERROR:
            # Assume exception for now.
            ex = self._ws.exception()  # type: ignore[union-attr]
            self._logger.warning(
                "encountered unexpected error: %s",
                ex,
                exc_info=ex if self._logger.isEnabledFor(logging.DEBUG) else None,
            )
            raise errors.GatewayError("Unexpected websocket exception from gateway") from ex

        return message

    async def _send_json(self, payload: data_binding.JSONObject) -> None:
        await self._ratelimiter.acquire()
        message = data_binding.dump_json(payload)
        self._log_debug_payload(message, "sending json payload [op:%s]", payload.get("op"))
        await self._ws.send_str(message)  # type: ignore[union-attr]

    def _dispatch(self, event_name: str, event: data_binding.JSONObject) -> asyncio.Task[None]:
        return asyncio.create_task(
            self._event_consumer(self, event_name, event), name=f"gateway shard {self._shard_id} dispatch {event_name}",
        )

    def _log_debug_payload(self, payload: str, message: str, *args: typing.Any) -> None:
        # Prevent logging these payloads if logging is not enabled. This aids performance a little.
        if not self._logger.isEnabledFor(logging.DEBUG):
            return

        message = f"{message} [seq:%s, session:%s, size:%s]"
        if self._debug:
            message = f"{message} with raw payload: %s"
            args = (*args, self._seq, self._session_id, len(payload), payload)
        else:
            args = (*args, self._seq, self._session_id, len(payload))

        self._logger.debug(message, *args)

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
            payload.put("status", status, conversion=lambda s: typing.cast(str, s.value))
        return payload

    @staticmethod
    def _serialize_datetime(dt: typing.Optional[datetime.datetime]) -> typing.Optional[int]:
        if dt is None:
            return None

        return int(dt.timestamp() * 1_000)

    @staticmethod
    def _serialize_activity(activity: typing.Optional[presences.Activity]) -> data_binding.JSONish:
        if activity is None:
            return None

        return {"name": activity.name, "type": int(activity.type), "url": activity.url}


GatewayShardImpl = GatewayShardImplV6
"""Most up-to-date documented and stable release."""
