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
from hikari.internal import cdn
from hikari import channels
from hikari import guilds
from hikari import invites
from hikari import users
from tests.hikari import _helpers


@pytest.fixture()
def test_user_payload():
    return {"id": "2020202", "username": "bang", "discriminator": "2222", "avatar": None}


@pytest.fixture()
def test_2nd_user_payload():
    return {"id": "1231231", "username": "soad", "discriminator": "3333", "avatar": None}


@pytest.fixture()
def test_invite_guild_payload():
    return {
        "id": "56188492224814744",
        "name": "Testin' Your Scene",
        "splash": "aSplashForSure",
        "banner": "aBannerForSure",
        "description": "Describe me cute kitty.",
        "icon": "bb71f469c158984e265093a81b3397fb",
        "features": [],
        "verification_level": 2,
        "vanity_url_code": "I-am-very-vain",
    }


@pytest.fixture()
def test_partial_channel():
    return {"id": "303030", "name": "channel-time", "type": 3}


@pytest.fixture()
def test_invite_payload(test_user_payload, test_2nd_user_payload, test_invite_guild_payload, test_partial_channel):
    return {
        "code": "aCode",
        "guild": test_invite_guild_payload,
        "channel": test_partial_channel,
        "inviter": test_user_payload,
        "target_user": test_2nd_user_payload,
        "target_user_type": 1,
        "approximate_presence_count": 42,
        "approximate_member_count": 84,
    }


@pytest.fixture()
def test_invite_with_metadata_payload(test_invite_payload):
    return {
        **test_invite_payload,
        "uses": 3,
        "max_uses": 8,
        "max_age": 239349393,
        "temporary": True,
        "created_at": "2015-04-26T06:26:56.936000+00:00",
    }


class TestInviteGuild:
    @pytest.fixture()
    def invite_guild_obj(self, test_invite_guild_payload):
        return invites.InviteGuild.deserialize(test_invite_guild_payload)

    def test_deserialize(self, invite_guild_obj):
        assert invite_guild_obj.splash_hash == "aSplashForSure"
        assert invite_guild_obj.banner_hash == "aBannerForSure"
        assert invite_guild_obj.description == "Describe me cute kitty."
        assert invite_guild_obj.verification_level is guilds.GuildVerificationLevel.MEDIUM
        assert invite_guild_obj.vanity_url_code == "I-am-very-vain"

    def test_format_splash_url(self, invite_guild_obj):
        mock_url = "https://not-al"
        with mock.patch.object(cdn, "generate_cdn_url", return_value=mock_url):
            url = invite_guild_obj.format_splash_url(fmt="nyaapeg", size=4000)
            cdn.generate_cdn_url.assert_called_once_with(
                "splashes", "56188492224814744", "aSplashForSure", fmt="nyaapeg", size=4000
            )
        assert url is mock_url

    def test_format_splash_url_returns_none(self, invite_guild_obj):
        invite_guild_obj.splash_hash = None
        with mock.patch.object(cdn, "generate_cdn_url", return_value=...):
            url = invite_guild_obj.format_splash_url()
            cdn.generate_cdn_url.assert_not_called()
        assert url is None

    def test_splash_url(self, invite_guild_obj):
        mock_url = "https://not-al"
        with mock.patch.object(cdn, "generate_cdn_url", return_value=mock_url):
            url = invite_guild_obj.splash_url
            cdn.generate_cdn_url.assert_called_once()
        assert url is mock_url

    def test_format_banner_url(self, invite_guild_obj):
        mock_url = "https://not-al"
        with mock.patch.object(cdn, "generate_cdn_url", return_value=mock_url):
            url = invite_guild_obj.format_banner_url(fmt="nyaapeg", size=4000)
            cdn.generate_cdn_url.assert_called_once_with(
                "banners", "56188492224814744", "aBannerForSure", fmt="nyaapeg", size=4000
            )
        assert url is mock_url

    def test_format_banner_url_returns_none(self, invite_guild_obj):
        invite_guild_obj.banner_hash = None
        with mock.patch.object(cdn, "generate_cdn_url", return_value=...):
            url = invite_guild_obj.format_banner_url()
            cdn.generate_cdn_url.assert_not_called()
        assert url is None

    def test_banner_url(self, invite_guild_obj):
        mock_url = "https://not-al"
        with mock.patch.object(cdn, "generate_cdn_url", return_value=mock_url):
            url = invite_guild_obj.banner_url
            cdn.generate_cdn_url.assert_called_once()
        assert url is mock_url


class TestVanityUrl:
    @pytest.fixture()
    def vanity_url_payload(self):
        return {"code": "iamacode", "uses": 42}

    def test_deserialize(self, vanity_url_payload):
        vanity_url_obj = invites.VanityUrl.deserialize(vanity_url_payload)
        assert vanity_url_obj.code == "iamacode"
        assert vanity_url_obj.uses == 42


class TestInvite:
    def test_deserialize(
        self,
        test_invite_payload,
        test_user_payload,
        test_2nd_user_payload,
        test_partial_channel,
        test_invite_guild_payload,
    ):
        mock_guild = mock.MagicMock(invites.InviteGuild)
        mock_channel = mock.MagicMock(channels.PartialChannel)
        mock_user_1 = mock.MagicMock(users.User)
        mock_user_2 = mock.MagicMock(users.User)
        with _helpers.patch_marshal_attr(
            invites.Invite, "guild", deserializer=invites.InviteGuild.deserialize, return_value=mock_guild
        ) as mock_guld_deseralize:
            with _helpers.patch_marshal_attr(
                invites.Invite, "channel", deserializer=channels.PartialChannel.deserialize, return_value=mock_channel
            ) as mock_channel_deseralize:
                with _helpers.patch_marshal_attr(
                    invites.Invite, "inviter", deserializer=users.User.deserialize, return_value=mock_user_1
                ) as mock_inviter_deseralize:
                    with _helpers.patch_marshal_attr(
                        invites.Invite, "target_user", deserializer=users.User.deserialize, return_value=mock_user_2
                    ) as mock_target_user_deseralize:
                        invite_obj = invites.Invite.deserialize(test_invite_payload)
                        mock_target_user_deseralize.assert_called_once_with(test_2nd_user_payload)
                    mock_inviter_deseralize.assert_called_once_with(test_user_payload)
                mock_channel_deseralize.assert_called_once_with(test_partial_channel)
            mock_guld_deseralize.assert_called_once_with(test_invite_guild_payload)
        assert invite_obj.code == "aCode"
        assert invite_obj.guild is mock_guild
        assert invite_obj.channel is mock_channel
        assert invite_obj.inviter is mock_user_1
        assert invite_obj.target_user is mock_user_2
        assert invite_obj.target_user_type is invites.TargetUserType.STREAM
        assert invite_obj.approximate_member_count == 84
        assert invite_obj.approximate_presence_count == 42


class TestInviteWithMetadata:
    @pytest.fixture()
    @_helpers.patch_marshal_attr(invites.InviteWithMetadata, "guild", deserializer=invites.InviteGuild.deserialize)
    @_helpers.patch_marshal_attr(
        invites.InviteWithMetadata, "channel", deserializer=channels.PartialChannel.deserialize
    )
    @_helpers.patch_marshal_attr(invites.InviteWithMetadata, "inviter", deserializer=users.User.deserialize)
    @_helpers.patch_marshal_attr(invites.InviteWithMetadata, "target_user", deserializer=users.User.deserialize)
    def mock_invite_with_metadata(self, *args, test_invite_with_metadata_payload):
        return invites.InviteWithMetadata.deserialize(test_invite_with_metadata_payload)

    @_helpers.patch_marshal_attr(invites.InviteWithMetadata, "guild", deserializer=invites.InviteGuild.deserialize)
    @_helpers.patch_marshal_attr(
        invites.InviteWithMetadata, "channel", deserializer=channels.PartialChannel.deserialize
    )
    @_helpers.patch_marshal_attr(invites.InviteWithMetadata, "inviter", deserializer=users.User.deserialize)
    @_helpers.patch_marshal_attr(invites.InviteWithMetadata, "target_user", deserializer=users.User.deserialize)
    def test_deserialize(self, *deserializers, test_invite_with_metadata_payload):
        mock_datetime = mock.MagicMock(datetime.datetime)
        with _helpers.patch_marshal_attr(
            invites.InviteWithMetadata,
            "created_at",
            deserializer=hikari.internal.conversions.parse_iso_8601_ts,
            return_value=mock_datetime,
        ) as mock_created_at_deserializer:
            invite_with_metadata_obj = invites.InviteWithMetadata.deserialize(test_invite_with_metadata_payload)
            mock_created_at_deserializer.assert_called_once_with("2015-04-26T06:26:56.936000+00:00")
        assert invite_with_metadata_obj.uses == 3
        assert invite_with_metadata_obj.max_uses == 8
        assert invite_with_metadata_obj.max_age == datetime.timedelta(seconds=239349393)
        assert invite_with_metadata_obj.is_temporary is True
        assert invite_with_metadata_obj.created_at is mock_datetime

    def test_max_age_when_zero(self, test_invite_with_metadata_payload):
        test_invite_with_metadata_payload["max_age"] = 0
        assert invites.InviteWithMetadata.deserialize(test_invite_with_metadata_payload).max_age is None

    def test_expires_at(self, mock_invite_with_metadata):
        assert mock_invite_with_metadata.expires_at == datetime.datetime.fromisoformat(
            "2022-11-25 12:23:29.936000+00:00"
        )

    def test_expires_at_returns_None(self, mock_invite_with_metadata):
        mock_invite_with_metadata.max_age = None
        assert mock_invite_with_metadata.expires_at is None
