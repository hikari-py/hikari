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
IO utilities.
"""
import typing

__all__ = ("make_resource_seekable",)

import io


def make_resource_seekable(resource):
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


#: Type description for any object that can be considered to be file-like.
FileLike = typing.Union[
    bytes,
    bytearray,
    memoryview,
    str,
    io.IOBase,
    io.StringIO,
    io.BytesIO,
    io.BufferedRandom,
    io.BufferedReader,
    io.BufferedRWPair,
]
