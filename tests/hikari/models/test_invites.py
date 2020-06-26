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

from hikari.models import invites


def test_TargetUserType_str_operator():
    type = invites.TargetUserType(1)
    assert str(type) == "STREAM"


def test_VanityURL_str_operator():
    url = invites.VanityURL()
    url.code = "hikari"
    assert str(url) == "https://discord.gg/hikari"


def test_Invite_str_operator():
    invite = invites.Invite()
    invite.code = "abcdef"
    assert str(invite) == "https://discord.gg/abcdef"
