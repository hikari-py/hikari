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
import contextlib
import datetime

import mock
import pytest

from hikari import channels
from hikari import colors
from hikari import emojis
from hikari import guilds
from hikari import permissions
from hikari import unset
from hikari import users
from hikari.clients import components
from hikari.internal import conversions
from hikari.internal import urls
from tests.hikari import _helpers


@pytest.fixture
def test_emoji_payload():
    return {
        "id": "41771983429993937",
        "name": "LUL",
        "roles": ["41771983429993000", "41771983429993111"],
        "user": {
            "username": "Luigi",
            "discriminator": "0002",
            "id": "96008815106887111",
            "avatar": "5500909a3274e1812beb4e8de6631111",
        },
        "require_colons": True,
        "managed": False,
        "animated": False,
    }


@pytest.fixture
def test_roles_payload():
    return {
        "id": "41771983423143936",
        "name": "WE DEM BOYZZ!!!!!!",
        "color": 3_447_003,
        "hoist": True,
        "position": 0,
        "permissions": 66_321_471,
        "managed": False,
        "mentionable": False,
    }


@pytest.fixture
def test_channel_payload():
    return {
        "type": 0,
        "id": "1234567",
        "guild_id": "696969",
        "position": 100,
        "permission_overwrites": [],
        "nsfw": True,
        "parent_id": None,
        "rate_limit_per_user": 420,
        "topic": "nsfw stuff",
        "name": "shh!",
        "last_message_id": "1234",
    }


@pytest.fixture
def test_user_payload():
    return {
        "id": "123456",
        "username": "Boris Johnson",
        "discriminator": "6969",
        "avatar": "1a2b3c4d",
        "mfa_enabled": True,
        "locale": "gb",
        "system": True,
        "bot": True,
        "flags": 0b00101101,
        "premium_type": 1,
        "public_flags": 0b0001101,
    }


@pytest.fixture
def test_member_payload(test_user_payload):
    return {
        "nick": "foobarbaz",
        "roles": ["11111", "22222", "33333", "44444"],
        "joined_at": "2015-04-26T06:26:56.936000+00:00",
        "premium_since": "2019-05-17T06:26:56.936000+00:00",
        # These should be completely ignored.
        "deaf": False,
        "mute": True,
        "user": test_user_payload,
    }


@pytest.fixture
def test_voice_state_payload():
    return {
        "channel_id": "432123321",
        "user_id": "6543453",
        "session_id": "350a109226bd6f43c81f12c7c08de20a",
        "deaf": False,
        "mute": True,
        "self_deaf": True,
        "self_mute": False,
        "self_stream": True,
        "suppress": False,
    }


@pytest.fixture()
def test_activity_party_payload():
    return {"id": "spotify:3234234234", "size": [2, 5]}


@pytest.fixture()
def test_activity_timestamps_payload():
    return {
        "start": 1584996792798,
        "end": 1999999792798,
    }


@pytest.fixture()
def test_activity_assets_payload():
    return {
        "large_image": "34234234234243",
        "large_text": "LARGE TEXT",
        "small_image": "3939393",
        "small_text": "small text",
    }


@pytest.fixture()
def test_activity_secrets_payload():
    return {"join": "who's a good secret?", "spectate": "I'm a good secret", "match": "No."}


@pytest.fixture()
def test_presence_activity_payload(
    test_activity_timestamps_payload,
    test_emoji_payload,
    test_activity_party_payload,
    test_activity_assets_payload,
    test_activity_secrets_payload,
):
    return {
        "name": "an activity",
        "type": 1,
        "url": "https://69.420.owouwunyaa",
        "created_at": 1584996792798,
        "timestamps": test_activity_timestamps_payload,
        "application_id": "40404040404040",
        "details": "They are doing stuff",
        "state": "STATED",
        "emoji": test_emoji_payload,
        "party": test_activity_party_payload,
        "assets": test_activity_assets_payload,
        "secrets": test_activity_secrets_payload,
        "instance": True,
        "flags": 3,
    }


@pytest.fixture()
def test_partial_guild_payload():
    return {
        "id": "152559372126519269",
        "name": "Isopropyl",
        "icon": "d4a983885dsaa7691ce8bcaaf945a",
        "features": ["DISCOVERABLE"],
    }


@pytest.fixture()
def test_guild_preview_payload(test_emoji_payload):
    return {
        "id": "152559372126519269",
        "name": "Isopropyl",
        "icon": "d4a983885dsaa7691ce8bcaaf945a",
        "splash": "dsa345tfcdg54b",
        "discovery_splash": "lkodwaidi09239uid",
        "emojis": [test_emoji_payload],
        "features": ["DISCOVERABLE"],
        "approximate_member_count": 69,
        "approximate_presence_count": 42,
        "description": "A DESCRIPTION.",
    }


@pytest.fixture
def test_guild_payload(
    test_emoji_payload,
    test_roles_payload,
    test_channel_payload,
    test_member_payload,
    test_voice_state_payload,
    test_guild_member_presence,
):
    return {
        "afk_channel_id": "99998888777766",
        "afk_timeout": 1200,
        "application_id": "39494949",
        "approximate_member_count": 15,
        "approximate_presence_count": 7,
        "banner": "1a2b3c",
        "channels": [test_channel_payload],
        "default_message_notifications": 1,
        "description": "This is a server I guess, its a bit crap though",
        "discovery_splash": "famfamFAMFAMfam",
        "embed_channel_id": "9439394949",
        "embed_enabled": True,
        "emojis": [test_emoji_payload],
        "explicit_content_filter": 2,
        "features": ["ANIMATED_ICON", "MORE_EMOJI", "NEWS", "SOME_UNDOCUMENTED_FEATURE"],
        "icon": "1a2b3c4d",
        "id": "265828729970753537",
        "joined_at": "2019-05-17T06:26:56.936000+00:00",
        "large": False,
        "max_members": 25000,
        "max_presences": 250,
        "max_video_channel_users": 25,
        "member_count": 14,
        "members": [test_member_payload],
        "mfa_level": 1,
        "name": "L33t guild",
        "owner_id": "6969696",
        "permissions": 66_321_471,
        "preferred_locale": "en-GB",
        "premium_subscription_count": 1,
        "premium_tier": 2,
        "presences": [test_guild_member_presence],
        "public_updates_channel_id": "33333333",
        "region": "eu-central",
        "roles": [test_roles_payload],
        "rules_channel_id": "42042069",
        "splash": "0ff0ff0ff",
        "system_channel_flags": 3,
        "system_channel_id": "19216801",
        "unavailable": False,
        "vanity_url_code": "loool",
        "verification_level": 4,
        "voice_states": [test_voice_state_payload],
        "widget_channel_id": "9439394949",
        "widget_enabled": True,
    }


@pytest.fixture()
def mock_components():
    return mock.MagicMock(components.Components)


class TestGuildEmbed:
    @pytest.fixture()
    def test_guild_embed_payload(self):
        return {"channel_id": "123123123", "enabled": True}

    def test_deserialize(self, test_guild_embed_payload, mock_components):
        guild_embed_obj = guilds.GuildEmbed.deserialize(test_guild_embed_payload, components=mock_components)
        assert guild_embed_obj.channel_id == 123123123
        assert guild_embed_obj.is_enabled is True


class TestGuildMember:
    def test_deserialize(self, test_member_payload, test_user_payload, mock_components):
        mock_user = mock.MagicMock(users.User)
        mock_datetime_1 = mock.MagicMock(datetime.datetime)
        mock_datetime_2 = mock.MagicMock(datetime.datetime)
        stack = contextlib.ExitStack()
        patched_user_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                guilds.GuildMember, "user", deserializer=users.User.deserialize, return_value=mock_user
            )
        )
        patched_joined_at_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                guilds.GuildMember,
                "joined_at",
                deserializer=conversions.parse_iso_8601_ts,
                return_value=mock_datetime_1,
            )
        )
        patched_premium_since_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                guilds.GuildMember,
                "premium_since",
                deserializer=conversions.parse_iso_8601_ts,
                return_value=mock_datetime_2,
            )
        )
        with stack:
            guild_member_obj = guilds.GuildMember.deserialize(test_member_payload, components=mock_components)
            patched_premium_since_deserializer.assert_called_once_with("2019-05-17T06:26:56.936000+00:00")
            patched_joined_at_deserializer.assert_called_once_with("2015-04-26T06:26:56.936000+00:00")
            patched_user_deserializer.assert_called_once_with(test_user_payload, components=mock_components)
        assert guild_member_obj.user is mock_user
        assert guild_member_obj.nickname == "foobarbaz"
        assert guild_member_obj.role_ids == [11111, 22222, 33333, 44444]
        assert guild_member_obj.joined_at is mock_datetime_1
        assert guild_member_obj.premium_since is mock_datetime_2
        assert guild_member_obj.is_deaf is False
        assert guild_member_obj.is_mute is True


class TestPartialGuildRole:
    @pytest.fixture()
    def test_partial_guild_role_payload(self):
        return {
            "id": "41771983423143936",
            "name": "WE DEM BOYZZ!!!!!!",
        }

    def test_deserialize(self, test_partial_guild_role_payload, mock_components):
        partial_guild_role_obj = guilds.PartialGuildRole.deserialize(
            test_partial_guild_role_payload, components=mock_components
        )
        assert partial_guild_role_obj.name == "WE DEM BOYZZ!!!!!!"


class TestGuildRole:
    @pytest.fixture()
    def test_guild_role_payload(self):
        return {
            "id": "41771983423143936",
            "name": "WE DEM BOYZZ!!!!!!",
            "color": 3_447_003,
            "hoist": True,
            "position": 0,
            "permissions": 66_321_471,
            "managed": False,
            "mentionable": False,
        }

    def test_deserialize(self, test_guild_role_payload, mock_components):
        guild_role_obj = guilds.GuildRole.deserialize(test_guild_role_payload, components=mock_components)
        assert guild_role_obj.color == 3_447_003
        assert guild_role_obj.is_hoisted is True
        assert guild_role_obj.position == 0
        assert guild_role_obj.permissions == 66_321_471
        assert guild_role_obj.is_managed is False
        assert guild_role_obj.is_mentionable is False

    def test_serialize_full_role(self):
        guild_role_obj = guilds.GuildRole(
            name="aRole",
            color=colors.Color(444),
            is_hoisted=True,
            position=42,
            permissions=permissions.Permission(69),
            is_mentionable=True,
            id=123,
        )
        assert guild_role_obj.serialize() == {
            "name": "aRole",
            "color": 444,
            "hoist": True,
            "position": 42,
            "permissions": 69,
            "mentionable": True,
            "id": "123",
        }

    def test_serialize_partial_role(self):
        guild_role_obj = guilds.GuildRole(name="aRole", id=123)
        assert guild_role_obj.serialize() == {
            "name": "aRole",
            "color": 0,
            "hoist": False,
            "permissions": 0,
            "mentionable": False,
            "id": "123",
        }


class TestActivityTimestamps:
    def test_deserialize(self, test_activity_timestamps_payload, mock_components):
        mock_start_date = mock.MagicMock(datetime.datetime)
        mock_end_date = mock.MagicMock(datetime.datetime)
        stack = contextlib.ExitStack()
        patched_start_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                guilds.ActivityTimestamps,
                "start",
                deserializer=conversions.unix_epoch_to_datetime,
                return_value=mock_start_date,
            )
        )
        patched_end_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                guilds.ActivityTimestamps,
                "end",
                deserializer=conversions.unix_epoch_to_datetime,
                return_value=mock_end_date,
            )
        )
        with stack:
            activity_timestamps_obj = guilds.ActivityTimestamps.deserialize(
                test_activity_timestamps_payload, components=mock_components
            )
            patched_end_deserializer.assert_called_once_with(1999999792798)
            patched_start_deserializer.assert_called_once_with(1584996792798)
        assert activity_timestamps_obj.start is mock_start_date
        assert activity_timestamps_obj.end is mock_end_date


class TestActivityParty:
    @pytest.fixture()
    def test_activity_party_obj(self, test_activity_party_payload):
        return guilds.ActivityParty.deserialize(test_activity_party_payload)

    def test_deserialize(self, test_activity_party_obj):
        assert test_activity_party_obj.id == "spotify:3234234234"
        assert test_activity_party_obj._size_information == (2, 5)

    def test_current_size(self, test_activity_party_obj):
        assert test_activity_party_obj.current_size == 2

    def test_current_size_when_null(self, test_activity_party_obj):
        test_activity_party_obj._size_information = None
        assert test_activity_party_obj.current_size is None

    def test_max_size(self, test_activity_party_obj):
        assert test_activity_party_obj.max_size == 5

    def test_max_size_when_null(self, test_activity_party_obj):
        test_activity_party_obj._size_information = None
        assert test_activity_party_obj.max_size is None


class TestActivityAssets:
    def test_deserialize(self, test_activity_assets_payload, mock_components):
        activity_assets_obj = guilds.ActivityAssets.deserialize(
            test_activity_assets_payload, components=mock_components
        )
        assert activity_assets_obj.large_image == "34234234234243"
        assert activity_assets_obj.large_text == "LARGE TEXT"
        assert activity_assets_obj.small_image == "3939393"
        assert activity_assets_obj.small_text == "small text"


class TestActivitySecret:
    def test_deserialize(self, test_activity_secrets_payload, mock_components):
        activity_secret_obj = guilds.ActivitySecret.deserialize(
            test_activity_secrets_payload, components=mock_components
        )
        assert activity_secret_obj.join == "who's a good secret?"
        assert activity_secret_obj.spectate == "I'm a good secret"
        assert activity_secret_obj.match == "No."


class TestPresenceActivity:
    def test_deserialize(
        self,
        test_presence_activity_payload,
        test_activity_secrets_payload,
        test_activity_assets_payload,
        test_activity_party_payload,
        test_emoji_payload,
        test_activity_timestamps_payload,
        mock_components,
    ):
        mock_created_at = mock.MagicMock(datetime.datetime)
        mock_emoji = mock.MagicMock(emojis.CustomEmoji)
        stack = contextlib.ExitStack()
        patched_created_at_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                guilds.PresenceActivity,
                "created_at",
                deserializer=conversions.unix_epoch_to_datetime,
                return_value=mock_created_at,
            )
        )
        patched_emoji_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                guilds.PresenceActivity,
                "emoji",
                deserializer=emojis.deserialize_reaction_emoji,
                return_value=mock_emoji,
            )
        )
        with stack:
            presence_activity_obj = guilds.PresenceActivity.deserialize(
                test_presence_activity_payload, components=mock_components
            )
            patched_emoji_deserializer.assert_called_once_with(test_emoji_payload, components=mock_components)
            patched_created_at_deserializer.assert_called_once_with(1584996792798)
        assert presence_activity_obj.name == "an activity"
        assert presence_activity_obj.type is guilds.ActivityType.STREAMING
        assert presence_activity_obj.url == "https://69.420.owouwunyaa"
        assert presence_activity_obj.created_at is mock_created_at
        assert presence_activity_obj.timestamps == guilds.ActivityTimestamps.deserialize(
            test_activity_timestamps_payload
        )
        assert presence_activity_obj.timestamps._components is mock_components
        assert presence_activity_obj.application_id == 40404040404040
        assert presence_activity_obj.details == "They are doing stuff"
        assert presence_activity_obj.state == "STATED"
        assert presence_activity_obj.emoji is mock_emoji
        assert presence_activity_obj.party == guilds.ActivityParty.deserialize(test_activity_party_payload)
        assert presence_activity_obj.party._components is mock_components
        assert presence_activity_obj.assets == guilds.ActivityAssets.deserialize(test_activity_assets_payload)
        assert presence_activity_obj.assets._components is mock_components
        assert presence_activity_obj.secrets == guilds.ActivitySecret.deserialize(test_activity_secrets_payload)
        assert presence_activity_obj.secrets._components is mock_components
        assert presence_activity_obj.is_instance is True
        assert presence_activity_obj.flags == guilds.ActivityFlag.INSTANCE | guilds.ActivityFlag.JOIN


@pytest.fixture()
def test_client_status_payload():
    return {"desktop": "online", "mobile": "idle"}


class TestClientStatus:
    def test_deserialize(self, test_client_status_payload, mock_components):
        client_status_obj = guilds.ClientStatus.deserialize(test_client_status_payload, components=mock_components)
        assert client_status_obj.desktop is guilds.PresenceStatus.ONLINE
        assert client_status_obj.mobile is guilds.PresenceStatus.IDLE
        assert client_status_obj.web is guilds.PresenceStatus.OFFLINE


class TestPresenceUser:
    def test_deserialize_filled_presence_user(self, test_user_payload, mock_components):
        presence_user_obj = guilds.PresenceUser.deserialize(test_user_payload, components=mock_components)
        assert presence_user_obj.username == "Boris Johnson"
        assert presence_user_obj.discriminator == "6969"
        assert presence_user_obj.avatar_hash == "1a2b3c4d"
        assert presence_user_obj.is_system is True
        assert presence_user_obj.is_bot is True
        assert presence_user_obj.flags == users.UserFlag(0b0001101)

    def test_deserialize_partial_presence_user(self, mock_components):
        presence_user_obj = guilds.PresenceUser.deserialize({"id": "115590097100865541"}, components=mock_components)
        assert presence_user_obj.id == 115590097100865541
        for attr in presence_user_obj.__slots__:
            if attr not in ("id", "_components"):
                assert getattr(presence_user_obj, attr) is unset.UNSET

    @pytest.fixture()
    def test_presence_user_obj(self):
        return guilds.PresenceUser(
            id=4242424242,
            discriminator=unset.UNSET,
            username=unset.UNSET,
            avatar_hash=unset.UNSET,
            is_bot=unset.UNSET,
            is_system=unset.UNSET,
            flags=unset.UNSET,
        )

    def test_avatar_url(self, test_presence_user_obj):
        mock_url = mock.MagicMock(str)
        test_presence_user_obj.discriminator = 2222
        with mock.patch.object(users.User, "format_avatar_url", return_value=mock_url):
            assert test_presence_user_obj.avatar_url is mock_url
            users.User.format_avatar_url.assert_called_once()

    @pytest.mark.parametrize(["avatar_hash", "discriminator"], [("dwaea22", unset.UNSET), (unset.UNSET, "2929")])
    def test_format_avatar_url_when_discriminator_or_avatar_hash_set_without_optionals(
        self, test_presence_user_obj, avatar_hash, discriminator
    ):
        test_presence_user_obj.avatar_hash = avatar_hash
        test_presence_user_obj.discriminator = discriminator
        mock_url = mock.MagicMock(str)
        with mock.patch.object(users.User, "format_avatar_url", return_value=mock_url):
            assert test_presence_user_obj.format_avatar_url() is mock_url
            users.User.format_avatar_url.assert_called_once_with(fmt=None, size=4096)

    @pytest.mark.parametrize(["avatar_hash", "discriminator"], [("dwaea22", unset.UNSET), (unset.UNSET, "2929")])
    def test_format_avatar_url_when_discriminator_or_avatar_hash_set_with_optionals(
        self, test_presence_user_obj, avatar_hash, discriminator
    ):
        test_presence_user_obj.avatar_hash = avatar_hash
        test_presence_user_obj.discriminator = discriminator
        mock_url = mock.MagicMock(str)
        with mock.patch.object(users.User, "format_avatar_url", return_value=mock_url):
            assert test_presence_user_obj.format_avatar_url(fmt="nyaapeg", size=2048) is mock_url
            users.User.format_avatar_url.assert_called_once_with(fmt="nyaapeg", size=2048)

    def test_format_avatar_url_when_discriminator_and_avatar_hash_unset(self, test_presence_user_obj):
        test_presence_user_obj.avatar_hash = unset.UNSET
        test_presence_user_obj.discriminator = unset.UNSET
        with mock.patch.object(users.User, "format_avatar_url", return_value=...):
            assert test_presence_user_obj.format_avatar_url() is unset.UNSET
            users.User.format_avatar_url.assert_not_called()

    def test_default_avatar_when_discriminator_set(self, test_presence_user_obj):
        test_presence_user_obj.discriminator = 4242
        assert test_presence_user_obj.default_avatar == 2

    def test_default_avatar_when_discriminator_unset(self, test_presence_user_obj):
        test_presence_user_obj.discriminator = unset.UNSET
        assert test_presence_user_obj.default_avatar is unset.UNSET


@pytest.fixture()
def test_guild_member_presence(test_user_payload, test_presence_activity_payload, test_client_status_payload):
    return {
        "user": test_user_payload,
        "roles": ["49494949"],
        "game": test_presence_activity_payload,
        "guild_id": "44004040",
        "status": "dnd",
        "activities": [test_presence_activity_payload],
        "client_status": test_client_status_payload,
        "premium_since": "2015-04-26T06:26:56.936000+00:00",
        "nick": "Nick",
    }


class TestGuildMemberPresence:
    def test_deserialize(
        self,
        test_guild_member_presence,
        test_user_payload,
        test_presence_activity_payload,
        test_client_status_payload,
        mock_components,
    ):
        mock_since = mock.MagicMock(datetime.datetime)
        with _helpers.patch_marshal_attr(
            guilds.GuildMemberPresence,
            "premium_since",
            deserializer=conversions.parse_iso_8601_ts,
            return_value=mock_since,
        ) as patched_since_deserializer:
            guild_member_presence_obj = guilds.GuildMemberPresence.deserialize(
                test_guild_member_presence, components=mock_components
            )
            patched_since_deserializer.assert_called_once_with("2015-04-26T06:26:56.936000+00:00")
        assert guild_member_presence_obj.user == guilds.PresenceUser.deserialize(test_user_payload)
        assert guild_member_presence_obj.user._components is mock_components
        assert guild_member_presence_obj.role_ids == [49494949]
        assert guild_member_presence_obj.guild_id == 44004040
        assert guild_member_presence_obj.visible_status is guilds.PresenceStatus.DND
        assert guild_member_presence_obj.activities == [
            guilds.PresenceActivity.deserialize(test_presence_activity_payload)
        ]
        assert guild_member_presence_obj.activities[0]._components is mock_components
        assert guild_member_presence_obj.client_status == guilds.ClientStatus.deserialize(test_client_status_payload)
        assert guild_member_presence_obj.client_status._components is mock_components
        assert guild_member_presence_obj.premium_since is mock_since
        assert guild_member_presence_obj.nick == "Nick"


class TestGuildMemberBan:
    @pytest.fixture()
    def test_guild_member_ban_payload(self, test_user_payload):
        return {"reason": "Get Nyaa'ed", "user": test_user_payload}

    def test_deserializer(self, test_guild_member_ban_payload, test_user_payload, mock_components):
        mock_user = mock.MagicMock(users.User)
        with _helpers.patch_marshal_attr(
            guilds.GuildMemberBan, "user", deserializer=users.User.deserialize, return_value=mock_user
        ) as patched_user_deserializer:
            guild_member_ban_obj = guilds.GuildMemberBan.deserialize(
                test_guild_member_ban_payload, components=mock_components
            )
            patched_user_deserializer.assert_called_once_with(test_user_payload, components=mock_components)
        assert guild_member_ban_obj.reason == "Get Nyaa'ed"
        assert guild_member_ban_obj.user is mock_user


@pytest.fixture()
def test_integration_account_payload():
    return {"id": "543453", "name": "Blah Blah"}


class TestIntegrationAccount:
    def test_deserializer(self, test_integration_account_payload, mock_components):
        integration_account_obj = guilds.IntegrationAccount.deserialize(
            test_integration_account_payload, components=mock_components
        )
        assert integration_account_obj.id == "543453"
        assert integration_account_obj.name == "Blah Blah"


@pytest.fixture()
def test_partial_guild_integration_payload(test_integration_account_payload):
    return {
        "id": "4949494949",
        "name": "Blah blah",
        "type": "twitch",
        "account": test_integration_account_payload,
    }


class TestPartialGuildIntegration:
    def test_deserialise(
        self, test_partial_guild_integration_payload, test_integration_account_payload, mock_components
    ):
        partial_guild_integration_obj = guilds.PartialGuildIntegration.deserialize(
            test_partial_guild_integration_payload, components=mock_components
        )
        assert partial_guild_integration_obj.name == "Blah blah"
        assert partial_guild_integration_obj.type == "twitch"
        assert partial_guild_integration_obj.account == guilds.IntegrationAccount.deserialize(
            test_integration_account_payload
        )
        assert partial_guild_integration_obj.account._components is mock_components


class TestGuildIntegration:
    @pytest.fixture()
    def test_guild_integration_payload(self, test_user_payload, test_partial_guild_integration_payload):
        return {
            **test_partial_guild_integration_payload,
            "enabled": True,
            "syncing": False,
            "role_id": "98494949",
            "enable_emoticons": False,
            "expire_behavior": 1,
            "expire_grace_period": 7,
            "user": test_user_payload,
            "synced_at": "2015-04-26T06:26:56.936000+00:00",
        }

    def test_deserialize(
        self, test_guild_integration_payload, test_user_payload, test_integration_account_payload, mock_components
    ):
        mock_user = mock.MagicMock(users.User)
        mock_sync_date = mock.MagicMock(datetime.datetime)
        stack = contextlib.ExitStack()
        patched_sync_at_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                guilds.GuildIntegration,
                "last_synced_at",
                deserializer=conversions.parse_iso_8601_ts,
                return_value=mock_sync_date,
            )
        )
        patched_user_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                guilds.GuildIntegration, "user", deserializer=users.User.deserialize, return_value=mock_user
            )
        )
        with stack:
            guild_integration_obj = guilds.GuildIntegration.deserialize(
                test_guild_integration_payload, components=mock_components
            )
            patched_user_deserializer.assert_called_once_with(test_user_payload, components=mock_components)
            patched_sync_at_deserializer.assert_called_once_with("2015-04-26T06:26:56.936000+00:00")

        assert guild_integration_obj.is_enabled is True
        assert guild_integration_obj.is_syncing is False
        assert guild_integration_obj.role_id == 98494949
        assert guild_integration_obj.is_emojis_enabled is False
        assert guild_integration_obj.expire_behavior is guilds.IntegrationExpireBehaviour.KICK
        assert guild_integration_obj.expire_grace_period == datetime.timedelta(days=7)
        assert guild_integration_obj.user is mock_user
        assert guild_integration_obj.last_synced_at is mock_sync_date


class TestUnavailableGuild:
    def test_deserialize_when_unavailable_is_defined(self, mock_components):
        guild_delete_event_obj = guilds.UnavailableGuild.deserialize(
            {"id": "293293939", "unavailable": True}, components=mock_components
        )
        assert guild_delete_event_obj.is_unavailable is True

    def test_deserialize_when_unavailable_is_undefined(self, mock_components):
        guild_delete_event_obj = guilds.UnavailableGuild.deserialize({"id": "293293939"}, components=mock_components)
        assert guild_delete_event_obj.is_unavailable is True


class TestPartialGuild:
    def test_deserialize(self, test_partial_guild_payload, mock_components):
        partial_guild_obj = guilds.PartialGuild.deserialize(test_partial_guild_payload, components=mock_components)
        assert partial_guild_obj.id == 152559372126519269
        assert partial_guild_obj.name == "Isopropyl"
        assert partial_guild_obj.icon_hash == "d4a983885dsaa7691ce8bcaaf945a"
        assert partial_guild_obj.features == {guilds.GuildFeature.DISCOVERABLE}

    @pytest.fixture()
    def partial_guild_obj(self, test_partial_guild_payload):
        return _helpers.unslot_class(guilds.PartialGuild)(
            id=152559372126519269, icon_hash="d4a983885dsaa7691ce8bcaaf945a", name=None, features=None,
        )

    def test_format_icon_url(self, partial_guild_obj):
        mock_url = "https://cdn.discordapp.com/icons/152559372126519269/d4a983885dsaa7691ce8bcaaf945a.png?size=20"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = partial_guild_obj.format_icon_url(fmt="nyaapeg", size=42)
            urls.generate_cdn_url.assert_called_once_with(
                "icons", "152559372126519269", "d4a983885dsaa7691ce8bcaaf945a", fmt="nyaapeg", size=42
            )
        assert url == mock_url

    def test_format_icon_url_animated_default(self, partial_guild_obj):
        partial_guild_obj.icon_hash = "a_d4a983885dsaa7691ce8bcaaf945a"
        mock_url = "https://cdn.discordapp.com/icons/152559372126519269/a_d4a983885dsaa7691ce8bcaaf945a.gif?size=20"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = partial_guild_obj.format_icon_url()
            urls.generate_cdn_url.assert_called_once_with(
                "icons", "152559372126519269", "a_d4a983885dsaa7691ce8bcaaf945a", fmt="gif", size=4096
            )
        assert url == mock_url

    def test_format_icon_url_none_animated_default(self, partial_guild_obj):
        partial_guild_obj.icon_hash = "d4a983885dsaa7691ce8bcaaf945a"
        mock_url = "https://cdn.discordapp.com/icons/152559372126519269/d4a983885dsaa7691ce8bcaaf945a.png?size=20"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = partial_guild_obj.format_icon_url()
            urls.generate_cdn_url.assert_called_once_with(
                "icons", "152559372126519269", "d4a983885dsaa7691ce8bcaaf945a", fmt="png", size=4096
            )
        assert url == mock_url

    def test_format_icon_url_returns_none(self, partial_guild_obj):
        partial_guild_obj.icon_hash = None
        with mock.patch.object(urls, "generate_cdn_url", return_value=...):
            url = partial_guild_obj.format_icon_url(fmt="nyaapeg", size=42)
            urls.generate_cdn_url.assert_not_called()
        assert url is None

    @pytest.mark.parametrize(
        ["fmt", "expected_fmt", "icon_hash", "size"],
        [
            ("png", "png", "a_1a2b3c", 1 << 4),
            ("png", "png", "1a2b3c", 1 << 5),
            ("jpeg", "jpeg", "a_1a2b3c", 1 << 6),
            ("jpeg", "jpeg", "1a2b3c", 1 << 7),
            ("jpg", "jpg", "a_1a2b3c", 1 << 8),
            ("jpg", "jpg", "1a2b3c", 1 << 9),
            ("webp", "webp", "a_1a2b3c", 1 << 10),
            ("webp", "webp", "1a2b3c", 1 << 11),
            ("gif", "gif", "a_1a2b3c", 1 << 12),
            ("gif", "gif", "1a2b3c", 1 << 7),
            (None, "gif", "a_1a2b3c", 1 << 5),
            (None, "png", "1a2b3c", 1 << 10),
        ],
    )
    def test_format_icon_url(self, partial_guild_obj, fmt, expected_fmt, icon_hash, size):
        mock_url = "https://cdn.discordapp.com/icons/152559372126519269/d4a983885dsaa7691ce8bcaaf945a.png?size=20"
        partial_guild_obj.icon_hash = icon_hash
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = partial_guild_obj.format_icon_url(fmt, size)
            urls.generate_cdn_url.assert_called_once_with(
                "icons", str(partial_guild_obj.id), partial_guild_obj.icon_hash, fmt=expected_fmt, size=size
            )
        assert url == mock_url

    def test_icon_url_default(self, partial_guild_obj):
        result = mock.MagicMock()
        partial_guild_obj.format_icon_url = mock.MagicMock(return_value=result)
        assert partial_guild_obj.icon_url is result
        partial_guild_obj.format_icon_url.assert_called_once_with()


class TestGuildPreview:
    def test_deserialize(self, test_guild_preview_payload, test_emoji_payload, mock_components):
        mock_emoji = mock.MagicMock(emojis.KnownCustomEmoji, id=41771983429993937)
        with mock.patch.object(emojis.KnownCustomEmoji, "deserialize", return_value=mock_emoji):
            guild_preview_obj = guilds.GuildPreview.deserialize(test_guild_preview_payload, components=mock_components)
            emojis.KnownCustomEmoji.deserialize.assert_called_once_with(test_emoji_payload, components=mock_components)
        assert guild_preview_obj.splash_hash == "dsa345tfcdg54b"
        assert guild_preview_obj.discovery_splash_hash == "lkodwaidi09239uid"
        assert guild_preview_obj.emojis == {41771983429993937: mock_emoji}
        assert guild_preview_obj.approximate_presence_count == 42
        assert guild_preview_obj.approximate_member_count == 69
        assert guild_preview_obj.description == "A DESCRIPTION."

    @pytest.fixture()
    def test_guild_preview_obj(self):
        return guilds.GuildPreview(
            id="23123123123",
            name=None,
            icon_hash=None,
            features=None,
            splash_hash="dsa345tfcdg54b",
            discovery_splash_hash="lkodwaidi09239uid",
            emojis=None,
            approximate_presence_count=None,
            approximate_member_count=None,
            description=None,
        )

    def test_format_discovery_splash_url(self, test_guild_preview_obj):
        mock_url = "https://not-al"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = test_guild_preview_obj.format_discovery_splash_url(fmt="nyaapeg", size=4000)
            urls.generate_cdn_url.assert_called_once_with(
                "discovery-splashes", "23123123123", "lkodwaidi09239uid", fmt="nyaapeg", size=4000
            )
        assert url == mock_url

    def test_format_discovery_splash_returns_none(self, test_guild_preview_obj):
        test_guild_preview_obj.discovery_splash_hash = None
        with mock.patch.object(urls, "generate_cdn_url", return_value=...):
            url = test_guild_preview_obj.format_discovery_splash_url()
            urls.generate_cdn_url.assert_not_called()
        assert url is None

    def test_discover_splash_url(self, test_guild_preview_obj):
        mock_url = "https://not-al"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = test_guild_preview_obj.discovery_splash_url
            urls.generate_cdn_url.assert_called_once()
        assert url == mock_url

    def test_format_splash_url(self, test_guild_preview_obj):
        mock_url = "https://not-al"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = test_guild_preview_obj.format_splash_url(fmt="nyaapeg", size=4000)
            urls.generate_cdn_url.assert_called_once_with(
                "splashes", "23123123123", "dsa345tfcdg54b", fmt="nyaapeg", size=4000
            )
        assert url == mock_url

    def test_format_splash_returns_none(self, test_guild_preview_obj):
        test_guild_preview_obj.splash_hash = None
        with mock.patch.object(urls, "generate_cdn_url", return_value=...):
            url = test_guild_preview_obj.format_splash_url()
            urls.generate_cdn_url.assert_not_called()
        assert url is None

    def test_splash_url(self, test_guild_preview_obj):
        mock_url = "https://not-al"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = test_guild_preview_obj.splash_url
            urls.generate_cdn_url.assert_called_once()
        assert url == mock_url


class TestGuild:
    def test_deserialize(
        self,
        mock_components,
        test_guild_payload,
        test_roles_payload,
        test_emoji_payload,
        test_member_payload,
        test_channel_payload,
        test_guild_member_presence,
    ):
        mock_emoji = mock.MagicMock(emojis.KnownCustomEmoji, id=41771983429993937)
        mock_guild_channel = mock.MagicMock(channels.GuildChannel, id=1234567)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(emojis.KnownCustomEmoji, "deserialize", return_value=mock_emoji))
        stack.enter_context(mock.patch.object(channels, "deserialize_channel", return_value=mock_guild_channel))
        stack.enter_context(
            _helpers.patch_marshal_attr(
                guilds.GuildMember, "user", deserializer=users.User.deserialize, return_value=mock.MagicMock(users.User)
            )
        )
        with stack:
            guild_obj = guilds.Guild.deserialize(test_guild_payload, components=mock_components)
            channels.deserialize_channel.assert_called_once_with(test_channel_payload, components=mock_components)
            emojis.KnownCustomEmoji.deserialize.assert_called_once_with(test_emoji_payload, components=mock_components)
            assert guild_obj.members == {123456: guilds.GuildMember.deserialize(test_member_payload)}
            assert guild_obj.members[123456]._components is mock_components
        assert guild_obj.presences == {123456: guilds.GuildMemberPresence.deserialize(test_guild_member_presence)}
        assert guild_obj.presences[123456]._components is mock_components
        assert guild_obj.splash_hash == "0ff0ff0ff"
        assert guild_obj.discovery_splash_hash == "famfamFAMFAMfam"
        assert guild_obj.owner_id == 6969696
        assert guild_obj.my_permissions == 66_321_471
        assert guild_obj.region == "eu-central"
        assert guild_obj.afk_channel_id == 99998888777766
        assert guild_obj.afk_timeout == datetime.timedelta(minutes=20)
        assert guild_obj.is_embed_enabled is True
        assert guild_obj.embed_channel_id == 9439394949
        assert guild_obj.is_widget_enabled is True
        assert guild_obj.widget_channel_id == 9439394949
        assert guild_obj.verification_level is guilds.GuildVerificationLevel.VERY_HIGH
        assert guild_obj.default_message_notifications is guilds.GuildMessageNotificationsLevel.ONLY_MENTIONS
        assert guild_obj.explicit_content_filter is guilds.GuildExplicitContentFilterLevel.ALL_MEMBERS
        assert guild_obj.roles == {41771983423143936: guilds.GuildRole.deserialize(test_roles_payload)}
        assert guild_obj.roles[41771983423143936]._components is mock_components
        assert guild_obj.emojis == {41771983429993937: mock_emoji}
        assert guild_obj.mfa_level is guilds.GuildMFALevel.ELEVATED
        assert guild_obj.application_id == 39494949
        assert guild_obj.is_unavailable is False
        assert guild_obj.system_channel_id == 19216801
        assert (
            guild_obj.system_channel_flags
            == guilds.GuildSystemChannelFlag.SUPPRESS_PREMIUM_SUBSCRIPTION
            | guilds.GuildSystemChannelFlag.SUPPRESS_USER_JOIN
        )
        assert guild_obj.rules_channel_id == 42042069
        assert guild_obj.joined_at == conversions.parse_iso_8601_ts("2019-05-17T06:26:56.936000+00:00")
        assert guild_obj.is_large is False
        assert guild_obj.member_count == 14
        assert guild_obj.channels == {1234567: mock_guild_channel}
        assert guild_obj.max_presences == 250
        assert guild_obj.max_members == 25000
        assert guild_obj.vanity_url_code == "loool"
        assert guild_obj.description == "This is a server I guess, its a bit crap though"
        assert guild_obj.banner_hash == "1a2b3c"
        assert guild_obj.premium_tier is guilds.GuildPremiumTier.TIER_2
        assert guild_obj.premium_subscription_count == 1
        assert guild_obj.preferred_locale == "en-GB"
        assert guild_obj.public_updates_channel_id == 33333333
        assert guild_obj.max_video_channel_users == 25
        assert guild_obj.approximate_member_count == 15
        assert guild_obj.approximate_active_member_count == 7

    @pytest.fixture()
    def test_guild_obj(self):
        return guilds.Guild(
            # TODO: fix null spam here, it is terrible test data, as it is not possible!!!!
            id=265828729970753537,
            icon_hash=None,
            name=None,
            features=None,
            splash_hash="0ff0ff0ff",
            banner_hash="1a2b3c",
            discovery_splash_hash="famfamFAMFAMfam",
            owner_id=None,
            my_permissions=None,
            region=None,
            afk_channel_id=None,
            afk_timeout=None,
            is_embed_enabled=None,
            embed_channel_id=None,
            verification_level=None,
            default_message_notifications=None,
            explicit_content_filter=None,
            roles=None,
            emojis=None,
            mfa_level=None,
            application_id=None,
            is_unavailable=None,
            is_widget_enabled=None,
            widget_channel_id=None,
            system_channel_id=None,
            system_channel_flags=None,
            rules_channel_id=None,
            joined_at=None,
            is_large=None,
            member_count=None,
            members=None,
            channels=None,
            presences=None,
            max_presences=None,
            max_members=None,
            vanity_url_code=None,
            description=None,
            premium_tier=None,
            premium_subscription_count=None,
            preferred_locale=None,
            public_updates_channel_id=None,
            approximate_active_member_count=None,
            approximate_member_count=None,
            max_video_channel_users=None,
        )

    def test_format_banner_url(self, test_guild_obj):
        mock_url = "https://not-al"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = test_guild_obj.format_banner_url(fmt="nyaapeg", size=4000)
            urls.generate_cdn_url.assert_called_once_with(
                "banners", "265828729970753537", "1a2b3c", fmt="nyaapeg", size=4000
            )
        assert url == mock_url

    def test_format_banner_url_returns_none(self, test_guild_obj):
        test_guild_obj.banner_hash = None
        with mock.patch.object(urls, "generate_cdn_url", return_value=...):
            url = test_guild_obj.format_banner_url()
            urls.generate_cdn_url.assert_not_called()
        assert url is None

    def test_banner_url(self, test_guild_obj):
        mock_url = "https://not-al"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = test_guild_obj.banner_url
            urls.generate_cdn_url.assert_called_once()
        assert url == mock_url

    def test_format_discovery_splash_url(self, test_guild_obj):
        mock_url = "https://not-al"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = test_guild_obj.format_discovery_splash_url(fmt="nyaapeg", size=4000)
            urls.generate_cdn_url.assert_called_once_with(
                "discovery-splashes", "265828729970753537", "famfamFAMFAMfam", fmt="nyaapeg", size=4000
            )
        assert url == mock_url

    def test_format_discovery_splash_returns_none(self, test_guild_obj):
        test_guild_obj.discovery_splash_hash = None
        with mock.patch.object(urls, "generate_cdn_url", return_value=...):
            url = test_guild_obj.format_discovery_splash_url()
            urls.generate_cdn_url.assert_not_called()
        assert url is None

    def test_discover_splash_url(self, test_guild_obj):
        mock_url = "https://not-al"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = test_guild_obj.discovery_splash_url
            urls.generate_cdn_url.assert_called_once()
        assert url == mock_url

    def test_format_splash_url(self, test_guild_obj):
        mock_url = "https://not-al"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = test_guild_obj.format_splash_url(fmt="nyaapeg", size=4000)
            urls.generate_cdn_url.assert_called_once_with(
                "splashes", "265828729970753537", "0ff0ff0ff", fmt="nyaapeg", size=4000
            )
        assert url == mock_url

    def test_format_splash_returns_none(self, test_guild_obj):
        test_guild_obj.splash_hash = None
        with mock.patch.object(urls, "generate_cdn_url", return_value=...):
            url = test_guild_obj.format_splash_url()
            urls.generate_cdn_url.assert_not_called()
        assert url is None

    def test_splash_url(self, test_guild_obj):
        mock_url = "https://not-al"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = test_guild_obj.splash_url
            urls.generate_cdn_url.assert_called_once()
        assert url == mock_url
