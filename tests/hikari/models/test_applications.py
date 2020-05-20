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

from hikari import application
from hikari.net import urls
from hikari.models import applications
from hikari.models import guilds
from hikari.models import users
from tests.hikari import _helpers


@pytest.fixture()
def mock_app():
    return mock.MagicMock(application.Application)


@pytest.fixture()
def test_partial_integration():
    return {
        "id": "123123123123123",
        "name": "A Name",
        "type": "twitch",
        "account": {"name": "twitchUsername", "id": "123123"},
    }


@pytest.fixture()
def own_connection_payload(test_partial_integration):
    return {
        "friend_sync": False,
        "id": "2513849648",
        "integrations": [test_partial_integration],
        "name": "FS",
        "revoked": False,
        "show_activity": True,
        "type": "twitter",
        "verified": True,
        "visibility": 0,
    }


@pytest.fixture()
def own_guild_payload():
    return {
        "id": "152559372126519269",
        "name": "Isopropyl",
        "icon": "d4a983885dsaa7691ce8bcaaf945a",
        "owner": False,
        "permissions": 2147483647,
        "features": ["DISCOVERABLE"],
    }


@pytest.fixture()
def owner_payload():
    return {"username": "agent 47", "avatar": "hashed", "discriminator": "4747", "id": "474747474", "flags": 1 << 10}


@pytest.fixture()
def team_user_payload():
    return {"username": "aka", "avatar": "I am an avatar", "discriminator": "2222", "id": "202292292"}


@pytest.fixture()
def member_payload(team_user_payload):
    return {"membership_state": 1, "permissions": ["*"], "team_id": "209333111222", "user": team_user_payload}


@pytest.fixture()
def team_payload(member_payload):
    return {"icon": "hashtag", "id": "202020202", "members": [member_payload], "owner_user_id": "393030292"}


@pytest.fixture()
def application_information_payload(owner_payload, team_payload):
    return {
        "id": "209333111222",
        "name": "Dream Sweet in Sea Major",
        "icon": "iwiwiwiwiw",
        "description": "I am an application",
        "rpc_origins": ["127.0.0.0"],
        "bot_public": True,
        "bot_require_code_grant": False,
        "owner": owner_payload,
        "summary": "",
        "verify_key": "698c5d0859abb686be1f8a19e0e7634d8471e33817650f9fb29076de227bca90",
        "team": team_payload,
        "guild_id": "2020293939",
        "primary_sku_id": "2020202002",
        "slug": "192.168.1.254",
        "cover_image": "hashmebaby",
    }


class TestOwnConnection:
    def test_deserialize(self, own_connection_payload, test_partial_integration, mock_app):
        mock_integration_obj = mock.MagicMock(guilds.PartialGuildIntegration)
        with mock.patch.object(guilds.PartialGuildIntegration, "deserialize", return_value=mock_integration_obj):
            connection_obj = applications.OwnConnection.deserialize(own_connection_payload, app=mock_app)
            guilds.PartialGuildIntegration.deserialize.assert_called_once_with(test_partial_integration, app=mock_app)
        assert connection_obj.id == "2513849648"
        assert connection_obj.name == "FS"
        assert connection_obj.type == "twitter"
        assert connection_obj.is_revoked is False
        assert connection_obj.integrations == [mock_integration_obj]
        assert connection_obj.is_verified is True
        assert connection_obj.is_friend_syncing is False
        assert connection_obj.is_showing_activity is True
        assert connection_obj.visibility is applications.ConnectionVisibility.NONE


class TestOwnGuild:
    def test_deserialize(self, own_guild_payload, mock_app):
        own_guild_obj = applications.OwnGuild.deserialize(own_guild_payload, app=mock_app)
        assert own_guild_obj.is_owner is False
        assert own_guild_obj.my_permissions == 2147483647


class TestApplicationOwner:
    def test_deserialize(self, owner_payload, mock_app):
        owner_obj = applications.ApplicationOwner.deserialize(owner_payload, app=mock_app)
        assert owner_obj.username == "agent 47"
        assert owner_obj.discriminator == "4747"
        assert owner_obj.id == 474747474
        assert owner_obj.flags == users.UserFlag.TEAM_USER
        assert owner_obj.avatar_hash == "hashed"

    @pytest.fixture()
    def owner_obj(self, owner_payload, mock_app):
        return applications.ApplicationOwner(username=None, discriminator=None, id=None, flags=None, avatar_hash=None)

    def test_is_team_user(self, owner_obj):
        owner_obj.flags = users.UserFlag.TEAM_USER | users.UserFlag.SYSTEM
        assert owner_obj.is_team_user is True
        owner_obj.flags = users.UserFlag.BUG_HUNTER_LEVEL_1 | users.UserFlag.HYPESQUAD_EVENTS
        assert owner_obj.is_team_user is False


class TestTeamMember:
    def test_deserialize(self, member_payload, team_user_payload, mock_app):
        mock_team_user = mock.MagicMock(users.User)
        with _helpers.patch_marshal_attr(
            applications.TeamMember, "user", deserializer=users.User.deserialize, return_value=mock_team_user
        ) as patched_deserializer:
            member_obj = applications.TeamMember.deserialize(member_payload, app=mock_app)
            patched_deserializer.assert_called_once_with(team_user_payload, app=mock_app)
        assert member_obj.user is mock_team_user
        assert member_obj.membership_state is applications.TeamMembershipState.INVITED
        assert member_obj.permissions == {"*"}
        assert member_obj.team_id == 209333111222


class TestTeam:
    def test_deserialize(self, team_payload, member_payload, mock_app):
        mock_member = mock.MagicMock(applications.Team, user=mock.MagicMock(id=202292292))
        with mock.patch.object(applications.TeamMember, "deserialize", return_value=mock_member):
            team_obj = applications.Team.deserialize(team_payload, app=mock_app)
            applications.TeamMember.deserialize.assert_called_once_with(member_payload, app=mock_app)
        assert team_obj.members == {202292292: mock_member}
        assert team_obj.icon_hash == "hashtag"
        assert team_obj.id == 202020202
        assert team_obj.owner_user_id == 393030292

    @pytest.fixture()
    def team_obj(self, team_payload):
        return applications.Team(id=None, icon_hash="3o2o32o", members=None, owner_user_id=None,)

    def test_format_icon_url(self):
        mock_team = mock.MagicMock(applications.Team, icon_hash="3o2o32o", id=22323)
        mock_url = "https://cdn.discordapp.com/team-icons/22323/3o2o32o.jpg?size=64"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = applications.Team.format_icon_url(mock_team, format_="jpg", size=64)
            urls.generate_cdn_url.assert_called_once_with("team-icons", "22323", "3o2o32o", format_="jpg", size=64)
        assert url == mock_url

    def test_format_icon_url_returns_none(self):
        mock_team = mock.MagicMock(applications.Team, icon_hash=None, id=22323)
        with mock.patch.object(urls, "generate_cdn_url", return_value=...):
            url = applications.Team.format_icon_url(mock_team, format_="jpg", size=64)
            urls.generate_cdn_url.assert_not_called()
        assert url is None

    def test_icon_url(self, team_obj):
        mock_url = "https://cdn.discordapp.com/team-icons/202020202/hashtag.png?size=4096"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = team_obj.icon_url
            urls.generate_cdn_url.assert_called_once()
        assert url == mock_url


class TestApplication:
    def test_deserialize(self, application_information_payload, team_payload, owner_payload, mock_app):
        application_obj = applications.Application.deserialize(application_information_payload, app=mock_app)
        assert application_obj.team == applications.Team.deserialize(team_payload)
        assert application_obj.team._gateway_consumer is mock_app
        assert application_obj.owner == applications.ApplicationOwner.deserialize(owner_payload)
        assert application_obj.owner._gateway_consumer is mock_app
        assert application_obj.id == 209333111222
        assert application_obj.name == "Dream Sweet in Sea Major"
        assert application_obj.icon_hash == "iwiwiwiwiw"
        assert application_obj.description == "I am an application"
        assert application_obj.rpc_origins == {"127.0.0.0"}
        assert application_obj.is_bot_public is True
        assert application_obj.is_bot_code_grant_required is False
        assert application_obj.summary == ""
        assert application_obj.verify_key == b"698c5d0859abb686be1f8a19e0e7634d8471e33817650f9fb29076de227bca90"
        assert application_obj.guild_id == 2020293939
        assert application_obj.primary_sku_id == 2020202002
        assert application_obj.slug == "192.168.1.254"
        assert application_obj.cover_image_hash == "hashmebaby"

    @pytest.fixture()
    def application_obj(self, application_information_payload):
        return applications.Application(
            team=None,
            owner=None,
            id=209333111222,
            name=None,
            icon_hash="iwiwiwiwiw",
            description=None,
            rpc_origins=None,
            is_bot_public=None,
            is_bot_code_grant_required=None,
            summary=None,
            verify_key=None,
            guild_id=None,
            primary_sku_id=None,
            slug=None,
            cover_image_hash="hashmebaby",
        )

    @pytest.fixture()
    def mock_application(self):
        return mock.MagicMock(applications.Application, id=22222)

    def test_icon_url(self, application_obj):
        mock_url = "https://cdn.discordapp.com/app-icons/209333111222/iwiwiwiwiw.png?size=4096"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = application_obj.icon_url
            urls.generate_cdn_url.assert_called_once()
        assert url == "https://cdn.discordapp.com/app-icons/209333111222/iwiwiwiwiw.png?size=4096"

    def test_format_icon_url(self, mock_application):
        mock_application.icon_hash = "wosososoos"
        mock_url = "https://cdn.discordapp.com/app-icons/22222/wosososoos.jpg?size=4"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = applications.Application.format_icon_url(mock_application, format_="jpg", size=4)
            urls.generate_cdn_url.assert_called_once_with(
                "application-icons", "22222", "wosososoos", format_="jpg", size=4
            )
        assert url == mock_url

    def test_format_icon_url_returns_none(self, mock_application):
        mock_application.icon_hash = None
        with mock.patch.object(urls, "generate_cdn_url", return_value=...):
            url = applications.Application.format_icon_url(mock_application, format_="jpg", size=4)
            urls.generate_cdn_url.assert_not_called()
        assert url is None

    def test_cover_image_url(self, application_obj):
        mock_url = "https://cdn.discordapp.com/app-assets/209333111222/hashmebaby.png?size=4096"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = application_obj.cover_image_url
            urls.generate_cdn_url.assert_called_once()
        assert url == mock_url

    def test_format_cover_image_url(self, mock_application):
        mock_application.cover_image_hash = "wowowowowo"
        mock_url = "https://cdn.discordapp.com/app-assets/22222/wowowowowo.jpg?size=42"
        with mock.patch.object(urls, "generate_cdn_url", return_value=mock_url):
            url = applications.Application.format_cover_image_url(mock_application, format_="jpg", size=42)
            urls.generate_cdn_url.assert_called_once_with(
                "application-assets", "22222", "wowowowowo", format_="jpg", size=42
            )
        assert url == mock_url

    def test_format_cover_image_url_returns_none(self, mock_application):
        mock_application.cover_image_hash = None
        with mock.patch.object(urls, "generate_cdn_url", return_value=...):
            url = applications.Application.format_cover_image_url(mock_application, format_="jpg", size=42)
            urls.generate_cdn_url.assert_not_called()
        assert url is None
