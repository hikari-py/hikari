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
Represents various forms of media such as images.
"""
from __future__ import annotations

import abc
import asyncio
import base64
import dataclasses
import io
import mimetypes
import re
import typing
from concurrent import futures

import aiofiles
import aiohttp

from hikari.core.models import base
from hikari.internal_utilities import auto_repr
from hikari.internal_utilities import io_helpers
from hikari.internal_utilities import transformations

_DATA_URI_SCHEME_REGEX = re.compile(r"^data:([^;]+);base64,(.+)$", re.I | re.U)


@dataclasses.dataclass()
class Avatar(base.HikariModel):
    """
    Represents an Avatar. This contains compressed raw byte data of the given image.

    The object is initialized from a MIME type and base 64 string. This base 64 string is decoded on initialization
    which reduces the overall byte string size by roughly 1/3.
    """

    __slots__ = ("mime_type", "data")

    #: The MIME type of the data.
    #:
    #: :type: :class:`str`
    mime_type: str

    #: Image data
    #:
    #: :type: :class:`bytes`
    data: bytes

    __repr__ = auto_repr.repr_of("mime_type")

    def __init__(self, mime_type: str, base64_data: bytes) -> None:
        """
        Args:
            mime_type:
                The MIME type of the data.
            base64_data:
                The raw Base64 data that was provided from the data URI scheme.
        """
        self.mime_type = mime_type
        self.data = base64.b64decode(base64_data)

    def get_file_types(self) -> typing.Sequence[str]:
        """
        Returns:
            A sequence of guessed file extensions that are valid for the given MIME type of this avatar. Each will begin
            with a period `.` and is simply an educated guess.
        """
        return mimetypes.guess_all_extensions(self.mime_type, strict=True)

    def to_data_uri(self) -> str:
        """
        Returns:
            A data URI of the given image.
            See the :attr:`data` note for performance information.
        """
        b64 = base64.b64encode(self.data).decode()
        return f"data:{self.mime_type};base64,{b64}"

    def to_file_object(self) -> io.BytesIO:
        """
        Returns:
            A file-like object that is seekable containing the uncompressed image data.
        """
        return io.BytesIO(self.data)

    @classmethod
    def from_data_uri_scheme(cls, data_uri_scheme: str) -> Avatar:
        """
        Consumes a given base64-type data URI scheme and produces a compressed Avatar object from it.

        Args:
            data_uri_scheme:
                The data URI scheme to parse.
        Returns:
            A compressed Avatar object.
        """
        try:
            mime_type, b64 = _DATA_URI_SCHEME_REGEX.findall(data_uri_scheme)[0]
            return cls(mime_type, bytes(b64, "ascii"))
        except IndexError:
            raise TypeError("Invalid data URI scheme provided") from None

    def __len__(self):
        return len(self.data)


@dataclasses.dataclass()
class Attachment(base.HikariModel, base.Snowflake):
    """
    An attachment that is received from Discord in a message.
    """

    __slots__ = ("id", "filename", "size", "url", "proxy_url", "width", "height")

    #: ID of the attachment.
    #:
    #: :type: :class:`int`
    id: int

    #: Filename of the attachment.
    #:
    #: :type: :class:`str`
    filename: str

    #: Size of the attachment.
    #:
    #: :type: :class:`int`
    size: int

    #: URL of the attachment.
    #:
    #: :type: :class:`str`
    url: str

    #: Proxied URL of the attachment.
    #:
    #: :type: :class:`str`
    proxy_url: str

    #: Width of the attachment (`None` unless the attachment is an image).
    #:
    #: :type: :class:`int` or `None`
    width: typing.Optional[int]

    #: Height of the attachment (`None` unless the attachment is an image).
    #:
    #: :type: :class:`int` or `None`
    height: typing.Optional[int]

    __repr__ = auto_repr.repr_of("id", "filename", "size")

    def __init__(self, payload):
        self.id = int(payload["id"])
        self.filename = payload["filename"]
        self.size = int(payload["size"])
        self.url = payload["url"]
        self.proxy_url = payload["proxy_url"]
        self.width = transformations.nullable_cast(payload.get("width"), int)
        self.height = transformations.nullable_cast(payload.get("height"), int)

    async def read(self) -> typing.Union[bytes]:
        async with aiohttp.request("get", self.url) as resp:
            resp.raise_for_status()
            return await resp.read()

    async def save(
        self,
        path: str,
        *,
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
        executor: typing.Optional[futures.Executor] = None,
    ) -> None:
        async with aiohttp.request("get", self.url) as resp:
            resp.raise_for_status()

            # Use bit-inception to download the resource.
            # await resp.read() would call await resp.content.read() which is defined here:
            # https://github.com/aio-libs/aiohttp/blob/6dedbca7325c35daaa1810a4617c49f9adca5dbc/aiohttp/streams.py#L332
            # We can use that somewhat-internal (but still part of the public API) implementation detail to stream
            # the information incrementally between the response stream and the threadpool without reading the
            # entire content into memory at once, which is more efficient on memory usage for large files.
            async with aiofiles.open(path, "wb", executor=executor, loop=loop) as afp:
                block = ...
                while block is not None:
                    block = await resp.content.readany()
                    await afp.write(block)


@dataclasses.dataclass()
class AbstractFile(base.HikariModel, abc.ABC):
    """
    Provides base functionality for a file-like object of some sort to enable reading it
    efficiently with :mod:`asyncio`.
    """

    __slots__ = ("name",)

    #: The file name.
    #:
    #: :type: :class:`str`
    name: str

    @abc.abstractmethod
    def open(
        self,
        mode: str = "r",
        buffering: int = -1,
        encoding: typing.Optional[str] = None,
        errors: typing.Optional[str] = None,
        newline: str = None,
        opener: typing.Optional[typing.Callable[[str, int], ...]] = None,
        *,
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
        executor: typing.Optional[futures.Executor] = None,
    ) -> aiofiles.threadpool.AsyncFileIO:
        """
        Reads the contents of the file safely.

        Due to how Python implements :mod:`asyncio`, performing IO-based tasks such as reading/writing from/to
        secondary storage will block the event loop. While this happens, your bot loses the ability to
        multitask at all and will appear to have frozen.

        A module called :mod:`aiofiles` is used to mitigate this issue by running the read task in a thread pool or
        process pool. It will then await the buffers in those pools to be filled and release the event loop to the
        rest of the application while it waits for this.

        All file operations will need to be `await`ed, but apart from this, usage is mostly the same as with the
        standard :func:`builtins.open` builtin routine. The differences are that the `closefd` and `file` arguments
        are ommitted, and you can optionally pass an :class:`asyncio.AbstractEventLoop` `loop` if you want to run
        this on a different loop. You can also optionally pass an :class:`concurrent.futures.Executor` if you don't
        want the operation to run on the default executor as per :meth:`asyncio.AbstractEventLoop.run_in_executor`.

        Example:

            >>> # Reading a file in text mode, one line at a time.
            >>> file = File("banner.txt")
            >>> async with file.open() as afp:
            ...     async for line in afp:
            ...         # Technically this can block too, but just ignore that for the sake of this example.
            ...         print(line)

            >>> # Reading an entire file at once, reading it in binary mode.
            >>> file = File("cat.png")
            >>> async with file.open("b") as afp:
            ...     data = await afp.read()

            >>> # Taking an MD5 hash of the PC's hostname
            >>> # and then using a custom thread pool to write it to a file.
            >>> hostname = platform.uname()[1]
            >>> md5_hash = hashlib.md5().digest()
            >>> tpe = concurrent.futures.ThreadPoolExecutor()
            >>> file = File("important-stuff.sh")
            >>> async with file.open("wb", executor=tpe, loop=loop) as afp:
            ...     await afp.write(md5_hash)

        """

    @abc.abstractmethod
    def __hash__(self):
        """
        Our name makes us unique.

        This is abstract to enforce you implement it. Being a dataclass, each subclass will
        drop the `__hash__` implementation, which is somewhat annoying as it means I can't define it
        in one place. Thus, if you are subclassing this, be sure to define the hash as being the
        hash code of the file name!
        """


@dataclasses.dataclass()
class InMemoryFile(AbstractFile):
    """
    Wraps a bytes-like object that is assumed to be located in-memory and provides the same interface to it
    that :class:`File` does. This allows you to upload attachments such as images that are in memory rather
    than ones that are stored on disk.
    """

    __slots__ = ("data",)

    #: A bytes-like object containing the data to upload.
    #:
    #: :type: :class:`hikari.core.utils.io_utils.BytesLikeT`
    data: io_helpers.BytesLikeT

    def open(self, *args, **kwargs):
        """
        Returns a seekable object across the contents of the file. This will either
        be a :class:`io.StringIO` if a string-like object, or otherwise a :class:`io.BytesIO`.

        Warning:
              All arguments are ignored to this call, as they are irrelevant and are implemented
              purely to provide a consistent interface.

              This means that passing the `mode` will have no effect on the return type.
        """
        return io_helpers.make_resource_seekable(self.data)

    def __hash__(self):
        return hash(self.name)


@dataclasses.dataclass()
class File(AbstractFile):
    """
    Represents a file stored on a secondary storage device such as your local disk, or on a mounted
    network drive.

    Provides a mechanism to read the file without blocking the event loop.
    """

    __slots__ = ()

    def open(self, *args, **kwargs):
        return aiofiles.open(self.name, *args, **kwargs)

    def __hash__(self):
        return hash(self.name)


__all__ = ["Avatar", "Attachment", "File", "InMemoryFile"]
