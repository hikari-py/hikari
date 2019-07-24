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
"""
Model that represents a common RGB color and provides simple conversions to other common color systems.
"""

from __future__ import annotations

__all__ = ("Color",)

import string
import typing


class Color(int):
    """
    Representation of a color. This value is immutable.

    This is a specialization of :class:`int` which provides alternative overrides for common methods and color system
    conversions.

    This currently supports:

    - RGB
    - RGB (float)
    - 3-digit hex codes (e.g. 0xF1A -- web safe)
    - 6-digit hex codes (e.g. 0xFF11AA)

    Examples of conversions to given formats:
        >>> c = Color(0xFF051A)
        Color(r=0xff, g=0x5, b=0x1a)
        >>> hex(c)
        0xff051a
        >>> c.hex_code
        #FF051A
        >>> str(c)
        #FF051A
        >>> int(c)
        16712986
        >>> c.rgb
        (255, 5, 26)
        >>> c.rgb_float
        (1.0, 0.0196078431372549, 0.10196078431372549)

    Examples of initialization of Color objects from given formats:
        >>> c = Color(16712986)
        Color(r=0xff, g=0x5, b=0x1a)
        >>> c = Color.from_rgb(255, 5, 26)
        Color(r=0xff, g=0x5, b=1xa)
        >>> c = Color.from_hex_code("#1a2b3c")
        Color(r=0x1a, g=0x2b, b=0x3c)
        >>> c = Color.from_hex_code("#1AB")
        Color(r=0x11, g=0xaa, b=0xbb)
        >>> c = Color.from_rgb_float(1.0, 0.0196078431372549, 0.10196078431372549)
        Color(r=0xff, g=0x5, b=0x1a)
    """

    __slots__ = ()

    def __new__(cls: typing.Type[Color], raw_rgb: int) -> Color:
        _assert_in_range(raw_rgb, 0, 0xFF_FF_FF, "integer value")
        return super(Color, cls).__new__(cls, raw_rgb)

    def __repr__(self) -> str:
        r, g, b = self.rgb
        return f"Color(r={hex(r)}, g={hex(g)}, b={hex(b)})"

    def __str__(self) -> str:
        return self.hex_code

    def __int__(self):
        # Binary-OR to make raw int.
        return self | 0

    @property
    def rgb(self) -> typing.Tuple[int, int, int]:
        """
        The RGB representation of this Color. Represented a tuple of R, G, B. Each value is in the range [0, 0xFF].
        """
        return (self >> 16) & 0xFF, (self >> 8) & 0xFF, self & 0xFF

    @property
    def rgb_float(self) -> typing.Tuple[float, float, float]:
        """
        Return the floating-point RGB representation of this Color. Represented as a tuple of R, G, B. Each value is in
        the range [0, 1].
        """
        r, g, b = self.rgb
        return r / 0xFF, g / 0xFF, b / 0xFF

    @property
    def hex_code(self) -> str:
        """
        The six-digit hexadecimal color code for this Color. This is prepended with a `#` symbol, and will be
        in upper case.

        Example:
            #1A2B3C
        """
        return "#" + self.raw_hex_code

    @property
    def raw_hex_code(self) -> str:
        """
        The raw hex code.

        Example:
             1A2B3C
        """
        components = self.rgb
        return "".join(hex(c)[2:].zfill(2) for c in components).upper()

    @property
    def is_web_safe(self) -> bool:
        """
        True if this colour is a web-safe colour, False otherwise.
        """
        hex_code = self.raw_hex_code
        return all(_all_same(*c) for c in (hex_code[:2], hex_code[2:4], hex_code[4:]))

    @classmethod
    def from_rgb(cls: typing.Type[Color], red: int, green: int, blue: int) -> Color:
        """
        Convert the given RGB colorspace represented in values within the range [0, 255]: [0x0, 0xFF], to a Color
        object.

        Args:
            red:
                Red channel.
            green:
                Green channel.
            blue:
                Blue channel.

        Returns:
            A Color object.

        Raises:
              ValueError: if red, green, or blue are outside the range [0x0, 0xFF]
        """
        _assert_in_range(red, 0, 0xFF, "red")
        _assert_in_range(green, 0, 0xFF, "green")
        _assert_in_range(blue, 0, 0xFF, "blue")
        return cls((red << 16) | (green << 8) | blue)

    @classmethod
    def from_rgb_float(cls: typing.Type[Color], red_f: float, green_f: float, blue_f: float) -> Color:
        """
        Convert the given RGB colorspace represented using floats in the range [0, 1] to a Color object.

        Args:
            red_f:
                Red channel.
            green_f:
                Green channel.
            blue_f:
                Blue channel.

        Returns:
            A Color object.

        Raises:
            ValueError: if red, green or blue are outside the range [0, 1]
        """
        _assert_in_range(red_f, 0, 1, "red")
        _assert_in_range(green_f, 0, 1, "green")
        _assert_in_range(blue_f, 0, 1, "blue")
        return cls.from_rgb(int(red_f * 0xFF), int(green_f * 0xFF), int(blue_f * 0xFF))

    @classmethod
    def from_hex_code(cls: typing.Type[Color], hex_code: str) -> Color:
        """
        Consumes a string hexadecimal color code and produces a Color.

        The inputs may be of the following format (case insensitive):
            `1a2`, `#1a2`, `0x1a2` (for websafe colors), or
            `1a2b3c`, `#1a2b3c` `0x1a2b3c` (for regular 3-byte color-codes).

        Args:
            hex_code:
                A hexadecimal color code to parse.

        Returns:
            A corresponding Color object.

        Raises:
            Value error if the Color
        """
        if hex_code.startswith("#"):
            hex_code = hex_code[1:]
        elif hex_code.startswith(("0x", "0X")):
            hex_code = hex_code[2:]

        if not all(c in string.hexdigits for c in hex_code):
            raise ValueError("Color code must be hexadecimal")

        if len(hex_code) == 3:
            # Web-safe
            components = (int(c, 16) for c in hex_code)
            return cls.from_rgb(*(c << 4 | c for c in components))

        if len(hex_code) == 6:
            components = hex_code[:2], hex_code[2:4], hex_code[4:6]
            return cls.from_rgb(*(int(c, 16) for c in components))

        raise ValueError("Color code is invalid length. Must be 3 or 6 digits")

    @classmethod
    def from_int(cls: typing.Type[Color], i: int) -> Color:
        """
        Create a color from a raw integer that Discord can understand.

        Args:
            i:
                The raw colour integer.

        Returns:
            The Color object.
        """
        return cls(i)


def _assert_in_range(value, min_inclusive, max_inclusive, name):
    if not (min_inclusive <= value <= max_inclusive):
        raise ValueError(f"{name} must be in the inclusive range of {min_inclusive} and {max_inclusive}")


def _all_same(first, *rest):
    for r in rest:
        if r != first:
            return False

    return True
