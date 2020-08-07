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
"""Utility methods used for parsing timestamps and datetimes from Discord."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "DISCORD_EPOCH",
    "rfc7231_datetime_string_to_datetime",
    "datetime_to_discord_epoch",
    "discord_epoch_to_datetime",
    "unix_epoch_to_datetime",
    "Intervalish",
    "timespan_to_int",
    "local_datetime",
    "utc_datetime",
    "monotonic",
    "monotonic_ns",
    "uuid",
]

import datetime
import email.utils
import re
import time
import typing
import uuid as uuid_

Intervalish = typing.Union[int, float, datetime.timedelta]
"""Type hint representing a naive time period or time span.

This is a type that is like an interval of some sort.

This is an alias for `typing.Union[int, float, datetime.datetime]`,
where `builtins.int` and `builtins.float` types are interpreted as a number of seconds.
"""

DISCORD_EPOCH: typing.Final[int] = 1_420_070_400
"""Discord epoch used within snowflake identifiers.

This is defined as the number of seconds between
`1/1/1970 00:00:00 UTC` and `1/1/2015 00:00:00 UTC`.

References
----------
* [Discord API documentation - Snowflakes](https://discord.com/developers/docs/reference#snowflakes)
"""

_ISO_8601_DATE: typing.Final[typing.Pattern[str]] = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
_ISO_8601_TIME: typing.Final[typing.Pattern[str]] = re.compile(r"T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?", re.I)
_ISO_8601_TZ: typing.Final[typing.Pattern[str]] = re.compile(r"([+-])(\d{2}):(\d{2})$")


def rfc7231_datetime_string_to_datetime(date_str: str, /) -> datetime.datetime:
    """Return the HTTP date as a datetime object.

    Parameters
    ----------
    date_str : builtins.str
        The RFC-2822 (section 3.3) compliant date string to parse.

    Returns
    -------
    datetime.datetime
        The HTTP date as a datetime object.

    References
    ----------
    * [RFC-2822](https://www.ietf.org/rfc/rfc2822.txt)
    * [Mozilla documentation for `Date` HTTP header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Date)
    """
    # According to Mozilla, these are always going to be GMT (which is UTC).
    return email.utils.parsedate_to_datetime(date_str).replace(tzinfo=datetime.timezone.utc)


def iso8601_datetime_string_to_datetime(date_string: str, /) -> datetime.datetime:
    """Parse an ISO 8601 date string into a `datetime.datetime` object.

    Parameters
    ----------
    date_string : builtins.str
        The ISO-8601 compliant date string to parse.

    Returns
    -------
    datetime.datetime
        The ISO-8601 date string as a datetime object.

    References
    ----------
    * [ISO-8601](https://en.wikipedia.org/wiki/ISO_8601)
    """
    year, month, day = map(int, _ISO_8601_DATE.findall(date_string)[0])

    time_part = _ISO_8601_TIME.findall(date_string)[0]
    hour, minute, second, partial = time_part

    # Pad the millisecond part if it is not in microseconds, otherwise Python will complain.
    partial = partial + (6 - len(partial)) * "0"
    hour, minute, second, partial = int(hour), int(minute), int(second), int(partial)
    if date_string.endswith(("Z", "z")):
        timezone = datetime.timezone.utc
    else:
        sign, tz_hour, tz_minute = _ISO_8601_TZ.findall(date_string)[0]
        tz_hour, tz_minute = int(tz_hour), int(tz_minute)
        offset = datetime.timedelta(hours=tz_hour, minutes=tz_minute)
        if sign == "-":
            offset = -offset
        timezone = datetime.timezone(offset)

    return datetime.datetime(year, month, day, hour, minute, second, partial, timezone)


def discord_epoch_to_datetime(epoch: int, /) -> datetime.datetime:
    """Parse a Discord epoch into a `datetime.datetime` object.

    Parameters
    ----------
    epoch : builtins.int
        Number of milliseconds since `1/1/2015 00:00:00 UTC`.

    Returns
    -------
    datetime.datetime
        Number of seconds since `1/1/1970 00:00:00 UTC`.
    """
    return datetime.datetime.fromtimestamp(epoch / 1_000 + DISCORD_EPOCH, datetime.timezone.utc)


def datetime_to_discord_epoch(timestamp: datetime.datetime) -> int:
    """Parse a `datetime.datetime` object into an `builtins.int` `DISCORD_EPOCH` offset.

    Parameters
    ----------
    timestamp : datetime.datetime
        Number of seconds since `1/1/1970 00:00:00 UTC`.

    Returns
    -------
    builtins.int
        Number of milliseconds since `1/1/2015 00:00:00 UTC`.
    """
    return int((timestamp.timestamp() - DISCORD_EPOCH) * 1_000)


def unix_epoch_to_datetime(epoch: typing.Union[int, float], /, *, is_millis: bool = True) -> datetime.datetime:
    """Parse a UNIX epoch to a `datetime.datetime` object.

    !!! note
        If an epoch that's outside the range of what this system can handle,
        this will return `datetime.datetime.max` if the timestamp is positive,
        or `datetime.datetime.min` otherwise.

    Parameters
    ----------
    epoch : builtins.int or builtins.float
        Number of seconds/milliseconds since `1/1/1970 00:00:00 UTC`.
    is_millis : builtins.bool
        `builtins.True` by default, indicates the input timestamp is measured in
        milliseconds rather than seconds

    Returns
    -------
    datetime.datetime
        Number of seconds since `1/1/1970 00:00:00 UTC`.
    """
    # Datetime seems to raise an OSError when you try to convert an out of range timestamp on Windows and a ValueError
    # if you try on a UNIX system so we want to catch both.
    try:
        epoch /= (is_millis * 1_000) or 1
        return datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc)
    except (OSError, ValueError):
        if epoch > 0:
            return datetime.datetime.max
        else:
            return datetime.datetime.min


def timespan_to_int(value: Intervalish, /) -> int:
    """Cast the given timespan in seconds to an integer value.

    Parameters
    ----------
    value : TimeSpan
        The number of seconds.

    Returns
    -------
    builtins.int
        The integer number of seconds. Fractions are discarded. Negative values
        are removed.
    """
    if isinstance(value, datetime.timedelta):
        value = value.total_seconds()
    return int(max(0, value))


def local_datetime() -> datetime.datetime:
    """Return the current date/time for the system's time zone."""
    return utc_datetime().astimezone()


def utc_datetime() -> datetime.datetime:
    """Return the current date/time for UTC (GMT+0)."""
    return datetime.datetime.now(tz=datetime.timezone.utc)


# date.monotonic_ns is no slower than time.monotonic, but is more accurate.
# Also, fun fact that monotonic_ns appears to be 1µs faster on average than
# monotonic on AARM64 architectures, but on x86, monotonic is around 1ns faster
# than monotonic_ns. Just thought that was kind of interesting to note down.
# (RPi 3B versus i7 6700)

# time.perf_counter and time.perf_counter_ns dont have proper typehints, causing
# pdoc to not be able to recognice them. This is just a little hack around that.
def monotonic() -> float:
    """Performance counter for benchmarking."""  # noqa: D401 - Imperative mood
    return time.perf_counter()


def monotonic_ns() -> int:
    """Performance counter for benchmarking as nanoseconds."""  # noqa: D401 - Imperative mood
    return time.perf_counter_ns()


def uuid() -> str:
    """Generate a unique UUID (1ns precision)."""
    return uuid_.uuid1(None, monotonic_ns()).hex
