#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime

from hikari import _utils


def test_get_from_map_as_when_value_is_right_type():
    d = {"foo": 9, "bar": 18}
    assert _utils.get_from_map_as(d, "foo", int) == 9


def test_get_from_map_as_when_value_is_not_right_type():
    d = {"foo": 9, "bar": 18}
    assert _utils.get_from_map_as(d, "bar", str) == "18"


def test_get_from_map_as_value_when_not_present_returns_None():
    d = {"foo": 9, "bar": 18}
    assert _utils.get_from_map_as(d, "baz", int) is None


def test_get_from_map_as_value_when_not_present_with_custom_default_returns_that_default():
    d = {"foo": 9, "bar": 18}
    sentinel = object()
    assert _utils.get_from_map_as(d, "baz", int, sentinel) is sentinel


def test_get_from_map_as_value_when_cast_error_not_suppressed_raises_exception():
    d = {"foo": 9, "bar": 18, "baz": {9, 18, 27}}
    try:
        _utils.get_from_map_as(d, "baz", datetime.timedelta)
        assert False, "Error did not propagate"
    except Exception:
        assert True, "Success. Error is raised"


def test_get_from_map_as_value_when_cast_error_suppressed_returns_default():
    d = {"foo": 9, "bar": 18, "baz": {9, 18, 27}}
    assert _utils.get_from_map_as(d, "baz", datetime.timedelta, default_on_error=True) is None


def test_parse_http_date():
    rfc_timestamp = "Mon, 03 Jun 2019 17:54:26 GMT"
    expected_timestamp = datetime.datetime(2019, 6, 3, 17, 54, 26, tzinfo=datetime.timezone.utc)

    assert _utils.parse_http_date(rfc_timestamp) == expected_timestamp


def test_parse_rate_limit_headers_with_all_expected_values():
    timestamp = 1559584466

    headers = {
        "Date": "Mon, 03 Jun 2019 17:54:26 GMT",
        "X-RateLimit-Reset": str(timestamp + 34),
        "X-RateLimit-Remain": "69",
        "X-RateLimit-Total": "113",
        "Content-Type": "application/who-gives-a-schmidtt",
    }

    result = _utils.parse_rate_limit_headers(headers)

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

    result = _utils.parse_rate_limit_headers(headers)

    assert result.remain is None
    assert result.total == 113
    assert result.reset is None
    assert result.now.timestamp() == timestamp


def test_library_version_is_callable_and_produces_string():
    result = _utils.library_version()
    assert result.startswith("hikari v")


def test_python_version_is_callable_and_produces_string():
    result = _utils.python_version()
    assert isinstance(result, str) and len(result.strip()) > 0


def test_Resource_bucket():
    a = _utils.Resource(
        "http://base.lan",
        "get",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    b = _utils.Resource(
        "http://base.lan",
        "GET",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    c = _utils.Resource(
        "http://base.lan", "get", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )
    d = _utils.Resource(
        "http://base.lan", "post", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )

    assert a.bucket == b.bucket
    assert c.bucket != d.bucket
    assert a.bucket == c.bucket
    assert b.bucket == c.bucket
    assert a.bucket != d.bucket
    assert b.bucket != d.bucket


def test_Resource_hash():
    a = _utils.Resource(
        "http://base.lan",
        "get",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    b = _utils.Resource(
        "http://base.lan",
        "GET",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    c = _utils.Resource(
        "http://base.lan", "get", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )
    d = _utils.Resource(
        "http://base.lan", "post", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )

    assert hash(a) == hash(b)
    assert hash(c) != hash(d)
    assert hash(a) == hash(c)
    assert hash(b) == hash(c)
    assert hash(a) != hash(d)
    assert hash(b) != hash(d)


def test_Resource_equality():
    a = _utils.Resource(
        "http://base.lan",
        "get",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    b = _utils.Resource(
        "http://base.lan",
        "GET",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    c = _utils.Resource(
        "http://base.lan", "get", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )
    d = _utils.Resource(
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
    a = _utils.Resource(
        "http://foo.com",
        "get",
        "/foo/{channel_id}/bar/{guild_id}/baz/{potatos}",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
    )
    assert a.uri == "http://foo.com/foo/1234/bar/5678/baz/spaghetti"


def test_can_apply_link_developer_portal_with_no_impl_uri():
    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    def foo():
        pass


def test_unspecified_str():
    assert str(_utils.unspecified) == "unspecified"


def test_unspecified_repr():
    assert repr(_utils.unspecified) == "unspecified"


def test_put_if_specified_when_specified():
    d = {}
    _utils.put_if_specified(d, "foo", 69)
    _utils.put_if_specified(d, "bar", "hi")
    _utils.put_if_specified(d, "bar", None)
    assert d == {"foo": 69, "bar": None}


def test_put_if_specified_when_unspecified():
    d = {}
    _utils.put_if_specified(d, "bar", _utils.unspecified)
    assert d == {}
