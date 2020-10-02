# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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
import mock
import pytest

from hikari import applications
from hikari import urls
from hikari import users
from hikari.internal import routes
from tests.hikari import hikari_test_helpers


def test_OAuth2Scope_str_operator():
    scope = applications.OAuth2Scope("activities.read")
    assert str(scope) == "ACTIVITIES_READ"


def test_ConnectionVisibility_str_operator():
    connection_visibility = applications.ConnectionVisibility(1)
    assert str(connection_visibility) == "EVERYONE"


def test_TeamMembershipState_str_operator():
    state = applications.TeamMembershipState(2)
    assert str(state) == "ACCEPTED"


def test_TeamMember_str_operator():
    mock_team_member = mock.Mock(
        applications.TeamMember, user=mock.Mock(users.User, __str__=mock.Mock(return_value="mario#1234"))
    )
    assert applications.TeamMember.__str__(mock_team_member) == "mario#1234"


def test_Team_str_operator():
    team = applications.Team(id=696969, app=object(), icon_hash="", members=[], owner_id=0)
    assert str(team) == "Team 696969"


def test_Application_str_operator():
    mock_application = mock.Mock(applications.Application)
    mock_application.name = "beans"
    assert applications.Application.__str__(mock_application) == "beans"


class TestTeam:
    @pytest.fixture()
    def model(self):
        return hikari_test_helpers.mock_class_namespace(
            applications.Team, slots_=False, init_=False, id=123, icon_hash="ahashicon"
        )()

    def test_icon_url_property(self, model):
        model.format_icon = mock.Mock(return_value="url")

        assert model.icon_url == "url"

        model.format_icon.assert_called_once_with()

    def test_format_icon_when_hash_is_None(self, model):
        model.icon_hash = None

        with mock.patch.object(
            routes, "CDN_TEAM_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.format_icon(ext="jpeg", size=1) is None

        route.compile_to_file.assert_not_called()

    def test_format_icon_when_hash_is_not_None(self, model):
        with mock.patch.object(
            routes, "CDN_TEAM_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.format_icon(ext="jpeg", size=1) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, team_id=123, hash="ahashicon", size=1, file_format="jpeg"
        )


class TestApplication:
    @pytest.fixture()
    def model(self):
        return hikari_test_helpers.mock_class_namespace(
            applications.Application,
            init_=False,
            slots_=False,
            id=123,
            icon_hash="ahashicon",
            cover_image_hash="ahashcover",
        )()

    def test_icon_url_property(self, model):
        model.format_icon = mock.Mock(return_value="url")

        assert model.icon_url == "url"

        model.format_icon.assert_called_once_with()

    def test_format_icon_when_hash_is_None(self, model):
        model.icon_hash = None

        with mock.patch.object(
            routes, "CDN_APPLICATION_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.format_icon(ext="jpeg", size=1) is None

        route.compile_to_file.assert_not_called()

    def test_format_icon_when_hash_is_not_None(self, model):
        with mock.patch.object(
            routes, "CDN_APPLICATION_ICON", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.format_icon(ext="jpeg", size=1) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, application_id=123, hash="ahashicon", size=1, file_format="jpeg"
        )

    def test_cover_image_url_property(self, model):
        model.format_cover_image = mock.Mock(return_value="url")

        assert model.cover_image_url == "url"

        model.format_cover_image.assert_called_once_with()

    def test_format_cover_image_when_hash_is_None(self, model):
        model.cover_image_hash = None

        with mock.patch.object(
            routes, "CDN_APPLICATION_COVER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.format_cover_image(ext="jpeg", size=1) is None

        route.compile_to_file.assert_not_called()

    def test_format_cover_image_when_hash_is_not_None(self, model):
        with mock.patch.object(
            routes, "CDN_APPLICATION_COVER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert model.format_cover_image(ext="jpeg", size=1) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, application_id=123, hash="ahashcover", size=1, file_format="jpeg"
        )
