# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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
import math

import pytest

from hikari import colors


class TestColor:
    @pytest.mark.parametrize("i", [0, 0x1, 0x11, 0x111, 0x1111, 0x11111, 0xFFFFFF])
    def test_Color_validates_constructor_and_passes_for_valid_values(self, i):
        assert colors.Color(i) is not None

    @pytest.mark.parametrize("i", [-1, 0x1000000])
    def test_Color_validates_constructor_and_fails_for_out_of_range_values(self, i):
        with pytest.raises(ValueError):
            colors.Color(i)

    @pytest.mark.parametrize("i", [0, 0x1, 0x11, 0x111, 0x1111, 0x11111, 0xFFFFFF])
    def test_Color_from_int_passes_for_valid_values(self, i):
        assert colors.Color.from_int(i) is not None

    @pytest.mark.parametrize("i", [-1, 0x1000000])
    def test_Color_from_int_fails_for_out_of_range_values(self, i):
        with pytest.raises(ValueError):
            colors.Color.from_int(i)

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

    def test_color_from_rgb_raises_value_error_on_invalid_red(self):
        with pytest.raises(ValueError):
            colors.Color.from_rgb(0x999, 32, 32)

    def test_color_from_rgb_raises_value_error_on_invalid_green(self):
        with pytest.raises(ValueError):
            colors.Color.from_rgb(32, 0x999, 32)

    def test_color_from_rgb_raises_value_error_on_invalid_blue(self):
        with pytest.raises(ValueError):
            colors.Color.from_rgb(32, 32, 0x999)

    @pytest.mark.parametrize(
        ["r", "g", "b", "expected"],
        [(0x09 / 0xFF, 0x18 / 0xFF, 0x27 / 0xFF, 0x91827), (0x55 / 0xFF, 0x1A / 0xFF, 0xFF / 0xFF, 0x551AFF)],
    )
    def test_Color_from_rgb_float(self, r, g, b, expected):
        assert math.isclose(colors.Color.from_rgb_float(r, g, b), expected, abs_tol=1)

    def test_color_from_rgb_float_raises_value_error_on_invalid_red(self):
        with pytest.raises(ValueError):
            colors.Color.from_rgb_float(1.5, 0.5, 0.5)

    def test_color_from_rgb_float_raises_value_error_on_invalid_green(self):
        with pytest.raises(ValueError):
            colors.Color.from_rgb_float(0.5, 1.5, 0.5)

    def test_color_from_rgb_float_raises_value_error_on_invalid_blue(self):
        with pytest.raises(ValueError):
            colors.Color.from_rgb_float(0.5, 0.5, 1.5)

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
        with pytest.raises(ValueError):
            colors.Color.from_hex_code("0xlmfao")

    def test_Color_from_hex_code_ValueError_when_not_6_or_3_in_size(self):
        with pytest.raises(ValueError):
            colors.Color.from_hex_code("0x1111")

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
            ((1, 0.5, 0), colors.Color(0xFF7F00)),
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
    def test_Color_of_happy_path(self, input, expected_result):
        result = colors.Color.of(input)
        assert result == expected_result, f"{input}"

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
    def test_Color_of_sad_path(self, input):
        with pytest.raises(ValueError):
            colors.Color.of(input)

    def test_Color_of_with_multiple_args(self):
        result = colors.Color.of((0xFF, 0x5, 0x1A))
        assert result == colors.Color(0xFF051A)

    def test_Color___repr__(self):
        assert repr(colors.Color.of("#1a2b3c")) == "Color(r=0x1a, g=0x2b, b=0x3c)"

    def test_Color_str_operator(self):
        color = colors.Color(0xFFFFFF)
        assert str(color) == "#FFFFFF"
