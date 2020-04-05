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
__all__ = [
    "CastInputT",
    "CastOutputT",
    "DefaultT",
    "TypeCastT",
    "ResultT",
    "nullable_cast",
    "try_cast",
    "put_if_specified",
    "image_bytes_to_image_data",
    "pluralize",
]

import base64
import contextlib
import datetime
import email.utils
import io
import re
import typing

CastInputT = typing.TypeVar("CastInputT")
CastOutputT = typing.TypeVar("CastOutputT")
DefaultT = typing.TypeVar("DefaultT")
TypeCastT = typing.Callable[[CastInputT], CastOutputT]
ResultT = typing.Union[CastOutputT, DefaultT]


def nullable_cast(value: CastInputT, cast: TypeCastT) -> ResultT:
    """Attempt to cast the given ``value`` with the given ``cast``.

    This will only succeed if ``value`` is not ``None``. If it is ``None``, then
    ``None`` is returned instead.
    """
    if value is None:
        return None
    return cast(value)


def try_cast(value: CastInputT, cast: TypeCastT, default: DefaultT = None) -> ResultT:
    """Try to cast the given value to the given cast.

    If it throws a :obj:`Exception` or derivative, it will return ``default``
    instead of the cast value instead.
    """
    with contextlib.suppress(Exception):
        return cast(value)
    return default


def put_if_specified(
    mapping: typing.Dict[typing.Hashable, typing.Any],
    key: typing.Hashable,
    value: typing.Any,
    type_after: typing.Optional[TypeCastT] = None,
) -> None:
    """Add a value to the mapping under the given key as long as the value is not ``...``.

    Parameters
    ----------
    mapping : :obj:`typing.Dict` [ :obj:`typing.Hashable`, :obj:`typing.Any` ]
        The mapping to add to.
    key : :obj:`typing.Hashable`
        The key to add the value under.
    value : :obj:`typing.Any`
        The value to add.
    type_after : :obj:`typing.Callable` [ [ ``input type`` ], ``output type`` ], optional
        Type to apply to the value when added.
    """
    if value is not ...:
        if type_after:
            mapping[key] = type_after(value)
        else:
            mapping[key] = value


def image_bytes_to_image_data(img_bytes: typing.Optional[bytes] = None) -> typing.Optional[str]:
    """Encode image bytes into an image data string.

    Parameters
    ----------
    img_bytes : :obj:`bytes`, optional
        The image bytes.

    Raises
    ------
    :obj:`ValueError`
        If the image type passed is not supported.

    Returns
    -------
    :obj:`str`, optional
        The ``image_bytes`` given encoded into an image data string or ``None``.

    Note
    ----
    Supported image types: ``.png``, ``.jpeg``, ``.jfif``, ``.gif``, ``.webp``
    """
    if img_bytes is None:
        return None

    if img_bytes[:8] == b"\211PNG\r\n\032\n":
        img_type = "image/png"
    elif img_bytes[6:10] in (b"Exif", b"JFIF"):
        img_type = "image/jpeg"
    elif img_bytes[:6] in (b"GIF87a", b"GIF89a"):
        img_type = "image/gif"
    elif img_bytes.startswith(b"RIFF") and img_bytes[8:12] == b"WEBP":
        img_type = "image/webp"
    else:
        raise ValueError("Unsupported image type passed")

    image_data = base64.b64encode(img_bytes).decode()

    return f"data:{img_type};base64,{image_data}"


def try_cast_or_defer_unary_operator(type_):
    """Return a unary operator that will try to cast the given input to the type provided.

    Parameters
    ----------
    type_ : :obj:`typing.Callable` [ ..., ``output type`` ]
        The type to cast to.
    """
    return lambda data: try_cast(data, type_, data)


def parse_http_date(date_str: str) -> datetime.datetime:
    """Return the HTTP date as a datetime object.

    Parameters
    ----------
    date_str : :obj:`str`
        The RFC-2822 (section 3.3) compliant date string to parse.

    Returns
    -------
    :obj:`datetime.datetime`
        The HTTP date as a datetime object.

    See Also
    --------
    `<https://www.ietf.org/rfc/rfc2822.txt>`_
    """
    return email.utils.parsedate_to_datetime(date_str)


ISO_8601_DATE_PART = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
ISO_8601_TIME_PART = re.compile(r"T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?", re.I)
ISO_8601_TZ_PART = re.compile(r"([+-])(\d{2}):(\d{2})$")


def parse_iso_8601_ts(date_string: str) -> datetime.datetime:
    """Parse an ISO 8601 date string into a :obj:`datetime.datetime` object.

    Parameters
    ----------
    date_string : :obj:`str`
        The ISO 8601 compliant date string to parse.

    Returns
    -------
    :obj:`datetime.datetime`
        The ISO 8601 date string as a datetime object.

    See Also
    --------
    `<https://en.wikipedia.org/wiki/ISO_8601>`_
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


DISCORD_EPOCH = 1_420_070_400


def discord_epoch_to_datetime(epoch: int) -> datetime.datetime:
    """Parse a Discord epoch into a :obj:`datetime.datetime` object.

    Parameters
    ----------
    epoch : :obj:`int`
        Number of milliseconds since 1/1/2015 (UTC)

    Returns
    -------
    :obj:`datetime.datetime`
        Number of seconds since 1/1/1970 within a datetime object (UTC).
    """
    return datetime.datetime.fromtimestamp(epoch / 1000 + DISCORD_EPOCH, datetime.timezone.utc)


def unix_epoch_to_ts(epoch: int) -> datetime.datetime:
    """Parse a UNIX epoch to a :obj:`datetime.datetime` object.

    Parameters
    ----------
    epoch : :obj:`int`
        Number of milliseconds since 1/1/1970 (UTC)

    Returns
    -------
    :obj:`datetime.datetime`
        Number of seconds since 1/1/1970 within a datetime object (UTC).
    """
    return datetime.datetime.fromtimestamp(epoch / 1000, datetime.timezone.utc)


def make_resource_seekable(resource: typing.Any) -> typing.Union[io.BytesIO, io.StringIO]:
    """Make a seekable resource to use off some representation of data.

    This supports :obj:`bytes`, :obj:`bytearray`, :obj:`memoryview`, and
    :obj:`str`. Anything else is just returned.

    Parameters
    ----------
    resource : :obj:`typing.Any`
        The resource to check.

    Returns
    -------
    :obj:`typing.Union` [ :obj:`io.BytesIO`, :obj:`io.StringIO` ]
        An stream-compatible resource where possible.
    """
    if isinstance(resource, (bytes, bytearray)):
        resource = io.BytesIO(resource)
    elif isinstance(resource, memoryview):
        resource = io.BytesIO(resource.tobytes())
    elif isinstance(resource, str):
        resource = io.StringIO(resource)

    return resource


def pluralize(count: int, name: str, suffix: str = "s") -> str:
    """Pluralizes a word."""
    return f"{count} {name + suffix}" if count - 1 else f"{count} {name}"


BytesLikeT = typing.Union[bytes, bytearray, memoryview, str, io.StringIO, io.BytesIO]
FileLikeT = typing.Union[BytesLikeT, io.BufferedRandom, io.BufferedReader, io.BufferedRWPair]
