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

from hikari.internal_utilities import assertions
from tests.hikari import _helpers


@_helpers.assert_does_not_raise(type_=ValueError)
def test_assert_that_when_True():
    assertions.assert_that(True)


@_helpers.assert_raises(type_=ValueError)
def test_assert_that_when_False():
    assertions.assert_that(False, "bang")


@_helpers.assert_raises(type_=ValueError)
def test_assert_not_none_when_none():
    assertions.assert_not_none(None)


@pytest.mark.parametrize("arg", [9, "foo", False, 0, 0.0, "", [], {}, set(), ..., NotImplemented])
@_helpers.assert_does_not_raise(type_=ValueError)
def test_assert_not_none_when_not_none(arg):
    assertions.assert_not_none(arg)
