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
    team_member = applications.TeamMember()
    team_member_user = users.User()
    team_member_user.username = "mario"
    team_member_user.discriminator = "1234"
    team_member.user = team_member_user
    assert str(team_member) == "mario#1234"


def test_Team_str_operator():
    team = applications.Team()
    team.id = 696969
    assert str(team) == "Team 696969"


def test_Application_str_operator():
    application = applications.Application()
    application.name = "beans"
    assert str(application) == "beans"
