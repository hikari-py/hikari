#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Internal utilities and helper methods for network logic."""
import collections
import datetime
import email
import platform

#: Generic type variable describing "something or other". No one knows for sure what that something is. Perhaps no one
#: even cares...
from hikari.compat import typing

AnyT = typing.TypeVar("AnyT")


def get_from_map_as(mapping: dict, key: typing.Any, klazz: typing.Type[AnyT]) -> typing.Optional[AnyT]:
    """
    Get from a map and perform a type cast where possible.

    Args:
        mapping:
            dict to read from.
        key:
            key to access.
        klazz:
            type to cast to if required.

    Returns:
        An optional casted value, or `None` if it wasn't in the `mapping` at the start.
    """
    raw = mapping.get(key)
    if isinstance(raw, klazz):
        return raw
    elif raw is None:
        return None
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


#: Type type of a body for a Gateway or HTTP request and response.
#:
#: This is a :class:`builtins.dict` of :class:`builtins.str` keys that map to any value. Since the :module:`hikari.net`
#: module does not enforce concrete models for values sent and received, mappings are passed around to represent request
#: and response data. This allows an implementation to use this layer as desired.
RequestBody = typing.Dict[str, typing.Any]


#: The signature of an event dispatcher function. Consumes two arguments. The first is an event name from the gateway,
#: the second is the payload which is assumed to always be a :class:`dict` with :class:`str` keys. This should be
#: a coroutine function; if it is not, it should be expected to be promoted to a coroutine function internally.
#:
#: Example:
#:     >>> async def on_dispatch(event: str, payload: Dict[str, Any]) -> None:
#:     ...     logger.info("Dispatching %s with payload %r", event, payload)
DispatchHandler = typing.Callable[[str, typing.Dict[str, typing.Any]], typing.Union[None, typing.Awaitable[None]]]
