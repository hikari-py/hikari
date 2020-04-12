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
import datetime
import math
import asyncio
import aiohttp

import cymock as mock
import pytest

from hikari import guilds
from hikari import errors
from hikari.net import shard
from hikari.net import codes
from hikari.state import raw_event_consumers
from hikari.clients import shard_clients
from hikari.clients import configs
from tests.hikari import _helpers


class TestShardClient:
    @pytest.fixture
    def shard_client_obj(self):
        mock_shard_connection = mock.MagicMock(
            shard.ShardConnection,
            heartbeat_latency=float("nan"),
            heartbeat_interval=float("nan"),
            reconnect_count=0,
            seq=None,
            session_id=None,
        )
        with mock.patch("hikari.net.shard.ShardConnection", return_value=mock_shard_connection):
            return _helpers.unslot_class(shard_clients.ShardClient)(0, 1, configs.WebsocketConfig(), None, "some_url")

    def _generate_mock_task(self, exception=None):
        class Task(mock.MagicMock):
            def __init__(self, exception):
                super().__init__()
                self._exception = exception

            def exception(self):
                return self._exception

        return Task(exception)

    def test_raw_event_consumer_in_shardclient(self):
        class DummyConsumer(raw_event_consumers.RawEventConsumer):
            def process_raw_event(self, _client, name, payload):
                return "ASSERT TRUE"

        shard_client_obj = shard_clients.ShardClient(0, 1, configs.WebsocketConfig(), DummyConsumer(), "some_url")

        assert shard_client_obj._connection.dispatch(shard_client_obj, "TEST", {}) == "ASSERT TRUE"

    def test_connection(self, shard_client_obj):
        mock_shard_connection = mock.MagicMock(shard.ShardConnection)

        with mock.patch("hikari.net.shard.ShardConnection", return_value=mock_shard_connection):
            shard_client_obj = shard_clients.ShardClient(0, 1, configs.WebsocketConfig(), None, "some_url")

        assert shard_client_obj.connection == mock_shard_connection

    def test_status(self, shard_client_obj):
        assert shard_client_obj.status == guilds.PresenceStatus.ONLINE

    def test_activity(self, shard_client_obj):
        assert shard_client_obj.activity is None

    def test_idle_since(self, shard_client_obj):
        assert shard_client_obj.idle_since is None

    def test_is_afk(self, shard_client_obj):
        assert shard_client_obj.is_afk is False

    def test_latency(self, shard_client_obj):
        assert math.isnan(shard_client_obj.latency)

    def test_heartbeat_interval(self, shard_client_obj):
        assert math.isnan(shard_client_obj.heartbeat_interval)

    def test_reconnect_count(self, shard_client_obj):
        assert shard_client_obj.reconnect_count == 0

    def test_connection_state(self, shard_client_obj):
        assert shard_client_obj.connection_state == shard_clients.ShardState.NOT_RUNNING

    @pytest.mark.asyncio
    async def test_start_when_ready_event_completes_first(self, shard_client_obj):
        shard_client_obj._keep_alive = mock.AsyncMock()
        task_mock = self._generate_mock_task()

        with mock.patch("asyncio.create_task", return_value=task_mock):
            with mock.patch("asyncio.wait", return_value=([], None)):
                await shard_client_obj.start()

    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.asyncio
    async def test_start_when_task_completes(self, shard_client_obj):
        shard_client_obj._keep_alive = mock.AsyncMock()
        task_mock = self._generate_mock_task(RuntimeError)

        with mock.patch("asyncio.create_task", return_value=task_mock):
            with mock.patch("asyncio.wait", return_value=([task_mock], None)):
                await shard_client_obj.start()

    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.asyncio
    async def test_start_when_already_started(self, shard_client_obj):
        shard_client_obj._shard_state = shard_clients.ShardState.READY

        await shard_client_obj.start()

    @pytest.mark.asyncio
    async def test_join_when__task(self, shard_client_obj):
        shard_client_obj._task = _helpers.AwaitableMock()

        await shard_client_obj.join()

        shard_client_obj._task.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_join_when_not__task(self, shard_client_obj):
        shard_client_obj._task = None

        await shard_client_obj.join()

    @pytest.mark.asyncio
    async def test_close(self, shard_client_obj):
        shard_client_obj._dispatch = _helpers.AwaitableMock()
        shard_client_obj._task = _helpers.AwaitableMock()

        await shard_client_obj.close()

        shard_client_obj._connection.close.assert_called_once()
        shard_client_obj._task.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_close_when_already_stopping(self, shard_client_obj):
        shard_client_obj._shard_state = shard_clients.ShardState.STOPPING

        await shard_client_obj.close()

        shard_client_obj._connection.close.assert_not_called()

    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.parametrize(
        "error",
        [
            None,
            aiohttp.ClientConnectorError(mock.MagicMock(), mock.MagicMock()),
            errors.GatewayZombiedError,
            errors.GatewayInvalidSessionError(False),
            errors.GatewayInvalidSessionError(True),
            errors.GatewayMustReconnectError,
        ],
    )
    @pytest.mark.asyncio
    async def test__keep_alive_handles_errors(self, error, shard_client_obj):
        should_return = False

        def side_effect(*args):
            nonlocal should_return
            if should_return:
                return _helpers.AwaitableMock(return_value=RuntimeError)

            should_return = True
            return _helpers.AwaitableMock(return_value=error)

        shard_client_obj._spin_up = mock.AsyncMock(side_effect=side_effect)

        with mock.patch("asyncio.sleep", new=mock.AsyncMock()):
            await shard_client_obj._keep_alive()

    @pytest.mark.asyncio
    async def test__keep_alive_shuts_down_when_GatewayClientClosedError(self, shard_client_obj):
        shard_client_obj._spin_up = mock.AsyncMock(
            return_value=_helpers.AwaitableMock(return_value=errors.GatewayClientClosedError)
        )

        with mock.patch("asyncio.sleep", new=mock.AsyncMock()):
            await shard_client_obj._keep_alive()

    @_helpers.assert_raises(type_=errors.GatewayServerClosedConnectionError)
    @pytest.mark.parametrize(
        "code",
        [
            codes.GatewayCloseCode.NOT_AUTHENTICATED,
            codes.GatewayCloseCode.AUTHENTICATION_FAILED,
            codes.GatewayCloseCode.ALREADY_AUTHENTICATED,
            codes.GatewayCloseCode.SHARDING_REQUIRED,
            codes.GatewayCloseCode.INVALID_VERSION,
            codes.GatewayCloseCode.INVALID_INTENT,
            codes.GatewayCloseCode.DISALLOWED_INTENT,
        ],
    )
    @pytest.mark.asyncio
    async def test__keep_alive_shuts_down_when_GatewayServerClosedConnectionError(self, code, shard_client_obj):
        shard_client_obj._spin_up = mock.AsyncMock(
            return_value=_helpers.AwaitableMock(return_value=errors.GatewayServerClosedConnectionError(code))
        )

        with mock.patch("asyncio.sleep", new=mock.AsyncMock()):
            await shard_client_obj._keep_alive()

    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.asyncio
    async def test__keep_alive_ignores_when_GatewayServerClosedConnectionError_with_other_code(self, shard_client_obj):
        should_return = False

        def side_effect(*args):
            nonlocal should_return
            if should_return:
                return _helpers.AwaitableMock(return_value=RuntimeError)

            should_return = True
            return _helpers.AwaitableMock(
                return_value=errors.GatewayServerClosedConnectionError(codes.GatewayCloseCode.NORMAL_CLOSURE)
            )

        shard_client_obj._spin_up = mock.AsyncMock(side_effect=side_effect)

        with mock.patch("asyncio.sleep", new=mock.AsyncMock()):
            await shard_client_obj._keep_alive()

    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.asyncio
    async def test__spin_up_if_connect_task_is_completed_raises_exception_during_hello_event(self, shard_client_obj):
        task_mock = self._generate_mock_task(RuntimeError)

        with mock.patch("asyncio.create_task", return_value=task_mock):
            with mock.patch("asyncio.wait", return_value=([task_mock], None)):
                await shard_client_obj._spin_up()

    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.asyncio
    async def test__spin_up_if_connect_task_is_completed_raises_exception_during_identify_event(self, shard_client_obj):
        task_mock = self._generate_mock_task(RuntimeError)

        with mock.patch("asyncio.create_task", return_value=task_mock):
            with mock.patch("asyncio.wait", side_effect=[([], None), ([task_mock], None)]):
                await shard_client_obj._spin_up()

    @pytest.mark.asyncio
    async def test__spin_up_when_resuming(self, shard_client_obj):
        shard_client_obj._connection.seq = 123
        shard_client_obj._connection.session_id = 123
        task_mock = self._generate_mock_task()

        with mock.patch("asyncio.create_task", return_value=task_mock):
            with mock.patch("asyncio.wait", side_effect=[([], None), ([], None), ([], None)]):
                assert await shard_client_obj._spin_up() == task_mock

    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.asyncio
    async def test__spin_up_if_connect_task_is_completed_raises_exception_during_resumed_event(self, shard_client_obj):
        shard_client_obj._connection.seq = 123
        shard_client_obj._connection.session_id = 123
        task_mock = self._generate_mock_task(RuntimeError)

        with mock.patch("asyncio.create_task", return_value=task_mock):
            with mock.patch("asyncio.wait", side_effect=[([], None), ([], None), ([task_mock], None)]):
                await shard_client_obj._spin_up()

    @pytest.mark.asyncio
    async def test__spin_up_when_not_resuming(self, shard_client_obj):
        task_mock = self._generate_mock_task()

        with mock.patch("asyncio.create_task", return_value=task_mock):
            with mock.patch("asyncio.wait", side_effect=[([], None), ([], None), ([], None)]):
                assert await shard_client_obj._spin_up() == task_mock

    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.asyncio
    async def test__spin_up_if_connect_task_is_completed_raises_exception_during_ready_event(self, shard_client_obj):
        task_mock = self._generate_mock_task(RuntimeError)

        with mock.patch("asyncio.create_task", return_value=task_mock):
            with mock.patch("asyncio.wait", side_effect=[([], None), ([], None), ([task_mock], None)]):
                await shard_client_obj._spin_up()

    @pytest.mark.asyncio
    async def test_update_presence(self, shard_client_obj):
        await shard_client_obj.update_presence()

        shard_client_obj._connection.update_presence.assert_called_once_with(
            {"status": "online", "game": None, "idle_since": None, "afk": False}
        )

        assert shard_client_obj._status == guilds.PresenceStatus.ONLINE
        assert shard_client_obj._activity == None
        assert shard_client_obj._idle_since == None
        assert shard_client_obj._is_afk is False

    @pytest.mark.asyncio
    async def test_update_presence_with_optionals(self, shard_client_obj):
        datetime_obj = datetime.datetime.now()

        await shard_client_obj.update_presence(
            status=guilds.PresenceStatus.DND, activity=None, idle_since=datetime_obj, is_afk=True
        )

        shard_client_obj._connection.update_presence.assert_called_once_with(
            {"status": "dnd", "game": None, "idle_since": datetime_obj.timestamp() * 1000, "afk": True}
        )

        assert shard_client_obj._status == guilds.PresenceStatus.DND
        assert shard_client_obj._activity == None
        assert shard_client_obj._idle_since == datetime_obj
        assert shard_client_obj._is_afk is True

    def test__create_presence_pl(self, shard_client_obj):
        datetime_obj = datetime.datetime.now()
        returned = shard_client_obj._create_presence_pl(guilds.PresenceStatus.DND, None, datetime_obj, True)

        assert returned == {
            "status": "dnd",
            "game": None,
            "idle_since": datetime_obj.timestamp() * 1000,
            "afk": True,
        }
