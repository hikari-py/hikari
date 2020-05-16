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
import asyncio
import datetime

import aiohttp
import async_timeout
import mock
import pytest

import hikari.gateway.gateway_state
from hikari.models import guilds
from hikari import errors
from hikari.components import application
from hikari import configs
from hikari.gateway import client as high_level_shards
from hikari.components import consumers
from hikari.internal import more_asyncio
from hikari.internal import codes
from hikari.gateway import connection as low_level_shards
from tests.hikari import _helpers


def _generate_mock_task(exception=None):
    class Task(mock.MagicMock):
        def __init__(self):
            super().__init__()
            self._exception = exception

        def exception(self):
            return self._exception

        def done(self):
            return True

    return Task()


@pytest.fixture
def mock_components():
    class ApplicationImpl(application.Application):
        def __init__(self):
            super().__init__(
                config=mock.MagicMock(),
                event_dispatcher=mock.MagicMock(dispatch_event=mock.MagicMock(return_value=_helpers.AwaitableMock())),
                event_manager=mock.MagicMock(),
                rest=mock.MagicMock(),
                shards=mock.MagicMock(),
            )

    return ApplicationImpl()


@pytest.fixture
def shard_client_obj(mock_components):
    mock_shard_connection = mock.MagicMock(
        low_level_shards.Shard,
        heartbeat_latency=float("nan"),
        heartbeat_interval=float("nan"),
        reconnect_count=0,
        seq=None,
        session_id=None,
    )
    with mock.patch("hikari.net.shards.Shard", return_value=mock_shard_connection):
        return _helpers.unslot_class(high_level_shards.GatewayClient)(0, 1, mock_components, "some_url")


class TestShardClientImpl:
    def test_raw_event_consumer_in_ShardClientImpl(self):
        class DummyConsumer(consumers.RawEventConsumer):
            def process_raw_event(self, _client, name, payload):
                return "ASSERT TRUE"

        shard_client_obj = high_level_shards.GatewayClient(
            0,
            1,
            mock.MagicMock(application.Application, config=configs.GatewayConfig(), event_manager=DummyConsumer()),
            "some_url",
        )

        assert shard_client_obj._connection.dispatcher(shard_client_obj, "TEST", {}) == "ASSERT TRUE"

    def test_connection_is_set(self, shard_client_obj):
        mock_shard_connection = mock.MagicMock(low_level_shards.Shard)

        with mock.patch("hikari.net.shards.Shard", return_value=mock_shard_connection):
            shard_client_obj = high_level_shards.GatewayClient(
                0,
                1,
                mock.MagicMock(application.Application, event_manager=None, config=configs.GatewayConfig()),
                "some_url",
            )

        assert shard_client_obj._connection is mock_shard_connection


class TestShardClientImplDelegateProperties:
    def test_shard_id(self, shard_client_obj):
        marker = object()
        shard_client_obj._connection.shard_id = marker
        assert shard_client_obj.shard_id is marker

    def test_shard_count(self, shard_client_obj):
        marker = object()
        shard_client_obj._connection.shard_count = marker
        assert shard_client_obj.shard_count is marker

    def test_status(self, shard_client_obj):
        marker = object()
        shard_client_obj._status = marker
        assert shard_client_obj.status is marker

    def test_activity(self, shard_client_obj):
        marker = object()
        shard_client_obj._activity = marker
        assert shard_client_obj.activity is marker

    def test_idle_since(self, shard_client_obj):
        marker = object()
        shard_client_obj._idle_since = marker
        assert shard_client_obj.idle_since is marker

    def test_is_afk(self, shard_client_obj):
        marker = object()
        shard_client_obj._is_afk = marker
        assert shard_client_obj.is_afk is marker

    def test_heartbeat_latency(self, shard_client_obj):
        marker = object()
        shard_client_obj._connection.heartbeat_latency = marker
        assert shard_client_obj.heartbeat_latency is marker

    def test_heartbeat_interval(self, shard_client_obj):
        marker = object()
        shard_client_obj._connection.heartbeat_interval = marker
        assert shard_client_obj.heartbeat_interval is marker

    def test_reconnect_count(self, shard_client_obj):
        marker = object()
        shard_client_obj._connection.reconnect_count = marker
        assert shard_client_obj.reconnect_count is marker

    def test_disconnect_count(self, shard_client_obj):
        marker = object()
        shard_client_obj._connection.disconnect_count = marker
        assert shard_client_obj.disconnect_count is marker

    def test_connection_state(self, shard_client_obj):
        marker = object()
        shard_client_obj._shard_state = marker
        assert shard_client_obj.connection_state is marker

    def test_is_connected(self, shard_client_obj):
        marker = object()
        shard_client_obj._connection.is_connected = marker
        assert shard_client_obj.is_connected is marker

    def test_seq(self, shard_client_obj):
        marker = object()
        shard_client_obj._connection.seq = marker
        assert shard_client_obj.seq is marker

    def test_session_id(self, shard_client_obj):
        marker = object()
        shard_client_obj._connection.session_id = marker
        assert shard_client_obj.session_id is marker

    def test_version(self, shard_client_obj):
        marker = object()
        shard_client_obj._connection.version = marker
        assert shard_client_obj.version is marker

    def test_intents(self, shard_client_obj):
        marker = object()
        shard_client_obj._connection.intents = marker
        assert shard_client_obj.intents is marker


class TestShardClientImplStart:
    @pytest.mark.asyncio
    async def test_start_when_ready_event_completes_first_without_error(self, shard_client_obj):
        shard_client_obj._connection.seq = 123
        shard_client_obj._connection.session_id = 123
        stop_event = asyncio.Event()
        try:

            async def forever():
                # make this so that it doesn't complete in time;
                await stop_event.wait()

            shard_client_obj._keep_alive = mock.MagicMock(wraps=forever)
            # Make this last a really long time so it doesn't complete immediately.
            shard_client_obj._connection.ready_event = mock.MagicMock(wait=mock.AsyncMock())

            # Do iiiit.
            await shard_client_obj.start()
        finally:
            stop_event.set()

    @_helpers.assert_raises(type_=LookupError)
    @pytest.mark.asyncio
    async def test_start_when_ready_event_completes_first_with_error(self, shard_client_obj):
        shard_client_obj._connection.seq = 123
        shard_client_obj._connection.session_id = 123
        stop_event = asyncio.Event()
        try:

            async def forever():
                # make this so that it doesn't complete in time;
                await stop_event.wait()

            shard_client_obj._keep_alive = mock.MagicMock(wraps=forever)
            # Make this last a really long time so it doesn't complete immediately.
            shard_client_obj._connection.ready_event = mock.MagicMock(wait=mock.AsyncMock(side_effect=LookupError))

            # Do iiiit.
            await shard_client_obj.start()
        finally:
            stop_event.set()

    @pytest.mark.asyncio
    async def test_start_when_task_completes_with_no_exception(self, shard_client_obj):
        shard_client_obj._connection.seq = 123
        shard_client_obj._connection.session_id = 123
        stop_event = asyncio.Event()
        try:

            async def forever():
                # make this so that it doesn't complete in time;
                await stop_event.wait()

            shard_client_obj._keep_alive = mock.AsyncMock()
            # Make this last a really long time so it doesn't complete immediately.
            shard_client_obj._connection.ready_event = mock.MagicMock(wait=forever)

            # Do iiiit.
            await shard_client_obj.start()
        finally:
            stop_event.set()

    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.asyncio
    async def test_start_when_task_completes_with_exception(self, shard_client_obj):
        shard_client_obj._connection.seq = 123
        shard_client_obj._connection.session_id = 123
        stop_event = asyncio.Event()
        try:

            async def forever():
                # make this so that it doesn't complete in time;
                await stop_event.wait()

            shard_client_obj._keep_alive = mock.AsyncMock(side_effect=RuntimeError)
            # Make this last a really long time so it doesn't complete immediately.
            shard_client_obj._connection.ready_event = mock.MagicMock(wait=forever)

            # Do iiiit.
            await shard_client_obj.start()
        finally:
            stop_event.set()

    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.asyncio
    async def test_start_when_already_started(self, shard_client_obj):
        shard_client_obj._shard_state = hikari.gateway.gateway_state.GatewayState.READY

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
        shard_client_obj._shard_state = hikari.gateway.gateway_state.GatewayState.STOPPING

        await shard_client_obj.close()

        shard_client_obj._connection.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_close_when_not_running_is_not_an_error(self, shard_client_obj):
        shard_client_obj._shard_state = hikari.gateway.gateway_state.GatewayState.NOT_RUNNING
        shard_client_obj._task = None

        await shard_client_obj.close()

        shard_client_obj._connection.close.assert_called_once()

    @_helpers.timeout_after(5)
    @pytest.mark.asyncio
    async def test__keep_alive_repeats_silently_if_task_returns(self, shard_client_obj):
        shard_client_obj._spin_up = mock.AsyncMock(return_value=more_asyncio.completed_future())

        try:
            async with async_timeout.timeout(1):
                await shard_client_obj._keep_alive()
            assert False
        except asyncio.TimeoutError:
            assert shard_client_obj._spin_up.await_count > 0

    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.parametrize(
        "error",
        [
            aiohttp.ClientConnectorError(mock.MagicMock(), mock.MagicMock()),
            errors.GatewayZombiedError(),
            errors.GatewayInvalidSessionError(False),
            errors.GatewayInvalidSessionError(True),
            errors.GatewayMustReconnectError(),
            errors.GatewayClientDisconnectedError(),
        ],
    )
    @pytest.mark.asyncio
    @_helpers.timeout_after(5)
    async def test__keep_alive_handles_errors(self, error, shard_client_obj):
        should_return = False

        def side_effect(*args):
            nonlocal should_return
            if should_return:
                return _helpers.AwaitableMock(return_value=RuntimeError)

            should_return = True
            return _helpers.AwaitableMock(return_value=error)

        shard_client_obj._spin_up = mock.MagicMock(side_effect=side_effect)

        with mock.patch("asyncio.sleep", new=mock.AsyncMock()):
            await shard_client_obj._keep_alive()

    @pytest.mark.asyncio
    @_helpers.timeout_after(5)
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
    @_helpers.timeout_after(5)
    async def test__keep_alive_shuts_down_when_GatewayServerClosedConnectionError(self, code, shard_client_obj):
        shard_client_obj._spin_up = mock.AsyncMock(
            return_value=_helpers.AwaitableMock(return_value=errors.GatewayServerClosedConnectionError(code))
        )

        with mock.patch("asyncio.sleep", new=mock.AsyncMock()):
            await shard_client_obj._keep_alive()

    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.asyncio
    @_helpers.timeout_after(5)
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


class TestShardClientImplSpinUp:
    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.asyncio
    async def test__spin_up_if_connect_task_is_completed_raises_exception_during_hello_event(self, shard_client_obj):
        stop_event = asyncio.Event()
        try:

            async def forever():
                # make this so that it doesn't complete in time;
                await stop_event.wait()

            # Make this last a really long time so it doesn't complete immediately.
            shard_client_obj._connection.connect = mock.MagicMock(wraps=forever)

            # Make these finish immediately.
            shard_client_obj._connection.hello_event = mock.MagicMock(wait=mock.AsyncMock(side_effect=RuntimeError))

            # Do iiiit.
            await shard_client_obj._spin_up()
        finally:
            stop_event.set()

    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.asyncio
    async def test__spin_up_if_connect_task_is_completed_raises_exception_during_identify_event(self, shard_client_obj):
        stop_event = asyncio.Event()
        try:

            async def forever():
                # make this so that it doesn't complete in time;
                await stop_event.wait()

            # Make this last a really long time so it doesn't complete immediately.
            shard_client_obj._connection.connect = mock.MagicMock(wraps=forever)

            # Make these finish immediately.
            shard_client_obj._connection.hello_event = mock.MagicMock(wait=mock.AsyncMock())
            shard_client_obj._connection.handshake_event = mock.MagicMock(wait=mock.AsyncMock(side_effect=RuntimeError))

            # Do iiiit.
            await shard_client_obj._spin_up()
        finally:
            stop_event.set()

    @pytest.mark.asyncio
    async def test__spin_up_when_resuming(self, shard_client_obj):
        shard_client_obj._connection.seq = 123
        shard_client_obj._connection.session_id = 123
        stop_event = asyncio.Event()
        try:

            async def forever():
                # make this so that it doesn't complete in time;
                await stop_event.wait()

            # Make this last a really long time so it doesn't complete immediately.
            shard_client_obj._connection.connect = mock.MagicMock(wraps=forever)

            # Make these finish immediately.
            shard_client_obj._connection.hello_event = mock.MagicMock(wait=mock.AsyncMock())
            shard_client_obj._connection.handshake_event = mock.MagicMock(wait=mock.AsyncMock())

            # Make this one go boom.
            shard_client_obj._connection.resumed_event = mock.MagicMock(wait=mock.AsyncMock())

            # Do iiiit.
            await shard_client_obj._spin_up()
        finally:
            stop_event.set()

    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.asyncio
    async def test__spin_up_if_connect_task_is_completed_raises_exception_during_resumed_event(self, shard_client_obj):
        shard_client_obj._connection.seq = 123
        shard_client_obj._connection.session_id = 123
        stop_event = asyncio.Event()
        try:

            async def forever():
                # make this so that it doesn't complete in time;
                await stop_event.wait()

            # Make this last a really long time so it doesn't complete immediately.
            shard_client_obj._connection.connect = mock.MagicMock(wraps=forever)

            # Make these finish immediately.
            shard_client_obj._connection.hello_event = mock.MagicMock(wait=mock.AsyncMock())
            shard_client_obj._connection.handshake_event = mock.MagicMock(wait=mock.AsyncMock())

            # Make this one go boom.
            shard_client_obj._connection.resumed_event = mock.MagicMock(wait=mock.AsyncMock(side_effect=RuntimeError))

            # Do iiiit.
            await shard_client_obj._spin_up()
        finally:
            stop_event.set()

    @pytest.mark.asyncio
    async def test__spin_up_when_not_resuming(self, shard_client_obj):
        shard_client_obj._connection.seq = None
        shard_client_obj._connection.session_id = None
        stop_event = asyncio.Event()
        try:

            async def forever():
                # make this so that it doesn't complete in time;
                await stop_event.wait()

            # Make this last a really long time so it doesn't complete immediately.
            shard_client_obj._connection.connect = mock.MagicMock(wraps=forever)

            # Make these finish immediately.
            shard_client_obj._connection.hello_event = mock.MagicMock(wait=mock.AsyncMock())
            shard_client_obj._connection.handshake_event = mock.MagicMock(wait=mock.AsyncMock())

            # Make this one go boom.
            shard_client_obj._connection.ready_event = mock.MagicMock(wait=mock.AsyncMock())

            # Do iiiit.
            await shard_client_obj._spin_up()
        finally:
            stop_event.set()

    @_helpers.timeout_after(10)
    @_helpers.assert_raises(type_=RuntimeError)
    @pytest.mark.asyncio
    async def test__spin_up_if_connect_task_is_completed_raises_exception_during_ready_event(self, shard_client_obj):
        stop_event = asyncio.Event()
        try:

            async def forever():
                # make this so that it doesn't complete in time;
                await stop_event.wait()

            # Make this last a really long time so it doesn't complete immediately.
            shard_client_obj._connection.connect = mock.MagicMock(wraps=forever)

            # Make these finish immediately.
            shard_client_obj._connection.hello_event = mock.MagicMock(wait=mock.AsyncMock())
            shard_client_obj._connection.handshake_event = mock.MagicMock(wait=mock.AsyncMock())

            # Make this one go boom.
            shard_client_obj._connection.ready_event = mock.MagicMock(wait=mock.AsyncMock(side_effect=RuntimeError))

            # Do iiiit.
            await shard_client_obj._spin_up()
        finally:
            stop_event.set()


class TestShardClientImplUpdatePresence:
    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=ValueError)
    async def test_update_presence_with_no_arguments(self, shard_client_obj):
        await shard_client_obj.update_presence()

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
        assert shard_client_obj._activity is None
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
