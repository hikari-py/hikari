# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
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
"""Data binding utilities."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "Headers",
    "Query",
    "JSONObject",
    "JSONArray",
    "JSONish",
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

from hikari import snowflakes
from hikari import undefined

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

JSONish = typing.Union[str, int, float, bool, None, JSONArray, JSONObject]
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

    This will consume any items that are not `hikari.undefined.UndefinedType`.
    If a value _is_ unspecified, it will be ignored when inserting it. This reduces
    the amount of boilerplate needed for generating the headers and query strings for
    low-level HTTP API interaction, amongst other things.

    !!! warn
        Because this subclasses `builtins.dict`, you should not use the
        index operator to set items on this object. Doing so will skip any
        form of validation on the type. Use the `put*` methods instead.
    """

    __slots__: typing.Sequence[str] = ()

    def __init__(self) -> None:
        super().__init__()

    def put(
        self,
        key: str,
        value: undefined.UndefinedOr[typing.Any],
        /,
        *,
        conversion: typing.Optional[typing.Callable[[typing.Any], typing.Any]] = None,
    ) -> None:
        """Add a key and value to the string map.

        Parameters
        ----------
        key : builtins.str
            The string key.
        value : hikari.undefined.UndefinedOr[typing.Any]
            The value to set.
        conversion : typing.Optional[typing.Callable[[typing.Any], typing.Any]]
            An optional conversion to perform.

        !!! note
            The value will always be cast to a `builtins.str` before inserting it.

            `builtins.True` will be translated to `"true"`, `builtins.False`
            ill be translated to `"false"`, and `builtins.None` will be
            translated to `"null"`.
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
            elif isinstance(value, snowflakes.Unique):
                value = str(value.id)
            else:
                value = str(value)

            # __setitem__ just overwrites the previous value.
            self.add(key, value)


@typing.final
class JSONObjectBuilder(typing.Dict[str, JSONish]):
    """Helper class used to quickly build JSON objects from various values.

    If provided with any values that are `hikari.undefined.UndefinedType`,
    then these values will be ignored.

    This speeds up generation of JSON payloads for low level HTTP and websocket
    API interaction.

    !!! warn
        Because this subclasses `builtins.dict`, you should not use the
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
        conversion: typing.Optional[typing.Callable[[typing.Any], JSONish]] = None,
    ) -> None:
        """Put a JSON value.

        If the value is undefined, then it will not be stored.

        Parameters
        ----------
        key : builtins.str
            The key to give the element.
        value : typing.Any or hikari.undefined.UndefinedType
            The JSON type to put. This may be a non-JSON type if a conversion
            is also specified. This may alternatively be undefined. In the latter
            case, nothing is performed.
        conversion : typing.Optional[typing.Callable[[typing.Any], JSONish]]
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
        values: undefined.UndefinedOr[typing.Iterable[T]],
        /,
        *,
        conversion: typing.Optional[typing.Callable[[T], JSONish]] = None,
    ) -> None:
        """Put a JSON array.

        If the value is undefined, then it will not be stored.

        If provided, a conversion will be applied to each item.

        Parameters
        ----------
        key : builtins.str
            The key to give the element.
        values : typing.Iterable[T] or hikari.undefined.UndefinedType
            The JSON types to put. This may be an iterable of non-JSON types if
            a conversion is also specified. This may alternatively be undefined.
            In the latter case, nothing is performed.
        conversion : typing.Optional[typing.Callable[[typing.Any], JSONType]]
            Optional conversion to apply.
        """
        if values is not undefined.UNDEFINED:
            if conversion is not None:
                self[key] = [conversion(value) for value in values]
            else:
                self[key] = list(values)

    def put_snowflake(
        self, key: str, value: undefined.UndefinedNoneOr[snowflakes.SnowflakeishOr[snowflakes.Unique]], /
    ) -> None:
        """Put a key with a snowflake value into the builder.

        Parameters
        ----------
        key : builtins.str
            The key to give the element.
        value : hikari.undefined.UndefinedNoneOr[hikari.snowflakes.SnowflakeishOr[hikari.snowflakes.Unique]]
            The JSON type to put. This may alternatively be undefined, in this
            case, nothing is performed. This may also be `builtins.None`, in this
            case the value isn't cast.
        """
        if value is not undefined.UNDEFINED and value is not None:
            self[key] = str(int(value))
        elif value is None:
            self[key] = value

    def put_snowflake_array(
        self, key: str, values: undefined.UndefinedOr[typing.Iterable[snowflakes.SnowflakeishOr[snowflakes.Unique]]], /,
    ) -> None:
        """Put an array of snowflakes with the given key into this builder.

        If an undefined value is given, it is ignored.

        Each snowflake should be castable to an `builtins.int`.

        Parameters
        ----------
        key : builtins.str
            The key to give the element.
        values : hikari.undefined.UndefinedOr[typing.Iterable[hikari.snowflakes.SnowflakeishOr[hikari.snowflakes.Unique]]]
            The JSON snowflakes to put. This may alternatively be undefined.
            In the latter case, nothing is performed.
        """  # noqa: E501 - Line too long
        if values is not undefined.UNDEFINED:
            self[key] = [str(int(value)) for value in values]


def cast_json_array(array: JSONArray, /, cast: typing.Callable[..., T], **kwargs: typing.Any) -> typing.List[T]:
    """Cast a JSON array to a given generic collection type.

    This will perform casts on each internal item individually.

    Note that

        >>> cast_json_array(raw_list, foo, bar="OK")

    ...is equivalent to doing....

        >>> [foo(item, bar="OK") for item in raw_list]

    Parameters
    ----------
    array : JSONArray
        The raw JSON-decoded array.
    cast : typing.Callable[[JSONish], T]
        The cast to apply to each item in the array. This should
        consume any valid JSON-decoded type and return the type
        corresponding to the generic type of the provided collection.
    **kwargs : typing.Any
        Extra keyword arguments to be passed during every call to cast.

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
    return [cast(item, **kwargs) for item in array]
