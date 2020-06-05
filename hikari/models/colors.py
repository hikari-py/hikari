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
"""Model that represents a common RGB color and provides simple conversions to other common color systems."""

from __future__ import annotations

__all__ = ["Color"]

import string
import typing


class Color(int):
    """Representation of a color.

    This value is immutable.

    This is a specialization of `int` which provides alternative overrides for
    common methods and color system conversions.

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

    ```py
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
    ```

    Alternatively, if you have an arbitrary input in one of the above formats
    that you wish to become a color, you can use `Color.of` on the class itself
    to automatically attempt to resolve the color:

    ```py
    >>> Color.of(0xFF051A)
    Color(r=0xff, g=0x5, b=0x1a)

    >>> Color.of(16712986)
    Color(r=0xff, g=0x5, b=0x1a)

    >>> c = Color.of((255, 5, 26))
    Color(r=0xff, g=0x5, b=1xa)

    >>> c = Color.of(255, 5, 26)
    Color(r=0xff, g=0x5, b=1xa)

    >>> c = Color.of([0xFF, 0x5, 0x1a])
    Color(r=0xff, g=0x5, b=1xa)

    >>> c = Color.of("#1a2b3c")
    Color(r=0x1a, g=0x2b, b=0x3c)

    >>> c = Color.of("#1AB")
    Color(r=0x11, g=0xaa, b=0xbb)

    >>> c = Color.of((1.0, 0.0196078431372549, 0.10196078431372549))
    Color(r=0xff, g=0x5, b=0x1a)

    >>> c = Color.of([1.0, 0.0196078431372549, 0.10196078431372549])
    Color(r=0xff, g=0x5, b=0x1a)
    ```

    Examples of initialization of Color objects from given formats include:

    ```py
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
    ```
    """

    __slots__ = ()

    def __new__(cls, raw_rgb: typing.Union[int, typing.SupportsInt], /) -> Color:
        if not 0 <= int(raw_rgb) <= 0xFF_FF_FF:
            raise ValueError(f"raw_rgb must be in the exclusive range of 0 and {0xFF_FF_FF}")
        return super(Color, cls).__new__(cls, raw_rgb)

    def __repr__(self) -> str:
        r, g, b = self.rgb
        return f"Color(r={hex(r)}, g={hex(g)}, b={hex(b)})"

    def __str__(self) -> str:
        return self.hex_code

    # Ignore docstring not starting in an imperative mood
    @property
    def rgb(self) -> typing.Tuple[int, int, int]:  # noqa: D401
        """The RGB representation of this Color.

        Represented as a tuple of R, G, B. Each value is
        in the range [0, 0xFF].

        Example
        -------
        `(123, 234, 47)`
        """
        return (self >> 16) & 0xFF, (self >> 8) & 0xFF, self & 0xFF

    @property
    def rgb_float(self) -> typing.Tuple[float, float, float]:
        """Return the floating-point RGB representation of this Color.

        Represented as a tuple of R, G, B. Each value is in the range [0, 1].

        Example
        -------
        `(0.1, 0.2, 0.76)`
        """
        r, g, b = self.rgb
        return r / 0xFF, g / 0xFF, b / 0xFF

    @property
    def hex_code(self) -> str:
        """Six-digit hexadecimal color code for this Color.

        This is prepended with a `#` symbol, and will be in upper case.

        Example
        -------
        `#1A2B3C`
        """
        return "#" + self.raw_hex_code

    @property
    def raw_hex_code(self) -> str:
        """Raw hex code.

        Example
        -------
        `1A2B3C`
        """
        components = self.rgb
        return "".join(hex(c)[2:].zfill(2) for c in components).upper()

    # Ignore docstring not starting in an imperative mood
    @property
    def is_web_safe(self) -> bool:  # noqa: D401
        """`True` if the color is web safe, `False` otherwise."""
        return not (((self & 0xFF0000) % 0x110000) or ((self & 0xFF00) % 0x1100) or ((self & 0xFF) % 0x11))

    @classmethod
    def from_rgb(cls, red: int, green: int, blue: int, /) -> Color:
        """Convert the given RGB to a `Color` object.

        Each channel must be withing the range [0, 255] (0x0, 0xFF).

        Parameters
        ----------
        red : int
            Red channel.
        green : int
            Green channel.
        blue : int
            Blue channel.

        Returns
        -------
        Color
            A Color object.

        Raises
        ------
        ValueError
            If red, green, or blue are outside the range [0x0, 0xFF].
        """
        if not 0 <= red <= 0xFF:
            raise ValueError("red must be in the inclusive range of 0 and 255")
        if not 0 <= green <= 0xFF:
            raise ValueError("green must be in the inclusive range of 0 and 255")
        if not 0 <= blue <= 0xFF:
            raise ValueError("blue must be in the inclusive range of 0 and 255")
        # noinspection PyTypeChecker
        return cls((red << 16) | (green << 8) | blue)

    @classmethod
    def from_rgb_float(cls, red: float, green: float, blue: float, /) -> Color:
        """Convert the given RGB to a `Color` object.

        The color-space represented values have to be within the
        range [0, 1].

        Parameters
        ----------
        red : float
            Red channel.
        green : float
            Green channel.
        blue : float
            Blue channel.

        Returns
        -------
        Color
            A Color object.

        Raises
        ------
        ValueError
            If red, green or blue are outside the range [0, 1].
        """
        if not 0 <= red <= 1:
            raise ValueError("red must be in the inclusive range of 0 and 1.")
        if not 0 <= green <= 1:
            raise ValueError("green must be in the inclusive range of 0 and 1.")
        if not 0 <= blue <= 1:
            raise ValueError("blue must be in the inclusive range of 0 and 1.")
        # noinspection PyTypeChecker
        return cls.from_rgb(int(red * 0xFF), int(green * 0xFF), int(blue * 0xFF))

    @classmethod
    def from_hex_code(cls, hex_code: str, /) -> Color:
        """Convert the given hexadecimal color code to a `Color`.

        The inputs may be of the following format (case insensitive):
        `1a2`, `#1a2`, `0x1a2` (for web-safe colors), or
        `1a2b3c`, `#1a2b3c`, `0x1a2b3c` (for regular 3-byte color-codes).

        Parameters
        ----------
        hex_code : str
            A hexadecimal color code to parse. This may optionally start with
            a case insensitive `0x` or `#`.

        Returns
        -------
        Color
            A corresponding Color object.

        Raises
        ------
        ValueError
            If `hex_code` is not a hexadecimal or is a invalid length.
        """
        if hex_code.startswith("#"):
            hex_code = hex_code[1:]
        elif hex_code.startswith(("0x", "0X")):
            hex_code = hex_code[2:]

        if not all(c in string.hexdigits for c in hex_code):
            raise ValueError("Color code must be hexadecimal")

        if len(hex_code) == 3:
            # Web-safe
            r, g, b = (c << 4 | c for c in (int(c, 16) for c in hex_code))
            # noinspection PyTypeChecker
            return cls.from_rgb(r, g, b)

        if len(hex_code) == 6:
            return cls.from_rgb(int(hex_code[:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16))

        raise ValueError("Color code is invalid length. Must be 3 or 6 digits")

    @classmethod
    def from_int(cls, integer: typing.SupportsInt, /) -> Color:
        """Convert the given `typing.SupportsInt` to a `Color`.

        Parameters
        ----------
        integer : typing.SupportsInt
            The raw color integer.

        Returns
        -------
        Color
            The Color object.
        """
        return cls(integer)

    # Partially chose to override these as the docstrings contain typos according to Sphinx.
    @classmethod
    def from_bytes(cls, bytes_: typing.Sequence[int], byteorder: str, *, signed: bool = True) -> Color:
        """Convert the bytes to a `Color`.

        Parameters
        ----------
        bytes_ : typing.Iterable[int]
            A iterable of int byte values.

        byteorder : str
            The endianess of the value represented by the bytes.
            Can be `"big"` endian or `"little"` endian.

        signed : bool
            Whether the value is signed or unsigned.

        Returns
        -------
        Color
            The Color object.
        """
        return Color(int.from_bytes(bytes_, byteorder, signed=signed))

    @classmethod
    def of(
        cls,
        *values: typing.Union[
            Color,
            typing.SupportsInt,
            typing.Tuple[typing.SupportsInt, typing.SupportsInt, typing.SupportsInt],
            typing.Tuple[typing.SupportsFloat, typing.SupportsFloat, typing.SupportsFloat],
            typing.Sequence[typing.SupportsInt],
            typing.Sequence[typing.SupportsFloat],
            str,
        ],
    ) -> Color:
        """Convert the value to a `Color`.

        This attempts to determine the correct data format based on the
        information provided.

        Parameters
        ----------
        values : ColorCompatibleT
            A color compatible values.

        Examples
        --------
        ```py
        >>> Color.of(0xFF051A)
        Color(r=0xff, g=0x5, b=0x1a)

        >>> Color.of(16712986)
        Color(r=0xff, g=0x5, b=0x1a)

        >>> c = Color.of((255, 5, 26))
        Color(r=0xff, g=0x5, b=1xa)

        >>> c = Color.of(255, 5, 26)
        Color(r=0xff, g=0x5, b=1xa)

        >>> c = Color.of([0xFF, 0x5, 0x1a])
        Color(r=0xff, g=0x5, b=1xa)

        >>> c = Color.of("#1a2b3c")
        Color(r=0x1a, g=0x2b, b=0x3c)

        >>> c = Color.of("#1AB")
        Color(r=0x11, g=0xaa, b=0xbb)

        >>> c = Color.of((1.0, 0.0196078431372549, 0.10196078431372549))
        Color(r=0xff, g=0x5, b=0x1a)

        >>> c = Color.of([1.0, 0.0196078431372549, 0.10196078431372549])
        Color(r=0xff, g=0x5, b=0x1a)
        ```

        Returns
        -------
        Color
            The Color object.
        """
        if len(values) == 1:
            values = values[0]

        if isinstance(values, cls):
            return values
        if isinstance(values, int):
            return cls.from_int(values)
        if isinstance(values, (list, tuple)):
            if len(values) != 3:
                raise ValueError(f"color must be an RGB triplet if set to a {type(values).__name__} type")

            if any(isinstance(c, float) for c in values):
                r, g, b = values
                return cls.from_rgb_float(r, g, b)

            if all(isinstance(c, int) for c in values):
                r, g, b = values
                return cls.from_rgb(r, g, b)

        if isinstance(values, str):
            is_start_hash_or_hex_literal = values.casefold().startswith(("#", "0x"))
            is_hex_digits = all(c in string.hexdigits for c in values) and len(values) in (3, 6)
            if is_start_hash_or_hex_literal or is_hex_digits:
                return cls.from_hex_code(values)

        raise ValueError(f"Could not transform {values!r} into a {cls.__qualname__} object")

    def to_bytes(self, length: int, byteorder: str, *, signed: bool = True) -> bytes:
        """Convert the color code to bytes.

        Parameters
        ----------
        length : int
            The number of bytes to produce. Should be around `3`, but not less.
        byteorder : str
            The endianess of the value represented by the bytes.
            Can be `"big"` endian or `"little"` endian.
        signed : bool
            Whether the value is signed or unsigned.

        Returns
        -------
        bytes
            The bytes representation of the Color.
        """
        return int(self).to_bytes(length, byteorder, signed=signed)
