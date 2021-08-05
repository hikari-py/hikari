# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
import datetime

import mock
import pytest

from hikari import channels as channel_models
from hikari import emojis as emoji_models
from hikari import traits
from hikari import undefined
from hikari import users as user_models
from hikari.events import channel_events
from hikari.events import guild_events
from hikari.events import interaction_events
from hikari.events import lifetime_events
from hikari.events import member_events
from hikari.events import message_events
from hikari.events import reaction_events
from hikari.events import role_events
from hikari.events import shard_events
from hikari.events import typing_events
from hikari.events import user_events
from hikari.events import voice_events
from hikari.impl import event_factory as event_factory_


class TestEventFactoryImpl:
    @pytest.fixture()
    def mock_app(self):
        return mock.Mock(traits.RESTAware)

    @pytest.fixture()
    def mock_shard(self):
        return mock.Mock(traits.ShardAware)

    @pytest.fixture()
    def event_factory(self, mock_app):
        return event_factory_.EventFactoryImpl(mock_app)

    ##################
    # CHANNEL EVENTS #
    ##################

    def test_deserialize_channel_create_event_for_guild_channel(self, event_factory, mock_app, mock_shard):
        mock_app.entity_factory.deserialize_channel.return_value = mock.Mock(spec=channel_models.GuildChannel)
        mock_payload = mock.Mock(app=mock_app)

        event = event_factory.deserialize_channel_create_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_channel.assert_called_once_with(mock_payload)
        assert isinstance(event, channel_events.GuildChannelCreateEvent)
        assert event.shard is mock_shard
        assert event.channel is mock_app.entity_factory.deserialize_channel.return_value

    def test_deserialize_channel_create_event_for_dm_channel(self, event_factory, mock_app, mock_shard):
        mock_app.entity_factory.deserialize_channel.return_value = mock.Mock(spec=channel_models.DMChannel)

        with pytest.raises(NotImplementedError):
            event_factory.deserialize_channel_create_event(mock_shard, {"id": "42"})

    def test_deserialize_channel_create_event_for_unexpected_channel_type(self, event_factory, mock_app, mock_shard):
        with pytest.raises(TypeError, match="Expected GuildChannel or PrivateChannel but received Mock"):
            event_factory.deserialize_channel_create_event(mock_shard, {"id": "42"})

    def test_deserialize_channel_update_event_with_guild_channel(self, event_factory, mock_app, mock_shard):
        mock_app.entity_factory.deserialize_channel.return_value = mock.Mock(spec=channel_models.GuildChannel)
        mock_old_channel = object()
        mock_payload = object()

        event = event_factory.deserialize_channel_update_event(mock_shard, mock_payload, old_channel=mock_old_channel)

        mock_app.entity_factory.deserialize_channel.assert_called_once_with(mock_payload)
        assert isinstance(event, channel_events.GuildChannelUpdateEvent)
        assert event.shard is mock_shard
        assert event.channel is mock_app.entity_factory.deserialize_channel.return_value
        assert event.old_channel is mock_old_channel

    def test_deserialize_channel_update_event_with_dm_channel(self, event_factory, mock_app, mock_shard):
        mock_app.entity_factory.deserialize_channel.return_value = mock.Mock(spec=channel_models.DMChannel)

        with pytest.raises(NotImplementedError):
            event_factory.deserialize_channel_update_event(mock_shard, {"id": "42"}, old_channel=None)

    def test_deserialize_channel_update_event_with_unexpected_channel_type(self, event_factory, mock_app, mock_shard):
        with pytest.raises(TypeError, match="Expected GuildChannel or PrivateChannel but received Mock"):
            event_factory.deserialize_channel_update_event(mock_shard, {"id": "42"}, old_channel=None)

    def test_deserialize_channel_delete_event_with_guild_channel(self, event_factory, mock_app, mock_shard):
        mock_app.entity_factory.deserialize_channel.return_value = mock.Mock(spec=channel_models.GuildChannel)
        mock_payload = mock.Mock(app=mock_app)

        event = event_factory.deserialize_channel_delete_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_channel.assert_called_once_with(mock_payload)
        assert isinstance(event, channel_events.GuildChannelDeleteEvent)
        assert event.shard is mock_shard
        assert event.channel is mock_app.entity_factory.deserialize_channel.return_value

    def test_deserialize_channel_delete_event_with_dm_channel(self, event_factory, mock_app, mock_shard):
        mock_app.entity_factory.deserialize_channel.return_value = mock.Mock(spec=channel_models.DMChannel)
        mock_payload = object()

        with pytest.raises(NotImplementedError):
            event_factory.deserialize_channel_delete_event(mock_shard, mock_payload)

    def test_deserialize_channel_delete_event_with_unexpected_channel_type(self, event_factory, mock_app, mock_shard):
        mock_payload = object()

        with pytest.raises(TypeError, match="Expected GuildChannel or PrivateChannel but received Mock"):
            event_factory.deserialize_channel_delete_event(mock_shard, mock_payload)

    def test_deserialize_channel_pins_update_event_for_guild(self, event_factory, mock_app, mock_shard):
        mock_payload = {"channel_id": "123435", "last_pin_timestamp": None, "guild_id": "43123123"}

        event = event_factory.deserialize_channel_pins_update_event(mock_shard, mock_payload)

        assert isinstance(event, channel_events.GuildPinsUpdateEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.guild_id == 43123123
        assert event.last_pin_timestamp is None

    def test_deserialize_channel_pins_update_event_for_dm(self, event_factory, mock_app, mock_shard):
        mock_payload = {"channel_id": "123435", "last_pin_timestamp": "2020-03-15T15:23:32.686000+00:00"}

        event = event_factory.deserialize_channel_pins_update_event(mock_shard, mock_payload)

        assert isinstance(event, channel_events.DMPinsUpdateEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.last_pin_timestamp == datetime.datetime(
            2020, 3, 15, 15, 23, 32, 686000, tzinfo=datetime.timezone.utc
        )

    def test_deserialize_channel_pins_update_event_without_last_pin_timestamp(
        self, event_factory, mock_app, mock_shard
    ):
        mock_payload = {"channel_id": "123435", "guild_id": "43123123"}

        event = event_factory.deserialize_channel_pins_update_event(mock_shard, mock_payload)

        assert event.last_pin_timestamp is None

    def test_deserialize_webhook_update_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {"guild_id": "123123", "channel_id": "4393939"}

        event = event_factory.deserialize_webhook_update_event(mock_shard, mock_payload)

        assert isinstance(event, channel_events.WebhookUpdateEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.channel_id == 4393939
        assert event.guild_id == 123123

    def test_deserialize_invite_create_event(self, event_factory, mock_app, mock_shard):
        mock_payload = mock.Mock(app=mock_app)

        event = event_factory.deserialize_invite_create_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_invite_with_metadata.assert_called_once_with(mock_payload)
        assert isinstance(event, channel_events.InviteCreateEvent)
        assert event.shard is mock_shard
        assert event.invite is mock_app.entity_factory.deserialize_invite_with_metadata.return_value

    def test_deserialize_invite_delete_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {"guild_id": "1231234", "channel_id": "123123", "code": "no u"}
        mock_old_invite = object()

        event = event_factory.deserialize_invite_delete_event(mock_shard, mock_payload, old_invite=mock_old_invite)

        assert isinstance(event, channel_events.InviteDeleteEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.channel_id == 123123
        assert event.guild_id == 1231234
        assert event.code == "no u"
        assert event.old_invite is mock_old_invite

    #################
    # TYPING EVENTS #
    ##################

    def test_deserialize_typing_start_event_for_guild(self, event_factory, mock_app, mock_shard):
        mock_member_payload = object()
        mock_payload = {
            "guild_id": "123321",
            "channel_id": "48585858",
            "timestamp": 7634521233,
            "member": mock_member_payload,
        }
        mock_app.entity_factory.deserialize_member.return_value = mock.Mock(app=mock_app)

        event = event_factory.deserialize_typing_start_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_member.assert_called_once_with(mock_member_payload, guild_id=123321)
        assert isinstance(event, typing_events.GuildTypingEvent)
        assert event.shard is mock_shard
        assert event.channel_id == 48585858
        assert event.guild_id == 123321
        assert event.timestamp == datetime.datetime(2211, 12, 6, 12, 20, 33, tzinfo=datetime.timezone.utc)
        assert event.member == mock_app.entity_factory.deserialize_member.return_value

    def test_deserialize_typing_start_event_for_dm(self, event_factory, mock_app, mock_shard):
        mock_payload = {"channel_id": "534123", "timestamp": 7634521212, "user_id": "9494994"}

        event = event_factory.deserialize_typing_start_event(mock_shard, mock_payload)

        assert isinstance(event, typing_events.DMTypingEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.channel_id == 534123
        assert event.timestamp == datetime.datetime(2211, 12, 6, 12, 20, 12, tzinfo=datetime.timezone.utc)
        assert event.user_id == 9494994

    ################
    # GUILD EVENTS #
    ################

    def test_deserialize_guild_create_event(self, event_factory, mock_app, mock_shard):
        mock_payload = mock.Mock(app=mock_app)

        event = event_factory.deserialize_guild_create_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_gateway_guild.assert_called_once_with(mock_payload)
        assert isinstance(event, guild_events.GuildAvailableEvent)
        assert event.shard is mock_shard
        assert event.guild is mock_app.entity_factory.deserialize_gateway_guild.return_value.guild
        assert event.emojis is mock_app.entity_factory.deserialize_gateway_guild.return_value.emojis
        assert event.roles is mock_app.entity_factory.deserialize_gateway_guild.return_value.roles
        assert event.channels is mock_app.entity_factory.deserialize_gateway_guild.return_value.channels
        assert event.members is mock_app.entity_factory.deserialize_gateway_guild.return_value.members
        assert event.presences is mock_app.entity_factory.deserialize_gateway_guild.return_value.presences
        assert event.voice_states is mock_app.entity_factory.deserialize_gateway_guild.return_value.voice_states

    def test_deserialize_guild_update_event(self, event_factory, mock_app, mock_shard):
        mock_payload = mock.Mock(app=mock_app)
        mock_old_guild = object()

        event = event_factory.deserialize_guild_update_event(mock_shard, mock_payload, old_guild=mock_old_guild)

        mock_app.entity_factory.deserialize_gateway_guild.assert_called_once_with(mock_payload)
        assert isinstance(event, guild_events.GuildUpdateEvent)
        assert event.shard is mock_shard
        assert event.guild is mock_app.entity_factory.deserialize_gateway_guild.return_value.guild
        assert event.emojis is mock_app.entity_factory.deserialize_gateway_guild.return_value.emojis
        assert event.roles is mock_app.entity_factory.deserialize_gateway_guild.return_value.roles
        assert event.old_guild is mock_old_guild

    def test_deserialize_guild_leave_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {"id": "43123123"}

        event = event_factory.deserialize_guild_leave_event(mock_shard, mock_payload)

        assert isinstance(event, guild_events.GuildLeaveEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.guild_id == 43123123

    def test_deserialize_guild_unavailable_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {"id": "6541233"}

        event = event_factory.deserialize_guild_unavailable_event(mock_shard, mock_payload)

        assert isinstance(event, guild_events.GuildUnavailableEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.guild_id == 6541233

    def test_deserialize_guild_ban_add_event(self, event_factory, mock_app, mock_shard):
        mock_user_payload = mock.Mock(app=mock_app)
        mock_payload = {"guild_id": "4212312", "user": mock_user_payload}

        event = event_factory.deserialize_guild_ban_add_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_user.assert_called_once_with(mock_user_payload)
        assert isinstance(event, guild_events.BanCreateEvent)
        assert event.shard is mock_shard
        assert event.guild_id == 4212312
        assert event.user is mock_app.entity_factory.deserialize_user.return_value

    def test_deserialize_guild_ban_remove_event(self, event_factory, mock_app, mock_shard):
        mock_user_payload = mock.Mock(app=mock_app)
        mock_payload = {"guild_id": "9292929", "user": mock_user_payload}

        event = event_factory.deserialize_guild_ban_remove_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_user.assert_called_once_with(mock_user_payload)
        assert isinstance(event, guild_events.BanDeleteEvent)
        assert event.shard is mock_shard
        assert event.guild_id == 9292929
        assert event.user is mock_app.entity_factory.deserialize_user.return_value

    def test_deserialize_guild_emojis_update_event(self, event_factory, mock_app, mock_shard):
        mock_emoji_payload = object()
        mock_old_emojis = object()
        mock_payload = {"guild_id": "123431", "emojis": [mock_emoji_payload]}

        event = event_factory.deserialize_guild_emojis_update_event(
            mock_shard, mock_payload, old_emojis=mock_old_emojis
        )

        mock_app.entity_factory.deserialize_known_custom_emoji.assert_called_once_with(
            mock_emoji_payload, guild_id=123431
        )
        assert isinstance(event, guild_events.EmojisUpdateEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.emojis == [mock_app.entity_factory.deserialize_known_custom_emoji.return_value]
        assert event.guild_id == 123431
        assert event.old_emojis is mock_old_emojis

    def test_deserialize_integration_create_event(self, event_factory, mock_app, mock_shard):
        mock_payload = object()

        event = event_factory.deserialize_integration_create_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_integration.assert_called_once_with(mock_payload)
        assert isinstance(event, guild_events.IntegrationCreateEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.integration is mock_app.entity_factory.deserialize_integration.return_value

    def test_deserialize_integration_delete_event_with_application_id(self, event_factory, mock_app, mock_shard):
        mock_payload = {"id": "123321", "guild_id": "59595959", "application_id": "934949494"}

        event = event_factory.deserialize_integration_delete_event(mock_shard, mock_payload)

        assert isinstance(event, guild_events.IntegrationDeleteEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.id == 123321
        assert event.guild_id == 59595959
        assert event.application_id == 934949494

    def test_deserialize_integration_delete_event_without_application_id(self, event_factory, mock_app, mock_shard):
        mock_payload = {"id": "123321", "guild_id": "59595959"}

        event = event_factory.deserialize_integration_delete_event(mock_shard, mock_payload)

        assert event.application_id is None

    def test_deserialize_integration_update_event(self, event_factory, mock_app, mock_shard):
        mock_payload = object()

        event = event_factory.deserialize_integration_update_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_integration.assert_called_once_with(mock_payload)
        assert isinstance(event, guild_events.IntegrationUpdateEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.integration is mock_app.entity_factory.deserialize_integration.return_value

    def test_deserialize_presence_update_event_with_only_user_id(self, event_factory, mock_app, mock_shard):
        mock_payload = {"user": {"id": "1231312"}}
        mock_old_presence = object()
        mock_app.entity_factory.deserialize_member_presence.return_value = mock.Mock(app=mock_app)

        event = event_factory.deserialize_presence_update_event(
            mock_shard, mock_payload, old_presence=mock_old_presence
        )

        mock_app.entity_factory.deserialize_member_presence.assert_called_once_with(mock_payload)
        assert isinstance(event, guild_events.PresenceUpdateEvent)
        assert event.shard is mock_shard
        assert event.old_presence is mock_old_presence
        assert event.user is None
        assert event.presence is mock_app.entity_factory.deserialize_member_presence.return_value

    def test_deserialize_presence_update_event_with_full_user_object(self, event_factory, mock_app, mock_shard):
        mock_payload = {
            "user": {
                "id": "1231312",
                "username": "OK",
                "avatar": "NOK",
                "bot": True,
                "system": False,
                "public_flags": 42,
                "discriminator": "1231",
            }
        }
        mock_old_presence = mock.Mock(app=mock_app)

        event = event_factory.deserialize_presence_update_event(
            mock_shard, mock_payload, old_presence=mock_old_presence
        )

        mock_app.entity_factory.deserialize_member_presence.assert_called_once_with(mock_payload)
        assert isinstance(event, guild_events.PresenceUpdateEvent)
        assert event.shard is mock_shard
        assert event.old_presence is mock_old_presence

        assert isinstance(event.user, user_models.PartialUser)
        assert event.user.id == 1231312
        assert event.user.username == "OK"
        assert event.user.discriminator == "1231"
        assert event.user.avatar_hash == "NOK"
        assert event.user.is_bot is True
        assert event.user.is_system is False
        assert event.user.flags == 42

        assert event.presence is mock_app.entity_factory.deserialize_member_presence.return_value

    def test_deserialize_presence_update_event_with_partial_user_object(self, event_factory, mock_app, mock_shard):
        mock_payload = {"user": {"id": "1231312", "e": "OK"}}
        mock_old_presence = object()
        mock_app.entity_factory.deserialize_member_presence.return_value = mock.Mock(app=mock_app)

        event = event_factory.deserialize_presence_update_event(
            mock_shard, mock_payload, old_presence=mock_old_presence
        )

        mock_app.entity_factory.deserialize_member_presence.assert_called_once_with(mock_payload)
        assert isinstance(event, guild_events.PresenceUpdateEvent)
        assert event.shard is mock_shard
        assert event.old_presence is mock_old_presence

        assert isinstance(event.user, user_models.PartialUser)
        assert event.user.id == 1231312
        assert event.user.username is undefined.UNDEFINED
        assert event.user.discriminator is undefined.UNDEFINED
        assert event.user.avatar_hash is undefined.UNDEFINED
        assert event.user.is_bot is undefined.UNDEFINED
        assert event.user.is_system is undefined.UNDEFINED
        assert event.user.flags is undefined.UNDEFINED

        assert event.presence is mock_app.entity_factory.deserialize_member_presence.return_value

    ######################
    # INTERACTION EVENTS #
    ######################

    def test_deserialize_command_create_event(self, event_factory, mock_app, mock_shard):
        payload = {"id": "123"}

        result = event_factory.deserialize_command_create_event(mock_shard, payload)

        mock_app.entity_factory.deserialize_command.assert_called_once_with(payload)
        assert result.shard is mock_shard
        assert result.command is mock_app.entity_factory.deserialize_command.return_value
        assert isinstance(result, interaction_events.CommandCreateEvent)

    def test_deserialize_command_update_event(self, event_factory, mock_app, mock_shard):
        payload = {"id": "12344"}

        result = event_factory.deserialize_command_update_event(mock_shard, payload)

        mock_app.entity_factory.deserialize_command.assert_called_once_with(payload)
        assert result.shard is mock_shard
        assert result.command is mock_app.entity_factory.deserialize_command.return_value
        assert isinstance(result, interaction_events.CommandUpdateEvent)

    def test_deserialize_command_delete_event(self, event_factory, mock_app, mock_shard):
        payload = {"id": "1561232344"}

        result = event_factory.deserialize_command_delete_event(mock_shard, payload)

        mock_app.entity_factory.deserialize_command.assert_called_once_with(payload)
        assert result.shard is mock_shard
        assert result.command is mock_app.entity_factory.deserialize_command.return_value
        assert isinstance(result, interaction_events.CommandDeleteEvent)

    def test_deserialize_interaction_create_event(self, event_factory, mock_app, mock_shard):
        payload = {"id": "1561232344"}

        result = event_factory.deserialize_interaction_create_event(mock_shard, payload)

        mock_app.entity_factory.deserialize_interaction.assert_called_once_with(payload)
        assert result.shard is mock_shard
        assert result.interaction is mock_app.entity_factory.deserialize_interaction.return_value
        assert isinstance(result, interaction_events.InteractionCreateEvent)

    #################
    # MEMBER EVENTS #
    #################

    def test_deserialize_guild_member_add_event(self, event_factory, mock_app, mock_shard):
        mock_payload = mock.Mock(app=mock_app)

        event = event_factory.deserialize_guild_member_add_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_member.assert_called_once_with(mock_payload)
        assert isinstance(event, member_events.MemberCreateEvent)
        assert event.shard is mock_shard
        assert event.member is mock_app.entity_factory.deserialize_member.return_value

    def test_deserialize_guild_member_update_event(self, event_factory, mock_app, mock_shard):
        mock_payload = mock.Mock(app=mock_app)
        mock_old_member = object()

        event = event_factory.deserialize_guild_member_update_event(
            mock_shard, mock_payload, old_member=mock_old_member
        )

        mock_app.entity_factory.deserialize_member.assert_called_once_with(mock_payload)
        assert isinstance(event, member_events.MemberUpdateEvent)
        assert event.shard is mock_shard
        assert event.member is mock_app.entity_factory.deserialize_member.return_value
        assert event.old_member is mock_old_member

    def test_deserialize_guild_member_remove_event(self, event_factory, mock_app, mock_shard):
        mock_user_payload = mock.Mock(app=mock_app)
        mock_old_member = object()
        mock_payload = {"guild_id": "43123", "user": mock_user_payload}

        event = event_factory.deserialize_guild_member_remove_event(
            mock_shard, mock_payload, old_member=mock_old_member
        )

        mock_app.entity_factory.deserialize_user.assert_called_once_with(mock_user_payload)
        assert isinstance(event, member_events.MemberDeleteEvent)
        assert event.shard is mock_shard
        assert event.guild_id == 43123
        assert event.user is mock_app.entity_factory.deserialize_user.return_value
        assert event.old_member is mock_old_member

    ###############
    # ROLE EVENTS #
    ###############

    def test_deserialize_guild_role_create_event(self, event_factory, mock_app, mock_shard):
        mock_role_payload = mock.Mock(app=mock_app)
        mock_payload = {"role": mock_role_payload, "guild_id": "45123"}

        event = event_factory.deserialize_guild_role_create_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_role.assert_called_once_with(mock_role_payload, guild_id=45123)
        assert isinstance(event, role_events.RoleCreateEvent)
        assert event.shard is mock_shard
        assert event.role is mock_app.entity_factory.deserialize_role.return_value

    def test_deserialize_guild_role_update_event(self, event_factory, mock_app, mock_shard):
        mock_role_payload = mock.Mock(app=mock_app)
        mock_old_role = object()
        mock_payload = {"role": mock_role_payload, "guild_id": "45123"}

        event = event_factory.deserialize_guild_role_update_event(mock_shard, mock_payload, old_role=mock_old_role)

        mock_app.entity_factory.deserialize_role.assert_called_once_with(mock_role_payload, guild_id=45123)
        assert isinstance(event, role_events.RoleUpdateEvent)
        assert event.shard is mock_shard
        assert event.role is mock_app.entity_factory.deserialize_role.return_value
        assert event.old_role is mock_old_role

    def test_deserialize_guild_role_delete_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {"guild_id": "432123", "role_id": "848484"}
        mock_old_role = object()

        event = event_factory.deserialize_guild_role_delete_event(mock_shard, mock_payload, old_role=mock_old_role)

        assert isinstance(event, role_events.RoleDeleteEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.guild_id == 432123
        assert event.role_id == 848484
        assert event.old_role is mock_old_role

    ###################
    # LIFETIME EVENTS #
    ###################

    def test_deserialize_starting_event(self, event_factory, mock_app):
        event = event_factory.deserialize_starting_event()

        assert isinstance(event, lifetime_events.StartingEvent)
        assert event.app is mock_app

    def test_deserialize_started_event(self, event_factory, mock_app):
        event = event_factory.deserialize_started_event()

        assert isinstance(event, lifetime_events.StartedEvent)
        assert event.app is mock_app

    def test_deserialize_stopping_event(self, event_factory, mock_app):
        event = event_factory.deserialize_stopping_event()

        assert isinstance(event, lifetime_events.StoppingEvent)
        assert event.app is mock_app

    def test_deserialize_stopped_event(self, event_factory, mock_app):
        event = event_factory.deserialize_stopped_event()

        assert isinstance(event, lifetime_events.StoppedEvent)
        assert event.app is mock_app

    ##################
    # MESSAGE EVENTS #
    ##################

    def test_deserialize_message_create_event_in_guild(self, event_factory, mock_app, mock_shard):
        mock_payload = mock.Mock(app=mock_app)
        mock_app.entity_factory.deserialize_message.return_value = mock.Mock(guild_id=123321)

        event = event_factory.deserialize_message_create_event(mock_shard, mock_payload)

        assert isinstance(event, message_events.GuildMessageCreateEvent)
        assert event.shard is mock_shard
        assert event.message is mock_app.entity_factory.deserialize_message.return_value

    def test_deserialize_message_create_event_in_dm(self, event_factory, mock_app, mock_shard):
        mock_payload = mock.Mock(app=mock_app)
        mock_app.entity_factory.deserialize_message.return_value = mock.Mock(guild_id=None)

        event = event_factory.deserialize_message_create_event(mock_shard, mock_payload)

        assert isinstance(event, message_events.DMMessageCreateEvent)
        assert event.shard is mock_shard
        assert event.message is mock_app.entity_factory.deserialize_message.return_value

    def test_deserialize_message_update_event_in_guild(self, event_factory, mock_app, mock_shard):
        mock_payload = mock.Mock(app=mock_app)
        mock_old_message = object()
        mock_app.entity_factory.deserialize_partial_message.return_value = mock.Mock(guild_id=123321, app=mock_app)

        event = event_factory.deserialize_message_update_event(mock_shard, mock_payload, old_message=mock_old_message)

        assert isinstance(event, message_events.GuildMessageUpdateEvent)
        assert event.shard is mock_shard
        assert event.message is mock_app.entity_factory.deserialize_partial_message.return_value
        assert event.old_message is mock_old_message

    def test_deserialize_message_update_event_in_dm(self, event_factory, mock_app, mock_shard):
        mock_payload = mock.Mock(app=mock_app)
        mock_old_message = object()
        mock_app.entity_factory.deserialize_partial_message.return_value = mock.Mock(guild_id=None)

        event = event_factory.deserialize_message_update_event(mock_shard, mock_payload, old_message=mock_old_message)

        assert isinstance(event, message_events.DMMessageUpdateEvent)
        assert event.shard is mock_shard
        assert event.message is mock_app.entity_factory.deserialize_partial_message.return_value
        assert event.old_message is mock_old_message

    def test_deserialize_message_delete_event_in_guild(self, event_factory, mock_app, mock_shard):
        mock_payload = {"id": "5412", "channel_id": "541123", "guild_id": "9494949"}

        event = event_factory.deserialize_message_delete_event(mock_shard, mock_payload)

        assert isinstance(event, message_events.GuildMessageDeleteEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.channel_id == 541123
        assert event.message_ids == {5412}
        assert event.is_bulk is False
        assert event.guild_id == 9494949

    def test_deserialize_message_delete_event_in_dm(self, event_factory, mock_app, mock_shard):
        mock_payload = {"id": "5412", "channel_id": "541123"}

        event = event_factory.deserialize_message_delete_event(mock_shard, mock_payload)

        assert isinstance(event, message_events.DMMessageDeleteEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.channel_id == 541123
        assert event.message_ids == {5412}
        assert event.is_bulk is False

    def test_deserialize_message_delete_bulk_event_in_guild(self, event_factory, mock_app, mock_shard):
        mock_payload = {"ids": ["6523423", "345123"], "channel_id": "564123", "guild_id": "4394949"}

        event = event_factory.deserialize_message_delete_bulk_event(mock_shard, mock_payload)

        assert isinstance(event, message_events.GuildMessageDeleteEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.channel_id == 564123
        assert event.message_ids == {6523423, 345123}
        assert event.is_bulk is True
        assert event.guild_id == 4394949

    def test_deserialize_message_delete_bulk_event_in_dm(self, event_factory, mock_app, mock_shard):
        mock_payload = {"ids": ["6523423", "345123"], "channel_id": "564123"}

        event = event_factory.deserialize_message_delete_bulk_event(mock_shard, mock_payload)

        assert isinstance(event, message_events.DMMessageDeleteEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.channel_id == 564123
        assert event.message_ids == {6523423, 345123}
        assert event.is_bulk is True

    ###################
    # REACTION EVENTS #
    ###################

    def test_deserialize_message_reaction_add_event_in_guild(self, event_factory, mock_shard, mock_app):
        mock_member_payload = mock.Mock(app=mock_app)
        mock_payload = {
            "member": mock_member_payload,
            "channel_id": "34123",
            "message_id": "43123123",
            "guild_id": "43949494",
            "emoji": {"id": "123312", "name": "okok", "animated": True},
        }

        event = event_factory.deserialize_message_reaction_add_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_member.assert_called_once_with(mock_member_payload, guild_id=43949494)
        assert isinstance(event, reaction_events.GuildReactionAddEvent)
        assert event.shard is mock_shard
        assert event.channel_id == 34123
        assert event.message_id == 43123123
        assert event.member is mock_app.entity_factory.deserialize_member.return_value
        assert not isinstance(event.emoji_name, emoji_models.UnicodeEmoji)
        assert event.emoji_name == "okok"
        assert event.emoji_id == 123312
        assert event.is_animated is True

    def test_deserialize_message_reaction_add_event_in_guild_when_partial_custom(
        self, event_factory, mock_shard, mock_app
    ):
        mock_member_payload = object()
        mock_payload = {
            "member": mock_member_payload,
            "channel_id": "34123",
            "message_id": "43123123",
            "guild_id": "43949494",
            "emoji": {"id": "123312", "name": None},
        }

        event = event_factory.deserialize_message_reaction_add_event(mock_shard, mock_payload)

        assert event.is_animated is False
        assert event.emoji_id == 123312
        assert event.emoji_name is None

    def test_deserialize_message_reaction_add_event_in_guild_when_unicode(self, event_factory, mock_shard, mock_app):
        mock_member_payload = object()
        mock_payload = {
            "member": mock_member_payload,
            "channel_id": "34123",
            "message_id": "43123123",
            "guild_id": "43949494",
            "emoji": {"name": "hi", "id": None},
        }

        event = event_factory.deserialize_message_reaction_add_event(mock_shard, mock_payload)

        assert isinstance(event.emoji_name, emoji_models.UnicodeEmoji)
        assert event.emoji_name == "hi"
        assert event.emoji_id is None
        assert event.is_animated is False

    def test_deserialize_message_reaction_add_event_in_dm(self, event_factory, mock_shard, mock_app):
        mock_payload = {
            "channel_id": "34123",
            "message_id": "43123123",
            "user_id": "43949494",
            "emoji": {"id": "3293939", "name": "vohio", "animated": True},
        }

        event = event_factory.deserialize_message_reaction_add_event(mock_shard, mock_payload)

        assert isinstance(event, reaction_events.DMReactionAddEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.channel_id == 34123
        assert event.message_id == 43123123
        assert event.user_id == 43949494
        assert not isinstance(event.emoji_name, emoji_models.UnicodeEmoji)
        assert event.emoji_name == "vohio"
        assert event.emoji_id == 3293939
        assert event.is_animated is True

    def test_deserialize_message_reaction_add_event_in_dm_when_partial_custom(
        self, event_factory, mock_shard, mock_app
    ):
        mock_payload = {
            "channel_id": "34123",
            "message_id": "43123123",
            "user_id": "43949494",
            "emoji": {"id": "3293939", "name": None},
        }

        event = event_factory.deserialize_message_reaction_add_event(mock_shard, mock_payload)

        assert event.emoji_name is None
        assert event.emoji_id == 3293939
        assert event.is_animated is False

    def test_deserialize_message_reaction_add_event_in_dm_when_unicode(self, event_factory, mock_shard, mock_app):
        mock_payload = {
            "channel_id": "34123",
            "message_id": "43123123",
            "user_id": "43949494",
            "emoji": {"name": "bye"},
        }

        event = event_factory.deserialize_message_reaction_add_event(mock_shard, mock_payload)

        assert isinstance(event, reaction_events.DMReactionAddEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.channel_id == 34123
        assert event.message_id == 43123123
        assert event.user_id == 43949494
        assert isinstance(event.emoji_name, emoji_models.UnicodeEmoji)
        assert event.emoji_name == "bye"
        assert event.emoji_id is None
        assert event.is_animated is False

    def test_deserialize_message_reaction_remove_event_in_guild(self, event_factory, mock_app, mock_shard):
        mock_payload = {
            "user_id": "43123",
            "channel_id": "484848",
            "message_id": "43234",
            "guild_id": "383838",
            "emoji": {"id": "123432", "name": "fififiif"},
        }

        event = event_factory.deserialize_message_reaction_remove_event(mock_shard, mock_payload)

        assert isinstance(event, reaction_events.GuildReactionDeleteEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.user_id == 43123
        assert event.channel_id == 484848
        assert event.message_id == 43234
        assert event.guild_id == 383838
        assert event.emoji_id == 123432
        assert event.emoji_name == "fififiif"
        assert not isinstance(event.emoji_name, emoji_models.UnicodeEmoji)

    def test_deserialize_message_reaction_remove_event_in_guild_with_unicode_emoji(
        self, event_factory, mock_app, mock_shard
    ):
        mock_payload = {
            "user_id": "43123",
            "channel_id": "484848",
            "message_id": "43234",
            "guild_id": "383838",
            "emoji": {"name": "o"},
        }

        event = event_factory.deserialize_message_reaction_remove_event(mock_shard, mock_payload)

        assert isinstance(event, reaction_events.GuildReactionDeleteEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.user_id == 43123
        assert event.channel_id == 484848
        assert event.message_id == 43234
        assert event.guild_id == 383838
        assert event.emoji_id is None
        assert event.emoji_name == "o"
        assert isinstance(event.emoji_name, emoji_models.UnicodeEmoji)

    def test_deserialize_message_reaction_remove_event_in_dm(self, event_factory, mock_app, mock_shard):
        mock_payload = {
            "user_id": "43123",
            "channel_id": "484848",
            "message_id": "43234",
            "emoji": {"id": "123123", "name": "okok"},
        }

        event = event_factory.deserialize_message_reaction_remove_event(mock_shard, mock_payload)

        assert isinstance(event, reaction_events.DMReactionDeleteEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.user_id == 43123
        assert event.channel_id == 484848
        assert event.message_id == 43234
        assert not isinstance(event.emoji_name, emoji_models.UnicodeEmoji)
        assert event.emoji_name == "okok"
        assert event.emoji_id == 123123

    def test_deserialize_message_reaction_remove_event_in_dm_with_unicode_emoji(
        self, event_factory, mock_app, mock_shard
    ):
        mock_payload = {"user_id": "43123", "channel_id": "484848", "message_id": "43234", "emoji": {"name": "wwww"}}

        event = event_factory.deserialize_message_reaction_remove_event(mock_shard, mock_payload)

        assert isinstance(event, reaction_events.DMReactionDeleteEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.user_id == 43123
        assert event.channel_id == 484848
        assert event.message_id == 43234
        assert isinstance(event.emoji_name, emoji_models.UnicodeEmoji)
        assert event.emoji_name == "wwww"
        assert event.emoji_id is None

    def test_deserialize_message_reaction_remove_all_event_in_guild(self, event_factory, mock_app, mock_shard):
        mock_payload = {"channel_id": "312312", "message_id": "34323", "guild_id": "393939"}

        event = event_factory.deserialize_message_reaction_remove_all_event(mock_shard, mock_payload)

        assert isinstance(event, reaction_events.GuildReactionDeleteAllEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.channel_id == 312312
        assert event.message_id == 34323
        assert event.guild_id == 393939

    def test_deserialize_message_reaction_remove_all_event_in_dm(self, event_factory, mock_app, mock_shard):
        mock_payload = {"channel_id": "312312", "message_id": "34323"}

        event = event_factory.deserialize_message_reaction_remove_all_event(mock_shard, mock_payload)

        assert isinstance(event, reaction_events.DMReactionDeleteAllEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.channel_id == 312312
        assert event.message_id == 34323

    def test_deserialize_message_reaction_remove_emoji_event_in_guild(self, event_factory, mock_app, mock_shard):
        mock_payload = {
            "channel_id": "123123",
            "guild_id": "423412",
            "message_id": "99999",
            "emoji": {"id": "3123123", "name": "okokok"},
        }

        event = event_factory.deserialize_message_reaction_remove_emoji_event(mock_shard, mock_payload)

        assert isinstance(event, reaction_events.GuildReactionDeleteEmojiEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.channel_id == 123123
        assert event.guild_id == 423412
        assert event.message_id == 99999
        assert event.emoji_id == 3123123
        assert event.emoji_name == "okokok"
        assert not isinstance(event.emoji_name, emoji_models.UnicodeEmoji)

    def test_deserialize_message_reaction_remove_emoji_event_in_guild_with_unicode_emoji(
        self, event_factory, mock_app, mock_shard
    ):
        mock_payload = {
            "channel_id": "123123",
            "guild_id": "423412",
            "message_id": "99999",
            "emoji": {"name": "okokok"},
        }

        event = event_factory.deserialize_message_reaction_remove_emoji_event(mock_shard, mock_payload)

        assert event.emoji_name == "okokok"
        assert isinstance(event.emoji_name, emoji_models.UnicodeEmoji)

    def test_deserialize_message_reaction_remove_emoji_event_in_dm(self, event_factory, mock_app, mock_shard):
        mock_payload = {"channel_id": "123123", "message_id": "99999", "emoji": {"id": "123321", "name": "nom"}}

        event = event_factory.deserialize_message_reaction_remove_emoji_event(mock_shard, mock_payload)

        assert isinstance(event, reaction_events.DMReactionDeleteEmojiEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.channel_id == 123123
        assert event.message_id == 99999
        assert event.emoji_id == 123321
        assert event.emoji_name == "nom"
        assert not isinstance(event.emoji_name, emoji_models.UnicodeEmoji)

    def test_deserialize_message_reaction_remove_emoji_event_in_dm_with_unicode_emoji(
        self, event_factory, mock_app, mock_shard
    ):
        mock_payload = {"channel_id": "123123", "message_id": "99999", "emoji": {"name": "gg"}}

        event = event_factory.deserialize_message_reaction_remove_emoji_event(mock_shard, mock_payload)

        assert isinstance(event, reaction_events.DMReactionDeleteEmojiEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.channel_id == 123123
        assert event.message_id == 99999
        assert event.emoji_id is None
        assert event.emoji_name == "gg"
        assert isinstance(event.emoji_name, emoji_models.UnicodeEmoji)

    ################
    # SHARD EVENTS #
    ################

    def test_deserialize_shard_payload_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {"id": "123123"}

        event = event_factory.deserialize_shard_payload_event(mock_shard, mock_payload, name="ooga booga")

        assert event.app is mock_app
        assert event.name == "ooga booga"
        assert event.payload == mock_payload
        assert event.shard is mock_shard

    def test_deserialize_ready_event(self, event_factory, mock_app, mock_shard):
        mock_user_payload = object()
        mock_payload = {
            "v": "69",
            "user": mock_user_payload,
            "guilds": [{"id": "432123"}, {"id": "949494"}],
            "session_id": "kjsdjiodsaiosad",
            "application": {"id": "4123212", "flags": "4949494"},
        }
        mock_app.entity_factory.deserialize_my_user.return_value = mock.Mock(app=mock_app)

        event = event_factory.deserialize_ready_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_my_user.assert_called_once_with(mock_user_payload)
        assert isinstance(event, shard_events.ShardReadyEvent)
        assert event.shard is mock_shard
        assert event.actual_gateway_version == 69
        assert event.my_user is mock_app.entity_factory.deserialize_my_user.return_value
        assert event.unavailable_guilds == [432123, 949494]
        assert event.session_id == "kjsdjiodsaiosad"
        assert event.application_id == 4123212
        assert event.application_flags == 4949494

    def test_deserialize_connected_event(self, event_factory, mock_app, mock_shard):
        event = event_factory.deserialize_connected_event(mock_shard)

        assert isinstance(event, shard_events.ShardConnectedEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard

    def test_deserialize_disconnected_event(self, event_factory, mock_app, mock_shard):
        event = event_factory.deserialize_disconnected_event(mock_shard)

        assert isinstance(event, shard_events.ShardDisconnectedEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard

    def test_deserialize_resumed_event(self, event_factory, mock_app, mock_shard):
        event = event_factory.deserialize_resumed_event(mock_shard)

        assert isinstance(event, shard_events.ShardResumedEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard

    def test_deserialize_guild_member_chunk_event_with_optional_fields(self, event_factory, mock_app, mock_shard):
        mock_member_payload = {"user": {"id": "4222222"}}
        mock_presence_payload = {"user": {"id": "43123123"}}
        mock_payload = {
            "guild_id": "123432123",
            "members": [mock_member_payload],
            "chunk_index": 3,
            "chunk_count": 54,
            "not_found": ["34212312312", 323123123],
            "presences": [mock_presence_payload],
            "nonce": "OKOKOKOK",
        }

        event = event_factory.deserialize_guild_member_chunk_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_member.assert_called_once_with(mock_member_payload, guild_id=123432123)
        mock_app.entity_factory.deserialize_member_presence.assert_called_once_with(
            mock_presence_payload, guild_id=123432123
        )
        assert isinstance(event, shard_events.MemberChunkEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.guild_id == 123432123
        assert event.members == {4222222: mock_app.entity_factory.deserialize_member.return_value}
        assert event.chunk_count == 54
        assert event.chunk_index == 3
        assert event.not_found == [34212312312, 323123123]
        assert event.presences == {43123123: mock_app.entity_factory.deserialize_member_presence.return_value}
        assert event.nonce == "OKOKOKOK"

    def test_deserialize_guild_member_chunk_event_without_optional_fields(self, event_factory, mock_app, mock_shard):
        mock_member_payload = {"user": {"id": "4222222"}}
        mock_payload = {
            "guild_id": "123432123",
            "members": [mock_member_payload],
            "chunk_index": 3,
            "chunk_count": 54,
        }

        event = event_factory.deserialize_guild_member_chunk_event(mock_shard, mock_payload)

        assert event.not_found == []
        assert event.presences == {}
        assert event.nonce is None

    ###############
    # USER EVENTS #
    ###############

    def test_deserialize_own_user_update_event(self, event_factory, mock_app, mock_shard):
        mock_payload = mock.Mock(app=mock_app)
        mock_old_user = object()
        mock_app.entity_factory.deserialize_my_user.return_value = mock.Mock(app=mock_app)

        event = event_factory.deserialize_own_user_update_event(mock_shard, mock_payload, old_user=mock_old_user)

        mock_app.entity_factory.deserialize_my_user.assert_called_once_with(mock_payload)
        assert isinstance(event, user_events.OwnUserUpdateEvent)
        assert event.shard is mock_shard
        assert event.user is mock_app.entity_factory.deserialize_my_user.return_value
        assert event.old_user is mock_old_user

    ################
    # VOICE EVENTS #
    ################

    def test_deserialize_voice_state_update_event(self, event_factory, mock_app, mock_shard):
        mock_payload = object()
        mock_old_voice_state = object()
        mock_app.entity_factory.deserialize_voice_state.return_value = mock.Mock(app=mock_app)

        event = event_factory.deserialize_voice_state_update_event(
            mock_shard, mock_payload, old_state=mock_old_voice_state
        )

        mock_app.entity_factory.deserialize_voice_state.assert_called_once_with(mock_payload)
        assert isinstance(event, voice_events.VoiceStateUpdateEvent)
        assert event.shard is mock_shard
        assert event.state is mock_app.entity_factory.deserialize_voice_state.return_value
        assert event.old_state is mock_old_voice_state

    def test_deserialize_voice_server_update_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {"token": "okokok", "guild_id": "3122312", "endpoint": "httppppppp"}

        event = event_factory.deserialize_voice_server_update_event(mock_shard, mock_payload)

        assert isinstance(event, voice_events.VoiceServerUpdateEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.token == "okokok"
        assert event.guild_id == 3122312
        assert event.raw_endpoint == "httppppppp"
