#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import json
import logging
import time
import weakref

import async_timeout
import websockets

from hikari.utils import backoff

_LOGGER = logging.getLogger(__name__)


class _Heartbeat:
    """A heartbeat implementation for the Gateway implementation in this file."""
    #: If a ping task takes longer than this to perform, we have potentially got
    #: issues with something being a blocking task, or the event loop is overloaded.
    DANGER_LATENCY = 4.0
    
    __slots__ = ['stop_flag', 'ws', '_last_ping', '_last_ack']

    def __init__(self, websocket: Gateway) -> None:
        self.stop_flag = asyncio.Event(loop=websocket.loop)
        self.ws: Gateway = weakref.proxy(websocket)
        self._last_ping = float('nan')
        self._last_ack = float('nan')
        self.latency = float('nan')

    async def run(self):
        """Heartbeat timing logic."""
        _LOGGER.debug("Started heartbeat task for shard %s", self.ws.shard_id)

        while not self.stop_flag.is_set():
            try:
                ping = asyncio.create_task(self.ping_gateway())
                ping_start = time.perf_counter()
                await ping
                ping_time = time.perf_counter() - ping_start

                if ping_time >= self.DANGER_LATENCY:
                    _LOGGER.warning("Shard %s took %s to send a heartbeat. Your connection may be poor or the event "
                                    "loop may be blocking", self.ws.shard_id, ping_time)

                with async_timeout.timeout(self.ws.heartbeat_interval):
                    await self.stop_flag.wait()
            except asyncio.TimeoutError:
                pass
            except (asyncio.CancelledError, ReferenceError) as ex:
                if isinstance(ex, ReferenceError):
                    _LOGGER.warning("Gateway shut down but did not stop the heartbeat. Did it stop abnormally?")
                _LOGGER.debug("Closing heartbeat task")

    async def ping_gateway(self):
        """Ping the gateway with the given op-code."""
        _LOGGER.debug("Sending heartbeat to gateway for shard %s", self.ws.shard_id)
        await self.ws.send_json({'op': self.ws.HEARTBEAT_OP})
        self._last_ping = self.ws.loop.time()

    async def ack_gateway(self):
        _LOGGER.debug("Sending heartbeat ack to gateway for shard %s", self.ws.shard_id)
        await self.ws.send_json({'op': self.ws.HEARTBEAT_ACK_OP})
        self._last_ping = self.ws.loop.time()

    def handle_gateway_ack(self):
        """Register an acknowledgement from the gateway..."""
        self._last_ack = time.perf_counter()
        self.latency = self._last_ack - self._last_ping
        if self.latency >= self.DANGER_LATENCY:
            _LOGGER.warning("Gateway for shard %s took %s to acknowledge most recent heartbeat. Your connection may be "
                            "poor or Discord may be having serverside issues.", self.ws.shard_id, self.latency)
        _LOGGER.debug("Received heartbeat ack from gateway for shard %s in approx %ss", self.ws.shard_id, self.latency)


class Gateway(websockets.WebSocketClientProtocol):
    """
    Implementation of the gateway communication layer.
    """
    API_VERSION = 7
    PAYLOAD_TYPE = 'json'
    TRANSPORT_ENCODING = 'zlib-stream'
    ZLIB_SUFFIX = b'\x00\x00\xff\xff'

    # Opcodes
    # =======

    DISPATCH_OP = 0
    HEARTBEAT_OP = 1
    IDENTIFY_OP = 2
    STATUS_UPDATE_OP = 3
    VOICE_STATE_UPDATE_OP = 4
    VOICE_PING_OP = 5
    RESUME_OP = 6
    RECONNECT_OP = 7
    REQUEST_GUILD_MEMBERS_OP = 8
    INVALID_SESSION_OP = 9
    HELLO_OP = 10
    HEARTBEAT_ACK_OP = 11
    GUILD_SYNC_OP = 12

    async def send_json(self, payload):
        """Decodes the given object to a JSON string and sends it to the gateway."""
        raw = json.dumps(payload)
        return await self.send(raw)

    @backoff.default_network_connectivity_backoff()
    async def send(self, payload):
        await super().send(payload)

    """
    STUBBED METHODS AND FIELDS
    """
    heartbeat_interval: float
    max_heartbeat_timeout: float
    shard_id: int

