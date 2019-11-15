#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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

import pytest

from hikari.state import state_registry
from hikari.state.models import guilds
from hikari.state.models import permissions


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
def test_guild_payload(test_emoji_payload, test_roles_payloads, test_channel_payloads, test_member_payload):
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
        "member_count": 14,
        "mfa_level": 1,
        "joined_at": "2019-05-17T06:26:56.936000+00:00",
        "large": False,
        "unavailable": False,
        "voice_states": [],
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


@pytest.mark.model
class TestGuild:
    def test_available_Guild(self, test_guild_payload, test_emoji_payload, test_member_payload):
        s = mock.MagicMock(spec_set=state_registry.IStateRegistry)
        g = guilds.Guild(s, test_guild_payload)

        assert g.id == 123_456
        assert g._afk_channel_id == 99_998_888_777_766
        assert g._owner_id == 6_969_696
        assert g._voice_region == "eu-central"
        assert g._system_channel_id == 19_216_801
        assert g.creator_application_id == 10_987_654_321
        assert g.id == 123456
        assert g.afk_channel_id == 99998888777766
        assert g.owner_id == 6969696
        assert g.voice_region == "eu-central"
        assert g.system_channel_id == 19216801
        assert g.creator_application_id == 10987654321
        assert g.name == "L33t guild"
        assert g.icon_hash == "1a2b3c4d"
        assert g.splash_hash == "0ff0ff0ff"
        assert g.afk_timeout == 1200
        assert g.verification_level == guilds.VerificationLevel.VERY_HIGH
        assert g.message_notification_level == guilds.NotificationLevel.ONLY_MENTIONS
        assert g.explicit_content_filter_level == guilds.ExplicitContentFilterLevel.ALL_MEMBERS
        assert len(g.features) == 4
        assert guilds.Feature.ANIMATED_ICON in g.features
        assert g.member_count == 14
        assert g.mfa_level == guilds.MFALevel.ELEVATED
        assert g.my_permissions == (
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
        assert g.max_members == 25000
        assert g.vanity_url_code == "loool"
        assert g.description == "This is a server I guess, its a bit crap though"
        assert g.banner_hash == "1a2b3c"
        assert g.premium_tier == guilds.PremiumTier.TIER_2
        assert g.premium_subscription_count == 1
        assert g.system_channel_flags & guilds.SystemChannelFlag.PREMIUM_SUBSCRIPTION
        assert g.system_channel_flags & guilds.SystemChannelFlag.USER_JOIN
        assert g.preferred_locale == "en-GB"

        assert s.parse_role.call_count == 2
        s.parse_emoji.assert_called_once_with(test_emoji_payload, g.id)
        s.parse_member.assert_called_once_with(test_member_payload, g.id)
        assert s.parse_channel.call_count == 3

    def test_unavailable_Guild(self):
        s = mock.MagicMock(spec_set=state_registry.IStateRegistry)
        g = guilds.Guild(s, {"id": "12345678910", "unavailable": True})

        assert g.id == 12_345_678_910
        assert g.unavailable

    def test_Ban(self):
        s = mock.MagicMock(spec_set=state_registry.IStateRegistry)
        user = object()
        ban = guilds.Ban(s, {"user": user, "reason": "being bad"})
        assert ban.reason == "being bad"
        s.parse_user.assert_called_once_with(user)
