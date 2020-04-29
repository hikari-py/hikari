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

from __future__ import annotations

__all__ = ["GatewayCloseCode", "GatewayOpcode", "JSONErrorCode"]

from hikari.internal import more_enums


@more_enums.must_be_unique
class GatewayCloseCode(int, more_enums.Enum):
    """Reasons for closing a gateway connection.

    !!! note
        Any codes greater than or equal to `4000` are server-side codes. Any
        codes between `1000` and `1999` inclusive are generally client-side codes.
    """

    NORMAL_CLOSURE = 1000
    """The application running closed."""

    UNKNOWN_ERROR = 4000
    """Discord is not sure what went wrong. Try reconnecting?"""

    UNKNOWN_OPCODE = 4001
    """You sent an invalid Gateway opcode or an invalid payload for an opcode.

    Don't do that!
    """

    DECODE_ERROR = 4002
    """You sent an invalid payload to Discord. Don't do that!"""

    NOT_AUTHENTICATED = 4003
    """You sent Discord a payload prior to IDENTIFYing."""

    AUTHENTICATION_FAILED = 4004
    """The account token sent with your identify payload is incorrect."""

    ALREADY_AUTHENTICATED = 4005
    """You sent more than one identify payload. Don't do that!"""

    INVALID_SEQ = 4007
    """The sequence sent when resuming the session was invalid.

    Reconnect and start a new session.
    """

    RATE_LIMITED = 4008
    """Woah nelly! You're sending payloads to Discord too quickly. Slow it down!"""

    SESSION_TIMEOUT = 4009
    """Your session timed out. Reconnect and start a new one."""

    INVALID_SHARD = 4010
    """You sent Discord an invalid shard when IDENTIFYing."""

    SHARDING_REQUIRED = 4011
    """The session would have handled too many guilds.

    You are required to shard your connection in order to connect.
    """

    INVALID_VERSION = 4012
    """You sent an invalid version for the gateway."""

    INVALID_INTENT = 4013
    """You sent an invalid intent for a Gateway Intent.

    You may have incorrectly calculated the bitwise value.
    """

    DISALLOWED_INTENT = 4014
    """You sent a disallowed intent for a Gateway Intent.

    You may have tried to specify an intent that you have not enabled or are not
    whitelisted for.
    """

    def __str__(self) -> str:
        name = self.name.replace("_", " ").title()
        return f"{self.value} {name}"


@more_enums.must_be_unique
class GatewayOpcode(int, more_enums.Enum):
    """Opcodes that the gateway uses internally."""

    DISPATCH = 0
    """An event was dispatched."""

    HEARTBEAT = 1
    """Used for ping checking."""

    IDENTIFY = 2
    """Used for client handshake."""

    PRESENCE_UPDATE = 3
    """Used to update the client status."""

    VOICE_STATE_UPDATE = 4
    """Used to join/move/leave voice channels."""

    RESUME = 6
    """Used to resume a closed connection."""

    RECONNECT = 7
    """Used to tell clients to reconnect to the gateway."""

    REQUEST_GUILD_MEMBERS = 8
    """Used to request guild members."""

    INVALID_SESSION = 9
    """Used to notify client they have an invalid session id."""

    HELLO = 10
    """Sent immediately after connecting.

    Contains heartbeat and server debug information.
    """

    HEARTBEAT_ACK = 11
    """Sent immediately following a client heartbeat that was received."""

    GUILD_SYNC = 12
    """Not yet documented, so do not use."""

    def __str__(self) -> str:
        name = self.name.replace("_", " ").title()
        return f"{self.value} {name}"


@more_enums.must_be_unique
class JSONErrorCode(int, more_enums.Enum):
    """Error codes that can be returned by the REST API."""

    GENERAL_ERROR = 0
    """This is sent if the payload is screwed up, etc."""

    UNKNOWN_ACCOUNT = 10_001
    """Unknown account"""

    UNKNOWN_APPLICATION = 10_002
    """Unknown application"""

    UNKNOWN_CHANNEL = 10_003
    """Unknown channel"""

    UNKNOWN_GUILD = 10_004
    """Unknown guild"""

    UNKNOWN_INTEGRATION = 10_005
    """Unknown integration"""

    UNKNOWN_INVITE = 10_006
    """Unknown invite"""

    UNKNOWN_MEMBER = 10_007
    """Unknown member"""

    UNKNOWN_MESSAGE = 10_008
    """Unknown message"""

    UNKNOWN_OVERWRITE = 10_009
    """Unknown overwrite"""

    UNKNOWN_PROVIDER = 10_010
    """Unknown provider"""

    UNKNOWN_ROLE = 10_011
    """Unknown role"""

    UNKNOWN_TOKEN = 10_012
    """Unknown token"""

    UNKNOWN_USER = 10_013
    """Unknown user"""

    UNKNOWN_EMOJI = 10_014
    """Unknown emoji"""

    UNKNOWN_WEBHOOK = 10_015
    """Unknown Webhook"""

    UNKNOWN_BAN = 10_026
    """Unknown ban"""

    USERS_ONLY = 20_001
    """Bots cannot use this endpoint

    !!! note
        You should never expect to receive this in normal API usage.
    """

    BOTS_ONLY = 20_002
    """Only bots can use this endpoint.

    !!! note
        You should never expect to receive this in normal API usage.
    """

    MAX_GUILDS_REACHED = 30_001
    """Maximum number of guilds reached (100)

    !!! note
        You should never expect to receive this in normal API usage as this only
        applies to user accounts.

    This is unlimited for bot accounts.
    """

    MAX_FRIENDS_REACHED = 30_002
    """Maximum number of friends reached (1000)

    !!! note
        You should never expect to receive this in normal API usage as this only
        applies to user accounts.

        Bots cannot have friends :( .
    """

    MAX_PINS_REACHED = 30_003
    """Maximum number of pins reached (50)"""

    MAX_GUILD_ROLES_REACHED = 30_005
    """Maximum number of guild roles reached (250)"""

    MAX_WEBHOOKS_REACHED = 30_007
    """Maximum number of webhooks reached (10)"""

    MAX_REACTIONS_REACHED = 30_010
    """Maximum number of reactions reached (20)"""

    MAX_GUILD_CHANNELS_REACHED = 30_013
    """Maximum number of guild channels reached (500)"""

    MAX_MESSAGE_ATTACHMENTS_REACHED = 30_015
    """Maximum number of attachments in a message reached (10)"""

    MAX_INVITES_REACHED = 30_016
    """Maximum number of invites reached (10000)"""

    NEEDS_VERIFICATION = 40_002
    """You need to verify your account to perform this action."""

    UNAUTHORIZED = 40_001
    """Unauthorized"""

    TOO_LARGE = 40_005
    """Request entity too large. Try sending something smaller in size"""

    DISABLED_TEMPORARILY = 40_006
    """This feature has been temporarily disabled server-side"""

    USER_BANNED = 40_007
    """The user is banned from this guild"""

    MISSING_ACCESS = 50_001
    """Missing access"""

    INVALID_ACCOUNT_TYPE = 50_002
    """Invalid account type"""

    CANNOT_EXECUTE_ACTION_ON_DM_CHANNEL = 50_003
    """Cannot execute action on a DM channel"""

    WIDGET_DISABLED = 50_004
    """Widget Disabled"""

    CANNOT_EDIT_A_MESSAGE_AUTHORED_BY_ANOTHER_USER = 50_005
    """Cannot edit a message authored by another user"""

    CANNOT_SEND_AN_EMPTY_MESSAGE = 50_006
    """Cannot send an empty message"""

    CANNOT_SEND_MESSAGES_TO_THIS_USER = 50_007
    """Cannot send messages to this user"""

    CANNOT_SEND_MESSAGES_IN_VOICE_CHANNEL = 50_008
    """Cannot send messages in a voice channel"""

    CHANNEL_VERIFICATION_TOO_HIGH = 50_009
    """Channel verification level is too high"""

    OAUTH2_APPLICATION_DOES_NOT_HAVE_A_BOT = 50_010
    """OAuth2 application does not have a bot"""

    OAUTH2_APPLICATION_LIMIT_REACHED = 50_011
    """OAuth2 application limit reached"""

    INVALID_OAUTH2_STATE = 50_012
    """Invalid OAuth state"""

    MISSING_PERMISSIONS = 50_013
    """Missing permissions"""

    INVALID_AUTHENTICATION_TOKEN = 50_014
    """Invalid authentication token"""

    NOTE_IS_TOO_LONG = 50_015
    """Note is too long"""

    INVALID_NUMBER_OF_MESSAGES_TO_DELETE = 50_016
    """Provided too few or too many messages to delete.

    Must provide at least 2 and fewer than 100 messages to delete.
    """

    CANNOT_PIN_A_MESSAGE_IN_A_DIFFERENT_CHANNEL = 50_019
    """A message can only be pinned to the channel it was sent in"""

    INVALID_INVITE = 50_020
    """Invite code is either invalid or taken."""

    CANNOT_EXECUTE_ACTION_ON_SYSTEM_MESSAGE = 50_021
    """Cannot execute action on a system message"""

    INVALID_OAUTH2_TOKEN = 50_025
    """Invalid OAuth2 access token"""

    MESSAGE_PROVIDED_WAS_TOO_OLD_TO_BULK_DELETE = 50_034
    """A message provided was too old to bulk delete"""

    INVALID_FORM_BODY = 50_035
    """Invalid Form Body"""

    ACCEPTED_INVITE_TO_GUILD_BOT_IS_NOT_IN = 50_036
    """An invite was accepted to a guild the application's bot is not in"""

    INVALID_API_VERSION = 50_041
    """Invalid API version"""

    REACTION_BLOCKED = 90_001
    """Reaction blocked"""

    RESOURCE_OVERLOADED = 130_000
    """The resource is overloaded."""

    def __str__(self) -> str:
        name = self.name.replace("_", " ").title()
        return f"{self.value} {name}"


# pylint: enable=no-member
