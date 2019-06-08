#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime

from hikari.net import utils


def test_get_from_map_as_when_value_is_right_type():
    d = {"foo": 9, "bar": 18}
    assert utils.get_from_map_as(d, "foo", int) == 9


def test_get_from_map_as_when_value_is_not_right_type():
    d = {"foo": 9, "bar": 18}
    assert utils.get_from_map_as(d, "bar", str) == "18"


def test_get_from_map_as_value_when_not_present():
    d = {"foo": 9, "bar": 18}
    assert utils.get_from_map_as(d, "baz", int) is None


def test_parse_http_date():
    rfc_timestamp = "Mon, 03 Jun 2019 17:54:26 GMT"
    expected_timestamp = datetime.datetime(2019, 6, 3, 17, 54, 26, tzinfo=datetime.timezone.utc)

    assert utils.parse_http_date(rfc_timestamp) == expected_timestamp


def test_parse_rate_limit_headers_with_all_expected_values():
    timestamp = 1559584466

    headers = {
        "Date": "Mon, 03 Jun 2019 17:54:26 GMT",
        "X-RateLimit-Reset": str(timestamp + 34),
        "X-RateLimit-Remain": "69",
        "X-RateLimit-Total": "113",
        "Content-Type": "application/who-gives-a-schmidtt",
    }

    result = utils.parse_rate_limit_headers(headers)

    assert result.remain == 69
    assert result.total == 113
    assert int((result.reset - result.now).total_seconds()) == 34
    assert result.now.timestamp() == timestamp


def test_parse_rate_limit_headers_with_missing_values():
    timestamp = 1559584466

    headers = {
        "Date": "Mon, 03 Jun 2019 17:54:26 GMT",
        "X-RateLimit-Total": "113",
        "Content-Type": "application/who-gives-a-schmidtt",
    }

    result = utils.parse_rate_limit_headers(headers)

    assert result.remain is None
    assert result.total == 113
    assert result.reset is None
    assert result.now.timestamp() == timestamp


def test_library_version_is_callable_and_produces_string():
    result = utils.library_version()
    assert result.startswith("hikari v")


def test_python_version_is_callable_and_produces_string():
    result = utils.python_version()
    assert isinstance(result, str) and len(result.strip()) > 0
