# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import annotations

import datetime

import mock
import pytest

from hikari import applications
from hikari import snowflakes
from hikari import traits
from hikari import urls
from hikari import users
from hikari.internal import routes


class TestTeamMember:
    @pytest.fixture
    def model(self):
        user = mock.Mock(users.User)
        user.avatar_hash = "a_test"
        user.banner_hash = "a_test2"
        return applications.TeamMember(
            membership_state=4, permissions=["*"], team_id=snowflakes.Snowflake(34123), user=user
        )

    def test_app_property(self, model: applications.TeamMember):
        assert model.app is model.user.app

    def test_avatar_decoration_property(self, model: applications.TeamMember):
        assert model.avatar_decoration is model.user.avatar_decoration

    def test_avatar_hash_property(self, model: applications.TeamMember):
        assert model.avatar_hash is model.user.avatar_hash

    def test_avatar_url_property(self, model: applications.TeamMember):
        assert model.avatar_url is model.user.make_avatar_url()

    def test_banner_hash_property(self, model: applications.TeamMember):
        assert model.banner_hash is model.user.banner_hash

    def test_banner_url_property(self, model: applications.TeamMember):
        assert model.banner_url is model.user.make_banner_url()

    def test_make_avatar_url(self, model: applications.TeamMember):
        assert model.make_avatar_url() is model.user.make_avatar_url()

    def test_make_banner_url(self, model: applications.TeamMember):
        assert model.make_banner_url() is model.user.make_banner_url()

    def test_accent_color_property(self, model: applications.TeamMember):
        assert model.accent_color is model.user.accent_color

    def test_default_avatar_url_property(self, model: applications.TeamMember):
        assert model.default_avatar_url is model.user.default_avatar_url

    def test_discriminator_property(self, model: applications.TeamMember):
        assert model.discriminator is model.user.discriminator

    def test_flags_property(self, model: applications.TeamMember):
        assert model.flags is model.user.flags

    def test_id_property(self, model: applications.TeamMember):
        assert model.id is model.user.id

    def test_is_bot_property(self, model: applications.TeamMember):
        assert model.is_bot is model.user.is_bot

    def test_is_system_property(self, model: applications.TeamMember):
        assert model.is_system is model.user.is_system

    def test_mention_property(self, model: applications.TeamMember):
        assert model.mention is model.user.mention

    def test_username_property(self, model: applications.TeamMember):
        assert model.username is model.user.username

    def test_str_operator(self):
        mock_team_member = mock.Mock(
            applications.TeamMember, user=mock.Mock(users.User, __str__=mock.Mock(return_value="mario#1234"))
        )
        assert applications.TeamMember.__str__(mock_team_member) == "mario#1234"


class TestTeam:
    @pytest.fixture
    def team(self) -> applications.Team:
        return applications.Team(
            app=mock.Mock(traits.RESTAware),
            id=snowflakes.Snowflake(123),
            name="beanos",
            icon_hash="icon_hash",
            members={},
            owner_id=snowflakes.Snowflake(456),
        )

    def test_str_operator(self, team: applications.Team):
        assert str(team) == "Team beanos (123)"

    def test_make_icon_url_format_set_to_deprecated_ext_argument_if_provided(self, team: applications.Team):
        with mock.patch.object(
            routes, "CDN_TEAM_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert team.make_icon_url(ext="JPEG") == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, team_id=123, hash="icon_hash", size=4096, file_format="JPEG", lossless=True
        )

    def test_icon_url_property(self, team: applications.Team):
        with mock.patch.object(applications.Team, "make_icon_url", return_value="url"):
            assert team.icon_url == "url"

    def test_make_icon_url_when_hash_is_None(self, team: applications.Team):
        with (
            mock.patch.object(team, "icon_hash", None),
            mock.patch.object(
                routes, "CDN_TEAM_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
            ) as patched_cdn_team_icon_route,
        ):
            assert team.make_icon_url(file_format="JPEG", size=1) is None

        patched_cdn_team_icon_route.compile_to_file.assert_not_called()

    def test_make_icon_url_when_hash_is_not_None(self, team: applications.Team):
        with mock.patch.object(
            routes, "CDN_TEAM_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert team.make_icon_url(file_format="JPEG", size=1) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, team_id=123, hash="icon_hash", size=1, file_format="JPEG", lossless=True
        )


class TestApplication:
    @pytest.fixture
    def application(self) -> applications.Application:
        return applications.Application(
            id=snowflakes.Snowflake(123),
            name="name",
            description="description",
            icon_hash="icon_hash",
            app=mock.Mock(),
            is_bot_public=False,
            is_bot_code_grant_required=False,
            owner=mock.Mock(),
            rpc_origins=None,
            flags=applications.ApplicationFlags.EMBEDDED,
            public_key=b"public_key",
            team=None,
            cover_image_hash="cover_image_hash",
            terms_of_service_url=None,
            privacy_policy_url=None,
            role_connections_verification_url=None,
            custom_install_url=None,
            tags=[],
            install_parameters=None,
            approximate_guild_count=0,
            approximate_user_install_count=0,
            integration_types_config={},
        )

    def test_make_icon_url_format_set_to_deprecated_ext_argument_if_provided(
        self, application: applications.Application
    ):
        with mock.patch.object(
            routes, "CDN_APPLICATION_COVER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert application.make_cover_image_url(ext="JPEG") == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, application_id=123, hash="cover_image_hash", size=4096, file_format="JPEG", lossless=True
        )

    def test_cover_image_url_property(self, application: applications.Application):
        with mock.patch.object(
            routes, "CDN_APPLICATION_COVER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as patched_cdn_application_cover:
            assert application.make_cover_image_url(file_format="JPEG", size=1) == "file"

        patched_cdn_application_cover.compile_to_file.assert_called_once_with(
            "https://cdn.discordapp.com",
            application_id=123,
            hash="cover_image_hash",
            size=1,
            file_format="JPEG",
            lossless=True,
        )

    def test_make_cover_image_url_when_hash_is_not_None(self, application: applications.Application):
        with mock.patch.object(
            routes, "CDN_APPLICATION_COVER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as patched_cdn_application_cover:
            assert application.make_cover_image_url(file_format="JPEG", size=1) == "file"

        patched_cdn_application_cover.compile_to_file.assert_called_once_with(
            urls.CDN_URL, application_id=123, hash="cover_image_hash", size=1, file_format="JPEG", lossless=True
        )


class TestPartialOAuth2Token:
    def test__str__(self):
        token = applications.PartialOAuth2Token(
            access_token="54123123123",
            token_type=applications.TokenType.BEARER,
            expires_in=datetime.timedelta(300),
            scopes=[applications.OAuth2Scope.APPLICATIONS_COMMANDS],
        )

        assert str(token) == "54123123123"


def test_get_token_id_extracts_id():
    assert applications.get_token_id("MTE1NTkwMDk3MTAwODY1NTQx.x.y") == 115590097100865541


def test_get_token_id_adds_padding():
    assert applications.get_token_id("NDMxMjMxMjMxMjM.blam.bop") == 43123123123


@pytest.mark.parametrize("token", ["______.222222.dessddssd", "", "b2tva29r.b2tva29r.b2tva29r"])
def test_get_token_id_handles_invalid_token(token: str):
    with pytest.raises(ValueError, match="Unexpected token format"):
        applications.get_token_id(token)
