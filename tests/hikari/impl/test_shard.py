# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
import re

import aiohttp
import mock
import pytest

from hikari import _about
from hikari import errors
from hikari import intents
from hikari import presences
from hikari import urls
from hikari.impl import config
from hikari.impl import shard
from hikari.internal import aio
from hikari.internal import net
from hikari.internal import time
from hikari.internal import ux
from tests.hikari import hikari_test_helpers


def test_log_filterer():
    filterer = shard._log_filterer("TOKEN")

    returned = filterer("this log contains the TOKEN and it should get removed and the TOKEN here too")
    assert returned == (
        "this log contains the **REDACTED TOKEN** and it should get removed and the **REDACTED TOKEN** here too"
    )


def test__serialize_activity_when_activity_is_None():
    assert shard._serialize_activity(None) is None


def test__serialize_activity_when_activity_is_not_None():
    activity = presences.Activity(name="some name", type=0, state="blah", url="https://some.url")
    assert shard._serialize_activity(activity) == {
        "name": "some name",
        "type": 0,
        "state": "blah",
        "url": "https://some.url",
    }


@pytest.mark.parametrize(
    ("activity_name", "activity_state", "expected_name", "expected_state"),
    [("Testing!", None, "Custom Status", "Testing!"), ("Blah name!", "Testing!", "Blah name!", "Testing!")],
)
def test__serialize_activity_custom_activity_syntactic_sugar(
    activity_name, activity_state, expected_name, expected_state
):
    activity = presences.Activity(name=activity_name, state=activity_state, type=presences.ActivityType.CUSTOM)

    assert shard._serialize_activity(activity) == {
        "type": 4,
        "name": expected_name,
        "state": expected_state,
        "url": None,
    }


def test__serialize_datetime_when_datetime_is_None():
    assert shard._serialize_datetime(None) is None


def test__serialize_datetime_when_datetime_is_not_None():
    dt = datetime.datetime(2004, 11, 22, tzinfo=datetime.timezone.utc)
    assert shard._serialize_datetime(dt) == 1101081600000


@pytest.fixture()
def http_settings():
    return mock.Mock(spec_set=config.HTTPSettings)


@pytest.fixture()
def proxy_settings():
    return mock.Mock(spec_set=config.ProxySettings)


class StubResponse:
    def __init__(self, *, type=None, data=None, extra=None):
        self.type = type
        self.data = data
        self.extra = extra


class TestGatewayTransport:
    @pytest.fixture()
    def transport_impl(self):
        return shard._GatewayTransport(
            ws=mock.Mock(),
            exit_stack=mock.AsyncMock(),
            logger=mock.Mock(),
            log_filterer=mock.Mock(),
            loads=mock.Mock(),
            dumps=mock.Mock(),
            transport_compression=True,
        )

    def test_init_when_transport_compression(self):
        transport = shard._GatewayTransport(
            ws=mock.Mock(),
            exit_stack=mock.AsyncMock(),
            logger=mock.Mock(),
            log_filterer=mock.Mock(),
            loads=mock.Mock(),
            dumps=mock.Mock(),
            transport_compression=True,
        )

        assert transport._receive_and_check == transport._receive_and_check_zlib

    def test_init_when_no_transport_compression(self):
        transport = shard._GatewayTransport(
            ws=mock.Mock(),
            exit_stack=mock.AsyncMock(),
            logger=mock.Mock(isEnabledFor=mock.Mock(return_value=False)),
            log_filterer=mock.Mock(),
            loads=mock.Mock(),
            dumps=mock.Mock(),
            transport_compression=False,
        )

        assert transport._receive_and_check == transport._receive_and_check_text

    @pytest.mark.asyncio()
    async def test_send_close(self, transport_impl):
        transport_impl._sent_close = False

        with mock.patch.object(asyncio, "wait_for", return_value=mock.AsyncMock()) as wait_for:
            with mock.patch.object(asyncio, "sleep") as sleep:
                await transport_impl.send_close(code=1234, message=b"some message")

        wait_for.assert_awaited_once_with(transport_impl._ws.close.return_value, timeout=5)
        transport_impl._ws.close.assert_called_once_with(code=1234, message=b"some message")
        transport_impl._exit_stack.aclose.assert_awaited_once_with()
        sleep.assert_awaited_once_with(0.25)

    @pytest.mark.asyncio()
    async def test_send_close_when_TimeoutError(self, transport_impl):
        transport_impl._sent_close = False
        transport_impl._ws.close.side_effect = asyncio.TimeoutError

        with mock.patch.object(asyncio, "sleep") as sleep:
            await transport_impl.send_close(code=1234, message=b"some message")

        transport_impl._ws.close.assert_called_once_with(code=1234, message=b"some message")
        transport_impl._exit_stack.aclose.assert_awaited_once_with()
        sleep.assert_awaited_once_with(0.25)

    @pytest.mark.asyncio()
    async def test_send_close_when_already_sent(self, transport_impl):
        transport_impl._sent_close = True

        with mock.patch.object(aiohttp.ClientWebSocketResponse, "close", side_effect=asyncio.TimeoutError) as close:
            await transport_impl.send_close(code=1234, message=b"some message")

        close.assert_not_called()

    @pytest.mark.asyncio()
    @pytest.mark.parametrize("trace", [True, False])
    async def test_receive_json(self, transport_impl, trace):
        transport_impl._receive_and_check = mock.AsyncMock()
        transport_impl._logger = mock.Mock(enabled_for=mock.Mock(return_value=trace))

        assert await transport_impl.receive_json() == transport_impl._loads.return_value

        transport_impl._receive_and_check.assert_awaited_once_with()
        transport_impl._loads.assert_called_once_with(transport_impl._receive_and_check.return_value)

    @pytest.mark.asyncio()
    @pytest.mark.parametrize("trace", [True, False])
    async def test_send_json(self, transport_impl, trace):
        transport_impl._ws.send_bytes = mock.AsyncMock()
        transport_impl._logger = mock.Mock(enabled_for=mock.Mock(return_value=trace))
        transport_impl._dumps = mock.Mock(return_value=b"some data")

        await transport_impl.send_json({"json_send": None})

        transport_impl._ws.send_bytes.assert_awaited_once_with(b"some data")

    @pytest.mark.asyncio()
    async def test__handle_other_message_when_TEXT(self, transport_impl):
        stub_response = StubResponse(type=aiohttp.WSMsgType.TEXT)

        with pytest.raises(errors.GatewayError, match="Unexpected message type received TEXT, expected BINARY"):
            transport_impl._handle_other_message(stub_response)

    @pytest.mark.asyncio()
    async def test__handle_other_message_when_BINARY(self, transport_impl):
        stub_response = StubResponse(type=aiohttp.WSMsgType.BINARY)

        with pytest.raises(errors.GatewayError, match="Unexpected message type received BINARY, expected TEXT"):
            transport_impl._handle_other_message(stub_response)

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
    def test__handle_other_message_when_message_type_is_CLOSE_and_should_reconnect(self, code, transport_impl):
        stub_response = StubResponse(type=aiohttp.WSMsgType.CLOSE, extra="some error extra", data=code)

        with pytest.raises(errors.GatewayServerClosedConnectionError) as exinfo:
            transport_impl._handle_other_message(stub_response)

        exception = exinfo.value
        assert exception.reason == "some error extra"
        assert exception.code == int(code)
        assert exception.can_reconnect is True

    @pytest.mark.parametrize("code", [*range(4010, 4020), 5000])
    def test__handle_other_message_when_message_type_is_CLOSE_and_should_not_reconnect(self, code, transport_impl):
        stub_response = StubResponse(type=aiohttp.WSMsgType.CLOSE, extra="don't reconnect", data=code)

        with pytest.raises(errors.GatewayServerClosedConnectionError) as exinfo:
            transport_impl._handle_other_message(stub_response)

        exception = exinfo.value
        assert exception.reason == "don't reconnect"
        assert exception.code == int(code)
        assert exception.can_reconnect is False

    def test__handle_other_message_when_message_type_is_CLOSING(self, transport_impl):
        stub_response = StubResponse(type=aiohttp.WSMsgType.CLOSING)

        with pytest.raises(errors.GatewayError, match="Socket has closed"):
            transport_impl._handle_other_message(stub_response)

    def test__handle_other_message_when_message_type_is_CLOSED(self, transport_impl):
        stub_response = StubResponse(type=aiohttp.WSMsgType.CLOSED)

        with pytest.raises(errors.GatewayError, match="Socket has closed"):
            transport_impl._handle_other_message(stub_response)

    def test__handle_other_message_when_message_type_is_unknown(self, transport_impl):
        stub_response = mock.AsyncMock(return_value=StubResponse(type=aiohttp.WSMsgType.ERROR))
        exception = Exception("some error")
        transport_impl._ws.exception = mock.Mock(return_value=exception)

        with pytest.raises(errors.GatewayError, match="Unexpected websocket exception from gateway") as exc_info:
            transport_impl._handle_other_message(stub_response)

        assert exc_info.value.__cause__ is exception

    @pytest.mark.asyncio()
    async def test__receive_and_check_text_when_message_type_is_TEXT(self, transport_impl):
        transport_impl._ws.receive = mock.AsyncMock(
            return_value=StubResponse(type=aiohttp.WSMsgType.TEXT, data="some text")
        )

        assert await transport_impl._receive_and_check_text() == "some text"

        transport_impl._ws.receive.assert_awaited_once_with()

    @pytest.mark.asyncio()
    async def test__receive_and_check_text_when_message_type_is_unknown(self, transport_impl):
        mock_exception = errors.GatewayError("aye")
        transport_impl._ws.receive = mock.AsyncMock(return_value=StubResponse(type=aiohttp.WSMsgType.BINARY))

        with mock.patch.object(
            shard._GatewayTransport, "_handle_other_message", side_effect=mock_exception
        ) as handle_other_message:
            with pytest.raises(errors.GatewayError) as exc_info:
                await transport_impl._receive_and_check_text()

        assert exc_info.value is mock_exception
        transport_impl._ws.receive.assert_awaited_once_with()
        handle_other_message.assert_called_once_with(transport_impl._ws.receive.return_value)

    @pytest.mark.asyncio()
    async def test__receive_and_check_zlib_when_message_type_is_BINARY(self, transport_impl):
        response = StubResponse(type=aiohttp.WSMsgType.BINARY, data=b"some initial data")
        transport_impl._ws.receive = mock.AsyncMock(return_value=response)

        with mock.patch.object(
            shard._GatewayTransport, "_receive_and_check_complete_zlib_package"
        ) as receive_and_check_complete_zlib_package:
            assert (
                await transport_impl._receive_and_check_zlib() is receive_and_check_complete_zlib_package.return_value
            )

        transport_impl._ws.receive.assert_awaited_once_with()
        receive_and_check_complete_zlib_package.assert_awaited_once_with(b"some initial data")

    @pytest.mark.asyncio()
    async def test__receive_and_check_zlib_when_message_type_is_BINARY_and_the_full_payload(self, transport_impl):
        response = StubResponse(type=aiohttp.WSMsgType.BINARY, data=b"some initial data\x00\x00\xff\xff")
        transport_impl._ws.receive = mock.AsyncMock(return_value=response)
        transport_impl._zlib = mock.Mock(decompress=mock.Mock(return_value=b"aaaaaaaaaaaaaaaaaa"))

        assert await transport_impl._receive_and_check_zlib() == "aaaaaaaaaaaaaaaaaa"

        transport_impl._ws.receive.assert_awaited_once_with()
        transport_impl._zlib.decompress.assert_called_once_with(response.data)

    @pytest.mark.asyncio()
    async def test__receive_and_check_zlib_when_message_type_is_unknown(self, transport_impl):
        mock_exception = errors.GatewayError("aye")
        transport_impl._ws.receive = mock.AsyncMock(return_value=StubResponse(type=aiohttp.WSMsgType.TEXT))

        with mock.patch.object(
            shard._GatewayTransport, "_handle_other_message", side_effect=mock_exception
        ) as handle_other_message:
            with pytest.raises(errors.GatewayError) as exc_info:
                await transport_impl._receive_and_check_zlib()

        assert exc_info.value is mock_exception
        transport_impl._ws.receive.assert_awaited_once_with()
        handle_other_message.assert_called_once_with(transport_impl._ws.receive.return_value)

    @pytest.mark.asyncio()
    async def test__receive_and_check_complete_zlib_package_for_unexpected_message_type(self, transport_impl):
        mock_exception = errors.GatewayError("aye")
        response = StubResponse(type=aiohttp.WSMsgType.TEXT)
        transport_impl._ws.receive = mock.AsyncMock(return_value=response)

        with mock.patch.object(
            shard._GatewayTransport, "_handle_other_message", side_effect=mock_exception
        ) as handle_other_message:
            with pytest.raises(errors.GatewayError) as exc_info:
                await transport_impl._receive_and_check_complete_zlib_package(b"some")

        assert exc_info.value is mock_exception
        transport_impl._ws.receive.assert_awaited_with()
        handle_other_message.assert_called_once_with(response)

    @pytest.mark.asyncio()
    async def test__receive_and_check_complete_zlib_package(self, transport_impl):
        response1 = StubResponse(type=aiohttp.WSMsgType.BINARY, data=b"more")
        response2 = StubResponse(type=aiohttp.WSMsgType.BINARY, data=b"data")
        response3 = StubResponse(type=aiohttp.WSMsgType.BINARY, data=b"\x00\x00\xff\xff")
        transport_impl._ws.receive = mock.AsyncMock(side_effect=[response1, response2, response3])
        transport_impl._zlib = mock.Mock(decompress=mock.Mock(return_value=b"decoded utf-8 encoded bytes"))

        assert await transport_impl._receive_and_check_complete_zlib_package(b"some") == "decoded utf-8 encoded bytes"

        assert transport_impl._ws.receive.call_count == 3
        transport_impl._ws.receive.assert_has_awaits([mock.call(), mock.call(), mock.call()])
        transport_impl._zlib.decompress.assert_called_once_with(bytearray(b"somemoredata\x00\x00\xff\xff"))

    @pytest.mark.parametrize("transport_compression", [True, False])
    @pytest.mark.asyncio()
    async def test_connect(self, http_settings, proxy_settings, transport_compression):
        logger = mock.Mock()
        log_filterer = mock.Mock()
        client_session = mock.Mock()
        websocket = mock.Mock()
        loads = mock.Mock()
        dumps = mock.Mock()
        exit_stack = mock.AsyncMock(enter_async_context=mock.AsyncMock(side_effect=[client_session, websocket]))

        stack = contextlib.ExitStack()
        sleep = stack.enter_context(mock.patch.object(asyncio, "sleep"))
        create_tcp_connector = stack.enter_context(mock.patch.object(net, "create_tcp_connector"))
        create_client_session = stack.enter_context(mock.patch.object(net, "create_client_session"))
        stack.enter_context(mock.patch.object(contextlib, "AsyncExitStack", return_value=exit_stack))

        with stack:
            ws = await shard._GatewayTransport.connect(
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                logger=logger,
                url="testing.com",
                log_filterer=log_filterer,
                loads=loads,
                dumps=dumps,
                transport_compression=transport_compression,
            )

        assert isinstance(ws, shard._GatewayTransport)
        assert ws._ws is websocket
        assert ws._exit_stack is exit_stack
        assert ws._logger is logger
        assert ws._log_filterer is log_filterer
        assert ws._loads is loads
        assert ws._dumps is dumps

        if transport_compression:
            assert ws._receive_and_check == ws._receive_and_check_zlib
        else:
            assert ws._receive_and_check == ws._receive_and_check_text

        assert exit_stack.enter_async_context.call_count == 2
        exit_stack.enter_async_context.assert_has_calls(
            [mock.call(create_client_session.return_value), mock.call(client_session.ws_connect.return_value)]
        )

        create_tcp_connector.assert_called_once_with(http_settings=http_settings, dns_cache=False, limit=1)
        create_client_session.assert_called_once_with(
            connector=create_tcp_connector.return_value,
            connector_owner=True,
            raise_for_status=True,
            http_settings=http_settings,
            trust_env=proxy_settings.trust_env,
        )
        client_session.ws_connect.assert_called_once_with(
            max_msg_size=0,
            proxy=proxy_settings.url,
            proxy_headers=proxy_settings.headers,
            url="testing.com",
            autoclose=False,
        )
        exit_stack.aclose.assert_not_called()
        sleep.assert_not_called()

    @pytest.mark.asyncio()
    async def test_connect_when_error_while_connecting(self, http_settings, proxy_settings):
        logger = mock.Mock()
        log_filterer = mock.Mock()
        client_session = mock.Mock()
        websocket = mock.Mock()
        exit_stack = mock.AsyncMock(enter_async_context=mock.AsyncMock(side_effect=[client_session, websocket]))

        stack = contextlib.ExitStack()
        sleep = stack.enter_context(mock.patch.object(asyncio, "sleep"))
        stack.enter_context(mock.patch.object(net, "create_tcp_connector", side_effect=RuntimeError))
        stack.enter_context(mock.patch.object(contextlib, "AsyncExitStack", return_value=exit_stack))
        stack.enter_context(pytest.raises(RuntimeError))

        with stack:
            await shard._GatewayTransport.connect(
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                logger=logger,
                url="https://some.url",
                log_filterer=log_filterer,
                loads=object(),
                dumps=object(),
                transport_compression=True,
            )

        exit_stack.aclose.assert_awaited_once_with()
        sleep.assert_awaited_once_with(0.25)

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        ("error", "reason"),
        [
            (
                aiohttp.WSServerHandshakeError(status=123, message="some error", request_info=None, history=None),
                "WSServerHandshakeError(None, None, status=123, message='some error')",
            ),
            (aiohttp.ClientOSError("some os error"), "some os error"),
            (aiohttp.ClientConnectionError("some error"), "some error"),
            (asyncio.TimeoutError("some error"), "Timeout exceeded"),
        ],
    )
    async def test_connect_when_expected_error_while_connecting(self, http_settings, proxy_settings, error, reason):
        logger = mock.Mock()
        log_filterer = mock.Mock()
        client_session = mock.Mock()
        websocket = mock.Mock()
        exit_stack = mock.AsyncMock(enter_async_context=mock.AsyncMock(side_effect=[client_session, websocket]))

        stack = contextlib.ExitStack()
        sleep = stack.enter_context(mock.patch.object(asyncio, "sleep"))
        stack.enter_context(mock.patch.object(net, "create_tcp_connector", side_effect=error))
        stack.enter_context(mock.patch.object(contextlib, "AsyncExitStack", return_value=exit_stack))
        stack.enter_context(
            pytest.raises(errors.GatewayConnectionError, match=re.escape(f"Failed to connect to server: {reason!r}"))
        )

        with stack:
            await shard._GatewayTransport.connect(
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                logger=logger,
                url="https://some.url",
                log_filterer=log_filterer,
                transport_compression=True,
                loads=object(),
                dumps=object(),
            )

        exit_stack.aclose.assert_awaited_once_with()
        sleep.assert_awaited_once_with(0.25)


@pytest.fixture()
def client(http_settings, proxy_settings):
    return shard.GatewayShardImpl(
        event_manager=mock.Mock(),
        event_factory=mock.Mock(),
        url="wss://gateway.discord.gg",
        intents=intents.Intents.ALL,
        token="lol",
        http_settings=http_settings,
        proxy_settings=proxy_settings,
    )


class TestGatewayShardImpl:
    def test__init__when_unsupported_compression_format(self):
        with pytest.raises(NotImplementedError, match=r"Unsupported compression format something"):
            shard.GatewayShardImpl(
                event_manager=mock.Mock(),
                event_factory=mock.Mock(),
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                intents=intents.Intents.ALL,
                url="wss://gaytewhuy.discord.meh",
                data_format="json",
                compression="something",
                token="12345",
            )

    def test_using_etf_is_unsupported(self, http_settings, proxy_settings):
        with pytest.raises(NotImplementedError, match="Unsupported gateway data format: etf"):
            shard.GatewayShardImpl(
                event_manager=mock.Mock(),
                event_factory=mock.Mock(),
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                token=mock.Mock(),
                url="wss://erlpack-is-broken-lol.discord.meh",
                intents=intents.Intents.ALL,
                data_format="etf",
                compression="testing",
            )

    def test_heartbeat_latency_property(self, client):
        client._heartbeat_latency = 420
        assert client.heartbeat_latency == 420

    def test_id_property(self, client):
        client._shard_id = 101
        assert client.id == 101

    def test_intents_property(self, client):
        mock_intents = object()
        client._intents = mock_intents
        assert client.intents is mock_intents

    @pytest.mark.parametrize(("keep_alive_task", "expected"), [(None, False), ("some", True)])
    def test_is_alive_property(self, client, keep_alive_task, expected):
        client._keep_alive_task = keep_alive_task

        assert client.is_alive is expected

    @pytest.mark.parametrize(
        ("ws", "handshake_event", "expected"),
        [
            (None, None, False),
            (None, True, False),
            (None, False, False),
            ("something", None, False),
            ("something", True, True),
            ("something", False, False),
        ],
    )
    def test_is_connected_property(self, client, ws, handshake_event, expected):
        client._ws = ws
        client._handshake_event = (
            None if handshake_event is None else mock.Mock(is_set=mock.Mock(return_value=handshake_event))
        )

        assert client.is_connected is expected

    def test_shard_count_property(self, client):
        client._shard_count = 69
        assert client.shard_count == 69

    def test_shard__check_if_connected_when_not_alive(self, client):
        with mock.patch.object(shard.GatewayShardImpl, "is_connected", new=False):
            with pytest.raises(errors.ComponentStateConflictError):
                client._check_if_connected()

    def test_shard__check_if_connected_when_alive(self, client):
        with mock.patch.object(shard.GatewayShardImpl, "is_connected", new=True):
            client._check_if_connected()

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

        if activity is not None:
            expected_activity = {
                "name": activity.name,
                "state": activity.state,
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
            "afk": afk,
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

    def test_get_user_id(self, client):
        client._user_id = 123

        with mock.patch.object(shard.GatewayShardImpl, "_check_if_connected") as check_if_alive:
            assert client.get_user_id() == 123

        check_if_alive.assert_called_once_with()


@pytest.mark.asyncio()
class TestGatewayShardImplAsync:
    async def test_close_when_no_keep_alive_task(self, client):
        client._keep_alive_task = None

        with pytest.raises(errors.ComponentStateConflictError):
            await client.close()

    async def test_close_when_closing_event_set(self, client):
        client._keep_alive_task = mock.Mock(cancel=mock.AsyncMock())
        client._non_priority_rate_limit = mock.Mock()
        client._total_rate_limit = mock.Mock()
        client._is_closing = True

        with mock.patch.object(shard.GatewayShardImpl, "join") as join:
            await client.close()

        join.assert_awaited_once_with()
        client._keep_alive_task.cancel.assert_not_called()
        client._non_priority_rate_limit.close.assert_not_called()
        client._total_rate_limit.close.assert_not_called()

    async def test_close_when_closing_event_not_set(self, client):
        cancel_async_mock = mock.Mock()

        class TaskMock:
            def __init__(self):
                self._awaited_count = 0

            def __await__(self):
                self._awaited_count += 1
                raise asyncio.CancelledError

            @property
            def cancel(self):
                return cancel_async_mock

            def assert_awaited_once(self):
                assert self._awaited_count == 1

        client._keep_alive_task = keep_alive_task = TaskMock()
        client._non_priority_rate_limit = mock.Mock()
        client._total_rate_limit = mock.Mock()

        with mock.patch.object(shard.GatewayShardImpl, "join") as join:
            await client.close()

        join.assert_not_called()
        cancel_async_mock.assert_called_once_with()
        keep_alive_task.assert_awaited_once()
        client._non_priority_rate_limit.close.assert_called_once_with()
        client._total_rate_limit.close.assert_called_once_with()

    async def test_join_when_not_alive(self, client):
        client._keep_alive_task = None

        with pytest.raises(errors.ComponentStateConflictError):
            await client.join()

    async def test_join(self, client):
        client._keep_alive_task = object()

        with mock.patch.object(asyncio, "wait_for") as wait_for:
            with mock.patch.object(asyncio, "shield", new=mock.Mock()) as shield:
                await client.join()

        shield.assert_called_once_with(client._keep_alive_task)
        wait_for.assert_awaited_once_with(shield.return_value, timeout=None)

    async def test__send_json(self, client):
        client._total_rate_limit = mock.AsyncMock()
        client._non_priority_rate_limit = mock.AsyncMock()
        client._ws = mock.AsyncMock()
        data = object()

        await client._send_json(data)

        client._non_priority_rate_limit.acquire.assert_awaited_once_with()
        client._total_rate_limit.acquire.assert_awaited_once_with()
        client._ws.send_json.assert_awaited_once_with(data)

    async def test__send_json_when_priority(self, client):
        client._total_rate_limit = mock.AsyncMock()
        client._non_priority_rate_limit = mock.AsyncMock()
        client._ws = mock.AsyncMock()
        data = object()

        await client._send_json(data, priority=True)

        client._non_priority_rate_limit.acquire.assert_not_called()
        client._total_rate_limit.acquire.assert_awaited_once_with()
        client._ws.send_json.assert_awaited_once_with(data)

    async def test_request_guild_members_when_no_query_and_no_limit_and_GUILD_MEMBERS_not_enabled(self, client):
        client._intents = intents.Intents.GUILD_INTEGRATIONS

        with mock.patch.object(shard.GatewayShardImpl, "_check_if_connected") as check_if_alive:
            with pytest.raises(errors.MissingIntentError):
                await client.request_guild_members(123, query="", limit=0)

        check_if_alive.assert_called_once_with()

    async def test_request_guild_members_when_presences_and_GUILD_PRESENCES_not_enabled(self, client):
        client._intents = intents.Intents.GUILD_INTEGRATIONS

        with mock.patch.object(shard.GatewayShardImpl, "_check_if_connected") as check_if_alive:
            with pytest.raises(errors.MissingIntentError):
                await client.request_guild_members(123, query="test", limit=1, include_presences=True)

        check_if_alive.assert_called_once_with()

    async def test_request_guild_members_when_presences_false_and_GUILD_PRESENCES_not_enabled(self, client):
        client._intents = intents.Intents.GUILD_INTEGRATIONS

        with mock.patch.object(shard.GatewayShardImpl, "_send_json") as send_json:
            with mock.patch.object(shard.GatewayShardImpl, "_check_if_connected") as check_if_alive:
                await client.request_guild_members(123, query="test", limit=1, include_presences=False)

        send_json.assert_awaited_once_with(
            {"op": 8, "d": {"guild_id": "123", "query": "test", "presences": False, "limit": 1}}
        )

        check_if_alive.assert_called_once_with()

    @pytest.mark.parametrize("kwargs", [{"query": "some query"}, {"limit": 1}])
    async def test_request_guild_members_when_specifiying_users_with_limit_or_query(self, client, kwargs):
        client._intents = intents.Intents.GUILD_INTEGRATIONS

        with mock.patch.object(shard.GatewayShardImpl, "_check_if_connected") as check_if_alive:
            with pytest.raises(ValueError, match="Cannot specify limit/query with users"):
                await client.request_guild_members(123, users=[], **kwargs)

        check_if_alive.assert_called_once_with()

    @pytest.mark.parametrize("limit", [-1, 101])
    async def test_request_guild_members_when_limit_under_0_or_over_100(self, client, limit):
        client._intents = intents.Intents.ALL

        with mock.patch.object(shard.GatewayShardImpl, "_check_if_connected") as check_if_alive:
            with pytest.raises(ValueError, match="'limit' must be between 0 and 100, both inclusive"):
                await client.request_guild_members(123, limit=limit)

        check_if_alive.assert_called_once_with()

    async def test_request_guild_members_when_users_over_100(self, client):
        client._intents = intents.Intents.ALL

        with mock.patch.object(shard.GatewayShardImpl, "_check_if_connected") as check_if_alive:
            with pytest.raises(ValueError, match="'users' is limited to 100 users"):
                await client.request_guild_members(123, users=range(101))

        check_if_alive.assert_called_once_with()

    async def test_request_guild_members_when_nonce_over_32_chars(self, client):
        client._intents = intents.Intents.ALL

        with mock.patch.object(shard.GatewayShardImpl, "_check_if_connected") as check_if_alive:
            with pytest.raises(ValueError, match="'nonce' can be no longer than 32 byte characters long."):
                await client.request_guild_members(123, nonce="x" * 33)

        check_if_alive.assert_called_once_with()

    @pytest.mark.parametrize("include_presences", [True, False])
    async def test_request_guild_members(self, client, include_presences):
        client._intents = intents.Intents.ALL

        with mock.patch.object(shard.GatewayShardImpl, "_send_json") as send_json:
            with mock.patch.object(shard.GatewayShardImpl, "_check_if_connected") as check_if_alive:
                await client.request_guild_members(123, include_presences=include_presences)

        send_json.assert_awaited_once_with(
            {"op": 8, "d": {"guild_id": "123", "query": "", "presences": include_presences, "limit": 0}}
        )
        check_if_alive.assert_called_once_with()

    @pytest.mark.parametrize("attr", ["_keep_alive_task", "_handshake_event"])
    async def test_start_when_already_running(self, client, attr):
        setattr(client, attr, object())

        with pytest.raises(errors.ComponentStateConflictError):
            await client.start()

    async def test_start_when_shard_closed_before_starting(self, client):
        client._keep_alive_task = None
        client._shard_id = 20
        handshake_event = mock.Mock(is_set=mock.Mock(return_value=False))

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(aio, "first_completed"))
        stack.enter_context(mock.patch.object(asyncio, "shield"))
        stack.enter_context(mock.patch.object(asyncio, "create_task"))
        stack.enter_context(mock.patch.object(shard.GatewayShardImpl, "_keep_alive", new=mock.Mock()))
        stack.enter_context(mock.patch.object(asyncio, "Event", return_value=handshake_event))
        stack.enter_context(pytest.raises(RuntimeError, match="shard 20 was closed before it could start successfully"))

        with stack:
            await client.start()

        assert client._keep_alive_task is None

    async def test_start(self, client):
        client._keep_alive_task = None
        client._shard_id = 20
        handshake_event = mock.Mock(is_set=mock.Mock(return_value=True))
        keep_alive_task = mock.Mock()

        stack = contextlib.ExitStack()
        first_completed = stack.enter_context(mock.patch.object(aio, "first_completed"))
        shield = stack.enter_context(mock.patch.object(asyncio, "shield"))
        create_task = stack.enter_context(mock.patch.object(asyncio, "create_task", return_value=keep_alive_task))
        keep_alive = stack.enter_context(mock.patch.object(shard.GatewayShardImpl, "_keep_alive", new=mock.Mock()))
        stack.enter_context(mock.patch.object(asyncio, "Event", return_value=handshake_event))

        with stack:
            await client.start()

        assert client._keep_alive_task is keep_alive_task

        create_task.assert_called_once_with(keep_alive.return_value, name="keep alive (shard 20)")
        shield.assert_called_once_with(create_task.return_value)
        first_completed.assert_awaited_once_with(handshake_event.wait.return_value, shield.return_value)

    async def test_update_presence(self, client):
        with mock.patch.object(shard.GatewayShardImpl, "_serialize_and_store_presence_payload") as presence:
            with mock.patch.object(shard.GatewayShardImpl, "_check_if_connected") as check_if_alive:
                with mock.patch.object(shard.GatewayShardImpl, "_send_json") as send_json:
                    await client.update_presence(
                        idle_since=datetime.datetime.now(), afk=True, status=presences.Status.IDLE, activity=None
                    )

        send_json.assert_awaited_once_with({"op": 3, "d": presence.return_value})
        check_if_alive.assert_called_once_with()

    async def test_update_voice_state(self, client):
        with mock.patch.object(shard.GatewayShardImpl, "_check_if_connected") as check_if_alive:
            with mock.patch.object(shard.GatewayShardImpl, "_send_json") as send_json:
                await client.update_voice_state(123456, 6969420, self_mute=False, self_deaf=True)

        send_json.assert_awaited_once_with(
            {"op": 4, "d": {"guild_id": "123456", "channel_id": "6969420", "self_mute": False, "self_deaf": True}}
        )
        check_if_alive.assert_called_once_with()

    async def test_update_voice_state_without_optionals(self, client):
        with mock.patch.object(shard.GatewayShardImpl, "_check_if_connected") as check_if_alive:
            with mock.patch.object(shard.GatewayShardImpl, "_send_json") as send_json:
                await client.update_voice_state(123456, 6969420)

        send_json.assert_awaited_once_with({"op": 4, "d": {"guild_id": "123456", "channel_id": "6969420"}})
        check_if_alive.assert_called_once_with()

    @hikari_test_helpers.timeout()
    async def test__heartbeat(self, client):
        client._last_heartbeat_sent = 5
        client._logger = mock.Mock()

        class ExitException(Exception): ...

        stack = contextlib.ExitStack()
        sleep = stack.enter_context(mock.patch.object(asyncio, "sleep", side_effect=[None, ExitException]))
        stack.enter_context(mock.patch.object(time, "monotonic", return_value=10))
        send_heartbeat = stack.enter_context(mock.patch.object(shard.GatewayShardImpl, "_send_heartbeat"))
        stack.enter_context(pytest.raises(ExitException))

        with stack:
            await client._heartbeat(20)

        assert send_heartbeat.await_count == 2
        send_heartbeat.assert_has_awaits([mock.call(), mock.call()])
        assert sleep.await_count == 2
        sleep.assert_has_awaits([mock.call(20), mock.call(20)])

    @hikari_test_helpers.timeout()
    async def test__heartbeat_when_zombie(self, client):
        client._last_heartbeat_sent = 10
        client._logger = mock.Mock()

        with mock.patch.object(time, "monotonic", return_value=5):
            with mock.patch.object(asyncio, "sleep") as sleep:
                await client._heartbeat(20)

        sleep.assert_not_called()

    async def test__connect_when_ws(self, client):
        client._ws = object()

        with pytest.raises(errors.ComponentStateConflictError):
            await client._connect()

    async def test__connect_when_not_reconnecting(self, client, http_settings, proxy_settings):
        ws = mock.AsyncMock()
        ws.receive_json.return_value = {"op": 10, "d": {"heartbeat_interval": 10}}
        client._transport_compression = False
        client._shard_id = 20
        client._shard_count = 100
        client._gateway_url = "wss://somewhere.com?somewhere=true"
        client._resume_gateway_url = None
        client._token = "sometoken"
        client._logger = mock.Mock()
        client._handshake_event = mock.Mock()
        client._seq = None
        client._large_threshold = "your mom"
        client._intents = 9

        heartbeat_task = object()
        poll_events_task = object()
        shielded_heartbeat_task = object()
        shielded_poll_events_task = object()

        stack = contextlib.ExitStack()
        create_task = stack.enter_context(
            mock.patch.object(asyncio, "create_task", side_effect=[heartbeat_task, poll_events_task])
        )
        shield = stack.enter_context(
            mock.patch.object(asyncio, "shield", side_effect=[shielded_heartbeat_task, shielded_poll_events_task])
        )
        first_completed = stack.enter_context(mock.patch.object(aio, "first_completed"))
        log_filterer = stack.enter_context(mock.patch.object(shard, "_log_filterer"))
        serialize_and_store_presence_payload = stack.enter_context(
            mock.patch.object(shard.GatewayShardImpl, "_serialize_and_store_presence_payload")
        )
        send_json = stack.enter_context(mock.patch.object(shard.GatewayShardImpl, "_send_json"))
        heartbeat = stack.enter_context(mock.patch.object(shard.GatewayShardImpl, "_heartbeat", new=mock.Mock()))
        poll_events = stack.enter_context(mock.patch.object(shard.GatewayShardImpl, "_poll_events", new=mock.Mock()))
        gateway_transport_connect = stack.enter_context(
            mock.patch.object(shard._GatewayTransport, "connect", return_value=ws)
        )
        stack.enter_context(mock.patch.object(urls, "VERSION", new=400))
        stack.enter_context(mock.patch.object(platform, "system", return_value="Potato OS"))
        stack.enter_context(mock.patch.object(platform, "architecture", return_value=["ARM64"]))
        stack.enter_context(mock.patch.object(aiohttp, "__version__", new="4.0"))
        stack.enter_context(mock.patch.object(_about, "__version__", new="1.0.0"))

        with stack:
            assert await client._connect() == (heartbeat_task, poll_events_task)

        log_filterer.assert_called_once_with("sometoken")
        gateway_transport_connect.assert_called_once_with(
            http_settings=http_settings,
            log_filterer=log_filterer.return_value,
            logger=client._logger,
            proxy_settings=proxy_settings,
            transport_compression=False,
            loads=client._loads,
            dumps=client._dumps,
            url="wss://somewhere.com?somewhere=true&v=400&encoding=json",
        )

        assert create_task.call_count == 2
        create_task.assert_has_calls(
            [
                mock.call(heartbeat.return_value, name="heartbeat (shard 20)"),
                mock.call(poll_events.return_value, name="poll events (shard 20)"),
            ]
        )
        heartbeat.assert_called_once_with(0.01)

        ws.receive_json.assert_awaited_once_with()
        send_json.assert_called_once_with(
            {
                "op": 2,
                "d": {
                    "token": "sometoken",
                    "compress": False,
                    "large_threshold": "your mom",
                    "properties": {
                        "os": "Potato OS ARM64",
                        "browser": "hikari (1.0.0, aiohttp 4.0)",
                        "device": "hikari 1.0.0",
                    },
                    "shard": [20, 100],
                    "intents": 9,
                    "presence": serialize_and_store_presence_payload.return_value,
                },
            }
        )

        assert shield.call_count == 2
        shield.assert_has_calls([mock.call(heartbeat_task), mock.call(poll_events_task)])
        first_completed.assert_called_once_with(
            client._handshake_event.wait.return_value, shielded_heartbeat_task, shielded_poll_events_task
        )

    async def test__connect_when_reconnecting(self, client, http_settings, proxy_settings):
        ws = mock.AsyncMock()
        ws.receive_json.return_value = {"op": 10, "d": {"heartbeat_interval": 10}}
        client._transport_compression = True
        client._shard_id = 20
        client._gateway_url = "wss://somewhere.com?somewhere=false"
        client._resume_gateway_url = "wss://notsomewhere.com?somewhere=true"
        client._token = "sometoken"
        client._logger = mock.Mock()
        client._handshake_event = mock.Mock()
        client._seq = 1234
        client._session_id = "some session id"

        heartbeat_task = object()
        poll_events_task = object()
        shielded_heartbeat_task = object()
        shielded_poll_events_task = object()

        stack = contextlib.ExitStack()
        create_task = stack.enter_context(
            mock.patch.object(asyncio, "create_task", side_effect=[heartbeat_task, poll_events_task])
        )
        shield = stack.enter_context(
            mock.patch.object(asyncio, "shield", side_effect=[shielded_heartbeat_task, shielded_poll_events_task])
        )
        first_completed = stack.enter_context(mock.patch.object(aio, "first_completed"))
        log_filterer = stack.enter_context(mock.patch.object(shard, "_log_filterer"))
        send_json = stack.enter_context(mock.patch.object(shard.GatewayShardImpl, "_send_json"))
        heartbeat = stack.enter_context(mock.patch.object(shard.GatewayShardImpl, "_heartbeat", new=mock.Mock()))
        poll_events = stack.enter_context(mock.patch.object(shard.GatewayShardImpl, "_poll_events", new=mock.Mock()))
        gateway_transport_connect = stack.enter_context(
            mock.patch.object(shard._GatewayTransport, "connect", return_value=ws)
        )
        stack.enter_context(mock.patch.object(urls, "VERSION", new=400))

        with stack:
            assert await client._connect() == (heartbeat_task, poll_events_task)

        log_filterer.assert_called_once_with("sometoken")
        gateway_transport_connect.assert_called_once_with(
            http_settings=http_settings,
            log_filterer=log_filterer.return_value,
            logger=client._logger,
            proxy_settings=proxy_settings,
            loads=client._loads,
            dumps=client._dumps,
            transport_compression=True,
            url="wss://notsomewhere.com?somewhere=true&v=400&encoding=json&compress=zlib-stream",
        )

        assert create_task.call_count == 2
        create_task.assert_has_calls(
            [
                mock.call(heartbeat.return_value, name="heartbeat (shard 20)"),
                mock.call(poll_events.return_value, name="poll events (shard 20)"),
            ]
        )
        heartbeat.assert_called_once_with(0.01)

        ws.receive_json.assert_awaited_once_with()
        send_json.assert_called_once_with(
            {"op": 6, "d": {"token": "sometoken", "seq": 1234, "session_id": "some session id"}}
        )

        assert shield.call_count == 2
        shield.assert_has_calls([mock.call(heartbeat_task), mock.call(poll_events_task)])
        first_completed.assert_called_once_with(
            client._handshake_event.wait.return_value, shielded_heartbeat_task, shielded_poll_events_task
        )

    async def test__connect_when_op_received_is_not_HELLO(self, client):
        ws = mock.AsyncMock()
        ws.receive_json.return_value = {"op": 0, "d": {"not": "hello"}}
        client._gateway_url = "somewhere.com"
        client._logger = mock.Mock()
        client._handshake_event = object()

        stack = contextlib.ExitStack()
        stack.enter_context(pytest.raises(errors.GatewayError))
        gateway_transport_connect = stack.enter_context(
            mock.patch.object(shard._GatewayTransport, "connect", return_value=ws)
        )

        with stack:
            assert await client._connect()

        gateway_transport_connect.return_value.send_close.assert_awaited_once_with(
            code=1002, message=b"Expected HELLO op"
        )

    @pytest.mark.skip("TODO")
    async def test__keep_alive(self, client): ...

    async def test__send_heartbeat(self, client):
        client._last_heartbeat_sent = 0
        client._seq = 10

        with mock.patch.object(shard.GatewayShardImpl, "_send_json") as send_json:
            with mock.patch.object(time, "monotonic", return_value=200):
                await client._send_heartbeat()

        send_json.assert_awaited_once_with({"op": 1, "d": 10}, priority=True)
        assert client._last_heartbeat_sent == 200

    async def test__poll_events_on_dispatch(self, client):
        payload = {"op": 0, "t": "SOMETHING", "d": {"some": "test"}, "s": 101}

        client._ws = mock.Mock(receive_json=mock.AsyncMock(side_effect=[payload, RuntimeError]))
        client._seq = 1000
        client._event_manager.consume_raw_event = mock.Mock(side_effect=[LookupError])
        client._handshake_event = mock.Mock()

        with pytest.raises(RuntimeError):
            await client._poll_events()

        assert client._ws.receive_json.await_count == 2
        assert client._seq == 101
        client._event_manager.consume_raw_event.assert_called_once_with("SOMETHING", client, {"some": "test"})
        client._handshake_event.set.assert_not_called()

    async def test__poll_events_on_dispatch_when_READY(self, client):
        data = {
            "v": 10,
            "session_id": 100001,
            "resume_gateway_url": "testing_endpoint",
            "user": {"id": 123, "username": "davfsa", "discriminator": "7026"},
            "guilds": ["1"] * 100,
        }

        payload = {"op": 0, "t": "READY", "d": data, "s": 101}

        client._ws = mock.Mock(receive_json=mock.AsyncMock(side_effect=[payload, RuntimeError]))
        client._seq = None
        client._session_id = None
        client._resume_gateway_url = None
        client._user_id = None
        client._event_manager.consume_raw_event = mock.Mock(side_effect=[LookupError])
        client._handshake_event = mock.Mock()

        with pytest.raises(RuntimeError):
            await client._poll_events()

        assert client._ws.receive_json.await_count == 2
        assert client._seq == 101
        assert client._resume_gateway_url == "testing_endpoint"
        assert client._session_id == 100001
        assert client._user_id == 123
        client._event_manager.consume_raw_event.assert_called_once_with("READY", client, data)
        client._handshake_event.set.assert_called_once_with()

    async def test__poll_events_on_dispatch_when_RESUMED(self, client):
        payload = {"op": 0, "t": "RESUMED", "d": {"some": "test"}, "s": 101}

        client._ws = mock.Mock(receive_json=mock.AsyncMock(side_effect=[payload, RuntimeError]))
        client._seq = 1000
        client._event_manager.consume_raw_event = mock.Mock(side_effect=[LookupError])
        client._handshake_event = mock.Mock()

        with pytest.raises(RuntimeError):
            await client._poll_events()

        assert client._ws.receive_json.await_count == 2
        assert client._seq == 101
        client._event_manager.consume_raw_event.assert_called_once_with("RESUMED", client, {"some": "test"})
        client._handshake_event.set.assert_called_once_with()

    async def test__poll_events_on_heartbeat_ack(self, client):
        payload = {"op": 11}

        client._ws = mock.Mock(receive_json=mock.AsyncMock(side_effect=[payload, RuntimeError]))
        client._heartbeat_latency = 0
        client._last_heartbeat_ack_received = 0
        client._last_heartbeat_sent = 1.5
        client._handshake_event = mock.Mock()

        with mock.patch.object(time, "monotonic", return_value=3):
            with pytest.raises(RuntimeError):
                await client._poll_events()

        assert client._ws.receive_json.await_count == 2
        assert client._last_heartbeat_ack_received == 3
        assert client._heartbeat_latency == 1.5
        client._handshake_event.set.assert_not_called()

    async def test__poll_events_on_heartbeat(self, client):
        payload = {"op": 1}

        client._ws = mock.Mock(receive_json=mock.AsyncMock(side_effect=[payload, RuntimeError]))
        client._handshake_event = mock.Mock()

        with mock.patch.object(shard.GatewayShardImpl, "_send_heartbeat") as send_heartbeat:
            with pytest.raises(RuntimeError):
                await client._poll_events()

        assert client._ws.receive_json.await_count == 2
        send_heartbeat.assert_awaited_once_with()
        client._handshake_event.set.assert_not_called()

    async def test__poll_events_on_reconnect(self, client):
        payload = {"op": 7}

        client._ws = mock.Mock(receive_json=mock.AsyncMock(side_effect=[payload, RuntimeError]))
        client._handshake_event = mock.Mock()

        await client._poll_events()

        assert client._ws.receive_json.await_count == 1
        client._handshake_event.set.assert_not_called()

    async def test__poll_events_on_invalid_session_when_can_resume(self, client):
        payload = {"op": 9, "d": True}

        client._seq = 123
        client._session_id = 456
        client._ws = mock.Mock(receive_json=mock.AsyncMock(side_effect=[payload, RuntimeError]))
        client._handshake_event = mock.Mock()

        await client._poll_events()

        assert client._ws.receive_json.await_count == 1
        assert client._seq == 123
        assert client._session_id == 456
        client._handshake_event.set.assert_not_called()

    async def test__poll_events_on_invalid_session_when_cant_resume(self, client):
        payload = {"op": 9, "d": False}

        client._seq = 123
        client._session_id = 456
        client._ws = mock.Mock(receive_json=mock.AsyncMock(side_effect=[payload, RuntimeError]))
        client._handshake_event = mock.Mock()

        await client._poll_events()

        assert client._ws.receive_json.await_count == 1
        assert client._seq is None
        assert client._session_id is None
        client._handshake_event.set.assert_not_called()

    async def test__poll_events_on_unknown_op(self, client):
        payload = {"op": 69, "d": "DATA"}

        client._logger = mock.Mock()
        client._ws = mock.Mock(receive_json=mock.AsyncMock(side_effect=[payload, RuntimeError]))
        client._handshake_event = mock.Mock()

        with pytest.raises(RuntimeError):
            await client._poll_events()

        assert client._ws.receive_json.await_count == 2
        client._logger.log.assert_called_once_with(ux.TRACE, "unknown opcode %s received, it will be ignored...", 69)
        client._handshake_event.set.assert_not_called()
