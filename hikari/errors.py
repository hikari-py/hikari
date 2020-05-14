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

from hikari.net import codes


class HikariError(RuntimeError):
    """Base for an error raised by this API.

    Any exceptions should derive from this.

    !!! note
        You should never initialize this exception directly.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({str(self)!r})"


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
    reason : str
        A string explaining the issue.
    """

    __slots__ = ("reason",)

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

    __slots__ = ()

    def __init__(self, reason: str = "The gateway client has been closed") -> None:
        super().__init__(reason)


class GatewayClientDisconnectedError(GatewayError):
    """An exception raised when the bot client-side disconnects unexpectedly.

    Parameters
    ----------
    reason : str
        A string explaining the issue.
    """

    __slots__ = ()

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

    __slots__ = ("close_code",)

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

    __slots__ = ()

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

    __slots__ = ("can_resume",)

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

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(reason="The gateway server has requested that the client reconnects with a new session")


class GatewayNeedsShardingError(GatewayServerClosedConnectionError):
    """An exception raised if you have too many guilds on one of the current Gateway shards.

    This is a sign you need to increase the number of shards that your bot is
    running with in order to connect to Discord.
    """

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(
            codes.GatewayCloseCode.SHARDING_REQUIRED, "You are in too many guilds. Shard the bot to connect",
        )


class GatewayZombiedError(GatewayClientClosedError):
    """An exception raised if a shard becomes zombied.

    This means that Discord is no longer responding to us, and we have
    disconnected due to a timeout.
    """

    __slots__ = ()

    def __init__(self) -> None:
        super().__init__("No heartbeat was received, the connection has been closed")


class HTTPError(HikariError):
    """Base exception raised if an HTTP error occurs while making a request.

    Parameters
    ----------
    message : str
        The error message.
    url : str
        The URL that produced this error.
    """

    __slots__ = ("message", "url")

    message: str
    """The error message."""

    url: str
    """The URL that produced this error message."""

    def __init__(self, url: str, message: str) -> None:
        super().__init__()
        self.message = message
        self.url = url


class HTTPErrorResponse(HTTPError):
    """Base exception for an erroneous HTTP response.

    Parameters
    ----------
    url : str
        The URL that produced the error message.
    status : http.HTTPStatus
        The HTTP status code of the response that caused this error.
    headers : aiohttp.typedefs.LooseHeaders
        Any headers that were given in the response.
    raw_body : typing.Any
        The body that was received.
    """

    __slots__ = ("status", "headers", "raw_body")

    status: http.HTTPStatus
    """The HTTP status code for the response."""

    headers: aiohttp.typedefs.LooseHeaders
    """The headers received in the error response."""

    raw_body: typing.Any
    """The response body."""

    def __init__(
        self,
        url: str,
        status: typing.Union[int, http.HTTPStatus],
        headers: aiohttp.typedefs.LooseHeaders,
        raw_body: typing.Any,
    ) -> None:
        super().__init__(url, f"{status}: {raw_body}")
        self.status = status
        self.headers = headers
        self.raw_body = raw_body

    def __str__(self) -> str:
        try:
            raw_body = self.raw_body.decode("utf-8")
        except (AttributeError, UnicodeDecodeError):
            raw_body = str(self.raw_body)

        chomped = len(raw_body) > 200
        name = self.status.name.replace("_", " ").title()
        return f"{self.status.value} {name}: {raw_body[:200]}{'...' if chomped else ''}"


class ClientHTTPErrorResponse(HTTPErrorResponse):
    """Base exception for an erroneous HTTP response that is a client error.

    All exceptions derived from this base should be treated as 4xx client
    errors when encountered.
    """

    __slots__ = ()


class BadRequest(ClientHTTPErrorResponse):
    """Raised when you send an invalid request somehow.

    Parameters
    ----------
    url : str
        The URL that produced the error message.
    headers : aiohttp.typedefs.LooseHeaders
        Any headers that were given in the response.
    raw_body : typing.Any
        The body that was received.
    """

    __slots__ = ()

    def __init__(self, url: str, headers: aiohttp.typedefs.LooseHeaders, raw_body: typing.AnyStr) -> None:
        status = http.HTTPStatus.BAD_REQUEST
        super().__init__(url, status, headers, raw_body)


class Unauthorized(ClientHTTPErrorResponse):
    """Raised when you are not authorized to access a specific resource.

    This generally means you did not provide a token, or the token is invalid.

    Parameters
    ----------
    url : str
        The URL that produced the error message.
    headers : aiohttp.typedefs.LooseHeaders
        Any headers that were given in the response.
    raw_body : typing.Any
        The body that was received.
    """

    __slots__ = ()

    def __init__(self, url: str, headers: aiohttp.typedefs.LooseHeaders, raw_body: typing.AnyStr) -> None:
        status = http.HTTPStatus.UNAUTHORIZED
        super().__init__(url, status, headers, raw_body)


class Forbidden(ClientHTTPErrorResponse):
    """Raised when you are not allowed to access a specific resource.

    This means you lack the permissions to do something, either because of
    permissions set in a guild, or because your application is not whitelisted
    to use a specific endpoint.

    Parameters
    ----------
    url : str
        The URL that produced the error message.
    headers : aiohttp.typedefs.LooseHeaders
        Any headers that were given in the response.
    raw_body : typing.Any
        The body that was received.
    """

    __slots__ = ()

    def __init__(self, url: str, headers: aiohttp.typedefs.LooseHeaders, raw_body: typing.AnyStr) -> None:
        status = http.HTTPStatus.FORBIDDEN
        super().__init__(url, status, headers, raw_body)


class NotFound(ClientHTTPErrorResponse):
    """Raised when something is not found.

    Parameters
    ----------
    url : str
        The URL that produced the error message.
    headers : aiohttp.typedefs.LooseHeaders
        Any headers that were given in the response.
    raw_body : typing.Any
        The body that was received.
    """

    __slots__ = ()

    def __init__(self, url: str, headers: aiohttp.typedefs.LooseHeaders, raw_body: typing.AnyStr) -> None:
        status = http.HTTPStatus.NOT_FOUND
        super().__init__(url, status, headers, raw_body)


class ServerHTTPErrorResponse(HTTPErrorResponse):
    """Base exception for an erroneous HTTP response that is a server error.

    All exceptions derived from this base should be treated as 5xx server
    errors when encountered. If you get one of these, it isn't your fault!
    """

    __slots__ = ()


class IntentWarning(HikariWarning):
    """Warning raised when subscribing to an event that cannot be fired.

    This is caused by your application missing certain intents.
    """

    __slots__ = ()
