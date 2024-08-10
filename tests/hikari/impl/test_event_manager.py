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
import base64
import contextlib
import random

import mock
import pytest

from hikari import channels
from hikari import errors
from hikari import intents
from hikari import presences
from hikari.api import event_factory as event_factory_
from hikari.events import guild_events
from hikari.impl import config
from hikari.impl import event_manager
from hikari.internal import time
from tests.hikari import hikari_test_helpers


def test_fixed_size_nonce():
    stack = contextlib.ExitStack()
    monotonic = stack.enter_context(mock.patch.object(time, "monotonic_ns"))
    monotonic.return_value.to_bytes = mock.Mock(return_value="foo")

    randbits = stack.enter_context(mock.patch.object(random, "getrandbits"))
    randbits.return_value.to_bytes = mock.Mock(return_value="bar")

    encode = stack.enter_context(mock.patch.object(base64, "b64encode"))
    encode.return_value.decode = mock.Mock(return_value="nonce")

    with stack:
        assert event_manager._fixed_size_nonce() == "nonce"

    monotonic.assert_called_once_with()
    monotonic.return_value.to_bytes.assert_called_once_with(8, "big")

    randbits.assert_called_once_with(92)
    randbits.return_value.to_bytes.assert_called_once_with(12, "big")

    encode.assert_called_once_with("foobar")
    encode.return_value.decode.assert_called_once_with("ascii")


@pytest.fixture
def shard():
    return mock.Mock(id=987)


@pytest.mark.asyncio
async def test__request_guild_members(shard):
    shard.request_guild_members = mock.AsyncMock()

    await event_manager._request_guild_members(shard, 123, include_presences=True, nonce="okokok")

    shard.request_guild_members.assert_awaited_once_with(123, include_presences=True, nonce="okokok")


@pytest.mark.asyncio
async def test__request_guild_members_handles_state_conflict_error(shard):
    shard.request_guild_members = mock.AsyncMock(side_effect=errors.ComponentStateConflictError(reason="OK"))

    await event_manager._request_guild_members(shard, 123, include_presences=True, nonce="okokok")

    shard.request_guild_members.assert_awaited_once_with(123, include_presences=True, nonce="okokok")


class TestEventManagerImpl:
    @pytest.fixture
    def entity_factory(self):
        return mock.Mock()

    @pytest.fixture
    def event_factory(self):
        return mock.Mock()

    @pytest.fixture
    def event_manager_impl(self, entity_factory, event_factory):
        obj = hikari_test_helpers.mock_class_namespace(event_manager.EventManagerImpl, slots_=False)(
            entity_factory, event_factory, intents.Intents.ALL, cache=mock.Mock(settings=config.CacheSettings())
        )

        obj.dispatch = mock.AsyncMock()
        return obj

    @pytest.fixture
    def stateless_event_manager_impl(self, event_factory, entity_factory):
        obj = hikari_test_helpers.mock_class_namespace(event_manager.EventManagerImpl, slots_=False)(
            entity_factory, event_factory, intents.Intents.ALL, cache=None
        )

        obj.dispatch = mock.AsyncMock()
        return obj

    @pytest.mark.asyncio
    async def test_on_ready_stateful(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock(my_user=mock.Mock())

        event_factory.deserialize_ready_event.return_value = event

        await event_manager_impl.on_ready(shard, payload)

        event_manager_impl._cache.update_me.assert_called_once_with(event.my_user)
        event_factory.deserialize_ready_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_ready_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_ready(shard, payload)

        event_factory.deserialize_ready_event.assert_called_once_with(shard, payload)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_ready_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_resumed(self, event_manager_impl, shard, event_factory):
        payload = {}

        await event_manager_impl.on_resumed(shard, payload)

        event_factory.deserialize_resumed_event.assert_called_once_with(shard)
        event_manager_impl.dispatch.assert_awaited_once_with(event_factory.deserialize_resumed_event.return_value)

    @pytest.mark.asyncio
    async def test_on_application_command_permissions_update(self, event_manager_impl, shard, event_factory):
        payload = {}

        await event_manager_impl.on_application_command_permissions_update(shard, payload)

        event_factory.deserialize_application_command_permission_update_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_application_command_permission_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_channel_create_stateful(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock(channel=mock.Mock(channels.GuildChannel))

        event_factory.deserialize_guild_channel_create_event.return_value = event

        await event_manager_impl.on_channel_create(shard, payload)

        event_manager_impl._cache.set_guild_channel.assert_called_once_with(event.channel)
        event_factory.deserialize_guild_channel_create_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_channel_create_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_channel_create(shard, payload)

        event_factory.deserialize_guild_channel_create_event.assert_called_once_with(shard, payload)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_channel_create_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_channel_update_stateful(self, event_manager_impl, shard, event_factory):
        payload = {"id": 123}
        old_channel = object()
        event = mock.Mock(channel=mock.Mock(channels.GuildChannel))

        event_factory.deserialize_guild_channel_update_event.return_value = event
        event_manager_impl._cache.get_guild_channel.return_value = old_channel

        await event_manager_impl.on_channel_update(shard, payload)

        event_manager_impl._cache.get_guild_channel.assert_called_once_with(123)
        event_manager_impl._cache.update_guild_channel.assert_called_once_with(event.channel)
        event_factory.deserialize_guild_channel_update_event.assert_called_once_with(
            shard, payload, old_channel=old_channel
        )
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_channel_update_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {"id": 123}

        await stateless_event_manager_impl.on_channel_update(shard, payload)

        event_factory.deserialize_guild_channel_update_event.assert_called_once_with(shard, payload, old_channel=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_channel_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_channel_delete_stateful(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock(channel=mock.Mock(id=123))

        event_factory.deserialize_guild_channel_delete_event.return_value = event

        await event_manager_impl.on_channel_delete(shard, payload)

        event_manager_impl._cache.delete_guild_channel.assert_called_once_with(123)
        event_factory.deserialize_guild_channel_delete_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_channel_delete_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_channel_delete(shard, payload)

        event_factory.deserialize_guild_channel_delete_event.assert_called_once_with(shard, payload)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_channel_delete_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_channel_pins_update(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_channel_pins_update(shard, payload)

        event_factory.deserialize_channel_pins_update_event.assert_called_once_with(shard, payload)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_channel_pins_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_thread_create_when_create_stateful(
        self, event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: mock.Mock
    ):
        mock_payload = {"id": "123321", "newly_created": True}
        await event_manager_impl.on_thread_create(shard, mock_payload)

        event = event_factory.deserialize_guild_thread_create_event.return_value
        event_manager_impl._cache.set_thread.assert_called_once_with(event.thread)
        event_manager_impl.dispatch.assert_awaited_once_with(event)
        event_factory.deserialize_guild_thread_create_event.assert_called_once_with(shard, mock_payload)

    @pytest.mark.asyncio
    async def test_on_thread_create_stateless(
        self, stateless_event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: mock.Mock
    ):
        mock_payload = {"id": "123321", "newly_created": True}
        await stateless_event_manager_impl.on_thread_create(shard, mock_payload)

        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_thread_create_event.return_value
        )
        event_factory.deserialize_guild_thread_create_event.assert_called_once_with(shard, mock_payload)

    @pytest.mark.asyncio
    async def test_on_thread_create_for_access_stateful(
        self, event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: mock.Mock
    ):
        mock_payload = {"id": "123321"}
        await event_manager_impl.on_thread_create(shard, mock_payload)

        event = event_factory.deserialize_guild_thread_access_event.return_value
        event_manager_impl._cache.set_thread.assert_called_once_with(event.thread)
        event_manager_impl.dispatch.assert_awaited_once_with(event)
        event_factory.deserialize_guild_thread_access_event.assert_called_once_with(shard, mock_payload)

    @pytest.mark.asyncio
    async def test_on_thread_create_for_access_stateless(
        self, stateless_event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: mock.Mock
    ):
        mock_payload = {"id": "123321"}
        await stateless_event_manager_impl.on_thread_create(shard, mock_payload)

        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_thread_access_event.return_value
        )
        event_factory.deserialize_guild_thread_access_event.assert_called_once_with(shard, mock_payload)

    @pytest.mark.asyncio
    async def test_on_thread_update_stateful(
        self, event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: mock.Mock
    ):
        mock_payload = mock.Mock()
        await event_manager_impl.on_thread_update(shard, mock_payload)

        event = event_factory.deserialize_guild_thread_update_event.return_value
        event_manager_impl._cache.update_thread.assert_called_once_with(event.thread)
        event_manager_impl.dispatch.assert_awaited_once_with(event)
        event_factory.deserialize_guild_thread_update_event.assert_called_once_with(shard, mock_payload)

    @pytest.mark.asyncio
    async def test_on_thread_update_stateless(
        self, stateless_event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: mock.Mock
    ):
        mock_payload = mock.Mock()
        await stateless_event_manager_impl.on_thread_update(shard, mock_payload)

        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_thread_update_event.return_value
        )
        event_factory.deserialize_guild_thread_update_event.assert_called_once_with(shard, mock_payload)

    @pytest.mark.asyncio
    async def test_on_thread_delete_stateful(
        self, event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: mock.Mock
    ):
        mock_payload = mock.Mock()
        await event_manager_impl.on_thread_delete(shard, mock_payload)

        event = event_factory.deserialize_guild_thread_delete_event.return_value
        event_manager_impl._cache.delete_thread.assert_called_once_with(event.thread_id)
        event_manager_impl.dispatch.assert_awaited_once_with(event)
        event_factory.deserialize_guild_thread_delete_event.assert_called_once_with(shard, mock_payload)

    @pytest.mark.asyncio
    async def test_on_thread_delete_stateless(
        self, stateless_event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: mock.Mock
    ):
        mock_payload = mock.Mock()
        await stateless_event_manager_impl.on_thread_delete(shard, mock_payload)

        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_thread_delete_event.return_value
        )
        event_factory.deserialize_guild_thread_delete_event.assert_called_once_with(shard, mock_payload)

    @pytest.mark.asyncio
    async def test_on_thread_list_sync_stateful_when_channel_ids(
        self, event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: mock.Mock
    ):
        event = event_factory.deserialize_thread_list_sync_event.return_value
        event.channel_ids = ["1", "2"]
        event.threads = {1: "thread1"}

        mock_payload = mock.Mock()
        await event_manager_impl.on_thread_list_sync(shard, mock_payload)

        assert event_manager_impl._cache.clear_threads_for_channel.call_count == 2
        event_manager_impl._cache.clear_threads_for_channel.assert_has_calls(
            [mock.call(event.guild_id, "1"), mock.call(event.guild_id, "2")]
        )
        event_manager_impl._cache.set_thread("thread1")
        event_manager_impl.dispatch.assert_awaited_once_with(event)
        event_factory.deserialize_thread_list_sync_event.assert_called_once_with(shard, mock_payload)

    @pytest.mark.asyncio
    async def test_on_thread_list_sync_stateful_when_not_channel_ids(
        self, event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: mock.Mock
    ):
        event = event_factory.deserialize_thread_list_sync_event.return_value
        event.channel_ids = None
        event.threads = {1: "thread1"}

        mock_payload = mock.Mock()
        await event_manager_impl.on_thread_list_sync(shard, mock_payload)

        event_manager_impl._cache.clear_threads_for_guild.assert_called_once_with(event.guild_id)
        event_manager_impl._cache.set_thread("thread1")
        event_manager_impl.dispatch.assert_awaited_once_with(event)
        event_factory.deserialize_thread_list_sync_event.assert_called_once_with(shard, mock_payload)

    @pytest.mark.asyncio
    async def test_on_thread_list_sync_stateless(
        self, stateless_event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: mock.Mock
    ):
        mock_payload = mock.Mock()
        await stateless_event_manager_impl.on_thread_list_sync(shard, mock_payload)

        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_thread_list_sync_event.return_value
        )
        event_factory.deserialize_thread_list_sync_event.assert_called_once_with(shard, mock_payload)

    @pytest.mark.asyncio
    async def test_on_thread_members_update_stateful_when_id_in_removed(
        self, event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: mock.Mock
    ):
        event = event_factory.deserialize_thread_members_update_event.return_value
        event.removed_member_ids = [1, 2, 3]
        event.shard.get_user_id.return_value = 1
        mock_payload = mock.Mock()
        await event_manager_impl.on_thread_members_update(shard, mock_payload)

        event_manager_impl._cache.delete_thread.assert_called_once_with(event.thread_id)
        event_manager_impl.dispatch.assert_awaited_once_with(event)
        event_factory.deserialize_thread_members_update_event.assert_called_once_with(shard, mock_payload)

    @pytest.mark.asyncio
    async def test_on_thread_members_update_stateful_when_id_not_in_removed(
        self, event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: mock.Mock
    ):
        event = event_factory.deserialize_thread_members_update_event.return_value
        event.removed_member_ids = [1, 2, 3]
        event.shard.get_user_id.return_value = 69
        mock_payload = mock.Mock()
        await event_manager_impl.on_thread_members_update(shard, mock_payload)

        event_manager_impl._cache.delete_thread.assert_not_called()
        event_manager_impl.dispatch.assert_awaited_once_with(event)
        event_factory.deserialize_thread_members_update_event.assert_called_once_with(shard, mock_payload)

    @pytest.mark.asyncio
    async def test_on_thread_members_update_stateless(
        self, stateless_event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: mock.Mock
    ):
        mock_payload = mock.Mock()
        await stateless_event_manager_impl.on_thread_members_update(shard, mock_payload)

        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_thread_members_update_event.return_value
        )
        event_factory.deserialize_thread_members_update_event.assert_called_once_with(shard, mock_payload)

    @pytest.mark.asyncio
    async def test_on_guild_create_when_unavailable_guild(
        self, event_manager_impl, shard, event_factory, entity_factory
    ):
        payload = {"unavailable": True}
        event_manager_impl._cache_enabled_for = mock.Mock(return_value=True)
        event_manager_impl._enabled_for_event = mock.Mock(return_value=True)

        with mock.patch.object(event_manager, "_request_guild_members") as request_guild_members:
            await event_manager_impl.on_guild_create(shard, payload)

        event_manager_impl._enabled_for_event.assert_not_called()
        event_factory.deserialize_guild_available_event.assert_not_called()
        event_factory.deserialize_guild_join_event.assert_not_called()

        event_manager_impl._cache.update_guild.assert_not_called()
        event_manager_impl._cache.clear_guild_channels_for_guild.assert_not_called()
        event_manager_impl._cache.set_guild_channel.assert_not_called()
        event_manager_impl._cache.clear_emojis_for_guild.assert_not_called()
        event_manager_impl._cache.set_emoji.assert_not_called()
        event_manager_impl._cache.clear_stickers_for_guild.assert_not_called()
        event_manager_impl._cache.set_sticker.assert_not_called()
        event_manager_impl._cache.clear_roles_for_guild.assert_not_called()
        event_manager_impl._cache.set_role.assert_not_called()
        event_manager_impl._cache.clear_members_for_guild.assert_not_called()
        event_manager_impl._cache.set_member.assert_not_called()
        event_manager_impl._cache.clear_presences_for_guild.assert_not_called()
        event_manager_impl._cache.set_presence.assert_not_called()
        event_manager_impl._cache.clear_voice_states_for_guild.assert_not_called()
        event_manager_impl._cache.set_voice_state.assert_not_called()
        request_guild_members.assert_not_called()

        event_manager_impl.dispatch.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("include_unavailable", [True, False])
    async def test_on_guild_create_when_dispatching_and_not_caching(
        self, event_manager_impl, shard, event_factory, entity_factory, include_unavailable
    ):
        payload = {"unavailable": False} if include_unavailable else {}
        event_manager_impl._intents = intents.Intents.NONE
        event_manager_impl._cache_enabled_for = mock.Mock(return_value=False)
        event_manager_impl._enabled_for_event = mock.Mock(return_value=True)

        with mock.patch.object(event_manager, "_request_guild_members") as request_guild_members:
            await event_manager_impl.on_guild_create(shard, payload)

        if include_unavailable:
            event_manager_impl._enabled_for_event.assert_called_once_with(guild_events.GuildAvailableEvent)
            event_factory.deserialize_guild_available_event.assert_called_once_with(shard, payload)
            event = event_factory.deserialize_guild_available_event.return_value
        else:
            event_manager_impl._enabled_for_event.assert_called_once_with(guild_events.GuildJoinEvent)
            event_factory.deserialize_guild_join_event.assert_called_once_with(shard, payload)
            event = event_factory.deserialize_guild_join_event.return_value

        event_manager_impl._cache.update_guild.assert_not_called()
        event_manager_impl._cache.clear_guild_channels_for_guild.assert_not_called()
        event_manager_impl._cache.set_guild_channel.assert_not_called()
        event_manager_impl._cache.clear_threads_for_guild.assert_not_called()
        event_manager_impl._cache.set_thread.assert_not_called()
        event_manager_impl._cache.clear_emojis_for_guild.assert_not_called()
        event_manager_impl._cache.set_emoji.assert_not_called()
        event_manager_impl._cache.clear_stickers_for_guild.assert_not_called()
        event_manager_impl._cache.set_sticker.assert_not_called()
        event_manager_impl._cache.clear_roles_for_guild.assert_not_called()
        event_manager_impl._cache.set_role.assert_not_called()
        event_manager_impl._cache.clear_members_for_guild.assert_not_called()
        event_manager_impl._cache.set_member.assert_not_called()
        event_manager_impl._cache.clear_presences_for_guild.assert_not_called()
        event_manager_impl._cache.set_presence.assert_not_called()
        event_manager_impl._cache.clear_voice_states_for_guild.assert_not_called()
        event_manager_impl._cache.set_voice_state.assert_not_called()
        request_guild_members.assert_not_called()

        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.parametrize("include_unavailable", [True, False])
    @pytest.mark.asyncio
    async def test_on_guild_create_when_not_dispatching_and_not_caching(
        self, event_manager_impl, shard, event_factory, entity_factory, include_unavailable
    ):
        payload = {"unavailable": False} if include_unavailable else {}
        event_manager_impl._intents = intents.Intents.NONE
        event_manager_impl._cache_enabled_for = mock.Mock(return_value=False)
        event_manager_impl._enabled_for_event = mock.Mock(return_value=False)

        with mock.patch.object(event_manager, "_request_guild_members") as request_guild_members:
            await event_manager_impl.on_guild_create(shard, payload)

        if include_unavailable:
            event_manager_impl._enabled_for_event.assert_called_once_with(guild_events.GuildAvailableEvent)
        else:
            event_manager_impl._enabled_for_event.assert_called_once_with(guild_events.GuildJoinEvent)

        event_factory.deserialize_guild_join_event.assert_not_called()
        event_factory.deserialize_guild_available_event.assert_not_called()
        entity_factory.deserialize_gateway_guild.assert_called_once_with(
            payload, user_id=shard.get_user_id.return_value
        )
        event_manager_impl._cache.update_guild.assert_not_called()
        event_manager_impl._cache.clear_guild_channels_for_guild.assert_not_called()
        event_manager_impl._cache.set_guild_channel.assert_not_called()
        event_manager_impl._cache.clear_threads_for_guild.assert_not_called()
        event_manager_impl._cache.set_thread.assert_not_called()
        event_manager_impl._cache.clear_emojis_for_guild.assert_not_called()
        event_manager_impl._cache.set_emoji.assert_not_called()
        event_manager_impl._cache.clear_stickers_for_guild.assert_not_called()
        event_manager_impl._cache.set_sticker.assert_not_called()
        event_manager_impl._cache.clear_roles_for_guild.assert_not_called()
        event_manager_impl._cache.set_role.assert_not_called()
        event_manager_impl._cache.clear_members_for_guild.assert_not_called()
        event_manager_impl._cache.set_member.assert_not_called()
        event_manager_impl._cache.clear_presences_for_guild.assert_not_called()
        event_manager_impl._cache.set_presence.assert_not_called()
        event_manager_impl._cache.clear_voice_states_for_guild.assert_not_called()
        event_manager_impl._cache.set_voice_state.assert_not_called()
        shard.get_user_id.assert_called_once_with()
        request_guild_members.assert_not_called()

        event_manager_impl.dispatch.assert_not_called()

    @pytest.mark.parametrize(
        ("include_unavailable", "only_my_member"), [(True, True), (True, False), (False, True), (False, False)]
    )
    @pytest.mark.asyncio
    async def test_on_guild_create_when_not_dispatching_and_caching(
        self, event_manager_impl, shard, event_factory, entity_factory, include_unavailable, only_my_member
    ):
        payload = {"unavailable": False} if include_unavailable else {}
        event_manager_impl._intents = intents.Intents.NONE
        event_manager_impl._cache_enabled_for = mock.Mock(return_value=True)
        event_manager_impl._enabled_for_event = mock.Mock(return_value=False)
        event_manager_impl._cache.settings.only_my_member = only_my_member
        shard.get_user_id.return_value = 1
        gateway_guild = entity_factory.deserialize_gateway_guild.return_value
        gateway_guild.channels.return_value = {1: "channel1", 2: "channel2"}
        gateway_guild.emojis.return_value = {1: "emoji1", 2: "emoji2"}
        gateway_guild.roles.return_value = {1: "role1", 2: "role2"}
        gateway_guild.voice_states.return_value = {1: "voice1", 2: "voice2"}
        gateway_guild.presences.return_value = {1: "presence1", 2: "presence2"}
        gateway_guild.members.return_value = {1: "member1", 2: "member2"}
        gateway_guild.stickers.return_value = {1: "sticker1", 2: "sticker2"}
        gateway_guild.threads.return_value = {1: "thread1", 2: "thread2"}

        with mock.patch.object(event_manager, "_request_guild_members") as request_guild_members:
            await event_manager_impl.on_guild_create(shard, payload)

        if include_unavailable:
            event_manager_impl._enabled_for_event.assert_called_once_with(guild_events.GuildAvailableEvent)
        else:
            event_manager_impl._enabled_for_event.assert_called_once_with(guild_events.GuildJoinEvent)

        event_factory.deserialize_guild_join_event.assert_not_called()
        event_factory.deserialize_guild_available_event.assert_not_called()
        entity_factory.deserialize_gateway_guild.assert_called_once_with(
            payload, user_id=shard.get_user_id.return_value
        )
        event_manager_impl._cache.update_guild.assert_called_once_with(gateway_guild.guild.return_value)
        event_manager_impl._cache.clear_guild_channels_for_guild.assert_called_once_with(gateway_guild.id)
        event_manager_impl._cache.set_guild_channel.assert_has_calls([mock.call("channel1"), mock.call("channel2")])
        event_manager_impl._cache.clear_threads_for_guild.assert_called_once_with(gateway_guild.id)
        event_manager_impl._cache.set_thread.assert_has_calls([mock.call("thread1"), mock.call("thread2")])
        event_manager_impl._cache.clear_emojis_for_guild.assert_called_once_with(gateway_guild.id)
        event_manager_impl._cache.set_emoji.assert_has_calls([mock.call("emoji1"), mock.call("emoji2")])
        event_manager_impl._cache.clear_stickers_for_guild.assert_called_once_with(gateway_guild.id)
        event_manager_impl._cache.set_sticker.assert_has_calls([mock.call("sticker1"), mock.call("sticker2")])
        event_manager_impl._cache.clear_roles_for_guild.assert_called_once_with(gateway_guild.id)
        event_manager_impl._cache.set_role.assert_has_calls([mock.call("role1"), mock.call("role2")])
        event_manager_impl._cache.clear_members_for_guild.assert_called_once_with(gateway_guild.id)
        if only_my_member:
            event_manager_impl._cache.set_member.assert_called_once_with("member1")
            shard.get_user_id.assert_has_calls([mock.call(), mock.call()])
        else:
            event_manager_impl._cache.set_member.assert_has_calls([mock.call("member1"), mock.call("member2")])
            shard.get_user_id.assert_called_once_with()
        event_manager_impl._cache.clear_presences_for_guild.assert_called_once_with(gateway_guild.id)
        event_manager_impl._cache.set_presence.assert_has_calls([mock.call("presence1"), mock.call("presence2")])
        event_manager_impl._cache.clear_voice_states_for_guild.assert_called_once_with(gateway_guild.id)
        event_manager_impl._cache.set_voice_state.assert_has_calls([mock.call("voice1"), mock.call("voice2")])
        request_guild_members.assert_not_called()

        event_manager_impl.dispatch.assert_not_called()

    @pytest.mark.parametrize("include_unavailable", [True, False])
    @pytest.mark.asyncio
    async def test_on_guild_create_when_stateless(
        self, stateless_event_manager_impl, shard, event_factory, entity_factory, include_unavailable
    ):
        payload = {"id": 123}
        if include_unavailable:
            payload["unavailable"] = False

        stateless_event_manager_impl._intents = intents.Intents.NONE
        stateless_event_manager_impl._cache_enabled_for = mock.Mock(return_value=True)
        stateless_event_manager_impl._enabled_for_event = mock.Mock(return_value=False)

        with mock.patch.object(event_manager, "_request_guild_members") as request_guild_members:
            await stateless_event_manager_impl.on_guild_create(shard, payload)

        if include_unavailable:
            stateless_event_manager_impl._enabled_for_event.assert_called_once_with(guild_events.GuildAvailableEvent)
        else:
            stateless_event_manager_impl._enabled_for_event.assert_called_once_with(guild_events.GuildJoinEvent)

        event_factory.deserialize_guild_join_event.assert_not_called()
        event_factory.deserialize_guild_available_event.assert_not_called()
        request_guild_members.assert_not_called()

        stateless_event_manager_impl.dispatch.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_guild_create_when_members_declared_and_member_cache_enabled_but_only_my_member_not_enabled(
        self, event_manager_impl, shard, event_factory, entity_factory
    ):
        def cache_enabled_for_members_only(component):
            return component == config.CacheComponents.MEMBERS

        shard.id = 123
        event_manager_impl._cache.settings.only_my_member = False
        event_manager_impl._intents = intents.Intents.GUILD_MEMBERS
        event_manager_impl._cache_enabled_for = cache_enabled_for_members_only
        event_manager_impl._enabled_for_event = mock.Mock(return_value=False)
        gateway_guild = entity_factory.deserialize_gateway_guild.return_value
        gateway_guild.id = 456
        gateway_guild.members.return_value = {1: "member1", 2: "member2"}
        mock_request_guild_members = mock.Mock()

        with mock.patch.object(asyncio, "create_task") as create_task:
            with mock.patch.object(event_manager, "_fixed_size_nonce", return_value="abc"):
                with mock.patch.object(event_manager, "_request_guild_members", new=mock_request_guild_members):
                    await event_manager_impl.on_guild_create(shard, {"id": 456, "large": False})

        mock_request_guild_members.assert_called_once_with(shard, 456, include_presences=False, nonce="123.abc")
        create_task.assert_called_once_with(
            mock_request_guild_members.return_value, name="123:456 guild create members request"
        )

    @pytest.mark.asyncio
    async def test_on_guild_create_when_members_declared_and_member_cache_but_only_my_member_enabled(
        self, event_manager_impl, shard, event_factory, entity_factory
    ):
        def cache_enabled_for_members_only(component):
            return component == config.CacheComponents.MEMBERS

        shard.id = 123
        shard.get_user_id.return_value = 1
        event_manager_impl._cache.settings.only_my_member = True
        event_manager_impl._intents = intents.Intents.GUILD_MEMBERS
        event_manager_impl._cache_enabled_for = cache_enabled_for_members_only
        event_manager_impl._enabled_for_event = mock.Mock(return_value=False)
        gateway_guild = entity_factory.deserialize_gateway_guild.return_value
        gateway_guild.members.return_value = {1: "member1", 2: "member2"}

        mock_request_guild_members = mock.Mock()

        with mock.patch.object(asyncio, "create_task") as create_task:
            with mock.patch.object(event_manager, "_fixed_size_nonce", return_value="abc"):
                with mock.patch.object(event_manager, "_request_guild_members", new=mock_request_guild_members):
                    await event_manager_impl.on_guild_create(shard, {"id": 456, "large": False})

        mock_request_guild_members.assert_not_called()
        create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_guild_create_when_members_declared_and_enabled_for_member_chunk_event(
        self, stateless_event_manager_impl, shard, event_factory, entity_factory
    ):
        shard.id = 123
        stateless_event_manager_impl._intents = intents.Intents.GUILD_MEMBERS
        stateless_event_manager_impl._cache_enabled_for = mock.Mock(return_value=False)
        stateless_event_manager_impl._enabled_for_event = mock.Mock(return_value=True)
        mock_event = mock.Mock()
        mock_event.guild.id = 456
        event_factory.deserialize_guild_join_event.return_value = mock_event

        mock_request_guild_members = mock.Mock()

        with mock.patch.object(asyncio, "create_task") as create_task:
            with mock.patch.object(event_manager, "_fixed_size_nonce", return_value="abc"):
                with mock.patch.object(event_manager, "_request_guild_members", new=mock_request_guild_members):
                    await stateless_event_manager_impl.on_guild_create(shard, {"large": True})

        mock_request_guild_members.assert_called_once_with(shard, 456, include_presences=False, nonce="123.abc")
        create_task.assert_called_once_with(
            mock_request_guild_members.return_value, name="123:456 guild create members request"
        )
        assert mock_event.chunk_nonce == "123.abc"
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(mock_event)

    @pytest.mark.parametrize("cache_enabled", [True, False])
    @pytest.mark.parametrize("large", [True, False])
    @pytest.mark.parametrize("enabled_for_event", [True, False])
    @pytest.mark.asyncio
    async def test_on_guild_create_when_chunk_members_disabled(
        self, stateless_event_manager_impl, shard, large, cache_enabled, enabled_for_event
    ):
        shard.id = 123
        stateless_event_manager_impl._intents = intents.Intents.GUILD_MEMBERS
        stateless_event_manager_impl._cache_enabled_for = mock.Mock(return_value=cache_enabled)
        stateless_event_manager_impl._enabled_for_event = mock.Mock(return_value=enabled_for_event)
        stateless_event_manager_impl._auto_chunk_members = False

        with mock.patch.object(event_manager, "_request_guild_members") as request_guild_members:
            await stateless_event_manager_impl.on_guild_create(shard, {"id": 456, "large": large})

        request_guild_members.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_guild_update_when_stateless(
        self, stateless_event_manager_impl, shard, event_factory, entity_factory
    ):
        stateless_event_manager_impl._intents = intents.Intents.NONE
        stateless_event_manager_impl._cache_enabled_for = mock.Mock(return_value=True)
        stateless_event_manager_impl._enabled_for_event = mock.Mock(return_value=False)

        await stateless_event_manager_impl.on_guild_update(shard, {})

        stateless_event_manager_impl._enabled_for_event.assert_called_once_with(guild_events.GuildUpdateEvent)
        event_factory.deserialize_guild_update_event.assert_not_called()

        stateless_event_manager_impl.dispatch.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_guild_update_stateful_and_dispatching(
        self, event_manager_impl, shard, event_factory, entity_factory
    ):
        payload = {"id": 123}
        old_guild = object()
        mock_role = object()
        mock_emoji = object()
        mock_sticker = object()
        event_manager_impl._enabled_for_event = mock.Mock(return_value=True)
        event = mock.Mock(
            roles={555: mock_role}, emojis={333: mock_emoji}, guild=mock.Mock(id=123), stickers={444: mock_sticker}
        )

        event_factory.deserialize_guild_update_event.return_value = event
        event_manager_impl._cache.get_guild.return_value = old_guild

        await event_manager_impl.on_guild_update(shard, payload)

        event_manager_impl._enabled_for_event.assert_called_once_with(guild_events.GuildUpdateEvent)
        event_manager_impl._cache.get_guild.assert_called_once_with(123)
        event_manager_impl._cache.update_guild.assert_called_once_with(event.guild)
        event_manager_impl._cache.clear_roles_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.set_role.assert_called_once_with(mock_role)
        event_manager_impl._cache.clear_emojis_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.set_emoji.assert_called_once_with(mock_emoji)
        event_manager_impl._cache.clear_stickers_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.set_sticker.assert_called_once_with(mock_sticker)
        entity_factory.deserialize_gateway_guild.assert_not_called()
        event_factory.deserialize_guild_update_event.assert_called_once_with(shard, payload, old_guild=old_guild)
        event_manager_impl.dispatch.assert_awaited_once_with(event)
        shard.get_user_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_guild_update_all_cache_components_and_not_dispatching(
        self, event_manager_impl, shard, event_factory, entity_factory
    ):
        payload = {"id": 123}
        mock_role = object()
        mock_emoji = object()
        mock_sticker = object()
        event_manager_impl._enabled_for_event = mock.Mock(return_value=False)
        guild_definition = entity_factory.deserialize_gateway_guild.return_value
        guild_definition.id = 123
        guild_definition.emojis.return_value = {0: mock_emoji}
        guild_definition.roles.return_value = {1: mock_role}
        guild_definition.stickers.return_value = {4: mock_sticker}

        await event_manager_impl.on_guild_update(shard, payload)

        entity_factory.deserialize_gateway_guild.assert_called_once_with(
            {"id": 123}, user_id=shard.get_user_id.return_value
        )
        event_manager_impl._enabled_for_event.assert_called_once_with(guild_events.GuildUpdateEvent)
        event_manager_impl._cache.update_guild.assert_called_once_with(guild_definition.guild.return_value)
        event_manager_impl._cache.clear_emojis_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.set_emoji.assert_called_once_with(mock_emoji)
        event_manager_impl._cache.clear_stickers_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.set_sticker.assert_called_once_with(mock_sticker)
        event_manager_impl._cache.clear_roles_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.set_role.assert_called_once_with(mock_role)
        shard.get_user_id.assert_called_once_with()
        event_factory.deserialize_guild_update_event.assert_not_called()
        event_manager_impl.dispatch.assert_not_called()
        guild_definition.emojis.assert_called_once_with()
        guild_definition.roles.assert_called_once_with()
        guild_definition.guild.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_on_guild_update_no_cache_components_and_not_dispatching(
        self, event_manager_impl, shard, event_factory, entity_factory
    ):
        payload = {"id": 123}
        event_manager_impl._cache_enabled_for = mock.Mock(return_value=False)
        event_manager_impl._enabled_for_event = mock.Mock(return_value=False)
        guild_definition = entity_factory.deserialize_gateway_guild.return_value

        await event_manager_impl.on_guild_update(shard, payload)

        entity_factory.deserialize_gateway_guild.assert_called_once_with(
            {"id": 123}, user_id=shard.get_user_id.return_value
        )
        event_manager_impl._enabled_for_event.assert_called_once_with(guild_events.GuildUpdateEvent)
        event_manager_impl._cache.update_guild.assert_not_called()
        event_manager_impl._cache.clear_emojis_for_guild.assert_not_called()
        event_manager_impl._cache.set_emoji.assert_not_called()
        event_manager_impl._cache.clear_stickers_for_guild.assert_not_called()
        event_manager_impl._cache.set_sticker.assert_not_called()
        event_manager_impl._cache.clear_roles_for_guild.assert_not_called()
        event_manager_impl._cache.set_role.assert_not_called()
        event_factory.deserialize_guild_update_event.assert_not_called()
        event_manager_impl.dispatch.assert_not_called()
        guild_definition.emojis.assert_not_called()
        guild_definition.roles.assert_not_called()
        guild_definition.guild.assert_not_called()
        shard.get_user_id.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_on_guild_update_stateless_and_dispatching(
        self, stateless_event_manager_impl, shard, event_factory, entity_factory
    ):
        payload = {"id": 123}
        stateless_event_manager_impl._enabled_for_event = mock.Mock(return_value=True)

        await stateless_event_manager_impl.on_guild_update(shard, payload)

        stateless_event_manager_impl._enabled_for_event.assert_called_once_with(guild_events.GuildUpdateEvent)
        shard.get_user_id.deserialize_gateway_guild.assert_not_called()
        shard.user_id.assert_not_called()
        event_factory.deserialize_guild_update_event.assert_called_once_with(shard, payload, old_guild=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_delete_stateful_when_available(self, event_manager_impl, shard, event_factory):
        payload = {"unavailable": False, "id": "123"}
        event = mock.Mock(guild_id=123)

        event_factory.deserialize_guild_leave_event.return_value = event

        await event_manager_impl.on_guild_delete(shard, payload)

        event_manager_impl._cache.delete_guild.assert_called_once_with(123)
        event_manager_impl._cache.clear_voice_states_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.clear_invites_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.clear_members_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.clear_presences_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.clear_guild_channels_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.clear_threads_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.clear_emojis_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.clear_stickers_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.clear_roles_for_guild.assert_called_once_with(123)
        event_factory.deserialize_guild_leave_event.assert_called_once_with(
            shard, payload, old_guild=event_manager_impl._cache.delete_guild.return_value
        )
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_delete_stateful_when_unavailable(self, event_manager_impl, shard, event_factory):
        payload = {"unavailable": True, "id": "123"}
        event = mock.Mock(guild_id=123)

        event_factory.deserialize_guild_unavailable_event.return_value = event

        await event_manager_impl.on_guild_delete(shard, payload)

        event_manager_impl._cache.set_guild_availability.assert_called_once_with(event.guild_id, False)
        event_factory.deserialize_guild_unavailable_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_delete_stateless_when_available(self, stateless_event_manager_impl, shard, event_factory):
        payload = {"unavailable": False, "id": "123"}

        await stateless_event_manager_impl.on_guild_delete(shard, payload)

        event_factory.deserialize_guild_leave_event.assert_called_once_with(shard, payload, old_guild=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_leave_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_delete_stateless_when_unavailable(self, stateless_event_manager_impl, shard, event_factory):
        payload = {"unavailable": True}

        await stateless_event_manager_impl.on_guild_delete(shard, payload)

        event_factory.deserialize_guild_unavailable_event.assert_called_once_with(shard, payload)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_unavailable_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_ban_add(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock()

        event_factory.deserialize_guild_ban_add_event.return_value = event

        await event_manager_impl.on_guild_ban_add(shard, payload)

        event_factory.deserialize_guild_ban_add_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_ban_remove(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock()

        event_factory.deserialize_guild_ban_remove_event.return_value = event

        await event_manager_impl.on_guild_ban_remove(shard, payload)

        event_factory.deserialize_guild_ban_remove_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_emojis_update_stateful(self, event_manager_impl, shard, event_factory):
        payload = {"guild_id": 123}
        old_emojis = {"Test": 123}
        mock_emoji = object()
        event = mock.Mock(emojis=[mock_emoji], guild_id=123)

        event_factory.deserialize_guild_emojis_update_event.return_value = event
        event_manager_impl._cache.clear_emojis_for_guild.return_value = old_emojis

        await event_manager_impl.on_guild_emojis_update(shard, payload)

        event_manager_impl._cache.clear_emojis_for_guild.assert_called_once_with(123)
        event_manager_impl._cache.set_emoji.assert_called_once_with(mock_emoji)
        event_factory.deserialize_guild_emojis_update_event.assert_called_once_with(shard, payload, old_emojis=[123])
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_emojis_update_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {"guild_id": 123}

        await stateless_event_manager_impl.on_guild_emojis_update(shard, payload)

        event_factory.deserialize_guild_emojis_update_event.assert_called_once_with(shard, payload, old_emojis=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_emojis_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_stickers_update_stateful(self, event_manager_impl, shard, event_factory):
        payload = {"guild_id": 720}
        old_stickers = {700: 123}
        mock_sticker = object()
        event = mock.Mock(stickers=[mock_sticker], guild_id=123)

        event_factory.deserialize_guild_stickers_update_event.return_value = event
        event_manager_impl._cache.clear_stickers_for_guild.return_value = old_stickers

        await event_manager_impl.on_guild_stickers_update(shard, payload)

        event_manager_impl._cache.clear_stickers_for_guild.assert_called_once_with(720)
        event_manager_impl._cache.set_sticker.assert_called_once_with(mock_sticker)
        event_factory.deserialize_guild_stickers_update_event.assert_called_once_with(
            shard, payload, old_stickers=[123]
        )
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_stickers_update_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {"guild_id": 123}

        await stateless_event_manager_impl.on_guild_stickers_update(shard, payload)

        event_factory.deserialize_guild_stickers_update_event.assert_called_once_with(shard, payload, old_stickers=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_stickers_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_integrations_update(self, event_manager_impl, shard):
        with pytest.raises(NotImplementedError):
            await event_manager_impl.on_guild_integrations_update(shard, {})

        event_manager_impl.dispatch.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_integration_create(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock()

        event_factory.deserialize_integration_create_event.return_value = event

        await event_manager_impl.on_integration_create(shard, payload)

        event_factory.deserialize_integration_create_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_integration_delete(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock()

        event_factory.deserialize_integration_delete_event.return_value = event

        await event_manager_impl.on_integration_delete(shard, payload)

        event_factory.deserialize_integration_delete_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_integration_update(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock()

        event_factory.deserialize_integration_update_event.return_value = event

        await event_manager_impl.on_integration_update(shard, payload)

        event_factory.deserialize_integration_update_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_member_add_stateful(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock(user=object(), member=object())

        event_factory.deserialize_guild_member_add_event.return_value = event

        await event_manager_impl.on_guild_member_add(shard, payload)

        event_manager_impl._cache.update_member.assert_called_once_with(event.member)
        event_factory.deserialize_guild_member_add_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_member_add_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_guild_member_add(shard, payload)

        event_factory.deserialize_guild_member_add_event.assert_called_once_with(shard, payload)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_member_add_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_member_remove_stateful(self, event_manager_impl, shard, event_factory):
        payload = {"guild_id": "456", "user": {"id": "123"}}

        await event_manager_impl.on_guild_member_remove(shard, payload)

        event_manager_impl._cache.delete_member.assert_called_once_with(456, 123)
        event_factory.deserialize_guild_member_remove_event.assert_called_once_with(
            shard, payload, old_member=event_manager_impl._cache.delete_member.return_value
        )
        event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_member_remove_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_member_remove_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_guild_member_remove(shard, payload)

        event_factory.deserialize_guild_member_remove_event.assert_called_once_with(shard, payload, old_member=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_member_remove_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_member_update_stateful(self, event_manager_impl, shard, event_factory):
        payload = {"user": {"id": 123}, "guild_id": 456}
        old_member = object()
        event = mock.Mock(member=mock.Mock())

        event_factory.deserialize_guild_member_update_event.return_value = event
        event_manager_impl._cache.get_member.return_value = old_member

        await event_manager_impl.on_guild_member_update(shard, payload)

        event_manager_impl._cache.get_member.assert_called_once_with(456, 123)
        event_manager_impl._cache.update_member.assert_called_once_with(event.member)
        event_factory.deserialize_guild_member_update_event.assert_called_once_with(
            shard, payload, old_member=old_member
        )
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_member_update_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {"user": {"id": 123}, "guild_id": 456}

        await stateless_event_manager_impl.on_guild_member_update(shard, payload)

        event_factory.deserialize_guild_member_update_event.assert_called_once_with(shard, payload, old_member=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_member_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_members_chunk_stateful(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock(members={"TestMember": 123}, presences={"TestPresences": 456})
        event_factory.deserialize_guild_member_chunk_event.return_value = event

        await event_manager_impl.on_guild_members_chunk(shard, payload)

        event_manager_impl._cache.set_member.assert_called_once_with(123)
        event_manager_impl._cache.set_presence.assert_called_once_with(456)
        event_factory.deserialize_guild_member_chunk_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_members_chunk_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_guild_members_chunk(shard, payload)

        event_factory.deserialize_guild_member_chunk_event.assert_called_once_with(shard, payload)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_member_chunk_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_role_create_stateful(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock(role=object())

        event_factory.deserialize_guild_role_create_event.return_value = event

        await event_manager_impl.on_guild_role_create(shard, payload)

        event_manager_impl._cache.set_role.assert_called_once_with(event.role)
        event_factory.deserialize_guild_role_create_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_role_create_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_guild_role_create(shard, payload)

        event_factory.deserialize_guild_role_create_event.assert_called_once_with(shard, payload)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_role_create_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_role_update_stateful(self, event_manager_impl, shard, event_factory):
        payload = {"role": {"id": 123}}
        old_role = object()
        event = mock.Mock(role=mock.Mock())

        event_factory.deserialize_guild_role_update_event.return_value = event
        event_manager_impl._cache.get_role.return_value = old_role

        await event_manager_impl.on_guild_role_update(shard, payload)

        event_manager_impl._cache.get_role.assert_called_once_with(123)
        event_manager_impl._cache.update_role.assert_called_once_with(event.role)
        event_factory.deserialize_guild_role_update_event.assert_called_once_with(shard, payload, old_role=old_role)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_role_update_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {"role": {"id": 123}}

        await stateless_event_manager_impl.on_guild_role_update(shard, payload)

        event_factory.deserialize_guild_role_update_event.assert_called_once_with(shard, payload, old_role=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_role_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_role_delete_stateful(self, event_manager_impl, shard, event_factory):
        payload = {"role_id": "123"}

        await event_manager_impl.on_guild_role_delete(shard, payload)

        event_manager_impl._cache.delete_role.assert_called_once_with(123)
        event_factory.deserialize_guild_role_delete_event.assert_called_once_with(
            shard, payload, old_role=event_manager_impl._cache.delete_role.return_value
        )
        event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_role_delete_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_role_delete_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_guild_role_delete(shard, payload)

        event_factory.deserialize_guild_role_delete_event.assert_called_once_with(shard, payload, old_role=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_role_delete_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_invite_create_stateful(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock(invite="qwerty")

        event_factory.deserialize_invite_create_event.return_value = event

        await event_manager_impl.on_invite_create(shard, payload)

        event_manager_impl._cache.set_invite.assert_called_once_with("qwerty")
        event_factory.deserialize_invite_create_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_invite_create_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_invite_create(shard, payload)

        event_factory.deserialize_invite_create_event.assert_called_once_with(shard, payload)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_invite_create_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_invite_delete_stateful(self, event_manager_impl, shard, event_factory):
        payload = {"code": "qwerty"}

        await event_manager_impl.on_invite_delete(shard, payload)

        event_manager_impl._cache.delete_invite.assert_called_once_with("qwerty")
        event_factory.deserialize_invite_delete_event.assert_called_once_with(
            shard, payload, old_invite=event_manager_impl._cache.delete_invite.return_value
        )
        event_manager_impl.dispatch.assert_awaited_once_with(event_factory.deserialize_invite_delete_event.return_value)

    @pytest.mark.asyncio
    async def test_on_invite_delete_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_invite_delete(shard, payload)

        event_factory.deserialize_invite_delete_event.assert_called_once_with(shard, payload, old_invite=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_invite_delete_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_message_create_stateful(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock(message=object())

        event_factory.deserialize_message_create_event.return_value = event

        await event_manager_impl.on_message_create(shard, payload)

        event_manager_impl._cache.set_message.assert_called_once_with(event.message)
        event_factory.deserialize_message_create_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_create_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_message_create(shard, payload)

        event_factory.deserialize_message_create_event.assert_called_once_with(shard, payload)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_message_create_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_message_update_stateful(self, event_manager_impl, shard, event_factory):
        payload = {"id": 123}
        old_message = object()
        event = mock.Mock(message=mock.Mock())

        event_factory.deserialize_message_update_event.return_value = event
        event_manager_impl._cache.get_message.return_value = old_message

        await event_manager_impl.on_message_update(shard, payload)

        event_manager_impl._cache.get_message.assert_called_once_with(123)
        event_manager_impl._cache.update_message.assert_called_once_with(event.message)
        event_factory.deserialize_message_update_event.assert_called_once_with(shard, payload, old_message=old_message)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_update_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {"id": 123}

        await stateless_event_manager_impl.on_message_update(shard, payload)

        event_factory.deserialize_message_update_event.assert_called_once_with(shard, payload, old_message=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_message_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_message_delete_stateful(self, event_manager_impl, shard, event_factory):
        payload = {"id": 123}

        await event_manager_impl.on_message_delete(shard, payload)

        event_manager_impl._cache.delete_message.assert_called_once_with(123)
        event_factory.deserialize_message_delete_event.assert_called_once_with(
            shard, payload, old_message=event_manager_impl._cache.delete_message.return_value
        )
        event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_message_delete_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_message_delete_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_message_delete(shard, payload)

        event_factory.deserialize_message_delete_event.assert_called_once_with(shard, payload, old_message=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_message_delete_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_message_delete_bulk_stateful(self, event_manager_impl, shard, event_factory):
        payload = {"ids": [123, 456, 789, 987]}
        message1 = object()
        message2 = object()
        message3 = object()
        event_manager_impl._cache.delete_message.side_effect = [message1, message2, message3, None]

        await event_manager_impl.on_message_delete_bulk(shard, payload)

        event_manager_impl._cache.delete_message.assert_has_calls(
            [mock.call(123), mock.call(456), mock.call(789), mock.call(987)]
        )
        event_factory.deserialize_guild_message_delete_bulk_event.assert_called_once_with(
            shard, payload, old_messages={123: message1, 456: message2, 789: message3}
        )
        event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_message_delete_bulk_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_message_delete_bulk_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_message_delete_bulk(shard, payload)

        event_factory.deserialize_guild_message_delete_bulk_event.assert_called_once_with(
            shard, payload, old_messages={}
        )
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_guild_message_delete_bulk_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_message_reaction_add(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock()

        event_factory.deserialize_message_reaction_add_event.return_value = event

        await event_manager_impl.on_message_reaction_add(shard, payload)

        event_factory.deserialize_message_reaction_add_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_reaction_remove(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock()

        event_factory.deserialize_message_reaction_remove_event.return_value = event

        await event_manager_impl.on_message_reaction_remove(shard, payload)

        event_factory.deserialize_message_reaction_remove_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_reaction_remove_all(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock()

        event_factory.deserialize_message_reaction_remove_all_event.return_value = event

        await event_manager_impl.on_message_reaction_remove_all(shard, payload)

        event_factory.deserialize_message_reaction_remove_all_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_reaction_remove_emoji(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock()

        event_factory.deserialize_message_reaction_remove_emoji_event.return_value = event

        await event_manager_impl.on_message_reaction_remove_emoji(shard, payload)

        event_factory.deserialize_message_reaction_remove_emoji_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_presence_update_stateful_update(self, event_manager_impl, shard, event_factory):
        payload = {"user": {"id": 123}, "guild_id": 456}
        old_presence = object()
        event = mock.Mock(presence=mock.Mock(visible_status=presences.Status.ONLINE))

        event_factory.deserialize_presence_update_event.return_value = event
        event_manager_impl._cache.get_presence.return_value = old_presence

        await event_manager_impl.on_presence_update(shard, payload)

        event_manager_impl._cache.get_presence.assert_called_once_with(456, 123)
        event_manager_impl._cache.update_presence.assert_called_once_with(event.presence)
        event_factory.deserialize_presence_update_event.assert_called_once_with(
            shard, payload, old_presence=old_presence
        )
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_presence_update_stateful_delete(self, event_manager_impl, shard, event_factory):
        payload = {"user": {"id": 123}, "guild_id": 456}
        old_presence = object()
        event = mock.Mock(presence=mock.Mock(visible_status=presences.Status.OFFLINE))

        event_factory.deserialize_presence_update_event.return_value = event
        event_manager_impl._cache.get_presence.return_value = old_presence

        await event_manager_impl.on_presence_update(shard, payload)

        event_manager_impl._cache.get_presence.assert_called_once_with(456, 123)
        event_manager_impl._cache.delete_presence.assert_called_once_with(
            event.presence.guild_id, event.presence.user_id
        )
        event_factory.deserialize_presence_update_event.assert_called_once_with(
            shard, payload, old_presence=old_presence
        )
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_presence_update_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {"user": {"id": 123}, "guild_id": 456}

        await stateless_event_manager_impl.on_presence_update(shard, payload)

        event_factory.deserialize_presence_update_event.assert_called_once_with(shard, payload, old_presence=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_presence_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_typing_start(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock()

        event_factory.deserialize_typing_start_event.return_value = event

        await event_manager_impl.on_typing_start(shard, payload)

        event_factory.deserialize_typing_start_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_user_update_stateful(self, event_manager_impl, shard, event_factory):
        payload = {}
        old_user = object()
        event = mock.Mock(user=mock.Mock())

        event_factory.deserialize_own_user_update_event.return_value = event
        event_manager_impl._cache.get_me.return_value = old_user

        await event_manager_impl.on_user_update(shard, payload)

        event_manager_impl._cache.update_me.assert_called_once_with(event.user)
        event_factory.deserialize_own_user_update_event.assert_called_once_with(shard, payload, old_user=old_user)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_user_update_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {}

        await stateless_event_manager_impl.on_user_update(shard, payload)

        event_factory.deserialize_own_user_update_event.assert_called_once_with(shard, payload, old_user=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_own_user_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_voice_state_update_stateful_update(self, event_manager_impl, shard, event_factory):
        payload = {"user_id": 123, "guild_id": 456}
        old_state = object()
        event = mock.Mock(state=mock.Mock(channel_id=123))

        event_factory.deserialize_voice_state_update_event.return_value = event
        event_manager_impl._cache.get_voice_state.return_value = old_state

        await event_manager_impl.on_voice_state_update(shard, payload)

        event_manager_impl._cache.get_voice_state.assert_called_once_with(456, 123)
        event_manager_impl._cache.update_voice_state.assert_called_once_with(event.state)
        event_factory.deserialize_voice_state_update_event.assert_called_once_with(shard, payload, old_state=old_state)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_voice_state_update_stateful_delete(self, event_manager_impl, shard, event_factory):
        payload = {"user_id": 123, "guild_id": 456}
        old_state = object()
        event = mock.Mock(state=mock.Mock(channel_id=None))

        event_factory.deserialize_voice_state_update_event.return_value = event
        event_manager_impl._cache.get_voice_state.return_value = old_state

        await event_manager_impl.on_voice_state_update(shard, payload)

        event_manager_impl._cache.get_voice_state.assert_called_once_with(456, 123)
        event_manager_impl._cache.delete_voice_state.assert_called_once_with(event.state.guild_id, event.state.user_id)
        event_factory.deserialize_voice_state_update_event.assert_called_once_with(shard, payload, old_state=old_state)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_voice_state_update_stateless(self, stateless_event_manager_impl, shard, event_factory):
        payload = {"user_id": 123, "guild_id": 456}

        await stateless_event_manager_impl.on_voice_state_update(shard, payload)

        event_factory.deserialize_voice_state_update_event.assert_called_once_with(shard, payload, old_state=None)
        stateless_event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_voice_state_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_voice_server_update(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock()

        event_factory.deserialize_voice_server_update_event.return_value = event

        await event_manager_impl.on_voice_server_update(shard, payload)

        event_factory.deserialize_voice_server_update_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_webhooks_update(self, event_manager_impl, shard, event_factory):
        payload = {}
        event = mock.Mock()

        event_factory.deserialize_webhook_update_event.return_value = event

        await event_manager_impl.on_webhooks_update(shard, payload)

        event_factory.deserialize_webhook_update_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_interaction_create(self, event_manager_impl, shard, event_factory):
        payload = {"id": "123"}

        await event_manager_impl.on_interaction_create(shard, payload)

        event_factory.deserialize_interaction_create_event.assert_called_once_with(shard, payload)
        event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_interaction_create_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_scheduled_event_create(
        self,
        event_manager_impl: event_manager.EventManagerImpl,
        shard: mock.Mock,
        event_factory: event_factory_.EventFactory,
    ):
        mock_payload = mock.Mock()

        await event_manager_impl.on_guild_scheduled_event_create(shard, mock_payload)

        event_factory.deserialize_scheduled_event_create_event.assert_called_once_with(shard, mock_payload)
        event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_scheduled_event_create_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_scheduled_event_delete(
        self,
        event_manager_impl: event_manager.EventManagerImpl,
        shard: mock.Mock,
        event_factory: event_factory_.EventFactory,
    ):
        mock_payload = mock.Mock()

        await event_manager_impl.on_guild_scheduled_event_delete(shard, mock_payload)

        event_factory.deserialize_scheduled_event_delete_event.assert_called_once_with(shard, mock_payload)
        event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_scheduled_event_delete_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_scheduled_event_update(
        self,
        event_manager_impl: event_manager.EventManagerImpl,
        shard: mock.Mock,
        event_factory: event_factory_.EventFactory,
    ):
        mock_payload = mock.Mock()

        await event_manager_impl.on_guild_scheduled_event_update(shard, mock_payload)

        event_factory.deserialize_scheduled_event_update_event.assert_called_once_with(shard, mock_payload)
        event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_scheduled_event_update_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_scheduled_event_user_add(
        self,
        event_manager_impl: event_manager.EventManagerImpl,
        shard: mock.Mock,
        event_factory: event_factory_.EventFactory,
    ):
        mock_payload = mock.Mock()

        await event_manager_impl.on_guild_scheduled_event_user_add(shard, mock_payload)

        event_factory.deserialize_scheduled_event_user_add_event.assert_called_once_with(shard, mock_payload)
        event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_scheduled_event_user_add_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_scheduled_event_user_remove(
        self,
        event_manager_impl: event_manager.EventManagerImpl,
        shard: mock.Mock,
        event_factory: event_factory_.EventFactory,
    ):
        mock_payload = mock.Mock()

        await event_manager_impl.on_guild_scheduled_event_user_remove(shard, mock_payload)

        event_factory.deserialize_scheduled_event_user_remove_event.assert_called_once_with(shard, mock_payload)
        event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_scheduled_event_user_remove_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_guild_audit_log_entry_create(
        self,
        event_manager_impl: event_manager.EventManagerImpl,
        shard: mock.Mock,
        event_factory: event_factory_.EventFactory,
    ):
        mock_payload = mock.Mock()

        await event_manager_impl.on_guild_audit_log_entry_create(shard, mock_payload)

        event_factory.deserialize_audit_log_entry_create_event.assert_called_once_with(shard, mock_payload)
        event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_audit_log_entry_create_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_message_poll_vote_add(
        event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: event_factory_.EventFactory
    ):
        mock_payload = mock.Mock()

        await event_manager_impl.on_message_poll_vote_add(shard, mock_payload)

        event_factory.deserialize_poll_vote_create_event.assert_called_once_with(shard, mock_payload)
        event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_audit_log_entry_create_event.return_value
        )

    @pytest.mark.asyncio
    async def test_on_message_poll_vote_remove(
        event_manager_impl: event_manager.EventManagerImpl, shard: mock.Mock, event_factory: event_factory_.EventFactory
    ):
        mock_payload = mock.Mock()

        await event_manager_impl.on_message_poll_vote_remove(shard, mock_payload)

        event_factory.deserialize_poll_vote_delete_event.assert_called_once_with(shard, mock_payload)
        event_manager_impl.dispatch.assert_awaited_once_with(
            event_factory.deserialize_audit_log_entry_create_event.return_value
        )
