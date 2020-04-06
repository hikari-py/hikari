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
import io
import json
import logging
import ssl
import unittest.mock

import aiohttp
import cymock as mock
import pytest

from hikari.internal import conversions
from hikari import errors
from hikari.net import ratelimits
from hikari.net import rest
from hikari.net import routes
from hikari.net import versions
from tests.hikari import _helpers


class TestLowLevelRestfulClient:
    @pytest.fixture
    def rest_impl(self):
        class LowLevelRestfulClientImpl(rest.LowLevelRestfulClient):
            def __init__(self, *args, **kwargs):
                self.base_url = "https://discordapp.com/api/v6"
                self.client_session = mock.MagicMock(close=mock.AsyncMock())
                self.logger = mock.MagicMock()
                self.ratelimiter = mock.create_autospec(
                    ratelimits.HTTPBucketRateLimiterManager,
                    auto_spec=True,
                    acquire=mock.MagicMock(),
                    update_rate_limits=mock.MagicMock(),
                )
                self.global_ratelimiter = mock.create_autospec(
                    ratelimits.ManualRateLimiter, auto_spec=True, acquire=mock.MagicMock(), throttle=mock.MagicMock()
                )
                self._request = mock.AsyncMock(return_value=...)

        return LowLevelRestfulClientImpl()

    @pytest.fixture
    def compiled_route(self):
        class CompiledRoute:
            method: str = "get"

            def create_url(self, base_url: str):
                return base_url + "/somewhere"

        return CompiledRoute()

    @pytest.fixture
    def exit_error(self):
        class ExitError(BaseException):
            ...

        return ExitError

    @pytest.fixture
    def discord_response(self):
        class Response:
            headers: dict = {"Date": "Mon, 16 Nov 2009 13:32:02 +0100", "Content-Type": "application/json"}
            status: int = 0
            reason: str = "some reason"
            raw_body: str = '{"message": "some_message", "code": 123}'

            async def read(self):
                return self.raw_body

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        return Response()

    @pytest.mark.asyncio
    async def test_rest___aenter___and___aexit__(self):
        class LowLevelRestfulClientImpl(rest.LowLevelRestfulClient):
            def __init__(self, *args, **kwargs):
                kwargs.setdefault("token", "Bearer xxx")
                super().__init__(*args, **kwargs)
                self.close = mock.AsyncMock()

        inst = LowLevelRestfulClientImpl()

        async with inst as client:
            assert client is inst

        inst.close.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_rest_close_calls_client_session_close(self):
        class LowLevelRestfulClientImpl(rest.LowLevelRestfulClient):
            def __init__(self, *args, **kwargs):
                self.client_session = mock.MagicMock()
                self.client_session.close = mock.AsyncMock()
                self.logger = logging.getLogger(__name__)

        inst = LowLevelRestfulClientImpl()

        await inst.close()

        inst.client_session.close.assert_called_with()

    @pytest.mark.asyncio
    async def test__init__with_bot_token_and_without_optionals(self):
        mock_manual_rate_limiter = mock.MagicMock()
        buckets_mock = mock.MagicMock()

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(ratelimits, "ManualRateLimiter", return_value=mock_manual_rate_limiter))
        stack.enter_context(mock.patch.object(ratelimits, "HTTPBucketRateLimiterManager", return_value=buckets_mock))

        with stack:
            client = rest.LowLevelRestfulClient(token="Bot token.otacon.a-token")

        assert client.base_url == f"https://discordapp.com/api/v{int(versions.HTTPAPIVersion.STABLE)}"
        assert client.global_ratelimiter is mock_manual_rate_limiter
        assert client.json_serialize is json.dumps
        assert client.json_deserialize is json.loads
        assert client.ratelimiter is buckets_mock
        assert client.token == "Bot token.otacon.a-token"

    @pytest.mark.asyncio
    async def test__init__with_bearer_token_and_without_optionals(self):
        client = rest.LowLevelRestfulClient(token="Bearer token.otacon.a-token")
        assert client.token == "Bearer token.otacon.a-token"

    @pytest.mark.asyncio
    async def test__init__with_optionals(self):
        mock_manual_rate_limiter = mock.MagicMock(ratelimits.ManualRateLimiter)
        mock_http_bucket_rate_limit_manager = mock.MagicMock(ratelimits.HTTPBucketRateLimiterManager)
        mock_connector = mock.MagicMock(aiohttp.BaseConnector)
        mock_dumps = mock.MagicMock(json.dumps)
        mock_loads = mock.MagicMock(json.loads)
        mock_proxy_auth = mock.MagicMock(aiohttp.BasicAuth)
        mock_proxy_headers = {"User-Agent": "Agent 42"}
        mock_ssl_context = mock.MagicMock(ssl.SSLContext)

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(aiohttp, "ClientSession"))
        stack.enter_context(mock.patch.object(ratelimits, "ManualRateLimiter", return_value=mock_manual_rate_limiter))
        stack.enter_context(
            mock.patch.object(
                ratelimits, "HTTPBucketRateLimiterManager", return_value=mock_http_bucket_rate_limit_manager
            )
        )

        with stack:
            client = rest.LowLevelRestfulClient(
                token="Bot token.otacon.a-token",
                base_url="https://discordapp.com/api/v69420",
                allow_redirects=True,
                connector=mock_connector,
                proxy_headers=mock_proxy_headers,
                proxy_auth=mock_proxy_auth,
                proxy_url="a.proxy.url.today.nep",
                ssl_context=mock_ssl_context,
                verify_ssl=False,
                timeout=30.53,
                json_deserialize=mock_loads,
                json_serialize=mock_dumps,
            )
            assert client.base_url == "https://discordapp.com/api/v69420"
            assert client.global_ratelimiter is mock_manual_rate_limiter
            assert client.json_serialize is mock_dumps
            assert client.json_deserialize is mock_loads
            assert client.ratelimiter is mock_http_bucket_rate_limit_manager
            assert client.token == "Bot token.otacon.a-token"

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=RuntimeError)
    async def test__init__raises_runtime_error_with_invalid_token(self, *_):
        async with rest.LowLevelRestfulClient(token="An-invalid-TOKEN"):
            pass

    @pytest.mark.asyncio
    async def test_close(self, rest_impl):
        await rest_impl.close()
        rest_impl.ratelimiter.close.assert_called_once_with()
        rest_impl.client_session.close.assert_called_once_with()

    @pytest.fixture()
    @mock.patch.object(ratelimits, "ManualRateLimiter")
    @mock.patch.object(ratelimits, "HTTPBucketRateLimiterManager")
    async def rest_impl_with__request(self, *args):
        rest_impl = rest.LowLevelRestfulClient(token="Bot token")
        rest_impl.logger = mock.MagicMock(debug=mock.MagicMock())
        rest_impl.ratelimiter = mock.create_autospec(
            ratelimits.HTTPBucketRateLimiterManager,
            auto_spec=True,
            acquire=mock.MagicMock(),
            update_rate_limits=mock.MagicMock(),
        )
        rest_impl.global_ratelimiter = mock.create_autospec(
            ratelimits.ManualRateLimiter, auto_spec=True, acquire=mock.MagicMock(), throttle=mock.MagicMock()
        )
        return rest_impl

    @pytest.mark.asyncio
    async def test__request_acquires_ratelimiter(self, compiled_route, exit_error, rest_impl_with__request):
        rest_impl = await rest_impl_with__request
        rest_impl.logger.debug.side_effect = exit_error

        with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()):
            try:
                await rest_impl._request(compiled_route)
            except exit_error:
                pass

            rest_impl.ratelimiter.acquire.asset_called_once_with(compiled_route)

    @pytest.mark.asyncio
    async def test__request_sets_Authentication_if_token(self, compiled_route, exit_error, rest_impl_with__request):
        rest_impl = await rest_impl_with__request
        rest_impl.logger.debug.side_effect = [None, exit_error]

        stack = contextlib.ExitStack()
        mock_request = stack.enter_context(mock.patch.object(aiohttp.ClientSession, "request"))
        stack.enter_context(mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()))

        with stack:
            try:
                await rest_impl._request(compiled_route)
            except exit_error:
                pass

            mock_request.assert_called_with(
                "get",
                "https://discordapp.com/api/v6/somewhere",
                headers={"X-RateLimit-Precision": "millisecond", "Authorization": "Bot token"},
                json=None,
                params=None,
                data=None,
                allow_redirects=False,
                proxy=None,
                proxy_auth=None,
                proxy_headers=None,
                verify_ssl=True,
                ssl_context=None,
                timeout=None,
            )

    @pytest.mark.asyncio
    async def test__request_doesnt_set_Authentication_if_suppress_authorization_header(
        self, compiled_route, exit_error, rest_impl_with__request
    ):
        rest_impl = await rest_impl_with__request
        rest_impl.logger.debug.side_effect = [None, exit_error]

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()))
        mock_request = stack.enter_context(mock.patch.object(aiohttp.ClientSession, "request"))

        with stack:
            try:
                await rest_impl._request(compiled_route, suppress_authorization_header=True)
            except exit_error:
                pass

            mock_request.assert_called_with(
                "get",
                "https://discordapp.com/api/v6/somewhere",
                headers={"X-RateLimit-Precision": "millisecond"},
                json=None,
                params=None,
                data=None,
                allow_redirects=False,
                proxy=None,
                proxy_auth=None,
                proxy_headers=None,
                verify_ssl=True,
                ssl_context=None,
                timeout=None,
            )

    @pytest.mark.asyncio
    async def test__request_sets_X_Audit_Log_Reason_if_reason(
        self, compiled_route, exit_error, rest_impl_with__request
    ):
        rest_impl = await rest_impl_with__request
        rest_impl.logger.debug.side_effect = [None, exit_error]

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()))
        mock_request = stack.enter_context(mock.patch.object(aiohttp.ClientSession, "request"))

        with stack:
            try:
                await rest_impl._request(compiled_route, reason="test reason")
            except exit_error:
                pass

            mock_request.assert_called_with(
                "get",
                "https://discordapp.com/api/v6/somewhere",
                headers={
                    "X-RateLimit-Precision": "millisecond",
                    "Authorization": "Bot token",
                    "X-Audit-Log-Reason": "test reason",
                },
                json=None,
                params=None,
                data=None,
                allow_redirects=False,
                proxy=None,
                proxy_auth=None,
                proxy_headers=None,
                verify_ssl=True,
                ssl_context=None,
                timeout=None,
            )

    @pytest.mark.asyncio
    async def test__request_updates_headers_with_provided_headers(
        self, compiled_route, exit_error, rest_impl_with__request
    ):
        rest_impl = await rest_impl_with__request
        rest_impl.logger.debug.side_effect = [None, exit_error]

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()))
        mock_request = stack.enter_context(mock.patch.object(aiohttp.ClientSession, "request"))

        with stack:
            try:
                await rest_impl._request(
                    compiled_route, headers={"X-RateLimit-Precision": "nanosecond", "Authorization": "Bearer token"}
                )
            except exit_error:
                pass

            mock_request.assert_called_with(
                "get",
                "https://discordapp.com/api/v6/somewhere",
                headers={"X-RateLimit-Precision": "nanosecond", "Authorization": "Bearer token"},
                json=None,
                params=None,
                data=None,
                allow_redirects=False,
                proxy=None,
                proxy_auth=None,
                proxy_headers=None,
                verify_ssl=True,
                ssl_context=None,
                timeout=None,
            )

    @pytest.mark.asyncio
    async def test__request_resets_seek_on_seekable_resources(
        self, compiled_route, exit_error, rest_impl_with__request
    ):
        class SeekableResource:
            seeked: bool
            pos: int
            initial_pos: int

            def __init__(self, pos):
                self.pos = pos
                self.initial_pos = pos
                self.seeked = False

            def seek(self, pos):
                self.seeked = True
                self.pos = pos

            def tell(self):
                return self.pos

            def assert_seek_called(self):
                assert self.seeked

            def read(self):
                ...

            def close(self):
                ...

        rest_impl = await rest_impl_with__request
        rest_impl.logger.debug.side_effect = exit_error
        seekable_resources = [SeekableResource(5), SeekableResource(37), SeekableResource(16)]

        with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()):
            try:
                await rest_impl._request(compiled_route, re_seekable_resources=seekable_resources)
            except exit_error:
                pass

            for resource in seekable_resources:
                resource.assert_seek_called()
                assert resource.pos == resource.initial_pos

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "content_type", ["text/plain", "text/html"],
    )
    async def test__request_handles_bad_response_when_content_type_is_plain_or_html(
        self, content_type, exit_error, compiled_route, discord_response, rest_impl_with__request
    ):
        discord_response.headers["Content-Type"] = content_type
        rest_impl = await rest_impl_with__request
        rest_impl._handle_bad_response = mock.AsyncMock(side_effect=[None, exit_error])

        rest_impl.client_session.request = mock.MagicMock(return_value=discord_response)
        with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()):
            try:
                await rest_impl._request(compiled_route)
            except exit_error:
                pass

            rest_impl._handle_bad_response.assert_called()

    @pytest.mark.asyncio
    async def test__request_when_invalid_content_type(self, compiled_route, discord_response, rest_impl_with__request):
        discord_response.headers["Content-Type"] = "something/invalid"
        rest_impl = await rest_impl_with__request

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()))
        stack.enter_context(mock.patch.object(aiohttp.ClientSession, "request", return_value=discord_response))

        with stack:
            assert await rest_impl._request(compiled_route, json_body={}) is None

    @pytest.mark.asyncio
    async def test__request_when_TOO_MANY_REQUESTS_when_global(
        self, compiled_route, exit_error, discord_response, rest_impl_with__request
    ):
        discord_response.status = 429
        discord_response.raw_body = '{"retry_after": 1, "global": true}'
        rest_impl = await rest_impl_with__request
        rest_impl.global_ratelimiter.throttle = mock.MagicMock(side_effect=[None, exit_error])

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()))
        stack.enter_context(mock.patch.object(aiohttp.ClientSession, "request", return_value=discord_response))

        with stack:
            try:
                await rest_impl._request(compiled_route)
            except exit_error:
                pass

            rest_impl.global_ratelimiter.throttle.assert_called_with(0.001)

    @pytest.mark.asyncio
    async def test__request_when_TOO_MANY_REQUESTS_when_not_global(
        self, compiled_route, exit_error, discord_response, rest_impl_with__request
    ):
        discord_response.status = 429
        discord_response.raw_body = '{"retry_after": 1, "global": false}'
        rest_impl = await rest_impl_with__request
        rest_impl.logger.debug.side_effect = [None, exit_error]

        with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()):
            with mock.patch.object(rest.LowLevelRestfulClient, "_request", return_value=discord_response):
                try:
                    await rest_impl._request(compiled_route)
                except exit_error:
                    pass

                rest_impl.global_ratelimiter.throttle.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("api_version", [versions.HTTPAPIVersion.V6, versions.HTTPAPIVersion.V7])
    @pytest.mark.parametrize(
        ["status_code", "error"],
        [
            (400, errors.BadRequestHTTPError),
            (401, errors.UnauthorizedHTTPError),
            (403, errors.ForbiddenHTTPError),
            (404, errors.NotFoundHTTPError),
            (405, errors.ClientHTTPError),
        ],
    )
    @mock.patch.object(ratelimits, "ManualRateLimiter")
    @mock.patch.object(ratelimits, "HTTPBucketRateLimiterManager")
    async def test__request_raises_appropriate_error_for_status_code(
        self, *patches, status_code, error, compiled_route, discord_response, api_version
    ):
        discord_response.status = status_code
        rest_impl = rest.LowLevelRestfulClient(token="Bot token", version=api_version)
        rest_impl.ratelimiter = mock.MagicMock()
        rest_impl.global_ratelimiter = mock.MagicMock()
        rest_impl.client_session.request = mock.MagicMock(return_value=discord_response)

        with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()):
            try:
                await rest_impl._request(compiled_route)
                assert False
            except error:
                assert True

    @pytest.mark.asyncio
    async def test__request_when_NO_CONTENT(self, compiled_route, discord_response, rest_impl_with__request):
        discord_response.status = 204
        rest_impl = await rest_impl_with__request
        rest_impl.client_session.request = mock.MagicMock(return_value=discord_response)

        with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()):
            assert await rest_impl._request(compiled_route, form_body=aiohttp.FormData()) is None

    @pytest.mark.asyncio
    async def test__request_handles_bad_response_when_error_results_in_retry(
        self, exit_error, compiled_route, discord_response, rest_impl_with__request
    ):
        discord_response.raw_body = "{}"
        discord_response.status = 1000
        rest_impl = await rest_impl_with__request
        rest_impl._handle_bad_response = mock.AsyncMock(side_effect=[None, exit_error])

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(aiohttp.ClientSession, "request", return_value=discord_response))
        stack.enter_context(mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()))

        with stack:
            try:
                await rest_impl._request(compiled_route)
            except exit_error:
                pass

            assert rest_impl._handle_bad_response.call_count == 2

    @pytest.mark.asyncio
    async def test_handle_bad_response(self, rest_impl):
        backoff = _helpers.create_autospec(ratelimits.ExponentialBackOff, __next__=mock.MagicMock(return_value=4))
        mock_route = mock.MagicMock(routes.CompiledRoute)
        with mock.patch.object(asyncio, "sleep"):
            await rest_impl._handle_bad_response(backoff, "Being spammy", mock_route, "You are being rate limited", 429)
            asyncio.sleep.assert_called_once_with(4)

    @pytest.mark.asyncio
    async def test_handle_bad_response_raises_server_http_error_on_timeout(self, rest_impl):
        backoff = _helpers.create_autospec(
            ratelimits.ExponentialBackOff, __next__=mock.MagicMock(side_effect=asyncio.TimeoutError())
        )
        mock_route = mock.MagicMock(routes.CompiledRoute)
        mock_exception = errors.ServerHTTPError("A reason", ..., ..., ...)
        excepted_exception = errors.ServerHTTPError
        with mock.patch.object(errors, "ServerHTTPError", side_effect=mock_exception):
            try:
                await rest_impl._handle_bad_response(
                    backoff, "Being spammy", mock_route, "You are being rate limited", 429
                )
            except excepted_exception as e:
                assert e is mock_exception
                errors.ServerHTTPError.assert_called_once_with(
                    "Being spammy", mock_route, "You are being rate limited", 429
                )
            else:
                assert False, "Missing `ServerHTTPError`, should be raised on timeout."

    @pytest.mark.asyncio
    async def test_get_gateway(self, rest_impl):
        rest_impl._request.return_value = {"url": "discord.discord///"}
        mock_route = mock.MagicMock(routes.GATEWAY)
        with mock.patch.object(routes, "GATEWAY", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_gateway() == "discord.discord///"
            routes.GATEWAY.compile.assert_called_once_with(rest_impl.GET)
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_gateway_bot(self, rest_impl):
        mock_response = {"url": "discord.discord///"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GATEWAY_BOT)
        with mock.patch.object(routes, "GATEWAY_BOT", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_gateway_bot() is mock_response
            routes.GATEWAY_BOT.compile.assert_called_once_with(rest_impl.GET)
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_guild_audit_log_without_optionals(self, rest_impl):
        mock_response = {"webhooks": [], "users": []}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_AUDIT_LOGS)
        with mock.patch.object(routes, "GUILD_AUDIT_LOGS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_guild_audit_log("2929292929") is mock_response
            routes.GUILD_AUDIT_LOGS.compile.assert_called_once_with(rest_impl.GET, guild_id="2929292929")
        rest_impl._request.assert_called_once_with(mock_route, query={})

    @pytest.mark.asyncio
    async def test_get_guild_audit_log_with_optionals(self, rest_impl):
        mock_response = {"webhooks": [], "users": []}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_AUDIT_LOGS)
        with mock.patch.object(routes, "GUILD_AUDIT_LOGS", compile=mock.MagicMock(return_value=mock_route)):
            assert (
                await rest_impl.get_guild_audit_log(
                    "2929292929", user_id="115590097100865541", action_type=42, limit=5, before="123123123"
                )
                is mock_response
            )
            routes.GUILD_AUDIT_LOGS.compile.assert_called_once_with(rest_impl.GET, guild_id="2929292929")
        rest_impl._request.assert_called_once_with(
            mock_route, query={"user_id": "115590097100865541", "action_type": 42, "limit": 5, "before": "123123123"}
        )

    @pytest.mark.asyncio
    async def test_get_channel(self, rest_impl):
        mock_response = {"id": "20202020200202"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL)
        with mock.patch.object(routes, "CHANNEL", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_channel("20202020020202") is mock_response
            routes.CHANNEL.compile.assert_called_once_with(rest_impl.GET, channel_id="20202020020202")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_modify_channel_without_optionals(self, rest_impl):
        mock_response = {"id": "20393939"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL)
        with mock.patch.object(routes, "CHANNEL", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.modify_channel("6942069420") is mock_response
            routes.CHANNEL.compile.assert_called_once_with(rest_impl.PATCH, channel_id="6942069420")
        rest_impl._request.assert_called_once_with(mock_route, json_body={}, reason=...)

    @pytest.mark.asyncio
    async def test_modify_channel_with_optionals(self, rest_impl):
        mock_response = {"id": "20393939"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL)
        with mock.patch.object(routes, "CHANNEL", compile=mock.MagicMock(return_value=mock_route)):
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
            routes.CHANNEL.compile.assert_called_once_with(rest_impl.PATCH, channel_id="6942069420")
        rest_impl._request.assert_called_once_with(
            mock_route,
            json_body={
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
        mock_route = mock.MagicMock(routes.CHANNEL)
        with mock.patch.object(routes, "CHANNEL", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_close_channel("939392929") is None
            routes.CHANNEL.compile.assert_called_once_with(rest_impl.DELETE, channel_id="939392929")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_channel_messages_without_optionals(self, rest_impl):
        mock_response = [{"id": "29492", "content": "Kon'nichiwa"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL_MESSAGES)
        with mock.patch.object(routes, "CHANNEL_MESSAGES", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_channel_messages("9292929292") is mock_response
            routes.CHANNEL_MESSAGES.compile.assert_called_once_with(rest_impl.GET, channel_id="9292929292")
        rest_impl._request.assert_called_once_with(mock_route, query={})

    @pytest.mark.asyncio
    async def test_get_channel_messages_with_optionals(self, rest_impl):
        mock_response = [{"id": "29492", "content": "Kon'nichiwa"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL_MESSAGES)
        with mock.patch.object(routes, "CHANNEL_MESSAGES", compile=mock.MagicMock(return_value=mock_route)):
            assert (
                await rest_impl.get_channel_messages(
                    "9292929292", limit=42, after="293939393", before="4945959595", around="44444444",
                )
                is mock_response
            )
            routes.CHANNEL_MESSAGES.compile.assert_called_once_with(rest_impl.GET, channel_id="9292929292")
        rest_impl._request.assert_called_once_with(
            mock_route, query={"limit": 42, "after": "293939393", "before": "4945959595", "around": "44444444",}
        )

    @pytest.mark.asyncio
    async def test_get_channel_message(self, rest_impl):
        mock_response = {"content": "I'm really into networking with cute routers and modems."}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL_MESSAGE)
        with mock.patch.object(routes, "CHANNEL_MESSAGE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_channel_message("1111111111", "42424242") is mock_response
            routes.CHANNEL_MESSAGE.compile.assert_called_once_with(
                rest_impl.GET, channel_id="1111111111", message_id="42424242"
            )
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_create_message_without_optionals(self, rest_impl):
        mock_response = {"content": "nyaa, nyaa, nyaa."}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL_MESSAGE)
        mock_form = mock.MagicMock(spec_set=aiohttp.FormData, add_field=mock.MagicMock())
        with mock.patch.object(routes, "CHANNEL_MESSAGES", compile=mock.MagicMock(return_value=mock_route)):
            with mock.patch.object(aiohttp, "FormData", autospec=True, return_value=mock_form):
                assert await rest_impl.create_message("22222222") is mock_response
                routes.CHANNEL_MESSAGES.compile.assert_called_once_with(rest_impl.POST, channel_id="22222222")
                mock_form.add_field.assert_called_once_with(
                    "payload_json", json.dumps({}), content_type="application/json"
                )
        rest_impl._request.assert_called_once_with(mock_route, form_body=mock_form, re_seekable_resources=[])

    @pytest.mark.asyncio
    @unittest.mock.patch.object(routes, "CHANNEL_MESSAGES")
    @unittest.mock.patch.object(aiohttp, "FormData", autospec=True)
    @unittest.mock.patch.object(conversions, "make_resource_seekable")
    @unittest.mock.patch.object(json, "dumps")
    async def test_create_message_with_optionals(
        self, dumps, make_resource_seekable, FormData, CHANNEL_MESSAGES, rest_impl
    ):
        mock_response = {"content": "nyaa, nyaa, nyaa."}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL_MESSAGE)
        CHANNEL_MESSAGES.compile.return_value = mock_route
        mock_form = mock.MagicMock(spec_set=aiohttp.FormData, add_field=mock.MagicMock())
        FormData.return_value = mock_form
        mock_file = mock.MagicMock(io.BytesIO)
        make_resource_seekable.return_value = mock_file
        mock_json = '{"description": "I am a message", "tts": "True"}'
        dumps.return_value = mock_json

        result = await rest_impl.create_message(
            "22222222",
            content="I am a message",
            nonce="ag993okskm_cdolsio",
            tts=True,
            files=[("file.txt", b"okdsio9u8oij32")],
            embed={"description": "I am an embed"},
            allowed_mentions={"users": ["123"], "roles": ["456"]},
        )
        assert result is mock_response
        CHANNEL_MESSAGES.compile.assert_called_once_with(rest_impl.POST, channel_id="22222222")
        make_resource_seekable.assert_called_once_with(b"okdsio9u8oij32")
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
        rest_impl._request.assert_called_once_with(mock_route, form_body=mock_form, re_seekable_resources=[mock_file])

    @pytest.mark.asyncio
    async def test_create_reaction(self, rest_impl):
        mock_route = mock.MagicMock(routes.OWN_REACTION)
        with mock.patch.object(routes, "OWN_REACTION", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.create_reaction("20202020", "8484848", "emoji:2929") is None
            routes.OWN_REACTION.compile.assert_called_once_with(
                rest_impl.PUT, channel_id="20202020", message_id="8484848", emoji="emoji:2929"
            )
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_delete_own_reaction(self, rest_impl):
        mock_route = mock.MagicMock(routes.OWN_REACTION)
        with mock.patch.object(routes, "OWN_REACTION", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_own_reaction("20202020", "8484848", "emoji:2929") is None
            routes.OWN_REACTION.compile.assert_called_once_with(
                rest_impl.DELETE, channel_id="20202020", message_id="8484848", emoji="emoji:2929"
            )
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_delete_all_reactions_for_emoji(self, rest_impl):
        mock_route = mock.MagicMock(routes.REACTION_EMOJI)
        with mock.patch.object(routes, "REACTION_EMOJI", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_all_reactions_for_emoji("222", "333", "222:owo") is None
            routes.REACTION_EMOJI.compile.assert_called_once_with(
                rest_impl.DELETE, channel_id="222", message_id="333", emoji="222:owo"
            )

    @pytest.mark.asyncio
    async def test_delete_user_reaction(self, rest_impl):
        mock_route = mock.MagicMock(routes.REACTION_EMOJI_USER)
        with mock.patch.object(routes, "REACTION_EMOJI_USER", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_user_reaction("11111", "4444", "emoji:42", "29292992") is None
            routes.REACTION_EMOJI_USER.compile.assert_called_once_with(
                rest_impl.DELETE, channel_id="11111", message_id="4444", emoji="emoji:42", user_id="29292992"
            )
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_reactions_without_optionals(self, rest_impl):
        mock_response = [{"id": "42"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.REACTIONS)
        with mock.patch.object(routes, "REACTIONS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_reactions("29292929", "48484848", "emoji:42") is mock_response
            routes.REACTIONS.compile.assert_called_once_with(
                rest_impl.GET, channel_id="29292929", message_id="48484848", emoji="emoji:42"
            )
        rest_impl._request.assert_called_once_with(mock_route, query={})

    @pytest.mark.asyncio
    async def test_get_reactions_with_optionals(self, rest_impl):
        mock_response = [{"id": "42"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.REACTIONS)
        with mock.patch.object(routes, "REACTIONS", compile=mock.MagicMock(return_value=mock_route)):
            assert (
                await rest_impl.get_reactions("29292929", "48484848", "emoji:42", after="3333333", limit=40)
                is mock_response
            )
            routes.REACTIONS.compile.assert_called_once_with(
                rest_impl.GET, channel_id="29292929", message_id="48484848", emoji="emoji:42"
            )
        rest_impl._request.assert_called_once_with(mock_route, query={"after": "3333333", "limit": 40})

    @pytest.mark.asyncio
    async def test_delete_all_reactions(self, rest_impl):
        mock_route = mock.MagicMock(routes.ALL_REACTIONS)
        with mock.patch.object(routes, "ALL_REACTIONS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_all_reactions("44444", "999999") is None
            routes.ALL_REACTIONS.compile.assert_called_once_with(
                rest_impl.DELETE, channel_id="44444", message_id="999999"
            )
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_edit_message_without_optionals(self, rest_impl):
        mock_response = {"flags": 3, "content": "edited for the win."}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL_MESSAGE)
        with mock.patch.object(routes, "CHANNEL_MESSAGE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.edit_message("9292929", "484848") is mock_response
            routes.CHANNEL_MESSAGE.compile.assert_called_once_with(
                rest_impl.PATCH, channel_id="9292929", message_id="484848"
            )
        rest_impl._request.assert_called_once_with(mock_route, json_body={})

    @pytest.mark.asyncio
    async def test_edit_message_with_optionals(self, rest_impl):
        mock_response = {"flags": 3, "content": "edited for the win."}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL_MESSAGE)
        with mock.patch.object(routes, "CHANNEL_MESSAGE", compile=mock.MagicMock(return_value=mock_route)):
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
            routes.CHANNEL_MESSAGE.compile.assert_called_once_with(
                rest_impl.PATCH, channel_id="9292929", message_id="484848"
            )
        rest_impl._request.assert_called_once_with(
            mock_route,
            json_body={
                "content": "42",
                "embed": {"content": "I AM AN EMBED"},
                "flags": 2,
                "allowed_mentions": {"parse": ["everyone", "users"]},
            },
        )

    @pytest.mark.asyncio
    async def test_delete_message(self, rest_impl):
        mock_route = mock.MagicMock(routes.CHANNEL_MESSAGE)
        with mock.patch.object(routes, "CHANNEL_MESSAGE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_message("20202", "484848") is None
            routes.CHANNEL_MESSAGE.compile.assert_called_once_with(
                rest_impl.DELETE, channel_id="20202", message_id="484848"
            )
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_bulk_delete_messages(self, rest_impl):
        mock_route = mock.MagicMock(routes.CHANNEL_MESSAGES_BULK_DELETE)
        with mock.patch.object(routes, "CHANNEL_MESSAGES_BULK_DELETE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.bulk_delete_messages("111", ["222", "333"]) is None
            routes.CHANNEL_MESSAGES_BULK_DELETE.compile.assert_called_once_with(rest_impl.POST, channel_id="111")
        rest_impl._request.assert_called_once_with(mock_route, json_body={"messages": ["222", "333"]})

    @pytest.mark.asyncio
    async def test_edit_channel_permissions_without_optionals(self, rest_impl):
        mock_route = mock.MagicMock(routes.CHANNEL_PERMISSIONS)
        with mock.patch.object(routes, "CHANNEL_PERMISSIONS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.edit_channel_permissions("101010101010", "100101010", type_="user") is None
            routes.CHANNEL_PERMISSIONS.compile.assert_called_once_with(
                rest_impl.PATCH, channel_id="101010101010", overwrite_id="100101010"
            )
        rest_impl._request.assert_called_once_with(mock_route, json_body={"type": "user"}, reason=...)

    @pytest.mark.asyncio
    async def test_edit_channel_permissions_with_optionals(self, rest_impl):
        mock_route = mock.MagicMock(routes.CHANNEL_PERMISSIONS)
        with mock.patch.object(routes, "CHANNEL_PERMISSIONS", compile=mock.MagicMock(return_value=mock_route)):
            assert (
                await rest_impl.edit_channel_permissions(
                    "101010101010", "100101010", allow=243, deny=333, type_="user", reason="get vectored"
                )
                is None
            )
            routes.CHANNEL_PERMISSIONS.compile.assert_called_once_with(
                rest_impl.PATCH, channel_id="101010101010", overwrite_id="100101010"
            )
        rest_impl._request.assert_called_once_with(
            mock_route, json_body={"allow": 243, "deny": 333, "type": "user"}, reason="get vectored"
        )

    @pytest.mark.asyncio
    async def test_get_channel_invites(self, rest_impl):
        mock_response = {"code": "dasd32"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL_INVITES)
        with mock.patch.object(routes, "CHANNEL_INVITES", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_channel_invites("999999999") is mock_response
            routes.CHANNEL_INVITES.compile.assert_called_once_with(rest_impl.GET, channel_id="999999999")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_create_channel_invite_without_optionals(self, rest_impl):
        mock_response = {"code": "ro934jsd"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL_INVITES)
        with mock.patch.object(routes, "CHANNEL_INVITES", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.create_channel_invite("99992929") is mock_response
            routes.CHANNEL_INVITES.compile.assert_called_once_with(rest_impl.POST, channel_id="99992929")
        rest_impl._request.assert_called_once_with(mock_route, json_body={}, reason=...)

    @pytest.mark.asyncio
    async def test_create_channel_invite_with_optionals(self, rest_impl):
        mock_response = {"code": "ro934jsd"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL_INVITES)
        with mock.patch.object(routes, "CHANNEL_INVITES", compile=mock.MagicMock(return_value=mock_route)):
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
            routes.CHANNEL_INVITES.compile.assert_called_once_with(rest_impl.POST, channel_id="99992929")
        rest_impl._request.assert_called_once_with(
            mock_route,
            json_body={
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
        mock_route = mock.MagicMock(routes.CHANNEL_PERMISSIONS)
        with mock.patch.object(routes, "CHANNEL_PERMISSIONS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_channel_permission("9292929", "74574747") is None
            routes.CHANNEL_PERMISSIONS.compile.assert_called_once_with(
                rest_impl.DELETE, channel_id="9292929", overwrite_id="74574747"
            )
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_trigger_typing_indicator(self, rest_impl):
        mock_route = mock.MagicMock(routes.CHANNEL_TYPING)
        with mock.patch.object(routes, "CHANNEL_TYPING", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.trigger_typing_indicator("11111111111") is None
            routes.CHANNEL_TYPING.compile.assert_called_once_with(rest_impl.POST, channel_id="11111111111")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_pinned_messages(self, rest_impl):
        mock_response = [{"content": "no u", "id": "4212"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL_PINS)
        with mock.patch.object(routes, "CHANNEL_PINS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_pinned_messages("393939") is mock_response
            routes.CHANNEL_PINS.compile.assert_called_once_with(rest_impl.GET, channel_id="393939")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_add_pinned_channel_message(self, rest_impl):
        mock_route = mock.MagicMock(routes.CHANNEL_PIN)
        with mock.patch.object(routes, "CHANNEL_PINS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.add_pinned_channel_message("292929", "48458484") is None
            routes.CHANNEL_PINS.compile.assert_called_once_with(
                rest_impl.PUT, channel_id="292929", message_id="48458484"
            )
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_delete_pinned_channel_message(self, rest_impl):
        mock_route = mock.MagicMock(routes.CHANNEL_PIN)
        with mock.patch.object(routes, "CHANNEL_PIN", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_pinned_channel_message("929292", "292929") is None
            routes.CHANNEL_PIN.compile.assert_called_once_with(
                rest_impl.DELETE, channel_id="929292", message_id="292929"
            )
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_list_guild_emojis(self, rest_impl):
        mock_response = [{"id": "444", "name": "nekonyan"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_EMOJIS)
        with mock.patch.object(routes, "GUILD_EMOJIS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.list_guild_emojis("9929292") is mock_response
            routes.GUILD_EMOJIS.compile.assert_called_once_with(rest_impl.GET, guild_id="9929292")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_guild_emoji(self, rest_impl):
        mock_response = {"id": "444", "name": "nekonyan"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_EMOJI)
        with mock.patch.object(routes, "GUILD_EMOJI", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_guild_emoji("292929", "44848") is mock_response
            routes.GUILD_EMOJI.compile.assert_called_once_with(rest_impl.GET, guild_id="292929", emoji_id="44848")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_create_guild_emoji_without_optionals(self, rest_impl):
        mock_response = {"id": "33", "name": "OwO"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_EMOJI)
        mock_image_data = "data:image/png;base64,iVBORw0KGgpibGFo"
        with mock.patch.object(routes, "GUILD_EMOJIS", compile=mock.MagicMock(return_value=mock_route)):
            with mock.patch.object(conversions, "image_bytes_to_image_data", return_value=mock_image_data):
                result = await rest_impl.create_guild_emoji("2222", "iEmoji", b"\211PNG\r\n\032\nblah")
                assert result is mock_response
                conversions.image_bytes_to_image_data.assert_called_once_with(b"\211PNG\r\n\032\nblah")
                routes.GUILD_EMOJIS.compile.assert_called_once_with(rest_impl.POST, guild_id="2222")
        rest_impl._request.assert_called_once_with(
            mock_route, json_body={"name": "iEmoji", "roles": [], "image": mock_image_data}, reason=...,
        )

    @pytest.mark.asyncio
    async def test_create_guild_emoji_with_optionals(self, rest_impl):
        mock_response = {"id": "33", "name": "OwO"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_EMOJI)
        mock_image_data = "data:image/png;base64,iVBORw0KGgpibGFo"
        with mock.patch.object(routes, "GUILD_EMOJIS", compile=mock.MagicMock(return_value=mock_route)):
            with mock.patch.object(conversions, "image_bytes_to_image_data", return_value=mock_image_data):
                result = await rest_impl.create_guild_emoji(
                    "2222", "iEmoji", b"\211PNG\r\n\032\nblah", roles=["292929", "484884"], reason="uwu owo"
                )
                assert result is mock_response
                conversions.image_bytes_to_image_data.assert_called_once_with(b"\211PNG\r\n\032\nblah")
                routes.GUILD_EMOJIS.compile.assert_called_once_with(rest_impl.POST, guild_id="2222")
        rest_impl._request.assert_called_once_with(
            mock_route,
            json_body={"name": "iEmoji", "roles": ["292929", "484884"], "image": mock_image_data},
            reason="uwu owo",
        )

    @pytest.mark.asyncio
    async def test_modify_guild_emoji_without_optionals(self, rest_impl):
        mock_response = {"id": "20202", "name": "jeje"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_EMOJI)
        with mock.patch.object(routes, "GUILD_EMOJI", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.modify_guild_emoji("292929", "3484848") is mock_response
            routes.GUILD_EMOJI.compile.assert_called_once_with(rest_impl.PATCH, guild_id="292929", emoji_id="3484848")
        rest_impl._request.assert_called_once_with(mock_route, json_body={}, reason=...)

    @pytest.mark.asyncio
    async def test_modify_guild_emoji_with_optionals(self, rest_impl):
        mock_response = {"id": "20202", "name": "jeje"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_EMOJI)
        with mock.patch.object(routes, "GUILD_EMOJI", compile=mock.MagicMock(return_value=mock_route)):
            assert (
                await rest_impl.modify_guild_emoji("292929", "3484848", name="ok", roles=["222", "111"])
                is mock_response
            )
            routes.GUILD_EMOJI.compile.assert_called_once_with(rest_impl.PATCH, guild_id="292929", emoji_id="3484848")
        rest_impl._request.assert_called_once_with(
            mock_route, json_body={"name": "ok", "roles": ["222", "111"]}, reason=...
        )

    @pytest.mark.asyncio
    async def test_delete_guild_emoji(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_EMOJI)
        with mock.patch.object(routes, "GUILD_EMOJI", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_guild_emoji("202", "4454") is None
            routes.GUILD_EMOJI.compile.assert_called_once_with(rest_impl.DELETE, guild_id="202", emoji_id="4454")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_create_guild_without_optionals(self, rest_impl):
        mock_response = {"id": "99999", "name": "Guildith-Sama"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD)
        with mock.patch.object(routes, "GUILDS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.create_guild("GUILD TIME") is mock_response
            routes.GUILDS.compile.assert_called_once_with(rest_impl.POST)
        rest_impl._request.assert_called_once_with(mock_route, json_body={"name": "GUILD TIME"})

    @pytest.mark.asyncio
    async def test_create_guild_with_optionals(self, rest_impl):
        mock_response = {"id": "99999", "name": "Guildith-Sama"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD)
        mock_image_data = "data:image/png;base64,iVBORw0KGgpibGFo"
        with mock.patch.object(routes, "GUILDS", compile=mock.MagicMock(return_value=mock_route)):
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
                routes.GUILDS.compile.assert_called_once_with(rest_impl.POST)
                conversions.image_bytes_to_image_data.assert_called_once_with(b"\211PNG\r\n\032\nblah")
        rest_impl._request.assert_called_once_with(
            mock_route,
            json_body={
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
    async def test_get_guild(self, rest_impl):
        mock_response = {"id": "42", "name": "Hikari"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD)
        with mock.patch.object(routes, "GUILD", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_guild("3939393993939") is mock_response
            routes.GUILD.compile.assert_called_once_with(rest_impl.GET, guild_id="3939393993939")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_modify_guild_without_optionals(self, rest_impl):
        mock_response = {"id": "42", "name": "Hikari"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD)
        with mock.patch.object(routes, "GUILD", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.modify_guild("49949495") is mock_response
            routes.GUILD.compile.assert_called_once_with(rest_impl.PATCH, guild_id="49949495")
        rest_impl._request.assert_called_once_with(mock_route, json_body={}, reason=...)

    @pytest.mark.asyncio
    async def test_modify_guild_with_optionals(self, rest_impl):
        mock_response = {"id": "42", "name": "Hikari"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD)
        mock_icon_data = "data:image/png;base64,iVBORw0KGgpibGFo"
        mock_splash_data = "data:image/png;base64,iVBORw0KGgpicnVo"
        with mock.patch.object(routes, "GUILD", compile=mock.MagicMock(return_value=mock_route)):
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

                routes.GUILD.compile.assert_called_once_with(rest_impl.PATCH, guild_id="49949495")
                assert conversions.image_bytes_to_image_data.call_count == 2
                conversions.image_bytes_to_image_data.assert_has_calls(
                    (
                        mock.call.__bool__(),
                        mock.call(b"\211PNG\r\n\032\nblah"),
                        mock.call.__bool__(),
                        mock.call(b"\211PNG\r\n\032\nbruh"),
                    )
                )
        rest_impl._request.assert_called_once_with(
            mock_route,
            json_body={
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
        mock_route = mock.MagicMock(routes.GUILD)
        with mock.patch.object(routes, "GUILD", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_guild("92847478") is None
            routes.GUILD.compile.assert_called_once_with(rest_impl.DELETE, guild_id="92847478")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_guild_channels(self, rest_impl):
        mock_response = [{"type": 2, "id": "21", "name": "Watashi-wa-channel-desu"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_CHANNELS)
        with mock.patch.object(routes, "GUILD_CHANNELS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.list_guild_channels("393939393") is mock_response
            routes.GUILD_CHANNELS.compile.assert_called_once_with(rest_impl.GET, guild_id="393939393")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_create_guild_channel_without_optionals(self, rest_impl):
        mock_response = {"type": 2, "id": "3333"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_CHANNELS)
        with mock.patch.object(routes, "GUILD_CHANNELS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.create_guild_channel("292929", "I am a channel") is mock_response
            routes.GUILD_CHANNELS.compile.assert_called_once_with(rest_impl.POST, guild_id="292929")
        rest_impl._request.assert_called_once_with(mock_route, json_body={"name": "I am a channel"}, reason=...)

    @pytest.mark.asyncio
    async def test_create_guild_channel_with_optionals(self, rest_impl):
        mock_response = {"type": 2, "id": "379953393319542784"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_CHANNELS)
        with mock.patch.object(routes, "GUILD_CHANNELS", compile=mock.MagicMock(return_value=mock_route)):
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

            routes.GUILD_CHANNELS.compile.assert_called_once_with(rest_impl.POST, guild_id="292929")
        rest_impl._request.assert_called_once_with(
            mock_route,
            json_body={
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
        mock_route = mock.MagicMock(routes.GUILD_CHANNELS)
        with mock.patch.object(routes, "GUILD_CHANNELS", compile=mock.MagicMock(return_value=mock_route)):
            assert (
                await rest_impl.modify_guild_channel_positions("379953393319542784", ("29292", 0), ("3838", 1)) is None
            )
            routes.GUILD_CHANNELS.compile.assert_called_once_with(rest_impl.PATCH, guild_id="379953393319542784")
        rest_impl._request.assert_called_once_with(
            mock_route, json_body=[{"id": "29292", "position": 0}, {"id": "3838", "position": 1}]
        )

    @pytest.mark.asyncio
    async def test_get_guild_member(self, rest_impl):
        mock_response = {"id": "379953393319542784", "nick": "Big Moh"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_MEMBER)
        with mock.patch.object(routes, "GUILD_MEMBER", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_guild_member("115590097100865541", "379953393319542784") is mock_response
            routes.GUILD_MEMBER.compile.assert_called_once_with(
                rest_impl.GET, guild_id="115590097100865541", user_id="379953393319542784"
            )
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_list_guild_members_without_optionals(self, rest_impl):
        mock_response = [{"id": "379953393319542784", "nick": "Big Moh"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_MEMBERS)
        with mock.patch.object(routes, "GUILD_MEMBERS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.list_guild_members("115590097100865541") is mock_response
            routes.GUILD_MEMBERS.compile.assert_called_once_with(rest_impl.GET, guild_id="115590097100865541")
        rest_impl._request.assert_called_once_with(mock_route, query={})

    @pytest.mark.asyncio
    async def test_list_guild_members_with_optionals(self, rest_impl):
        mock_response = [{"id": "379953393319542784", "nick": "Big Moh"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_MEMBERS)
        with mock.patch.object(routes, "GUILD_MEMBERS", compile=mock.MagicMock(return_value=mock_route)):
            assert (
                await rest_impl.list_guild_members("115590097100865541", limit=5, after="4444444444") is mock_response
            )
            routes.GUILD_MEMBERS.compile.assert_called_once_with(rest_impl.GET, guild_id="115590097100865541")
        rest_impl._request.assert_called_once_with(mock_route, query={"limit": 5, "after": "4444444444"})

    @pytest.mark.asyncio
    async def test_modify_guild_member_without_optionals(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_MEMBER)
        with mock.patch.object(routes, "GUILD_MEMBER", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.modify_guild_member("115590097100865541", "379953393319542784") is None
            routes.GUILD_MEMBER.compile.assert_called_once_with(
                rest_impl.PATCH, guild_id="115590097100865541", user_id="379953393319542784"
            )
        rest_impl._request.assert_called_once_with(mock_route, json_body={}, reason=...)

    @pytest.mark.asyncio
    async def test_modify_guild_member_with_optionals(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_MEMBER)
        with mock.patch.object(routes, "GUILD_MEMBER", compile=mock.MagicMock(return_value=mock_route)):
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

            routes.GUILD_MEMBER.compile.assert_called_once_with(
                rest_impl.PATCH, guild_id="115590097100865541", user_id="379953393319542784"
            )
        rest_impl._request.assert_called_once_with(
            mock_route,
            json_body={"nick": "QT", "roles": ["222222222"], "mute": True, "deaf": True, "channel_id": "777"},
            reason="I will drink your blood.",
        )

    @pytest.mark.asyncio
    async def test_modify_current_user_nick_without_reason(self, rest_impl):
        mock_route = mock.MagicMock(routes.OWN_GUILD_NICKNAME)
        with mock.patch.object(routes, "OWN_GUILD_NICKNAME", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.modify_current_user_nick("202020202", "Nickname me") is None
            routes.OWN_GUILD_NICKNAME.compile.assert_called_once_with(rest_impl.PATCH, guild_id="202020202")
        rest_impl._request.assert_called_once_with(mock_route, json_body={"nick": "Nickname me"}, reason=...)

    @pytest.mark.asyncio
    async def test_modify_current_user_nick_with_reason(self, rest_impl):
        mock_route = mock.MagicMock(routes.OWN_GUILD_NICKNAME)
        with mock.patch.object(routes, "OWN_GUILD_NICKNAME", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.modify_current_user_nick("202020202", "Nickname me", reason="Look at me") is None
            routes.OWN_GUILD_NICKNAME.compile.assert_called_once_with(rest_impl.PATCH, guild_id="202020202")
        rest_impl._request.assert_called_once_with(mock_route, json_body={"nick": "Nickname me"}, reason="Look at me")

    @pytest.mark.asyncio
    async def test_add_guild_member_role_without_reason(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_MEMBER_ROLE)
        with mock.patch.object(routes, "GUILD_MEMBER_ROLE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.add_guild_member_role("3939393", "2838383", "84384848") is None
            routes.GUILD_MEMBER_ROLE.compile.assert_called_once_with(
                rest_impl.PUT, guild_id="3939393", user_id="2838383", role_id="84384848"
            )
        rest_impl._request.assert_called_once_with(mock_route, reason=...)

    @pytest.mark.asyncio
    async def test_add_guild_member_role_with_reason(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_MEMBER_ROLE)
        with mock.patch.object(routes, "GUILD_MEMBER_ROLE", compile=mock.MagicMock(return_value=mock_route)):
            assert (
                await rest_impl.add_guild_member_role(
                    "3939393", "2838383", "84384848", reason="A special role for a special somebody"
                )
                is None
            )
            routes.GUILD_MEMBER_ROLE.compile.assert_called_once_with(
                rest_impl.PUT, guild_id="3939393", user_id="2838383", role_id="84384848"
            )
        rest_impl._request.assert_called_once_with(mock_route, reason="A special role for a special somebody")

    @pytest.mark.asyncio
    async def test_remove_guild_member_role_without_reason(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_MEMBER_ROLE)
        with mock.patch.object(routes, "GUILD_MEMBER_ROLE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.remove_guild_member_role("22222", "3333", "44444") is None
            routes.GUILD_MEMBER_ROLE.compile.assert_called_once_with(
                rest_impl.DELETE, guild_id="22222", user_id="3333", role_id="44444"
            )
        rest_impl._request.assert_called_once_with(mock_route, reason=...)

    @pytest.mark.asyncio
    async def test_remove_guild_member_role_with_reason(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_MEMBER_ROLE)
        with mock.patch.object(routes, "GUILD_MEMBER_ROLE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.remove_guild_member_role("22222", "3333", "44444", reason="bye") is None
            routes.GUILD_MEMBER_ROLE.compile.assert_called_once_with(
                rest_impl.DELETE, guild_id="22222", user_id="3333", role_id="44444"
            )
        rest_impl._request.assert_called_once_with(mock_route, reason="bye")

    @pytest.mark.asyncio
    async def test_remove_guild_member_without_reason(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_MEMBER)
        with mock.patch.object(routes, "GUILD_MEMBER", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.remove_guild_member("393939", "82828") is None
            routes.GUILD_MEMBER.compile.assert_called_once_with(rest_impl.DELETE, guild_id="393939", user_id="82828")
        rest_impl._request.assert_called_once_with(mock_route, reason=...)

    @pytest.mark.asyncio
    async def test_remove_guild_member_with_reason(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_MEMBER)
        with mock.patch.object(routes, "GUILD_MEMBER", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.remove_guild_member("393939", "82828", reason="super bye") is None
            routes.GUILD_MEMBER.compile.assert_called_once_with(rest_impl.DELETE, guild_id="393939", user_id="82828")
        rest_impl._request.assert_called_once_with(mock_route, reason="super bye")

    @pytest.mark.asyncio
    async def test_get_guild_bans(self, rest_impl):
        mock_response = [{"id": "3939393"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_BANS)
        with mock.patch.object(routes, "GUILD_BANS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_guild_bans("292929") is mock_response
            routes.GUILD_BANS.compile.assert_called_once_with(rest_impl.GET, guild_id="292929")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_guild_ban(self, rest_impl):
        mock_response = {"id": "3939393"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_BAN)
        with mock.patch.object(routes, "GUILD_BAN", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_guild_ban("92929", "44848") is mock_response
            routes.GUILD_BAN.compile.assert_called_once_with(rest_impl.GET, guild_id="92929", user_id="44848")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_create_guild_ban_without_optionals(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_BAN)
        with mock.patch.object(routes, "GUILD_BAN", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.create_guild_ban("222", "444") is None
            routes.GUILD_BAN.compile.assert_called_once_with(rest_impl.PUT, guild_id="222", user_id="444")
        rest_impl._request.assert_called_once_with(mock_route, query={})

    @pytest.mark.asyncio
    async def test_create_guild_ban_with_optionals(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_BAN)
        with mock.patch.object(routes, "GUILD_BAN", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.create_guild_ban("222", "444", delete_message_days=5, reason="TRUE") is None
            routes.GUILD_BAN.compile.assert_called_once_with(rest_impl.PUT, guild_id="222", user_id="444")
        rest_impl._request.assert_called_once_with(mock_route, query={"delete-message-days": 5, "reason": "TRUE"})

    @pytest.mark.asyncio
    async def test_remove_guild_ban_without_reason(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_BAN)
        with mock.patch.object(routes, "GUILD_BAN", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.remove_guild_ban("494949", "3737") is None
            routes.GUILD_BAN.compile.assert_called_once_with(rest_impl.DELETE, guild_id="494949", user_id="3737")
        rest_impl._request.assert_called_once_with(mock_route, reason=...)

    @pytest.mark.asyncio
    async def test_remove_guild_ban_with_reason(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_BAN)
        with mock.patch.object(routes, "GUILD_BAN", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.remove_guild_ban("494949", "3737", reason="LMFAO") is None
            routes.GUILD_BAN.compile.assert_called_once_with(rest_impl.DELETE, guild_id="494949", user_id="3737")
        rest_impl._request.assert_called_once_with(mock_route, reason="LMFAO")

    @pytest.mark.asyncio
    async def test_get_guild_roles(self, rest_impl):
        mock_response = [{"name": "role", "id": "4949494994"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_ROLES)
        with mock.patch.object(routes, "GUILD_ROLES", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_guild_roles("909") is mock_response
            routes.GUILD_ROLES.compile.assert_called_once_with(rest_impl.GET, guild_id="909")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_create_guild_role_without_optionals(self, rest_impl):
        mock_response = {"id": "42"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_ROLES)
        with mock.patch.object(routes, "GUILD_ROLES", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.create_guild_role("9494") is mock_response
            routes.GUILD_ROLES.compile.assert_called_once_with(rest_impl.POST, guild_id="9494")
        rest_impl._request.assert_called_once_with(mock_route, json_body={}, reason=...)

    @pytest.mark.asyncio
    async def test_create_guild_role_with_optionals(self, rest_impl):
        mock_response = {"id": "42"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_ROLES)
        with mock.patch.object(routes, "GUILD_ROLES", compile=mock.MagicMock(return_value=mock_route)):
            assert (
                await rest_impl.create_guild_role(
                    "9494", name="role sama", permissions=22, color=12, hoist=True, mentionable=True, reason="eat dirt"
                )
                is mock_response
            )
            routes.GUILD_ROLES.compile.assert_called_once_with(rest_impl.POST, guild_id="9494")
        rest_impl._request.assert_called_once_with(
            mock_route,
            json_body={"name": "role sama", "permissions": 22, "color": 12, "hoist": True, "mentionable": True,},
            reason="eat dirt",
        )

    @pytest.mark.asyncio
    async def test_modify_guild_role_positions(self, rest_impl):
        mock_response = [{"id": "444", "position": 0}, {"id": "999", "position": 1}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_ROLES)
        with mock.patch.object(routes, "GUILD_ROLES", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.modify_guild_role_positions("292929", ("444", 0), ("999", 1)) is mock_response
            routes.GUILD_ROLES.compile.assert_called_once_with(rest_impl.PATCH, guild_id="292929")
        rest_impl._request.assert_called_once_with(
            mock_route, json_body=[{"id": "444", "position": 0}, {"id": "999", "position": 1}]
        )

    @pytest.mark.asyncio
    async def test_modify_guild_role_with_optionals(self, rest_impl):
        mock_response = {"id": "54234", "name": "roleio roleio"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_ROLE)
        with mock.patch.object(routes, "GUILD_ROLE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.modify_guild_role("999999", "54234") is mock_response
            routes.GUILD_ROLE.compile.assert_called_once_with(rest_impl.PATCH, guild_id="999999", role_id="54234")
        rest_impl._request.assert_called_once_with(mock_route, json_body={}, reason=...)

    @pytest.mark.asyncio
    async def test_modify_guild_role_without_optionals(self, rest_impl):
        mock_response = {"id": "54234", "name": "roleio roleio"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_ROLE)
        with mock.patch.object(routes, "GUILD_ROLE", compile=mock.MagicMock(return_value=mock_route)):
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
            routes.GUILD_ROLE.compile.assert_called_once_with(rest_impl.PATCH, guild_id="999999", role_id="54234")
        rest_impl._request.assert_called_once_with(
            mock_route,
            json_body={"name": "HAHA", "permissions": 42, "color": 69, "hoist": True, "mentionable": False,},
            reason="You are a pirate.",
        )

    @pytest.mark.asyncio
    async def test_delete_guild_role(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_ROLE)
        with mock.patch.object(routes, "GUILD_ROLE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_guild_role("29292", "4848") is None
            routes.GUILD_ROLE.compile.assert_called_once_with(rest_impl.DELETE, guild_id="29292", role_id="4848")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_guild_prune_count(self, rest_impl):
        mock_response = {"pruned": 7}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_PRUNE)
        with mock.patch.object(routes, "GUILD_PRUNE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_guild_prune_count("29292", 14) == 7
            routes.GUILD_PRUNE.compile.assert_called_once_with(rest_impl.GET, guild_id="29292")
        rest_impl._request.assert_called_once_with(mock_route, query={"days": 14})

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mock_response", ({"pruned": None}, {}))
    async def test_begin_guild_prune_without_optionals_returns_none(self, rest_impl, mock_response):
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_PRUNE)
        with mock.patch.object(routes, "GUILD_PRUNE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.begin_guild_prune("39393", 14) is None
        rest_impl._request.assert_called_once_with(mock_route, query={"days": 14}, reason=...)

    @pytest.mark.asyncio
    async def test_begin_guild_prune_with_optionals(self, rest_impl):
        rest_impl._request.return_value = {"pruned": 32}
        mock_route = mock.MagicMock(routes.GUILD_PRUNE)
        with mock.patch.object(routes, "GUILD_PRUNE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.begin_guild_prune("39393", 14, compute_prune_count=True, reason="BYEBYE") == 32
        rest_impl._request.assert_called_once_with(
            mock_route, query={"days": 14, "compute_prune_count": "True"}, reason="BYEBYE"
        )

    @pytest.mark.asyncio
    async def test_get_guild_voice_regions(self, rest_impl):
        mock_response = [{"name": "london", "vip": True}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_VOICE_REGIONS)
        with mock.patch.object(routes, "GUILD_VOICE_REGIONS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_guild_voice_regions("2393939") is mock_response
            routes.GUILD_VOICE_REGIONS.compile.assert_called_once_with(rest_impl.GET, guild_id="2393939")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_guild_invites(self, rest_impl):
        mock_response = [{"code": "ewkkww"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_INVITES)
        with mock.patch.object(routes, "GUILD_INVITES", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_guild_invites("9292929") is mock_response
            routes.GUILD_INVITES.compile.assert_called_once_with(rest_impl.GET, guild_id="9292929")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_guild_integrations(self, rest_impl):
        mock_response = [{"id": "4242"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_INTEGRATIONS)
        with mock.patch.object(routes, "GUILD_INTEGRATIONS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_guild_integrations("537340989808050216") is mock_response
            routes.GUILD_INTEGRATIONS.compile.assert_called_once_with(rest_impl.GET, guild_id="537340989808050216")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_modify_guild_integration_without_optionals(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_INTEGRATION)
        with mock.patch.object(routes, "GUILD_INTEGRATION", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.modify_guild_integration("292929", "747474") is None
            routes.GUILD_INTEGRATION.compile.assert_called_once_with(
                rest_impl.PATCH, guild_id="292929", integration_id="747474"
            )
        rest_impl._request.assert_called_once_with(mock_route, json_body={}, reason=...)

    @pytest.mark.asyncio
    async def test_modify_guild_integration_with_optionals(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_INTEGRATION)
        with mock.patch.object(routes, "GUILD_INTEGRATION", compile=mock.MagicMock(return_value=mock_route)):
            result = await rest_impl.modify_guild_integration(
                "292929",
                "747474",
                expire_behaviour=2,
                expire_grace_period=1,
                enable_emojis=True,
                reason="This password is already taken by {redacted}",
            )
            assert result is None

            routes.GUILD_INTEGRATION.compile.assert_called_once_with(
                rest_impl.PATCH, guild_id="292929", integration_id="747474"
            )
        rest_impl._request.assert_called_once_with(
            mock_route,
            json_body={"expire_behaviour": 2, "expire_grace_period": 1, "enable_emoticons": True},
            reason="This password is already taken by {redacted}",
        )

    @pytest.mark.asyncio
    async def test_delete_guild_integration_without_reason(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_INTEGRATION)
        with mock.patch.object(routes, "GUILD_INTEGRATION", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_guild_integration("23992", "7474") is None
            routes.GUILD_INTEGRATION.compile.assert_called_once_with(
                rest_impl.DELETE, guild_id="23992", integration_id="7474"
            )
        rest_impl._request.assert_called_once_with(mock_route, reason=...)

    @pytest.mark.asyncio
    async def test_delete_guild_integration_with_reason(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_INTEGRATION)
        with mock.patch.object(routes, "GUILD_INTEGRATION", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_guild_integration("23992", "7474", reason="HOT") is None
            routes.GUILD_INTEGRATION.compile.assert_called_once_with(
                rest_impl.DELETE, guild_id="23992", integration_id="7474"
            )
        rest_impl._request.assert_called_once_with(mock_route, reason="HOT")

    @pytest.mark.asyncio
    async def test_sync_guild_integration(self, rest_impl):
        mock_route = mock.MagicMock(routes.GUILD_INTEGRATION_SYNC)
        with mock.patch.object(routes, "GUILD_INTEGRATION_SYNC", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.sync_guild_integration("3939439", "84884") is None
            routes.GUILD_INTEGRATION_SYNC.compile.assert_called_once_with(
                rest_impl.POST, guild_id="3939439", integration_id="84884"
            )
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_guild_embed(self, rest_impl):
        mock_response = {"channel_id": "4304040", "enabled": True}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_EMBED)
        with mock.patch.object(routes, "GUILD_EMBED", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_guild_embed("4949") is mock_response
            routes.GUILD_EMBED.compile.assert_called_once_with(rest_impl.GET, guild_id="4949")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_modify_guild_embed_without_reason(self, rest_impl):
        mock_response = {"channel_id": "4444", "enabled": False}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_EMBED)
        with mock.patch.object(routes, "GUILD_EMBED", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.modify_guild_embed("393939", channel_id="222", enabled=True) is mock_response
            routes.GUILD_EMBED.compile.assert_called_once_with(rest_impl.PATCH, guild_id="393939")
        rest_impl._request.assert_called_once_with(
            mock_route, json_body={"channel_id": "222", "enabled": True}, reason=...
        )

    @pytest.mark.asyncio
    async def test_modify_guild_embed_with_reason(self, rest_impl):
        mock_response = {"channel_id": "4444", "enabled": False}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_EMBED)
        with mock.patch.object(routes, "GUILD_EMBED", compile=mock.MagicMock(return_value=mock_route)):
            assert (
                await rest_impl.modify_guild_embed("393939", channel_id="222", enabled=True, reason="OK")
                is mock_response
            )
            routes.GUILD_EMBED.compile.assert_called_once_with(rest_impl.PATCH, guild_id="393939")
        rest_impl._request.assert_called_once_with(
            mock_route, json_body={"channel_id": "222", "enabled": True}, reason="OK"
        )

    @pytest.mark.asyncio
    async def test_get_guild_vanity_url(self, rest_impl):
        mock_response = {"code": "dsidid"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_VANITY_URL)
        with mock.patch.object(routes, "GUILD_VANITY_URL", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_guild_vanity_url("399393") is mock_response
            routes.GUILD_VANITY_URL.compile.assert_called_once_with(rest_impl.GET, guild_id="399393")
        rest_impl._request.assert_called_once_with(mock_route)

    def test_get_guild_widget_image_url_without_style(self, rest_impl):
        url = rest_impl.get_guild_widget_image_url("54949")
        assert url == "https://discordapp.com/api/v6/guilds/54949/widget.png"

    def test_get_guild_widget_image_url_with_style(self, rest_impl):
        url = rest_impl.get_guild_widget_image_url("54949", style="banner2")
        assert url == "https://discordapp.com/api/v6/guilds/54949/widget.png?style=banner2"

    @pytest.mark.asyncio
    async def test_get_invite_without_counts(self, rest_impl):
        mock_response = {"code": "fesdfes"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.INVITE)
        with mock.patch.object(routes, "INVITE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_invite("fesdfes") is mock_response
            routes.INVITE.compile.assert_called_once_with(rest_impl.GET, invite_code="fesdfes")
        rest_impl._request.assert_called_once_with(mock_route, query={})

    @pytest.mark.asyncio
    async def test_get_invite_with_counts(self, rest_impl):
        mock_response = {"code": "fesdfes"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.INVITE)
        with mock.patch.object(routes, "INVITE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_invite("fesdfes", with_counts=True) is mock_response
            routes.INVITE.compile.assert_called_once_with(rest_impl.GET, invite_code="fesdfes")
        rest_impl._request.assert_called_once_with(mock_route, query={"with_counts": "True"})

    @pytest.mark.asyncio
    async def test_delete_invite(self, rest_impl):
        mock_response = {"code": "diidsk"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.INVITE)
        with mock.patch.object(routes, "INVITE", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_invite("diidsk") is mock_response
            routes.INVITE.compile.assert_called_once_with(rest_impl.DELETE, invite_code="diidsk")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_current_application_info(self, rest_impl):
        mock_response = {"bot_public": True}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.OAUTH2_APPLICATIONS_ME)
        with mock.patch.object(routes, "OAUTH2_APPLICATIONS_ME", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_current_application_info() is mock_response
            routes.OAUTH2_APPLICATIONS_ME.compile.assert_called_once_with(rest_impl.GET)
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_current_user(self, rest_impl):
        mock_response = {"id": "494949", "username": "A name"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.OWN_USER)
        with mock.patch.object(routes, "OWN_USER", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_current_user() is mock_response
            routes.OWN_USER.compile.assert_called_once_with(rest_impl.GET)
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_user(self, rest_impl):
        mock_response = {"id": "54959"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.USER)
        with mock.patch.object(routes, "USER", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_user("54959") is mock_response
            routes.USER.compile.assert_called_once_with(rest_impl.GET, user_id="54959")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_modify_current_user_without_optionals(self, rest_impl):
        mock_response = {"id": "44444", "username": "Watashi"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.OWN_USER)
        with mock.patch.object(routes, "OWN_USER", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.modify_current_user() is mock_response
            routes.OWN_USER.compile.assert_called_once_with(rest_impl.PATCH)
        rest_impl._request.assert_called_once_with(mock_route, json_body={})

    @pytest.mark.asyncio
    async def test_modify_current_user_with_optionals(self, rest_impl):
        mock_response = {"id": "44444", "username": "Watashi"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.OWN_USER)
        mock_image_data = "data:image/png;base64,iVBORw0KGgpibGFo"
        with mock.patch.object(routes, "OWN_USER", compile=mock.MagicMock(return_value=mock_route)):
            with mock.patch.object(conversions, "image_bytes_to_image_data", return_value=mock_image_data):
                result = await rest_impl.modify_current_user(username="Watashi 2", avatar=b"\211PNG\r\n\032\nblah")
                assert result is mock_response
                routes.OWN_USER.compile.assert_called_once_with(rest_impl.PATCH)
                conversions.image_bytes_to_image_data.assert_called_once_with(b"\211PNG\r\n\032\nblah")
        rest_impl._request.assert_called_once_with(
            mock_route, json_body={"username": "Watashi 2", "avatar": mock_image_data}
        )

    @pytest.mark.asyncio
    async def test_get_current_user_connections(self, rest_impl):
        mock_response = [{"id": "fspeed", "revoked": False}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.OWN_CONNECTIONS)
        with mock.patch.object(routes, "OWN_CONNECTIONS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_current_user_connections() is mock_response
            routes.OWN_CONNECTIONS.compile.assert_called_once_with(rest_impl.GET)
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_current_user_guilds_without_optionals(self, rest_impl):
        mock_response = [{"id": "452", "owner_id": "4949"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.OWN_GUILDS)
        with mock.patch.object(routes, "OWN_GUILDS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_current_user_guilds() is mock_response
            routes.OWN_GUILDS.compile.assert_called_once_with(rest_impl.GET)
        rest_impl._request.assert_called_once_with(mock_route, query={})

    @pytest.mark.asyncio
    async def test_get_current_user_guilds_with_optionals(self, rest_impl):
        mock_response = [{"id": "452", "owner_id": "4949"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.OWN_GUILDS)
        with mock.patch.object(routes, "OWN_GUILDS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_current_user_guilds(before="292929", after="22288", limit=5) is mock_response
            routes.OWN_GUILDS.compile.assert_called_once_with(rest_impl.GET)
        rest_impl._request.assert_called_once_with(mock_route, query={"before": "292929", "after": "22288", "limit": 5})

    @pytest.mark.asyncio
    async def test_leave_guild(self, rest_impl):
        mock_route = mock.MagicMock(routes.LEAVE_GUILD)
        with mock.patch.object(routes, "LEAVE_GUILD", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.leave_guild("292929") is None
            routes.LEAVE_GUILD.compile.assert_called_once_with(rest_impl.DELETE, guild_id="292929")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_create_dm(self, rest_impl):
        mock_response = {"id": "404040", "recipients": []}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.OWN_DMS)
        with mock.patch.object(routes, "OWN_DMS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.create_dm("409491291156774923") is mock_response
            routes.OWN_DMS.compile.assert_called_once_with(rest_impl.POST)
        rest_impl._request.assert_called_once_with(mock_route, json_body={"recipient_id": "409491291156774923"})

    @pytest.mark.asyncio
    async def test_list_voice_regions(self, rest_impl):
        mock_response = [{"name": "neko-cafe"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.VOICE_REGIONS)
        with mock.patch.object(routes, "VOICE_REGIONS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.list_voice_regions() is mock_response
            routes.VOICE_REGIONS.compile.assert_called_once_with(rest_impl.GET)
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_create_webhook_without_optionals(self, rest_impl):
        mock_response = {"channel_id": "39393993", "id": "8383838"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL_WEBHOOKS)
        with mock.patch.object(routes, "CHANNEL_WEBHOOKS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.create_webhook("39393939", "I am a webhook") is mock_response
            routes.CHANNEL_WEBHOOKS.compile.assert_called_once_with(rest_impl.POST, channel_id="39393939")
        rest_impl._request.assert_called_once_with(mock_route, json_body={"name": "I am a webhook"}, reason=...)

    @pytest.mark.asyncio
    async def test_create_webhook_with_optionals(self, rest_impl):
        mock_response = {"channel_id": "39393993", "id": "8383838"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL_WEBHOOKS)
        mock_image_data = "data:image/png;base64,iVBORw0KGgpibGFo"
        with mock.patch.object(routes, "CHANNEL_WEBHOOKS", compile=mock.MagicMock(return_value=mock_route)):
            with mock.patch.object(conversions, "image_bytes_to_image_data", return_value=mock_image_data):
                result = await rest_impl.create_webhook(
                    "39393939", "I am a webhook", avatar=b"\211PNG\r\n\032\nblah", reason="get reasoned"
                )
                assert result is mock_response
                routes.CHANNEL_WEBHOOKS.compile.assert_called_once_with(rest_impl.POST, channel_id="39393939")
                conversions.image_bytes_to_image_data.assert_called_once_with(b"\211PNG\r\n\032\nblah")
        rest_impl._request.assert_called_once_with(
            mock_route, json_body={"name": "I am a webhook", "avatar": mock_image_data}, reason="get reasoned",
        )

    @pytest.mark.asyncio
    async def test_get_channel_webhooks(self, rest_impl):
        mock_response = [{"channel_id": "39393993", "id": "8383838"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.CHANNEL_WEBHOOKS)
        with mock.patch.object(routes, "CHANNEL_WEBHOOKS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_channel_webhooks("9393939") is mock_response
            routes.CHANNEL_WEBHOOKS.compile.assert_called_once_with(rest_impl.GET, channel_id="9393939")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_guild_webhooks(self, rest_impl):
        mock_response = [{"channel_id": "39393993", "id": "8383838"}]
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.GUILD_WEBHOOKS)
        with mock.patch.object(routes, "GUILD_WEBHOOKS", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_guild_webhooks("9393939") is mock_response
            routes.GUILD_WEBHOOKS.compile.assert_called_once_with(rest_impl.GET, guild_id="9393939")
        rest_impl._request.assert_called_once_with(mock_route)

    @pytest.mark.asyncio
    async def test_get_webhook_without_token(self, rest_impl):
        mock_response = {"channel_id": "39393993", "id": "8383838"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.WEBHOOK)
        with mock.patch.object(routes, "WEBHOOK", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_webhook("9393939") is mock_response
            routes.WEBHOOK.compile.assert_called_once_with(rest_impl.GET, webhook_id="9393939")
        rest_impl._request.assert_called_once_with(mock_route, suppress_authorization_header=False)

    @pytest.mark.asyncio
    async def test_get_webhook_with_token(self, rest_impl):
        mock_response = {"channel_id": "39393993", "id": "8383838"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.WEBHOOK_WITH_TOKEN)
        with mock.patch.object(routes, "WEBHOOK_WITH_TOKEN", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.get_webhook("9393939", webhook_token="a_webhook_token") is mock_response
            routes.WEBHOOK_WITH_TOKEN.compile.assert_called_once_with(
                rest_impl.GET, webhook_id="9393939", webhook_token="a_webhook_token"
            )
        rest_impl._request.assert_called_once_with(mock_route, suppress_authorization_header=True)

    @pytest.mark.asyncio
    async def test_modify_webhook_without_optionals_without_token(self, rest_impl):
        mock_response = {"channel_id": "39393993", "id": "8383838"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.WEBHOOK)
        with mock.patch.object(routes, "WEBHOOK", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.modify_webhook("929292") is mock_response
            routes.WEBHOOK.compile.assert_called_once_with(rest_impl.PATCH, webhook_id="929292")
        rest_impl._request.assert_called_once_with(
            mock_route, json_body={}, reason=..., suppress_authorization_header=False
        )

    @pytest.mark.asyncio
    async def test_modify_webhook_with_optionals_without_token(self, rest_impl):
        mock_response = {"channel_id": "39393993", "id": "8383838"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.WEBHOOK)
        with mock.patch.object(routes, "WEBHOOK", compile=mock.MagicMock(return_value=mock_route)):
            assert (
                await rest_impl.modify_webhook(
                    "929292", name="nyaa", avatar=b"\211PNG\r\n\032\nblah", channel_id="2929292929", reason="nuzzle",
                )
                is mock_response
            )
            routes.WEBHOOK.compile.assert_called_once_with(rest_impl.PATCH, webhook_id="929292")
        rest_impl._request.assert_called_once_with(
            mock_route,
            json_body={"name": "nyaa", "avatar": "data:image/png;base64,iVBORw0KGgpibGFo", "channel_id": "2929292929",},
            reason="nuzzle",
            suppress_authorization_header=False,
        )

    @pytest.mark.asyncio
    async def test_modify_webhook_without_optionals_with_token(self, rest_impl):
        mock_response = {"channel_id": "39393993", "id": "8383838"}
        rest_impl._request.return_value = mock_response
        mock_route = mock.MagicMock(routes.WEBHOOK_WITH_TOKEN)
        with mock.patch.object(routes, "WEBHOOK_WITH_TOKEN", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.modify_webhook("929292", webhook_token="a_webhook_token") is mock_response
            routes.WEBHOOK_WITH_TOKEN.compile.assert_called_once_with(
                rest_impl.PATCH, webhook_id="929292", webhook_token="a_webhook_token"
            )
        rest_impl._request.assert_called_once_with(
            mock_route, json_body={}, reason=..., suppress_authorization_header=True
        )

    @pytest.mark.asyncio
    async def test_delete_webhook_without_token(self, rest_impl):
        mock_route = mock.MagicMock(routes.WEBHOOK)
        with mock.patch.object(routes, "WEBHOOK", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_webhook("9393939") is None
            routes.WEBHOOK.compile.assert_called_once_with(rest_impl.DELETE, webhook_id="9393939")
        rest_impl._request.assert_called_once_with(mock_route, suppress_authorization_header=False)

    @pytest.mark.asyncio
    async def test_delete_webhook_with_token(self, rest_impl):
        mock_route = mock.MagicMock(routes.WEBHOOK_WITH_TOKEN)
        with mock.patch.object(routes, "WEBHOOK_WITH_TOKEN", compile=mock.MagicMock(return_value=mock_route)):
            assert await rest_impl.delete_webhook("9393939", webhook_token="a_webhook_token") is None
            routes.WEBHOOK_WITH_TOKEN.compile.assert_called_once_with(
                rest_impl.DELETE, webhook_id="9393939", webhook_token="a_webhook_token"
            )
        rest_impl._request.assert_called_once_with(mock_route, suppress_authorization_header=True)

    @pytest.mark.asyncio
    async def test_execute_webhook_without_optionals(self, rest_impl):
        mock_form = mock.MagicMock(spec_set=aiohttp.FormData, add_field=mock.MagicMock())
        mock_route = mock.MagicMock(routes.WEBHOOK_WITH_TOKEN)
        rest_impl._request.return_value = None
        mock_json = "{}"
        with mock.patch.object(aiohttp, "FormData", autospec=True, return_value=mock_form):
            with mock.patch.object(routes, "WEBHOOK_WITH_TOKEN", compile=mock.MagicMock(return_value=mock_route)):
                with mock.patch.object(json, "dumps", return_value=mock_json):
                    assert await rest_impl.execute_webhook("9393939", "a_webhook_token") is None
                    routes.WEBHOOK_WITH_TOKEN.compile.assert_called_once_with(
                        rest_impl.POST, webhook_id="9393939", webhook_token="a_webhook_token"
                    )
                    json.dumps.assert_called_once_with({})
        mock_form.add_field.assert_called_once_with("payload_json", mock_json, content_type="application/json")
        rest_impl._request.assert_called_once_with(
            mock_route, form_body=mock_form, re_seekable_resources=[], query={}, suppress_authorization_header=True,
        )

    # cymock doesn't work right with the patch
    @pytest.mark.asyncio
    @unittest.mock.patch.object(aiohttp, "FormData", autospec=True)
    @unittest.mock.patch.object(routes, "WEBHOOK_WITH_TOKEN")
    @unittest.mock.patch.object(json, "dumps")
    @unittest.mock.patch.object(conversions, "make_resource_seekable")
    async def test_execute_webhook_with_optionals(
        self, make_resource_seekable, dumps, WEBHOOK_WITH_TOKEN, FormData, rest_impl
    ):
        mock_form = mock.MagicMock(spec_set=aiohttp.FormData, add_field=mock.MagicMock())
        FormData.return_value = mock_form
        mock_route = mock.MagicMock(routes.WEBHOOK_WITH_TOKEN)
        WEBHOOK_WITH_TOKEN.compile.return_value = mock_route
        mock_response = {"id": "53", "content": "la"}
        rest_impl._request.return_value = mock_response
        mock_bytes = mock.MagicMock(io.BytesIO)
        make_resource_seekable.return_value = mock_bytes
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
            file=("file.txt", b"4444ididid"),
            embeds=[{"type": "rich", "description": "A DESCRIPTION"}],
            allowed_mentions={"users": ["123"], "roles": ["456"]},
        )
        assert response is mock_response
        make_resource_seekable.assert_called_once_with(b"4444ididid")
        routes.WEBHOOK_WITH_TOKEN.compile.assert_called_once_with(
            rest_impl.POST, webhook_id="9393939", webhook_token="a_webhook_token"
        )
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

        assert mock_form.add_field.call_count == 2
        mock_form.add_field.assert_has_calls(
            (
                mock.call("payload_json", mock_json, content_type="application/json"),
                mock.call("file", mock_bytes, filename="file.txt", content_type="application/octet-stream"),
            ),
            any_order=True,
        )

        rest_impl._request.assert_called_once_with(
            mock_route,
            form_body=mock_form,
            re_seekable_resources=[mock_bytes],
            query={"wait": "True"},
            suppress_authorization_header=True,
        )
