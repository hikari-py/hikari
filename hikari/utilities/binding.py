#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
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
"""Data binding utilities."""
from __future__ import annotations

__all__ = [
    "Headers",
    "Query",
    "JSONObject",
    "JSONArray",
    "JSONNull",
    "JSONBoolean",
    "JSONString",
    "JSONNumber",
    "JSONAny",
    "URLEncodedForm",
    "MultipartForm",
    "dump_json",
    "load_json",
    "JSONObjectBuilder",
    "cast_json_array",
]

import json
import typing

import aiohttp.typedefs

from hikari.models import bases
from hikari.utilities import unset

Headers = typing.Mapping[str, str]
"""HTTP headers."""

Query = typing.Dict[str, str]
"""HTTP query string."""

URLEncodedForm = aiohttp.FormData
"""Content of type application/x-www-form-encoded"""

MultipartForm = aiohttp.FormData
"""Content of type multipart/form-data"""

JSONString = str
"""A JSON string."""

JSONNumber = typing.Union[int, float]
"""A JSON numeric value."""

JSONBoolean = bool
"""A JSON boolean value."""

JSONNull = None
"""A null JSON value."""

# We cant include JSONArray and JSONObject in the definition as MyPY does not support
# recursive type definitions, sadly.
JSONObject = typing.Dict[JSONString, typing.Union[JSONString, JSONNumber, JSONBoolean, JSONNull, list, dict]]
"""A JSON object representation as a dict."""

JSONArray = typing.List[typing.Union[JSONString, JSONNumber, JSONBoolean, JSONNull, dict, list]]
"""A JSON array representation as a list."""

JSONAny = typing.Union[JSONString, JSONNumber, JSONBoolean, JSONNull, JSONArray, JSONObject]
"""Any JSON type."""

if typing.TYPE_CHECKING:

    def dump_json(_: typing.Union[JSONArray, JSONObject]) -> str:
        ...

    def load_json(_: str) -> typing.Union[JSONArray, JSONObject]:
        ...


else:
    dump_json = json.dumps
    """Convert a Python type to a JSON string."""

    load_json = json.loads
    """Convert a JSON string to a Python type."""


class StringMapBuilder(typing.Dict[str, str]):
    """Helper class used to quickly build query strings or header maps."""

    __slots__ = ()

    def __init__(self):
        super().__init__()

    def put(
        self,
        key: str,
        value: typing.Union[unset.Unset, typing.Any],
        conversion: typing.Optional[typing.Callable[[typing.Any], typing.Any]] = None,
    ) -> None:
        """Add a key and value to the string map.

        Parameters
        ----------
        key : str
            The string key.
        value : hikari.utilities.unset.Unset | typing.Any
            The value to set.
        conversion : typing.Callable[[typing.Any], typing.Any] | None
            An optional conversion to perform.

        !!! note
            The value will always be cast to a `str` before inserting it.
        """
        if not unset.is_unset(value):
            if conversion is not None:
                value = conversion(value)

            if value is True:
                value = "true"
            elif value is False:
                value = "false"
            elif value is None:
                value = "null"
            elif isinstance(value, bases.Unique):
                value = str(value.id)
            else:
                value = str(value)

            self[key] = value

    @classmethod
    def from_dict(cls, d: typing.Union[unset.Unset, typing.Dict[str, typing.Any]]) -> StringMapBuilder:
        """Build a query from an existing dict."""
        sb = cls()

        if unset.is_unset(d):
            return sb

        for k, v in d.items():
            sb.put(k, v)

        return sb


class JSONObjectBuilder(typing.Dict[JSONString, JSONAny]):
    """Helper class used to quickly build JSON objects from various values."""

    __slots__ = ()

    def __init__(self):
        super().__init__()

    def put(
        self,
        key: JSONString,
        value: typing.Any,
        conversion: typing.Optional[typing.Callable[[typing.Any], JSONAny]] = None,
    ) -> None:
        """Put a JSON value.

        If the value is unset, then it will not be stored.

        Parameters
        ----------
        key : JSONString
            The key to give the element.
        value : JSONType | typing.Any | hikari.utilities.unset.Unset
            The JSON type to put. This may be a non-JSON type if a conversion
            is also specified. This may alternatively be unset. In the latter
            case, nothing is performed.
        conversion : typing.Callable[[typing.Any], JSONType] | None
            Optional conversion to apply.
        """
        if not unset.is_unset(value):
            if conversion is not None:
                self[key] = conversion(value)
            else:
                self[key] = value

    def put_array(
        self,
        key: JSONString,
        values: typing.Union[unset.Unset, typing.Iterable[_T]],
        conversion: typing.Optional[typing.Callable[[_T], JSONAny]] = None,
    ) -> None:
        """Put a JSON array.

        If the value is unset, then it will not be stored.

        Parameters
        ----------
        key : JSONString
            The key to give the element.
        values : JSONType | typing.Any | hikari.utilities.unset.Unset
            The JSON types to put. This may be an iterable of non-JSON types if
            a conversion is also specified. This may alternatively be unset.
            In the latter case, nothing is performed.
        conversion : typing.Callable[[typing.Any], JSONType] | None
            Optional conversion to apply.
        """
        if not unset.is_unset(values):
            if conversion is not None:
                self[key] = [conversion(value) for value in values]
            else:
                self[key] = list(values)

    def put_snowflake(self, key: JSONString, value: typing.Union[unset.Unset, typing.SupportsInt, int]) -> None:
        """Put a snowflake.

        Parameters
        ----------
        key : JSONString
            The key to give the element.
        value : JSONType | hikari.utilities.unset.Unset
            The JSON type to put. This may alternatively be unset. In the latter
            case, nothing is performed.
        """
        if not unset.is_unset(value):
            self[key] = str(int(value))

    def put_snowflake_array(
        self, key: JSONString, values: typing.Union[unset.Unset, typing.Iterable[typing.SupportsInt, int]]
    ) -> None:
        """Put an array of snowflakes.

        Parameters
        ----------
        key : JSONString
            The key to give the element.
        values : typing.Iterable[typing.SupportsInt, int] | hikari.utilities.unset.Unset
            The JSON snowflakes to put. This may alternatively be unset. In the latter
            case, nothing is performed.
        """
        if not unset.is_unset(values):
            self[key] = [str(int(value)) for value in values]


_T = typing.TypeVar("_T", covariant=True)
_CT = typing.TypeVar("_CT", bound=typing.Collection, contravariant=True)


def cast_json_array(
    array: JSONArray, cast: typing.Callable[[JSONAny], _T], collection_type: typing.Type[_CT] = list
) -> _CT:
    """Cast a JSON array to a given collection type, casting each item."""
    return collection_type(cast(item) for item in array)
