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
"""Core errors that may be raised by this API implementation."""

from __future__ import annotations

__all__ = [
    "HikariError",
    "HikariWarning",
    "NotFound",
    "Unauthorized",
    "Forbidden",
    "BadRequest",
    "HTTPError",
    "HTTPErrorResponse",
    "ClientHTTPErrorResponse",
    "ServerHTTPErrorResponse",
    "GatewayZombiedError",
    "GatewayNeedsShardingError",
    "GatewayMustReconnectError",
    "GatewayInvalidSessionError",
    "GatewayInvalidTokenError",
    "GatewayServerClosedConnectionError",
    "GatewayClientClosedError",
    "GatewayClientDisconnectedError",
    "GatewayError",
]

import http
import typing

import aiohttp.typedefs
import attr

from hikari.net import codes

if typing.TYPE_CHECKING:
    pass


class HikariError(RuntimeError):
    """Base for an error raised by this API.

    Any exceptions should derive from this.

    !!! note
        You should never initialize this exception directly.
    """

    __slots__ = ()


class HikariWarning(RuntimeWarning):
    """Base for a warning raised by this API.

    Any warnings should derive from this.

    !!! note
        You should never initialize this warning directly.
    """

    __slots__ = ()


class GatewayError(HikariError):
    """A base exception type for anything that can be thrown by the Gateway.

    Parameters
    ----------
    reason : st
        A string explaining the issue.
    """

    reason: str
    """A string to explain the issue."""

    def __init__(self, reason: str) -> None:
        super().__init__()
        self.reason = reason

    def __str__(self) -> str:
        return self.reason


class GatewayClientClosedError(GatewayError):
    """An exception raised when you programmatically shut down the bot client-side.

    Parameters
    ----------
    reason : str
        A string explaining the issue.
    """

    def __init__(self, reason: str = "The gateway client has been closed") -> None:
        super().__init__(reason)


class GatewayClientDisconnectedError(GatewayError):
    """An exception raised when the bot client-side disconnects unexpectedly.

    Parameters
    ----------
    reason : str
        A string explaining the issue.
    """

    def __init__(self, reason: str = "The gateway client has disconnected unexpectedly") -> None:
        super().__init__(reason)


class GatewayServerClosedConnectionError(GatewayError):
    """An exception raised when the server closes the connection.

    Parameters
    ----------
    close_code : typing.Union[hikari.net.codes.GatewayCloseCode, int], optional
        The close code provided by the server, if there was one.
    reason : str, optional
        A string explaining the issue.
    """

    close_code: typing.Union[codes.GatewayCloseCode, int, None]

    def __init__(
        self,
        close_code: typing.Optional[typing.Union[codes.GatewayCloseCode, int]] = None,
        reason: typing.Optional[str] = None,
    ) -> None:
        try:
            name = close_code.name
        except AttributeError:
            name = str(close_code) if close_code is not None else "no reason"

        if reason is None:
            reason = f"Gateway connection closed by server ({name})"

        self.close_code = close_code
        super().__init__(reason)


class GatewayInvalidTokenError(GatewayServerClosedConnectionError):
    """An exception that is raised if you failed to authenticate with a valid token to the Gateway."""

    def __init__(self) -> None:
        super().__init__(
            codes.GatewayCloseCode.AUTHENTICATION_FAILED,
            "The account token specified is invalid for the gateway connection",
        )


class GatewayInvalidSessionError(GatewayServerClosedConnectionError):
    """An exception raised if a Gateway session becomes invalid.

    Parameters
    ----------
    can_resume : bool
        `True` if the connection will be able to RESUME next time it starts
        rather than re-IDENTIFYing, or `False` if you need to IDENTIFY
        again instead.
    """

    can_resume: bool
    """`True` if the next reconnection can be RESUMED,
    `False` if it has to be coordinated by re-IDENFITYing.
    """

    def __init__(self, can_resume: bool) -> None:
        self.can_resume = can_resume
        instruction = "restart the shard and RESUME" if can_resume else "restart the shard with a fresh session"
        super().__init__(reason=f"The session has been invalidated; {instruction}")


class GatewayMustReconnectError(GatewayServerClosedConnectionError):
    """An exception raised when the Gateway has to re-connect with a new session.

    This will cause a re-IDENTIFY.
    """

    def __init__(self) -> None:
        super().__init__(reason="The gateway server has requested that the client reconnects with a new session")


class GatewayNeedsShardingError(GatewayServerClosedConnectionError):
    """An exception raised if you have too many guilds on one of the current Gateway shards.

    This is a sign you need to increase the number of shards that your bot is
    running with in order to connect to Discord.
    """

    def __init__(self) -> None:
        super().__init__(
            codes.GatewayCloseCode.SHARDING_REQUIRED, "You are in too many guilds. Shard the bot to connect",
        )


class GatewayZombiedError(GatewayClientClosedError):
    """An exception raised if a shard becomes zombied.

    This means that Discord is no longer responding to us, and we have
    disconnected due to a timeout.
    """

    def __init__(self) -> None:
        super().__init__("No heartbeat was received, the connection has been closed")


class HTTPError(HikariError):
    """Base exception raised if an HTTP error occurs while making a request."""

    def __init__(self, url: str, message: str):
        self.message = message
        self.url = url


class HTTPErrorResponse(HTTPError):
    def __init__(
        self,
        url: str,
        status: http.HTTPStatus,
        headers: aiohttp.typedefs.LooseHeaders,
        raw_body: typing.AnyStr,
    ) -> None:
        super().__init__(url, str(status))
        self.status = status
        self.headers = headers
        self.raw_body = raw_body


class ClientHTTPErrorResponse(HTTPErrorResponse):
    pass


class BadRequest(ClientHTTPErrorResponse):
    def __init__(
        self,
        url: str,
        headers: aiohttp.typedefs.LooseHeaders,
        raw_body: typing.AnyStr,
    ) -> None:
        status = http.HTTPStatus.BAD_REQUEST
        super().__init__(url, status, headers, raw_body)


class Unauthorized(ClientHTTPErrorResponse):
    def __init__(
        self,
        url: str,
        headers: aiohttp.typedefs.LooseHeaders,
        raw_body: typing.AnyStr,
    ) -> None:
        status = http.HTTPStatus.UNAUTHORIZED
        super().__init__(url, status, headers, raw_body)


class Forbidden(ClientHTTPErrorResponse):
    def __init__(
        self,
        url: str,
        headers: aiohttp.typedefs.LooseHeaders,
        raw_body: typing.AnyStr,
    ) -> None:
        status = http.HTTPStatus.FORBIDDEN
        super().__init__(url, status, headers, raw_body)


class NotFound(ClientHTTPErrorResponse):
    def __init__(
        self,
        url: str,
        headers: aiohttp.typedefs.LooseHeaders,
        raw_body: typing.AnyStr,
    ) -> None:
        status = http.HTTPStatus.NOT_FOUND
        super().__init__(url, status, headers, raw_body)


class ServerHTTPErrorResponse(HTTPErrorResponse):
    pass


class IntentWarning(HikariWarning):
    """Warning raised when subscribing to an event that cannot be fired.

    This is caused by your application missing certain intents.
    """
