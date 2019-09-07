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

import base64
import dataclasses
import io
import mimetypes
import re
import typing

from hikari.core.model import base
from hikari.core.utils import transform

_DATA_URI_SCHEME_REGEX = re.compile(r"^data:([^;]+);base64,(.+)$", re.I | re.U)


@dataclasses.dataclass()
class Avatar:
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

    def get_file_types(self) -> typing.List[str]:
        """
        Returns:
            A list of guessed file extensions that are valid for the given MIME type of this avatar. Each will begin
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
class Attachment(base.Snowflake):
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

    def __init__(self, payload):
        self.id = int(payload["id"])
        self.filename = payload["filename"]
        self.size = int(payload["size"])
        self.url = payload["url"]
        self.proxy_url = payload["proxy_url"]
        self.width = transform.nullable_cast(payload.get("width"), int)
        self.height = transform.nullable_cast(payload.get("height"), int)


__all__ = ["Avatar", "Attachment"]
