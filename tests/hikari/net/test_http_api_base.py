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

"""
Tests the low level handler logic all endpoints will be expected to use.
"""
import datetime
import email
import json
import re
import time

import async_timeout
import asyncmock as mock
import pytest

from hikari import errors
from hikari.internal_utilities import unspecified
from hikari.net import http_api_base
from hikari.net import opcodes
from hikari.net import rates
from tests.hikari import _helpers
from tests.hikari._helpers import mock_methods_on


########################################################################################################################


class UnslottedMockedGlobalRateLimitFacade(rates.TimedLatchBucket):
    """This has no slots so allows injection of mocks, et cetera."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apparently an issue on CPython3.6 where it can't determine if this is a coroutine or not.
        self.acquire = mock.AsyncMock()


async def return_None(*_, **__):
    return None


async def return_arg(arg, *_, **__):
    return arg


async def return_dict(*_, **__):
    return {}


class MockAiohttpResponse:
    __aenter__ = return_arg
    __aexit__ = return_None
    json = mock.AsyncMock(wraps=return_dict)
    close = mock.AsyncMock()
    status = 200
    reason = "OK"
    headers = {}
    content_length = 500
    read = mock.AsyncMock(return_value='{"foo": "bar"}')

    @property
    def content_type(self):
        return self.headers.get("Content-Type", "application/json")


class MockAiohttpSession:
    def __init__(self, *a, **k):
        self.mock_response = MockAiohttpResponse()

    def request(self, *a, **k):
        return self.mock_response

    close = mock.AsyncMock()


class MockBaseHTTPClient(http_api_base.HTTPAPIBase):
    def __init__(self, *a, **k):
        with _helpers.mock_patch("aiohttp.ClientSession", new=MockAiohttpSession):
            super().__init__(*a, **k)
        self.json_unmarshaller = json.loads
        self.json_marshaller = json.dumps
        self.json_unmarshaller_object_hook = dict
        self.global_rate_limit = UnslottedMockedGlobalRateLimitFacade(self.loop)

    @property
    def version(self) -> int:
        return 7

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_http_connection(event_loop):
    return MockBaseHTTPClient(loop=event_loop, token="xxx")


@pytest.fixture
def res():
    return http_api_base.Resource("http://test.lan", "get", "/foo/bar")


########################################################################################################################


@pytest.mark.asyncio
async def test_request_forwards_known_arguments_to_request_once(mock_http_connection):
    mock_http_connection.request_once = mock.AsyncMock()
    method = "get"
    path = "/foo/bar/{channel_id}"
    re_seekable_resources = ("foo", "bar", "baz")
    headers = {"foo": "bar", "baz": "bork"}
    query = {"potatos": "good", "spinach": "not so good"}
    data = {"this": "is", "some": "form", "data": "lol"}
    json = {"this": "will", "become": "a", "json": ["o", "b", "j", "e", "c", "t"]}

    await mock_http_connection.request(
        method=method,
        path=path,
        re_seekable_resources=re_seekable_resources,
        headers=headers,
        query=query,
        data=data,
        json=json,
        this_should_not_be_passed=":-)",
        neither_should_this=":-P",
        channel_id="912000",
    )

    res = http_api_base.Resource(
        mock_http_connection.base_uri,
        "get",
        "/foo/bar/{channel_id}",
        this_should_not_be_passed=":-)",
        neither_should_this=":-P",
        channel_id="912000",
    )

    mock_http_connection.request_once.assert_called_once_with(
        resource=res, query=query, data=data, json=json, headers=headers, reason=None
    )

    assert res.params.get("channel_id") == "912000"
    assert res.params.get("guild_id") is None
    assert res.params.get("webhook_id") is None
    assert "/foo/bar/" in res.bucket


@pytest.mark.asyncio
async def test_default_json_parameters():
    with mock.patch("aiohttp.ClientSession") as ClientSession:

        class Deriv(http_api_base.HTTPAPIBase):
            @property
            def version(self) -> int:
                return 69

        Deriv(json_marshaller=None)
        _, kwargs = ClientSession.call_args
        assert "json_serialize" in kwargs, str(kwargs)
        assert kwargs["json_serialize"] is json.dumps


@pytest.mark.asyncio
async def test_detecting_bot_authentication_type(event_loop):
    mock_token = "bot.token"
    mock_http_connection = MockBaseHTTPClient(loop=event_loop, token=mock_token)

    assert mock_http_connection.authorization == f"Bot {mock_token}"


@pytest.mark.asyncio
async def test_detecting_bearer_authentication_type(event_loop):
    mock_token = "bearertoken"
    mock_http_connection = MockBaseHTTPClient(loop=event_loop, token=mock_token)

    assert mock_http_connection.authorization == f"Bearer {mock_token}"


@pytest.mark.asyncio
async def test_detecting_no_authentication_type(event_loop):
    mock_http_connection = MockBaseHTTPClient(loop=event_loop)

    assert mock_http_connection.authorization is None


@pytest.mark.asyncio
async def test_request_retries_indefinitely(mock_http_connection):
    count = 0

    def _request_once(*args, **kwargs):
        nonlocal count
        count += 1
        if count >= 100:
            return
        else:
            raise http_api_base._RateLimited()

    mock_http_connection.request_once = mock.AsyncMock(wraps=_request_once)

    # If we get stuck in a loop, don't hang the tests.
    async with async_timeout.timeout(1000):
        await mock_http_connection.request(method="get", path="/foo/bar")

    assert mock_http_connection.request_once.call_count == 100


@pytest.mark.asyncio
async def test_request_seeks_to_zero_on_each_error_for_each_reseekable_resource_given(mock_http_connection):
    mock_http_connection.request_once = mock.AsyncMock(
        side_effect=[http_api_base._RateLimited, http_api_base._RateLimited, http_api_base._RateLimited, None,]
    )

    re_seekable_resources = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock()]

    await mock_http_connection.request(method="get", path="/foo/bar", re_seekable_resources=re_seekable_resources)

    for re_seekable_resource in re_seekable_resources:
        re_seekable_resource.assert_has_calls([mock.call.seek(0)] * 3)


@pytest.mark.asyncio
async def test_request_does_not_retry_on_success(mock_http_connection):
    expected_result = object()
    mock_http_connection.request_once = mock.AsyncMock(
        side_effect=[http_api_base._RateLimited(), http_api_base._RateLimited(), expected_result]
    )
    actual_result = await mock_http_connection.request(method="get", path="/foo/bar")
    assert mock_http_connection.request_once.call_count == 3
    assert actual_result is expected_result


@pytest.mark.asyncio
async def test_reason_header_is_not_added_if_None_during_request(mock_http_connection):
    mock_http_connection.client_session.request = mock.MagicMock(
        return_value=mock_http_connection.client_session.mock_response
    )
    await mock_http_connection.request("get", "/foo/bar", reason=None)
    args, kwargs = mock_http_connection.client_session.request.call_args
    headers = kwargs["headers"]
    assert "X-Audit-Log-Reason" not in headers


@pytest.mark.asyncio
async def test_reason_header_is_not_added_if_unspecified_during_request(mock_http_connection):
    mock_http_connection.client_session.request = mock.MagicMock(
        return_value=mock_http_connection.client_session.mock_response
    )
    await mock_http_connection.request("get", "/foo/bar", reason=unspecified.UNSPECIFIED)
    args, kwargs = mock_http_connection.client_session.request.call_args
    headers = kwargs["headers"]
    assert "X-Audit-Log-Reason" not in headers


@pytest.mark.asyncio
async def test_reason_header_is_added_if_provided_during_request(mock_http_connection):
    mock_http_connection.client_session.request = mock.MagicMock(
        return_value=mock_http_connection.client_session.mock_response
    )
    await mock_http_connection.request("get", "/foo/bar", reason="because i can")
    args, kwargs = mock_http_connection.client_session.request.call_args
    headers = kwargs["headers"]
    assert headers["X-Audit-Log-Reason"] == "because i can"


@pytest.mark.asyncio
async def test_request_once_calls_session_request_with_expected_arguments(mock_http_connection):
    mock_http_connection.client_session.request = mock.MagicMock(
        return_value=mock_http_connection.client_session.mock_response
    )
    path = "/foo/bar/{channel_id}"
    res = http_api_base.Resource(mock_http_connection.base_uri, "get", path, channel_id="12321")
    headers = {
        "foo": "bar",
        "baz": "bork",
        "User-Agent": "lol i overrode this",
        "Accept": "application/json",
        "Authorization": "lol i overrode this too",
    }
    query = {"potatos": "good", "spinach": "not so good"}
    data = {"this": "is", "some": "form", "data": "lol"}
    json = {"this": "will", "become": "a", "json": ["o", "b", "j", "e", "c", "t"]}

    await mock_http_connection.request_once(resource=res, query=query, data=data, json=json, headers=headers)

    mock_http_connection.client_session.request.assert_called_once_with(
        "GET",
        f"{mock_http_connection.base_uri}/foo/bar/12321",
        params=query,
        data=data,
        json=json,
        headers=headers,
        allow_redirects=mock_http_connection.allow_redirects,
        proxy=None,
        proxy_auth=None,
        proxy_headers=None,
        ssl_context=None,
        timeout=None,
        verify_ssl=True,
    )


@pytest.mark.asyncio
async def test_request_once_acquires_global_rate_limit_bucket(mock_http_connection, res):
    mock_http_connection = mock_methods_on(mock_http_connection, except_=["request_once"])
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b"{}")
    try:
        await mock_http_connection.request_once(resource=res, data={})
        assert False
    except http_api_base._RateLimited:
        mock_http_connection.global_rate_limit.acquire.assert_called_once()


@pytest.mark.asyncio
async def test_request_once_acquires_local_rate_limit_bucket(mock_http_connection, res):
    mock_http_connection = mock_methods_on(mock_http_connection, except_=["request_once"])
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b"{}")
    bucket = mock.MagicMock()
    bucket.acquire = mock.AsyncMock()
    mock_http_connection.buckets[res] = bucket
    try:
        await mock_http_connection.request_once(resource=res, data={})
        assert False
    except http_api_base._RateLimited:
        bucket.acquire.assert_called_once()


@pytest.mark.asyncio
async def test_request_once_calls_rate_limit_handler(mock_http_connection, res):
    mock_http_connection = mock_methods_on(mock_http_connection, except_=["request_once"])
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b"{}")
    try:
        await mock_http_connection.request_once(resource=res)
        assert False
    except http_api_base._RateLimited:
        mock_http_connection._is_rate_limited.assert_called_once()


@pytest.mark.asyncio
async def test_request_once_raises_RateLimited_if_rate_limit_handler_returned_true(mock_http_connection, res):
    mock_http_connection = mock_methods_on(mock_http_connection, except_=["request_once"])
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b"{}")
    mock_http_connection._is_rate_limited = mock.MagicMock(return_value=True)
    try:
        await mock_http_connection.request_once(resource=res)
        assert False
    except http_api_base._RateLimited:
        pass


@pytest.mark.asyncio
async def test_request_once_does_not_raise_RateLimited_if_rate_limit_handler_returned_false(mock_http_connection, res):
    mock_http_connection = mock_methods_on(mock_http_connection, except_=["request_once"])
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b"{}")
    mock_http_connection._is_rate_limited = mock.MagicMock(return_value=False)
    await mock_http_connection.request_once(resource=res)


@pytest.mark.asyncio
async def test_log_rate_limit_already_in_progress_logs_something(mock_http_connection, res):
    mock_http_connection.logger = mock.MagicMock(wraps=mock_http_connection.logger)
    mock_http_connection._log_rate_limit_already_in_progress(res)
    mock_http_connection.logger.debug.assert_called_once()


@pytest.mark.asyncio
async def test_is_rate_limited_locks_global_rate_limit_if_set(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )
    mock_http_connection._is_rate_limited(
        res,
        opcodes.HTTPStatus.TOO_MANY_REQUESTS,
        headers={"X-RateLimit-Global": "true"},
        body={"message": "You are being rate limited", "retry_after": 500, "global": True},
    )

    mock_http_connection.global_rate_limit.lock.assert_called_once_with(0.5)


@pytest.mark.asyncio
async def test_is_rate_limited_returns_True_when_globally_rate_limited(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )
    result = mock_http_connection._is_rate_limited(
        res,
        opcodes.HTTPStatus.TOO_MANY_REQUESTS,
        headers={"X-RateLimit-Global": "true"},
        body={"message": "You are being rate limited", "retry_after": 500, "global": True},
    )

    assert result is True


@pytest.mark.asyncio
async def test_is_rate_limited_does_not_lock_global_rate_limit_if_XRateLimitGlobal_is_false(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )
    mock_http_connection._is_rate_limited(
        res,
        opcodes.HTTPStatus.TOO_MANY_REQUESTS,
        headers={"X-RateLimit-Global": "false"},
        body={"message": "You are being rate limited", "retry_after": 500, "global": False},
    )

    mock_http_connection.global_rate_limit.lock.assert_not_called()


@pytest.mark.asyncio
async def test_is_rate_limited_does_not_lock_global_rate_limit_if_not_a_429_response(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )
    mock_http_connection._is_rate_limited(
        res,
        opcodes.HTTPStatus.OK,
        headers={"X-RateLimit-Global": "true"},  # we will ignore this as it isn't a 429
        body={"message": "You are being rate limited", "retry_after": 500, "global": False},
    )

    mock_http_connection.global_rate_limit.lock.assert_not_called()


@pytest.mark.asyncio
async def test_is_rate_limited_does_not_lock_global_rate_limit_if_XRateLimitGlobal_is_not_present(
    mock_http_connection, res
):
    mock_http_connection = mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )
    mock_http_connection._is_rate_limited(
        res,
        opcodes.HTTPStatus.TOO_MANY_REQUESTS,
        headers={},
        body={"message": "You are being rate limited", "retry_after": 500, "global": False},
    )

    mock_http_connection.global_rate_limit.lock.assert_not_called()


@pytest.mark.asyncio
async def test_is_rate_limited_creates_a_local_bucket_if_one_does_not_exist_for_the_current_resource_locally(
    mock_http_connection, res
):
    mock_http_connection.buckets.clear()
    now = time.time()
    now_dt = email.utils.format_datetime(datetime.datetime.utcnow())
    mock_http_connection = mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )

    assert len(mock_http_connection.buckets) == 0
    mock_http_connection._is_rate_limited(
        res,
        opcodes.HTTPStatus.OK,
        headers={"Date": now_dt, "X-RateLimit-Remaining": 5, "X-RateLimit-Limit": 10, "X-RateLimit-Reset": now + 5},
        body={},
    )

    assert len(mock_http_connection.buckets) == 1
    assert isinstance(mock_http_connection.buckets[res], rates.VariableTokenBucket)


@pytest.mark.asyncio
async def test_is_rate_limited_updates_existing_bucket_if_one_already_exists_for_the_current_resource_locally(
    mock_http_connection, res
):
    mock_http_connection.buckets.clear()
    now = time.time()
    now_dt = email.utils.format_datetime(datetime.datetime.utcnow())
    mock_http_connection = mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )

    actual_bucket = rates.VariableTokenBucket(10, 10, 0, 10, mock_http_connection.loop)
    mock_http_connection.buckets[res] = actual_bucket

    assert len(mock_http_connection.buckets) == 1
    mock_http_connection._is_rate_limited(
        res,
        opcodes.HTTPStatus.OK,
        headers={"Date": now_dt, "X-RateLimit-Remaining": 5, "X-RateLimit-Limit": 10, "X-RateLimit-Reset": now + 5},
        body={},
    )
    assert len(mock_http_connection.buckets) == 1
    assert mock_http_connection.buckets[res] is actual_bucket


@pytest.mark.asyncio
async def test_is_rate_limited_returns_True_if_429_received(mock_http_connection, res):
    mock_http_connection.buckets.clear()
    now = time.time()
    now_dt = email.utils.format_datetime(datetime.datetime.utcnow())
    mock_http_connection = mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )

    result = mock_http_connection._is_rate_limited(
        res,
        opcodes.HTTPStatus.TOO_MANY_REQUESTS,
        headers={"Date": now_dt, "X-RateLimit-Remaining": 0, "X-RateLimit-Limit": 10, "X-RateLimit-Reset": now + 5},
        body={},
    )

    assert result is True


@pytest.mark.asyncio
async def test_is_rate_limited_returns_False_if_not_local_or_global_rate_limit(mock_http_connection, res):
    mock_http_connection.buckets.clear()
    now = time.time()
    now_dt = email.utils.format_datetime(datetime.datetime.utcnow())
    mock_http_connection = mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )

    result = mock_http_connection._is_rate_limited(
        res,
        opcodes.HTTPStatus.OK,
        headers={"Date": now_dt, "X-RateLimit-Remaining": 5, "X-RateLimit-Limit": 10, "X-RateLimit-Reset": now + 5},
        body={},
    )

    assert result is False


@pytest.mark.asyncio
async def test_HTTP_request_has_User_Agent_header_as_expected(mock_http_connection, res):
    # This is a requirement from Discord or they can ban accounts.
    mock_http_connection = mock_methods_on(mock_http_connection, except_=["request_once", "_is_rate_limited"])
    mock_http_connection.client_session.request = mock.MagicMock(wraps=mock_http_connection.client_session.request)
    mock_http_connection.client_session.mock_response.headers["Content-Type"] = "application/json"
    mock_http_connection.client_session.mock_response.status = int(opcodes.HTTPStatus.OK)
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"foo": "bar"}')
    await mock_http_connection.request_once(resource=res)
    assert mock_http_connection.client_session.request.call_count == 1
    args, kwargs = mock_http_connection.client_session.request.call_args_list[0]
    headers = kwargs["headers"]
    user_agent = headers["User-Agent"]
    assert re.match(r"^DiscordBot \(.*?, .*?\).*$", user_agent)


@pytest.mark.asyncio
async def test_HTTP_request_has_XRateLimitPrecision_header_as_expected(mock_http_connection, res):
    # This is a requirement from Discord or they can ban accounts.
    mock_http_connection = mock_methods_on(mock_http_connection, except_=["request_once", "_is_rate_limited"])
    mock_http_connection.client_session.request = mock.MagicMock(wraps=mock_http_connection.client_session.request)

    mock_http_connection.client_session.mock_response.headers["Content-Type"] = "application/json"
    mock_http_connection.client_session.mock_response.status = int(opcodes.HTTPStatus.OK)
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"foo": "bar"}')

    await mock_http_connection.request_once(resource=res)
    assert mock_http_connection.client_session.request.call_count == 1
    args, kwargs = mock_http_connection.client_session.request.call_args_list[0]
    headers = kwargs["headers"]
    precision = headers["X-RateLimit-Precision"]
    assert precision == "millisecond"


@pytest.mark.asyncio
async def test_HTTP_request_has_Authorization_header_if_specified(mock_http_connection, res):
    # This is a requirement from Discord or they can ban accounts.
    mock_http_connection = mock_methods_on(mock_http_connection, except_=["request_once", "_is_rate_limited"])
    mock_http_connection.client_session.request = mock.MagicMock(wraps=mock_http_connection.client_session.request)
    mock_http_connection.client_session.mock_response.headers["Content-Type"] = "application/json"
    mock_http_connection.client_session.mock_response.status = int(opcodes.HTTPStatus.OK)
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"foo": "bar"}')
    mock_http_connection.authorization = "Bot foobar"
    await mock_http_connection.request_once(resource=res)
    assert mock_http_connection.client_session.request.call_count == 1
    args, kwargs = mock_http_connection.client_session.request.call_args_list[0]
    headers = kwargs["headers"]
    assert "Authorization" in headers
    assert headers["Authorization"] == "Bot foobar"


@pytest.mark.asyncio
async def test_HTTP_request_has_no_Authorization_header_if_unspecified(mock_http_connection, res):
    # This is a requirement from Discord or they can ban accounts.
    mock_http_connection = mock_methods_on(mock_http_connection, except_=["request_once", "_is_rate_limited"])
    mock_http_connection.client_session.request = mock.MagicMock(wraps=mock_http_connection.client_session.request)
    mock_http_connection.client_session.mock_response.headers["Content-Type"] = "application/json"
    mock_http_connection.client_session.mock_response.status = int(opcodes.HTTPStatus.OK)
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"foo": "bar"}')
    mock_http_connection.authorization = None
    await mock_http_connection.request_once(resource=res)
    assert mock_http_connection.client_session.request.call_count == 1
    args, kwargs = mock_http_connection.client_session.request.call_args_list[0]
    headers = kwargs["headers"]
    assert "Authorization" not in headers


@pytest.mark.asyncio
async def test_HTTP_request_has_Accept_header(mock_http_connection, res):
    # This is a requirement from Discord or they can ban accounts.
    mock_http_connection = mock_methods_on(mock_http_connection, except_=["request_once", "_is_rate_limited"])
    mock_http_connection.client_session.request = mock.MagicMock(wraps=mock_http_connection.client_session.request)
    mock_http_connection.client_session.mock_response.headers["Content-Type"] = "application/json"
    mock_http_connection.client_session.mock_response.status = int(opcodes.HTTPStatus.OK)
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"foo": "bar"}')
    mock_http_connection.authorization = None
    await mock_http_connection.request_once(resource=res)
    assert mock_http_connection.client_session.request.call_count == 1
    args, kwargs = mock_http_connection.client_session.request.call_args_list[0]
    headers = kwargs["headers"]
    assert "Accept" in headers
    assert headers["Accept"] == "application/json"


@pytest.mark.asyncio
async def test_some_response_that_has_a_json_object_body_gets_decoded_as_expected(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection,
        except_=[
            "request_once",
            "_is_rate_limited",
            "json_marshaller",
            "json_unmarshaller",
            "json_unmarshaller_object_hook",
        ],
    )

    mock_http_connection.client_session.mock_response.headers["Content-Type"] = "application/json"
    mock_http_connection.client_session.mock_response.status = int(opcodes.HTTPStatus.OK)
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"foo": "bar"}')
    body = await mock_http_connection.request_once(resource=res)
    assert body == {"foo": "bar"}


@pytest.mark.asyncio
async def test_plain_text_gets_decoded_as_unicode(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection,
        except_=[
            "request_once",
            "_is_rate_limited",
            "json_marshaller",
            "json_unmarshaller",
            "json_unmarshaller_object_hook",
        ],
    )

    mock_http_connection.client_session.mock_response.headers["Content-Type"] = "text/plain"
    mock_http_connection.client_session.mock_response.status = int(opcodes.HTTPStatus.OK)
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"foo": "bar"}')
    body = await mock_http_connection.request_once(resource=res)
    assert body == '{"foo": "bar"}'


@pytest.mark.asyncio
async def test_html_gets_decoded_as_unicode(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection,
        except_=[
            "request_once",
            "_is_rate_limited",
            "json_marshaller",
            "json_unmarshaller",
            "json_unmarshaller_object_hook",
        ],
    )

    mock_http_connection.client_session.mock_response.headers["Content-Type"] = "text/html"
    mock_http_connection.client_session.mock_response.status = int(opcodes.HTTPStatus.OK)
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(
        return_value=b"<!doctype html><html></html>"
    )
    body = await mock_http_connection.request_once(resource=res)
    assert body == "<!doctype html><html></html>"


@pytest.mark.asyncio
async def test_NO_CONTENT_response_with_no_body_present(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection,
        except_=[
            "request_once",
            "_is_rate_limited",
            "json_marshaller",
            "json_unmarshaller",
            "json_unmarshaller_object_hook",
        ],
    )
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=None)
    mock_http_connection.client_session.mock_response.headers["Content-Type"] = None
    mock_http_connection.client_session.mock_response.status = int(opcodes.HTTPStatus.NO_CONTENT)
    res = http_api_base.Resource("http://test.lan", "get", "/foo/bar")
    body = await mock_http_connection.request_once(resource=res)
    assert not body


@pytest.mark.asyncio
async def test_some_response_that_has_an_unrecognised_content_type_returns_bytes(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection,
        except_=[
            "request_once",
            "_is_rate_limited",
            "json_marshaller",
            "json_unmarshaller",
            "json_unmarshaller_object_hook",
        ],
    )

    mock_http_connection.client_session.mock_response.headers["Content-Type"] = "mac-and/cheese"
    mock_http_connection.client_session.mock_response.status = int(opcodes.HTTPStatus.CREATED)
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"foo": "bar"}')
    body = await mock_http_connection.request_once(resource=res)
    assert isinstance(body, bytes)


@pytest.mark.asyncio
async def test_4xx_hits_handle_client_error_response(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection,
        except_=[
            "request_once",
            "_is_rate_limited",
            "json_marshaller",
            "json_unmarshaller",
            "json_unmarshaller_object_hook",
        ],
    )

    mock_http_connection.client_session.mock_response.headers["Content-Type"] = "application/json"
    mock_http_connection.client_session.mock_response.status = int(opcodes.HTTPStatus.BAD_REQUEST)
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"foo": "bar"}')
    await mock_http_connection.request_once(resource=res)
    mock_http_connection._handle_client_error_response.assert_called_once_with(
        res, opcodes.HTTPStatus.BAD_REQUEST, {"foo": "bar"}
    )


@pytest.mark.asyncio
async def test_5xx_hits_handle_server_error_response(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection,
        except_=[
            "request_once",
            "_is_rate_limited",
            "json_marshaller",
            "json_unmarshaller",
            "json_unmarshaller_object_hook",
        ],
    )

    mock_http_connection.client_session.mock_response.headers["Content-Type"] = "application/json"
    mock_http_connection.client_session.mock_response.status = int(opcodes.HTTPStatus.GATEWAY_TIMEOUT)
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"foo": "bar"}')
    await mock_http_connection.request_once(resource=res)
    mock_http_connection._handle_server_error_response.assert_called_once_with(
        res, opcodes.HTTPStatus.GATEWAY_TIMEOUT, {"foo": "bar"}
    )


@pytest.mark.asyncio
async def test_ValueError_on_unrecognised_HTTP_status(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection,
        except_=[
            "request_once",
            "_is_rate_limited",
            "json_marshaller",
            "json_unmarshaller",
            "json_unmarshaller_object_hook",
        ],
    )
    mock_http_connection._is_rate_limited = mock.MagicMock(return_value=False)
    mock_http_connection.client_session.mock_response.status = 669
    mock_http_connection.client_session.mock_response.headers = {"foo": "bar", "baz": "bork"}
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"lorem":"ipsum"}')
    try:
        await mock_http_connection.request_once(resource=res)
        assert False, "No exception raised"
    except ValueError:
        pass


@pytest.mark.asyncio
async def test_2xx_returns_object(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection,
        except_=[
            "request_once",
            "_is_rate_limited",
            "json_marshaller",
            "json_unmarshaller",
            "json_unmarshaller_object_hook",
        ],
    )
    mock_http_connection._is_rate_limited = mock.MagicMock(return_value=False)
    mock_http_connection.client_session.mock_response.status = 201
    mock_http_connection.client_session.mock_response.headers = {"foo": "bar", "baz": "bork"}
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"lorem":"ipsum"}')
    result = await mock_http_connection.request_once(resource=res)
    # Assert we can unpack as tuple
    assert result == {"lorem": "ipsum"}


@pytest.mark.asyncio
async def test_3xx_returns_tuple(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection,
        except_=[
            "request_once",
            "_is_rate_limited",
            "json_marshaller",
            "json_unmarshaller",
            "json_unmarshaller_object_hook",
        ],
    )
    mock_http_connection._is_rate_limited = mock.MagicMock(return_value=False)
    mock_http_connection.client_session.mock_response.status = 304
    mock_http_connection.client_session.mock_response.headers = {"foo": "bar", "baz": "bork"}
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"lorem":"ipsum"}')
    result = await mock_http_connection.request_once(resource=res)
    # Assert we can unpack as tuple
    assert result == {"lorem": "ipsum"}


@pytest.mark.asyncio
async def test_4xx_is_handled_as_4xx_error_response(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection,
        except_=[
            "request_once",
            "_is_rate_limited",
            "json_marshaller",
            "json_unmarshaller",
            "json_unmarshaller_object_hook",
        ],
    )
    mock_http_connection._is_rate_limited = mock.MagicMock(return_value=False)
    mock_http_connection.client_session.mock_response.status = 401
    mock_http_connection.client_session.mock_response.headers = {"foo": "bar", "baz": "bork"}
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"lorem":"ipsum"}')
    await mock_http_connection.request_once(resource=res)
    mock_http_connection._handle_client_error_response.assert_called_once_with(
        res, opcodes.HTTPStatus(401), {"lorem": "ipsum"}
    )


@pytest.mark.asyncio
async def test_5xx_is_handled_as_5xx_error_response(mock_http_connection, res):
    mock_http_connection = mock_methods_on(
        mock_http_connection,
        except_=[
            "request_once",
            "_is_rate_limited",
            "json_marshaller",
            "json_unmarshaller",
            "json_unmarshaller_object_hook",
        ],
    )
    mock_http_connection._is_rate_limited = mock.MagicMock(return_value=False)
    mock_http_connection.client_session.mock_response.status = 501
    mock_http_connection.client_session.mock_response.headers = {"foo": "bar", "baz": "bork"}
    mock_http_connection.client_session.mock_response.read = mock.AsyncMock(return_value=b'{"lorem":"ipsum"}')
    await mock_http_connection.request_once(resource=res)
    mock_http_connection._handle_server_error_response.assert_called_once_with(
        res, opcodes.HTTPStatus(501), {"lorem": "ipsum"}
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["status", "exception_type"],
    [
        (opcodes.HTTPStatus.BAD_REQUEST, errors.BadRequest),
        (opcodes.HTTPStatus.UNAUTHORIZED, errors.UnauthorizedError),
        (opcodes.HTTPStatus.FORBIDDEN, errors.ForbiddenError),
        (opcodes.HTTPStatus.NOT_FOUND, errors.NotFoundError),
        (opcodes.HTTPStatus.TOO_MANY_REQUESTS, errors.ClientError),
        (opcodes.HTTPStatus.NO_CONTENT, errors.ClientError),  # I know this isn't a 4xx.
    ],
)
async def test_handle_client_error_response_when_no_error_in_json(status, exception_type, mock_http_connection, res):
    pl = {"foo": "bar", "code": int(opcodes.JSONErrorCode.USERS_ONLY)}
    try:
        mock_http_connection._handle_client_error_response(res, status, pl)
        assert False, "No exception was raised"
    except exception_type as ex:
        assert ex.status == status
        assert ex.error_code is opcodes.JSONErrorCode.USERS_ONLY
        assert ex.message is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["status", "exception_type"],
    [
        (opcodes.HTTPStatus.BAD_REQUEST, errors.BadRequest),
        (opcodes.HTTPStatus.UNAUTHORIZED, errors.UnauthorizedError),
        (opcodes.HTTPStatus.FORBIDDEN, errors.ForbiddenError),
        (opcodes.HTTPStatus.NOT_FOUND, errors.NotFoundError),
        (opcodes.HTTPStatus.TOO_MANY_REQUESTS, errors.ClientError),
        (opcodes.HTTPStatus.NO_CONTENT, errors.ClientError),  # I know this isn't a 4xx.
    ],
)
async def test_handle_client_error_response_when_only_message_in_json_body(
    status, exception_type, mock_http_connection, res
):
    try:
        mock_http_connection._handle_client_error_response(res, status, {"foo": "bar", "message": "foo"})
        assert False, "No exception was raised"
    except exception_type as ex:
        assert ex.status == status
        assert ex.error_code is None
        assert ex.message == "foo"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["status", "exception_type"],
    [
        (opcodes.HTTPStatus.BAD_REQUEST, errors.BadRequest),
        (opcodes.HTTPStatus.UNAUTHORIZED, errors.UnauthorizedError),
        (opcodes.HTTPStatus.FORBIDDEN, errors.ForbiddenError),
        (opcodes.HTTPStatus.NOT_FOUND, errors.NotFoundError),
        (opcodes.HTTPStatus.TOO_MANY_REQUESTS, errors.ClientError),
        (opcodes.HTTPStatus.NO_CONTENT, errors.ClientError),  # I know this isn't a 4xx.
    ],
)
async def test_handle_client_error_response_when_only_error_code_in_json_body(
    status, exception_type, mock_http_connection, res
):
    pl = {"foo": "bar", "code": 10001}
    try:
        mock_http_connection._handle_client_error_response(res, status, pl)
        assert False, "No exception was raised"
    except exception_type as ex:
        assert ex.status == status
        assert ex.error_code is opcodes.JSONErrorCode.UNKNOWN_ACCOUNT
        assert ex.message is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["status", "exception_type"],
    [
        (opcodes.HTTPStatus.BAD_REQUEST, errors.BadRequest),
        (opcodes.HTTPStatus.UNAUTHORIZED, errors.UnauthorizedError),
        (opcodes.HTTPStatus.FORBIDDEN, errors.ForbiddenError),
        (opcodes.HTTPStatus.NOT_FOUND, errors.NotFoundError),
        (opcodes.HTTPStatus.TOO_MANY_REQUESTS, errors.ClientError),
        (opcodes.HTTPStatus.NO_CONTENT, errors.ClientError),  # I know this isn't a 4xx.
    ],
)
async def test_handle_client_error_response_when_not_json_body(status, exception_type, mock_http_connection, res):
    try:
        mock_http_connection._handle_client_error_response(res, status, "potato")
        assert False, "No exception was raised"
    except exception_type as ex:
        assert ex.status == status
        assert ex.error_code is None
        assert ex.message == "potato"


@pytest.mark.asyncio
async def test_handle_server_error_response_when_body_has_a_message_and_is_a_dict(mock_http_connection, res):
    try:
        mock_http_connection._handle_server_error_response(res, opcodes.HTTPStatus.GATEWAY_TIMEOUT, {"message": "aaah"})
        assert False, "No exception was raised"
    except errors.ServerError as ex:
        assert ex.message == "aaah"


@pytest.mark.asyncio
async def test_handle_server_error_response_when_body_has_a_dict_without_a_message(mock_http_connection, res):
    try:
        mock_http_connection._handle_server_error_response(res, opcodes.HTTPStatus.GATEWAY_TIMEOUT, {"foo": "bar"})
        assert False, "No exception was raised"
    except errors.ServerError as ex:
        assert ex.message == opcodes.HTTPStatus.GATEWAY_TIMEOUT.name.replace("_", " ").title()


@pytest.mark.asyncio
async def test_handle_server_error_response_when_body_is_not_a_dict(mock_http_connection, res):
    try:
        mock_http_connection._handle_server_error_response(res, opcodes.HTTPStatus.GATEWAY_TIMEOUT, "errrooorr")
        assert False, "No exception was raised"
    except errors.ServerError as ex:
        assert ex.message == "errrooorr"


def test_Resource_bucket():
    a = http_api_base.Resource(
        "http://base.lan",
        "get",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    b = http_api_base.Resource(
        "http://base.lan",
        "GET",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    c = http_api_base.Resource(
        "http://base.lan", "get", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )
    d = http_api_base.Resource(
        "http://base.lan", "post", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )

    assert a.bucket == b.bucket
    assert c.bucket != d.bucket
    assert a.bucket == c.bucket
    assert b.bucket == c.bucket
    assert a.bucket != d.bucket
    assert b.bucket != d.bucket


def test_Resource_hash():
    a = http_api_base.Resource(
        "http://base.lan",
        "get",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    b = http_api_base.Resource(
        "http://base.lan",
        "GET",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    c = http_api_base.Resource(
        "http://base.lan", "get", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )
    d = http_api_base.Resource(
        "http://base.lan", "post", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )

    assert hash(a) == hash(b)
    assert hash(c) != hash(d)
    assert hash(a) == hash(c)
    assert hash(b) == hash(c)
    assert hash(a) != hash(d)
    assert hash(b) != hash(d)


def test_Resource_equality():
    a = http_api_base.Resource(
        "http://base.lan",
        "get",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    b = http_api_base.Resource(
        "http://base.lan",
        "GET",
        "/foo/bar",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
        webhook_id="91011",
    )
    c = http_api_base.Resource(
        "http://base.lan", "get", "/foo/bar", channel_id="1234", potatos="toast", guild_id="5678", webhook_id="91011"
    )
    d = http_api_base.Resource(
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
    a = http_api_base.Resource(
        "http://foo.com",
        "get",
        "/foo/{channel_id}/bar/{guild_id}/baz/{potatos}",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
    )
    assert a.uri == "http://foo.com/foo/1234/bar/5678/baz/spaghetti"


def test_resource_repr():
    a = http_api_base.Resource(
        "http://foo.com",
        "get",
        "/foo/{channel_id}/bar/{guild_id}/baz/{potatos}",
        channel_id="1234",
        potatos="spaghetti",
        guild_id="5678",
    )

    assert repr(a) == "GET /foo/1234/bar/5678/baz/{potatos}"
