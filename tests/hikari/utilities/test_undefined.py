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
        assert repr(undefined.UNDEFINED) == "<undefined value>"

    def test_str(self):
        assert str(undefined.UNDEFINED) == "UNDEFINED"

    def test_bool(self):
        assert bool(undefined.UNDEFINED) is False

    # noinspection PyComparisonWithNone
    def test_singleton_behaviour(self):
        assert undefined.UNDEFINED is undefined.UNDEFINED
        assert undefined.UNDEFINED == undefined.UNDEFINED
        assert undefined.UNDEFINED != None
        assert undefined.UNDEFINED != False

    def test_count(self):
        assert undefined.count(9, 18, undefined.UNDEFINED, 36, undefined.UNDEFINED, 54) == 2

    @_helpers.assert_raises(type_=TypeError)
    def test_cannot_reinstatiate(self):
        type(undefined.UNDEFINED)()
