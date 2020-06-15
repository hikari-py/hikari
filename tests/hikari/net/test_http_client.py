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
import json
import types

import aiohttp
import mock
import pytest

from hikari.net import http_client
from hikari.net import http_settings
from hikari.net import tracing
from tests.hikari import _helpers


@pytest.fixture
def client_session():
    client_session = mock.create_autospec(aiohttp.ClientSession, spec_set=True)
    with mock.patch.object(aiohttp, "ClientSession", return_value=client_session):
        yield client_session


@pytest.fixture
def client(client_session):
    assert client_session, "this param is needed, it ensures aiohttp is patched for the test"
    client = _helpers.unslot_class(http_client.HTTPClient)(mock.MagicMock())
    yield client


@pytest.mark.asyncio
class TestInit:
    async def test_CFRayTracer_used_for_non_debug(self):
        async with http_client.HTTPClient(debug=False, logger=mock.MagicMock()) as client:
            assert len(client._tracers) == 1
            assert isinstance(client._tracers[0], tracing.CFRayTracer)

    async def test_DebugTracer_used_for_debug(self):
        async with http_client.HTTPClient(debug=True, logger=mock.MagicMock()) as client:
            assert len(client._tracers) == 1
            assert isinstance(client._tracers[0], tracing.DebugTracer)


@pytest.mark.asyncio
class TestAcquireClientSession:
    async def test_acquire_creates_new_session_if_one_does_not_exist(self, client):
        client._config = http_settings.HTTPSettings()
        client._config.tcp_connector_factory = mock.MagicMock()
        client._config.trust_env = mock.MagicMock()

        client._client_session = None
        cs = client.get_client_session()
        assert client._client_session is cs
        aiohttp.ClientSession.assert_called_once_with(
            connector=client._config.tcp_connector_factory(),
            trust_env=client._config.trust_env,
            version=aiohttp.HttpVersion11,
            json_serialize=json.dumps,
            trace_configs=[t.trace_config for t in client._tracers],
        )

    async def test_acquire_repeated_calls_caches_client_session(self, client):
        cs = client.get_client_session()

        for i in range(10):
            aiohttp.ClientSession.reset_mock()
            assert cs is client.get_client_session()
            aiohttp.ClientSession.assert_not_called()


@pytest.mark.asyncio
class TestClose:
    async def test_close_when_not_running(self, client, client_session):
        client._client_session = None
        await client.close()
        assert client._client_session is None

    async def test_close_when_running(self, client, client_session):
        client._client_session = client_session
        await client.close()
        assert client._client_session is None
        client_session.close.assert_awaited_once_with()


@pytest.mark.asyncio
class TestPerformRequest:
    async def test_perform_request_form_data(self, client, client_session):
        client._config = http_settings.HTTPSettings()
        client._config.allow_redirects = mock.MagicMock()
        client._config.proxy_url = mock.MagicMock()
        client._config.proxy_auth = mock.MagicMock()
        client._config.proxy_headers = mock.MagicMock()
        client._config.verify_ssl = mock.MagicMock()
        client._config.ssl_context = mock.MagicMock()
        client._config.request_timeout = mock.MagicMock()

        form_data = aiohttp.FormData()

        trace_request_ctx = types.SimpleNamespace()
        trace_request_ctx.request_body = form_data

        expected_response = mock.MagicMock()
        client_session.request = mock.AsyncMock(return_value=expected_response)

        actual_response = await client._perform_request(
            method="POST", url="http://foo.bar", headers={"X-Foo-Count": "122"}, body=form_data, query={"foo": "bar"},
        )

        assert expected_response is actual_response
        client_session.request.assert_awaited_once_with(
            method="POST",
            url="http://foo.bar",
            params={"foo": "bar"},
            headers={"X-Foo-Count": "122"},
            data=form_data,
            allow_redirects=client._config.allow_redirects,
            proxy=client._config.proxy_url,
            proxy_auth=client._config.proxy_auth,
            proxy_headers=client._config.proxy_headers,
            verify_ssl=client._config.verify_ssl,
            ssl_context=client._config.ssl_context,
            timeout=client._config.request_timeout,
            trace_request_ctx=trace_request_ctx,
        )

    async def test_perform_request_json(self, client, client_session):
        client._config = http_settings.HTTPSettings()
        client._config.allow_redirects = mock.MagicMock()
        client._config.proxy_url = mock.MagicMock()
        client._config.proxy_auth = mock.MagicMock()
        client._config.proxy_headers = mock.MagicMock()
        client._config.verify_ssl = mock.MagicMock()
        client._config.ssl_context = mock.MagicMock()
        client._config.request_timeout = mock.MagicMock()

        req = {"hello": "world"}

        trace_request_ctx = types.SimpleNamespace()
        trace_request_ctx.request_body = req

        expected_response = mock.MagicMock()
        client_session.request = mock.AsyncMock(return_value=expected_response)

        actual_response = await client._perform_request(
            method="POST", url="http://foo.bar", headers={"X-Foo-Count": "122"}, body=req, query={"foo": "bar"},
        )

        assert expected_response is actual_response
        client_session.request.assert_awaited_once_with(
            method="POST",
            url="http://foo.bar",
            params={"foo": "bar"},
            headers={"X-Foo-Count": "122"},
            json=req,
            allow_redirects=client._config.allow_redirects,
            proxy=client._config.proxy_url,
            proxy_auth=client._config.proxy_auth,
            proxy_headers=client._config.proxy_headers,
            verify_ssl=client._config.verify_ssl,
            ssl_context=client._config.ssl_context,
            timeout=client._config.request_timeout,
            trace_request_ctx=trace_request_ctx,
        )


@pytest.mark.asyncio
class TestCreateWs:
    async def test_create_ws(self, client, client_session):
        client._config = http_settings.HTTPSettings()
        client._config.allow_redirects = mock.MagicMock()
        client._config.proxy_url = mock.MagicMock()
        client._config.proxy_auth = mock.MagicMock()
        client._config.proxy_headers = mock.MagicMock()
        client._config.verify_ssl = mock.MagicMock()
        client._config.ssl_context = mock.MagicMock()
        client._config.request_timeout = mock.MagicMock()

        expected_ws = mock.MagicMock()
        client_session.ws_connect = mock.AsyncMock(return_value=expected_ws)

        actual_ws = await client._create_ws("foo://bar", compress=5, auto_ping=True, max_msg_size=3)

        assert expected_ws is actual_ws

        client_session.ws_connect.assert_awaited_once_with(
            url="foo://bar",
            compress=5,
            autoping=True,
            max_msg_size=3,
            proxy=client._config.proxy_url,
            proxy_auth=client._config.proxy_auth,
            proxy_headers=client._config.proxy_headers,
            verify_ssl=client._config.verify_ssl,
            ssl_context=client._config.ssl_context,
        )
