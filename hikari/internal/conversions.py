#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""Basic transformation utilities."""

from __future__ import annotations

__all__ = [
    "nullable_cast",
    "try_cast",
    "try_cast_or_defer_unary_operator",
    "put_if_specified",
    "parse_http_date",
    "parse_iso_8601_ts",
    "discord_epoch_to_datetime",
    "unix_epoch_to_datetime",
    "pluralize",
    "resolve_signature",
    "EMPTY",
    "cast_to_str_id",
    "timespan_as_int",
]

import contextlib
import datetime
import email.utils
import inspect
import re
import typing

from hikari.models import unset

if typing.TYPE_CHECKING:
    import enum

    IntFlagT = typing.TypeVar("IntFlagT", bound=enum.IntFlag)
    RawIntFlagValueT = typing.Union[typing.AnyStr, typing.SupportsInt, int]
    CastInputT = typing.TypeVar("CastInputT")
    CastOutputT = typing.TypeVar("CastOutputT")
    DefaultT = typing.TypeVar("DefaultT")
    TypeCastT = typing.Callable[[CastInputT], CastOutputT]
    ResultT = typing.Union[CastOutputT, DefaultT]

DISCORD_EPOCH: typing.Final[int] = 1_420_070_400
ISO_8601_DATE_PART: typing.Final[typing.Pattern] = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
ISO_8601_TIME_PART: typing.Final[typing.Pattern] = re.compile(r"T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?", re.I)
ISO_8601_TZ_PART: typing.Final[typing.Pattern] = re.compile(r"([+-])(\d{2}):(\d{2})$")


def nullable_cast(value: CastInputT, cast: TypeCastT, /) -> ResultT:
    """Attempt to cast the given `value` with the given `cast`.

    This will only succeed if `value` is not `None`. If it is `None`, then
    `None` is returned instead.
    """
    if value is None:
        return None
    return cast(value)


def try_cast(value: CastInputT, cast: TypeCastT, default: DefaultT = None, /) -> ResultT:
    """Try to cast the given value to the given cast.

    If it throws a `Exception` or derivative, it will return `default`
    instead of the cast value instead.
    """
    with contextlib.suppress(Exception):
        return cast(value)
    return default


def try_cast_or_defer_unary_operator(type_: typing.Type, /):
    """Return a unary operator that will try to cast the given input to the type provided.

    Parameters
    ----------
    type_ : typing.Callable[..., `output type`]
        The type to cast to.
    """
    return lambda data: try_cast(data, type_, data)


def put_if_specified(
    mapping: typing.Dict[typing.Hashable, typing.Any],
    key: typing.Hashable,
    value: typing.Any,
    type_after: typing.Optional[TypeCastT] = None,
    /,
) -> None:
    """Add a value to the mapping under the given key as long as the value is not `...`.

    Parameters
    ----------
    mapping : typing.Dict[typing.Hashable, typing.Any]
        The mapping to add to.
    key : typing.Hashable
        The key to add the value under.
    value : typing.Any
        The value to add.
    type_after : typing.Callable[[`input type`], `output type`] | None
        Type to apply to the value when added.
    """
    if value is not unset.UNSET:
        if type_after:
            mapping[key] = type_after(value)
        else:
            mapping[key] = value


def parse_http_date(date_str: str, /) -> datetime.datetime:
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
    [RFC 2822](https://www.ietf.org/rfc/rfc2822.txt)
    [Mozilla documentation for Date header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Date)
    """
    # According to Mozilla, these are always going to be GMT (which is UTC).
    return email.utils.parsedate_to_datetime(date_str).replace(tzinfo=datetime.timezone.utc)


def parse_iso_8601_ts(date_string: str, /) -> datetime.datetime:
    """Parse an ISO 8601 date string into a `datetime.datetime` object.

    Parameters
    ----------
    date_string : str
        The ISO 8601 compliant date string to parse.

    Returns
    -------
    datetime.datetime
        The ISO 8601 date string as a datetime object.

    References
    ----------
    [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601)
    """
    year, month, day = map(int, ISO_8601_DATE_PART.findall(date_string)[0])

    time_part = ISO_8601_TIME_PART.findall(date_string)[0]
    hour, minute, second, partial = time_part

    # Pad the millisecond part if it is not in microseconds, otherwise Python will complain.
    partial = partial + (6 - len(partial)) * "0"
    hour, minute, second, partial = int(hour), int(minute), int(second), int(partial)
    if date_string.endswith(("Z", "z")):
        timezone = datetime.timezone.utc
    else:
        sign, tz_hour, tz_minute = ISO_8601_TZ_PART.findall(date_string)[0]
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
        Number of milliseconds since 1/1/2015 (UTC)

    Returns
    -------
    datetime.datetime
        Number of seconds since 1/1/1970 within a datetime object (UTC).
    """
    return datetime.datetime.fromtimestamp(epoch / 1000 + DISCORD_EPOCH, datetime.timezone.utc)


def unix_epoch_to_datetime(epoch: int, /) -> datetime.datetime:
    """Parse a UNIX epoch to a `datetime.datetime` object.

    Parameters
    ----------
    epoch : int
        Number of milliseconds since 1/1/1970 (UTC)

    Returns
    -------
    datetime.datetime
        Number of seconds since 1/1/1970 within a datetime object (UTC).

    !!! note
        If an epoch that's outside the range of what this system can handle,
        this will return `datetime.datetime.max` or `datetime.datetime.min`.
    """
    try:
        return datetime.datetime.fromtimestamp(epoch / 1000, datetime.timezone.utc)
    # Datetime seems to raise an OSError when you try to convert an out of range timestamp on Windows and a ValueError
    # if you try on a UNIX system so we want to catch both.
    except (OSError, ValueError):
        if epoch > 0:
            return datetime.datetime.max
        else:
            return datetime.datetime.min


def pluralize(count: int, name: str, suffix: str = "s") -> str:
    """Pluralizes a word."""
    return f"{count} {name + suffix}" if count - 1 else f"{count} {name}"


EMPTY: typing.Final[inspect.Parameter.empty] = inspect.Parameter.empty
"""A singleton that empty annotations will be set to in `resolve_signature`."""


def resolve_signature(func: typing.Callable) -> inspect.Signature:
    """Get the `inspect.Signature` of `func` with resolved forward annotations.

    Parameters
    ----------
    func : typing.Callable[[...], ...]
        The function to get the resolved annotations from.

    Returns
    -------
    typing.Signature
        A `typing.Signature` object with all forward reference annotations
        resolved.
    """
    signature = inspect.signature(func)
    resolved_type_hints = None
    parameters = []
    for key, value in signature.parameters.items():
        if isinstance(value.annotation, str):
            if resolved_type_hints is None:
                resolved_type_hints = typing.get_type_hints(func)
            parameters.append(value.replace(annotation=resolved_type_hints[key]))
        else:
            parameters.append(value)
    signature = signature.replace(parameters=parameters)

    if isinstance(signature.return_annotation, str):
        if resolved_type_hints is None:
            return_annotation = typing.get_type_hints(func)["return"]
        else:
            return_annotation = resolved_type_hints["return"]
        signature = signature.replace(return_annotation=return_annotation)

    return signature


def cast_to_str_id(value: typing.Union[typing.SupportsInt, int]) -> str:
    """Cast the given object to an int and return the result as a string.

    Parameters
    ----------
    value : typing.SupportsInt | int
        A value that can be cast to an `int`.

    Returns
    -------
    str
        The string representation of the integer value.
    """
    return str(int(value))


def timespan_as_int(value: typing.Union[int, datetime.timedelta, float]) -> int:
    """Cast the given timespan in seconds to an integer value.

    Parameters
    ----------
    value : int | float | datetime.timedelta
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
