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
"""Component used to represent types of file to make it easier to upload."""

from __future__ import annotations

__all__ = ["BaseStream", "AsyncIteratorStream", "WebResourceStream", "FileStream", "ByteStream"]

import abc
import asyncio
import concurrent.futures
import functools
import http
import io
import os
import typing

import aiohttp

from hikari import errors


MAGIC_NUMBER: typing.Final[int] = 64 * 1024


class BaseStream(abc.ABC, typing.AsyncIterable[bytes]):
    """A data stream that can be uploaded in a message or downloaded.

    This is a wrapper for an async iterable of bytes.
    """

    filename: str
    """The name of the stream."""

    def __init__(self, filename: str) -> None:
        self.filename = filename

    async def read(self) -> bytes:
        """Return the entire contents of the data stream."""
        data = b""
        async for chunk in self:
            data += chunk
        return data


class AsyncIteratorStream(BaseStream):
    """A simple data stream that wraps an async iterable or async iterator.

    Parameters
    ----------
    filename : str
        The file name to use.
    obj : typing.AsyncIterator[bytes] OR typing.AsyncIterable[str]
        The async iterator/iterable of bytes to use.
    """

    def __init__(
        self, filename: str, obj: typing.Union[typing.AsyncIterator[bytes], typing.AsyncIterable[bytes]]
    ) -> None:
        super().__init__(filename)
        self._obj = obj

    async def __aiter__(self) -> typing.AsyncIterator[bytes]:

        if isinstance(self._obj, typing.AsyncIterator):
            iterator = self._obj
        else:
            iterator = self._obj.__aiter__()

        async for chunk in iterator:
            yield chunk


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
    """

    url: str
    """The URL of the resource."""

    def __init__(self, filename: str, url: str) -> None:
        super().__init__(filename)
        self.url = url

    async def __aiter__(self) -> typing.AsyncIterator[bytes]:
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


class FileStream(BaseStream):
    """Asynchronous reader for a local file.

    This takes one of two formats:

        FileStream("path/to/cat.png")

        FileStream("kitteh.png", "path/to/cat.png")

    Parameters
    ----------
    *args : (str, str OR os.PathLike) OR (str OR os.PathLike)
        Either two arguments, the first being the string file name and the
        second being the file path; or one argument which is the file path.

        If one argument is given, the file name is used for the upload.
    executor : concurrent.futures.Executor, optional
        An optional executor to run the IO operations in. If not specified, the
        default executor for this loop will
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
            super().__init__(os.path.basename(*args))
            self.path = args[0]
        else:
            name, path = args
            super().__init__(name)
            self.path = path
        self._executor = executor

    async def __aiter__(self) -> typing.AsyncIterator[bytes]:
        loop = asyncio.get_event_loop()
        fp = await loop.run_in_executor(self._executor, functools.partial(open, self.path, "rb"))
        try:
            while chunk := await loop.run_in_executor(self._executor, fp.read, MAGIC_NUMBER):
                yield chunk
        finally:
            await loop.run_in_executor(self._executor, fp.close)


class ByteStream(BaseStream):
    """A stream of raw bytes.

    Parameters
    ----------
    filename : str
        The name of the resource.
    data : bytes, bytearray, memoryview, str, io.BytesIO, io.StringIO
        The data to stream.
    """

    def __init__(
        self, filename: str, data: typing.Union[io.BytesIO, io.StringIO, str, bytes, bytearray, memoryview]
    ) -> None:
        super().__init__(filename)

        if isinstance(data, (io.BytesIO, io.StringIO)):
            data = data.read()

        if isinstance(data, str):
            data = bytes(data, "utf-8")
        elif isinstance(data, memoryview):
            data = data.tobytes()

        self.data = data

    async def __aiter__(self) -> typing.AsyncIterator[bytes]:
        for i in range(0, len(self.data), MAGIC_NUMBER):
            yield self.data[i : i + MAGIC_NUMBER]
