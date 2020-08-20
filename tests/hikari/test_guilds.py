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

from hikari import guilds
from hikari import users
from tests.hikari import hikari_test_helpers


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
    member = hikari_test_helpers.stub_class(guilds.Member, user=object(), nickname="davb")
    assert member.display_name == "davb"


def test_Member_display_name_property_when_nickname_not_set():
    member = hikari_test_helpers.stub_class(guilds.Member, user=mock.Mock(users.User, username="davfsa"), nickname=None)
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
