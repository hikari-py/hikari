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
from __future__ import annotations

__all__ = []

import abc
import asyncio
import base64
import contextlib
import logging
import mimetypes
import os
import pathlib
import time
import typing
import urllib.parse

import aiohttp.client
import attr

from hikari.net import http_client
from hikari.utilities import klass

if typing.TYPE_CHECKING:
    import concurrent.futures

_LOGGER: typing.Final[logging.Logger] = klass.get_logger(__name__)
_MAGIC: typing.Final[int] = 50 * 1024
_FILE: typing.Final[str] = "file://"


def ensure_resource(url_or_resource: typing.Union[str, Resource]) -> Resource:
    """Given a resource or string, convert it to a valid resource as needed."""
    if isinstance(url_or_resource, Resource):
        return url_or_resource
    else:
        if url_or_resource.startswith(_FILE):
            return File(url_or_resource[len(_FILE):])
        return URL(url_or_resource)


def guess_mimetype_from_filename(name: str) -> typing.Optional[str]:
    """Guess the mimetype of an object given a filename.

    Returns
    -------
    str or None
        The closest guess to the given filename. May be `None` if
        no match was found.
    """
    return mimetypes.guess_type(name)


def guess_mimetype_from_data(data: bytes) -> typing.Optional[str]:
    if data.startswith(b"\211PNG\r\n\032\n"):
        return "image/png"
    elif data[6:].startswith((b"Exif", b"JFIF")):
        return "image/jpeg"
    elif data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    elif data.startswith(b"RIFF") and data[8:].startswith(b"WEBP"):
        return "image/webp"
    else:
        return None


def guess_file_extension(mimetype: str) -> typing.Optional[str]:
    return mimetypes.guess_extension(mimetype)


def generate_filename_from_details(
    *,
    mimetype: typing.Optional[str] = None,
    extension: typing.Optional[str] = None,
    data: typing.Optional[bytes] = None,
) -> str:
    if data is not None and mimetype is None:
        mimetype = guess_mimetype_from_data(data)

    if extension is None and mimetype is not None:
        extension = guess_file_extension(mimetype)

    if extension is None or extension == "":
        extension = ""
    elif not extension.startswith("."):
        extension = f".{extension}"

    return str(time.perf_counter_ns()) + extension


def to_data_uri(data: bytes, mimetype: typing.Optional[str]) -> str:
    if mimetype is None:
        mimetype = guess_mimetype_from_data(data)

        if mimetype is None:
            raise TypeError("Cannot infer mimetype from input data, specify it manually.")

    b64 = base64.b64encode(data).decode()
    return f"data:{mimetype};base64,{b64}"


@attr.s(auto_attribs=True, slots=True)
class AsyncReader(typing.AsyncIterable[bytes], abc.ABC):
    filename: str
    mimetype: typing.Optional[str]

    async def data_uri(self) -> str:
        return to_data_uri(await self.read(), self.mimetype)

    async def read(self) -> bytes:
        buff = bytearray()
        async for chunk in self:
            buff.extend(chunk)
        return buff


@attr.s(auto_attribs=True, slots=True)
class ByteReader(AsyncReader):
    data: bytes

    def __aiter__(self) -> typing.AsyncGenerator[typing.Any, bytes]:
        for i in range(0, len(self.data), _MAGIC):
            yield self.data[i : i + _MAGIC]


@attr.s(auto_attribs=True, slots=True)
class FileReader(AsyncReader):
    executor: typing.Optional[concurrent.futures.Executor]
    path: typing.Union[str, os.PathLike]
    loop: asyncio.AbstractEventLoop = attr.ib(factory=asyncio.get_running_loop)

    async def __aiter__(self) -> typing.AsyncGenerator[typing.Any, bytes]:
        fp = await self.loop.run_in_executor(self.executor, self._open, self.path)
        try:
            while True:
                chunk = await self.loop.run_in_executor(self.executor, self._read_chunk, fp, _MAGIC)
                yield chunk
                if len(chunk) < _MAGIC:
                    break
        finally:
            await self.loop.run_in_executor(self.executor, self._close, fp)

    @staticmethod
    def _read_chunk(fp: typing.IO[bytes], n: int = 10_000) -> bytes:
        return fp.read(n)

    @staticmethod
    def _open(path: typing.Union[str, os.PathLike]) -> typing.IO[bytes]:
        return open(path, "rb")

    @staticmethod
    def _close(fp: typing.IO[bytes]) -> None:
        fp.close()


@attr.s(auto_attribs=True, slots=True)
class WebReader(AsyncReader):
    stream: aiohttp.StreamReader
    uri: str
    status: int
    reason: str
    charset: typing.Optional[str]
    size: typing.Optional[int]

    async def read(self) -> bytes:
        return await self.stream.read()

    async def __aiter__(self) -> typing.AsyncGenerator[typing.Any, bytes]:
        while not self.stream.at_eof():
            chunk = await self.stream.readchunk()
            yield chunk[0]


@attr.s(auto_attribs=True)
class Resource(abc.ABC):
    @property
    @abc.abstractmethod
    def url(self) -> str:
        """The URL, if known."""

    @property
    @abc.abstractmethod
    def filename(self) -> typing.Optional[str]:
        """The filename, if known."""

    @abc.abstractmethod
    @contextlib.asynccontextmanager
    async def stream(self) -> AsyncReader:
        """Return an async iterable of bytes to stream."""


class RawBytes(Resource):
    def __init__(
        self,
        data: bytes,
        /,
        mimetype: typing.Optional[str] = None,
        filename: typing.Optional[str] = None,
        extension: typing.Optional[str] = None,
    ) -> None:
        self.data = data

        if filename is None:
            filename = generate_filename_from_details(mimetype=mimetype, extension=extension, data=data)
        elif mimetype is None:
            mimetype = guess_mimetype_from_filename(filename)

        if extension is None and mimetype is not None:
            extension = guess_file_extension(mimetype)

        if filename is None and mimetype is None:
            if extension is None:
                raise TypeError("Cannot infer data type details, please specify one of filetype, filename, extension")
            else:
                raise TypeError("Cannot infer data type details from extension. Please specify mimetype or filename")

        self._filename = filename
        self.mimetype: str = mimetype
        self.extension: typing.Optional[str] = extension

    @property
    def url(self) -> str:
        return to_data_uri(self.data, self.mimetype)

    @property
    def filename(self) -> typing.Optional[str]:
        return self._filename

    @contextlib.asynccontextmanager
    async def stream(self) -> AsyncReader:
        yield ByteReader(self.filename, self.mimetype, self.data)


class WebResource(Resource, abc.ABC):
    @contextlib.asynccontextmanager
    async def stream(self) -> WebReader:
        """Start streaming the content into memory by downloading it.

        You can use this to fetch the entire resource, parts of the resource,
        or just to view any metadata that may be provided.

        Examples
        --------
        Downloading an entire resource at once into memory:
        ```py
        async with obj.stream() as stream:
            data = await stream.read()
        ```
        Checking the metadata:
        ```py
        async with obj.stream() as stream:
            mimetype = stream.mimetype

        if mimetype is None:
            ...
        elif mimetype not in whitelisted_mimetypes:
            ...
        else:
            ...
        ```
        Fetching the data-uri of a resource:
        ```py
        async with obj.stream() as stream:
            data_uri = await stream.data_uri()
        ```

        Returns
        -------
        WebReader
            The download stream.

        Raises
        ------
        hikari.errors.BadRequest
            If a 400 is returned.
        hikari.errors.Unauthorized
            If a 401 is returned.
        hikari.errors.Forbidden
            If a 403 is returned.
        hikari.errors.NotFound
            If a 404 is returned.
        hikari.errors.ClientHTTPErrorResponse
            If any other 4xx is returned.
        hikari.errors.ServerHTTPErrorResponse
            If any other 5xx is returned.
        hikari.errors.HTTPErrorResponse
            If any other unexpected response code is returned.
        """

        async with aiohttp.ClientSession() as session:
            async with session.request("get", self.url, raise_for_status=False) as resp:
                if 200 <= resp.status < 400:
                    mimetype = None
                    filename = self.filename

                    if resp.content_disposition is not None:
                        mimetype = resp.content_disposition.type

                    if mimetype is None:
                        mimetype = resp.content_type

                    if filename is None:
                        if resp.content_disposition is not None:
                            filename = resp.content_disposition.filename

                        if filename is None:
                            filename = generate_filename_from_details(mimetype=mimetype)

                    yield WebReader(
                        stream=resp.content,
                        uri=str(resp.real_url),
                        status=resp.status,
                        reason=resp.reason,
                        filename=filename,
                        charset=resp.charset,
                        mimetype=mimetype,
                        size=resp.content_length,
                    )
                else:
                    await http_client.parse_error_response(resp)


@attr.s(auto_attribs=True)
class URL(WebResource):
    """A URL that represents a web resource."""

    _url: str

    @property
    def url(self) -> str:
        return self._url

    @property
    def filename(self) -> str:
        url = urllib.parse.urlparse(self._url)
        return os.path.basename(url.path)


class File(Resource):
    def __init__(
        self,
        path: typing.Union[str, os.PathLike],
        *,
        filename: typing.Optional[str] = None,
        executor: typing.Optional[concurrent.futures.Executor] = None,
    ) -> None:
        self.path = path
        self._filename = filename if filename is not None else os.path.basename(path)
        self.executor = executor

    @property
    def url(self) -> str:
        return pathlib.PurePath(self.path).as_uri()

    @property
    def filename(self) -> typing.Optional[str]:
        return self._filename

    @contextlib.asynccontextmanager
    async def stream(self) -> AsyncReader:
        yield FileReader(self.filename, None, self.executor, self.path)
