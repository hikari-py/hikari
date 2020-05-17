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
import mock
import pytest

from hikari import rest
from hikari import application
from hikari.models import bases
from hikari.models import users
from hikari.internal import urls


@pytest.fixture()
def test_user_payload():
    return {
        "id": "115590097100865541",
        "username": "nyaa",
        "avatar": "b3b24c6d7cbcdec129d5d537067061a8",
        "discriminator": "6127",
        "bot": True,
        "system": True,
        "public_flags": int(users.UserFlag.VERIFIED_BOT_DEVELOPER),
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
        "public_flags": int(users.UserFlag.VERIFIED_BOT_DEVELOPER),
        "flags": int(users.UserFlag.DISCORD_PARTNER | users.UserFlag.DISCORD_EMPLOYEE),
        "premium_type": 1,
    }


@pytest.fixture()
def mock_app() -> application.Application:
    return mock.MagicMock(application.Application, rest=mock.AsyncMock(rest.RESTClient))


class TestUser:
    def test_deserialize(self, test_user_payload, mock_app):
        user_obj = users.User.deserialize(test_user_payload, app=mock_app)
        assert user_obj.id == 115590097100865541
        assert user_obj.username == "nyaa"
        assert user_obj.avatar_hash == "b3b24c6d7cbcdec129d5d537067061a8"
        assert user_obj.discriminator == "6127"
        assert user_obj.is_bot is True
        assert user_obj.is_system is True
        assert user_obj.flags == users.UserFlag.VERIFIED_BOT_DEVELOPER

    @pytest.fixture()
    def user_obj(self, test_user_payload, mock_app):
        return users.User(
            app=mock_app,
            id=bases.Snowflake(115590097100865541),
            username=None,
            avatar_hash="b3b24c6d7cbcdec129d5d537067061a8",
            discriminator="6127",
            is_bot=None,
            is_system=None,
            flags=None,
        )

    @pytest.mark.asyncio
    async def test_fetch_self(self, user_obj, mock_app):
        mock_user = mock.MagicMock(users.User)
        mock_app.rest.fetch_user.return_value = mock_user
        assert await user_obj.fetch_self() is mock_user
        mock_app.rest.fetch_user.assert_called_once_with(user=115590097100865541)

    def test_avatar_url(self, user_obj):
        mock_url = "https://cdn.discordapp.com/avatars/115590097100865541"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = user_obj.avatar_url
            urls.generate_cdn_url.assert_called_once()
        assert url == mock_url

    def test_default_avatar_index(self, user_obj):
        assert user_obj.default_avatar_index == 2

    def test_default_avatar_url(self, user_obj):
        mock_url = "https://cdn.discordapp.com/embed/avatars/2.png"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = user_obj.default_avatar_url
            urls.generate_cdn_url.assert_called_once_with("embed", "avatars", "2", format_="png", size=None)
        assert url == mock_url

    def test_format_avatar_url_when_animated(self, user_obj):
        mock_url = "https://cdn.discordapp.com/avatars/115590097100865541/a_820d0e50543216e812ad94e6ab7.gif?size=3232"
        user_obj.avatar_hash = "a_820d0e50543216e812ad94e6ab7"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = user_obj.format_avatar_url(size=3232)
            urls.generate_cdn_url.assert_called_once_with(
                "avatars", "115590097100865541", "a_820d0e50543216e812ad94e6ab7", format_="gif", size=3232
            )
        assert url == mock_url

    def test_format_avatar_url_default(self, user_obj):
        user_obj.avatar_hash = None
        mock_url = "https://cdn.discordapp.com/embed/avatars/2.png"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = user_obj.format_avatar_url(size=3232)
            urls.generate_cdn_url.assert_called_once_with("embed", "avatars", "2", format_="png", size=None)
        assert url == mock_url

    def test_format_avatar_url_when_format_specified(self, user_obj):
        mock_url = "https://cdn.discordapp.com/avatars/115590097100865541/b3b24c6d7c37067061a8.nyaapeg?size=1024"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = user_obj.format_avatar_url(format_="nyaapeg", size=1024)
            urls.generate_cdn_url.assert_called_once_with(
                "avatars", "115590097100865541", "b3b24c6d7cbcdec129d5d537067061a8", format_="nyaapeg", size=1024
            )
        assert url == mock_url


class TestMyUser:
    def test_deserialize(self, test_oauth_user_payload, mock_app):
        my_user_obj = users.MyUser.deserialize(test_oauth_user_payload, app=mock_app)
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

    @pytest.fixture()
    def my_user_obj(self, mock_app):
        return users.MyUser(
            app=mock_app,
            id=None,
            username=None,
            avatar_hash=None,
            discriminator=None,
            is_mfa_enabled=None,
            locale=None,
            is_verified=None,
            email=None,
            flags=None,
            premium_type=None,
        )

    @pytest.mark.asyncio
    async def test_fetch_me(self, my_user_obj, mock_app):
        mock_user = mock.MagicMock(users.MyUser)
        mock_app.rest.fetch_me.return_value = mock_user
        assert await my_user_obj.fetch_self() is mock_user
        mock_app.rest.fetch_me.assert_called_once()
