# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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

import mock
import pytest

from hikari.events import shard_events
from hikari.impl import stateless_event_manager
from tests.hikari import hikari_test_helpers


@pytest.mark.asyncio
class TestStatelessEventManager:
    @pytest.fixture()
    def shard(self):
        return object()

    @pytest.fixture()
    def app(self):
        return mock.Mock()

    @pytest.fixture()
    def payload(self):
        return object()

    @pytest.fixture()
    def event_manager(self, app):
        obj = hikari_test_helpers.mock_class_namespace(stateless_event_manager.StatelessEventManagerImpl, slots_=False)(
            app, object()
        )
        obj.dispatch = mock.AsyncMock()
        return obj

    async def test_on_connected(self, event_manager, app, shard, payload):
        expected_dispatch = shard_events.ShardConnectedEvent(app=app, shard=shard)

        await event_manager.on_connected(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(expected_dispatch)

    async def test_on_disconnected(self, event_manager, app, shard, payload):
        expected_dispatch = shard_events.ShardDisconnectedEvent(app=app, shard=shard)

        await event_manager.on_disconnected(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(expected_dispatch)

    async def test_on_ready(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_ready_event = mock.Mock(return_value=event)

        await event_manager.on_ready(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_ready_event.assert_called_once_with(shard, payload)

    async def test_on_resumed(self, event_manager, app, shard, payload):
        expected_dispatch = shard_events.ShardResumedEvent(app=app, shard=shard)

        await event_manager.on_resumed(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(expected_dispatch)

    async def test_on_channel_create(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_channel_create_event = mock.Mock(return_value=event)

        await event_manager.on_channel_create(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_channel_create_event.assert_called_once_with(shard, payload)

    async def test_on_channel_update(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_channel_update_event = mock.Mock(return_value=event)

        await event_manager.on_channel_update(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_channel_update_event.assert_called_once_with(shard, payload)

    async def test_on_channel_delete(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_channel_delete_event = mock.Mock(return_value=event)

        await event_manager.on_channel_delete(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_channel_delete_event.assert_called_once_with(shard, payload)

    async def test_on_channel_pins_update(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_channel_pins_update_event = mock.Mock(return_value=event)

        await event_manager.on_channel_pins_update(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_channel_pins_update_event.assert_called_once_with(shard, payload)

    async def test_on_guild_create(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_guild_create_event = mock.Mock(return_value=event)

        await event_manager.on_guild_create(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_create_event.assert_called_once_with(shard, payload)

    async def test_on_guild_update(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_guild_update_event = mock.Mock(return_value=event)

        await event_manager.on_guild_update(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_update_event.assert_called_once_with(shard, payload)

    async def test_on_guild_delete(self, event_manager, shard):
        payload = {"unavailable": False}
        event = object()
        event_manager._app.event_factory.deserialize_guild_leave_event = mock.Mock(return_value=event)

        await event_manager.on_guild_delete(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_leave_event.assert_called_once_with(shard, payload)

    async def test_on_guild_delete_when_unavailable(self, event_manager, shard):
        payload = {"unavailable": True}
        event = object()
        event_manager._app.event_factory.deserialize_guild_unavailable_event = mock.Mock(return_value=event)

        await event_manager.on_guild_delete(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_unavailable_event.assert_called_once_with(shard, payload)

    async def test_on_guild_ban_add(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_guild_ban_add_event = mock.Mock(return_value=event)

        await event_manager.on_guild_ban_add(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_ban_add_event.assert_called_once_with(shard, payload)

    async def test_on_guild_ban_remove(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_guild_ban_remove_event = mock.Mock(return_value=event)

        await event_manager.on_guild_ban_remove(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_ban_remove_event.assert_called_once_with(shard, payload)

    async def test_on_guild_emojis_update(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_guild_emojis_update_event = mock.Mock(return_value=event)

        await event_manager.on_guild_emojis_update(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_emojis_update_event.assert_called_once_with(shard, payload)

    async def test_on_guild_integrations_update(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_guild_integrations_update_event = mock.Mock(return_value=event)

        await event_manager.on_guild_integrations_update(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_integrations_update_event.assert_called_once_with(
            shard, payload
        )

    async def test_on_guild_member_add(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_guild_member_add_event = mock.Mock(return_value=event)

        await event_manager.on_guild_member_add(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_member_add_event.assert_called_once_with(shard, payload)

    async def test_on_guild_member_remove(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_guild_member_remove_event = mock.Mock(return_value=event)

        await event_manager.on_guild_member_remove(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_member_remove_event.assert_called_once_with(shard, payload)

    async def test_on_guild_member_update(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_guild_member_update_event = mock.Mock(return_value=event)

        await event_manager.on_guild_member_update(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_member_update_event.assert_called_once_with(shard, payload)

    async def test_on_guild_members_chunk(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_guild_member_chunk_event = mock.Mock(return_value=event)

        await event_manager.on_guild_members_chunk(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_member_chunk_event.assert_called_once_with(shard, payload)

    async def test_on_guild_role_create(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_guild_role_create_event = mock.Mock(return_value=event)

        await event_manager.on_guild_role_create(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_role_create_event.assert_called_once_with(shard, payload)

    async def test_on_guild_role_update(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_guild_role_update_event = mock.Mock(return_value=event)

        await event_manager.on_guild_role_update(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_role_update_event.assert_called_once_with(shard, payload)

    async def test_on_guild_role_delete(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_guild_role_delete_event = mock.Mock(return_value=event)

        await event_manager.on_guild_role_delete(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_guild_role_delete_event.assert_called_once_with(shard, payload)

    async def test_on_invite_create(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_invite_create_event = mock.Mock(return_value=event)

        await event_manager.on_invite_create(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_invite_create_event.assert_called_once_with(shard, payload)

    async def test_on_invite_delete(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_invite_delete_event = mock.Mock(return_value=event)

        await event_manager.on_invite_delete(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_invite_delete_event.assert_called_once_with(shard, payload)

    async def test_on_message_create(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_message_create_event = mock.Mock(return_value=event)

        await event_manager.on_message_create(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_message_create_event.assert_called_once_with(shard, payload)

    async def test_on_message_update(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_message_update_event = mock.Mock(return_value=event)

        await event_manager.on_message_update(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_message_update_event.assert_called_once_with(shard, payload)

    async def test_on_message_delete(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_message_delete_event = mock.Mock(return_value=event)

        await event_manager.on_message_delete(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_message_delete_event.assert_called_once_with(shard, payload)

    async def test_on_message_delete_bulk(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_message_delete_bulk_event = mock.Mock(return_value=event)

        await event_manager.on_message_delete_bulk(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_message_delete_bulk_event.assert_called_once_with(shard, payload)

    async def test_on_message_reaction_add(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_message_reaction_add_event = mock.Mock(return_value=event)

        await event_manager.on_message_reaction_add(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_message_reaction_add_event.assert_called_once_with(shard, payload)

    async def test_on_message_reaction_remove(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_message_reaction_remove_event = mock.Mock(return_value=event)

        await event_manager.on_message_reaction_remove(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_message_reaction_remove_event.assert_called_once_with(
            shard, payload
        )

    async def test_on_message_reaction_remove_all(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_message_reaction_remove_all_event = mock.Mock(return_value=event)

        await event_manager.on_message_reaction_remove_all(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_message_reaction_remove_all_event.assert_called_once_with(
            shard, payload
        )

    async def test_on_message_reaction_remove_emoji(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_message_reaction_remove_emoji_event = mock.Mock(return_value=event)

        await event_manager.on_message_reaction_remove_emoji(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_message_reaction_remove_emoji_event.assert_called_once_with(
            shard, payload
        )

    async def test_on_presence_update(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_presence_update_event = mock.Mock(return_value=event)

        await event_manager.on_presence_update(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_presence_update_event.assert_called_once_with(shard, payload)

    async def test_on_typing_start(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_typing_start_event = mock.Mock(return_value=event)

        await event_manager.on_typing_start(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_typing_start_event.assert_called_once_with(shard, payload)

    async def test_on_user_update(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_own_user_update_event = mock.Mock(return_value=event)

        await event_manager.on_user_update(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_own_user_update_event.assert_called_once_with(shard, payload)

    async def test_on_voice_state_update(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_voice_state_update_event = mock.Mock(return_value=event)

        await event_manager.on_voice_state_update(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_voice_state_update_event.assert_called_once_with(shard, payload)

    async def test_on_voice_server_update(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_voice_server_update_event = mock.Mock(return_value=event)

        await event_manager.on_voice_server_update(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_voice_server_update_event.assert_called_once_with(shard, payload)

    async def test_on_webhooks_update(self, event_manager, shard, payload):
        event = object()
        event_manager._app.event_factory.deserialize_webhook_update_event = mock.Mock(return_value=event)

        await event_manager.on_webhooks_update(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)
        event_manager._app.event_factory.deserialize_webhook_update_event.assert_called_once_with(shard, payload)
