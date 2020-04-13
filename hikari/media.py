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
"""Represents various forms of media such as images."""
__all__ = ["TextIO", "BytesIO", "IO", "safe_read_file"]

import io
import typing

import aiofiles

from hikari.internal import conversions

TextIO = typing.Union[aiofiles.threadpool.text.AsyncTextIOWrapper, typing.TextIO, io.StringIO, str]

BytesIO = typing.Union[
    aiofiles.threadpool.binary.AsyncBufferedIOBase,
    aiofiles.threadpool.binary.AsyncBufferedReader,
    aiofiles.threadpool.binary.AsyncFileIO,
    typing.BinaryIO,
    io.BytesIO,
    bytes,
    bytearray,
    memoryview,
]

IO = typing.Union[TextIO, BytesIO]


async def safe_read_file(file: IO) -> typing.Tuple[str, conversions.FileLikeT]:
    """Safely read an ``IO`` like object."""
    raise NotImplementedError  # TODO: Nekokatt: update this.
