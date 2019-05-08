#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single-threaded asyncio V7 Gateway implementation with enforced rate limits to prevent disconnects, and basic
reconnection logic to handle reconnection and resume operations. Handles regular heartbeating in a background task
on the same event loop. Implements zlib transport compression only.

Can be used as the main gateway connection for a single-sharded bot, or the gateway connection for a specific shard
in a swarm of shards making up a larger bot.

References:
    - IANA WS closure code standards: https://www.iana.org/assignments/websocket/websocket.xhtml
    - Gateway documentation: https://discordapp.com/developers/docs/topics/gateway
    - Opcode documentation: https://discordapp.com/developers/docs/topics/opcodes-and-status-codes
"""

import asyncio
import json
import logging
import platform
import time
import zlib

from typing import Any, Awaitable, Callable, Dict, List, NoReturn, Optional, Union

import websockets


class ResumeConnection(websockets.ConnectionClosed):
    """Request to restart the client connection using a resume. This is only used internally."""


class RestartConnection(websockets.ConnectionClosed):
    """Request by the gateway to completely reconnect using a fresh connection. This is only used internally."""


def library_version() -> str:
    """Creates a string that is representative of the version of this library. This is only used internally."""
    import hikari

    return f"{hikari.__name__} v{hikari.__version__}"


def python_version() -> str:
    """Creates a comprehensive string representative of this version of python. This is only used internally."""
    attrs = [
        platform.python_implementation(),
        platform.python_version(),
        platform.python_revision(),
        platform.python_branch(),
        platform.python_compiler(),
        " ".join(platform.python_build()),
    ]
    return " ".join(a for a in attrs if a.strip())


#: The signature of an event dispatcher function. Consumes two arguments. The first is an event name from the gateway,
#: the second is the payload which is assumed to always be a :class:`dict` with :class:`str` keys. This should be
#: a coroutine function; if it is not, it should be expected to be promoted to a coroutine function internally.
#:
#: Example:
#:     >>> async def on_dispatch(event: str, payload: Dict[str, Any]) -> None:
#:     ...     logger.info("Dispatching %s with payload %r", event, payload)
DispatchHandler = Callable[[str, Dict[str, Any]], Union[None, Awaitable[None]]]

#: A payload received from the gateway or sent to the gateway.
GatewayPayload = Dict[str, Any]


# noinspection PyAsyncCall
class GatewayConnection:
    """
    Implementation of the gateway communication layer. This is single threaded and can represent the connection for
    an un-sharded bot, or for a specific gateway shard. This does not implement voice activity.

    Args:
        dispatch: A non-coroutine function that consumes a string event name and a JSON dispatch event payload consumed
            from the gateway to call each time a dispatch occurs. This payload will be a dict as described on the
            Gateway documentation.
        host: the host to connect to, in the format `wss://gateway.net` or `wss://gateway.net:port` without a query
            fragment.
        incognito: defaults to `False`. If `True`, then the platform, library version, and python version information
            in the `IDENTIFY` header will be redacted.
        initial_presence: A JSON-serializable dict containing the initial presence to set, or `None` to just appear
            `online`. See https://discordapp.com/developers/docs/topics/gateway#update-status for a description
            of this `update-status` payload object.
        large_threshold: the large threshold limit. Defaults to 50.
        loop: the event loop to run on. Required.
        max_persistent_buffer_size: Max size to allow the zlib buffer to grow to before recreating it. This defaults to
            3MiB. A larger value favours a slight (most likely unnoticeable) overall performance increase, at the cost
            of memory usage, since the gateway can send payloads tens of megabytes in size potentially. Without
            truncating, the payload will remain at the largest allocated size even when no longer required to provide
            that capacity.
        shard_count: the shard count to use, or `None` if sharding is to be disabled (default).
        shard_id: the shard ID to use, or `None` if sharding is to be disabled (default).
        token: the token to use to authenticate with the gateway.
    """

    #: The API version that this gateway client handles.
    API_VERSION = 7
    #: Number of payloads we are allowed to send within a :attr:`RATELIMIT_COOLDOWN` period.
    RATELIMIT_TOLERANCE = 119
    #: The length of a ratelimit cooldown, in seconds.
    RATELIMIT_COOLDOWN = 60

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

    _REDACTED = "redacted"

    def __init__(
        self,
        *,
        host: str,
        token: str,
        loop: asyncio.AbstractEventLoop,
        shard_id: Optional[int] = None,
        shard_count: Optional[int] = None,
        incognito: bool = False,
        large_threshold: int = 50,
        initial_presence: Optional[GatewayPayload] = None,
        dispatch: DispatchHandler = lambda t, d: None,
        max_persistent_buffer_size: int = 3 * 1024 ** 2,
    ) -> None:
        if not asyncio.iscoroutinefunction(dispatch):
            dispatch = asyncio.coroutine(dispatch)

        self._heartbeat_interval = float("nan")
        self._in_buffer: bytearray = bytearray()
        self._zlib_decompressor: Any = zlib.decompressobj()
        self._initial_presence = initial_presence
        self._last_ack_received = float("nan")
        self._last_heartbeat_sent = float("nan")
        self._logger = logging.getLogger(type(self).__name__)
        self._seq = None
        self._session_id = None
        self._rate_limit = asyncio.BoundedSemaphore(self.RATELIMIT_TOLERANCE, loop=loop)

        #: An :class:`asyncio.Event` that will be triggered whenever the gateway disconnects.
        self.closed_event = asyncio.Event(loop=loop)
        self.dispatch = dispatch
        #: The time period in seconds that the last heartbeat we sent took to be acknowledged by the gateway. This
        #: will be `float('nan')` until the first heartbeat is performed and acknowledged.
        self.heartbeat_latency = float("nan")
        self.incognito = incognito
        self.large_threshold = large_threshold
        self.loop = loop
        self.max_persistent_buffer_size = max_persistent_buffer_size
        #: A list of gateway servers that are connected to, once connected.
        self.trace: List[str] = []
        self.shard_count = shard_count
        self.shard_id = shard_id
        self.token = token
        #: The URI being connected to.
        self.uri = f"{host}?v={self.API_VERSION}&encoding=json&compression=zlib-stream"
        #: The :class:`websockets.WebSocketClientProtocol` handling the low-level connection logic. Populated only while
        #: connected.
        self.ws: Optional[websockets.WebSocketClientProtocol] = None

    async def _do_resume(self, code: int, reason: str) -> NoReturn:
        """Trigger a `RESUME` operation. This will raise a :class:`ResumableConnectionClosed` exception."""
        await self.ws.close(code=code, reason=reason)
        raise ResumeConnection(code=code, reason=reason)

    async def _do_reidentify(self, code: int, reason: str) -> NoReturn:
        """Trigger a re-`IDENTIFY` operation. This will raise a :class:`GatewayRequestedReconnection` exception."""
        await self.ws.close(code=code, reason=reason)
        raise RestartConnection(code=code, reason=reason)

    def _send_json_async(self, payload: GatewayPayload) -> asyncio.Future:
        """Sends a JSON payload asynchronously."""
        return self.loop.create_task(self._send_json(payload))

    async def _send_json(self, payload: GatewayPayload) -> None:
        """Sends a JSON payload now, awaiting any rate limit that may occur."""
        if self._rate_limit.locked():
            self._logger.debug("Shard %s: now being rate-limited", self.shard_id)

        async with self._rate_limit:
            raw = json.dumps(payload)

            if len(raw) > 4096:
                self._logger.error(
                    "Shard %s: Failed to send payload as it was too large. Sending this would result in "
                    "a disconnect. Payload was: %s",
                    self.shard_id,
                    payload,
                )
                return

            await self.ws.send(raw)

            # TODO: refactor to not spam the event loop with long-running tasks that are being awaited (use buckets)
            await asyncio.sleep(self.RATELIMIT_COOLDOWN)

    async def _receive_json(self) -> GatewayPayload:
        """Receives a string or zlib-compressed set of payloads and handles decoding it into a JSON object."""
        msg = await self.ws.recv()

        if type(msg) is bytes:
            self._in_buffer.extend(msg)
            while not self._in_buffer.endswith(b"\x00\x00\xff\xff"):
                msg = await self.ws.recv()
                self._in_buffer.extend(msg)

            msg = self._zlib_decompressor.decompress(self._in_buffer).decode("utf-8")

            # Prevent large packets persisting a massive buffer we never utilise.
            if len(self._in_buffer) > self.max_persistent_buffer_size:
                self._in_buffer = bytearray()
            else:
                self._in_buffer.clear()

        payload = json.loads(msg, encoding="utf-8")

        if not isinstance(payload, dict):
            return await self._do_reidentify(code=1007, reason="Expected JSON object.")

        return payload

    async def _keep_alive(self) -> None:
        """
        Runs the gateway client and attempts to keep it alive for as long as possible,
        handling restarts where appropriate.
        """
        while not self.closed_event.is_set():
            try:
                if (
                    self._last_heartbeat_sent + self._heartbeat_interval
                    < time.perf_counter()
                ):
                    last_sent = time.perf_counter() - self._last_heartbeat_sent
                    msg = f"Failed to receive an acknowledgement from the previous heartbeat sent ~{last_sent}s ago"
                    return await self._do_resume(code=1008, reason=msg)

                await asyncio.wait_for(
                    self.closed_event.wait(), timeout=self._heartbeat_interval
                )
            except asyncio.TimeoutError:
                start = time.perf_counter()
                await self._send_heartbeat()
                time_taken = time.perf_counter() - start

                if time_taken > 0.15 * self.heartbeat_latency:
                    self._logger.warning(
                        "Shard %s took %sms to send HEARTBEAT, which is more than 15%% of the heartbeat interval. "
                        "Your connection may be poor or the event loop may be blocking",
                        self.shard_id,
                        time_taken * 1_000,
                    )
            else:
                await self.ws.close(code=1000, reason="User requested shutdown")

    async def _send_heartbeat(self) -> None:
        """Sends a `HEARTBEAT` payload."""
        self._send_json_async({"op": self.HEARTBEAT_OP, "d": self._seq})
        self._logger.debug("Shard %s: sent HEARTBEAT", self.shard_id)
        self._last_heartbeat_sent = time.perf_counter()

    async def _send_ack(self) -> None:
        """Sends a `HEARTBEAT_ACK` payload."""
        self._send_json_async({"op": self.HEARTBEAT_ACK_OP})
        self._logger.debug("Shard %s: sent HEARTBEAT_ACK", self.shard_id)

    async def _handle_ack(self) -> None:
        """Should be triggered when a `HEARTBEAT_ACK` is received."""
        self._last_ack_received = time.perf_counter()
        self.heartbeat_latency = self._last_ack_received - self._last_heartbeat_sent
        self._logger.debug(
            "Shard %s: received expected HEARTBEAT_ACK after %sms",
            self.shard_id,
            self.heartbeat_latency * 1000,
        )

    async def _recv_hello(self) -> None:
        """Handles receiving a `HELLO` payload."""
        hello = await self._receive_json()
        op = hello["op"]
        if op != int(self.HELLO_OP):
            return await self._do_resume(
                code=1002, reason=f'Expected a "HELLO" opcode but got {op}'
            )

        d = hello["d"]
        self.trace = d["_trace"]
        self._heartbeat_interval = d["heartbeat_interval"] / 1_000.0
        self._logger.info(
            "Shard %s: received HELLO from %s with heartbeat interval %ss",
            self.shard_id,
            self.trace,
            self._heartbeat_interval,
        )

    async def _send_resume(self) -> None:
        """Sends a `RESUME` payload."""
        payload = {
            "op": self.RESUME_OP,
            "d": {
                "token": self.token,
                "session_id": self._session_id,
                "seq": self._seq,
            },
        }
        self._send_json_async(payload)
        self._logger.info(
            "Shard %s: RESUME connection to %s (session ID: %s)",
            self.shard_id,
            self.trace,
            self._session_id,
        )

    async def _send_identify(self) -> None:
        """Sends an `IDENTIFY` payload."""
        self._logger.info(
            "Shard %s: IDENTIFY with %s (session ID: %s)",
            self.shard_id,
            self.trace,
            self._session_id,
        )

        payload = {
            "op": self.IDENTIFY_OP,
            "d": {
                "token": self.token,
                "compress": False,
                "large_threshold": self.large_threshold,
                "properties": {
                    "$os": self.incognito and self._REDACTED or platform.system(),
                    "$browser": self.incognito and self._REDACTED or library_version(),
                    "$device": self.incognito and self._REDACTED or python_version(),
                },
            },
        }

        if self._initial_presence is not None:
            payload["d"]["status"] = self._initial_presence

        if self.shard_id is not None and self.shard_count is not None:
            # noinspection PyTypeChecker
            payload["d"]["shard"] = [self.shard_id, self.shard_count]

        self._send_json_async(payload)

    async def _process_events(self) -> None:
        """Polls the gateway for new packets and handles dispatching the results."""
        while not self.closed_event.is_set():
            message = await self._receive_json()
            op = message["op"]
            d = message["d"]
            seq = message.get("s", None)
            t = message.get("t", None)

            if seq is not None:
                self._seq = seq

            if op == self.DISPATCH_OP:
                self._logger.info("Shard %s: DISPATCH %s", self.shard_id, t)
                await self.dispatch(t, d)
            elif op == self.HEARTBEAT_OP:
                await self._send_ack()
            elif op == self.HEARTBEAT_ACK_OP:
                await self._handle_ack()
            elif op == self.RECONNECT_OP:
                self._logger.warning(
                    "Shard %s: instructed to disconnect and RESUME with gateway",
                    self.shard_id,
                )
                await self._do_reidentify(
                    code=1003, reason="Reconnect opcode was received, will reconnect"
                )
            elif op == self.INVALID_SESSION_OP:
                self._logger.warning(
                    "Shard %s: INVALID SESSION (id: %s), will try to re-IDENTIFY",
                    self.shard_id,
                    self._session_id,
                )

                if d:
                    await self._do_resume(
                        code=1003, reason="Session ID reported invalid, will resume"
                    )
                else:
                    await self._do_reidentify(
                        code=1003, reason="Session ID reported invalid, will disconnect"
                    )
            else:
                self._logger.warning(
                    "Shard %s: received unrecognised opcode %s", self.shard_id, op
                )

            # Yield to the event loop to prevent blocking it if we only logged.
            await asyncio.sleep(0)

    async def request_guild_members(self, guild_id: int) -> None:
        """
        Requests guild members from the given Guild ID. This can be used to retrieve all members available in a guild.

        Args:
            guild_id: the guild ID to request members from.

        Warning:
            Results will be dispatched as events in chunks of 1000 members per guild.
        """
        self._logger.debug(
            "Shard %s: requesting members in guild %s", self.shard_id, guild_id
        )
        self._send_json_async(
            {
                "op": self.REQUEST_GUILD_MEMBERS_OP,
                "d": {"guild_id": str(guild_id), "query": "", "limit": 0},
            }
        )

    async def update_status(
        self,
        idle_since: Optional[int],
        game: Optional[GatewayPayload],
        status: str,
        afk: bool,
    ) -> None:
        """
        Updates the bot user's status in this shard.

        Args:
            idle_since: unix timestamp in milliseconds that the user has been idle for, or `None` if not idle.
            game: an activity object representing the activity, or `None` if no activity is set.
            status: the status string to set.
            afk: True if the client is AFK, false otherwise.
        See:
            - Activity objects: https://discordapp.com/developers/docs/topics/gateway#activity-object
            - Valid statuses: https://discordapp.com/developers/docs/topics/gateway#update-status-status-types
        """
        self._logger.debug(
            "Shard %s: updating status to idle=%s, game=%s, status=%s, afk=%s",
            self.shard_id,
            idle_since,
            game,
            status,
            afk,
        )
        self._send_json_async(
            {
                "op": self.STATUS_UPDATE_OP,
                "d": {"idle": idle_since, "game": game, "status": status, "afk": afk},
            }
        )

    async def update_voice_state(
        self, guild_id: int, channel_id: Optional[int], self_mute: bool, self_deaf: bool
    ) -> None:
        """
        Updates the given shard's voice state (used to connect to/disconnect from/move between voice channels.

        Args:
            guild_id: the guild ID.
            channel_id: the channel ID, or `None` if you wish to disconnect.
            self_mute: if `True`, mute the bot, else if `False` keep the bot unmuted.
            self_deaf: if `True`, deafen the bot, else if `False`, keep the bot listening.
        """
        self._logger.debug(
            "Shard %s: updating voice state in guild %s, channel %s, mute: %s, deaf: %s",
            self.shard_id,
            guild_id,
            channel_id,
            self_mute,
            self_deaf,
        )
        self._send_json_async(
            {
                "op": self.VOICE_STATE_UPDATE_OP,
                "d": {
                    "guild_id": str(guild_id),
                    "channel_id": str(channel_id),
                    "self_mute": self_mute,
                    "self_deaf": self_deaf,
                },
            }
        )

    async def run(self) -> None:
        """Run the gateway and attempt to keep it alive for as long as possible using restarts and resumes if needed."""
        while not self.closed_event.is_set():
            try:
                kwargs = {"loop": self.loop, "uri": self.uri, "compression": None}
                async with websockets.connect(**kwargs) as self.ws:
                    await self._recv_hello()
                    is_resume = self._seq is not None and self._session_id is not None
                    await (self._send_resume() if is_resume else self._send_identify())
                    await asyncio.gather(self._keep_alive(), self._process_events())
            except (RestartConnection, ResumeConnection) as ex:
                self._logger.warning(
                    "Shard %s: reconnecting after %s [%s]", 
                    self.shard_id,
                    ex.reason,
                    ex.code,
                )

                if isinstance(ex, RestartConnection):
                    self._seq, self._session_id, self.trace = None, None, None
                await asyncio.sleep(2)
            self._logger.info("Shard %s: gateway client shutting down", self.shard_id)

    async def close(self, block=True) -> None:
        """
        Request that the gateway gracefully shuts down. Once this has occurred, you should not reuse this object. Doing
        so will result in undefined behaviour.

        Args:
            block: await the closure of the websocket connection. Defaults to `True`. If `False`, then nothing is
                waited for.
        """
        self.closed_event.set()
        if block:
            await self.ws.wait_closed()
