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

import datetime

import pytest

from hikari import utils


def test_get_from_map_as_when_value_is_right_type():
    d = {"foo": 9, "bar": 18}
    assert utils.get_from_map_as(d, "foo", int) == 9


def test_get_from_map_as_when_value_is_not_right_type():
    d = {"foo": 9, "bar": 18}
    assert utils.get_from_map_as(d, "bar", str) == "18"


def test_get_from_map_as_value_when_not_present_returns_None():
    d = {"foo": 9, "bar": 18}
    assert utils.get_from_map_as(d, "baz", int) is None


def test_get_from_map_as_value_when_not_present_with_custom_default_returns_that_default():
    d = {"foo": 9, "bar": 18}
    sentinel = object()
    assert utils.get_from_map_as(d, "baz", int, sentinel) is sentinel


def test_get_from_map_as_value_when_cast_error_not_suppressed_raises_exception():
    d = {"foo": 9, "bar": 18, "baz": {9, 18, 27}}
    try:
        utils.get_from_map_as(d, "baz", datetime.timedelta)
        assert False, "Error did not propagate"
    except Exception:
        assert True, "Success. Error is raised"


def test_get_from_map_as_value_when_cast_error_suppressed_returns_default():
    d = {"foo": 9, "bar": 18, "baz": {9, 18, 27}}
    assert utils.get_from_map_as(d, "baz", datetime.timedelta, default_on_error=True) is None


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


def test_Resource_bucket():
    a = utils.Resource(
        "http://base.lan",
        "get",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    b = utils.Resource(
        "http://base.lan",
        "GET",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    c = utils.Resource(
        "http://base.lan", "get", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )
    d = utils.Resource(
        "http://base.lan", "post", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )

    assert a.bucket == b.bucket
    assert c.bucket != d.bucket
    assert a.bucket == c.bucket
    assert b.bucket == c.bucket
    assert a.bucket != d.bucket
    assert b.bucket != d.bucket


def test_Resource_hash():
    a = utils.Resource(
        "http://base.lan",
        "get",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    b = utils.Resource(
        "http://base.lan",
        "GET",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    c = utils.Resource(
        "http://base.lan", "get", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )
    d = utils.Resource(
        "http://base.lan", "post", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )

    assert hash(a) == hash(b)
    assert hash(c) != hash(d)
    assert hash(a) == hash(c)
    assert hash(b) == hash(c)
    assert hash(a) != hash(d)
    assert hash(b) != hash(d)


def test_Resource_equality():
    a = utils.Resource(
        "http://base.lan",
        "get",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    b = utils.Resource(
        "http://base.lan",
        "GET",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    c = utils.Resource(
        "http://base.lan", "get", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )
    d = utils.Resource(
        "http://base.lan", "post", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )

    assert a == b
    assert b == a
    assert c != d
    assert a == c
    assert b == c
    assert a != d
    assert b != d


def test_resource_get_uri():
    a = utils.Resource(
        "http://foo.com",
        "get",
        "/foo/{channel_id}/bar/{guild_id}/baz/{potatos}",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
    )
    assert a.uri == "http://foo.com/foo/1234/bar/5678/baz/spaghetti"


def test_can_apply_link_developer_portal_with_no_impl_uri():
    @utils.link_developer_portal(utils.APIResource.CHANNEL)
    def foo():
        pass


def test_unspecified_str():
    assert str(utils.UNSPECIFIED) == "unspecified"


def test_unspecified_repr():
    assert repr(utils.UNSPECIFIED) == "unspecified"


def test_unspecified_bool():
    assert not utils.UNSPECIFIED
    assert bool(utils.UNSPECIFIED) is False


def test_put_if_specified_when_specified():
    d = {}
    utils.put_if_specified(d, "foo", 69)
    utils.put_if_specified(d, "bar", "hi")
    utils.put_if_specified(d, "bar", None)
    assert d == {"foo": 69, "bar": None}


def test_put_if_specified_when_unspecified():
    d = {}
    utils.put_if_specified(d, "bar", utils.UNSPECIFIED)
    assert d == {}


def test_assert_not_none_when_none():
    try:
        utils.assert_not_none(None)
        assert False, "No error raised"
    except ValueError:
        pass


@pytest.mark.parametrize("arg", [9, "foo", False, 0, 0.0, "", [], {}, set(), ..., NotImplemented])
def test_assert_not_none_when_not_none(arg):
    utils.assert_not_none(arg)


def test_ObjectProxy():
    dop = utils.ObjectProxy({"foo": "bar"})
    assert dop["foo"] == dop.foo


def test_parse_iso_8601_date_with_negative_timezone():
    string = "2019-10-10T05:22:33.023456-02:30"
    date = utils.parse_iso_8601_datetime(string)
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
    date = utils.parse_iso_8601_datetime(string)
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
    date = utils.parse_iso_8601_datetime(string)
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
    date = utils.parse_iso_8601_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 23000


def test_mixin_applied_to_something_that_is_not_a_class():
    try:
        @utils.mixin
        def foo():
            pass
        assert False, "No error thrown"
    except TypeError:
        pass


def test_mixin_applied_to_something_that_is_not_slotted():
    try:
        @utils.mixin
        class FooMixin:
            pass
        assert False, "No error thrown"
    except TypeError:
        pass


def test_mixin_applied_to_something_that_is_slotted_but_not_multiple_inheritance_compatible():
    try:
        @utils.mixin
        class FooMixin:
            __slots__ = ('nine', 'eighteen', 'twentyseven')

        assert False, "No error thrown"
    except TypeError:
        pass


def test_mixin_applied_to_something_that_is_not_named_correctly():
    try:
        @utils.mixin
        class FooMixer:
            __slots__ = ()

        assert False, "No error thrown"
    except NameError:
        pass


def test_mixin_on_compliant_solution():
    @utils.mixin
    class FooMixin:
        __slots__ = ()
