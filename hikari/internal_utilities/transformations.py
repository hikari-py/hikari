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
"""Basic transformation utilities."""
__all__ = [
    "CastInputT",
    "CastOutputT",
    "DefaultT",
    "TypeCastT",
    "ResultT",
    "nullable_cast",
    "try_cast",
    "put_if_specified",
    "image_bytes_to_image_data",
]

import base64
import contextlib
import typing

CastInputT = typing.TypeVar("CastInputT")
CastOutputT = typing.TypeVar("CastOutputT")
DefaultT = typing.TypeVar("DefaultT")
TypeCastT = typing.Callable[[CastInputT], CastOutputT]
ResultT = typing.Union[CastOutputT, DefaultT]


def nullable_cast(value: CastInputT, cast: TypeCastT) -> ResultT:
    """
    Attempts to cast the given ``value`` with the given ``cast``, but only if the 
    ``value`` is not ``None``. If it is ``None``, then ``None`` is returned instead.
    """
    if value is None:
        return None
    return cast(value)


def try_cast(value: CastInputT, cast: TypeCastT, default: DefaultT = None) -> ResultT:
    """Try to cast the given value to the given cast.
    
    If it throws a :obj:`Exception` or derivative, it will return ``default`` instead 
    of the cast value instead.
    """
    with contextlib.suppress(Exception):
        return cast(value)
    return default


def put_if_specified(
    mapping: typing.Dict[typing.Hashable, typing.Any],
    key: typing.Hashable,
    value: typing.Any,
    type_after: typing.Optional[TypeCastT] = None,
) -> None:
    """Add a value to the mapping under the given key as long as the value is not :obj:`typing.Literal`

    Parameters
    ----------
    mapping : :obj:`typing.Dict` [ :obj:`typing.Hashable`, :obj:`typing.Any` ]
        The mapping to add to.
    key : :obj:`typing.Hashable`
        The key to add the value under.
    value : :obj:`typing.Any`
        The value to add.
    type_after : :obj:`TypeCastT`, optional
        Type to apply to the value when added.
    """
    if value is not ...:
        if type_after:
            mapping[key] = type_after(value)
        else:
            mapping[key] = value


def image_bytes_to_image_data(img_bytes: typing.Optional[bytes] = None) -> typing.Optional[str]:
    """Encode image bytes into an image data string.

    Parameters
    ----------
    img_bytes : :obj:`bytes`, optional
        The image bytes.

    Raises
    ------
    :obj:`ValueError`
        If the image type passed is not supported.

    Returns
    -------
    :obj:`str`, optional
        The ``image_bytes`` given encoded into an image data string or ``None``.

    Note
    ----
    Supported image types: ``.png``, ``.jpeg``, ``.jfif``, ``.gif``, ``.webp``
    """
    if img_bytes is None:
        return None

    if img_bytes[:8] == b"\211PNG\r\n\032\n":
        img_type = "image/png"
    elif img_bytes[6:10] in (b"Exif", b"JFIF"):
        img_type = "image/jpeg"
    elif img_bytes[:6] in (b"GIF87a", b"GIF89a"):
        img_type = "image/gif"
    elif img_bytes.startswith(b"RIFF") and img_bytes[8:12] == b"WEBP":
        img_type = "image/webp"
    else:
        raise ValueError("Unsupported image type passed")

    image_data = base64.b64encode(img_bytes).decode()

    return f"data:{img_type};base64,{image_data}"


def try_cast_or_defer_unary_operator(type_):
    return lambda data: try_cast(data, type_, data)
