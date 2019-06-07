#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest

from hikari import errors
from hikari.net import http
from hikari_tests._helpers import _mock_methods_on


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


class HTTPContext(http.HTTPConnection):
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


@pytest.mark.asyncio
async def test_request_retries_then_errors(event_loop):
    async with HTTPContext(loop=event_loop, token="xxx") as h:
        h._request_once = asynctest.CoroutineMock(return_value=http._RATE_LIMITED_SENTINEL)
        try:
            await h._request(method="get", path="/foo/bar")
            assert False, "No error was thrown but it was expected!"
        except errors.DiscordHTTPError:
            pass

        assert h._request_once.call_count == h._RATELIMIT_RETRIES


@pytest.mark.asyncio
async def test_request_does_not_retry_on_success(event_loop):
    async with HTTPContext(loop=event_loop, token="xxx") as h:
        expected_result = object()
        h._request_once = asynctest.CoroutineMock(
            side_effect=[http._RATE_LIMITED_SENTINEL, http._RATE_LIMITED_SENTINEL, expected_result]
        )
        actual_result = await h._request(method="get", path="/foo/bar")
        assert h._request_once.call_count == 3
        assert actual_result is expected_result


def _mock_for_request_once(event_loop) -> http.HTTPConnection:
    with asynctest.patch("aiohttp.ClientSession", new=asynctest.MagicMock()):
        mock = _mock_methods_on(
            HTTPContext(loop=event_loop, token="xxx"),
            except_=["_request_once", "_get_bucket_key"],
            also_mock=["global_rate_limit.acquire"],
        )

        mock.session.___response = asynctest.MagicMock()
        mock.session.request = asynctest.CoroutineMock(return_value=mock.session.___response)
        mock.session.___response.json = asynctest.CoroutineMock()
        mock.session.___response.close = asynctest.CoroutineMock()
        return mock


@pytest.mark.asyncio
async def test_request_once_acquires_global_rate_limit_bucket(event_loop):
    h = _mock_for_request_once(event_loop)
    res = http.Resource("get", "/foo/bar")
    await h._request_once(retry=0, resource=res, json_body={})
    h.global_rate_limit.acquire.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_once_acquires_local_rate_limit_bucket(event_loop):
    h = _mock_for_request_once(event_loop)
    res = http.Resource("get", "/foo/bar")
    bucket = asynctest.MagicMock()
    bucket.acquire = asynctest.CoroutineMock()
    h.buckets[res] = bucket
    await h._request_once(retry=0, resource=res, json_body={})
    bucket.acquire.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_once_calls_rate_limit_handler(event_loop):
    h = _mock_for_request_once(event_loop)
    res = http.Resource("get", "/foo/bar")
    await h._request_once(retry=0, resource=res)
    h._is_rate_limited.assert_called_once()


@pytest.mark.asyncio
async def test_request_once_returns_sentinel_if_rate_limit_handler_returned_true(event_loop):
    h = _mock_for_request_once(event_loop)
    res = http.Resource("get", "/foo/bar")
    h._is_rate_limited = asynctest.MagicMock(return_value=True)
    result = await h._request_once(retry=0, resource=res)
    assert result is http._RATE_LIMITED_SENTINEL


@pytest.mark.asyncio
async def test_request_once_does_not_return_sentinel_if_rate_limit_handler_returned_false(event_loop):
    h = _mock_for_request_once(event_loop)
    res = http.Resource("get", "/foo/bar")
    h._is_rate_limited = asynctest.MagicMock(return_value=False)
    result = await h._request_once(retry=0, resource=res)
    assert result is not http._RATE_LIMITED_SENTINEL


@pytest.mark.asyncio
async def test_log_rate_limit_already_in_progress_logs_something(event_loop):
    async with HTTPContext(loop=event_loop, token="xxx") as h:
        res = http.Resource("get", "/foo/bar")
        h.logger = asynctest.MagicMock(wraps=h.logger)
        h._log_rate_limit_already_in_progress(res)
        h.logger.debug.assert_called_once()


@pytest.mark.asyncio
async def test_log_rate_limit_starting_logs_something(event_loop):
    async with HTTPContext(loop=event_loop, token="xxx") as h:
        res = http.Resource("get", "/foo/bar")
        h.logger = asynctest.MagicMock(wraps=h.logger)
        h._log_rate_limit_starting(res, 123.45)
        h.logger.debug.assert_called_once()


@pytest.mark.asyncio
async def test_is_rate_limited_locks_global_rate_limit_if_set(event_loop):
    async with HTTPContext(loop=event_loop, token="xxx") as h:
        pass
