#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
import math
import signal

import pytest

import asyncmock as mock

from hikari import client as _client
from hikari import client_options as _client_options
from hikari.net import gateway
from hikari.net import http_api
from hikari.orm import fabric as _fabric
from hikari.orm.gateway import basic_chunker_impl
from hikari.orm.gateway import dispatching_event_adapter_impl
from hikari.orm.http import http_adapter_impl
from hikari.orm.models import gateway_bot
from hikari.orm.state import state_registry_impl
from tests.hikari import _helpers


class TestClient:
    # Lets us prevent "unclosed session" warnings, etc.
    @pytest.fixture()
    def patched_client_session_class(self):
        with mock.patch("aiohttp.ClientSession") as cs:
            yield cs

    @pytest.mark.asyncio
    async def test_init_new_application_fabric_initializes_fabric(self):
        client = _helpers.mock_methods_on(_client.Client("token"), except_=("_init_new_application_fabric",))

        await client._init_new_application_fabric()
        assert isinstance(client._fabric, _fabric.Fabric)
        assert client._fabric.state_registry == await client._new_state_registry()
        assert client._fabric.event_handler == await client._new_event_handler()
        assert client._fabric.http_api == await client._new_http_api()
        assert client._fabric.http_adapter == await client._new_http_adapter()
        assert client._fabric.gateways == await client._new_shard_map()
        assert client._fabric.chunker == await client._new_chunker()

    @pytest.mark.asyncio
    async def test_failing_to_initialize_application_fabric_closes_self(self):
        client = _helpers.mock_methods_on(_client.Client("token"), except_=("_init_new_application_fabric",))
        client._new_state_registry = mock.MagicMock(side_effect=ConnectionRefusedError)

        with contextlib.suppress(RuntimeError):
            await client._init_new_application_fabric()

        client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_failing_to_initialize_application_fabric_destroys_fabric(self):
        client = _helpers.mock_methods_on(_client.Client("token"), except_=("_init_new_application_fabric",))
        client._new_state_registry = mock.MagicMock(side_effect=ConnectionRefusedError)

        with contextlib.suppress(RuntimeError):
            await client._init_new_application_fabric()

        assert client._fabric is None

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=RuntimeError)
    async def test_failing_to_initialize_application_fabric_raises_RuntimeError(self):
        client = _helpers.mock_methods_on(_client.Client("token"), except_=("_init_new_application_fabric",))
        client._new_state_registry = mock.MagicMock(side_effect=ConnectionRefusedError)

        await client._init_new_application_fabric()

    @pytest.mark.asyncio
    async def test_new_state_registry_delegates_correctly(self):
        client_opts = mock.MagicMock(spec_set=_client_options.ClientOptions)
        client = _client.Client("token", client_opts)
        client._fabric = mock.MagicMock(spec_set=_fabric.Fabric)

        expected_registry = mock.MagicMock(spec_set=state_registry_impl.StateRegistryImpl)
        with mock.patch(
            "hikari.orm.state.state_registry_impl.StateRegistryImpl", return_value=expected_registry
        ) as StateRegistry:
            result = await client._new_state_registry()

        StateRegistry.assert_called_once_with(
            client._fabric, client_opts.max_message_cache_size, client_opts.max_user_dm_channel_count,
        )

        assert result is expected_registry

    @pytest.mark.asyncio
    async def test_new_event_handler_delegates_correctly(self):
        client_opts = mock.MagicMock(spec_set=_client_options.ClientOptions)
        client = _client.Client("token", client_opts)
        client._fabric = mock.MagicMock(spec_set=_fabric.Fabric)

        expected_handler = mock.MagicMock(spec_set=dispatching_event_adapter_impl.DispatchingEventAdapterImpl)
        with mock.patch(
            "hikari.orm.gateway.dispatching_event_adapter_impl.DispatchingEventAdapterImpl",
            return_value=expected_handler,
        ) as DispatchingEventAdapterImpl:
            result = await client._new_event_handler()

        DispatchingEventAdapterImpl.assert_called_once_with(
            client._fabric, client.dispatch, request_chunks_mode=client_opts.chunk_mode
        )

        assert result is expected_handler

    @pytest.mark.asyncio
    async def test_new_http_api_delegates_correctly(self):
        client_opts = mock.MagicMock(spec_set=_client_options.ClientOptions)
        client = _client.Client("token", client_opts)
        client._fabric = mock.MagicMock(spec_set=_fabric.Fabric)

        expected_http = mock.MagicMock(spec_set=http_api.HTTPAPIImpl)
        with mock.patch("hikari.net.http_api.HTTPAPIImpl", return_value=expected_http) as HTTPAPIImpl:
            result = await client._new_http_api()

        HTTPAPIImpl.assert_called_once_with(
            allow_redirects=client_opts.allow_redirects,
            max_retries=client_opts.http_max_retries,
            token="token",
            connector=client_opts.connector,
            proxy_headers=client_opts.proxy_headers,
            proxy_auth=client_opts.proxy_auth,
            proxy_url=client_opts.proxy_url,
            ssl_context=client_opts.ssl_context,
            verify_ssl=client_opts.verify_ssl,
            timeout=client_opts.http_timeout,
        )

        assert result is expected_http

    @pytest.mark.asyncio
    async def test_new_http_adapter_delegates_correctly(self):
        client_opts = mock.MagicMock(spec_set=_client_options.ClientOptions)
        client = _client.Client("token", client_opts)
        client._fabric = mock.MagicMock(spec_set=_fabric.Fabric)

        expected_adapter = mock.MagicMock(spec_set=http_adapter_impl.HTTPAdapterImpl)
        with mock.patch(
            "hikari.orm.http.http_adapter_impl.HTTPAdapterImpl", return_value=expected_adapter
        ) as HTTPAdapterImpl:
            result = await client._new_http_adapter()

        HTTPAdapterImpl.assert_called_once_with(client._fabric,)

        assert result is expected_adapter

    @pytest.mark.asyncio
    async def test_new_shard_map_for_autosharded_gateway_no_shards(self):
        client_opts = mock.MagicMock(spec_set=_client_options.ClientOptions)
        client_opts.shards = _client_options.AUTO_SHARD
        client = _client.Client("token", client_opts)
        client._fabric = mock.MagicMock(spec_set=_fabric.Fabric)
        session_start_limit_pl = _helpers.mock_model(
            gateway_bot.SessionStartLimit,
            used=10,
            remaining=5,
            reset_at=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        gateway_bot_pl = _helpers.mock_model(
            gateway_bot.GatewayBot, session_start_limit=session_start_limit_pl, shards=1, url="local://some-url",
        )
        client._fabric.http_adapter.fetch_gateway_bot = mock.AsyncMock(return_value=gateway_bot_pl)

        gateway_client = mock.MagicMock(spec_set=gateway.GatewayClient)
        with mock.patch("hikari.net.gateway.GatewayClient", return_value=gateway_client) as GatewayClient:
            shard_map = await client._new_shard_map()

        assert shard_map == {None: gateway_client}

        GatewayClient.assert_called_once_with(
            token="token",
            uri=gateway_bot_pl.url,
            connector=client_opts.connector,
            proxy_headers=client_opts.proxy_headers,
            proxy_auth=client_opts.proxy_auth,
            proxy_url=client_opts.proxy_url,
            ssl_context=client_opts.ssl_context,
            verify_ssl=client_opts.verify_ssl,
            http_timeout=client_opts.http_timeout,
            max_persistent_buffer_size=client_opts.max_persistent_gateway_buffer_size,
            large_threshold=client_opts.large_guild_threshold,
            enable_guild_subscription_events=client_opts.enable_guild_subscription_events,
            intents=client_opts.intents,
            initial_presence=client_opts.presence.to_dict(),
            shard_id=None,
            shard_count=1,
            gateway_event_dispatcher=client._fabric.event_handler.consume_raw_event,
            internal_event_dispatcher=client._fabric.event_handler.consume_raw_event,
        )

    @pytest.mark.asyncio
    async def test_new_shard_map_for_autosharded_gateway_many_shards(self):
        client_opts = mock.MagicMock(spec_set=_client_options.ClientOptions)
        client_opts.shards = _client_options.AUTO_SHARD
        client = _client.Client("token", client_opts)
        client._fabric = mock.MagicMock(spec_set=_fabric.Fabric)
        session_start_limit_pl = _helpers.mock_model(
            gateway_bot.SessionStartLimit,
            used=10,
            remaining=5,
            reset_at=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        gateway_bot_pl = _helpers.mock_model(
            gateway_bot.GatewayBot, session_start_limit=session_start_limit_pl, shards=50, url="local://some-url",
        )
        client._fabric.http_adapter.fetch_gateway_bot = mock.AsyncMock(return_value=gateway_bot_pl)

        gateway_clients = [mock.MagicMock(spec_set=gateway.GatewayClient) for _ in range(gateway_bot_pl.shards)]

        with mock.patch(
            "hikari.net.gateway.GatewayClient", wraps=lambda *a, shard_id, **k: gateway_clients[shard_id]
        ) as GatewayClient:
            shard_map = await client._new_shard_map()

        for shard_id in range(gateway_bot_pl.shards):
            assert shard_map[shard_id] == gateway_clients[shard_id]

            GatewayClient.assert_any_call(
                token="token",
                uri=gateway_bot_pl.url,
                connector=client_opts.connector,
                proxy_headers=client_opts.proxy_headers,
                proxy_auth=client_opts.proxy_auth,
                proxy_url=client_opts.proxy_url,
                ssl_context=client_opts.ssl_context,
                verify_ssl=client_opts.verify_ssl,
                http_timeout=client_opts.http_timeout,
                max_persistent_buffer_size=client_opts.max_persistent_gateway_buffer_size,
                large_threshold=client_opts.large_guild_threshold,
                enable_guild_subscription_events=client_opts.enable_guild_subscription_events,
                intents=client_opts.intents,
                initial_presence=client_opts.presence.to_dict(),
                shard_id=shard_id,
                shard_count=50,
                gateway_event_dispatcher=client._fabric.event_handler.consume_raw_event,
                internal_event_dispatcher=client._fabric.event_handler.consume_raw_event,
            )

    @pytest.mark.asyncio
    async def test_new_shard_map_for_manually_configured_no_shards(self, event_loop):
        client_opts = mock.MagicMock(spec_set=_client_options.ClientOptions)
        client_opts.shards = None
        client = _client.Client("token", client_opts)
        client._fabric = mock.MagicMock(spec_set=_fabric.Fabric)
        gateway_url = "local://some-url"
        gateway_url_future = event_loop.create_future()
        gateway_url_future.set_result(gateway_url)
        client._fabric.http_adapter.gateway_url = gateway_url_future

        gateway_client = mock.MagicMock(spec_set=gateway.GatewayClient)
        with mock.patch("hikari.net.gateway.GatewayClient", return_value=gateway_client) as GatewayClient:
            shard_map = await client._new_shard_map()

        assert shard_map == {None: gateway_client}

        GatewayClient.assert_called_once_with(
            token="token",
            uri=gateway_url,
            connector=client_opts.connector,
            proxy_headers=client_opts.proxy_headers,
            proxy_auth=client_opts.proxy_auth,
            proxy_url=client_opts.proxy_url,
            ssl_context=client_opts.ssl_context,
            verify_ssl=client_opts.verify_ssl,
            http_timeout=client_opts.http_timeout,
            max_persistent_buffer_size=client_opts.max_persistent_gateway_buffer_size,
            large_threshold=client_opts.large_guild_threshold,
            enable_guild_subscription_events=client_opts.enable_guild_subscription_events,
            intents=client_opts.intents,
            initial_presence=client_opts.presence.to_dict(),
            shard_id=None,
            shard_count=1,
            gateway_event_dispatcher=client._fabric.event_handler.consume_raw_event,
            internal_event_dispatcher=client._fabric.event_handler.consume_raw_event,
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ["shards", "shard_count", "expected_count"],
        [(range(1, 15), 20, 14), (slice(1, 15, 2), 20, 7), ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 10, 10)],
    )
    async def test_new_shard_map_for_manually_configured_gateway_many_shards(
        self, event_loop, shards, shard_count, expected_count
    ):
        client_opts = mock.MagicMock(spec_set=_client_options.ClientOptions)
        client_opts.shards = _client_options.ShardOptions(shards, shard_count)
        client = _client.Client("token", client_opts)
        client._fabric = mock.MagicMock(spec_set=_fabric.Fabric)
        gateway_url = "local://some-url"
        gateway_url_future = event_loop.create_future()
        gateway_url_future.set_result(gateway_url)
        client._fabric.http_adapter.gateway_url = gateway_url_future

        gateway_clients = mock.MagicMock()
        with mock.patch(
            "hikari.net.gateway.GatewayClient", wraps=lambda *a, shard_id, **k: gateway_clients(shard_id)
        ) as GatewayClient:
            shard_map = await client._new_shard_map()

        assert len(shard_map) == expected_count

        for shard_id in shard_map:
            assert shard_map[shard_id] == gateway_clients(shard_id)
            GatewayClient.assert_any_call(
                token="token",
                uri=gateway_url,
                connector=client_opts.connector,
                proxy_headers=client_opts.proxy_headers,
                proxy_auth=client_opts.proxy_auth,
                proxy_url=client_opts.proxy_url,
                ssl_context=client_opts.ssl_context,
                verify_ssl=client_opts.verify_ssl,
                http_timeout=client_opts.http_timeout,
                max_persistent_buffer_size=client_opts.max_persistent_gateway_buffer_size,
                large_threshold=client_opts.large_guild_threshold,
                enable_guild_subscription_events=client_opts.enable_guild_subscription_events,
                intents=client_opts.intents,
                initial_presence=client_opts.presence.to_dict(),
                shard_id=shard_id,
                shard_count=shard_count,
                gateway_event_dispatcher=client._fabric.event_handler.consume_raw_event,
                internal_event_dispatcher=client._fabric.event_handler.consume_raw_event,
            )

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=RuntimeError)
    async def test_new_shard_map_for_unknown_shard_field_raises_RuntimeError(self):
        client_opts = mock.MagicMock(spec_set=_client_options.ClientOptions)
        client_opts.shards = 180
        client = _client.Client("token", client_opts)
        client._fabric = mock.MagicMock(spec_set=_fabric.Fabric)
        await client._new_shard_map()

    @pytest.mark.asyncio
    async def test_new_chunker_delegates_correctly(self):
        client_opts = mock.MagicMock(spec_set=_client_options.ClientOptions)
        client = _client.Client("token", client_opts)
        client._fabric = mock.MagicMock(spec_set=_fabric.Fabric)

        expected_chunker = mock.MagicMock(spec_set=basic_chunker_impl.BasicChunkerImpl)
        with mock.patch(
            "hikari.orm.gateway.basic_chunker_impl.BasicChunkerImpl", return_value=expected_chunker,
        ) as BasicChunkerImpl:
            result = await client._new_chunker()

        BasicChunkerImpl.assert_called_once_with(client._fabric)

        assert result is expected_chunker

    @pytest.mark.asyncio
    async def test_run_shard_when_successful_run(self):
        client = _client.Client("token")

        class Shard:
            def __init__(self):
                self.shard_id = 123

            async def run(self):
                await asyncio.sleep(0.01)
                return "ayy"

        shard = Shard()

        actual_shard, result = await client._run_shard(shard)
        assert actual_shard is shard
        assert result == "ayy"

    @pytest.mark.asyncio
    async def test_run_shard_when_failed_run(self):
        client = _client.Client("token")
        ex = RuntimeError("ARGH!!!")

        class Shard:
            def __init__(self):
                self.shard_id = 123

            async def run(self):
                await asyncio.sleep(0.01)
                raise ex

        shard = Shard()

        actual_shard, result = await client._run_shard(shard)
        assert actual_shard is shard
        assert result == ex

    @pytest.mark.asyncio
    async def test_start_shard_and_wait_ready_when_ready_satisfied(self, event_loop):
        assert event_loop, "this isn't used but it ensures pytest doesn't close it early and fail the test"
        client = _client.Client("token")

        class Shard:
            def __init__(self):
                self.ready_event = asyncio.Event()
                self.shard_id = 123

            async def run(self):
                await asyncio.sleep(0.01)
                return "yeet"

        shard = Shard()
        shard.ready_event.set()
        actual_shard, task = await client._start_shard_and_wait_ready(shard)
        assert actual_shard is shard
        actual_shard_again, result = await task
        assert actual_shard_again is shard
        assert result == "yeet"

    @pytest.mark.asyncio
    async def test_start_shard_and_wait_ready_when_ready_never_reached_because_of_exception(self):
        client = _client.Client("token")
        ex = RuntimeError("yeeet")

        class Shard:
            def __init__(self):
                self.ready_event = asyncio.Event()
                self.shard_id = 123

            async def run(self):
                raise ex

        shard = Shard()

        try:
            await client._start_shard_and_wait_ready(shard)
            assert False
        except RuntimeError as thrown_ex:
            assert thrown_ex.__cause__ is ex

    @pytest.mark.asyncio
    async def test_start_shard_and_wait_ready_when_ready_never_reached_because_it_just_finished(self):
        client = _client.Client("token")

        class Shard:
            def __init__(self):
                self.ready_event = asyncio.Event()
                self.shard_id = 123

            async def run(self):
                return "yeeeeeet"

        shard = Shard()

        try:
            await client._start_shard_and_wait_ready(shard)
            assert False
        except RuntimeError as thrown_ex:
            assert thrown_ex.__cause__ is None

    @_helpers.run_in_own_thread
    def test_run_invokes_run_async_in_event_loop(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        client = _client.Client("token")
        client.run_async = mock.AsyncMock()
        client.run()
        client.run_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_await_registers_signals(self, event_loop):
        client = _client.Client("token")
        client.start = mock.AsyncMock()
        client.join = mock.AsyncMock()
        event_loop.add_signal_handler = mock.MagicMock(wraps=event_loop.add_signal_handler)
        await client.run_async()
        for signal_id in client._SHUTDOWN_SIGNALS:
            for (actual_signal_id, _cb, signal_id_to_pass, event_loop_to_pass), _ in event_loop.add_signal_handler.call_args_list:
                if signal_id == actual_signal_id:
                    assert signal_id_to_pass == actual_signal_id and signal_id_to_pass == signal_id
                    assert event_loop_to_pass is event_loop
                    break
            else:
                assert False, f"Signal {signal_id} was not registered"

    @pytest.mark.asyncio
    async def test_run_await_unregisters_signals(self, event_loop):
        client = _client.Client("token")
        client.start = mock.AsyncMock()
        client.join = mock.AsyncMock()
        event_loop.remove_signal_handler = mock.MagicMock()

        await client.run_async()
        for signal_id in client._SHUTDOWN_SIGNALS:
            event_loop.remove_signal_handler.assert_any_call(signal_id)

    @pytest.mark.asyncio
    async def test_run_await_KeyboardInterrupt_delegates_to_SIGINT_handler(self, event_loop):
        client = _client.Client("token")
        assert signal.SIGINT in client._SHUTDOWN_SIGNALS, "we cant delegate to SIGINT if SIGINT isn't a tracked signal!"

        client._signal_handler = mock.MagicMock()

        client.start = mock.AsyncMock()
        client.join = mock.AsyncMock(side_effect=KeyboardInterrupt)

        await client.run_async()

        client._signal_handler.assert_any_call(signal.SIGINT, event_loop)

    @pytest.mark.asyncio
    async def test_signal_handler_closes_threadsafe(self):
        client = _client.Client("token")
        loop = mock.MagicMock()
        client.close = mock.MagicMock()
        with mock.patch("asyncio.run_coroutine_threadsafe") as run_coroutine_threadsafe:
            with mock.patch("hikari.internal_utilities.compat.signal.strsignal"):
                client._signal_handler(mock.MagicMock(spec_set=signal.Signals), loop)
        run_coroutine_threadsafe.assert_called_once_with(client.close(), loop)

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=RuntimeError)
    async def test_start_refuses_to_run_if_already_running(self):
        client = _client.Client("token")
        client._shard_tasks = ...
        await client.start()

    @pytest.mark.asyncio
    async def test_start_initializes_fabric(self, event_loop):
        def make_finished_future():
            f = event_loop.create_future()
            f.set_result(None)
            return f

        client = _client.Client("token")
        client._init_new_application_fabric = mock.AsyncMock()
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {0: mock.MagicMock(), 1: mock.MagicMock()}
        client._start_shard_and_wait_ready = mock.AsyncMock(
            side_effect=[
                (client._fabric.gateways[0], make_finished_future()),
                (client._fabric.gateways[1], make_finished_future()),
            ]
        )
        await client.start()

        client._init_new_application_fabric.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_start_waits_for_ready(self, event_loop):
        def make_finished_future():
            f = event_loop.create_future()
            f.set_result(None)
            return f

        client = _client.Client("token")
        client._init_new_application_fabric = mock.AsyncMock()
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {0: mock.MagicMock(), 1: mock.MagicMock()}
        client._start_shard_and_wait_ready = mock.AsyncMock(
            side_effect=[
                (client._fabric.gateways[0], make_finished_future()),
                (client._fabric.gateways[1], make_finished_future()),
            ]
        )

        await client.start()

        client._start_shard_and_wait_ready.assert_any_call(client._fabric.gateways[0])
        client._start_shard_and_wait_ready.assert_any_call(client._fabric.gateways[1])

    def test_run_invokes_run_async(self):
        pass

    @pytest.mark.asyncio
    async def test_start_sets_task_map_on_client(self):
        client = _client.Client("token")
        client._init_new_application_fabric = mock.AsyncMock()
        client._fabric = _fabric.Fabric()

        gw0 = mock.MagicMock()
        gw0.shard_id = 0

        gw1 = mock.MagicMock()
        gw1.shard_id = 1
        client._fabric.gateways = {0: gw0, 1: gw1}

        task_map = {
            client._fabric.gateways[0]: mock.MagicMock(),
            client._fabric.gateways[1]: mock.MagicMock(),
        }

        client._start_shard_and_wait_ready = mock.AsyncMock(side_effect=[(k, v) for k, v in task_map.items()])

        await client.start()

        assert client._shard_tasks == {shard.shard_id: fut for shard, fut in task_map.items()}

    @pytest.mark.asyncio
    async def test_start_returns_mapping_proxy_of_shard_tasks(self):
        def gw(id):
            gw = mock.MagicMock()
            gw.shard_id = id
            return gw

        f0 = mock.MagicMock()
        f1 = mock.MagicMock()
        client = _client.Client("token")
        client._init_new_application_fabric = mock.AsyncMock()
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {0: gw(0), 1: gw(1)}
        client._start_shard_and_wait_ready = mock.AsyncMock(
            side_effect=[(client._fabric.gateways[0], f0), (client._fabric.gateways[1], f1),]
        )

        result = await client.start()
        assert result == {0: f0, 1: f1}
        assert result is not client._shard_tasks

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=RuntimeError)
    async def test_join_when_not_running_raises(self):
        client = _client.Client("token")
        client._shard_tasks = None
        await client.join()

    @pytest.mark.asyncio
    async def test_join_iterates_across_failures_to_manage_non_exception(self):
        client = _client.Client("token")
        client.close = mock.AsyncMock()
        client._fabric = mock.MagicMock()

        async def dump_after(what, after):
            await asyncio.sleep(after)
            return mock.MagicMock(), what

        client._shard_tasks = {
            0: asyncio.create_task(dump_after(123, 0.75)),
            1: asyncio.create_task(dump_after(345, 0.25)),
            2: asyncio.create_task(dump_after(456, 0.5)),
        }

        await client.join()

    @pytest.mark.asyncio
    async def test_join_iterates_across_failures_to_raise_first_exception(self):
        client = _client.Client("token")
        client.close = mock.AsyncMock()
        client._fabric = mock.MagicMock(spec_set=_fabric.Fabric)

        async def dump_after(what, after):
            await asyncio.sleep(after)
            return mock.MagicMock(), what()

        class Ex1(Exception):
            pass

        class Ex2(Exception):
            pass

        class Ex3(Exception):
            pass

        client._shard_tasks = {
            0: asyncio.create_task(dump_after(Ex1, 0.75)),
            1: asyncio.create_task(dump_after(Ex2, 0.1)),
            2: asyncio.create_task(dump_after(Ex3, 0.5)),
        }

        try:
            await client.join()
            assert False, "Nothing was attempted to be joined!"
        except Ex2:
            pass

    @pytest.mark.asyncio
    async def test_close_when_not_running_ignores(self):
        class Shard:
            def __init__(self, id):
                self.shard_id = id
                self.is_running = False
                self.close = mock.AsyncMock()

        shard0 = Shard(0)
        shard1 = Shard(1)

        client = _client.Client("token")
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {shard0.shard_id: shard0, shard1.shard_id: shard1}
        client._fabric.http_api = mock.AsyncMock()
        client._shard_tasks = {}

        await client.close()

        shard0.close.assert_not_called()
        shard1.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_close_closes_http_api(self):
        class Shard:
            def __init__(self, id):
                self.shard_id = id
                self.is_running = True

            async def close(self):
                return

        shard0 = Shard(0)
        shard1 = Shard(1)

        client = _client.Client("token")
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {shard0.shard_id: shard0, shard1.shard_id: shard1}
        client._fabric.http_api = mock.AsyncMock()
        client._shard_tasks = {}

        await client.close()

        client._fabric.http_api.close.assert_called_with()

    @pytest.mark.asyncio
    async def test_close_shuts_down_shards(self):
        class Shard:
            def __init__(self, id):
                self.shard_id = id
                self.is_running = True

            async def close(self):
                return

        shard0 = Shard(0)
        shard1 = Shard(1)
        shard0.close = mock.MagicMock()
        shard1.close = mock.MagicMock()

        client = _client.Client("token")
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {shard0.shard_id: shard0, shard1.shard_id: shard1}
        client._fabric.http_api = mock.AsyncMock()
        client._shard_tasks = {}

        with mock.patch("hikari.internal_utilities.compat.asyncio.create_task", new=mock.AsyncMock()) as create_task:
            await client.close()

            for shard_id, shard in client._fabric.gateways.items():
                create_task.assert_any_call(shard.close(), name=f"waiting for shard {shard_id} to close")



    @pytest.mark.asyncio
    async def test_dispatch(self):
        client = _client.Client("token")
        client._event_dispatcher.dispatch = mock.MagicMock()

        client.dispatch("message_create", "foo", 1, True)

        client._event_dispatcher.dispatch.assert_called_with("message_create", "foo", 1, True)

    @pytest.mark.asyncio
    async def test_add_event(self):
        async def foo():
            ...

        client = _client.Client("token")
        client._event_dispatcher.add = mock.MagicMock()

        client.add_event("message_create", foo)

        client._event_dispatcher.add.assert_called_with("message_create", foo)

    @pytest.mark.asyncio
    async def test_remove_event(self):
        async def foo():
            ...

        client = _client.Client("token")
        client._event_dispatcher.remove = mock.MagicMock()

        client.remove_event("message_create", foo)

        client._event_dispatcher.remove.assert_called_with("message_create", foo)

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=RuntimeError)
    async def test_event_when_name_is_not_str_nor_None_raises(self):
        client = _client.Client("token")

        @client.event(True)
        async def on_message_create():
            ...

    @pytest.mark.asyncio
    async def test_event_without_name_and_starts_with_on(self):
        client = _client.Client("token")

        with mock.patch("hikari.client.Client.add_event") as add_event:

            @client.event()
            async def on_message_create():
                ...

            add_event.assert_called_with("message_create", on_message_create)

    @pytest.mark.asyncio
    async def test_event_without_name_and_doesnt_start_with_on(self):
        client = _client.Client("token")

        with mock.patch("hikari.client.Client.add_event") as add_event:

            @client.event()
            async def message_create():
                ...

            add_event.assert_called_with("message_create", message_create)

    @pytest.mark.asyncio
    async def test_event_with_name(self):
        client = _client.Client("token")

        with mock.patch("hikari.client.Client.add_event") as add_event:

            @client.event("message_create")
            async def foo():
                ...

            add_event.assert_called_with("message_create", foo)

    @pytest.mark.asyncio
    async def test_heartbeat_latency_when_bot_not_started_is_nan(self):
        client = _client.Client("token")
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {}

        assert math.isnan(client.heartbeat_latency)

    @pytest.mark.asyncio
    async def test_heartbeat_latency_when_bot_started(self):
        def gw(id, latency):
            gw = mock.MagicMock()
            gw.shard_id = id
            gw.heartbeat_latency = latency
            return gw

        client = _client.Client("token")
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {0: gw(0, 1), 1: gw(1, 2)}

        assert client.heartbeat_latency == 1.5

    @pytest.mark.asyncio
    async def test_hearbeat_latencies_when_bot_not_started(self):
        client = _client.Client("token")
        client._fabric = None

        assert client.heartbeat_latencies == {}

    @pytest.mark.asyncio
    async def test_hearbeat_latencies(self):
        def gw(id, latency):
            gw = mock.MagicMock()
            gw.shard_id = id
            gw.heartbeat_latency = latency
            return gw

        client = _client.Client("token")
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {0: gw(0, 0.1), 1: gw(1, 0.2)}

        assert client.heartbeat_latencies == {0: 0.1, 1: 0.2}
