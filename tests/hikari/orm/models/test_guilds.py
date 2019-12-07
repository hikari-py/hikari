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
from unittest import mock
import datetime

import pytest

from hikari.orm import fabric
from hikari.orm import state_registry
from hikari.orm.models import guilds
from hikari.orm.models import permissions


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
def test_channel_payloads():
    return [
        {
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
        },
        {
            "type": 4,
            "id": "123456",
            "guild_id": "54321",
            "position": 69,
            "permission_overwrites": [],
            "name": "dank category",
        },
        {
            "type": 2,
            "id": "9292929",
            "guild_id": "929",
            "position": 66,
            "permission_overwrites": [],
            "name": "roy rodgers mc freely",
            "bitrate": 999,
            "user_limit": 0,
            "parent_id": "42",
        },
    ]


@pytest.fixture
def test_member_payload():
    return {
        "nick": "foobarbaz",
        "roles": ["11111", "22222", "33333", "44444"],
        "joined_at": "2015-04-26T06:26:56.936000+00:00",
        "premium_since": "2019-05-17T06:26:56.936000+00:00",
        # These should be completely ignored.
        "deaf": False,
        "mute": True,
        "user": {
            "id": "123456",
            "username": "Boris Johnson",
            "discriminator": "6969",
            "avatar": "1a2b3c4d",
            "mfa_enabled": True,
            "locale": "gb",
            "flags": 0b00101101,
            "premium_type": 0b1101101,
        },
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


@pytest.fixture
def test_guild_payload(
    test_emoji_payload, test_roles_payloads, test_channel_payloads, test_member_payload, test_voice_state_payload
):
    return {
        "id": "123456",
        "afk_channel_id": "99998888777766",
        "owner_id": "6969696",
        "region": "eu-central",
        "system_channel_id": "19216801",
        "application_id": "10987654321",
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
        "channels": test_channel_payloads,
        "max_members": 25000,
        "vanity_url_code": "loool",
        "description": "This is a server I guess, its a bit crap though",
        "banner": "1a2b3c",
        "premium_tier": 2,
        "premium_subscription_count": 1,
        "preferred_locale": "en-GB",
        "system_channel_flags": 3,
    }


@pytest.fixture()
def mock_state_registry():
    return mock.MagicMock(spec_set=state_registry.IStateRegistry)


@pytest.fixture()
def fabric_obj(mock_state_registry):
    return fabric.Fabric(state_registry=mock_state_registry)


@pytest.mark.model
def test_PartialGuild():
    partial_guild_obj = guilds.PartialGuild(
        {
            "id": "515260097702789121",
            "name": "Catgirls Affinity",
            "splash": "03lf834sa3",
            "banner": "9s9f9f94d",
            "description": "Nyaa",
            "icon": "bb71f469c158984e265093a81b3397fb",
            "features": ["VANITY_URL"],
            "verification_level": 2,
            "vanity_url_code": "nekotime",
        }
    )
    assert partial_guild_obj.id == 515260097702789121
    assert partial_guild_obj.name == "Catgirls Affinity"
    assert partial_guild_obj.splash_hash == "03lf834sa3"
    assert partial_guild_obj.banner_hash == "9s9f9f94d"
    assert partial_guild_obj.description == "Nyaa"
    assert partial_guild_obj.icon_hash == "bb71f469c158984e265093a81b3397fb"
    assert partial_guild_obj.features.pop() is guilds.Feature.VANITY_URL
    assert partial_guild_obj.verification_level is guilds.VerificationLevel.MEDIUM
    assert partial_guild_obj.vanity_url_code == "nekotime"
    partial_guild_obj.__repr__()


@pytest.mark.model
class TestGuild:
    def test_available_Guild(
        self, test_guild_payload, test_emoji_payload, test_member_payload, test_voice_state_payload, fabric_obj
    ):
        guild_obj = guilds.Guild(fabric_obj, test_guild_payload, 9876)

        assert guild_obj.shard_id == 9876
        assert guild_obj.id == 123_456
        assert guild_obj.afk_channel_id == 99_998_888_777_766
        assert guild_obj.owner_id == 6_969_696
        assert guild_obj.voice_region == "eu-central"
        assert guild_obj.system_channel_id == 19_216_801
        assert guild_obj.creator_application_id == 10_987_654_321
        assert guild_obj.name == "L33t guild"
        assert guild_obj.icon_hash == "1a2b3c4d"
        assert guild_obj.splash_hash == "0ff0ff0ff"
        assert guild_obj.afk_timeout == 1200
        assert guild_obj.verification_level == guilds.VerificationLevel.VERY_HIGH
        assert guild_obj.message_notification_level == guilds.DefaultMessageNotificationsLevel.ONLY_MENTIONS
        assert guild_obj.explicit_content_filter_level == guilds.ExplicitContentFilterLevel.ALL_MEMBERS
        assert len(guild_obj.features) == 4
        assert guilds.Feature.ANIMATED_ICON in guild_obj.features
        assert guild_obj.member_count == 14
        assert guild_obj.mfa_level == guilds.MFALevel.ELEVATED
        assert guild_obj.joined_at == datetime.datetime(2019, 5, 17, 6, 26, 56, 936000, datetime.timezone.utc)
        assert guild_obj.is_large is False
        assert guild_obj.is_unavailable is False
        assert guild_obj.my_permissions == (
            permissions.Permission.USE_VAD
            | permissions.Permission.MOVE_MEMBERS
            | permissions.Permission.DEAFEN_MEMBERS
            | permissions.Permission.MUTE_MEMBERS
            | permissions.Permission.SPEAK
            | permissions.Permission.CONNECT
            | permissions.Permission.MENTION_EVERYONE
            | permissions.Permission.READ_MESSAGE_HISTORY
            | permissions.Permission.ATTACH_FILES
            | permissions.Permission.EMBED_LINKS
            | permissions.Permission.MANAGE_MESSAGES
            | permissions.Permission.SEND_TTS_MESSAGES
            | permissions.Permission.SEND_MESSAGES
            | permissions.Permission.VIEW_CHANNEL
            | permissions.Permission.MANAGE_GUILD
            | permissions.Permission.MANAGE_CHANNELS
            | permissions.Permission.ADMINISTRATOR
            | permissions.Permission.BAN_MEMBERS
            | permissions.Permission.KICK_MEMBERS
            | permissions.Permission.CREATE_INSTANT_INVITE
        )
        assert guild_obj.max_members == 25000
        assert guild_obj.vanity_url_code == "loool"
        assert guild_obj.description == "This is a server I guess, its a bit crap though"
        assert guild_obj.banner_hash == "1a2b3c"
        assert guild_obj.premium_tier == guilds.PremiumTier.TIER_2
        assert guild_obj.premium_subscription_count == 1
        assert guild_obj.system_channel_flags & guilds.SystemChannelFlag.PREMIUM_SUBSCRIPTION
        assert guild_obj.system_channel_flags & guilds.SystemChannelFlag.USER_JOIN
        assert guild_obj.preferred_locale == "en-GB"
        guild_obj.__repr__()

        assert fabric_obj.state_registry.parse_role.call_count == 2
        fabric_obj.state_registry.parse_emoji.assert_called_once_with(test_emoji_payload, guild_obj)
        fabric_obj.state_registry.parse_member.assert_called_once_with(test_member_payload, guild_obj)
        assert fabric_obj.state_registry.parse_channel.call_count == 3
        fabric_obj.state_registry.parse_voice_state.assert_called_once_with(test_voice_state_payload, guild_obj)

    def test_unavailable_Guild(self, fabric_obj):
        guild_obj = guilds.Guild(fabric_obj, {"id": "12345678910", "unavailable": True}, 9876)

        assert guild_obj.shard_id == 9876
        assert guild_obj.id == 12_345_678_910
        assert guild_obj.is_unavailable
        guild_obj.__repr__()

    def test_Ban(self, fabric_obj):
        user = object()
        ban = guilds.Ban(fabric_obj, {"user": user, "reason": "being bad"})
        assert ban.reason == "being bad"
        ban.__repr__()
        fabric_obj.state_registry.parse_user.assert_called_once_with(user)
