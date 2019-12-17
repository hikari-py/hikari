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
import contextlib
import typing

from hikari.internal_utilities import unspecified

ValueT = typing.TypeVar("ValueT")
DefaultT = typing.TypeVar("DefaultT")
TypeCastT = typing.Type[ValueT]
CastT = typing.Union[TypeCastT, typing.Callable[[typing.Any], ValueT]]


def nullable_cast(value: typing.Any, cast: CastT) -> typing.Optional[ValueT]:
    """
    Attempts to cast the given `value` with the given `cast`, but only if the `value` is
    not `None`. If it is `None`, then `None` is returned instead.
    """
    if value is None:
        return None
    return cast(value)


def try_cast(value: typing.Any, cast: CastT, default: DefaultT = None) -> typing.Union[ValueT, DefaultT]:
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
    type_after: CastT = unspecified.UNSPECIFIED,
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
            Defaults to :attr:`hikari.internal_utilities.unspecified.UNSPECIFIED`.
    """
    if value is not unspecified.UNSPECIFIED:
        if type_after is not unspecified.UNSPECIFIED:
            mapping[key] = type_after(value)
        else:
            mapping[key] = value


def put_if_not_none(
    mapping: typing.Dict[typing.Hashable, typing.Any],
    key: typing.Hashable,
    value: typing.Any,
    type_after: CastT = unspecified.UNSPECIFIED,
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
            Defaults to :attr:`hikari.internal_utilities.unspecified.UNSPECIFIED`.
    """
    if value is not None:
        if type_after is not unspecified.UNSPECIFIED:
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


def id_map(snowflake_iterable: typing.Iterable[ValueT]) -> typing.MutableMapping[int, ValueT]:
    """
    Given an iterable of elements with an :class:`int` `id` attribute, produce a mutable mapping
    of the IDs to their underlying values.
    """
    return {snowflake.id: snowflake for snowflake in snowflake_iterable}
