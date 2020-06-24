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
"""Utilities and classes for interacting with files and web resources."""

from __future__ import annotations

__all__ = [
    "ensure_resource",
    "AsyncReader",
    "ByteReader",
    "FileReader",
    "WebReader",
    "AsyncReaderContextManager",
    "Resource",
    "Bytes",
    "File",
    "WebResource",
    "URL",
]

import abc
import asyncio
import base64
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

if typing.TYPE_CHECKING:
    import concurrent.futures
    import types

_LOGGER: typing.Final[logging.Logger] = logging.getLogger(__name__)
_MAGIC: typing.Final[int] = 50 * 1024


@typing.overload
def ensure_resource(url_or_resource: None, /) -> None:
    """Given None, return None."""


@typing.overload
def ensure_resource(url_or_resource: str, /) -> Resource:
    """Given a string, convert it to a resource."""


@typing.overload
def ensure_resource(url_or_resource: Resource, /) -> Resource:
    """Given a resource, return it."""


def ensure_resource(url_or_resource: typing.Union[None, str, Resource], /) -> typing.Optional[Resource]:
    """Given a resource or string, convert it to a valid resource as needed.

    Parameters
    ----------
    url_or_resource : None or str or Resource
        The item to convert. If the item is `None`, then `None` is returned.
        Likewise if a `Resource` is passed, it is simply returned again.
        Anything else is converted to a `Resource` first.

    Returns
    -------
    Resource or None
        The resource to use, or `None` if `None` was input.
    """
    if isinstance(url_or_resource, Resource):
        return url_or_resource

    if url_or_resource is None:
        return None

    if url_or_resource.startswith(("https://", "http://")):
        return URL(url_or_resource)

    path = pathlib.Path(url_or_resource)
    return File(path, path.name)


def guess_mimetype_from_filename(name: str, /) -> typing.Optional[str]:
    """Guess the mimetype of an object given a filename.

    Parameters
    ----------
    name : bytes
        The filename to inspect.

    Returns
    -------
    str or None
        The closest guess to the given filename. May be `None` if
        no match was found.
    """
    guess, _ = mimetypes.guess_type(name)
    return guess


def guess_mimetype_from_data(data: bytes, /) -> typing.Optional[str]:
    """Guess the mimetype of some data from the header.

    !!! warning
        This function only detects valid image headers that Discord allows
        the use of. Anything else will go undetected.

    Parameters
    ----------
    data : bytes
        The byte content to inspect.

    Returns
    -------
    str or None
        The mimetype, if it was found. If the header is unrecognised, then
        `None` is returned.
    """
    if data.startswith(b"\211PNG\r\n\032\n"):
        return "image/png"
    if data[6:].startswith((b"Exif", b"JFIF")):
        return "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:].startswith(b"WEBP"):
        return "image/webp"
    return None


def guess_file_extension(mimetype: str) -> typing.Optional[str]:
    """Guess the file extension for a given mimetype.

    Parameters
    ----------
    mimetype : str
        The mimetype to guess the extension for.

    Example
    -------
    ```py
    >>> guess_file_extension("image/png")
    ".png"
    ```

    Returns
    -------
    str or None
        The file extension, prepended with a `.`. If no match was found,
        return `None`.
    """
    return mimetypes.guess_extension(mimetype)


def generate_filename_from_details(
    *,
    mimetype: typing.Optional[str] = None,
    extension: typing.Optional[str] = None,
    data: typing.Optional[bytes] = None,
) -> str:
    """Given optional information about a resource, generate a filename.

    Parameters
    ----------
    mimetype : str or None
        The mimetype of the content, or `None` if not known.
    extension : str or None
        The file extension to use, or `None` if not known.
    data : bytes or None
        The data to inspect, or `None` if not known.

    Returns
    -------
    str
        A generated quasi-unique filename.
    """
    if data is not None and mimetype is None:
        mimetype = guess_mimetype_from_data(data)

    if extension is None and mimetype is not None:
        extension = guess_file_extension(mimetype)

    if not extension:
        extension = ""
    elif not extension.startswith("."):
        extension = f".{extension}"

    return str(time.perf_counter_ns()) + extension


def to_data_uri(data: bytes, mimetype: typing.Optional[str]) -> str:
    """Convert the data and mimetype to a data URI.

    Parameters
    ----------
    data : bytes
        The data to encode as base64.
    mimetype : str or None
        The mimetype, or `None` if we should attempt to guess it.

    Returns
    -------
    str
        A data URI string.
    """
    if mimetype is None:
        mimetype = guess_mimetype_from_data(data)

        if mimetype is None:
            raise TypeError("Cannot infer mimetype from input data, specify it manually.")

    b64 = base64.b64encode(data).decode()
    return f"data:{mimetype};base64,{b64}"


@attr.s(auto_attribs=True, slots=True)
class AsyncReader(typing.AsyncIterable[bytes], abc.ABC):
    """Protocol for reading a resource asynchronously using bit inception.

    This supports being used as an async iterable, although the implementation
    detail is left to each implementation of this class to define.
    """

    filename: str
    """The filename of the resource."""

    mimetype: typing.Optional[str]
    """The mimetype of the resource. May be `None` if not known."""

    async def data_uri(self) -> str:
        """Fetch the data URI.

        This reads the entire resource.
        """
        return to_data_uri(await self.read(), self.mimetype)

    async def read(self) -> bytes:
        """Read the rest of the resource and return it in a `bytes` object."""
        buff = bytearray()
        async for chunk in self:
            buff.extend(chunk)
        return buff


ReaderImplT = typing.TypeVar("ReaderImplT", bound=AsyncReader)


@attr.s(auto_attribs=True, slots=True)
class ByteReader(AsyncReader):
    """Asynchronous file reader that operates on in-memory data."""

    data: bytes
    """The data that will be yielded in chunks."""

    async def __aiter__(self) -> typing.AsyncGenerator[typing.Any, bytes]:
        for i in range(0, len(self.data), _MAGIC):
            yield self.data[i : i + _MAGIC]  # noqa: E203


@attr.s(auto_attribs=True, slots=True)
class WebReader(AsyncReader):
    """Asynchronous reader to use to read data from a web resource."""

    stream: aiohttp.StreamReader
    """The `aiohttp.StreamReader` to read the content from."""

    url: str
    """The URL being read from."""

    status: int
    """The initial HTTP response status."""

    reason: str
    """The HTTP response status reason."""

    charset: typing.Optional[str]
    """Optional character set information, if known."""

    size: typing.Optional[int]
    """The size of the resource, if known."""

    head_only: bool
    """If `True`, then only the HEAD was requested.

    In this case, neither `__aiter__` nor `read` would return anything other
    than an empty byte string.
    """

    async def read(self) -> bytes:
        return b"" if self.head_only else await self.stream.read()

    async def __aiter__(self) -> typing.AsyncGenerator[typing.Any, bytes]:
        if self.head_only:
            yield b""
        else:
            while not self.stream.at_eof():
                chunk, _ = await self.stream.readchunk()
                yield chunk


@attr.s(auto_attribs=True, slots=True)
class FileReader(AsyncReader):
    """Asynchronous file reader that reads a resource from local storage."""

    executor: typing.Optional[concurrent.futures.Executor]
    """The associated `concurrent.futures.Executor` to use for blocking IO."""

    path: typing.Union[str, pathlib.Path]
    """The path to the resource to read."""

    loop: asyncio.AbstractEventLoop = attr.ib(factory=asyncio.get_running_loop)
    """The event loop to use."""

    async def __aiter__(self) -> typing.AsyncGenerator[typing.Any, bytes]:
        path = self.path
        if isinstance(path, pathlib.Path):
            path = await self.loop.run_in_executor(self.executor, self._expand, self.path)

        fp = await self.loop.run_in_executor(self.executor, self._open, path)

        try:
            while True:
                chunk = await self.loop.run_in_executor(self.executor, self._read_chunk, fp, _MAGIC)
                yield chunk
                if len(chunk) < _MAGIC:
                    break

        finally:
            await self.loop.run_in_executor(self.executor, self._close, fp)

    @staticmethod
    def _expand(path: pathlib.Path) -> pathlib.Path:
        # .expanduser is Platform dependent. Will expand stuff like ~ to /home/<user> on posix.
        # .resolve will follow symlinks and what-have-we to translate stuff like `..` to proper paths.
        return path.expanduser().resolve()

    @staticmethod
    @typing.final
    def _read_chunk(fp: typing.IO[bytes], n: int = 10_000) -> bytes:
        return fp.read(n)

    @staticmethod
    def _open(path: typing.Union[str, os.PathLike]) -> typing.IO[bytes]:
        return open(path, "rb")

    @staticmethod
    def _close(fp: typing.IO[bytes]) -> None:
        fp.close()


class AsyncReaderContextManager(typing.Generic[ReaderImplT]):
    """Context manager that returns a reader."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    async def __aenter__(self) -> ReaderImplT:
        ...

    @abc.abstractmethod
    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        ...


@typing.final
class _NoOpAsyncReaderContextManagerImpl(typing.Generic[ReaderImplT], AsyncReaderContextManager[ReaderImplT]):
    __slots__: typing.Sequence[str] = ("impl",)

    def __init__(self, impl: ReaderImplT) -> None:
        self.impl = impl

    async def __aenter__(self) -> ReaderImplT:
        return self.impl

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        pass


@typing.final
class _WebReaderAsyncReaderContextManagerImpl(AsyncReaderContextManager[WebReader]):
    __slots__: typing.Sequence[str] = ("_web_resource", "_head_only", "_client_response_ctx", "_client_session")

    def __init__(self, web_resource: WebResource, head_only: bool) -> None:
        self._web_resource = web_resource
        self._head_only = head_only
        self._client_session: aiohttp.ClientSession = NotImplemented
        self._client_response_ctx: typing.AsyncContextManager = NotImplemented

    async def __aenter__(self) -> WebReader:
        client_session = aiohttp.ClientSession()

        method = "HEAD" if self._head_only else "GET"

        ctx = client_session.request(method, self._web_resource.url, raise_for_status=False)

        try:
            resp: aiohttp.ClientResponse = await ctx.__aenter__()

            if 200 <= resp.status < 400:
                mimetype = None
                filename = self._web_resource.filename

                if resp.content_disposition is not None:
                    mimetype = resp.content_disposition.type

                if mimetype is None:
                    mimetype = resp.content_type

                self._client_response_ctx = ctx
                self._client_session = client_session

                return WebReader(
                    stream=resp.content,
                    url=str(resp.real_url),
                    status=resp.status,
                    reason=str(resp.reason),
                    filename=filename,
                    charset=resp.charset,
                    mimetype=mimetype,
                    size=resp.content_length,
                    head_only=self._head_only,
                )
            else:
                raise await http_client.generate_error_response(resp)

        except Exception as ex:
            await ctx.__aexit__(type(ex), ex, ex.__traceback__)
            await client_session.close()
            raise

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        await self._client_response_ctx.__aexit__(exc_type, exc, exc_tb)
        await self._client_session.close()


class Resource(typing.Generic[ReaderImplT], abc.ABC):
    """Base for any uploadable or downloadable representation of information.

    These representations can be streamed using bit inception for performance,
    which may result in significant decrease in memory usage for larger
    resources.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def url(self) -> str:
        """URL of the resource."""

    @property
    @abc.abstractmethod
    def filename(self) -> str:
        """Filename of the resource."""

    @abc.abstractmethod
    def stream(
        self, *, executor: typing.Optional[concurrent.futures.Executor] = None, head_only: bool = False,
    ) -> AsyncReaderContextManager[ReaderImplT]:
        """Produce a stream of data for the resource.

        Parameters
        ----------
        executor : concurrent.futures.Executor or None
            The executor to run in for blocking operations.
            If `None`, then the default executor is used for the current
            event loop.
        head_only : bool
            Defaults to `False`. If `True`, then the implementation may
            only retrieve HEAD information if supported. This currently
            only has any effect for web requests.

        Returns
        -------
        AsyncReaderContextManager[AsyncReader]
            An async iterable of bytes to stream.
        """

    def __str__(self) -> str:
        return self.url

    def __repr__(self) -> str:
        return f"{type(self).__name__}(url={self.url!r}, filename={self.filename!r})"

    def __eq__(self, other: typing.Any) -> bool:
        if isinstance(other, Resource):
            return self.url == other.url
        return False

    def __hash__(self) -> int:
        return hash((self.__class__, self.url))


class Bytes(Resource[ByteReader]):
    """Representation of in-memory data to upload.

    Parameters
    ----------
    data : bytes
        The raw data.
    mimetype : str or None
        The mimetype, or `None` if you do not wish to specify this.
    filename : str or None
        The filename to use, or `None` if one should be generated as needed.
    extension : str or None
        The file extension to use, or `None` if one should be determined
        manually as needed.

    !!! note
        You only need to provide one of `mimetype`, `filename`, or `extension`.
        The other information will be determined using Python's `mimetypes`
        module.

        If none of these three are provided, then a crude guess may be
        made successfully for specific image types. If no file format
        information can be calculated, then the resource will fail during
        uploading.
    """

    __slots__: typing.Sequence[str] = ("data", "_filename", "mimetype", "extension")

    data: bytes
    """The raw data to upload."""

    mimetype: typing.Optional[str]
    """The provided mimetype, if specified. Otherwise `None`."""

    extension: typing.Optional[str]
    """The provided file extension, if specified. Otherwise `None`."""

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

        if mimetype is None:
            # TODO: should I just default to application/octet-stream here?
            if extension is None:
                raise TypeError("Cannot infer data type details, please specify a mimetype or an extension")
            raise TypeError("Cannot infer data type details from extension. Please specify a mimetype")

        self._filename = filename
        self.mimetype = mimetype
        self.extension = extension

    @property
    def url(self) -> str:
        return f"attachment://{self.filename}"

    @property
    def filename(self) -> str:
        return self._filename

    def stream(
        self, *, executor: typing.Optional[concurrent.futures.Executor] = None, head_only: bool = False,
    ) -> AsyncReaderContextManager[ByteReader]:
        """Start streaming the content in chunks.

        Parameters
        ----------
        executor : concurrent.futures.Executor or None
            Not used. Provided only to match the underlying interface.
        head_only : bool
            Not used. Provided only to match the underlying interface.

        Returns
        -------
        AsyncReaderContextManager[ByteReader]
            An async context manager that when entered, produces the
            data stream.
        """
        return _NoOpAsyncReaderContextManagerImpl(ByteReader(self.filename, self.mimetype, self.data))


class WebResource(Resource[WebReader], abc.ABC):
    """Base class for a resource that resides on the internet.

    The logic for identifying this resource is left to each implementation
    to define.

    !!! info
        For a usable concrete implementation, use `URL` instead.

    !!! note
        Some components may choose to not upload this resource directly and
        instead simply refer to the URL as needed. The main place this will
        occur is within embeds.

        If you need to re-upload the resource, you should download it into
        a `Bytes` and pass that instead in these cases.
    """

    __slots__: typing.Sequence[str] = ()

    def stream(
        self, *, executor: typing.Optional[concurrent.futures.Executor] = None, head_only: bool = False,
    ) -> AsyncReaderContextManager[WebReader]:
        """Start streaming the content into memory by downloading it.

        You can use this to fetch the entire resource, parts of the resource,
        or just to view any metadata that may be provided.

        Parameters
        ----------
        executor : concurrent.futures.Executor or None
            Not used. Provided only to match the underlying interface.
        head_only : bool
            Defaults to `False`. If `True`, then the implementation may
            only retrieve HEAD information if supported. This currently
            only has any effect for web requests.

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
        AsyncReaderContextManager[WebReader]
            An async context manager that when entered, produces the
            data stream.

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
        return _WebReaderAsyncReaderContextManagerImpl(self, head_only)


@typing.final
class URL(WebResource):
    """A URL that represents a web resource.

    Parameters
    ----------
    url : str
        The URL of the resource.

    !!! note
        Some components may choose to not upload this resource directly and
        instead simply refer to the URL as needed. The main place this will
        occur is within embeds.

        If you need to re-upload the resource, you should download it into
        a `Bytes` and pass that instead in these cases.
    """

    __slots__: typing.Sequence[str] = ("_url",)

    def __init__(self, url: str) -> None:
        self._url = url

    @property
    def url(self) -> str:
        return self._url

    @property
    def filename(self) -> str:
        url = urllib.parse.urlparse(self._url)
        return os.path.basename(url.path)


class File(Resource[FileReader]):
    """A resource that exists on the local machine's storage to be uploaded.

    Parameters
    ----------
    path : str or os.PathLike or pathlib.Path
        The path to use.

        !!! note
            If passing a `pathlib.Path`, this must not be a `pathlib.PurePath`
            directly, as it will be used to expand tokens such as `~` that
            denote the home directory, and `..` for relative paths.

            This will all be performed as required in an executor to prevent
            blocking the event loop.

    filename : str or None
        The filename to use. If this is `None`, the name of the file is taken
        from the path instead.
    """

    __slots__: typing.Sequence[str] = ("path", "_filename")

    path: typing.Union[str, pathlib.Path]
    _filename: typing.Optional[str]

    def __init__(self, path: typing.Union[str, pathlib.Path], filename: typing.Optional[str] = None) -> None:
        self.path = path
        self._filename = filename

    @property
    @typing.final
    def url(self) -> str:
        return f"attachment://{self.filename}"

    @property
    def filename(self) -> str:
        if self._filename is None:
            return os.path.basename(self.path)
        return self._filename

    def stream(
        self, *, executor: typing.Optional[concurrent.futures.Executor] = None, head_only: bool = False,
    ) -> AsyncReaderContextManager[FileReader]:
        """Start streaming the resource using a thread pool executor.

        Parameters
        ----------
        executor : typing.Optional[concurrent.futures.Executor]
            The executor to run the blocking read operations in. If `None`,
            the default executor for the running event loop will be used
            instead.
        head_only : bool
            Not used. Provided only to match the underlying interface.

        Returns
        -------
        AsyncReaderContextManager[FileReader]
            An async context manager that when entered, produces the
            data stream.
        """
        return _NoOpAsyncReaderContextManagerImpl(FileReader(self.filename, None, executor, self.path))
