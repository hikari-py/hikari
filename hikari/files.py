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
"""Components used to make uploading data simpler.

What should I use?
------------------

- **"I have a file I want to read."**
    Use `FileStream`.
- **"The data is on a website or network resource."**
    Use `WebResourceStream`.
- **"The data is in an `io.BytesIO` or `io.StringIO`."**
    Use `ByteStream`.
- **"The data is a `bytes`, `bytearray`, `memoryview`, or `str`."**
    Use `ByteStream`.
- **"The data is provided in an async iterable or async iterator."**
    Use `ByteStream`.
- **"The data is in some other format."**
    Convert the data to one of the above descriptions, or implement your
    own provider by subclassing `BaseStream`.

How exactly do I use each one of these?
---------------------------------------
Check the documentation for each implementation to see examples and caveats.

Why is this so complicated?
---------------------------
Unfortunately, Python deals with async file IO in a really bad way. This means
that it is very easy to let IO operations impede the performance of your
application. Using these implementations correctly will enable you to mostly
offset that overhead.

General implications of not using these implementations can include increased
memory usage, and the application becoming unresponsive during IO.
"""

from __future__ import annotations

__all__ = ["BaseStream", "ByteStream", "WebResourceStream", "FileStream"]

import abc
import asyncio
import concurrent.futures
import functools
import http
import inspect
import io
import os
import typing

import aiohttp

from hikari import errors
from hikari.internal import more_asyncio

# XXX: find optimal size.
MAGIC_NUMBER: typing.Final[int] = 128 * 1024


class BaseStream(abc.ABC, typing.AsyncIterable[bytes]):
    """A data stream that can be uploaded in a message or downloaded.

    This is a wrapper for an async iterable of bytes.

    Implementations should provide an `__aiter__` method yielding chunks
    to upload. Chunks can be any size that is non-zero, but for performance
    should be around 64-256KiB in size.

    Example
    -------
        class HelloWorldStream(BaseStream):
            def __init__(self):
                super().__init__("hello-world.txt")

            async def __aiter__(self):
                for byte in b"hello, world!":
                    yield byte

        stream = HelloWorldStream()

    You can also use an implementation to read contents into memory

        >>> stream = HelloWorldStream()
        >>> data = await stream.read()
        >>> print(data)
        b"hello, world!"

    """

    @property
    @abc.abstractmethod
    def filename(self) -> str:
        """Ffilename for the file object."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(filename={self.filename!r})"

    async def read(self) -> bytes:
        """Return the entire contents of the data stream."""
        data = io.BytesIO()
        async for chunk in self:
            data.write(chunk)
        return data.getvalue()


class ByteStream(BaseStream):
    """A simple data stream that wraps something that gives bytes.

    For any asyncio-compatible stream that is an async iterator, or for
    any in-memory data, you can use this to safely upload the information
    in an API call.

    Parameters
    ----------
    filename : str
        The file name to use.
    obj : byte-like provider
        A provider of bytes-like objects. See the following sections for
        what is acceptable.

    A byte-like provider can be one of the following types:

    - A bytes-like object (see below)
    - **`AsyncIterator[bytes-like object]`**
    - **`AsyncIterable[bytes-like object]`**
    - **`AsyncGenerator[Any, bytes-like object]`** - an async generator that
        yields bytes-like objects.
    - **`io.BytesIO`**
    - **`io.StringIO`**

    A bytes-like object can be one of the following types:

    - **bytes**
    - **bytearray**
    - **str**
    - **memoryview**

    !!! warning
        Do not pass blocking IO streams!

        You should not use this to wrap any IO or file-like object other
        Standard Python file objects perform blocking IO, which will block
        the event loop each time a chunk is read.

        To read a file, use `FileStream` instead. This will read the file
        object incrementally, reducing memory usage significantly.

        Passing a different type of file object to this class may result in
        undefined behaviour.

    !!! note
        String objects get treated as UTF-8.

        String objects will always be treated as UTF-8 encoded byte objects.
        If you need to use a different encoding, you should transform the
        data manually into a bytes object first and pass the result to this
        class.

    !!! note
        Additional notes about performance.

        If you pass a bytes-like object, `io.BytesIO`, or `io.StringIO`, the
        resource will be transformed internally into a bytes object, and
        read in larger chunks using an `io.BytesIO` under the hood. This is done
        to increase performance, as yielding individual bytes would be very
        slow.

        If you pass an async iterator/iterable/generator directly, this will not
        be collected into chunks. Whatever is yielded will be the chunk that is
        uploaded. This allows for bit-inception with async iterators provided
        by other libraries tidily.

    Examples
    --------
    Passing bytes-like objects:

        >>> # A stream of bytes.
        >>> stream = ByteStream("hello.txt", b"hello, world!")

        >>> # A stream from a bytearray.
        >>> stream = ByteStream("hello.txt", bytearray(b"hello, world!"))

        >>> # A stream from a string. This will be treated as UTF-8 always.
        >>> stream = ByteStream("hello.txt", "hello, world!")

        >>> # A stream from an io.BytesIO
        >>> obj = io.BytesIO(some_data)
        >>> stream = ByteStream("cat.png", obj)

        >>> # A stream from an io.StringIO
        >>> obj = io.StringIO(some_data)
        >>> stream = ByteStream("some_text.txt", obj)

    Passing async iterators, iterables:

        >>> stream = ByteStream("cat.png", some_async_iterator)

        >>> stream = ByteStream("cat.png", some_async_iterable)

        >>> stream = ByteStream("cat.png", some_asyncio_stream_reader)

    Passing async generators:

        >>> async def asyncgen():
        ...    yield b"foo "
        ...    yield b"bar "

        >>> # You can pass the generator directly...
        >>> stream = ByteStream("foobar.txt", asyncgen())

        >>> # Or, if the generator function takes no parameters, you can pass the
        >>> # function reference instead.
        >>> stream = ByteStream("foobar.txt", asyncgen)

    Using a third-party non-blocking library such as `aiofiles` is possible
    if you can pass an async iterator:

        >>> async with aiofiles.open("cat.png", "rb") as afp:
        ...    stream = ByteStream("cat.png", afp)

    !!! warning
        Async iterators are read lazily. You should ensure in the latter
        example that the `afp` is not closed before you use the stream in a
        request.

    !!! note
        `aiofiles` is not included with this library, and serves as an example
        only. You can make use of `FileStream` instead if you need to read a
        file using non-blocking IO.

    """

    ___VALID_BYTE_TYPES___ = typing.Union[
        bytes, bytearray, str, memoryview,
    ]

    ___VALID_TYPES___ = typing.Union[
        typing.AsyncGenerator[typing.Any, ___VALID_BYTE_TYPES___],
        typing.AsyncIterator[___VALID_BYTE_TYPES___],
        typing.AsyncIterable[___VALID_BYTE_TYPES___],
        ___VALID_BYTE_TYPES___,
        io.BytesIO,
        io.StringIO,
    ]

    _obj: typing.Union[
        typing.AsyncGenerator[typing.Any, ___VALID_BYTE_TYPES___],
        typing.AsyncIterable[typing.Any, ___VALID_BYTE_TYPES___],
    ]

    def __init__(self, filename: str, obj: ___VALID_TYPES___) -> None:
        self._filename = filename

        if inspect.isasyncgenfunction(obj):
            self._obj = obj()
            return

        if more_asyncio.is_async_iterable(obj):
            obj = obj.__aiter__()

        if more_asyncio.is_async_iterator(obj):
            self._obj = self._aiter_async_iterator(obj)
            return

        if inspect.isasyncgen(obj):
            self._obj = obj
            return

        if isinstance(obj, (io.StringIO, io.BytesIO)):
            obj = obj.getvalue()

        if isinstance(obj, (str, memoryview, bytearray)):
            obj = self._to_bytes(obj)

        if isinstance(obj, bytes):
            self._obj = self._aiter_bytes(obj)
            return

        raise TypeError(f"Expected bytes-like object or async generator, got {type(obj).__qualname__}")

    async def __aiter__(self) -> typing.AsyncGenerator[bytes]:
        async for chunk in self._obj:
            yield self._to_bytes(chunk)

    @property
    def filename(self) -> str:
        return self._filename

    async def _aiter_async_iterator(
        self, async_iterator: typing.AsyncGenerator[___VALID_BYTE_TYPES___]
    ) -> typing.AsyncIterator[bytes]:
        try:
            while True:
                yield self._to_bytes(await async_iterator.__anext__())
        except StopAsyncIteration:
            pass

    @staticmethod
    async def _aiter_bytes(bytes_: bytes) -> typing.AsyncGenerator[bytes]:
        stream = io.BytesIO(bytes_)
        while chunk := stream.read(MAGIC_NUMBER):
            yield chunk

    @staticmethod
    def _to_bytes(byte_like: ___VALID_BYTE_TYPES___) -> bytes:
        if isinstance(byte_like, str):
            return bytes(byte_like, "utf-8")
        if isinstance(byte_like, memoryview):
            return byte_like.tobytes()
        if isinstance(byte_like, bytearray):
            return bytes(byte_like)
        if isinstance(byte_like, bytes):
            return byte_like
        raise TypeError(f"Expected bytes-like chunks, got {type(byte_like).__qualname__}")


class WebResourceStream(BaseStream):
    """An async iterable of bytes that is represented by a web resource.

    Using this to upload an attachment will lazily load chunks and send them
    using bit-inception, vastly reducing the memory overhead by not storing the
    entire resource in memory before sending it.

    Parameters
    ----------
    filename : str
        The file name to use.
    url : str
        The URL to the resource to stream.

    Example
    -------
        >>> stream = WebResourceStream("cat-not-found.png", "https://http.cat/404")
    """

    url: str
    """The URL of the resource."""

    def __init__(self, filename: str, url: str) -> None:
        self._filename = filename
        self.url = url

    async def __aiter__(self) -> typing.AsyncGenerator[bytes]:
        async with aiohttp.request("GET", self.url) as response:
            if 200 <= response.status < 300:
                async for chunk in response.content:
                    yield chunk
                return

            raw_body = await response.read()

        real_url = str(response.real_url)

        if response.status == http.HTTPStatus.BAD_REQUEST:
            raise errors.BadRequest(real_url, response.headers, raw_body)
        if response.status == http.HTTPStatus.UNAUTHORIZED:
            raise errors.Unauthorized(real_url, response.headers, raw_body)
        if response.status == http.HTTPStatus.FORBIDDEN:
            raise errors.Forbidden(real_url, response.headers, raw_body)
        if response.status == http.HTTPStatus.NOT_FOUND:
            raise errors.NotFound(real_url, response.headers, raw_body)

        if 400 <= response.status < 500:
            cls = errors.ClientHTTPErrorResponse
        elif 500 <= response.status < 600:
            cls = errors.ServerHTTPErrorResponse
        else:
            cls = errors.HTTPErrorResponse

        raise cls(real_url, http.HTTPStatus(response.status), response.headers, raw_body)

    @property
    def filename(self) -> str:
        return self._filename


class FileStream(BaseStream):
    r"""Asynchronous reader for a local file.

    Parameters
    ----------
    filename : str, optional
        The custom file name to give the file when uploading it. May be
        omitted.
    path : str OR os.PathLike
        The path-like object that describes the file to upload.

    executor : concurrent.futures.Executor, optional
        An optional executor to run the IO operations in. If not specified, the
        default executor for this loop will be used instead.

    Examples
    --------
    Providing an explicit custom filename:

        >>> # UNIX/Linux/MacOS users
        >>> FileStream("kitteh.png", "path/to/cat.png")
        >>> FileStream("kitteh.png", "/mnt/cat-pictures/cat.png")

        >>> # Windows users
        >>> FileStream("kitteh.png", r"Pictures\Cat.png")
        >>> FileStream("kitteh.png", r"C:\Users\CatPerson\Pictures\Cat.png")

    Inferring the filename from the file path:

        >>> # UNIX/Linux/MacOS users
        >>> FileStream("path/to/cat.png")
        >>> FileStream("/mnt/cat-pictures/cat.png")

        >>> # Windows users
        >>> FileStream(r"Pictures\Cat.png")
        >>> FileStream(r"C:\Users\CatPerson\Pictures\Cat.png")

    !!! note
        This implementation only provides the basis for READING
        a file without blocking. For writing to files asynchronously,
        you should consider using a third-party library such as
        `aiofiles` or `aiofile`, or using an `Executor` instead.

    !!! warning
        While it is possible to use a ProcessPoolExecutor executor
        implementation with this class, use is discouraged. Process pools
        can only communicate using pipes or the pickle protocol, which
        makes the vanilla Python implementation unsuitable for use with
        async iterators. Since file handles cannot be pickled, the use
        of a ProcessPoolExecutor will result in the entire file being read
        in one chunk, which increases memory usage drastically.
    """

    @typing.overload
    def __init__(
        self,
        filename: str,
        path: typing.Union[str, os.PathLike],
        *,
        executor: typing.Optional[concurrent.futures.Executor] = None,
    ) -> None:
        ...

    @typing.overload
    def __init__(
        self, path: typing.Union[str, os.PathLike], /, *, executor: typing.Optional[concurrent.futures.Executor] = None,
    ) -> None:
        ...

    def __init__(self, *args, executor=None) -> None:
        if len(args) == 1:
            self._filename = os.path.basename(args[0])
            self.path = args[0]
        else:
            self._filename, self.path = args
        self._executor = executor

    def __aiter__(self) -> typing.AsyncGenerator[bytes]:
        loop = asyncio.get_event_loop()
        # We cant use a process pool in the same way we do a thread pool, as
        # we cannot pickle file objects that we pass between threads. This
        # method instead will stream the data via a pipe to us.
        if isinstance(self._executor, concurrent.futures.ProcessPoolExecutor):

            return self._processpool_strategy(loop)

        return self._threadpool_strategy(loop)

    @property
    def filename(self) -> str:
        return self._filename

    async def _threadpool_strategy(self, loop):
        fp = await loop.run_in_executor(self._executor, functools.partial(open, self.path, "rb"))
        try:
            while chunk := await loop.run_in_executor(self._executor, fp.read, MAGIC_NUMBER):
                yield chunk
        finally:
            await loop.run_in_executor(self._executor, fp.close)

    async def _processpool_strategy(self, loop):
        yield await loop.run_in_executor(self._executor, self._read_all, self.path)

    @staticmethod
    def _read_all(path):
        with open(path, "rb") as fp:
            return fp.read()
