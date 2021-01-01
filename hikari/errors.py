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
    "ComponentNotRunningError",
    "NotFoundError",
    "RateLimitedError",
    "RateLimitTooLongError",
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
class ComponentNotRunningError(HikariError):
    """An exception thrown if trying to interact with a component that is not running."""

    reason: str = attr.ib()
    """A string to explain the issue."""

    def __str__(self) -> str:
        return self.reason


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
        # Appears to be some MyPy bug where == is expected to
        # return anything.
        return bool((self.value // 1000) == 1)


@attr.s(auto_exc=True, slots=True, repr=False, weakref_slot=False)
class GatewayConnectionError(GatewayError):
    """An exception thrown if a connection issue occurs."""

    def __str__(self) -> str:
        return f"Failed to connect to server: {self.reason!r}"


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

    UNKNOWN_ERROR = -1
    """Error is not known."""

    GENERAL_ERROR = 0
    """A general error, no further info provided."""

    UNKNOWN_APPLICATION = 10_002
    """Unknown application provided."""

    UNKNOWN_CHANNEL = 10_003
    """Unknown channel provided."""

    UNKNOWN_GUILD = 10_004
    """Unknown guild provided."""

    UNKNOWN_INTEGRATION = 10_005
    """Unknown integration provided."""

    UNKNOWN_INVITE = 10_006
    """Unknown invite provided."""

    UNKNOWN_MEMBER = 10_007
    """Unknown member provided."""

    UNKNOWN_MESSAGE = 10_008
    """Unknown message provided."""

    UNKNOWN_PERMISSION_OVERWRITE = 10_009
    """Unknown permission overwrite provided."""

    UNKNOWN_ROLE = 10_011
    """Unknown role provided."""

    UNKNOWN_USER = 10_013
    """Unknown user provided."""

    UNKNOWN_EMOJI = 10_014
    """Unknown emoji provided."""

    UNKNOWN_WEBHOOK = 10_015
    """Unknown webhook provided."""

    UNKNOWN_BAN = 10_026
    """Unknown ban provided."""

    ANNOUNCEMENT_LIMIT_HIT = 20_022
    """Message can not be edited due to announcement rate limits."""

    WRITE_LIMIT_HIT = 20_028
    """The global write limit on a channel has been hit."""

    MAXIMUM_GUILDS = 30_001
    """Maximum number of guilds reached (100)."""

    MAXIMUM_PINS = 30_003
    """Maximum number of pins reached for the channel (50)."""

    MAXIMUM_ROLES = 30_005
    """Maximum number of guild roles reached (250)."""

    MAXIMUM_WEBHOOKS = 30_007
    """Maximum number of webhooks in a channel reached (10)."""

    MAXIMUM_REACTIONS = 30_010
    """Maximum number of reactions on a message reached (20)."""

    MAXIMUM_CHANNELS = 30_013
    """Maximum number of guild channels reached (500)."""

    MAXIMUM_INVITES = 30_016
    """Maximum number of invites reached (1000)."""

    REQUEST_TOO_LARGE = 40_005
    """Request too large. Try sending something smaller in size."""

    TEMPORARILY_DISABLED = 40_006
    """This feature has been temporarily disabled server-side."""

    ALREADY_CROSSPOSTED = 40_033
    """This message has already been crossposted."""

    MISSING_ACCESS = 50_001
    """Missing access."""

    PROHIBITED_ON_DM = 50_003
    """Cannot execute action on a DM channel."""

    NOT_MESSAGE_AUTHOR = 50_005
    """Cannot edit a message authored by another user."""

    EMPTY_MESSAGE = 50_006
    """Cannot send an empty message."""

    USER_DM_CLOSED = 50_007
    """Cannot send messages to this user."""

    MESSAGE_IN_VC = 50_008
    """Cannot send messages in a voice channel."""

    CHANNEL_VERIFICATION_TOO_HIGH = 50_009
    """Channel verification level is too high for you to gain access."""

    PINS_ONLY_ON_ORIGIN_CHANNEL = 50_019
    """A message can only be pinned to the channel it was sent in."""

    INVALID_INVITE_CODE = 50_020
    """Invite code was either invalid or taken."""

    PROHIBITED_ON_SYSTEM_MESSAGE = 50_021
    """Cannot execute action on a system message."""

    INVALID_RECIPIENTS = 50_033
    """Invalid recipients."""

    MESSAGE_TOO_OLD = 50_034
    """A message provided was too old to bulk delete."""

    REQUIRED_CHANNEL = 50_074
    """Cannot delete a channel required for community guilds."""

    REACTION_BLOCKED = 90_001
    """The reaction was blocked."""

    TWO_FACTOR_AUTHENTICATION_REQUIRED = 60_003
    """2FA is required to use this endpoint."""

    SYSTEM_OVERLOADED = 130_000
    """API resource is currently overloaded. Try again a little later."""


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

    route: routes.CompiledRoute = attr.ib()
    """The route that produced this error."""

    retry_after: float = attr.ib()
    """How many seconds to wait before you can reuse the route with the specific request."""

    status: http.HTTPStatus = attr.ib(default=http.HTTPStatus.TOO_MANY_REQUESTS, init=False)
    """The HTTP status code for the response."""

    message: str = attr.ib(init=False)
    """The error message."""

    @message.default
    def _(self) -> str:
        return f"You are being rate-limited for {self.retry_after:,} seconds on route {self.route}. Please slow down!"


@attr.s(auto_exc=True, kw_only=True, slots=True, repr=False, weakref_slot=False)
class RateLimitTooLongError(HTTPError):
    """Internal error raised if the wait for a rate limit is too long.

    This is similar to `asyncio.TimeoutError` in the way that it is used,
    but this will be raised pre-emptively and immediately if the period
    of time needed to wait is greater than a user-defined limit.

    This will almost always be route-specific. If you receive this, it is
    unlikely that performing the same call for a different channel/guild/user
    will also have this rate limit.
    """

    route: routes.CompiledRoute = attr.ib()
    """The route that produced this error."""

    retry_after: float = attr.ib()
    """How many seconds to wait before you can retry this specific request."""

    max_retry_after: float = attr.ib()
    """How long the client is allowed to wait for at a maximum before raising."""

    reset_at: float = attr.ib()
    """UNIX timestamp of when this limit will be lifted."""

    limit: int = attr.ib()
    """The maximum number of calls per window for this rate limit."""

    period: float = attr.ib()
    """How long the rate limit window lasts for from start to end."""

    message: str = attr.ib(init=False)
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
    def remaining(self) -> typing.Literal[0]:  # noqa: D401 - Imperative mood
        """The number of requests that are remaining in this window.

        This will always be `0` symbolically.

        Returns
        -------
        builtins.int
            The number of requests remaining. Always `0`.
        """
        return 0

    def __str__(self) -> str:
        return self.message


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

    messages_deleted: snowflakes.SnowflakeishSequence[messages.PartialMessage] = attr.ib()
    """Any message objects that were deleted before an exception occurred."""

    messages_skipped: snowflakes.SnowflakeishSequence[messages.PartialMessage] = attr.ib()
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
        return "You are missing the following intent(s): " + ", ".join(map(str, self.intents.split()))
