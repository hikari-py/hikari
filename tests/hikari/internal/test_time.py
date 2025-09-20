# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
from __future__ import annotations

import datetime

import mock
import pytest

from hikari.internal import time


def test_parse_iso_8601_date_with_negative_timezone():
    string = "2019-10-10T05:22:33.023456-02:30"
    date = time.iso8601_datetime_string_to_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 23456
    offset = date.tzinfo.utcoffset(None)
    assert offset == datetime.timedelta(hours=-2, minutes=-30)


def test_slow_parse_iso_8601_date_with_positive_timezone():
    string = "2019-10-10T05:22:33.023456+02:30"
    date = time.iso8601_datetime_string_to_datetime(string)
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
    date = time.iso8601_datetime_string_to_datetime(string)
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
    date = time.iso8601_datetime_string_to_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 23000


def test_parse_iso_8601_date_with_no_fraction():
    string = "2019-10-10T05:22:33Z"
    date = time.iso8601_datetime_string_to_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 0


def test_speedup_replaces_python_version_when_available():
    try:
        import ciso8601

        assert time.fast_iso8601_datetime_string_to_datetime is ciso8601.parse_rfc3339
        assert time.iso8601_datetime_string_to_datetime is ciso8601.parse_rfc3339
    except ModuleNotFoundError:
        # No speedups, test pure version has been setup correctly

        assert time.fast_iso8601_datetime_string_to_datetime is None
        assert time.iso8601_datetime_string_to_datetime is time.slow_iso8601_datetime_string_to_datetime


def test_parse_discord_epoch_to_datetime():
    discord_timestamp = 37921278956
    expected_timestamp = datetime.datetime(2016, 3, 14, 21, 41, 18, 956000, tzinfo=datetime.timezone.utc)
    assert time.discord_epoch_to_datetime(discord_timestamp) == expected_timestamp


def test_parse_datetime_to_discord_epoch():
    # This specific timestamp (amongst others) has given problems in the past with
    # float precision, so make sure it doesn't happen again.
    timestamp = datetime.datetime(2022, 8, 13, 23, 10, 35, 843000, tzinfo=datetime.timezone.utc)
    expected_discord_timestamp = 240361835843
    assert time.datetime_to_discord_epoch(timestamp) == expected_discord_timestamp


def test_parse_unix_epoch_to_datetime():
    unix_timestamp = 1457991678956
    expected_timestamp = datetime.datetime(2016, 3, 14, 21, 41, 18, 956000, tzinfo=datetime.timezone.utc)
    assert time.unix_epoch_to_datetime(unix_timestamp) == expected_timestamp


def test_unix_epoch_to_datetime_with_out_of_range_positive_timestamp():
    assert time.unix_epoch_to_datetime(996877846784536) == datetime.datetime.max.replace(tzinfo=datetime.timezone.utc)


def test_unix_epoch_to_datetime_with_out_of_range_negative_timestamp():
    assert time.unix_epoch_to_datetime(-996877846784536) == datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)


@pytest.mark.parametrize(
    ("input_value", "expected_result"),
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
    assert time.timespan_to_int(input_value) == expected_result


def test_utc_datetime():
    current_datetime = datetime.datetime.now(tz=datetime.timezone.utc)

    # We can't mock datetime normally as it is a C module :(
    class datetime_module:
        timezone = datetime.timezone

        class datetime:
            now = mock.Mock(return_value=current_datetime)

    with mock.patch.object(time, "datetime", datetime_module):
        result = time.utc_datetime()

    datetime_module.datetime.now.assert_called_once_with(tz=datetime.timezone.utc)

    assert result == current_datetime


def test_local_datetime():
    current_datetime = datetime.datetime.now(tz=datetime.timezone.utc)

    # We can't mock datetime normally as it is a C module :(
    class datetime_module:
        timezone = datetime.timezone

        class datetime:
            now = mock.Mock(return_value=current_datetime)

    with mock.patch.object(time, "datetime", datetime_module):
        result = time.local_datetime()

    datetime_module.datetime.now.assert_called_once_with(tz=datetime.timezone.utc)

    assert result == current_datetime.astimezone()
