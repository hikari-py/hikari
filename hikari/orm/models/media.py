#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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

__all__ = ["AbstractFile", "Attachment", "File", "InMemoryFile", "safe_read_file"]

import abc
import dataclasses
import re
import typing

import aiofiles
import aiohttp

from hikari.internal_utilities import reprs
from hikari.internal_utilities import storage
from hikari.internal_utilities import transformations
from hikari.internal_utilities import type_hints
from hikari.orm.models import bases

if typing.TYPE_CHECKING:
    import asyncio
    import io
    from concurrent import futures

_DATA_URI_SCHEME_REGEX = re.compile(r"^data:([^;]+);base64,(.+)$", re.I | re.U)


class Attachment(bases.BaseModel, bases.SnowflakeMixin):
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
    width: type_hints.Nullable[int]

    #: Height of the attachment (`None` unless the attachment is an image).
    #:
    #: :type: :class:`int` or `None`
    height: type_hints.Nullable[int]

    __repr__ = reprs.repr_of("id", "filename", "size")

    def __init__(self, payload: type_hints.JSONObject) -> None:
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
        loop: type_hints.Nullable[asyncio.AbstractEventLoop] = None,
        executor: type_hints.Nullable[futures.Executor] = None,
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
                while block := await resp.content.readany():
                    await afp.write(block)


@dataclasses.dataclass()
class AbstractFile(bases.BaseModel, abc.ABC):
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
        encoding: type_hints.Nullable[str] = None,
        errors: type_hints.Nullable[str] = None,
        newline: str = None,
        opener: type_hints.Nullable[typing.Callable[[str, int], ...]] = None,
        *,
        loop: type_hints.Nullable[asyncio.AbstractEventLoop] = None,
        executor: type_hints.Nullable[futures.Executor] = None,
    ) -> io.IOBase:
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
            >>>
            >>> async with file.open() as afp:
            ...     async for line in afp:
            ...         # Technically this can block too, but just ignore that for the sake of this example.
            ...         print(line)

            >>> # Reading an entire file at once, reading it in binary mode.
            >>> file = File("cat.png")
            >>>
            >>> async with file.open("b") as afp:
            ...     data = await afp.read()

            >>> # Taking an MD5 hash of the PC's hostname
            >>> # and then using a custom thread pool to write it to a file.
            >>> import platform, concurrent.futures, hashlib
            >>>
            >>> hostname = platform.uname()[1]
            >>> md5_hash = hashlib.md5().digest()
            >>> tpe = concurrent.futures.ThreadPoolExecutor()
            >>>
            >>> file = File("important-stuff.sh")
            >>>
            >>> async with file.open("wb", executor=tpe, loop=loop) as afp:
            ...     await afp.write(md5_hash)

        """

    @abc.abstractmethod
    def __hash__(self) -> int:
        """
        Our name makes us unique.

        This is abstract to enforce you implement it. Being a dataclass, each subclass will
        drop the `__hash__` implementation, which is somewhat annoying as it means I can't define it
        in one place. Thus, if you are subclassing this, be sure to define the hash as being the
        hash code of the file name!
        """


class InMemoryFile(AbstractFile):
    """
    Wraps a bytes-like object that is assumed to be located in-memory and provides the same interface to it
    that :class:`File` does. This allows you to upload attachments such as images that are in memory rather
    than ones that are stored on disk.
    """

    __slots__ = ("data",)

    #: A bytes-like object containing the data to upload.
    #:
    #: :type: :class:`hikari.internal_utilities.io_helpers.BytesLikeT`
    data: storage.BytesLikeT

    def __init__(self, name: str, data: storage.BytesLikeT) -> None:
        super().__init__(name)
        self.data = data

    def open(self, *args, **kwargs) -> typing.Union[io.BytesIO, io.StringIO]:
        """
        Returns a seekable object across the contents of the file. This will either
        be a :class:`io.StringIO` if a string-like object, or otherwise a :class:`io.BytesIO`.

        Warning:
              All arguments are ignored to this call, as they are irrelevant and are implemented
              purely to provide a consistent interface.

              This means that passing the `mode` will have no effect on the return type.
        """
        return storage.make_resource_seekable(self.data)

    def __hash__(self) -> int:
        return hash(self.name)


@dataclasses.dataclass()
class File(AbstractFile):
    """
    Represents a file stored on a secondary storage device such as your local disk, or on a mounted
    network drive.

    Provides a mechanism to read the file without blocking the event loop.
    """

    __slots__ = ()

    def open(self, *args, **kwargs) -> aiofiles.threadpool.AsyncFileIO:
        return aiofiles.open(self.name, *args, **kwargs)

    def __hash__(self) -> int:
        return hash(self.name)


async def safe_read_file(file: AbstractFile) -> typing.Tuple[str, storage.FileLikeT]:
    """
    Read a file object derived from :class:`AbstractFile` and then close if necessary.

    Args:
        file:
            The :class:`AbstractFile` derived file object.

    Returns:
        First the file's :class:`str` name.
        Second, the read :class:`storage.FileLikeT` data.

    Raises:
        ValueError:
            If `file` isn't a :class:`AbstractFile` derived object.
    """
    name = getattr(file, "name", None)
    if isinstance(file, InMemoryFile):
        file_output = file.open().read()
    elif isinstance(file, File):
        async with file.open() as fp:
            file_output = await fp.read()
    else:
        raise ValueError(f"Invalid file type '{type(file)}' provided, expected an AbstractFile derivative.")

    return name, file_output
