#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import collections
import inspect
import json
import logging
import socket
import zlib

import websockets.server


def _on(opcode):
    def decorator(fn):
        setattr(fn, "opcode", opcode)
        return fn

    return decorator


class MockGatewayServerV7:
    DISPATCH_OP = 0
    HEARTBEAT_OP = 1
    IDENTIFY_OP = 2
    STATUS_UPDATE_OP = 3
    VOICE_STATE_UPDATE_OP = 4
    VOICE_PING = 5
    RESUME_OP = 6
    RECONNECT_OP = 7
    REQUEST_GUILD_MEMBERS_OP = 8
    INVALID_SESSION_OP = 9
    HELLO_OP = 10
    HEARTBEAT_ACK_OP = 11
    GUILD_SYNC_OP = 12

    UNKNOWN_ERROR = 4000, "unknown error"
    UNKNOWN_OPCODE = 4001, "unknown opcode"
    DECODE_ERROR = 4002, "decode error"
    NOT_AUTHENTICATED = 4003, "not authenticated"
    AUTHENTICATION_FAILED = 4004, "authentication failed"
    ALREADY_AUTHENTICATED = 4005, "already authenticated"
    INVALID_SEQ = 4007, "invalid seq"
    RATE_LIMITED = 4008, "rate limited"
    SESSION_TIMEOUT = 4009, "session timeout"
    INVALID_SHARD = 4010, "invalid shard"
    SHARDING_REQUIRED = 4011, "sharding required"

    LOGGER = logging.getLogger("MockGatewayServerV7")

    server: websockets.server.WebSocketServer
    task: asyncio.Task
    ready: asyncio.Event

    def __init__(self, loop, valid_token):
        self.protocol = None
        self.connection_made = asyncio.Event()
        self.ready = asyncio.Event()
        self.closures = []
        self.loop = loop
        self.seq = 0
        self.valid_token = valid_token
        self.heartbeat_interval = 4_000
        self.trace = [socket.gethostname()]

        # Store the payloads we receive, maps opcode to bodies.
        self.received = collections.defaultdict(list)
        # List of tuples of futures and predicates.
        self.waiters = []

    async def start(self, host, port):
        self.task = self.loop.create_task(self.run(host, port))

        await self.ready.wait()

    async def run(self, host, port):

        async with websockets.serve(
            self.handler, host, port, loop=self.loop
        ) as self.server:
            try:
                self.ready.set()
                await self.server.closed_waiter
            except Exception as ex:
                self.LOGGER.critical("%s %s", type(ex).__name__, ex)
                self.closures.append(ex)
            finally:
                self.ready.clear()
                self.protocol = None

    async def send_compressed_json(self, body):
        payload = json.dumps(body).encode("utf-8")
        payload = zlib.compress(payload) + b"\x00\x00\xff\xff"

        chunk_size = 16
        for i in range(0, len(payload), chunk_size):
            chunk = payload[i : i + chunk_size]
            self.LOGGER.info("Sending chunk %s", chunk)
            await self.protocol.send(chunk)

    async def send_json(self, body):
        payload = json.dumps(body)
        await self.protocol.send(payload)

    async def receive_json(self):
        payload = await self.protocol.recv()
        data = json.loads(payload)
        self.received[data["op"]].append(data)
        self._dispatch_internal_event(data)
        return data

    def _dispatch_internal_event(self, payload):
        for waiter in [*self.waiters]:
            future, pred = waiter
            if pred(payload):
                future.set_result(payload)
                self.waiters.remove(waiter)

    def make_payload(self, opcode, data, seq=None, event=None):
        if opcode == self.DISPATCH_OP:
            return dict(op=opcode, d=data, s=seq, t=event)
        else:
            return dict(op=opcode, d=data)

    async def handler(
        self, protocol: websockets.server.WebSocketServerProtocol, path: str
    ):
        await asyncio.sleep(0.5)

        if self.protocol is not None:
            raise RuntimeError("More than one connection attempted!!!!!!")

        self.LOGGER.info(
            "Received connection to %s:%s at %s", protocol.host, protocol.port, path
        )
        self.protocol = protocol

        self.connection_made.set()
        await asyncio.sleep(0)

        while not self.protocol.closed:
            data = await self.receive_json()
            op = data["op"]
            seq = data.get("s")

            if seq is not None:
                self.seq = seq + 1

            for name, member in inspect.getmembers(
                self, lambda m: getattr(m, "opcode", None) == op
            ):
                self.LOGGER.info("Dispatching %s", name)
                await member(data)

    async def wait_for(self, condition):
        future = self.loop.create_future()
        self.waiters.append((future, condition))
        return await future

    async def send_hello(self):
        pl = self.make_payload(
            self.HELLO_OP,
            {"heartbeat_interval": self.heartbeat_interval, "_trace": self.trace},
        )
        await self.send_json(pl)

    async def send_invalid_session(self, can_resume=False):
        pl = self.make_payload(self.INVALID_SESSION_OP, can_resume)
        await self.send_json(pl)

    async def send_reconnect(self):
        pl = self.make_payload(self.RECONNECT_OP, None)
        await self.send_json(pl)

    async def send_heartbeat(self):
        pl = self.make_payload(self.HEARTBEAT_OP, self.seq)
        await self.send_json(pl)

    async def send_heartbeat_ack(self):
        pl = self.make_payload(self.HEARTBEAT_ACK_OP, None)
        await self.send_json(pl)

    async def send_dispatch(self, event_name, body):
        pl = self.make_payload(self.DISPATCH_OP, event=event_name, data=body)
        await self.send_json(pl)

    async def stop(self):
        self.server.close()
        await self.task

    @_on(HEARTBEAT_OP)
    async def receive_heartbeat(self, _):
        self.LOGGER.info("Received heartbeat, sending heartbeat ACK")
        await self.send_heartbeat_ack()

    @_on(HEARTBEAT_ACK_OP)
    async def receive_heartbeat_ack(self, _):
        self.LOGGER.info("Received heartbeat ack, sending heartbeat ACK")

    @_on(IDENTIFY_OP)
    async def receive_identify(self, payload):
        self.LOGGER.info("Received identify of %s", payload)
        d = payload["d"]
        if d["token"] != self.valid_token:
            await self.protocol.close(*self.AUTHENTICATION_FAILED)

    @_on(STATUS_UPDATE_OP)
    async def receive_status_update(self, payload):
        self.LOGGER.info("Received status update of %s", payload)

    @_on(RESUME_OP)
    async def receive_resume(self, payload):
        self.LOGGER.info("Received resume of %s", payload)

    @_on(REQUEST_GUILD_MEMBERS_OP)
    async def receive_request_guild_members(self, payload):
        self.LOGGER.info("Received request of guild members for %s", payload)
