#!/usr/bin/env python3
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
import datetime

import pytest

from hikari.utilities import date as date_


def test_parse_iso_8601_date_with_negative_timezone():
    string = "2019-10-10T05:22:33.023456-02:30"
    date = date_.iso8601_datetime_string_to_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 23456
    offset = date.tzinfo.utcoffset(None)
    assert offset == datetime.timedelta(hours=-2, minutes=-30)


def test_parse_iso_8601_date_with_positive_timezone():
    string = "2019-10-10T05:22:33.023456+02:30"
    date = date_.iso8601_datetime_string_to_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 23456
    offset = date.tzinfo.utcoffset(None)
    assert offset == datetime.timedelta(hours=2, minutes=30)


def test_parse_iso_8601_date_with_zulu():
    string = "2019-10-10T05:22:33.023456Z"
    date = date_.iso8601_datetime_string_to_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 23456
    offset = date.tzinfo.utcoffset(None)
    assert offset == datetime.timedelta(seconds=0)


def test_parse_iso_8601_date_with_milliseconds_instead_of_microseconds():
    string = "2019-10-10T05:22:33.023Z"
    date = date_.iso8601_datetime_string_to_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 23000


def test_parse_iso_8601_date_with_no_fraction():
    string = "2019-10-10T05:22:33Z"
    date = date_.iso8601_datetime_string_to_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 0


def test_parse_http_date():
    rfc_timestamp = "Mon, 03 Jun 2019 17:54:26 GMT"
    expected_timestamp = datetime.datetime(2019, 6, 3, 17, 54, 26, tzinfo=datetime.timezone.utc)
    assert date_.rfc7231_datetime_string_to_datetime(rfc_timestamp) == expected_timestamp


def test_parse_discord_epoch_to_datetime():
    discord_timestamp = 37921278956
    expected_timestamp = datetime.datetime(2016, 3, 14, 21, 41, 18, 956000, tzinfo=datetime.timezone.utc)
    assert date_.discord_epoch_to_datetime(discord_timestamp) == expected_timestamp


def test_parse_datetime_to_discord_epoch():
    timestamp = datetime.datetime(2016, 3, 14, 21, 41, 18, 956000, tzinfo=datetime.timezone.utc)
    expected_discord_timestamp = 37921278956
    assert date_.datetime_to_discord_epoch(timestamp) == expected_discord_timestamp


def test_parse_unix_epoch_to_datetime():
    unix_timestamp = 1457991678956
    expected_timestamp = datetime.datetime(2016, 3, 14, 21, 41, 18, 956000, tzinfo=datetime.timezone.utc)
    assert date_.unix_epoch_to_datetime(unix_timestamp) == expected_timestamp


def test_unix_epoch_to_datetime_with_out_of_range_positive_timestamp():
    assert date_.unix_epoch_to_datetime(996877846784536) == datetime.datetime.max


def test_unix_epoch_to_datetime_with_out_of_range_negative_timestamp():
    assert date_.unix_epoch_to_datetime(-996877846784536) == datetime.datetime.min


@pytest.mark.parametrize(
    ["input_value", "expected_result"],
    [
        (5, 5),
        (2.718281828459045, 2),
        (datetime.timedelta(days=5, seconds=3, milliseconds=12), 432_003),
        (-5, 0),
        (-2.718281828459045, 0),
        (datetime.timedelta(days=-5, seconds=-3, milliseconds=12), 0),
    ],
)
def test_timespan_to_int(input_value, expected_result):
    assert date_.timespan_to_int(input_value) == expected_result
