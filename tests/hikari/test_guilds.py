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

import hikari.internal.conversions
from hikari.internal import urls
from hikari import emojis
from hikari import entities
from hikari import guilds
from hikari import users
from hikari import channels

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
def test_roles_payloads():
    return [
        {
            "id": "41771983423143936",
            "name": "WE DEM BOYZZ!!!!!!",
            "color": 3_447_003,
            "hoist": True,
            "position": 0,
            "permissions": 66_321_471,
            "managed": False,
            "mentionable": False,
        },
        {
            "id": "1111223",
            "name": "some unfunny pun here",
            "color": 0xFF00FF,
            "hoist": False,
            "position": 1,
            "permissions": 1,
            "managed": False,
            "mentionable": True,
        },
    ]


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
        "flags": 0b00101101,
        "premium_type": 0b1101101,
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


@pytest.fixture
def test_guild_payload(
    test_emoji_payload,
    test_roles_payloads,
    test_channel_payload,
    test_member_payload,
    test_voice_state_payload,
    test_guild_member_presence,
):
    return {
        "id": "265828729970753537",
        "afk_channel_id": "99998888777766",
        "owner_id": "6969696",
        "region": "eu-central",
        "system_channel_id": "19216801",
        "application_id": "39494949",
        "name": "L33t guild",
        "icon": "1a2b3c4d",
        "splash": "0ff0ff0ff",
        "afk_timeout": 1200,
        "verification_level": 4,
        "default_message_notifications": 1,
        "explicit_content_filter": 2,
        "roles": test_roles_payloads,
        "emojis": [test_emoji_payload],
        "features": ["ANIMATED_ICON", "MORE_EMOJI", "NEWS", "SOME_UNDOCUMENTED_FEATURE"],
        "voice_states": [test_voice_state_payload],
        "member_count": 14,
        "mfa_level": 1,
        "joined_at": "2019-05-17T06:26:56.936000+00:00",
        "large": False,
        "unavailable": False,
        "permissions": 66_321_471,
        "members": [test_member_payload],
        "channels": [test_channel_payload],
        "max_members": 25000,
        "vanity_url_code": "loool",
        "description": "This is a server I guess, its a bit crap though",
        "banner": "1a2b3c",
        "premium_tier": 2,
        "premium_subscription_count": 1,
        "preferred_locale": "en-GB",
        "system_channel_flags": 3,
        "rules_channel_id": "42042069",
        "discovery_splash": "famfamFAMFAMfam",
        "embed_enabled": True,
        "embed_channel_id": "9439394949",
        "widget_enabled": True,
        "widget_channel_id": "9439394949",
        "public_updates_channel_id": "33333333",
        "presences": [test_guild_member_presence],
        "max_presences": 250,
    }


class TestGuildMember:
    def test_deserialize(self, test_member_payload, test_user_payload):
        mock_user = mock.create_autospec(users.User)
        mock_datetime_1 = mock.create_autospec(datetime.datetime)
        mock_datetime_2 = mock.create_autospec(datetime.datetime)
        with _helpers.patch_marshal_attr(
            guilds.GuildMember, "user", deserializer=users.User.deserialize, return_value=mock_user
        ) as patched_user_deserializer:
            with _helpers.patch_marshal_attr(
                guilds.GuildMember,
                "joined_at",
                deserializer=hikari.internal.conversions.parse_iso_8601_ts,
                return_value=mock_datetime_1,
            ) as patched_joined_at_deserializer:
                with _helpers.patch_marshal_attr(
                    guilds.GuildMember,
                    "premium_since",
                    deserializer=hikari.internal.conversions.parse_iso_8601_ts,
                    return_value=mock_datetime_2,
                ) as patched_premium_since_deserializer:
                    guild_member_obj = guilds.GuildMember.deserialize(test_member_payload)
                    patched_premium_since_deserializer.assert_called_once_with("2019-05-17T06:26:56.936000+00:00")
                patched_joined_at_deserializer.assert_called_once_with("2015-04-26T06:26:56.936000+00:00")
            patched_user_deserializer.assert_called_once_with(test_user_payload)
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

    def test_deserialize(self, test_partial_guild_role_payload):
        partial_guild_role_obj = guilds.PartialGuildRole.deserialize(test_partial_guild_role_payload)
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

    def test_deserialize(self, test_guild_role_payload):
        guild_role_obj = guilds.GuildRole.deserialize(test_guild_role_payload)
        assert guild_role_obj.color == 3_447_003
        assert guild_role_obj.is_hoisted is True
        assert guild_role_obj.position == 0
        assert guild_role_obj.permissions == 66_321_471
        assert guild_role_obj.is_managed is False
        assert guild_role_obj.is_mentionable is False


class TestActivityTimestamps:
    def test_deserialize(self, test_activity_timestamps_payload):
        mock_start_date = mock.create_autospec(datetime.datetime)
        mock_end_date = mock.create_autospec(datetime.datetime)
        with _helpers.patch_marshal_attr(
            guilds.ActivityTimestamps,
            "start",
            deserializer=hikari.internal.conversions.unix_epoch_to_datetime,
            return_value=mock_start_date,
        ) as patched_start_deserializer:
            with _helpers.patch_marshal_attr(
                guilds.ActivityTimestamps,
                "end",
                deserializer=hikari.internal.conversions.unix_epoch_to_datetime,
                return_value=mock_end_date,
            ) as patched_end_deserializer:
                activity_timestamps_obj = guilds.ActivityTimestamps.deserialize(test_activity_timestamps_payload)
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
    def test_deserialize(self, test_activity_assets_payload):
        activity_assets_obj = guilds.ActivityAssets.deserialize(test_activity_assets_payload)
        assert activity_assets_obj.large_image == "34234234234243"
        assert activity_assets_obj.large_text == "LARGE TEXT"
        assert activity_assets_obj.small_image == "3939393"
        assert activity_assets_obj.small_text == "small text"


class TestActivitySecret:
    def test_deserialize(self, test_activity_secrets_payload):
        activity_secret_obj = guilds.ActivitySecret.deserialize(test_activity_secrets_payload)
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
    ):
        mock_created_at = mock.create_autospec(datetime.datetime)
        mock_emoji = mock.create_autospec(emojis.UnknownEmoji)
        with _helpers.patch_marshal_attr(
            guilds.PresenceActivity,
            "created_at",
            deserializer=hikari.internal.conversions.unix_epoch_to_datetime,
            return_value=mock_created_at,
        ) as patched_created_at_deserializer:
            with _helpers.patch_marshal_attr(
                guilds.PresenceActivity,
                "emoji",
                deserializer=emojis.deserialize_reaction_emoji,
                return_value=mock_emoji,
            ) as patched_emoji_deserializer:
                presence_activity_obj = guilds.PresenceActivity.deserialize(test_presence_activity_payload)
                patched_emoji_deserializer.assert_called_once_with(test_emoji_payload)
            patched_created_at_deserializer.assert_called_once_with(1584996792798)
        assert presence_activity_obj.name == "an activity"
        assert presence_activity_obj.type is guilds.ActivityType.STREAMING
        assert presence_activity_obj.url == "https://69.420.owouwunyaa"
        assert presence_activity_obj.created_at is mock_created_at
        assert presence_activity_obj.timestamps == guilds.ActivityTimestamps.deserialize(
            test_activity_timestamps_payload
        )
        assert presence_activity_obj.application_id == 40404040404040
        assert presence_activity_obj.details == "They are doing stuff"
        assert presence_activity_obj.state == "STATED"
        assert presence_activity_obj.emoji is mock_emoji
        assert presence_activity_obj.party == guilds.ActivityParty.deserialize(test_activity_party_payload)
        assert presence_activity_obj.assets == guilds.ActivityAssets.deserialize(test_activity_assets_payload)
        assert presence_activity_obj.secrets == guilds.ActivitySecret.deserialize(test_activity_secrets_payload)
        assert presence_activity_obj.is_instance is True
        assert presence_activity_obj.flags == guilds.ActivityFlag.INSTANCE | guilds.ActivityFlag.JOIN


@pytest.fixture()
def test_client_status_payload():
    return {"desktop": "online", "mobile": "idle"}


class TestClientStatus:
    def test_deserialize(self, test_client_status_payload):
        client_status_obj = guilds.ClientStatus.deserialize(test_client_status_payload)
        assert client_status_obj.desktop is guilds.PresenceStatus.ONLINE
        assert client_status_obj.mobile is guilds.PresenceStatus.IDLE
        assert client_status_obj.web is guilds.PresenceStatus.OFFLINE


class TestPresenceUser:
    def test_deserialize_filled_presence_user(self, test_user_payload):
        presence_user_obj = guilds.PresenceUser.deserialize(test_user_payload)
        assert presence_user_obj.username == "Boris Johnson"
        assert presence_user_obj.discriminator == "6969"
        assert presence_user_obj.avatar_hash == "1a2b3c4d"

    def test_deserialize_partial_presence_user(self):
        presence_user_obj = guilds.PresenceUser.deserialize({"id": "115590097100865541"})
        assert presence_user_obj.id == 115590097100865541
        for attr in presence_user_obj.__slots__:
            if attr != "id":
                assert getattr(presence_user_obj, attr) is entities.UNSET


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
        self, test_guild_member_presence, test_user_payload, test_presence_activity_payload, test_client_status_payload
    ):
        mock_since = mock.create_autospec(datetime.datetime)
        with _helpers.patch_marshal_attr(
            guilds.GuildMemberPresence,
            "premium_since",
            deserializer=hikari.internal.conversions.parse_iso_8601_ts,
            return_value=mock_since,
        ) as patched_since_deserializer:
            guild_member_presence_obj = guilds.GuildMemberPresence.deserialize(test_guild_member_presence)
            patched_since_deserializer.assert_called_once_with("2015-04-26T06:26:56.936000+00:00")
        assert guild_member_presence_obj.user == guilds.PresenceUser.deserialize(test_user_payload)
        assert guild_member_presence_obj.role_ids == [49494949]
        assert guild_member_presence_obj.guild_id == 44004040
        assert guild_member_presence_obj.visible_status is guilds.PresenceStatus.DND
        assert guild_member_presence_obj.activities == [
            guilds.PresenceActivity.deserialize(test_presence_activity_payload)
        ]
        assert guild_member_presence_obj.client_status == guilds.ClientStatus.deserialize(test_client_status_payload)
        assert guild_member_presence_obj.premium_since is mock_since
        assert guild_member_presence_obj.nick == "Nick"


class TestGuildMemberBan:
    @pytest.fixture()
    def test_guild_member_ban_payload(self, test_user_payload):
        return {"reason": "Get Nyaa'ed", "user": test_user_payload}

    def test_deserializer(self, test_guild_member_ban_payload, test_user_payload):
        mock_user = mock.create_autospec(users.User)
        with _helpers.patch_marshal_attr(
            guilds.GuildMemberBan, "user", deserializer=users.User.deserialize, return_value=mock_user
        ) as patched_user_deserializer:
            guild_member_ban_obj = guilds.GuildMemberBan.deserialize(test_guild_member_ban_payload)
            patched_user_deserializer.assert_called_once_with(test_user_payload)
        assert guild_member_ban_obj.reason == "Get Nyaa'ed"
        assert guild_member_ban_obj.user is mock_user


@pytest.fixture()
def test_integration_account_payload():
    return {"id": "543453", "name": "Blah Blah"}


class TestIntegrationAccount:
    def test_deserializer(self, test_integration_account_payload):
        integration_account_obj = guilds.IntegrationAccount.deserialize(test_integration_account_payload)
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
    def test_deserialise(self, test_partial_guild_integration_payload, test_integration_account_payload):
        partial_guild_integration_obj = guilds.PartialGuildIntegration.deserialize(
            test_partial_guild_integration_payload
        )
        assert partial_guild_integration_obj.name == "Blah blah"
        assert partial_guild_integration_obj.type == "twitch"
        assert partial_guild_integration_obj.account == guilds.IntegrationAccount.deserialize(
            test_integration_account_payload
        )


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

    def test_deserialize(self, test_guild_integration_payload, test_user_payload, test_integration_account_payload):
        mock_user = mock.create_autospec(users.User)
        mock_sync_date = mock.create_autospec(datetime.datetime)
        with _helpers.patch_marshal_attr(
            guilds.GuildIntegration,
            "last_synced_at",
            deserializer=hikari.internal.conversions.parse_iso_8601_ts,
            return_value=mock_sync_date,
        ) as patched_sync_at_deserializer:
            with _helpers.patch_marshal_attr(
                guilds.GuildIntegration, "user", deserializer=users.User.deserialize, return_value=mock_user
            ) as patched_user_deserializer:
                guild_integration_obj = guilds.GuildIntegration.deserialize(test_guild_integration_payload)
                patched_user_deserializer.assert_called_once_with(test_user_payload)
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
    def test_deserialize_when_unavailable_is_defined(self):
        guild_delete_event_obj = guilds.UnavailableGuild.deserialize({"id": "293293939", "unavailable": True})
        assert guild_delete_event_obj.is_unavailable is True

    def test_deserialize_when_unavailable_is_undefined(self):
        guild_delete_event_obj = guilds.UnavailableGuild.deserialize({"id": "293293939"})
        assert guild_delete_event_obj.is_unavailable is True


class TestPartialGuild:
    @pytest.fixture()
    def partial_guild_obj(self, test_partial_guild_payload):
        return guilds.PartialGuild.deserialize(test_partial_guild_payload)

    def test_deserialize(self, partial_guild_obj):
        assert partial_guild_obj.id == 152559372126519269
        assert partial_guild_obj.name == "Isopropyl"
        assert partial_guild_obj.icon_hash == "d4a983885dsaa7691ce8bcaaf945a"
        assert partial_guild_obj.features == {guilds.GuildFeature.DISCOVERABLE}

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
                "icons", "152559372126519269", "a_d4a983885dsaa7691ce8bcaaf945a", fmt="gif", size=2048
            )
        assert url == mock_url

    def test_format_icon_url_none_animated_default(self, partial_guild_obj):
        partial_guild_obj.icon_hash = "d4a983885dsaa7691ce8bcaaf945a"
        mock_url = "https://cdn.discordapp.com/icons/152559372126519269/d4a983885dsaa7691ce8bcaaf945a.png?size=20"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = partial_guild_obj.format_icon_url()
            urls.generate_cdn_url.assert_called_once_with(
                "icons", "152559372126519269", "d4a983885dsaa7691ce8bcaaf945a", fmt="png", size=2048
            )
        assert url == mock_url

    def test_format_icon_url_returns_none(self, partial_guild_obj):
        partial_guild_obj.icon_hash = None
        with mock.patch.object(urls, "generate_cdn_url", return_value=...):
            url = partial_guild_obj.format_icon_url(fmt="nyaapeg", size=42)
            urls.generate_cdn_url.assert_not_called()
        assert url is None

    def test_format_icon_url(self, partial_guild_obj):
        mock_url = "https://cdn.discordapp.com/icons/152559372126519269/d4a983885dsaa7691ce8bcaaf945a.png?size=20"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = partial_guild_obj.icon_url
            urls.generate_cdn_url.assert_called_once()
        assert url == mock_url


class TestGuild:
    def test_deserialize(
        self,
        test_guild_payload,
        test_roles_payloads,
        test_emoji_payload,
        test_member_payload,
        test_channel_payload,
        test_guild_member_presence,
    ):
        mock_emoji = mock.create_autospec(emojis.GuildEmoji, id=42)
        mock_user = mock.create_autospec(users.User, id=84)
        mock_guild_channel = mock.create_autospec(channels.GuildChannel, id=6969)
        with mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji):
            with _helpers.patch_marshal_attr(
                guilds.GuildMemberPresence, "user", deserializer=guilds.PresenceUser.deserialize, return_value=mock_user
            ) as patched_user_deserializer:
                with _helpers.patch_marshal_attr(
                    guilds.GuildMember, "user", deserializer=users.User.deserialize, return_value=mock_user
                ) as patched_member_user_deserializer:
                    with mock.patch.object(channels, "deserialize_channel", return_value=mock_guild_channel):
                        guild_obj = guilds.Guild.deserialize(test_guild_payload)
                        channels.deserialize_channel.assert_called_once_with(test_channel_payload)
                    patched_member_user_deserializer.assert_called_once_with(test_member_payload["user"])
                    assert guild_obj.members == {84: guilds.GuildMember.deserialize(test_member_payload)}
                patched_user_deserializer.assert_called_once_with(test_member_payload["user"])
                assert guild_obj.presences == {84: guilds.GuildMemberPresence.deserialize(test_guild_member_presence)}
            emojis.GuildEmoji.deserialize.assert_called_once_with(test_emoji_payload)
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
        assert guild_obj.roles == {r.id: r for r in map(guilds.GuildRole.deserialize, test_roles_payloads)}
        assert guild_obj.emojis == {42: mock_emoji}
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
        assert guild_obj.joined_at == hikari.internal.conversions.parse_iso_8601_ts("2019-05-17T06:26:56.936000+00:00")
        assert guild_obj.is_large is False
        assert guild_obj.member_count == 14
        assert guild_obj.channels == {6969: mock_guild_channel}
        assert guild_obj.max_presences == 250
        assert guild_obj.max_members == 25000
        assert guild_obj.vanity_url_code == "loool"
        assert guild_obj.description == "This is a server I guess, its a bit crap though"
        assert guild_obj.banner_hash == "1a2b3c"
        assert guild_obj.premium_tier is guilds.GuildPremiumTier.TIER_2
        assert guild_obj.premium_subscription_count == 1
        assert guild_obj.preferred_locale == "en-GB"
        assert guild_obj.public_updates_channel_id == 33333333

    @pytest.fixture()
    @mock.patch.object(emojis.GuildEmoji, "deserialize")
    def test_guild_obj(self, *patched_objs, test_guild_payload):
        return guilds.Guild.deserialize(test_guild_payload)

    def test_format_banner_url(self, test_guild_obj):
        mock_url = "https://not-al"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = test_guild_obj.format_banner_url(fmt="nyaapeg", size=4000)
            urls.generate_cdn_url.assert_called_once_with(
                "banners", "265828729970753537", "1a2b3c", fmt="nyaapeg", size=4000
            )
        assert url is mock_url

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
        assert url is mock_url

    def test_format_discovery_splash_url(self, test_guild_obj):
        mock_url = "https://not-al"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = test_guild_obj.format_discovery_splash_url(fmt="nyaapeg", size=4000)
            urls.generate_cdn_url.assert_called_once_with(
                "discovery-splashes", "265828729970753537", "famfamFAMFAMfam", fmt="nyaapeg", size=4000
            )
        assert url is mock_url

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
        assert url is mock_url

    def test_format_splash_url(self, test_guild_obj):
        mock_url = "https://not-al"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = test_guild_obj.format_splash_url(fmt="nyaapeg", size=4000)
            urls.generate_cdn_url.assert_called_once_with(
                "splashes", "265828729970753537", "0ff0ff0ff", fmt="nyaapeg", size=4000
            )
        assert url is mock_url

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
        assert url is mock_url
