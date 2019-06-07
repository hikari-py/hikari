#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asynctest
import pytest

from hikari import errors
from hikari.net import http


class HTTPContext(http.HTTPConnection):
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


@pytest.mark.asyncio
async def test_get_bucket_id(event_loop):
    async with HTTPContext(loop=event_loop, token='xxx') as h:
        b = h._get_bucket_key(
            'get',
            '/foo/{channel_id}/bar/{guild_id}/baz/{potato_id}',
            channel_id=6969,
            guild_id=1010,
            potato_id='very potato'
        )

        assert b == ('get', '/foo/{channel_id}/bar/{guild_id}/baz/{potato_id}', 6969, 1010, None)


@pytest.mark.asyncio
async def test_request_retries_then_errors(event_loop):
    async with HTTPContext(loop=event_loop, token='xxx') as h:
        h._request_once = asynctest.CoroutineMock(return_value=http._RATE_LIMITED_SENTINEL)
        try:
            await h._request('get', '/foo/bar')
            assert False, 'No error was thrown but it was expected!'
        except errors.DiscordHTTPError:
            pass

        assert h._request_once.call_count == h.RATELIMIT_RETRIES


@pytest.mark.asyncio
async def test_request_does_not_retry_on_success(event_loop):
    """blah blah blah"""
    async with HTTPContext(loop=event_loop, token='xxx') as h:
        expected_result = object()
        h._request_once = asynctest.CoroutineMock(side_effect=[
            http._RATE_LIMITED_SENTINEL, http._RATE_LIMITED_SENTINEL, expected_result
        ])
        actual_result = await h._request('get', '/foo/bar')
        assert h._request_once.call_count == 3
        assert actual_result is expected_result

