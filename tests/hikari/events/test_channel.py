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
import datetime
import contextlib

import pytest
import mock

from hikari import users
from hikari import guilds
from hikari import invites
from hikari import channels
from hikari.events import channel
from hikari.internal import conversions
from tests.hikari import _helpers


@pytest.fixture()
def test_user_payload():
    return {"id": "2929292", "username": "agent 69", "discriminator": "4444", "avatar": "9292929292929292"}


class TestBaseChannelEvent:
    @pytest.fixture()
    def test_overwrite_payload(self):
        return {"id": "292929", "type": "member", "allow": 49152, "deny": 0}

    @pytest.fixture()
    def test_base_channel_payload(self, test_overwrite_payload, test_user_payload):
        return {
            "id": "424242",
            "type": 2,
            "guild_id": "69240",
            "position": 7,
            "permission_overwrites": [test_overwrite_payload],
            "name": "Name",
            "topic": "Topically drunk",
            "nsfw": True,
            "last_message_id": "22222222",
            "bitrate": 96000,
            "user_limit": 42,
            "rate_limit_per_user": 2333,
            "recipients": [test_user_payload],
            "icon": "sdodsooioio2oi",
            "owner_id": "32939393",
            "application_id": "202020202",
            "parent_id": "2030302939",
            "last_pin_timestamp": "2019-05-17T06:26:56.936000+00:00",
        }

    def test_deserialize(self, test_base_channel_payload, test_overwrite_payload, test_user_payload):
        mock_timestamp = mock.MagicMock(datetime.datetime)
        mock_user = mock.MagicMock(users.User, id=42)
        mock_overwrite = mock.MagicMock(channels.PermissionOverwrite, id=64)
        stack = contextlib.ExitStack()
        patched_timestamp_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                channel.BaseChannelEvent,
                "last_pin_timestamp",
                deserializer=conversions.parse_iso_8601_ts,
                return_value=mock_timestamp,
            )
        )
        stack.enter_context(mock.patch.object(users.User, "deserialize", return_value=mock_user))
        stack.enter_context(mock.patch.object(channels.PermissionOverwrite, "deserialize", return_value=mock_overwrite))
        with stack:
            base_channel_payload = channel.BaseChannelEvent.deserialize(test_base_channel_payload)
            channels.PermissionOverwrite.deserialize.assert_called_once_with(test_overwrite_payload)
            users.User.deserialize.assert_called_once_with(test_user_payload)
            patched_timestamp_deserializer.assert_called_once_with("2019-05-17T06:26:56.936000+00:00")
        assert base_channel_payload.type is channels.ChannelType.GUILD_VOICE
        assert base_channel_payload.guild_id == 69240
        assert base_channel_payload.position == 7
        assert base_channel_payload.permission_overwrites == {64: mock_overwrite}
        assert base_channel_payload.name == "Name"
        assert base_channel_payload.topic == "Topically drunk"
        assert base_channel_payload.is_nsfw is True
        assert base_channel_payload.last_message_id == 22222222
        assert base_channel_payload.bitrate == 96000
        assert base_channel_payload.user_limit == 42
        assert base_channel_payload.rate_limit_per_user == datetime.timedelta(seconds=2333)
        assert base_channel_payload.recipients == {42: mock_user}
        assert base_channel_payload.icon_hash == "sdodsooioio2oi"
        assert base_channel_payload.owner_id == 32939393
        assert base_channel_payload.application_id == 202020202
        assert base_channel_payload.parent_id == 2030302939
        assert base_channel_payload.last_pin_timestamp is mock_timestamp


# Doesn't declare any new fields.
class TestChannelCreateEvent:
    ...


# Doesn't declare any new fields.
class TestChannelUpdateEvent:
    ...


# Doesn't declare any new fields.
class TestChannelDeleteEvent:
    ...


class TestChannelPinUpdateEvent:
    @pytest.fixture()
    def test_chanel_pin_update_payload(self):
        return {
            "guild_id": "424242",
            "channel_id": "29292929",
            "last_pin_timestamp": "2020-03-20T16:08:25.412000+00:00",
        }

    def test_deserialize(self, test_chanel_pin_update_payload):
        mock_timestamp = mock.MagicMock(datetime.datetime)
        with _helpers.patch_marshal_attr(
            channel.ChannelPinUpdateEvent,
            "last_pin_timestamp",
            deserializer=conversions.parse_iso_8601_ts,
            return_value=mock_timestamp,
        ) as patched_iso_parser:
            channel_pin_add_obj = channel.ChannelPinUpdateEvent.deserialize(test_chanel_pin_update_payload)
            patched_iso_parser.assert_called_once_with("2020-03-20T16:08:25.412000+00:00")
        assert channel_pin_add_obj.guild_id == 424242
        assert channel_pin_add_obj.channel_id == 29292929
        assert channel_pin_add_obj.last_pin_timestamp is mock_timestamp


class TestWebhookUpdateEvent:
    @pytest.fixture()
    def test_webhook_update_payload(self):
        return {"guild_id": "2929292", "channel_id": "94949494"}

    def test_deserialize(self, test_webhook_update_payload):
        webhook_update_obj = channel.WebhookUpdateEvent.deserialize(test_webhook_update_payload)
        assert webhook_update_obj.guild_id == 2929292
        assert webhook_update_obj.channel_id == 94949494


class TestTypingStartEvent:
    @pytest.fixture()
    def test_member_payload(self, test_user_payload):
        return {
            "user": test_user_payload,
            "nick": "Agent 42",
            "roles": [],
            "joined_at": "2015-04-26T06:26:56.936000+00:00",
            "premium_since": "2019-05-17T06:26:56.936000+00:00",
            "deaf": True,
            "mute": False,
        }

    @pytest.fixture()
    def test_typing_start_event_payload(self, test_member_payload):
        return {
            "channel_id": "123123123",
            "guild_id": "33333333",
            "user_id": "2020202",
            "timestamp": 1231231231,
            "member": test_member_payload,
        }

    def test_deserialize(self, test_typing_start_event_payload, test_member_payload):
        mock_member = mock.MagicMock(guilds.GuildMember)
        mock_datetime = mock.MagicMock(datetime.datetime)
        stack = contextlib.ExitStack()
        mock_member_deserialize = stack.enter_context(
            _helpers.patch_marshal_attr(
                channel.TypingStartEvent,
                "member",
                deserializer=guilds.GuildMember.deserialize,
                return_value=mock_member,
            )
        )
        stack.enter_context(
            mock.patch.object(datetime, "datetime", fromtimestamp=mock.MagicMock(return_value=mock_datetime))
        )
        with stack:
            typing_start_event_obj = channel.TypingStartEvent.deserialize(test_typing_start_event_payload)
            datetime.datetime.fromtimestamp.assert_called_once_with(1231231231, datetime.timezone.utc)
            mock_member_deserialize.assert_called_once_with(test_member_payload)
        assert typing_start_event_obj.channel_id == 123123123
        assert typing_start_event_obj.guild_id == 33333333
        assert typing_start_event_obj.user_id == 2020202
        assert typing_start_event_obj.timestamp is mock_datetime
        assert typing_start_event_obj.member is mock_member


class TestInviteCreateEvent:
    @pytest.fixture()
    def test_invite_create_payload(self, test_user_payload):
        return {
            "channel_id": "939393",
            "code": "owouwuowouwu",
            "created_at": "2019-05-17T06:26:56.936000+00:00",
            "guild_id": "45949",
            "inviter": test_user_payload,
            "max_age": 42,
            "max_uses": 69,
            "target_user": {"id": "420", "username": "blah", "discriminator": "4242", "avatar": "ha"},
            "target_user_type": 1,
            "temporary": True,
            "uses": 42,
        }

    def test_deserialize(self, test_invite_create_payload, test_user_payload):
        mock_inviter = mock.MagicMock(users.User)
        mock_target = mock.MagicMock(users.User)
        mock_created_at = mock.MagicMock(datetime.datetime)
        stack = contextlib.ExitStack()
        patched_inviter_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                channel.InviteCreateEvent, "inviter", deserializer=users.User.deserialize, return_value=mock_inviter
            )
        )
        patched_target_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                channel.InviteCreateEvent, "target_user", deserializer=users.User.deserialize, return_value=mock_target
            )
        )
        patched_created_at_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                channel.InviteCreateEvent,
                "created_at",
                deserializer=conversions.parse_iso_8601_ts,
                return_value=mock_created_at,
            )
        )
        with stack:
            invite_create_obj = channel.InviteCreateEvent.deserialize(test_invite_create_payload)
            patched_created_at_deserializer.assert_called_once_with("2019-05-17T06:26:56.936000+00:00")
            patched_target_deserializer.assert_called_once_with(
                {"id": "420", "username": "blah", "discriminator": "4242", "avatar": "ha"}
            )
            patched_inviter_deserializer.assert_called_once_with(test_user_payload)
        assert invite_create_obj.channel_id == 939393
        assert invite_create_obj.code == "owouwuowouwu"
        assert invite_create_obj.created_at is mock_created_at
        assert invite_create_obj.guild_id == 45949
        assert invite_create_obj.inviter is mock_inviter
        assert invite_create_obj.max_age == datetime.timedelta(seconds=42)
        assert invite_create_obj.max_uses == 69
        assert invite_create_obj.target_user is mock_target
        assert invite_create_obj.target_user_type is invites.TargetUserType.STREAM
        assert invite_create_obj.is_temporary is True
        assert invite_create_obj.uses == 42

    def test_max_age_when_zero(self, test_invite_create_payload):
        test_invite_create_payload["max_age"] = 0
        assert channel.InviteCreateEvent.deserialize(test_invite_create_payload).max_age is None


class TestInviteDeleteEvent:
    @pytest.fixture()
    def test_invite_delete_payload(self):
        return {"channel_id": "393939", "code": "blahblahblah", "guild_id": "3834833"}

    def test_deserialize(self, test_invite_delete_payload):
        invite_delete_obj = channel.InviteDeleteEvent.deserialize(test_invite_delete_payload)
        assert invite_delete_obj.channel_id == 393939
        assert invite_delete_obj.code == "blahblahblah"
        assert invite_delete_obj.guild_id == 3834833


# Doesn't declare any new fields.
class TestVoiceStateUpdateEvent:
    ...


class TestVoiceServerUpdateEvent:
    @pytest.fixture()
    def test_voice_server_update_payload(self):
        return {"token": "a_token", "guild_id": "303030300303", "endpoint": "smart.loyal.discord.gg"}

    def test_deserialize(self, test_voice_server_update_payload):
        voice_server_update_obj = channel.VoiceServerUpdateEvent.deserialize(test_voice_server_update_payload)
        assert voice_server_update_obj.token == "a_token"
        assert voice_server_update_obj.guild_id == 303030300303
        assert voice_server_update_obj.endpoint == "smart.loyal.discord.gg"
