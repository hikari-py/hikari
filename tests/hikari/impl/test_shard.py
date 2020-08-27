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

import aiohttp.client_reqrep
import mock
import pytest

from hikari import config
from hikari import errors
from hikari import intents
from hikari import presences
from hikari import snowflakes
from hikari import undefined
from hikari.impl import shard
from hikari.utilities import constants
from hikari.utilities import date as hikari_date
from tests.hikari import client_session_stub
from tests.hikari import hikari_test_helpers

# TODO: testing all properties


@pytest.fixture()
def http_settings():
    return mock.Mock(spec_set=config.HTTPSettings)


@pytest.fixture()
def proxy_settings():
    return mock.Mock(spec_set=config.ProxySettings)


@pytest.fixture()
def client_session():
    stub = client_session_stub.ClientSessionStub()
    with mock.patch.object(aiohttp, "ClientSession", new=stub):
        yield stub


@pytest.fixture(scope="module")
def unslotted_client_type():
    return hikari_test_helpers.unslot_class(shard.GatewayShardImpl)


@pytest.fixture()
def client(http_settings, proxy_settings, unslotted_client_type):
    return unslotted_client_type(
        url="wss://gateway.discord.gg",
        token="lol",
        event_consumer=mock.Mock(),
        http_settings=http_settings,
        proxy_settings=proxy_settings,
    )


class TestInit:
    @pytest.mark.parametrize(
        ["v", "compression", "expect"],
        [
            (6, None, "v=6&encoding=json"),
            (6, "payload_zlib_stream", "v=6&encoding=json&compress=zlib-stream"),
            (7, None, "v=7&encoding=json"),
            (7, "payload_zlib_stream", "v=7&encoding=json&compress=zlib-stream"),
        ],
    )
    def test_url_is_correct_json(self, v, compression, expect, http_settings, proxy_settings):
        g = shard.GatewayShardImpl(
            event_consumer=mock.Mock(),
            token=mock.Mock(),
            http_settings=http_settings,
            proxy_settings=proxy_settings,
            url="wss://gaytewhuy.discord.meh",
            version=v,
            data_format="json",
            compression=compression,
        )

        assert g.url == f"wss://gaytewhuy.discord.meh?{expect}"

    @pytest.mark.parametrize(["v", "use_compression"], [(6, False), (6, True), (7, False), (7, True)])
    def test_using_etf_is_unsupported(self, v, use_compression, http_settings, proxy_settings):
        compression = "payload_zlib_stream" if use_compression else None

        with pytest.raises(NotImplementedError):
            shard.GatewayShardImpl(
                event_consumer=mock.Mock(),
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                token=mock.Mock(),
                url="wss://erlpack-is-broken-lol.discord.meh",
                version=v,
                data_format="etf",
                compression=compression,
            )


class TestIsAliveProperty:
    def test_is_alive(self, client):
        client._connected_at = 1234
        assert client.is_alive

    def test_not_is_alive(self, client):
        client._connected_at = None
        assert not client.is_alive


@pytest.mark.asyncio
class TestGetUserID:
    async def test_when__user_id_is_None(self, client):
        client._handshake_event = mock.Mock(wait=mock.AsyncMock())
        client._user_id = None
        with pytest.raises(RuntimeError):
            assert await client.get_user_id()

    async def test_when__user_id_is_not_None(self, client):
        client._handshake_event = mock.Mock(wait=mock.AsyncMock())
        client._user_id = 123
        assert await client.get_user_id() == 123


@pytest.mark.asyncio
class TestStart:
    @pytest.mark.parametrize("shard_id", [0, 1, 2])
    @hikari_test_helpers.timeout()
    async def test_starts_task(self, event_loop, shard_id, http_settings=http_settings, proxy_settings=proxy_settings):
        g = hikari_test_helpers.unslot_class(shard.GatewayShardImpl)(
            url="wss://gateway.discord.gg",
            token="lol",
            event_consumer=mock.Mock(),
            http_settings=http_settings,
            proxy_settings=proxy_settings,
            shard_id=shard_id,
            shard_count=100,
        )

        g._handshake_event = mock.MagicMock(asyncio.Event)
        g._run = mock.Mock()

        future = event_loop.create_future()
        future.set_result(None)

        with mock.patch.object(asyncio, "create_task", return_value=future) as create_task:
            result = await g.start()
            assert result is future
            create_task.assert_called_once_with(g._run(), name=f"shard {shard_id} keep-alive")

    @hikari_test_helpers.timeout()
    async def test_waits_for_ready(self, client):
        client._handshake_event = mock.Mock()
        client._handshake_event.wait = mock.AsyncMock()
        client._run = mock.AsyncMock()

        await client.start()
        client._handshake_event.wait.assert_awaited_once_with()

    @hikari_test_helpers.timeout()
    async def test_exception_is_raised_immediately(self, client):
        client._handshake_event = mock.Mock()
        client._handshake_event.wait = mock.AsyncMock()
        client._run = mock.AsyncMock(side_effect=RuntimeError)

        with pytest.raises(RuntimeError):
            await client.start()


@pytest.mark.asyncio
class TestClose:
    @pytest.fixture
    def client(self):
        class GatewayStub(shard.GatewayShardImpl):
            @property
            def is_alive(self):
                return getattr(self, "_is_alive", False)

        return GatewayStub(
            url="wss://gateway.discord.gg",
            token="lol",
            event_consumer=mock.Mock(),
            http_settings=http_settings,
            proxy_settings=proxy_settings,
        )

    async def test_when_already_closed_does_nothing(self, client):
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.Mock(return_value=True)

        await client.close()

        client._request_close_event.set.assert_not_called()

    @pytest.mark.parametrize("is_alive", [True, False])
    async def test_close_sets_request_close_event(self, client, is_alive):
        client.__dict__["_is_alive"] = is_alive
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.Mock(return_value=False)

        await client.close()

        client._request_close_event.set.assert_called_once_with()

    @pytest.mark.parametrize("is_alive", [True, False])
    async def test_websocket_closed_if_not_None(self, client, is_alive):
        client.__dict__["_is_alive"] = is_alive
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.Mock(return_value=False)
        client._close_ws = mock.AsyncMock()
        client._ws = mock.Mock()

        await client.close()

        client._close_ws.assert_awaited_once_with(errors.ShardCloseCode.NORMAL_CLOSURE, "client shut down")

    @pytest.mark.parametrize("is_alive", [True, False])
    async def test_websocket_not_closed_if_None(self, client, is_alive):
        client.__dict__["_is_alive"] = is_alive
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.Mock(return_value=False)
        client._close_ws = mock.AsyncMock()
        client._ws = None

        await client.close()

        client._close_ws.assert_not_called()


@pytest.mark.asyncio
class TestRun:
    @hikari_test_helpers.timeout()
    async def test_aiohttp_ClientSession_is_initialized(self, unslotted_client_type):
        verify_ssl = True
        acquire_and_connect = 3.3
        request_socket_read = None
        request_socket_connect = 1.2
        total = 4.5
        max_redirects = 0
        allow_redirects = True
        trust_env = True
        event_consumer = lambda s, n, pl: None

        client = unslotted_client_type(
            event_consumer=event_consumer,
            token="shh",
            url="http://localhost:0",
            http_settings=config.HTTPSettings(
                verify_ssl=verify_ssl,
                timeouts=config.HTTPTimeoutSettings(
                    acquire_and_connect=acquire_and_connect,
                    request_socket_read=request_socket_read,
                    request_socket_connect=request_socket_connect,
                    total=total,
                ),
                max_redirects=max_redirects,
                allow_redirects=allow_redirects,
            ),
            proxy_settings=config.ProxySettings(trust_env=trust_env),
        )

        client._run_once = mock.AsyncMock()

        stack = contextlib.ExitStack()
        stack.enter_context(pytest.raises(errors.GatewayClientClosedError))
        client_session = stack.enter_context(mock.patch.object(aiohttp, "ClientSession"))
        tcp_connector = stack.enter_context(mock.patch.object(aiohttp, "TCPConnector"))
        timeout = stack.enter_context(mock.patch.object(aiohttp, "ClientTimeout"))

        with stack:
            await client._run()

        client_session.assert_called_once_with(
            connector_owner=True,
            connector=tcp_connector(verify_ssl=verify_ssl, limit=1, limit_per_host=1, force_close=True),
            version=aiohttp.HttpVersion11,
            timeout=timeout(
                total=total,
                connect=acquire_and_connect,
                sock_read=request_socket_read,
                sock_connect=request_socket_connect,
            ),
            trust_env=trust_env,
        )

    @hikari_test_helpers.timeout()
    async def test_repeatedly_invokes_run_once_shielded_while_request_close_event_not_set(self, client):
        i = 0

        def is_set():
            nonlocal i

            if i >= 5:
                return True
            else:
                i += 1
                return False

        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = is_set
        client._run_once_shielded = mock.AsyncMock()

        with pytest.raises(errors.GatewayClientClosedError):
            await client._run()

        assert i == 5
        assert client._run_once_shielded.call_count == i

    @hikari_test_helpers.timeout()
    async def test_sets_handshake_event_on_finish(self, client):
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._handshake_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.Mock(return_value=True)
        client._run_once = mock.AsyncMock()

        with pytest.raises(errors.GatewayClientClosedError):
            await client._run()

        client._handshake_event.set.assert_called_once_with()


@pytest.mark.asyncio
class TestRunOnceShielded:
    @pytest.fixture
    def client(self, http_settings=http_settings, proxy_settings=proxy_settings):
        client = hikari_test_helpers.unslot_class(shard.GatewayShardImpl)(
            url="wss://gateway.discord.gg",
            token="lol",
            event_consumer=mock.Mock(),
            shard_id=3,
            shard_count=17,
            http_settings=http_settings,
            proxy_settings=proxy_settings,
        )
        client = hikari_test_helpers.mock_methods_on(
            client,
            except_=(
                "_run_once_shielded",
                "_InvalidSession",
                "_Reconnect",
                "_SocketClosed",
                "_Opcode",
            ),
            also_mock=["_backoff", "_handshake_event", "_request_close_event", "_logger", "_event_consumer"],
        )
        # Disable backoff checking by making the condition a negative tautology.
        client._RESTART_RATELIMIT_WINDOW = -1
        return client

    @hikari_test_helpers.timeout()
    async def test_invokes_run_once_shielded(self, client, client_session):
        await client._run_once_shielded(client_session)
        client._run_once.assert_awaited_once_with(client_session)

    @hikari_test_helpers.timeout()
    async def test_happy_path_returns_False(self, client, client_session):
        assert await client._run_once_shielded(client_session) is False

    @pytest.mark.parametrize(
        ["zombied", "request_close", "expect_backoff_called"],
        [
            (True, True, True),
            (True, False, True),
            (False, True, False),
            (False, False, False),
        ],
    )
    @hikari_test_helpers.timeout()
    async def test_socket_closed_resets_backoff(
        self, client, zombied, request_close, expect_backoff_called, client_session
    ):
        client._request_close_event.is_set = mock.Mock(return_value=request_close)

        def run_once():
            client._zombied = zombied
            raise shard.GatewayShardImpl._SocketClosed()

        client._run_once = mock.AsyncMock(wraps=run_once)
        await client._run_once_shielded(client_session)

        if expect_backoff_called:
            client._backoff.reset.assert_called_once_with()
        else:
            client._backoff.reset.assert_not_called()

    @hikari_test_helpers.timeout()
    async def test_invalid_session_resume_does_not_clear_seq_or_session_id(self, client, client_session):
        client._run_once = mock.AsyncMock(side_effect=shard.GatewayShardImpl._InvalidSession(True))
        client._seq = 1234
        client._session_id = "69420"
        await client._run_once_shielded(client_session)
        assert client._seq == 1234
        assert client._session_id == "69420"

    @pytest.mark.parametrize("request_close", [True, False])
    @hikari_test_helpers.timeout()
    async def test_socket_closed_is_restartable_if_no_closure_request(self, client, request_close, client_session):
        client._request_close_event.is_set = mock.Mock(return_value=request_close)
        client._run_once = mock.AsyncMock(side_effect=shard.GatewayShardImpl._SocketClosed())
        assert await client._run_once_shielded(client_session) is not request_close

    @hikari_test_helpers.timeout()
    async def test_ClientConnectionError_is_restartable(self, client, client_session):
        key = aiohttp.client_reqrep.ConnectionKey(
            host="localhost",
            port=6996,
            is_ssl=False,
            ssl=None,
            proxy=None,
            proxy_auth=None,
            proxy_headers_hash=69420,
        )
        error = aiohttp.ClientConnectorError(key, OSError())

        client._run_once = mock.AsyncMock(side_effect=error)
        assert await client._run_once_shielded(client_session) is True

    @hikari_test_helpers.timeout()
    async def test_WSServerHandshakeError_is_restartable(self, client, client_session):
        error = aiohttp.WSServerHandshakeError(
            mock.Mock(spec_set=aiohttp.RequestInfo),
            history=(mock.Mock(spec_set=aiohttp.ClientResponse),),
            status=520,
            message="Discord returned a 520 which means they are broken",
        )

        client._run_once = mock.AsyncMock(side_effect=error)
        assert await client._run_once_shielded(client_session) is True

    @hikari_test_helpers.timeout()
    async def test_invalid_session_is_restartable(self, client, client_session):
        client._run_once = mock.AsyncMock(side_effect=shard.GatewayShardImpl._InvalidSession())
        assert await client._run_once_shielded(client_session) is True

    @hikari_test_helpers.timeout()
    async def test_invalid_session_resume_does_not_invalidate_session(self, client, client_session):
        client._run_once = mock.AsyncMock(side_effect=shard.GatewayShardImpl._InvalidSession(True))
        await client._run_once_shielded(client_session)
        client._close_ws.assert_awaited_once_with(3000, "invalid session (resume)")

    @hikari_test_helpers.timeout()
    async def test_invalid_session_no_resume_invalidates_session(self, client, client_session):
        client._run_once = mock.AsyncMock(side_effect=shard.GatewayShardImpl._InvalidSession(False))
        await client._run_once_shielded(client_session)
        client._close_ws.assert_awaited_once_with(errors.ShardCloseCode.NORMAL_CLOSURE, "invalid session (no resume)")

    @hikari_test_helpers.timeout()
    async def test_invalid_session_no_resume_clears_seq_and_session_id(self, client, client_session):
        client._run_once = mock.AsyncMock(side_effect=shard.GatewayShardImpl._InvalidSession(False))
        client._seq = 1234
        client._session_id = "69420"
        await client._run_once_shielded(client_session)
        assert client._seq is None
        assert client._session_id is None

    @hikari_test_helpers.timeout()
    async def test_reconnect_is_restartable(self, client, client_session):
        client._run_once = mock.AsyncMock(side_effect=shard.GatewayShardImpl._Reconnect())
        assert await client._run_once_shielded(client_session) is True

    @hikari_test_helpers.timeout()
    async def test_server_connection_error_resumes_if_reconnectable(self, client, client_session):
        client._run_once = mock.AsyncMock(side_effect=errors.GatewayServerClosedConnectionError("blah", None, True))
        client._seq = 1234
        client._session_id = "69420"
        assert await client._run_once_shielded(client_session) is True
        assert client._seq == 1234
        assert client._session_id == "69420"

    @hikari_test_helpers.timeout()
    async def test_server_connection_error_does_not_reconnect_if_not_reconnectable(self, client, client_session):
        client._run_once = mock.AsyncMock(side_effect=errors.GatewayServerClosedConnectionError("blah", None, False))
        client._seq = 1234
        client._session_id = "69420"
        with pytest.raises(errors.GatewayServerClosedConnectionError):
            await client._run_once_shielded(client_session)
        client._request_close_event.set.assert_called_once_with()
        assert client._seq is None
        assert client._session_id is None
        client._backoff.reset.assert_called_once_with()

    @pytest.mark.parametrize(
        ["zombied", "request_close", "expect_backoff_called"],
        [(True, True, True), (True, False, True), (False, True, False), (False, False, False)],
    )
    @hikari_test_helpers.timeout()
    async def test_socket_closed_resets_backoff(
        self, client, zombied, request_close, expect_backoff_called, client_session
    ):
        client._request_close_event.is_set = mock.Mock(return_value=request_close)

        def run_once(_):
            client._zombied = zombied
            raise shard.GatewayShardImpl._SocketClosed()

        client._run_once = mock.AsyncMock(wraps=run_once)
        await client._run_once_shielded(client_session)

        if expect_backoff_called:
            client._backoff.reset.assert_called_once_with()
        else:
            client._backoff.reset.assert_not_called()

    async def test_other_exception_closes_websocket(self, client, client_session):
        client._run_once = mock.AsyncMock(side_effect=RuntimeError())

        with pytest.raises(RuntimeError):
            await client._run_once_shielded(client_session)

        client._close_ws.assert_awaited_once_with(
            errors.ShardCloseCode.UNEXPECTED_CONDITION, "unexpected error occurred"
        )


@pytest.mark.asyncio
class TestRunOnce:
    @pytest.fixture
    def client(self, http_settings, proxy_settings):
        client = hikari_test_helpers.unslot_class(shard.GatewayShardImpl)(
            url="wss://gateway.discord.gg",
            token="lol",
            event_consumer=mock.Mock(),
            shard_id=3,
            shard_count=17,
            http_settings=http_settings,
            proxy_settings=proxy_settings,
        )
        client = hikari_test_helpers.mock_methods_on(
            client,
            except_=(
                "_run_once",
                "_InvalidSession",
                "_Reconnect",
                "_SocketClosed",
                "_Opcode",
            ),
            also_mock=["_backoff", "_handshake_event", "_request_close_event", "_logger", "_event_consumer"],
        )
        # Disable backoff checking by making the condition a negative tautology.
        client._RESTART_RATELIMIT_WINDOW = -1
        return client

    @hikari_test_helpers.timeout()
    async def test_resets_close_event(self, client, client_session):
        await client._run_once(client_session)

        client._request_close_event.clear.assert_called_with()

    @hikari_test_helpers.timeout()
    async def test_resets_zombie_status(self, client, client_session):
        client._zombied = True

        await client._run_once(client_session)

        assert client._zombied is False

    @hikari_test_helpers.timeout()
    async def test_backoff_and_waits_if_restarted_too_quickly(self, client, client_session):
        client._RESTART_RATELIMIT_WINDOW = 30
        client._last_run_started_at = 40
        client._backoff.__next__ = mock.Mock(return_value=24.37)

        # We mock create_task, so this will never be awaited if not.
        client._heartbeat_keepalive = mock.Mock()

        stack = contextlib.ExitStack()
        wait_for = stack.enter_context(mock.patch.object(asyncio, "wait_for", side_effect=asyncio.TimeoutError))
        create_task = stack.enter_context(mock.patch.object(asyncio, "create_task"))
        stack.enter_context(mock.patch.object(hikari_date, "monotonic", return_value=60))

        with stack:
            await client._run_once(client_session)

        client._backoff.__next__.assert_called_once_with()
        create_task.assert_any_call(client._request_close_event.wait(), name="gateway shard 3 backing off")
        wait_for.assert_called_once_with(create_task(), timeout=24.37)

    @hikari_test_helpers.timeout()
    async def test_closing_bot_during_backoff_immediately_interrupts_it(self, client, client_session):
        client._RESTART_RATELIMIT_WINDOW = 30
        client._last_run_started_at = 40
        client._backoff.__next__ = mock.Mock(return_value=24.37)
        client._request_close_event = asyncio.Event()

        # use 60s since it is outside the 30s backoff window.
        with mock.patch.object(hikari_date, "monotonic", return_value=60.0):
            task = asyncio.create_task(client._run_once(client_session))

            try:
                # Let the backoff spin up and start waiting in the background.
                await hikari_test_helpers.idle()

                # Should be pretty much immediate.
                with hikari_test_helpers.ensure_occurs_quickly():
                    assert task.done() is False
                    client._request_close_event.set()
                    await task

                # The false instructs the caller to not restart again, but to just
                # drop everything and stop execution.
                # We never return a value on this task anymore.
                assert task.result() is None

            finally:
                task.cancel()

    @hikari_test_helpers.timeout()
    async def test_backoff_does_not_trigger_if_not_restarting_in_small_window(self, client, client_session):
        with mock.patch.object(hikari_date, "monotonic", return_value=60):
            client._last_run_started_at = 40
            client._backoff.__next__ = mock.Mock(
                side_effect=AssertionError(
                    "backoff was incremented, but this is not expected to occur in this test case scenario!"
                )
            )

            # We mock create_task, so this will never be awaited if not.
            client._heartbeat_keepalive = mock.Mock()

            stack = contextlib.ExitStack()
            stack.enter_context(mock.patch.object(asyncio, "wait_for"))
            stack.enter_context(mock.patch.object(asyncio, "create_task"))

            with stack:
                # This will raise an assertion error if the backoff is incremented.
                await client._run_once(client_session)

    @hikari_test_helpers.timeout()
    async def test_last_run_started_at_set_to_current_time(self, client, client_session):
        # Windows does some batshit crazy stuff in perf_counter, like only
        # returning process time elapsed rather than monotonic time since
        # startup, so I guess I will put this random value here to show the
        # code doesn't really care what this value is contextually.
        client._last_run_started_at = -100_000

        with mock.patch.object(hikari_date, "monotonic", return_value=1.0):
            await client._run_once(client_session)

        assert client._last_run_started_at == 1.0

    @hikari_test_helpers.timeout()
    async def test_ws_gets_created(self, client, client_session):
        proxy_settings = config.ProxySettings(
            url="http://my-proxy.net",
            headers={"foo": "bar"},
            trust_env=True,
            auth=config.BasicAuthHeader(username="banana", password="fan fo"),
        )
        http_settings = config.HTTPSettings(verify_ssl=False)
        client._http_settings = http_settings
        client._proxy_settings = proxy_settings

        await client._run_once(client_session)
        client_session.ws_connect.assert_called_once_with(
            url=client.url,
            autoping=True,
            autoclose=True,
            proxy=proxy_settings.url,
            proxy_headers=proxy_settings.all_headers,
            verify_ssl=http_settings.verify_ssl,
            # Discord can send massive messages that lead us to being disconnected
            # without this. It is a bit shit that there is no guarantee of the size
            # of these messages, but there isn't much we can do about this one.
            max_msg_size=0,
        )
        client_session.ws_connect_stub.assert_awaited_once()

    @hikari_test_helpers.timeout()
    async def test_zlib_decompressobj_set(self, client, client_session):
        assert client._zlib is None
        await client._run_once(client_session)
        assert client._zlib is not None

    @hikari_test_helpers.timeout()
    async def test_handshake_event_cleared(self, client, client_session):
        client._handshake_event = asyncio.Event()
        client._handshake_event.set()
        await client._run_once(client_session)
        assert not client._handshake_event.is_set()

    @hikari_test_helpers.timeout()
    async def test_handshake_invoked(self, client, client_session):
        await client._run_once(client_session)
        client._handshake.assert_awaited_once_with()

    @hikari_test_helpers.timeout()
    async def test_connected_event_dispatched_before_polling_events(self, client, client_session):
        class Error(Exception):
            pass

        client._poll_events = mock.AsyncMock(side_effect=Error)

        with pytest.raises(Error):
            await client._run_once(client_session)

        client._event_consumer.assert_any_call(client, "CONNECTED", {})

    @hikari_test_helpers.timeout()
    async def test_heartbeat_is_not_started_before_handshake_completes(self, client, client_session):
        class Error(Exception):
            pass

        client._heartbeat_keepalive = mock.Mock()

        client._handshake = mock.AsyncMock(side_effect=Error)

        with mock.patch.object(asyncio, "create_task") as create_task:
            with pytest.raises(Error):
                await client._run_once(client_session)

        call = mock.call(client._heartbeat_keepalive(), name=mock.ANY)
        assert call not in create_task.call_args_list

    @hikari_test_helpers.timeout()
    async def test_heartbeat_is_started(self, client, client_session):
        client._heartbeat_keepalive = mock.Mock()

        with mock.patch.object(asyncio, "create_task") as create_task:
            await client._run_once(client_session)

        call = mock.call(client._heartbeat_keepalive(), name="gateway shard 3 heartbeat")
        assert call in create_task.call_args_list

    @hikari_test_helpers.timeout()
    async def test_poll_events_invoked(self, client, client_session):
        await client._run_once(client_session)
        client._poll_events.assert_awaited_once_with()

    @hikari_test_helpers.timeout()
    async def test_heartbeat_is_stopped_when_poll_events_stops(self, client, client_session):
        client._heartbeat_keepalive = mock.Mock()
        client._poll_events = mock.AsyncMock(side_effect=Exception)

        task = mock.Mock(spec_set=asyncio.Task)

        with mock.patch.object(asyncio, "create_task", return_value=task):
            with pytest.raises(Exception):
                await client._run_once(client_session)

        task.cancel.assert_called_once_with()

    async def test_dispatches_disconnect_if_connected(self, client, client_session):
        await client._run_once(client_session)
        client._event_consumer.assert_any_call(client, "CONNECTED", {})
        client._event_consumer.assert_any_call(client, "DISCONNECTED", {})

    async def test_no_dispatch_disconnect_if_not_connected(self, client, client_session):
        client_session.ws_connect = mock.Mock(side_effect=RuntimeError)
        with pytest.raises(RuntimeError):
            await client._run_once(client_session)
        client._event_consumer.assert_not_called()

    async def test_connected_at_reset_to_None_on_exit(self, client, client_session):
        await client._run_once(client_session)
        assert client._connected_at is None


@pytest.mark.asyncio
class TestUpdatePresence:
    @pytest.mark.parametrize("is_alive", [True, False])
    async def test_sends_to_websocket_if_alive(self, client, is_alive):
        presence_payload = object()
        client._connected_at = 1234.5 if is_alive else None
        client._serialize_and_store_presence_payload = mock.Mock(return_value=presence_payload)
        client._send_json = mock.AsyncMock()

        await client.update_presence(
            idle_since=datetime.datetime.now(),
            afk=True,
            status=presences.Status.IDLE,
            activity=None,
        )

        if is_alive:
            client._send_json.assert_awaited_once_with({"op": 3, "d": presence_payload})
        else:
            client._send_json.assert_not_called()


@pytest.mark.asyncio
class TestUpdateVoiceState:
    @pytest.fixture
    def client(self, proxy_settings, http_settings):
        client = hikari_test_helpers.unslot_class(shard.GatewayShardImpl)(
            url="wss://gateway.discord.gg",
            token="lol",
            event_consumer=mock.Mock(),
            http_settings=http_settings,
            proxy_settings=proxy_settings,
            shard_id=3,
            shard_count=17,
        )
        return hikari_test_helpers.mock_methods_on(
            client,
            except_=(
                "update_voice_state",
                "_InvalidSession",
                "_Reconnect",
                "_SocketClosed",
                "_Opcode",
            ),
        )

    @pytest.mark.parametrize("channel", [12345, None])
    @pytest.mark.parametrize("self_deaf", [True, False])
    @pytest.mark.parametrize("self_mute", [True, False])
    async def test_serialized_result_sent_on_websocket(self, client, channel, self_deaf, self_mute):
        payload = {
            "channel_id": str(channel) if channel is not None else None,
            "guild_id": "6969420",
            "deaf": self_deaf,
            "mute": self_mute,
        }

        await client.update_voice_state("6969420", channel, self_mute=self_mute, self_deaf=self_deaf)

        client._send_json.assert_awaited_once_with(
            {"op": shard.GatewayShardImpl._Opcode.VOICE_STATE_UPDATE, "d": payload}
        )


@pytest.mark.asyncio
class TestRequestGuildMembers:
    @pytest.fixture
    def client(self, proxy_settings, http_settings):
        client = hikari_test_helpers.unslot_class(shard.GatewayShardImpl)(
            url="wss://gateway.discord.gg",
            token="lol",
            event_consumer=mock.Mock(),
            http_settings=http_settings,
            proxy_settings=proxy_settings,
            shard_id=3,
            shard_count=17,
        )
        return hikari_test_helpers.mock_methods_on(
            client,
            except_=(
                "request_guild_members",
                "_InvalidSession",
                "_Reconnect",
                "_SocketClosed",
                "_Opcode",
            ),
        )

    async def test_when_no_query_and_no_limit_and_GUILD_MEMBERS_not_enabled(self, client):
        client._intents = intents.Intents.GUILD_INTEGRATIONS

        with pytest.raises(errors.MissingIntentError):
            await client.request_guild_members(123, query="", limit=0)

    async def test_when_presences_and_GUILD_PRESENCES_not_enabled(self, client):
        client._intents = intents.Intents.GUILD_INTEGRATIONS

        with pytest.raises(errors.MissingIntentError):
            await client.request_guild_members(123, query="test", limit=1, include_presences=True)

    @pytest.mark.parametrize("kwargs", [{"query": "some query"}, {"limit": 1}])
    async def test_when_specifiying_users_with_limit_or_query(self, client, kwargs):
        client._intents = intents.Intents.GUILD_INTEGRATIONS

        with pytest.raises(ValueError):
            await client.request_guild_members(123, user_ids=[], **kwargs)

    @pytest.mark.parametrize("limit", [-1, 101])
    async def test_when_limit_under_0_or_over_100(self, client, limit):
        client._intents = None

        with pytest.raises(ValueError):
            await client.request_guild_members(123, limit=limit)

    async def test_when_users_over_100(self, client):
        client._intents = None

        with pytest.raises(ValueError):
            await client.request_guild_members(123, user_ids=range(101))

    async def test_request_guild_members(self, client):
        client._intents = None
        client._send_json = mock.AsyncMock()

        await client.request_guild_members(123)

        client._send_json.assert_awaited_once_with(
            {"op": client._Opcode.REQUEST_GUILD_MEMBERS, "d": {"guild_id": "123", "query": "", "limit": 0}}
        )


@pytest.mark.asyncio
class TestCloseWs:
    async def test_when_connected(self, client):
        client._ws = mock.Mock(spec_set=aiohttp.ClientWebSocketResponse)
        client._ws.close = mock.AsyncMock()

        await client._close_ws(6969420, "you got yeeted")

        client._ws.close.assert_awaited_once_with(code=6969420, message=b"you got yeeted")

    async def test_when_disconnected(self, client):
        client._ws = None
        await client._close_ws(6969420, "you got yeeted")
        # Do not expect any error or anything to happen.
        assert True


@pytest.mark.asyncio
class TestHandshake:
    async def test__handshake_when__session_id_is_not_None(self, client):
        client._expect_opcode = mock.AsyncMock()
        client._session_id = 123
        client._token = "token"
        client._seq = 456
        client._send_json = mock.AsyncMock()

        await client._handshake()

        expected_json = {"op": client._Opcode.RESUME, "d": {"token": "token", "seq": 456, "session_id": 123}}
        client._send_json.assert_awaited_once_with(expected_json)

    async def test__handshake_when__session_id_is_None_and_no_intents(self, client):
        client._expect_opcode = mock.AsyncMock()
        client._session_id = None
        client._token = "token"
        client._intents = None
        client._large_threshold = 123
        client._shard_id = 0
        client._shard_count = 1
        client._send_json = mock.AsyncMock()

        await client._handshake()

        expected_json = {
            "op": client._Opcode.IDENTIFY,
            "d": {
                "token": "token",
                "compress": False,
                "large_threshold": 123,
                "properties": {
                    "$os": constants.SYSTEM_TYPE,
                    "$browser": constants.AIOHTTP_VERSION,
                    "$device": constants.LIBRARY_VERSION,
                },
                "shard": [0, 1],
                "presence": {"since": None, "afk": False, "status": presences.Status.ONLINE, "game": None},
            },
        }
        client._send_json.assert_awaited_once_with(expected_json)

    async def test__handshake_when__session_id_is_None_and_intents(self, client):
        client._expect_opcode = mock.AsyncMock()
        client._session_id = None
        client._token = "token"
        client._intents = intents.Intents.ALL_UNPRIVILEGED
        client._large_threshold = 123
        client._shard_id = 0
        client._shard_count = 1
        client._send_json = mock.AsyncMock()

        await client._handshake()

        expected_json = {
            "op": client._Opcode.IDENTIFY,
            "d": {
                "token": "token",
                "compress": False,
                "large_threshold": 123,
                "properties": {
                    "$os": constants.SYSTEM_TYPE,
                    "$browser": constants.AIOHTTP_VERSION,
                    "$device": constants.LIBRARY_VERSION,
                },
                "shard": [0, 1],
                "intents": intents.Intents.ALL_UNPRIVILEGED,
                "presence": {"since": None, "afk": False, "status": presences.Status.ONLINE, "game": None},
            },
        }
        client._send_json.assert_awaited_once_with(expected_json)

    @pytest.mark.parametrize("idle_since", [None, datetime.datetime.now()])
    @pytest.mark.parametrize("afk", [None, True, False])
    @pytest.mark.parametrize(
        "status",
        [presences.Status.DO_NOT_DISTURB, presences.Status.IDLE, presences.Status.ONLINE, presences.Status.OFFLINE],
    )
    @pytest.mark.parametrize("activity", [presences.Activity(name="foo"), None])
    async def test__handshake_when__session_id_is_None_and_activity(self, client, idle_since, afk, status, activity):
        client._expect_opcode = mock.AsyncMock()
        client._session_id = None
        client._token = "token"
        client._intents = None
        client._large_threshold = 123
        client._activity = activity
        client._status = status
        client._idle_since = idle_since
        client._is_afk = afk
        client._shard_id = 0
        client._shard_count = 1
        client._send_json = mock.AsyncMock()
        client._app = mock.Mock()
        client._serialize_and_store_presence_payload = mock.Mock(
            return_value={
                "since": int(idle_since.timestamp() * 1_000) if idle_since is not None else None,
                "afk": afk,
                "status": status,
                "game": activity,
            }
        )

        await client._handshake()

        expected_json = {
            "op": client._Opcode.IDENTIFY,
            "d": {
                "token": "token",
                "compress": False,
                "large_threshold": 123,
                "properties": {
                    "$os": constants.SYSTEM_TYPE,
                    "$browser": constants.AIOHTTP_VERSION,
                    "$device": constants.LIBRARY_VERSION,
                },
                "shard": [0, 1],
                "presence": {
                    "since": int(idle_since.timestamp() * 1_000) if idle_since is not None else None,
                    "afk": afk,
                    "status": status,
                    "game": activity,
                },
            },
        }
        client._send_json.assert_awaited_once_with(expected_json)
        client._serialize_and_store_presence_payload.assert_called_once_with()


@pytest.mark.asyncio
class TestHeartbeatKeepalive:
    @hikari_test_helpers.timeout()
    async def test_when_not_zombie(self, client):
        client._last_message_received = 5
        client._heartbeat_interval = 5
        client._last_heartbeat_sent = 2
        client._seq = 123
        client._close_zombie = mock.AsyncMock()
        client._send_json = mock.AsyncMock()
        client._request_close_event = mock.Mock(is_set=mock.Mock(return_value=False))

        with mock.patch.object(hikari_date, "monotonic", side_effect=[10, 10, asyncio.CancelledError]):
            with mock.patch.object(asyncio, "wait_for", side_effect=asyncio.TimeoutError):
                with mock.patch.object(asyncio, "sleep"):
                    await client._heartbeat_keepalive()

        client._close_zombie.assert_not_called()
        client._send_json.assert_awaited_once_with({"op": client._Opcode.HEARTBEAT, "d": 123})
        assert client._last_heartbeat_sent == 10

    @hikari_test_helpers.timeout()
    async def test_when_zombie(self, client):
        client._last_message_received = 1
        client._heartbeat_interval = 5
        client._last_heartbeat_sent = 2
        client._close_zombie = mock.AsyncMock()
        client._send_json = mock.AsyncMock()

        with mock.patch.object(hikari_date, "monotonic", return_value=10):
            with mock.patch.object(asyncio, "sleep"):
                await client._heartbeat_keepalive()

        client._close_zombie.assert_awaited_once_with()
        client._send_json.assert_not_called()

    @hikari_test_helpers.timeout()
    async def test_when_request_close_event_set(self, client):
        client._heartbeat_interval = 5
        client._close_zombie = mock.AsyncMock()
        client._send_json = mock.AsyncMock()
        client._request_close_event = mock.Mock(is_set=mock.Mock(return_value=True))

        with mock.patch.object(asyncio, "sleep"):
            await client._heartbeat_keepalive()

        client._close_zombie.assert_not_called()
        client._send_json.assert_not_called()


@pytest.mark.asyncio
class TestCloseZombie:
    async def test_close_zombie(self, client):
        class AsyncMock:
            def __init__(self):
                self.await_count = 0

            def __await__(self):
                self.await_count += 1

        client._close_ws = mock.Mock()
        client._ws = mock.Mock()
        client._zombied = False
        mock_task = AsyncMock()

        with mock.patch.object(asyncio, "create_task", return_value=mock_task) as create_task:
            with mock.patch.object(asyncio, "sleep") as sleep:
                await client._close_zombie()

        assert client._zombied is True
        client._close_ws.assert_called_once_with(code=errors.ShardCloseCode.PROTOCOL_ERROR, message="heartbeat timeout")
        create_task.assert_called_once_with(client._close_ws())
        assert mock_task.await_count == 1
        sleep.assert_awaited_once_with(0.1)


@pytest.mark.asyncio
class TestPollEvents:
    @pytest.fixture
    def exit_error(self):
        class ExitError(BaseException):
            ...

        return ExitError

    @hikari_test_helpers.timeout()
    async def test_when_opcode_is_DISPATCH_and_event_is_READY(self, client, exit_error):
        data_payload = {"session_id": 123, "user": {"id": 456, "username": "hikari", "discriminator": "0001"}}
        payload = {
            "op": client._Opcode.DISPATCH,
            "d": data_payload,
            "t": "READY",
            "s": 101,
        }
        client._receive_json = mock.AsyncMock(side_effect=[payload, exit_error])
        timestamp = datetime.datetime.now()

        with mock.patch.object(hikari_date, "monotonic", return_value=timestamp):
            with pytest.raises(exit_error):
                await client._poll_events()

        client._event_consumer.assert_any_call(client, "READY", data_payload)
        assert client._handshake_event.is_set()
        assert client._session_id == 123
        assert client._seq == 101
        assert client._user_id == snowflakes.Snowflake(456)
        assert client._session_started_at == timestamp

    @hikari_test_helpers.timeout()
    async def test_when_opcode_is_DISPATCH_and_event_is_RESUME(self, client, exit_error):
        payload = {
            "op": client._Opcode.DISPATCH,
            "d": "some data",
            "t": "RESUME",
            "s": 101,
        }
        client._receive_json = mock.AsyncMock(side_effect=[payload, exit_error])

        with pytest.raises(exit_error):
            await client._poll_events()

        client._event_consumer.assert_any_call(client, "RESUME", "some data")
        assert client._handshake_event.is_set()

    @hikari_test_helpers.timeout()
    async def test_when_opcode_is_DISPATCH_and_event_is_not_handled(self, client, exit_error):
        payload = {
            "op": client._Opcode.DISPATCH,
            "d": "some data",
            "t": "UNKNOWN",
            "s": 101,
        }
        client._receive_json = mock.AsyncMock(side_effect=[payload, exit_error])

        with pytest.raises(exit_error):
            await client._poll_events()

        client._event_consumer.assert_any_call(client, "UNKNOWN", "some data")

    @hikari_test_helpers.timeout()
    async def test_when_opcode_is_HEARTBEAT(self, client, exit_error):
        payload = {
            "op": client._Opcode.HEARTBEAT,
            "d": "some data",
        }
        client._receive_json = mock.AsyncMock(side_effect=[payload, exit_error])
        client._send_json = mock.AsyncMock()

        with pytest.raises(exit_error):
            await client._poll_events()

        client._send_json.assert_awaited_once_with({"op": client._Opcode.HEARTBEAT_ACK})

    @hikari_test_helpers.timeout()
    async def test_when_opcode_is_HEARTBEAT_ACK(self, client, exit_error):
        payload = {
            "op": client._Opcode.HEARTBEAT_ACK,
            "d": "some data",
        }
        client._receive_json = mock.AsyncMock(side_effect=[payload, exit_error])
        client._last_heartbeat_sent = 5

        with mock.patch.object(hikari_date, "monotonic", return_value=13):
            with pytest.raises(exit_error):
                await client._poll_events()

        assert client._heartbeat_latency == 8

    @hikari_test_helpers.timeout()
    async def test_when_opcode_is_RECONNECT(self, client):
        payload = {
            "op": client._Opcode.RECONNECT,
            "d": "some data",
        }
        client._receive_json = mock.AsyncMock(return_value=payload)

        with pytest.raises(client._Reconnect):
            await client._poll_events()

    @hikari_test_helpers.timeout()
    async def test_when_opcode_is_INVALID_SESSION(self, client):
        payload = {
            "op": client._Opcode.INVALID_SESSION,
            "d": "some data",
        }
        client._receive_json = mock.AsyncMock(return_value=payload)

        with pytest.raises(client._InvalidSession):
            await client._poll_events()

    @hikari_test_helpers.timeout()
    async def test_when_opcode_is_unknown(self, client, exit_error):
        payload = {
            "op": 101,
            "d": "some data",
        }
        client._receive_json = mock.AsyncMock(side_effect=[payload, exit_error])

        with pytest.raises(exit_error):
            await client._poll_events()

    @hikari_test_helpers.timeout()
    async def test_when_request_close_event_is_set(self, client, exit_error):
        client._request_close_event.set()

        await client._poll_events()


@pytest.mark.asyncio()
class TestExpectOpcode:
    async def test_when_correct_opcode_received(self, client):
        payload = {
            "op": client._Opcode.HEARTBEAT,
            "d": "some data",
        }
        client._receive_json = mock.AsyncMock(return_value=payload)

        assert await client._expect_opcode(client._Opcode.HEARTBEAT) == "some data"

    async def test_when_incorrect_opcode_received(self, client):
        payload = {
            "op": client._Opcode.HEARTBEAT_ACK,
            "d": "some data",
        }
        client._receive_json = mock.AsyncMock(return_value=payload)
        client._close_ws = mock.AsyncMock()

        with pytest.raises(errors.GatewayError):
            await client._expect_opcode(client._Opcode.HEARTBEAT)

        client._close_ws.assert_awaited_once_with(
            errors.ShardCloseCode.PROTOCOL_ERROR,
            f"Unexpected opcode {client._Opcode.HEARTBEAT_ACK} received, expected {client._Opcode.HEARTBEAT}",
        )


class StubResponse:
    extra = None

    def __init__(self, type, data):
        self.type = type
        self.data = data

    def __repr__(self):
        return f"Stub Reponse (type:{self.type})"


@pytest.mark.asyncio
class TestReceiveJson:
    async def test_when_type_is_BINARY(self, client):
        client._receive_raw = mock.AsyncMock(return_value=StubResponse(aiohttp.WSMsgType.BINARY, "some data"))
        client._receive_zlib_message = mock.AsyncMock(return_value=(4, '{"op": 1, "t": "some t"}'))

        assert await client._receive_json() == {"op": 1, "t": "some t"}

        client._receive_zlib_message.assert_awaited_once_with("some data")

    async def test_when_type_is_TEXT(self, client):
        client._receive_raw = mock.AsyncMock(
            return_value=StubResponse(aiohttp.WSMsgType.TEXT, '{"op": 1, "t": "some t"}')
        )

        assert await client._receive_json() == {"op": 1, "t": "some t"}

    async def test_when_type_is_UNKNOWN(self, client):
        client._receive_raw = mock.AsyncMock(return_value=StubResponse("some type", "some data"))
        with pytest.raises(TypeError):
            await client._receive_json()


@pytest.mark.asyncio
class TestReceiveZlibMessage:
    async def test_receive_zlib_message(self, client):
        client._receive_raw = mock.AsyncMock(
            side_effect=[
                StubResponse(aiohttp.WSMsgType.BINARY, 0),
                StubResponse(aiohttp.WSMsgType.BINARY, 255),
                StubResponse(aiohttp.WSMsgType.BINARY, 255),
            ]
        )
        mock_decompress_return = mock.Mock(decode=mock.Mock(return_value=b"final data"))
        client._zlib = mock.Mock()
        client._zlib.decompress = mock.Mock(return_value=mock_decompress_return)

        assert await client._receive_zlib_message(b"\x00") == (4, b"final data")
        client._zlib.decompress.assert_called_once_with(bytearray(b"\x00\x00\xff\xff"))
        mock_decompress_return.decode.assert_called_once_with("utf-8")

    async def test_when_next_received_is_not_BINARY(self, client):
        client._receive_raw = mock.AsyncMock(return_value=StubResponse(aiohttp.WSMsgType.TEXT, 0))

        with pytest.raises(errors.GatewayError):
            await client._receive_zlib_message(b"\x00")


@pytest.mark.asyncio
class TestReceiveRaw:
    async def test_receive_raw(self, client):
        message = StubResponse(aiohttp.WSMsgType.TEXT, "some text")
        client._ws = mock.Mock(receive=mock.AsyncMock(return_value=message))

        with mock.patch.object(hikari_date, "monotonic", return_value=123):
            assert await client._receive_raw() == message

        assert client._last_message_received == 123

    @pytest.mark.parametrize(
        ("received", "expected_error"),
        [
            (StubResponse(aiohttp.WSMsgType.CLOSE, 0), errors.GatewayServerClosedConnectionError),
            (StubResponse(aiohttp.WSMsgType.CLOSING, 0), "_SocketClosed"),
            (StubResponse(aiohttp.WSMsgType.CLOSED, 0), "_SocketClosed"),
            (StubResponse(aiohttp.WSMsgType.ERROR, 0), errors.GatewayError),
        ],
    )
    async def test_handling_types(self, client, received, expected_error):
        if isinstance(expected_error, str):
            expected_error = getattr(client, expected_error)

        client._ws = mock.Mock()
        client._ws.receive = mock.AsyncMock(return_value=received)
        client._ws.exception = mock.Mock(return_value=RuntimeError)

        with mock.patch.object(hikari_date, "monotonic", return_value=123):
            with pytest.raises(expected_error):
                await client._receive_raw()

        assert client._last_message_received == 123


@pytest.mark.asyncio
class TestSendJson:
    async def test_send_json(self, client):
        client._ratelimiter = mock.Mock(acquire=mock.AsyncMock())
        client._ws = mock.Mock(send_str=mock.AsyncMock())

        await client._send_json({"some": "payload"})

        client._ratelimiter.acquire.assert_awaited_once_with()
        client._ws.send_str.assert_awaited_once_with('{"some": "payload"}')


class TestLogDebugPayload:
    def test_when_logging_debug_disabled(self, client):
        client._logger.isEnabledFor = mock.Mock(return_value=False)
        client._logger.debug = mock.Mock()

        client._log_debug_payload({"some": "payload"}, "some message", "args")

        client._logger.debug.assert_not_called()

    def test_when_debug(self, client):
        client._logger.isEnabledFor = mock.Mock(return_value=True)
        client._logger.debug = mock.Mock()
        client._debug = True
        client._session_id = 123
        client._seq = 456

        client._log_debug_payload({"some": "payload"}, "some message %s", "args")

        client._logger.debug.assert_called_once_with(
            "some message %s [seq:%s, session:%s, size:%s] with raw payload: %s",
            "args",
            456,
            123,
            1,
            {"some": "payload"},
        )

    def test_when_not_debug(self, client):
        client._logger.isEnabledFor = mock.Mock(return_value=True)
        client._logger.debug = mock.Mock()
        client._debug = False
        client._session_id = 123
        client._seq = 456

        client._log_debug_payload({"some": "payload"}, "some message %s", "args")

        client._logger.debug.assert_called_once_with(
            "some message %s [seq:%s, session:%s, size:%s]", "args", 456, 123, 1
        )


class TestSerializeAndStorePresencePayload:
    @pytest.mark.parametrize("idle_since", [datetime.datetime.now(), None])
    @pytest.mark.parametrize("afk", [True, False])
    @pytest.mark.parametrize(
        "status",
        [presences.Status.DO_NOT_DISTURB, presences.Status.IDLE, presences.Status.ONLINE, presences.Status.OFFLINE],
    )
    @pytest.mark.parametrize("activity", [presences.Activity(name="foo"), None])
    def test_when_all_args_undefined(self, client, idle_since, afk, status, activity):
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
    def test_sets_state(self, client, idle_since, afk, status, activity):
        client._serialize_and_store_presence_payload(idle_since=idle_since, afk=afk, status=status, activity=activity)

        assert client._activity == activity
        assert client._idle_since == idle_since
        assert client._is_afk == afk
        assert client._status == status


class TestSerializeDatetime:
    def test_when_None(self, client):
        assert client._serialize_datetime(None) is None

    def test_when_not_None(self, client):
        date_obj = datetime.datetime(2020, 7, 22, 22, 22, 36, 988017, tzinfo=datetime.timezone.utc)
        assert client._serialize_datetime(date_obj) == 1595456556988


class TestSerializeActivity:
    def test_when_None(self, client):
        assert client._serialize_activity(None) is None

    def test_when_not_None(self, client):
        activity_obj = presences.Activity(name="foo", type=presences.ActivityType.PLAYING, url="some.url")
        assert client._serialize_activity(activity_obj) == {"name": "foo", "type": 0, "url": "some.url"}
