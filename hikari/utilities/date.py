# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""Utility methods used for parsing timestamps and datetimes from Discord."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = [
    "DISCORD_EPOCH",
    "rfc7231_datetime_string_to_datetime",
    "datetime_to_discord_epoch",
    "discord_epoch_to_datetime",
    "unix_epoch_to_datetime",
    "TimeSpan",
    "timespan_to_int",
]

import datetime
import email.utils
import re
import typing


TimeSpan = typing.Union[int, float, datetime.timedelta]
"""Type hint representing a naive time period or time span.

This is an alias for `typing.Union[int, float, datetime.datetime]`,
where `int` and `float` types are interpreted as a number of seconds.
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
    date_str : str
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
    date_string : str
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
    epoch : int
        Number of milliseconds since `1/1/2015 00:00:00 UTC`.

    Returns
    -------
    datetime.datetime
        Number of seconds since `1/1/1970 00:00:00 UTC`.
    """
    return datetime.datetime.fromtimestamp(epoch / 1_000 + DISCORD_EPOCH, datetime.timezone.utc)


def datetime_to_discord_epoch(timestamp: datetime.datetime) -> int:
    """Parse a `datetime.datetime` object into an `int` `DISCORD_EPOCH` offset.

    Parameters
    ----------
    timestamp : datetime.datetime
        Number of seconds since `1/1/1970 00:00:00 UTC`.

    Returns
    -------
    int
        Number of milliseconds since `1/1/2015 00:00:00 UTC`.
    """
    return int((timestamp.timestamp() - DISCORD_EPOCH) * 1_000)


def unix_epoch_to_datetime(epoch: int, /) -> datetime.datetime:
    """Parse a UNIX epoch to a `datetime.datetime` object.

    Parameters
    ----------
    epoch : int
        Number of milliseconds since `1/1/1970 00:00:00 UTC`.

    Returns
    -------
    datetime.datetime
        Number of seconds since `1/1/1970 00:00:00 UTC`.

    !!! note
        If an epoch that's outside the range of what this system can handle,
        this will return `datetime.datetime.max` if the timestamp is positive,
        or `datetime.datetime.min` otherwise.
    """
    # Datetime seems to raise an OSError when you try to convert an out of range timestamp on Windows and a ValueError
    # if you try on a UNIX system so we want to catch both.
    try:
        return datetime.datetime.fromtimestamp(epoch / 1000, datetime.timezone.utc)
    except (OSError, ValueError):
        if epoch > 0:
            return datetime.datetime.max
        else:
            return datetime.datetime.min


def timespan_to_int(value: TimeSpan, /) -> int:
    """Cast the given timespan in seconds to an integer value.

    Parameters
    ----------
    value : TimeSpan
        The number of seconds.

    Returns
    -------
    int
        The integer number of seconds. Fractions are discarded. Negative values
        are removed.
    """
    if isinstance(value, datetime.timedelta):
        value = value.total_seconds()
    return int(max(0, value))
