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
import mock

from hikari.impl import routes


class TestCompiledRoute:
    @pytest.fixture
    def compiled_route(self):
        return routes.CompiledRoute(
            major_param_hash="abc123", route=mock.Mock(method="GET"), compiled_path="/some/endpoint"
        )

    def test_method(self, compiled_route):
        assert compiled_route.method == "GET"

    def test_create_url(self, compiled_route):
        assert compiled_route.create_url("https://some.url/api") == "https://some.url/api/some/endpoint"

    def test_create_real_bucket_hash(self, compiled_route):
        assert compiled_route.create_real_bucket_hash("UNKNOWN") == "UNKNOWN;abc123"

    def test__str__(self, compiled_route):
        assert str(compiled_route) == "GET /some/endpoint"


class TestRoute:
    @pytest.fixture
    def route(self):
        return routes.Route(method="GET", path_template="/some/endpoint/{channel}")

    def test_compile(self, route):
        expected = routes.CompiledRoute(route=route, compiled_path="/some/endpoint/1234", major_param_hash="1234")
        assert route.compile(channel=1234) == expected

    def test__str__(self, route):
        assert str(route) == "/some/endpoint/{channel}"
