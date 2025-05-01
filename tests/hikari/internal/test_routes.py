# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import annotations

import mock
import pytest

from hikari import files
from hikari.internal import routes
from tests.hikari import hikari_test_helpers


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
        assert compiled_route.create_real_bucket_hash("UNKNOWN", "AUTH_HASH") == "UNKNOWN;AUTH_HASH;abc123"

    def test__str__(self, compiled_route):
        assert str(compiled_route) == "GET /some/endpoint"


class TestRoute:
    @pytest.mark.parametrize(
        ("route", "params"),
        [
            (routes.DELETE_CHANNEL, frozenset(("channel",))),
            (routes.PATCH_GUILD, frozenset(("guild",))),
            (routes.POST_WEBHOOK_WITH_TOKEN, frozenset(("webhook", "token"))),
            (routes.GET_WEBHOOK, frozenset(("webhook",))),
            (routes.GET_INVITE, None),
        ],
    )
    def test_major_params(self, route, params):
        assert route.major_params == params

    def test_compile_with_no_major_params(self):
        route = routes.Route(method="GET", path_template="/some/endpoint/{baguette}")
        expected = routes.CompiledRoute(route=route, compiled_path="/some/endpoint/1234", major_param_hash="-")

        assert route.compile(baguette=1234) == expected

    def test_compile_with_channel_major_params(self):
        route = routes.Route(method="GET", path_template="/channels/{channel}")
        expected = routes.CompiledRoute(route=route, compiled_path="/channels/4325", major_param_hash="4325")

        assert route.compile(channel=4325) == expected

    def test_compile_with_guild_major_params(self):
        route = routes.Route(method="GET", path_template="/guilds/{guild}")
        expected = routes.CompiledRoute(route=route, compiled_path="/guilds/5555", major_param_hash="5555")

        assert route.compile(guild=5555) == expected

    def test_compile_with_webhook_major_params(self):
        route = routes.Route(method="GET", path_template="/webhooks/{webhook}/{token}")
        expected = routes.CompiledRoute(
            route=route, compiled_path="/webhooks/123/okfdkdfkdf", major_param_hash="123:okfdkdfkdf"
        )

        assert route.compile(webhook=123, token="okfdkdfkdf") == expected

    def test__str__(self):
        assert (
            str(routes.Route(method="GET", path_template="/some/endpoint/{channel}")) == "GET /some/endpoint/{channel}"
        )


class TestCDNRoute:
    def test_zero_formats_results_in_error(self):
        with pytest.raises(ValueError, match="/foo/bar must have at least one valid format set"):
            routes.CDNRoute("/foo/bar", set())

    def test_any_formats_results_in_no_error(self):
        routes.CDNRoute("/foo/bar", {"DO", "RAY", "ME"})

    def test_formats_converted_to_frozenset(self):
        route = routes.CDNRoute("/foo/bar", {"I", "REALLY", "LIKE", "CATS"})
        assert isinstance(route.valid_formats, frozenset)
        assert route.valid_formats == {"I", "REALLY", "LIKE", "CATS"}

    def test_formats_converted_to_upper(self):
        route = routes.CDNRoute("/foo/bar", {"FOO", "BaR", "bAz", "bork"})
        assert route.valid_formats == {"FOO", "BAR", "BAZ", "BORK"}

    def test_eq_operator__considers_path_template_only(self):
        route1 = routes.CDNRoute("/foo/bar", {"HELLO", "WORLD"})
        route2 = routes.CDNRoute("/foo/bar", {"I", "SAID", "MEOW"})
        route3 = routes.CDNRoute("/foo/bar", {"I", "SAID", "MEOW"})
        route4 = routes.CDNRoute("/foo/bar/baz", {"I", "SAID", "MEOW"})
        assert route1 == route2
        assert route1 == route3
        assert route1 != route4
        assert route2 == route3
        assert route2 != route4
        assert route3 != route4

    def test_hash_operator_considers_path_template_only(self):
        route1 = routes.CDNRoute("/foo/bar", {"HELLO", "WORLD"})
        route2 = routes.CDNRoute("/foo/bar", {"I", "SAID", "MEOW"})
        route3 = routes.CDNRoute("/foo/bar", {"I", "SAID", "MEOW"})
        route4 = routes.CDNRoute("/foo/bar/baz", {"I", "SAID", "MEOW"})
        assert hash(route1) == hash(route2)
        assert hash(route1) == hash(route3)
        assert hash(route1) != hash(route4)
        assert hash(route2) == hash(route3)
        assert hash(route2) != hash(route4)
        assert hash(route3) != hash(route4)

    @pytest.mark.parametrize(
        ("input_file_format", "expected_file_format"),
        [
            ("PNG", "png"),
            ("JPG", "jpg"),
            ("JPEG", "jpeg"),
            ("WEBP", "webp"),
            ("AWEBP", "webp"),
            ("APNG", "png"),
            ("GIF", "gif"),
            ("LOTTIE", "json"),
        ],
    )
    def test_compile_uses_correct_extensions(self, input_file_format, expected_file_format):
        route = routes.CDNRoute("/foo/bar", {"PNG", "JPG", "JPEG", "WEBP", "AWEBP", "APNG", "GIF", "LOTTIE"})

        compiled_url = route.compile("http://example.com", file_format=input_file_format)

        assert f".{expected_file_format}" in compiled_url, f"compiled_url={compiled_url}"

    def test_size_parameter_when_specified(self):
        route = routes.CDNRoute("/foo/bar", {"APNG", "LOTTIE", "PNG", "JPG", "GIF"})

        compiled_url = route.compile("http://example.com", file_format="PNG", size=128)

        assert f"size=128" in compiled_url, f"compiled_url={compiled_url}"

    def test_compile_includes_lossless_on_webp(self):
        route = routes.CDNRoute("/foo/bar", {"WEBP", "AWEBP", "GIF"})

        compiled_url = route.compile("http://example.com", file_format="WEBP", hash="a_boooob", lossless=False)

        assert "lossless=false" in compiled_url, f"compiled_url={compiled_url}"

    @pytest.mark.parametrize(
        ("input_file_format", "expected_file_format"), [("JPG", "jpg"), ("jpg", "jpg"), ("PNG", "png"), ("PNG", "png")]
    )
    def test_compile_uses_lowercase_file_format_always(self, input_file_format, expected_file_format):
        route = routes.CDNRoute("/foo/bar", {"PNG", "JPG"})

        compiled_url = route.compile("http://example.com", file_format=input_file_format)

        assert compiled_url.endswith(f".{expected_file_format}"), f"compiled_url={compiled_url}"

    def test_disallowed_file_format_raises_TypeError(self):
        route = routes.CDNRoute("/foo/bar", {"PNG", "JPG"})

        with pytest.raises(TypeError, match="not a valid format for this asset"):
            route.compile("http://example.com", file_format="GIF")

    def test_allowed_file_format_does_not_raise_TypeError(self):
        route = routes.CDNRoute("/foo/bar", {"PNG", "JPG"})

        route.compile("http://example.com", file_format="PNG")

    def test_sets_animated_when_requesting_awebp(self):
        route = routes.CDNRoute("/foo/bar", {"AWEBP"})

        compiled_url = route.compile("http://example.com", file_format="AWEBP", hash="a_boooob")

        assert "animated=true" in compiled_url, f"compiled_url={compiled_url}"

    def test_sets_passthrough_when_requesting_png_on_apng_supporting_asset(self):
        route = routes.CDNRoute("/foo/bar", {"PNG", "APNG"})

        compiled_url = route.compile("http://example.com", file_format="PNG", hash="boooob")

        assert "passthrough=false" in compiled_url, f"compiled_url={compiled_url}"

    def test_passing_non_power_of_2_sizes_to_sizable_raises_ValueError(self):
        route = routes.CDNRoute("/foo/bar", {"PNG", "JPG", "GIF"})
        with pytest.raises(ValueError, match="size must be an integer power of 2 between 16 and 4096 inclusive"):
            route.compile("http://example.com", file_format="PNG", hash="boooob", size=123)

    def test_passing_invalid_magnitude_sizes_to_sizable_raises_ValueError(self):
        route = routes.CDNRoute("/foo/bar", {"PNG", "JPG", "GIF"})
        with pytest.raises(ValueError, match="size must be an integer power of 2 between 16 and 4096 inclusive"):
            route.compile("http://example.com", file_format="PNG", hash="boooob", size=int(2**13))

    def test_passing_negative_sizes_to_sizable_raises_ValueError(self):
        route = routes.CDNRoute("/foo/bar", {"PNG", "JPG", "GIF"})
        with pytest.raises(ValueError, match="size must be positive"):
            route.compile("http://example.com", file_format="PNG", hash="boooob", size=-10)

    @pytest.mark.parametrize("size", [int(2**size) for size in range(4, 13)])
    def test_passing_valid_sizes_to_sizable_does_not_raise_ValueError(self, size):
        route = routes.CDNRoute("/foo/bar", {"PNG", "JPG", "GIF"})
        route.compile("http://example.com", file_format="PNG", hash="boooob", size=size)

    def test_passing_size_adds_query_string(self):
        route = routes.CDNRoute("/foo/bar", {"PNG", "JPG", "GIF"})
        compiled_url = route.compile("http://example.com", file_format="PNG", hash="boooob", size=128)
        assert compiled_url.endswith(".png?size=128"), f"compiled_url={compiled_url}"

    def test_passing_no_size_does_not_add_query_string(self):
        route = routes.CDNRoute("/foo/bar", {"PNG", "JPG", "GIF"})
        compiled_url = route.compile("http://example.com", file_format="PNG", hash="boooob")
        assert "size=" not in compiled_url, f"compiled_url={compiled_url}"

    @pytest.mark.parametrize(
        ("base_url", "template", "file_format", "kwds", "foo", "bar", "expected_url"),
        [
            ("http://example.com", "/{foo}/bar", "GIF", {}, "baz", "bork qux", "http://example.com/baz/bar.gif"),
            ("http://example.com", "/{foo}/bar", "GIF", {}, "baz", "bork qux", "http://example.com/baz/bar.gif"),
            (
                "http://example.com",
                "/{foo}/{bar}",
                "PNG",
                {"size": 128},
                "baz",
                "bork qux",
                "http://example.com/baz/bork%20qux.png?size=128&passthrough=false",
            ),
            (
                "http://example.com",
                "/{foo}/{bar}",
                "APNG",
                {},
                "baz",
                "bork qux",
                "http://example.com/baz/bork%20qux.png",
            ),
            (
                "http://example.com",
                "/{foo}/bar",
                "JPG",
                {"size": 128},
                "baz",
                "bork qux",
                "http://example.com/baz/bar.jpg?size=128",
            ),
            (
                "http://example.com",
                "/{foo}/{bar}",
                "WEBP",
                {},
                "baz",
                "bork qux",
                "http://example.com/baz/bork%20qux.webp?lossless=true",
            ),
            (
                "http://example.com",
                "/{foo}/{bar}",
                "WEBP",
                {"lossless": False},
                "baz",
                123456,
                "http://example.com/baz/123456.webp?lossless=false",
            ),
        ],
    )
    def test_compile_generates_expected_url(self, base_url, template, file_format, kwds, foo, bar, expected_url):
        route = routes.CDNRoute(template, {"PNG", "GIF", "JPG", "WEBP", "APNG"})

        actual_url = route.compile(base_url=base_url, file_format=file_format, foo=foo, bar=bar, **kwds)

        assert actual_url == expected_url

    def test_compile_to_file_calls_compile(self):
        route = routes.CDNRoute("/hello/world", {"PNG", "JPG"})

        with mock.patch.object(routes.CDNRoute, "compile") as patched_compile:
            route.compile_to_file(
                "https://blep.com", file_format="FORMAT", size=256, lossless=True, boop="oyy lumo", nya="weeb"
            )

        patched_compile.assert_called_once_with(
            "https://blep.com", file_format="FORMAT", size=256, lossless=True, boop="oyy lumo", nya="weeb"
        )

    def test_compile_to_file_passes_compile_result_to_URL_and_returns_constructed_url(self):
        resultant_url_str = "http://blep.com/hello/world/weeb/oyy%20lumo"
        route = routes.CDNRoute("/hello/world/{nya}/{boop}", {"PNG", "JPG"})

        with mock.patch.object(routes.CDNRoute, "compile", return_value=resultant_url_str):
            result = route.compile_to_file("https://blep.com", file_format="PNG", size=64, boop="oyy lumo", nya="weeb")

        assert result == files.URL(resultant_url_str)
