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
"""IO utilities."""
__all__ = ["make_resource_seekable", "FileLikeT", "BytesLikeT"]

import io
import typing


def make_resource_seekable(resource: typing.Any) -> typing.Union[io.BytesIO, io.StringIO]:
    """Given some representation of data, make a seekable resource to use. 
    
    This supports :obj:`bytes`, :obj:`bytearray`, :obj:`memoryview`, and :obj:`str`. 
    Anything else is just returned.

    Parameters
    ----------
    resource : :obj:`typing.Any`
        The resource to check.

    Returns
    -------
    :obj:`typing.Union` [ :obj:`io.BytesIO`, :obj:`io.StringIO` ]
        An stream-compatible resource where possible.
    """
    if isinstance(resource, (bytes, bytearray)):
        resource = io.BytesIO(resource)
    elif isinstance(resource, memoryview):
        resource = io.BytesIO(resource.tobytes())
    elif isinstance(resource, str):
        resource = io.StringIO(resource)

    return resource


#: A bytes-like object, such as a :obj:`str`, raw :obj:`bytes`, or view across a bytes-like object.
BytesLikeT = typing.Union[bytes, bytearray, memoryview, str, io.StringIO, io.BytesIO]

#: Type description for any object that can be considered to be file-like.
FileLikeT = typing.Union[BytesLikeT, io.BufferedRandom, io.BufferedReader, io.BufferedRWPair]
