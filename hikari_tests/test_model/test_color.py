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

from hikari.model import color


@pytest.mark.model
class TestColor:
    @pytest.mark.parametrize("i", [0, 0x1, 0x11, 0x111, 0x1111, 0x11111, 0xFFFFFF])
    def test_Color_validates_constructor_and_passes_for_valid_values(self, i):
        assert color.Color(i) is not None

    @pytest.mark.parametrize("i", [-1, 0x1000000])
    def test_Color_validates_constructor_and_fails_for_out_of_range_values(self, i):
        try:
            color.Color(i)
            assert False, "Failed to fail validation for bad values"
        except ValueError:
            pass

    @pytest.mark.parametrize("i", [0, 0x1, 0x11, 0x111, 0x1111, 0x11111, 0xFFFFFF])
    def test_Color_from_int_passes_for_valid_values(self, i):
        assert color.Color.from_int(i) is not None

    @pytest.mark.parametrize("i", [-1, 0x1000000])
    def test_Color_from_int_fails_for_out_of_range_values(self, i):
        try:
            color.Color.from_int(i)
            assert False, "Failed to fail validation for bad values"
        except ValueError:
            pass

    def test_equality_with_int(self):
        assert color.Color(0xFA) == 0xFA

    def test_cast_to_int(self):
        assert int(color.Color(0xFA)) == 0xFA

    @pytest.mark.parametrize(
        ["i", "string"], [(0x1A2B3C, "Color(r=0x1a, g=0x2b, b=0x3c)"), (0x1A2, "Color(r=0x0, g=0x1, b=0xa2)")]
    )
    def test_Color_repr_operator(self, i, string):
        assert repr(color.Color(i)) == string

    @pytest.mark.parametrize(["i", "string"], [(0x1A2B3C, "#1A2B3C"), (0x1A2, "#0001A2")])
    def test_Color_str_operator(self, i, string):
        assert str(color.Color(i)) == string

    @pytest.mark.parametrize(["i", "string"], [(0x1A2B3C, "#1A2B3C"), (0x1A2, "#0001A2")])
    def test_Color_hex_code(self, i, string):
        assert color.Color(i).hex_code == string

    @pytest.mark.parametrize(["i", "string"], [(0x1A2B3C, "1A2B3C"), (0x1A2, "0001A2")])
    def test_Color_raw_hex_code(self, i, string):
        assert color.Color(i).raw_hex_code == string

    @pytest.mark.parametrize(
        ["i", "expected_outcome"], [(0x1A2B3C, False), (0x1AAA2B, False), (0x0, True), (0x11AA33, True)]
    )
    def test_Color_is_web_safe(self, i, expected_outcome):
        assert color.Color(i).is_web_safe is expected_outcome

    @pytest.mark.parametrize(["r", "g", "b", "expected"], [(0x9, 0x18, 0x27, 0x91827), (0x55, 0x1A, 0xFF, 0x551AFF)])
    def test_Color_from_rgb(self, r, g, b, expected):
        assert color.Color.from_rgb(r, g, b) == expected

    @pytest.mark.parametrize(
        ["r", "g", "b", "expected"],
        [(0x09 / 0xFF, 0x18 / 0xFF, 0x27 / 0xFF, 0x91827), (0x55 / 0xFF, 0x1A / 0xFF, 0xFF / 0xFF, 0x551AFF)],
    )
    def test_Color_from_rgb_float(self, r, g, b, expected):
        assert math.isclose(color.Color.from_rgb_float(r, g, b), expected, abs_tol=1)

    @pytest.mark.parametrize(["input", "r", "g", "b"], [(0x91827, 0x9, 0x18, 0x27), (0x551AFF, 0x55, 0x1A, 0xFF)])
    def test_Color_rgb(self, input, r, g, b):
        assert color.Color(input).rgb == (r, g, b)

    @pytest.mark.parametrize(
        ["input", "r", "g", "b"],
        [(0x91827, 0x09 / 0xFF, 0x18 / 0xFF, 0x27 / 0xFF), (0x551AFF, 0x55 / 0xFF, 0x1A / 0xFF, 0xFF / 0xFF)],
    )
    def test_Color_rgb_float(self, input, r, g, b):
        assert color.Color(input).rgb_float == (r, g, b)

    @pytest.mark.parametrize("prefix", ["0x", "0X", "#", ""])
    @pytest.mark.parametrize(
        ["expected", "string"], [(0x1A2B3C, "1A2B3C"), (0x1A2, "0001A2"), (0xAABBCC, "ABC"), (0x00AA00, "0A0")]
    )
    def test_Color_from_hex_code(self, prefix, string, expected):
        actual_string = prefix + string
        assert color.Color.from_hex_code(actual_string) == expected

    def test_Color_from_hex_code_ValueError_when_not_hex(self):
        try:
            color.Color.from_hex_code("0xlmfao")
            assert False, "No failure"
        except ValueError:
            pass

    def test_Color_from_hex_code_ValueError_when_not_6_or_3_in_size(self):
        try:
            color.Color.from_hex_code("0x1111")
            assert False, "No failure"
        except ValueError:
            pass
