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

__all__: typing.Final[typing.Sequence[str]] = ["Gateway"]

import asyncio
import enum
import logging
import math
import time
import typing
import urllib.parse
import zlib

import aiohttp
import attr

from hikari import errors
from hikari.models import presences
from hikari.net import rate_limits
from hikari.net import strings
from hikari.utilities import data_binding
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import datetime

    from hikari.api import event_consumer
    from hikari.net import config
    from hikari.models import channels
    from hikari.models import guilds
    from hikari.models import intents as intents_
    from hikari.utilities import snowflake


class Gateway:
    """Implementation of a V6 and V7 compatible gateway.

    Parameters
    ----------
    app : hikari.api.event_consumer.IEventConsumerApp
        The base application.
    debug : bool
        If `True`, each sent and received payload is dumped to the logs. If
        `False`, only the fact that data has been sent/received will be logged.
    http_settings : hikari.net.config.HTTPSettings
        The HTTP-related settings to use while negotiating a websocket.
    initial_activity : hikari.models.presences.Activity or None or hikari.utilities.undefined.UndefinedType
        The initial activity to appear to have for this shard.
    initial_idle_since : datetime.datetime or None or hikari.utilities.undefined.UndefinedType
        The datetime to appear to be idle since.
    initial_is_afk : bool or hikari.utilities.undefined.UndefinedType
        Whether to appear to be AFK or not on login.
    initial_status : hikari.models.presences.Status or hikari.utilities.undefined.UndefinedType
        The initial status to set on login for the shard.
    intents : hikari.models.intents.Intent or None
        Collection of intents to use, or `None` to not use intents at all.
    large_threshold : int
        The number of members to have in a guild for it to be considered large.
    proxy_settings : hikari.net.config.ProxySettings
        The proxy settings to use while negotiating a websocket.
    shard_id : int
        The shard ID.
    shard_count : int
        The shard count.
    token : str
        The bot token to use.
    url : str
        The gateway URL to use. This should not contain a query-string or
        fragments.
    use_compression : bool
        If `True`, then transport compression is enabled.
    use_etf : bool
        If `True`, ETF is used to receive payloads instead of JSON. Defaults to
        `False`. Currently, setting this to `True` will raise a
        `NotImplementedError`.
    version : int
        Gateway API version to use.

    !!! note
        If all four of `initial_activity`, `initial_idle_since`,
        `initial_is_afk`, and `initial_status` are not defined and left to their
        default values, then the presence will not be _updated_ on startup
        at all.
    """

    @enum.unique
    @typing.final
    class _GatewayCloseCode(enum.IntEnum):
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
    @typing.final
    class _GatewayOpcode(enum.IntEnum):
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

    @typing.final
    class _Reconnect(RuntimeError):
        __slots__: typing.Sequence[str] = ()

    @typing.final
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
        use_compression: bool = True,
        use_etf: bool = False,
        version: int = 6,
    ) -> None:
        self._activity: typing.Union[undefined.UndefinedType, None, presences.Activity] = initial_activity
        self._app = app
        self._backoff = rate_limits.ExponentialBackOff(base=1.85, maximum=600, initial_increment=2)
        self._debug = debug
        self._handshake_event = asyncio.Event()
        self._http_settings = http_settings
        self._idle_since: typing.Union[undefined.UndefinedType, None, datetime.datetime] = initial_idle_since
        self._intents: typing.Optional[intents_.Intent] = intents
        self._is_afk: typing.Union[undefined.UndefinedType, bool] = initial_is_afk
        self._last_run_started_at = float("nan")
        self._logger = logging.getLogger(f"hikari.net.gateway.{shard_id}")
        self._proxy_settings = proxy_settings
        self._request_close_event = asyncio.Event()
        self._seq: typing.Optional[str] = None
        self._shard_id: int = shard_id
        self._shard_count: int = shard_count
        self._status: typing.Union[undefined.UndefinedType, presences.Status] = initial_status
        self._token = token
        self._use_compression = use_compression
        self._version = version
        self._ws: typing.Optional[aiohttp.ClientWebSocketResponse] = None
        # No typeshed/stub.
        self._zlib: typing.Any = None
        self._zombied = False

        self.connected_at = float("nan")
        self.heartbeat_interval = float("nan")
        self.heartbeat_latency = float("nan")
        self.last_heartbeat_sent = float("nan")
        self.last_message_received = float("nan")
        self.large_threshold = large_threshold
        self.ratelimiter = rate_limits.WindowedBurstRateLimiter(str(shard_id), 60.0, 120)
        self.session_id: typing.Optional[str] = None

        scheme, netloc, path, params, _, _ = urllib.parse.urlparse(url, allow_fragments=True)

        if use_etf:
            raise NotImplementedError("ETF support is not available currently")

        new_query = dict(v=int(version), encoding="etf" if use_etf else "json")
        if use_compression:
            # payload compression
            new_query["compress"] = "zlib-stream"

        new_query = urllib.parse.urlencode(new_query)

        self.url = urllib.parse.urlunparse((scheme, netloc, path, params, new_query, ""))

    @property
    @typing.final
    def app(self) -> event_consumer.IEventConsumerApp:
        return self._app

    @property
    def is_alive(self) -> bool:
        """Return whether the shard is alive."""
        return not math.isnan(self.connected_at)

    async def start(self) -> asyncio.Task[None]:
        """Start the shard, wait for it to become ready.

        Returns
        -------
        asyncio.Task
            The task containing the shard running logic. Awaiting this will
            wait until the shard has shut down before returning.
        """
        run_task = asyncio.create_task(self._run(), name=f"shard {self._shard_id} keep-alive")
        await self._handshake_event.wait()
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
                await self._close_ws(self._GatewayCloseCode.RFC_6455_NORMAL_CLOSURE, "client shut down")

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
        # Returns `True` if we can reconnect, or `False` otherwise.
        # Wraps the runner logic in the standard exception handling mechanisms.
        try:
            await self._run_once(client_session)
            return False
        except aiohttp.ClientConnectorError as ex:
            self._logger.error(
                "failed to connect to Discord because %s.%s: %s", type(ex).__module__, type(ex).__qualname__, str(ex),
            )

        except self._InvalidSession as ex:
            if ex.can_resume:
                self._logger.warning("invalid session, so will attempt to resume session %s", self.session_id)
                await self._close_ws(self._GatewayCloseCode.DO_NOT_INVALIDATE_SESSION, "invalid session (resume)")
            else:
                self._logger.warning("invalid session, so will attempt to reconnect with new session")
                await self._close_ws(self._GatewayCloseCode.RFC_6455_NORMAL_CLOSURE, "invalid session (no resume)")
                self._seq = None
                self.session_id = None

        except self._Reconnect:
            self._logger.warning("instructed by Discord to reconnect and resume session %s", self.session_id)
            self._backoff.reset()
            await self._close_ws(self._GatewayCloseCode.DO_NOT_INVALIDATE_SESSION, "reconnecting")

        except self._SocketClosed:
            # The socket has already closed, so no need to close it again.
            if self._zombied:
                self._backoff.reset()

            if not self._request_close_event.is_set():
                self._logger.warning("unexpected socket closure, will attempt to reconnect")

            return not self._request_close_event.is_set()

        except errors.GatewayServerClosedConnectionError as ex:
            if ex.can_reconnect:
                self._logger.warning(
                    "server closed the connection with %s (%s), will attempt to reconnect", ex.code, ex.reason,
                )
                await self._close_ws(self._GatewayCloseCode.RFC_6455_NORMAL_CLOSURE, "you hung up on me")
            else:
                await self._close_ws(self._GatewayCloseCode.RFC_6455_UNEXPECTED_CONDITION, "you broke the connection")
                self._seq = None
                self.session_id = None
                self._backoff.reset()
                self._request_close_event.set()
                raise

        except Exception as ex:
            self._logger.error("unexpected exception occurred, shard will now die", exc_info=ex)
            await self._close_ws(self._GatewayCloseCode.RFC_6455_UNEXPECTED_CONDITION, "unexpected error occurred")
            raise

        return True

    async def _run_once(self, client_session: aiohttp.ClientSession) -> None:
        # Physical runner logic without error handling.
        self._request_close_event.clear()

        self._zombied = False

        if self._now() - self._last_run_started_at < self._RESTART_RATELIMIT_WINDOW:
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
        self._last_run_started_at = self._now()

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

        self.connected_at = self._now()

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
            self.connected_at = float("nan")

    async def update_presence(
        self,
        *,
        idle_since: typing.Union[undefined.UndefinedType, None, datetime.datetime] = undefined.UNDEFINED,
        afk: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        activity: typing.Union[undefined.UndefinedType, None, presences.Activity] = undefined.UNDEFINED,
        status: typing.Union[undefined.UndefinedType, presences.Status] = undefined.UNDEFINED,
    ) -> None:
        """Update the presence of the shard user.

        Parameters
        ----------
        idle_since : datetime.datetime or None or hikari.utilities.undefined.UndefinedType
            The datetime that the user started being idle. If undefined, this
            will not be changed.
        afk : bool or hikari.utilities.undefined.UndefinedType
            If `True`, the user is marked as AFK. If `False`, the user is marked
            as being active. If undefined, this will not be changed.
        activity : hikari.models.presences.Activity or None or hikari.utilities.undefined.UndefinedType
            The activity to appear to be playing. If undefined, this will not be
            changed.
        status : hikari.models.presences.Status or hikari.utilities.undefined.UndefinedType
            The web status to show. If undefined, this will not be changed.
        """
        if idle_since is undefined.UNDEFINED:
            idle_since = self._idle_since
        if afk is undefined.UNDEFINED:
            afk = self._is_afk
        if status is undefined.UNDEFINED:
            status = self._status
        if activity is undefined.UNDEFINED:
            activity = self._activity

        presence = self._app.entity_factory.serialize_gateway_presence(
            idle_since=idle_since, afk=afk, status=status, activity=activity
        )

        payload: data_binding.JSONObject = {"op": self._GatewayOpcode.PRESENCE_UPDATE, "d": presence}

        await self._send_json(payload)

        # Update internal status.
        self._idle_since = idle_since if idle_since is not undefined.UNDEFINED else self._idle_since
        self._is_afk = afk if afk is not undefined.UNDEFINED else self._is_afk
        self._activity = activity if activity is not undefined.UNDEFINED else self._activity
        self._status = status if status is not undefined.UNDEFINED else self._status

    async def update_voice_state(
        self,
        guild: typing.Union[guilds.PartialGuild, snowflake.Snowflake, int, str],
        channel: typing.Union[channels.GuildVoiceChannel, snowflake.Snowflake, int, str, None],
        *,
        self_mute: bool = False,
        self_deaf: bool = False,
    ) -> None:
        """Update the voice state for this shard in a given guild.

        Parameters
        ----------
        guild : hikari.models.guilds.PartialGuild or hikari.utilities.snowflake.UniqueObject
            The guild or guild ID to update the voice state for.
        channel : hikari.models.channels.GuildVoiceChannel or hikari.utilities.snowflake.UniqueObject or None
            The channel or channel ID to update the voice state for. If `None`
            then the bot will leave the voice channel that it is in for the
            given guild.
        self_mute : bool
            If `True`, the bot will mute itself in that voice channel. If
            `False`, then it will unmute itself.
        self_deaf : bool
            If `True`, the bot will deafen itself in that voice channel. If
            `False`, then it will undeafen itself.
        """
        payload = self._app.entity_factory.serialize_gateway_voice_state_update(guild, channel, self_mute, self_deaf)
        await self._send_json({"op": self._GatewayOpcode.VOICE_STATE_UPDATE, "d": payload})

    async def _close_ws(self, code: int, message: str) -> None:
        self._logger.debug("sending close frame with code %s and message %r", int(code), message)
        # None if the websocket error'ed on initialization.
        if self._ws is not None:
            await self._ws.close(code=code, message=bytes(message, "utf-8"))

    async def _handshake(self) -> None:
        await self._hello()
        await self._identify() if self.session_id is None else await self._resume()

    async def _hello(self) -> None:
        message = await self._receive_json_payload()
        op = message["op"]
        if message["op"] != self._GatewayOpcode.HELLO:
            await self._close_ws(self._GatewayCloseCode.RFC_6455_POLICY_VIOLATION.value, "did not receive HELLO")
            raise errors.GatewayError(f"Expected HELLO opcode {self._GatewayOpcode.HELLO.value} but received {op}")

        self.heartbeat_interval = message["d"]["heartbeat_interval"] / 1_000.0
        self._logger.info("received HELLO, heartbeat interval is %ss", self.heartbeat_interval)

    async def _identify(self) -> None:
        payload: data_binding.JSONObject = {
            "op": self._GatewayOpcode.IDENTIFY,
            "d": {
                "token": self._token,
                "compress": False,
                "large_threshold": self.large_threshold,
                "properties": {
                    "$os": strings.SYSTEM_TYPE,
                    "$browser": strings.AIOHTTP_VERSION,
                    "$device": strings.LIBRARY_VERSION,
                },
                "shard": [self._shard_id, self._shard_count],
            },
        }

        if self._intents is not None:
            payload["d"]["intents"] = self._intents

        if undefined.count(self._activity, self._status, self._idle_since, self._is_afk) != 4:
            # noinspection PyTypeChecker
            payload["d"]["presence"] = self._app.entity_factory.serialize_gateway_presence(
                self._idle_since, self._is_afk, self._status, self._activity,
            )

        await self._send_json(payload)

    async def _resume(self) -> None:
        await self._send_json(
            {
                "op": self._GatewayOpcode.RESUME,
                "d": {"token": self._token, "seq": self._seq, "session_id": self.session_id},
            }
        )

    async def _heartbeat_keepalive(self) -> None:
        try:
            while not self._request_close_event.is_set():
                now = self._now()
                time_since_message = now - self.last_message_received
                time_since_heartbeat_sent = now - self.last_heartbeat_sent

                if self.heartbeat_interval < time_since_message:
                    self._logger.error(
                        "connection is a zombie, haven't received any message for %ss, last heartbeat sent %ss ago",
                        time_since_message,
                        time_since_heartbeat_sent,
                    )
                    self._zombied = True
                    await self._close_ws(self._GatewayCloseCode.DO_NOT_INVALIDATE_SESSION, "zombie connection")
                    return

                self._logger.debug(
                    "preparing to send HEARTBEAT [s:%s, interval:%ss]", self._seq, self.heartbeat_interval
                )
                await self._send_json({"op": self._GatewayOpcode.HEARTBEAT, "d": self._seq})
                self.last_heartbeat_sent = self._now()

                try:
                    await asyncio.wait_for(self._request_close_event.wait(), timeout=self.heartbeat_interval)
                except asyncio.TimeoutError:
                    pass

        except asyncio.CancelledError:
            # This happens if the poll task has stopped. It isn't a problem we need to report.
            pass

    async def _poll_events(self) -> None:
        while not self._request_close_event.is_set():
            message = await self._receive_json_payload()

            op = message["op"]
            data = message["d"]

            if op == self._GatewayOpcode.DISPATCH:
                event = message["t"]
                self._seq = message["s"]

                if event == "READY":
                    self.session_id = data["session_id"]
                    user_pl = data["user"]
                    user_id = user_pl["id"]
                    tag = user_pl["username"] + "#" + user_pl["discriminator"]
                    self._logger.info(
                        "shard is ready [session:%s, user_id:%s, tag:%s]", self.session_id, user_id, tag,
                    )
                    self._handshake_event.set()

                elif event == "RESUME":
                    self._logger.info("shard has resumed [session:%s, seq:%s]", self.session_id, self._seq)
                    self._handshake_event.set()

                self._dispatch(event, data)

            elif op == self._GatewayOpcode.HEARTBEAT:
                self._logger.debug("received HEARTBEAT; sending HEARTBEAT ACK")
                await self._send_json({"op": self._GatewayOpcode.HEARTBEAT_ACK})

            elif op == self._GatewayOpcode.HEARTBEAT_ACK:
                self.heartbeat_latency = self._now() - self.last_heartbeat_sent
                self._logger.debug("received HEARTBEAT ACK [latency:%ss]", self.heartbeat_latency)

            elif op == self._GatewayOpcode.RECONNECT:
                self._logger.debug("RECONNECT")
                raise self._Reconnect

            elif op == self._GatewayOpcode.INVALID_SESSION:
                self._logger.debug("INVALID SESSION [resume:%s]", data)
                raise self._InvalidSession(data)

            else:
                self._logger.debug("ignoring unrecognised opcode %s", op)

    async def _receive_json_payload(self) -> data_binding.JSONObject:
        message = await self._receive_raw()

        if message.type == aiohttp.WSMsgType.BINARY:
            n, string = await self._receive_zlib_message(message.data)
            payload: data_binding.JSONObject = data_binding.load_json(string)  # type: ignore
            self._log_debug_payload(
                string, "received %s zlib encoded packets [t:%s, op:%s]", n, payload.get("t"), payload.get("op"),
            )
            return payload

        if message.type == aiohttp.WSMsgType.TEXT:
            string = message.data
            payload: data_binding.JSONObject = data_binding.load_json(string)  # type: ignore
            self._log_debug_payload(string, "received text payload [t:%s, op:%s]", payload.get("t"), payload.get("op"))
            return payload

        if message.type == aiohttp.WSMsgType.CLOSE:
            close_code = self._ws.close_code
            self._logger.debug("connection closed with code %s", close_code)

            if close_code in self._GatewayCloseCode.__members__.values():
                reason = self._GatewayCloseCode(close_code).name
            else:
                reason = f"unknown close code {close_code}"

            can_reconnect = close_code < 4000 or close_code in (
                self._GatewayCloseCode.DECODE_ERROR,
                self._GatewayCloseCode.INVALID_SEQ,
                self._GatewayCloseCode.UNKNOWN_ERROR,
                self._GatewayCloseCode.SESSION_TIMEOUT,
                self._GatewayCloseCode.RATE_LIMITED,
            )

            # Assume we can always resume first.
            raise errors.GatewayServerClosedConnectionError(reason, close_code, can_reconnect)

        if message.type == aiohttp.WSMsgType.CLOSING or message.type == aiohttp.WSMsgType.CLOSED:
            raise self._SocketClosed

        # Assume exception for now.
        ex = self._ws.exception()
        self._logger.debug("encountered unexpected error", exc_info=ex)
        raise errors.GatewayError("Unexpected websocket exception from gateway") from ex

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
        packet = await self._ws.receive()
        self.last_message_received = self._now()
        return packet

    async def _send_json(self, payload: data_binding.JSONObject) -> None:
        await self.ratelimiter.acquire()
        message = data_binding.dump_json(payload)
        self._log_debug_payload(message, "sending json payload [t:%s]", payload.get("t"))
        await self._ws.send_str(message)

    def _dispatch(self, event_name: str, event: data_binding.JSONObject) -> asyncio.Task[None]:
        return asyncio.create_task(
            self._app.event_consumer.consume_raw_event(self, event_name, event),
            name=f"gateway shard {self._shard_id} dispatch {event_name}",
        )

    @staticmethod
    def _now() -> float:
        return time.perf_counter()

    def _log_debug_payload(self, payload: str, message: str, *args: typing.Any) -> None:
        # Prevent logging these payloads if logging isn't enabled. This aids performance a little.
        if not self._logger.isEnabledFor(logging.DEBUG):
            return

        message = f"{message} [seq:%s, session:%s, size:%s]"
        if self._debug:
            message = f"{message} with raw payload: %s"
            args = (*args, self._seq, self.session_id, len(payload), payload)
        else:
            args = (*args, self._seq, self.session_id, len(payload))

        self._logger.debug(message, *args)
