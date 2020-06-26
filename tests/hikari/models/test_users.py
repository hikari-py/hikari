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

from hikari.models import users


def test_UserFlag_str_operator():
    flag = users.UserFlag(1 << 17)
    assert str(flag) == "VERIFIED_BOT_DEVELOPER"


def test_PremiumType_str_operator():
    type = users.PremiumType(1)
    assert str(type) == "NITRO_CLASSIC"


def test_PartialUser_str_operator():
    user = users.PartialUser()
    user.username = "thomm.o"
    user.discriminator = "8637"
    assert str(user) == "thomm.o#8637"
