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
import math
import os
import signal
from unittest import mock

import aiohttp
import pytest

from hikari.net import errors as _errors
from hikari.net import gateway as _gateway
from hikari.net import http_client as _http_client
from hikari.orm import client as _client
from hikari.orm import client_options
from hikari.orm import fabric as _fabric
from hikari.orm.gateway import base_event_handler as _base_event_handler
from hikari.orm.gateway import basic_chunker_impl as _basic_chunker_impl
from hikari.orm.http import http_adapter_impl as _http_adapter_impl
from tests.hikari import _helpers


@pytest.mark.asyncio
class TestClient:
    def gateway_client(self, id, latency=None):
        gw = _helpers.create_autospec(_gateway.GatewayClient)
        gw.shard_id = id
        gw.heartbeat_latency = latency
        return gw

    @pytest.fixture
    def empty_obj(self):
        class Foo:
            ...

        return Foo()

    @pytest.fixture
    def fabric(self):
        fabric = _fabric.Fabric()

        fabric.http_adapter = _helpers.create_autospec(_http_adapter_impl.HTTPAdapterImpl)
        fabric.event_handler = _helpers.create_autospec(_base_event_handler.BaseEventHandler)

        return fabric

    async def test_init_raises_RuntimeError_if_raised_when_getting_loop(self):
        with mock.patch("asyncio.get_event_loop", side_effect=RuntimeError):
            try:
                _client.Client()
                assert False
            except RuntimeError:
                pass

    async def test_init_sets_token_to_None(self):
        assert _client.Client().token is None

    async def test__init_new_application_fabric_closes_and_raises_RuntimeError_when_error_when_initiating_fabric(self):
        client = _client.Client()
        client.shutdown = mock.AsyncMock()
        client._new_state_registry = mock.AsyncMock(side_effect=RuntimeError)

        try:
            await client._init_new_application_fabric()
            assert False
        except RuntimeError:
            client.shutdown.assert_called_once()

    async def test__init_new_application_fabric(self, empty_obj):
        client = _client.Client()
        client._new_state_registry = mock.AsyncMock(return_value=empty_obj)
        client._new_event_handler = mock.AsyncMock(return_value=empty_obj)
        client._new_http_client = mock.AsyncMock(return_value=empty_obj)
        client._new_http_adapter = mock.AsyncMock(return_value=empty_obj)
        client._new_shard_map = mock.AsyncMock(return_value=(empty_obj, 10))
        client._new_chunker = mock.AsyncMock(return_value=empty_obj)

        await client._init_new_application_fabric()

        client._fabric.state_registry = empty_obj
        client._fabric.event_handler = empty_obj
        client._fabric.http_client = empty_obj
        client._fabric.http_adapter = empty_obj
        client._fabric.gateways = empty_obj
        client._fabric.shard_count = 10
        client._fabric.chunker = empty_obj

    async def test__new_state_registry(self, empty_obj):
        client = _client.Client()

        with mock.patch("hikari.orm.state.state_registry_impl.StateRegistryImpl", return_value=empty_obj):
            assert await client._new_state_registry() == empty_obj

    async def test__new_event_handler(self, empty_obj):
        client = _client.Client()

        with mock.patch(
            "hikari.orm.gateway.dispatching_event_adapter_impl.DispatchingEventAdapterImpl", return_value=empty_obj
        ) as _class:
            assert await client._new_event_handler() == empty_obj

    async def test__new_http_client(self, empty_obj):
        client = _client.Client()

        with mock.patch("hikari.net.http_client.HTTPClient", return_value=empty_obj):
            assert await client._new_http_client() == empty_obj

    async def test__new_http_adapter(self, empty_obj):
        client = _client.Client()

        with mock.patch("hikari.orm.http.http_adapter_impl.HTTPAdapterImpl", return_value=empty_obj):
            assert await client._new_http_adapter() == empty_obj

    @_helpers.assert_raises(type_=RuntimeError)
    async def test__new_shard_map_errors_when_invalid_shards(self):
        client = _client.Client()
        client._client_options = client_options.ClientOptions(shards=None)

        await client._new_shard_map()

    @_helpers.assert_raises(type_=RuntimeError)
    async def test__new_shard_map_when_autoshard_provided_raises_RuntimeError_if_hit_IDENTIFY_limit(self, fabric):
        class Remaining:
            remaining: int = 0

        class GatewayBot:
            session_start_limit: Remaining = Remaining()
            shards: int = 10

        client = _client.Client()
        client._fabric = fabric
        client._fabric.http_adapter.fetch_gateway_bot = mock.AsyncMock(return_value=GatewayBot)
        client._client_options = client_options.ClientOptions(shards=client_options.AUTO_SHARD)

        await client._new_shard_map()

    async def test__new_shard_map_when_autoshard_provided_uses_recomended_shards(self, fabric, empty_obj):
        class Remaining:
            used: int = 100
            remaining: int = 10
            reset_at: float = datetime.datetime.now(tz=datetime.timezone.utc)

        class GatewayBot:
            session_start_limit: Remaining = Remaining()
            url: str = "wss://some-site.com"
            shards: int = 3

        client = _client.Client()
        client._fabric = fabric
        client._fabric.http_adapter.fetch_gateway_bot = mock.AsyncMock(return_value=GatewayBot)
        client._client_options = client_options.ClientOptions(shards=client_options.AUTO_SHARD)

        with mock.patch("hikari.net.gateway.GatewayClient", return_value=empty_obj):
            shard_map, shard_count = await client._new_shard_map()

        assert shard_count == 3
        assert shard_map == {0: empty_obj, 1: empty_obj, 2: empty_obj}

    async def test__new_shard_map_when_no_sharding(self, fabric, empty_obj):
        async def get_gateway():
            return "wss://some-site.com"

        client = _client.Client()
        client._fabric = fabric
        client._fabric.http_adapter.gateway_url = get_gateway()
        client._client_options = client_options.ClientOptions(shards=client_options.NO_SHARDING)

        with mock.patch("hikari.net.gateway.GatewayClient", return_value=empty_obj):
            shard_map, shard_count = await client._new_shard_map()

        assert shard_count == 1
        assert shard_map == {0: empty_obj}

    async def test__new_shard_map_when_slice_provided(self, fabric, empty_obj):
        async def get_gateway():
            return "wss://some-site.com"

        client = _client.Client()
        client._fabric = fabric
        client._fabric.http_adapter.gateway_url = get_gateway()
        client._client_options = client_options.ClientOptions(shards=client_options.ShardOptions(slice(25, 27), 30))

        with mock.patch("hikari.net.gateway.GatewayClient", return_value=empty_obj):
            shard_map, shard_count = await client._new_shard_map()

        assert shard_count == 30
        assert shard_map == {25: empty_obj, 26: empty_obj}

    async def test__new_chunker(self, empty_obj):
        client = _client.Client()

        with mock.patch("hikari.orm.gateway.basic_chunker_impl.BasicChunkerImpl", return_value=empty_obj):
            assert await client._new_chunker() == empty_obj

    async def test__shard_keep_alive_when_shard_shuts_down_silently(self):
        client = _client.Client()
        shard0 = self.gateway_client(0)
        shard0.connect = mock.AsyncMock(side_effect=[None, RuntimeError])

        try:
            await client._shard_keep_alive(shard0)
            assert False
        except Exception as ex:
            assert isinstance(ex, RuntimeError)

    @pytest.mark.parametrize(
        "error",
        [
            aiohttp.ClientConnectorError(mock.MagicMock(), mock.MagicMock()),
            _errors.GatewayZombiedError,
            _errors.GatewayInvalidSessionError(False),
            _errors.GatewayInvalidSessionError(True),
            _errors.GatewayMustReconnectError,
            _errors.GatewayConnectionClosedError,
        ],
    )
    async def test__shard_keep_alive_handles_errors(self, error):
        client = _client.Client()
        shard0 = self.gateway_client(0)
        shard0.connect = mock.AsyncMock(side_effect=[error, RuntimeError])

        with mock.patch("asyncio.sleep", new=mock.AsyncMock()):
            try:
                await client._shard_keep_alive(shard0)
                assert False
            except Exception as ex:
                assert isinstance(ex, RuntimeError)

    async def test__shard_keep_alive_ignores_ClientClosedError(self):
        client = _client.Client()
        shard0 = self.gateway_client(0)
        shard0.connect = mock.AsyncMock(side_effect=_errors.GatewayClientClosedError)

        with mock.patch("asyncio.sleep", new=mock.AsyncMock()):
            try:
                await client._shard_keep_alive(shard0)
                assert True
            except Exception as ex:
                assert False

    async def test_start_sets_token(self):
        client = _client.Client()
        client._init_new_application_fabric = mock.AsyncMock()
        client._fabric = _fabric.Fabric()

        await client.start("token")
        assert client.token == "token"

    async def test_start_initializes_fabric(self):
        client = _client.Client()
        client._init_new_application_fabric = mock.AsyncMock()
        client._fabric = _fabric.Fabric()

        await client.start("token")

        client._init_new_application_fabric.assert_called_once()

    async def test_start_waits_5s_before_starting_greater_than_0_shards(self):
        shard0 = self.gateway_client(0)
        shard0.identify_event.wait = mock.AsyncMock()
        shard1 = self.gateway_client(1)
        shard1.identify_event.wait = mock.AsyncMock()

        client = _client.Client()
        client._init_new_application_fabric = mock.AsyncMock()
        client._fabric = _fabric.Fabric(gateways={0: shard0, 1: shard1})

        with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()):
            with mock.patch("asyncio.sleep", new=mock.AsyncMock()) as sleep:
                await client.start("token")

                sleep.assert_called_once_with(5)

    async def test_start_starts_keep_alive_tasks(self):
        shard0 = self.gateway_client(0)
        shard0.identify_event.wait = mock.AsyncMock()

        client = _client.Client()
        client._init_new_application_fabric = mock.AsyncMock()
        client._shard_keep_alive = mock.MagicMock()
        client._fabric = _fabric.Fabric(gateways={0: shard0})

        with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()):
            with mock.patch("asyncio.create_task") as create_task:
                await client.start("1a2b3c")

            create_task.assert_called_with(client._shard_keep_alive(shard0))

    async def test_start_waits_for_shards_to_identify(self):
        shard0 = self.gateway_client(0)
        shard0.identify_event.wait = mock.AsyncMock()

        client = _client.Client()
        client._init_new_application_fabric = mock.AsyncMock()
        client._fabric = _fabric.Fabric(gateways={0: shard0})

        with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()):
            await client.start("token")

        shard0.identify_event.wait.assert_called_once()

    async def test_join_gathers_shard_keepalive_tasks(self, event_loop):
        client = _client.Client()
        shard = self.gateway_client(0)
        task = _helpers.create_autospec(asyncio.Task)
        client._shard_keepalive_tasks = {shard: task}

        with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()) as gather:
            await client.join()

            gather.assert_called_once_with(*[task])

    async def test_destroy_doesnt_destroy_the_shard_if_done(self, event_loop):
        client = _client.Client()
        shard = self.gateway_client(0)
        task = _helpers.create_autospec(asyncio.Task)
        task.done = mock.MagicMock(return_value=True)
        client._shard_keepalive_tasks = {shard: task}

        with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()) as gather:
            await client.destroy()

            task.cancel.assert_not_called()

    async def test_shutdown_returns_when_already_closed(self):
        shard0 = self.gateway_client(0)
        shard0.requesting_close_event.is_set = mock.MagicMock(return_value=False)

        client = _client.Client()
        client._fabric = _fabric.Fabric(gateways={0: shard0})
        client.is_closed = True
        gather_future = _helpers.AwaitableMock()

        with mock.patch("asyncio.gather", return_value=gather_future):
            await client.shutdown()

        gather_future.assert_not_awaited()

    async def test_shutdown_unclosed_shards(self):
        shard0 = self.gateway_client(0)
        shard0.requesting_close_event.is_set = mock.MagicMock(return_value=True)
        shard1 = self.gateway_client(1)
        shard1.requesting_close_event.is_set = mock.MagicMock(return_value=False)

        client = _client.Client()
        client._fabric = _fabric.Fabric(
            gateways={0: shard0, 1: shard1}, chunker=_helpers.create_autospec(_basic_chunker_impl.BasicChunkerImpl)
        )
        gather_future = _helpers.AwaitableMock()

        with mock.patch("asyncio.gather", return_value=gather_future):
            await client.shutdown()

        gather_future.assert_awaited_once()
        shard0.close.assert_not_called()
        shard1.close.assert_called_once()

    async def test_shutdown_catches_exception_when_shutting_down_shards(self):
        shard0 = self.gateway_client(0)
        shard0.requesting_close_event.is_set = mock.MagicMock(return_value=True)
        shard1 = self.gateway_client(1)
        shard1.requesting_close_event.is_set = mock.MagicMock(return_value=False)

        client = _client.Client()
        client._fabric = _fabric.Fabric(
            gateways={0: shard0, 1: shard1}, chunker=_helpers.create_autospec(_basic_chunker_impl.BasicChunkerImpl)
        )

        with mock.patch("asyncio.gather", side_effect=RuntimeError) as gather:
            await client.shutdown()
            gather.assert_called_once()

    async def test_shutdown_doesnt_do_anything_if_shards_are_closed(self):
        shard0 = self.gateway_client(0)
        shard0.requesting_close_event.is_set = mock.MagicMock(return_value=True)
        shard1 = self.gateway_client(1)
        shard1.requesting_close_event.is_set = mock.MagicMock(return_value=True)

        client = _client.Client()
        client._fabric = _fabric.Fabric(
            gateways={0: shard0, 1: shard1}, chunker=_helpers.create_autospec(_basic_chunker_impl.BasicChunkerImpl)
        )
        gather_future = _helpers.AwaitableMock()

        with mock.patch("asyncio.gather", return_value=gather_future):
            await client.shutdown()

        gather_future.assert_not_awaited()
        shard0.close.assert_not_called()
        shard1.close.assert_not_called()

    async def test_shutdown_closes_chunker(self):
        client = _client.Client()
        chunker = _helpers.create_autospec(_basic_chunker_impl.BasicChunkerImpl)
        client._fabric = _fabric.Fabric(gateways={}, chunker=chunker)

        await client.shutdown()

        chunker.close.assert_called_once()

    async def test_shutdown_doesnt_do_anything_if_no_fabric(self):
        client = _client.Client()
        client._fabric = None
        gather_future = _helpers.AwaitableMock()

        with mock.patch("asyncio.gather", return_value=gather_future):
            await client.shutdown()

        gather_future.assert_not_awaited()

    @_helpers.stupid_windows_please_stop_breaking_my_tests
    async def test_run_calls_shutdown_when_KeyboardInterrupt(self):
        client = _client.Client()
        client.shutdown = mock.MagicMock()
        client.loop.run_until_complete = mock.MagicMock(side_effect=[KeyboardInterrupt, None])

        client.run("token")
        client.loop.run_until_complete.assert_called_with(client.shutdown())

    async def test_run_calls_start(self):
        client = _client.Client()
        client.start = mock.MagicMock()
        client.join = mock.MagicMock()
        client.loop.run_until_complete = mock.MagicMock()

        client.run("token")

        client.loop.run_until_complete.assert_any_call(client.start("token"))

    async def test_run_calls_join(self):
        client = _client.Client()
        client.start = mock.MagicMock()
        client.join = mock.MagicMock()
        client.loop.run_until_complete = mock.MagicMock()

        client.run("token")

        client.loop.run_until_complete.assert_any_call(client.join())

    async def test_dispatch(self):
        client = _client.Client()
        client._event_dispatcher.dispatch = mock.MagicMock()

        client.dispatch("message_create", "foo", 1, True)

        client._event_dispatcher.dispatch.assert_called_with("message_create", "foo", 1, True)

    async def test_add_event(self):
        async def foo():
            ...

        client = _client.Client()
        client._event_dispatcher.add = mock.MagicMock()

        client.add_event("message_create", foo)

        client._event_dispatcher.add.assert_called_with("message_create", foo)

    async def test_remove_event(self):
        async def foo():
            ...

        client = _client.Client()
        client._event_dispatcher.remove = mock.MagicMock()

        client.remove_event("message_create", foo)

        client._event_dispatcher.remove.assert_called_with("message_create", foo)

    @_helpers.assert_raises(type_=RuntimeError)
    async def test_event_when_name_is_not_str_nor_None_raises(self):
        client = _client.Client()

        @client.event(True)
        async def on_message_create():
            ...

    async def test_event_without_name_and_starts_with_on(self):
        client = _client.Client()

        with mock.patch("hikari.client.Client.add_event") as add_event:

            @client.event()
            async def on_message_create():
                ...

            add_event.assert_called_with("message_create", on_message_create)

    async def test_event_without_name_and_doesnt_start_with_on(self):
        client = _client.Client()

        with mock.patch("hikari.client.Client.add_event") as add_event:

            @client.event()
            async def message_create():
                ...

            add_event.assert_called_with("message_create", message_create)

    async def test_event_with_name(self):
        client = _client.Client()

        with mock.patch("hikari.client.Client.add_event") as add_event:

            @client.event("message_create")
            async def foo():
                ...

            add_event.assert_called_with("message_create", foo)

    async def test_heartbeat_latency_when_bot_not_started_is_nan(self):
        client = _client.Client()
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {}

        assert math.isnan(client.heartbeat_latency)

    async def test_heartbeat_latency_when_bot_started(self):
        client = _client.Client()
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {0: self.gateway_client(0, 1), 1: self.gateway_client(1, 2)}

        assert client.heartbeat_latency == 1.5

    async def test_hearbeat_latencies_when_bot_not_started(self):
        client = _client.Client()
        client._fabric = None

        assert client.heartbeat_latencies == {}

    async def test_hearbeat_latencies(self):
        client = _client.Client()
        client._fabric = _fabric.Fabric()
        client._fabric.gateways = {0: self.gateway_client(0, 0.1), 1: self.gateway_client(1, 0.2)}

        assert client.heartbeat_latencies == {0: 0.1, 1: 0.2}

    async def test_shards_when_bot_not_started(self):
        client = _client.Client()
        client._fabric = None

        assert client.shards == {}

    async def test_shards(self):
        shard0 = self.gateway_client(0)
        shard1 = self.gateway_client(1)

        client = _client.Client()
        client._fabric = _fabric.Fabric(gateways={0: shard0, 1: shard1})

        assert client.shards == {0: shard0, 1: shard1}


def filter_unimplemented(*args):
    return [arg for arg in args if arg is not NotImplemented]


class TestClientShutdownHandling:
    def _do_test_safe_signal_handling(self, signal_to_fire):
        loop = asyncio.new_event_loop()
        loop.set_debug(True)
        asyncio.set_event_loop(loop)

        mock_http_client = mock.create_autospec(_http_client.HTTPClient, spec_set=True)

        def mock_shard(id: int, count: int):
            class MockShard(_gateway.GatewayClient):
                async def connect(self, client_session_type=aiohttp.ClientSession):
                    await asyncio.sleep(0.1)
                    print("mocking identify")
                    self.identify_event.set()

            return MockShard(shard_id=id, shard_count=count, token="1a2b3c", url="wss://localhost:8080")

        shards = [mock_shard(i, 5) for i in range(5)]

        class Client(_client.Client):
            _SHARD_IDENTIFY_WAIT = 0.1

            def __init__(self, *args, **kwargs):
                self.shutdown = mock.MagicMock(wraps=super().shutdown)
                self.destroy = mock.MagicMock(wraps=super().destroy)
                super().__init__(*args, **kwargs)

            async def _new_shard_map(self):
                print("shard_map is created")
                return {shard.shard_id: shard for shard in shards}, len(shards)

            async def _new_http_client(self):
                print("http_client is up")
                return mock_http_client

            async def _shard_keep_alive(self, shard: _gateway.GatewayClient) -> None:
                print("shard is up")
                await asyncio.get_event_loop().create_future()

        bot = Client(loop=loop)

        try:
            bot.loop.call_later(0.5, os.kill, os.getpid(), signal_to_fire)
            bot.run("1a2b3c")
        finally:
            bot.loop.close()
            bot.shutdown.assert_called_once()
            bot.destroy.assert_called_once()

    @_helpers.stupid_windows_please_stop_breaking_my_tests
    def test_sigint(self):
        self._do_test_safe_signal_handling(signal.SIGINT)

    @_helpers.stupid_windows_please_stop_breaking_my_tests
    def test_sigterm(self):
        self._do_test_safe_signal_handling(signal.SIGTERM)
