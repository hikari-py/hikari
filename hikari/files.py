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
"""Component used to represent a file to make it easier to upload."""

from __future__ import annotations

__all__ = ["File"]

import asyncio
import io
import logging
import os
import time
import typing
from concurrent import futures

from hikari.internal import assertions


class File(typing.AsyncIterable[bytes]):
    """A file object.

    It is an async iterator of bytes that is compatible with being passed into
    aiohttp requests and read asynchronously. By doing this, it facades multiple
    otherwise incompatible and sometimes blocking IO protocols that Python provides
    in a way that should be simple to use and require as little consideration from
    the user as possible.

    In short, it is a facade for `bytes`, `bytearray`, `memoryview`, `io.BytesIO`,
    `io.IOBase`, `Iterator[bytes]`, `Iterator[bytearray]`, `AsyncIterator[bytes]`,
    `AsyncIterator[bytearray]`, and for file-system paths that are passed as either
    `str` or `os.PathLike` objects.

    !!! note
        This class is an async iterable, so it can be iterated across asynchronously
        to yield arbitrary sized chunks of `bytes` objects from the data stream.

        These iterators do not alter any internal seek of the stream, but will
        result in the data being cached in-memory after the first full iteration.
    """

    __slots__ = ("name", "_data", "_path", "_executor")

    _LOGGER = logging.getLogger("hikari.File")
    ___VALID_TYPES___ = typing.Union[
        io.BytesIO,
        io.RawIOBase,
        bytes,
        bytearray,
        memoryview,
        typing.AsyncIterable[bytes],
        typing.Iterable[bytes],
        os.PathLike,
        str,
    ]

    def __init__(
        self,
        name: typing.Union[os.PathLike, str],
        data: typing.Optional[___VALID_TYPES___] = None,
        executor: typing.Optional[futures.Executor] = None,
    ):
        self._executor = executor

        if isinstance(name, os.PathLike):
            self._LOGGER.debug("given a path-like %s to interpret as a name, will first convert into str", name)
            name = str(name.__fspath__())

        if data is None:
            self.name = os.path.basename(name)
            self._path = name
            self._data = None
            self._LOGGER.debug("given only a file path %s, using that as path; name will be %s", self._path, self.name)
            return

        self.name = name
        self._LOGGER.debug("file name is %s", self.name)

        if isinstance(data, memoryview):
            self._LOGGER.debug("given a memoryview to interpret as a file, will first convert into bytes")
            data = data.tobytes()

        elif isinstance(data, io.BytesIO):
            self._LOGGER.debug("given a bytesio to interpret as a file, will read the buffer immediately")
            data = data.read()

        if isinstance(data, os.PathLike):
            self._LOGGER.debug("retrieving str file path from path-like %s", data)
            data = str(data.__fspath__())

        if isinstance(data, str):
            self._LOGGER.debug("given %s as a file-system path", data)
            self._path = data
            self._data = None
            return

        if isinstance(data, (io.IOBase, typing.Iterable, typing.AsyncIterable, bytes, bytearray)):
            self._LOGGER.debug("given a RawIOBase, Iterable, AsyncIterable, bytes, or bytearray")
            self._path = None
            self._data = data
        else:
            raise TypeError(
                "Expected file object, path-like, str, iterable bytes, async iterable bytes, memoryview, bytes, "
                f"or bytearray as file data type, but received {type(data).__module__}.{type(data).__qualname__}"
            )

    async def __aiter__(self) -> typing.AsyncIterator[typing.Union[bytes, bytearray]]:
        if self._path is not None and self._data is None:
            self._LOGGER.debug("reading path %s from filesystem in executor", self._path)
            # They passed a file-system path.
            # Open the file in binary read mode and return the contents. Do it in
            # the executor to ensure that it doesn't block.
            start = time.perf_counter()
            self._data = await asyncio.get_event_loop().run_in_executor(self._executor, self._read_path)
            duration = (time.perf_counter() - start) * 1_000
            self._LOGGER.debug("read %s bytes from filesystem asynchronously in %sms", self._path, duration)
            yield self._data

        elif isinstance(self._data, io.IOBase):
            self._LOGGER.debug("reading blocking IO object using executor")
            # Some raw IO object that was not a bytesio we decoded earlier.
            # Try to make sure nothing blocks.
            start = time.perf_counter()
            self._data = await asyncio.get_event_loop().run_in_executor(self._executor, self._read_lines)
            duration = (time.perf_counter() - start) * 1_000
            self._LOGGER.debug("read %s bytes from IO object asynchronously in %sms", self._path, duration)
            yield self._data

        elif isinstance(self._data, typing.AsyncIterable):
            self._LOGGER.debug("yielding chunks of data from async iterable")
            # An async iterable of (hopefully) bytes.
            async for chunk in self._data:
                assertions.assert_that(isinstance(chunk, bytes), "async iterator must yield bytes only")
                yield chunk

        elif isinstance(self._data, (bytes, bytearray)):
            self._LOGGER.debug("yielding slab of binary data (%s bytes)", len(self._data))
            # Normal byte array or bytes object. Just yield the whole chunk and let aiohttp swallow it
            # elsewhere. This is already in-memory
            yield self._data

        elif isinstance(self._data, typing.Iterable):
            self._LOGGER.debug("yielding chunks of data from iterable")

            # A normal iterable of (hopefully) bytes.
            for chunk in self._data:
                assertions.assert_that(isinstance(chunk, bytes), "iterator must yield bytes only")
                yield chunk

        else:
            # Shouldn't ever happen unless the user messes around with the internals, but to be
            # safe, lets tell them off for it.
            raise TypeError("Incompatible type passed to file for internal content. Please don't do that!")

    async def read_all(self) -> bytes:
        """Return the whole file data."""
        data = b""
        async for chunk in self:
            data += chunk

        return data

    def _read_path(self):
        with open(self._path, "rb") as fp:
            return fp.read()

    def _read_lines(self):
        lines = self._data.readlines()

        if lines and isinstance(lines[0], str):
            raise TypeError("Please pass a file object in binary mode only!")

        return b"".join(lines)
