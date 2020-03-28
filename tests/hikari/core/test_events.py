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

import cymock as mock
import pytest

from hikari.core import channels
from hikari.core import embeds
from hikari.core import emojis
from hikari.core import entities
from hikari.core import events
from hikari.core import guilds
from hikari.core import invites
from hikari.core import messages
from hikari.core import oauth2
from hikari.core import users
from hikari.internal_utilities import dates

from tests.hikari import _helpers


@pytest.fixture()
def test_emoji_payload():
    return {"id": "4242", "name": "blahblah", "animated": True}


@pytest.fixture()
def test_user_payload():
    return {"id": "2929292", "username": "agent 69", "discriminator": "4444", "avatar": "9292929292929292"}


@pytest.fixture()
def test_guild_payload():
    return {"id": "40404040", "name": "electric guild boogaloo"}


@pytest.fixture()
def test_member_payload(test_user_payload):
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
def test_role_payload():
    return {
        "id": "2929292929",
        "name": "nyaa nyaa nyaa",
        "color": 16735488,
        "hoist": True,
        "permissions": 2146959103,
        "managed": False,
        "mentionable": False,
    }


@pytest.fixture()
def test_channel_payload():
    return {"id": "393939", "name": "a channel", "type": 2}


@pytest.fixture()
def test_overwrite_payload():
    return {"id": "292929", "type": "member", "allow": 49152, "deny": 0}


# Base event, is not deserialized
class TestHikariEvent:
    ...


# Synthetic event, is not deserialized
class TestConnectedEvent:
    ...


# Synthetic event, is not deserialized
class TestDisconnectedEvent:
    ...


# Synthetic event, is not deserialized
class TestReconnectedEvent:
    ...


# Synthetic event, is not deserialized
class TestStartedEvent:
    ...


# Synthetic event, is not deserialized
class TestStoppingEvent:
    ...


# Synthetic event, is not deserialized
class TestStoppedEvent:
    ...


class TestReadyEvent:
    @pytest.fixture()
    def test_read_event_payload(self, test_guild_payload, test_user_payload):
        return {
            "v": 69420,
            "user": test_user_payload,
            "private_channels": [],
            "guilds": [test_guild_payload],
            "session_id": "osdkoiiodsaooeiwio9",
            "shard": [42, 80],
        }

    def test_deserialize(self, test_read_event_payload, test_guild_payload, test_user_payload):
        mock_guild = mock.MagicMock(guilds.Guild, id=40404040)
        mock_user = mock.MagicMock(users.MyUser)
        with mock.patch.object(guilds.UnavailableGuild, "deserialize", return_value=mock_guild):
            with _helpers.patch_marshal_attr(
                events.ReadyEvent, "my_user", deserializer=users.MyUser.deserialize, return_value=mock_user
            ) as patched_user_deserialize:
                ready_obj = events.ReadyEvent.deserialize(test_read_event_payload)
                patched_user_deserialize.assert_called_once_with(test_user_payload)
            guilds.UnavailableGuild.deserialize.assert_called_once_with(test_guild_payload)
        assert ready_obj.gateway_version == 69420
        assert ready_obj.my_user is mock_user
        assert ready_obj.unavailable_guilds == {40404040: mock_guild}
        assert ready_obj.session_id == "osdkoiiodsaooeiwio9"
        assert ready_obj._shard_information == (42, 80)

    @pytest.fixture()
    @mock.patch.object(guilds.UnavailableGuild, "deserialize")
    @_helpers.patch_marshal_attr(events.ReadyEvent, "my_user", deserializer=users.MyUser.deserialize)
    def mock_ready_event_obj(self, *args, test_read_event_payload):
        return events.ReadyEvent.deserialize(test_read_event_payload)

    def test_shard_id_when_information_set(self, mock_ready_event_obj):
        assert mock_ready_event_obj.shard_id == 42

    def test_shard_count_when_information_set(self, mock_ready_event_obj):
        assert mock_ready_event_obj.shard_count == 80

    def test_shard_id_when_information_not_set(self, mock_ready_event_obj):
        mock_ready_event_obj._shard_information = None
        assert mock_ready_event_obj.shard_id is None

    def test_shard_count_when_information_not_set(self, mock_ready_event_obj):
        mock_ready_event_obj._shard_information = None
        assert mock_ready_event_obj.shard_count is None


# Doesn't have any fields.
class TestResumedEvent:
    ...


class TestBaseChannelEvent:
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
        with _helpers.patch_marshal_attr(
            events.BaseChannelEvent,
            "last_pin_timestamp",
            deserializer=dates.parse_iso_8601_ts,
            return_value=mock_timestamp,
        ) as patched_timestamp_deserializer:
            with mock.patch.object(users.User, "deserialize", return_value=mock_user):
                with mock.patch.object(channels.PermissionOverwrite, "deserialize", return_value=mock_overwrite):
                    base_channel_payload = events.BaseChannelEvent.deserialize(test_base_channel_payload)
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
            events.ChannelPinUpdateEvent,
            "last_pin_timestamp",
            deserializer=dates.parse_iso_8601_ts,
            return_value=mock_timestamp,
        ) as patched_iso_parser:
            channel_pin_add_obj = events.ChannelPinUpdateEvent.deserialize(test_chanel_pin_update_payload)
            patched_iso_parser.assert_called_once_with("2020-03-20T16:08:25.412000+00:00")
        assert channel_pin_add_obj.guild_id == 424242
        assert channel_pin_add_obj.channel_id == 29292929
        assert channel_pin_add_obj.last_pin_timestamp is mock_timestamp


# Doesn't declare any new fields.
class TestGuildCreateEvent:
    ...


# Doesn't declare any new fields.
class TestGuildUpdateEvent:
    ...


# Doesn't declare any new fields.
class GuildLeaveEvent:
    ...


# Doesn't declare any new fields.
class GuildUnavailableEvent:
    ...


class TestBaseGuildBanEvent:
    @pytest.fixture()
    def test_guild_ban_payload(self, test_user_payload):
        return {"user": test_user_payload, "guild_id": "5959"}

    def test_deserialize(self, test_guild_ban_payload, test_user_payload):
        mock_user = mock.MagicMock(users.User)
        with _helpers.patch_marshal_attr(
            events.BaseGuildBanEvent, "user", deserializer=users.User.deserialize, return_value=mock_user
        ) as patched_user_deserializer:
            base_guild_ban_object = events.BaseGuildBanEvent.deserialize(test_guild_ban_payload)
            patched_user_deserializer.assert_called_once_with(test_user_payload)
        assert base_guild_ban_object.user is mock_user
        assert base_guild_ban_object.guild_id == 5959


# Doesn't declare any new fields.
class TestGuildBanAddEvent:
    ...


# Doesn't declare any new fields.
class TestGuildBanRemoveEvent:
    ...


class TestGuildEmojisUpdateEvent:
    @pytest.fixture()
    def test_guild_emojis_update_payload(self, test_emoji_payload):
        return {"emojis": [test_emoji_payload], "guild_id": "696969"}

    def test_deserialize(self, test_guild_emojis_update_payload, test_emoji_payload):
        mock_emoji = _helpers.mock_model(emojis.GuildEmoji, id=240)
        with mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji):
            guild_emojis_update_obj = events.GuildEmojisUpdateEvent.deserialize(test_guild_emojis_update_payload)
            emojis.GuildEmoji.deserialize.assert_called_once_with(test_emoji_payload)
        assert guild_emojis_update_obj.emojis == {mock_emoji.id: mock_emoji}
        assert guild_emojis_update_obj.guild_id == 696969


class TestGuildIntegrationsUpdateEvent:
    def test_deserialize(self):
        assert events.GuildIntegrationsUpdateEvent.deserialize({"guild_id": "1234"}).guild_id == 1234


class TestGuildMemberAddEvent:
    @pytest.fixture()
    def test_guild_member_add_payload(self, test_member_payload):
        return {**test_member_payload, "guild_id": "292929"}

    def test_deserialize(self, test_guild_member_add_payload):
        guild_member_add_obj = events.GuildMemberAddEvent.deserialize(test_guild_member_add_payload)
        assert guild_member_add_obj.guild_id == 292929


class TestGuildMemberRemoveEvent:
    @pytest.fixture()
    def test_guild_member_remove_payload(self, test_user_payload):
        return {"guild_id": "9494949", "user": test_user_payload}

    def test_deserialize(self, test_guild_member_remove_payload, test_user_payload):
        mock_user = mock.MagicMock(users.User)
        with _helpers.patch_marshal_attr(
            events.GuildMemberRemoveEvent, "user", deserializer=users.User.deserialize, return_value=mock_user
        ) as patched_user_deseializer:
            guild_member_remove_payload = events.GuildMemberRemoveEvent.deserialize(test_guild_member_remove_payload)
            patched_user_deseializer.assert_called_once_with(test_user_payload)
        assert guild_member_remove_payload.guild_id == 9494949
        assert guild_member_remove_payload.user is mock_user


class TestGuildMemberUpdateEvent:
    @pytest.fixture()
    def guild_member_update_payload(self, test_user_payload):
        return {
            "guild_id": "292929",
            "roles": ["213", "412"],
            "user": test_user_payload,
            "nick": "konnichiwa",
            "premium_since": "2019-05-17T06:26:56.936000+00:00",
        }

    def test_deserialize(self, guild_member_update_payload, test_user_payload):
        mock_user = mock.MagicMock(users.User)
        mock_premium_since = mock.MagicMock(datetime.datetime)
        with _helpers.patch_marshal_attr(
            events.GuildMemberUpdateEvent, "user", deserializer=users.User.deserialize, return_value=mock_user
        ) as patched_user_deserializer:
            with _helpers.patch_marshal_attr(
                events.GuildMemberUpdateEvent,
                "premium_since",
                deserializer=dates.parse_iso_8601_ts,
                return_value=mock_premium_since,
            ) as patched_premium_since_deserializer:
                guild_member_update_obj = events.GuildMemberUpdateEvent.deserialize(guild_member_update_payload)
                patched_premium_since_deserializer.assert_called_once_with("2019-05-17T06:26:56.936000+00:00")
            patched_user_deserializer.assert_called_once_with(test_user_payload)
        assert guild_member_update_obj.guild_id == 292929
        assert guild_member_update_obj.role_ids == [213, 412]
        assert guild_member_update_obj.user is mock_user
        assert guild_member_update_obj.nickname == "konnichiwa"
        assert guild_member_update_obj.premium_since is mock_premium_since

    def test_partial_deserializer(self, guild_member_update_payload):
        del guild_member_update_payload["nick"]
        del guild_member_update_payload["premium_since"]
        with _helpers.patch_marshal_attr(events.GuildMemberUpdateEvent, "user", deserializer=users.User.deserialize):
            guild_member_update_obj = events.GuildMemberUpdateEvent.deserialize(guild_member_update_payload)
        assert guild_member_update_obj.nickname is entities.UNSET
        assert guild_member_update_obj.premium_since is entities.UNSET


@pytest.fixture()
def test_guild_role_create_update_payload(test_guild_payload):
    return {"guild_id": "69240", "role": test_guild_payload}


class TestGuildRoleCreateEvent:
    def test_deserialize(self, test_guild_role_create_update_payload, test_guild_payload):
        mock_role = mock.MagicMock(guilds.GuildRole)
        with _helpers.patch_marshal_attr(
            events.GuildRoleCreateEvent, "role", deserializer=guilds.GuildRole.deserialize, return_value=mock_role
        ) as patched_role_deserializer:
            guild_role_create_obj = events.GuildRoleCreateEvent.deserialize(test_guild_role_create_update_payload)
            patched_role_deserializer.assert_called_once_with(test_guild_payload)
        assert guild_role_create_obj.role is mock_role
        assert guild_role_create_obj.guild_id == 69240


class TestGuildRoleUpdateEvent:
    @pytest.fixture()
    def test_guild_role_create_fixture(self, test_guild_payload):
        return {"guild_id": "69240", "role": test_guild_payload}

    def test_deserialize(self, test_guild_role_create_update_payload, test_guild_payload):
        mock_role = mock.MagicMock(guilds.GuildRole)
        with _helpers.patch_marshal_attr(
            events.GuildRoleUpdateEvent, "role", deserializer=guilds.GuildRole.deserialize, return_value=mock_role
        ) as patched_role_deserializer:
            guild_role_create_obj = events.GuildRoleUpdateEvent.deserialize(test_guild_role_create_update_payload)
            patched_role_deserializer.assert_called_once_with(test_guild_payload)
        assert guild_role_create_obj.role is mock_role
        assert guild_role_create_obj.guild_id == 69240


class TestGuildRoleDeleteEvent:
    @pytest.fixture()
    def test_guild_role_delete_payload(self):
        return {"guild_id": "424242", "role_id": "94595959"}

    def test_deserialize(self, test_guild_role_delete_payload):
        guild_role_delete_payload = events.GuildRoleDeleteEvent.deserialize(test_guild_role_delete_payload)
        assert guild_role_delete_payload.guild_id == 424242
        assert guild_role_delete_payload.role_id == 94595959


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
        with _helpers.patch_marshal_attr(
            events.InviteCreateEvent, "inviter", deserializer=users.User.deserialize, return_value=mock_inviter
        ) as patched_inviter_deserializer:
            with _helpers.patch_marshal_attr(
                events.InviteCreateEvent, "target_user", deserializer=users.User.deserialize, return_value=mock_target
            ) as patched_target_deserializer:
                with _helpers.patch_marshal_attr(
                    events.InviteCreateEvent,
                    "created_at",
                    deserializer=dates.parse_iso_8601_ts,
                    return_value=mock_created_at,
                ) as patched_created_at_deserializer:
                    invite_create_obj = events.InviteCreateEvent.deserialize(test_invite_create_payload)
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
        assert events.InviteCreateEvent.deserialize(test_invite_create_payload).max_age is None


class TestInviteDeleteEvent:
    @pytest.fixture()
    def test_invite_delete_payload(self):
        return {"channel_id": "393939", "code": "blahblahblah", "guild_id": "3834833"}

    def test_deserialize(self, test_invite_delete_payload):
        invite_delete_obj = events.InviteDeleteEvent.deserialize(test_invite_delete_payload)
        assert invite_delete_obj.channel_id == 393939
        assert invite_delete_obj.code == "blahblahblah"
        assert invite_delete_obj.guild_id == 3834833


# Doesn't declare any new fields.
class TestMessageCreateEvent:
    ...


class TestMessageUpdateEvent:
    @pytest.fixture()
    def test_attachment_payload(self):
        return {
            "id": "4242",
            "filename": "nyaa.png",
            "size": 1024,
            "url": "heck.heck",
            "proxy_url": "proxy.proxy?heck",
            "height": 42,
            "width": 84,
        }

    @pytest.fixture()
    def test_embed_payload(self):
        return {"title": "42", "description": "blah blah blah"}

    @pytest.fixture()
    def test_reaction_payload(self):
        return {"count": 69, "me": True, "emoji": "🤣"}

    @pytest.fixture()
    def test_activity_payload(self):
        return {"type": 1, "party_id": "spotify:23123123"}

    @pytest.fixture()
    def test_application_payload(self):
        return {"id": "292929", "icon": None, "description": "descript", "name": "A name"}

    @pytest.fixture()
    def test_reference_payload(self):
        return {"channel_id": "432341231231"}

    @pytest.fixture()
    def test_message_update_payload(
        self,
        test_user_payload,
        test_member_payload,
        test_attachment_payload,
        test_embed_payload,
        test_reaction_payload,
        test_activity_payload,
        test_application_payload,
        test_reference_payload,
        test_channel_payload,
    ):
        return {
            "id": "3939399393",
            "channel_id": "93939393939",
            "guild_id": "66557744883399",
            "author": test_user_payload,
            "member": test_member_payload,
            "content": "THIS IS A CONTENT",
            "timestamp": "2019-05-17T06:26:56.936000+00:00",
            "edited_timestamp": "2019-05-17T06:58:56.936000+00:00",
            "tts": True,
            "mention_everyone": True,
            "mentions": [test_user_payload],
            "mention_roles": ["123"],
            "mention_channels": [test_channel_payload],
            "attachments": [test_attachment_payload],
            "embeds": [test_embed_payload],
            "reactions": [test_reaction_payload],
            "nonce": "6454345345345345",
            "pinned": True,
            "webhook_id": "212231231232123",
            "type": 2,
            "activity": test_activity_payload,
            "application": test_application_payload,
            "message_reference": test_reference_payload,
            "flags": 3,
        }

    def test_deserialize(
        self,
        test_message_update_payload,
        test_user_payload,
        test_member_payload,
        test_activity_payload,
        test_application_payload,
        test_reference_payload,
        test_attachment_payload,
        test_embed_payload,
        test_reaction_payload,
    ):
        mock_author = mock.MagicMock(users.User)
        mock_member = mock.MagicMock(guilds.GuildMember)
        mock_timestamp = mock.MagicMock(datetime.datetime)
        mock_edited_timestamp = mock.MagicMock(datetime.datetime)
        mock_attachment = mock.MagicMock(messages.Attachment)
        mock_embed = mock.MagicMock(embeds.Embed)
        mock_reaction = mock.MagicMock(messages.Reaction)
        mock_activity = mock.MagicMock(messages.MessageActivity)
        mock_application = mock.MagicMock(oauth2.Application)
        mock_reference = mock.MagicMock(messages.MessageCrosspost)
        with _helpers.patch_marshal_attr(
            events.MessageUpdateEvent, "author", deserializer=users.User.deserialize, return_value=mock_author
        ) as patched_author_deserializer:
            with _helpers.patch_marshal_attr(
                events.MessageUpdateEvent,
                "member",
                deserializer=guilds.GuildMember.deserialize,
                return_value=mock_member,
            ) as patched_member_deserializer:
                with _helpers.patch_marshal_attr(
                    events.MessageUpdateEvent,
                    "timestamp",
                    deserializer=dates.parse_iso_8601_ts,
                    return_value=mock_timestamp,
                ) as patched_timestamp_deserializer:
                    with _helpers.patch_marshal_attr(
                        events.MessageUpdateEvent,
                        "edited_timestamp",
                        deserializer=dates.parse_iso_8601_ts,
                        return_value=mock_edited_timestamp,
                    ) as patched_edit_deserializer:
                        with _helpers.patch_marshal_attr(
                            events.MessageUpdateEvent,
                            "activity",
                            deserializer=messages.MessageActivity.deserialize,
                            return_value=mock_activity,
                        ) as patched_activity_deserializer:
                            with _helpers.patch_marshal_attr(
                                events.MessageUpdateEvent,
                                "application",
                                deserializer=oauth2.Application.deserialize,
                                return_value=mock_application,
                            ) as patched_application_deserializer:
                                with _helpers.patch_marshal_attr(
                                    events.MessageUpdateEvent,
                                    "message_reference",
                                    deserializer=messages.MessageCrosspost.deserialize,
                                    return_value=mock_reference,
                                ) as patched_reference_deserializer:
                                    with mock.patch.object(
                                        messages.Attachment, "deserialize", return_value=mock_attachment
                                    ):
                                        with mock.patch.object(embeds.Embed, "deserialize", return_value=mock_embed):
                                            with mock.patch.object(
                                                messages.Reaction, "deserialize", return_value=mock_reaction
                                            ):
                                                message_update_payload = events.MessageUpdateEvent.deserialize(
                                                    test_message_update_payload
                                                )
                                                messages.Reaction.deserialize.assert_called_once_with(
                                                    test_reaction_payload
                                                )
                                            embeds.Embed.deserialize.assert_called_once_with(test_embed_payload)
                                        messages.Attachment.deserialize.assert_called_once_with(test_attachment_payload)
                                patched_reference_deserializer.assert_called_once_with(test_reference_payload)
                                patched_application_deserializer.assert_called_once_with(test_application_payload)
                            patched_activity_deserializer.assert_called_once_with(test_activity_payload)
                        patched_edit_deserializer.assert_called_once_with("2019-05-17T06:58:56.936000+00:00")
                    patched_timestamp_deserializer.assert_called_once_with("2019-05-17T06:26:56.936000+00:00")
                patched_member_deserializer.assert_called_once_with(test_member_payload)
            patched_author_deserializer.assert_called_once_with(test_user_payload)
        assert message_update_payload.channel_id == 93939393939
        assert message_update_payload.guild_id == 66557744883399
        assert message_update_payload.author is mock_author
        assert message_update_payload.member is mock_member
        assert message_update_payload.content == "THIS IS A CONTENT"
        assert message_update_payload.timestamp is mock_timestamp
        assert message_update_payload.edited_timestamp is mock_edited_timestamp
        assert message_update_payload.is_tts is True
        assert message_update_payload.is_mentioning_everyone is True
        assert message_update_payload.user_mentions == {2929292}
        assert message_update_payload.role_mentions == {123}
        assert message_update_payload.channel_mentions == {393939}
        assert message_update_payload.attachments == [mock_attachment]
        assert message_update_payload.embeds == [mock_embed]
        assert message_update_payload.reactions == [mock_reaction]
        assert message_update_payload.is_pinned is True
        assert message_update_payload.webhook_id == 212231231232123
        assert message_update_payload.type is messages.MessageType.RECIPIENT_REMOVE
        assert message_update_payload.activity is mock_activity
        assert message_update_payload.application is mock_application
        assert message_update_payload.message_reference is mock_reference
        assert message_update_payload.flags == messages.MessageFlag.CROSSPOSTED | messages.MessageFlag.IS_CROSSPOST

    def test_partial_message_update(self):
        message_update_obj = events.MessageUpdateEvent.deserialize({"id": "393939", "channel_id": "434949"})
        for key in message_update_obj.__slots__:
            if key in ("id", "channel_id"):
                continue
            assert getattr(message_update_obj, key) is entities.UNSET
        assert message_update_obj.id == 393939
        assert message_update_obj.channel_id == 434949


class TestMessageDeleteEvent:
    @pytest.fixture()
    def test_message_delete_payload(self):
        return {"channel_id": "20202020", "id": "2929", "guild_id": "1010101"}

    def test_deserialize(self, test_message_delete_payload):
        message_delete_obj = events.MessageDeleteEvent.deserialize(test_message_delete_payload)
        assert message_delete_obj.channel_id == 20202020
        assert message_delete_obj.message_id == 2929
        assert message_delete_obj.guild_id == 1010101


class TestMessageDeleteBulkEvent:
    @pytest.fixture()
    def test_message_delete_bulk_payload(self):
        return {"channel_id": "20202020", "ids": ["2929", "4394"], "guild_id": "1010101"}

    def test_deserialize(self, test_message_delete_bulk_payload):
        message_delete_bulk_obj = events.MessageDeleteBulkEvent.deserialize(test_message_delete_bulk_payload)
        assert message_delete_bulk_obj.channel_id == 20202020
        assert message_delete_bulk_obj.guild_id == 1010101
        assert message_delete_bulk_obj.message_ids == {2929, 4394}


class TestMessageReactionAddEvent:
    @pytest.fixture()
    def test_message_reaction_add_payload(self, test_member_payload, test_emoji_payload):
        return {
            "user_id": "9494949",
            "channel_id": "4393939",
            "message_id": "2993993",
            "guild_id": "49494949",
            "member": test_member_payload,
            "emoji": test_emoji_payload,
        }

    def test_deserialize(self, test_message_reaction_add_payload, test_member_payload, test_emoji_payload):
        mock_member = mock.MagicMock(guilds.GuildMember)
        mock_emoji = mock.MagicMock(emojis.UnknownEmoji)
        with _helpers.patch_marshal_attr(
            events.MessageReactionAddEvent,
            "member",
            deserializer=guilds.GuildMember.deserialize,
            return_value=mock_member,
        ) as patched_member_deserializer:
            with _helpers.patch_marshal_attr(
                events.MessageReactionAddEvent,
                "emoji",
                deserializer=emojis.deserialize_reaction_emoji,
                return_value=mock_emoji,
            ) as patched_emoji_deserializer:
                message_reaction_add_obj = events.MessageReactionAddEvent.deserialize(test_message_reaction_add_payload)
                patched_emoji_deserializer.assert_called_once_with(test_emoji_payload)
            patched_member_deserializer.assert_called_once_with(test_member_payload)
        assert message_reaction_add_obj.user_id == 9494949
        assert message_reaction_add_obj.channel_id == 4393939
        assert message_reaction_add_obj.message_id == 2993993
        assert message_reaction_add_obj.guild_id == 49494949
        assert message_reaction_add_obj.member is mock_member
        assert message_reaction_add_obj.emoji is mock_emoji


class TestMessageReactionRemoveEvent:
    @pytest.fixture()
    def test_message_reaction_remove_payload(self, test_emoji_payload):
        return {
            "user_id": "9494949",
            "channel_id": "4393939",
            "message_id": "2993993",
            "guild_id": "49494949",
            "emoji": test_emoji_payload,
        }

    def test_deserialize(self, test_message_reaction_remove_payload, test_emoji_payload):
        mock_emoji = mock.MagicMock(emojis.UnknownEmoji)
        with _helpers.patch_marshal_attr(
            events.MessageReactionRemoveEvent,
            "emoji",
            deserializer=emojis.deserialize_reaction_emoji,
            return_value=mock_emoji,
        ) as patched_emoji_deserializer:
            message_reaction_remove_obj = events.MessageReactionRemoveEvent.deserialize(
                test_message_reaction_remove_payload
            )
            patched_emoji_deserializer.assert_called_once_with(test_emoji_payload)
        assert message_reaction_remove_obj.user_id == 9494949
        assert message_reaction_remove_obj.channel_id == 4393939
        assert message_reaction_remove_obj.message_id == 2993993
        assert message_reaction_remove_obj.guild_id == 49494949
        assert message_reaction_remove_obj.emoji is mock_emoji


class TestMessageReactionRemoveAllEvent:
    @pytest.fixture()
    def test_reaction_remove_all_payload(self):
        return {"channel_id": "3493939", "message_id": "944949", "guild_id": "49494949"}

    def test_deserialize(self, test_reaction_remove_all_payload):
        message_reaction_remove_all_obj = events.MessageReactionRemoveAllEvent.deserialize(
            test_reaction_remove_all_payload
        )
        assert message_reaction_remove_all_obj.channel_id == 3493939
        assert message_reaction_remove_all_obj.message_id == 944949
        assert message_reaction_remove_all_obj.guild_id == 49494949


class TestMessageReactionRemoveEmojiEvent:
    @pytest.fixture()
    def test_message_reaction_remove_emoji_payload(self, test_emoji_payload):
        return {"channel_id": "4393939", "message_id": "2993993", "guild_id": "49494949", "emoji": test_emoji_payload}

    def test_deserialize(self, test_message_reaction_remove_emoji_payload, test_emoji_payload):
        mock_emoji = mock.MagicMock(emojis.UnknownEmoji)
        with _helpers.patch_marshal_attr(
            events.MessageReactionRemoveEmojiEvent,
            "emoji",
            deserializer=emojis.deserialize_reaction_emoji,
            return_value=mock_emoji,
        ) as patched_emoji_deserializer:
            message_reaction_remove_emoji_obj = events.MessageReactionRemoveEmojiEvent.deserialize(
                test_message_reaction_remove_emoji_payload
            )
            patched_emoji_deserializer.assert_called_once_with(test_emoji_payload)
        assert message_reaction_remove_emoji_obj.channel_id == 4393939
        assert message_reaction_remove_emoji_obj.message_id == 2993993
        assert message_reaction_remove_emoji_obj.guild_id == 49494949
        assert message_reaction_remove_emoji_obj.emoji is mock_emoji


# Doesn't declare any new fields.
class TestPresenceUpdateEvent:
    ...


class TestTypingStartEvent:
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
        with _helpers.patch_marshal_attr(
            events.TypingStartEvent, "member", deserializer=guilds.GuildMember.deserialize, return_value=mock_member
        ) as mock_member_deserialize:
            with mock.patch.object(datetime, "datetime", fromtimestamp=mock.MagicMock(return_value=mock_datetime)):
                typing_start_event_obj = events.TypingStartEvent.deserialize(test_typing_start_event_payload)
                datetime.datetime.fromtimestamp.assert_called_once_with(1231231231, datetime.timezone.utc)
            mock_member_deserialize.assert_called_once_with(test_member_payload)
        assert typing_start_event_obj.channel_id == 123123123
        assert typing_start_event_obj.guild_id == 33333333
        assert typing_start_event_obj.user_id == 2020202
        assert typing_start_event_obj.timestamp is mock_datetime
        assert typing_start_event_obj.member is mock_member


# Doesn't declare any new fields.
class TestUserUpdateEvent:
    ...


# Doesn't declare any new fields.
class TestVoiceStateUpdateEvent:
    ...


class TestVoiceServerUpdateEvent:
    @pytest.fixture()
    def test_voice_server_update_payload(self):
        return {"token": "a_token", "guild_id": "303030300303", "endpoint": "smart.loyal.discord.gg"}

    def test_deserialize(self, test_voice_server_update_payload):
        voice_server_update_obj = events.VoiceServerUpdateEvent.deserialize(test_voice_server_update_payload)
        assert voice_server_update_obj.token == "a_token"
        assert voice_server_update_obj.guild_id == 303030300303
        assert voice_server_update_obj.endpoint == "smart.loyal.discord.gg"


class TestWebhookUpdate:
    @pytest.fixture()
    def test_webhook_update_payload(self):
        return {"guild_id": "2929292", "channel_id": "94949494"}

    def test_deserialize(self, test_webhook_update_payload):
        webhook_update_obj = events.WebhookUpdate.deserialize(test_webhook_update_payload)
        assert webhook_update_obj.guild_id == 2929292
        assert webhook_update_obj.channel_id == 94949494
