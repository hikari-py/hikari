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
import math

import mock
import pytest

from hikari import errors
from hikari.net import gateway
from hikari.net import http_client
from tests.hikari import hikari_test_helpers


@pytest.fixture()
def client():
    return gateway.Gateway(url="wss://gateway.discord.gg", token="lol", app=mock.MagicMock(), config=mock.MagicMock())


class TestInit:
    @pytest.mark.parametrize(
        ["v", "use_compression", "expect"],
        [
            (6, False, "v=6&encoding=json"),
            (6, True, "v=6&encoding=json&compress=zlib-stream"),
            (7, False, "v=7&encoding=json"),
            (7, True, "v=7&encoding=json&compress=zlib-stream"),
        ],
    )
    def test_url_is_correct_json(self, v, use_compression, expect):
        g = gateway.Gateway(
            app=mock.MagicMock(),
            config=mock.MagicMock(),
            token=mock.MagicMock(),
            url="wss://gaytewhuy.discord.meh",
            version=v,
            use_etf=False,
            use_compression=use_compression,
        )

        assert g.url == f"wss://gaytewhuy.discord.meh?{expect}"

    @pytest.mark.parametrize(["v", "use_compression"], [(6, False), (6, True), (7, False), (7, True),])
    def test_using_etf_is_unsupported(self, v, use_compression):
        with pytest.raises(NotImplementedError):
            gateway.Gateway(
                app=mock.MagicMock(),
                config=mock.MagicMock(),
                token=mock.MagicMock(),
                url="wss://erlpack-is-broken-lol.discord.meh",
                version=v,
                use_etf=True,
                use_compression=use_compression,
            )


class TestAppProperty:
    def test_returns_app(self):
        app = mock.MagicMock()
        g = gateway.Gateway(url="wss://gateway.discord.gg", token="lol", app=app, config=mock.MagicMock())
        assert g.app is app


class TestIsAliveProperty:
    def test_is_alive(self, client):
        client.connected_at = 1234
        assert client.is_alive

    def test_not_is_alive(self, client):
        client.connected_at = float("nan")
        assert not client.is_alive


@pytest.mark.asyncio
class TestStart:
    @pytest.mark.parametrize("shard_id", [0, 1, 2])
    @hikari_test_helpers.timeout()
    async def test_starts_task(self, event_loop, shard_id):
        g = gateway.Gateway(
            url="wss://gateway.discord.gg",
            token="lol",
            app=mock.MagicMock(),
            config=mock.MagicMock(),
            shard_id=shard_id,
            shard_count=100,
        )

        g._handshake_event = mock.MagicMock(asyncio.Event)
        g._run = mock.MagicMock()

        future = event_loop.create_future()
        future.set_result(None)

        with mock.patch.object(asyncio, "create_task", return_value=future) as create_task:
            result = await g.start()
            assert result is future
            create_task.assert_called_once_with(g._run(), name=f"shard {shard_id} keep-alive")

    @hikari_test_helpers.timeout()
    async def test_waits_for_ready(self, client):
        client._handshake_event = mock.MagicMock()
        client._handshake_event.wait = mock.AsyncMock()
        client._run = mock.AsyncMock()

        await client.start()
        client._handshake_event.wait.assert_awaited_once_with()


@pytest.mark.asyncio
class TestClose:
    async def test_when_already_closed_does_nothing(self, client):
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.MagicMock(return_value=True)

        await client.close()

        client._request_close_event.set.assert_not_called()

    @pytest.mark.parametrize("is_alive", [True, False])
    async def test_close_sets_request_close_event(self, client, is_alive):
        client.__dict__["is_alive"] = is_alive
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.MagicMock(return_value=False)

        await client.close()

        client._request_close_event.set.assert_called_once_with()

    @pytest.mark.parametrize("is_alive", [True, False])
    async def test_websocket_closed_if_not_None(self, client, is_alive):
        client.__dict__["is_alive"] = is_alive
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.MagicMock(return_value=False)
        client._close_ws = mock.AsyncMock()
        client._ws = mock.MagicMock()

        await client.close()

        client._close_ws.assert_awaited_once_with(client._GatewayCloseCode.RFC_6455_NORMAL_CLOSURE, "client shut down")

    @pytest.mark.parametrize("is_alive", [True, False])
    async def test_websocket_not_closed_if_None(self, client, is_alive):
        client.__dict__["is_alive"] = is_alive
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.MagicMock(return_value=False)
        client._close_ws = mock.AsyncMock()
        client._ws = None

        await client.close()

        client._close_ws.assert_not_called()


@pytest.mark.asyncio
class TestRun:
    @hikari_test_helpers.timeout()
    async def test_repeatedly_invokes_run_once_while_request_close_event_not_set(self, client):
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
        client._run_once = mock.AsyncMock()

        with pytest.raises(errors.GatewayClientClosedError):
            await client._run()

        assert i == 5
        assert client._run_once.call_count == i

    @hikari_test_helpers.timeout()
    async def test_sets_handshake_event_on_finish(self, client):
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._handshake_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.MagicMock(return_value=True)
        client._run_once = mock.AsyncMock()

        with pytest.raises(errors.GatewayClientClosedError):
            await client._run()

        client._handshake_event.set.assert_called_once_with()

    @hikari_test_helpers.timeout()
    async def test_closes_super_on_finish(self, client):
        client._request_close_event = mock.MagicMock(asyncio.Event)
        client._handshake_event = mock.MagicMock(asyncio.Event)
        client._request_close_event.is_set = mock.MagicMock(return_value=True)
        client._run_once = mock.AsyncMock()

        with mock.patch.object(http_client.HTTPClient, "close") as close_mock:
            with pytest.raises(errors.GatewayClientClosedError):
                await client._run()

        close_mock.assert_awaited_once_with(client)


@pytest.mark.asyncio
class TestRunOnce:
    @pytest.fixture
    def client(self):
        client = hikari_test_helpers.unslot_class(gateway.Gateway)(
            url="wss://gateway.discord.gg",
            token="lol",
            app=mock.MagicMock(),
            config=mock.MagicMock(),
            shard_id=3,
            shard_count=17,
        )
        client = hikari_test_helpers.mock_methods_on(
            client,
            except_=("_run_once", "_InvalidSession", "_Reconnect", "_SocketClosed", "_dispatch", "_now"),
            also_mock=["_backoff", "_handshake_event", "_request_close_event", "_logger",],
        )
        client._dispatch = mock.AsyncMock()
        # Disable backoff checking by making the condition a negative tautology.
        client._RESTART_RATELIMIT_WINDOW = -1
        # First call is used for backoff checks, the second call is used
        # for updating the _last_run_started_at attribute.
        # 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, ..., ..., ...
        client._now = mock.MagicMock(side_effect=map(lambda n: n / 2, range(1, 100)))
        return client

    @hikari_test_helpers.timeout()
    async def test_resets_close_event(self, client):
        with contextlib.suppress(Exception):
            await client._run_once()

        client._request_close_event.clear.assert_called_with()

    @hikari_test_helpers.timeout()
    async def test_backoff_and_waits_if_restarted_too_quickly(self, client):
        client._now = mock.MagicMock(return_value=60)
        client._RESTART_RATELIMIT_WINDOW = 30
        client._last_run_started_at = 40
        client._backoff.__next__ = mock.MagicMock(return_value=24.37)

        stack = contextlib.ExitStack()
        wait_for = stack.enter_context(mock.patch.object(asyncio, "wait_for"))
        create_task = stack.enter_context(mock.patch.object(asyncio, "create_task"))

        with stack:
            await client._run_once()

        client._backoff.__next__.assert_called_once_with()
        create_task.assert_called_once_with(client._request_close_event.wait(), name="gateway shard 3 backing off")
        wait_for.assert_called_once_with(create_task(), timeout=24.37)

    @hikari_test_helpers.timeout()
    async def test_closing_bot_during_backoff_immediately_interrupts_it(self, client):
        client._now = mock.MagicMock(return_value=60)
        client._RESTART_RATELIMIT_WINDOW = 30
        client._last_run_started_at = 40
        client._backoff.__next__ = mock.MagicMock(return_value=24.37)
        client._request_close_event = asyncio.Event()

        task = asyncio.create_task(client._run_once())

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
            assert task.result() is False

        finally:
            task.cancel()

    @hikari_test_helpers.timeout()
    async def test_backoff_does_not_trigger_if_not_restarting_in_small_window(self, client):
        client._now = mock.MagicMock(return_value=60)
        client._last_run_started_at = 40
        client._backoff.__next__ = mock.MagicMock(
            side_effect=AssertionError(
                "backoff was incremented, but this is not expected to occur in this test case scenario!"
            )
        )

        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(asyncio, "wait_for"))
        stack.enter_context(mock.patch.object(asyncio, "create_task"))

        with stack:
            # This will raise an assertion error if the backoff is incremented.
            await client._run_once()

    @hikari_test_helpers.timeout()
    async def test_last_run_started_at_set_to_current_time(self, client):
        # Windows does some batshit crazy stuff in perf_counter, like only
        # returning process time elapsed rather than monotonic time since
        # startup, so I guess I will put this random value here to show the
        # code doesn't really care what this value is contextually.
        client._last_run_started_at = -100_000

        await client._run_once()

        assert client._last_run_started_at == 1.0

    @hikari_test_helpers.timeout()
    async def test_ws_gets_created(self, client):
        await client._run_once()
        client._create_ws.assert_awaited_once_with(client.url)

    @hikari_test_helpers.timeout()
    async def test_connected_at_is_set_before_handshake_and_is_cancelled_after(self, client):
        assert math.isnan(client.connected_at)

        initial = -2.718281828459045
        client.connected_at = initial

        def ensure_connected_at_set():
            assert client.connected_at != initial

        client._handshake = mock.AsyncMock(wraps=ensure_connected_at_set)

        await client._run_once()

        assert math.isnan(client.connected_at)

    @hikari_test_helpers.timeout()
    async def test_zlib_decompressobj_set(self, client):
        assert client._zlib is None
        await client._run_once()
        assert client._zlib is not None

    @hikari_test_helpers.timeout()
    async def test_handshake_event_cleared(self, client):
        client._handshake_event = asyncio.Event()
        client._handshake_event.set()
        await client._run_once()
        assert not client._handshake_event.is_set()

    @hikari_test_helpers.timeout()
    async def test_handshake_invoked(self, client):
        await client._run_once()
        client._handshake.assert_awaited_once_with()

    @hikari_test_helpers.timeout()
    async def test_poll_events_invoked(self, client):
        await client._run_once()
        client._poll_events.assert_awaited_once_with()

    @hikari_test_helpers.timeout()
    async def test_happy_path_returns_False(self, client):
        assert await client._run_once() is False
