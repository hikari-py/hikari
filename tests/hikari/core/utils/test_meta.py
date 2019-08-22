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
from hikari.core.utils import meta


def test_library_version_is_callable_and_produces_string():
    result = meta.library_version()
    assert result.startswith("hikari.core ")


def test_python_version_is_callable_and_produces_string():
    result = meta.python_version()
    assert isinstance(result, str) and len(result.strip()) > 0


def test_can_apply_link_developer_portal_with_no_impl_uri():
    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    def foo():
        pass
