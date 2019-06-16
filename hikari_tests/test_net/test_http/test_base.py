#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests the low level handler logic all endpoints will be expected to use.
"""
import asyncio
import datetime
import email
import re
import time

import asynctest
import pytest

import hikari.net.utils
from hikari import errors
from hikari.net import opcodes
from hikari.net import rates
from hikari.net.http import base
from hikari_tests._helpers import _mock_methods_on


########################################################################################################################


class UnslottedMockedGlobalRateLimitFacade(rates.TimedLatchBucket):
    """This has no slots so allows injection of mocks, et cetera."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apparently an issue on CPython3.6 where it can't determine if this is a coroutine or not.
        self.acquire = asynctest.CoroutineMock()


class MockAiohttpResponse:
    __aenter__ = asyncio.coroutine(lambda self: self)
    __aexit__ = asyncio.coroutine(lambda self, *_, **__: None)
    json = asynctest.CoroutineMock(wraps=asyncio.coroutine(lambda _: {}))
    close = asynctest.CoroutineMock()
    status = 200
    reason = "OK"
    headers = {}
    content_length = 500
    read = asynctest.CoroutineMock(return_value=None)

    @property
    def content_type(self):
        return self.headers.get("Content-Type", "application/json")


class MockAiohttpSession:
    def __init__(self, *a, **k):
        self.mock_response = MockAiohttpResponse()

    def request(self, *a, **k):
        return self.mock_response

    close = asynctest.CoroutineMock()


class MockBaseHTTPClient(base.BaseHTTPClient):
    def __init__(self, *a, **k):
        with asynctest.patch("aiohttp.ClientSession", new=MockAiohttpSession):
            super().__init__(*a, **k)
        self.global_rate_limit = UnslottedMockedGlobalRateLimitFacade(self.loop)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_http_connection(event_loop):
    return MockBaseHTTPClient(loop=event_loop, token="xxx")


@pytest.fixture
def res():
    return hikari.net.utils.Resource("http://test.lan", "get", "/foo/bar")


########################################################################################################################


@pytest.mark.asyncio
async def test_close_will_close_session(mock_http_connection):
    await mock_http_connection.close()
    mock_http_connection.session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_retries_then_errors(mock_http_connection):
    mock_http_connection._request_once = asynctest.CoroutineMock(side_effect=base._RateLimited)
    try:
        await mock_http_connection.request(method="get", path="/foo/bar")
        assert False, "No error was thrown but it was expected!"
    except errors.ClientError:
        pass

    assert mock_http_connection._request_once.call_count == 5


@pytest.mark.asyncio
async def test_request_does_not_retry_on_success(mock_http_connection):
    expected_result = object()
    mock_http_connection._request_once = asynctest.CoroutineMock(
        side_effect=[base._RateLimited(), base._RateLimited(), expected_result]
    )
    actual_result = await mock_http_connection.request(method="get", path="/foo/bar")
    assert mock_http_connection._request_once.call_count == 3
    assert actual_result is expected_result


@pytest.mark.asyncio
async def test_request_once_acquires_global_rate_limit_bucket(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once"])
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b"{}")
    try:
        await mock_http_connection._request_once(retry=0, resource=res, json_body={})
        assert False
    except base._RateLimited:
        mock_http_connection.global_rate_limit.acquire.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_once_acquires_local_rate_limit_bucket(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once"])
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b"{}")
    bucket = asynctest.MagicMock()
    bucket.acquire = asynctest.CoroutineMock()
    mock_http_connection.buckets[res] = bucket
    try:
        await mock_http_connection._request_once(retry=0, resource=res, json_body={})
        assert False
    except base._RateLimited:
        bucket.acquire.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_once_calls_rate_limit_handler(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once"])
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b"{}")
    try:
        await mock_http_connection._request_once(retry=0, resource=res)
        assert False
    except base._RateLimited:
        mock_http_connection._is_rate_limited.assert_called_once()


@pytest.mark.asyncio
async def test_request_once_raises_RateLimited_if_rate_limit_handler_returned_true(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once"])
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b"{}")
    mock_http_connection._is_rate_limited = asynctest.MagicMock(return_value=True)
    try:
        await mock_http_connection._request_once(retry=0, resource=res)
        assert False
    except base._RateLimited:
        pass


@pytest.mark.asyncio
async def test_request_once_does_not_raise_RateLimited_if_rate_limit_handler_returned_false(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once"])
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b"{}")
    mock_http_connection._is_rate_limited = asynctest.MagicMock(return_value=False)
    await mock_http_connection._request_once(retry=0, resource=res)


@pytest.mark.asyncio
async def test_log_rate_limit_already_in_progress_logs_something(mock_http_connection, res):
    mock_http_connection.logger = asynctest.MagicMock(wraps=mock_http_connection.logger)
    mock_http_connection._log_rate_limit_already_in_progress(res)
    mock_http_connection.logger.debug.assert_called_once()


@pytest.mark.asyncio
async def test_log_rate_limit_starting_logs_something(mock_http_connection, res):
    mock_http_connection.logger = asynctest.MagicMock(wraps=mock_http_connection.logger)
    mock_http_connection._log_rate_limit_starting(res, 123.45)
    mock_http_connection.logger.debug.assert_called_once()


@pytest.mark.asyncio
async def test_is_rate_limited_locks_global_rate_limit_if_set(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(
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
    mock_http_connection = _mock_methods_on(
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
async def test_is_rate_limited_calls_log_rate_limit_starting(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )
    mock_http_connection._is_rate_limited(
        res,
        opcodes.HTTPStatus.TOO_MANY_REQUESTS,
        headers={"X-RateLimit-Global": "true"},
        body={"message": "You are being rate limited", "retry_after": 500, "global": True},
    )

    mock_http_connection._log_rate_limit_starting.assert_called_once()


@pytest.mark.asyncio
async def test_is_rate_limited_does_not_lock_global_rate_limit_if_XRateLimitGlobal_is_false(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(
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
    mock_http_connection = _mock_methods_on(
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
    mock_http_connection = _mock_methods_on(
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
    mock_http_connection = _mock_methods_on(
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
    mock_http_connection = _mock_methods_on(
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
async def test_is_rate_limited_doesnt_call_log_rate_limit_starting_if_not_locking_locally(mock_http_connection, res):
    mock_http_connection.buckets.clear()
    now = time.time()
    now_dt = email.utils.format_datetime(datetime.datetime.utcnow())
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )

    mock_http_connection._is_rate_limited(
        res,
        opcodes.HTTPStatus.OK,
        headers={"Date": now_dt, "X-RateLimit-Remaining": 5, "X-RateLimit-Limit": 10, "X-RateLimit-Reset": now + 5},
        body={},
    )

    mock_http_connection._log_rate_limit_starting.assert_not_called()


@pytest.mark.asyncio
async def test_is_rate_limited_calls_log_rate_limit_starting_if_locking_locally(mock_http_connection, res):
    mock_http_connection.buckets.clear()
    now = time.time()
    now_dt = email.utils.format_datetime(datetime.datetime.utcnow())
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )

    mock_http_connection._is_rate_limited(
        res,
        opcodes.HTTPStatus.OK,
        headers={"Date": now_dt, "X-RateLimit-Remaining": 0, "X-RateLimit-Limit": 10, "X-RateLimit-Reset": now + 5},
        body={},
    )

    mock_http_connection._log_rate_limit_starting.assert_called_once()


@pytest.mark.asyncio
async def test_is_rate_limited_returns_True_if_local_rate_limit(mock_http_connection, res):
    mock_http_connection.buckets.clear()
    now = time.time()
    now_dt = email.utils.format_datetime(datetime.datetime.utcnow())
    mock_http_connection = _mock_methods_on(
        mock_http_connection, except_=["_is_rate_limited"], also_mock=["global_rate_limit"]
    )

    result = mock_http_connection._is_rate_limited(
        res,
        opcodes.HTTPStatus.OK,
        headers={"Date": now_dt, "X-RateLimit-Remaining": 0, "X-RateLimit-Limit": 10, "X-RateLimit-Reset": now + 5},
        body={},
    )

    assert result is True


@pytest.mark.asyncio
async def test_is_rate_limited_returns_False_if_not_local_or_global_rate_limit(mock_http_connection, res):
    mock_http_connection.buckets.clear()
    now = time.time()
    now_dt = email.utils.format_datetime(datetime.datetime.utcnow())
    mock_http_connection = _mock_methods_on(
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
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once", "_is_rate_limited"])
    mock_http_connection.session.request = asynctest.MagicMock(wraps=mock_http_connection.session.request)
    mock_http_connection.session.mock_response.headers["Content-Type"] = "application/json"
    mock_http_connection.session.mock_response.status = int(opcodes.HTTPStatus.OK)
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b'{"foo": "bar"}')
    await mock_http_connection._request_once(retry=0, resource=res)
    assert mock_http_connection.session.request.call_count == 1
    args, kwargs = mock_http_connection.session.request.call_args_list[0]
    headers = kwargs["headers"]
    user_agent = headers["User-Agent"]
    assert re.match(r"^DiscordBot \(.*?, .*?\).*$", user_agent)


@pytest.mark.asyncio
async def test_some_response_that_has_a_json_object_body_gets_decoded_as_expected(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once", "_is_rate_limited"])

    mock_http_connection.session.mock_response.headers["Content-Type"] = "application/json"
    mock_http_connection.session.mock_response.status = int(opcodes.HTTPStatus.OK)
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b'{"foo": "bar"}')
    status, headers, body = await mock_http_connection._request_once(retry=0, resource=res)
    assert status is opcodes.HTTPStatus.OK
    assert body == {"foo": "bar"}


@pytest.mark.asyncio
async def test_plain_text_gets_decoded_as_unicode(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once", "_is_rate_limited"])

    mock_http_connection.session.mock_response.headers["Content-Type"] = "text/plain"
    mock_http_connection.session.mock_response.status = int(opcodes.HTTPStatus.OK)
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b'{"foo": "bar"}')
    status, headers, body = await mock_http_connection._request_once(retry=0, resource=res)
    assert status is opcodes.HTTPStatus.OK
    assert body == '{"foo": "bar"}'


@pytest.mark.asyncio
async def test_html_gets_decoded_as_unicode(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once", "_is_rate_limited"])

    mock_http_connection.session.mock_response.headers["Content-Type"] = "text/html"
    mock_http_connection.session.mock_response.status = int(opcodes.HTTPStatus.OK)
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(
        return_value=b"<!doctype html><html></html>"
    )
    status, headers, body = await mock_http_connection._request_once(retry=0, resource=res)
    assert status is opcodes.HTTPStatus.OK
    assert body == "<!doctype html><html></html>"


@pytest.mark.asyncio
async def test_NO_CONTENT_response_with_no_body_present(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once", "_is_rate_limited"])

    mock_http_connection.session.mock_response.headers["Content-Type"] = None
    mock_http_connection.session.mock_response.status = int(opcodes.HTTPStatus.NO_CONTENT)
    res = hikari.net.utils.Resource("http://test.lan", "get", "/foo/bar")
    status, headers, body = await mock_http_connection._request_once(retry=0, resource=res)
    assert status is opcodes.HTTPStatus.NO_CONTENT
    assert body is None


@pytest.mark.asyncio
async def test_some_response_that_has_an_unrecognised_content_type_returns_bytes(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once", "_is_rate_limited"])

    mock_http_connection.session.mock_response.headers["Content-Type"] = "mac-and/cheese"
    mock_http_connection.session.mock_response.status = int(opcodes.HTTPStatus.CREATED)
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b'{"foo": "bar"}')
    status, headers, body = await mock_http_connection._request_once(retry=0, resource=res)
    assert isinstance(body, bytes)


@pytest.mark.asyncio
async def test_4xx_hits_handle_client_error_response(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once", "_is_rate_limited"])

    mock_http_connection.session.mock_response.headers["Content-Type"] = "application/json"
    mock_http_connection.session.mock_response.status = int(opcodes.HTTPStatus.BAD_REQUEST)
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b'{"foo": "bar"}')
    await mock_http_connection._request_once(retry=0, resource=res)
    mock_http_connection._handle_client_error_response.assert_called_once_with(
        res, opcodes.HTTPStatus.BAD_REQUEST, {"foo": "bar"}
    )


@pytest.mark.asyncio
async def test_5xx_hits_handle_server_error_response(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once", "_is_rate_limited"])

    mock_http_connection.session.mock_response.headers["Content-Type"] = "application/json"
    mock_http_connection.session.mock_response.status = int(opcodes.HTTPStatus.GATEWAY_TIMEOUT)
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b'{"foo": "bar"}')
    await mock_http_connection._request_once(retry=0, resource=res)
    mock_http_connection._handle_server_error_response.assert_called_once_with(
        res, opcodes.HTTPStatus.GATEWAY_TIMEOUT, {"foo": "bar"}
    )


@pytest.mark.asyncio
async def test_ValueError_on_unrecognised_HTTP_status(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once"])
    mock_http_connection._is_rate_limited = asynctest.MagicMock(return_value=False)
    mock_http_connection.session.mock_response.status = 669
    mock_http_connection.session.mock_response.headers = {"foo": "bar", "baz": "bork"}
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b'{"lorem":"ipsum"}')
    try:
        await mock_http_connection._request_once(retry=0, resource=res)
        assert False, "No exception raised"
    except ValueError:
        pass


@pytest.mark.asyncio
async def test_2xx_returns_tuple(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once"])
    mock_http_connection._is_rate_limited = asynctest.MagicMock(return_value=False)
    mock_http_connection.session.mock_response.status = 201
    mock_http_connection.session.mock_response.headers = {"foo": "bar", "baz": "bork"}
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b'{"lorem":"ipsum"}')
    result = await mock_http_connection._request_once(retry=0, resource=res)
    # Assert we can unpack as tuple
    status, headers, body = result

    assert status == 201
    assert headers == {"foo": "bar", "baz": "bork"}
    assert body == {"lorem": "ipsum"}


@pytest.mark.asyncio
async def test_3xx_returns_tuple(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once"])
    mock_http_connection._is_rate_limited = asynctest.MagicMock(return_value=False)
    mock_http_connection.session.mock_response.status = 304
    mock_http_connection.session.mock_response.headers = {"foo": "bar", "baz": "bork"}
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b'{"lorem":"ipsum"}')
    result = await mock_http_connection._request_once(retry=0, resource=res)
    # Assert we can unpack as tuple
    status, headers, body = result

    assert status == 304
    assert headers == {"foo": "bar", "baz": "bork"}
    assert body == {"lorem": "ipsum"}


@pytest.mark.asyncio
async def test_4xx_is_handled_as_4xx_error_response(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once"])
    mock_http_connection._is_rate_limited = asynctest.MagicMock(return_value=False)
    mock_http_connection.session.mock_response.status = 401
    mock_http_connection.session.mock_response.headers = {"foo": "bar", "baz": "bork"}
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b'{"lorem":"ipsum"}')
    await mock_http_connection._request_once(retry=0, resource=res)
    mock_http_connection._handle_client_error_response.assert_called_once_with(
        res, opcodes.HTTPStatus(401), {"lorem": "ipsum"}
    )


@pytest.mark.asyncio
async def test_5xx_is_handled_as_5xx_error_response(mock_http_connection, res):
    mock_http_connection = _mock_methods_on(mock_http_connection, except_=["_request_once"])
    mock_http_connection._is_rate_limited = asynctest.MagicMock(return_value=False)
    mock_http_connection.session.mock_response.status = 501
    mock_http_connection.session.mock_response.headers = {"foo": "bar", "baz": "bork"}
    mock_http_connection.session.mock_response.read = asynctest.CoroutineMock(return_value=b'{"lorem":"ipsum"}')
    await mock_http_connection._request_once(retry=0, resource=res)
    mock_http_connection._handle_server_error_response.assert_called_once_with(
        res, opcodes.HTTPStatus(501), {"lorem": "ipsum"}
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["status", "exception_type"],
    [
        (opcodes.HTTPStatus.BAD_REQUEST, errors.BadRequest),
        (opcodes.HTTPStatus.UNAUTHORIZED, errors.Unauthorized),
        (opcodes.HTTPStatus.FORBIDDEN, errors.Forbidden),
        (opcodes.HTTPStatus.NOT_FOUND, errors.NotFound),
        (opcodes.HTTPStatus.TOO_MANY_REQUESTS, errors.ClientError),
        (opcodes.HTTPStatus.NO_CONTENT, errors.ClientError),  # I know this isn't a 4xx.
    ],
    ids=lambda status: f" considering {status} ",
)
async def test_handle_client_error_response_when_no_error_in_json(status, exception_type, mock_http_connection, res):
    try:
        mock_http_connection._handle_client_error_response(res, status, {"foo": "bar"})
        assert False, "No exception was raised"
    except exception_type as ex:
        assert ex.status == status
        assert ex.error_code is None
        assert ex.message is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["status", "exception_type"],
    [
        (opcodes.HTTPStatus.BAD_REQUEST, errors.BadRequest),
        (opcodes.HTTPStatus.UNAUTHORIZED, errors.Unauthorized),
        (opcodes.HTTPStatus.FORBIDDEN, errors.Forbidden),
        (opcodes.HTTPStatus.NOT_FOUND, errors.NotFound),
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
        (opcodes.HTTPStatus.UNAUTHORIZED, errors.Unauthorized),
        (opcodes.HTTPStatus.FORBIDDEN, errors.Forbidden),
        (opcodes.HTTPStatus.NOT_FOUND, errors.NotFound),
        (opcodes.HTTPStatus.TOO_MANY_REQUESTS, errors.ClientError),
        (opcodes.HTTPStatus.NO_CONTENT, errors.ClientError),  # I know this isn't a 4xx.
    ],
)
async def test_handle_client_error_response_when_only_error_code_in_json_body(
    status, exception_type, mock_http_connection, res
):
    try:
        mock_http_connection._handle_client_error_response(res, status, {"foo": "bar", "code": 10_001})
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
        (opcodes.HTTPStatus.UNAUTHORIZED, errors.Unauthorized),
        (opcodes.HTTPStatus.FORBIDDEN, errors.Forbidden),
        (opcodes.HTTPStatus.NOT_FOUND, errors.NotFound),
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
