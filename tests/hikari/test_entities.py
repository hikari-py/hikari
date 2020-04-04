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
# along ith Hikari. If not, see <https://www.gnu.org/licenses/>.
from hikari import entities


class TestUnset:
    def test_repr(self):
        assert repr(entities.UNSET) == "UNSET"

    def test_str(self):
        assert str(entities.UNSET) == "UNSET"

    def test_bool(self):
        assert bool(entities.UNSET) is False

    def test_singleton_behaviour(self):
        assert entities.Unset() is entities.Unset()
        assert entities.UNSET is entities.Unset()
