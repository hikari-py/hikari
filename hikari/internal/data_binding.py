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
"""Data binding utilities."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "Headers",
    "Query",
    "JSONObject",
    "JSONArray",
    "JSONish",
    "default_json_loads",
    "default_json_dumps",
    "JSONObjectBuilder",
    "JSONPayload",
    "StringMapBuilder",
    "URLEncodedFormBuilder",
)

import typing

import aiohttp
import multidict

from hikari import errors
from hikari import files
from hikari import snowflakes
from hikari import undefined

if typing.TYPE_CHECKING:
    import concurrent.futures
    import contextlib

    T_co = typing.TypeVar("T_co", covariant=True)
    T = typing.TypeVar("T")

Headers = typing.Mapping[str, str]
"""Type hint for HTTP headers."""

Query = typing.Union[typing.Dict[str, str], multidict.MultiDict[str]]
"""Type hint for HTTP query string."""

# MyPy does not support recursive types yet. This has been ongoing for a long time, unfortunately.
# See https://github.com/python/typing/issues/182

JSONObject = typing.Mapping[str, typing.Any]
"""Type hint for a JSON-decoded object representation as a mapping."""

JSONArray = typing.Sequence[typing.Any]
"""Type hint for a JSON-decoded array representation as a sequence."""

JSONish = typing.Union[str, int, float, bool, None, JSONArray, JSONObject]
"""Type hint for any valid JSON-decoded type."""

Stringish = typing.Union[str, int, bool, undefined.UndefinedType, None, snowflakes.Unique]
"""Type hint for any valid that can be put in a StringMapBuilder"""

JSONEncoder = typing.Callable[[typing.Union[JSONArray, JSONObject]], bytes]
"""Type hint for hikari-compatible JSON encoders.

A hikari-compatible JSON encoder is one which will take in a JSON-ish object and output either [`str`][]
or [`bytes`][].
"""

JSONDecoder = typing.Callable[[typing.Union[str, bytes]], typing.Union[JSONArray, JSONObject]]
"""Type hint for hikari-compatible JSON decoder.

A hikari-compatible JSON decoder is one which will take either a [`str`][] or [`bytes`][] and outputs
the JSON-ish object, as well as raises a [`ValueError`][] on an incorrect JSON payload being passed in.
"""

_StringMapBuilderArg = typing.Union[
    typing.Mapping[str, str], multidict.MultiMapping[str], typing.Iterable[typing.Tuple[str, str]]
]

_APPLICATION_OCTET_STREAM: typing.Final[str] = "application/octet-stream"
_JSON_CONTENT_TYPE: typing.Final[str] = "application/json"
_BINARY: typing.Final[str] = "binary"
_UTF_8: typing.Final[str] = "utf-8"

default_json_dumps: JSONEncoder
"""Default json encoder to use."""

default_json_loads: JSONDecoder
"""Default json decoder to use."""

try:
    import orjson

    default_json_dumps = orjson.dumps
    default_json_loads = orjson.loads
except ModuleNotFoundError:
    import json

    _json_separators = (",", ":")

    def default_json_dumps(obj: typing.Union[JSONArray, JSONObject]) -> bytes:
        """Encode a JSON object to a [`str`][]."""
        return json.dumps(obj, separators=_json_separators).encode(_UTF_8)

    default_json_loads = json.loads


@typing.final
class JSONPayload(aiohttp.BytesPayload):
    """A JSON payload to use in an aiohttp request."""

    def __init__(self, value: typing.Any, dumps: JSONEncoder = default_json_dumps) -> None:
        super().__init__(dumps(value), content_type=_JSON_CONTENT_TYPE, encoding=_UTF_8)


@typing.final
class URLEncodedFormBuilder:
    """Helper class to generate [`aiohttp.FormData`][]."""

    __slots__: typing.Sequence[str] = ("_fields", "_resources")

    def __init__(self) -> None:
        self._fields: typing.List[typing.Tuple[str, typing.Union[str, bytes], typing.Optional[str]]] = []
        self._resources: typing.List[typing.Tuple[str, files.Resource[files.AsyncReader]]] = []

    def add_field(
        self, name: str, data: typing.Union[str, bytes], *, content_type: typing.Optional[str] = None
    ) -> None:
        self._fields.append((name, data, content_type))

    def add_resource(self, name: str, resource: files.Resource[files.AsyncReader]) -> None:
        self._resources.append((name, resource))

    async def build(
        self, stack: contextlib.AsyncExitStack, executor: typing.Optional[concurrent.futures.Executor] = None
    ) -> aiohttp.FormData:
        form = aiohttp.FormData()

        for field in self._fields:
            form.add_field(field[0], field[1], content_type=field[2], content_transfer_encoding=_BINARY)

        for name, resource in self._resources:
            stream = await stack.enter_async_context(resource.stream(executor=executor))
            mimetype = stream.mimetype or _APPLICATION_OCTET_STREAM
            form.add_field(name, stream, filename=stream.filename, content_type=mimetype)

        return form


@typing.final
class StringMapBuilder(multidict.MultiDict[str]):
    """Helper class used to quickly build query strings or header maps.

    This will consume any items that are not [`hikari.undefined.UNDEFINED`][].
    If a value is unspecified, it will be ignored when inserting it. This reduces
    the amount of boilerplate needed for generating the headers and query strings for
    low-level HTTP API interaction, amongst other things.

    !!! warning
        Because this subclasses [`dict`][], you should not use the
        index operator to set items on this object. Doing so will skip any
        form of validation on the type. Use the [put*][] methods instead.
    """

    __slots__: typing.Sequence[str] = ()

    def __init__(self, arg: _StringMapBuilderArg = (), **kwargs: str) -> None:
        # We have to allow arguments to be passed to the init here otherwise the inherited copy behaviour from
        # multidict.MultiDict fails.
        super().__init__(arg, **kwargs)

    @typing.overload
    def put(self, key: str, value: Stringish, /) -> None: ...

    @typing.overload
    def put(
        self, key: str, value: undefined.UndefinedOr[T_co], /, *, conversion: typing.Callable[[T_co], Stringish]
    ) -> None: ...

    def put(
        self,
        key: str,
        value: undefined.UndefinedOr[typing.Any],
        /,
        *,
        conversion: typing.Optional[typing.Callable[[typing.Any], typing.Any]] = None,
    ) -> None:
        """Add a key and value to the string map.

        !!! note
            The value will always be cast to a [`str`][] before inserting it.
            [`True`][] will be translated to `"true"`, [`False`][] will be
            translated to `"false"`, and [`None`][] will be translated to
            `"null"`.

        Parameters
        ----------
        key : str
            The string key.
        value : hikari.undefined.UndefinedOr[typing.Any]
            The value to set.

        Other Parameters
        ----------------
        conversion : typing.Optional[typing.Callable[[typing.Any], typing.Any]]
            An optional conversion to perform.
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

    If provided with any values that are [`hikari.undefined.UNDEFINED`][],
    then these values will be ignored.

    This speeds up generation of JSON payloads for low level HTTP and websocket
    API interaction.

    !!! warning
        Because this subclasses [`dict`][], you should not use the
        index operator to set items on this object. Doing so will skip any
        form of validation on the type. Use the [put*][] methods instead.
    """

    __slots__: typing.Sequence[str] = ()

    def __init__(self) -> None:
        # Only allow use of empty constructor here.
        super().__init__()

    @typing.overload
    def put(self, key: str, value: undefined.UndefinedNoneOr[JSONish], /) -> None: ...

    @typing.overload
    def put(
        self, key: str, value: undefined.UndefinedNoneOr[T_co], /, *, conversion: typing.Callable[[T_co], JSONish]
    ) -> None: ...

    def put(
        self,
        key: str,
        value: undefined.UndefinedNoneOr[typing.Any],
        /,
        *,
        conversion: typing.Optional[typing.Callable[[typing.Any], JSONish]] = None,
    ) -> None:
        """Put a JSON value.

        If the value is [`hikari.undefined.UNDEFINED`][] it will not be stored.

        Parameters
        ----------
        key : str
            The key to give the element.
        value : hikari.undefined.UndefinedOr[typing.Any]
            The JSON type to put. This may be a non-JSON type if a conversion
            is also specified. This may alternatively be undefined. In the latter
            case, nothing is performed.

        Other Parameters
        ----------------
        conversion : typing.Optional[typing.Callable[[typing.Any], JSONish]]
            The optional conversion to apply.
        """
        if value is undefined.UNDEFINED:
            return

        if conversion is None or value is None:
            self[key] = value
        else:
            self[key] = conversion(value)

    @typing.overload
    def put_array(self, key: str, values: undefined.UndefinedOr[typing.Iterable[JSONish]], /) -> None: ...

    @typing.overload
    def put_array(
        self,
        key: str,
        values: undefined.UndefinedOr[typing.Iterable[T_co]],
        /,
        *,
        conversion: typing.Callable[[T_co], JSONish],
    ) -> None: ...

    def put_array(
        self,
        key: str,
        values: undefined.UndefinedOr[typing.Iterable[typing.Any]],
        /,
        *,
        conversion: typing.Optional[typing.Callable[[typing.Any], JSONish]] = None,
    ) -> None:
        """Put a JSON array.

        If the value is [`hikari.undefined.UNDEFINED`][] it will not be stored.

        If provided, a conversion will be applied to each item.

        Parameters
        ----------
        key : str
            The key to give the element.
        values : hikari.undefined.UndefinedOr[typing.Iterable[T_co]]
            The JSON types to put. This may be an iterable of non-JSON types if
            a conversion is also specified. This may alternatively be undefined.
            In the latter case, nothing is performed.

        Other Parameters
        ----------------
        conversion : typing.Optional[typing.Callable[[typing.Any], JSONType]]
            The optional conversion to apply.
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

        If the value is [`hikari.undefined.UNDEFINED`][] it will not be stored.

        Parameters
        ----------
        key : str
            The key to give the element.
        value : hikari.undefined.UndefinedNoneOr[hikari.snowflakes.SnowflakeishOr[hikari.snowflakes.Unique]]
            The JSON type to put. This may alternatively be undefined, in this
            case, nothing is performed. This may also be [`None`][], in this
            case the value isn't cast.
        """
        if value is not undefined.UNDEFINED and value is not None:
            self[key] = str(int(value))
        elif value is None:
            self[key] = value

    def put_snowflake_array(
        self, key: str, values: undefined.UndefinedOr[typing.Iterable[snowflakes.SnowflakeishOr[snowflakes.Unique]]], /
    ) -> None:
        """Put an array of snowflakes with the given key into this builder.

        If the value is [`hikari.undefined.UNDEFINED`][] it will not be stored.

        Each snowflake should be castable to an [`int`][].

        Parameters
        ----------
        key : str
            The key to give the element.
        values : hikari.undefined.UndefinedOr[typing.Iterable[hikari.snowflakes.SnowflakeishOr[hikari.snowflakes.Unique]]]
            The JSON snowflakes to put. This may alternatively be undefined.
            In the latter case, nothing is performed.
        """
        if values is not undefined.UNDEFINED:
            self[key] = [str(int(value)) for value in values]


def cast_variants_array(cast: typing.Callable[[T_co], T], raw_values: typing.Iterable[T_co], /) -> typing.List[T]:
    """Cast an array of enum variants while ignoring unrecognised variant types.

    Parameters
    ----------
    cast : typing.Callable[[T_co], T]
        Callback to cast each variant to.

        This will ignore any variants which raises
        [`hikari.errors.UnrecognisedEntityError`][] on cast.
    raw_values : typing.Iterable[T_co]
        Iterable of the raw values to cast.

    Returns
    -------
    typing.List[T]
        A list of the casted variants (with any unrecognised types ignored).
    """
    results: typing.List[T] = []

    for value in raw_values:
        try:
            results.append(cast(value))

        except errors.UnrecognisedEntityError:
            pass

    return results
