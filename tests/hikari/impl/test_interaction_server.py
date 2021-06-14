# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import asyncio
import contextlib

import aiohttp.web
import aiohttp.web_runner
import mock
import pytest

from hikari import errors
from hikari.impl import entity_factory as entity_factory_impl
from hikari.impl import interaction_server as interaction_server_impl
from hikari.impl import rest as rest_impl
from hikari.interactions import bases as interaction_base
from hikari.internal import ed25519
from tests.hikari import hikari_test_helpers


class Test_Response:
    def test_when_only_status(self):
        response = interaction_server_impl._Response(status_code=204)

        assert response.payload is None
        assert response.headers is None
        assert response.status_code == 204

    def test_defaults_to_text_content_type(self):
        response = interaction_server_impl._Response(status_code=200, payload=b"hi there")

        assert response.headers == {"Content-Type": "text/plain; charset=UTF-8"}
        assert response.payload == b"hi there"
        assert response.status_code == 200

    def test_when_content_type_provided(self):
        response = interaction_server_impl._Response(
            status_code=201, payload=b'{"ok": "no"}', content_type="application/json"
        )

        assert response.headers == {"Content-Type": "application/json"}
        assert response.payload == b'{"ok": "no"}'
        assert response.status_code == 201


class TestInteractionServer:
    @pytest.fixture()
    def mock_entity_factory(self):
        return mock.Mock(entity_factory_impl.EntityFactoryImpl)

    @pytest.fixture()
    def mock_rest_client(self):
        return mock.Mock(rest_impl.RESTClientImpl)

    @pytest.fixture()
    def mock_verifier(self):
        return mock.Mock()

    @pytest.fixture()
    def mock_application(self):
        return mock.Mock(aiohttp.web.Application)

    @pytest.fixture()
    def mock_interaction_server(self, mock_entity_factory, mock_rest_client, mock_verifier, mock_application):
        cls = hikari_test_helpers.mock_class_namespace(interaction_server_impl.InteractionServer, slots_=False)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(ed25519, "build_ed25519_verifier", return_value=mock_verifier))
        stack.enter_context(mock.patch.object(rest_impl, "RESTClientImpl", return_value=mock_rest_client))
        stack.enter_context(mock.patch.object(aiohttp.web, "Application", return_value=mock_application))

        with stack:
            return cls(entity_factory=mock_entity_factory, rest_client=mock_rest_client)

    def test___init__(self, mock_application, mock_verifier, mock_rest_client, mock_entity_factory):
        mock_dumps = object()
        mock_loads = object()

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(aiohttp.web, "Application", return_value=mock_application))
        stack.enter_context(mock.patch.object(ed25519, "build_ed25519_verifier", return_value=mock_verifier))

        with stack:
            result = interaction_server_impl.InteractionServer(
                dumps=mock_dumps,
                entity_factory=mock_entity_factory,
                loads=mock_loads,
                rest_client=mock_rest_client,
                public_key=b"okokok",
            )

            aiohttp.web.Application.assert_called_once()
            mock_application.add_routes.assert_called_once_with([aiohttp.web.post("/", result.aiohttp_hook)])
            assert result._server is mock_application

        assert result._dumps is mock_dumps
        assert result._entity_factory is mock_entity_factory
        assert result._loads is mock_loads
        assert result._rest_client is mock_rest_client
        assert result._verify is mock_verifier

    def test___init___without_public_key(self, mock_application, mock_verifier, mock_rest_client, mock_entity_factory):
        with mock.patch.object(aiohttp.web, "Application"):
            result = interaction_server_impl.InteractionServer(
                dumps=object(), entity_factory=object(), loads=object(), rest_client=object()
            )

        assert result._verify is None

    def test_is_alive_property_when_inactive(self, mock_interaction_server):
        assert mock_interaction_server.is_alive is False

    def test_is_alive_property_when_active(self, mock_interaction_server):
        mock_interaction_server._runner = object()

        assert mock_interaction_server.is_alive is True

    @pytest.mark.asyncio()
    async def test__fetch_public_key_fetch_authorization(self, mock_interaction_server, mock_rest_client):
        mock_rest_client.fetch_authorization = mock.AsyncMock()
        mock_lock = mock.AsyncMock()
        mock_interaction_server._application_fetch_lock = mock_lock

        with mock.patch.object(ed25519, "build_ed25519_verifier") as build_verifier:
            assert await mock_interaction_server._fetch_public_key() is build_verifier.return_value

            build_verifier.assert_called_once_with(
                mock_rest_client.fetch_authorization.return_value.application.public_key
            )

        mock_rest_client.fetch_authorization.assert_awaited_once()
        mock_rest_client.fetch_application.assert_not_called()
        mock_lock.__aenter__.assert_awaited_once()
        mock_lock.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test__fetch_public_key_fetch_application(self, mock_interaction_server, mock_rest_client):
        mock_rest_client.fetch_authorization = mock.AsyncMock(
            side_effect=errors.UnauthorizedError(url="", headers={}, raw_body="")
        )
        mock_rest_client.fetch_application = mock.AsyncMock()
        mock_lock = mock.AsyncMock()
        mock_interaction_server._application_fetch_lock = mock_lock

        with mock.patch.object(ed25519, "build_ed25519_verifier") as build_verifier:
            assert await mock_interaction_server._fetch_public_key() is build_verifier.return_value

            build_verifier.assert_called_once_with(mock_rest_client.fetch_application.return_value.public_key)

        mock_rest_client.fetch_authorization.assert_awaited_once()
        mock_rest_client.fetch_application.assert_awaited_once()
        mock_lock.__aenter__.assert_awaited_once()
        mock_lock.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test__fetch_public_key_when_verify_already_set(self, mock_interaction_server):
        mock_lock = mock.AsyncMock()
        mock_verify = object()
        mock_interaction_server._application_fetch_lock = mock_lock
        mock_interaction_server._verify = mock_verify

        assert await mock_interaction_server._fetch_public_key() is mock_verify

        mock_lock.__aenter__.assert_awaited_once()
        mock_lock.__aexit__.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_aiohttp_hook(self, mock_interaction_server):
        mock_interaction_server.on_interaction = mock.AsyncMock(
            return_value=mock.Mock(
                payload=b"abody", status_code=200, headers={"header1": "ok", "content-type": "oogabooga"}
            )
        )
        request = mock.Mock(
            aiohttp.web.Request,
            content_type="application/json",
            headers={"X-Signature-Ed25519": "74726f656b70657769656f6a6b736939", "X-Signature-Timestamp": "123123"},
            read=mock.AsyncMock(return_value=b"bfddasdasd"),
        )

        result = await mock_interaction_server.aiohttp_hook(request)

        mock_interaction_server.on_interaction.assert_awaited_once_with(
            body=b"bfddasdasd", signature=b"troekpewieojksi9", timestamp=b"123123"
        )
        assert result.body == b"abody"
        assert result.content_type == "oogabooga"
        assert result.headers == {"header1": "ok", "content-type": "oogabooga"}
        assert result.status == 200

    @pytest.mark.asyncio()
    async def test_aiohttp_hook_for_unsupported_media_type(self, mock_interaction_server):
        request = mock.Mock(aiohttp.web.Request, content_type="notjson")

        result = await mock_interaction_server.aiohttp_hook(request)

        assert result.body == b"Unsupported Media Type"
        assert result.charset == "UTF-8"
        assert result.content_type == "text/plain"
        assert result.status == 415

    @pytest.mark.asyncio()
    async def test_aiohttp_hook_with_missing_ed25519_header(self, mock_interaction_server):
        request = mock.Mock(aiohttp.web.Request, content_type="application/json", headers={"X-Signature-Timestamp": ""})

        result = await mock_interaction_server.aiohttp_hook(request)

        assert result.body == b"Missing or invalid required request signature header(s)"
        assert result.charset == "UTF-8"
        assert result.content_type == "text/plain"
        assert result.status == 400

    @pytest.mark.asyncio()
    async def test_aiohttp_hook_with_missing_timestamp_header(self, mock_interaction_server):
        request = mock.Mock(aiohttp.web.Request, content_type="application/json", headers={"X-Signature-Ed25519": ""})

        result = await mock_interaction_server.aiohttp_hook(request)

        assert result.body == b"Missing or invalid required request signature header(s)"
        assert result.charset == "UTF-8"
        assert result.content_type == "text/plain"
        assert result.status == 400

    @pytest.mark.asyncio()
    async def test_aiohttp_hook_with_invalid_ed25519_header(self, mock_interaction_server):
        request = mock.Mock(
            aiohttp.web.Request,
            content_type="application/json",
            headers={"X-Signature-Ed25519": "'#';[][];['345", "X-Signature-Timestamp": ""},
        )

        result = await mock_interaction_server.aiohttp_hook(request)

        assert result.body == b"Missing or invalid required request signature header(s)"
        assert result.charset == "UTF-8"
        assert result.content_type == "text/plain"
        assert result.status == 400

    @pytest.mark.asyncio()
    async def test_aiohttp_hook_when_payload_too_large(self, mock_interaction_server):
        request = mock.Mock(
            aiohttp.web.Request,
            content_type="application/json",
            headers={"X-Signature-Ed25519": "74726f656b70657769656f6a6b736939", "X-Signature-Timestamp": "123123"},
            read=mock.AsyncMock(side_effect=aiohttp.web.HTTPRequestEntityTooLarge(123, 321)),
        )

        result = await mock_interaction_server.aiohttp_hook(request)

        assert result.body == b"Payload too large"
        assert result.charset == "UTF-8"
        assert result.content_type == "text/plain"
        assert result.status == 413

    @pytest.mark.asyncio()
    async def test_aiohttp_hook_when_no_body(self, mock_interaction_server):
        request = mock.Mock(
            aiohttp.web.Request,
            content_type="application/json",
            headers={"X-Signature-Ed25519": "74726f656b70657769656f6a6b736939", "X-Signature-Timestamp": "123123"},
            read=mock.AsyncMock(return_value=""),
        )

        result = await mock_interaction_server.aiohttp_hook(request)

        assert result.body == b"POST request must have a body"
        assert result.charset == "UTF-8"
        assert result.content_type == "text/plain"
        assert result.status == 400

    @pytest.mark.asyncio()
    async def test_close(self, mock_interaction_server):
        mock_runner = mock.AsyncMock()
        mock_event = mock.Mock()
        mock_interaction_server._is_closing = False
        mock_interaction_server._runner = mock_runner
        mock_interaction_server._close_event = mock_event

        await mock_interaction_server.close()

        mock_runner.shutdown.assert_awaited_once()
        mock_runner.cleanup.assert_awaited_once()
        mock_event.set.assert_called_once()
        assert mock_interaction_server._is_closing is True

    @pytest.mark.asyncio()
    async def test_close_when_closing(self, mock_interaction_server):
        mock_runner = mock.AsyncMock()
        mock_event = mock.Mock()
        mock_interaction_server._runner = mock_runner
        mock_interaction_server._close_event = mock_event
        mock_interaction_server._is_closing = True
        mock_interaction_server.join = mock.AsyncMock()

        await mock_interaction_server.close()

        mock_runner.shutdown.assert_not_called()
        mock_runner.cleanup.assert_not_called()
        mock_event.set.assert_not_called()
        mock_interaction_server.join.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_close_when_not_running(self, mock_interaction_server):
        with pytest.raises(errors.ComponentStateConflictError):
            await mock_interaction_server.close()

    @pytest.mark.asyncio()
    async def test_join(self, mock_interaction_server):
        mock_event = mock.AsyncMock()
        mock_interaction_server._runner = object()
        mock_interaction_server._close_event = mock_event

        await mock_interaction_server.join()

        mock_event.wait.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_join_when_not_running(self, mock_interaction_server):
        with pytest.raises(errors.ComponentStateConflictError):
            await mock_interaction_server.join()

    @pytest.mark.asyncio()
    async def test_on_interaction(self, mock_interaction_server, mock_entity_factory):
        mock_verifier = mock.Mock(return_value=True)
        mock_interaction_server._verify = mock_verifier
        mock_entity_factory.deserialize_interaction.return_value = interaction_base.PartialInteraction(
            app=None, id=123, application_id=541324, type=2, token="ok", version=1
        )
        mock_builder = mock.Mock(build=mock.Mock(return_value={"ok": "No boomer"}))
        mock_listener = mock.AsyncMock(return_value=mock_builder)
        mock_interaction_server.set_listener(interaction_base.PartialInteraction, mock_listener)

        result = await mock_interaction_server.on_interaction(b'{"type": 2}', b"signature", b"timestamp")

        mock_verifier.assert_called_once_with(b'{"type": 2}', b"signature", b"timestamp")
        mock_listener.assert_awaited_once_with(mock_entity_factory.deserialize_interaction.return_value)
        mock_builder.build.assert_called_once_with(mock_entity_factory)
        assert result.headers == {"Content-Type": "application/json; charset=UTF-8"}
        assert result.payload == b'{"ok": "No boomer"}'
        assert result.status_code == 200

    @pytest.mark.asyncio()
    async def test_on_interaction_calls__fetch_public_key(self, mock_interaction_server):
        mock_fetcher = mock.AsyncMock(return_value=mock.Mock(return_value=False))
        mock_interaction_server._verify = None
        mock_interaction_server._fetch_public_key = mock_fetcher

        result = await mock_interaction_server.on_interaction(b"body", b"signature", b"timestamp")

        mock_fetcher.assert_awaited_once()
        mock_fetcher.return_value.assert_called_once_with(b"body", b"signature", b"timestamp")
        assert result.headers == {"Content-Type": "text/plain; charset=UTF-8"}
        assert result.payload == b"Invalid request signature"
        assert result.status_code == 400

    @pytest.mark.asyncio()
    async def test_on_interaction_when_public_key_mismatch(self, mock_interaction_server):
        mock_verifier = mock.Mock(return_value=False)
        mock_interaction_server._verify = mock_verifier

        result = await mock_interaction_server.on_interaction(b"body", b"signature", b"timestamp")

        mock_verifier.assert_called_once_with(b"body", b"signature", b"timestamp")
        assert result.headers == {"Content-Type": "text/plain; charset=UTF-8"}
        assert result.payload == b"Invalid request signature"
        assert result.status_code == 400

    @pytest.mark.parametrize("body", [b"not a json", b"\x80abc"])
    @pytest.mark.asyncio()
    async def test_on_interaction_when_bad_body(self, mock_interaction_server, body):
        mock_interaction_server._verify = mock.Mock(return_value=True)

        result = await mock_interaction_server.on_interaction(body, b"signature", b"timestamp")

        assert result.headers == {"Content-Type": "text/plain; charset=UTF-8"}
        assert result.payload == b"Invalid JSON body"
        assert result.status_code == 400

    @pytest.mark.asyncio()
    async def test_on_interaction_when_missing_type_key(self, mock_interaction_server):
        mock_interaction_server._verify = mock.Mock(return_value=True)

        result = await mock_interaction_server.on_interaction(b'{"key": "OK"}', b"signature", b"timestamp")

        assert result.headers == {"Content-Type": "text/plain; charset=UTF-8"}
        assert result.payload == b"Missing required 'type' field in payload"
        assert result.status_code == 400

    @pytest.mark.asyncio()
    async def test_on_interaction_on_ping(self, mock_interaction_server):
        mock_interaction_server._verify = mock.Mock(return_value=True)

        result = await mock_interaction_server.on_interaction(b'{"type": 1}', b"signature", b"timestamp")

        assert result.headers == {"Content-Type": "application/json; charset=UTF-8"}
        assert result.payload == b'{"type": 1}'
        assert result.status_code == 200

    @pytest.mark.asyncio()
    async def test_on_interaction_on_deserialize_unrecognised_entity_error(
        self, mock_interaction_server, mock_entity_factory
    ):
        mock_interaction_server._verify = mock.Mock(return_value=True)
        mock_entity_factory.deserialize_interaction.side_effect = errors.UnrecognisedEntityError("blah")

        result = await mock_interaction_server.on_interaction(b'{"type": 2}', b"signature", b"timestamp")

        assert result.headers == {"Content-Type": "text/plain; charset=UTF-8"}
        assert result.payload == b"Interaction type not implemented"
        assert result.status_code == 501

    @pytest.mark.asyncio()
    async def test_on_interaction_on_failed_deserialize(self, mock_interaction_server, mock_entity_factory):
        mock_interaction_server._verify = mock.Mock(return_value=True)
        mock_exception = TypeError("OK")
        mock_entity_factory.deserialize_interaction.side_effect = mock_exception

        with mock.patch.object(asyncio, "get_running_loop") as get_running_loop:
            result = await mock_interaction_server.on_interaction(b'{"type": 2}', b"signature", b"timestamp")

            get_running_loop.return_value.call_exception_handler.assert_called_once_with(
                {"message": "Exception occurred during interaction deserialization", "exception": mock_exception}
            )

        assert result.headers == {"Content-Type": "text/plain; charset=UTF-8"}
        assert result.payload == b"Exception occurred during interaction deserialization"
        assert result.status_code == 500

    @pytest.mark.asyncio()
    async def test_on_interaction_on_dispatch_error(self, mock_interaction_server, mock_entity_factory):
        mock_interaction_server._verify = mock.Mock(return_value=True)
        mock_exception = TypeError("OK")
        mock_entity_factory.deserialize_interaction.return_value = interaction_base.PartialInteraction(
            app=None, id=123, application_id=541324, type=2, token="ok", version=1
        )
        mock_interaction_server.set_listener(interaction_base.PartialInteraction, mock.Mock(side_effect=mock_exception))

        with mock.patch.object(asyncio, "get_running_loop") as get_running_loop:
            result = await mock_interaction_server.on_interaction(b'{"type": 2}', b"signature", b"timestamp")

            get_running_loop.return_value.call_exception_handler.assert_called_once_with(
                {"message": "Exception occurred during interaction dispatch", "exception": mock_exception}
            )

        assert result.headers == {"Content-Type": "text/plain; charset=UTF-8"}
        assert result.payload == b"Exception occurred during interaction dispatch"
        assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_on_interaction_when_response_builder_error(self, mock_interaction_server, mock_entity_factory):
        mock_interaction_server._verify = mock.Mock(return_value=True)
        mock_exception = TypeError("OK")
        mock_entity_factory.deserialize_interaction.return_value = interaction_base.PartialInteraction(
            app=None, id=123, application_id=541324, type=2, token="ok", version=1
        )
        mock_builder = mock.Mock(build=mock.Mock(side_effect=mock_exception))
        mock_interaction_server.set_listener(
            interaction_base.PartialInteraction, mock.AsyncMock(return_value=mock_builder)
        )

        with mock.patch.object(asyncio, "get_running_loop") as get_running_loop:
            result = await mock_interaction_server.on_interaction(b'{"type": 2}', b"signature", b"timestamp")

            get_running_loop.return_value.call_exception_handler.assert_called_once_with(
                {"message": "Exception occurred during interaction dispatch", "exception": mock_exception}
            )

        assert result.headers == {"Content-Type": "text/plain; charset=UTF-8"}
        assert result.payload == b"Exception occurred during interaction dispatch"
        assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_on_interaction_when_json_encode_fails(self, mock_interaction_server, mock_entity_factory):
        mock_interaction_server._verify = mock.Mock(return_value=True)
        mock_exception = TypeError("OK")
        mock_interaction_server._dumps = mock.Mock(side_effect=mock_exception)
        mock_entity_factory.deserialize_interaction.return_value = interaction_base.PartialInteraction(
            app=None, id=123, application_id=541324, type=2, token="ok", version=1
        )
        mock_builder = mock.Mock(build=mock.Mock())
        mock_interaction_server.set_listener(
            interaction_base.PartialInteraction, mock.AsyncMock(return_value=mock_builder)
        )

        with mock.patch.object(asyncio, "get_running_loop") as get_running_loop:
            result = await mock_interaction_server.on_interaction(b'{"type": 2}', b"signature", b"timestamp")

            get_running_loop.return_value.call_exception_handler.assert_called_once_with(
                {"message": "Exception occurred during interaction dispatch", "exception": mock_exception}
            )

        assert result.headers == {"Content-Type": "text/plain; charset=UTF-8"}
        assert result.payload == b"Exception occurred during interaction dispatch"
        assert result.status_code == 500

    @pytest.mark.asyncio()
    async def test_on_interaction_when_no_registered_listener(self, mock_interaction_server, mock_entity_factory):
        mock_interaction_server._verify = mock.Mock(return_value=True)

        result = await mock_interaction_server.on_interaction(b'{"type": 2}', b"signature", b"timestamp")

        assert result.headers == {"Content-Type": "text/plain; charset=UTF-8"}
        assert result.payload == b"Handler not set for this interaction type"
        assert result.status_code == 501

    @pytest.mark.asyncio()
    async def test_start(self, mock_interaction_server, mock_application):
        mock_context = object()
        mock_socket = object()
        mock_interaction_server._is_closing = True
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(aiohttp.web, "TCPSite", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web, "UnixSite", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web, "SockSite", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web_runner, "AppRunner", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(asyncio, "Event"))

        with stack:
            await mock_interaction_server.start(
                backlog=123123,
                enable_signal_handlers=False,
                host="hoototototo",
                port=123123123,
                path="hshshshshsh",
                reuse_address=True,
                reuse_port=False,
                socket=mock_socket,
                shutdown_timeout=3232.3232,
                ssl_context=mock_context,
            )

            aiohttp.web_runner.AppRunner.assert_called_once_with(
                mock_application, handle_signals=False, access_log=interaction_server_impl._LOGGER
            )
            aiohttp.web_runner.AppRunner.return_value.setup.assert_awaited_once()
            aiohttp.web.TCPSite.assert_called_once_with(
                aiohttp.web_runner.AppRunner.return_value,
                "hoototototo",
                123123123,
                shutdown_timeout=3232.3232,
                ssl_context=mock_context,
                backlog=123123,
                reuse_address=True,
                reuse_port=False,
            )
            aiohttp.web.UnixSite.assert_called_once_with(
                aiohttp.web_runner.AppRunner.return_value,
                "hshshshshsh",
                shutdown_timeout=3232.3232,
                ssl_context=mock_context,
                backlog=123123,
            )
            aiohttp.web.SockSite.assert_called_once_with(
                aiohttp.web_runner.AppRunner.return_value,
                mock_socket,
                shutdown_timeout=3232.3232,
                ssl_context=mock_context,
                backlog=123123,
            )
            aiohttp.web.TCPSite.return_value.start.assert_awaited_once()
            aiohttp.web.UnixSite.return_value.start.assert_awaited_once()
            aiohttp.web.SockSite.return_value.start.assert_awaited_once()
            assert mock_interaction_server._close_event is asyncio.Event.return_value
            assert mock_interaction_server._is_closing is False

    @pytest.mark.asyncio()
    async def test_start_with_default_behaviour(self, mock_interaction_server, mock_application):
        mock_context = object()
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(aiohttp.web, "TCPSite", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web_runner, "AppRunner", return_value=mock.AsyncMock()))

        with stack:
            await mock_interaction_server.start(ssl_context=mock_context)

            aiohttp.web_runner.AppRunner.assert_called_once_with(
                mock_application, handle_signals=True, access_log=interaction_server_impl._LOGGER
            )
            aiohttp.web_runner.AppRunner.return_value.setup.assert_awaited_once()
            aiohttp.web.TCPSite.assert_called_once_with(
                aiohttp.web_runner.AppRunner.return_value,
                port=None,
                shutdown_timeout=60.0,
                ssl_context=mock_context,
                backlog=128,
                reuse_address=None,
                reuse_port=None,
            )
            aiohttp.web.TCPSite.return_value.start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_with_multiple_hosts(self, mock_interaction_server, mock_application):
        mock_context = object()
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(aiohttp.web, "TCPSite", return_value=mock.AsyncMock()))
        stack.enter_context(mock.patch.object(aiohttp.web_runner, "AppRunner", return_value=mock.AsyncMock()))

        with stack:
            await mock_interaction_server.start(ssl_context=mock_context, host=["123", "4312"], port=453123)

            aiohttp.web_runner.AppRunner.assert_called_once_with(
                mock_application, handle_signals=True, access_log=interaction_server_impl._LOGGER
            )
            aiohttp.web_runner.AppRunner.return_value.setup.assert_awaited_once()
            aiohttp.web.TCPSite.assert_has_calls(
                [
                    mock.call(
                        aiohttp.web_runner.AppRunner.return_value,
                        "123",
                        453123,
                        shutdown_timeout=60.0,
                        ssl_context=mock_context,
                        backlog=128,
                        reuse_address=None,
                        reuse_port=None,
                    ),
                    mock.call(
                        aiohttp.web_runner.AppRunner.return_value,
                        "4312",
                        453123,
                        shutdown_timeout=60.0,
                        ssl_context=mock_context,
                        backlog=128,
                        reuse_address=None,
                        reuse_port=None,
                    ),
                ]
            )
            aiohttp.web.TCPSite.return_value.start.assert_has_awaits([mock.call(), mock.call()])

    @pytest.mark.asyncio()
    async def test_start_when_already_running(self, mock_interaction_server):
        mock_interaction_server._runner = object()

        with pytest.raises(errors.ComponentStateConflictError):
            await mock_interaction_server.start()

    def test_get_listener_when_unknown(self, mock_interaction_server):
        assert mock_interaction_server.get_listener(interaction_base.PartialInteraction) is None

    def test_get_listener_when_registered(self, mock_interaction_server):
        mock_listener = object()
        mock_interaction_server.set_listener(interaction_base.PartialInteraction, mock_listener)

        assert mock_interaction_server.get_listener(interaction_base.PartialInteraction) is mock_listener

    def test_set_listener(self, mock_interaction_server):
        mock_listener = object()

        mock_interaction_server.set_listener(interaction_base.PartialInteraction, mock_listener)

        assert mock_interaction_server.get_listener(interaction_base.PartialInteraction) is mock_listener

    def test_set_listener_when_already_registered_without_replace(self, mock_interaction_server):
        mock_interaction_server.set_listener(interaction_base.PartialInteraction, object())

        with pytest.raises(TypeError):
            mock_interaction_server.set_listener(interaction_base.PartialInteraction, object())

    def test_set_listener_when_already_registered_with_replace(self, mock_interaction_server):
        mock_listener = object()
        mock_interaction_server.set_listener(interaction_base.PartialInteraction, object())

        mock_interaction_server.set_listener(interaction_base.PartialInteraction, mock_listener, replace=True)

        assert mock_interaction_server.get_listener(interaction_base.PartialInteraction) is mock_listener

    def test_set_listener_when_removing_listener(self, mock_interaction_server):
        mock_interaction_server.set_listener(interaction_base.PartialInteraction, object())
        mock_interaction_server.set_listener(interaction_base.PartialInteraction, None)

        assert mock_interaction_server.get_listener(interaction_base.PartialInteraction) is None
