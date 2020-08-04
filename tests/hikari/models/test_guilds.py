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

from hikari.models import guilds
from hikari.models import users


def test_GuildExplicitContentFilterLevel_str_operator():
    level = guilds.GuildExplicitContentFilterLevel(1)
    assert str(level) == "MEMBERS_WITHOUT_ROLES"


def test_GuildFeature_str_operator():
    feature = guilds.GuildFeature("ANIMATED_ICON")
    assert str(feature) == "ANIMATED_ICON"


def test_GuildMessageNotificationsLevel_str_operator():
    level = guilds.GuildMessageNotificationsLevel(1)
    assert str(level) == "ONLY_MENTIONS"


def test_GuildMFALevel_str_operator():
    level = guilds.GuildMFALevel(1)
    assert str(level) == "ELEVATED"


def test_GuildPremiumTier_str_operator():
    level = guilds.GuildPremiumTier(1)
    assert str(level) == "TIER_1"


def test_GuildSystemChannelFlag_str_operator():
    flag = guilds.GuildSystemChannelFlag(1 << 0)
    assert str(flag) == "SUPPRESS_USER_JOIN"


def test_GuildVerificationLevel_str_operator():
    level = guilds.GuildVerificationLevel(0)
    assert str(level) == "NONE"


def test_Member_display_name_property_when_nickname_set():
    member = guilds.Member()
    user = users.UserImpl()
    user.username = "davfsa"
    member.user = user
    member.nickname = "davb"
    assert member.display_name == "davb"


def test_Member_display_name_property_when_nickname_not_set():
    member = guilds.Member()
    user = users.UserImpl()
    user.username = "davfsa"
    member.user = user
    member.nickname = None
    assert member.display_name == "davfsa"


def test_Member_str_operator():
    mock_user = mock.Mock(users.User, __str__=mock.Mock(return_value="thomm.o#8637"))
    mock_member = mock.Mock(guilds.Member, user=mock_user)
    assert guilds.Member.__str__(mock_member) == "thomm.o#8637"


def test_PartialRole_str_operator():
    mock_role = mock.Mock(guilds.Role)
    mock_role.name = "The Big Cool"
    assert guilds.PartialRole.__str__(mock_role) == "The Big Cool"


def test_IntegrationAccount_str_operator():
    mock_account = mock.Mock(guilds.IntegrationAccount)
    mock_account.name = "your mother"
    assert guilds.IntegrationAccount.__str__(mock_account) == "your mother"


def test_PartialIntegration_str_operator():
    mock_integration = mock.Mock(guilds.PartialIntegration)
    mock_integration.name = "not an integration"
    assert guilds.PartialIntegration.__str__(mock_integration) == "not an integration"


def test_PartialGuild_str_operator():
    mock_guild = mock.Mock(guilds.PartialGuild)
    mock_guild.name = "hikari"
    assert guilds.PartialGuild.__str__(mock_guild) == "hikari"
