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

import aiohttp.client_reqrep
import mock
import pytest

from hikari import config
from hikari import errors
from hikari.impl import shard
from hikari.models import presences
from hikari.utilities import date as hikari_date
from hikari.utilities import undefined
from tests.hikari import client_session_stub
from tests.hikari import hikari_test_helpers


@pytest.fixture()
def http_settings():
    return mock.create_autospec(spec=config.HTTPSettings, spec_set=True)


@pytest.fixture()
def proxy_settings():
    return mock.create_autospec(spec=config.ProxySettings, spec_set=True)


@pytest.fixture()
def client_session():
    stub = client_session_stub.ClientSessionStub()
    with mock.patch.object(aiohttp, "ClientSession", new=stub):
        yield stub


@pytest.fixture()
def client(http_settings, proxy_settings):
    return hikari_test_helpers.unslot_class(shard.GatewayShardImpl)(
        url="wss://gateway.discord.gg",
        token="lol",
        app=mock.Mock(),
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
            app=mock.Mock(),
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
                app=mock.Mock(),
                http_settings=http_settings,
                proxy_settings=proxy_settings,
                token=mock.Mock(),
                url="wss://erlpack-is-broken-lol.discord.meh",
                version=v,
                data_format="etf",
                compression=compression,
            )


class TestAppProperty:
    def test_returns_app(self, http_settings, proxy_settings):
        app = mock.Mock()
        g = shard.GatewayShardImpl(
            url="wss://gateway.discord.gg",
            token="lol",
            app=app,
            http_settings=http_settings,
            proxy_settings=proxy_settings,
        )
        assert g.app is app


class TestIsAliveProperty:
    def test_is_alive(self, client):
        client._connected_at = 1234
        assert client.is_alive

    def test_not_is_alive(self, client):
        client._connected_at = None
        assert not client.is_alive


@pytest.mark.asyncio
class TestStart:
    @pytest.mark.parametrize("shard_id", [0, 1, 2])
    @hikari_test_helpers.timeout()
    async def test_starts_task(self, event_loop, shard_id, http_settings=http_settings, proxy_settings=proxy_settings):
        g = hikari_test_helpers.unslot_class(shard.GatewayShardImpl)(
            url="wss://gateway.discord.gg",
            token="lol",
            app=mock.Mock(),
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
            app=mock.Mock(),
            http_settings=http_settings,
            proxy_settings=proxy_settings,
        )

    async def test_when_already_closed_does_nothing(self, client):
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.MagicMock(return_value=True)

        await client.close()

        client._request_close_event.set.assert_not_called()

    @pytest.mark.parametrize("is_alive", [True, False])
    async def test_close_sets_request_close_event(self, client, is_alive):
        client.__dict__["_is_alive"] = is_alive
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.MagicMock(return_value=False)

        await client.close()

        client._request_close_event.set.assert_called_once_with()

    @pytest.mark.parametrize("is_alive", [True, False])
    async def test_websocket_closed_if_not_None(self, client, is_alive):
        client.__dict__["_is_alive"] = is_alive
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.MagicMock(return_value=False)
        client._close_ws = mock.AsyncMock()
        client._ws = mock.Mock()

        await client.close()

        client._close_ws.assert_awaited_once_with(client._CloseCode.RFC_6455_NORMAL_CLOSURE, "client shut down")

    @pytest.mark.parametrize("is_alive", [True, False])
    async def test_websocket_not_closed_if_None(self, client, is_alive):
        client.__dict__["_is_alive"] = is_alive
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.MagicMock(return_value=False)
        client._close_ws = mock.AsyncMock()
        client._ws = None

        await client.close()

        client._close_ws.assert_not_called()


@pytest.mark.asyncio
class TestRun:
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
        client._request_close_event.is_set = mock.MagicMock(return_value=True)
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
            app=mock.Mock(),
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
                "_dispatch",
                "_CloseCode",
                "_Opcode",
            ),
            also_mock=["_backoff", "_handshake_event", "_request_close_event", "_logger"],
        )
        client._dispatch = mock.AsyncMock()
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
        [(True, True, True), (True, False, True), (False, True, False), (False, False, False),],
    )
    @hikari_test_helpers.timeout()
    async def test_socket_closed_resets_backoff(
        self, client, zombied, request_close, expect_backoff_called, client_session
    ):
        client._request_close_event.is_set = mock.MagicMock(return_value=request_close)

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
        client._request_close_event.is_set = mock.MagicMock(return_value=request_close)
        client._run_once = mock.AsyncMock(side_effect=shard.GatewayShardImpl._SocketClosed())
        assert await client._run_once_shielded(client_session) is not request_close

    @hikari_test_helpers.timeout()
    async def test_ClientConnectionError_is_restartable(self, client, client_session):
        key = aiohttp.client_reqrep.ConnectionKey(
            host="localhost", port=6996, is_ssl=False, ssl=None, proxy=None, proxy_auth=None, proxy_headers_hash=69420,
        )
        error = aiohttp.ClientConnectorError(key, OSError())

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
        client._close_ws.assert_awaited_once_with(
            shard.GatewayShardImpl._CloseCode.DO_NOT_INVALIDATE_SESSION, "invalid session (resume)"
        )

    @hikari_test_helpers.timeout()
    async def test_invalid_session_no_resume_invalidates_session(self, client, client_session):
        client._run_once = mock.AsyncMock(side_effect=shard.GatewayShardImpl._InvalidSession(False))
        await client._run_once_shielded(client_session)
        client._close_ws.assert_awaited_once_with(
            shard.GatewayShardImpl._CloseCode.RFC_6455_NORMAL_CLOSURE, "invalid session (no resume)"
        )

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
        client._request_close_event.is_set = mock.MagicMock(return_value=request_close)

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
            shard.GatewayShardImpl._CloseCode.RFC_6455_UNEXPECTED_CONDITION, "unexpected error occurred"
        )


@pytest.mark.asyncio
class TestRunOnce:
    @pytest.fixture
    def client(self, http_settings, proxy_settings):
        client = hikari_test_helpers.unslot_class(shard.GatewayShardImpl)(
            url="wss://gateway.discord.gg",
            token="lol",
            app=mock.Mock(),
            shard_id=3,
            shard_count=17,
            http_settings=http_settings,
            proxy_settings=proxy_settings,
        )
        client = hikari_test_helpers.mock_methods_on(
            client,
            except_=("_run_once", "_InvalidSession", "_Reconnect", "_SocketClosed", "_CloseCode", "_Opcode",),
            also_mock=["_backoff", "_handshake_event", "_request_close_event", "_logger",],
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
        client._backoff.__next__ = mock.MagicMock(return_value=24.37)

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
        client._backoff.__next__ = mock.MagicMock(return_value=24.37)
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
            client._backoff.__next__ = mock.MagicMock(
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

        client._dispatch.assert_any_call("CONNECTED", {})

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

        task = mock.create_autospec(asyncio.Task)

        with mock.patch.object(asyncio, "create_task", return_value=task):
            with pytest.raises(Exception):
                await client._run_once(client_session)

        task.cancel.assert_called_once_with()

    async def test_dispatches_disconnect_if_connected(self, client, client_session):
        await client._run_once(client_session)
        client._dispatch.assert_any_call("CONNECTED", {})
        client._dispatch.assert_any_call("DISCONNECTED", {})

    async def test_no_dispatch_disconnect_if_not_connected(self, client, client_session):
        client_session.ws_connect = mock.MagicMock(side_effect=RuntimeError)
        with pytest.raises(RuntimeError):
            await client._run_once(client_session)
        client._dispatch.assert_not_called()

    async def test_connected_at_reset_to_None_on_exit(self, client, client_session):
        await client._run_once(client_session)
        assert client._connected_at is None


@pytest.mark.asyncio
class TestUpdatePresence:
    @pytest.fixture
    def client(self, proxy_settings, http_settings):
        client = hikari_test_helpers.unslot_class(shard.GatewayShardImpl)(
            url="wss://gateway.discord.gg",
            token="lol",
            app=mock.Mock(),
            http_settings=http_settings,
            proxy_settings=proxy_settings,
            shard_id=3,
            shard_count=17,
        )
        return hikari_test_helpers.mock_methods_on(
            client,
            except_=("update_presence", "_InvalidSession", "_Reconnect", "_SocketClosed", "_CloseCode", "_Opcode",),
        )

    async def test_update_presence_transforms_all_params(self, client):
        now = datetime.datetime.now()
        idle_since = now
        afk = False
        activity = presences.Activity(type=presences.ActivityType.PLAYING, name="with my saxaphone")
        status = presences.Status.DO_NOT_DISTURB

        result = object()
        client._app.event_factory.serialize_gateway_presence = mock.MagicMock(return_value=result)

        await client.update_presence(
            idle_since=idle_since, afk=afk, activity=activity, status=status,
        )

        client._app.event_factory.serialize_gateway_presence.assert_called_once_with(
            idle_since=idle_since, afk=afk, activity=activity, status=status,
        )

        client._send_json.assert_awaited_once_with({"op": shard.GatewayShardImpl._Opcode.PRESENCE_UPDATE, "d": result})

    @pytest.mark.parametrize("idle_since", [undefined.UNDEFINED, datetime.datetime.now()])
    @pytest.mark.parametrize("afk", [undefined.UNDEFINED, True, False])
    @pytest.mark.parametrize(
        "status",
        [
            undefined.UNDEFINED,
            presences.Status.DO_NOT_DISTURB,
            presences.Status.IDLE,
            presences.Status.ONLINE,
            presences.Status.OFFLINE,
        ],
    )
    @pytest.mark.parametrize("activity", [undefined.UNDEFINED, presences.Activity(name="foo"), None])
    async def test_update_presence_ignores_undefined(self, client, idle_since, afk, status, activity):
        result = object()
        client_activity = mock.Mock()
        client_idle_since = mock.Mock()
        client_afk = mock.Mock()
        client_status = mock.Mock()

        client._activity = client_activity
        client._idle_since = client_idle_since
        client._is_afk = client_afk
        client._status = client_status

        client._app.event_factory.serialize_gateway_presence = mock.MagicMock(return_value=result)

        await client.update_presence(
            idle_since=idle_since, afk=afk, status=status, activity=activity,
        )

        client._app.event_factory.serialize_gateway_presence.assert_called_once_with(
            idle_since=idle_since if idle_since is not undefined.UNDEFINED else client_idle_since,
            afk=afk if afk is not undefined.UNDEFINED else client_afk,
            activity=activity if activity is not undefined.UNDEFINED else client_activity,
            status=status if status is not undefined.UNDEFINED else client_status,
        )

    async def test_update_presence_has_defaults_for_undefined_on_object(self, client):
        result = object()

        client._activity = undefined.UNDEFINED
        client._idle_since = undefined.UNDEFINED
        client._is_afk = undefined.UNDEFINED
        client._status = undefined.UNDEFINED

        client._app.event_factory.serialize_gateway_presence = mock.MagicMock(return_value=result)

        await client.update_presence(
            idle_since=undefined.UNDEFINED,
            afk=undefined.UNDEFINED,
            status=undefined.UNDEFINED,
            activity=undefined.UNDEFINED,
        )

        client._app.event_factory.serialize_gateway_presence.assert_called_once_with(
            idle_since=None, afk=False, activity=None, status=presences.Status.ONLINE,
        )


@pytest.mark.asyncio
class TestUpdateVoiceState:
    @pytest.fixture
    def client(self, proxy_settings, http_settings):
        client = hikari_test_helpers.unslot_class(shard.GatewayShardImpl)(
            url="wss://gateway.discord.gg",
            token="lol",
            app=mock.Mock(),
            http_settings=http_settings,
            proxy_settings=proxy_settings,
            shard_id=3,
            shard_count=17,
        )
        return hikari_test_helpers.mock_methods_on(
            client,
            except_=("update_voice_state", "_InvalidSession", "_Reconnect", "_SocketClosed", "_CloseCode", "_Opcode",),
        )

    @pytest.mark.parametrize("channel", ["12345", None])
    @pytest.mark.parametrize("self_deaf", [True, False])
    @pytest.mark.parametrize("self_mute", [True, False])
    async def test_invoked(self, client, channel, self_deaf, self_mute):
        await client.update_voice_state("69696", channel, self_deaf=self_deaf, self_mute=self_mute)
        client._app.event_factory.serialize_gateway_voice_state_update("69696", channel)

    async def test_serialized_result_sent_on_websocket(self, client):
        payload = mock.Mock()
        client._app.event_factory.serialize_gateway_voice_state_update = mock.MagicMock(return_value=payload)

        await client.update_voice_state("6969420", "12345")

        client._send_json.assert_awaited_once_with(
            {"op": shard.GatewayShardImpl._Opcode.VOICE_STATE_UPDATE, "d": payload}
        )


@pytest.mark.asyncio
class TestCloseWs:
    async def test_when_connected(self, client):
        client._ws = mock.create_autospec(aiohttp.ClientWebSocketResponse, spec_set=True)

        await client._close_ws(6969420, "you got yeeted")

        client._ws.close.assert_awaited_once_with(code=6969420, message=b"you got yeeted")

    async def test_when_disconnected(self, client):
        client._ws = None
        await client._close_ws(6969420, "you got yeeted")
        # Do not expect any error or anything to happen.
        assert True


@pytest.mark.asyncio
class TestHandshake:
    # TODO: this
    ...
