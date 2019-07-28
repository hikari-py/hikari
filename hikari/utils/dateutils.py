#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
"""
Date/Time utilities.
"""
__all__ = ("parse_http_date", "parse_iso_8601_datetime")

import datetime
import email
import re


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


ISO_8601_DATE_PART = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
ISO_8601_TIME_PART = re.compile(r"[Tt](\d{2}):(\d{2}):(\d{2})\.(\d{1,6})")
ISO_8601_TZ_PART = re.compile(r"([+-])(\d{2}):(\d{2})$")


def parse_iso_8601_datetime(date_string: str) -> datetime.datetime:
    """
    Parses an ISO 8601 date string into a datetime object

    See:
        https://en.wikipedia.org/wiki/ISO_8601
    """
    year, month, day = map(int, ISO_8601_DATE_PART.findall(date_string)[0])
    hour, minute, second, partial = ISO_8601_TIME_PART.findall(date_string)[0]
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


#: This represents the 1st January 2015 as the number of seconds since 1st January 1970 (Discord epoch)
DISCORD_EPOCH = 1_420_070_400


def discord_epoch_to_datetime(epoch) -> datetime.datetime:
    """
    Args:
        epoch:
            Number of milliseconds since 1/1/2015 (UTC)

    Returns:
        Number of seconds since 1/1/1970 within a datetime object (UTC).
    """
    return datetime.datetime.fromtimestamp(epoch / 1_000 + DISCORD_EPOCH, datetime.timezone.utc)
