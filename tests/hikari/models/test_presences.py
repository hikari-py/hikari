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

from hikari.models import presences


def test_ActivityType_str_operator():
    type = presences.ActivityType(4)
    assert str(type) == "CUSTOM"


def test_ActivityFlag_str_operator():
    flag = presences.ActivityFlag(1 << 4)
    assert str(flag) == "SYNC"


def test_Activity_str_operator():
    activity = presences.Activity(name="something", type=presences.ActivityType(1))
    assert str(activity) == "something"


def test_Status_str_operator():
    status = presences.Status("idle")
    assert str(status) == "IDLE"
