#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core errors that may be raised by this API implementation.
"""
from hikari.compat import typing
from hikari.net import opcodes
from hikari import _utils


def _abstract_constructor(*_, **__):
    raise NotImplementedError(
        "This type is not implemented. Please derive a class from it with a custom __init__ defined "
        "and initialize with that."
    )


class HikariError(RuntimeError):
    """
    Base for an error raised by this API. Any errors should derive from this.

    Warning:
        You may not initialize this exception directly.
    """

    __slots__ = ("message",)
    __init__ = _abstract_constructor

    def __str__(self):
        return self.message or ""

    def __repr__(self):
        return f"{type(self).__qualname__}: {self}"


class DiscordError(HikariError):
    """
    Base for an error that occurs with the Discord API somewhere.

    May also be used for edge cases where a custom error implementation does not exist.

    Warning:
        You may not initialize this exception directly.
    """

    __slots__ = ()
    __init__ = _abstract_constructor


class HTTPError(DiscordError):
    """
    An error that occurred within the HTTP component of the API from the result of a response, or during processing.

    Warning:
        You may not initialize this exception directly.
    """

    __slots__ = ()
    __init__ = _abstract_constructor


class GatewayError(DiscordError):
    """
    Occurs if Hikari encounters a gateway error and has to close. This may be caused by an error occurring in the
    gateway logic, causing a malformed payload to be sent. It may also be triggered if the client fails to send a
    heartbeat in due time. It is also possible that an error may have occurred server-side on the Gateway at
    Discord causing this to be raised.

    Args:
        code:
            The web-socket code that was returned.
        reason:
            The reason that the connection was closed.
    """

    __slots__ = ("code", "reason", "message")

    def __init__(self, code: opcodes.GatewayClosure, reason: str) -> None:
        #: The web socket code that was returned.
        self.code: opcodes.GatewayClosure = code
        #: The reason that the connection was closed.
        self.reason: str = reason
        self.message: str = f"{self.code.name} ({self.code.value}): {self.reason}"


class ServerError(HTTPError):
    """
    Raised if an error occurs server-side on the RESTful API due to errors in Discord. This is not your code, but a
    problem with Discord itself.

    Args:
        resource:
            The HTTP resource that was accessed.
        http_status:
            The HTTP status code this represents.
        message:
            The error message provided with the error, if there is one, otherwise this is the name of the HTTP status
            code.
    """

    __slots__ = ("resource", "http_status", "message")

    def __init__(
        self, resource: _utils.Resource, http_status: opcodes.HTTPStatus, message: typing.Optional[str] = None
    ) -> None:
        self.resource: _utils.Resource = resource
        self.http_status: opcodes.HTTPStatus = http_status
        self.message: str = message or http_status.name.replace("_", " ").title()


class ClientError(HTTPError):
    """
    Raised if an error occurs server-side on the RESTful API due to bad input. This is an indication of a problem with
    your logic or input.

    Args:
        resource:
            The HTTP resource that was accessed, if available.
        http_status:
            The HTTP status code provided, if available.
        json_error_code:
            The JSON error code that was provided with this error, or `None` if no error was available.
        message:
            Any additional message that was provided with this error.
    """

    __slots__ = ("resource", "status", "error_code", "message")

    def __init__(
        self,
        resource: typing.Optional[_utils.Resource],
        http_status: typing.Optional[opcodes.HTTPStatus],
        json_error_code: typing.Optional[opcodes.JSONErrorCode],
        message: str,
    ) -> None:
        self.resource: typing.Optional[_utils.Resource] = resource
        self.status: typing.Optional[opcodes.HTTPStatus] = http_status
        self.error_code: typing.Optional[opcodes.JSONErrorCode] = json_error_code
        self.message: str = message


class BadRequest(ClientError):
    """
    Occurs when the request was improperly formatted, or the server couldn't understand it.

    Args:
        resource:
            The HTTP resource that was accessed.
        json_error_code:
            The JSON error code that was provided with this error.
        message:
            Any additional message that was provided with this error.

    Note:
        Unlike in the base class :class:`ClientError`, you can assume that :attr:`json_error_code`,
        :attr:`resource`, and :attr:`http_status` are always populated if this exception is raised.
    """

    __slots__ = ()

    def __init__(self, resource: _utils.Resource, json_error_code: opcodes.JSONErrorCode, message: str) -> None:
        super().__init__(resource, opcodes.HTTPStatus.BAD_REQUEST, json_error_code, message)


class Unauthorized(ClientError):
    """
    Occurs when the request is unauthorized. This means the Authorization header or token is invalid/missing, or some
    other credential is incorrect.

    Args:
        resource:
            The HTTP resource that was accessed.
        json_error_code:
            The JSON error code that was provided with this error.
        message:
            Any additional message that was provided with this error.

    Note:
        Unlike in the base class :class:`ClientError`, you can assume that :attr:`json_error_code`,
        :attr:`resource`, and :attr:`http_status` are always populated if this exception is raised.
    """

    __slots__ = ()

    def __init__(self, resource: _utils.Resource, json_error_code: opcodes.JSONErrorCode, message: str) -> None:
        super().__init__(resource, opcodes.HTTPStatus.UNAUTHORIZED, json_error_code, message)


class Forbidden(ClientError):
    """
    Occurs when authorization is correct, but you do not have permission to access the resource.

    Args:
        resource:
            The HTTP resource that was accessed.
        json_error_code:
            The JSON error code that was provided with this error.
        message:
            Any additional message that was provided with this error.

    Note:
        Unlike in the base class :class:`ClientError`, you can assume that :attr:`json_error_code`,
        :attr:`resource`, and :attr:`http_status` are always populated if this exception is raised.
    """

    __slots__ = ()

    def __init__(self, resource: _utils.Resource, json_error_code: opcodes.JSONErrorCode, message: str) -> None:
        super().__init__(resource, opcodes.HTTPStatus.FORBIDDEN, json_error_code, message)


class NotFound(ClientError):
    """
    Occurs when an accessed resource does not exist, or is hidden from the user.

    Args:
        resource:
            The HTTP resource that was accessed.
        json_error_code:
            The JSON error code that was provided with this error.
        message:
            Any additional message that was provided with this error.

    Note:
        Unlike in the base class :class:`ClientError`, you can assume that :attr:`json_error_code`,
        :attr:`resource`, and :attr:`http_status` are always populated if this exception is raised.
    """

    __slots__ = ()

    def __init__(self, resource: _utils.Resource, json_error_code: opcodes.JSONErrorCode, message: str) -> None:
        super().__init__(resource, opcodes.HTTPStatus.NOT_FOUND, json_error_code, message)
