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

from hikari.models import applications
from hikari.models import users


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
