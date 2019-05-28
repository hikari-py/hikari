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
import contextlib
import enum
import json
import logging
import platform
import time
import zlib
import typing

import websockets

from . import bucket


class ResumeConnection(websockets.ConnectionClosed):
    """Request to restart the client connection using a resume. This is only used internally."""


class RestartConnection(websockets.ConnectionClosed):
    """Request by the gateway to completely reconnect using a fresh connection. This is only used internally."""


def library_version() -> str:
    """Creates a string that is representative of the version of this library. This is only used internally."""
    from hikari import __version__
    return f"hikari v{__version__}"


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
DispatchHandler = typing.Callable[[str, typing.Dict[str, typing.Any]], typing.Union[None, typing.Awaitable[None]]]

#: A payload received from the gateway or sent to the gateway.
GatewayPayload = typing.Dict[str, typing.Any]


class GatewayLogger(logging.LoggerAdapter):
    """Formatting shim for the logger API for gateway logging logic."""

    SHARDED_FMT = "{{shard:{shd}/{tshd} seq:{s} session:{sid} trace:{t}}} {msg}"
    UNSHARDED_FMT = "{{seq:{s} session:{sid} trace:{t}}} {msg}"

    def __init__(self, logger, extra, sharded: bool) -> None:
        super().__init__(logger, extra)
        self.__fmt = self.SHARDED_FMT if sharded else self.UNSHARDED_FMT

    def process(self, msg, kwargs):
        args = {k: v() if callable(v) else v for k, v in self.extra.items()}
        return self.__fmt.format(**args, msg=msg), kwargs


class Opcode(enum.IntEnum):
    """Gateway opcodes."""

    #: An event was dispatched.
    DISPATCH = 0
    #: Used for ping checking.
    HEARTBEAT = 1
    #: Used for client handshake.
    IDENTIFY = 2
    #: Used to update the client status.
    STATUS_UPDATE = 3
    #: Used to join/move/leave voice channels.
    VOICE_STATE_UPDATE = 4
    #: Deprecated. Do not use!
    VOICE_PING = 5
    #: Used to resume a closed connection.
    RESUME = 6
    #: Used to tell clients to reconnect to the gateway.
    RECONNECT = 7
    #: Used to request guild members.
    REQUEST_GUILD_MEMBERS = 8
    #: Used to notify client they have an invalid session id.
    INVALID_SESSION = 9
    #: Sent immediately after connecting, contains heartbeat and server debug information.
    HELLO = 10
    #: Sent immediately following a client heartbeat that was received.
    HEARTBEAT_ACK = 11
    #: Not yet documented, so do not use.
    GUILD_SYNC = 12


class ClientExit(enum.IntEnum):
    """Reasons for closing a connection that we can send the gateway."""

    #: Normal exit state (normal client workflow or a requested disconnect). Nothing is wrong.
    NORMAL_CLOSURE = 1000
    #: The client is shutting down and will not immediately come back up.
    GOING_AWAY = 1001
    #: The gateway did something we didn't expect it to do.
    PROTOCOL_VIOLATION = 1002
    #: The gateway sent something we didn't expect to receive.
    TYPE_ERROR = 1003
    #: Logic has failed internally.
    INTERNAL_ERROR = 1011


class ServerExit(enum.IntEnum):
    """Reasons for closing a connection that the gateway can send us."""

    #: We're not sure what went wrong. Try reconnecting?
    UNKNOWN_ERROR = 4000
    #: You sent an invalid Gateway opcode or an invalid payload for an opcode. Don't do that!
    UNKNOWN_OPCODE = 4001
    #: You sent an invalid payload to us. Don't do that!
    DECODE_ERROR = 4002
    #: You sent us a payload prior to identifying.
    NOT_AUTHENTICATED = 4003
    #: The account token sent with your identify payload is incorrect.
    AUTHENTICATION_FAILED = 4004
    #: You sent more than one identify payload. Don't do that!
    ALREADY_AUTHENTICATED = 4005
    #: The sequence sent when resuming the session was invalid. Reconnect and start a new session.
    INVALID_SEQ = 4007
    #: Woah nelly! You're sending payloads to us too quickly. Slow it down! (Hopefully this will be prevented).
    RATE_LIMITED = 4008
    #: Your session timed out. Reconnect and start a new one.
    SESSION_TIMEOUT = 4009
    #: You sent us an invalid shard when identifying.
    INVALID_SHARD = 4010
    #: The session would have handled too many guilds - you are required to shard your connection in order to connect.
    SHARDING_REQUIRED = 4011


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

    #: The API version we should request the use of.
    _REQUESTED_VERSION = 7
    _RATE_LIMIT_AT = 119
    _MAX_PAYLOAD_SIZE = 4096
    _COOLDOWN = 60
    _NEVER_RECONNECT_CODES = (ServerExit.AUTHENTICATION_FAILED, ServerExit.INVALID_SHARD, ServerExit.SHARDING_REQUIRED)
    _LOGGER = logging.getLogger(__name__)

    def __init__(
        self,
        *,
        host: str,
        token: str,
        loop: asyncio.AbstractEventLoop,
        shard_id: typing.Optional[int] = None,
        shard_count: typing.Optional[int] = None,
        incognito: bool = False,
        large_threshold: int = 50,
        initial_presence: typing.Optional[GatewayPayload] = None,
        dispatch: DispatchHandler = lambda t, d: None,
        max_persistent_buffer_size: int = 3 * 1024 ** 2,
    ) -> None:
        # Sharding info
        self.shard_count = shard_count
        self.shard_id = shard_id

        # Set up logging.
        extra = dict(
            shd=shard_id, tshd=shard_count, s=lambda: self._seq, t=lambda: self.trace, sid=lambda: self._session_id
        )
        self._logger = GatewayLogger(self._LOGGER, extra, self.is_shard)

        dispatch = asyncio.coroutine(dispatch)

        self._heartbeat_interval = float("nan")
        self._in_buffer: bytearray = bytearray()
        self._initial_presence = initial_presence
        self._last_ack_received = float("nan")
        self._last_heartbeat_sent = float("nan")
        self._seq = None
        self._session_id = None
        self._rate_limit = bucket.LeakyBucket(self._RATE_LIMIT_AT, self._COOLDOWN, loop)
        self._zlib_decompressor: typing.Any = zlib.decompressobj()

        #: An :class:`asyncio.Event` that will be triggered whenever the gateway disconnects.
        self.closed_event = asyncio.Event(loop=loop)
        #: The coroutine function to dispatch any events to.
        self.dispatch = dispatch
        #: The time period in seconds that the last heartbeat we sent took to be acknowledged by the gateway. This
        #: will be `float('nan')` until the first heartbeat is performed and acknowledged.
        self.heartbeat_latency = float("nan")
        self.incognito = incognito
        self.large_threshold = large_threshold
        self.loop = loop
        self.max_persistent_buffer_size = max_persistent_buffer_size
        #: A list of gateway servers that are connected to, once connected.
        self.trace: typing.List[str] = []
        self.token = token
        #: The URI being connected to.
        self.uri = f"{host}?v={self._REQUESTED_VERSION}&encoding=json&compression=zlib-stream"
        #: The :class:`websockets.WebSocketClientProtocol` handling the low-level connection logic. Populated only while
        #: connected.
        self.ws: typing.Optional[websockets.WebSocketClientProtocol] = None
        #: Gateway protocol version. Starts as the requested version, updated once ready with the actual version being
        #: used.
        self.version = self._REQUESTED_VERSION

    @property
    def is_shard(self) -> bool:
        """True if this is considered a shard, false otherwise."""
        return self.shard_id is not None and self.shard_count is not None

    async def _trigger_resume(self, code: int, reason: str) -> "typing.NoReturn":
        """Trigger a `RESUME` operation. This will raise a :class:`ResumableConnectionClosed` exception."""
        await self.ws.close(code=code, reason=reason)
        raise ResumeConnection(code=code, reason=reason)

    async def _trigger_reidentify(self, code: int, reason: str) -> "typing.NoReturn":
        """Trigger a re-`IDENTIFY` operation. This will raise a :class:`GatewayRequestedReconnection` exception."""
        await self.ws.close(code=code, reason=reason)
        raise RestartConnection(code=code, reason=reason)

    async def _send_json(self, payload) -> None:
        async with self._rate_limit:
            raw = json.dumps(payload)
            if len(raw) > self._MAX_PAYLOAD_SIZE:
                self._handle_payload_oversize(payload)
            else:
                await self.ws.send(raw)

    def _handle_payload_oversize(self, payload) -> None:
        self._logger.error(
            "refusing to send payload as it is too large. Sending this would result in "
            "a disconnect. Payload was: %s",
            payload,
        )

    async def _recv_json(self) -> GatewayPayload:
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

        payload = json.loads(msg)

        if not isinstance(payload, dict):
            return await self._trigger_reidentify(code=ClientExit.TYPE_ERROR, reason="Expected JSON object.")

        return payload

    async def _keep_alive(self) -> None:
        while not self.closed_event.is_set():
            try:
                if self._last_heartbeat_sent + self._heartbeat_interval < time.perf_counter():
                    last_sent = time.perf_counter() - self._last_heartbeat_sent
                    msg = f"Failed to receive an acknowledgement from the previous heartbeat sent ~{last_sent}s ago"
                    return await self._trigger_resume(code=ClientExit.PROTOCOL_VIOLATION, reason=msg)

                await asyncio.wait_for(self.closed_event.wait(), timeout=self._heartbeat_interval)
            except asyncio.TimeoutError:
                start = time.perf_counter()
                await self._send_heartbeat()
                time_taken = time.perf_counter() - start

                if time_taken > 0.15 * self.heartbeat_latency:
                    self._handle_slow_client(time_taken)

            else:
                await self.ws.close(code=ClientExit.GOING_AWAY, reason="User requested shutdown")

    def _handle_slow_client(self, time_taken) -> None:
        self._logger.warning(
            "took %sms to send HEARTBEAT, which is more than 15%% of the heartbeat interval. "
            "Your connection may be poor or the event loop may be blocked or under excessive load",
            time_taken * 1_000,
        )

    async def _send_heartbeat(self) -> None:
        await self._send_json({"op": Opcode.HEARTBEAT, "d": self._seq})
        self._logger.debug("sent HEARTBEAT")
        self._last_heartbeat_sent = time.perf_counter()

    async def _send_ack(self) -> None:
        await self._send_json({"op": Opcode.HEARTBEAT_ACK})
        self._logger.debug("sent HEARTBEAT_ACK")

    async def _handle_ack(self) -> None:
        self._last_ack_received = time.perf_counter()
        self.heartbeat_latency = self._last_ack_received - self._last_heartbeat_sent
        self._logger.debug("received HEARTBEAT_ACK after %sms", round(self.heartbeat_latency * 1000))

    async def _recv_hello(self) -> None:
        hello = await self._recv_json()
        op = hello["op"]
        if op != Opcode.HELLO:
            return await self._trigger_resume(code=ClientExit.PROTOCOL_VIOLATION, reason=f"Expected HELLO but got {op}")

        d = hello["d"]
        self.trace = d["_trace"]
        self._heartbeat_interval = d["heartbeat_interval"] / 1_000.0
        self._logger.info("received HELLO. heartbeat interval is %ss", self._heartbeat_interval)

    async def _send_resume(self) -> None:
        payload = {"op": Opcode.RESUME, "d": {"token": self.token, "session_id": self._session_id, "seq": self._seq}}
        await self._send_json(payload)
        self._logger.info("sent RESUME")

    async def _send_identify(self) -> None:
        payload = {
            "op": Opcode.IDENTIFY,
            "d": {
                "token": self.token,
                "compress": False,
                "large_threshold": self.large_threshold,
                "properties": {
                    "$os": "os" if self.incognito else platform.system(),
                    "$browser": "browser" if self.incognito else library_version(),
                    "$device": "device" if self.incognito else python_version(),
                },
            },
        }

        if self._initial_presence is not None:
            payload["d"]["status"] = self._initial_presence

        if self.is_shard:
            # noinspection PyTypeChecker
            payload["d"]["shard"] = [self.shard_id, self.shard_count]

        self._logger.info("sent IDENTIFY")
        await self._send_json(payload)

    async def _handle_dispatch(self, event: str, payload: GatewayPayload) -> None:
        event == "READY" and await self._handle_ready(payload)
        event == "RESUMED" and await self._handle_resumed(payload)
        self._logger.debug("DISPATCH %s", event)
        await self.dispatch(event, payload)

    async def _handle_ready(self, ready: GatewayPayload) -> None:
        self.trace = ready["_trace"]
        self._session_id = ready["session_id"]
        self.version = ready["v"]
        self._logger.info(
            "Now READY. Gateway v%s, user is %s#%s (%s)",
            self.version,
            ready["user"]["username"],
            ready["user"]["discriminator"],
            ready["user"]["id"],
        )

    async def _handle_resumed(self, resumed: GatewayPayload) -> None:
        self.trace = resumed["_trace"]
        self._logger.info("RESUMED successfully")

    async def _process_events(self) -> None:
        """Polls the gateway for new packets and handles dispatching the results."""
        while not self.closed_event.is_set():
            await self._process_one_event()

    async def _process_one_event(self) -> None:
        """Processes a single event."""
        message = await self._recv_json()
        op = message["op"]
        d = message["d"]
        seq = message.get("s", None)
        t = message.get("t", None)

        with contextlib.suppress(ValueError):
            op = Opcode(op)

        if seq is not None:
            self._seq = seq
        if op == Opcode.DISPATCH:
            await self._handle_dispatch(t, d)
        elif op == Opcode.HEARTBEAT:
            await self._send_ack()
        elif op == Opcode.HEARTBEAT_ACK:
            await self._handle_ack()
        elif op == Opcode.RECONNECT:
            self._logger.warning("instructed to disconnect and %s with gateway", op.name)
            await self._trigger_reidentify(code=ClientExit.NORMAL_CLOSURE, reason="you requested me to reconnect")
        elif op == Opcode.INVALID_SESSION:
            if d is True:
                self._logger.warning("%s (id: %s), will try to disconnect and RESUME", op.name, self._session_id)
                await self._trigger_resume(code=ClientExit.NORMAL_CLOSURE, reason="invalid session id so will resume")
            else:
                self._logger.warning("%s (id: %s), will try to re-IDENTIFY", op.name, self._session_id)
                await self._trigger_reidentify(
                    code=ClientExit.NORMAL_CLOSURE, reason="invalid session id so will close"
                )
        else:
            self._logger.warning("received unrecognised opcode %s", op)
            return

    async def request_guild_members(self, guild_id: int, query: str = "", limit: int = 0) -> None:
        """
        Requests guild members from the given Guild ID. This can be used to retrieve all members available in a guild.

        Args:
            guild_id: the guild ID to request members from.
            query: member names to search for, or empty string to remove the constraint.
            limit: max number of members to retrieve, or zero to remove the constraint.

        Warning:
            Results will be dispatched as events in chunks of 1000 members per guild.
        """
        self._logger.debug("requesting members in guild %s", guild_id)
        await self._send_json(
            {"op": Opcode.REQUEST_GUILD_MEMBERS, "d": {"guild_id": str(guild_id), "query": query, "limit": limit}}
        )

    async def update_status(
        self, idle_since: typing.Optional[int], game: typing.Optional[GatewayPayload], status: str, afk: bool
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
        self._logger.debug("updating status idle=%s, game=%s, status=%s, afk=%s", idle_since, game, status, afk)
        await self._send_json(
            {"op": Opcode.STATUS_UPDATE, "d": {"idle": idle_since, "game": game, "status": status, "afk": afk}}
        )

    async def update_voice_state(
        self, guild_id: int, channel_id: typing.Optional[int], self_mute: bool, self_deaf: bool
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
            "updating voice state guild %s, channel %s, mute: %s, deaf: %s", guild_id, channel_id, self_mute, self_deaf
        )
        await self._send_json(
            {
                "op": Opcode.VOICE_STATE_UPDATE,
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
        kwargs = {"loop": self.loop, "uri": self.uri, "compression": None}

        while not self.closed_event.is_set():
            await self.run_once(**kwargs)

    async def run_once(self, **kwargs) -> None:
        """Run the gateway once, then finish regardless of the closure reason."""
        try:
            async with websockets.connect(**kwargs) as self.ws:
                try:
                    await self._recv_hello()
                    is_resume = self._seq is not None and self._session_id is not None
                    await (self._send_resume() if is_resume else self._send_identify())
                    await asyncio.gather(self._keep_alive(), self._process_events())
                except (RestartConnection, ResumeConnection) as ex:
                    reason, code = ex.reason or "no reason", ServerExit(ex.code)
                    if ex.code in self._NEVER_RECONNECT_CODES:
                        self._logger.critical("disconnected after %s [%s]. Please rectify issue manually", reason, code)
                        raise RuntimeError("could not reconnect manually") from ex
                    else:
                        self._logger.warning("reconnecting after %s [%s]", reason, code)
                        if isinstance(ex, RestartConnection):
                            self._seq, self._session_id, self.trace = None, None, []
                        await asyncio.sleep(2)
        finally:
            self._logger.info("gateway client shutting down")

    async def close(self, block=True) -> None:
        """
        Request that the gateway gracefully shuts down. Once this has occurred, you should not reuse this object. Doing
        so will result in undefined behaviour.

        Args:
            block: await the closure of the websocket connection. Defaults to `True`. If `False`, then nothing is
                waited for.
        """
        self.closed_event.set()
        block and await self.ws.wait_closed()
