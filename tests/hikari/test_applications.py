# -*- coding: utf-8 -*-
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
import datetime

import mock
import pytest

from hikari import applications
from hikari import urls
from hikari import users
from hikari.errors import ForbiddenError
from hikari.errors import UnauthorizedError
from hikari.internal import routes
from tests.hikari import hikari_test_helpers


class TestTeamMember:
    @pytest.fixture
    def model(self):
        return applications.TeamMember(membership_state=4, permissions=["*"], team_id=34123, user=mock.Mock(users.User))

    def test_app_property(self, model):
        assert model.app is model.user.app

    def test_avatar_hash_property(self, model):
        assert model.avatar_hash is model.user.avatar_hash

    def test_avatar_url_property(self, model):
        assert model.avatar_url is model.user.avatar_url

    def test_banner_hash_property(self, model):
        assert model.banner_hash is model.user.banner_hash

    def test_banner_url_propert(self, model):
        assert model.banner_url is model.user.banner_url

    def test_accent_color_propert(self, model):
        assert model.accent_color is model.user.accent_color

    def test_default_avatar_url_property(self, model):
        assert model.default_avatar_url is model.user.default_avatar_url

    def test_discriminator_property(self, model):
        assert model.discriminator is model.user.discriminator

    def test_flags_property(self, model):
        assert model.flags is model.user.flags

    def test_id_property(self, model):
        assert model.id is model.user.id

    def test_is_bot_property(self, model):
        assert model.is_bot is model.user.is_bot

    def test_is_system_property(self, model):
        assert model.is_system is model.user.is_system

    def test_mention_property(self, model):
        assert model.mention is model.user.mention

    def test_username_property(self, model):
        assert model.username is model.user.username

    def test_str_operator(self):
        mock_team_member = mock.Mock(
            applications.TeamMember, user=mock.Mock(users.User, __str__=mock.Mock(return_value="mario#1234"))
        )
        assert applications.TeamMember.__str__(mock_team_member) == "mario#1234"


class TestTeam:
    @pytest.fixture
    def model(self):
        return hikari_test_helpers.mock_class_namespace(
            applications.Team, slots_=False, init_=False, id=123, icon_hash="ahashicon"
        )()

    def test_str_operator(self):
        team = applications.Team(id=696969, app=object(), name="test", icon_hash="", members=[], owner_id=0)
        assert str(team) == "Team test (696969)"

    def test_icon_url_property(self, model):
        model.make_icon_url = mock.Mock(return_value="url")

        assert model.icon_url == "url"

        model.make_icon_url.assert_called_once_with()

    def test_make_icon_url_when_hash_is_None(self, model):
        model.icon_hash = None

        with mock.patch.object(
            routes, "CDN_TEAM_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_icon_url(ext="jpeg", size=1) is None

        route.compile_to_file.assert_not_called()

    def test_make_icon_url_when_hash_is_not_None(self, model):
        with mock.patch.object(
            routes, "CDN_TEAM_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_icon_url(ext="jpeg", size=1) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, team_id=123, hash="ahashicon", size=1, file_format="jpeg"
        )


class TestApplication:
    @pytest.fixture
    def model(self):
        return hikari_test_helpers.mock_class_namespace(
            applications.Application,
            init_=False,
            slots_=False,
            id=123,
            icon_hash="ahashicon",
            cover_image_hash="ahashcover",
        )()

    def test_cover_image_url_property(self, model):
        model.make_cover_image_url = mock.Mock(return_value="url")

        assert model.cover_image_url == "url"

        model.make_cover_image_url.assert_called_once_with()

    def test_make_cover_image_url_when_hash_is_None(self, model):
        model.cover_image_hash = None

        with mock.patch.object(
            routes, "CDN_APPLICATION_COVER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_cover_image_url(ext="jpeg", size=1) is None

        route.compile_to_file.assert_not_called()

    def test_make_cover_image_url_when_hash_is_not_None(self, model):
        with mock.patch.object(
            routes, "CDN_APPLICATION_COVER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.make_cover_image_url(ext="jpeg", size=1) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, application_id=123, hash="ahashcover", size=1, file_format="jpeg"
        )

    @pytest.mark.asyncio
    async def test_fetch_guild(self, model):
        model.guild_id = 1234
        model.fetch_guild = mock.AsyncMock()

        model.fetch_guild.return_value.id = model.guild_id
        assert (await model.fetch_guild()).id == model.guild_id

        model.fetch_guild.side_effect = UnauthorizedError(
            "blah blah", "interesting", "foo bar", "this is an error", 403
        )
        with pytest.raises(UnauthorizedError):
            await model.fetch_guild()

    @pytest.mark.asyncio
    async def test_fetch_guild_preview(self, model):
        model.fetch_guild_preview = mock.AsyncMock()

        model.fetch_guild_preview.return_value.description = "poggers"
        assert (await model.fetch_guild_preview()).description == "poggers"

        model.fetch_guild_preview.side_effect = ForbiddenError(
            "blah blah", "interesting", "foo bar", "this is an error", 403
        )
        with pytest.raises(ForbiddenError):
            await model.fetch_guild_preview()


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
def test_get_token_id_handles_invalid_token(token):
    with pytest.raises(ValueError, match="Unexpected token format"):
        applications.get_token_id(token)
