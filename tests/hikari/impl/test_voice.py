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
from __future__ import annotations

import asyncio

import mock
import pytest

from hikari import errors
from hikari import snowflakes
from hikari import traits
from hikari.api import voice as voice_api
from hikari.events import voice_events
from hikari.impl import voice


class TestVoiceComponentImpl:
    @pytest.fixture
    def mock_app(self) -> traits.GatewayBotAware:
        return mock.Mock(traits.GatewayBotAware)

    @pytest.fixture
    def voice_client(self, mock_app: traits.GatewayBotAware) -> voice.VoiceComponentImpl:
        client = voice.VoiceComponentImpl(mock_app)
        client._is_alive = True
        return client

    def test_is_alive_property(self, voice_client: voice.VoiceComponentImpl):
        assert voice_client.is_alive is voice_client._is_alive

    def test__check_if_alive_when_alive(self, voice_client: voice.VoiceComponentImpl):
        with mock.patch.object(voice_client, "_is_alive", True):
            assert voice_client._check_if_alive() is None

    def test__check_if_alive_when_not_alive(self, voice_client: voice.VoiceComponentImpl):
        voice_client._is_alive = False

        with mock.patch.object(voice_client, "_is_alive", False), pytest.raises(errors.ComponentStateConflictError):
            voice_client._check_if_alive()

    def test__check_if_alive_when_closing(self, voice_client: voice.VoiceComponentImpl):
        with (
            mock.patch.object(voice_client, "_is_alive", True),
            mock.patch.object(voice_client, "_is_closing", True),
            pytest.raises(errors.ComponentStateConflictError),
        ):
            voice_client._check_if_alive()

    @pytest.mark.asyncio
    async def test_disconnect(self, voice_client: voice.VoiceComponentImpl):
        mock_connection = mock.AsyncMock()
        mock_connection_2 = mock.AsyncMock()
        voice_client._connections = {
            snowflakes.Snowflake(123): mock_connection,
            snowflakes.Snowflake(5324): mock_connection_2,
        }

        with mock.patch.object(voice.VoiceComponentImpl, "_check_if_alive") as patched__check_if_alive:
            await voice_client.disconnect(123)

            patched__check_if_alive.assert_called_once_with()
            mock_connection.disconnect.assert_awaited_once_with()
            mock_connection_2.disconnect.assert_not_called()

    @pytest.mark.asyncio
    async def test_disconnect_when_guild_id_not_in_connections(self, voice_client: voice.VoiceComponentImpl):
        mock_connection = mock.AsyncMock()
        mock_connection_2 = mock.AsyncMock()
        voice_client._connections = {
            snowflakes.Snowflake(123): mock_connection,
            snowflakes.Snowflake(5324): mock_connection_2,
        }

        with pytest.raises(errors.VoiceError):
            await voice_client.disconnect(1234567890)

        mock_connection.disconnect.assert_not_called()
        mock_connection_2.disconnect.assert_not_called()

    @pytest.mark.asyncio
    async def test__disconnect_all(self, voice_client: voice.VoiceComponentImpl):
        mock_connection = mock.AsyncMock()
        mock_connection_2 = mock.AsyncMock()
        voice_client._connections = {
            snowflakes.Snowflake(123): mock_connection,
            snowflakes.Snowflake(5324): mock_connection_2,
        }

        await voice_client._disconnect_all()

        mock_connection.disconnect.assert_awaited_once_with()
        mock_connection_2.disconnect.assert_awaited_once_with()

    @pytest.mark.asyncio
    async def test_disconnect_all(self, voice_client: voice.VoiceComponentImpl):
        with (
            mock.patch.object(voice.VoiceComponentImpl, "_disconnect_all", mock.AsyncMock()) as patched__disconnect_all,
            mock.patch.object(voice.VoiceComponentImpl, "_check_if_alive") as patched__check_if_alive,
        ):
            await voice_client.disconnect_all()

            patched__check_if_alive.assert_called_once_with()
            patched__disconnect_all.assert_awaited_once_with()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("voice_listener", [True, False])
    async def test_close(self, voice_client: voice.VoiceComponentImpl, voice_listener: bool):
        voice_client._connections = {snowflakes.Snowflake(123): mock.Mock()}

        with (
            mock.patch.object(voice.VoiceComponentImpl, "_disconnect_all", mock.AsyncMock()) as patched__disconnect_all,
            mock.patch.object(voice.VoiceComponentImpl, "_check_if_alive") as patched__check_if_alive,
            mock.patch.object(voice_client, "_voice_listener", voice_listener),
            mock.patch.object(voice_client, "_app", mock.Mock(traits.EventManagerAware)) as patched_app,
            mock.patch.object(patched_app.event_manager, "unsubscribe") as patched_unsubscribe,
        ):
            await voice_client.close()

            if voice_listener:
                patched_unsubscribe.assert_called_once_with(voice_events.VoiceEvent, voice_client._on_voice_event)
            else:
                patched_unsubscribe.assert_not_called()

            patched__check_if_alive.assert_called_once_with()
            patched__disconnect_all.assert_awaited_once_with()
            assert voice_client._is_alive is False
            assert voice_client._is_closing is False

    @pytest.mark.asyncio
    @pytest.mark.parametrize("voice_listener", [True, False])
    async def test_close_when_no_connections(self, voice_client: voice.VoiceComponentImpl, voice_listener: bool):
        voice_client._connections = {}

        with (
            mock.patch.object(voice.VoiceComponentImpl, "_disconnect_all", mock.AsyncMock()) as patched__disconnect_all,
            mock.patch.object(voice.VoiceComponentImpl, "_check_if_alive") as patched__check_if_alive,
            mock.patch.object(voice_client, "_voice_listener", voice_listener),
            mock.patch.object(voice_client, "_app", mock.Mock(traits.EventManagerAware)) as patched_app,
            mock.patch.object(patched_app.event_manager, "unsubscribe") as patched_unsubscribe,
        ):
            await voice_client.close()

            if voice_listener:
                patched_unsubscribe.assert_called_once_with(voice_events.VoiceEvent, voice_client._on_voice_event)
            else:
                patched_unsubscribe.assert_not_called()

            patched__check_if_alive.assert_called_once_with()
            patched__disconnect_all.assert_not_called()
            assert voice_client._is_alive is False
            assert voice_client._is_closing is False

    def test_start(self, voice_client: voice.VoiceComponentImpl):
        voice_client._is_alive = False

        voice_client.start()

        assert voice_client._is_alive is True

    @pytest.mark.asyncio
    async def test_start_when_already_alive(self, voice_client: voice.VoiceComponentImpl):
        voice_client._is_alive = True

        with pytest.raises(errors.ComponentStateConflictError):
            voice_client.start()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("voice_listener", [True, False])
    async def test_connect_to(
        self, voice_client: voice.VoiceComponentImpl, mock_app: traits.RESTAware, voice_listener: bool
    ):
        mock_shard = mock.AsyncMock(is_alive=True)

        with (
            mock.patch.object(
                voice.VoiceComponentImpl, "_init_state_update_predicate"
            ) as patched__init_state_update_predicate,
            mock.patch.object(
                voice.VoiceComponentImpl, "_init_server_update_predicate"
            ) as patched__init_server_update_predicate,
            mock.patch.object(mock_app, "shard_count", 42),
            mock.patch.object(mock_app, "shards", {0: mock_shard}),
            mock.patch.object(mock_app, "event_manager") as patched_event_manager,
            mock.patch.object(patched_event_manager, "wait_for", mock.AsyncMock()) as patched_wait_for,
            mock.patch.object(patched_event_manager, "subscribe") as patched_subscribe,
            mock.patch.object(voice.VoiceComponentImpl, "_check_if_alive") as patched__check_if_alive,
            mock.patch.object(mock_app.rest, "fetch_my_user") as patched_fetch_my_user,
            mock.patch.object(mock_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_me") as patched_get_me,
        ):
            mock_other_connection = mock.Mock(voice_api.VoiceComponent)
            voice_client._connections = {snowflakes.Snowflake(555): mock_other_connection}

            # FIXME: How is this even legal?????
            mock_connection_type = mock.Mock
            mock_connection_type.initialize = mock.AsyncMock()

            voice_client._voice_listener = voice_listener

            result = await voice_client.connect_to(123, 4532, mock_connection_type, deaf=False, mute=True, timeout=None)

            patched__check_if_alive.assert_called_once_with()
            patched_wait_for.assert_has_awaits(
                [
                    mock.call(
                        voice_events.VoiceStateUpdateEvent,
                        timeout=None,
                        predicate=patched__init_state_update_predicate.return_value,
                    ),
                    mock.call(
                        voice_events.VoiceServerUpdateEvent,
                        timeout=None,
                        predicate=patched__init_server_update_predicate.return_value,
                    ),
                ]
            )
            patched_fetch_my_user.assert_not_called()
            patched_get_me.assert_called_once_with()
            patched__init_state_update_predicate.assert_called_once_with(123, patched_get_me.return_value.id)
            patched__init_server_update_predicate.assert_called_once_with(123)
            if voice_listener:
                patched_subscribe.assert_not_called()
            else:
                patched_subscribe.assert_called_once_with(voice_events.VoiceEvent, voice_client._on_voice_event)

            assert voice_client._voice_listener is True
            mock_shard.update_voice_state.assert_awaited_once_with(123, 4532, self_deaf=False, self_mute=True)
            assert voice_client._connections == {
                123: mock_connection_type.initialize.return_value,
                555: mock_other_connection,
            }
            assert result is mock_connection_type.initialize.return_value

    @pytest.mark.asyncio
    async def test_connect_to_fails_when_wait_for_timeout(
        self, voice_client: voice.VoiceComponentImpl, mock_app: traits.RESTAware
    ):
        mock_shard = mock.AsyncMock(is_alive=True)
        mock_wait_for = mock.AsyncMock()
        mock_wait_for.side_effect = asyncio.TimeoutError
        mock_connection_type = mock.AsyncMock

        with (
            mock.patch.object(mock_app, "shard_count", 42),
            mock.patch.object(mock_app, "shards", {0: mock_shard}),
            mock.patch.object(mock_app, "event_manager") as patched_event_manager,
            mock.patch.object(patched_event_manager, "wait_for", mock_wait_for),
            pytest.raises(errors.VoiceError, match="Could not connect to voice channel 4532 in guild 123."),
        ):
            await voice_client.connect_to(123, 4532, mock_connection_type)

    @pytest.mark.asyncio
    async def test_connect_to_falls_back_to_rest_to_get_own_user(
        self, voice_client: voice.VoiceComponentImpl, mock_app: traits.RESTAware
    ):
        mock_shard = mock.AsyncMock(is_alive=True)

        with (
            mock.patch.object(
                voice.VoiceComponentImpl, "_init_state_update_predicate"
            ) as patched__init_state_update_predicate,
            mock.patch.object(
                voice.VoiceComponentImpl, "_init_server_update_predicate"
            ) as patched__init_server_update_predicate,
            mock.patch.object(mock_app, "shard_count", 42),
            mock.patch.object(mock_app, "shards", {0: mock_shard}),
            mock.patch.object(mock_app, "event_manager") as patched_event_manager,
            mock.patch.object(patched_event_manager, "wait_for", mock.AsyncMock()) as patched_wait_for,
            mock.patch.object(mock_app.rest, "fetch_my_user", mock.AsyncMock()) as patched_fetch_my_user,
            mock.patch.object(mock_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_me", return_value=None) as patched_get_me,
        ):
            mock_connection_type = mock.Mock
            mock_connection_type.initialize = mock.AsyncMock()

            await voice_client.connect_to(123, 4532, mock_connection_type, deaf=False, mute=True, timeout=None)

            patched_wait_for.assert_has_awaits(
                [
                    mock.call(
                        voice_events.VoiceStateUpdateEvent,
                        timeout=None,
                        predicate=patched__init_state_update_predicate.return_value,
                    ),
                    mock.call(
                        voice_events.VoiceServerUpdateEvent,
                        timeout=None,
                        predicate=patched__init_server_update_predicate.return_value,
                    ),
                ]
            )
            patched_get_me.assert_called_once_with()
            patched_fetch_my_user.assert_awaited_once_with()
            patched__init_state_update_predicate.assert_called_once_with(123, patched_fetch_my_user.return_value.id)

    @pytest.mark.asyncio
    async def test_connect_to_when_connection_already_present(
        self, voice_client: voice.VoiceComponentImpl, mock_app: traits.RESTAware
    ):
        voice_client._connections = {snowflakes.Snowflake(123): mock.Mock()}

        with pytest.raises(
            errors.VoiceError,
            match="Already in a voice channel for that guild. Disconnect before attempting to connect again",
        ):
            await voice_client.connect_to(123, 4532, mock.Mock)

    @pytest.mark.asyncio
    async def test_connect_to_for_unknown_shard(
        self, voice_client: voice.VoiceComponentImpl, mock_app: traits.RESTAware
    ):
        with (
            mock.patch.object(mock_app, "shard_count", 42),
            mock.patch.object(mock_app, "shards", {}),
            pytest.raises(
                errors.VoiceError, match="Cannot connect to shard 0 as it is not present in this application"
            ),
        ):
            await voice_client.connect_to(123, 4532, mock.Mock)

    @pytest.mark.asyncio
    async def test_connect_to_handles_failed_connection_initialise(
        self, voice_client: voice.VoiceComponentImpl, mock_app: traits.RESTAware
    ):
        mock_shard = mock.Mock(is_alive=True)

        update_voice_state_call_1 = mock.AsyncMock()
        update_voice_state_call_2 = mock.Mock()
        mock_shard.update_voice_state = mock.Mock(
            side_effect=[update_voice_state_call_1(), update_voice_state_call_2()]
        )

        with (
            mock.patch.object(
                voice.VoiceComponentImpl, "_init_state_update_predicate"
            ) as patched__init_state_update_predicate,
            mock.patch.object(
                voice.VoiceComponentImpl, "_init_server_update_predicate"
            ) as patched__init_server_update_predicate,
            mock.patch.object(mock_app, "shard_count", 42),
            mock.patch.object(mock_app, "shards", {0: mock_shard}),
            mock.patch.object(mock_app, "event_manager") as patched_event_manager,
            mock.patch.object(patched_event_manager, "wait_for", mock.AsyncMock()) as patched_wait_for,
            mock.patch.object(mock_app.rest, "fetch_my_user", mock.AsyncMock()),
            mock.patch.object(mock_app, "cache") as patched_cache,
            mock.patch.object(patched_cache, "get_me") as patched_get_me,
        ):

            class StubError(Exception): ...

            mock_connection_type = mock.Mock
            mock_connection_type.initialize = mock.AsyncMock(side_effect=StubError)

            with mock.patch.object(
                asyncio, "wait_for", new=mock.AsyncMock(side_effect=asyncio.TimeoutError)
            ) as asyncio_wait_for:
                with pytest.raises(StubError):
                    await voice_client.connect_to(123, 4532, mock_connection_type, deaf=False, mute=True, timeout=None)

            patched_wait_for.assert_has_awaits(
                [
                    mock.call(
                        voice_events.VoiceStateUpdateEvent,
                        timeout=None,
                        predicate=patched__init_state_update_predicate.return_value,
                    ),
                    mock.call(
                        voice_events.VoiceServerUpdateEvent,
                        timeout=None,
                        predicate=patched__init_server_update_predicate.return_value,
                    ),
                ]
            )
            patched_get_me.assert_called_once_with()
            patched__init_state_update_predicate.assert_called_once_with(123, patched_get_me.return_value.id)
            patched__init_server_update_predicate.assert_called_once_with(123)
            mock_shard.update_voice_state.assert_has_calls(
                [mock.call(123, 4532, self_deaf=False, self_mute=True), mock.call(123, None)]
            )
            update_voice_state_call_1.assert_awaited_once()
            asyncio_wait_for.assert_awaited_once_with(update_voice_state_call_2.return_value, timeout=5.0)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("more_connections", [True, False])
    async def test__on_connection_close(
        self, voice_client: voice.VoiceComponentImpl, mock_app: traits.RESTAware, more_connections: bool
    ):
        mock_shard = mock.AsyncMock()
        voice_client._connections = {snowflakes.Snowflake(65234123): mock.Mock()}
        expected_connections = {}
        if more_connections:
            mock_connection = mock.Mock()
            voice_client._connections[snowflakes.Snowflake(123)] = mock_connection
            expected_connections[123] = mock_connection

        with (
            mock.patch.object(mock_app, "shards", {69: mock_shard}),
            mock.patch.object(mock_app, "event_manager") as patched_event_manager,
            mock.patch.object(patched_event_manager, "unsubscribe") as patched_unsubscribe,
        ):
            await voice_client._on_connection_close(mock.Mock(guild_id=65234123, shard_id=69))

        if more_connections:
            patched_unsubscribe.assert_not_called()
        else:
            patched_unsubscribe.assert_called_once_with(voice_events.VoiceEvent, voice_client._on_voice_event)

        mock_shard.update_voice_state.assert_awaited_once_with(guild=65234123, channel=None)
        assert voice_client._connections == expected_connections

    def test__init_state_update_predicate_matches(self, voice_client: voice.VoiceComponentImpl):
        predicate = voice_client._init_state_update_predicate(snowflakes.Snowflake(42069), snowflakes.Snowflake(696969))
        mock_voice_state = mock.Mock(state=mock.Mock(guild_id=42069, user_id=696969))

        assert predicate(mock_voice_state) is True

    def test__init_state_update_predicate_ignores(self, voice_client: voice.VoiceComponentImpl):
        predicate = voice_client._init_state_update_predicate(snowflakes.Snowflake(999), snowflakes.Snowflake(420))
        mock_voice_state = mock.Mock(state=mock.Mock(guild_id=6969, user_id=3333))

        assert predicate(mock_voice_state) is False

    def test__init_server_update_predicate_matches(self, voice_client: voice.VoiceComponentImpl):
        predicate = voice_client._init_server_update_predicate(snowflakes.Snowflake(696969))
        mock_voice_state = mock.Mock(guild_id=696969)

        assert predicate(mock_voice_state) is True

    def test__init_server_update_predicate_ignores(self, voice_client: voice.VoiceComponentImpl):
        predicate = voice_client._init_server_update_predicate(snowflakes.Snowflake(321231))
        mock_voice_state = mock.Mock(guild_id=123123123)

        assert predicate(mock_voice_state) is False

    @pytest.mark.asyncio
    async def test__on_connection_close_ignores_unknown_voice_state(self, voice_client: voice.VoiceComponentImpl):
        connections: dict[snowflakes.Snowflake, voice_api.VoiceConnection] = {
            snowflakes.Snowflake(123132): mock.Mock(voice_api.VoiceConnection),
            snowflakes.Snowflake(65234234): mock.Mock(voice_api.VoiceConnection),
        }
        voice_client._connections = connections.copy()

        await voice_client._on_connection_close(mock.Mock(guild_id=-1))

        assert voice_client._connections == connections

    @pytest.mark.asyncio
    async def test__on_voice_event(self, voice_client: voice.VoiceComponentImpl):
        mock_connection = mock.AsyncMock()
        voice_client._connections = {snowflakes.Snowflake(6633): mock_connection}
        mock_event = mock.Mock(guild_id=6633)

        await voice_client._on_voice_event(mock_event)

        mock_connection.notify.assert_awaited_once_with(mock_event)

    @pytest.mark.asyncio
    async def test__on_voice_event_for_untracked_guild(self, voice_client: voice.VoiceComponentImpl):
        mock_event = mock.Mock(guild_id=44444)

        await voice_client._on_voice_event(mock_event)
