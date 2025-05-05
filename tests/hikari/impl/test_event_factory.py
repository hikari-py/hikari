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

import datetime
import typing

import mock
import pytest

from hikari import auto_mod
from hikari import channels as channel_models
from hikari import emojis as emoji_models
from hikari import traits
from hikari import undefined
from hikari import users as user_models
from hikari.api import shard
from hikari.events import application_events
from hikari.events import auto_mod_events
from hikari.events import channel_events
from hikari.events import guild_events
from hikari.events import interaction_events
from hikari.events import lifetime_events
from hikari.events import member_events
from hikari.events import message_events
from hikari.events import monetization_events
from hikari.events import poll_events
from hikari.events import reaction_events
from hikari.events import role_events
from hikari.events import scheduled_events
from hikari.events import shard_events
from hikari.events import stage_events
from hikari.events import typing_events
from hikari.events import user_events
from hikari.events import voice_events
from hikari.impl import event_factory as event_factory_
from hikari.interactions import base_interactions


class TestEventFactoryImpl:
    @pytest.fixture
    def mock_app(self):
        return mock.Mock(traits.RESTAware)

    @pytest.fixture
    def mock_shard(self):
        return mock.Mock(shard.GatewayShard)

    @pytest.fixture
    def event_factory(self, mock_app):
        return event_factory_.EventFactoryImpl(mock_app)

    ######################
    # APPLICATION EVENTS #
    ######################

    def test_deserialize_application_command_permission_update_event(self, event_factory, mock_app, mock_shard):
        mock_payload = object()

        event = event_factory.deserialize_application_command_permission_update_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_guild_command_permissions.assert_called_once_with(mock_payload)
        assert isinstance(event, application_events.ApplicationCommandPermissionsUpdateEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.permissions is mock_app.entity_factory.deserialize_guild_command_permissions.return_value

    ##################
    # CHANNEL EVENTS #
    ##################

    def test_deserialize_guild_channel_create_event(self, event_factory, mock_app, mock_shard):
        mock_app.entity_factory.deserialize_channel.return_value = mock.Mock(
            spec=channel_models.PermissibleGuildChannel
        )
        mock_payload = mock.Mock(app=mock_app)

        event = event_factory.deserialize_guild_channel_create_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_channel.assert_called_once_with(mock_payload)
        assert isinstance(event, channel_events.GuildChannelCreateEvent)
        assert event.shard is mock_shard
        assert event.channel is mock_app.entity_factory.deserialize_channel.return_value

    def test_deserialize_guild_channel_update_event(self, event_factory, mock_app, mock_shard):
        mock_app.entity_factory.deserialize_channel.return_value = mock.Mock(
            spec=channel_models.PermissibleGuildChannel
        )
        mock_old_channel = object()
        mock_payload = object()

        event = event_factory.deserialize_guild_channel_update_event(
            mock_shard, mock_payload, old_channel=mock_old_channel
        )

        mock_app.entity_factory.deserialize_channel.assert_called_once_with(mock_payload)
        assert isinstance(event, channel_events.GuildChannelUpdateEvent)
        assert event.shard is mock_shard
        assert event.channel is mock_app.entity_factory.deserialize_channel.return_value
        assert event.old_channel is mock_old_channel

    def test_deserialize_guild_channel_delete_event(self, event_factory, mock_app, mock_shard):
        mock_app.entity_factory.deserialize_channel.return_value = mock.Mock(
            spec=channel_models.PermissibleGuildChannel
        )
        mock_payload = mock.Mock(app=mock_app)

        event = event_factory.deserialize_guild_channel_delete_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_channel.assert_called_once_with(mock_payload)
        assert isinstance(event, channel_events.GuildChannelDeleteEvent)
        assert event.shard is mock_shard
        assert event.channel is mock_app.entity_factory.deserialize_channel.return_value

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

    def test_deserialize_guild_thread_create_event(
        self, event_factory: event_factory_.EventFactoryImpl, mock_app: mock.Mock, mock_shard: shard.GatewayShard
    ):
        mock_payload = mock.Mock()

        event = event_factory.deserialize_guild_thread_create_event(mock_shard, mock_payload)

        assert event.shard is mock_shard
        assert event.thread is mock_app.entity_factory.deserialize_guild_thread.return_value
        mock_app.entity_factory.deserialize_guild_thread.assert_called_once_with(mock_payload)
        assert isinstance(event, channel_events.GuildThreadCreateEvent)

    def test_deserialize_guild_thread_access_event(
        self, event_factory: event_factory_.EventFactoryImpl, mock_app: mock.Mock, mock_shard: shard.GatewayShard
    ):
        mock_payload = mock.Mock()

        event = event_factory.deserialize_guild_thread_access_event(mock_shard, mock_payload)

        assert event.shard is mock_shard
        assert event.thread is mock_app.entity_factory.deserialize_guild_thread.return_value
        mock_app.entity_factory.deserialize_guild_thread.assert_called_once_with(mock_payload)
        assert isinstance(event, channel_events.GuildThreadAccessEvent)

    def test_deserialize_guild_thread_update_event(
        self, event_factory: event_factory_.EventFactoryImpl, mock_app: mock.Mock, mock_shard: shard.GatewayShard
    ):
        mock_old_thread = object()
        mock_payload = mock.Mock()

        event = event_factory.deserialize_guild_thread_update_event(
            mock_shard, mock_payload, old_thread=mock_old_thread
        )

        mock_app.entity_factory.deserialize_guild_thread.assert_called_once_with(mock_payload)
        assert isinstance(event, channel_events.GuildThreadUpdateEvent)
        assert event.shard is mock_shard
        assert event.thread is mock_app.entity_factory.deserialize_guild_thread.return_value
        assert event.old_thread is mock_old_thread

    def test_deserialize_guild_thread_delete_event(
        self, event_factory: event_factory_.EventFactoryImpl, mock_app: mock.Mock, mock_shard: shard.GatewayShard
    ):
        mock_payload = {"id": "12332123321", "guild_id": "54544234342", "parent_id": "9494949", "type": 11}

        event = event_factory.deserialize_guild_thread_delete_event(mock_shard, mock_payload)

        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.thread_id == 12332123321
        assert event.guild_id == 54544234342
        assert event.parent_id == 9494949
        assert event.type is channel_models.ChannelType.GUILD_PUBLIC_THREAD
        assert isinstance(event, channel_events.GuildThreadDeleteEvent)

    def test_deserialize_thread_members_update_event(
        self, event_factory: event_factory_.EventFactoryImpl, mock_app: mock.Mock, mock_shard: shard.GatewayShard
    ):
        mock_thread_member_payload = {"id": "393939393", "user_id": "3933993"}
        mock_other_thread_member_payload = {"id": "393994954", "user_id": "123321123"}
        mock_thread_member = mock.Mock(user_id=123321123)
        mock_other_thread_member = mock.Mock(user_id=5454234)
        mock_app.entity_factory.deserialize_thread_member.side_effect = [mock_thread_member, mock_other_thread_member]
        payload = {
            "id": "92929929",
            "guild_id": "92929292",
            "member_count": "32",
            "added_members": [mock_thread_member_payload, mock_other_thread_member_payload],
            "removed_member_ids": ["4949534", "123321", "54234"],
        }

        event = event_factory.deserialize_thread_members_update_event(mock_shard, payload)

        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.thread_id == 92929929
        assert event.guild_id == 92929292
        assert event.added_members == {123321123: mock_thread_member, 5454234: mock_other_thread_member}
        assert event.removed_member_ids == [4949534, 123321, 54234]
        assert event.guild_members == {}
        assert event.guild_presences == {}
        mock_app.entity_factory.deserialize_thread_member.assert_has_calls(
            [mock.call(mock_thread_member_payload), mock.call(mock_other_thread_member_payload)]
        )

    def test_deserialize_thread_members_update_event_when_presences_and_real_members(
        self, event_factory: event_factory_.EventFactoryImpl, mock_app: mock.Mock, mock_shard: shard.GatewayShard
    ):
        mock_presence_payload = mock.Mock()
        mock_other_presence_payload = mock.Mock()
        mock_guild_member_payload = mock.Mock()
        mock_other_guild_member_payload = mock.Mock()
        mock_thread_member_payload = {
            "id": "393939393",
            "user_id": "3933993",
            "member": mock_guild_member_payload,
            "presence": mock_presence_payload,
        }
        mock_other_thread_member_payload = {
            "id": "393994954",
            "user_id": "123321123",
            "member": mock_other_guild_member_payload,
            "presence": mock_other_presence_payload,
        }
        mock_thread_member = mock.Mock(user_id=3933993)
        mock_other_thread_member = mock.Mock(user_id=123321123)
        mock_presence = mock.Mock()
        mock_other_presence = mock.Mock()
        mock_guild_member = mock.Mock()
        mock_other_guild_member = mock.Mock()
        mock_app.entity_factory.deserialize_thread_member.side_effect = [mock_thread_member, mock_other_thread_member]
        mock_app.entity_factory.deserialize_member.side_effect = [mock_guild_member, mock_other_guild_member]
        mock_app.entity_factory.deserialize_member_presence.side_effect = [mock_presence, mock_other_presence]
        payload = {
            "id": "92929929",
            "guild_id": "123321123123",
            "member_count": "32",
            "added_members": [mock_thread_member_payload, mock_other_thread_member_payload],
            "removed_member_ids": ["4949534", "123321", "54234"],
        }

        event = event_factory.deserialize_thread_members_update_event(mock_shard, payload)

        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.thread_id == 92929929
        assert event.guild_id == 123321123123
        assert event.added_members == {3933993: mock_thread_member, 123321123: mock_other_thread_member}
        assert event.removed_member_ids == [4949534, 123321, 54234]
        assert event.guild_members == {3933993: mock_guild_member, 123321123: mock_other_guild_member}
        assert event.guild_presences == {3933993: mock_presence, 123321123: mock_other_presence}
        mock_app.entity_factory.deserialize_thread_member.assert_has_calls(
            [mock.call(mock_thread_member_payload), mock.call(mock_other_thread_member_payload)]
        )
        mock_app.entity_factory.deserialize_member.assert_has_calls(
            [
                mock.call(mock_guild_member_payload, guild_id=123321123123),
                mock.call(mock_other_guild_member_payload, guild_id=123321123123),
            ]
        )
        mock_app.entity_factory.deserialize_member_presence.assert_has_calls(
            [
                mock.call(mock_presence_payload, guild_id=123321123123),
                mock.call(mock_other_presence_payload, guild_id=123321123123),
            ]
        )

    def test_deserialize_thread_members_update_event_partial(
        self, event_factory: event_factory_.EventFactoryImpl, mock_shard: shard.GatewayShard
    ):
        payload = {"id": "92929929", "guild_id": "92929292", "member_count": "32"}

        event = event_factory.deserialize_thread_members_update_event(mock_shard, payload)

        assert event.added_members == {}
        assert event.removed_member_ids == []
        assert event.guild_members == {}
        assert event.guild_presences == {}

    def test_deserialize_thread_list_sync_event(
        self, event_factory: event_factory_.EventFactoryImpl, mock_app: mock.Mock, mock_shard: shard.GatewayShard
    ):
        mock_thread_payload = {"id": "342123123", "name": "nyaa"}
        mock_other_thread_payload = {"id": "5454123123", "name": "meow"}
        mock_not_in_thread_payload = {"id": "94949494", "name": "123123123"}
        mokc_member_payload = {"id": "342123123", "user_id": "9349393939"}
        mock_other_member_payload = {"id": "5454123123", "user_id": "34949499494"}
        mock_thread = mock.Mock(id=342123123)
        mock_other_thread = mock.Mock(id=5454123123)
        mock_not_in_thread = mock.Mock(id=94949494)
        mock_member = mock.Mock(thread_id=342123123)
        mock_other_member = mock.Mock(thread_id=5454123123)
        mock_app.entity_factory.deserialize_guild_thread.side_effect = [
            mock_thread,
            mock_not_in_thread,
            mock_other_thread,
        ]
        mock_app.entity_factory.deserialize_thread_member.side_effect = [mock_member, mock_other_member]
        mock_payload = {
            "guild_id": "43123123",
            "channel_ids": ["54123", "123431", "43939", "12343123"],
            "threads": [mock_thread_payload, mock_not_in_thread_payload, mock_other_thread_payload],
            "members": [mock_other_member_payload, mokc_member_payload],
        }

        event = event_factory.deserialize_thread_list_sync_event(mock_shard, mock_payload)

        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.guild_id == 43123123
        assert event.channel_ids == [54123, 123431, 43939, 12343123]
        assert event.threads == {342123123: mock_thread, 5454123123: mock_other_thread, 94949494: mock_not_in_thread}
        mock_app.entity_factory.deserialize_thread_member.assert_has_calls(
            [mock.call(mock_other_member_payload), mock.call(mokc_member_payload)]
        )
        mock_app.entity_factory.deserialize_guild_thread.assert_has_calls(
            [
                mock.call(mock_thread_payload, guild_id=43123123, member=mock_member),
                mock.call(mock_not_in_thread_payload, guild_id=43123123, member=None),
                mock.call(mock_other_thread_payload, guild_id=43123123, member=mock_other_member),
            ]
        )

    def test_deserialize_thread_list_sync_event_when_not_channel_ids(
        self, event_factory: event_factory_.EventFactoryImpl, mock_app: mock.Mock, mock_shard: shard.GatewayShard
    ):
        mock_payload = {"guild_id": "123321", "threads": [], "members": []}

        event = event_factory.deserialize_thread_list_sync_event(mock_shard, mock_payload)

        assert event.channel_ids is None

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

    def test_deserialize_guild_available_event(self, event_factory, mock_app, mock_shard):
        mock_payload = mock.Mock(app=mock_app)

        event = event_factory.deserialize_guild_available_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_gateway_guild.assert_called_once_with(
            mock_payload, user_id=mock_shard.get_user_id.return_value
        )
        assert isinstance(event, guild_events.GuildAvailableEvent)
        assert event.shard is mock_shard
        guild_definition = mock_app.entity_factory.deserialize_gateway_guild.return_value
        assert event.guild is guild_definition.guild.return_value
        assert event.emojis is guild_definition.emojis.return_value
        assert event.stickers is guild_definition.stickers.return_value
        assert event.roles is guild_definition.roles.return_value
        assert event.channels is guild_definition.channels.return_value
        assert event.members is guild_definition.members.return_value
        assert event.presences is guild_definition.presences.return_value
        assert event.voice_states is guild_definition.voice_states.return_value
        guild_definition.guild.assert_called_once_with()
        guild_definition.emojis.assert_called_once_with()
        guild_definition.stickers.assert_called_once_with()
        guild_definition.roles.assert_called_once_with()
        guild_definition.channels.assert_called_once_with()
        guild_definition.members.assert_called_once_with()
        guild_definition.presences.assert_called_once_with()
        guild_definition.voice_states.assert_called_once_with()
        mock_shard.get_user_id.assert_called_once_with()

    def test_deserialize_guild_join_event(self, event_factory, mock_app, mock_shard):
        mock_payload = mock.Mock(app=mock_app)

        event = event_factory.deserialize_guild_join_event(mock_shard, mock_payload)

        mock_app.entity_factory.deserialize_gateway_guild.assert_called_once_with(
            mock_payload, user_id=mock_shard.get_user_id.return_value
        )
        assert isinstance(event, guild_events.GuildJoinEvent)
        assert event.shard is mock_shard
        guild_definition = mock_app.entity_factory.deserialize_gateway_guild.return_value
        assert event.guild is guild_definition.guild.return_value
        assert event.emojis is guild_definition.emojis.return_value
        assert event.roles is guild_definition.roles.return_value
        assert event.channels is guild_definition.channels.return_value
        assert event.members is guild_definition.members.return_value
        assert event.presences is guild_definition.presences.return_value
        assert event.voice_states is guild_definition.voice_states.return_value
        mock_shard.get_user_id.assert_called_once_with()

    def test_deserialize_guild_update_event(self, event_factory, mock_app, mock_shard):
        mock_payload = mock.Mock(app=mock_app)
        mock_old_guild = object()

        event = event_factory.deserialize_guild_update_event(mock_shard, mock_payload, old_guild=mock_old_guild)

        mock_app.entity_factory.deserialize_gateway_guild.assert_called_once_with(
            mock_payload, user_id=mock_shard.get_user_id.return_value
        )
        assert isinstance(event, guild_events.GuildUpdateEvent)
        assert event.shard is mock_shard
        guild_definition = mock_app.entity_factory.deserialize_gateway_guild.return_value
        assert event.guild is guild_definition.guild.return_value
        assert event.emojis is guild_definition.emojis.return_value
        assert event.roles is guild_definition.roles.return_value
        assert event.old_guild is mock_old_guild
        guild_definition.guild.assert_called_once_with()
        guild_definition.emojis.assert_called_once_with()
        guild_definition.roles.assert_called_once_with()
        mock_shard.get_user_id.assert_called_once_with()

    def test_deserialize_guild_leave_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {"id": "43123123"}
        mock_old_guild = object()

        event = event_factory.deserialize_guild_leave_event(mock_shard, mock_payload, old_guild=mock_old_guild)

        assert isinstance(event, guild_events.GuildLeaveEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.guild_id == 43123123
        assert event.old_guild is mock_old_guild

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

    def test_deserialize_guild_stickers_update_event(self, event_factory, mock_app, mock_shard):
        mock_sticker_payload = object()
        mock_old_stickers = object()
        mock_payload = {"guild_id": "472", "stickers": [mock_sticker_payload]}

        event = event_factory.deserialize_guild_stickers_update_event(
            mock_shard, mock_payload, old_stickers=mock_old_stickers
        )

        mock_app.entity_factory.deserialize_guild_sticker.assert_called_once_with(mock_sticker_payload)
        assert isinstance(event, guild_events.StickersUpdateEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.stickers == [mock_app.entity_factory.deserialize_guild_sticker.return_value]
        assert event.guild_id == 472
        assert event.old_stickers is mock_old_stickers

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
                "global_name": "blahaj",
                "avatar": "NOK",
                "banner": "12122hssjamanmdd",
                "accent_color": 12342,
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
        assert event.user.global_name == "blahaj"
        assert event.user.discriminator == "1231"
        assert event.user.avatar_hash == "NOK"
        assert event.user.banner_hash == "12122hssjamanmdd"
        assert event.user.accent_color == 12342
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
        assert event.user.global_name is undefined.UNDEFINED
        assert event.user.discriminator is undefined.UNDEFINED
        assert event.user.avatar_hash is undefined.UNDEFINED
        assert event.user.banner_hash is undefined.UNDEFINED
        assert event.user.accent_color is undefined.UNDEFINED
        assert event.user.is_bot is undefined.UNDEFINED
        assert event.user.is_system is undefined.UNDEFINED
        assert event.user.flags is undefined.UNDEFINED

        assert event.presence is mock_app.entity_factory.deserialize_member_presence.return_value

    def test_deserialize_audit_log_entry_create_event(
        self, event_factory: event_factory_.EventFactoryImpl, mock_app, mock_shard
    ):
        payload = {"id": "439034093490"}

        result = event_factory.deserialize_audit_log_entry_create_event(mock_shard, payload)

        mock_app.entity_factory.deserialize_audit_log_entry.assert_called_once_with(payload)
        assert result.entry is mock_app.entity_factory.deserialize_audit_log_entry.return_value
        assert result.shard is mock_shard
        assert isinstance(result, guild_events.AuditLogEntryCreateEvent)

    ######################
    # INTERACTION EVENTS #
    ######################

    @pytest.mark.parametrize(
        ("interaction_type", "expected"),
        [
            (base_interactions.InteractionType.APPLICATION_COMMAND, interaction_events.CommandInteractionCreateEvent),
            (base_interactions.InteractionType.MESSAGE_COMPONENT, interaction_events.ComponentInteractionCreateEvent),
            (base_interactions.InteractionType.AUTOCOMPLETE, interaction_events.AutocompleteInteractionCreateEvent),
            (base_interactions.InteractionType.MODAL_SUBMIT, interaction_events.ModalInteractionCreateEvent),
        ],
    )
    def test_deserialize_interaction_create_event(
        self,
        event_factory,
        mock_app,
        mock_shard,
        interaction_type: typing.Optional[base_interactions.InteractionType],
        expected: interaction_events.InteractionCreateEvent,
    ):
        payload = {"id": "1561232344"}
        if interaction_type:
            mock_app.entity_factory.deserialize_interaction.return_value = mock.Mock(type=interaction_type)
        result = event_factory.deserialize_interaction_create_event(mock_shard, payload)

        mock_app.entity_factory.deserialize_interaction.assert_called_once_with(payload)
        assert result.shard is mock_shard
        assert result.interaction is mock_app.entity_factory.deserialize_interaction.return_value
        assert isinstance(result, expected)

    def test_deserialize_interaction_create_event_error(self, event_factory, mock_app, mock_shard):
        payload = {"id": "1561232344"}
        with pytest.raises(KeyError):
            event_factory.deserialize_interaction_create_event(mock_shard, payload)

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

    ##########################
    # SCHEDULED EVENT EVENTS #
    ##########################

    def test_deserialize_scheduled_event_create_event(
        self, event_factory: event_factory_.EventFactoryImpl, mock_app: traits.RESTAware, mock_shard: mock.Mock
    ):
        mock_payload = mock.Mock()

        event = event_factory.deserialize_scheduled_event_create_event(mock_shard, mock_payload)

        assert event.shard is mock_shard
        assert event.event is mock_app.entity_factory.deserialize_scheduled_event.return_value
        assert isinstance(event, scheduled_events.ScheduledEventCreateEvent)
        mock_app.entity_factory.deserialize_scheduled_event.assert_called_once_with(mock_payload)

    def test_deserialize_scheduled_event_update_event(
        self, event_factory: event_factory_.EventFactoryImpl, mock_app: traits.RESTAware, mock_shard: mock.Mock
    ):
        mock_payload = mock.Mock()

        event = event_factory.deserialize_scheduled_event_update_event(mock_shard, mock_payload)

        assert event.shard is mock_shard
        assert event.event is mock_app.entity_factory.deserialize_scheduled_event.return_value
        assert isinstance(event, scheduled_events.ScheduledEventUpdateEvent)
        mock_app.entity_factory.deserialize_scheduled_event.assert_called_once_with(mock_payload)

    def test_deserialize_scheduled_event_delete_event(
        self, event_factory: event_factory_.EventFactoryImpl, mock_app: traits.RESTAware, mock_shard: mock.Mock
    ):
        mock_payload = mock.Mock()

        event = event_factory.deserialize_scheduled_event_delete_event(mock_shard, mock_payload)

        assert event.shard is mock_shard
        assert event.event is mock_app.entity_factory.deserialize_scheduled_event.return_value
        assert isinstance(event, scheduled_events.ScheduledEventDeleteEvent)
        mock_app.entity_factory.deserialize_scheduled_event.assert_called_once_with(mock_payload)

    def test_deserialize_scheduled_event_user_add_event(
        self, event_factory: event_factory_.EventFactoryImpl, mock_app: mock.Mock, mock_shard: mock.Mock
    ):
        mock_payload = {"guild_id": "494949", "user_id": "123123123", "guild_scheduled_event_id": "49494944"}

        event = event_factory.deserialize_scheduled_event_user_add_event(mock_shard, mock_payload)

        assert event.shard is mock_shard
        assert event.guild_id == 494949
        assert event.user_id == 123123123
        assert event.event_id == 49494944
        assert isinstance(event, scheduled_events.ScheduledEventUserAddEvent)

    def test_deserialize_scheduled_event_user_remove_event(
        self, event_factory: event_factory_.EventFactoryImpl, mock_app: mock.Mock, mock_shard: mock.Mock
    ):
        mock_payload = {"guild_id": "3244321", "user_id": "56423", "guild_scheduled_event_id": "1234312"}

        event = event_factory.deserialize_scheduled_event_user_remove_event(mock_shard, mock_payload)

        assert event.shard is mock_shard
        assert event.guild_id == 3244321
        assert event.user_id == 56423
        assert event.event_id == 1234312
        assert isinstance(event, scheduled_events.ScheduledEventUserRemoveEvent)

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
        old_message = object()

        event = event_factory.deserialize_message_delete_event(mock_shard, mock_payload, old_message=old_message)

        assert isinstance(event, message_events.GuildMessageDeleteEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.old_message is old_message
        assert event.channel_id == 541123
        assert event.message_id == 5412
        assert event.guild_id == 9494949

    def test_deserialize_message_delete_event_in_dm(self, event_factory, mock_app, mock_shard):
        mock_payload = {"id": "5412", "channel_id": "541123"}
        old_message = object()

        event = event_factory.deserialize_message_delete_event(mock_shard, mock_payload, old_message=old_message)

        assert isinstance(event, message_events.DMMessageDeleteEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.old_message is old_message
        assert event.channel_id == 541123
        assert event.message_id == 5412

    def test_deserialize_guild_message_delete_bulk_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {"ids": ["6523423", "345123"], "channel_id": "564123", "guild_id": "4394949"}
        old_messages = object()

        event = event_factory.deserialize_guild_message_delete_bulk_event(
            mock_shard, mock_payload, old_messages=old_messages
        )

        assert isinstance(event, message_events.GuildBulkMessageDeleteEvent)
        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.old_messages is old_messages
        assert event.channel_id == 564123
        assert event.message_ids == {6523423, 345123}
        assert event.guild_id == 4394949

    def test_deserialize_guild_message_delete_bulk_event_when_old_messages_is_none(
        self, event_factory, mock_app, mock_shard
    ):
        mock_payload = {"ids": ["6523423", "345123"], "channel_id": "564123", "guild_id": "4394949"}

        event = event_factory.deserialize_guild_message_delete_bulk_event(mock_shard, mock_payload)

        assert isinstance(event, message_events.GuildBulkMessageDeleteEvent)
        assert event.old_messages == {}

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
            "resume_gateway_url": "testing.com",
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
        assert event.resume_gateway_url == "testing.com"
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
        mock_payload = {"guild_id": "123432123", "members": [mock_member_payload], "chunk_index": 3, "chunk_count": 54}

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

    ##################
    #  MONETIZATION  #
    ##################

    def test_deserialize_entitlement_create_event(self, event_factory, mock_app, mock_shard):
        payload = {
            "id": "696969696969696",
            "sku_id": "420420420420420",
            "application_id": "123123123123123",
            "type": 8,
            "deleted": False,
            "starts_at": "2022-09-14T17:00:18.704163+00:00",
            "ends_at": "2022-10-14T17:00:18.704163+00:00",
            "guild_id": "1015034326372454400",
            "user_id": "115590097100865541",
            "subscription_id": "1019653835926409216",
        }

        event = event_factory.deserialize_entitlement_create_event(mock_shard, payload)

        assert isinstance(event, monetization_events.EntitlementCreateEvent)

    def test_deserialize_entitlement_update_event(self, event_factory, mock_app, mock_shard):
        payload = {
            "id": "696969696969696",
            "sku_id": "420420420420420",
            "application_id": "123123123123123",
            "type": 8,
            "deleted": False,
            "starts_at": "2022-09-14T17:00:18.704163+00:00",
            "ends_at": "2022-10-14T17:00:18.704163+00:00",
            "guild_id": "1015034326372454400",
            "user_id": "115590097100865541",
            "subscription_id": "1019653835926409216",
        }

        event = event_factory.deserialize_entitlement_update_event(mock_shard, payload)

        assert isinstance(event, monetization_events.EntitlementUpdateEvent)

    def test_deserialize_entitlement_delete_event(self, event_factory, mock_app, mock_shard):
        payload = {
            "id": "696969696969696",
            "sku_id": "420420420420420",
            "application_id": "123123123123123",
            "type": 8,
            "deleted": False,
            "starts_at": "2022-09-14T17:00:18.704163+00:00",
            "ends_at": "2022-10-14T17:00:18.704163+00:00",
            "guild_id": "1015034326372454400",
            "user_id": "115590097100865541",
            "subscription_id": "1019653835926409216",
        }

        event = event_factory.deserialize_entitlement_delete_event(mock_shard, payload)

        assert isinstance(event, monetization_events.EntitlementDeleteEvent)

    #########################
    # STAGE INSTANCE EVENTS #
    #########################

    def test_deserialize_stage_instance_create_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {
            "id": "840647391636226060",
            "guild_id": "197038439483310086",
            "channel_id": "733488538393510049",
            "topic": "Testing Testing, 123",
            "privacy_level": 1,
            "discoverable_disabled": False,
        }
        event = event_factory.deserialize_stage_instance_create_event(mock_shard, mock_payload)
        assert isinstance(event, stage_events.StageInstanceCreateEvent)

        assert event.shard is mock_shard
        assert event.app is event.stage_instance.app
        assert event.stage_instance == mock_app.entity_factory.deserialize_stage_instance.return_value

    def test_deserialize_stage_instance_update_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {
            "id": "840647391636226060",
            "guild_id": "197038439483310086",
            "channel_id": "733488538393510049",
            "topic": "Testing Testing, 124",
            "privacy_level": 2,
            "discoverable_disabled": True,
        }
        event = event_factory.deserialize_stage_instance_update_event(mock_shard, mock_payload)
        assert isinstance(event, stage_events.StageInstanceUpdateEvent)

        assert event.shard is mock_shard
        assert event.app is event.stage_instance.app
        assert event.stage_instance == mock_app.entity_factory.deserialize_stage_instance.return_value

    def test_deserialize_stage_instance_delete_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {
            "id": "840647391636226060",
            "guild_id": "197038439483310086",
            "channel_id": "733488538393510049",
            "topic": "Testing Testing, 124",
            "privacy_level": 2,
            "discoverable_disabled": True,
        }
        event = event_factory.deserialize_stage_instance_delete_event(mock_shard, mock_payload)
        assert isinstance(event, stage_events.StageInstanceDeleteEvent)

        assert event.shard is mock_shard
        assert event.app is event.stage_instance.app
        assert event.stage_instance == mock_app.entity_factory.deserialize_stage_instance.return_value

    ###########
    #  POLLS  #
    ###########

    def test_deserialize_poll_vote_create_event(self, event_factory, mock_app, mock_shard):
        payload = {
            "user_id": "3847382",
            "channel_id": "4598743",
            "message_id": "458437954",
            "guild_id": "3589273",
            "answer_id": 1,
        }

        event = event_factory.deserialize_poll_vote_create_event(mock_shard, payload)

        assert isinstance(event, poll_events.PollVoteCreateEvent)

    def test_deserialize_poll_vote_delete_event(self, event_factory, mock_app, mock_shard):
        payload = {
            "user_id": "3847382",
            "channel_id": "4598743",
            "message_id": "458437954",
            "guild_id": "3589273",
            "answer_id": 1,
        }

        event = event_factory.deserialize_poll_vote_delete_event(mock_shard, payload)

        assert isinstance(event, poll_events.PollVoteDeleteEvent)

    def test_deserialize_auto_mod_rule_create_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {"id": "49499494"}

        event = event_factory.deserialize_auto_mod_rule_create_event(mock_shard, mock_payload)

        assert isinstance(event, auto_mod_events.AutoModRuleCreateEvent)
        assert event.shard is mock_shard
        assert event.rule is mock_app.entity_factory.deserialize_auto_mod_rule.return_value
        mock_app.entity_factory.deserialize_auto_mod_rule.assert_called_once_with(mock_payload)

    def test_deserialize_auto_mod_rule_update_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {"id": "49499494"}

        event = event_factory.deserialize_auto_mod_rule_update_event(mock_shard, mock_payload)

        assert isinstance(event, auto_mod_events.AutoModRuleUpdateEvent)
        assert event.shard is mock_shard
        assert event.rule is mock_app.entity_factory.deserialize_auto_mod_rule.return_value
        mock_app.entity_factory.deserialize_auto_mod_rule.assert_called_once_with(mock_payload)

    def test_deserialize_auto_mod_rule_delete_event(self, event_factory, mock_app, mock_shard):
        mock_payload = {"id": "49499494"}

        event = event_factory.deserialize_auto_mod_rule_delete_event(mock_shard, mock_payload)

        assert isinstance(event, auto_mod_events.AutoModRuleDeleteEvent)
        assert event.shard is mock_shard
        assert event.rule is mock_app.entity_factory.deserialize_auto_mod_rule.return_value
        mock_app.entity_factory.deserialize_auto_mod_rule.assert_called_once_with(mock_payload)

    def test_deserialize_auto_mod_action_execution_event(self, event_factory, mock_app, mock_shard):
        mock_action_payload = {"type": "69"}

        event = event_factory.deserialize_auto_mod_action_execution_event(
            mock_shard,
            {
                "guild_id": "123321",
                "action": mock_action_payload,
                "rule_id": "4959595",
                "rule_trigger_type": 3,
                "user_id": "4949494",
                "channel_id": "5423234",
                "message_id": "49343292",
                "alert_system_message_id": "49211123",
                "content": "meow",
                "matched_keyword": "fredf",
                "matched_content": "dfofodofdodf",
            },
        )

        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.guild_id == 123321
        assert event.action is mock_app.entity_factory.deserialize_auto_mod_action.return_value
        assert event.rule_id == 4959595
        assert event.rule_trigger_type is auto_mod.AutoModTriggerType.SPAM
        assert event.user_id == 4949494
        assert event.channel_id == 5423234
        assert event.message_id == 49343292
        assert event.alert_system_message_id == 49211123
        assert event.content == "meow"
        assert event.matched_keyword == "fredf"
        assert event.matched_content == "dfofodofdodf"
        mock_app.entity_factory.deserialize_auto_mod_action.assert_called_once_with(mock_action_payload)

    def test_deserialize_auto_mod_action_execution_event_when_partial(self, event_factory, mock_app, mock_shard):
        mock_action_payload = {"type": "69"}

        event = event_factory.deserialize_auto_mod_action_execution_event(
            mock_shard,
            {
                "guild_id": "123321",
                "action": mock_action_payload,
                "rule_id": "4959595",
                "rule_trigger_type": 3,
                "user_id": "4949494",
                "content": "",
                "matched_keyword": None,
                "matched_content": None,
            },
        )

        assert event.app is mock_app
        assert event.shard is mock_shard
        assert event.guild_id == 123321
        assert event.action is mock_app.entity_factory.deserialize_auto_mod_action.return_value
        assert event.rule_id == 4959595
        assert event.rule_trigger_type is auto_mod.AutoModTriggerType.SPAM
        assert event.user_id == 4949494
        assert event.channel_id is None
        assert event.message_id is None
        assert event.alert_system_message_id is None
        assert event.content is None
        assert event.matched_keyword is None
        assert event.matched_content is None
        mock_app.entity_factory.deserialize_auto_mod_action.assert_called_once_with(mock_action_payload)
