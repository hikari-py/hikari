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

import mock
import pytest

from hikari import errors
from hikari import snowflakes
from hikari.events import voice_events
from hikari.impl import voice
from tests.hikari import hikari_test_helpers


class TestVoiceComponentImpl:
    @pytest.fixture
    def mock_app(self):
        return mock.Mock()

    @pytest.fixture
    def voice_client(self, mock_app):
        client = hikari_test_helpers.mock_class_namespace(voice.VoiceComponentImpl, slots_=False)(mock_app)
        client._is_alive = True
        return client

    def test_is_alive_property(self, voice_client):
        voice_client.is_alive is voice_client._is_alive

    def test__check_if_alive_when_alive(self, voice_client):
        voice_client._is_alive = True
        voice_client._check_if_alive()

    def test__check_if_alive_when_not_alive(self, voice_client):
        voice_client._is_alive = False

        with pytest.raises(errors.ComponentStateConflictError):
            voice_client._check_if_alive()

    def test__check_if_alive_when_closing(self, voice_client):
        voice_client._is_alive = True
        voice_client._is_closing = True

        with pytest.raises(errors.ComponentStateConflictError):
            voice_client._check_if_alive()

    @pytest.mark.asyncio
    async def test_disconnect(self, voice_client):
        mock_connection = mock.AsyncMock()
        mock_connection_2 = mock.AsyncMock()
        voice_client._connections = {
            snowflakes.Snowflake(123): mock_connection,
            snowflakes.Snowflake(5324): mock_connection_2,
        }
        voice_client._check_if_alive = mock.Mock()

        await voice_client.disconnect(123)

        voice_client._check_if_alive.assert_called_once_with()
        mock_connection.disconnect.assert_awaited_once_with()
        mock_connection_2.disconnect.assert_not_called()

    @pytest.mark.asyncio
    async def test_disconnect_when_guild_id_not_in_connections(self, voice_client):
        mock_connection = mock.AsyncMock()
        mock_connection_2 = mock.AsyncMock()
        voice_client._connections = {123: mock_connection, 5324: mock_connection_2}

        with pytest.raises(errors.VoiceError):
            await voice_client.disconnect(1234567890)

        mock_connection.disconnect.assert_not_called()
        mock_connection_2.disconnect.assert_not_called()

    @pytest.mark.asyncio
    async def test__disconnect_all(self, voice_client):
        mock_connection = mock.AsyncMock()
        mock_connection_2 = mock.AsyncMock()
        voice_client._connections = {123: mock_connection, 5324: mock_connection_2}

        await voice_client._disconnect_all()

        mock_connection.disconnect.assert_awaited_once_with()
        mock_connection_2.disconnect.assert_awaited_once_with()

    @pytest.mark.asyncio
    async def test_disconnect_all(self, voice_client):
        voice_client._disconnect_all = mock.AsyncMock()
        voice_client._check_if_alive = mock.Mock()

        await voice_client.disconnect_all()

        voice_client._check_if_alive.assert_called_once_with()
        voice_client._disconnect_all.assert_awaited_once_with()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("voice_listener", [True, False])
    async def test_close(self, voice_client, mock_app, voice_listener):
        voice_client._disconnect_all = mock.AsyncMock()
        voice_client._connections = {123: None}
        voice_client._check_if_alive = mock.Mock()
        voice_client._voice_listener = voice_listener

        await voice_client.close()

        if voice_listener:
            mock_app.event_manager.unsubscribe.assert_called_once_with(
                voice_events.VoiceEvent, voice_client._on_voice_event
            )
        else:
            mock_app.event_manager.unsubscribe.assert_not_called()

        voice_client._check_if_alive.assert_called_once_with()
        voice_client._disconnect_all.assert_awaited_once_with()
        assert voice_client._is_alive is False
        assert voice_client._is_closing is False

    @pytest.mark.asyncio
    @pytest.mark.parametrize("voice_listener", [True, False])
    async def test_close_when_no_connections(self, voice_client, mock_app, voice_listener):
        voice_client._disconnect_all = mock.AsyncMock()
        voice_client._connections = {}
        voice_client._check_if_alive = mock.Mock()
        voice_client._voice_listener = voice_listener

        await voice_client.close()

        if voice_listener:
            mock_app.event_manager.unsubscribe.assert_called_once_with(
                voice_events.VoiceEvent, voice_client._on_voice_event
            )
        else:
            mock_app.event_manager.unsubscribe.assert_not_called()

        voice_client._check_if_alive.assert_called_once_with()
        voice_client._disconnect_all.assert_not_called()
        assert voice_client._is_alive is False
        assert voice_client._is_closing is False

    def test_start(self, voice_client, mock_app):
        voice_client._is_alive = False

        voice_client.start()

        assert voice_client._is_alive is True

    @pytest.mark.asyncio
    async def test_start_when_already_alive(self, voice_client, mock_app):
        voice_client._is_alive = True

        with pytest.raises(errors.ComponentStateConflictError):
            await voice_client.start()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("voice_listener", [True, False])
    async def test_connect_to(self, voice_client, mock_app, voice_listener):
        voice_client._init_state_update_predicate = mock.Mock()
        voice_client._init_server_update_predicate = mock.Mock()
        mock_other_connection = object()
        voice_client._connections = {555: mock_other_connection}
        mock_shard = mock.AsyncMock(is_alive=True)
        mock_app.event_manager.wait_for = mock.AsyncMock()
        mock_app.shard_count = 42
        mock_app.shards = {0: mock_shard}
        mock_connection_type = mock.AsyncMock()
        voice_client._check_if_alive = mock.Mock()
        voice_client._voice_listener = voice_listener

        result = await voice_client.connect_to(123, 4532, mock_connection_type, deaf=False, mute=True, timeout=None)

        voice_client._check_if_alive.assert_called_once_with()
        mock_app.event_manager.wait_for.assert_has_awaits(
            [
                mock.call(
                    voice_events.VoiceStateUpdateEvent,
                    timeout=None,
                    predicate=voice_client._init_state_update_predicate.return_value,
                ),
                mock.call(
                    voice_events.VoiceServerUpdateEvent,
                    timeout=None,
                    predicate=voice_client._init_server_update_predicate.return_value,
                ),
            ]
        )
        mock_app.rest.fetch_my_user.assert_not_called()
        mock_app.cache.get_me.assert_called_once_with()
        voice_client._init_state_update_predicate.assert_called_once_with(123, mock_app.cache.get_me.return_value.id)
        voice_client._init_server_update_predicate.assert_called_once_with(123)
        if voice_listener:
            mock_app.event_manager.subscribe.assert_not_called()
        else:
            mock_app.event_manager.subscribe.assert_called_once_with(
                voice_events.VoiceEvent, voice_client._on_voice_event
            )

        assert voice_client._voice_listener is True
        mock_shard.update_voice_state.assert_awaited_once_with(123, 4532, self_deaf=False, self_mute=True)
        assert voice_client._connections == {
            123: mock_connection_type.initialize.return_value,
            555: mock_other_connection,
        }
        assert result is mock_connection_type.initialize.return_value

    @pytest.mark.asyncio
    async def test_connect_to_fails_when_wait_for_timeout(self, voice_client, mock_app):
        mock_shard = mock.AsyncMock(is_alive=True)
        mock_wait_for = mock.AsyncMock()
        mock_wait_for.side_effect = asyncio.TimeoutError
        mock_app.event_manager.wait_for = mock_wait_for
        mock_app.shard_count = 42
        mock_app.shards = {0: mock_shard}
        mock_connection_type = mock.AsyncMock()

        with pytest.raises(errors.VoiceError, match="Could not connect to voice channel 4532 in guild 123."):
            await voice_client.connect_to(123, 4532, mock_connection_type)

    @pytest.mark.asyncio
    async def test_connect_to_falls_back_to_rest_to_get_own_user(self, voice_client, mock_app):
        voice_client._init_state_update_predicate = mock.Mock()
        voice_client._init_server_update_predicate = mock.Mock()
        mock_shard = mock.AsyncMock(is_alive=True)
        mock_app.event_manager.wait_for = mock.AsyncMock()
        mock_app.shard_count = 42
        mock_app.shards = {0: mock_shard}
        mock_app.cache.get_me.return_value = None
        mock_app.rest = mock.AsyncMock()
        mock_connection_type = mock.AsyncMock()

        await voice_client.connect_to(123, 4532, mock_connection_type, deaf=False, mute=True, timeout=None)

        mock_app.event_manager.wait_for.assert_has_awaits(
            [
                mock.call(
                    voice_events.VoiceStateUpdateEvent,
                    timeout=None,
                    predicate=voice_client._init_state_update_predicate.return_value,
                ),
                mock.call(
                    voice_events.VoiceServerUpdateEvent,
                    timeout=None,
                    predicate=voice_client._init_server_update_predicate.return_value,
                ),
            ]
        )
        mock_app.cache.get_me.assert_called_once_with()
        mock_app.rest.fetch_my_user.assert_awaited_once_with()
        voice_client._init_state_update_predicate.assert_called_once_with(
            123, mock_app.rest.fetch_my_user.return_value.id
        )

    @pytest.mark.asyncio
    async def test_connect_to_when_connection_already_present(self, voice_client, mock_app):
        voice_client._connections = {snowflakes.Snowflake(123): object()}

        with pytest.raises(
            errors.VoiceError,
            match="Already in a voice channel for that guild. Disconnect before attempting to connect again",
        ):
            await voice_client.connect_to(123, 4532, object())

    @pytest.mark.asyncio
    async def test_connect_to_for_unknown_shard(self, voice_client, mock_app):
        mock_app.shard_count = 42
        mock_app.shards = {}

        with pytest.raises(
            errors.VoiceError, match="Cannot connect to shard 0 as it is not present in this application"
        ):
            await voice_client.connect_to(123, 4532, object())

    @pytest.mark.asyncio
    async def test_connect_to_handles_failed_connection_initialise(self, voice_client, mock_app):
        voice_client._init_state_update_predicate = mock.Mock()
        voice_client._init_server_update_predicate = mock.Mock()
        mock_shard = mock.Mock(is_alive=True)
        update_voice_state_call_1 = mock.AsyncMock()
        update_voice_state_call_2 = mock.Mock()
        mock_shard.update_voice_state = mock.Mock(
            side_effect=[update_voice_state_call_1(), update_voice_state_call_2()]
        )
        mock_app.event_manager.wait_for = mock.AsyncMock()
        mock_app.shard_count = 42
        mock_app.shards = {0: mock_shard}

        class StubError(Exception): ...

        mock_connection_type = mock.AsyncMock()
        mock_connection_type.initialize.side_effect = StubError

        with mock.patch.object(
            asyncio, "wait_for", new=mock.AsyncMock(side_effect=asyncio.TimeoutError)
        ) as asyncio_wait_for:
            with pytest.raises(StubError):
                await voice_client.connect_to(123, 4532, mock_connection_type, deaf=False, mute=True, timeout=None)

        mock_app.event_manager.wait_for.assert_has_awaits(
            [
                mock.call(
                    voice_events.VoiceStateUpdateEvent,
                    timeout=None,
                    predicate=voice_client._init_state_update_predicate.return_value,
                ),
                mock.call(
                    voice_events.VoiceServerUpdateEvent,
                    timeout=None,
                    predicate=voice_client._init_server_update_predicate.return_value,
                ),
            ]
        )
        mock_app.cache.get_me.assert_called_once_with()
        voice_client._init_state_update_predicate.assert_called_once_with(123, mock_app.cache.get_me.return_value.id)
        voice_client._init_server_update_predicate.assert_called_once_with(123)
        mock_shard.update_voice_state.assert_has_calls(
            [mock.call(123, 4532, self_deaf=False, self_mute=True), mock.call(123, None)]
        )
        update_voice_state_call_1.assert_awaited_once()
        asyncio_wait_for.assert_awaited_once_with(update_voice_state_call_2.return_value, timeout=5.0)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("more_connections", [True, False])
    async def test__on_connection_close(self, voice_client, mock_app, more_connections):
        mock_shard = mock.AsyncMock()
        mock_app.shards = {69: mock_shard}
        voice_client._connections = {65234123: object()}
        expected_connections = {}
        if more_connections:
            mock_connection = object()
            voice_client._connections[123] = mock_connection
            expected_connections[123] = mock_connection

        await voice_client._on_connection_close(mock.Mock(guild_id=65234123, shard_id=69))

        if more_connections:
            mock_app.event_manager.unsubscribe.assert_not_called()
        else:
            mock_app.event_manager.unsubscribe.assert_called_once_with(
                voice_events.VoiceEvent, voice_client._on_voice_event
            )

        mock_shard.update_voice_state.assert_awaited_once_with(guild=65234123, channel=None)
        assert voice_client._connections == expected_connections

    def test__init_state_update_predicate_matches(self, voice_client):
        predicate = voice_client._init_state_update_predicate(42069, 696969)
        mock_voice_state = mock.Mock(state=mock.Mock(guild_id=42069, user_id=696969))

        assert predicate(mock_voice_state) is True

    def test__init_state_update_predicate_ignores(self, voice_client):
        predicate = voice_client._init_state_update_predicate(999, 420)
        mock_voice_state = mock.Mock(state=mock.Mock(guild_id=6969, user_id=3333))

        assert predicate(mock_voice_state) is False

    def test__init_server_update_predicate_matches(self, voice_client):
        predicate = voice_client._init_server_update_predicate(696969)
        mock_voice_state = mock.Mock(guild_id=696969)

        assert predicate(mock_voice_state) is True

    def test__init_server_update_predicate_ignores(self, voice_client):
        predicate = voice_client._init_server_update_predicate(321231)
        mock_voice_state = mock.Mock(guild_id=123123123)

        assert predicate(mock_voice_state) is False

    @pytest.mark.asyncio
    async def test__on_connection_close_ignores_unknown_voice_state(self, voice_client):
        connections = {123132: object(), 65234234: object()}
        voice_client._connections = connections.copy()

        await voice_client._on_connection_close(mock.Mock(guild_id=-1))

        assert voice_client._connections == connections

    @pytest.mark.asyncio
    async def test__on_voice_event(self, voice_client):
        mock_connection = mock.AsyncMock()
        voice_client._connections = {6633: mock_connection}
        mock_event = mock.Mock(guild_id=6633)

        await voice_client._on_voice_event(mock_event)

        mock_connection.notify.assert_awaited_once_with(mock_event)

    @pytest.mark.asyncio
    async def test__on_voice_event_for_untracked_guild(self, voice_client):
        mock_event = mock.Mock(guild_id=44444)

        await voice_client._on_voice_event(mock_event)
