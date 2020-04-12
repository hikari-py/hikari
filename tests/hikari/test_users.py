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
from unittest import mock

import pytest

from hikari import users
from hikari.internal import urls


@pytest.fixture()
def test_user_payload():
    return {
        "id": "115590097100865541",
        "username": "nyaa",
        "avatar": "b3b24c6d7cbcdec129d5d537067061a8",
        "discriminator": "6127",
    }


@pytest.fixture()
def test_oauth_user_payload():
    return {
        "id": "379953393319542784",
        "username": "qt pi",
        "avatar": "820d0e50543216e812ad94e6ab7",
        "discriminator": "2880",
        "email": "blahblah@blah.blah",
        "verified": True,
        "locale": "en-US",
        "mfa_enabled": True,
        "flags": int(users.UserFlag.DISCORD_PARTNER | users.UserFlag.DISCORD_EMPLOYEE),
        "premium_type": 1,
    }


class TestUser:
    @pytest.fixture()
    def user_obj(self, test_user_payload):
        return users.User.deserialize(test_user_payload)

    def test_deserialize(self, user_obj):
        assert user_obj.id == 115590097100865541
        assert user_obj.username == "nyaa"
        assert user_obj.avatar_hash == "b3b24c6d7cbcdec129d5d537067061a8"
        assert user_obj.discriminator == "6127"

    def test_avatar_url(self, user_obj):
        mock_url = "https://cdn.discordapp.com/avatars/115590097100865541"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = user_obj.avatar_url
            urls.generate_cdn_url.assert_called_once()
        assert url == mock_url

    def test_default_avatar(self, user_obj):
        assert user_obj.default_avatar == 2

    def test_format_avatar_url_when_animated(self, user_obj):
        mock_url = "https://cdn.discordapp.com/avatars/115590097100865541/a_820d0e50543216e812ad94e6ab7.gif?size=3232"
        user_obj.avatar_hash = "a_820d0e50543216e812ad94e6ab7"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = user_obj.format_avatar_url(size=3232)
            urls.generate_cdn_url.assert_called_once_with(
                "avatars", "115590097100865541", "a_820d0e50543216e812ad94e6ab7", fmt="gif", size=3232
            )
        assert url == mock_url

    def test_format_avatar_url_default(self, user_obj):
        user_obj.avatar_hash = None
        mock_url = "https://cdn.discordapp.com/embed/avatars/2.png"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = user_obj.format_avatar_url(size=3232)
            urls.generate_cdn_url("embed/avatars", "115590097100865541", fmt="png", size=None)
        assert url == mock_url

    def test_format_avatar_url_when_format_specified(self, user_obj):
        mock_url = "https://cdn.discordapp.com/avatars/115590097100865541/b3b24c6d7c37067061a8.nyaapeg?size=1024"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = user_obj.format_avatar_url(fmt="nyaapeg", size=1024)
            urls.generate_cdn_url.assert_called_once_with(
                "avatars", "115590097100865541", "b3b24c6d7cbcdec129d5d537067061a8", fmt="nyaapeg", size=1024
            )
        assert url == mock_url


class TestMyUser:
    def test_deserialize(self, test_oauth_user_payload):
        my_user_obj = users.MyUser.deserialize(test_oauth_user_payload)
        assert my_user_obj.id == 379953393319542784
        assert my_user_obj.username == "qt pi"
        assert my_user_obj.avatar_hash == "820d0e50543216e812ad94e6ab7"
        assert my_user_obj.discriminator == "2880"
        assert my_user_obj.is_mfa_enabled is True
        assert my_user_obj.locale == "en-US"
        assert my_user_obj.is_verified is True
        assert my_user_obj.email == "blahblah@blah.blah"
        assert my_user_obj.flags == users.UserFlag.DISCORD_PARTNER | users.UserFlag.DISCORD_EMPLOYEE
        assert my_user_obj.premium_type is users.PremiumType.NITRO_CLASSIC
