#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single-threaded asyncio V7 Gateway implementation with enforced ratelimits.

References:
    IANA WS closure code standards: https://www.iana.org/assignments/websocket/websocket.xhtml
    Gateway documentation: https://discordapp.com/developers/docs/topics/gateway
    Opcode documentation: https://discordapp.com/developers/docs/topics/opcodes-and-status-codes
"""

import asyncio
import json
import logging
import platform
import time
import zlib

from typing import Any, Callable, Dict, List, NoReturn, Optional
from urllib import parse as urlparse

import websockets


class ResumableConnectionClosed(websockets.ConnectionClosed):
    """Request to restart the client connection using a resume."""


class GatewayRequestedReconnection(websockets.ConnectionClosed):
    """Request by the gateway to completely reconnect using a fresh connection."""


def _get_lib_version() -> str:
    # Get the version number of the lib. Done here to prevent circular references later.
    import hikari

    return f"{hikari.__name__} v{hikari.__version__}"


def _get_python_version() -> str:
    # Produce a signature of the python build being used.
    attrs = [
        platform.python_implementation(),
        platform.python_version(),
        platform.python_revision(),
        platform.python_branch(),
        platform.python_compiler(),
        " ".join(platform.python_build()),
    ]
    return " ".join(a for a in attrs if a.strip())


class GatewayConnection:
    """
    Implementation of the gateway communication layer. This is single threaded and can represent the connection for
    an un-sharded bot, or for a specific gateway shard. This does not implement voice activity.

    Args:
        uri:
            the URI to connect to.
        shard_id:
            the shard ID to use, or `None` if sharding is to be disabled (default).
        shard_count:
            the shard count to use, or `None` if sharding is to be disabled (default).
        loop:
            the event loop to run on. Required.
        token:
            the token to use to authenticate with the gateway.
        incognito:
            defaults to `False`. If `True`, then the platform, library version, and python version information in the
            `IDENTIFY` header will be redacted.
        large_threshold:
            the large threshold limit. Defaults to 50.
        initial_presence:
            A JSON-serializable dict containing the initial presence to set, or `None` to just appear `online`.
        dispatch:
            A non-coroutine function that consumes a string event name and a JSON dispatch event payload consumed from
            the gateway to call each time a dispatch occurs. This payload will be a dict as described on the Gateway
            documentation.
    """

    API_VERSION = 7
    PAYLOAD_ENCODING = "json"
    ZLIB_SUFFIX = b"\x00\x00\xff\xff"

    DISPATCH_OP = 0
    HEARTBEAT_OP = 1
    IDENTIFY_OP = 2
    STATUS_UPDATE_OP = 3
    VOICE_STATE_UPDATE_OP = 4
    RESUME_OP = 6
    RECONNECT_OP = 7
    REQUEST_GUILD_MEMBERS_OP = 8
    INVALID_SESSION_OP = 9
    HELLO_OP = 10
    HEARTBEAT_ACK_OP = 11
    GUILD_SYNC_OP = 12  # Awaiting proper documentation!

    REDACTED = "redacted"
    RATELIMIT_TOLERANCE = 119
    RATELIMIT_COOLDOWN = 60

    def __init__(
        self,
        *,
        uri: str,
        shard_id: Optional[int] = None,
        shard_count: Optional[int] = None,
        loop: asyncio.AbstractEventLoop,
        token: str,
        incognito: bool = False,
        large_threshold: int = 50,
        initial_presence=None,
        dispatch: Callable[[str, Dict[str, Any]], None] = lambda t, d: None,
    ) -> None:
        self._closed_event = asyncio.Event(loop=loop)
        self._heartbeat_interval = float("nan")
        self._last_ack_received = float("nan")
        self._last_heartbeat_sent = float("nan")
        self._seq = None
        self._session_id = None
        self.dispatch = dispatch
        self.heartbeat_latency = float("nan")
        self.inflator: Any = zlib.decompressobj()
        self.incognito = incognito
        self.in_buffer: bytearray = bytearray()
        self.large_threshold = large_threshold
        self.logger = logging.getLogger(type(self).__name__)
        self.loop = loop
        self.presence = initial_presence
        self.rate_limit_semaphore = asyncio.BoundedSemaphore(
            self.RATELIMIT_TOLERANCE, loop=loop
        )
        self.servers: List[str] = []
        self.shard_count = shard_count
        self.shard_id = shard_id
        self.token = token
        self.uri = f"{urlparse.splitquery(uri)[0]}?v={self.API_VERSION}&encoding={self.PAYLOAD_ENCODING}"

        # Populated as needed...
        self.ws: Optional[websockets.WebSocketClientProtocol] = None

    async def _force_resume(self, code: int, reason: str) -> NoReturn:
        await self.ws.close(code=code, reason=reason)
        raise ResumableConnectionClosed(code=code, reason=reason)

    async def _force_reidentify(self, code: int, reason: str) -> NoReturn:
        await self.ws.close(code=code, reason=reason)
        raise GatewayRequestedReconnection(code=code, reason=reason)

    async def _send_json(self, payload: Any) -> None:
        # Schedule to send a JSON payload to the gateway without awaiting completion.
        self.loop.create_task(self._send_json_now(payload))

    async def _send_json_now(self, payload: Any) -> None:
        # Send a JSON payload and await the completion, taking into account queueing if rate-limited.
        if self.rate_limit_semaphore.locked():
            self.logger.debug(
                "You are being rate-limited on the gateway to prevent disconnecting. If this keeps "
                "occurring you should consider sharding"
            )

        async with self.rate_limit_semaphore:
            raw = json.dumps(payload)
            await self.ws.send(raw)
            # 1 second + a slight overhead to prevent time differences ever causing an issue where we still get kicked.
            await asyncio.sleep(self.RATELIMIT_COOLDOWN)

    async def _receive_json(self) -> Dict[str, Any]:
        # Consumes a message from the gateway and decodes it as JSON before returning it.
        content = await self.ws.recv()

        if isinstance(content, bytes):
            self.in_buffer.extend(content)

            while not self.in_buffer.endswith(self.ZLIB_SUFFIX):
                next_packet = await self.ws.recv()
                self.in_buffer.extend(next_packet)

            content = self.inflator.decompress(self.in_buffer).decode("utf-8")
            self.in_buffer.clear()

        payload = json.loads(content, encoding="utf-8")

        if not isinstance(payload, dict):
            return await self._force_reidentify(
                code=1007, reason="Expected all payloads to be dictionaries."
            )

        return payload

    async def _hello(self) -> None:
        # Send the HELLO payload
        hello = await self._receive_json()
        op = hello["op"]
        if op != int(self.HELLO_OP):
            return await self._force_resume(
                code=1002, reason=f'Expected a "HELLO" opcode, got {op}'
            )

        d = hello["d"]
        self.servers = d["_trace"]
        self._heartbeat_interval = d["heartbeat_interval"] / 1_000
        self.logger.info(
            "Connected to %s with interval %ss on shard ID %s",
            ", ".join(self.servers),
            self._heartbeat_interval,
            self.shard_id,
        )

    async def _keep_alive(self) -> None:
        while True:
            try:
                if (
                    self._last_ack_received
                    < self._last_heartbeat_sent - self._heartbeat_interval
                ):
                    last_sent = time.perf_counter() - self._last_heartbeat_sent
                    msg = f"Failed to receive an acknowledgement from the previous heartbeat sent ~{last_sent}s ago"
                    return await self._force_resume(code=1008, reason=msg)

                await asyncio.wait_for(
                    self._closed_event.wait(), timeout=self._heartbeat_interval
                )
                await self.ws.close(code=1000, reason="User requested shutdown")
            except asyncio.TimeoutError:
                start = time.perf_counter()
                await self._send_heartbeat()
                time_taken = time.perf_counter() - start

                if time_taken > 0.15 * self.heartbeat_latency:
                    self.logger.warning(
                        "Shard %s took %sms to send a heartbeat, which is more than 15% of the heartbeat interval. "
                        "Your connection may be poor or the event loop may be blocking",
                        self.shard_id,
                        time_taken * 1_000,
                    )
                else:
                    self.logger.debug(
                        "Sent heartbeat to gateway %s for shard %s",
                        self.servers,
                        self.shard_id,
                    )

    async def _send_heartbeat(self) -> None:
        self.logger.debug(
            "Sending heartbeat to gateway %s for shard %s", self.servers, self.shard_id
        )
        await self._send_json({"op": self.HEARTBEAT_OP, "d": self._seq})
        self._last_heartbeat_sent = time.perf_counter()

    async def _send_ack(self) -> None:
        self.logger.debug(
            "Sending heartbeat ack to gateway %s for shard %s",
            self.servers,
            self.shard_id,
        )
        await self._send_json({"op": self.HEARTBEAT_ACK_OP})

    async def _handle_ack(self) -> None:
        self._last_ack_received = time.perf_counter()
        self.heartbeat_latency = self._last_ack_received - self._last_heartbeat_sent
        self.logger.debug(
            "Received heartbeat ack from gateway %s for shard %s in %sms",
            self.servers,
            self.shard_id,
            self.heartbeat_latency * 1000,
        )

    async def _resume(self) -> None:
        payload = {
            "op": self.RESUME_OP,
            "d": {
                "token": self.token,
                "session_id": self._session_id,
                "seq": self._seq,
            },
        }
        await self._send_json(payload)
        self.logger.info(
            "RESUMED connection to the gateway %s for shard %s (session id %s)",
            self.servers,
            self.shard_id,
            self._session_id,
        )

    async def _identify(self) -> None:
        self.logger.info(
            "IDENTIFIED shard %s with the gateway at %s", self.shard_id, self.servers
        )

        payload = {
            "op": self.IDENTIFY_OP,
            "d": {
                "token": self.token,
                "compress": False,
                "large_threshold": self.large_threshold,
                "properties": {
                    "$os": self.incognito and self.REDACTED or platform.system(),
                    "$browser": self.incognito and self.REDACTED or _get_lib_version(),
                    "$device": self.incognito
                    and self.REDACTED
                    or _get_python_version(),
                },
            },
        }

        if self.presence is not None:
            payload["d"]["status"] = self.presence

        if self.shard_id is not None and self.shard_count is not None:
            # noinspection PyTypeChecker
            payload["d"]["shard"] = [self.shard_id, self.shard_count]

        await self._send_json(payload)

    async def _dispatch(self, payload) -> None:
        self.logger.info(
            "Shard %s on gateway %s got dispatch of %s but it is not yet implemented",
            self.shard_id,
            self.servers,
            payload,
        )

    async def _process_events(self) -> None:
        while True:
            message = await self._receive_json()
            op = message["op"]
            d = message["d"]
            seq = message.get("s", None)
            t = message.get("t", None)

            if seq is not None:
                self._seq = seq

            if op == self.DISPATCH_OP:
                await self._dispatch(t, d)
            elif op == self.HEARTBEAT_OP:
                await self._send_ack()
            elif op == self.RECONNECT_OP:
                self.logger.warning(
                    "The gateway %s has requested shard %s reconnects to the gateway. "
                    "Disconnecting now",
                    self.servers,
                    self.shard_id,
                )
                return await self._force_reidentify(
                    code=1003, reason="Reconnect opcode was received"
                )
            elif op == self.INVALID_SESSION_OP:
                self.logger.warning(
                    "The session ID %s is invalid for shard %s connected to gateway %s. "
                    "Disconnecting now",
                    self._session_id,
                    self.shard_id,
                    self.servers,
                )
                return await self._force_reidentify(
                    code=1003, reason="Session ID was reported as being invalid"
                )
            elif op == self.HEARTBEAT_ACK_OP:
                await self._handle_ack()
            else:
                self.logger.warning(
                    "Shard %s connected to gateway %s received unrecognised opcode %s",
                    self.shard_id,
                    self.servers,
                    op,
                )

    async def run(self) -> None:
        while True:
            try:
                async with websockets.connect(self.uri) as self.ws:
                    await self._hello()
                    await (
                        self._identify()
                        if self._seq is None and self._session_id is None
                        else self._resume()
                    )
                    await asyncio.gather(self._keep_alive(), self._process_events())
                    raise AssertionError("This should never be hit")
            except (GatewayRequestedReconnection, ResumableConnectionClosed) as ex:
                self.logger.warning(
                    "Restarting shard %s connected to %s because %s %s",
                    self.shard_id,
                    self.servers,
                    ex.code,
                    ex.reason,
                )

                if isinstance(ex, GatewayRequestedReconnection):
                    self._seq = None
                    self._session_id = None
                    self.servers = None
                await asyncio.sleep(2)

    async def close(self) -> None:
        self._closed_event.set()
        await self.ws.wait_closed()
