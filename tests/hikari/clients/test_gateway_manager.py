#!/usr/bin/env python3
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
# along ith Hikari. If not, see <https://www.gnu.org/licenses/>.
import math

import cymock as mock
import pytest

from hikari.clients import gateway_manager
from hikari.clients import shard_client
from tests.hikari import _helpers


class TestGatewayManager:
    def test_latency(self):
        shard1 = mock.MagicMock(shard_client.ShardClient, latency=20)
        shard2 = mock.MagicMock(shard_client.ShardClient, latency=30)
        shard3 = mock.MagicMock(shard_client.ShardClient, latency=40)

        with mock.patch("hikari.clients.shard_client.ShardClient", side_effect=[shard1, shard2, shard3]):
            gateway_manager_obj = gateway_manager.GatewayManager(
                shard_ids=[0, 1, 2],
                shard_count=3,
                config=None,
                url="some_url",
                raw_event_consumer_impl=None,
                shard_type=shard_client.ShardClient,
            )

        assert gateway_manager_obj.latency == 30

    def test_latency_doesnt_take_into_a_count_shards_with_no_latency(self):
        shard1 = mock.MagicMock(shard_client.ShardClient, latency=20)
        shard2 = mock.MagicMock(shard_client.ShardClient, latency=30)
        shard3 = mock.MagicMock(shard_client.ShardClient, latency=float("nan"))

        with mock.patch("hikari.clients.shard_client.ShardClient", side_effect=[shard1, shard2, shard3]):
            gateway_manager_obj = gateway_manager.GatewayManager(
                shard_ids=[0, 1, 2],
                shard_count=3,
                config=None,
                url="some_url",
                raw_event_consumer_impl=None,
                shard_type=shard_client.ShardClient,
            )

        assert gateway_manager_obj.latency == 25

    def test_latency_returns_nan_if_all_shards_have_no_latency(self):
        shard1 = mock.MagicMock(shard_client.ShardClient, latency=float("nan"))
        shard2 = mock.MagicMock(shard_client.ShardClient, latency=float("nan"))
        shard3 = mock.MagicMock(shard_client.ShardClient, latency=float("nan"))

        with mock.patch("hikari.clients.shard_client.ShardClient", side_effect=[shard1, shard2, shard3]):
            gateway_manager_obj = gateway_manager.GatewayManager(
                shard_ids=[0, 1, 2],
                shard_count=3,
                config=None,
                url="some_url",
                raw_event_consumer_impl=None,
                shard_type=shard_client.ShardClient,
            )

        assert math.isnan(gateway_manager_obj.latency)

    @pytest.mark.asyncio
    async def test_start_waits_five_seconds_between_shard_startup(self):
        mock_sleep = mock.AsyncMock()

        class MockStart(mock.AsyncMock):
            def __init__(self, condition):
                super().__init__()
                self.condition = condition

            def __call__(self):
                if self.condition:
                    mock_sleep.assert_called_once_with(5)
                    mock_sleep.reset_mock()
                else:
                    mock_sleep.assert_not_called()

                return super().__call__()

        shard1 = mock.MagicMock(shard_client.ShardClient, start=MockStart(condition=False))
        shard2 = mock.MagicMock(shard_client.ShardClient, start=MockStart(condition=True))
        shard3 = mock.MagicMock(shard_client.ShardClient, start=MockStart(condition=True))

        with mock.patch("hikari.clients.shard_client.ShardClient", side_effect=[shard1, shard2, shard3]):
            with mock.patch("asyncio.sleep", wraps=mock_sleep):
                gateway_manager_obj = gateway_manager.GatewayManager(
                    shard_ids=[0, 1, 2],
                    shard_count=3,
                    config=None,
                    url="some_url",
                    raw_event_consumer_impl=None,
                    shard_type=shard_client.ShardClient,
                )
                await gateway_manager_obj.start()
                mock_sleep.assert_not_called()

        shard1.start.assert_called_once()
        shard2.start.assert_called_once()
        shard3.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_join_calls_join_on_all_shards(self):
        shard1 = mock.MagicMock(shard_client.ShardClient, join=mock.MagicMock())
        shard2 = mock.MagicMock(shard_client.ShardClient, join=mock.MagicMock())
        shard3 = mock.MagicMock(shard_client.ShardClient, join=mock.MagicMock())

        with mock.patch("hikari.clients.shard_client.ShardClient", side_effect=[shard1, shard2, shard3]):
            with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()):
                gateway_manager_obj = gateway_manager.GatewayManager(
                    shard_ids=[0, 1, 2],
                    shard_count=3,
                    config=None,
                    url="some_url",
                    raw_event_consumer_impl=None,
                    shard_type=shard_client.ShardClient,
                )
                await gateway_manager_obj.join()

        shard1.join.assert_called_once()
        shard2.join.assert_called_once()
        shard3.join.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("wait", [True, False])
    async def test_close_closes_all_shards(self, wait):
        shard1 = mock.MagicMock(shard_client.ShardClient, close=mock.MagicMock())
        shard2 = mock.MagicMock(shard_client.ShardClient, close=mock.MagicMock())
        shard3 = mock.MagicMock(shard_client.ShardClient, close=mock.MagicMock())

        with mock.patch("hikari.clients.shard_client.ShardClient", side_effect=[shard1, shard2, shard3]):
            with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()):
                gateway_manager_obj = gateway_manager.GatewayManager(
                    shard_ids=[0, 1, 2],
                    shard_count=3,
                    config=None,
                    url="some_url",
                    raw_event_consumer_impl=None,
                    shard_type=shard_client.ShardClient,
                )
                gateway_manager_obj._is_running = True
                await gateway_manager_obj.close(wait=wait)

        shard1.close.assert_called_once_with(wait)
        shard2.close.assert_called_once_with(wait)
        shard3.close.assert_called_once_with(wait)

    @pytest.mark.asyncio
    async def test_close_does_nothing_if_not_running(self):
        shard1 = mock.MagicMock(shard_client.ShardClient, close=mock.MagicMock())
        shard2 = mock.MagicMock(shard_client.ShardClient, close=mock.MagicMock())
        shard3 = mock.MagicMock(shard_client.ShardClient, close=mock.MagicMock())

        with mock.patch("hikari.clients.shard_client.ShardClient", side_effect=[shard1, shard2, shard3]):
            with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()):
                gateway_manager_obj = gateway_manager.GatewayManager(
                    shard_ids=[0, 1, 2],
                    shard_count=3,
                    config=None,
                    url="some_url",
                    raw_event_consumer_impl=None,
                    shard_type=shard_client.ShardClient,
                )
                gateway_manager_obj._is_running = False
                await gateway_manager_obj.close()

        shard1.close.assert_not_called()
        shard2.close.assert_not_called()
        shard3.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_presence_updates_presence_in_all_ready_or_waiting_for_ready_shards(self):
        shard1 = mock.MagicMock(
            shard_client.ShardClient, update_presence=mock.MagicMock(), connection_state=shard_client.ShardState.READY,
        )
        shard2 = mock.MagicMock(
            shard_client.ShardClient,
            update_presence=mock.MagicMock(),
            connection_state=shard_client.ShardState.WAITING_FOR_READY,
        )
        shard3 = mock.MagicMock(
            shard_client.ShardClient,
            update_presence=mock.MagicMock(),
            connection_state=shard_client.ShardState.CONNECTING,
        )

        with mock.patch("hikari.clients.shard_client.ShardClient", side_effect=[shard1, shard2, shard3]):
            with mock.patch("asyncio.gather", return_value=_helpers.AwaitableMock()):
                gateway_manager_obj = gateway_manager.GatewayManager(
                    shard_ids=[0, 1, 2],
                    shard_count=3,
                    config=None,
                    url="some_url",
                    raw_event_consumer_impl=None,
                    shard_type=shard_client.ShardClient,
                )
                await gateway_manager_obj.update_presence(status=None, activity=None, idle_since=None, is_afk=True)

        shard1.update_presence.assert_called_once_with(status=None, activity=None, idle_since=None, is_afk=True)
        shard2.update_presence.assert_called_once_with(status=None, activity=None, idle_since=None, is_afk=True)
        shard3.update_presence.assert_not_called()
