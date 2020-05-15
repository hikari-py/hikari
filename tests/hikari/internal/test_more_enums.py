#!/usr/bin/env python3
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

from hikari.internal import more_enums


class TestEnumMixin:
    def test_str(self):
        class TestType(more_enums.Enum):
            a = 1
            b = 2
            c = 4
            d = 8
            e = 16

        inst = TestType(2)
        assert str(inst) == "b"


class TestFlagMixin:
    def test_str(self):
        class TestType(more_enums.IntFlag):
            a = 1
            b = 2
            c = 4
            d = 8
            e = 16

        inst = TestType(7)

        assert str(inst) == "a, b, c"
