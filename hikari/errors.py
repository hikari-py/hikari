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
    "RESTErrorCode",
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


@typing.final
class RESTErrorCode(int, enums.Enum):
    """Non-exhaustive enum of error codes provided as further info on errors returned by the REST API."""

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

    UNKNOWN_GUILD_TEMPLATE = 10_057
    """Unknown guild template provided."""

    UNKNOWN_STICKER = 10_060
    """Unknown sticker provided."""

    UNKNOWN_INTERACTION = 10_062
    """Unknown interaction provided."""

    UNKNOWN_APPLICATION_COMMAND = 10_063
    """Unknown application command provided."""

    UNKNOWN_APPLICATION_COMMAND_PERMISSIONS = 10_066
    """Unknown application command permissions provided."""

    UNKNOWN_STAGE_INSTANCE = 10_067
    """Unknown stage instance provided."""

    UNKNOWN_GUILD_WELCOME_SCREEN = 10_069
    """Unknown guild welcome screen provided."""

    EXPLICIT_CONTENT_BLOCKED = 20_009
    """Explicit content cannot be sent to the desired recipient(s)."""

    ANNOUNCEMENT_LIMIT_HIT = 20_022
    """Message can not be edited due to announcement rate limits."""

    WRITE_LIMIT_HIT = 20_028
    """The global write limit on a channel has been hit."""

    DISALLOWED_WORDS_FOR_PUBLIC_STAGES = 20_031
    """The guild contains disallowed words for public stages.

    This may include guild name, guild description or channel names.
    """

    GUILD_PREMIUM_LEVEL_TOO_LOW = 20_035
    """The guilds premium level is too low."""

    MAXIMUM_GUILDS = 30_001
    """Maximum number of guilds reached (100)."""

    MAXIMUM_PINS = 30_003
    """Maximum number of pins reached for the channel (50)."""

    MAXIMUM_RECIPIENTS = 30_004
    """Maximum number of recipients reached (10)."""

    MAXIMUM_ROLES = 30_005
    """Maximum number of guild roles reached (250)."""

    MAXIMUM_WEBHOOKS = 30_007
    """Maximum number of webhooks in a channel reached (10)."""

    MAXIMUM_EMOJIS = 30_008
    """Maximum number of emojis reached."""

    MAXIMUM_REACTIONS = 30_010
    """Maximum number of reactions on a message reached (20)."""

    MAXIMUM_CHANNELS = 30_013
    """Maximum number of guild channels reached (500)."""

    MAXIMUM_INVITES = 30_016
    """Maximum number of invites reached (1000)."""

    MAXIMUM_ANIMATED_EMOJIS = 30_018
    """Maximum number of animated emojis reached."""

    MAXIMUM_NUMBER_OF_GUILD_MEMBERS_REACHED = 30_019
    """Maximum number of guild members reached."""

    GUILD_ALREADY_HAS_TEMPLATE = 30_031
    """Guild already has a template."""

    MAXIMUM_NUMBER_OF_THREAD_PARTICIPANTS_REACHED = 30_033
    """Maximum number of thread participants reached."""

    MAXIMUM_BANS_FOR_NON_GUILD_MEMBERS = 30_035
    """Maximum number of bans for non-guild members reached."""

    MAXIMUM_NUMBER_OF_STICKERS_REACHED = 30_037
    """Maximum number of stickers reached."""

    MAXIMUM_PRUNE_REQUESTS_REACHED = 30_040
    """Maximum number of prune requests has been reached. Try again later."""

    REQUEST_TOO_LARGE = 40_005
    """Request too large. Try sending something smaller in size."""

    TEMPORARILY_DISABLED = 40_006
    """This feature has been temporarily disabled server-side."""

    USER_BANNED = 40_003
    """The user is banned from this guild."""

    ALREADY_CROSSPOSTED = 40_033
    """This message has already been crossposted."""

    APPLICATION_COMMAND_ALREADY_EXISTS = 40_041
    """An application command with that name already exists."""

    INVALID_ACCOUNT_TYPE = 50_002
    """Invalid account type."""

    PROHIBITED_ON_DM = 50_003
    """Cannot execute action on a DM channel."""

    GUILD_WIDGET_DISABLED = 50_004
    """Guild widget disabled."""

    NOT_MESSAGE_AUTHOR = 50_005
    """Cannot edit a message created by another user."""

    EMPTY_MESSAGE = 50_006
    """Cannot send an empty message."""

    USER_DM_CLOSED = 50_007
    """Cannot send messages to this user."""

    MESSAGE_IN_VC = 50_008
    """Cannot send messages in a voice channel."""

    PINS_ONLY_ON_ORIGIN_CHANNEL = 50_019
    """A message can only be pinned to the channel it was sent in."""

    INVALID_INVITE_CODE = 50_020
    """Invite code was either invalid or taken."""

    PROHIBITED_ON_SYSTEM_MESSAGE = 50_021
    """Cannot execute action on a system message."""

    PROHIBITED_ON_CHANNEL_TYPE = 50_024
    """Cannot execute action on this channel type."""

    INVALID_OAUTH2_TOKEN = 50_025
    """Invalid OAuth2 access token provided."""

    MISSING_REQUIRED_OAUTH2_SCOPE = 50_026
    """Missing required OAuth2 scope."""

    INVALID_ROLE = 50_028
    """Invalid role."""

    INVALID_RECIPIENTS = 50_033
    """Invalid recipients."""

    MESSAGE_TOO_OLD = 50_034
    """A message provided was too old to bulk delete."""

    REQUIRED_CHANNEL = 50_074
    """Cannot delete a channel required for community guilds."""

    NO_USERS_WITH_TAG = 80_004
    """No users with this tag exist."""

    REACTION_BLOCKED = 90_001
    """The reaction was blocked."""

    TWO_FACTOR_AUTHENTICATION_REQUIRED = 60_003
    """2FA is required to use this endpoint."""

    SYSTEM_OVERLOADED = 130_000
    """API resource is currently overloaded. Try again a little later."""

    STAGE_ALREADY_OPEN = 150_006
    """The stage channel is already open."""


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

    code: typing.Union[RESTErrorCode, int] = attr.field(default=RESTErrorCode.GENERAL_ERROR)
    """The error code."""

    def __str__(self) -> str:
        name = self.status.name.replace("_", " ").title()
        name_value = f"{name} {self.status.value}"

        if isinstance(self.code, RESTErrorCode) and self.code != RESTErrorCode.GENERAL_ERROR:
            code_str = f" ({self.code.name})"
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
