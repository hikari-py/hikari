# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
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
"""Single-shard implementation for the V6 and V7 event gateway for Discord."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["GatewayShardImpl"]

import asyncio
import datetime
import enum
import logging
import math
import typing
import urllib.parse
import zlib

import aiohttp
import attr

from hikari import errors
from hikari.api import shard
from hikari.impl import rate_limits
from hikari.models import presences
from hikari.utilities import constants
from hikari.utilities import data_binding
from hikari.utilities import date
from hikari.utilities import snowflake
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari import config
    from hikari.api import event_consumer
    from hikari.models import channels
    from hikari.models import guilds
    from hikari.models import intents as intents_


@typing.final
class GatewayShardImpl(shard.IGatewayShard):
    """Implementation of a V6 and V7 compatible gateway.

    Parameters
    ----------
    app : hikari.api.gateway.consumer.IEventConsumerApp
        The base application.
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
    http_settings : hikari.config.HTTPSettings
        The HTTP-related settings to use while negotiating a websocket.
    initial_activity : hikari.models.presences.Activity or builtins.None or hikari.utilities.undefined.UndefinedType
        The initial activity to appear to have for this shard.
    initial_idle_since : datetime.datetime or builtins.None or hikari.utilities.undefined.UndefinedType
        The datetime to appear to be idle since.
    initial_is_afk : builtins.bool or hikari.utilities.undefined.UndefinedType
        Whether to appear to be AFK or not on login.
    initial_status : hikari.models.presences.Status or hikari.utilities.undefined.UndefinedType
        The initial status to set on login for the shard.
    intents : hikari.models.intents.Intent or builtins.None
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

    @enum.unique
    class _CloseCode(enum.IntEnum):
        RFC_6455_NORMAL_CLOSURE = 1000
        RFC_6455_GOING_AWAY = 1001
        RFC_6455_PROTOCOL_ERROR = 1002
        RFC_6455_TYPE_ERROR = 1003
        RFC_6455_ENCODING_ERROR = 1007
        RFC_6455_POLICY_VIOLATION = 1008
        RFC_6455_TOO_BIG = 1009
        RFC_6455_UNEXPECTED_CONDITION = 1011

        # Discord seems to invalidate sessions if I send a 1xxx, which is useless
        # for invalid session and reconnect messages where I want to be able to
        # resume.
        DO_NOT_INVALIDATE_SESSION = 3000

        UNKNOWN_ERROR = 4000
        UNKNOWN_OPCODE = 4001
        DECODE_ERROR = 4002
        NOT_AUTHENTICATED = 4003
        AUTHENTICATION_FAILED = 4004
        ALREADY_AUTHENTICATED = 4005
        INVALID_SEQ = 4007
        RATE_LIMITED = 4008
        SESSION_TIMEOUT = 4009
        INVALID_SHARD = 4010
        SHARDING_REQUIRED = 4011
        INVALID_VERSION = 4012
        INVALID_INTENT = 4013
        DISALLOWED_INTENT = 4014

    @enum.unique
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

    class _Reconnect(RuntimeError):
        __slots__: typing.Sequence[str] = ()

    class _SocketClosed(RuntimeError):
        __slots__: typing.Sequence[str] = ()

    @attr.s(auto_attribs=True, slots=True)
    class _InvalidSession(RuntimeError):
        can_resume: bool = False

    _RESTART_RATELIMIT_WINDOW: typing.Final[typing.ClassVar[float]] = 30.0
    """If the shard restarts more than once within this period of time, then
    exponentially back-off to prevent spamming the gateway or tanking the CPU.

    This is potentially important if the internet connection turns off, as the
    bot will simply attempt to reconnect repeatedly until the connection
    resumes.
    """

    def __init__(
        self,
        *,
        app: event_consumer.IEventConsumerApp,
        compression: typing.Optional[str] = shard.GatewayCompression.PAYLOAD_ZLIB_STREAM,
        data_format: str = shard.GatewayDataFormat.JSON,
        debug: bool = False,
        http_settings: config.HTTPSettings,
        initial_activity: typing.Union[undefined.UndefinedType, None, presences.Activity] = undefined.UNDEFINED,
        initial_idle_since: typing.Union[undefined.UndefinedType, None, datetime.datetime] = undefined.UNDEFINED,
        initial_is_afk: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        initial_status: typing.Union[undefined.UndefinedType, presences.Status] = undefined.UNDEFINED,
        intents: typing.Optional[intents_.Intent] = None,
        large_threshold: int = 250,
        proxy_settings: config.ProxySettings,
        shard_id: int = 0,
        shard_count: int = 1,
        token: str,
        url: str,
        version: int = 6,
    ) -> None:
        self._activity: typing.Union[undefined.UndefinedType, None, presences.Activity] = initial_activity
        self._app = app
        self._backoff = rate_limits.ExponentialBackOff(base=1.85, maximum=600, initial_increment=2)
        self._compression = compression.lower() if compression is not None else None
        self._connected_at: typing.Optional[float] = None
        self._data_format = data_format.lower()
        self._debug = debug
        self._handshake_event = asyncio.Event()
        self._heartbeat_interval = float("nan")
        self._heartbeat_latency = float("nan")
        self._http_settings = http_settings
        self._idle_since: typing.Union[undefined.UndefinedType, None, datetime.datetime] = initial_idle_since
        self._intents: typing.Optional[intents_.Intent] = intents
        self._is_afk: typing.Union[undefined.UndefinedType, bool] = initial_is_afk
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
        self._status: typing.Union[undefined.UndefinedType, presences.Status] = initial_status
        self._token = token
        self._user_id: typing.Optional[snowflake.Snowflake] = None
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
    def app(self) -> event_consumer.IEventConsumerApp:
        return self._app

    @property
    def compression(self) -> typing.Optional[str]:
        return self._compression

    @property
    def connection_uptime(self) -> datetime.timedelta:
        delta = date.monotonic() - self._connected_at if self._connected_at is not None else 0
        return datetime.timedelta(seconds=delta)

    @property
    def data_format(self) -> str:
        return self._data_format

    @property
    def heartbeat_interval(self) -> typing.Optional[datetime.timedelta]:
        interval = self._heartbeat_interval
        return datetime.timedelta(seconds=interval) if not math.isnan(interval) else None

    @property
    def heartbeat_latency(self) -> typing.Optional[datetime.timedelta]:
        latency = self._heartbeat_latency
        return datetime.timedelta(seconds=latency) if not math.isnan(latency) else None

    @property
    def http_settings(self) -> config.HTTPSettings:
        return self._http_settings

    @property
    def id(self) -> int:
        return self._shard_id

    @property
    def intents(self) -> typing.Optional[intents_.Intent]:
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
    def session_uptime(self) -> datetime.timedelta:
        delta = date.monotonic() - self._session_started_at if self._session_started_at is not None else 0
        return datetime.timedelta(seconds=delta)

    @property
    def shard_count(self) -> int:
        return self._shard_count

    @property
    def version(self) -> int:
        return self._version

    async def get_user_id(self) -> snowflake.Snowflake:
        await self._handshake_event.wait()
        if self._user_id is None:
            raise RuntimeError("user_id was not known, this is probably a bug")
        return self._user_id

    async def start(self) -> asyncio.Task[None]:
        run_task = asyncio.create_task(self._run(), name=f"shard {self._shard_id} keep-alive")
        handshake_future = asyncio.ensure_future(self._handshake_event.wait())
        await asyncio.wait([run_task, handshake_future], return_when=asyncio.FIRST_COMPLETED)  # type: ignore

        # Ensure we propogate a startup error without joining the run task first.
        # We shouldn't need to kill the handshake event, that should be done for us.
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
                await self._close_ws(self._CloseCode.RFC_6455_NORMAL_CLOSURE, "client shut down")

    async def update_presence(
        self,
        *,
        idle_since: typing.Union[undefined.UndefinedType, None, datetime.datetime] = undefined.UNDEFINED,
        afk: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        activity: typing.Union[undefined.UndefinedType, None, presences.Activity] = undefined.UNDEFINED,
        status: typing.Union[undefined.UndefinedType, presences.Status] = undefined.UNDEFINED,
    ) -> None:
        if idle_since is undefined.UNDEFINED:
            idle_since = self._idle_since if self._idle_since is not undefined.UNDEFINED else None
        if afk is undefined.UNDEFINED:
            afk = self._is_afk if self._is_afk is not undefined.UNDEFINED else False
        if status is undefined.UNDEFINED:
            status = self._status if self._status is not undefined.UNDEFINED else presences.Status.ONLINE
        if activity is undefined.UNDEFINED:
            activity = self._activity if self._activity is not undefined.UNDEFINED else None

        presence = self._app.entity_factory.serialize_gateway_presence(
            idle_since=idle_since, afk=afk, status=status, activity=activity
        )

        payload: data_binding.JSONObject = {"op": self._Opcode.PRESENCE_UPDATE, "d": presence}

        await self._send_json(payload)

        # Update internal status.
        self._idle_since = idle_since
        self._is_afk = afk
        self._activity = activity
        self._status = status

    async def update_voice_state(
        self,
        guild: typing.Union[guilds.PartialGuild, snowflake.UniqueObject],
        channel: typing.Union[channels.GuildVoiceChannel, snowflake.UniqueObject, None],
        *,
        self_mute: bool = False,
        self_deaf: bool = False,
    ) -> None:
        payload = self._app.entity_factory.serialize_gateway_voice_state_update(guild, channel, self_mute, self_deaf)
        await self._send_json({"op": self._Opcode.VOICE_STATE_UPDATE, "d": payload})

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
                self._logger.warning("invalid session, so will attempt to resume session %s", self._session_id)
                await self._close_ws(self._CloseCode.DO_NOT_INVALIDATE_SESSION, "invalid session (resume)")
            else:
                self._logger.warning("invalid session, so will attempt to reconnect with new session")
                await self._close_ws(self._CloseCode.RFC_6455_NORMAL_CLOSURE, "invalid session (no resume)")
                self._seq = None
                self._session_id = None
                self._session_started_at = None

        except self._Reconnect:
            self._logger.warning("instructed by Discord to reconnect and resume session %s", self._session_id)
            self._backoff.reset()
            await self._close_ws(self._CloseCode.DO_NOT_INVALIDATE_SESSION, "reconnecting")

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
            await self._close_ws(self._CloseCode.RFC_6455_UNEXPECTED_CONDITION, "unexpected error occurred")
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
            # of these messages, but there isn't much we can do about this one.
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

            if undefined.count(self._activity, self._status, self._idle_since, self._is_afk) != 4:
                # noinspection PyTypeChecker
                payload["d"]["presence"] = self._app.entity_factory.serialize_gateway_presence(
                    idle_since=self._idle_since if self._idle_since is not undefined.UNDEFINED else None,
                    afk=self._is_afk if self._is_afk is not undefined.UNDEFINED else False,
                    status=self._status if self._status is not undefined.UNDEFINED else presences.Status.ONLINE,
                    activity=self._activity if self._activity is not undefined.UNDEFINED else None,
                )

            await self._send_json(payload)

    async def _heartbeat_keepalive(self) -> None:
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
                    self._zombied = True
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
            # This happens if the poll task has stopped. It isn't a problem we need to report.
            pass

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
                    self._user_id = snowflake.Snowflake(user_id)
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

    async def _expect_opcode(self, opcode: _Opcode) -> typing.Mapping[str, typing.Any]:
        message = await self._receive_json()
        op = message["op"]

        if op == opcode:
            return message["d"]  # type: ignore[no-any-return]

        error_message = f"Unexpected opcode {op} received, expected {opcode}"
        await self._close_ws(self._CloseCode.RFC_6455_PROTOCOL_ERROR, error_message)
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
                self._CloseCode.DECODE_ERROR,
                self._CloseCode.INVALID_SEQ,
                self._CloseCode.UNKNOWN_ERROR,
                self._CloseCode.SESSION_TIMEOUT,
                self._CloseCode.RATE_LIMITED,
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
            self._app.event_consumer.consume_raw_event(self, event_name, event),
            name=f"gateway shard {self._shard_id} dispatch {event_name}",
        )

    def _log_debug_payload(self, payload: str, message: str, *args: typing.Any) -> None:
        # Prevent logging these payloads if logging isn't enabled. This aids performance a little.
        if not self._logger.isEnabledFor(logging.DEBUG):
            return

        message = f"{message} [seq:%s, session:%s, size:%s]"
        if self._debug:
            message = f"{message} with raw payload: %s"
            args = (*args, self._seq, self._session_id, len(payload), payload)
        else:
            args = (*args, self._seq, self._session_id, len(payload))

        self._logger.debug(message, *args)
