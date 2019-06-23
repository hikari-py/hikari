#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Internal utilities and helper methods for network logic."""
__all__ = (
    "APIResource",
    "DiscordObject",
    "DispatchHandler",
    "FileLike",
    "get_from_map_as",
    "library_version",
    "link_developer_portal",
    "parse_http_date",
    "parse_rate_limit_headers",
    "python_version",
    "Resource",
    "system_type",
    "unspecified",
    "user_agent",
)

import _io
import collections
import datetime
import email
import enum
import inspect
import io
import platform

from hikari.compat import typing

_T = typing.TypeVar("_T")


def get_from_map_as(
    mapping: dict, key: typing.Any, klazz: typing.Type[_T], default=None, *, default_on_error=False
) -> typing.Optional[_T]:
    """
    Get from a map and perform a type cast where possible.

    Args:
        mapping:
            dict to read from.
        key:
            key to access.
        klazz:
            type to cast to if required.
        default:
            default value to return, or `None` if unspecified.
        default_on_error:
            If `True`, any error occuring whilst casting will be suppressed and the default value will be returned.
            If `False`, as per the default, it will raise the error.

    Returns:
        An optional casted value, or `None` if it wasn't in the `mapping` at the start.
    """
    raw = mapping.get(key)
    if isinstance(raw, klazz):
        return raw
    elif raw is None:
        return default
    elif default_on_error:
        try:
            return klazz(raw)
        except Exception:
            return default
    else:
        return klazz(raw)


def parse_http_date(date_str: str) -> datetime.datetime:
    """
    Return the HTTP date as a datetime object.

    Args:
        date_str:
            The RFC-2822 (section 3.3) compliant date string to parse.

    See:
        https://www.ietf.org/rfc/rfc2822.txt
    """
    return email.utils.parsedate_to_datetime(date_str)


#: Parsed rate-limit information.
#: Args:
#:     now:
#:          The current system time when this stamp was made.
#:     reset:
#:          The epoch at which the limit resets.
#:     remain:
#:          The number of slots remaining in the ratelimit window.
#:     total:
#:          The total number of slots in the window.
HTTPRateLimit = collections.namedtuple("HTTPRateLimit", "now reset remain total")


def parse_rate_limit_headers(headers: dict) -> HTTPRateLimit:
    """
    Extract rate-limiting information from headers.

    Args:
        headers:
            The dict of response headers to parse.

    Returns:
        The rate limit information in a tuple of :class:`HTTPRateLimit` where fields may
        be `None` if not present in the headers.
    """
    now = parse_http_date(headers["Date"])
    reset = get_from_map_as(headers, "X-RateLimit-Reset", float)
    remain = get_from_map_as(headers, "X-RateLimit-Remain", int)
    total = get_from_map_as(headers, "X-RateLimit-Total", int)

    if reset is not None:
        reset = datetime.datetime.fromtimestamp(reset, datetime.timezone.utc)

    return HTTPRateLimit(now, reset, remain, total)


def library_version() -> str:
    """
    Creates a string that is representative of the version of this library.

    Example:
        hikari 0.0.1a1
    """
    from hikari import __version__

    return f"hikari v{__version__}"


def python_version() -> str:
    """
    Creates a comprehensive string representative of this version of Python, along with the compiler used, if present.

    Examples:
        CPython3.7:
            CPython 3.7.3 GCC 8.2.1 20181127
        PyPy3.6:
            PyPy 3.6.1 release-pypy3.6-v7.1.1
    """
    attrs = [
        platform.python_implementation(),
        platform.python_version(),
        platform.python_branch(),
        platform.python_compiler(),
    ]
    return " ".join(a for a in attrs if a.strip())


def system_type() -> str:
    """
    Get a string representing the system type.
    """
    # Might change this eventually to be more detailed, who knows.
    return platform.system()


def user_agent() -> str:
    """
    Creates a User-Agent header string acceptable by the API.

    Examples:
        CPython3.7:
            DiscordBot (https://gitlab.com/nekokatt/hikari, 0.0.1a) CPython 3.7.3 GCC 8.2.1 20181127 Linux
        PyPy3.6:
            DiscordBot (https://gitlab.com/nekokatt/hikari, 0.0.1a) PyPy 3.6.1 release-pypy3.6-v7.1.1 Linux
    """
    from hikari import __version__, __url__

    system = system_type()
    python = python_version()
    return f"DiscordBot ({__url__}, {__version__}) {python} {system}"


#: Type type of a body for a Gateway or HTTP request and response.
#:
#: This is a :class:`builtins.dict` of :class:`builtins.str` keys that map to any value. Since the :mod:`hikari.net`
#: module does not enforce concrete models for values sent and received, mappings are passed around to represent request
#: and response data. This allows an implementation to use this layer as desired.
DiscordObject = typing.Dict[str, typing.Any]

#: The signature of an event dispatcher function. Consumes two arguments. The first is an event name from the gateway,
#: the second is the payload which is assumed to always be a :class:`dict` with :class:`str` keys. This should be
#: a coroutine function; if it is not, it should be expected to be promoted to a coroutine function internally.
#:
#: Example:
#:     >>> async def on_dispatch(event: str, payload: Dict[str, Any]) -> None:
#:     ...     logger.info("Dispatching %s with payload %r", event, payload)
DispatchHandler = typing.Callable[[str, typing.Dict[str, typing.Any]], typing.Union[None, typing.Awaitable[None]]]


#: An object that can be considered to be file-like.
FileLike = typing.Union[
    bytes,
    bytearray,
    memoryview,
    str,
    io.IOBase,
    io.StringIO,
    io.BytesIO,
    io.BufferedRandom,
    io.BufferedReader,
    io.BufferedRWPair,
]


class Resource:
    """
    Represents an HTTP request in a format that can be passed around atomically.

    Also provides a mechanism to handle producing a rate limit identifier.

    Note:
        Comparisons of this object occur on the bucket
    """

    __slots__ = ("method", "path", "params", "bucket", "uri")

    def __init__(self, base_uri, method, path, **kwargs):
        #: The HTTP method to use (always upper-case)
        self.method = method.upper()
        #: The HTTP path to use (this can contain format-string style placeholders).
        self.path = path
        #: Any parameters to later interpolate into `path`.
        self.params = kwargs
        #: The bucket. This is a combination of the method, uninterpolated path, and optional `webhook_id`, `guild_id`
        #: and `channel_id`, and is how the hash code for this route is produced. The hash code is used to determine
        #: the bucket to use for local rate limiting in the HTTP component.
        self.bucket = "{0.method} {0.path} {0.webhook_id} {0.guild_id} {0.channel_id}".format(self)
        #: The full URI to use.
        self.uri = base_uri + path.format(**kwargs)

    #: The webhook ID, or `None` if it is not present.
    webhook_id = property(lambda self: self.params.get("webhook_id"))
    #: The guild ID, or `None` if it is not present.
    guild_id = property(lambda self: self.params.get("guild_id"))
    #: The channel ID, or `None` if it is not present.
    channel_id = property(lambda self: self.params.get("channel_id"))

    def __hash__(self):
        return hash(self.bucket)

    def __eq__(self, other) -> bool:
        return isinstance(other, Resource) and hash(self) == hash(other)


class APIResource(enum.Enum):
    """A documentation resource for the underlying API."""

    AUDIT_LOG = "/resources/audit-log"
    CHANNEL = "/resources/channel"
    EMOJI = "/resources/emoji"
    GUILD = "/resources/guild"
    INVITE = "/resources/invite"
    OAUTH2 = "/topics/oauth2"
    USER = "/resources/user"
    VOICE = "/resources/voice"
    WEBHOOK = "/resources/webhook"


def link_developer_portal(scope: APIResource, specific_resource: str = None):
    """Injects some common documentation into the given member's docstring."""

    def decorator(obj):
        BASE_URL = "https://discordapp.com/developers/docs"
        doc = inspect.cleandoc(inspect.getdoc(obj) or "")
        base_resource = BASE_URL + scope.value
        frag = obj.__name__.lower().replace("_", "-") if specific_resource is None else specific_resource
        uri = base_resource + "#" + frag

        setattr(obj, "__doc__", f"Read the documentation on `Discord's developer portal <{uri}>`_.\n\n{doc}")
        return obj

    return decorator


class _Unspecified:
    __slots__ = ()

    def __str__(self):
        return "unspecified"

    __repr__ = __str__


#: An attribute that is unspecified by default.
unspecified = _Unspecified()
