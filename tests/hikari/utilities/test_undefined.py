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

from hikari.utilities import undefined
from tests.hikari import _helpers


class TestUndefined:
    def test_repr(self):
        assert repr(undefined.Undefined()) == "UNDEFINED"

    def test_str(self):
        assert str(undefined.Undefined()) == "UNDEFINED"

    def test_bool(self):
        assert bool(undefined.Undefined()) is False

    # noinspection PyComparisonWithNone
    def test_singleton_behaviour(self):
        assert undefined.Undefined() is undefined.Undefined()
        assert undefined.Undefined() == undefined.Undefined()
        assert undefined.Undefined() != None
        assert undefined.Undefined() != False

    @_helpers.assert_raises(type_=TypeError)
    def test_cannot_subclass(self):
        class _(undefined.Undefined):
            pass

    def test_count(self):
        assert undefined.Undefined.count(9, 18, undefined.Undefined(), 36, undefined.Undefined(), 54) == 2
