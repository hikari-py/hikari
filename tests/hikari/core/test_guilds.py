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
import cymock as mock
import pytest

from hikari.core import guilds
from hikari.internal_utilities import cdn


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
    test_emoji_payload, test_roles_payloads, test_channel_payloads, test_member_payload, test_voice_state_payload
):
    return {
        "id": "265828729970753537",
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
        "rules_channel_id": "42042069",
    }


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
        with mock.patch.object(cdn, "generate_cdn_url", return_value=mock_url):
            url = partial_guild_obj.format_icon_url(fmt="nyaapeg", size=42)
            cdn.generate_cdn_url.assert_called_once_with(
                "icons", "152559372126519269", "d4a983885dsaa7691ce8bcaaf945a", fmt="nyaapeg", size=42
            )
        assert url == mock_url

    def test_format_icon_url_animated_default(self, partial_guild_obj):
        partial_guild_obj.icon_hash = "a_d4a983885dsaa7691ce8bcaaf945a"
        mock_url = "https://cdn.discordapp.com/icons/152559372126519269/a_d4a983885dsaa7691ce8bcaaf945a.gif?size=20"
        with mock.patch.object(cdn, "generate_cdn_url", return_value=mock_url):
            url = partial_guild_obj.format_icon_url()
            cdn.generate_cdn_url.assert_called_once_with(
                "icons", "152559372126519269", "a_d4a983885dsaa7691ce8bcaaf945a", fmt="gif", size=2048
            )
        assert url == mock_url

    def test_format_icon_url_none_animated_default(self, partial_guild_obj):
        partial_guild_obj.icon_hash = "d4a983885dsaa7691ce8bcaaf945a"
        mock_url = "https://cdn.discordapp.com/icons/152559372126519269/d4a983885dsaa7691ce8bcaaf945a.png?size=20"
        with mock.patch.object(cdn, "generate_cdn_url", return_value=mock_url):
            url = partial_guild_obj.format_icon_url()
            cdn.generate_cdn_url.assert_called_once_with(
                "icons", "152559372126519269", "d4a983885dsaa7691ce8bcaaf945a", fmt="png", size=2048
            )
        assert url == mock_url

    def test_format_icon_url_returns_none(self, partial_guild_obj):
        partial_guild_obj.icon_hash = None
        with mock.patch.object(cdn, "generate_cdn_url", return_value=...):
            url = partial_guild_obj.format_icon_url(fmt="nyaapeg", size=42)
            cdn.generate_cdn_url.assert_not_called()
        assert url is None

    def test_format_icon_url(self, partial_guild_obj):
        mock_url = "https://cdn.discordapp.com/icons/152559372126519269/d4a983885dsaa7691ce8bcaaf945a.png?size=20"
        with mock.patch.object(cdn, "generate_cdn_url", return_value=mock_url):
            url = partial_guild_obj.icon_url
            cdn.generate_cdn_url.assert_called_once()
        assert url == mock_url
