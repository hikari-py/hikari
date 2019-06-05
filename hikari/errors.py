#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core errors that may be raised by this API implementation.
"""
import typing

from hikari.net import opcodes


class HikariError(RuntimeError):
    """
    Base for an error raised by this API. Any errors should derive from this.

    Args:
        message:
            The message to show.
    """

    __slots__ = ("message",)

    def __init__(self, message: str) -> None:
        #: The message to show.
        self.message: str = message

    def __str__(self):
        return self.message

    def __repr__(self):
        return f"{type(self).__qualname__}: {self}"


class ClientError(HikariError):
    """Base for an error that occurs in this codebase specifically."""

    __slots__ = ()


class DiscordError(HikariError):
    """
    Base for an error that occurs with the Discord API somewhere.

    May also be used for edge cases where a custom error implementation does not exist.
    """

    __slots__ = ()


class DiscordBadRequest(DiscordError):
    """Occurs when the request was improperly formatted, or the server couldn't understand it."""

    __slots__ = ()


class DiscordUnauthorized(DiscordError):
    """Occurs when the request is unauthorized. This means the Authorization header or token is invalid."""

    __slots__ = ()


class DiscordForbidden(DiscordError):
    """Occurs when authorization is correct, but you do not have permission to access the resource."""

    __slots__ = ()


class DiscordNotFound(DiscordError):
    """Occurs when an accessed resource does not exist, or is hidden from the user."""

    __slots__ = ()


class DiscordGatewayError(DiscordError):
    """
    Occurs if Hikari encounters a gateway error and has to close. This may be caused by an error occurring in the
    gateway logic, causing a malformed payload to be sent. It may also be triggered if the client fails to send a
    heartbeat in due time. It is also possible that an error may have occurred server-side on the Gateway at
    Discord causing this to be raised.

    Args:
        code:
            The websocket code that was returned.
        reason:
            The reason that the connection was closed.
    """

    __slots__ = ("code", "reason")

    def __init__(self, code: opcodes.GatewayServerExit, reason: str) -> None:
        #: The websocket code that was returned.
        self.code: opcodes.GatewayServerExit = code
        #: The reason that the connection was closed.
        self.reason: str = reason
        super().__init__(f"{self.code.name} ({self.code.value}): {self.reason}")


class DiscordHTTPError(DiscordError):
    """
    Raised if an error occurs server-side on the RESTful API. This indicates a problem with Discord, not your code.

    Args:
        code:
            The code that was raised, if there was one.
        reason:
            The reason for the error.
    """

    __slots__ = ("code", "reason")

    def __init__(self, code: typing.Optional[int], reason: str) -> None:
        #: The code that was raised, or `None` if not applicable (e.g. a websocket error triggered this).
        self.code: typing.Optional[int] = code
        #: The reason for the error.
        self.reason: str = reason

        if code is not None:
            super().__init__(f"{self.code}: {self.reason}")
        else:
            super().__init__(self.reason)
