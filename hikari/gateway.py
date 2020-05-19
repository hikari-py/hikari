#!/usr/bin/env python3
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
"""Provides a facade around `hikari.gateway.connection.Shard`.

This handles parsing and initializing the object from a configuration, as
well as restarting it if it disconnects.

Additional functions and coroutines are provided to update the presence on the
shard using models defined in `hikari`.
"""

from __future__ import annotations

__all__ = ["Gateway"]

import asyncio
import contextlib
import json
import time
import typing
import urllib.parse
import zlib

import aiohttp

from hikari import errors
from hikari import http_settings
from hikari.internal import http_client
from hikari.internal import more_asyncio
from hikari.internal import more_enums
from hikari.internal import ratelimits
from hikari.internal import user_agents
from hikari.models import bases
from hikari.models import channels
from hikari.models import unset
from hikari.internal import more_typing


if typing.TYPE_CHECKING:
    import datetime

    from hikari.models import gateway
    from hikari.models import guilds
    from hikari.models import intents as intents_


@more_enums.must_be_unique
class _GatewayCloseCode(int, more_enums.Enum):
    """Reasons for closing a gateway connection."""

    NORMAL_CLOSURE = 1000
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

    def __str__(self) -> str:
        name = self.name.replace("_", " ").title()
        return f"{self.value} {name}"


@more_enums.must_be_unique
class _GatewayOpcode(int, more_enums.Enum):
    """Opcodes that the gateway uses internally."""

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

    def __str__(self) -> str:
        name = self.name.replace("_", " ").title()
        return f"{self.value} {name}"


RawDispatchT = typing.Callable[["Gateway", str, more_typing.JSONObject], more_typing.Coroutine[None]]


class _Reconnect(RuntimeError):
    __slots__ = ()


class _Zombie(RuntimeError):
    __slots__ = ()


class _InvalidSession(RuntimeError):
    __slots__ = ("can_resume",)

    def __init__(self, can_resume: bool) -> None:
        self.can_resume = can_resume


class Gateway(http_client.HTTPClient):
    """Blah blah
    """

    def __init__(
        self,
        *,
        config: http_settings.HTTPSettings,
        dispatch: RawDispatchT,
        debug: bool,
        initial_activity: typing.Optional[gateway.Activity] = None,
        initial_idle_since: typing.Optional[datetime.datetime] = None,
        initial_is_afk: typing.Optional[bool] = None,
        initial_status: typing.Optional[guilds.PresenceStatus] = None,
        intents: typing.Optional[intents_.Intent] = None,
        large_threshold: int = 250,
        shard_id: int,
        shard_count: int,
        token: str,
        url: str,
        use_compression: bool = True,
        version: int,
    ) -> None:
        super().__init__(
            allow_redirects=config.allow_redirects,
            connector=config.tcp_connector,
            debug=debug,
            logger_name=f"{type(self).__module__}.{type(self).__qualname__}.{shard_id}",
            proxy_auth=config.proxy_auth,
            proxy_headers=config.proxy_headers,
            proxy_url=config.proxy_url,
            ssl_context=config.ssl_context,
            verify_ssl=config.verify_ssl,
            timeout=config.request_timeout,
            trust_env=config.trust_env,
        )
        self._activity = initial_activity
        self._dead_event = asyncio.Event()
        self._dispatch = dispatch
        self._heartbeat_task = None
        self._idle_since = initial_idle_since
        self._intents = intents
        self._is_afk = initial_is_afk
        self._ready_event = asyncio.Event()
        self._request_close_event = asyncio.Event()
        self._resumed_event = asyncio.Event()
        self._run_task = None
        self._running = False
        self._seq = None
        self._session_id = None
        self._shard_id = shard_id
        self._shard_count = shard_count
        self._status = initial_status
        self._token = token
        self._use_compression = use_compression
        self._version = version
        self._ws = None
        self._zlib = None

        self.connected_at = float("nan")
        self.disconnect_count = 0
        self.heartbeat_interval = float("nan")
        self.heartbeat_latency = float("nan")
        self.last_heartbeat_sent = float("nan")
        self.last_message_received = float("nan")
        self.large_threshold = large_threshold
        self.ratelimiter = ratelimits.WindowedBurstRateLimiter(str(shard_id), 60.0, 120)

        scheme, netloc, path, params, _, _ = urllib.parse.urlparse(url, allow_fragments=True)

        new_query = dict(v=int(version), encoding="json")
        if use_compression:
            # payload compression
            new_query["compress"] = "zlib-stream"

        new_query = urllib.parse.urlencode(new_query)

        self.url = urllib.parse.urlunparse((scheme, netloc, path, params, new_query, ""))

    async def close(self) -> None:
        self._request_close_event.set()
        await self._dead_event.wait()

    async def update_presence(
        self,
        *,
        idle_since: unset.MayBeUnset[typing.Optional[datetime.datetime]] = unset.UNSET,
        is_afk: unset.MayBeUnset[bool] = unset.UNSET,
        activity: unset.MayBeUnset[typing.Optional[gateway.Activity]] = unset.UNSET,
        status: unset.MayBeUnset[guilds.PresenceStatus] = unset.UNSET,
    ) -> None:
        payload = self._build_presence_payload(idle_since, is_afk, activity, status)
        await self._send_json({"op": _GatewayOpcode.PRESENCE_UPDATE, "d": payload})
        self._idle_since = idle_since if not unset.is_unset(idle_since) else self._idle_since
        self._is_afk = is_afk if not unset.is_unset(is_afk) else self._is_afk
        self._activity = activity if not unset.is_unset(activity) else self._activity
        self._status = status if not unset.is_unset(status) else self._status

    async def update_voice_state(
        self,
        guild: typing.Union[guilds.PartialGuild, bases.Snowflake, int, str],
        channel: typing.Union[channels.GuildVoiceChannel, bases.Snowflake, int, str, None],
        *,
        self_mute: bool = False,
        self_deaf: bool = False,
    ) -> None:
        payload = {
            "op": _GatewayOpcode.VOICE_STATE_UPDATE,
            "d": {
                "guild_id": str(int(guild)),
                "channel": str(int(channel)) if channel is not None else None,
                "self_mute": self_mute,
                "self_deaf": self_deaf,
            },
        }
        await self._send_json(payload)

    async def run(self):
        self._run_task = asyncio.Task.current_task()
        self._dead_event.clear()

        back_off = ratelimits.ExponentialBackOff(base=1.85, maximum=600, initial_increment=2)
        last_start = self._now()
        do_not_back_off = True

        try:
            while True:
                try:
                    if not do_not_back_off and self._now() - last_start < 30:
                        next_back_off = next(back_off)
                        self.logger.info(
                            "restarted within 30 seconds, will back off for %.2fs", next_back_off,
                        )
                        await asyncio.sleep(next_back_off)
                    else:
                        back_off.reset()

                    last_start = self._now()
                    do_not_back_off = False

                    await self._run_once()

                    raise RuntimeError("This shouldn't be reached.")

                except aiohttp.ClientConnectorError as ex:
                    self.logger.exception(
                        "failed to connect to Discord to initialize a websocket connection", exc_info=ex,
                    )

                except _Zombie:
                    self.logger.warning("entered a zombie state and will be restarted")

                except _InvalidSession as ex:
                    if ex.can_resume:
                        self.logger.warning("invalid session, so will attempt to resume")
                    else:
                        self.logger.warning("invalid session, so will attempt to reconnect")
                        self._seq = None
                        self._session_id = None

                    do_not_back_off = True
                    await asyncio.sleep(5)

                except _Reconnect:
                    self.logger.warning("instructed by Discord to reconnect")
                    do_not_back_off = True
                    await asyncio.sleep(5)

                except errors.GatewayClientDisconnectedError:
                    self.logger.warning("unexpected connection close, will attempt to reconnect")

                except errors.GatewayClientClosedError:
                    self.logger.warning("gateway client closed by user, will not attempt to restart")
                    return
        finally:
            self._dead_event.set()

    async def _run_once(self) -> None:
        try:
            self.logger.debug("creating websocket connection to %s", self.url)
            self._ws = await self._create_ws(self.url)
            self._zlib = zlib.decompressobj()

            self._ready_event.clear()
            self._resumed_event.clear()
            self._request_close_event.clear()
            self._running = True

            await self._handshake()

            # We should ideally set this after HELLO, but it should be fine
            # here as well. If we don't heartbeat in time, something probably
            # went majorly wrong anyway.
            heartbeat_task = asyncio.create_task(
                self._maintain_heartbeat(), name=f"gateway shard {self._shard_id} heartbeat"
            )

            poll_events_task = asyncio.create_task(self._poll_events(), name=f"gateway shard {self._shard_id} poll")
            completed, pending = await more_asyncio.wait(
                [heartbeat_task, poll_events_task], return_when=asyncio.FIRST_COMPLETED
            )

            for pending_task in pending:
                pending_task.cancel()
                with contextlib.suppress(Exception):
                    # Clear any pending exception to prevent a nasty console message.
                    pending_task.result()

            ex = None
            while len(completed) > 0 and ex is None:
                ex = completed.pop().exception()

            # If the heartbeat call closes normally, then we want to get the exception
            # raised by the identify call if it raises anything. This prevents spammy
            # exceptions being thrown if the client shuts down during the handshake,
            # which becomes more and more likely when we consider bots may have many
            # shards running, each taking min of 5s to start up after the first.
            ex = None

            while len(completed) > 0 and ex is None:
                ex = completed.pop().exception()

            if isinstance(ex, asyncio.TimeoutError):
                # If we get _request_timeout errors receiving stuff, propagate as a zombied connection. This
                # is already done by the ping keepalive and heartbeat keepalive partially, but this
                # is a second edge case.
                raise _Zombie()

            if ex is not None:
                raise ex
        finally:
            asyncio.create_task(
                self._dispatch(self, "DISCONNECTED", {}), name=f"shard {self._shard_id} dispatch DISCONNECTED"
            )
            self._running = False

    async def _handshake(self) -> None:
        # HELLO!
        message = await self._recv_json()
        op = message["op"]
        if message["op"] != _GatewayOpcode.HELLO:
            raise errors.GatewayError(f"Expected HELLO opcode 10 but received {op}")

        self.heartbeat_interval = message["d"]["heartbeat_interval"] / 1_000.0

        asyncio.create_task(self._dispatch(self, "CONNECTED", {}), name=f"shard {self._shard_id} dispatch CONNECTED")
        self.logger.debug("received HELLO")

        if self._session_id is not None:
            # RESUME!
            await self._send_json(
                {
                    "op": _GatewayOpcode.RESUME,
                    "d": {"token": self._token, "seq": self._seq, "session_id": self._session_id},
                }
            )

        else:
            # IDENTIFY!
            # noinspection PyArgumentList
            payload = {
                "op": _GatewayOpcode.IDENTIFY,
                "d": {
                    "token": self._token,
                    "compress": False,
                    "large_threshold": self.large_threshold,
                    "properties": user_agents.UserAgent().websocket_triplet,
                    "shard": [self._shard_id, self._shard_count],
                },
            }

            if self._intents is not None:
                payload["d"]["intents"] = self._intents

            if any(item is not None for item in (self._activity, self._idle_since, self._is_afk, self._status)):
                # noinspection PyTypeChecker
                payload["d"]["presence"] = self._build_presence_payload()

            await self._send_json(payload)

    async def _maintain_heartbeat(self) -> None:
        while not self._request_close_event.is_set():
            time_since_message = self._now() - self.last_message_received
            if self.heartbeat_interval < time_since_message:
                self.logger.error("connection is a zombie, haven't received any message for %ss", time_since_message)
                raise _Zombie()

            self.logger.debug("preparing to send HEARTBEAT [s:%s, interval:%ss]", self._seq, self.heartbeat_interval)
            await self._send_json({"op": _GatewayOpcode.HEARTBEAT, "d": self._seq})
            self.last_heartbeat_sent = self._now()

            try:
                await asyncio.wait_for(self._request_close_event.wait(), timeout=self.heartbeat_interval)
            except asyncio.TimeoutError:
                pass

    async def _poll_events(self) -> None:
        while not self._request_close_event.is_set():
            message = await self._recv_json()

            op = message["op"]
            data = message["d"]

            if op == _GatewayOpcode.DISPATCH:
                event = message["t"]
                self._seq = message["s"]
                if event == "READY":
                    self._session_id = data["session_id"]
                    self.logger.info("connection is ready [session:%s]", self._session_id)
                    self._ready_event.set()
                elif event == "RESUME":
                    self.logger.info("connection has resumed [session:%s, seq:%s]", self._session_id, self._seq)
                    self._resumed_event.set()

                asyncio.create_task(self._dispatch(self, event, data), name=f"shard {self._shard_id} dispatch {event}")

            elif op == _GatewayOpcode.HEARTBEAT:
                self.logger.debug("received HEARTBEAT; sending HEARTBEAT ACK")
                await self._send_json({"op": _GatewayOpcode.HEARTBEAT_ACK})

            elif op == _GatewayOpcode.HEARTBEAT_ACK:
                self.heartbeat_latency = self._now() - self.last_heartbeat_sent
                self.logger.debug("received HEARTBEAT ACK [latency:%ss]", self.heartbeat_latency)

            elif op == _GatewayOpcode.RECONNECT:
                self.logger.debug("RECONNECT")

                # 4000 close code allows us to resume without the session being invalided
                await self._ws.close(code=4000, message=b"processing RECONNECT")
                raise _Reconnect()

            elif op == _GatewayOpcode.INVALID_SESSION:
                self.logger.debug("INVALID SESSION [resume:%s]", data)
                await self._ws.close(code=4000, message=b"processing INVALID SESSION")
                raise _InvalidSession(data)

            else:
                self.logger.debug("ignoring unrecognised opcode %s", op)

    async def _recv_json(self) -> more_typing.JSONObject:
        message = await self._recv_raw()

        if message.type == aiohttp.WSMsgType.BINARY:
            n, string = await self._recv_zlib_str(message.data)
            self._log_pl_debug(string, "received %s zlib encoded packets", n)
        elif message.type == aiohttp.WSMsgType.TEXT:
            string = message.data
            self._log_pl_debug(string, "received text payload")
        elif message.type == aiohttp.WSMsgType.CLOSE:
            close_code = self._ws.close_code
            self.logger.debug("connection closed with code %s", close_code)

            reason = _GatewayCloseCode(close_code).name if close_code in _GatewayCloseCode else "unknown close code"

            can_reconnect = close_code in (
                _GatewayCloseCode.DECODE_ERROR,
                _GatewayCloseCode.INVALID_SEQ,
                _GatewayCloseCode.UNKNOWN_ERROR,
                _GatewayCloseCode.SESSION_TIMEOUT,
                _GatewayCloseCode.RATE_LIMITED,
            )

            raise errors.GatewayServerClosedConnectionError(reason, close_code, can_reconnect, False, True)
        elif message.type == aiohttp.WSMsgType.CLOSING or message.type == aiohttp.WSMsgType.CLOSED:
            if self._request_close_event.is_set():
                self.logger.debug("user has requested the gateway to close")
                raise errors.GatewayClientClosedError()
            self.logger.debug("connection has been closed unexpectedly, probably a network issue")
            raise errors.GatewayClientDisconnectedError()
        else:
            # Assume exception for now.
            ex = self._ws.exception()
            self.logger.debug("encountered unexpected error", exc_info=ex)
            raise errors.GatewayError("Unexpected websocket exception from gateway") from ex

        return json.loads(string)

    async def _recv_zlib_str(self, first_packet: bytes) -> typing.Tuple[int, str]:
        buff = bytearray(first_packet)

        packets = 1

        while not buff.endswith(b"\x00\x00\xff\xff"):
            message = await self._recv_raw()
            if message.type != aiohttp.WSMsgType.BINARY:
                raise errors.GatewayError(f"Expected a binary message but got {message.type}")
            buff.append(message.data)
            packets += 1

        return packets, self._zlib.decompress(buff).decode("utf-8")

    async def _recv_raw(self) -> aiohttp.WSMessage:
        packet = await self._ws.receive()
        self.last_message_received = self._now()
        return packet

    async def _send_json(self, payload: more_typing.JSONObject) -> None:
        await self.ratelimiter.acquire()
        message = json.dumps(payload)
        self._log_pl_debug(message, "sending json payload")
        await self._ws.send_str(message)

    @staticmethod
    def _now() -> float:
        return time.perf_counter()

    def _log_pl_debug(self, payload: str, message: str, *args: typing.Any) -> None:
        message = f"{message} [seq:%s, session:%s, size:%s]"
        if self._debug:
            message = f"{message} with raw payload: %s"
            args = (*args, self._seq, self._session_id, len(payload), payload)
        else:
            args = (*args, self._seq, self._session_id, len(payload))

        self.logger.debug(message, *args)

    def _build_presence_payload(
        self,
        idle_since: unset.MayBeUnset[typing.Optional[datetime.datetime]] = unset.UNSET,
        is_afk: unset.MayBeUnset[bool] = unset.UNSET,
        status: unset.MayBeUnset[guilds.PresenceStatus] = unset.UNSET,
        activity: unset.MayBeUnset[typing.Optional[gateway.Activity]] = unset.UNSET,
    ) -> more_typing.JSONObject:
        if unset.is_unset(idle_since):
            idle_since = self._idle_since
        if unset.is_unset(is_afk):
            is_afk = self._is_afk
        if unset.is_unset(status):
            status = self._status
        if unset.is_unset(activity):
            activity = self._activity

        return {
            "since": idle_since.timestamp() if idle_since is not None else None,
            "afk": is_afk if is_afk is not None else False,
            "status": status.value if status is not None else guilds.PresenceStatus.ONLINE.value,
            "game": activity.serialize() if activity is not None else None,
        }
