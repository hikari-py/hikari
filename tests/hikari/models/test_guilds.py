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


def test_Member_str_operator():
    member = guilds.Member()
    user = users.UserImpl()
    user.username = "thomm.o"
    user.discriminator = "8637"
    member.user = user
    assert str(member) == "thomm.o#8637"


def test_PartialRole_str_operator():
    role = guilds.PartialRole()
    role.name = "The Big Cool"
    assert str(role) == "The Big Cool"


def test_IntegrationAccount_str_operator():
    account = guilds.IntegrationAccount()
    account.name = "your mother"
    assert str(account) == "your mother"


def test_PartialIntegration_str_operator():
    integration = guilds.PartialIntegration()
    integration.name = "not an integration"
    assert str(integration) == "not an integration"


def test_PartialGuild_str_operator():
    guild = guilds.PartialGuild()
    guild.name = "hikari"
    assert str(guild) == "hikari"
