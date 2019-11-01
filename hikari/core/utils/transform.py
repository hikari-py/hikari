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
Basic transformation utilities.
"""
import contextlib
import typing

from hikari.core.utils import unspecified

_T = typing.TypeVar("_T")
_U = typing.TypeVar("_U")
TypeCast = typing.Type[_T]
Cast = typing.Union[TypeCast, typing.Callable[[typing.Any], _T]]


def nullable_cast(value: typing.Any, cast: Cast) -> typing.Optional[_T]:
    if value is not None:
        return cast(value)
    return value


def try_cast(value: typing.Any, cast: Cast, default: _U = None) -> typing.Union[_T, _U]:
    with contextlib.suppress(Exception):
        return cast(value)
    return default


def put_if_specified(
    mapping: typing.Dict[typing.Hashable, typing.Any], key: typing.Hashable, value: typing.Any
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
    """
    if value is not unspecified.UNSPECIFIED:
        mapping[key] = value


def put_if_not_none(
    mapping: typing.Dict[typing.Hashable, typing.Any], key: typing.Hashable, value: typing.Optional[typing.Any]
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
    """
    if value is not None:
        mapping[key] = value


class SafeFormatDict(dict):
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
    return string.format_map(SafeFormatDict(**kwargs))


def id_map(snowflake_iterable):
    return {snowflake.id: snowflake for snowflake in snowflake_iterable}
