#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
from hikari.core.utils import unspecified


def test_unspecified_is_singleton():
    assert unspecified.Unspecified() is unspecified.Unspecified() is unspecified.UNSPECIFIED


def test_unspecified_str():
    assert str(unspecified.UNSPECIFIED) == "unspecified"


def test_unspecified_repr():
    assert repr(unspecified.UNSPECIFIED) == "unspecified"


def test_unspecified_bool():
    assert bool(unspecified.UNSPECIFIED) is False
