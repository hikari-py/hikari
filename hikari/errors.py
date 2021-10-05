# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
    "ComponentStateConflictError",
    "UnrecognisedEntityError",
    "NotFoundError",
    "RateLimitedError",
    "RateLimitTooLongError",
    "UnauthorizedError",
    "ForbiddenError",
    "BadRequestError",
    "HTTPError",
    "HTTPResponseError",
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
from hikari.internal import data_binding
from hikari.internal import enums

if typing.TYPE_CHECKING:
    from hikari import intents as intents_
    from hikari import messages
    from hikari import snowflakes
    from hikari.internal import routes


@attr_extensions.with_copy
@attr.define(auto_exc=True, repr=False, init=False, weakref_slot=False)
class HikariError(RuntimeError):
    """Base for an error raised by this API.

    Any exceptions should derive from this.

    !!! note
        You should never initialize this exception directly.
    """


@attr_extensions.with_copy
@attr.define(auto_exc=True, repr=False, init=False, weakref_slot=False)
class HikariWarning(RuntimeWarning):
    """Base for a warning raised by this API.

    Any warnings should derive from this.

    !!! note
        You should never initialize this warning directly.
    """


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class HikariInterrupt(KeyboardInterrupt, HikariError):
    """Exception raised when a kill signal is handled internally."""

    signum: int = attr.field()
    """The signal number that was raised."""

    signame: str = attr.field()
    """The signal name that was raised."""


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class ComponentStateConflictError(HikariError):
    """Exception thrown when an action cannot be executed in the component's current state.

    Dependent on context this will be thrown for components which are already
    running or haven't been started yet.
    """

    reason: str = attr.field()
    """A string to explain the issue."""

    def __str__(self) -> str:
        return self.reason


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class UnrecognisedEntityError(HikariError):
    """An exception thrown when an unrecognised entity is found."""

    reason: str = attr.field()
    """A string to explain the issue."""

    def __str__(self) -> str:
        return self.reason


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class GatewayError(HikariError):
    """A base exception type for anything that can be thrown by the Gateway."""

    reason: str = attr.field()
    """A string to explain the issue."""

    def __str__(self) -> str:
        return self.reason


@typing.final
class ShardCloseCode(int, enums.Enum):
    """Reasons for a shard connection closure."""

    NORMAL_CLOSURE = 1_000
    GOING_AWAY = 1_001
    PROTOCOL_ERROR = 1_002
    TYPE_ERROR = 1_003
    ENCODING_ERROR = 1_007
    POLICY_VIOLATION = 1_008
    TOO_BIG = 1_009
    UNEXPECTED_CONDITION = 1_011
    UNKNOWN_ERROR = 4_000
    UNKNOWN_OPCODE = 4_001
    DECODE_ERROR = 4_002
    NOT_AUTHENTICATED = 4_003
    AUTHENTICATION_FAILED = 4_004
    ALREADY_AUTHENTICATED = 4_005
    INVALID_SEQ = 4_007
    RATE_LIMITED = 4_008
    SESSION_TIMEOUT = 4_009
    INVALID_SHARD = 4_010
    SHARDING_REQUIRED = 4_011
    INVALID_VERSION = 4_012
    INVALID_INTENT = 4_013
    DISALLOWED_INTENT = 4_014

    @property
    def is_standard(self) -> bool:
        """Return `builtins.True` if this is a standard code."""
        return (self.value // 1000) == 1


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class GatewayConnectionError(GatewayError):
    """An exception thrown if a connection issue occurs."""

    def __str__(self) -> str:
        return f"Failed to connect to server: {self.reason!r}"


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class GatewayServerClosedConnectionError(GatewayError):
    """An exception raised when the server closes the connection."""

    code: typing.Union[ShardCloseCode, int, None] = attr.field(default=None)
    """Return the close code that was received, if there is one.

    Returns
    -------
    typing.Union[ShardCloseCode, builtins.int, builtins.None]
        The shard close code if there was one. Will be a `ShardCloseCode`
        if the definition is known. Undocumented close codes may instead be
        an `builtins.int` instead.

        If no close code was received, this will be `builtins.None`.
    """

    can_reconnect: bool = attr.field(default=False)
    """Return `builtins.True` if we can recover from this closure.

    If `builtins.True`, it will try to reconnect after this is raised rather
    than it being propagated to the caller. If `builtins.False`, this will
    be raised, thus stopping the application unless handled explicitly by the
    user.

    Returns
    -------
    builtins.bool
        Whether the closure can be recovered from via a reconnect.
    """

    def __str__(self) -> str:
        return f"Server closed connection with code {self.code} ({self.reason})"


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class HTTPError(HikariError):
    """Base exception raised if an HTTP error occurs while making a request."""

    message: str = attr.field()
    """The error message."""


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class HTTPResponseError(HTTPError):
    """Base exception for an erroneous HTTP response."""

    url: str = attr.field()
    """The URL that produced this error message."""

    status: http.HTTPStatus = attr.field()
    """The HTTP status code for the response."""

    headers: data_binding.Headers = attr.field()
    """The headers received in the error response."""

    raw_body: typing.Any = attr.field()
    """The response body."""

    message: str = attr.field(default="")
    """The error message."""

    code: int = attr.field(default=0)
    """The error code."""

    def __str__(self) -> str:
        name = self.status.name.replace("_", " ").title()
        name_value = f"{name} {self.status.value}"

        if self.code:
            code_str = f" ({self.code})"
        else:
            code_str = ""

        if self.message:
            body = self.message
        else:
            try:
                body = self.raw_body.decode("utf-8")
            except (AttributeError, UnicodeDecodeError, TypeError, ValueError):
                body = str(self.raw_body)

        chomped = len(body) > 200

        return f"{name_value}:{code_str} '{body[:200]}{'...' if chomped else ''}' for {self.url}"


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class ClientHTTPResponseError(HTTPResponseError):
    """Base exception for an erroneous HTTP response that is a client error.

    All exceptions derived from this base should be treated as 4xx client
    errors when encountered.
    """


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class BadRequestError(ClientHTTPResponseError):
    """Raised when you send an invalid request somehow."""

    status: http.HTTPStatus = attr.field(default=http.HTTPStatus.BAD_REQUEST, init=False)
    """The HTTP status code for the response."""

    errors: typing.Optional[typing.Dict[str, data_binding.JSONObject]] = attr.field(default=None, kw_only=True)
    """Dict of top level field names to field specific error paths.

    For more information, this error format is loosely defined at
    https://discord.com/developers/docs/reference#error-messages and is commonly
    returned for 50035 errors.
    """

    _cached_str: str = attr.field(default=None, init=False)

    def __str__(self) -> str:
        if self._cached_str:
            return self._cached_str

        value = super().__str__()
        if self.errors:
            value += "\n" + data_binding.dump_json(self.errors, indent=2)

        self._cached_str = value
        return value


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class UnauthorizedError(ClientHTTPResponseError):
    """Raised when you are not authorized to access a specific resource."""

    status: http.HTTPStatus = attr.field(default=http.HTTPStatus.UNAUTHORIZED, init=False)
    """The HTTP status code for the response."""


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class ForbiddenError(ClientHTTPResponseError):
    """Raised when you are not allowed to access a specific resource.

    This means you lack the permissions to do something, either because of
    permissions set in a guild, or because your application is not whitelisted
    to use a specific endpoint.
    """

    status: http.HTTPStatus = attr.field(default=http.HTTPStatus.FORBIDDEN, init=False)
    """The HTTP status code for the response."""


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class NotFoundError(ClientHTTPResponseError):
    """Raised when something is not found."""

    status: http.HTTPStatus = attr.field(default=http.HTTPStatus.NOT_FOUND, init=False)
    """The HTTP status code for the response."""


@attr.define(auto_exc=True, kw_only=True, repr=False, weakref_slot=False)
class RateLimitedError(ClientHTTPResponseError):
    """Raised when a non-global rate limit that cannot be handled occurs.

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
    """

    route: routes.CompiledRoute = attr.field()
    """The route that produced this error."""

    retry_after: float = attr.field()
    """How many seconds to wait before you can reuse the route with the specific request."""

    status: http.HTTPStatus = attr.field(default=http.HTTPStatus.TOO_MANY_REQUESTS, init=False)
    """The HTTP status code for the response."""

    message: str = attr.field(init=False)
    """The error message."""

    @message.default
    def _(self) -> str:
        return f"You are being rate-limited for {self.retry_after:,} seconds on route {self.route}. Please slow down!"


@attr.define(auto_exc=True, kw_only=True, repr=False, weakref_slot=False)
class RateLimitTooLongError(HTTPError):
    """Internal error raised if the wait for a rate limit is too long.

    This is similar to `asyncio.TimeoutError` in the way that it is used,
    but this will be raised pre-emptively and immediately if the period
    of time needed to wait is greater than a user-defined limit.

    This will almost always be route-specific. If you receive this, it is
    unlikely that performing the same call for a different channel/guild/user
    will also have this rate limit.
    """

    route: routes.CompiledRoute = attr.field()
    """The route that produced this error."""

    retry_after: float = attr.field()
    """How many seconds to wait before you can retry this specific request."""

    max_retry_after: float = attr.field()
    """How long the client is allowed to wait for at a maximum before raising."""

    reset_at: float = attr.field()
    """UNIX timestamp of when this limit will be lifted."""

    limit: int = attr.field()
    """The maximum number of calls per window for this rate limit."""

    period: float = attr.field()
    """How long the rate limit window lasts for from start to end."""

    message: str = attr.field(init=False)
    """The error message."""

    @message.default
    def _(self) -> str:
        return (
            "The request has been rejected, as you would be waiting for more than"
            f"the max retry-after ({self.max_retry_after}) on route {self.route}"
        )

    # This may support other types of limits in the future, this currently
    # exists to be self-documenting to the user and for future compatibility
    # only.
    @property
    def remaining(self) -> typing.Literal[0]:
        """The number of requests remaining in this window.

        This will always be `0` symbolically.

        Returns
        -------
        builtins.int
            The number of requests remaining. Always `0`.
        """  # noqa: D401 - Imperative mood
        return 0

    def __str__(self) -> str:
        return self.message


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class InternalServerError(HTTPResponseError):
    """Base exception for an erroneous HTTP response that is a server error.

    All exceptions derived from this base should be treated as 5xx server
    errors when encountered. If you get one of these, it is not your fault!
    """


@attr.define(auto_exc=True, repr=False, init=False, weakref_slot=False)
class MissingIntentWarning(HikariWarning):
    """Warning raised when subscribing to an event that cannot be fired.

    This is caused by your application missing certain intents.
    """


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class BulkDeleteError(HikariError):
    """Exception raised when a bulk delete fails midway through a call.

    This will contain the list of message items that failed to be deleted,
    and will have a cause containing the initial exception.
    """

    messages_deleted: snowflakes.SnowflakeishSequence[messages.PartialMessage] = attr.field()
    """Any message objects that were deleted before an exception occurred."""

    messages_skipped: snowflakes.SnowflakeishSequence[messages.PartialMessage] = attr.field()
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

    def __str__(self) -> str:
        deleted = len(self.messages_deleted)
        total = deleted + len(self.messages_skipped)
        return f"Error encountered when bulk deleting messages ({deleted}/{total} messages deleted)"


@attr.define(auto_exc=True, repr=False, init=False, weakref_slot=False)
class VoiceError(HikariError):
    """Error raised when a problem occurs with the voice subsystem."""


@attr.define(auto_exc=True, repr=False, weakref_slot=False)
class MissingIntentError(HikariError, ValueError):
    """Error raised when you try to perform an action without an intent.

    This is usually raised when querying the cache for something that is
    unavailable due to certain intents being disabled.
    """

    intents: intents_.Intents = attr.field()
    """The combination of intents that are missing."""

    def __str__(self) -> str:
        return "You are missing the following intent(s): " + ", ".join(map(str, self.intents.split()))
