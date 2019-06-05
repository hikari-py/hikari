#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Opcodes and constants used within the networking components of Hikari.

References:
    https://discordapp.com/developers/docs/topics/opcodes-and-status-codes
"""
import dataclasses
import enum


@dataclasses.dataclass(frozen=True, order=False)
class IntMember:
    """An int-enum member with a description attribute. For all other purposes it will mimic an int."""

    __slots__ = ("value", "description")

    value: int
    description: str

    def __str__(self) -> str:
        return self.description

    def __repr__(self) -> str:
        return f"{self.value} ({self.description})"

    def __int__(self) -> int:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other) -> bool:
        return int(self) == int(other)

    def __ne__(self, other) -> bool:
        return not (self == other)

    def __lt__(self, other) -> bool:
        return int(self) < int(other)

    def __le__(self, other) -> bool:
        return self < other or self == other

    def __gt__(self, other) -> bool:
        return not (self <= other)

    def __ge__(self, other) -> bool:
        return self > other or self == other


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
    NORMAL_CLOSURE = IntMember(1_000, "Nothing went wrong")
    #: The client is shutting down and will not immediately come back up.
    GOING_AWAY = IntMember(1_001, "Going away")
    #: The gateway did something we didn't expect it to do.
    PROTOCOL_VIOLATION = IntMember(1_002, "The gateway did something unexpected")
    #: The gateway sent something we didn't expect to receive.
    TYPE_ERROR = IntMember(1_003, "The gateway sent something unexpected")
    #: Logic has failed internally.
    INTERNAL_ERROR = IntMember(1_011, "Something went wrong in Hikari")


class GatewayServerExit(enum.IntEnum):
    """
    Reasons for closing a connection that the gateway can send us.

    Refer to https://discordapp.com/developers/docs/topics/opcodes-and-status-codes for an up-to-date description.

    """

    UNKNOWN_ERROR = IntMember(4_000, "We're not sure what went wrong. Try reconnecting?")
    UNKNOWN_OPCODE = IntMember(4_001, "You sent an invalid Gateway opcode or an invalid payload for an opcode")
    DECODE_ERROR = IntMember(4_002, "You sent an invalid payload to Discord")
    NOT_AUTHENTICATED = IntMember(4_003, "You did not authenticate properly")
    AUTHENTICATION_FAILED = IntMember(4_004, "Your authentication details failed to work")
    ALREADY_AUTHENTICATED = IntMember(4_005, "You tried to authenticate more than once")
    INVALID_SEQ = IntMember(4_007, "You failed to keep up with Discord, or something went out of sync")
    RATE_LIMITED = IntMember(4_008, "You are being rate limited")
    SESSION_TIMEOUT = IntMember(4_009, "Your session timed out")
    INVALID_SHARD = IntMember(4_010, "Your shard details were invalid")
    SHARDING_REQUIRED = IntMember(4_011, "You need to use sharding")


class JSONErrorCode(enum.IntEnum):
    """
    Error codes that can be returned by the REST API.

    Some specific errors such as those specifically for user accounts have been omitted, this is not
    a self-botting API.
    """

    UNKNOWN_ACCOUNT = 10_001
    UNKNOWN_APPLICATION = 10_002
    UNKNOWN_CHANNEL = 10_003
    UNKNOWN_GUILD = 10_004
    UNKNOWN_INTEGRATION = 10_005
    UNKNOWN_INVITE = 10_006
    UNKNOWN_MEMBER = 10_007
    UNKNOWN_MESSAGE = 10_008
    UNKNOWN_OVERWRITE = 10_009
    UNKNOWN_PROVIDER = 10_010
    UNKNOWN_ROLE = 10_011
    UNKNOWN_TOKEN = 10_012
    UNKNOWN_USER = 10_013
    UNKNOWN_EMOJI = 10_014
    UNKNOWN_WEBHOOK = 10_015

    MAX_PINS_REACHED = 30_003
    MAX_ROLES_REACHED = 30_005
    MAX_REACTIONS_REACHED = 30_010
    MAX_GUILD_CHANNELS_REACHED = 30_013

    UNAUTHORIZED = 40_001

    MISSING_ACCESS = 50_001
    INVALID_ACCOUNT_TYPE = 50_002
    CANNOT_EXECUTE_ACTION_ON_DM_CHANNEL = 50_003
    WIDGET_DISABLED = 50_004
    CANNOT_EDIT_MESSAGE_BY_ANOTHER_USER = 50_005
    CANNOT_SEND_EMPTY_MESSAGE = 50_006
    CANNOT_SEND_MESSAGES_TO_THIS_USER = 50_007
    CANNOT_SEND_MESSAGES_IN_VOICE_CHANNEL = 50_008
    CHANNEL_VERIFICATION_TOO_HIGH = 50_009
    OAUTH2_APPLICATION_IS_NOT_A_BOT = 50_010
    OAUTH2_APPLICATION_LIMIT_REACHED = 50_011
    INVALID_OAUTH2_STATE = 50_012
    MISSING_PERMISSIONS = 50_013
    INVALID_ACCESS_TOKEN = 50_014
    NOTE_IS_TOO_LONG = 50_015
    INVALID_NUMBER_OF_MESSAGES_TO_DELETE = 50_016
    CANNOT_PIN_A_MESSAGE_IN_A_DIFFERENT_CHANNEL = 50_019
    INVALID_INVITE = 50_020
    CANNOT_EXECUTE_ACTION_ON_SYSTEM_MESSAGE = 50_021
    INVALID_OAUTH2_TOKEN = 50_025
    MESSAGE_PROVIDED_WAS_TOO_OLD_TO_BULK_DELETE = 50_034
    INVALID_FORM_BODY = 50_035
    ACCEPTED_INVITE_TO_GUILD_BOT_IS_NOT_IN = 50_036
    INVALID_API_VERSION = 50_041
    REACTION_BLOCKED = 90_001
