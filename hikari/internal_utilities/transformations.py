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
"""
Basic transformation utilities.
"""
from __future__ import annotations

__all__ = [
    "CastInputT",
    "CastOutputT",
    "DefaultT",
    "TypeCastT",
    "ResultT",
    "nullable_cast",
    "try_cast",
    "put_if_specified",
    "get_id",
    "cast_if_specified",
    "put_if_not_none",
    "format_present_placeholders",
    "get_parent_id_from_model",
    "id_map",
    "guild_id_to_shard_id",
    "image_bytes_to_image_data",
]

import base64
import contextlib
import typing

from hikari.internal_utilities import unspecified

if typing.TYPE_CHECKING:
    from hikari.internal_utilities import type_hints
    from hikari.orm.models import bases

CastInputT = typing.TypeVar("CastInputT")
CastOutputT = typing.TypeVar("CastOutputT")
DefaultT = typing.TypeVar("DefaultT")
TypeCastT = typing.Callable[[CastInputT], CastOutputT]
ResultT = typing.Union[CastOutputT, DefaultT]


def nullable_cast(value: CastInputT, cast: TypeCastT) -> ResultT:
    """
    Attempts to cast the given `value` with the given `cast`, but only if the `value` is
    not `None`. If it is `None`, then `None` is returned instead.
    """
    if value is None:
        return None
    return cast(value)


def try_cast(value: CastInputT, cast: TypeCastT, default: DefaultT = None) -> ResultT:
    """
    Try to cast the given value to the given cast. If it throws a :class:`Exception` or derivative, it will
    return `default` instead of the cast value instead.
    """
    with contextlib.suppress(Exception):
        return cast(value)
    return default


def put_if_specified(
    mapping: typing.Dict[typing.Hashable, typing.Any],
    key: typing.Hashable,
    value: typing.Any,
    type_after: type_hints.Nullable[TypeCastT] = None,
) -> None:
    """
    Add a value to the mapping under the given key as long as the value is not :attr:`UNSPECIFIED`

    Args:
        mapping:
            The mapping to add to.
        key:
            The key to add the value under.
        value:
            The value to add.
        type_after:
            Optional type to apply to the value when added.
    """
    if value is not unspecified.UNSPECIFIED:
        if type_after:
            mapping[key] = type_after(value)
        else:
            mapping[key] = value


def get_id(value: bases.SnowflakeLikeT) -> str:
    """
    Used to get the snowflake ID from an object.

    Args:
        value: The :class:`hikari.orm.model.bases.SnowflakeLikeT` like object to get an ID from.

    Returns:
        The resultant snowflake ID as a :class:`str`.
    """
    return str(value.id if hasattr(value, "id") else int(value))


def cast_if_specified(
    data: typing.Union[CastInputT, typing.Iterable[CastInputT], unspecified.Unspecified, None],
    cast: TypeCastT,
    iterable: bool = False,
    nullable: bool = False,
    **kwargs,
) -> typing.Union[CastInputT, typing.Iterable[CastInputT], unspecified.Unspecified, None]:
    """
    Attempts to cast the supplied data if it is specified.

    Args:
        data:
            The data to cast if it is not :class:`UNSPECIFIED`.
        cast:
            The function or type to cast the supplied data with.
        iterable:
            If this should iterate through `data`, converting each entry defaults to `False`.
        nullable:
            If this should skip attempting to cast data when it's `None`, defaults to `False`. If both this and
            `iterable` are `True` then this will assume that data itself will be nullable rather than entries in data.
        **kwargs:
            Optional kwargs to pass-through to cast, along with the data.

    Returns:
        The casted data.
    """
    if data is not unspecified.UNSPECIFIED and (data is not None or not nullable):
        if iterable:
            data = [cast(value, **kwargs) for value in data]
        else:
            data = cast(data, **kwargs)

    return data


def put_if_not_none(
    mapping: typing.Dict[typing.Hashable, typing.Any],
    key: typing.Hashable,
    value: typing.Any,
    type_after: type_hints.Nullable[TypeCastT] = None,
) -> None:
    """
    Add a value to the mapping under the given key as long as the value is not :attr:`None`

    Args:
        mapping:
            The mapping to add to.
        key:
            The key to add the value under.
        value:
            The value to add.
        type_after:
            Optional type to apply to the value when added.
    """
    if value is not None:
        if type_after:
            mapping[key] = type_after(value)
        else:
            mapping[key] = value


class _SafeFormatDict(dict):
    """
    Used internally by :func:`format_present_placeholders`.
    """

    def __missing__(self, key):
        return f"{{{key}}}"


def format_present_placeholders(string: str, **kwargs) -> str:
    """
    Behaves mostly the same as :meth:`str.format`, but if a placeholder is not
    present, it just keeps the placeholder inplace rather than raising a KeyError.

    Example:
        >>> format_present_placeholders("{foo} {bar} {baz}", foo=9, baz=27)
        "9 {bar} 27"
    """
    return string.format_map(_SafeFormatDict(**kwargs))


def get_parent_id_from_model(
    obj: typing.Any, parent_object: type_hints.Nullable[bases.SnowflakeLikeT], attribute: str
) -> str:
    """
    Attempt to get a parent object ID from the parent object or an object that has the parent object as an attribute.

    Args:
        obj:
            The object to try and get the parent object's ID from if parent_object isn't passed.
        parent_object:
            Optional the parent object to get the ID from by default, required if obj doesn't
            have an equivalent to this attached to it as `obj.{attribute}`.
        attribute:
            The attribute that the parent_object's equivalent should be attached to obj with.

    Returns:
        The parent object's ID as :class:`str`.

    Raises:
        TypeError:
            If parent_object isn't passed when obj doesn't have it attached as attribute, or if
            `parent_object` or `obj.{attribute}` don't inherit from :class:`hikari.orm.models.bases.SnowflakeMixin`.
    """
    try:
        return get_id(parent_object or getattr(obj, attribute))
    except AttributeError:
        raise TypeError(
            f"Missing argument '{attribute}' required when passing through an ID or an "
            f"object that doesn't have '{attribute}' attached to it for a {attribute}-bound model."
        ) from None


def id_map(
    snowflake_iterable: typing.Iterable[bases.SnowflakeMixinT],
) -> typing.MutableMapping[int, bases.SnowflakeMixinT]:
    """
    Given an iterable of elements with an :class:`int` `id` attribute, produce a mutable mapping
    of the IDs to their underlying values.
    """
    return {snowflake.id: snowflake for snowflake in snowflake_iterable}


def image_bytes_to_image_data(img_bytes: bytes) -> type_hints.Nullable[str]:
    """
    Encode image bytes into an image data string.

    Args:
        img_bytes:
            The image bytes or `None`.

    Raises:
        ValueError:
            If the image type passed is not supported.

    Returns:
        The image_bytes given encoded into an image data string or `None`.

    Note:
        Supported image types: .png, .jpeg, .jfif, .gif, .webp
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


def guild_id_to_shard_id(guild_id: int, shard_count: int) -> int:
    """
    Get the shard id of the given guild id.

    Args:
        guild_id:
            The ID of the guild.
        shard_count:
            The ammount of shards that are being used overal to connect to Discord.

    Returns:
        The shard the given guild is in.
    """
    return (guild_id >> 22) % shard_count
