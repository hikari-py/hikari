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
Helper methods used for managing Mapping types during transformations.
"""
__all__ = ("flatten", "try_cast", "get_cast", "get_cast_or_raw", "get_sequence", "put_if_specified")

import inspect
import typing

from hikari.core.utils import unspecified

T = typing.TypeVar("T")
U = typing.TypeVar("U")
Seq = typing.TypeVar("Seq", bound=typing.Collection)
_CastFunc = typing.Union[typing.Type[T], typing.Callable[[typing.Any], T], typing.Callable[..., T]]

_EMPTY_TUPLE = ()
_BAD_OBJECT = object()


def flatten(objects, key_attr: str = "id"):
    return {getattr(o, key_attr): o for o in objects}


def try_cast(value: typing.Any, cast: _CastFunc, default: U, **kwargs) -> typing.Union[T, U]:
    """
    Try to cast a given value using the cast, or return default if it fails.
    Args:
        value:
            the value to cast.
        cast:
            the cast function.
        default:
            the default value if the cast fails.
        **kwargs:
            other kwargs to pass to the cast.

    Returns:
        The cast value or the default value otherwise.
    """
    # We could use a suppress here, but this is useful during debugging to explicitly see what the exception is
    # by adding traceback.print_exc() to the except suite.
    # noinspection PyBroadException
    try:
        return cast(value, **kwargs)
    except Exception:
        return default


def get_cast(
    mapping: typing.Dict[typing.Hashable, typing.Any],
    key: typing.Hashable,
    cast: typing.Callable[[typing.Any], T],
    default: typing.Any = None,
    *,
    default_on_error: bool = False,
) -> typing.Optional[T]:
    """
    Get from a map and perform a type cast where possible.

    Args:
        mapping:
            dict to read from.
        key:
            key to access.
        cast:
            type to cast to if required. This may instead be a function if the call should always be made regardless.
        default:
            default value to return, or `None` if unspecified.
        default_on_error:
            If `True`, any error occurring whilst casting will be suppressed and the default value will be returned.
            If `False`, as per the default, it will raise the error.

    Returns:
        An optional casted value, or `None` if it wasn't in the `mapping` at the start.
    """
    raw = mapping.get(key)
    is_method_or_function = inspect.isfunction(cast) or inspect.ismethod(cast)
    if not is_method_or_function and isinstance(raw, cast):
        return raw
    if raw is None:
        return default
    if default_on_error:
        return try_cast(raw, cast, default)
    return cast(raw)


def get_cast_or_raw(
    mapping: typing.Dict[typing.Hashable, typing.Any], key: typing.Hashable, cast: typing.Callable[[typing.Any], T]
) -> typing.Union[T, typing.Any]:
    """
    Get the value and cast it to the given cast, or return the raw value.

    If the value never existed, we return None instead.

    Args:
        mapping:
            The mapping to access.
        key:
            The key in the mapping to get.
        cast:
            The callable to cast to.

    Returns:
        Either a cast value, the raw value on failure, or None if the value never existed in the mapping.
    """
    value = mapping.get(key)
    return try_cast(value, cast, value)


def get_sequence(
    mapping: typing.Dict[typing.Hashable, typing.Any],
    key: typing.Hashable,
    inner_cast: typing.Callable[[typing.Any], T],
    sequence_type: typing.Union[typing.Type[Seq], typing.Callable[..., Seq]] = list,
    keep_failures: bool = False,
    **kwargs,
) -> Seq:
    """
    Get a collection at the given key in the given mapping and cast all values to the inner cast, then wrap in
    a python collection `sequence_type`.

    Any failed casts will be omitted from the result.

    Args:
        mapping:
            the mapping to access.
        key:
            the key to access.
        inner_cast:
            the callable to cast each item with.
        sequence_type:
            the collection type to wrap the collection in.
        keep_failures:
            defaults to False. If True, any failed casts will be stored as their input value rather than being omitted.
        **kwargs:
            other kwargs to pass to the cast.

    Returns:
        A collection of `sequence_type`.
    """
    initial_items = mapping.get(key, _EMPTY_TUPLE)
    if keep_failures:
        items = (try_cast(item, inner_cast, item, **kwargs) for item in initial_items)
    else:
        items = (try_cast(item, inner_cast, _BAD_OBJECT, **kwargs) for item in initial_items)

    sequence = sequence_type(item for item in items if item is not _BAD_OBJECT)
    return sequence


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
