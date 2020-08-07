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
