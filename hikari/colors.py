# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Model that represents a common RGB color and provides simple conversions to other common color systems."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("Color", "Colorish")

import re
import string
import typing


def _to_rgb_int(value: str, name: str) -> int:
    # Heavy validation that is user-friendly and doesn't allow exploiting overflows, etc easily.
    #
    # isdigit allows chars like ² according to the docs.
    if not all(c in string.digits for c in value):
        raise ValueError(f"Expected digits only for {name} channel")
    if not value or len(value) > 3:
        raise ValueError(f"Expected 1 to 3 digits for {name} channel, got {len(value)}")

    int_value = int(value)

    if int_value >= 256:
        raise ValueError(f"Expected {name} channel to be in the inclusive range of 0 and 255, got {value!r}")

    return int_value


_FLOAT_PATTERN: typing.Final[typing.Pattern[str]] = re.compile(r"0\.\d*|\.\d+|1\.0*")


def _to_rgb_float(value: str, name: str) -> float:
    # Floats are easier to handle, as they don't overflow, they just become `inf`.

    if value.count(".") != 1:
        raise ValueError(f'Expected exactly 1 decimal point "." in {name} channel')
    if not _FLOAT_PATTERN.match(value):
        raise ValueError(f"Expected {name} channel to be a decimal in the inclusive range of 0.0 and 1.0")
    return float(value)


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

    .. code-block:: python

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

    Alternatively, if you have an arbitrary input in one of the above formats
    that you wish to become a color, you can use `Color.of` on the class itself
    to automatically attempt to resolve the color:

    .. code-block:: python

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

    Examples of initialization of Color objects from given formats include:

    .. code-block:: python

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

    __slots__: typing.Sequence[str] = ()

    def __init__(self, raw_rgb: typing.SupportsInt) -> None:
        if not (0 <= int(raw_rgb) <= 0xFFFFFF):
            raise ValueError(f"raw_rgb must be in the exclusive range of 0 and {0xFF_FF_FF}")
        # The __new__ for `int` initializes the value for us, this super-call does nothing other
        # than keeping the linter happy.
        super().__init__()

    def __repr__(self) -> str:
        r, g, b = self.rgb
        return f"Color(r={hex(r)}, g={hex(g)}, b={hex(b)})"

    def __str__(self) -> str:
        return self.hex_code

    @property
    def rgb(self) -> typing.Tuple[int, int, int]:
        """The RGB representation of this Color.

        Represented as a tuple of R, G, B. Each value is
        in the range [0, 0xFF].

        Examples
        --------
        `(123, 234, 47)`
        """  # noqa: D401 - Imperative mood
        return (self >> 16) & 0xFF, (self >> 8) & 0xFF, self & 0xFF

    @property
    def rgb_float(self) -> typing.Tuple[float, float, float]:
        """Return the floating-point RGB representation of this Color.

        Represented as a tuple of R, G, B. Each value is in the range [0, 1].

        Examples
        --------
        `(0.1, 0.2, 0.76)`
        """
        r, g, b = self.rgb
        return r / 0xFF, g / 0xFF, b / 0xFF

    @property
    def hex_code(self) -> str:
        """Six-digit hexadecimal color code for this Color.

        This is prepended with a `#` symbol, and will be in upper case.

        Examples
        --------
        `#1A2B3C`
        """
        return "#" + self.raw_hex_code

    @property
    def raw_hex_code(self) -> str:
        """Raw hex code.

        Examples
        --------
        `1A2B3C`
        """
        components = self.rgb
        return "".join(hex(c)[2:].zfill(2) for c in components).upper()

    @property
    def is_web_safe(self) -> bool:
        """Whether this color is web safe."""
        return not (((self & 0xFF0000) % 0x110000) or ((self & 0xFF00) % 0x1100) or ((self & 0xFF) % 0x11))

    @classmethod
    def from_rgb(cls, red: int, green: int, blue: int, /) -> Color:
        """Convert the given RGB to a `Color` object.

        Each channel must be within the range [0, 255] (0x0, 0xFF).

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
            raise ValueError("Expected red channel to be in the inclusive range of 0 and 255")
        if not 0 <= green <= 0xFF:
            raise ValueError("Expected green channel to be in the inclusive range of 0 and 255")
        if not 0 <= blue <= 0xFF:
            raise ValueError("Expected blue channel to be in the inclusive range of 0 and 255")
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
            raise ValueError("Expected red channel to be in the inclusive range of 0.0 and 1.0")
        if not 0 <= green <= 1:
            raise ValueError("Expected green channel to be in the inclusive range of 0.0 and 1.0")
        if not 0 <= blue <= 1:
            raise ValueError("Expected blue channel to be in the inclusive range of 0.0 and 1.0")
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

    @classmethod
    def from_tuple_string(cls, tuple_str: str, /) -> Color:
        """Convert a string in a tuple-like format to a `Color`.

        This allows formats that are optionally enclosed by `()`, `{}`, or
        `[]`, and contain three floats or ints, either space separated or
        comma separated.

        If comma separated, trailing and leading whitespace around each member
        is truncated.

        This is provided to allow command frontends to directly pass user
        input for representing a given colour into this class safely.

        Examples
        --------
        .. code-block:: python

            # Floats
            "1.0 1.0 1.0"
            "(1.0 1.0 1.0)"
            "[1.0 1.0 1.0]"
            "{1.0 1.0 1.0}"
            "1.0, 1.0, 1.0"
            "(1.0, 1.0, 1.0)"
            "[1.0, 1.0, 1.0]"
            "{1.0, 1.0, 1.0}"

            # Ints
            "252 252 252"
            "(252 252 252)"
            "[252 252 252]"
            "{252 252 252}"
            "252, 252, 252"
            "(252, 252, 252)"
            "[252, 252, 252]"
            "{252, 252, 252}"

        Parameters
        ----------
        tuple_str : str
            The string to parse.

        Returns
        -------
        Color
            The parsed colour object.

        Raises
        ------
        ValueError
            If an invalid format is given, or if any values exceed 1.0 for
            floats or 255 for ints.
        """
        if tuple_str[:: len(tuple_str) - 1] in ("()", "{}", "<>", "[]"):
            tuple_str = tuple_str[1:-1].strip()

        try:
            if "," in tuple_str:
                r, g, b = (bit.strip() for bit in tuple_str.split(","))
            else:
                r, g, b = tuple_str.split()
        except ValueError:
            raise ValueError("Expected three comma/space separated values") from None

        if any("." in s for s in (r, g, b)):
            return cls.from_rgb_float(_to_rgb_float(r, "red"), _to_rgb_float(g, "green"), _to_rgb_float(b, "blue"))
        else:
            return cls.from_rgb(_to_rgb_int(r, "red"), _to_rgb_int(g, "green"), _to_rgb_int(b, "blue"))

    @classmethod
    def of(cls, value: Colorish, /) -> Color:
        """Convert the value to a `Color`.

        This attempts to determine the correct data format based on the
        information provided.

        Parameters
        ----------
        value : Colorish
            A color compatible values.

        Examples
        --------
        .. code-block:: python

            >>> Color.of(0xFF051A)
            Color(r=0xff, g=0x5, b=0x1a)

            >>> Color.of(16712986)
            Color(r=0xff, g=0x5, b=0x1a)

            >>> c = Color.of((255, 5, 26))
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

            # Commas and brackets are optional, whitespace is ignored, and these
            # are compatible with all-ints between 0-255 or all-floats between
            # 0.0 and 1.0 only.
            >>> c = Color.of("5, 22, 33")
            Color(r=0x5, g=0x16, b=0x21)
            >>> c = Color.of("(5, 22, 33)")
            Color(r=0x5, g=0x16, b=0x21)
            >>> c = Color.of("[5, 22, 33]")
            Color(r=0x5, g=0x16, b=0x21)
            >>> c = Color.of("{5, 22, 33}")
            Color(r=0x5, g=0x16, b=0x21)

        Returns
        -------
        Color
            The Color object.
        """
        if isinstance(value, cls):
            return value
        if isinstance(value, int):
            return cls.from_int(value)
        if isinstance(value, (list, tuple)):
            if len(value) != 3:
                raise ValueError(f"Color must be an RGB triplet if set to a {type(value).__name__} type")

            r, g, b = value

            if isinstance(r, float) and isinstance(g, float) and isinstance(b, float):
                return cls.from_rgb_float(r, g, b)

            if isinstance(r, int) and isinstance(g, int) and isinstance(b, int):
                return cls.from_rgb(r, g, b)

        if isinstance(value, str):
            if any(c in value for c in "({[<,. "):
                return cls.from_tuple_string(value)

            is_start_hash_or_hex_literal = value.casefold().startswith(("#", "0x"))
            is_hex_digits = all(c in string.hexdigits for c in value) and len(value) in (3, 6)
            if is_start_hash_or_hex_literal or is_hex_digits:
                return cls.from_hex_code(value)

        raise ValueError(f"Could not transform {value!r} into a {cls.__qualname__} object")

    def to_bytes(
        self,
        length: typing.SupportsIndex,
        byteorder: typing.Literal["little", "big"],
        *,
        signed: bool = True,
    ) -> bytes:
        """Convert the color code to bytes.

        Parameters
        ----------
        length : int
            The number of bytes to produce. Should be around `3`, but not less.
        byteorder : str
            The endianness of the value represented by the bytes.
            Can be `"big"` endian or `"little"` endian.
        signed : bool
            Whether the value is signed or unsigned.

        Returns
        -------
        bytes
            The bytes representation of the Color.
        """
        return int(self).to_bytes(length, byteorder, signed=signed)


Colorish = typing.Union[
    Color,
    typing.SupportsInt,
    typing.Tuple[typing.SupportsInt, typing.SupportsInt, typing.SupportsInt],
    typing.Tuple[typing.SupportsFloat, typing.SupportsFloat, typing.SupportsFloat],
    typing.Sequence[typing.SupportsInt],
    typing.Sequence[typing.SupportsFloat],
    str,
]
"""Type hint representing types of value compatible with a colour type.

This may be:

1. `hikari.colors.Color`
2. `hikari.colours.Colour` (an alias for `hikari.colors.Color`).
3. A value that can be cast to an `int` (RGB hex-code).
4. a 3-`tuple` of `int` (RGB integers in range 0 through 255).
5. a 3-`tuple` of `float` (RGB floats in range 0 through 1).
6. a list of `int`.
7. a list of `float`.
8. a `str` hex colour code.

A hex colour code is expected to be in one of the following formats. Each of the
following examples means the same thing semantically.

1. (web-safe) `"12F"` (equivalent to `"1122FF"`)
2. (web-safe) `"0x12F"` (equivalent to `"0x1122FF"`)
3. (web-safe) `"0X12F"` (equivalent to `"0X1122FF"`)
4. (web-safe) `"#12F"` (equivalent to `"#1122FF"`)
5. `"1122FF"`
6. `"0x1122FF"`
7. `"0X1122FF"`
8. `"#1122FF"`

Web-safe colours are three hex-digits wide, `XYZ` becomes `XXYYZZ` in full-form.
"""
