#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests the low level handler logic all endpoints will be expected to use.
"""
import asyncio
import datetime
import email
import time

import asynctest
import pytest

from hikari import errors
from hikari.net import http
from hikari.net import rates
from hikari_tests._helpers import _mock_methods_on


########################################################################################################################


class MockAiohttpResponse:
    __aenter__ = asyncio.coroutine(lambda self: self)
    __aexit__ = asyncio.coroutine(lambda self, *_, **__: None)
    json = asynctest.CoroutineMock()
    close = asynctest.CoroutineMock()
    status = 200
    reason = "OK"
    headers = {}
    content_length = 500

    @property
    def content_type(self):
        return self.headers.get("Content-Type", "application/json")


class MockAiohttpSession:
    def __init__(self, *a, **k):
        self.response = MockAiohttpResponse()

    def request(self, *a, **k):
        return self.response

    close = asynctest.CoroutineMock()


class MockHTTPConnection(http.HTTPConnection):
    def __init__(self, *a, **k):
        with asynctest.patch("aiohttp.ClientSession", new=MockAiohttpSession):
            super().__init__(*a, **k)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_http_connection(event_loop):
    return MockHTTPConnection(loop=event_loop, token="xxx")


########################################################################################################################


def test_resource_bucket():
    a = http.Resource("get", "/foo/bar", channel_id="1234", potatos="spaghetti", guild_id="5678", webhook_id="91011")
    b = http.Resource("GET", "/foo/bar", channel_id="1234", potatos="spaghetti", guild_id="5678", webhook_id="91011")
    c = http.Resource("get", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011")
    d = http.Resource("post", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011")

    assert a.bucket == b.bucket
    assert c.bucket != d.bucket
    assert a.bucket == c.bucket
    assert b.bucket == c.bucket
    assert a.bucket != d.bucket
    assert b.bucket != d.bucket


def test_resource_hash():
    a = http.Resource("get", "/foo/bar", channel_id="1234", potatos="spaghetti", guild_id="5678", webhook_id="91011")
    b = http.Resource("GET", "/foo/bar", channel_id="1234", potatos="spaghetti", guild_id="5678", webhook_id="91011")
    c = http.Resource("get", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011")
    d = http.Resource("post", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011")

    assert hash(a) == hash(b)
    assert hash(c) != hash(d)
    assert hash(a) == hash(c)
    assert hash(b) == hash(c)
    assert hash(a) != hash(d)
    assert hash(b) != hash(d)


def test_resource_get_uri():
    a = http.Resource(
        "get", "/foo/{channel_id}/bar/{guild_id}/baz/{potatos}", channel_id="1234", potatos="spaghetti", guild_id="5678"
    )
    assert a.get_uri("http://foo.com") == "http://foo.com/foo/1234/bar/5678/baz/spaghetti"


@pytest.mark.asyncio
async def test_close_will_close_session(mock_http_connection):
    await mock_http_connection.close()
    mock_http_connection.session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_retries_then_errors(mock_http_connection):
    mock_http_connection._request_once = asynctest.CoroutineMock(return_value=http._RATE_LIMITED_SENTINEL)
    try:
        await mock_http_connection._request(method="get", path="/foo/bar")
        assert False, "No error was thrown but it was expected!"
    except errors.DiscordHTTPError:
        pass

    assert mock_http_connection._request_once.call_count == mock_http_connection._RATELIMIT_RETRIES


@pytest.mark.asyncio
async def test_request_does_not_retry_on_success(mock_http_connection):
    expected_result = object()
    mock_http_connection._request_once = asynctest.CoroutineMock(
        side_effect=[http._RATE_LIMITED_SENTINEL, http._RATE_LIMITED_SENTINEL, expected_result]
    )
    actual_result = await mock_http_connection._request(method="get", path="/foo/bar")
    assert mock_http_connection._request_once.call_count == 3
    assert actual_result is expected_result


@pytest.mark.asyncio
async def test_request_once_acquires_global_rate_limit_bucket(mock_http_connection):
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_request_once", "_get_bucket_key"], also_mock=["global_rate_limit.acquire"]
    )
    res = http.Resource("get", "/foo/bar")
    await mock_http_connection._request_once(retry=0, resource=res, json_body={})
    mock_http_connection.global_rate_limit.acquire.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_once_acquires_local_rate_limit_bucket(mock_http_connection):
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_request_once", "_get_bucket_key"], also_mock=["global_rate_limit.acquire"]
    )
    res = http.Resource("get", "/foo/bar")
    bucket = asynctest.MagicMock()
    bucket.acquire = asynctest.CoroutineMock()
    mock_http_connection.buckets[res] = bucket
    await mock_http_connection._request_once(retry=0, resource=res, json_body={})
    bucket.acquire.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_once_calls_rate_limit_handler(mock_http_connection):
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_request_once", "_get_bucket_key"], also_mock=["global_rate_limit.acquire"]
    )
    res = http.Resource("get", "/foo/bar")
    await mock_http_connection._request_once(retry=0, resource=res)
    mock_http_connection._is_rate_limited.assert_called_once()


@pytest.mark.asyncio
async def test_request_once_returns_sentinel_if_rate_limit_handler_returned_true(mock_http_connection):
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_request_once", "_get_bucket_key"], also_mock=["global_rate_limit.acquire"]
    )
    res = http.Resource("get", "/foo/bar")
    mock_http_connection._is_rate_limited = asynctest.MagicMock(return_value=True)
    result = await mock_http_connection._request_once(retry=0, resource=res)
    assert result is http._RATE_LIMITED_SENTINEL


@pytest.mark.asyncio
async def test_request_once_does_not_return_sentinel_if_rate_limit_handler_returned_false(mock_http_connection):
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_request_once", "_get_bucket_key"], also_mock=["global_rate_limit.acquire"]
    )
    res = http.Resource("get", "/foo/bar")
    mock_http_connection._is_rate_limited = asynctest.MagicMock(return_value=False)
    result = await mock_http_connection._request_once(retry=0, resource=res)
    assert result is not http._RATE_LIMITED_SENTINEL


@pytest.mark.asyncio
async def test_log_rate_limit_already_in_progress_logs_something(mock_http_connection):
    res = http.Resource("get", "/foo/bar")
    mock_http_connection.logger = asynctest.MagicMock(wraps=mock_http_connection.logger)
    mock_http_connection._log_rate_limit_already_in_progress(res)
    mock_http_connection.logger.debug.assert_called_once()


@pytest.mark.asyncio
async def test_log_rate_limit_starting_logs_something(mock_http_connection):
    res = http.Resource("get", "/foo/bar")
    mock_http_connection.logger = asynctest.MagicMock(wraps=mock_http_connection.logger)
    mock_http_connection._log_rate_limit_starting(res, 123.45)
    mock_http_connection.logger.debug.assert_called_once()


@pytest.mark.asyncio
async def test_is_rate_limited_locks_global_rate_limit_if_set(mock_http_connection):
    res = http.Resource("get", "/foo/bar")
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )
    mock_http_connection._is_rate_limited(
        res,
        429,
        headers={"X-RateLimit-Global": "true"},
        body={"message": "You are being rate limited", "retry_after": 500, "global": True},
    )

    mock_http_connection.global_rate_limit.lock.assert_called_once_with(0.5)


@pytest.mark.asyncio
async def test_is_rate_limited_returns_True_when_globally_rate_limited(mock_http_connection):
    res = http.Resource("get", "/foo/bar")
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )
    result = mock_http_connection._is_rate_limited(
        res,
        429,
        headers={"X-RateLimit-Global": "true"},
        body={"message": "You are being rate limited", "retry_after": 500, "global": True},
    )

    assert result is True


@pytest.mark.asyncio
async def test_is_rate_limited_calls_log_rate_limit_starting(mock_http_connection):
    res = http.Resource("get", "/foo/bar")
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )
    mock_http_connection._is_rate_limited(
        res,
        429,
        headers={"X-RateLimit-Global": "true"},
        body={"message": "You are being rate limited", "retry_after": 500, "global": True},
    )

    mock_http_connection._log_rate_limit_starting.assert_called_once()


@pytest.mark.asyncio
async def test_is_rate_limited_does_not_lock_global_rate_limit_if_XRateLimitGlobal_is_false(mock_http_connection):
    res = http.Resource("get", "/foo/bar")
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )
    mock_http_connection._is_rate_limited(
        res,
        429,
        headers={"X-RateLimit-Global": "false"},
        body={"message": "You are being rate limited", "retry_after": 500, "global": False},
    )

    mock_http_connection.global_rate_limit.lock.assert_not_called()


@pytest.mark.asyncio
async def test_is_rate_limited_does_not_lock_global_rate_limit_if_not_a_429_response(mock_http_connection):
    res = http.Resource("get", "/foo/bar")
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )
    mock_http_connection._is_rate_limited(
        res,
        200,
        headers={"X-RateLimit-Global": "true"},  # we will ignore this as it isn't a 429
        body={"message": "You are being rate limited", "retry_after": 500, "global": False},
    )

    mock_http_connection.global_rate_limit.lock.assert_not_called()


@pytest.mark.asyncio
async def test_is_rate_limited_does_not_lock_global_rate_limit_if_XRateLimitGlobal_is_not_present(mock_http_connection):
    res = http.Resource("get", "/foo/bar")
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )
    mock_http_connection._is_rate_limited(
        res, 429, headers={}, body={"message": "You are being rate limited", "retry_after": 500, "global": False}
    )

    mock_http_connection.global_rate_limit.lock.assert_not_called()


@pytest.mark.asyncio
async def test_is_rate_limited_creates_a_local_bucket_if_one_does_not_exist_for_the_current_resource_locally(
    mock_http_connection
):
    mock_http_connection.buckets.clear()
    now = time.time()
    now_dt = email.utils.format_datetime(datetime.datetime.utcnow())
    res = http.Resource("get", "/foo/bar")
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )

    assert len(mock_http_connection.buckets) == 0
    mock_http_connection._is_rate_limited(
        res,
        200,
        headers={"Date": now_dt, "X-RateLimit-Remaining": 5, "X-RateLimit-Limit": 10, "X-RateLimit-Reset": now + 5},
        body={},
    )

    assert len(mock_http_connection.buckets) == 1
    assert isinstance(mock_http_connection.buckets[res], rates.VariableTokenBucket)


@pytest.mark.asyncio
async def test_is_rate_limited_updates_existing_bucket_if_one_already_exists_for_the_current_resource_locally(
    mock_http_connection
):
    mock_http_connection.buckets.clear()
    now = time.time()
    now_dt = email.utils.format_datetime(datetime.datetime.utcnow())
    res = http.Resource("get", "/foo/bar")
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )

    actual_bucket = rates.VariableTokenBucket(10, 10, 0, 10, mock_http_connection.loop)
    mock_http_connection.buckets[res] = actual_bucket

    assert len(mock_http_connection.buckets) == 1
    mock_http_connection._is_rate_limited(
        res,
        200,
        headers={"Date": now_dt, "X-RateLimit-Remaining": 5, "X-RateLimit-Limit": 10, "X-RateLimit-Reset": now + 5},
        body={},
    )
    assert len(mock_http_connection.buckets) == 1
    assert mock_http_connection.buckets[res] is actual_bucket


@pytest.mark.asyncio
async def test_is_rate_limited_doesnt_call_log_rate_limit_starting_if_not_locking_locally(mock_http_connection):
    mock_http_connection.buckets.clear()
    now = time.time()
    now_dt = email.utils.format_datetime(datetime.datetime.utcnow())
    res = http.Resource("get", "/foo/bar")
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )

    mock_http_connection._is_rate_limited(
        res,
        200,
        headers={"Date": now_dt, "X-RateLimit-Remaining": 5, "X-RateLimit-Limit": 10, "X-RateLimit-Reset": now + 5},
        body={},
    )

    mock_http_connection._log_rate_limit_starting.assert_not_called()


@pytest.mark.asyncio
async def test_is_rate_limited_calls_log_rate_limit_starting_if_locking_locally(mock_http_connection):
    mock_http_connection.buckets.clear()
    now = time.time()
    now_dt = email.utils.format_datetime(datetime.datetime.utcnow())
    res = http.Resource("get", "/foo/bar")
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )

    mock_http_connection._is_rate_limited(
        res,
        200,
        headers={"Date": now_dt, "X-RateLimit-Remaining": 0, "X-RateLimit-Limit": 10, "X-RateLimit-Reset": now + 5},
        body={},
    )

    mock_http_connection._log_rate_limit_starting.assert_called_once()


@pytest.mark.asyncio
async def test_is_rate_limited_returns_True_if_local_rate_limit(mock_http_connection):
    mock_http_connection.buckets.clear()
    now = time.time()
    now_dt = email.utils.format_datetime(datetime.datetime.utcnow())
    res = http.Resource("get", "/foo/bar")
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )

    result = mock_http_connection._is_rate_limited(
        res,
        200,
        headers={"Date": now_dt, "X-RateLimit-Remaining": 0, "X-RateLimit-Limit": 10, "X-RateLimit-Reset": now + 5},
        body={},
    )

    assert result is True


@pytest.mark.asyncio
async def test_is_rate_limited_returns_False_if_not_local_or_global_rate_limit(mock_http_connection):
    mock_http_connection.buckets.clear()
    now = time.time()
    now_dt = email.utils.format_datetime(datetime.datetime.utcnow())
    res = http.Resource("get", "/foo/bar")
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )

    result = mock_http_connection._is_rate_limited(
        res,
        200,
        headers={"Date": now_dt, "X-RateLimit-Remaining": 5, "X-RateLimit-Limit": 10, "X-RateLimit-Reset": now + 5},
        body={},
    )

    assert result is False
