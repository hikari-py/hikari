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
import math

import pytest

from hikari.orm.models import colors


@pytest.mark.model
class TestColor:
    @pytest.mark.parametrize("i", [0, 0x1, 0x11, 0x111, 0x1111, 0x11111, 0xFFFFFF])
    def test_Color_validates_constructor_and_passes_for_valid_values(self, i):
        assert colors.Color(i) is not None

    @pytest.mark.parametrize("i", [-1, 0x1000000])
    def test_Color_validates_constructor_and_fails_for_out_of_range_values(self, i):
        try:
            colors.Color(i)
            assert False, "Failed to fail validation for bad values"
        except ValueError:
            pass

    @pytest.mark.parametrize("i", [0, 0x1, 0x11, 0x111, 0x1111, 0x11111, 0xFFFFFF])
    def test_Color_from_int_passes_for_valid_values(self, i):
        assert colors.Color.from_int(i) is not None

    @pytest.mark.parametrize("i", [-1, 0x1000000])
    def test_Color_from_int_fails_for_out_of_range_values(self, i):
        try:
            colors.Color.from_int(i)
            assert False, "Failed to fail validation for bad values"
        except ValueError:
            pass

    def test_equality_with_int(self):
        assert colors.Color(0xFA) == 0xFA

    def test_cast_to_int(self):
        assert int(colors.Color(0xFA)) == 0xFA

    @pytest.mark.parametrize(
        ["i", "string"], [(0x1A2B3C, "Color(r=0x1a, g=0x2b, b=0x3c)"), (0x1A2, "Color(r=0x0, g=0x1, b=0xa2)")]
    )
    def test_Color_repr_operator(self, i, string):
        assert repr(colors.Color(i)) == string

    @pytest.mark.parametrize(["i", "string"], [(0x1A2B3C, "#1A2B3C"), (0x1A2, "#0001A2")])
    def test_Color_str_operator(self, i, string):
        assert str(colors.Color(i)) == string

    @pytest.mark.parametrize(["i", "string"], [(0x1A2B3C, "#1A2B3C"), (0x1A2, "#0001A2")])
    def test_Color_hex_code(self, i, string):
        assert colors.Color(i).hex_code == string

    @pytest.mark.parametrize(["i", "string"], [(0x1A2B3C, "1A2B3C"), (0x1A2, "0001A2")])
    def test_Color_raw_hex_code(self, i, string):
        assert colors.Color(i).raw_hex_code == string

    @pytest.mark.parametrize(
        ["i", "expected_outcome"], [(0x1A2B3C, False), (0x1AAA2B, False), (0x0, True), (0x11AA33, True)]
    )
    def test_Color_is_web_safe(self, i, expected_outcome):
        assert colors.Color(i).is_web_safe is expected_outcome

    @pytest.mark.parametrize(["r", "g", "b", "expected"], [(0x9, 0x18, 0x27, 0x91827), (0x55, 0x1A, 0xFF, 0x551AFF)])
    def test_Color_from_rgb(self, r, g, b, expected):
        assert colors.Color.from_rgb(r, g, b) == expected

    @pytest.mark.parametrize(
        ["r", "g", "b", "expected"],
        [(0x09 / 0xFF, 0x18 / 0xFF, 0x27 / 0xFF, 0x91827), (0x55 / 0xFF, 0x1A / 0xFF, 0xFF / 0xFF, 0x551AFF)],
    )
    def test_Color_from_rgb_float(self, r, g, b, expected):
        assert math.isclose(colors.Color.from_rgb_float(r, g, b), expected, abs_tol=1)

    @pytest.mark.parametrize(["input", "r", "g", "b"], [(0x91827, 0x9, 0x18, 0x27), (0x551AFF, 0x55, 0x1A, 0xFF)])
    def test_Color_rgb(self, input, r, g, b):
        assert colors.Color(input).rgb == (r, g, b)

    @pytest.mark.parametrize(
        ["input", "r", "g", "b"],
        [(0x91827, 0x09 / 0xFF, 0x18 / 0xFF, 0x27 / 0xFF), (0x551AFF, 0x55 / 0xFF, 0x1A / 0xFF, 0xFF / 0xFF)],
    )
    def test_Color_rgb_float(self, input, r, g, b):
        assert colors.Color(input).rgb_float == (r, g, b)

    @pytest.mark.parametrize("prefix", ["0x", "0X", "#", ""])
    @pytest.mark.parametrize(
        ["expected", "string"], [(0x1A2B3C, "1A2B3C"), (0x1A2, "0001A2"), (0xAABBCC, "ABC"), (0x00AA00, "0A0")]
    )
    def test_Color_from_hex_code(self, prefix, string, expected):
        actual_string = prefix + string
        assert colors.Color.from_hex_code(actual_string) == expected

    def test_Color_from_hex_code_ValueError_when_not_hex(self):
        try:
            colors.Color.from_hex_code("0xlmfao")
            assert False, "No failure"
        except ValueError:
            pass

    def test_Color_from_hex_code_ValueError_when_not_6_or_3_in_size(self):
        try:
            colors.Color.from_hex_code("0x1111")
            assert False, "No failure"
        except ValueError:
            pass

    def test_Color_from_bytes(self):
        assert colors.Color(0xFFAAFF) == colors.Color.from_bytes(b"\xff\xaa\xff\x00\x00\x00\x00\x00\x00\x00", "little")

    def test_Color_to_bytes(self):
        c = colors.Color(0xFFAAFF)
        b = c.to_bytes(10, "little")
        assert b == b"\xff\xaa\xff\x00\x00\x00\x00\x00\x00\x00"

    @pytest.mark.parametrize(
        ["input", "expected_result"],
        [
            (0xFF051A, colors.Color(0xFF051A)),
            (16712986, colors.Color(0xFF051A)),
            ((255, 5, 26), colors.Color(0xFF051A)),
            ([0xFF, 0x5, 0x1A], colors.Color(0xFF051A)),
            ("#1a2b3c", colors.Color(0x1A2B3C)),
            ("#123", colors.Color(0x112233)),
            ("0x1a2b3c", colors.Color(0x1A2B3C)),
            ("0x123", colors.Color(0x112233)),
            ("0X1a2b3c", colors.Color(0x1A2B3C)),
            ("0X123", colors.Color(0x112233)),
            ("1a2b3c", colors.Color(0x1A2B3C)),
            ("123", colors.Color(0x112233)),
            ((1.0, 0.0196078431372549, 0.10196078431372549), colors.Color(0xFF051A)),
            ([1.0, 0.0196078431372549, 0.10196078431372549], colors.Color(0xFF051A)),
        ],
    )
    def test_Color__cls_getattr___happy_path(self, input, expected_result):
        assert colors.Color[input] == expected_result, f"{input}"

    @pytest.mark.parametrize(
        "input",
        [
            "blah",
            "0xfff1",
            lambda: 22,
            NotImplementedError,
            NotImplemented,
            (1, 1, 1, 1),
            (1, "a", 1),
            (1, 1.1, 1),
            (),
            {},
            [],
            {1, 1, 1},
            set(),
            b"1ff1ff",
        ],
    )
    def test_Color__cls_getattr___sad_path(self, input):
        try:
            result = colors.Color[input]
            assert False, f"Expected ValueError, got {result} returned safely instead"
        except ValueError:
            pass
