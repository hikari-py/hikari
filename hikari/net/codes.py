#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""Enumerations for opcodes and status codes."""
__all__ = ["HTTPStatusCode", "GatewayCloseCode", "GatewayOpcode", "JSONErrorCode", "GatewayIntent"]

import enum


# Doesnt work correctly with enums, so since this file is all enums, ignore
# pylint: disable=no-member
class HTTPStatusCode(enum.IntEnum):
    """HTTP status codes that a conforming HTTP server should give us on Discord."""

    CONTINUE = 100

    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204

    MOVED_PERMANENTLY = 301

    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    PROXY_AUTHENTICATION_REQUIRED = 407
    REQUEST_ENTITY_TOO_LARGE = 413
    REQUEST_URI_TOO_LONG = 414
    UNSUPPORTED_MEDIA_TYPE = 415
    IM_A_TEAPOT = 418
    TOO_MANY_REQUESTS = 429

    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
    HTTP_VERSION_NOT_SUPPORTED = 505

    def __str__(self) -> str:
        name = self.name.replace("_", " ").title() if self is not HTTPStatusCode.IM_A_TEAPOT else "I'm a teapot"
        return f"{self.value} {name}"


class GatewayCloseCode(enum.IntEnum):
    """Reasons for closing a gateway connection.

    Notes
    -----
    Any codes greater than or equal to `4000` are server-side codes. Any codes
    between `1000` and `1999` inclusive are generally client-side codes.
    """

    #: You closed your bot manually.
    NORMAL_CLOSURE = 1000
    #: Your bot stopped working and shut down.
    ABNORMAL_CLOSURE = 1006
    #: Discord is not sure what went wrong. Try reconnecting?
    UNKNOWN_ERROR = 4000
    #: You sent an invalid Gateway opcode or an invalid payload for an opcode. Don't do that!
    UNKNOWN_OPCODE = 4001
    #: You sent an invalid payload to Discord. Don't do that!
    DECODE_ERROR = 4002
    #: You sent Discord a payload prior to identifying.
    NOT_AUTHENTICATED = 4003
    #: The account token sent with your identify payload is incorrect.
    AUTHENTICATION_FAILED = 4004
    #: You sent more than one identify payload. Don't do that!
    ALREADY_AUTHENTICATED = 4005
    #: The sequence sent when resuming the session was invalid. Reconnect and start a new session.
    INVALID_SEQ = 4007
    #: Woah nelly! You're sending payloads to Discord too quickly. Slow it down!
    RATE_LIMITED = 4008
    #: Your session timed out. Reconnect and start a new one.
    SESSION_TIMEOUT = 4009
    #: You sent Discord an invalid shard when identifying.
    INVALID_SHARD = 4010
    #: The session would have handled too many guilds - you are required to shard your connection in order to connect.
    SHARDING_REQUIRED = 4011
    #: You sent an invalid version for the gateway.
    INVALID_VERSION = 4012
    #: You sent an invalid intent for a Gateway Intent. You may have incorrectly calculated the bitwise value.
    INVALID_INTENT = 4013
    #: You sent a disallowed intent for a Gateway Intent. You may have tried to specify an intent that you
    #: have not enabled or are not whitelisted for.
    DISALLOWED_INTENT = 4014

    def __str__(self) -> str:
        name = self.name.replace("_", " ").title()
        return f"{self.value} {name}"


class GatewayOpcode(enum.IntEnum):
    """Opcodes that the gateway uses internally."""

    #: An event was dispatched.
    DISPATCH = 0

    #: Used for ping checking.
    HEARTBEAT = 1

    #: Used for client handshake.
    IDENTIFY = 2

    #: Used to update the client status.
    PRESENCE_UPDATE = 3

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

    def __str__(self) -> str:
        name = self.name.replace("_", " ").title()
        return f"{self.value} {name}"


class JSONErrorCode(enum.IntEnum):
    """Error codes that can be returned by the REST API."""

    #: This is sent if the payload is screwed up, etc.
    GENERAL_ERROR = 0

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

    #: Bots cannot use this endpoint
    #:
    #: Note
    #: ----
    #: You should never expect to receive this in normal API usage.
    USERS_ONLY = 20_001

    #: Only bots can use this endpoint.
    #:
    #: Note
    #: ----
    #: You should never expect to receive this in normal API usage.
    BOTS_ONLY = 20_002

    #: Maximum number of guilds reached (100)
    #:
    #: Note
    #: ----
    #: You should never expect to receive this in normal API usage as this only applies to user accounts.
    #: This is unlimited for bot accounts.
    MAX_GUILDS_REACHED = 30_001

    #: Maximum number of friends reached (1000)
    #:
    #: Note
    #: ----
    #: You should never expect to receive this in normal API usage as this only applies to user accounts.
    #: Bots cannot have friends :( .
    MAX_FRIENDS_REACHED = 30_002

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

    #: The resource is overloaded.
    RESOURCE_OVERLOADED = 130_000

    def __str__(self) -> str:
        name = self.name.replace("_", " ").title()
        return f"{self.value} {name}"


class GatewayIntent(enum.IntFlag):
    """Represents an intent on the gateway.

    This is a bitfield representation of all the categories of event
    that you wish to receive.

    Any events not in an intent category will be fired regardless of what intents you provide.

    Warnings
    --------
    If you are using the V7 Gateway, you will be REQUIRED to provide some form of intent value when
    you connect. Failure to do so may result in immediate termination of the session server-side.

    Notes
    -----
    Discord now places limits on certain events you can receive without whitelisting your bot first. On the
    ``Bot`` tab in the developer's portal for your bot, you should now have the option to enable functionality
    for receiving these events.

    If you attempt to request an intent type that you have not whitelisted your bot for, you will be
    disconnected on startup with a ``4014`` closure code.
    """

    #: Subscribes to the following events:
    #: * GUILD_CREATE
    #: * GUILD_DELETE
    #: * GUILD_ROLE_CREATE
    #: * GUILD_ROLE_UPDATE
    #: * GUILD_ROLE_DELETE
    #: * CHANNEL_CREATE
    #: * CHANNEL_UPDATE
    #: * CHANNEL_DELETE
    #: * CHANNEL_PINS_UPDATE
    GUILDS = 1 << 0

    #: Subscribes to the following events:
    #: * GUILD_MEMBER_ADD
    #: * GUILD_MEMBER_UPDATE
    #: * GUILD_MEMBER_REMOVE
    #:
    #: Warnings
    #: --------
    #: This intent is privileged, and requires enabling/whitelisting to use.
    GUILD_MEMBERS = 1 << 1

    #: Subscribes to the following events:
    #: * GUILD_BAN_ADD
    #: * GUILD_BAN_REMOVE
    GUILD_BANS = 1 << 2

    #: Subscribes to the following events:
    #: * GUILD_EMOJIS_UPDATE
    GUILD_EMOJIS = 1 << 3

    #: Subscribes to the following events:
    #: * GUILD_INTEGRATIONS_UPDATE
    GUILD_INTEGRATIONS = 1 << 4

    #: Subscribes to the following events:
    #: * WEBHOOKS_UPDATE
    GUILD_WEBHOOKS = 1 << 5

    #: Subscribes to the following events:
    #: * INVITE_CREATE
    #: * INVITE_DELETE
    GUILD_INVITES = 1 << 6

    #: Subscribes to the following events:
    #: * VOICE_STATE_UPDATE
    GUILD_VOICE_STATES = 1 << 7

    #: Subscribes to the following events:
    #: * PRESENCE_UPDATE
    #:
    #: Warnings
    #: --------
    #: This intent is privileged, and requires enabling/whitelisting to use.
    GUILD_PRESENCES = 1 << 8

    #: Subscribes to the following events:
    #: * MESSAGE_CREATE
    #: * MESSAGE_UPDATE
    #: * MESSAGE_DELETE
    GUILD_MESSAGES = 1 << 9

    #: Subscribes to the following events:
    #: * MESSAGE_REACTION_ADD
    #: * MESSAGE_REACTION_REMOVE
    #: * MESSAGE_REACTION_REMOVE_ALL
    #: * MESSAGE_REACTION_REMOVE_EMOJI
    GUILD_MESSAGE_REACTIONS = 1 << 10

    #: Subscribes to the following events:
    #: * TYPING_START
    GUILD_MESSAGE_TYPING = 1 << 11

    #: Subscribes to the following events:
    #: * CHANNEL_CREATE
    #: * MESSAGE_CREATE
    #: * MESSAGE_UPDATE
    #: * MESSAGE_DELETE
    DIRECT_MESSAGES = 1 << 12

    #: Subscribes to the following events:
    #: * MESSAGE_REACTION_ADD
    #: * MESSAGE_REACTION_REMOVE
    #: * MESSAGE_REACTION_REMOVE_ALL
    DIRECT_MESSAGE_REACTIONS = 1 << 13

    #: Subscribes to the following events
    #: * TYPING_START
    DIRECT_MESSAGE_TYPING = 1 << 14


# pylint: enable=no-member
