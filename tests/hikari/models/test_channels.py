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
import datetime

import mock
import pytest

from hikari.models import bases
from hikari.models import channels
from hikari.models import permissions
from hikari.models import users
from hikari import application
from hikari.net import urls


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
        "topic": "¯\\_(ツ)_/¯",
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


@pytest.fixture()
def mock_app():
    return mock.MagicMock(application.Application)


class TestPartialChannel:
    @pytest.fixture()
    def test_partial_channel_payload(self):
        return {"id": "561884984214814750", "name": "general", "type": 0}

    def test_deserialize(self, test_partial_channel_payload, mock_app):
        partial_channel_obj = channels.PartialChannel.deserialize(test_partial_channel_payload, app=mock_app)
        assert partial_channel_obj.id == 561884984214814750
        assert partial_channel_obj.name == "general"
        assert partial_channel_obj.type is channels.ChannelType.GUILD_TEXT


class TestPermissionOverwriteType:
    def test___int__(self):
        assert str(channels.PermissionOverwriteType.ROLE) == "role"


class TestPermissionOverwrite:
    def test_deserialize(self, test_permission_overwrite_payload, mock_app):
        permission_overwrite_obj = channels.PermissionOverwrite.deserialize(
            test_permission_overwrite_payload, app=mock_app
        )
        assert (
            permission_overwrite_obj.allow
            == permissions.Permission.CREATE_INSTANT_INVITE | permissions.Permission.ADD_REACTIONS
        )
        assert permission_overwrite_obj.deny == permissions.Permission.EMBED_LINKS | permissions.Permission.ATTACH_FILES

    def test_serialize_full_overwrite(self):
        permission_overwrite_obj = channels.PermissionOverwrite(
            id=bases.Snowflake(11111111),
            type=channels.PermissionOverwriteType.ROLE,
            allow=permissions.Permission(1321),
            deny=permissions.Permission(39939),
        )
        assert permission_overwrite_obj.serialize() == {"id": "11111111", "type": "role", "allow": 1321, "deny": 39939}

    def test_serialize_partial_overwrite(self):
        permission_overwrite_obj = channels.PermissionOverwrite(
            id=bases.Snowflake(11111111), type=channels.PermissionOverwriteType.ROLE,
        )
        assert permission_overwrite_obj.serialize() == {"id": "11111111", "type": "role", "allow": 0, "deny": 0}

    def test_unset(self):
        permission_overwrite_obj = channels.PermissionOverwrite(
            id=None, type=None, allow=permissions.Permission(65), deny=permissions.Permission(49152)
        )
        assert permission_overwrite_obj.unset == permissions.Permission(49217)
        assert isinstance(permission_overwrite_obj.unset, permissions.Permission)


class TestDMChannel:
    def test_deserialize(self, test_dm_channel_payload, test_recipient_payload, mock_app):
        mock_user = mock.MagicMock(users.User, id=987)

        with mock.patch.object(users.User, "deserialize", return_value=mock_user) as patched_user_deserialize:
            channel_obj = channels.DMChannel.deserialize(test_dm_channel_payload, app=mock_app)
            patched_user_deserialize.assert_called_once_with(test_recipient_payload, app=mock_app)

        assert channel_obj.id == 123
        assert channel_obj.last_message_id == 456
        assert channel_obj.type == channels.ChannelType.DM
        assert channel_obj.recipients == {987: mock_user}


class TestGroupDMChannel:
    def test_deserialize(self, test_group_dm_channel_payload, test_recipient_payload, mock_app):
        mock_user = mock.MagicMock(users.User, id=987)

        with mock.patch.object(users.User, "deserialize", return_value=mock_user) as patched_user_deserialize:
            channel_obj = channels.GroupDMChannel.deserialize(test_group_dm_channel_payload, app=mock_app)
            patched_user_deserialize.assert_called_once_with(test_recipient_payload, app=mock_app)

        assert channel_obj.id == 123
        assert channel_obj.last_message_id == 456
        assert channel_obj.type == channels.ChannelType.GROUP_DM
        assert channel_obj.recipients == {987: mock_user}
        assert channel_obj.name == "Secret Developer Group"
        assert channel_obj.icon_hash == "123asdf123adsf"
        assert channel_obj.owner_id == 456
        assert channel_obj.application_id == 123789

    @pytest.fixture()
    def group_dm_obj(self):
        return channels.GroupDMChannel(
            id=bases.Snowflake(123123123),
            last_message_id=None,
            type=None,
            recipients=None,
            name=None,
            icon_hash="123asdf123adsf",
            owner_id=None,
            application_id=None,
        )

    def test_icon_url(self, group_dm_obj):
        mock_url = "https://cdn.discordapp.com/channel-icons/209333111222/hashmebaby.png?size=4096"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = group_dm_obj.icon_url
            urls.generate_cdn_url.assert_called_once()
        assert url == mock_url

    def test_format_icon_url(self, group_dm_obj):
        mock_url = "https://cdn.discordapp.com/channel-icons/22222/wowowowowo.jpg?size=42"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = channels.GroupDMChannel.format_icon_url(group_dm_obj, format_="jpg", size=42)
            urls.generate_cdn_url.assert_called_once_with(
                "channel-icons", "123123123", "123asdf123adsf", format_="jpg", size=42
            )
        assert url == mock_url

    def test_format_icon_url_returns_none(self, group_dm_obj):
        group_dm_obj.icon_hash = None
        with mock.patch.object(urls, "generate_cdn_url", return_value=...):
            url = channels.GroupDMChannel.format_icon_url(group_dm_obj, format_="jpg", size=42)
            urls.generate_cdn_url.assert_not_called()
        assert url is None


class TestGuildCategory:
    def test_deserialize(self, test_guild_category_payload, test_permission_overwrite_payload, mock_app):
        channel_obj = channels.GuildCategory.deserialize(test_guild_category_payload, app=mock_app)

        assert channel_obj.id == 123
        assert channel_obj.permission_overwrites == {
            4242: channels.PermissionOverwrite.deserialize(test_permission_overwrite_payload)
        }
        assert channel_obj.permission_overwrites[4242]._gateway_consumer is mock_app
        assert channel_obj.guild_id == 9876
        assert channel_obj.position == 3
        assert channel_obj.name == "Test"
        assert channel_obj.is_nsfw is True
        assert channel_obj.parent_id is None
        assert channel_obj.type == channels.ChannelType.GUILD_CATEGORY


class TestGuildTextChannel:
    def test_deserialize(self, test_guild_text_channel_payload, test_permission_overwrite_payload, mock_app):
        channel_obj = channels.GuildTextChannel.deserialize(test_guild_text_channel_payload, app=mock_app)

        assert channel_obj.id == 123
        assert channel_obj.permission_overwrites == {
            4242: channels.PermissionOverwrite.deserialize(test_permission_overwrite_payload)
        }
        assert channel_obj.permission_overwrites[4242]._gateway_consumer is mock_app
        assert channel_obj.guild_id == 567
        assert channel_obj.position == 6
        assert channel_obj.name == "general"
        assert channel_obj.topic == "¯\\_(ツ)_/¯"
        assert channel_obj.is_nsfw is True
        assert channel_obj.parent_id == 987
        assert channel_obj.type == channels.ChannelType.GUILD_TEXT
        assert channel_obj.last_message_id == 123456
        assert channel_obj.rate_limit_per_user == datetime.timedelta(seconds=2)


class TestGuildNewsChannel:
    def test_deserialize(self, test_guild_news_channel_payload, test_permission_overwrite_payload, mock_app):
        channel_obj = channels.GuildNewsChannel.deserialize(test_guild_news_channel_payload, app=mock_app)

        assert channel_obj.id == 567
        assert channel_obj.permission_overwrites == {
            4242: channels.PermissionOverwrite.deserialize(test_permission_overwrite_payload)
        }
        assert channel_obj.permission_overwrites[4242]._gateway_consumer is mock_app
        assert channel_obj.guild_id == 123
        assert channel_obj.position == 0
        assert channel_obj.name == "Important Announcements"
        assert channel_obj.topic == "Super Important Announcements"
        assert channel_obj.is_nsfw is True
        assert channel_obj.parent_id == 654
        assert channel_obj.type == channels.ChannelType.GUILD_NEWS
        assert channel_obj.last_message_id == 456


class TestGuildStoreChannel:
    def test_deserialize(self, test_guild_store_channel_payload, test_permission_overwrite_payload, mock_app):
        channel_obj = channels.GuildStoreChannel.deserialize(test_guild_store_channel_payload, app=mock_app)

        assert channel_obj.id == 123
        assert channel_obj.permission_overwrites == {
            4242: channels.PermissionOverwrite.deserialize(test_permission_overwrite_payload)
        }
        assert channel_obj.permission_overwrites[4242]._gateway_consumer is mock_app
        assert channel_obj.guild_id == 1234
        assert channel_obj.position == 2
        assert channel_obj.name == "Half Life 3"
        assert channel_obj.is_nsfw is True
        assert channel_obj.parent_id == 9876
        assert channel_obj.type == channels.ChannelType.GUILD_STORE


class TestGuildVoiceChannell:
    def test_deserialize(self, test_guild_voice_channel_payload, test_permission_overwrite_payload, mock_app):
        channel_obj = channels.GuildVoiceChannel.deserialize(test_guild_voice_channel_payload, app=mock_app)

        assert channel_obj.id == 123
        assert channel_obj.permission_overwrites == {
            4242: channels.PermissionOverwrite.deserialize(test_permission_overwrite_payload)
        }
        assert channel_obj.permission_overwrites[4242]._gateway_consumer is mock_app
        assert channel_obj.guild_id == 789
        assert channel_obj.position == 4
        assert channel_obj.name == "Secret Developer Discussions"
        assert channel_obj.is_nsfw is True
        assert channel_obj.parent_id == 456
        assert channel_obj.type == channels.ChannelType.GUILD_VOICE
        assert channel_obj.bitrate == 64000
        assert channel_obj.user_limit == 3


class TestGuildChannelBuilder:
    def test___init__(self):
        channel_builder_obj = channels.GuildChannelBuilder(
            channel_name="A channel", channel_type=channels.ChannelType.GUILD_TEXT
        )
        assert channel_builder_obj._payload == {"type": 0, "name": "A channel"}

    def test_is_sfw(self):
        channel_builder_obj = channels.GuildChannelBuilder("A channel", channels.ChannelType.GUILD_TEXT).is_nsfw()
        assert channel_builder_obj._payload == {"type": 0, "name": "A channel", "nsfw": True}

    def test_with_permission_overwrites(self):
        channel_builder_obj = channels.GuildChannelBuilder(
            "A channel", channels.ChannelType.GUILD_TEXT
        ).with_permission_overwrites(
            [channels.PermissionOverwrite(id=1231, type=channels.PermissionOverwriteType.MEMBER)]
        )
        assert channel_builder_obj._payload == {
            "type": 0,
            "name": "A channel",
            "permission_overwrites": [{"type": "member", "id": "1231", "allow": 0, "deny": 0}],
        }

    def test_with_topic(self):
        channel_builder_obj = channels.GuildChannelBuilder("A channel", channels.ChannelType.GUILD_TEXT).with_topic(
            "A TOPIC"
        )
        assert channel_builder_obj._payload == {"type": 0, "name": "A channel", "topic": "A TOPIC"}

    def test_with_bitrate(self):
        channel_builder_obj = channels.GuildChannelBuilder("A channel", channels.ChannelType.GUILD_TEXT).with_bitrate(
            123123
        )
        assert channel_builder_obj._payload == {"type": 0, "name": "A channel", "bitrate": 123123}

    def test_with_user_limit(self):
        channel_builder_obj = channels.GuildChannelBuilder(
            "A channel", channels.ChannelType.GUILD_TEXT
        ).with_user_limit(123123)
        assert channel_builder_obj._payload == {"type": 0, "name": "A channel", "user_limit": 123123}

    @pytest.mark.parametrize("rate_limit", [3232, datetime.timedelta(seconds=3232)])
    def test_with_rate_limit_per_user(self, rate_limit):
        channel_builder_obj = channels.GuildChannelBuilder(
            "A channel", channels.ChannelType.GUILD_TEXT
        ).with_rate_limit_per_user(rate_limit)
        assert channel_builder_obj._payload == {"type": 0, "name": "A channel", "rate_limit_per_user": 3232}

    @pytest.mark.parametrize(
        "category", [54321, bases.Snowflake(54321)],
    )
    def test_with_parent_category(self, category):
        channel_builder_obj = channels.GuildChannelBuilder(
            "A channel", channels.ChannelType.GUILD_TEXT
        ).with_parent_category(category)
        assert channel_builder_obj._payload == {"type": 0, "name": "A channel", "parent_id": "54321"}

    @pytest.mark.parametrize("placeholder_id", [444444, bases.Snowflake(444444)])
    def test_with_id(self, placeholder_id):
        channel_builder_obj = channels.GuildChannelBuilder("A channel", channels.ChannelType.GUILD_TEXT).with_id(
            placeholder_id
        )
        assert channel_builder_obj._payload == {"type": 0, "name": "A channel", "id": "444444"}

    def test_serialize(self):
        mock_payload = {"id": "424242", "name": "aChannel", "type": 4, "nsfw": True}
        channel_builder_obj = channels.GuildChannelBuilder("A channel", channels.ChannelType.GUILD_TEXT)
        channel_builder_obj._payload = mock_payload
        assert channel_builder_obj.serialize() == mock_payload


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


def test_deserialize_channel_type_passes_kwargs(test_dm_channel_payload, mock_app):
    channel_obj = channels.deserialize_channel(test_dm_channel_payload, app=mock_app)
    assert channel_obj._app is mock_app
