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
"""
Errors that can be raised by networking components.
"""
import enum

from hikari import errors
from hikari.net import routes


class GatewayCloseCode(enum.IntEnum):
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
    #: Woah nelly! You're sending payloads to us too quickly. Slow it down!
    RATE_LIMITED = 4008
    #: Your session timed out. Reconnect and start a new one.
    SESSION_TIMEOUT = 4009
    #: You sent us an invalid shard when identifying.
    INVALID_SHARD = 4010
    #: The session would have handled too many guilds - you are required to shard your connection in order to connect.
    SHARDING_REQUIRED = 4011


class GatewayError(errors.HikariError):
    reason: str

    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return self.reason


class GatewayClientClosedError(GatewayError):
    def __init__(self, message="The gateway client has been closed"):
        super().__init__(message)


class GatewayConnectionClosedError(GatewayError):
    code: int

    def __init__(self, code: int = None, reason=None):
        self.code = code

        try:
            code = GatewayCloseCode(code)
            code_name = GatewayCloseCode(code).name
        except ValueError:
            super().__init__(reason or f"Gateway connection closed by server with code {code}")
        else:
            super().__init__(reason or f"Gateway connection closed by server with code {code_name} ({code})")


class GatewayInvalidTokenError(GatewayConnectionClosedError):
    def __init__(self):
        super().__init__(
            GatewayCloseCode.AUTHENTICATION_FAILED, "The account token specified is invalid for the gateway connection",
        )


class GatewayInvalidSessionError(GatewayConnectionClosedError):
    can_resume: bool

    def __init__(self, can_resume):
        self.can_resume = can_resume
        super().__init__(
            None,
            "The session has been invalidated. "
            + ("Restart the shard and RESUME" if can_resume else "Restart the shard with a fresh session"),
        )


class GatewayMustReconnectError(GatewayConnectionClosedError):
    def __init__(self):
        super().__init__(
            None, "The gateway server has requested that the client reconnects with a new session",
        )


class GatewayNeedsShardingError(GatewayConnectionClosedError):
    def __init__(self):
        super().__init__(
            GatewayCloseCode.SHARDING_REQUIRED, "You are in too many guilds. Shard the bot to connect",
        )


class GatewayZombiedError(GatewayClientClosedError):
    def __init__(self):
        super().__init__("No heartbeat was received, the connection has been closed")


class ShardPresence:
    __slots__ = ("activity", "status", "idle_since", "is_afk")

    def __init__(self, activity=None, status="online", idle_since=0, is_afk=False):
        self.activity = activity
        self.status = status
        self.idle_since = idle_since
        self.is_afk = is_afk

    def __repr__(self):
        this_type = type(self).__name__
        major_attributes = ", ".join(
            (
                f"activity={self.activity!r}",
                f"status={self.status!r}",
                f"idle_since={self.idle_since!r}",
                f"is_afk={self.is_afk!r}",
            )
        )
        return f"{this_type}({major_attributes})"


class HTTPError(errors.HikariError):
    reason: str

    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return self.reason


class ServerHTTPError(HTTPError):
    route: routes.CompiledRoute
    message: str
    status: int

    def __init__(self, reason, route, message, status):
        super().__init__(reason)
        self.route = route
        self.message = message
        self.status = status

    def __str__(self):
        return f"{self.reason}: {self.message}"


class ClientHTTPError(HTTPError):
    route: routes.CompiledRoute
    message: str
    code: int

    def __init__(self, reason, route, message, code):
        super().__init__(reason)
        self.route = route
        self.message = message
        self.code = code

    def __str__(self):
        return f"{self.reason}: ({self.code}) {self.message}"


class BadRequestHTTPError(ClientHTTPError):
    def __init__(self, route, message, code):
        super().__init__("400: Bad Request", route, message, code)


class UnauthorizedHTTPError(ClientHTTPError):
    def __init__(self, route, message, code):
        super().__init__("401: Unauthorized", route, message, code)


class ForbiddenHTTPError(ClientHTTPError):
    def __init__(self, route, message, code):
        super().__init__("403: Forbidden", route, message, code)


class NotFoundHTTPError(ClientHTTPError):
    def __init__(self, route, message, code):
        super().__init__("404: Not Found", route, message, code)


__all__ = (
    "GatewayCloseCode",
    "GatewayError",
    "GatewayClientClosedError",
    "GatewayConnectionClosedError",
    "GatewayInvalidTokenError",
    "GatewayInvalidSessionError",
    "GatewayMustReconnectError",
    "GatewayNeedsShardingError",
    "GatewayZombiedError",
    "ShardPresence",
    "HTTPError",
    "ServerHTTPError",
    "ClientHTTPError",
    "BadRequestHTTPError",
    "UnauthorizedHTTPError",
    "ForbiddenHTTPError",
    "NotFoundHTTPError",
)
