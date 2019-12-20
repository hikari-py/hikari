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
import hikari.net.user_agent


def test_library_version_is_callable_and_produces_string():
    result = hikari.net.user_agent.library_version()
    assert result.startswith("hikari ")


def test_python_version_is_callable_and_produces_string():
    result = hikari.net.user_agent.python_version()
    assert isinstance(result, str) and len(result.strip()) > 0


def test_system_type_produces_string():
    result = hikari.net.user_agent.system_type()
    assert isinstance(result, str) and len(result.strip()) > 0
