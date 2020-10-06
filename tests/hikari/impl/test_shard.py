# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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
import datetime
import platform

import aiohttp
import mock
import pytest

from hikari import _about
from hikari import config
from hikari import errors
from hikari import intents
from hikari import presences
from hikari import undefined
from hikari.impl import shard
from hikari.internal import aio
from hikari.internal import time
from tests.hikari import client_session_stub
from tests.hikari import hikari_test_helpers


def test_log_filterer():
    filterer = shard._log_filterer("TOKEN")

    returned = filterer("this log contains the TOKEN and it should get removed and the TOKEN here too")
    assert returned == (
        "this log contains the **REDACTED TOKEN** and it should get removed and the **REDACTED TOKEN** here too"
    )


@pytest.fixture()
def http_settings():
    return mock.Mock(spec_set=config.HTTPSettings)


@pytest.fixture()
def proxy_settings():
    return mock.Mock(spec_set=config.ProxySettings)


@pytest.mark.asyncio
class Test_V6GatewayTransport:
    @pytest.fixture()
    def transport_impl(self):
        with mock.patch.object(aiohttp.ClientWebSocketResponse, "__init__"):
            transport = shard._GatewayTransport()
            transport.logger = mock.Mock(getEffectiveLevel=mock.Mock(return_value=5))
            transport.log_filterer = mock.Mock()
            yield transport

    def test__init__calls_super(self):
        with mock.patch.object(aiohttp.ClientWebSocketResponse, "__init__") as init:
            shard._GatewayTransport("arg1", "arg2", some_kwarg="kwarg1")

        init.assert_called_once_with("arg1", "arg2", some_kwarg="kwarg1")

    async def test_send_close_when_not_closed_nor_closing_logs(self, transport_impl):
        transport_impl._closed = False
        transport_impl._closing = False
        transport_impl.logger = mock.Mock()

        with mock.patch.object(aiohttp.ClientWebSocketResponse, "close") as close:
            await transport_impl.send_close(code=1234, message=b"some message")

        transport_impl.logger.debug.assert_called_once_with(
            "sending close frame with code %s and message %s", 1234, b"some message"
        )
        close.assert_called_once_with(code=1234, message=b"some message")

    async def test_receive_json(self, transport_impl):
        transport_impl._receive_and_check = mock.AsyncMock(return_value="{'json_response': null}")
        transport_impl.log_payload = mock.Mock()
        mock_loads = mock.Mock(return_value={"json_response": None})

        assert await transport_impl.receive_json(loads=mock_loads, timeout=69) == {"json_response": None}

        transport_impl._receive_and_check.assert_awaited_once_with(69)
        mock_loads.assert_called_once_with("{'json_response': null}")

    async def test_send_json(self, transport_impl):
        transport_impl.send_str = mock.AsyncMock()
        transport_impl.log_payload = mock.Mock()
        mock_dumps = mock.Mock(return_value="{'json_send': null}")

        await transport_impl.send_json({"json_send": None}, 420, dumps=mock_dumps)

        transport_impl.send_str.assert_awaited_once_with("{'json_send': null}", 420)
        mock_dumps.assert_called_once_with({"json_send": None})

    class StubResponse:
        def __init__(
            self,
            *,
            type=None,
            data=None,
            extra=None,
        ):
            self.type = type
            self.data = data
            self.extra = extra

    @pytest.mark.parametrize(
        "code",
        [
            *range(3990, 4000),
            errors.ShardCloseCode.DECODE_ERROR,
            errors.ShardCloseCode.INVALID_SEQ,
            errors.ShardCloseCode.UNKNOWN_ERROR,
            errors.ShardCloseCode.SESSION_TIMEOUT,
            errors.ShardCloseCode.RATE_LIMITED,
        ],
    )
    async def test__receive_and_check_when_message_type_is_CLOSE_and_should_reconnect(self, code, transport_impl):
        stub_response = self.StubResponse(type=aiohttp.WSMsgType.CLOSE, extra="some error extra", data=code)
        transport_impl.receive = mock.AsyncMock(return_value=stub_response)
        transport_impl.logger = mock.Mock()

        with pytest.raises(errors.GatewayServerClosedConnectionError) as exinfo:
            await transport_impl._receive_and_check(10)

        exception = exinfo.value
        assert exception.reason == "some error extra"
        assert exception.code == int(code)
        assert exception.can_reconnect is True
        transport_impl.receive.assert_awaited_once_with(10)

    @pytest.mark.parametrize(
        "code",
        [*range(4010, 4020), 5000],
    )
    async def test__receive_and_check_when_message_type_is_CLOSE_and_should_not_reconnect(self, code, transport_impl):
        stub_response = self.StubResponse(type=aiohttp.WSMsgType.CLOSE, extra="dont reconnect", data=code)
        transport_impl.receive = mock.AsyncMock(return_value=stub_response)
        transport_impl.logger = mock.Mock()

        with pytest.raises(errors.GatewayServerClosedConnectionError) as exinfo:
            await transport_impl._receive_and_check(10)

        exception = exinfo.value
        assert exception.reason == "dont reconnect"
        assert exception.code == int(code)
        assert exception.can_reconnect is False
        transport_impl.receive.assert_awaited_once_with(10)

    async def test__receive_and_check_when_message_type_is_CLOSING(self, transport_impl):
        stub_response = self.StubResponse(type=aiohttp.WSMsgType.CLOSING)
        transport_impl.receive = mock.AsyncMock(return_value=stub_response)

        with pytest.raises(errors.GatewayError, match="Socket has closed"):
            await transport_impl._receive_and_check(10)

        transport_impl.receive.assert_awaited_once_with(10)

    async def test__receive_and_check_when_message_type_is_CLOSED(self, transport_impl):
        stub_response = self.StubResponse(type=aiohttp.WSMsgType.CLOSED)
        transport_impl.receive = mock.AsyncMock(return_value=stub_response)

        with pytest.raises(errors.GatewayError, match="Socket has closed"):
            await transport_impl._receive_and_check(10)

        transport_impl.receive.assert_awaited_once_with(10)

    async def test__receive_and_check_when_message_type_is_BINARY(self, transport_impl):
        response1 = self.StubResponse(type=aiohttp.WSMsgType.BINARY, data=b"some")
        response2 = self.StubResponse(type=aiohttp.WSMsgType.BINARY, data=b"data")
        response3 = self.StubResponse(type=aiohttp.WSMsgType.BINARY, data=b"\x00\x00\xff\xff")
        transport_impl.receive = mock.AsyncMock(side_effect=[response1, response2, response3])
        transport_impl.zlib = mock.Mock(decompress=mock.Mock(return_value=b"utf-8 encoded bytes"))

        assert await transport_impl._receive_and_check(10) == "utf-8 encoded bytes"

        transport_impl.receive.assert_awaited_with(10)
        transport_impl.zlib.decompress.assert_called_once_with(bytearray(b"somedata\x00\x00\xff\xff"))

    async def test__receive_and_check_when_buff_but_next_is_not_BINARY(self, transport_impl):
        response1 = self.StubResponse(type=aiohttp.WSMsgType.BINARY, data=b"some")
        response2 = self.StubResponse(type=aiohttp.WSMsgType.TEXT)
        transport_impl.receive = mock.AsyncMock(side_effect=[response1, response2])

        with pytest.raises(errors.GatewayError, match="Unexpected message type received TEXT, expected BINARY"):
            await transport_impl._receive_and_check(10)

        transport_impl.receive.assert_awaited_with(10)

    async def test__receive_and_check_when_message_type_is_TEXT(self, transport_impl):
        transport_impl.receive = mock.AsyncMock(
            return_value=self.StubResponse(type=aiohttp.WSMsgType.TEXT, data="some text")
        )

        assert await transport_impl._receive_and_check(10) == "some text"

        transport_impl.receive.assert_awaited_once_with(10)

    async def test__receive_and_check_when_message_type_is_unknown(self, transport_impl):
        transport_impl.receive = mock.AsyncMock(return_value=self.StubResponse(type=aiohttp.WSMsgType.ERROR))
        transport_impl.exception = mock.Mock(return_value=Exception)
        transport_impl.logger = mock.Mock()

        with pytest.raises(errors.GatewayError, match="Unexpected websocket exception from gateway"):
            await transport_impl._receive_and_check(10)

        transport_impl.receive.assert_awaited_once_with(10)

    async def test_connect_yields_websocket(self, http_settings, proxy_settings):
        class MockWS(hikari_test_helpers.AsyncContextManagerMock, shard._GatewayTransport):
            closed = True
            send_close = mock.AsyncMock()
            sent_close = False

            def __init__(self):
                pass

        mock_websocket = MockWS()
        mock_client_session = hikari_test_helpers.AsyncContextManagerMock()
        mock_client_session.ws_connect = mock.MagicMock(return_value=mock_websocket)

        stack = contextlib.ExitStack()
        sleep = stack.enter_context(mock.patch.object(asyncio, "sleep"))
        client_session = stack.enter_context(
            mock.patch.object(aiohttp, "ClientSession", return_value=mock_client_session)
        )
        tcp_connector = stack.enter_context(mock.patch.object(aiohttp, "TCPConnector"))
        client_timeout = stack.enter_context(mock.patch.object(aiohttp, "ClientTimeout"))
        logger = mock.Mock()
        log_filterer = mock.Mock()

        with stack:
            async with shard._GatewayTransport.connect(
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                logger=logger,
                url="https://some.url",
                log_filterer=log_filterer,
            ) as ws:
                assert ws.logger is logger

        tcp_connector.assert_called_once_with(
            limit=1,
            ttl_dns_cache=10,
            use_dns_cache=False,
            ssl_context=http_settings.ssl,
            enable_cleanup_closed=http_settings.enable_cleanup_closed,
            force_close=http_settings.force_close_transports,
        )
        client_timeout.assert_called_once_with(
            total=http_settings.timeouts.total,
            connect=http_settings.timeouts.acquire_and_connect,
            sock_read=http_settings.timeouts.request_socket_read,
            sock_connect=http_settings.timeouts.request_socket_connect,
        )
        client_session.assert_called_once_with(
            connector=tcp_connector(),
            connector_owner=True,
            raise_for_status=True,
            timeout=client_timeout(),
            trust_env=proxy_settings.trust_env,
            version=aiohttp.HttpVersion11,
            ws_response_class=shard._GatewayTransport,
        )
        mock_client_session.ws_connect.assert_called_once_with(
            max_msg_size=0,
            proxy=proxy_settings.url,
            proxy_headers=proxy_settings.headers,
            url="https://some.url",
        )
        mock_client_session.assert_used_once()
        mock_websocket.assert_used_once()
        sleep.assert_awaited_once_with(0.25)

    async def test_connect_when_gateway_error_after_connecting(self, http_settings, proxy_settings):
        class MockWS(hikari_test_helpers.AsyncContextManagerMock, shard._GatewayTransport):
            closed = False
            sent_close = False
            send_close = mock.AsyncMock()

            def __init__(self):
                pass

        mock_websocket = MockWS()
        mock_client_session = hikari_test_helpers.AsyncContextManagerMock()
        mock_client_session.ws_connect = mock.MagicMock(return_value=mock_websocket)

        stack = contextlib.ExitStack()
        sleep = stack.enter_context(mock.patch.object(asyncio, "sleep"))
        stack.enter_context(mock.patch.object(aiohttp, "ClientSession", return_value=mock_client_session))
        stack.enter_context(mock.patch.object(aiohttp, "TCPConnector"))
        stack.enter_context(mock.patch.object(aiohttp, "ClientTimeout"))
        stack.enter_context(pytest.raises(errors.GatewayError, match="some reason"))
        logger = mock.Mock()
        log_filterer = mock.Mock()

        with stack:
            async with shard._GatewayTransport.connect(
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                logger=logger,
                url="https://some.url",
                log_filterer=log_filterer,
            ):
                hikari_test_helpers.raiser(errors.GatewayError("some reason"))

        mock_websocket.send_close.assert_awaited_once_with(
            code=errors.ShardCloseCode.UNEXPECTED_CONDITION, message=b"unexpected fatal client error :-("
        )

        sleep.assert_awaited_once_with(0.25)
        mock_client_session.assert_used_once()
        mock_websocket.assert_used_once()

    async def test_connect_when_unexpected_error_after_connecting(self, http_settings, proxy_settings):
        class MockWS(hikari_test_helpers.AsyncContextManagerMock, shard._GatewayTransport):
            closed = False
            send_close = mock.AsyncMock()
            sent_close = False

            def __init__(self):
                pass

        mock_websocket = MockWS()
        mock_client_session = hikari_test_helpers.AsyncContextManagerMock()
        mock_client_session.ws_connect = mock.MagicMock(return_value=mock_websocket)

        stack = contextlib.ExitStack()
        sleep = stack.enter_context(mock.patch.object(asyncio, "sleep"))
        stack.enter_context(mock.patch.object(aiohttp, "ClientSession", return_value=mock_client_session))
        stack.enter_context(mock.patch.object(aiohttp, "TCPConnector"))
        stack.enter_context(mock.patch.object(aiohttp, "ClientTimeout"))
        stack.enter_context(pytest.raises(errors.GatewayError, match="Unexpected ValueError: testing"))
        logger = mock.Mock()
        log_filterer = mock.Mock()

        with stack:
            async with shard._GatewayTransport.connect(
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                logger=logger,
                url="https://some.url",
                log_filterer=log_filterer,
            ):
                hikari_test_helpers.raiser(ValueError("testing"))

        mock_websocket.send_close.assert_awaited_once_with(
            code=errors.ShardCloseCode.UNEXPECTED_CONDITION, message=b"unexpected fatal client error :-("
        )

        sleep.assert_awaited_once_with(0.25)
        mock_client_session.assert_used_once()
        mock_websocket.assert_used_once()

    async def test_connect_when_no_error_and_not_closing(self, http_settings, proxy_settings):
        class MockWS(hikari_test_helpers.AsyncContextManagerMock, shard._GatewayTransport):
            closed = False
            _closing = False
            sent_close = False
            send_close = mock.AsyncMock()

            def __init__(self):
                pass

        mock_websocket = MockWS()
        mock_client_session = hikari_test_helpers.AsyncContextManagerMock()
        mock_client_session.ws_connect = mock.MagicMock(return_value=mock_websocket)

        stack = contextlib.ExitStack()
        sleep = stack.enter_context(mock.patch.object(asyncio, "sleep"))
        stack.enter_context(mock.patch.object(aiohttp, "ClientSession", return_value=mock_client_session))
        stack.enter_context(mock.patch.object(aiohttp, "TCPConnector"))
        stack.enter_context(mock.patch.object(aiohttp, "ClientTimeout"))
        logger = mock.Mock()
        log_filterer = mock.Mock()

        with stack:
            async with shard._GatewayTransport.connect(
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                logger=logger,
                url="https://some.url",
                log_filterer=log_filterer,
            ):
                pass

        mock_websocket.send_close.assert_awaited_once_with(
            code=shard._RESUME_CLOSE_CODE, message=b"client is shutting down"
        )

        sleep.assert_awaited_once_with(0.25)
        mock_client_session.assert_used_once()
        mock_websocket.assert_used_once()

    async def test_connect_when_no_error_and_closing(self, http_settings, proxy_settings):
        class MockWS(hikari_test_helpers.AsyncContextManagerMock, shard._GatewayTransport):
            closed = False
            _closing = True
            close = mock.AsyncMock()

            def __init__(self):
                pass

        mock_websocket = MockWS()
        mock_client_session = hikari_test_helpers.AsyncContextManagerMock()
        mock_client_session.ws_connect = mock.MagicMock(return_value=mock_websocket)

        stack = contextlib.ExitStack()
        sleep = stack.enter_context(mock.patch.object(asyncio, "sleep"))
        stack.enter_context(mock.patch.object(aiohttp, "ClientSession", return_value=mock_client_session))
        stack.enter_context(mock.patch.object(aiohttp, "TCPConnector"))
        stack.enter_context(mock.patch.object(aiohttp, "ClientTimeout"))
        logger = mock.Mock()
        log_filterer = mock.Mock()

        with stack:
            async with shard._GatewayTransport.connect(
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                logger=logger,
                url="https://some.url",
                log_filterer=log_filterer,
            ):
                pass

        mock_websocket.close.assert_not_called()

        sleep.assert_awaited_once_with(0.25)
        mock_client_session.assert_used_once()
        mock_websocket.assert_used_once()

    async def test_connect_when_error_connecting(self, http_settings, proxy_settings):
        mock_client_session = hikari_test_helpers.AsyncContextManagerMock()
        mock_client_session.ws_connect = mock.MagicMock(side_effect=aiohttp.ClientConnectionError("some error"))

        stack = contextlib.ExitStack()
        sleep = stack.enter_context(mock.patch.object(asyncio, "sleep"))
        stack.enter_context(mock.patch.object(aiohttp, "ClientSession", return_value=mock_client_session))
        stack.enter_context(mock.patch.object(aiohttp, "TCPConnector"))
        stack.enter_context(mock.patch.object(aiohttp, "ClientTimeout"))
        stack.enter_context(
            pytest.raises(
                errors.GatewayError, match=r"Failed to connect to Discord: ClientConnectionError\('some error'\)"
            )
        )
        logger = mock.Mock()
        log_filterer = mock.Mock()

        with stack:
            async with shard._GatewayTransport.connect(
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                logger=logger,
                url="https://some.url",
                log_filterer=log_filterer,
            ):
                pass

        sleep.assert_awaited_once_with(0.25)
        mock_client_session.assert_used_once()

    async def test_connect_when_handshake_error_with_unknown_reason(self, http_settings, proxy_settings):
        mock_client_session = hikari_test_helpers.AsyncContextManagerMock()
        mock_client_session.ws_connect = mock.MagicMock(
            side_effect=aiohttp.WSServerHandshakeError(
                status=123, message="some error", request_info=None, history=None
            )
        )

        stack = contextlib.ExitStack()
        sleep = stack.enter_context(mock.patch.object(asyncio, "sleep"))
        stack.enter_context(mock.patch.object(aiohttp, "ClientSession", return_value=mock_client_session))
        stack.enter_context(mock.patch.object(aiohttp, "TCPConnector"))
        stack.enter_context(mock.patch.object(aiohttp, "ClientTimeout"))
        stack.enter_context(
            pytest.raises(
                errors.GatewayError,
                match=(
                    r"Failed to connect to Discord: "
                    r"WSServerHandshakeError\(None, None, status=123, message='some error'\)"
                ),
            )
        )
        logger = mock.Mock()
        log_filterer = mock.Mock()

        with stack:
            async with shard._GatewayTransport.connect(
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                logger=logger,
                url="https://some.url",
                log_filterer=log_filterer,
            ):
                pass

        sleep.assert_awaited_once_with(0.25)
        mock_client_session.assert_used_once()

    async def test_connect_when_handshake_error_with_known_reason(self, http_settings, proxy_settings):
        mock_client_session = hikari_test_helpers.AsyncContextManagerMock()
        mock_client_session.ws_connect = mock.MagicMock(
            side_effect=aiohttp.WSServerHandshakeError(
                status=500, message="some error", request_info=None, history=None
            )
        )

        stack = contextlib.ExitStack()
        sleep = stack.enter_context(mock.patch.object(asyncio, "sleep"))
        stack.enter_context(mock.patch.object(aiohttp, "ClientSession", return_value=mock_client_session))
        stack.enter_context(mock.patch.object(aiohttp, "TCPConnector"))
        stack.enter_context(mock.patch.object(aiohttp, "ClientTimeout"))
        stack.enter_context(
            pytest.raises(
                errors.GatewayError,
                match=(
                    r"Failed to connect to Discord: WSServerHandshakeError"
                    r"\(None, None, status=500, message='some error'\)"
                ),
            )
        )
        logger = mock.Mock()
        log_filterer = mock.Mock()

        with stack:
            async with shard._GatewayTransport.connect(
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                logger=logger,
                url="https://some.url",
                log_filterer=log_filterer,
            ):
                pass

        sleep.assert_awaited_once_with(0.25)
        mock_client_session.assert_used_once()


@pytest.mark.asyncio
class TestGatewayShardImpl:
    @pytest.fixture()
    def client_session(self):
        stub = client_session_stub.ClientSessionStub()
        with mock.patch.object(aiohttp, "ClientSession", new=stub):
            yield stub

    @pytest.fixture(scope="module")
    def unslotted_client_type(self):
        return hikari_test_helpers.mock_class_namespace(shard.GatewayShardImpl, slots_=False)

    @pytest.fixture()
    def client(self, http_settings, proxy_settings, unslotted_client_type):
        return unslotted_client_type(
            url="wss://gateway.discord.gg",
            intents=intents.Intents.ALL,
            token="lol",
            event_consumer=mock.Mock(),
            http_settings=http_settings,
            proxy_settings=proxy_settings,
        )

    @pytest.mark.parametrize(
        ("compression", "expect"),
        [
            (None, f"v={shard._VERSION}&encoding=json"),
            ("payload_zlib_stream", f"v={shard._VERSION}&encoding=json&compress=zlib-stream"),
        ],
    )
    def test__init__sets_url_is_correct_json(self, compression, expect, http_settings, proxy_settings):
        g = shard.GatewayShardImpl(
            event_consumer=mock.Mock(),
            http_settings=http_settings,
            proxy_settings=proxy_settings,
            intents=intents.Intents.ALL,
            url="wss://gaytewhuy.discord.meh",
            data_format="json",
            compression=compression,
            token="12345",
        )

        assert g._url == f"wss://gaytewhuy.discord.meh?{expect}"

    def test_using_etf_is_unsupported(self, http_settings, proxy_settings):
        with pytest.raises(NotImplementedError, match="Unsupported gateway data format: etf"):
            shard.GatewayShardImpl(
                event_consumer=mock.Mock(),
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                token=mock.Mock(),
                url="wss://erlpack-is-broken-lol.discord.meh",
                intents=intents.Intents.ALL,
                data_format="etf",
                compression=True,
            )

    def test_heartbeat_latency_property(self, client):
        client._heartbeat_latency = 420
        assert client.heartbeat_latency == 420

    def test_id_property(self, client):
        client._shard_id = 101
        assert client.id == 101

    def test_intents_property(self, client):
        intents = object()
        client._intents = intents
        assert client.intents is intents

    @pytest.mark.parametrize(
        ("run_task", "expected"),
        [
            (None, False),
            (asyncio.get_event_loop().create_future(), True),
            (aio.completed_future(), False),
        ],
    )
    def test_is_alive_property(self, run_task, expected, client):
        client._run_task = run_task
        assert client.is_alive is expected

    def test_shard_count_property(self, client):
        client._shard_count = 69
        assert client.shard_count == 69

    async def test_close_when_closing_set(self, client):
        client._closing = mock.Mock(is_set=mock.Mock(return_value=True))
        client._ws = mock.Mock()
        client._chunking_rate_limit = mock.Mock()
        client._total_rate_limit = mock.Mock()

        await client.close()

        client._closing.set.assert_not_called()
        client._ws.close.assert_not_called()
        client._chunking_rate_limit.close.assert_not_called()
        client._total_rate_limit.close.assert_not_called()

    async def test_close_when_closing_not_set(self, client):
        client._closing = mock.Mock(is_set=mock.Mock(return_value=False))
        client._ws = mock.Mock(close=mock.AsyncMock())
        client._chunking_rate_limit = mock.Mock()
        client._total_rate_limit = mock.Mock()

        await client.close()

        client._closing.set.assert_called_once_with()
        client._ws.close.assert_awaited_once_with(code=errors.ShardCloseCode.GOING_AWAY, message=b"shard disconnecting")
        client._chunking_rate_limit.close.assert_called_once_with()
        client._total_rate_limit.close.assert_called_once_with()

    async def test_close_when_closing_not_set_and_ws_is_None(self, client):
        client._closing = mock.Mock(is_set=mock.Mock(return_value=False))
        client._ws = None
        client._chunking_rate_limit = mock.Mock()
        client._total_rate_limit = mock.Mock()

        await client.close()

        client._closing.set.assert_called_once_with()
        client._chunking_rate_limit.close.assert_called_once_with()
        client._total_rate_limit.close.assert_called_once_with()

    async def test_when__user_id_is_None(self, client):
        client._handshake_completed = mock.Mock(wait=mock.AsyncMock())
        client._user_id = None
        with pytest.raises(RuntimeError):
            assert await client.get_user_id()

    async def test_when__user_id_is_not_None(self, client):
        client._handshake_completed = mock.Mock(wait=mock.AsyncMock())
        client._user_id = 123
        assert await client.get_user_id() == 123

    async def test_join(self, client):
        client._closed = mock.Mock(wait=mock.AsyncMock())

        await client.join()

        client._closed.wait.assert_awaited_once_with()

    async def test_request_guild_members_when_no_query_and_no_limit_and_GUILD_MEMBERS_not_enabled(self, client):
        client._intents = intents.Intents.GUILD_INTEGRATIONS

        with pytest.raises(errors.MissingIntentError):
            await client.request_guild_members(123, query="", limit=0)

    async def test_request_guild_members_when_presences_and_GUILD_PRESENCES_not_enabled(self, client):
        client._intents = intents.Intents.GUILD_INTEGRATIONS

        with pytest.raises(errors.MissingIntentError):
            await client.request_guild_members(123, query="test", limit=1, include_presences=True)

    @pytest.mark.parametrize("kwargs", [{"query": "some query"}, {"limit": 1}])
    async def test_request_guild_members_when_specifiying_users_with_limit_or_query(self, client, kwargs):
        client._intents = intents.Intents.GUILD_INTEGRATIONS

        with pytest.raises(ValueError, match="Cannot specify limit/query with users"):
            await client.request_guild_members(123, users=[], **kwargs)

    @pytest.mark.parametrize("limit", [-1, 101])
    async def test_request_guild_members_when_limit_under_0_or_over_100(self, client, limit):
        client._intents = intents.Intents.ALL

        with pytest.raises(ValueError, match="'limit' must be between 0 and 100, both inclusive"):
            await client.request_guild_members(123, limit=limit)

    async def test_request_guild_members_when_users_over_100(self, client):
        client._intents = intents.Intents.ALL

        with pytest.raises(ValueError, match="'users' is limited to 100 users"):
            await client.request_guild_members(123, users=range(101))

    async def test_request_guild_members_when_nonce_over_32_chars(self, client):
        client._intents = intents.Intents.ALL

        with pytest.raises(ValueError, match="'nonce' can be no longer than 32 byte characters long."):
            await client.request_guild_members(123, nonce="x" * 33)

    @pytest.mark.parametrize("include_presences", [True, False])
    async def test_request_guild_members(self, client, include_presences):
        client._intents = intents.Intents.ALL
        client._ws = mock.Mock(send_json=mock.AsyncMock())

        await client.request_guild_members(123, include_presences=include_presences)

        client._ws.send_json.assert_awaited_once_with(
            {
                "op": 8,
                "d": {"guild_id": "123", "query": "", "presences": include_presences, "limit": 0},
            }
        )

    async def test_start_when_already_running(self, client):
        client._run_task = object()

        with pytest.raises(RuntimeError, match="Cannot run more than one instance of one shard concurrently"):
            await client.start()

    async def test_start_when_shard_closed_before_starting(self, client):
        client._run_task = None
        client._shard_id = 20
        client._run = mock.Mock()
        client._handshake_completed = mock.Mock(wait=mock.Mock())
        run_task = mock.Mock()
        waiter = mock.Mock()

        stack = contextlib.ExitStack()
        create_task = stack.enter_context(mock.patch.object(asyncio, "create_task", side_effect=[run_task, waiter]))
        wait = stack.enter_context(mock.patch.object(asyncio, "wait", return_value=([run_task], [waiter])))
        stack.enter_context(
            pytest.raises(asyncio.CancelledError, match="Shard 20 was closed before it could start successfully")
        )

        with stack:
            await client.start()

        assert client._run_task is None

        assert create_task.call_count == 2
        create_task.has_call(mock.call(client._run(), name="run shard 20"))
        create_task.has_call(mock.call(client._handshake_completed.wait(), name="wait for shard 20 to start"))

        run_task.result.assert_called_once_with()
        waiter.cancel.assert_called_once_with()
        wait.assert_awaited_once_with((waiter, run_task), return_when=asyncio.FIRST_COMPLETED)

    async def test_start(self, client):
        client._run_task = None
        client._shard_id = 20
        client._run = mock.Mock()
        client._handshake_completed = mock.Mock(wait=mock.Mock())
        run_task = mock.Mock()
        waiter = mock.Mock()

        with mock.patch.object(asyncio, "create_task", side_effect=[run_task, waiter]) as create_task:
            with mock.patch.object(asyncio, "wait", return_value=([waiter], [run_task])) as wait:
                await client.start()

        assert client._run_task == run_task

        assert create_task.call_count == 2
        create_task.has_call(mock.call(client._run(), name="run shard 20"))
        create_task.has_call(mock.call(client._handshake_completed.wait(), name="wait for shard 20 to start"))

        run_task.result.assert_not_called()
        waiter.cancel.assert_called_once_with()
        wait.assert_awaited_once_with((waiter, run_task), return_when=asyncio.FIRST_COMPLETED)

    async def test_update_presence(self, client):
        presence_payload = object()
        client._ws = mock.Mock(send_json=mock.AsyncMock())
        client._serialize_and_store_presence_payload = mock.Mock(return_value=presence_payload)
        client._send_json = mock.AsyncMock()

        await client.update_presence(
            idle_since=datetime.datetime.now(),
            afk=True,
            status=presences.Status.IDLE,
            activity=None,
        )

        client._ws.send_json.assert_awaited_once_with({"op": 3, "d": presence_payload})

    @pytest.mark.parametrize("channel", [12345, None])
    @pytest.mark.parametrize("self_deaf", [True, False])
    @pytest.mark.parametrize("self_mute", [True, False])
    async def test_update_voice_state(self, client, channel, self_deaf, self_mute):
        client._ws = mock.Mock(send_json=mock.AsyncMock())
        payload = {
            "channel_id": str(channel) if channel is not None else None,
            "guild_id": "6969420",
            "deaf": self_deaf,
            "mute": self_mute,
        }

        await client.update_voice_state("6969420", channel, self_mute=self_mute, self_deaf=self_deaf)

        client._ws.send_json.assert_awaited_once_with({"op": 4, "d": payload})

    def test_dispatch_when_READY(self, client):
        client._seq = 0
        client._session_id = 0
        client._user_id = 0
        client._logger = mock.Mock()
        client._handshake_completed = mock.Mock()
        client._event_consumer = mock.Mock()

        pl = {
            "session_id": 101,
            "user": {"id": 123, "username": "hikari", "discriminator": "5863"},
            "guilds": [
                {"id": "123"},
                {"id": "456"},
                {"id": "789"},
            ],
            "v": 8,
        }

        client._dispatch(
            "READY",
            10,
            pl,
        )

        assert client._seq == 10
        assert client._session_id == 101
        assert client._user_id == 123
        client._logger.info.assert_called_once_with(
            "shard is ready: %s guilds, %s (%s), session %r on v%s gateway",
            3,
            "hikari#5863",
            123,
            101,
            8,
        )
        client._handshake_completed.set.assert_called_once_with()
        client._event_consumer.assert_called_once_with(
            client,
            "READY",
            pl,
        )

    def test__dipatch_when_RESUME(self, client):
        client._seq = 0
        client._session_id = 123
        client._logger = mock.Mock()
        client._handshake_completed = mock.Mock()
        client._event_consumer = mock.Mock()

        client._dispatch("RESUME", 10, {})

        assert client._seq == 10
        client._logger.info.assert_called_once_with("shard has resumed [session:%s, seq:%s]", 123, 10)
        client._handshake_completed.set.assert_called_once_with()
        client._event_consumer.assert_called_once_with(client, "RESUME", {})

    def test__dipatch(self, client):
        client._logger = mock.Mock()
        client._handshake_completed = mock.Mock()
        client._event_consumer = mock.Mock()

        client._dispatch("EVENT NAME", 10, {"payload": None})

        client._logger.info.assert_not_called()
        client._handshake_completed.set.assert_not_called()
        client._event_consumer.assert_called_once_with(client, "EVENT NAME", {"payload": None})

    async def test__identify(self, client):
        client._token = "token"
        client._intents = intents.Intents.ALL
        client._large_threshold = 123
        client._shard_id = 0
        client._shard_count = 1
        client._serialize_and_store_presence_payload = mock.Mock(return_value={"presence": "payload"})
        client._ws = mock.Mock(send_json=mock.AsyncMock())
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(platform, "system", return_value="Potato PC"))
        stack.enter_context(mock.patch.object(platform, "architecture", return_value=["ARM64"]))
        stack.enter_context(mock.patch.object(aiohttp, "__version__", new="v0.0.1"))
        stack.enter_context(mock.patch.object(_about, "__version__", new="v1.0.0"))

        with stack:
            await client._identify()

        expected_json = {
            "op": 2,
            "d": {
                "token": "token",
                "compress": False,
                "large_threshold": 123,
                "properties": {
                    "$os": "Potato PC ARM64",
                    "$browser": "aiohttp v0.0.1",
                    "$device": "hikari v1.0.0",
                },
                "shard": [0, 1],
                "intents": 32767,
                "presence": {"presence": "payload"},
            },
        }
        client._ws.send_json.assert_awaited_once_with(expected_json)

    @hikari_test_helpers.timeout()
    async def test__heartbeat(self, client):
        client._last_heartbeat_sent = 5
        client._logger = mock.Mock()
        client._closing = mock.Mock(is_set=mock.Mock(return_value=False))
        client._closed = mock.Mock(is_set=mock.Mock(return_value=False))
        client._send_heartbeat = mock.AsyncMock()

        with mock.patch.object(time, "monotonic", return_value=10):
            with mock.patch.object(asyncio, "wait_for", side_effect=[asyncio.TimeoutError, None]) as wait_for:
                assert await client._heartbeat(20) is False

        wait_for.assert_awaited_with(client._closing.wait(), timeout=20)

    @hikari_test_helpers.timeout()
    async def test__heartbeat_when_zombie(self, client):
        client._last_heartbeat_sent = 10
        client._logger = mock.Mock()

        with mock.patch.object(time, "monotonic", return_value=5):
            with mock.patch.object(asyncio, "wait_for") as wait_for:
                assert await client._heartbeat(20) is True

        wait_for.assert_not_called()

    async def test__resume(self, client):
        client._token = "token"
        client._seq = 123
        client._session_id = 456
        client._ws = mock.Mock(send_json=mock.AsyncMock())

        await client._resume()

        expected_json = {
            "op": 6,
            "d": {"token": "token", "seq": 123, "session_id": 456},
        }
        client._ws.send_json.assert_awaited_once_with(expected_json)

    @pytest.mark.skip("TODO")
    async def test__run(self, client):
        ...

    @pytest.mark.skip("TODO")
    async def test__run_once(self, client):
        ...

    async def test__send_heartbeat(self, client):
        client._ws = mock.Mock(send_json=mock.AsyncMock())
        client._last_heartbeat_sent = 0
        client._seq = 10

        with mock.patch.object(time, "monotonic", return_value=200):
            await client._send_heartbeat()

        client._ws.send_json.assert_awaited_once_with({"op": 1, "d": 10})
        assert client._last_heartbeat_sent == 200

    async def test__send_heartbeat_ack(self, client):
        client._ws = mock.Mock(send_json=mock.AsyncMock())

        await client._send_heartbeat_ack()

        client._ws.send_json.assert_awaited_once_with({"op": 11, "d": None})

    def test__serialize_activity_when_activity_is_None(self, client):
        assert client._serialize_activity(None) is None

    def test__serialize_activity_when_activity_is_not_None(self, client):
        activity = mock.Mock(type="0", url="https://some.url")
        activity.name = "some name"  # This has to be set seperate because if not, its set as the mock's name
        assert client._serialize_activity(activity) == {"name": "some name", "type": 0, "url": "https://some.url"}

    @pytest.mark.parametrize("idle_since", [datetime.datetime.now(), None])
    @pytest.mark.parametrize("afk", [True, False])
    @pytest.mark.parametrize(
        "status",
        [presences.Status.DO_NOT_DISTURB, presences.Status.IDLE, presences.Status.ONLINE, presences.Status.OFFLINE],
    )
    @pytest.mark.parametrize("activity", [presences.Activity(name="foo"), None])
    def test__serialize_and_store_presence_payload_when_all_args_undefined(
        self, client, idle_since, afk, status, activity
    ):
        client._activity = activity
        client._idle_since = idle_since
        client._is_afk = afk
        client._status = status

        actual_result = client._serialize_and_store_presence_payload()

        if activity is not undefined.UNDEFINED and activity is not None:
            expected_activity = {
                "name": activity.name,
                "type": activity.type,
                "url": activity.url,
            }
        else:
            expected_activity = None

        if status == presences.Status.OFFLINE:
            expected_status = "invisible"
        else:
            expected_status = status.value

        expected_result = {
            "game": expected_activity,
            "since": int(idle_since.timestamp() * 1_000) if idle_since is not None else None,
            "afk": afk if afk is not undefined.UNDEFINED else False,
            "status": expected_status,
        }

        assert expected_result == actual_result

    @pytest.mark.parametrize("idle_since", [datetime.datetime.now(), None])
    @pytest.mark.parametrize("afk", [True, False])
    @pytest.mark.parametrize(
        "status",
        [presences.Status.DO_NOT_DISTURB, presences.Status.IDLE, presences.Status.ONLINE, presences.Status.OFFLINE],
    )
    @pytest.mark.parametrize("activity", [presences.Activity(name="foo"), None])
    def test__serialize_and_store_presence_payload_sets_state(self, client, idle_since, afk, status, activity):
        client._serialize_and_store_presence_payload(idle_since=idle_since, afk=afk, status=status, activity=activity)

        assert client._activity == activity
        assert client._idle_since == idle_since
        assert client._is_afk == afk
        assert client._status == status

    def test__serialize_datetime_when_datetime_is_None(self, client):
        assert client._serialize_datetime(None) is None

    def test__serialize_datetime_when_datetime_is_not_None(self, client):
        dt = datetime.datetime(2004, 11, 22, tzinfo=datetime.timezone.utc)
        assert client._serialize_datetime(dt) == 1101081600000
