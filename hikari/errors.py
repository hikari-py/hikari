# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Exceptions and warnings that can be thrown by this library."""

from __future__ import annotations

__all__: typing.List[str] = [
    "HikariError",
    "HikariWarning",
    "HikariInterrupt",
    "NotFoundError",
    "RateLimitedError",
    "UnauthorizedError",
    "ForbiddenError",
    "BadRequestError",
    "RESTErrorCode",
    "HTTPError",
    "HTTPResponseError",
    "HTTPClientClosedError",
    "ClientHTTPResponseError",
    "InternalServerError",
    "ShardCloseCode",
    "GatewayConnectionError",
    "GatewayServerClosedConnectionError",
    "GatewayError",
    "MissingIntentWarning",
    "MissingIntentError",
    "BulkDeleteError",
    "VoiceError",
]

import http
import typing

import attr

from hikari.internal import attr_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    from hikari import intents as intents_
    from hikari import messages
    from hikari import snowflakes
    from hikari.internal import data_binding
    from hikari.internal import routes


@attr_extensions.with_copy
@attr.s(auto_exc=True, slots=True, repr=False, init=False, weakref_slot=False)
class HikariError(RuntimeError):
    """Base for an error raised by this API.

    Any exceptions should derive from this.

    !!! note
        You should never initialize this exception directly.
    """


@attr_extensions.with_copy
@attr.s(auto_exc=True, slots=True, repr=False, init=False, weakref_slot=False)
class HikariWarning(RuntimeWarning):
    """Base for a warning raised by this API.

    Any warnings should derive from this.

    !!! note
        You should never initialize this warning directly.
    """


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class HikariInterrupt(KeyboardInterrupt, HikariError):
    """Exception raised when a kill signal is handled internally."""

    signum: int = attr.ib()
    """The signal number that was raised."""

    signame: str = attr.ib()
    """The signal name that was raised."""


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class GatewayError(HikariError):
    """A base exception type for anything that can be thrown by the Gateway."""

    reason: str = attr.ib()
    """A string to explain the issue."""

    def __str__(self) -> str:
        return self.reason


@typing.final
class ShardCloseCode(int, enums.Enum):
    """Reasons for a shard connection closure."""

    NORMAL_CLOSURE = 1000
    GOING_AWAY = 1001
    PROTOCOL_ERROR = 1002
    TYPE_ERROR = 1003
    ENCODING_ERROR = 1007
    POLICY_VIOLATION = 1008
    TOO_BIG = 1009
    UNEXPECTED_CONDITION = 1011
    UNKNOWN_ERROR = 4000
    UNKNOWN_OPCODE = 4001
    DECODE_ERROR = 4002
    NOT_AUTHENTICATED = 4003
    AUTHENTICATION_FAILED = 4004
    ALREADY_AUTHENTICATED = 4005
    INVALID_SEQ = 4007
    RATE_LIMITED = 4008
    SESSION_TIMEOUT = 4009
    INVALID_SHARD = 4010
    SHARDING_REQUIRED = 4011
    INVALID_VERSION = 4012
    INVALID_INTENT = 4013
    DISALLOWED_INTENT = 4014

    def __str__(self) -> str:
        return self.name


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class GatewayConnectionError(GatewayError):
    """An exception thrown if a connection issue occurs."""


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class GatewayServerClosedConnectionError(GatewayError):
    """An exception raised when the server closes the connection."""

    code: typing.Union[ShardCloseCode, int, None] = attr.ib(default=None)
    """Return the close code that was received, if there is one.

    Returns
    -------
    typing.Union[ShardCloseCode, builtins.int, builtins.None]
        The shard close code if there was one. Will be a `ShardCloseCode`
        if the definition is known. Undocumented close codes may instead be
        an `builtins.int` instead.

        If no close code was received, this will be `builtins.None`.
    """

    can_reconnect: bool = attr.ib(default=False)
    """Return `builtins.True` if we can recover from this closure.

    If `builtins.True`, it will try to reconnect after this is raised rather
    than it being propagated to the caller. If `builtins.False`, this will
    be raised, thus stopping the applicaiton unless handled explicitly by the
    user.

    Returns
    -------
    builtins.bool
        Whether the closure can be recovered from via a reconnect.
    """

    def __str__(self) -> str:
        return f"Server closed connection with code {self.code} ({self.reason})"


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class HTTPError(HikariError):
    """Base exception raised if an HTTP error occurs while making a request."""

    message: str = attr.ib()
    """The error message."""


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class HTTPClientClosedError(HTTPError):
    """Exception raised if an `aiohttp.ClientSession` was closed.

    This fires when using a closed `aiohttp.ClientSession` to make a
    request.
    """

    message: str = attr.ib(default="The client session has been closed, no HTTP requests can occur.", init=False)
    """The error message."""


@typing.final
class RESTErrorCode(int, enums.Enum):
    """Error codes provided as further info on errors returned by the REST API."""

    GENERAL_ERROR = 0
    """A general error, no further info provided."""

    UNKNOWN_APPLICATION = 10002
    """Unknown application provided."""

    UNKNOWN_CHANNEL = 10003
    """Unknown channel provided."""

    UNKNOWN_GUILD = 10004
    """Unknown guild provided."""

    UNKNOWN_INTEGRATION = 10005
    """Unknown integration provided."""

    UNKNOWN_INVITE = 10006
    """Unknown invite provided."""

    UNKNOWN_MEMBER = 10007
    """Unknown member provided."""

    UNKNOWN_MESSAGE = 10008
    """Unknown message provided."""

    UNKNOWN_PERMISSION_OVERWRITE = 10009
    """Unknown permission overwrite provided."""

    UNKNOWN_ROLE = 10011
    """Unknown role provided."""

    UNKNOWN_USER = 10013
    """Unknown user provided."""

    UNKNOWN_EMOJI = 10014
    """Unknown emoji provided."""

    UNKNOWN_WEBHOOK = 10015
    """Unknown webhook provided."""

    UNKNOWN_BAN = 10026
    """Unknown ban provided."""

    WRITE_LIMIT_HIT = 20028
    """The global write limit on a channel has been hit."""

    MAXIMUM_GUILDS = 30001
    """Maximum number of guilds reached (100)."""

    MAXIMUM_PINS = 30003
    """Maximum number of pins reached for the channel (50)."""

    MAXIMUM_ROLES = 30005
    """Maximum number of guild roles reached (250)."""

    MAXIMUM_WEBHOOKS = 30007
    """Maximum number of webhooks in a channel reached (10)."""

    MAXIMUM_REACTIONS = 30010
    """Maximum number of reactions on a message reached (20)."""

    MAXIMUM_CHANNELS = 30013
    """Maximum number of guild channels reached (500)."""

    MAXIMUM_INVITES = 30016
    """Maximum number of invites reached (1000)."""

    REQUEST_TOO_LARGE = 40005
    """Request too large. Try sending something smaller in size."""

    TEMPORARILY_DISABLED = 40006
    """This feature has been temporarily disabled server-side."""

    ALREADY_CROSSPOSTED = 40033
    """This message has already been crossposted."""

    MISSING_ACCESS = 50001
    """Missing access."""

    PROHIBITED_ON_DM = 50003
    """Cannot execute action on a DM channel."""

    NOT_MESSAGE_AUTHOR = 50005
    """Cannot edit a message authored by another user."""

    EMPTY_MESSAGE = 50006
    """Cannot send an empty message."""

    USER_DM_CLOSED = 50007
    """Cannot send messages to this user."""

    MESSAGE_IN_VC = 50008
    """Cannot send messages in a voice channel."""

    PINS_ONLY_ON_ORIGIN_CHANNEL = 50019
    """A message can only be pinned to the channel it was sent in."""

    PROHIBITED_ON_SYSTEM_MESSAGE = 50021
    """Cannot execute action on a system message."""

    MESSAGE_TOO_OLD = 50034
    """A message provided was too old to bulk delete."""

    SYSTEM_OVERLOADED = 130000
    """API resource is currently overloaded. Try again a little later."""

    def __str__(self) -> str:
        return self.name


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class HTTPResponseError(HTTPError):
    """Base exception for an erroneous HTTP response."""

    url: str = attr.ib()
    """The URL that produced this error message."""

    status: typing.Union[int, http.HTTPStatus] = attr.ib()
    """The HTTP status code for the response."""

    headers: data_binding.Headers = attr.ib()
    """The headers received in the error response."""

    raw_body: typing.Any = attr.ib()
    """The response body."""

    message: str = attr.ib(default="")
    """The error message."""

    code: typing.Union[RESTErrorCode, int] = attr.ib(default=RESTErrorCode.GENERAL_ERROR)
    """The error code."""

    def __str__(self) -> str:
        if isinstance(self.status, http.HTTPStatus):
            name = self.status.name.replace("_", " ").title()
            name_value = f"{name} {self.status.value}"
        else:
            name_value = str(self.status).title()

        if self.message:
            body = self.message
        else:
            try:
                body = self.raw_body.decode("utf-8")
            except (AttributeError, UnicodeDecodeError, TypeError, ValueError):
                body = str(self.raw_body)

        chomped = len(body) > 200

        return f"{name_value}: '{body[:200]}{'...' if chomped else ''}' for {self.url}"


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class ClientHTTPResponseError(HTTPResponseError):
    """Base exception for an erroneous HTTP response that is a client error.

    All exceptions derived from this base should be treated as 4xx client
    errors when encountered.
    """


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class BadRequestError(ClientHTTPResponseError):
    """Raised when you send an invalid request somehow."""

    status: http.HTTPStatus = attr.ib(default=http.HTTPStatus.BAD_REQUEST, init=False)
    """The HTTP status code for the response."""


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class UnauthorizedError(ClientHTTPResponseError):
    """Raised when you are not authorized to access a specific resource."""

    status: http.HTTPStatus = attr.ib(default=http.HTTPStatus.UNAUTHORIZED, init=False)
    """The HTTP status code for the response."""


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class ForbiddenError(ClientHTTPResponseError):
    """Raised when you are not allowed to access a specific resource.

    This means you lack the permissions to do something, either because of
    permissions set in a guild, or because your application is not whitelisted
    to use a specific endpoint.
    """

    status: http.HTTPStatus = attr.ib(default=http.HTTPStatus.FORBIDDEN, init=False)
    """The HTTP status code for the response."""


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class NotFoundError(ClientHTTPResponseError):
    """Raised when something is not found."""

    status: http.HTTPStatus = attr.ib(default=http.HTTPStatus.NOT_FOUND, init=False)
    """The HTTP status code for the response."""


@attr.s(auto_exc=True, kw_only=True, slots=True, repr=False, weakref_slot=False)
class RateLimitedError(ClientHTTPResponseError):
    """Raised when a non-global ratelimit that cannot be handled occurs.

    This should only ever occur for specific routes that have additional
    rate-limits applied to them by Discord. At the time of writing, the
    PATCH CHANNEL _endpoint is the only one that knowingly implements this, and
    does so by implementing rate-limits on the usage of specific fields only.

    If you receive one of these, you should NOT try again until the given
    time has passed, either discarding the operation you performed, or waiting
    until the given time has passed first. Note that it may still be valid to
    send requests with different attributes in them.

    A use case for this by Discord appears to be to stop abuse from bots that
    change channel names, etc, regularly. This kind of action allegedly causes
    a fair amount of overhead internally for Discord. In the case you encounter
    this, you may be able to send different requests that manipulate the same
    entities (in this case editing the same channel) that do not use the same
    collection of attributes as the previous request.

    You should not usually see this occur, unless Discord vastly change their
    ratelimit system without prior warning, which might happen in the future.

    !!! note
        If you receive this regularly, please file a bug report, or contact
        Discord with the relevant debug information that can be obtained by
        enabling debug logs and enabling the debug mode on the HTTP components.
    """

    route: routes.CompiledRoute = attr.ib()
    """The route that produced this error."""

    retry_after: float = attr.ib()
    """How many seconds to wait before you can reuse the route with the specific request."""

    status: http.HTTPStatus = attr.ib(default=http.HTTPStatus.TOO_MANY_REQUESTS, init=False)
    """The HTTP status code for the response."""

    reason: str = attr.ib(init=False)
    """The error reason."""

    @reason.default
    def _(self) -> str:
        return f"You are being rate-limited for {self.retry_after:,} seconds on route {self.route}. Please slow down!"


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class InternalServerError(HTTPResponseError):
    """Base exception for an erroneous HTTP response that is a server error.

    All exceptions derived from this base should be treated as 5xx server
    errors when encountered. If you get one of these, it is not your fault!
    """


@attr.s(auto_exc=True, slots=True, repr=False, init=False, weakref_slot=False)
class MissingIntentWarning(HikariWarning):
    """Warning raised when subscribing to an event that cannot be fired.

    This is caused by your application missing certain intents.
    """


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class BulkDeleteError(HikariError):
    """Exception raised when a bulk delete fails midway through a call.

    This will contain the list of message items that failed to be deleted,
    and will have a cause containing the initial exception.
    """

    messages_deleted: typing.Sequence[snowflakes.SnowflakeishOr[messages.PartialMessage]] = attr.ib()
    """Any message objects that were deleted before an exception occurred."""

    messages_skipped: typing.Sequence[snowflakes.SnowflakeishOr[messages.PartialMessage]] = attr.ib()
    """Any message objects that were skipped due to an exception."""

    @property
    def percentage_completion(self) -> float:
        """Return the percentage completion of the bulk delete before it failed.

        Returns
        -------
        builtins.float
            A percentage completion between 0 and 100 inclusive.
        """
        deleted = len(self.messages_deleted)
        total = deleted + len(self.messages_skipped)
        return 100 * deleted / total


@attr.s(auto_exc=True, slots=True, repr=False, init=False, weakref_slot=False)
class VoiceError(HikariError):
    """Error raised when a problem occurs with the voice subsystem."""


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class MissingIntentError(HikariError, ValueError):
    """Error raised when you try to perform an action without an intent.

    This is usually raised when querying the cache for something that is
    unavailable due to certain intents being disabled.
    """

    intents: intents_.Intents = attr.ib()
    """The combination of intents that are missing."""

    def __str__(self) -> str:
        return f"You are missing the following intent(s): {str(self.intents)}"
