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
import pytest

from hikari.models import unset
from tests.hikari import _helpers


class TestUnset:
    def test_repr(self):
        assert repr(unset.UNSET) == "UNSET"

    def test_str(self):
        assert str(unset.UNSET) == "UNSET"

    def test_bool(self):
        assert bool(unset.UNSET) is False

    def test_singleton_behaviour(self):
        assert unset.Unset() is unset.Unset()
        assert unset.UNSET is unset.Unset()

    @_helpers.assert_raises(type_=TypeError)
    def test_cannot_subclass(self):
        class _(unset.Unset):
            pass


class TestIsUnset:
    @pytest.mark.parametrize(["obj", "is_unset"], [(unset.UNSET, True), (object(), False),])
    def test_is_unset(self, obj, is_unset):
        assert unset.is_unset(obj) is is_unset
