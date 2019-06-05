#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Opcodes and constants used within the networking components of Hikari.
"""
import enum


class GatewayOpcode(enum.IntEnum):
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


class GatewayClientExit(enum.IntEnum):
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


class GatewayServerExit(enum.IntEnum):
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
