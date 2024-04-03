# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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

__all__: typing.Sequence[str] = (
    "HikariError",
    "HikariWarning",
    "HikariInterrupt",
    "ComponentStateConflictError",
    "UnrecognisedEntityError",
    "NotFoundError",
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
)

import http
import json
import typing

import attrs

from hikari.internal import attrs_extensions
from hikari.internal import data_binding
from hikari.internal import enums

if typing.TYPE_CHECKING:
    from hikari import intents as intents_
    from hikari import messages
    from hikari import snowflakes
    from hikari.internal import routes


# The standard exceptions are all unslotted so slotting here would be a waste of time.
@attrs_extensions.with_copy
@attrs.define(auto_exc=True, repr=False, init=False, slots=False)
class HikariError(RuntimeError):
    """Base for an error raised by this API.

    Any exceptions should derive from this.

    !!! note
        You should never initialize this exception directly.
    """


# The standard warnings are all unslotted so slotting here would be a waste of time.
@attrs_extensions.with_copy
@attrs.define(auto_exc=True, repr=False, init=False, slots=False)
class HikariWarning(RuntimeWarning):
    """Base for a warning raised by this API.

    Any warnings should derive from this.

    !!! note
        You should never initialize this warning directly.
    """


@attrs.define(auto_exc=True, repr=False, slots=False)
class HikariInterrupt(KeyboardInterrupt, HikariError):
    """Exception raised when a kill signal is handled internally."""

    signum: int = attrs.field()
    """The signal number that was raised."""

    signame: str = attrs.field()
    """The signal name that was raised."""

    def __str__(self) -> str:
        return f"Signal {self.signum} ({self.signame}) received"


@attrs.define(auto_exc=True, repr=False, slots=False)
class ComponentStateConflictError(HikariError):
    """Exception thrown when an action cannot be executed in the component's current state.

    Dependent on context this will be thrown for components which are already
    running or haven't been started yet.
    """

    reason: str = attrs.field()
    """A string to explain the issue."""

    def __str__(self) -> str:
        return self.reason


@attrs.define(auto_exc=True, repr=False, slots=False)
class UnrecognisedEntityError(HikariError):
    """An exception thrown when an unrecognised entity is found."""

    reason: str = attrs.field()
    """A string to explain the issue."""

    def __str__(self) -> str:
        return self.reason


@attrs.define(auto_exc=True, repr=False, slots=False)
class GatewayError(HikariError):
    """A base exception type for anything that can be thrown by the Gateway."""

    reason: str = attrs.field()
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
        """Return [`True`][] if this is a standard code."""
        return (self.value // 1000) == 1


@attrs.define(auto_exc=True, repr=False, slots=False)
class GatewayConnectionError(GatewayError):
    """An exception thrown if a connection issue occurs."""

    def __str__(self) -> str:
        return f"Failed to connect to server: {self.reason!r}"


@attrs.define(auto_exc=True, repr=False, slots=False)
class GatewayServerClosedConnectionError(GatewayError):
    """An exception raised when the server closes the connection."""

    code: typing.Union[ShardCloseCode, int, None] = attrs.field(default=None)
    """Return the close code that was received, if there is one."""

    can_reconnect: bool = attrs.field(default=False)
    """Return [`True`][] if we can recover from this closure.

    If [`True`][], it will try to reconnect after this is raised rather
    than it being propagated to the caller. If [`False`][], this will
    be raised, thus stopping the application unless handled explicitly by the
    user.
    """

    def __str__(self) -> str:
        return f"Server closed connection with code {self.code} ({self.reason})"


@attrs.define(auto_exc=True, repr=False, slots=False)
class HTTPError(HikariError):
    """Base exception raised if an HTTP error occurs while making a request."""

    message: str = attrs.field()
    """The error message."""


@attrs.define(auto_exc=True, repr=False, slots=False)
class HTTPResponseError(HTTPError):
    """Base exception for an erroneous HTTP response."""

    url: str = attrs.field()
    """The URL that produced this error message."""

    status: typing.Union[http.HTTPStatus, int] = attrs.field()
    """The HTTP status code for the response.

    This will be [`int`][] if it's outside the range of status codes in the HTTP
    specification (e.g. one of Cloudflare's non-standard status codes).
    """

    headers: data_binding.Headers = attrs.field()
    """The headers received in the error response."""

    raw_body: typing.Any = attrs.field()
    """The response body."""

    message: str = attrs.field(default="")
    """The error message."""

    code: int = attrs.field(default=0)
    """The error code."""

    def __str__(self) -> str:
        if isinstance(self.status, http.HTTPStatus):
            name = self.status.name.replace("_", " ").title()
            name_value = f"{name} {self.status.value}"

        else:
            name_value = f"Unknown Status {self.status}"

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


@attrs.define(auto_exc=True, repr=False, slots=False)
class ClientHTTPResponseError(HTTPResponseError):
    """Base exception for an erroneous HTTP response that is a client error.

    All exceptions derived from this base should be treated as 4xx client
    errors when encountered.
    """


def _dump_errors(obj: data_binding.JSONObject, obj_string: str = "") -> str:
    string = ""
    for key, value in obj.items():
        if isinstance(value, typing.Sequence):
            string += (obj_string or "root") + ":"

            for item in value:
                string += f"\n - {item['message']}"

            string += "\n\n"

            continue

        current_obj_string = f"{obj_string}{'.' if obj_string else ''}{key}"
        string += _dump_errors(value, current_obj_string)

    return string


@attrs.define(auto_exc=True, repr=False, slots=False)
class BadRequestError(ClientHTTPResponseError):
    """Raised when you send an invalid request somehow."""

    status: http.HTTPStatus = attrs.field(default=http.HTTPStatus.BAD_REQUEST, init=False)
    """The HTTP status code for the response."""

    errors: typing.Optional[typing.Mapping[str, data_binding.JSONObject]] = attrs.field(default=None, kw_only=True)
    """Dict of top level field names to field specific error paths.

    For more information, this error format is loosely defined at
    <https://discord.com/developers/docs/reference#error-messages> and is commonly
    returned for 50035 errors.
    """

    _cached_str: str = attrs.field(default=None, init=False)

    def __str__(self) -> str:
        if self._cached_str:
            return self._cached_str

        value = super().__str__()
        if self.errors:
            value += "\n\n"

            try:
                value += _dump_errors(self.errors).strip("\n")
            except KeyError:
                # Use the stdlib json.dumps here to be able to indent
                value += json.dumps(self.errors, indent=2)

        self._cached_str = value
        return value


@attrs.define(auto_exc=True, repr=False, slots=False)
class UnauthorizedError(ClientHTTPResponseError):
    """Raised when you are not authorized to access a specific resource."""

    status: http.HTTPStatus = attrs.field(default=http.HTTPStatus.UNAUTHORIZED, init=False)
    """The HTTP status code for the response."""


@attrs.define(auto_exc=True, repr=False, slots=False)
class ForbiddenError(ClientHTTPResponseError):
    """Raised when you are not allowed to access a specific resource.

    This means you lack the permissions to do something, either because of
    permissions set in a guild, or because your application is not whitelisted
    to use a specific endpoint.
    """

    status: http.HTTPStatus = attrs.field(default=http.HTTPStatus.FORBIDDEN, init=False)
    """The HTTP status code for the response."""


@attrs.define(auto_exc=True, repr=False, slots=False)
class NotFoundError(ClientHTTPResponseError):
    """Raised when something is not found."""

    status: http.HTTPStatus = attrs.field(default=http.HTTPStatus.NOT_FOUND, init=False)
    """The HTTP status code for the response."""


@attrs.define(auto_exc=True, kw_only=True, repr=False, slots=False)
class RateLimitTooLongError(HTTPError):
    """Internal error raised if the wait for a rate limit is too long.

    This is similar to [`asyncio.TimeoutError`][] in the way that it is used,
    but this will be raised pre-emptively and immediately if the period
    of time needed to wait is greater than a user-defined limit.

    This will almost always be route-specific. If you receive this, it is
    unlikely that performing the same call for a different channel/guild/user
    will also have this rate limit.
    """

    route: routes.CompiledRoute = attrs.field()
    """The route that produced this error."""

    is_global: bool = attrs.field()
    """Whether the ratelimit is global."""

    retry_after: float = attrs.field()
    """How many seconds to wait before you can retry this specific request."""

    max_retry_after: float = attrs.field()
    """How long the client is allowed to wait for at a maximum before raising."""

    reset_at: float = attrs.field()
    """UNIX timestamp of when this limit will be lifted."""

    limit: typing.Optional[int] = attrs.field()
    """The maximum number of calls per window for this rate limit, if known."""

    period: typing.Optional[float] = attrs.field()
    """How long the rate limit window lasts for from start to end, if known."""

    message: str = attrs.field(init=False)
    """The error message."""

    @message.default
    def _(self) -> str:
        return (
            "The request has been rejected, as you would be waiting for more than "
            f"the max retry-after ({self.max_retry_after}) on route '{self.route}' "
            f"[is_global={self.is_global}]"
        )

    # This may support other types of limits in the future, this currently
    # exists to be self-documenting to the user and for future compatibility
    # only.
    @property
    def remaining(self) -> typing.Literal[0]:
        """Remaining requests in this window.

        This will always be `0` symbolically.
        """
        return 0

    def __str__(self) -> str:
        return self.message


@attrs.define(auto_exc=True, repr=False, slots=False)
class InternalServerError(HTTPResponseError):
    """Base exception for an erroneous HTTP response that is a server error.

    All exceptions derived from this base should be treated as 5xx server
    errors when encountered. If you get one of these, it is not your fault!
    """


@attrs.define(auto_exc=True, repr=False, init=False, slots=False)
class MissingIntentWarning(HikariWarning):
    """Warning raised when subscribing to an event that cannot be fired.

    This is caused by your application missing certain intents.
    """


@attrs.define(auto_exc=True, repr=False, slots=False)
class BulkDeleteError(HikariError):
    """Exception raised when a bulk delete fails midway through a call.

    This will contain the list of message items that failed to be deleted,
    and will have a cause containing the initial exception.
    """

    deleted_messages: snowflakes.SnowflakeishSequence[messages.PartialMessage] = attrs.field()
    """Any message objects that were deleted before an exception occurred."""

    def __str__(self) -> str:
        return f"Error encountered when bulk deleting messages ({len(self.deleted_messages)} messages deleted)"


@attrs.define(auto_exc=True, repr=False, init=False, slots=False)
class VoiceError(HikariError):
    """Error raised when a problem occurs with the voice subsystem."""


@attrs.define(auto_exc=True, repr=False, slots=False)
class MissingIntentError(HikariError, ValueError):
    """Error raised when you try to perform an action without an intent.

    This is usually raised when querying the cache for something that is
    unavailable due to certain intents being disabled.
    """

    intents: intents_.Intents = attrs.field()
    """The combination of intents that are missing."""

    def __str__(self) -> str:
        return "You are missing the following intent(s): " + ", ".join(map(str, self.intents.split()))
