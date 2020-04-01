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
from hikari.core import permissions
from hikari.core import users


@pytest.fixture()
def test_recipient_payload():
    return {"username": "someone", "discriminator": "9999", "id": "987", "avatar": "qrqwefasfefd"}


@pytest.fixture()
def test_permission_overwrite_payload():
    return {"id": "4242", "type": "member", "allow": 65, "deny": 49152}


@pytest.fixture()
def test_dm_channel_payload(test_recipient_payload):
    return {
        "id": "123",
        "last_message_id": "456",
        "type": 1,
        "recipients": [test_recipient_payload],
    }


@pytest.fixture()
def test_group_dm_channel_payload(test_recipient_payload):
    return {
        "id": "123",
        "name": "Secret Developer Group",
        "icon": "123asdf123adsf",
        "owner_id": "456",
        "application_id": "123789",
        "last_message_id": "456",
        "type": 3,
        "recipients": [test_recipient_payload],
    }


@pytest.fixture()
def test_guild_category_payload(test_permission_overwrite_payload):
    return {
        "id": "123",
        "permission_overwrites": [test_permission_overwrite_payload],
        "name": "Test",
        "parent_id": None,
        "nsfw": True,
        "position": 3,
        "guild_id": "9876",
        "type": 4,
    }


@pytest.fixture()
def test_guild_text_channel_payload(test_permission_overwrite_payload):
    return {
        "id": "123",
        "guild_id": "567",
        "name": "general",
        "type": 0,
        "position": 6,
        "permission_overwrites": [test_permission_overwrite_payload],
        "rate_limit_per_user": 2,
        "nsfw": True,
        "topic": "¯\_(ツ)_/¯",
        "last_message_id": "123456",
        "parent_id": "987",
    }


@pytest.fixture()
def test_guild_news_channel_payload(test_permission_overwrite_payload):
    return {
        "id": "567",
        "guild_id": "123",
        "name": "Important Announcements",
        "type": 5,
        "position": 0,
        "permission_overwrites": [test_permission_overwrite_payload],
        "nsfw": True,
        "topic": "Super Important Announcements",
        "last_message_id": "456",
        "parent_id": "654",
    }


@pytest.fixture()
def test_guild_store_channel_payload(test_permission_overwrite_payload):
    return {
        "id": "123",
        "permission_overwrites": [test_permission_overwrite_payload],
        "name": "Half Life 3",
        "parent_id": "9876",
        "nsfw": True,
        "position": 2,
        "guild_id": "1234",
        "type": 6,
    }


@pytest.fixture()
def test_guild_voice_channel_payload(test_permission_overwrite_payload):
    return {
        "id": "123",
        "guild_id": "789",
        "name": "Secret Developer Discussions",
        "type": 2,
        "nsfw": True,
        "position": 4,
        "permission_overwrites": [test_permission_overwrite_payload],
        "bitrate": 64000,
        "user_limit": 3,
        "parent_id": "456",
    }


class TestPartialChannel:
    @pytest.fixture()
    def test_partial_channel_payload(self):
        return {"id": "561884984214814750", "name": "general", "type": 0}

    def test_deserialize(self, test_partial_channel_payload):
        partial_channel_obj = channels.PartialChannel.deserialize(test_partial_channel_payload)
        assert partial_channel_obj.id == 561884984214814750
        assert partial_channel_obj.name == "general"
        assert partial_channel_obj.type is channels.ChannelType.GUILD_TEXT


class TestPermissionOverwrite:
    def test_deserialize(self, test_permission_overwrite_payload):
        permission_overwrite_obj = channels.PermissionOverwrite.deserialize(test_permission_overwrite_payload)
        assert (
            permission_overwrite_obj.allow
            == permissions.Permission.CREATE_INSTANT_INVITE | permissions.Permission.ADD_REACTIONS
        )
        assert permission_overwrite_obj.deny == permissions.Permission.EMBED_LINKS | permissions.Permission.ATTACH_FILES
        assert permission_overwrite_obj.unset == permissions.Permission(49217)
        assert isinstance(permission_overwrite_obj.unset, permissions.Permission)


class TestDMChannel:
    def test_deserialize(self, test_dm_channel_payload, test_recipient_payload):
        mock_user = mock.MagicMock(users.User, id=987)

        with mock.patch.object(users.User, "deserialize", return_value=mock_user) as patched_user_deserialize:
            channel_obj = channels.DMChannel.deserialize(test_dm_channel_payload)
            patched_user_deserialize.assert_called_once_with(test_recipient_payload)

        assert channel_obj.id == 123
        assert channel_obj.last_message_id == 456
        assert channel_obj.type == channels.ChannelType.DM
        assert channel_obj.recipients == {987: mock_user}


class TestGroupDMChannel:
    def test_deserialize(self, test_group_dm_channel_payload, test_recipient_payload):
        mock_user = mock.MagicMock(users.User, id=987)

        with mock.patch.object(users.User, "deserialize", return_value=mock_user) as patched_user_deserialize:
            channel_obj = channels.GroupDMChannel.deserialize(test_group_dm_channel_payload)
            patched_user_deserialize.assert_called_once_with(test_recipient_payload)

        assert channel_obj.id == 123
        assert channel_obj.last_message_id == 456
        assert channel_obj.type == channels.ChannelType.GROUP_DM
        assert channel_obj.recipients == {987: mock_user}
        assert channel_obj.name == "Secret Developer Group"
        assert channel_obj.icon_hash == "123asdf123adsf"
        assert channel_obj.owner_id == 456
        assert channel_obj.application_id == 123789


class TestGuildCategory:
    def test_deserialize(self, test_guild_category_payload, test_permission_overwrite_payload):
        channel_obj = channels.GuildCategory.deserialize(test_guild_category_payload)

        assert channel_obj.id == 123
        assert channel_obj.permission_overwrites == {
            4242: channels.PermissionOverwrite.deserialize(test_permission_overwrite_payload)
        }
        assert channel_obj.guild_id == 9876
        assert channel_obj.position == 3
        assert channel_obj.name == "Test"
        assert channel_obj.is_nsfw is True
        assert channel_obj.parent_id is None
        assert channel_obj.type == channels.ChannelType.GUILD_CATEGORY


class TestGuildTextChannel:
    def test_deserialize(self, test_guild_text_channel_payload, test_permission_overwrite_payload):
        channel_obj = channels.GuildTextChannel.deserialize(test_guild_text_channel_payload)

        assert channel_obj.id == 123
        assert channel_obj.permission_overwrites == {
            4242: channels.PermissionOverwrite.deserialize(test_permission_overwrite_payload)
        }
        assert channel_obj.guild_id == 567
        assert channel_obj.position == 6
        assert channel_obj.name == "general"
        assert channel_obj.topic == "¯\_(ツ)_/¯"
        assert channel_obj.is_nsfw is True
        assert channel_obj.parent_id == 987
        assert channel_obj.type == channels.ChannelType.GUILD_TEXT
        assert channel_obj.last_message_id == 123456
        assert channel_obj.rate_limit_per_user == datetime.timedelta(seconds=2)


class TestGuildNewsChannel:
    def test_deserialize(self, test_guild_news_channel_payload, test_permission_overwrite_payload):
        channel_obj = channels.GuildNewsChannel.deserialize(test_guild_news_channel_payload)

        assert channel_obj.id == 567
        assert channel_obj.permission_overwrites == {
            4242: channels.PermissionOverwrite.deserialize(test_permission_overwrite_payload)
        }
        assert channel_obj.guild_id == 123
        assert channel_obj.position == 0
        assert channel_obj.name == "Important Announcements"
        assert channel_obj.topic == "Super Important Announcements"
        assert channel_obj.is_nsfw is True
        assert channel_obj.parent_id == 654
        assert channel_obj.type == channels.ChannelType.GUILD_NEWS
        assert channel_obj.last_message_id == 456


class TestGuildStoreChannel:
    def test_deserialize(self, test_guild_store_channel_payload, test_permission_overwrite_payload):
        channel_obj = channels.GuildStoreChannel.deserialize(test_guild_store_channel_payload)

        assert channel_obj.id == 123
        assert channel_obj.permission_overwrites == {
            4242: channels.PermissionOverwrite.deserialize(test_permission_overwrite_payload)
        }
        assert channel_obj.guild_id == 1234
        assert channel_obj.position == 2
        assert channel_obj.name == "Half Life 3"
        assert channel_obj.is_nsfw is True
        assert channel_obj.parent_id == 9876
        assert channel_obj.type == channels.ChannelType.GUILD_STORE


class TestGuildVoiceChannell:
    def test_deserialize(self, test_guild_voice_channel_payload, test_permission_overwrite_payload):
        channel_obj = channels.GuildVoiceChannel.deserialize(test_guild_voice_channel_payload)

        assert channel_obj.id == 123
        assert channel_obj.permission_overwrites == {
            4242: channels.PermissionOverwrite.deserialize(test_permission_overwrite_payload)
        }
        assert channel_obj.guild_id == 789
        assert channel_obj.position == 4
        assert channel_obj.name == "Secret Developer Discussions"
        assert channel_obj.is_nsfw is True
        assert channel_obj.parent_id == 456
        assert channel_obj.type == channels.ChannelType.GUILD_VOICE
        assert channel_obj.bitrate == 64000
        assert channel_obj.user_limit == 3


def test_deserialize_channel_returns_correct_type(
    test_dm_channel_payload,
    test_group_dm_channel_payload,
    test_guild_category_payload,
    test_guild_text_channel_payload,
    test_guild_news_channel_payload,
    test_guild_store_channel_payload,
    test_guild_voice_channel_payload,
):
    assert isinstance(channels.deserialize_channel(test_dm_channel_payload), channels.DMChannel)
    assert isinstance(channels.deserialize_channel(test_group_dm_channel_payload), channels.GroupDMChannel)
    assert isinstance(channels.deserialize_channel(test_guild_category_payload), channels.GuildCategory)
    assert isinstance(channels.deserialize_channel(test_guild_text_channel_payload), channels.GuildTextChannel)
    assert isinstance(channels.deserialize_channel(test_guild_news_channel_payload), channels.GuildNewsChannel)
    assert isinstance(channels.deserialize_channel(test_guild_store_channel_payload), channels.GuildStoreChannel)
    assert isinstance(channels.deserialize_channel(test_guild_voice_channel_payload), channels.GuildVoiceChannel)
