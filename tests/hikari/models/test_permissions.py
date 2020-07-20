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

from hikari.models import permissions


def test_Permission_str_operator_on_zero_value():
    permission = permissions.Permission.NONE
    assert str(permission) == "NONE"


def test_Permission_str_operator():
    permission = permissions.Permission.MANAGE_EMOJIS
    assert str(permission) == "MANAGE_EMOJIS"


def test_combined_Permission_str_operator():
    permission = permissions.Permission.MANAGE_CHANNELS | permissions.Permission.MANAGE_EMOJIS
    assert str(permission) == "MANAGE_CHANNELS | MANAGE_EMOJIS"
