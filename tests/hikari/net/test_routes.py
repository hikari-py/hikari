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
import mock
import pytest

from hikari.net import routes


class TestCompiledRoute:
    @pytest.fixture
    def template_route(self):
        return routes.Route("get", "/somewhere/{channel_id}")

    @pytest.fixture
    def compiled_route(self, template_route):
        return routes.CompiledRoute(template_route, "/somewhere/123", "123")

    def test_create_url(self, compiled_route):
        assert compiled_route.create_url("https://something.com/api/v6") == "https://something.com/api/v6/somewhere/123"

    def test_create_real_bucket_hash(self, compiled_route):
        assert compiled_route.create_real_bucket_hash("SOMETHING") == "SOMETHING;123"

    def test__repr__(self, compiled_route):
        expected_repr = "CompiledRoute(method='get', compiled_path='/somewhere/123', major_params_hash='123')"

        assert compiled_route.__repr__() == expected_repr

    def test__str__(self, compiled_route):
        assert str(compiled_route) == "get /somewhere/123"

    def test___eq___positive(self):
        template = mock.MagicMock()
        assert routes.CompiledRoute(template, "/foo/bar", "1a2b3c") == routes.CompiledRoute(
            template, "/foo/bar", "1a2b3c"
        )

    def test___eq___negative_path(self):
        template = mock.MagicMock()
        assert routes.CompiledRoute(template, "/foo/baz", "1a2b3c") != routes.CompiledRoute(
            template, "/foo/bar", "1a2b3c"
        )

    def test___eq___negative_hash(self):
        template = mock.MagicMock()
        assert routes.CompiledRoute(template, "/foo/bar", "1a2b3d") != routes.CompiledRoute(
            template, "/foo/bar", "1a2b3c"
        )


class TestRouteTemplate:
    @pytest.fixture
    def template_route(self):
        return routes.Route("post", "/somewhere/{channel_id}")

    def test__init___without_major_params_uses_default_major_params(self, template_route):
        assert template_route.major_param == "channel_id"

    def test_compile(self, template_route):
        expected_compiled_route = routes.CompiledRoute(template_route, "/somewhere/123", "123")

        actual_compiled_route = template_route.compile(channel_id=123)
        assert actual_compiled_route == expected_compiled_route

    def test__repr__(self, template_route):
        expected_repr = "Route(path_template='/somewhere/{channel_id}', major_param='channel_id')"

        assert template_route.__repr__() == expected_repr

    def test__str__(self, template_route):
        assert str(template_route) == "/somewhere/{channel_id}"
