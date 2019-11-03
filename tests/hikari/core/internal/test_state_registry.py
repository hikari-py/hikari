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
from hikari.core.internal import state_registry


def test_MissingDependencyError_accesses_failed_method_correctly():
    payload = {"junk": "foo bar baz"}

    try:
        raise state_registry.MissingDependencyError(payload, "deez nuts")
    except state_registry.MissingDependencyError as ex:
        assert ex.payload is payload
        assert ex.missing == "deez nuts"
        assert ex.method == test_MissingDependencyError_accesses_failed_method_correctly.__name__
