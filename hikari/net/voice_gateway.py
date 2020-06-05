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
"""Implementation of the V4 voice gateway."""
from __future__ import annotations

__all__ = ["VoiceGateway"]

import asyncio
import enum
import math
import time
import typing
import urllib.parse

import aiohttp
import attr

from hikari import errors
from hikari.api import component
from hikari.net import http_client
from hikari.net import ratelimits
from hikari.utilities import data_binding
from hikari.utilities import klass

if typing.TYPE_CHECKING:
    from hikari.api import app as app_
    from hikari import bot
    from hikari.net import http_settings
    from hikari.models import bases


class VoiceGateway(http_client.HTTPClient, component.IComponent):
    """Implementation of the V4 Voice Gateway."""

    @enum.unique
    class _GatewayCloseCode(enum.IntEnum):
        """Reasons for closing a gateway connection."""

        RFC_6455_NORMAL_CLOSURE = 1000
        RFC_6455_GOING_AWAY = 1001
        RFC_6455_PROTOCOL_ERROR = 1002
        RFC_6455_TYPE_ERROR = 1003
        RFC_6455_ENCODING_ERROR = 1007
        RFC_6455_POLICY_VIOLATION = 1008
        RFC_6455_TOO_BIG = 1009
        RFC_6455_UNEXPECTED_CONDITION = 1011

        UNKNOWN_OPCODE = 4001
        NOT_AUTHENTICATED = 4003
        AUTHENTICATION_FAILED = 4004
        ALREADY_AUTHENTICATED = 4005
        SESSION_NO_LONGER_VALID = 4006
        SESSION_TIMEOUT = 4009
        SERVER_NOT_FOUND = 4011
        UNKNOWN_PROTOCOL = 4012
        DISCONNECTED = 4014
        VOICE_SERVER_CRASHED = 4015
        UNKNOWN_ENCRYPTION_MODE = 4016

    @enum.unique
    class _GatewayOpcode(enum.IntEnum):
        IDENTIFY = 0
        SELECT_PROTOCOL = 1
        READY = 2
        HEARTBEAT = 3
        SESSION_DESCRIPTION = 4
        SPEAKING = 5
        HEARTBEAT_ACK = 6
        RESUME = 7
        HELLO = 8
        RESUMED = 9
        CLIENT_DISCONNECT = 13

    class _Reconnect(RuntimeError):
        __slots__ = ()

    class _SocketClosed(RuntimeError):
        __slots__ = ()

    @attr.s(auto_attribs=True, slots=True)
    class _InvalidSession(RuntimeError):
        can_resume: bool = False

    def __init__(
        self,
        *,
        app: bot.IBot,
        config: http_settings.HTTPSettings,
        debug: bool = False,
        endpoint: str,
        session_id: str,
        user_id: bases.UniqueObject,
        server_id: bases.UniqueObject,
        token: str,
    ) -> None:
        super().__init__(
            allow_redirects=config.allow_redirects,
            connector=config.tcp_connector_factory() if config.tcp_connector_factory else None,
            debug=debug,
            # Use the server ID to identify each websocket based on a server.
            logger=klass.get_logger(self, str(int(server_id))),
            proxy_auth=config.proxy_auth,
            proxy_headers=config.proxy_headers,
            proxy_url=config.proxy_url,
            ssl_context=config.ssl_context,
            verify_ssl=config.verify_ssl,
            timeout=config.request_timeout,
            trust_env=config.trust_env,
        )

        # The port Discord gives me is plain wrong, which is helpful.
        path = endpoint.rpartition(":")[0]
        query = urllib.parse.urlencode({"v": "4"})
        self._url = f"wss://{path}?{query}"

        self._app = app
        self._backoff = ratelimits.ExponentialBackOff(base=1.85, maximum=600, initial_increment=2)
        self._last_run_started_at = float("nan")
        self._nonce = None
        self._request_close_event = asyncio.Event()
        self._resumable = False
        self._server_id = str(int(server_id))
        self._session_id = session_id
        self._token = token
        self._user_id = str(int(user_id))
        self._voice_ip = None
        self._voice_modes = []
        self._voice_port = None
        self._voice_ssrc = None
        self._ws = None
        self._zombied = False

        self.connected_at = float("nan")
        self.heartbeat_interval = float("nan")
        self.heartbeat_latency = float("nan")
        self.last_heartbeat_sent = float("nan")
        self.last_message_received = float("nan")

    @property
    def is_alive(self) -> bool:
        """Return whether the client is alive."""
        return not math.isnan(self.connected_at)

    @property
    def app(self) -> app_.IApp:
        return self._app

    async def run(self) -> None:
        """Start the voice gateway client session."""
        try:
            while not self._request_close_event.is_set() and await self._run_once():
                pass
        finally:
            # Close the aiohttp client session.
            await super().close()

    async def close(self) -> None:
        """Close the websocket."""
        if not self._request_close_event.is_set():
            if self.is_alive:
                self.logger.info("received request to shut down voice gateway client")
            else:
                self.logger.debug("voice gateway client marked as closed before it was able to start")
            self._request_close_event.set()

            if self._ws is not None:
                self.logger.warning("voice gateway client closed by user, will not attempt to restart")
                await self._close_ws(self._GatewayCloseCode.RFC_6455_NORMAL_CLOSURE, "user shut down application")

    async def _close_ws(self, code: int, message: str):
        self.logger.debug("sending close frame with code %s and message %r", int(code), message)
        # None if the websocket errored on initialziation.
        if self._ws is not None:
            await self._ws.close(code=code, message=bytes(message, "utf-8"))

    async def _run_once(self):
        self._request_close_event.clear()

        if self._now() - self._last_run_started_at < 30:
            # Interrupt sleep immediately if a request to close is fired.
            wait_task = asyncio.create_task(
                self._request_close_event.wait(), name=f"voice gateway client {self._server_id} backing off"
            )
            try:
                backoff = next(self._backoff)
                self.logger.debug("backing off for %ss", backoff)
                await asyncio.wait_for(wait_task, timeout=backoff)
                return False
            except asyncio.TimeoutError:
                pass

        # Do this after; it prevents backing off on the first try.
        self._last_run_started_at = self._now()

        try:
            self.logger.debug("creating websocket connection to %s", self._url)
            self._ws = await self._create_ws(self._url)
            self.connected_at = self._now()
            await self._handshake()

            # Technically we are connected after the hello, but this ensures we can send and receive
            # before firing that event.
            await self._on_connect()

            # We should ideally set this after HELLO, but it should be fine
            # here as well. If we don't heartbeat in time, something probably
            # went majorly wrong anyway.
            heartbeat = asyncio.create_task(self._pulse(), name=f"voice gateway client {self._server_id} heartbeat")

            try:
                await self._poll_events()
            finally:
                heartbeat.cancel()
        except aiohttp.ClientConnectionError as ex:
            self.logger.error(
                "failed to connect to Discord because %s.%s: %s", type(ex).__module__, type(ex).__qualname__, str(ex),
            )

        except Exception as ex:
            self.logger.error("unexpected exception occurred, shard will now die", exc_info=ex)
            await self._close_ws(self._GatewayCloseCode.RFC_6455_UNEXPECTED_CONDITION, "unexpected error occurred")
            raise

        finally:
            if not math.isnan(self.connected_at):
                # Only dispatch this if we actually connected before we failed!
                await self._on_disconnect()

            self.connected_at = float("nan")
        return True

    async def _poll_events(self):
        while not self._request_close_event.is_set():
            message = await self._receive_json_payload()

            op = message["op"]
            data = message["d"]

            if op == self._GatewayOpcode.READY:
                self.logger.debug(
                    "voice websocket is ready [session_id:%s, url:%s]", self._session_id, self._url,
                )
            elif op == self._GatewayOpcode.RESUMED:
                self.logger.debug(
                    "voice websocket has resumed [session_id:%s, nonce:%s, url:%s]",
                    self._session_id,
                    self._nonce,
                    self._url,
                )
            elif op == self._GatewayOpcode.HEARTBEAT:
                self.logger.debug("received HEARTBEAT; sending HEARTBEAT ACK")
                await self._send_json({"op": self._GatewayOpcode.HEARTBEAT_ACK, "d": self._nonce})
            elif op == self._GatewayOpcode.HEARTBEAT_ACK:
                self.heartbeat_latency = self._now() - self.last_heartbeat_sent
                self.logger.debug("received HEARTBEAT ACK [latency:%ss]", self.heartbeat_latency)
            elif op == self._GatewayOpcode.SESSION_DESCRIPTION:
                self.logger.debug("received session description data %s", data)
            elif op == self._GatewayOpcode.SPEAKING:
                self.logger.debug("someone is speaking with data %s", data)
            elif op == self._GatewayOpcode.CLIENT_DISCONNECT:
                self.logger.debug("a client has disconnected with data %s", data)
            else:
                self.logger.debug("ignoring unrecognised opcode %s", op)

    async def _pulse(self) -> None:
        try:
            while not self._request_close_event.is_set():
                now = self._now()
                time_since_message = now - self.last_message_received
                time_since_heartbeat_sent = now - self.last_heartbeat_sent

                if self.heartbeat_interval < time_since_message:
                    self.logger.error(
                        "connection is a zombie, haven't received any message for %ss, last heartbeat sent %ss ago",
                        time_since_message,
                        time_since_heartbeat_sent,
                    )
                    self._zombied = True
                    await self._close_ws(self._GatewayCloseCode.DO_NOT_INVALIDATE_SESSION, "zombie connection")
                    return

                self.logger.debug(
                    "preparing to send HEARTBEAT [nonce:%s, interval:%ss]", self._nonce, self.heartbeat_interval
                )
                await self._send_json({"op": self._GatewayOpcode.HEARTBEAT, "d": self._nonce})
                self.last_heartbeat_sent = self._now()

                try:
                    await asyncio.wait_for(self._request_close_event.wait(), timeout=self.heartbeat_interval)
                except asyncio.TimeoutError:
                    pass

        except asyncio.CancelledError:
            # This happens if the poll task has stopped. It isn't a problem we need to report.
            pass

    async def _on_connect(self):
        pass

    async def _on_disconnect(self):
        pass

    async def _handshake(self):
        # HELLO!
        message = await self._receive_json_payload()
        op = message["op"]
        if message["op"] != self._GatewayOpcode.HELLO:
            await self._close_ws(self._GatewayCloseCode.RFC_6455_POLICY_VIOLATION.value, "did not receive HELLO")
            raise errors.GatewayError(f"Expected HELLO opcode {self._GatewayOpcode.HELLO.value} but received {op}")

        self.heartbeat_interval = message["d"]["heartbeat_interval"]

        self.logger.debug("received HELLO, heartbeat interval is %s", self.heartbeat_interval)

        if self._session_id is not None:
            # RESUME!
            await self._send_json(
                {
                    "op": self._GatewayOpcode.RESUME,
                    "d": {"token": self._token, "server_id": self._server_id, "session_id": self._session_id},
                }
            )
        else:
            await self._send_json(
                {
                    "op": self._GatewayOpcode.IDENTIFY,
                    "d": {
                        "token": self._token,
                        "server_id": self._server_id,
                        "user_id": self._user_id,
                        "session_id": self._session_id,
                    },
                }
            )

    async def _receive_json_payload(self) -> data_binding.JSONObject:
        message = await self._ws.receive()
        self.last_message_received = self._now()

        if message.type == aiohttp.WSMsgType.TEXT:
            self._log_debug_payload(message.data, "received text payload")
            return data_binding.load_json(message.data)

        elif message.type == aiohttp.WSMsgType.CLOSE:
            close_code = self._ws.close_code
            self.logger.debug("connection closed with code %s", close_code)

            if close_code in self._GatewayCloseCode.__members__.values():
                reason = self._GatewayCloseCode(close_code).name
            else:
                reason = f"unknown close code {close_code}"

            can_reconnect = close_code in (
                self._GatewayCloseCode.SESSION_NO_LONGER_VALID,
                self._GatewayCloseCode.SESSION_TIMEOUT,
                self._GatewayCloseCode.DISCONNECTED,
                self._GatewayCloseCode.VOICE_SERVER_CRASHED,
            )

            raise errors.GatewayServerClosedConnectionError(reason, close_code, can_reconnect, False, True)

        elif message.type == aiohttp.WSMsgType.CLOSING or message.type == aiohttp.WSMsgType.CLOSED:
            raise self._SocketClosed()
        else:
            # Assume exception for now.
            ex = self._ws.exception()
            self.logger.debug("encountered unexpected error", exc_info=ex)
            raise errors.GatewayError("Unexpected websocket exception from gateway") from ex

    async def _send_json(self, payload: data_binding.JSONObject) -> None:
        message = data_binding.dump_json(payload)
        self._log_debug_payload(message, "sending json payload")
        await self._ws.send_str(message)

    def _log_debug_payload(self, payload: str, message: str, *args: typing.Any) -> None:
        message = f"{message} [nonce:%s, url:%s, session_id: %s, server: %s, size:%s]"
        if self._debug:
            message = f"{message} with raw payload: %s"
            args = (*args, self._nonce, self._url, self._session_id, self._server_id, len(payload), payload)
        else:
            args = (*args, self._nonce, self._url, self._session_id, self._server_id, len(payload))

        self.logger.debug(message, *args)

    @staticmethod
    def _now() -> float:
        return time.perf_counter()
