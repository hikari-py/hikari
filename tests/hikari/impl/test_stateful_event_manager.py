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

from hikari import channels
from hikari import intents
from hikari.events import shard_events
from hikari.impl import stateful_event_manager
from tests.hikari import hikari_test_helpers


class TestStatefulEventManagerImpl:
    @pytest.fixture()
    def app(self):
        return mock.Mock()

    @pytest.fixture()
    def shard(self):
        return mock.Mock()

    @pytest.fixture()
    def event_manager(self, app):
        obj = hikari_test_helpers.mock_class_namespace(stateful_event_manager.StatefulEventManagerImpl, slots_=False)(
            app, mock.Mock(), intents.Intents.ALL
        )

        obj.dispatch = mock.AsyncMock()
        return obj

    @pytest.mark.asyncio
    async def test_on_connected(self, event_manager, shard, app):
        payload = {}
        event = shard_events.ShardConnectedEvent(app=app, shard=shard)

        await event_manager.on_connected(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_disconnected(self, event_manager, shard, app):
        payload = {}
        event = shard_events.ShardDisconnectedEvent(app=app, shard=shard)

        await event_manager.on_disconnected(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_ready(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(my_user=mock.Mock())

        event_manager._app.event_factory.deserialize_ready_event.return_value = event

        await event_manager.on_ready(shard, payload)

        event_manager._cache.update_me.assert_called_once_with(event.my_user)
        event_manager._app.event_factory.deserialize_ready_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_resumed(self, event_manager, shard, app):
        payload = {}
        event = shard_events.ShardResumedEvent(app=app, shard=shard)

        await event_manager.on_resumed(shard, payload)

        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_channel_create(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(channel=mock.Mock(channels.GuildChannel))

        event_manager._app.event_factory.deserialize_channel_create_event.return_value = event

        await event_manager.on_channel_create(shard, payload)

        event_manager._cache.set_guild_channel.assert_called_once_with(event.channel)
        event_manager._app.event_factory.deserialize_channel_create_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_channel_update(self, event_manager, shard, app):
        payload = {"id": 123}
        old_channel = object()
        event = mock.Mock(channel=mock.Mock(channels.GuildChannel))

        event_manager._app.event_factory.deserialize_channel_update_event.return_value = event
        event_manager._cache.get_guild_channel.return_value = old_channel

        await event_manager.on_channel_update(shard, payload)

        event_manager._cache.get_guild_channel.assert_called_once_with(123)
        event_manager._cache.update_guild_channel.assert_called_once_with(event.channel)
        event_manager._app.event_factory.deserialize_channel_update_event.assert_called_once_with(
            shard, payload, old_channel=old_channel
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_channel_delete(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(channel=mock.Mock(id=123))

        event_manager._app.event_factory.deserialize_channel_delete_event.return_value = event

        await event_manager.on_channel_delete(shard, payload)

        event_manager._cache.delete_guild_channel.assert_called_once_with(123)
        event_manager._app.event_factory.deserialize_channel_delete_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_channel_pins_update(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_channel_pins_update_event.return_value = event

        await event_manager.on_channel_pins_update(shard, payload)

        event_manager._app.event_factory.deserialize_channel_pins_update_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_create(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(
            guild=mock.Mock(id=123),
            channels={"TestChannel": 456},
            emojis={"TestEmoji": 789},
            roles={"TestRole": 1234},
            members={"TestMember": 5678},
            presences={"TestPresence": 9012},
            voice_states={"TestState": 345},
        )

        event_manager._app.event_factory.deserialize_guild_create_event.return_value = event
        shard.request_guild_members = mock.AsyncMock()

        await event_manager.on_guild_create(shard, payload)

        event_manager._cache.update_guild.assert_called_once_with(event.guild)

        event_manager._cache.clear_guild_channels_for_guild.assert_called_once_with(123)
        event_manager._cache.set_guild_channel.assert_called_once_with(456)

        event_manager._cache.clear_emojis_for_guild.assert_called_once_with(123)
        event_manager._cache.set_emoji.assert_called_once_with(789)

        event_manager._cache.clear_roles_for_guild.assert_called_once_with(123)
        event_manager._cache.set_role.assert_called_once_with(1234)

        event_manager._cache.clear_members_for_guild.assert_called_once_with(123)
        event_manager._cache.set_member.assert_called_once_with(5678)

        event_manager._cache.clear_presences_for_guild.assert_called_once_with(123)
        event_manager._cache.set_presence.assert_called_once_with(9012)

        event_manager._cache.clear_voice_states_for_guild.assert_called_once_with(123)
        event_manager._cache.set_voice_state.assert_called_once_with(345)

        event_manager._app.event_factory.deserialize_guild_create_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_update(self, event_manager, shard, app):
        payload = {"id": 123}
        old_guild = object()
        event = mock.Mock(roles={}, emojis={}, guild=mock.Mock(id=123))

        event_manager._app.event_factory.deserialize_guild_update_event.return_value = event
        event_manager._cache.get_guild.return_value = old_guild

        await event_manager.on_guild_update(shard, payload)

        event_manager._cache.get_guild.assert_called_once_with(123)
        event_manager._cache.update_guild.assert_called_once_with(event.guild)
        event_manager._cache.clear_roles_for_guild.assert_called_once_with(123)
        event_manager._cache.clear_emojis_for_guild.assert_called_once_with(123)
        event_manager._app.event_factory.deserialize_guild_update_event.assert_called_once_with(
            shard, payload, old_guild=old_guild
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_delete(self, event_manager, shard, app):
        payload = {"unavailable": False}
        event = mock.Mock(guild_id=123)

        event_manager._app.event_factory.deserialize_guild_leave_event.return_value = event

        await event_manager.on_guild_delete(shard, payload)

        event_manager._cache.delete_guild.assert_called_once_with(123)
        event_manager._cache.clear_voice_states_for_guild.assert_called_once_with(123)
        event_manager._cache.clear_invites_for_guild.assert_called_once_with(123)
        event_manager._cache.clear_members_for_guild.assert_called_once_with(123)
        event_manager._cache.clear_presences_for_guild.assert_called_once_with(123)
        event_manager._cache.clear_guild_channels_for_guild.assert_called_once_with(123)
        event_manager._cache.clear_emojis_for_guild.assert_called_once_with(123)
        event_manager._cache.clear_roles_for_guild.assert_called_once_with(123)
        event_manager._app.event_factory.deserialize_guild_leave_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_ban_add(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_guild_ban_add_event.return_value = event

        await event_manager.on_guild_ban_add(shard, payload)

        event_manager._app.event_factory.deserialize_guild_ban_add_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_ban_remove(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_guild_ban_remove_event.return_value = event

        await event_manager.on_guild_ban_remove(shard, payload)

        event_manager._app.event_factory.deserialize_guild_ban_remove_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_emojis_update(self, event_manager, shard, app):
        payload = {"guild_id": 123}
        old_emojis = {"Test": 123}
        event = mock.Mock(emojis={}, guild_id=123)

        event_manager._app.event_factory.deserialize_guild_emojis_update_event.return_value = event
        event_manager._cache.get_emojis_view_for_guild.return_value = old_emojis

        await event_manager.on_guild_emojis_update(shard, payload)

        event_manager._cache.get_emojis_view_for_guild.assert_called_once_with(123)
        event_manager._cache.clear_emojis_for_guild.assert_called_once_with(123)
        event_manager._app.event_factory.deserialize_guild_emojis_update_event.assert_called_once_with(
            shard, payload, old_emojis=[123]
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_integration_create(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_integration_create_event.return_value = event

        await event_manager.on_integration_create(shard, payload)

        event_manager._app.event_factory.deserialize_integration_create_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_integration_delete(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_integration_delete_event.return_value = event

        await event_manager.on_integration_delete(shard, payload)

        event_manager._app.event_factory.deserialize_integration_delete_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_integration_update(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_integration_update_event.return_value = event

        await event_manager.on_integration_update(shard, payload)

        event_manager._app.event_factory.deserialize_integration_update_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_member_add(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(user=object(), member=object())

        event_manager._app.event_factory.deserialize_guild_member_add_event.return_value = event

        await event_manager.on_guild_member_add(shard, payload)

        event_manager._cache.update_member.assert_called_once_with(event.member)
        event_manager._app.event_factory.deserialize_guild_member_add_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_member_remove(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(user=mock.Mock(id=123), guild_id=456)

        event_manager._app.event_factory.deserialize_guild_member_remove_event.return_value = event

        await event_manager.on_guild_member_remove(shard, payload)

        event_manager._cache.delete_member.assert_called_once_with(456, 123)
        event_manager._app.event_factory.deserialize_guild_member_remove_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_member_update(self, event_manager, shard, app):
        payload = {"user": {"id": 123}, "guild_id": 456}
        old_member = object()
        event = mock.Mock(member=mock.Mock())

        event_manager._app.event_factory.deserialize_guild_member_update_event.return_value = event
        event_manager._cache.get_member.return_value = old_member

        await event_manager.on_guild_member_update(shard, payload)

        event_manager._cache.get_member.assert_called_once_with(456, 123)
        event_manager._cache.update_member.assert_called_once_with(event.member)
        event_manager._app.event_factory.deserialize_guild_member_update_event.assert_called_once_with(
            shard, payload, old_member=old_member
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_members_chunk(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(members={"TestMember": 123}, presences={"TestPresences": 456})

        event_manager._app.event_factory.deserialize_guild_member_chunk_event.return_value = event
        event_manager._app.chunker.consume_chunk_event = mock.AsyncMock()

        await event_manager.on_guild_members_chunk(shard, payload)

        event_manager._cache.set_member.assert_called_once_with(123)
        event_manager._cache.set_presence.assert_called_once_with(456)
        event_manager._app.event_factory.deserialize_guild_member_chunk_event.assert_called_once_with(shard, payload)
        event_manager._app.chunker.consume_chunk_event.assert_awaited_once_with(event)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_role_create(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(role=object())

        event_manager._app.event_factory.deserialize_guild_role_create_event.return_value = event

        await event_manager.on_guild_role_create(shard, payload)

        event_manager._cache.set_role.assert_called_once_with(event.role)
        event_manager._app.event_factory.deserialize_guild_role_create_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_role_update(self, event_manager, shard, app):
        payload = {"role": {"id": 123}}
        old_role = object()
        event = mock.Mock(role=mock.Mock())

        event_manager._app.event_factory.deserialize_guild_role_update_event.return_value = event
        event_manager._cache.get_role.return_value = old_role

        await event_manager.on_guild_role_update(shard, payload)

        event_manager._cache.get_role.assert_called_once_with(123)
        event_manager._cache.update_role.assert_called_once_with(event.role)
        event_manager._app.event_factory.deserialize_guild_role_update_event.assert_called_once_with(
            shard, payload, old_role=old_role
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_guild_role_delete(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(role_id=123)

        event_manager._app.event_factory.deserialize_guild_role_delete_event.return_value = event

        await event_manager.on_guild_role_delete(shard, payload)

        event_manager._cache.delete_role.assert_called_once_with(123)
        event_manager._app.event_factory.deserialize_guild_role_delete_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_invite_create(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(invite="qwerty")

        event_manager._app.event_factory.deserialize_invite_create_event.return_value = event

        await event_manager.on_invite_create(shard, payload)

        event_manager._cache.set_invite.assert_called_once_with("qwerty")
        event_manager._app.event_factory.deserialize_invite_create_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_invite_delete(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(code="qwerty")

        event_manager._app.event_factory.deserialize_invite_delete_event.return_value = event

        await event_manager.on_invite_delete(shard, payload)

        event_manager._cache.delete_invite.assert_called_once_with("qwerty")
        event_manager._app.event_factory.deserialize_invite_delete_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_create(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(message=object())

        event_manager._app.event_factory.deserialize_message_create_event.return_value = event

        await event_manager.on_message_create(shard, payload)

        event_manager._cache.set_message.assert_called_once_with(event.message)
        event_manager._app.event_factory.deserialize_message_create_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_update(self, event_manager, shard, app):
        payload = {"id": 123}
        old_message = object()
        event = mock.Mock(message=mock.Mock())

        event_manager._app.event_factory.deserialize_message_update_event.return_value = event
        event_manager._cache.get_message.return_value = old_message

        await event_manager.on_message_update(shard, payload)

        event_manager._cache.get_message.assert_called_once_with(123)
        event_manager._cache.update_message.assert_called_once_with(event.message)
        event_manager._app.event_factory.deserialize_message_update_event.assert_called_once_with(
            shard, payload, old_message=old_message
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_delete(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(message_id=123)

        event_manager._app.event_factory.deserialize_message_delete_event.return_value = event

        await event_manager.on_message_delete(shard, payload)

        event_manager._cache.delete_message.assert_called_once_with(123)
        event_manager._app.event_factory.deserialize_message_delete_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_delete_bulk(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock(message_ids=[123, 456, 789])

        event_manager._app.event_factory.deserialize_message_delete_bulk_event.return_value = event

        await event_manager.on_message_delete_bulk(shard, payload)

        assert len(event_manager._cache.delete_message.mock_calls) == 3
        event_manager._app.event_factory.deserialize_message_delete_bulk_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_reaction_add(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_message_reaction_add_event.return_value = event

        await event_manager.on_message_reaction_add(shard, payload)

        event_manager._app.event_factory.deserialize_message_reaction_add_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_reaction_remove(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_message_reaction_remove_event.return_value = event

        await event_manager.on_message_reaction_remove(shard, payload)

        event_manager._app.event_factory.deserialize_message_reaction_remove_event.assert_called_once_with(
            shard, payload
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_reaction_remove_all(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_message_reaction_remove_all_event.return_value = event

        await event_manager.on_message_reaction_remove_all(shard, payload)

        event_manager._app.event_factory.deserialize_message_reaction_remove_all_event.assert_called_once_with(
            shard, payload
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_message_reaction_remove_emoji(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_message_reaction_remove_emoji_event.return_value = event

        await event_manager.on_message_reaction_remove_emoji(shard, payload)

        event_manager._app.event_factory.deserialize_message_reaction_remove_emoji_event.assert_called_once_with(
            shard, payload
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_presence_update(self, event_manager, shard, app):
        payload = {"user": {"id": 123}, "guild_id": 456}
        old_presence = object()
        event = mock.Mock(presence=mock.Mock())

        event_manager._app.event_factory.deserialize_presence_update_event.return_value = event
        event_manager._cache.get_presence.return_value = old_presence

        await event_manager.on_presence_update(shard, payload)

        event_manager._cache.get_presence.assert_called_once_with(456, 123)
        event_manager._cache.update_presence.assert_called_once_with(event.presence)
        event_manager._app.event_factory.deserialize_presence_update_event.assert_called_once_with(
            shard, payload, old_presence=old_presence
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_typing_start(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_typing_start_event.return_value = event

        await event_manager.on_typing_start(shard, payload)

        event_manager._app.event_factory.deserialize_typing_start_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_user_update(self, event_manager, shard, app):
        payload = {}
        old_user = object()
        event = mock.Mock(user=mock.Mock())

        event_manager._app.event_factory.deserialize_own_user_update_event.return_value = event
        event_manager._cache.get_me.return_value = old_user

        await event_manager.on_user_update(shard, payload)

        event_manager._cache.update_me.assert_called_once_with(event.user)
        event_manager._app.event_factory.deserialize_own_user_update_event.assert_called_once_with(
            shard, payload, old_user=old_user
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_voice_state_update(self, event_manager, shard, app):
        payload = {"user_id": 123, "guild_id": 456}
        old_state = object()
        event = mock.Mock(state=mock.Mock())

        event_manager._app.event_factory.deserialize_voice_state_update_event.return_value = event
        event_manager._cache.get_voice_state.return_value = old_state

        await event_manager.on_voice_state_update(shard, payload)

        event_manager._cache.get_voice_state.assert_called_once_with(456, 123)
        event_manager._cache.update_voice_state.assert_called_once_with(event.state)
        event_manager._app.event_factory.deserialize_voice_state_update_event.assert_called_once_with(
            shard, payload, old_state=old_state
        )
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_voice_server_update(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_voice_server_update_event.return_value = event

        await event_manager.on_voice_server_update(shard, payload)

        event_manager._app.event_factory.deserialize_voice_server_update_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_webhooks_update(self, event_manager, shard, app):
        payload = {}
        event = mock.Mock()

        event_manager._app.event_factory.deserialize_webhook_update_event.return_value = event

        await event_manager.on_webhooks_update(shard, payload)

        event_manager._app.event_factory.deserialize_webhook_update_event.assert_called_once_with(shard, payload)
        event_manager.dispatch.assert_awaited_once_with(event)
