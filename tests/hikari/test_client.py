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
import datetime

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
            timeout=client_opts.http_timeout,
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
                timeout=client_opts.http_timeout,
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
            timeout=client_opts.http_timeout,
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
                timeout=client_opts.http_timeout,
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
    async def test_start_shard_and_wait_ready_when_ready_satisfied(self):
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
