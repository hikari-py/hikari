#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""Model that represents a common RGB color and provides simple conversions to other common color systems.

.. inheritance-diagram::
    builtins.int
    hikari.colors
    :parts: 1
"""
from __future__ import annotations

__all__ = ["Color", "ColorCompatibleT"]

import string
import typing

from hikari.internal import assertions


class Color(int, typing.SupportsInt):
    """Representation of a color.

    This value is immutable.

    This is a specialization of :obj:`int` which provides alternative overrides for common methods and color system
    conversions.

    This currently supports:

    * RGB
    * RGB (float)
    * 3-digit hex codes (e.g. 0xF1A -- web safe)
    * 6-digit hex codes (e.g. 0xFF11AA)
    * 3-digit RGB strings (e.g. #1A2 -- web safe)
    * 6-digit RGB hash strings (e.g. #1A2B3C)

    Examples
    --------
    Examples of conversions to given formats include:
    .. code-block::python

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

    Alternatively, if you have an arbitrary input in one of the above formats that you wish to become a color, you can
    use the get-attribute operator on the class itself to automatically attempt to resolve the color:
    .. code-block::python

        >>> Color[0xFF051A]
        Color(r=0xff, g=0x5, b=0x1a)
        >>> Color[16712986]
        Color(r=0xff, g=0x5, b=0x1a)
        >>> c = Color[(255, 5, 26)]
        Color(r=0xff, g=0x5, b=1xa)
        >>> c = Color[[0xFF, 0x5, 0x1a]]
        Color(r=0xff, g=0x5, b=1xa)
        >>> c = Color["#1a2b3c"]
        Color(r=0x1a, g=0x2b, b=0x3c)
        >>> c = Color["#1AB"]
        Color(r=0x11, g=0xaa, b=0xbb)
        >>> c = Color[(1.0, 0.0196078431372549, 0.10196078431372549)]
        Color(r=0xff, g=0x5, b=0x1a)
        >>> c = Color[[1.0, 0.0196078431372549, 0.10196078431372549]]
        Color(r=0xff, g=0x5, b=0x1a)

    Examples of initialization of Color objects from given formats include:
    .. code-block::python

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

    def __new__(cls, raw_rgb: typing.SupportsInt) -> Color:
        assertions.assert_in_range(raw_rgb, 0, 0xFF_FF_FF, "integer value")
        return super(Color, cls).__new__(cls, raw_rgb)

    def __repr__(self) -> str:
        r, g, b = self.rgb
        return f"Color(r={hex(r)}, g={hex(g)}, b={hex(b)})"

    def __str__(self) -> str:
        return self.hex_code

    def __int__(self):
        # Binary-OR to make raw int.
        return self | 0

    # Ignore docstring not starting in an imperative mood
    @property
    def rgb(self) -> typing.Tuple[int, int, int]:  # noqa: D401
        """The RGB representation of this Color.

        Represented as a tuple of R, G, B. Each value is
        in the range [0, 0xFF].
        """
        return (self >> 16) & 0xFF, (self >> 8) & 0xFF, self & 0xFF

    @property
    def rgb_float(self) -> typing.Tuple[float, float, float]:
        """Return the floating-point RGB representation of this Color.

        Represented as a tuple of R, G, B. Each value is in the range [0, 1].
        """
        r, g, b = self.rgb
        return r / 0xFF, g / 0xFF, b / 0xFF

    @property
    def hex_code(self) -> str:
        """Six-digit hexadecimal color code for this Color.

        This is prepended with a ``#`` symbol, and will be in upper case.

        Example
        -------
        ``#1A2B3C``
        """
        return "#" + self.raw_hex_code

    @property
    def raw_hex_code(self) -> str:
        """Raw hex code.

        Example
        -------
        ``1A2B3C``
        """
        components = self.rgb
        return "".join(hex(c)[2:].zfill(2) for c in components).upper()

    # Ignore docstring not starting in an imperative mood
    @property
    def is_web_safe(self) -> bool:  # noqa: D401
        """``True`` if the color is web safe, ``False`` otherwise."""
        hex_code = self.raw_hex_code
        return all(_all_same(*c) for c in (hex_code[:2], hex_code[2:4], hex_code[4:]))

    @classmethod
    def from_rgb(cls, red: int, green: int, blue: int) -> Color:
        """Convert the given RGB to a :obj:`Color` object.

        Each channel must be withing the range [0, 255] (0x0, 0xFF).

        Parameters
        ----------
        red : :obj:`int`
            Red channel.
        green : :obj:`int`
            Green channel.
        blue : :obj:`int`
            Blue channel.

        Returns
        -------
        :obj:`Color`
            A Color object.

        Raises
        ------
        :obj:`ValueError`
            If red, green, or blue are outside the range [0x0, 0xFF].
        """
        assertions.assert_in_range(red, 0, 0xFF, "red")
        assertions.assert_in_range(green, 0, 0xFF, "green")
        assertions.assert_in_range(blue, 0, 0xFF, "blue")
        # noinspection PyTypeChecker
        return cls((red << 16) | (green << 8) | blue)

    @classmethod
    def from_rgb_float(cls, red_f: float, green_f: float, blue_f: float) -> Color:
        """Convert the given RGB to a :obj:`Color` object.

        The colorspace represented values have to be within the
        range [0, 1].

        Parameters
        ----------
        red_f : :obj:`float`
            Red channel.
        green_f : :obj:`float`
            Green channel.
        blue_f : :obj:`float`
            Blue channel.

        Returns
        -------
        :obj:`Color`
            A Color object.

        Raises
        ------
        :obj:`ValueError`
            If red, green or blue are outside the range [0, 1].
        """
        assertions.assert_in_range(red_f, 0, 1, "red")
        assertions.assert_in_range(green_f, 0, 1, "green")
        assertions.assert_in_range(blue_f, 0, 1, "blue")
        # noinspection PyTypeChecker
        return cls.from_rgb(int(red_f * 0xFF), int(green_f * 0xFF), int(blue_f * 0xFF))

    @classmethod
    def from_hex_code(cls, hex_code: str) -> Color:
        """Convert the given hexadecimal color code to a :obj:`Color`.

        The inputs may be of the following format (case insensitive):
        ``1a2``, ``#1a2``, ``0x1a2`` (for websafe colors), or
        ``1a2b3c``, ``#1a2b3c``, ``0x1a2b3c`` (for regular 3-byte color-codes).

        Parameters
        ----------
        hex_code : :obj:`str`
            A hexadecimal color code to parse.

        Returns
        -------
        :obj:`Color`
            A corresponding Color object.

        Raises
        ------
        :obj:`ValueError`
            If ``hex_code`` is not a hexadecimal or is a inalid length.
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
            # noinspection PyTypeChecker
            return cls.from_rgb(*[(c << 4 | c) for c in components])

        if len(hex_code) == 6:
            return cls.from_rgb(int(hex_code[:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16))

        raise ValueError("Color code is invalid length. Must be 3 or 6 digits")

    @classmethod
    def from_int(cls, i: typing.SupportsInt) -> Color:
        """Convert the given :obj:`typing.SupportsInt` to a :obj:`Color`.

        Parameters
        ----------
        i : :obj:`typing.SupportsInt`
            The raw color integer.

        Returns
        -------
        :obj:`Color`
            The Color object.
        """
        return cls(i)

    # Partially chose to override these as the docstrings contain typos according to Sphinx.
    @classmethod
    def from_bytes(cls, bytes_: typing.Sequence[int], byteorder: str, *, signed: bool = True) -> Color:
        """Convert the bytes to a :obj:`Color`.

        Parameters
        ----------
        bytes_ : :obj:`typing.Iterable` [ :obj:`int` ]
            A iterable of :obj:`int` byte values.

        byteorder : :obj:`str`
            The endianess of the value represented by the bytes.
            Can be ``"big"`` endian or ``"little"`` endian.

        signed : :obj:`bool`
            Whether the value is signed or unsigned.

        Returns
        -------
        :obj:`Color`
            The Color object.
        """
        return Color(int.from_bytes(bytes_, byteorder, signed=signed))

    def to_bytes(self, length: int, byteorder: str, *, signed: bool = True) -> bytes:
        """Convert the color code to bytes.

        Parameters
        ----------
        length : :obj:`int`
            The number of bytes to produce. Should be around ``3``, but not less.

        byteorder : :obj:`str`
            The endianess of the value represented by the bytes.
            Can be ``"big"`` endian or ``"little"`` endian.

        signed : :obj:`bool`
            Whether the value is signed or unsigned.

        Returns
        -------
        :obj:`bytes`
            The bytes representation of the Color.
        """
        return int(self).to_bytes(length, byteorder, signed=signed)

    @classmethod
    def __class_getitem__(cls, color: ColorCompatibleT) -> Color:  # pylint:disable=arguments-differ
        if isinstance(color, cls):
            return color
        elif isinstance(color, int):
            return cls.from_int(color)
        elif isinstance(color, (list, tuple)):
            assertions.assert_that(
                len(color) == 3, f"color must be an RGB triplet if set to a {type(color).__name__} type"
            )

            if _all_same(*map(type, color)):
                first = color[0]
                if isinstance(first, float):
                    return cls.from_rgb_float(*color)
                if isinstance(first, int):
                    return cls.from_rgb(*color)

                raise ValueError(
                    "all three channels must be all int or all float types if setting the color to an RGB triplet"
                )
        if isinstance(color, str):
            is_start_hash_or_hex_literal = color.casefold().startswith(("#", "0x"))
            is_hex_digits = all(c in string.hexdigits for c in color) and len(color) in (3, 6)
            if is_start_hash_or_hex_literal or is_hex_digits:
                return cls.from_hex_code(color)

        raise ValueError(f"Could not transform {color!r} into a {cls.__qualname__} object")


def _all_same(first, *rest):
    for r in rest:
        if r != first:
            return False

    return True


#: Any type that can be converted into a color object.
ColorCompatibleT = typing.Union[
    Color,
    typing.SupportsInt,
    typing.Tuple[typing.SupportsInt, typing.SupportsInt, typing.SupportsInt],
    typing.Tuple[typing.SupportsFloat, typing.SupportsFloat, typing.SupportsFloat],
    typing.Sequence[typing.SupportsInt],
    typing.Sequence[typing.SupportsFloat],
    str,
]
