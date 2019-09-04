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
Embeds.
"""
from __future__ import annotations

import dataclasses
import datetime
import typing

from hikari.core.model import color as _color
from hikari.core.utils import dateutils
from hikari.core.utils import transform
from hikari.core.utils import unspecified


@dataclasses.dataclass()
class Embed:
    __slots__ = (
        "title",
        "description",
        "url",
        "timestamp",
        "color",
        # Should be applied using setters only, as have fields only allowed to be set by Discord themselves.
        "_footer",
        "_image",
        "_thumbnail",
        "_author",
        "_fields",
        # Read-only, should not be settable.
        "_type",
        "_video",
        "_provider",
    )

    _footer: EmbedFooter
    _image: EmbedImage
    _thumbnail: EmbedImage
    _author: EmbedAuthor
    _fields: typing.List[EmbedField]

    _type: str
    _video: EmbedVideo
    _provider: EmbedProvider

    #: The embed title.
    title: str
    #: The embed description.
    description: str
    #: The URL of the embed's title.
    url: str
    #: The timestamp to show on the embed.
    timestamp: datetime.datetime
    #: The color of the embed.
    color: typing.Union[int, _color.Color]

    def __init__(
        self,
        *,
        title: str = unspecified.UNSPECIFIED,
        description: str = unspecified.UNSPECIFIED,
        url: str = unspecified.UNSPECIFIED,
        timestamp: datetime.datetime = unspecified.UNSPECIFIED,
        color: typing.Union[int, _color.Color] = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Args:
            title:
                the optional title of the embed.
            description:
                the optional description of the embed.
            url:
                the optional hyperlink of the embed title.
            timestamp:
                an optional timestamp for the embed. This should be UTC.
            color:
                the optional Color or int color code.
        """
        self.title = title
        self.description = description
        self.url = url
        self.timestamp = timestamp
        self.color = _color.Color(color) if color is not unspecified.UNSPECIFIED else unspecified.UNSPECIFIED
        self._footer = unspecified.UNSPECIFIED
        self._image = unspecified.UNSPECIFIED
        self._thumbnail = unspecified.UNSPECIFIED
        self._author = unspecified.UNSPECIFIED
        self._fields = []
        self._type = unspecified.UNSPECIFIED
        self._video = unspecified.UNSPECIFIED
        self._provider = unspecified.UNSPECIFIED

    @property
    def footer(self) -> typing.Optional[EmbedFooter]:
        """
        The optional footer in this embed.
        """
        return self._footer

    def set_footer(self, *, icon_url: str = unspecified.UNSPECIFIED, text: str = unspecified.UNSPECIFIED) -> Embed:
        """
        Set the footer.

        Args:
            icon_url: optional icon_url to set.
            text: optional text to set.

        If you call this and do not specify a value for a field, it will clear the existing value.

        Returns:
            This embed to allow method chaining.

        """
        self._footer = EmbedFooter(icon_url, text, unspecified.UNSPECIFIED)
        return self

    @property
    def image(self) -> typing.Optional[EmbedImage]:
        """
        The optional image for this embed.
        """
        return self._image

    def set_image(self, *, url: str = unspecified.UNSPECIFIED) -> Embed:
        """
        Set the image.

        Args:
            url: the optional URL to the image to set.

        If you call this and do not specify a value for a field, it will clear the existing value. This will clear any
        existing thumbnail, additionally.

        Returns:
            This embed to allow method chaining.

        """
        self._image = EmbedImage(url=url)
        self._thumbnail = unspecified.UNSPECIFIED
        return self

    @property
    def thumbnail(self) -> typing.Optional[EmbedImage]:
        """
        The optional thumbnail for this embed.
        """
        return self._thumbnail

    def set_thumbnail(self, *, url: str = unspecified.UNSPECIFIED) -> Embed:
        """
        Set the thumbnail image.

        Args:
            url: the optional URL to the image to set.

        If you call this and do not specify a value for a field, it will clear the existing value. This will clear any
        existing image, additionally.

        Returns:
            This embed to allow method chaining.
        """
        self._thumbnail = EmbedImage(url=url)
        self._image = unspecified.UNSPECIFIED
        return self

    @property
    def author(self) -> typing.Optional[EmbedAuthor]:
        """
        The optional author for this embed.
        """
        return self._author

    def set_author(self, *, name: str = unspecified.UNSPECIFIED, url: str = unspecified.UNSPECIFIED, icon_url: str = unspecified.UNSPECIFIED) -> Embed:
        """
        Set the author of this embed.

        Args:
            name: the optional author name.
            url: the optional URL to make the author text link to.
            icon_url: the optional icon URL to use.

        If you call this and do not specify a value for a field, it will clear the existing value.

        Returns:
            This embed to allow method chaining.
        """
        self._author = EmbedAuthor(name=name, url=url, icon_url=icon_url)
        return self

    @property
    def fields(self) -> typing.Sequence[EmbedField]:
        """
        A sequence of the embed fields for this embed. This may be empty.
        """
        return self._fields

    def add_field(self, *, name: str, value: str, inline: bool = False, index: int = ...) -> Embed:
        """
        Add a field to this embed.

        Args:
            name: the field name (title).
            value: the field value.
            inline: whether to set the field to behave as if it were inline or not.
            index: optional index to insert the field at. If unspecified, it will append to the end.

        Returns:
            This embed to allow method chaining.
        """
        index = index if index is not ... else len(self._fields)
        self._fields.insert(index, EmbedField(name=name, value=value, inline=inline))
        return self

    def remove_field(self, index: int) -> Embed:
        """
        Remove a field at the given index.

        Args:
            index:
                The index of the field to remove.

        Returns:
            This embed to allow method chaining.

        Raises:
            IndexError if you referred to an index that doesn't exist.
        """
        del self._fields[index]
        return self

    @property
    def type(self) -> str:
        """
        Gets the embed type, if it is provided.
        """
        return self._type if self._type is not NotImplemented else "rich"

    @property
    def video(self) -> typing.Optional[EmbedVideo]:
        """
        An optional video for this embed.
        """
        return self._video

    @property
    def provider(self) -> typing.Optional[EmbedProvider]:
        """
        An optional provider for the embed.
        """
        return self._provider

    def to_dict(self, *, dict_factory=dict):
        d = dict_factory()
        transform.put_if_specified(d, "title", self.title)
        transform.put_if_specified(d, "description", self.description)
        transform.put_if_specified(d, "url", self.url)

        if self.timestamp is not unspecified.UNSPECIFIED:
            d["timestamp"] = self.timestamp.replace(tzinfo=datetime.timezone.utc).isoformat()
        if self.color is not unspecified.UNSPECIFIED:
            d["color"] = int(self.color)
        if self.footer is not unspecified.UNSPECIFIED:
            d["footer"] = self.footer.to_dict(dict_factory=dict_factory)
        if self.image is not unspecified.UNSPECIFIED:
            d["image"] = self.image.to_dict(dict_factory=dict_factory)
        if self.thumbnail is not unspecified.UNSPECIFIED:
            d["thumbnail"] = self.thumbnail.to_dict(dict_factory=dict_factory)
        if self.author is not unspecified.UNSPECIFIED:
            d["author"] = self.author.to_dict(dict_factory=dict_factory)
        if self._fields:
            d["fields"] = [f.to_dict(dict_factory=dict_factory) for f in self._fields]

        return d

    @staticmethod
    def from_dict(payload):
        timestamp = payload.get("timestamp", unspecified.UNSPECIFIED)
        if timestamp is not unspecified.UNSPECIFIED:
            timestamp = dateutils.parse_iso_8601_datetime(timestamp)

        embed = Embed(
            title=payload.get("title", unspecified.UNSPECIFIED),
            description=payload.get("description", unspecified.UNSPECIFIED),
            url=payload.get("url", unspecified.UNSPECIFIED),
            timestamp=timestamp,
            color=payload.get("color", unspecified.UNSPECIFIED),
        )

        embed._type = payload["type"]

        if "author" in payload:
            embed._author = EmbedAuthor.from_dict(**payload["author"])
        if "footer" in payload:
            embed._footer = EmbedFooter.from_dict(**payload["footer"])
        if "image" in payload:
            embed._image = EmbedImage.from_dict(**payload["image"])
        if "thumbnail" in payload:
            embed._thumbnail = EmbedImage.from_dict(**payload["thumbnail"])
        if "fields" in payload:
            embed._fields = [EmbedField.from_dict(**f) for f in payload["fields"]]
        if "provider" in payload:
            embed._provider = EmbedProvider.from_dict(**payload["provider"])
        if "video" in payload:
            embed._video = EmbedVideo.from_dict(**payload["video"])

        return embed


class _EmbedComponent:
    __slots__ = ()

    def to_dict(self, *, dict_factory=dict):
        attrs = {a: getattr(self, a) for a in self.__slots__}
        # noinspection PyArgumentList,PyTypeChecker
        return dict_factory(**{k: v for k, v in attrs.items() if v is not unspecified.UNSPECIFIED})

    # noinspection PyArgumentList,PyDataclass
    @classmethod
    def from_dict(cls, **kwargs):
        params = {field.name: kwargs.get(field.name) for field in dataclasses.fields(cls)}
        return cls(**params)


@dataclasses.dataclass()
class EmbedVideo(_EmbedComponent):
    """A video in an embed."""

    __slots__ = ("url", "height", "width")

    url: str
    height: int
    width: int

    def __init__(self, url: str = unspecified.UNSPECIFIED, height: int = unspecified.UNSPECIFIED, width: int = unspecified.UNSPECIFIED) -> None:
        self.url = url
        self.height = height
        self.width = width


@dataclasses.dataclass()
class EmbedImage(_EmbedComponent):
    """An video in an embed."""

    __slots__ = ("url", "proxy_url", "height", "width")

    url: str
    proxy_url: str
    height: int
    width: int

    def __init__(
        self, url: str = unspecified.UNSPECIFIED, proxy_url: str = unspecified.UNSPECIFIED, height: int = unspecified.UNSPECIFIED, width: int = unspecified.UNSPECIFIED
    ) -> None:
        self.url = url
        self.proxy_url = proxy_url
        self.height = height
        self.width = width


@dataclasses.dataclass()
class EmbedProvider(_EmbedComponent):
    """A provider in an embed."""

    __slots__ = ("name", "url")

    name: str
    url: str

    def __init__(self, name: str = unspecified.UNSPECIFIED, url: str = unspecified.UNSPECIFIED) -> None:
        self.name = name
        self.url = url


@dataclasses.dataclass()
class EmbedAuthor(_EmbedComponent):
    """An author in an embed."""

    __slots__ = ("name", "url", "icon_url", "proxy_icon_url")

    name: str
    url: str
    icon_url: str
    proxy_icon_url: str

    def __init__(
        self,
        name: str = unspecified.UNSPECIFIED,
        url: str = unspecified.UNSPECIFIED,
        icon_url: str = unspecified.UNSPECIFIED,
        proxy_icon_url: str = unspecified.UNSPECIFIED,
    ) -> None:
        self.name = name
        self.url = url
        self.icon_url = icon_url
        self.proxy_icon_url = proxy_icon_url


@dataclasses.dataclass()
class EmbedFooter(_EmbedComponent):
    """A footer in an embed."""

    __slots__ = ("icon_url", "text", "proxy_icon_url")

    icon_url: str
    text: str
    proxy_icon_url: str

    def __init__(self, icon_url: str = unspecified.UNSPECIFIED, text: str = unspecified.UNSPECIFIED, proxy_icon_url: str = unspecified.UNSPECIFIED) -> None:
        self.icon_url = icon_url
        self.text = text
        self.proxy_icon_url = proxy_icon_url


@dataclasses.dataclass()
class EmbedField(_EmbedComponent):
    """A field in an embed."""

    __slots__ = ("name", "value", "inline")

    name: str
    value: str
    inline: bool

    def __init__(self, name: str, value: str, inline: bool = False) -> None:
        self.name = name
        self.value = value
        self.inline = inline


__all__ = ["Embed"]
