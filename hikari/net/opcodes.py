#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Opcodes and constants used within the networking components of Hikari.

References:
    https://discordapp.com/developers/docs/topics/opcodes-and-status-codes
"""
__all__ = ("GatewayOpcode", "GatewayClosure", "HTTPStatus", "JSONErrorCode", "VoiceOpcode", "VoiceClosure")

import enum


class GatewayOpcode(enum.IntEnum):
    """
    Gateway opcodes.
    """

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


class VoiceOpcode(enum.Enum):
    """
    Voice server opcodes.
    """

    #: Begin a voice websocket connection.
    IDENTIFY = 0

    #: Select the voice protocol.
    SELECT_PROTOCOL = 1

    #: Complete the websocket handshake.
    READY = 2

    #: Keeps the websocket connection alive.
    HEARTBEAT = 3

    #: Describe the session.
    SESSION_DESCRIPTION = 4

    #: Indicate which users are speaking.
    SPEAKING = 5

    #: Acknowledge a heartbeat opcode.
    HEARTBEAT_ACK = 6

    #: Resume a connection
    RESUME = 7

    #: Contains the continuous interval in milliseconds after which the client should send a heartbeat
    HELLO = 8

    #: Acknowledge a resume occurred.
    RESUMED = 9

    #: A client has disconnected from the voice channel.
    CLIENT_DISCONNECT = 13


class GatewayClosure(enum.IntEnum):
    """
    Reasons for closing a connection.

    Note:
        Flags in the range [1000,2000) are flags that we can send to Discord.
        Flags in the range [4000,5000) are flags that Discord can send to us.
    """

    #: We are shutting down normally, we might come back up soon.
    NORMAL_CLOSURE = 1_000

    #: We are shutting down for the foreseeable future (our process is stopping).
    GOING_AWAY = 1_001

    #: We expected a specific payload or opcode but Discord failed to provide it to us.
    PROTOCOL_VIOLATION = 1_002

    #: We expected a specific type of object but Discord failed to provide the correct type to us.
    TYPE_ERROR = 1_003

    #: Something has failed internally in the Hikari Gateway code.
    INTERNAL_ERROR = 1_011

    #: We're not sure what went wrong. Try reconnecting?
    UNKNOWN_ERROR = 4_000

    #: You sent an invalid Gateway opcode or an invalid payload for an opcode. Don't do that!
    UNKNOWN_OPCODE = 4_001

    #: You sent an invalid payload to us. Don't do that!
    DECODE_ERROR = 4_002

    #: You sent us a payload prior to identifying.
    NOT_AUTHENTICATED = 4_003

    #: The account token sent with your identify payload is incorrect.
    AUTHENTICATION_FAILED = 4_004

    #: You sent more than one identify payload. Don't do that!
    ALREADY_AUTHENTICATED = 4_005

    #: The sequence sent when resuming the session was invalid. Reconnect and start a new session.
    INVALID_SEQ = 4_007

    #: Woah nelly! You're sending payloads to us too quickly. Slow it down!
    RATE_LIMITED = 4_008

    #: Your session timed out. Reconnect and start a new one.
    SESSION_TIMEOUT = 4_009

    #: You sent us an invalid shard when identifying.
    INVALID_SHARD = 4_010

    #: The session would have handled too many guilds - you are required to shard your connection in order to connect.
    SHARDING_REQUIRED = 4_011


class VoiceClosure(enum.IntEnum):
    """
    Reasons for closing a voice connection.

    Note:
        Flags in the range [1000,2000) are flags that we can send to Discord.
        Flags in the range [4000,5000) are flags that Discord can send to us.
    """

    #: We are shutting down normally, we might come back up soon.
    NORMAL_CLOSURE = 1_000

    #: We are shutting down for the foreseeable future (our process is stopping).
    GOING_AWAY = 1_001

    #: We expected a specific payload or opcode but Discord failed to provide it to us.
    PROTOCOL_VIOLATION = 1_002

    #: We expected a specific type of object but Discord failed to provide the correct type to us.
    TYPE_ERROR = 1_003

    #: Something has failed internally in the Hikari voice connection code.
    INTERNAL_ERROR = 1_011

    #: You sent an invalid opcode
    UNKNOWN_OPCODE = 4_001

    #: You sent a payload before identifying with the Gateway.
    NOT_AUTHENTICATED = 4_003

    #: Authentication failed
    AUTHENTICATION_FAILED = 4_004

    #: You sent more than one identify payload. Stahp.
    ALREADY_AUTHENTICATED = 4_005

    #: Your session is no longer valid.
    SESSION_NO_LONGER_VALID = 4_006

    #: Your session has timed out.
    SESSION_TIMEOUT = 4_009

    #: We can't find the server you're trying to connect to.
    SERVER_NOT_FOUND = 4_011

    #: We didn't recognize the protocol you sent.
    UNKNOWN_PROTOCOL = 4_012

    #: Oh no! You've been disconnected! Try resuming.
    DISCONNECTED = 4_014

    #: The server crashed. Our bad! Try resuming.
    VOICE_SERVER_CRASHED = 4_015

    #: We didn't recognize your encryption.
    UNKNOWN_ENCRYPTION_MODE = 4_016


class JSONErrorCode(enum.IntEnum):
    """
    Error codes that can be returned by the REST API.
    """

    #: Unknown account
    UNKNOWN_ACCOUNT = 10_001

    #: Unknown application
    UNKNOWN_APPLICATION = 10_002

    #: Unknown channel
    UNKNOWN_CHANNEL = 10_003

    #: Unknown guild
    UNKNOWN_GUILD = 10_004

    #: Unknown integration
    UNKNOWN_INTEGRATION = 10_005

    #: Unknown invite
    UNKNOWN_INVITE = 10_006

    #: Unknown member
    UNKNOWN_MEMBER = 10_007

    #: Unknown message
    UNKNOWN_MESSAGE = 10_008

    #: Unknown overwrite
    UNKNOWN_OVERWRITE = 10_009

    #: Unknown provider
    UNKNOWN_PROVIDER = 10_010

    #: Unknown role
    UNKNOWN_ROLE = 10_011

    #: Unknown token
    UNKNOWN_TOKEN = 10_012

    #: Unknown user
    UNKNOWN_USER = 10_013

    #: Unknown Emoji
    UNKNOWN_EMOJI = 10_014

    #: Unknown Webhook
    UNKNOWN_WEBHOOK = 10_015

    #: Maximum number of pins reached (50)
    MAX_PINS_REACHED = 30_003

    #: Maximum number of guild roles reached (250)
    MAX_GUILD_ROLES_REACHED = 30_005

    #: Maximum number of reactions reached (20)
    MAX_REACTIONS_REACHED = 30_010

    #: Maximum number of guild channels reached (500)
    MAX_GUILD_CHANNELS_REACHED = 30_013

    #: Unauthorized
    UNAUTHORIZED = 40_001

    #: Missing access
    MISSING_ACCESS = 50_001

    #: Invalid account type
    INVALID_ACCOUNT_TYPE = 50_002

    #: Cannot execute action on a DM channel
    CANNOT_EXECUTE_ACTION_ON_DM_CHANNEL = 50_003

    #: Widget Disabled
    WIDGET_DISABLED = 50_004

    #: Cannot edit a message authored by another user
    CANNOT_EDIT_A_MESSAGE_AUTHORED_BY_ANOTHER_USER = 50_005

    #: Cannot send an empty message
    CANNOT_SEND_AN_EMPTY_MESSAGE = 50_006

    #: Cannot send messages to this user
    CANNOT_SEND_MESSAGES_TO_THIS_USER = 50_007

    #: Cannot send messages in a voice channel
    CANNOT_SEND_MESSAGES_IN_VOICE_CHANNEL = 50_008

    #: Channel verification level is too high
    CHANNEL_VERIFICATION_TOO_HIGH = 50_009

    #: OAuth2 application does not have a bot
    OAUTH2_APPLICATION_DOES_NOT_HAVE_A_BOT = 50_010

    #: OAuth2 application limit reached
    OAUTH2_APPLICATION_LIMIT_REACHED = 50_011

    #: Invalid OAuth state
    INVALID_OAUTH2_STATE = 50_012

    #: Missing permissions
    MISSING_PERMISSIONS = 50_013

    #: Invalid authentication token
    INVALID_AUTHENTICATION_TOKEN = 50_014

    #: Note is too long
    NOTE_IS_TOO_LONG = 50_015

    #: Provided too few or too many messages to delete. Must provide at least 2 and fewer than 100 messages to delete.
    INVALID_NUMBER_OF_MESSAGES_TO_DELETE = 50_016

    #: A message can only be pinned to the channel it was sent in
    CANNOT_PIN_A_MESSAGE_IN_A_DIFFERENT_CHANNEL = 50_019

    #: Invite code is either invalid or taken.
    INVALID_INVITE = 50_020

    #: Cannot execute action on a system message
    CANNOT_EXECUTE_ACTION_ON_SYSTEM_MESSAGE = 50_021

    #: Invalid OAuth2 access token
    INVALID_OAUTH2_TOKEN = 50_025

    #: A message provided was too old to bulk delete
    MESSAGE_PROVIDED_WAS_TOO_OLD_TO_BULK_DELETE = 50_034

    #: Invalid Form Body
    INVALID_FORM_BODY = 50_035

    #: An invite was accepted to a guild the application's bot is not in
    ACCEPTED_INVITE_TO_GUILD_BOT_IS_NOT_IN = 50_036

    #: Invalid API version
    INVALID_API_VERSION = 50_041

    #: Reaction blocked
    REACTION_BLOCKED = 90_001

    #: Bots cannot use this endpoint
    #:
    #: Note:
    #:     You should never expect to receive this in normal API usage.
    USERS_ONLY = 20_001

    #: Only bots can use this endpoint.
    #:
    #: Note:
    #:     You should never expect to receive this in normal API usage.
    BOTS_ONLY = 20_002

    #: Maximum number of guilds reached (100)
    #:
    #: Note:
    #:     You should never expect to receive this in normal API usage as this only applies to user accounts.
    #:     This is unlimited for bot accounts.
    MAX_GUILDS_REACHED = 30_001

    #: Maximum number of friends reached (1000)
    #:
    #: Note:
    #:     You should never expect to receive this in normal API usage as this only applies to user accounts.
    #:     Bots cannot have friends.
    MAX_FRIENDS_REACHED = 30_002


class HTTPStatus(enum.IntEnum):
    """
    HTTP status codes.
    """

    #: The request completed successfully
    OK = 200

    #: The entity was created successfully
    CREATED = 201

    #: The request completed successfully but returned no content
    NO_CONTENT = 204

    #: The entity was not modified (no action was taken)
    NOT_MODIFIED = 304

    #: The request was improperly formatted, or the server couldn't understand it
    BAD_REQUEST = 400

    #: The Authorization header was missing or invalid
    UNAUTHORIZED = 401

    #: The Authorization token you passed did not have permission to the resource
    FORBIDDEN = 403

    #: The resource at the location specified doesn't exist
    NOT_FOUND = 404

    #: The HTTP method used is not valid for the location specified
    #:
    #: Note:
    #:     You should never expect to receive this in normal API usage. Receiving this indicates that either the
    #:     HTTP API has changed, or that Hikari is not implementing a call correctly (if so, please file an
    #:     issue on the `issue tracker <https://gitlab.com/nekokatt/hikari/issues>`_ so that it can be amended).
    METHOD_NOT_ALLOWED = 405

    #: Note:
    #:     You can expect this response code to be handled internally silently usually.
    TOO_MANY_REQUESTS = 429

    #: Something went wrong internally on Discord's side.
    #:
    #: Note:
    #:     Discord does not explicitly specify that this can be raised in normal behaviour for the V7 API, however
    #:     it is handled regardless as a standard response that is possible from an HTTP API.
    INTERNAL_SERVER_ERROR = 500

    #: You are trying to use something that is not yet implemented.
    #:
    #: Note:
    #:     Discord does not explicitly specify that this can be raised in normal behaviour for the V7 API, however
    #:     it is handled regardless as a standard response that is possible from an HTTP API.
    NOT_IMPLEMENTED = 501

    #: There was not a gateway available to process your request. Wait a bit and retry
    #:
    #: Note:
    #:     This does not refer to the same type of "gateway" as the websocket Gateway, despite the same name.
    GATEWAY_UNAVAILABLE = 502

    #: Discord is probably down.
    #:
    #: Note:
    #:     Discord does not explicitly specify that this can be raised in normal behaviour for the V7 API, however
    #:     it is handled regardless as a standard response that is possible from an HTTP API.
    SERVICE_UNAVAILABLE = 503

    #:
    #: Note:
    #:     This does not refer to the same type of "gateway" as the websocket Gateway, despite the same name.
    #:
    #:     Discord does not explicitly specify that this can be raised in normal behaviour for the V7 API, however
    #:     it is handled regardless as a standard response that is possible from an HTTP API.
    GATEWAY_TIMEOUT = 504
