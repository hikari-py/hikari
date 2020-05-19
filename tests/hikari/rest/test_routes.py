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

from hikari.rest import routes


class TestCompiledRoute:
    @pytest.fixture
    def template_route(self):
        return routes.Route("get", "/somewhere/{channel}")

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
        t = mock.MagicMock()
        assert routes.CompiledRoute(t, "/foo/bar", "1a2b3d") != routes.CompiledRoute(t, "/foo/bar", "1a2b3c")

    def test___hash___positive(self):
        t = mock.MagicMock()
        assert hash(routes.CompiledRoute(t, "/foo/bar", "1a2b3")) == hash(routes.CompiledRoute(t, "/foo/bar", "1a2b3"))

    def test___hash___negative(self):
        t = mock.MagicMock()
        assert hash(routes.CompiledRoute(t, "/foo/bar", "1a2b3c")) != hash(routes.CompiledRoute(t, "/foo/bar", "1a2b3"))


class TestRoute:
    @pytest.fixture
    def route(self):
        return routes.Route("post", "/somewhere/{channel}")

    def test__init___without_major_params_uses_default_major_params(self, route):
        assert route.major_param == "channel"

    def test_compile(self, route):
        expected_compiled_route = routes.CompiledRoute(route, "/somewhere/123", "123")

        actual_compiled_route = route.compile(channel_id=123)
        assert actual_compiled_route == expected_compiled_route

    def test__repr__(self, route):
        expected_repr = "Route(path_template='/somewhere/{channel}', major_param='channel')"

        assert route.__repr__() == expected_repr

    def test__str__(self, route):
        assert str(route) == "/somewhere/{channel}"

    def test___eq__(self):
        assert routes.Route("foo", "bar") == routes.Route("foo", "bar")

    def test___ne___method(self):
        assert routes.Route("foobar", "bar") != routes.Route("foo", "bar")

    def test___ne___path(self):
        assert routes.Route("foo", "barbaz") != routes.Route("foo", "bar")

    def test___hash__when_equal(self):
        assert hash(routes.Route("foo", "bar")) == hash(routes.Route("foo", "bar"))

    def test___hash___when_path_differs(self):
        assert hash(routes.Route("foo", "barbaz")) != hash(routes.Route("foo", "bar"))

    def test___hash___when_method_differs(self):
        assert hash(routes.Route("foobar", "baz")) != hash(routes.Route("foo", "baz"))
