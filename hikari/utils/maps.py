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
Helper methods used for managing Mapping types.
"""
__all__ = ("get_from_map_as",)

import contextlib
import inspect
import typing

from hikari.utils import unspecified

T = typing.TypeVar("T")


def get_from_map_as(
    mapping: dict,
    key: typing.Any,
    cast: typing.Union[typing.Callable[[typing.Any], T], typing.Type[T]],
    default=None,
    *,
    default_on_error=False,
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
            If `True`, any error occuring whilst casting will be suppressed and the default value will be returned.
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
        with contextlib.suppress(Exception):
            return cast(raw)
        return default
    return cast(raw)


def put_if_specified(mapping, key, value) -> None:
    """Add a value to the mapping under the given key as long as the value is not :attr:`UNSPECIFIED`"""
    if value is not unspecified.UNSPECIFIED:
        mapping[key] = value
