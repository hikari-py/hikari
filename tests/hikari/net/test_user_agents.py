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
from hikari.net import user_agents


def test_library_version_is_callable_and_produces_string():
    assert isinstance(user_agents.UserAgent().library_version, str)


def test_platform_version_is_callable_and_produces_string():
    assert isinstance(user_agents.UserAgent().platform_version, str)


def test_system_type_produces_string():
    assert isinstance(user_agents.UserAgent().system_type, str)


def test_websocket_triplet_produces_trio():
    assert user_agents.UserAgent().websocket_triplet == {
        "$os": user_agents.UserAgent().system_type,
        "$browser": user_agents.UserAgent().library_version,
        "$device": user_agents.UserAgent().platform_version,
    }
