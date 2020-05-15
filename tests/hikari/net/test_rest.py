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
import asyncio
import contextlib
import datetime
import email.utils
import http
import json
import logging

import aiohttp
import mock
import pytest

from hikari import errors
from hikari import files
from hikari.internal import conversions
from hikari.net import http_client
from hikari.net import ratelimits
from hikari.net import rest
from hikari.net import routes
from tests.hikari import _helpers


class MockResponse:
    def __init__(self, body=None, status=204, real_url="http://example.com", content_type=None, headers=None, **kwargs):
        self.body = body
        self.status = status
        self.real_url = real_url
        self.content_type = content_type
        headers = {} if headers is None else headers
        headers["content-type"] = content_type
        headers.setdefault("date", email.utils.format_datetime(datetime.datetime.utcnow()))
        self.headers = headers
        self.__dict__.update(kwargs)

    async def read(self):
        return self.body

    async def json(self):
        return json.loads(await self.read())


@contextlib.contextmanager
def mock_patch_route(real_route):
    compiled_route = mock.MagicMock(routes.CompiledRoute)
    compile = mock.Mock(spec=routes.RouteTemplate.compile, spec_set=True, return_value=compiled_route)
    route_template = mock.MagicMock(spec_set=routes.RouteTemplate, compile=compile)
    with mock.patch.object(routes, real_route, new=route_template):
        yield route_template, compiled_route


# noinspection PyUnresolvedReferences
@pytest.mark.asyncio
class TestRESTInit:
    async def test_base_url_is_formatted_correctly(self):
        async with rest.REST(base_url="http://example.com/api/v{0.version}/test", token=None, version=69) as client:
            assert client.base_url == "http://example.com/api/v69/test"

    async def test_no_token_sets_field_to_None(self):
        async with rest.REST(token=None) as client:
            assert client._token is None

    @_helpers.assert_raises(type_=RuntimeError)
    async def test_bare_old_token_without_auth_scheme_raises_error(self):
        async with rest.REST(token="1a2b.3c4d") as client:
            pass

    @_helpers.assert_raises(type_=RuntimeError)
    async def test_bare_old_token_without_recognised_auth_scheme_raises_error(self):
        async with rest.REST(token="Token 1a2b.3c4d") as client:
            pass

    @pytest.mark.parametrize("auth_type", ["Bot", "Bearer"])
    async def test_known_auth_type_is_allowed(self, auth_type):
        token = f"{auth_type} 1a2b.3c4d"
        async with rest.REST(token=token) as client:
            assert client._token == token


@pytest.mark.asyncio
class TestRESTClose:
    @pytest.fixture
    def rest_impl(self, event_loop):
        rest_impl = rest.REST(token="Bot token")
        yield rest_impl
        event_loop.run_until_complete(super(rest.REST, rest_impl).close())
        rest_impl.bucket_ratelimiters.close()
        rest_impl.global_ratelimiter.close()

    @pytest.mark.parametrize("ratelimiter", ["bucket_ratelimiters", "global_ratelimiter"])
    async def test_close_calls_ratelimiter_close(self, rest_impl, ratelimiter):
        with mock.patch.object(rest_impl, ratelimiter) as m:
            await rest_impl.close()
        m.close.assert_called_once_with()


@pytest.fixture
def compiled_route():
    template = routes.RouteTemplate("POST", "/foo/{bar}/baz")
    return routes.CompiledRoute(template, "/foo/bar/baz", "1a2a3b4b5c6d")


@pytest.mark.asyncio
class TestRESTRequestJsonResponse:
    @pytest.fixture
    def bucket_ratelimiters(self):
        limiter = mock.MagicMock(spec_set=ratelimits.RESTBucketManager)
        limiter.acquire = mock.MagicMock(return_value=_helpers.AwaitableMock())
        return limiter

    @pytest.fixture
    def global_ratelimiter(self):
        limiter = mock.MagicMock(spec_set=ratelimits.ManualRateLimiter)
        limiter.acquire = mock.MagicMock(return_value=_helpers.AwaitableMock())
        return limiter

    @pytest.fixture
    def rest_impl(self, bucket_ratelimiters, global_ratelimiter):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(http_client.HTTPClient, "__init__", new=lambda *_, **__: None))
        stack.enter_context(mock.patch.object(ratelimits, "RESTBucketManager", return_value=bucket_ratelimiters))
        stack.enter_context(mock.patch.object(ratelimits, "ManualRateLimiter", return_value=global_ratelimiter))
        with stack:
            client = rest.REST(base_url="http://example.bloop.com", token="Bot blah.blah.blah")
        client.logger = mock.MagicMock(spec_set=logging.Logger)
        client.json_deserialize = json.loads
        client.serialize = json.dumps
        client._perform_request = mock.AsyncMock(spec_set=client._perform_request, return_value=MockResponse(None))
        client._handle_rate_limits_for_response = mock.AsyncMock()
        return client

    async def test_bucket_ratelimiters_are_started_when_not_running(self, rest_impl, compiled_route):
        # given
        rest_impl.bucket_ratelimiters.is_started = False
        # when
        await rest_impl._request_json_response(compiled_route)
        # then
        rest_impl.bucket_ratelimiters.start.assert_called_once_with()

    async def test_bucket_ratelimiters_are_not_restarted_when_already_running(self, rest_impl, compiled_route):
        # given
        rest_impl.bucket_ratelimiters.is_started = True
        # when
        await rest_impl._request_json_response(compiled_route)
        # then
        rest_impl.bucket_ratelimiters.start.assert_not_called()

    async def test_perform_request_awaited(self, rest_impl, compiled_route):
        # when
        await rest_impl._request_json_response(compiled_route)
        # then
        rest_impl._perform_request.assert_awaited_once()

    async def test_passes_method_kwarg(self, rest_impl, compiled_route):
        # when
        await rest_impl._request_json_response(compiled_route)
        # then
        _, kwargs = rest_impl._perform_request.call_args
        assert kwargs["method"] == "POST"

    async def test_passes_url_kwarg(self, rest_impl, compiled_route):
        # when
        await rest_impl._request_json_response(compiled_route)
        # then
        _, kwargs = rest_impl._perform_request.call_args
        assert kwargs["url"] == "http://example.bloop.com/foo/bar/baz"

    async def test_passes_headers(self, rest_impl, compiled_route):
        # given
        headers = {
            "X-Floofy-Floof": "ayaayayayayayaya",
            "X-Cider-Preference": "Strongbow Rose",
            "Correlation-ID": "128374ad-23vsvdbdbnd-123-12314145",
            "Connection": "keepalive",
        }
        # when
        await rest_impl._request_json_response(compiled_route, headers=headers)
        # then
        _, kwargs = rest_impl._perform_request.call_args
        for k, v in headers.items():
            assert k in kwargs["headers"]
            assert kwargs["headers"][k] == v

    async def test_accept_header_injected(self, rest_impl, compiled_route):
        # when
        await rest_impl._request_json_response(compiled_route)
        # then
        _, kwargs = rest_impl._perform_request.call_args
        assert kwargs["headers"]["accept"] == "application/json"

    async def test_precision_header_injected(self, rest_impl, compiled_route):
        # when
        await rest_impl._request_json_response(compiled_route)
        # then
        _, kwargs = rest_impl._perform_request.call_args
        assert kwargs["headers"]["x-ratelimit-precision"] == "millisecond"

    async def test_authorization_header_not_injected_if_none(self, rest_impl, compiled_route):
        # given
        rest_impl._token = None
        # when
        await rest_impl._request_json_response(compiled_route)
        # then
        assert "authorization" not in map(str.lower, rest_impl._perform_request.call_args[1]["headers"].keys())

    async def test_authorization_header_injected_if_present(self, rest_impl, compiled_route):
        # when
        await rest_impl._request_json_response(compiled_route)
        # then
        _, kwargs = rest_impl._perform_request.call_args
        assert kwargs["headers"]["authorization"] == rest_impl._token

    async def test_authorization_header_not_injected_if_present_but_suppress_arg_true(self, rest_impl, compiled_route):
        # when
        await rest_impl._request_json_response(compiled_route, suppress_authorization_header=True)
        # then
        assert "authorization" not in map(str.lower, rest_impl._perform_request.call_args[1]["headers"].keys())

    async def test_auditlog_reason_header_not_injected_if_omitted(self, rest_impl, compiled_route):
        # when
        await rest_impl._request_json_response(compiled_route)
        # then
        assert "x-audit-log-reason" not in map(str.lower, rest_impl._perform_request.call_args[1]["headers"].keys())

    async def test_auditlog_reason_header_not_injected_if_omitted(self, rest_impl, compiled_route):
        # when
        await rest_impl._request_json_response(compiled_route, reason="he was evil")
        # then
        headers = rest_impl._perform_request.call_args[1]["headers"]
        assert headers["x-audit-log-reason"] == "he was evil"

    async def test_waits_for_rate_limits_before_requesting(self, rest_impl, compiled_route):
        await_ratelimiter = object()
        await_request = object()

        order = []

        def on_gather(*_, **__):
            order.append(await_ratelimiter)

        def on_request(*_, **__):
            order.append(await_request)
            return MockResponse()

        rest_impl._perform_request = mock.AsyncMock(wraps=on_request)

        with mock.patch.object(asyncio, "gather", new=mock.AsyncMock(wraps=on_gather)) as gather:
            await rest_impl._request_json_response(compiled_route)

        rest_impl.bucket_ratelimiters.acquire.assert_called_once_with(compiled_route)
        rest_impl.global_ratelimiter.acquire.assert_called_once_with()

        assert order == [await_ratelimiter, await_request]

        gather.assert_awaited_once_with(
            rest_impl.bucket_ratelimiters.acquire(compiled_route), rest_impl.global_ratelimiter.acquire(),
        )

    async def test_response_ratelimits_considered(self, rest_impl, compiled_route):
        response = MockResponse()
        rest_impl._perform_request = mock.AsyncMock(return_value=response)

        await rest_impl._request_json_response(compiled_route)

        rest_impl._handle_rate_limits_for_response.assert_awaited_once_with(compiled_route, response)

    async def test_204_returns_None(self, rest_impl, compiled_route):
        response = MockResponse(status=204, body="this is most certainly not None but it shouldn't be considered")
        rest_impl._perform_request = mock.AsyncMock(return_value=response)

        assert await rest_impl._request_json_response(compiled_route) is None

    @pytest.mark.parametrize("status", [200, 201, 202, 203])
    async def test_2xx_returns_json_body_if_json_type(self, rest_impl, compiled_route, status):
        response = MockResponse(status=status, body='{"foo": "bar"}', content_type="application/json")
        rest_impl._perform_request = mock.AsyncMock(return_value=response)

        assert await rest_impl._request_json_response(compiled_route) == {"foo": "bar"}

    @pytest.mark.parametrize("status", [200, 201, 202, 203])
    @_helpers.assert_raises(type_=errors.HTTPError)
    async def test_2xx_raises_http_error_if_unexpected_content_type(self, rest_impl, compiled_route, status):
        response = MockResponse(status=status, body='{"foo": "bar"}', content_type="application/foobar")
        rest_impl._perform_request = mock.AsyncMock(return_value=response)

        await rest_impl._request_json_response(compiled_route)

    @pytest.mark.parametrize(
        ["status", "expected_exception_type"],
        [
            (100, errors.HTTPErrorResponse),
            (304, errors.HTTPErrorResponse),
            (400, errors.BadRequest),
            (401, errors.Unauthorized),
            (403, errors.Forbidden),
            (404, errors.NotFound),
            (406, errors.ClientHTTPErrorResponse),
            (408, errors.ClientHTTPErrorResponse),
            (415, errors.ClientHTTPErrorResponse),
            (500, errors.ServerHTTPErrorResponse),
            (501, errors.ServerHTTPErrorResponse),
            (502, errors.ServerHTTPErrorResponse),
            (503, errors.ServerHTTPErrorResponse),
            (504, errors.ServerHTTPErrorResponse),
        ],
    )
    async def test_error_responses_raises_error(self, rest_impl, compiled_route, status, expected_exception_type):
        response = MockResponse(status=status, body="this is most certainly not None but it shouldn't be considered")
        rest_impl._perform_request = mock.AsyncMock(return_value=response)

        try:
            await rest_impl._request_json_response(compiled_route)
            assert False
        except expected_exception_type as ex:
            assert ex.headers is response.headers
            assert ex.status == response.status
            assert isinstance(ex.status, http.HTTPStatus)
            assert ex.raw_body is response.body

    async def test_ratelimited_429_retries_request_until_it_works(self, compiled_route, rest_impl):
        # given
        response = MockResponse()
        rest_impl._handle_rate_limits_for_response = mock.AsyncMock(
            # In reality, the ratelimiting logic will ensure we wait before retrying, but this
            # is a test for a spammy edge-case scenario.
            side_effect=[rest._RateLimited, rest._RateLimited, rest._RateLimited, None]
        )
        # when
        await rest_impl._request_json_response(compiled_route)
        # then
        assert len(rest_impl._perform_request.call_args_list) == 4, rest_impl._perform_request.call_args_list
        for args, kwargs in rest_impl._perform_request.call_args_list:
            assert kwargs == {
                "method": "POST",
                "url": "http://example.bloop.com/foo/bar/baz",
                "headers": mock.ANY,
                "body": mock.ANY,
                "query": mock.ANY,
            }


@pytest.mark.asyncio
class TestHandleRateLimitsForResponse:
    @pytest.fixture
    def bucket_ratelimiters(self):
        limiter = mock.MagicMock(spec_set=ratelimits.RESTBucketManager)
        limiter.update_rate_limits = mock.MagicMock()
        return limiter

    @pytest.fixture
    def global_ratelimiter(self):
        limiter = mock.MagicMock(spec_set=ratelimits.ManualRateLimiter)
        limiter.throttle = mock.MagicMock()
        return limiter

    @pytest.fixture
    def rest_impl(self, bucket_ratelimiters, global_ratelimiter):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(http_client.HTTPClient, "__init__", new=lambda *_, **__: None))
        stack.enter_context(mock.patch.object(ratelimits, "RESTBucketManager", return_value=bucket_ratelimiters))
        stack.enter_context(mock.patch.object(ratelimits, "ManualRateLimiter", return_value=global_ratelimiter))
        with stack:
            client = rest.REST(base_url="http://example.bloop.com", token="Bot blah.blah.blah")
        client.logger = mock.MagicMock(spec_set=logging.Logger)
        return client

    @pytest.mark.parametrize("status", [200, 201, 202, 203, 204, 400, 401, 403, 404, 429, 500])
    @pytest.mark.parametrize("content_type", ["application/json", "text/x-yaml", None])
    async def test_bucket_ratelimiter_updated(
        self, bucket_ratelimiters, rest_impl, compiled_route, status, content_type
    ):
        response = MockResponse(
            headers={
                "x-ratelimit-limit": "15",
                "x-ratelimit-remaining": "3",
                "x-ratelimit-bucket": "foobar",
                "date": "Fri, 01 May 2020 10:23:54 GMT",
                "x-ratelimit-reset": "1588334400",
            },
            status=status,
            content_type=content_type,
        )

        # We don't care about the result, as some cases throw exceptions purposely. We just want
        # to invoke it and check a call is made before it returns. This ensures 429s still take
        # into account the headers first.
        with contextlib.suppress(Exception):
            await rest_impl._handle_rate_limits_for_response(compiled_route, response)

        bucket_ratelimiters.update_rate_limits.assert_called_once_with(
            compiled_route=compiled_route,
            bucket_header="foobar",
            remaining_header=3,
            limit_header=15,
            date_header=datetime.datetime(2020, 5, 1, 10, 23, 54, tzinfo=datetime.timezone.utc),
            reset_at_header=datetime.datetime(2020, 5, 1, 12, tzinfo=datetime.timezone.utc),
        )

    @pytest.mark.parametrize("body", [b"{}", b'{"global": false}'])
    @_helpers.assert_raises(type_=rest._RateLimited)
    async def test_non_global_429_raises_Ratelimited(self, rest_impl, compiled_route, body):
        response = MockResponse(
            headers={
                "x-ratelimit-limit": "15",
                "x-ratelimit-remaining": "3",
                "x-ratelimit-bucket": "foobar",
                "date": "Fri, 01 May 2020 10:23:54 GMT",
                "x-ratelimit-reset": "1588334400",
            },
            status=429,
            content_type="application/json",
            body=body,
        )

        await rest_impl._handle_rate_limits_for_response(compiled_route, response)

    async def test_global_429_throttles_then_raises_Ratelimited(self, global_ratelimiter, rest_impl, compiled_route):
        response = MockResponse(
            headers={
                "x-ratelimit-limit": "15",
                "x-ratelimit-remaining": "3",
                "x-ratelimit-bucket": "foobar",
                "date": "Fri, 01 May 2020 10:23:54 GMT",
                "x-ratelimit-reset": "1588334400",
            },
            status=429,
            content_type="application/json",
            body=b'{"global": true, "retry_after": 1024768}',
        )

        try:
            await rest_impl._handle_rate_limits_for_response(compiled_route, response)
            assert False
        except rest._RateLimited:
            global_ratelimiter.throttle.assert_called_once_with(1024.768)

    async def test_non_json_429_causes_httperror(self, rest_impl, compiled_route):
        response = MockResponse(
            headers={
                "x-ratelimit-limit": "15",
                "x-ratelimit-remaining": "3",
                "x-ratelimit-bucket": "foobar",
                "date": "Fri, 01 May 2020 10:23:54 GMT",
                "x-ratelimit-reset": "1588334400",
            },
            status=429,
            content_type="text/x-markdown",
            body=b'{"global": true, "retry_after": 1024768}',
            real_url="http://foo-bar.com/api/v169/ree",
        )

        try:
            await rest_impl._handle_rate_limits_for_response(compiled_route, response)
            assert False
        except errors.HTTPError as ex:
            # We don't want a subclass, as this is an edge case.
            assert type(ex) is errors.HTTPError
            assert ex.url == "http://foo-bar.com/api/v169/ree"


class TestRESTEndpoints:
    @pytest.fixture
    def rest_impl(self):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(http_client.HTTPClient, "__init__", new=lambda *_, **__: None))
        stack.enter_context(mock.patch.object(ratelimits, "RESTBucketManager"))
        stack.enter_context(mock.patch.object(ratelimits, "ManualRateLimiter"))
        with stack:
            client = rest.REST(base_url="https://discord.com/api/v6", token="Bot blah.blah.blah")
        client.logger = mock.MagicMock(spec_set=logging.Logger)
        client._request_json_response = mock.AsyncMock(return_value=...)
        client.client_session = mock.MagicMock(aiohttp.ClientSession, spec_set=True)

        return client

    @pytest.mark.asyncio
    async def test_get_gateway(self, rest_impl):
        rest_impl._request_json_response.return_value = {"url": "discord.discord///"}
        with mock_patch_route("GET_GATEWAY") as (template, compiled):
            assert await rest_impl.get_gateway() == "discord.discord///"
            template.compile.assert_called_once_with()
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_gateway_bot(self, rest_impl):
        mock_response = {"url": "discord.discord///"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GATEWAY_BOT") as (template, compiled):
            assert await rest_impl.get_gateway_bot() is mock_response
            template.compile.assert_called_once_with()
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_guild_audit_log_without_optionals(self, rest_impl):
        mock_response = {"webhooks": [], "users": []}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_AUDIT_LOGS") as (template, compiled):
            assert await rest_impl.get_guild_audit_log("2929292929") is mock_response
            template.compile.assert_called_once_with(guild_id="2929292929")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, query={})

    @pytest.mark.asyncio
    async def test_get_guild_audit_log_with_optionals(self, rest_impl):
        mock_response = {"webhooks": [], "users": []}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_AUDIT_LOGS") as (template, compiled):
            assert (
                await rest_impl.get_guild_audit_log(
                    "2929292929", user_id="115590097100865541", action_type=42, limit=5, before="123123123"
                )
                is mock_response
            )
            template.compile.assert_called_once_with(guild_id="2929292929")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, query={"user_id": "115590097100865541", "action_type": 42, "limit": 5, "before": "123123123"}
        )

    @pytest.mark.asyncio
    async def test_get_channel(self, rest_impl):
        mock_response = {"id": "20202020200202"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_CHANNEL") as (template, compiled):
            assert await rest_impl.get_channel("20202020020202") is mock_response
            template.compile.assert_called_once_with(channel_id="20202020020202")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_modify_channel_without_optionals(self, rest_impl):
        mock_response = {"id": "20393939"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_CHANNEL") as (template, compiled):
            assert await rest_impl.modify_channel("6942069420") is mock_response
            template.compile.assert_called_once_with(channel_id="6942069420")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={}, reason=...)

    @pytest.mark.asyncio
    async def test_modify_channel_with_optionals(self, rest_impl):
        mock_response = {"id": "20393939"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_CHANNEL") as (template, compiled):
            result = await rest_impl.modify_channel(
                "6942069420",
                position=22,
                topic="HAHAHAHHAHAHA",
                nsfw=True,
                rate_limit_per_user=222,
                bitrate=320,
                user_limit=5,
                permission_overwrites=[{"type": "user", "allow": 33}],
                parent_id="55555",
                reason="Get channel'ed",
            )
            assert result is mock_response
            template.compile.assert_called_once_with(channel_id="6942069420")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled,
            body={
                "position": 22,
                "topic": "HAHAHAHHAHAHA",
                "nsfw": True,
                "rate_limit_per_user": 222,
                "bitrate": 320,
                "user_limit": 5,
                "permission_overwrites": [{"type": "user", "allow": 33}],
                "parent_id": "55555",
            },
            reason="Get channel'ed",
        )

    @pytest.mark.asyncio
    async def test_delete_channel_close(self, rest_impl):
        mock_route = mock.MagicMock(routes.DELETE_CHANNEL)
        with mock_patch_route("DELETE_CHANNEL") as (template, compiled):
            assert await rest_impl.delete_close_channel("939392929") is None
            template.compile.assert_called_once_with(channel_id="939392929")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_channel_messages_without_optionals(self, rest_impl):
        mock_response = [{"id": "29492", "content": "Kon'nichiwa"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_CHANNEL_MESSAGES") as (template, compiled):
            assert await rest_impl.get_channel_messages("9292929292") is mock_response
            template.compile.assert_called_once_with(channel_id="9292929292")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, query={})

    @pytest.mark.asyncio
    async def test_get_channel_messages_with_optionals(self, rest_impl):
        mock_response = [{"id": "29492", "content": "Kon'nichiwa"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_CHANNEL_MESSAGES") as (template, compiled):
            assert (
                await rest_impl.get_channel_messages(
                    "9292929292", limit=42, after="293939393", before="4945959595", around="44444444",
                )
                is mock_response
            )
            template.compile.assert_called_once_with(channel_id="9292929292")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, query={"limit": 42, "after": "293939393", "before": "4945959595", "around": "44444444",}
        )

    @pytest.mark.asyncio
    async def test_get_channel_message(self, rest_impl):
        mock_response = {"content": "I'm really into networking with cute routers and modems."}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_CHANNEL_MESSAGE") as (template, compiled):
            assert await rest_impl.get_channel_message("1111111111", "42424242") is mock_response
            template.compile.assert_called_once_with(channel_id="1111111111", message_id="42424242")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_create_message_without_optionals(self, rest_impl):
        mock_response = {"content": "nyaa, nyaa, nyaa."}
        rest_impl._request_json_response.return_value = mock_response
        mock_form = mock.MagicMock(aiohttp.FormData, add_field=mock.MagicMock())
        with mock_patch_route("POST_CHANNEL_MESSAGES") as (template, compiled):
            with mock.patch.object(aiohttp, "FormData", return_value=mock_form):
                assert await rest_impl.create_message("22222222") is mock_response
                template.compile.assert_called_once_with(channel_id="22222222")
                mock_form.add_field.assert_called_once_with(
                    "payload_json", json.dumps({}), content_type="application/json"
                )
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body=mock_form)

    @pytest.mark.asyncio
    @mock.patch.object(routes, "POST_CHANNEL_MESSAGES")
    @mock.patch.object(aiohttp, "FormData")
    @mock.patch.object(json, "dumps")
    async def test_create_message_with_optionals(self, dumps, FormData, POST_CHANNEL_MESSAGES, rest_impl):
        mock_response = {"content": "nyaa, nyaa, nyaa."}
        rest_impl._request_json_response.return_value = mock_response

        mock_form = mock.MagicMock(aiohttp.FormData, add_field=mock.MagicMock())
        FormData.return_value = mock_form
        mock_file = mock.MagicMock(files.BaseStream)
        mock_file.filename = "file.txt"
        mock_json = '{"description": "I am a message", "tts": "True"}'
        dumps.return_value = mock_json

        with mock_patch_route("POST_CHANNEL_MESSAGES") as (template, compiled):
            result = await rest_impl.create_message(
                "22222222",
                content="I am a message",
                nonce="ag993okskm_cdolsio",
                tts=True,
                files=[mock_file],
                embed={"description": "I am an embed"},
                allowed_mentions={"users": ["123"], "roles": ["456"]},
            )
            assert result is mock_response
            template.compile.assert_called_once_with(channel_id="22222222")
        dumps.assert_called_once_with(
            {
                "tts": True,
                "content": "I am a message",
                "nonce": "ag993okskm_cdolsio",
                "embed": {"description": "I am an embed"},
                "allowed_mentions": {"users": ["123"], "roles": ["456"]},
            }
        )

        mock_form.add_field.assert_has_calls(
            (
                mock.call("payload_json", mock_json, content_type="application/json"),
                mock.call("file0", mock_file, filename="file.txt", content_type="application/octet-stream"),
            ),
            any_order=True,
        )
        assert mock_form.add_field.call_count == 2
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body=mock_form)

    @pytest.mark.asyncio
    async def test_create_reaction(self, rest_impl):
        with mock_patch_route("PUT_MY_REACTION") as (template, compiled):
            assert await rest_impl.create_reaction("20202020", "8484848", "emoji:2929") is None
            template.compile.assert_called_once_with(channel_id="20202020", message_id="8484848", emoji="emoji:2929")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_delete_own_reaction(self, rest_impl):
        with mock_patch_route("DELETE_MY_REACTION") as (template, compiled):
            assert await rest_impl.delete_own_reaction("20202020", "8484848", "emoji:2929") is None
            template.compile.assert_called_once_with(channel_id="20202020", message_id="8484848", emoji="emoji:2929")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_delete_all_reactions_for_emoji(self, rest_impl):
        with mock_patch_route("DELETE_REACTION_EMOJI") as (template, compiled):
            assert await rest_impl.delete_all_reactions_for_emoji("222", "333", "222:owo") is None
            template.compile.assert_called_once_with(channel_id="222", message_id="333", emoji="222:owo")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_delete_user_reaction(self, rest_impl):
        with mock_patch_route("DELETE_REACTION_USER") as (template, compiled):
            assert await rest_impl.delete_user_reaction("11111", "4444", "emoji:42", "29292992") is None
            template.compile.assert_called_once_with(
                channel_id="11111", message_id="4444", emoji="emoji:42", user_id="29292992"
            )
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_reactions_without_optionals(self, rest_impl):
        mock_response = [{"id": "42"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_REACTIONS") as (template, compiled):
            assert await rest_impl.get_reactions("29292929", "48484848", "emoji:42") is mock_response
            template.compile.assert_called_once_with(channel_id="29292929", message_id="48484848", emoji="emoji:42")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, query={})

    @pytest.mark.asyncio
    async def test_get_reactions_with_optionals(self, rest_impl):
        mock_response = [{"id": "42"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_REACTIONS") as (template, compiled):
            assert (
                await rest_impl.get_reactions("29292929", "48484848", "emoji:42", after="3333333", limit=40)
                is mock_response
            )
            template.compile.assert_called_once_with(channel_id="29292929", message_id="48484848", emoji="emoji:42")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, query={"after": "3333333", "limit": 40})

    @pytest.mark.asyncio
    async def test_delete_all_reactions(self, rest_impl):
        with mock_patch_route("DELETE_ALL_REACTIONS") as (template, compiled):
            assert await rest_impl.delete_all_reactions("44444", "999999") is None
            template.compile.assert_called_once_with(channel_id="44444", message_id="999999")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_edit_message_without_optionals(self, rest_impl):
        mock_response = {"flags": 3, "content": "edited for the win."}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_CHANNEL_MESSAGE") as (template, compiled):
            assert await rest_impl.edit_message("9292929", "484848") is mock_response
            template.compile.assert_called_once_with(channel_id="9292929", message_id="484848")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={})

    @pytest.mark.asyncio
    async def test_edit_message_with_optionals(self, rest_impl):
        mock_response = {"flags": 3, "content": "edited for the win."}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_CHANNEL_MESSAGE") as (template, compiled):
            assert (
                await rest_impl.edit_message(
                    "9292929",
                    "484848",
                    content="42",
                    embed={"content": "I AM AN EMBED"},
                    flags=2,
                    allowed_mentions={"parse": ["everyone", "users"]},
                )
                is mock_response
            )
            template.compile.assert_called_once_with(channel_id="9292929", message_id="484848")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled,
            body={
                "content": "42",
                "embed": {"content": "I AM AN EMBED"},
                "flags": 2,
                "allowed_mentions": {"parse": ["everyone", "users"]},
            },
        )

    @pytest.mark.asyncio
    async def test_delete_message(self, rest_impl):
        with mock_patch_route("DELETE_CHANNEL_MESSAGE") as (template, compiled):
            assert await rest_impl.delete_message("20202", "484848") is None
            template.compile.assert_called_once_with(channel_id="20202", message_id="484848")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_bulk_delete_messages(self, rest_impl):
        with mock_patch_route("POST_DELETE_CHANNEL_MESSAGES_BULK") as (template, compiled):
            assert await rest_impl.bulk_delete_messages("111", ["222", "333"]) is None
            template.compile.assert_called_once_with(channel_id="111")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={"messages": ["222", "333"]})

    @pytest.mark.asyncio
    async def test_edit_channel_permissions_without_optionals(self, rest_impl):
        with mock_patch_route("PATCH_CHANNEL_PERMISSIONS") as (template, compiled):
            assert await rest_impl.edit_channel_permissions("101010101010", "100101010", type_="user") is None
            template.compile.assert_called_once_with(channel_id="101010101010", overwrite_id="100101010")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={"type": "user"}, reason=...)

    @pytest.mark.asyncio
    async def test_edit_channel_permissions_with_optionals(self, rest_impl):
        with mock_patch_route("PATCH_CHANNEL_PERMISSIONS") as (template, compiled):
            assert (
                await rest_impl.edit_channel_permissions(
                    "101010101010", "100101010", allow=243, deny=333, type_="user", reason="get vectored"
                )
                is None
            )
            template.compile.assert_called_once_with(channel_id="101010101010", overwrite_id="100101010")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, body={"allow": 243, "deny": 333, "type": "user"}, reason="get vectored"
        )

    @pytest.mark.asyncio
    async def test_get_channel_invites(self, rest_impl):
        mock_response = {"code": "dasd32"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_CHANNEL_INVITES") as (template, compiled):
            assert await rest_impl.get_channel_invites("999999999") is mock_response
            template.compile.assert_called_once_with(channel_id="999999999")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_create_channel_invite_without_optionals(self, rest_impl):
        mock_response = {"code": "ro934jsd"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("POST_CHANNEL_INVITES") as (template, compiled):
            assert await rest_impl.create_channel_invite("99992929") is mock_response
            template.compile.assert_called_once_with(channel_id="99992929")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={}, reason=...)

    @pytest.mark.asyncio
    async def test_create_channel_invite_with_optionals(self, rest_impl):
        mock_response = {"code": "ro934jsd"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("POST_CHANNEL_INVITES") as (template, compiled):
            assert (
                await rest_impl.create_channel_invite(
                    "99992929",
                    max_age=5,
                    max_uses=7,
                    temporary=True,
                    unique=False,
                    target_user="29292929292",
                    target_user_type=2,
                    reason="XD",
                )
                is mock_response
            )
            template.compile.assert_called_once_with(channel_id="99992929")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled,
            body={
                "max_age": 5,
                "max_uses": 7,
                "temporary": True,
                "unique": False,
                "target_user": "29292929292",
                "target_user_type": 2,
            },
            reason="XD",
        )

    @pytest.mark.asyncio
    async def test_delete_channel_permission(self, rest_impl):
        with mock_patch_route("DELETE_CHANNEL_PERMISSIONS") as (template, compiled):
            assert await rest_impl.delete_channel_permission("9292929", "74574747") is None
            template.compile.assert_called_once_with(channel_id="9292929", overwrite_id="74574747")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_trigger_typing_indicator(self, rest_impl):
        with mock_patch_route("POST_CHANNEL_TYPING") as (template, compiled):
            assert await rest_impl.trigger_typing_indicator("11111111111") is None
            template.compile.assert_called_once_with(channel_id="11111111111")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_pinned_messages(self, rest_impl):
        mock_response = [{"content": "no u", "id": "4212"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_CHANNEL_PINS") as (template, compiled):
            assert await rest_impl.get_pinned_messages("393939") is mock_response
            template.compile.assert_called_once_with(channel_id="393939")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_add_pinned_channel_message(self, rest_impl):
        with mock_patch_route("PUT_CHANNEL_PINS") as (template, compiled):
            assert await rest_impl.add_pinned_channel_message("292929", "48458484") is None
            template.compile.assert_called_once_with(channel_id="292929", message_id="48458484")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_delete_pinned_channel_message(self, rest_impl):
        with mock_patch_route("DELETE_CHANNEL_PIN") as (template, compiled):
            assert await rest_impl.delete_pinned_channel_message("929292", "292929") is None
            template.compile.assert_called_once_with(channel_id="929292", message_id="292929")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_list_guild_emojis(self, rest_impl):
        mock_response = [{"id": "444", "name": "nekonyan"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_EMOJIS") as (template, compiled):
            assert await rest_impl.list_guild_emojis("9929292") is mock_response
            template.compile.assert_called_once_with(guild_id="9929292")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_guild_emoji(self, rest_impl):
        mock_response = {"id": "444", "name": "nekonyan"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_EMOJI") as (template, compiled):
            assert await rest_impl.get_guild_emoji("292929", "44848") is mock_response
            template.compile.assert_called_once_with(guild_id="292929", emoji_id="44848")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_create_guild_emoji_without_optionals(self, rest_impl):
        mock_response = {"id": "33", "name": "OwO"}
        rest_impl._request_json_response.return_value = mock_response
        mock_image_data = "data:image/png;base64,iVBORw0KGgpibGFo"
        with mock_patch_route("POST_GUILD_EMOJIS") as (template, compiled):
            with mock.patch.object(conversions, "image_bytes_to_image_data", return_value=mock_image_data):
                result = await rest_impl.create_guild_emoji("2222", "iEmoji", b"\211PNG\r\n\032\nblah")
                assert result is mock_response
                conversions.image_bytes_to_image_data.assert_called_once_with(b"\211PNG\r\n\032\nblah")
                template.compile.assert_called_once_with(guild_id="2222")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, body={"name": "iEmoji", "roles": [], "image": mock_image_data}, reason=...,
        )

    @pytest.mark.asyncio
    async def test_create_guild_emoji_with_optionals(self, rest_impl):
        mock_response = {"id": "33", "name": "OwO"}
        rest_impl._request_json_response.return_value = mock_response
        mock_image_data = "data:image/png;base64,iVBORw0KGgpibGFo"
        with mock_patch_route("POST_GUILD_EMOJIS") as (template, compiled):
            with mock.patch.object(conversions, "image_bytes_to_image_data", return_value=mock_image_data):
                result = await rest_impl.create_guild_emoji(
                    "2222", "iEmoji", b"\211PNG\r\n\032\nblah", roles=["292929", "484884"], reason="uwu owo"
                )
                assert result is mock_response
                conversions.image_bytes_to_image_data.assert_called_once_with(b"\211PNG\r\n\032\nblah")
                template.compile.assert_called_once_with(guild_id="2222")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled,
            body={"name": "iEmoji", "roles": ["292929", "484884"], "image": mock_image_data},
            reason="uwu owo",
        )

    @pytest.mark.asyncio
    async def test_modify_guild_emoji_without_optionals(self, rest_impl):
        mock_response = {"id": "20202", "name": "jeje"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_GUILD_EMOJI") as (template, compiled):
            assert await rest_impl.modify_guild_emoji("292929", "3484848") is mock_response
            template.compile.assert_called_once_with(guild_id="292929", emoji_id="3484848")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={}, reason=...)

    @pytest.mark.asyncio
    async def test_modify_guild_emoji_with_optionals(self, rest_impl):
        mock_response = {"id": "20202", "name": "jeje"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_GUILD_EMOJI") as (template, compiled):
            assert (
                await rest_impl.modify_guild_emoji("292929", "3484848", name="ok", roles=["222", "111"])
                is mock_response
            )
            template.compile.assert_called_once_with(guild_id="292929", emoji_id="3484848")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, body={"name": "ok", "roles": ["222", "111"]}, reason=...
        )

    @pytest.mark.asyncio
    async def test_delete_guild_emoji(self, rest_impl):
        with mock_patch_route("DELETE_GUILD_EMOJI") as (template, compiled):
            assert await rest_impl.delete_guild_emoji("202", "4454") is None
            template.compile.assert_called_once_with(guild_id="202", emoji_id="4454")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_create_guild_without_optionals(self, rest_impl):
        mock_response = {"id": "99999", "name": "Guildith-Sama"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("POST_GUILDS") as (template, compiled):
            assert await rest_impl.create_guild("GUILD TIME") is mock_response
            template.compile.assert_called_once_with()
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={"name": "GUILD TIME"})

    @pytest.mark.asyncio
    async def test_create_guild_with_optionals(self, rest_impl):
        mock_response = {"id": "99999", "name": "Guildith-Sama"}
        rest_impl._request_json_response.return_value = mock_response
        mock_image_data = "data:image/png;base64,iVBORw0KGgpibGFo"
        with mock_patch_route("POST_GUILDS") as (template, compiled):
            with mock.patch.object(conversions, "image_bytes_to_image_data", return_value=mock_image_data):
                result = await rest_impl.create_guild(
                    "GUILD TIME",
                    region="london",
                    icon=b"\211PNG\r\n\032\nblah",
                    verification_level=2,
                    explicit_content_filter=1,
                    roles=[{"name": "a role"}],
                    channels=[{"type": 0, "name": "444"}],
                )
                assert result is mock_response
                template.compile.assert_called_once_with()
                conversions.image_bytes_to_image_data.assert_called_once_with(b"\211PNG\r\n\032\nblah")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled,
            body={
                "name": "GUILD TIME",
                "region": "london",
                "icon": mock_image_data,
                "verification_level": 2,
                "explicit_content_filter": 1,
                "roles": [{"name": "a role"}],
                "channels": [{"type": 0, "name": "444"}],
            },
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("kwargs", "with_counts"),
        [({"with_counts": True}, "true"), ({"with_counts": False}, "false"), ({}, "true"),],  # default value only
    )
    async def test_get_guild(self, rest_impl, kwargs, with_counts):
        mock_response = {"id": "42", "name": "Hikari"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD") as (template, compiled):
            assert await rest_impl.get_guild("3939393993939", **kwargs) is mock_response
            template.compile.assert_called_once_with(guild_id="3939393993939")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, query={"with_counts": with_counts})

    @pytest.mark.asyncio
    async def test_get_guild_preview(self, rest_impl):
        mock_response = {"id": "42", "name": "Hikari"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_PREVIEW") as (template, compiled):
            assert await rest_impl.get_guild_preview("3939393993939") is mock_response
            template.compile.assert_called_once_with(guild_id="3939393993939")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_modify_guild_without_optionals(self, rest_impl):
        mock_response = {"id": "42", "name": "Hikari"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_GUILD") as (template, compiled):
            assert await rest_impl.modify_guild("49949495") is mock_response
            template.compile.assert_called_once_with(guild_id="49949495")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={}, reason=...)

    @pytest.mark.asyncio
    async def test_modify_guild_with_optionals(self, rest_impl):
        mock_response = {"id": "42", "name": "Hikari"}
        rest_impl._request_json_response.return_value = mock_response
        mock_icon_data = "data:image/png;base64,iVBORw0KGgpibGFo"
        mock_splash_data = "data:image/png;base64,iVBORw0KGgpicnVo"
        with mock_patch_route("PATCH_GUILD") as (template, compiled):
            with mock.patch.object(
                conversions, "image_bytes_to_image_data", side_effect=(mock_icon_data, mock_splash_data)
            ):
                result = await rest_impl.modify_guild(
                    "49949495",
                    name="Deutschland",
                    region="deutschland",
                    verification_level=2,
                    default_message_notifications=1,
                    explicit_content_filter=0,
                    afk_channel_id="49494949",
                    afk_timeout=5,
                    icon=b"\211PNG\r\n\032\nblah",
                    owner_id="379953393319542784",
                    splash=b"\211PNG\r\n\032\nbruh",
                    system_channel_id="123123123123",
                    reason="I USED TO RULE THE WORLD.",
                )
                assert result is mock_response

                template.compile.assert_called_once_with(guild_id="49949495")
                assert conversions.image_bytes_to_image_data.call_count == 2
                conversions.image_bytes_to_image_data.assert_has_calls(
                    (
                        mock.call.__bool__(),
                        mock.call(b"\211PNG\r\n\032\nblah"),
                        mock.call.__bool__(),
                        mock.call(b"\211PNG\r\n\032\nbruh"),
                    )
                )
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled,
            body={
                "name": "Deutschland",
                "region": "deutschland",
                "verification_level": 2,
                "default_message_notifications": 1,
                "explicit_content_filter": 0,
                "afk_channel_id": "49494949",
                "afk_timeout": 5,
                "icon": mock_icon_data,
                "owner_id": "379953393319542784",
                "splash": mock_splash_data,
                "system_channel_id": "123123123123",
            },
            reason="I USED TO RULE THE WORLD.",
        )

    @pytest.mark.asyncio
    async def test_delete_guild(self, rest_impl):
        with mock_patch_route("DELETE_GUILD") as (template, compiled):
            assert await rest_impl.delete_guild("92847478") is None
            template.compile.assert_called_once_with(guild_id="92847478")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_guild_channels(self, rest_impl):
        mock_response = [{"type": 2, "id": "21", "name": "Watashi-wa-channel-desu"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_CHANNELS") as (template, compiled):
            assert await rest_impl.list_guild_channels("393939393") is mock_response
            template.compile.assert_called_once_with(guild_id="393939393")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_create_guild_channel_without_optionals(self, rest_impl):
        mock_response = {"type": 2, "id": "3333"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("POST_GUILD_CHANNELS") as (template, compiled):
            assert await rest_impl.create_guild_channel("292929", "I am a channel") is mock_response
            template.compile.assert_called_once_with(guild_id="292929")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={"name": "I am a channel"}, reason=...)

    @pytest.mark.asyncio
    async def test_create_guild_channel_with_optionals(self, rest_impl):
        mock_response = {"type": 2, "id": "379953393319542784"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("POST_GUILD_CHANNELS") as (template, compiled):
            result = await rest_impl.create_guild_channel(
                "292929",
                "I am a channel",
                type_=2,
                topic="chatter chatter",
                bitrate=320,
                user_limit=4,
                rate_limit_per_user=2,
                position=42,
                permission_overwrites=[{"target": "379953393319542784", "type": "user"}],
                parent_id="379953393319542784",
                nsfw=True,
                reason="Made a channel for you qt.",
            )
            assert result is mock_response

            template.compile.assert_called_once_with(guild_id="292929")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled,
            body={
                "name": "I am a channel",
                "type": 2,
                "topic": "chatter chatter",
                "bitrate": 320,
                "user_limit": 4,
                "rate_limit_per_user": 2,
                "position": 42,
                "permission_overwrites": [{"target": "379953393319542784", "type": "user"}],
                "parent_id": "379953393319542784",
                "nsfw": True,
            },
            reason="Made a channel for you qt.",
        )

    @pytest.mark.asyncio
    async def test_modify_guild_channel_positions(self, rest_impl):
        with mock_patch_route("PATCH_GUILD_CHANNELS") as (template, compiled):
            assert (
                await rest_impl.modify_guild_channel_positions("379953393319542784", ("29292", 0), ("3838", 1)) is None
            )
            template.compile.assert_called_once_with(guild_id="379953393319542784")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, body=[{"id": "29292", "position": 0}, {"id": "3838", "position": 1}]
        )

    @pytest.mark.asyncio
    async def test_get_guild_member(self, rest_impl):
        mock_response = {"id": "379953393319542784", "nick": "Big Moh"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_MEMBER") as (template, compiled):
            assert await rest_impl.get_guild_member("115590097100865541", "379953393319542784") is mock_response
            template.compile.assert_called_once_with(guild_id="115590097100865541", user_id="379953393319542784")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_list_guild_members_without_optionals(self, rest_impl):
        mock_response = [{"id": "379953393319542784", "nick": "Big Moh"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_MEMBERS") as (template, compiled):
            assert await rest_impl.list_guild_members("115590097100865541") is mock_response
            template.compile.assert_called_once_with(guild_id="115590097100865541")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, query={})

    @pytest.mark.asyncio
    async def test_list_guild_members_with_optionals(self, rest_impl):
        mock_response = [{"id": "379953393319542784", "nick": "Big Moh"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_MEMBERS") as (template, compiled):
            assert (
                await rest_impl.list_guild_members("115590097100865541", limit=5, after="4444444444") is mock_response
            )
            template.compile.assert_called_once_with(guild_id="115590097100865541")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, query={"limit": 5, "after": "4444444444"})

    @pytest.mark.asyncio
    async def test_modify_guild_member_without_optionals(self, rest_impl):
        with mock_patch_route("PATCH_GUILD_MEMBER") as (template, compiled):
            assert await rest_impl.modify_guild_member("115590097100865541", "379953393319542784") is None
            template.compile.assert_called_once_with(guild_id="115590097100865541", user_id="379953393319542784")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={}, reason=...)

    @pytest.mark.asyncio
    async def test_modify_guild_member_with_optionals(self, rest_impl):
        with mock_patch_route("PATCH_GUILD_MEMBER") as (template, compiled):
            result = await rest_impl.modify_guild_member(
                "115590097100865541",
                "379953393319542784",
                nick="QT",
                roles=["222222222"],
                mute=True,
                deaf=True,
                channel_id="777",
                reason="I will drink your blood.",
            )
            assert result is None

            template.compile.assert_called_once_with(guild_id="115590097100865541", user_id="379953393319542784")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled,
            body={"nick": "QT", "roles": ["222222222"], "mute": True, "deaf": True, "channel_id": "777"},
            reason="I will drink your blood.",
        )

    @pytest.mark.asyncio
    async def test_modify_current_user_nick_without_reason(self, rest_impl):
        with mock_patch_route("PATCH_MY_GUILD_NICKNAME") as (template, compiled):
            assert await rest_impl.modify_current_user_nick("202020202", "Nickname me") is None
            template.compile.assert_called_once_with(guild_id="202020202")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={"nick": "Nickname me"}, reason=...)

    @pytest.mark.asyncio
    async def test_modify_current_user_nick_with_reason(self, rest_impl):
        with mock_patch_route("PATCH_MY_GUILD_NICKNAME") as (template, compiled):
            assert await rest_impl.modify_current_user_nick("202020202", "Nickname me", reason="Look at me") is None
            template.compile.assert_called_once_with(guild_id="202020202")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, body={"nick": "Nickname me"}, reason="Look at me"
        )

    @pytest.mark.asyncio
    async def test_add_guild_member_role_without_reason(self, rest_impl):
        with mock_patch_route("PUT_GUILD_MEMBER_ROLE") as (template, compiled):
            assert await rest_impl.add_guild_member_role("3939393", "2838383", "84384848") is None
            template.compile.assert_called_once_with(guild_id="3939393", user_id="2838383", role_id="84384848")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, reason=...)

    @pytest.mark.asyncio
    async def test_add_guild_member_role_with_reason(self, rest_impl):
        with mock_patch_route("PUT_GUILD_MEMBER_ROLE") as (template, compiled):
            assert (
                await rest_impl.add_guild_member_role(
                    "3939393", "2838383", "84384848", reason="A special role for a special somebody"
                )
                is None
            )
            template.compile.assert_called_once_with(guild_id="3939393", user_id="2838383", role_id="84384848")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, reason="A special role for a special somebody"
        )

    @pytest.mark.asyncio
    async def test_remove_guild_member_role_without_reason(self, rest_impl):
        with mock_patch_route("DELETE_GUILD_MEMBER_ROLE") as (template, compiled):
            assert await rest_impl.remove_guild_member_role("22222", "3333", "44444") is None
            template.compile.assert_called_once_with(guild_id="22222", user_id="3333", role_id="44444")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, reason=...)

    @pytest.mark.asyncio
    async def test_remove_guild_member_role_with_reason(self, rest_impl):
        with mock_patch_route("DELETE_GUILD_MEMBER_ROLE") as (template, compiled):
            assert await rest_impl.remove_guild_member_role("22222", "3333", "44444", reason="bye") is None
            template.compile.assert_called_once_with(guild_id="22222", user_id="3333", role_id="44444")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, reason="bye")

    @pytest.mark.asyncio
    async def test_remove_guild_member_without_reason(self, rest_impl):
        with mock_patch_route("DELETE_GUILD_MEMBER") as (template, compiled):
            assert await rest_impl.remove_guild_member("393939", "82828") is None
            template.compile.assert_called_once_with(guild_id="393939", user_id="82828")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, reason=...)

    @pytest.mark.asyncio
    async def test_remove_guild_member_with_reason(self, rest_impl):
        with mock_patch_route("DELETE_GUILD_MEMBER") as (template, compiled):
            assert await rest_impl.remove_guild_member("393939", "82828", reason="super bye") is None
            template.compile.assert_called_once_with(guild_id="393939", user_id="82828")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, reason="super bye")

    @pytest.mark.asyncio
    async def test_get_guild_bans(self, rest_impl):
        mock_response = [{"id": "3939393"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_BANS") as (template, compiled):
            assert await rest_impl.get_guild_bans("292929") is mock_response
            template.compile.assert_called_once_with(guild_id="292929")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_guild_ban(self, rest_impl):
        mock_response = {"id": "3939393"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_BAN") as (template, compiled):
            assert await rest_impl.get_guild_ban("92929", "44848") is mock_response
            template.compile.assert_called_once_with(guild_id="92929", user_id="44848")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_create_guild_ban_without_optionals(self, rest_impl):
        with mock_patch_route("PUT_GUILD_BAN") as (template, compiled):
            assert await rest_impl.create_guild_ban("222", "444") is None
            template.compile.assert_called_once_with(guild_id="222", user_id="444")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, query={})

    @pytest.mark.asyncio
    async def test_create_guild_ban_with_optionals(self, rest_impl):
        with mock_patch_route("PUT_GUILD_BAN") as (template, compiled):
            assert await rest_impl.create_guild_ban("222", "444", delete_message_days=5, reason="TRUE") is None
            template.compile.assert_called_once_with(guild_id="222", user_id="444")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, query={"delete-message-days": 5, "reason": "TRUE"}
        )

    @pytest.mark.asyncio
    async def test_remove_guild_ban_without_reason(self, rest_impl):
        with mock_patch_route("DELETE_GUILD_BAN") as (template, compiled):
            assert await rest_impl.remove_guild_ban("494949", "3737") is None
            template.compile.assert_called_once_with(guild_id="494949", user_id="3737")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, reason=...)

    @pytest.mark.asyncio
    async def test_remove_guild_ban_with_reason(self, rest_impl):
        with mock_patch_route("DELETE_GUILD_BAN") as (template, compiled):
            assert await rest_impl.remove_guild_ban("494949", "3737", reason="LMFAO") is None
            template.compile.assert_called_once_with(guild_id="494949", user_id="3737")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, reason="LMFAO")

    @pytest.mark.asyncio
    async def test_get_guild_roles(self, rest_impl):
        mock_response = [{"name": "role", "id": "4949494994"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_ROLES") as (template, compiled):
            assert await rest_impl.get_guild_roles("909") is mock_response
            template.compile.assert_called_once_with(guild_id="909")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_create_guild_role_without_optionals(self, rest_impl):
        mock_response = {"id": "42"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("POST_GUILD_ROLES") as (template, compiled):
            assert await rest_impl.create_guild_role("9494") is mock_response
            template.compile.assert_called_once_with(guild_id="9494")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={}, reason=...)

    @pytest.mark.asyncio
    async def test_create_guild_role_with_optionals(self, rest_impl):
        mock_response = {"id": "42"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("POST_GUILD_ROLES") as (template, compiled):
            assert (
                await rest_impl.create_guild_role(
                    "9494", name="role sama", permissions=22, color=12, hoist=True, mentionable=True, reason="eat dirt"
                )
                is mock_response
            )
            template.compile.assert_called_once_with(guild_id="9494")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled,
            body={"name": "role sama", "permissions": 22, "color": 12, "hoist": True, "mentionable": True,},
            reason="eat dirt",
        )

    @pytest.mark.asyncio
    async def test_modify_guild_role_positions(self, rest_impl):
        mock_response = [{"id": "444", "position": 0}, {"id": "999", "position": 1}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_GUILD_ROLES") as (template, compiled):
            assert await rest_impl.modify_guild_role_positions("292929", ("444", 0), ("999", 1)) is mock_response
            template.compile.assert_called_once_with(guild_id="292929")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, body=[{"id": "444", "position": 0}, {"id": "999", "position": 1}]
        )

    @pytest.mark.asyncio
    async def test_modify_guild_role_with_optionals(self, rest_impl):
        mock_response = {"id": "54234", "name": "roleio roleio"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_GUILD_ROLE") as (template, compiled):
            assert await rest_impl.modify_guild_role("999999", "54234") is mock_response
            template.compile.assert_called_once_with(guild_id="999999", role_id="54234")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={}, reason=...)

    @pytest.mark.asyncio
    async def test_modify_guild_role_without_optionals(self, rest_impl):
        mock_response = {"id": "54234", "name": "roleio roleio"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_GUILD_ROLE") as (template, compiled):
            result = await rest_impl.modify_guild_role(
                "999999",
                "54234",
                name="HAHA",
                permissions=42,
                color=69,
                hoist=True,
                mentionable=False,
                reason="You are a pirate.",
            )
            assert result is mock_response
            template.compile.assert_called_once_with(guild_id="999999", role_id="54234")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled,
            body={"name": "HAHA", "permissions": 42, "color": 69, "hoist": True, "mentionable": False,},
            reason="You are a pirate.",
        )

    @pytest.mark.asyncio
    async def test_delete_guild_role(self, rest_impl):
        with mock_patch_route("DELETE_GUILD_ROLE") as (template, compiled):
            assert await rest_impl.delete_guild_role("29292", "4848") is None
            template.compile.assert_called_once_with(guild_id="29292", role_id="4848")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_guild_prune_count(self, rest_impl):
        mock_response = {"pruned": 7}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_PRUNE") as (template, compiled):
            assert await rest_impl.get_guild_prune_count("29292", 14) == 7
            template.compile.assert_called_once_with(guild_id="29292")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, query={"days": 14})

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_response", ({"pruned": None}, {}))
    async def test_begin_guild_prune_without_optionals_returns_none(self, rest_impl, mock_response):
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("POST_GUILD_PRUNE") as (template, compiled):
            assert await rest_impl.begin_guild_prune("39393", 14) is None
            template.compile.assert_called_once_with(guild_id="39393")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, query={"days": 14}, reason=...)

    @pytest.mark.asyncio
    async def test_begin_guild_prune_with_optionals(self, rest_impl):
        rest_impl._request_json_response.return_value = {"pruned": 32}
        with mock_patch_route("POST_GUILD_PRUNE") as (template, compiled):
            assert await rest_impl.begin_guild_prune("39393", 14, compute_prune_count=True, reason="BYEBYE") == 32
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, query={"days": 14, "compute_prune_count": "true"}, reason="BYEBYE"
        )

    @pytest.mark.asyncio
    async def test_get_guild_voice_regions(self, rest_impl):
        mock_response = [{"name": "london", "vip": True}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_VOICE_REGIONS") as (template, compiled):
            assert await rest_impl.get_guild_voice_regions("2393939") is mock_response
            template.compile.assert_called_once_with(guild_id="2393939")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_guild_invites(self, rest_impl):
        mock_response = [{"code": "ewkkww"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_INVITES") as (template, compiled):
            assert await rest_impl.get_guild_invites("9292929") is mock_response
            template.compile.assert_called_once_with(guild_id="9292929")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_guild_integrations(self, rest_impl):
        mock_response = [{"id": "4242"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_INTEGRATIONS") as (template, compiled):
            assert await rest_impl.get_guild_integrations("537340989808050216") is mock_response
            template.compile.assert_called_once_with(guild_id="537340989808050216")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_modify_guild_integration_without_optionals(self, rest_impl):
        with mock_patch_route("PATCH_GUILD_INTEGRATION") as (template, compiled):
            assert await rest_impl.modify_guild_integration("292929", "747474") is None
            template.compile.assert_called_once_with(guild_id="292929", integration_id="747474")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={}, reason=...)

    @pytest.mark.asyncio
    async def test_modify_guild_integration_with_optionals(self, rest_impl):
        with mock_patch_route("PATCH_GUILD_INTEGRATION") as (template, compiled):
            result = await rest_impl.modify_guild_integration(
                "292929",
                "747474",
                expire_behaviour=2,
                expire_grace_period=1,
                enable_emojis=True,
                reason="This password is already taken by {redacted}",
            )
            assert result is None

            template.compile.assert_called_once_with(guild_id="292929", integration_id="747474")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled,
            body={"expire_behaviour": 2, "expire_grace_period": 1, "enable_emoticons": True},
            reason="This password is already taken by {redacted}",
        )

    @pytest.mark.asyncio
    async def test_delete_guild_integration_without_reason(self, rest_impl):
        with mock_patch_route("DELETE_GUILD_INTEGRATION") as (template, compiled):
            assert await rest_impl.delete_guild_integration("23992", "7474") is None
            template.compile.assert_called_once_with(guild_id="23992", integration_id="7474")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, reason=...)

    @pytest.mark.asyncio
    async def test_delete_guild_integration_with_reason(self, rest_impl):
        with mock_patch_route("DELETE_GUILD_INTEGRATION") as (template, compiled):
            assert await rest_impl.delete_guild_integration("23992", "7474", reason="HOT") is None
            template.compile.assert_called_once_with(guild_id="23992", integration_id="7474")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, reason="HOT")

    @pytest.mark.asyncio
    async def test_sync_guild_integration(self, rest_impl):
        with mock_patch_route("POST_GUILD_INTEGRATION_SYNC") as (template, compiled):
            assert await rest_impl.sync_guild_integration("3939439", "84884") is None
            template.compile.assert_called_once_with(guild_id="3939439", integration_id="84884")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_guild_embed(self, rest_impl):
        mock_response = {"channel_id": "4304040", "enabled": True}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_EMBED") as (template, compiled):
            assert await rest_impl.get_guild_embed("4949") is mock_response
            template.compile.assert_called_once_with(guild_id="4949")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_modify_guild_embed_without_reason(self, rest_impl):
        mock_response = {"channel_id": "4444", "enabled": False}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_GUILD_EMBED") as (template, compiled):
            assert await rest_impl.modify_guild_embed("393939", channel_id="222", enabled=True) is mock_response
            template.compile.assert_called_once_with(guild_id="393939")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, body={"channel_id": "222", "enabled": True}, reason=...
        )

    @pytest.mark.asyncio
    async def test_modify_guild_embed_with_reason(self, rest_impl):
        mock_response = {"channel_id": "4444", "enabled": False}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_GUILD_EMBED") as (template, compiled):
            assert (
                await rest_impl.modify_guild_embed("393939", channel_id="222", enabled=True, reason="OK")
                is mock_response
            )
            template.compile.assert_called_once_with(guild_id="393939")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, body={"channel_id": "222", "enabled": True}, reason="OK"
        )

    @pytest.mark.asyncio
    async def test_get_guild_vanity_url(self, rest_impl):
        mock_response = {"code": "dsidid"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_VANITY_URL") as (template, compiled):
            assert await rest_impl.get_guild_vanity_url("399393") is mock_response
            template.compile.assert_called_once_with(guild_id="399393")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    def test_get_guild_widget_image_url_without_style(self, rest_impl):
        url = rest_impl.get_guild_widget_image_url("54949")
        assert url == "https://discord.com/api/v6/guilds/54949/widget.png"

    def test_get_guild_widget_image_url_with_style(self, rest_impl):
        url = rest_impl.get_guild_widget_image_url("54949", style="banner2")
        assert url == "https://discord.com/api/v6/guilds/54949/widget.png?style=banner2"

    @pytest.mark.asyncio
    async def test_get_invite_without_counts(self, rest_impl):
        mock_response = {"code": "fesdfes"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_INVITE") as (template, compiled):
            assert await rest_impl.get_invite("fesdfes") is mock_response
            template.compile.assert_called_once_with(invite_code="fesdfes")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, query={})

    @pytest.mark.asyncio
    async def test_get_invite_with_counts(self, rest_impl):
        mock_response = {"code": "fesdfes"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_INVITE") as (template, compiled):
            assert await rest_impl.get_invite("fesdfes", with_counts=True) is mock_response
            template.compile.assert_called_once_with(invite_code="fesdfes")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, query={"with_counts": "true"})

    @pytest.mark.asyncio
    async def test_delete_invite(self, rest_impl):
        mock_response = {"code": "diidsk"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("DELETE_INVITE") as (template, compiled):
            assert await rest_impl.delete_invite("diidsk") is mock_response
            template.compile.assert_called_once_with(invite_code="diidsk")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_current_application_info(self, rest_impl):
        mock_response = {"bot_public": True}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_MY_APPLICATION") as (template, compiled):
            assert await rest_impl.get_current_application_info() is mock_response
            template.compile.assert_called_once_with()
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_current_user(self, rest_impl):
        mock_response = {"id": "494949", "username": "A name"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_MY_USER") as (template, compiled):
            assert await rest_impl.get_current_user() is mock_response
            template.compile.assert_called_once_with()
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_user(self, rest_impl):
        mock_response = {"id": "54959"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_USER") as (template, compiled):
            assert await rest_impl.get_user("54959") is mock_response
            template.compile.assert_called_once_with(user_id="54959")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_modify_current_user_without_optionals(self, rest_impl):
        mock_response = {"id": "44444", "username": "Watashi"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_MY_USER") as (template, compiled):
            assert await rest_impl.modify_current_user() is mock_response
            template.compile.assert_called_once_with()
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={})

    @pytest.mark.asyncio
    async def test_modify_current_user_with_optionals(self, rest_impl):
        mock_response = {"id": "44444", "username": "Watashi"}
        rest_impl._request_json_response.return_value = mock_response
        mock_route = mock.MagicMock(routes.PATCH_MY_USER)
        mock_image_data = "data:image/png;base64,iVBORw0KGgpibGFo"
        with mock_patch_route("PATCH_MY_USER") as (template, compiled):
            with mock.patch.object(conversions, "image_bytes_to_image_data", return_value=mock_image_data):
                result = await rest_impl.modify_current_user(username="Watashi 2", avatar=b"\211PNG\r\n\032\nblah")
                assert result is mock_response
                template.compile.assert_called_once_with()
                conversions.image_bytes_to_image_data.assert_called_once_with(b"\211PNG\r\n\032\nblah")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, body={"username": "Watashi 2", "avatar": mock_image_data}
        )

    @pytest.mark.asyncio
    async def test_get_current_user_connections(self, rest_impl):
        mock_response = [{"id": "fspeed", "revoked": False}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_MY_CONNECTIONS") as (template, compiled):
            assert await rest_impl.get_current_user_connections() is mock_response
            template.compile.assert_called_once_with()
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_current_user_guilds_without_optionals(self, rest_impl):
        mock_response = [{"id": "452", "owner_id": "4949"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_MY_GUILDS") as (template, compiled):
            assert await rest_impl.get_current_user_guilds() is mock_response
            template.compile.assert_called_once_with()
        rest_impl._request_json_response.assert_awaited_once_with(compiled, query={})

    @pytest.mark.asyncio
    async def test_get_current_user_guilds_with_optionals(self, rest_impl):
        mock_response = [{"id": "452", "owner_id": "4949"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_MY_GUILDS") as (template, compiled):
            assert await rest_impl.get_current_user_guilds(before="292929", after="22288", limit=5) is mock_response
            template.compile.assert_called_once_with()
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, query={"before": "292929", "after": "22288", "limit": 5}
        )

    @pytest.mark.asyncio
    async def test_leave_guild(self, rest_impl):
        with mock_patch_route("DELETE_MY_GUILD") as (template, compiled):
            assert await rest_impl.leave_guild("292929") is None
            template.compile.assert_called_once_with(guild_id="292929")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_create_dm(self, rest_impl):
        mock_response = {"id": "404040", "recipients": []}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("POST_MY_CHANNELS") as (template, compiled):
            assert await rest_impl.create_dm("409491291156774923") is mock_response
            template.compile.assert_called_once_with()
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={"recipient_id": "409491291156774923"})

    @pytest.mark.asyncio
    async def test_list_voice_regions(self, rest_impl):
        mock_response = [{"name": "neko-cafe"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_VOICE_REGIONS") as (template, compiled):
            assert await rest_impl.list_voice_regions() is mock_response
            template.compile.assert_called_once_with()
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_create_webhook_without_optionals(self, rest_impl):
        mock_response = {"channel_id": "39393993", "id": "8383838"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("POST_CHANNEL_WEBHOOKS") as (template, compiled):
            assert await rest_impl.create_webhook("39393939", "I am a webhook") is mock_response
            template.compile.assert_called_once_with(channel_id="39393939")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, body={"name": "I am a webhook"}, reason=...)

    @pytest.mark.asyncio
    async def test_create_webhook_with_optionals(self, rest_impl):
        mock_response = {"channel_id": "39393993", "id": "8383838"}
        rest_impl._request_json_response.return_value = mock_response
        mock_image_data = "data:image/png;base64,iVBORw0KGgpibGFo"
        with mock_patch_route("POST_CHANNEL_WEBHOOKS") as (template, compiled):
            with mock.patch.object(conversions, "image_bytes_to_image_data", return_value=mock_image_data):
                result = await rest_impl.create_webhook(
                    "39393939", "I am a webhook", avatar=b"\211PNG\r\n\032\nblah", reason="get reasoned"
                )
                assert result is mock_response
                template.compile.assert_called_once_with(channel_id="39393939")
                conversions.image_bytes_to_image_data.assert_called_once_with(b"\211PNG\r\n\032\nblah")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, body={"name": "I am a webhook", "avatar": mock_image_data}, reason="get reasoned",
        )

    @pytest.mark.asyncio
    async def test_get_channel_webhooks(self, rest_impl):
        mock_response = [{"channel_id": "39393993", "id": "8383838"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_CHANNEL_WEBHOOKS") as (template, compiled):
            assert await rest_impl.get_channel_webhooks("9393939") is mock_response
            template.compile.assert_called_once_with(channel_id="9393939")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_guild_webhooks(self, rest_impl):
        mock_response = [{"channel_id": "39393993", "id": "8383838"}]
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_GUILD_WEBHOOKS") as (template, compiled):
            assert await rest_impl.get_guild_webhooks("9393939") is mock_response
            template.compile.assert_called_once_with(guild_id="9393939")
        rest_impl._request_json_response.assert_awaited_once_with(compiled)

    @pytest.mark.asyncio
    async def test_get_webhook_without_token(self, rest_impl):
        mock_response = {"channel_id": "39393993", "id": "8383838"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_WEBHOOK") as (template, compiled):
            assert await rest_impl.get_webhook("9393939") is mock_response
            template.compile.assert_called_once_with(webhook_id="9393939")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, suppress_authorization_header=False)

    @pytest.mark.asyncio
    async def test_get_webhook_with_token(self, rest_impl):
        mock_response = {"channel_id": "39393993", "id": "8383838"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("GET_WEBHOOK_WITH_TOKEN") as (template, compiled):
            assert await rest_impl.get_webhook("9393939", webhook_token="a_webhook_token") is mock_response
            template.compile.assert_called_once_with(webhook_id="9393939", webhook_token="a_webhook_token")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, suppress_authorization_header=True)

    @pytest.mark.asyncio
    async def test_modify_webhook_without_optionals_without_token(self, rest_impl):
        mock_response = {"channel_id": "39393993", "id": "8383838"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_WEBHOOK") as (template, compiled):
            assert await rest_impl.modify_webhook("929292") is mock_response
            template.compile.assert_called_once_with(webhook_id="929292")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, body={}, reason=..., suppress_authorization_header=False
        )

    @pytest.mark.asyncio
    async def test_modify_webhook_with_optionals_without_token(self, rest_impl):
        mock_response = {"channel_id": "39393993", "id": "8383838"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_WEBHOOK") as (template, compiled):
            assert (
                await rest_impl.modify_webhook(
                    "929292", name="nyaa", avatar=b"\211PNG\r\n\032\nblah", channel_id="2929292929", reason="nuzzle",
                )
                is mock_response
            )
            template.compile.assert_called_once_with(webhook_id="929292")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled,
            body={"name": "nyaa", "avatar": "data:image/png;base64,iVBORw0KGgpibGFo", "channel_id": "2929292929",},
            reason="nuzzle",
            suppress_authorization_header=False,
        )

    @pytest.mark.asyncio
    async def test_modify_webhook_without_optionals_with_token(self, rest_impl):
        mock_response = {"channel_id": "39393993", "id": "8383838"}
        rest_impl._request_json_response.return_value = mock_response
        with mock_patch_route("PATCH_WEBHOOK_WITH_TOKEN") as (template, compiled):
            assert await rest_impl.modify_webhook("929292", webhook_token="a_webhook_token") is mock_response
            template.compile.assert_called_once_with(webhook_id="929292", webhook_token="a_webhook_token")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, body={}, reason=..., suppress_authorization_header=True
        )

    @pytest.mark.asyncio
    async def test_delete_webhook_without_token(self, rest_impl):
        with mock_patch_route("DELETE_WEBHOOK") as (template, compiled):
            assert await rest_impl.delete_webhook("9393939") is None
            template.compile.assert_called_once_with(webhook_id="9393939")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, suppress_authorization_header=False)

    @pytest.mark.asyncio
    async def test_delete_webhook_with_token(self, rest_impl):
        with mock_patch_route("DELETE_WEBHOOK_WITH_TOKEN") as (template, compiled):
            assert await rest_impl.delete_webhook("9393939", webhook_token="a_webhook_token") is None
            template.compile.assert_called_once_with(webhook_id="9393939", webhook_token="a_webhook_token")
        rest_impl._request_json_response.assert_awaited_once_with(compiled, suppress_authorization_header=True)

    @pytest.mark.asyncio
    async def test_execute_webhook_without_optionals(self, rest_impl):
        mock_form = mock.MagicMock(aiohttp.FormData, add_field=mock.MagicMock())
        rest_impl._request_json_response.return_value = None
        mock_json = "{}"
        with mock.patch.object(aiohttp, "FormData", return_value=mock_form):
            with mock_patch_route("POST_WEBHOOK_WITH_TOKEN") as (template, compiled):
                with mock.patch.object(json, "dumps", return_value=mock_json):
                    assert await rest_impl.execute_webhook("9393939", "a_webhook_token") is None
                    template.compile.assert_called_once_with(webhook_id="9393939", webhook_token="a_webhook_token")
                    json.dumps.assert_called_once_with({})
        mock_form.add_field.assert_called_once_with("payload_json", mock_json, content_type="application/json")
        rest_impl._request_json_response.assert_awaited_once_with(
            compiled, body=mock_form, query={}, suppress_authorization_header=True,
        )

    @pytest.mark.asyncio
    @mock.patch.object(aiohttp, "FormData")
    @mock.patch.object(json, "dumps")
    async def test_execute_webhook_with_optionals(self, dumps, FormData, rest_impl):
        with mock_patch_route("POST_WEBHOOK_WITH_TOKEN") as (template, compiled):
            mock_form = mock.MagicMock(aiohttp.FormData, add_field=mock.MagicMock())
            FormData.return_value = mock_form
            mock_response = {"id": "53", "content": "la"}
            rest_impl._request_json_response.return_value = mock_response
            mock_file = mock.MagicMock(files.BaseStream)
            mock_file.name = "file.txt"
            mock_file2 = mock.MagicMock(files.BaseStream)
            mock_file2.name = "file2.txt"
            mock_json = '{"content": "A messages", "username": "agent 42"}'
            dumps.return_value = mock_json
            response = await rest_impl.execute_webhook(
                "9393939",
                "a_webhook_token",
                content="A message",
                username="agent 42",
                avatar_url="https://localhost.bump",
                tts=True,
                wait=True,
                files=[mock_file, mock_file2],
                embeds=[{"type": "rich", "description": "A DESCRIPTION"}],
                allowed_mentions={"users": ["123"], "roles": ["456"]},
            )
            assert response is mock_response
            template.compile.assert_called_once_with(webhook_id="9393939", webhook_token="a_webhook_token")
            dumps.assert_called_once_with(
                {
                    "tts": True,
                    "content": "A message",
                    "username": "agent 42",
                    "avatar_url": "https://localhost.bump",
                    "embeds": [{"type": "rich", "description": "A DESCRIPTION"}],
                    "allowed_mentions": {"users": ["123"], "roles": ["456"]},
                }
            )

            assert mock_form.add_field.call_count == 3
            mock_form.add_field.assert_has_calls(
                (
                    mock.call("payload_json", mock_json, content_type="application/json"),
                    mock.call("file0", mock_file, filename="file.txt", content_type="application/octet-stream"),
                    mock.call("file1", mock_file2, filename="file2.txt", content_type="application/octet-stream"),
                ),
                any_order=True,
            )

            rest_impl._request_json_response.assert_awaited_once_with(
                compiled, body=mock_form, query={"wait": "true"}, suppress_authorization_header=True,
            )
