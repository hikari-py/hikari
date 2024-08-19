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

import math

import pytest

from hikari import colors

tuple_str_happy_test_data = [
    # No brackets, no commas
    ("1 2           3", colors.Color(0x010203)),
    ("0 0 0", colors.Color(0x0)),
    ("0.0 0.0 0.0", colors.Color(0x0)),
    ("0.5 0.6 0.7", colors.Color(0x7F99B2)),
    ("127 153 178", colors.Color(0x7F99B2)),
    ("255 255 255", colors.Color(0xFFFFFF)),
    ("1.0 1.0 1.0", colors.Color(0xFFFFFF)),
    # Parenthesis, no commas
    ("(1 2      3)", colors.Color(0x010203)),
    ("(0 0 0)", colors.Color(0x0)),
    ("(0.0 0.0 0.0)", colors.Color(0x0)),
    ("(0.5 0.6 0.7)", colors.Color(0x7F99B2)),
    ("(127 153 178)", colors.Color(0x7F99B2)),
    ("(255 255 255)", colors.Color(0xFFFFFF)),
    ("(1.0 1.0 1.0)", colors.Color(0xFFFFFF)),
    # Square brackets, no commas
    ("[1 2 3]", colors.Color(0x010203)),
    ("[0 0 0]", colors.Color(0x0)),
    ("[0.0 0.0 0.0]", colors.Color(0x0)),
    ("[0.5 0.6 0.7]", colors.Color(0x7F99B2)),
    ("[127 153 178]", colors.Color(0x7F99B2)),
    ("[255 255 255]", colors.Color(0xFFFFFF)),
    ("[1.0 1.0 1.0]", colors.Color(0xFFFFFF)),
    # Braces, no commas
    ("{1 2 3}", colors.Color(0x010203)),
    ("{0 0 0}", colors.Color(0x0)),
    ("{0.0 0.0 0.0}", colors.Color(0x0)),
    ("{0.5 0.6 0.7}", colors.Color(0x7F99B2)),
    ("{127 153 178}", colors.Color(0x7F99B2)),
    ("{255 255 255}", colors.Color(0xFFFFFF)),
    ("{1.0 1.0 1.0}", colors.Color(0xFFFFFF)),
    # Angle brackets, no commas
    ("< 1 2   3>", colors.Color(0x010203)),
    ("<0 0  0>", colors.Color(0x0)),
    ("<0.0 0.0 0.0>", colors.Color(0x0)),
    ("<0.5\n0.6\n\t0.7>", colors.Color(0x7F99B2)),
    ("<127 153 178>", colors.Color(0x7F99B2)),
    ("<255 255 255>", colors.Color(0xFFFFFF)),
    ("<1.0 1.0 1.0>", colors.Color(0xFFFFFF)),
    # No brackets, commas
    ("1, 2  , 3", colors.Color(0x010203)),
    ("0, 0, 0", colors.Color(0x0)),
    ("0.0, 0.0, 0.0", colors.Color(0x0)),
    ("0.5, 0.6, 0.7", colors.Color(0x7F99B2)),
    ("127, 153, 178", colors.Color(0x7F99B2)),
    ("255, 255, 255", colors.Color(0xFFFFFF)),
    ("1.0, 1.0, 1.0", colors.Color(0xFFFFFF)),
    # Parenthesis, commas
    ("(1, 2  , 3)", colors.Color(0x010203)),
    ("(0,0,0)", colors.Color(0x0)),
    ("(0.0, 0.0, 0.0)", colors.Color(0x0)),
    ("(0.5, 0.6, 0.7)", colors.Color(0x7F99B2)),
    ("(127, 153, 178)", colors.Color(0x7F99B2)),
    ("(255, 255, 255)", colors.Color(0xFFFFFF)),
    ("(1.0, 1.0, 1.0)", colors.Color(0xFFFFFF)),
    # Square brackets, commas
    ("[1, 2, 3]", colors.Color(0x010203)),
    ("[0,0,0]", colors.Color(0x0)),
    ("[0., .0, .0]", colors.Color(0x0)),
    ("[.5, .6, .7]", colors.Color(0x7F99B2)),
    ("[127, 153, 178]", colors.Color(0x7F99B2)),
    ("[255, 255, 255]", colors.Color(0xFFFFFF)),
    ("[1.0, 1.0, 1.0]", colors.Color(0xFFFFFF)),
    # Braces, commas
    ("{1, 2, 3}", colors.Color(0x010203)),
    ("{0, 0, 0}", colors.Color(0x0)),
    ("{0.0, 0.0, 0.0}", colors.Color(0x0)),
    ("{0.5, 0.6, 0.7}", colors.Color(0x7F99B2)),
    ("{127, 153, 178}", colors.Color(0x7F99B2)),
    ("{255, 255, 255}", colors.Color(0xFFFFFF)),
    ("{1.0, 1.0, 1.0}", colors.Color(0xFFFFFF)),
    # Angle brackets, commas
    ("<1, 2, 3>", colors.Color(0x010203)),
    ("<0, 0, 0>", colors.Color(0x0)),
    ("<0.0, 0.0, 0.0>", colors.Color(0x0)),
    ("<0.5, 0.6, 0.7>", colors.Color(0x7F99B2)),
    ("<127, 153, 178>", colors.Color(0x7F99B2)),
    ("<255, 255, 255>", colors.Color(0xFFFFFF)),
    ("<1.0, 1.0, 1.0>", colors.Color(0xFFFFFF)),
]

tuple_str_sad_test_data = [
    # Empty inputs
    ("{}", r"Expected three comma/space separated values"),
    ("[]", r"Expected three comma/space separated values"),
    ("()", r"Expected three comma/space separated values"),
    ("<>", r"Expected three comma/space separated values"),
    # Letters in inputs
    ("{a, 1, 2}", r"Expected digits only for red channel"),
    ("[1, b, 2]", r"Expected digits only for green channel"),
    ("(1, 2, c)", r"Expected digits only for blue channel"),
    ("<d, d, d>", r"Expected digits only for red channel"),
    ("e, e, e", r"Expected digits only for red channel"),
    ("{a 1 2}", r"Expected digits only for red channel"),
    ("[1 b 2]", r"Expected digits only for green channel"),
    ("(1 2 c)", r"Expected digits only for blue channel"),
    ("<d d d>", r"Expected digits only for red channel"),
    ("e e e", r"Expected digits only for red channel"),
    # Mixing ints and floats
    ("1.0, 1.0, 3", r'Expected exactly 1 decimal point "\." in blue channel'),
    ("1.0 2 3", r'Expected exactly 1 decimal point "\." in green channel'),
    # Weird decimals out of range
    ("0.1 2. 0.5", r"Expected green channel to be a decimal in the inclusive range of 0.0 and 1.0"),
    # Too many int digits
    ("0 25600 200", r"Expected 1 to 3 digits for green channel, got 5"),
    # Ints out of range
    ("0 256 200", r"Expected green channel to be in the inclusive range of 0 and 255, got '256'"),
    # Floats out of range
    ("0.0 1.1 0.5", r"Expected green channel to be in the inclusive range of 0.0 and 1.0"),
    # Too few ints
    ("10 20", r"Expected three comma/space separated values"),
    # Too many ints
    ("10 20 30 40", r"Expected three comma/space separated values"),
    # Too few floats
    ("0.5", r"Expected three comma/space separated values"),
    ("0.5 0.5", r"Expected three comma/space separated values"),
    # Too many floats
    ("0.5 0.5 0.5 0.5", r"Expected three comma/space separated values"),
    # Too many commas
    ("100,,100, 100", r"Expected three comma/space separated values"),
    # Mixing commas and spaces without commas
    ("100,100 100", r"Expected three comma/space separated values"),
]


class TestColor:
    @pytest.mark.parametrize("i", [0, 0x1, 0x11, 0x111, 0x1111, 0x11111, 0xFFFFFF])
    def test_Color_validates_constructor_and_passes_for_valid_values(self, i):
        assert colors.Color(i) is not None

    @pytest.mark.parametrize("i", [-1, 0x1000000])
    def test_Color_validates_constructor_and_fails_for_out_of_range_values(self, i):
        with pytest.raises(ValueError, match=r"raw_rgb must be in the exclusive range of 0 and 16777215"):
            colors.Color(i)

    @pytest.mark.parametrize("i", [0, 0x1, 0x11, 0x111, 0x1111, 0x11111, 0xFFFFFF])
    def test_Color_from_int_passes_for_valid_values(self, i):
        assert colors.Color.from_int(i) is not None

    @pytest.mark.parametrize("i", [-1, 0x1000000])
    def test_Color_from_int_fails_for_out_of_range_values(self, i):
        with pytest.raises(ValueError, match=r"raw_rgb must be in the exclusive range of 0 and 16777215"):
            colors.Color.from_int(i)

    def test_equality_with_int(self):
        assert colors.Color(0xFA) == 0xFA

    def test_cast_to_int(self):
        assert int(colors.Color(0xFA)) == 0xFA

    @pytest.mark.parametrize(
        ("i", "string"), [(0x1A2B3C, "Color(r=0x1a, g=0x2b, b=0x3c)"), (0x1A2, "Color(r=0x0, g=0x1, b=0xa2)")]
    )
    def test_Color_repr_operator(self, i, string):
        assert repr(colors.Color(i)) == string

    @pytest.mark.parametrize(("i", "string"), [(0x1A2B3C, "#1A2B3C"), (0x1A2, "#0001A2")])
    def test_Color_str_operator(self, i, string):
        assert str(colors.Color(i)) == string

    @pytest.mark.parametrize(("i", "string"), [(0x1A2B3C, "#1A2B3C"), (0x1A2, "#0001A2")])
    def test_Color_hex_code(self, i, string):
        assert colors.Color(i).hex_code == string

    @pytest.mark.parametrize(("i", "string"), [(0x1A2B3C, "1A2B3C"), (0x1A2, "0001A2")])
    def test_Color_raw_hex_code(self, i, string):
        assert colors.Color(i).raw_hex_code == string

    @pytest.mark.parametrize(
        ("i", "expected_outcome"), [(0x1A2B3C, False), (0x1AAA2B, False), (0x0, True), (0x11AA33, True)]
    )
    def test_Color_is_web_safe(self, i, expected_outcome):
        assert colors.Color(i).is_web_safe is expected_outcome

    @pytest.mark.parametrize(("r", "g", "b", "expected"), [(0x9, 0x18, 0x27, 0x91827), (0x55, 0x1A, 0xFF, 0x551AFF)])
    def test_Color_from_rgb(self, r, g, b, expected):
        assert colors.Color.from_rgb(r, g, b) == expected

    def test_color_from_rgb_raises_value_error_on_invalid_red(self):
        with pytest.raises(ValueError, match=r"Expected red channel to be in the inclusive range of 0 and 255"):
            colors.Color.from_rgb(0x999, 32, 32)

    def test_color_from_rgb_raises_value_error_on_invalid_green(self):
        with pytest.raises(ValueError, match=r"Expected green channel to be in the inclusive range of 0 and 255"):
            colors.Color.from_rgb(32, 0x999, 32)

    def test_color_from_rgb_raises_value_error_on_invalid_blue(self):
        with pytest.raises(ValueError, match=r"Expected blue channel to be in the inclusive range of 0 and 255"):
            colors.Color.from_rgb(32, 32, 0x999)

    @pytest.mark.parametrize(
        ("r", "g", "b", "expected"),
        [(0x09 / 0xFF, 0x18 / 0xFF, 0x27 / 0xFF, 0x91827), (0x55 / 0xFF, 0x1A / 0xFF, 0xFF / 0xFF, 0x551AFF)],
    )
    def test_Color_from_rgb_float(self, r, g, b, expected):
        assert math.isclose(colors.Color.from_rgb_float(r, g, b), expected, abs_tol=1)

    def test_color_from_rgb_float_raises_value_error_on_invalid_red(self):
        with pytest.raises(ValueError, match=r"Expected red channel to be in the inclusive range of 0.0 and 1.0"):
            colors.Color.from_rgb_float(1.5, 0.5, 0.5)

    def test_color_from_rgb_float_raises_value_error_on_invalid_green(self):
        with pytest.raises(ValueError, match=r"Expected green channel to be in the inclusive range of 0.0 and 1.0"):
            colors.Color.from_rgb_float(0.5, 1.5, 0.5)

    def test_color_from_rgb_float_raises_value_error_on_invalid_blue(self):
        with pytest.raises(ValueError, match=r"Expected blue channel to be in the inclusive range of 0.0 and 1.0"):
            colors.Color.from_rgb_float(0.5, 0.5, 1.5)

    @pytest.mark.parametrize(("input", "r", "g", "b"), [(0x91827, 0x9, 0x18, 0x27), (0x551AFF, 0x55, 0x1A, 0xFF)])
    def test_Color_rgb(self, input, r, g, b):
        assert colors.Color(input).rgb == (r, g, b)

    @pytest.mark.parametrize(
        ("input", "r", "g", "b"),
        [(0x91827, 0x09 / 0xFF, 0x18 / 0xFF, 0x27 / 0xFF), (0x551AFF, 0x55 / 0xFF, 0x1A / 0xFF, 0xFF / 0xFF)],
    )
    def test_Color_rgb_float(self, input, r, g, b):
        assert colors.Color(input).rgb_float == (r, g, b)

    @pytest.mark.parametrize("prefix", ["0x", "0X", "#", ""])
    @pytest.mark.parametrize(
        ("expected", "string"), [(0x1A2B3C, "1A2B3C"), (0x1A2, "0001A2"), (0xAABBCC, "ABC"), (0x00AA00, "0A0")]
    )
    def test_Color_from_hex_code(self, prefix, string, expected):
        actual_string = prefix + string
        assert colors.Color.from_hex_code(actual_string) == expected

    def test_Color_from_hex_code_ValueError_when_not_hex(self):
        with pytest.raises(ValueError, match=r"Color code must be hexadecimal"):
            colors.Color.from_hex_code("0xlmfao")

    def test_Color_from_hex_code_ValueError_when_not_6_or_3_in_size(self):
        with pytest.raises(ValueError, match=r"Color code is invalid length. Must be 3 or 6 digits"):
            colors.Color.from_hex_code("0x1111")

    def test_Color_from_bytes(self):
        assert colors.Color(0xFFAAFF) == colors.Color.from_bytes(b"\xff\xaa\xff\x00\x00\x00\x00\x00\x00\x00", "little")

    def test_Color_to_bytes(self):
        c = colors.Color(0xFFAAFF)
        b = c.to_bytes(10, "little")
        assert b == b"\xff\xaa\xff\x00\x00\x00\x00\x00\x00\x00"

    @pytest.mark.parametrize(
        ("input", "expected_result"),
        [
            (colors.Color(0xFF051A), colors.Color(0xFF051A)),
            (0xFF051A, colors.Color(0xFF051A)),
            ((1.0, 0.5, 0.0), colors.Color(0xFF7F00)),
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
            *tuple_str_happy_test_data,
        ],
    )
    def test_Color_of_happy_path(self, input, expected_result):
        result = colors.Color.of(input)
        assert result == expected_result, f"{input}"

    @pytest.mark.parametrize(
        ("input_string", "value_error_match"),
        [
            ("blah", r"Could not transform 'blah' into a Color object"),
            ("0xfff1", r"Color code is invalid length\. Must be 3 or 6 digits"),
            (lambda: 22, r"Could not transform <function TestColor\.<lambda> at 0x[a-zA-Z0-9]+> into a Color object"),
            (NotImplementedError, r"Could not transform <class 'NotImplementedError'> into a Color object"),
            (NotImplemented, r"Could not transform NotImplemented into a Color object"),
            ((1, 1, 1, 1), r"Color must be an RGB triplet if set to a tuple type"),
            ((1, "a", 1), r"Could not transform \(1, 'a', 1\) into a Color object"),
            ((1.1, 1.0, 1.0), r"Expected red channel to be in the inclusive range of 0.0 and 1.0"),
            ((1.0, 1.1, 1.0), r"Expected green channel to be in the inclusive range of 0.0 and 1.0"),
            ((1.0, 1.0, 1.1), r"Expected blue channel to be in the inclusive range of 0.0 and 1.0"),
            ((), r"Color must be an RGB triplet if set to a tuple type"),
            ({}, r"Could not transform \{\} into a Color object"),
            ([], r"Color must be an RGB triplet if set to a list type"),
            ({1, 1, 1}, r"Could not transform \{1\} into a Color object"),
            (set(), r"Could not transform set\(\) into a Color object"),
            (b"1ff1ff", r"Could not transform b'1ff1ff' into a Color object"),
            *tuple_str_sad_test_data,
        ],
    )
    def test_Color_of_sad_path(self, input_string, value_error_match):
        with pytest.raises(ValueError, match=value_error_match):
            colors.Color.of(input_string)

    def test_Color_of_with_multiple_args(self):
        result = colors.Color.of((0xFF, 0x5, 0x1A))
        assert result == colors.Color(0xFF051A)

    @pytest.mark.parametrize(("input_string", "expected_color"), tuple_str_happy_test_data)
    def test_from_tuple_string_happy_path(self, input_string, expected_color):
        assert colors.Color.from_tuple_string(input_string) == expected_color

    @pytest.mark.parametrize(("input_string", "value_error_match"), tuple_str_sad_test_data)
    def test_from_tuple_string_sad_path(self, input_string, value_error_match):
        with pytest.raises(ValueError, match=value_error_match):
            colors.Color.from_tuple_string(input_string)
