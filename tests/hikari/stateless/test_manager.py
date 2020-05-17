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

from hikari import application
from hikari.events import channel
from hikari.events import guild
from hikari.events import message
from hikari.events import other
from hikari.events import voice
from hikari.gateway import client
from hikari.stateless import manager


class TestStatelessEventManagerImpl:
    @pytest.fixture
    def mock_payload(self):
        return {}

    @pytest.fixture
    def event_manager_impl(self):
        class MockDispatcher:
            dispatch_event = mock.AsyncMock()

        return manager.StatelessEventManagerImpl(
            app=mock.MagicMock(application.Application, event_dispatcher=MockDispatcher())
        )

    @pytest.fixture
    def mock_shard(self):
        return mock.MagicMock(client.GatewayClient)

    @pytest.mark.asyncio
    async def test_on_connect(self, event_manager_impl, mock_shard):
        mock_event = mock.MagicMock(other.ConnectedEvent)

        with mock.patch("hikari.events.other.ConnectedEvent", return_value=mock_event) as event:
            await event_manager_impl.on_connect(mock_shard, {})

            assert event_manager_impl.on_connect.___event_name___ == {"CONNECTED"}
            event.assert_called_once_with(shard=mock_shard)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_disconnect(self, event_manager_impl, mock_shard):
        mock_event = mock.MagicMock(other.DisconnectedEvent)

        with mock.patch("hikari.events.other.DisconnectedEvent", return_value=mock_event) as event:
            await event_manager_impl.on_disconnect(mock_shard, {})

            assert event_manager_impl.on_disconnect.___event_name___ == {"DISCONNECTED"}
            event.assert_called_once_with(shard=mock_shard)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_resume(self, event_manager_impl, mock_shard):
        mock_event = mock.MagicMock(other.ResumedEvent)

        with mock.patch("hikari.events.other.ResumedEvent", return_value=mock_event) as event:
            await event_manager_impl.on_resume(mock_shard, {})

            assert event_manager_impl.on_resume.___event_name___ == {"RESUME"}
            event.assert_called_once_with(shard=mock_shard)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_ready(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(other.ReadyEvent)

        with mock.patch("hikari.events.other.ReadyEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_ready(None, mock_payload)

            assert event_manager_impl.on_ready.___event_name___ == {"READY"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_channel_create(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channel.ChannelCreateEvent)

        with mock.patch("hikari.events.channel.ChannelCreateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_channel_create(None, mock_payload)

            assert event_manager_impl.on_channel_create.___event_name___ == {"CHANNEL_CREATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_channel_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channel.ChannelUpdateEvent)

        with mock.patch("hikari.events.channel.ChannelUpdateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_channel_update(None, mock_payload)

            assert event_manager_impl.on_channel_update.___event_name___ == {"CHANNEL_UPDATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_channel_delete(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channel.ChannelDeleteEvent)

        with mock.patch("hikari.events.channel.ChannelDeleteEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_channel_delete(None, mock_payload)

            assert event_manager_impl.on_channel_delete.___event_name___ == {"CHANNEL_DELETE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_channel_pins_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channel.ChannelPinsUpdateEvent)

        with mock.patch("hikari.events.channel.ChannelPinsUpdateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_channel_pins_update(None, mock_payload)

            assert event_manager_impl.on_channel_pins_update.___event_name___ == {"CHANNEL_PINS_UPDATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_guild_create(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guild.GuildCreateEvent)

        with mock.patch("hikari.events.guild.GuildCreateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_guild_create(None, mock_payload)

            assert event_manager_impl.on_guild_create.___event_name___ == {"GUILD_CREATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_guild_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guild.GuildUpdateEvent)

        with mock.patch("hikari.events.guild.GuildUpdateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_guild_update(None, mock_payload)

            assert event_manager_impl.on_guild_update.___event_name___ == {"GUILD_UPDATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_guild_delete_handles_guild_leave(self, event_manager_impl, mock_payload):
        mock_payload.pop("unavailable", None)
        mock_event = mock.MagicMock(guild.GuildLeaveEvent)

        with mock.patch("hikari.events.guild.GuildLeaveEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_guild_delete(None, mock_payload)

            assert event_manager_impl.on_guild_delete.___event_name___ == {"GUILD_DELETE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_guild_delete_handles_guild_unavailable(self, event_manager_impl, mock_payload):
        mock_payload["unavailable"] = True
        mock_event = mock.MagicMock(guild.GuildUnavailableEvent)

        with mock.patch("hikari.events.guild.GuildUnavailableEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_guild_delete(None, mock_payload)

            assert event_manager_impl.on_guild_delete.___event_name___ == {"GUILD_DELETE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_guild_ban_add(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guild.GuildBanAddEvent)

        with mock.patch("hikari.events.guild.GuildBanAddEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_guild_ban_add(None, mock_payload)

            assert event_manager_impl.on_guild_ban_add.___event_name___ == {"GUILD_BAN_ADD"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_guild_ban_remove(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guild.GuildBanRemoveEvent)

        with mock.patch("hikari.events.guild.GuildBanRemoveEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_guild_ban_remove(None, mock_payload)

            assert event_manager_impl.on_guild_ban_remove.___event_name___ == {"GUILD_BAN_REMOVE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_guild_emojis_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guild.GuildEmojisUpdateEvent)

        with mock.patch("hikari.events.guild.GuildEmojisUpdateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_guild_emojis_update(None, mock_payload)

            assert event_manager_impl.on_guild_emojis_update.___event_name___ == {"GUILD_EMOJIS_UPDATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_guild_integrations_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guild.GuildIntegrationsUpdateEvent)

        with mock.patch(
            "hikari.events.guild.GuildIntegrationsUpdateEvent.deserialize", return_value=mock_event
        ) as event:
            await event_manager_impl.on_guild_integrations_update(None, mock_payload)

            assert event_manager_impl.on_guild_integrations_update.___event_name___ == {"GUILD_INTEGRATIONS_UPDATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_guild_member_add(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guild.GuildMemberAddEvent)

        with mock.patch("hikari.events.guild.GuildMemberAddEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_guild_member_add(None, mock_payload)

            assert event_manager_impl.on_guild_member_add.___event_name___ == {"GUILD_MEMBER_ADD"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_guild_member_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guild.GuildMemberUpdateEvent)

        with mock.patch("hikari.events.guild.GuildMemberUpdateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_guild_member_update(None, mock_payload)

            assert event_manager_impl.on_guild_member_update.___event_name___ == {"GUILD_MEMBER_UPDATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_guild_member_remove(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guild.GuildMemberRemoveEvent)

        with mock.patch("hikari.events.guild.GuildMemberRemoveEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_guild_member_remove(None, mock_payload)

            assert event_manager_impl.on_guild_member_remove.___event_name___ == {"GUILD_MEMBER_REMOVE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_guild_role_create(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guild.GuildRoleCreateEvent)

        with mock.patch("hikari.events.guild.GuildRoleCreateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_guild_role_create(None, mock_payload)

            assert event_manager_impl.on_guild_role_create.___event_name___ == {"GUILD_ROLE_CREATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_guild_role_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guild.GuildRoleUpdateEvent)

        with mock.patch("hikari.events.guild.GuildRoleUpdateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_guild_role_update(None, mock_payload)

            assert event_manager_impl.on_guild_role_update.___event_name___ == {"GUILD_ROLE_UPDATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_guild_role_delete(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guild.GuildRoleDeleteEvent)

        with mock.patch("hikari.events.guild.GuildRoleDeleteEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_guild_role_delete(None, mock_payload)

            assert event_manager_impl.on_guild_role_delete.___event_name___ == {"GUILD_ROLE_DELETE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_invite_create(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channel.InviteCreateEvent)

        with mock.patch("hikari.events.channel.InviteCreateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_invite_create(None, mock_payload)

            assert event_manager_impl.on_invite_create.___event_name___ == {"INVITE_CREATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_invite_delete(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channel.InviteDeleteEvent)

        with mock.patch("hikari.events.channel.InviteDeleteEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_invite_delete(None, mock_payload)

            assert event_manager_impl.on_invite_delete.___event_name___ == {"INVITE_DELETE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_message_create_without_member_payload(self, event_manager_impl):
        mock_payload = {"id": "424242", "user": {"id": "111", "username": "okokok", "discrim": "4242"}}
        mock_event = mock.MagicMock(message.MessageCreateEvent)

        with mock.patch("hikari.events.message.MessageCreateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_message_create(None, mock_payload)

            assert event_manager_impl.on_message_create.___event_name___ == {"MESSAGE_CREATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_message_create_injects_user_into_member_payload(self, event_manager_impl):
        mock_payload = {"id": "424242", "author": {"id": "111", "username": "okokok", "discrim": "4242"}, "member": {}}
        mock_event = mock.MagicMock(message.MessageCreateEvent)

        with mock.patch("hikari.events.message.MessageCreateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_message_create(None, mock_payload)

            assert event_manager_impl.on_message_create.___event_name___ == {"MESSAGE_CREATE"}
            event.assert_called_once_with(
                {
                    "id": "424242",
                    "author": {"id": "111", "username": "okokok", "discrim": "4242"},
                    "member": {"user": {"id": "111", "username": "okokok", "discrim": "4242"}},
                },
                app=event_manager_impl._app,
            )
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_message_update_without_member_payload(self, event_manager_impl, mock_payload):
        mock_payload = {"id": "424242", "user": {"id": "111", "username": "okokok", "discrim": "4242"}}
        mock_event = mock.MagicMock(message.MessageUpdateEvent)

        with mock.patch("hikari.events.message.MessageUpdateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_message_update(None, mock_payload)

            assert event_manager_impl.on_message_update.___event_name___ == {"MESSAGE_UPDATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_message_update_injects_user_into_member_payload(self, event_manager_impl, mock_payload):
        mock_payload = {"id": "424242", "author": {"id": "111", "username": "okokok", "discrim": "4242"}, "member": {}}
        mock_event = mock.MagicMock(message.MessageUpdateEvent)

        with mock.patch("hikari.events.message.MessageUpdateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_message_update(None, mock_payload)

            assert event_manager_impl.on_message_update.___event_name___ == {"MESSAGE_UPDATE"}
            event.assert_called_once_with(
                {
                    "id": "424242",
                    "author": {"id": "111", "username": "okokok", "discrim": "4242"},
                    "member": {"user": {"id": "111", "username": "okokok", "discrim": "4242"}},
                },
                app=event_manager_impl._app,
            )
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_message_delete(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(message.MessageDeleteEvent)

        with mock.patch("hikari.events.message.MessageDeleteEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_message_delete(None, mock_payload)

            assert event_manager_impl.on_message_delete.___event_name___ == {"MESSAGE_DELETE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_message_delete_bulk(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(message.MessageDeleteBulkEvent)

        with mock.patch("hikari.events.message.MessageDeleteBulkEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_message_delete_bulk(None, mock_payload)

            assert event_manager_impl.on_message_delete_bulk.___event_name___ == {"MESSAGE_DELETE_BULK"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_message_reaction_add(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(message.MessageReactionAddEvent)

        with mock.patch("hikari.events.message.MessageReactionAddEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_message_reaction_add(None, mock_payload)

            assert event_manager_impl.on_message_reaction_add.___event_name___ == {"MESSAGE_REACTION_ADD"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_message_reaction_remove(self, event_manager_impl, mock_payload):
        mock_payload["emoji"] = {}
        mock_event = mock.MagicMock(message.MessageReactionRemoveEvent)

        with mock.patch(
            "hikari.events.message.MessageReactionRemoveEvent.deserialize", return_value=mock_event
        ) as event:
            await event_manager_impl.on_message_reaction_remove(None, mock_payload)

            assert event_manager_impl.on_message_reaction_remove.___event_name___ == {"MESSAGE_REACTION_REMOVE"}
            event.assert_called_once_with({"emoji": {"animated": None}}, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_message_reaction_remove_emoji(self, event_manager_impl, mock_payload):
        mock_payload["emoji"] = {}
        mock_event = mock.MagicMock(message.MessageReactionRemoveEmojiEvent)

        with mock.patch(
            "hikari.events.message.MessageReactionRemoveEmojiEvent.deserialize", return_value=mock_event
        ) as event:
            await event_manager_impl.on_message_reaction_remove_emoji(None, mock_payload)

            assert event_manager_impl.on_message_reaction_remove_emoji.___event_name___ == {
                "MESSAGE_REACTION_REMOVE_EMOJI"
            }
            event.assert_called_once_with({"emoji": {"animated": None}}, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_presence_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(guild.PresenceUpdateEvent)

        with mock.patch("hikari.events.guild.PresenceUpdateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_presence_update(None, mock_payload)

            assert event_manager_impl.on_presence_update.___event_name___ == {"PRESENCE_UPDATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_typing_start(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channel.TypingStartEvent)

        with mock.patch("hikari.events.channel.TypingStartEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_typing_start(None, mock_payload)

            assert event_manager_impl.on_typing_start.___event_name___ == {"TYPING_START"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_my_user_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(other.MyUserUpdateEvent)

        with mock.patch("hikari.events.other.MyUserUpdateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_my_user_update(None, mock_payload)

            assert event_manager_impl.on_my_user_update.___event_name___ == {"USER_UPDATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_voice_state_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(voice.VoiceStateUpdateEvent)

        with mock.patch("hikari.events.voice.VoiceStateUpdateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_voice_state_update(None, mock_payload)

            assert event_manager_impl.on_voice_state_update.___event_name___ == {"VOICE_STATE_UPDATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_voice_server_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(voice.VoiceStateUpdateEvent)

        with mock.patch("hikari.events.voice.VoiceServerUpdateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_voice_server_update(None, mock_payload)

            assert event_manager_impl.on_voice_server_update.___event_name___ == {"VOICE_SERVER_UPDATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)

    @pytest.mark.asyncio
    async def test_on_webhook_update(self, event_manager_impl, mock_payload):
        mock_event = mock.MagicMock(channel.WebhookUpdateEvent)

        with mock.patch("hikari.events.channel.WebhookUpdateEvent.deserialize", return_value=mock_event) as event:
            await event_manager_impl.on_webhook_update(None, mock_payload)

            assert event_manager_impl.on_webhook_update.___event_name___ == {"WEBHOOK_UPDATE"}
            event.assert_called_once_with(mock_payload, app=event_manager_impl._app)
            event_manager_impl._app.event_dispatcher.dispatch_event.assert_called_once_with(mock_event)
