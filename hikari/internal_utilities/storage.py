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
IO utilities.
"""
import io
import typing


def make_resource_seekable(resource) -> typing.Union[io.BytesIO, io.StringIO]:
    """
    Given some representation of data, make a seekable resource to use. This supports bytes, bytearray, memoryview,
    and strings. Anything else is just returned.

    Args:
        resource:
            the resource to check.
    Returns:
        An stream-compatible resource where possible.
    """
    if isinstance(resource, (bytes, bytearray)):
        resource = io.BytesIO(resource)
    elif isinstance(resource, memoryview):
        resource = io.BytesIO(resource.tobytes())
    elif isinstance(resource, str):
        resource = io.StringIO(resource)

    return resource


def get_bytes_from_resource(resource) -> bytes:
    """
    Take in any object that can be considered file-like and return the raw bytes data from it.
    Supports any :class:`FileLikeT` type that isn't string based. Anything else is just returned.

    Args:
        resource:
            The resource to get bytes from.

    Returns:
        The resulting :class:`bytes`.
    """
    if isinstance(resource, bytearray):
        resource = bytes(resource)
    elif isinstance(resource, memoryview):
        resource = resource.tobytes()
    #  Targets the io types found in FileLikeT and BytesLikeT
    elif hasattr(resource, "read"):
        resource = resource.read()

    return resource


#: A bytes-like object, such as a :class:`str`, raw :class:`bytes`, or view across a bytes-like object.
BytesLikeT = typing.Union[bytes, bytearray, memoryview, str, io.StringIO, io.BytesIO]

#: Type description for any object that can be considered to be file-like.
FileLikeT = typing.Union[BytesLikeT, io.BufferedRandom, io.BufferedReader, io.BufferedRWPair]

__all__ = ("make_resource_seekable", "get_bytes_from_resource", "FileLikeT", "BytesLikeT")
