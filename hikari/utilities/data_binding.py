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

__all__: typing.Final[typing.Sequence[str]] = [
    "Headers",
    "Query",
    "JSONObject",
    "JSONArray",
    "JSONAny",
    "URLEncodedForm",
    "MultipartForm",
    "ContentDisposition",
    "dump_json",
    "load_json",
    "JSONObjectBuilder",
    "cast_json_array",
]

import json
import typing

import aiohttp.client_reqrep
import aiohttp.typedefs
import multidict

from hikari.utilities import snowflake
from hikari.utilities import undefined

T = typing.TypeVar("T", covariant=True)

Headers = typing.Mapping[str, str]
"""Type hint for HTTP headers."""

Query = typing.Union[typing.Dict[str, str], multidict.MultiDict[str]]
"""Type hint for HTTP query string."""

URLEncodedForm = aiohttp.FormData
"""Type hint for content of type application/x-www-form-encoded."""

MultipartForm = aiohttp.FormData
"""Type hint for content of type multipart/form-data."""

ContentDisposition = aiohttp.client_reqrep.ContentDisposition
"""Type hint for content disposition information."""

# MyPy does not support recursive types yet. This has been ongoing for a long time, unfortunately.
# See https://github.com/python/typing/issues/182

JSONObject = typing.Dict[str, typing.Any]
"""Type hint for a JSON-decoded object representation as a mapping."""

JSONArray = typing.List[typing.Any]
"""Type hint for a JSON-decoded array representation as a sequence."""

JSONAny = typing.Union[str, int, float, bool, None, JSONArray, JSONObject]
"""Type hint for any valid JSON-decoded type."""

if typing.TYPE_CHECKING:

    def dump_json(_: typing.Union[JSONArray, JSONObject]) -> str:
        """Convert a Python type to a JSON string."""

    def load_json(_: typing.AnyStr) -> typing.Union[JSONArray, JSONObject]:
        """Convert a JSON string to a Python type."""


else:
    dump_json = json.dumps
    """Convert a Python type to a JSON string."""

    load_json = json.loads
    """Convert a JSON string to a Python type."""


@typing.final
class StringMapBuilder(multidict.MultiDict[str]):
    """Helper class used to quickly build query strings or header maps.

    This will consume any items that are not `hikari.utilities.undefined.UndefinedType`.
    If a value _is_ unspecified, it will be ignored when inserting it. This reduces
    the amount of boilerplate needed for generating the headers and query strings for
    low-level HTTP API interaction, amongst other things.

    !!! warn
        Because this subclasses `dict`, you should not use the
        index operator to set items on this object. Doing so will skip any
        form of validation on the type. Use the `put*` methods instead.
    """

    __slots__: typing.Sequence[str] = ()

    def __init__(self) -> None:
        super().__init__()

    def put(
        self,
        key: str,
        value: typing.Union[undefined.UndefinedType, typing.Any],
        /,
        *,
        conversion: typing.Optional[typing.Callable[[typing.Any], typing.Any]] = None,
    ) -> None:
        """Add a key and value to the string map.

        Parameters
        ----------
        key : str
            The string key.
        value : hikari.utilities.undefined.UndefinedType or typing.Any
            The value to set.
        conversion : typing.Callable[[typing.Any], typing.Any] or None
            An optional conversion to perform.

        !!! note
            The value will always be cast to a `str` before inserting it.

            `True` will be translated to `"true"`, `False` will be translated
            to `"false"`, and `None` will be translated to `"null"`.
        """
        if value is not undefined.UNDEFINED:
            if conversion is not None:
                value = conversion(value)

            if value is True:
                value = "true"
            elif value is False:
                value = "false"
            elif value is None:
                value = "null"
            elif isinstance(value, snowflake.Unique):
                value = str(value.id)
            else:
                value = str(value)

            # __setitem__ just overwrites the previous value.
            self.add(key, value)


@typing.final
class JSONObjectBuilder(typing.Dict[str, JSONAny]):
    """Helper class used to quickly build JSON objects from various values.

    If provided with any values that are `hikari.utilities.undefined.UndefinedType`,
    then these values will be ignored.

    This speeds up generation of JSON payloads for low level HTTP and websocket
    API interaction.

    !!! warn
        Because this subclasses `dict`, you should not use the
        index operator to set items on this object. Doing so will skip any
        form of validation on the type. Use the `put*` methods instead.
    """

    __slots__: typing.Sequence[str] = ()

    def __init__(self) -> None:
        super().__init__()

    def put(
        self,
        key: str,
        value: typing.Any,
        /,
        *,
        conversion: typing.Optional[typing.Callable[[typing.Any], JSONAny]] = None,
    ) -> None:
        """Put a JSON value.

        If the value is undefined, then it will not be stored.

        Parameters
        ----------
        key : str
            The key to give the element.
        value : JSONAny or typing.Any or hikari.utilities.undefined.UndefinedType
            The JSON type to put. This may be a non-JSON type if a conversion
            is also specified. This may alternatively be undefined. In the latter
            case, nothing is performed.
        conversion : typing.Callable[[typing.Any], JSONAny] or None
            Optional conversion to apply.
        """
        if value is not undefined.UNDEFINED:
            if conversion is not None:
                self[key] = conversion(value)
            else:
                self[key] = value

    def put_array(
        self,
        key: str,
        values: typing.Union[undefined.UndefinedType, typing.Iterable[T]],
        /,
        *,
        conversion: typing.Optional[typing.Callable[[T], JSONAny]] = None,
    ) -> None:
        """Put a JSON array.

        If the value is undefined, then it will not be stored.

        If provided, a conversion will be applied to each item.

        Parameters
        ----------
        key : str
            The key to give the element.
        values : JSONAny or Any or hikari.utilities.undefined.UndefinedType
            The JSON types to put. This may be an iterable of non-JSON types if
            a conversion is also specified. This may alternatively be undefined.
            In the latter case, nothing is performed.
        conversion : typing.Callable[[typing.Any], JSONType] or None
            Optional conversion to apply.
        """
        if values is not undefined.UNDEFINED:
            if conversion is not None:
                self[key] = [conversion(value) for value in values]
            else:
                self[key] = list(values)

    def put_snowflake(self, key: str, value: typing.Union[undefined.UndefinedType, snowflake.UniqueObject], /) -> None:
        """Put a key with a snowflake value into the builder.

        Parameters
        ----------
        key : str
            The key to give the element.
        value : JSONAny or hikari.utilities.undefined.UndefinedType
            The JSON type to put. This may alternatively be undefined. In the latter
            case, nothing is performed.
        """
        if value is not undefined.UNDEFINED:
            self[key] = str(int(value))

    def put_snowflake_array(
        self, key: str, values: typing.Union[undefined.UndefinedType, typing.Iterable[snowflake.UniqueObject]], /,
    ) -> None:
        """Put an array of snowflakes with the given key into this builder.

        If an undefined value is given, it is ignored.

        Each snowflake should be castable to an `int`.

        Parameters
        ----------
        key : str
            The key to give the element.
        values : typing.Iterable[typing.SupportsInt] or hikari.utilities.undefined.UndefinedType
            The JSON snowflakes to put. This may alternatively be undefined.
            In the latter case, nothing is performed.
        """
        if values is not undefined.UNDEFINED:
            self[key] = [str(int(value)) for value in values]


def cast_json_array(array: JSONArray, cast: typing.Callable[[typing.Any], T]) -> typing.List[T]:
    """Cast a JSON array to a given generic collection type.

    This will perform casts on each internal item individually.

    Note that

        >>> cast_json_array(raw_list, foo, bar)

    ...is equivalent to doing....

        >>> bar(foo(item) for item in raw_list)

    Parameters
    ----------
    array : JSONArray
        The raw JSON-decoded array.
    cast : typing.Callable[[JSONAny], T]
        The cast to apply to each item in the array. This should
        consume any valid JSON-decoded type and return the type
        corresponding to the generic type of the provided collection.

    Returns
    -------
    typing.List[T]
        The generated list.

    Example
    -------
    ```py
    >>> arr = [123, 456, 789, 123]
    >>> cast_json_array(arr, str)
    ["123", "456", "789", "123"]
    ```
    """
    return [cast(item) for item in array]
