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
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
import mock
import pytest

from hikari.events import channels
from hikari.events import guilds
from hikari.events import messages
from hikari.events import other
from hikari.clients import shards
from hikari.state import stateless


class TestStatelessEventManagerImpl:
    @pytest.fixture
    def mock_payload(self):
        return {}

    @pytest.fixture
    def event_manager_impl(self):
        class MockDispatcher:
            dispatch_event = mock.MagicMock()

        return stateless.StatelessEventManagerImpl(event_dispatcher_impl=MockDispatcher())

    @pytest.fixture
    def mock_shard(self):
        return mock.MagicMock(shards.ShardClient)

    def test_on_connect(self, event_manager_impl, mock_shard):
        mock_event = mock.MagicMock(other.ConnectedEvent)

        with mock.patch("hikari.events.other.ConnectedEvent", return_value=mock_event) as event:
            event_manager_impl.on_connect(mock_shard, {})

            assert event_manager_impl.on_connect.___event_name___ == {"CONNECTED"}
            event.assert_called_once_with(shard=mock_shard)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_disconnect(self, event_manager_impl, mock_shard):
        mock_event = mock.MagicMock(other.DisconnectedEvent)

        with mock.patch("hikari.events.other.DisconnectedEvent", return_value=mock_event) as event:
            event_manager_impl.on_disconnect(mock_shard, {})

            assert event_manager_impl.on_disconnect.___event_name___ == {"DISCONNECTED"}
            event.assert_called_once_with(shard=mock_shard)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_resume(self, event_manager_impl, mock_shard):
        mock_event = mock.MagicMock(other.ResumedEvent)

        with mock.patch("hikari.events.other.ResumedEvent", return_value=mock_event) as event:
            event_manager_impl.on_resume(mock_shard, {})

            assert event_manager_impl.on_resume.___event_name___ == {"RESUME"}
            event.assert_called_once_with(shard=mock_shard)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_ready(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(other.ReadyEvent)

        with mock.patch("hikari.events.other.ReadyEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_ready(None, mock_payload)

            assert event_manager_impl.on_ready.___event_name___ == {"READY"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_channel_create(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channels.ChannelCreateEvent)

        with mock.patch("hikari.events.channels.ChannelCreateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_channel_create(None, mock_payload)

            assert event_manager_impl.on_channel_create.___event_name___ == {"CHANNEL_CREATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_channel_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channels.ChannelUpdateEvent)

        with mock.patch("hikari.events.channels.ChannelUpdateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_channel_update(None, mock_payload)

            assert event_manager_impl.on_channel_update.___event_name___ == {"CHANNEL_UPDATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_channel_delete(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channels.ChannelDeleteEvent)

        with mock.patch("hikari.events.channels.ChannelDeleteEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_channel_delete(None, mock_payload)

            assert event_manager_impl.on_channel_delete.___event_name___ == {"CHANNEL_DELETE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_channel_pin_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channels.ChannelPinUpdateEvent)

        with mock.patch("hikari.events.channels.ChannelPinUpdateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_channel_pin_update(None, mock_payload)

            assert event_manager_impl.on_channel_pin_update.___event_name___ == {"CHANNEL_PIN_UPDATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_guild_create(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guilds.GuildCreateEvent)

        with mock.patch("hikari.events.guilds.GuildCreateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_guild_create(None, mock_payload)

            assert event_manager_impl.on_guild_create.___event_name___ == {"GUILD_CREATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_guild_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guilds.GuildUpdateEvent)

        with mock.patch("hikari.events.guilds.GuildUpdateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_guild_update(None, mock_payload)

            assert event_manager_impl.on_guild_update.___event_name___ == {"GUILD_UPDATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_guild_delete_handles_guild_leave(self, event_manager_impl, mock_payload):
        mock_payload.pop("unavailable", None)
        mock_event = mock.MagicMock(guilds.GuildLeaveEvent)

        with mock.patch("hikari.events.guilds.GuildLeaveEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_guild_delete(None, mock_payload)

            assert event_manager_impl.on_guild_delete.___event_name___ == {"GUILD_DELETE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_guild_delete_handles_guild_unavailable(self, event_manager_impl, mock_payload):
        mock_payload["unavailable"] = True
        mock_event = mock.MagicMock(guilds.GuildUnavailableEvent)

        with mock.patch("hikari.events.guilds.GuildUnavailableEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_guild_delete(None, mock_payload)

            assert event_manager_impl.on_guild_delete.___event_name___ == {"GUILD_DELETE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_guild_ban_add(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guilds.GuildBanAddEvent)

        with mock.patch("hikari.events.guilds.GuildBanAddEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_guild_ban_add(None, mock_payload)

            assert event_manager_impl.on_guild_ban_add.___event_name___ == {"GUILD_BAN_ADD"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_guild_ban_remove(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guilds.GuildBanRemoveEvent)

        with mock.patch("hikari.events.guilds.GuildBanRemoveEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_guild_ban_remove(None, mock_payload)

            assert event_manager_impl.on_guild_ban_remove.___event_name___ == {"GUILD_BAN_REMOVE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_guild_emojis_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guilds.GuildEmojisUpdateEvent)

        with mock.patch("hikari.events.guilds.GuildEmojisUpdateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_guild_emojis_update(None, mock_payload)

            assert event_manager_impl.on_guild_emojis_update.___event_name___ == {"GUILD_EMOJIS_UPDATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_guild_integrations_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guilds.GuildIntegrationsUpdateEvent)

        with mock.patch(
            "hikari.events.guilds.GuildIntegrationsUpdateEvent.deserialize", return_value=mock_event
        ) as event:
            event_manager_impl.on_guild_integrations_update(None, mock_payload)

            assert event_manager_impl.on_guild_integrations_update.___event_name___ == {"GUILD_INTEGRATIONS_UPDATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_guild_member_add(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guilds.GuildMemberAddEvent)

        with mock.patch("hikari.events.guilds.GuildMemberAddEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_guild_member_add(None, mock_payload)

            assert event_manager_impl.on_guild_member_add.___event_name___ == {"GUILD_MEMBER_ADD"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_guild_member_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guilds.GuildMemberUpdateEvent)

        with mock.patch("hikari.events.guilds.GuildMemberUpdateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_guild_member_update(None, mock_payload)

            assert event_manager_impl.on_guild_member_update.___event_name___ == {"GUILD_MEMBER_UPDATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_guild_member_remove(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guilds.GuildMemberRemoveEvent)

        with mock.patch("hikari.events.guilds.GuildMemberRemoveEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_guild_member_remove(None, mock_payload)

            assert event_manager_impl.on_guild_member_remove.___event_name___ == {"GUILD_MEMBER_REMOVE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_guild_role_create(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guilds.GuildRoleCreateEvent)

        with mock.patch("hikari.events.guilds.GuildRoleCreateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_guild_role_create(None, mock_payload)

            assert event_manager_impl.on_guild_role_create.___event_name___ == {"GUILD_ROLE_CREATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_guild_role_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guilds.GuildRoleUpdateEvent)

        with mock.patch("hikari.events.guilds.GuildRoleUpdateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_guild_role_update(None, mock_payload)

            assert event_manager_impl.on_guild_role_update.___event_name___ == {"GUILD_ROLE_UPDATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_guild_role_delete(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guilds.GuildRoleDeleteEvent)

        with mock.patch("hikari.events.guilds.GuildRoleDeleteEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_guild_role_delete(None, mock_payload)

            assert event_manager_impl.on_guild_role_delete.___event_name___ == {"GUILD_ROLE_DELETE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_invite_create(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channels.InviteCreateEvent)

        with mock.patch("hikari.events.channels.InviteCreateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_invite_create(None, mock_payload)

            assert event_manager_impl.on_invite_create.___event_name___ == {"INVITE_CREATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_invite_delete(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channels.InviteDeleteEvent)

        with mock.patch("hikari.events.channels.InviteDeleteEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_invite_delete(None, mock_payload)

            assert event_manager_impl.on_invite_delete.___event_name___ == {"INVITE_DELETE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_message_create(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(messages.MessageCreateEvent)

        with mock.patch("hikari.events.messages.MessageCreateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_message_create(None, mock_payload)

            assert event_manager_impl.on_message_create.___event_name___ == {"MESSAGE_CREATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_message_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(messages.MessageUpdateEvent)

        with mock.patch("hikari.events.messages.MessageUpdateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_message_update(None, mock_payload)

            assert event_manager_impl.on_message_update.___event_name___ == {"MESSAGE_UPDATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_message_delete(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(messages.MessageDeleteEvent)

        with mock.patch("hikari.events.messages.MessageDeleteEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_message_delete(None, mock_payload)

            assert event_manager_impl.on_message_delete.___event_name___ == {"MESSAGE_DELETE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_message_delete_bulk(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(messages.MessageDeleteBulkEvent)

        with mock.patch("hikari.events.messages.MessageDeleteBulkEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_message_delete_bulk(None, mock_payload)

            assert event_manager_impl.on_message_delete_bulk.___event_name___ == {"MESSAGE_DELETE_BULK"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_message_reaction_add(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(messages.MessageReactionAddEvent)

        with mock.patch("hikari.events.messages.MessageReactionAddEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_message_reaction_add(None, mock_payload)

            assert event_manager_impl.on_message_reaction_add.___event_name___ == {"MESSAGE_REACTION_ADD"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_message_reaction_remove(self, event_manager_impl, mock_payload):
        mock_payload["emoji"] = {}
        mock_event = mock.MagicMock(messages.MessageReactionRemoveEvent)

        with mock.patch(
            "hikari.events.messages.MessageReactionRemoveEvent.deserialize", return_value=mock_event
        ) as event:
            event_manager_impl.on_message_reaction_remove(None, mock_payload)

            assert event_manager_impl.on_message_reaction_remove.___event_name___ == {"MESSAGE_REACTION_REMOVE"}
            event.assert_called_once_with({"emoji": {"animated": None}})
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_message_reaction_remove_emoji(self, event_manager_impl, mock_payload):
        mock_payload["emoji"] = {}
        mock_event = mock.MagicMock(messages.MessageReactionRemoveEmojiEvent)

        with mock.patch(
            "hikari.events.messages.MessageReactionRemoveEmojiEvent.deserialize", return_value=mock_event
        ) as event:
            event_manager_impl.on_message_reaction_remove_emoji(None, mock_payload)

            assert event_manager_impl.on_message_reaction_remove_emoji.___event_name___ == {
                "MESSAGE_REACTION_REMOVE_EMOJI"
            }
            event.assert_called_once_with({"emoji": {"animated": None}})
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_presence_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guilds.PresenceUpdateEvent)

        with mock.patch("hikari.events.guilds.PresenceUpdateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_presence_update(None, mock_payload)

            assert event_manager_impl.on_presence_update.___event_name___ == {"PRESENCE_UPDATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_typing_start(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channels.TypingStartEvent)

        with mock.patch("hikari.events.channels.TypingStartEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_typing_start(None, mock_payload)

            assert event_manager_impl.on_typing_start.___event_name___ == {"TYPING_START"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_user_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(other.UserUpdateEvent)

        with mock.patch("hikari.events.other.UserUpdateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_user_update(None, mock_payload)

            assert event_manager_impl.on_user_update.___event_name___ == {"USER_UPDATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_voice_state_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channels.VoiceStateUpdateEvent)

        with mock.patch("hikari.events.channels.VoiceStateUpdateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_voice_state_update(None, mock_payload)

            assert event_manager_impl.on_voice_state_update.___event_name___ == {"VOICE_STATE_UPDATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_voice_server_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channels.VoiceStateUpdateEvent)

        with mock.patch("hikari.events.channels.VoiceStateUpdateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_voice_server_update(None, mock_payload)

            assert event_manager_impl.on_voice_server_update.___event_name___ == {"VOICE_SERVER_UPDATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    def test_on_webhook_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channels.WebhookUpdateEvent)

        with mock.patch("hikari.events.channels.WebhookUpdateEvent.deserialize", return_value=mock_event) as event:
            event_manager_impl.on_webhook_update(None, mock_payload)

            assert event_manager_impl.on_webhook_update.___event_name___ == {"WEBHOOK_UPDATE"}
            event.assert_called_once_with(mock_payload)
            event_manager_impl.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)
