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

from hikari.utils import assertions
from hikari.utils import dateutils
from hikari.utils import maps
from hikari.utils import meta
from hikari.utils import types
from hikari.utils import unspecified


def test_get_from_map_as_when_value_is_right_type():
    d = {"foo": 9, "bar": 18}
    assert maps.get_from_map_as(d, "foo", int) == 9


def test_get_from_map_as_when_value_is_not_right_type():
    d = {"foo": 9, "bar": 18}
    assert maps.get_from_map_as(d, "bar", str) == "18"


def test_get_from_map_as_value_when_not_present_returns_None():
    d = {"foo": 9, "bar": 18}
    assert maps.get_from_map_as(d, "baz", int) is None


def test_get_from_map_as_value_when_not_present_with_custom_default_returns_that_default():
    d = {"foo": 9, "bar": 18}
    sentinel = object()
    assert maps.get_from_map_as(d, "baz", int, sentinel) is sentinel


def test_get_from_map_as_value_when_cast_error_not_suppressed_raises_exception():
    d = {"foo": 9, "bar": 18, "baz": {9, 18, 27}}
    try:
        maps.get_from_map_as(d, "baz", datetime.timedelta)
        assert False, "Error did not propagate"
    except Exception:
        assert True, "Success. Error is raised"


def test_get_from_map_as_value_when_cast_error_suppressed_returns_default():
    d = {"foo": 9, "bar": 18, "baz": {9, 18, 27}}
    assert maps.get_from_map_as(d, "baz", datetime.timedelta, default_on_error=True) is None


def test_parse_http_date():
    rfc_timestamp = "Mon, 03 Jun 2019 17:54:26 GMT"
    expected_timestamp = datetime.datetime(2019, 6, 3, 17, 54, 26, tzinfo=datetime.timezone.utc)

    assert dateutils.parse_http_date(rfc_timestamp) == expected_timestamp


def test_library_version_is_callable_and_produces_string():
    result = meta.library_version()
    assert result.startswith("hikari v")


def test_python_version_is_callable_and_produces_string():
    result = meta.python_version()
    assert isinstance(result, str) and len(result.strip()) > 0


def test_can_apply_link_developer_portal_with_no_impl_uri():
    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    def foo():
        pass


def test_unspecified_str():
    assert str(unspecified.UNSPECIFIED) == "unspecified"


def test_unspecified_repr():
    assert repr(unspecified.UNSPECIFIED) == "unspecified"


def test_unspecified_bool():
    assert not unspecified.UNSPECIFIED
    assert bool(unspecified.UNSPECIFIED) is False


def test_put_if_specified_when_specified():
    d = {}
    maps.put_if_specified(d, "foo", 69)
    maps.put_if_specified(d, "bar", "hi")
    maps.put_if_specified(d, "bar", None)
    assert d == {"foo": 69, "bar": None}


def test_put_if_specified_when_unspecified():
    d = {}
    maps.put_if_specified(d, "bar", unspecified.UNSPECIFIED)
    assert d == {}


def test_assert_not_none_when_none():
    try:
        assertions.assert_not_none(None)
        assert False, "No error raised"
    except ValueError:
        pass


@pytest.mark.parametrize("arg", [9, "foo", False, 0, 0.0, "", [], {}, set(), ..., NotImplemented])
def test_assert_not_none_when_not_none(arg):
    assertions.assert_not_none(arg)


def test_ObjectProxy():
    dop = types.ObjectProxy({"foo": "bar"})
    assert dop["foo"] == dop.foo


def test_parse_iso_8601_date_with_negative_timezone():
    string = "2019-10-10T05:22:33.023456-02:30"
    date = dateutils.parse_iso_8601_datetime(string)
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
    date = dateutils.parse_iso_8601_datetime(string)
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
    date = dateutils.parse_iso_8601_datetime(string)
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
    date = dateutils.parse_iso_8601_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 23000


def test_assert_is_mixin_applied_to_something_that_is_not_a_class():
    try:
        @assertions.assert_is_mixin
        def foo():
            pass

        assert False, "No error thrown"
    except TypeError:
        pass


def test_assert_is_mixin_applied_to_something_that_is_directly_derived_from_object_or_mixin():
    try:
        class Bar:
            pass

        @assertions.assert_is_mixin
        class FooMixin(Bar):
            pass

        assert False, "No error thrown"
    except TypeError:
        pass


def test_assert_is_mixin_applied_to_something_that_is_not_slotted():
    try:
        @assertions.assert_is_mixin
        class FooMixin:
            pass

        assert False, "No error thrown"
    except TypeError:
        pass


def test_assert_is_mixin_applied_to_something_that_is_slotted_but_not_multiple_inheritance_compatible():
    try:
        @assertions.assert_is_mixin
        class FooMixin:
            __slots__ = ('nine', 'eighteen', 'twentyseven')

        assert False, "No error thrown"
    except TypeError:
        pass


def test_assert_is_mixin_applied_to_something_that_is_not_named_correctly():
    try:
        @assertions.assert_is_mixin
        class FooMixer:
            __slots__ = ()

        assert False, "No error thrown"
    except NameError:
        pass


def test_assert_is_mixin_applied_to_something_that_is_directly_derived_from_mixins_and_directly_from_object():
    @assertions.assert_is_mixin
    class BarMixin:
        __slots__ = ()

    @assertions.assert_is_mixin
    class FooMixin(BarMixin):
        __slots__ = ()


def test_unspecified_is_singleton():
    assert unspecified.Unspecified() is unspecified.Unspecified() is unspecified.UNSPECIFIED
