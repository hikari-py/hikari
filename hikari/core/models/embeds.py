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

import abc
import dataclasses
import datetime
import typing
import weakref

from hikari.core.models import base
from hikari.core.models import colors
from hikari.core.models import media
from hikari.core.utils import assertions
from hikari.core.utils import auto_repr
from hikari.core.utils import custom_types
from hikari.core.utils import date_utils
from hikari.core.utils import transform


class EmbedPart(base.HikariModel, abc.ABC):
    """
    Abstract base for any internal component for an embed.

    **You should never need to use this directly.**
    """

    __slots__ = ("__weakref__",)

    # Abstract to enforce subclassing.
    @abc.abstractmethod
    def __init__(self):
        pass

    def __delattr__(self, item):
        setattr(self, item, None)

    def to_dict(self, *, dict_factory=dict):
        attrs = {a: getattr(self, a) for a in self.__slots__}
        # noinspection PyArgumentList,PyTypeChecker
        return dict_factory(**{k: v for k, v in attrs.items() if v is not None})

    # noinspection PyArgumentList,PyDataclass
    @classmethod
    def from_dict(cls, **kwargs):
        params = {field.name: kwargs.get(field.name) for field in dataclasses.fields(cls)}
        return cls(**params)


@dataclasses.dataclass()
class EmbedVideo(EmbedPart):
    """
    A video in an embed.

    **You should never need to create one of these directly.**
    """

    __slots__ = ("url", "height", "width")

    #: A :class:`str` containing the URL to the video.
    url: str
    #: A :class:`int` containing the height of the video.
    height: int
    #: A :class:`int` containing the width of the video.
    width: int

    def __init__(self, url: str = None, height: int = None, width: int = None,) -> None:
        super().__init__()
        self.url = url
        self.height = height
        self.width = width


@dataclasses.dataclass()
class EmbedImage(EmbedPart):
    """
    An image in an embed.

    **You should never need to create one of these directly.**
    """

    __slots__ = ("url", "proxy_url", "height", "width")

    #: A :class:`str` containing the URL to the image.
    url: str
    #: A :class:`str` containing the proxied URL to the image.
    proxy_url: str
    #: A :class:`int` containing the height of the image.
    height: int
    #: A :class:`int` containing the width of the image.
    width: int

    def __init__(self, url: str = None, proxy_url: str = None, height: int = None, width: int = None,) -> None:
        super().__init__()
        self.url = url
        self.proxy_url = proxy_url
        self.height = height
        self.width = width


@dataclasses.dataclass()
class EmbedProvider(EmbedPart):
    """
    A provider in an embed.

    **You should never need to create one of these directly.**
    """

    __slots__ = ("name", "url")

    #: A :class:`str` containing the name of the provider of the embed.
    name: str
    #: A :class:`str` containing the URL of the provider for the embed.
    url: str

    def __init__(self, name: str = None, url: str = None) -> None:
        super().__init__()
        self.name = name
        self.url = url


@dataclasses.dataclass()
class EmbedAuthor(EmbedPart):
    """
    An author in an embed.

    **You should never need to create one of these directly.**
    """

    __slots__ = ("name", "url", "icon_url", "proxy_icon_url")

    #: A :class:`str` containing the name of the author for the embed.
    name: str
    #: A :class:`str` containing the URL link for the author in the embed.
    url: str
    #: A :class:`str` containing the URL link for the author's icon in the embed.
    icon_url: str
    #: A :class:`str` containing the proxy URL link for the author's icon in the embed.
    proxy_icon_url: str

    def __init__(self, name: str = None, url: str = None, icon_url: str = None, proxy_icon_url: str = None,) -> None:
        super().__init__()
        self.name = name
        self.url = url
        self.icon_url = icon_url
        self.proxy_icon_url = proxy_icon_url


@dataclasses.dataclass()
class EmbedFooter(EmbedPart):
    """
    A footer in an embed.

    **You should never need to create one of these directly.**
    """

    __slots__ = ("icon_url", "text", "proxy_icon_url")

    #: A :class:`str` containing the URL to the icon of this footer.
    icon_url: str
    #: A :class:`str` containing the text content in this footer.
    text: str
    #: A :class:`str` containing the proxied URL to the icon of this footer.
    proxy_icon_url: str

    def __init__(self, icon_url: str = None, text: str = None, proxy_icon_url: str = None,) -> None:
        super().__init__()
        self.icon_url = icon_url
        self.text = text
        self.proxy_icon_url = proxy_icon_url


@dataclasses.dataclass()
class EmbedField(EmbedPart):
    """
    A field in an embed.

    **You should never need to create one of these directly.**
    """

    __slots__ = ("name", "value", "inline")

    #: A :class:`str` heading for a field.
    name: str
    #: A :class:`str` body for a field.
    value: str
    #: A :class:`bool` that is `True` if the field is inlined or `False` otherwise.
    inline: bool

    def __init__(self, name: str, value: str, inline: bool = False) -> None:
        super().__init__()
        self.name = name
        self.value = value
        self.inline = inline


EmbedT = typing.TypeVar("EmbedT")
DictImplT = typing.TypeVar("DictImplT", typing.Dict, dict)
DictFactoryT = typing.Union[typing.Type[DictImplT], typing.Callable[[], DictImplT]]


@dataclasses.dataclass()
class BaseEmbed:
    """
    Abstract definition of what makes up any type of embed.

    Note:
         Accessors for nested types will return a :class:`weakref.proxy` to the specified value.
         This is to support internal cleanup operations regarding resource management.
         While this should not affect proper day-to-day usage of this module, if you attempt to
         reference the private `_`-prefixed  variables directly, you may interrupt this cleanup
         management and may cause strange side effects to manifest themselves. So don't do that.

    **You never need to initialize this base class directly. Use the Embed class for that instead.**
    """

    __slots__ = (
        "_title",
        "_description",
        "_url",
        "_timestamp",
        "_color",
        # Should be applied using setters only, as have fields only allowed to be set by Discord themselves.
        "_footer",
        "_image",
        "_thumbnail",
        "_author",
        "_fields",
        "_type",
    )

    _type: str
    _footer: typing.Optional[EmbedFooter]
    _image: typing.Optional[EmbedImage]
    _thumbnail: typing.Optional[EmbedImage]
    _author: typing.Optional[EmbedAuthor]
    _fields: typing.MutableSequence[EmbedField]

    _title: typing.Optional[str]
    _description: typing.Optional[str]
    _url: typing.Optional[str]
    _timestamp: typing.Optional[datetime.datetime]
    _color: typing.Optional[typing.Union[int, colors.Color]]

    __repr__ = auto_repr.repr_of("title", "timestamp", "color")

    def __init__(
        self,
        *,
        type: str = "rich",
        title: str = None,
        description: str = None,
        url: str = None,
        timestamp: datetime.datetime = None,
        color: typing.Union[int, colors.Color] = None,
    ) -> None:
        self._type = type
        self.title = title
        self.description = description
        self.url = url
        self.timestamp = timestamp
        self.color = colors.Color(color) if color is not None else None
        self._footer = None
        self._image = None
        self._thumbnail = None
        self._author = None
        self._fields = []

    @property
    def type(self) -> typing.Optional[str]:
        """
        The embed type, if it is provided.
        """
        return self._type

    @property
    def title(self) -> typing.Optional[str]:
        """
        The title of the embed. Can be set and removed using the `del` operator additionally.

        Warning:
            This may be an empty string or whitespace, but can be no more than 256
            characters in size.
        """
        return self._title

    @title.setter
    def title(self, title: str):
        assertions.assert_that(title is None or len(title) <= 256, "embed.title must not exceed 256 characters")
        self._title = title

    @title.deleter
    def title(self):
        self._title = None

    @property
    def url(self) -> typing.Optional[str]:
        """
        The URL of the embed's title. Can be set and removed using the `del` operator additionally.
        """
        return self._url

    @url.setter
    def url(self, url: str):
        self._url = url

    @url.deleter
    def url(self):
        self._url = None

    @property
    def timestamp(self) -> typing.Optional[datetime.datetime]:
        """
        The timestamp to set on the embed. Can be set and removed using the `del` operator additionally.
        """
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp: datetime.datetime):
        self._timestamp = timestamp

    @timestamp.deleter
    def timestamp(self):
        self._timestamp = None

    @property
    def description(self) -> typing.Optional[str]:
        """
        The description of the embed. Can be set and removed using the `del` operator additionally.

        Warning:
            This may be an empty string or whitespace, but can be no more than
            2048 characters in size.
        """
        return self._description

    @description.setter
    def description(self, description: str):
        assertions.assert_that(
            description is None or len(description) <= 2048, "embed.title must not exceed 2048 characters"
        )

        self._description = description

    @description.deleter
    def description(self):
        self._description = None

    @property
    def color(self) -> typing.Optional[typing.Union[colors.Color, int]]:
        """
        The color of the embed. Can be set and removed using the `del` operator additionally.

        Can be a :class:`hikari.core.models.color.Color` or an :class:`int`.
        """
        return self._color

    @color.setter
    def color(self, color: typing.Optional[typing.Union[colors.Color, int]]) -> None:
        self._color = colors.Color(color) if color is not None and not isinstance(color, colors.Color) else color

    @color.deleter
    def color(self):
        self._color = None

    #: An alias for :attr:`color` for non-american users.
    colour = color

    @property
    def footer(self) -> typing.Optional[EmbedFooter]:
        """
        The optional footer in this embed. Can also be removed using the `del` operator if you wish to remove
        it entirely.

        Note:
            This is a :class:`weakref.proxy`. It will only exist while the embed
            itself exists. Assigning it and passing it around once the embed is no longer
            accessible **will not work**.
        """
        return weakref.proxy(self._footer) if self._footer is not None else None

    @footer.deleter
    def footer(self):
        self._footer = None

    @property
    def image(self) -> typing.Optional[EmbedImage]:
        """
        The optional image for this embed. Can also be removed using the `del` operator if you wish to remove
        it entirely.

        Note:
            This is a :class:`weakref.proxy`. It will only exist while the embed
            itself exists. Assigning it and passing it around once the embed is no longer
            accessible **will not work**.
        """
        return weakref.proxy(self._image) if self._image is not None else None

    @image.deleter
    def image(self):
        self._image = None

    @property
    def thumbnail(self) -> typing.Optional[EmbedImage]:
        """
        The optional thumbnail for this embed. Can also be removed using the `del` operator if you wish to remove
        it entirely.

        Note:
            This is a :class:`weakref.proxy`. It will only exist while the embed
            itself exists. Assigning it and passing it around once the embed is no longer
            accessible **will not work**.
        """
        return weakref.proxy(self._thumbnail) if self._thumbnail is not None else None

    @thumbnail.deleter
    def thumbnail(self):
        self._thumbnail = None

    @property
    def author(self) -> typing.Optional[EmbedAuthor]:
        """
        The optional author for this embed. Can also be removed using the `del` operator if you wish to remove
        it entirely.

        Note:
            This is a :class:`weakref.proxy`. It will only exist while the embed
            itself exists. Assigning it and passing it around once the embed is no longer
            accessible **will not work**.
        """
        return weakref.proxy(self._author) if self._author is not None else None

    @author.deleter
    def author(self):
        self._author = None

    @property
    def fields(self) -> typing.Sequence[EmbedField]:
        """
        A sequence of the embed fields for this embed. This may be empty.

        Note:
            This is a collection of :class:`weakref.proxy`. They will only exist while the embed
            itself exists. Extracting them and storing them separately **will not work**.
        """
        return list(map(weakref.proxy, self._fields))

    def to_dict(self, *, dict_factory: DictFactoryT = dict) -> DictImplT:
        """
        Converts this embed into a raw payload that Discord's HTTP API will understand.

        Returns:
            :type: the result of calling the `dict_factory`, or :class:`dict` by default.
        """
        # TODO: potentially add the 6k char limit checks RE http://github.com/discordapp/discord-api-docs/issues/1173

        d = dict_factory()
        transform.put_if_not_none(d, "title", self.title)
        transform.put_if_not_none(d, "description", self.description)
        transform.put_if_not_none(d, "url", self.url)
        d["type"] = self.type

        if self.timestamp is not None:
            d["timestamp"] = self.timestamp.replace(tzinfo=datetime.timezone.utc).isoformat()
        if self.color is not None:
            d["color"] = int(self.color)
        if self.footer is not None:
            d["footer"] = self.footer.to_dict(dict_factory=dict_factory)
        if self.image is not None:
            d["image"] = self.image.to_dict(dict_factory=dict_factory)
        if self.thumbnail is not None:
            d["thumbnail"] = self.thumbnail.to_dict(dict_factory=dict_factory)
        if self.author is not None:
            d["author"] = self.author.to_dict(dict_factory=dict_factory)
        if self._fields:
            d["fields"] = [f.to_dict(dict_factory=dict_factory) for f in self._fields]

        return d

    @classmethod
    def from_dict(cls: typing.Type[EmbedT], payload: custom_types.DiscordObject) -> EmbedT:
        """
        Parses an instance of this embed type from a raw Discord payload.

        Returns:
            :type: an instance of this class initialized with the values in the :class:`dict` payload passed.
        """
        timestamp = payload.get("timestamp")
        if timestamp is not None:
            timestamp = date_utils.parse_iso_8601_ts(timestamp)

        embed = cls(
            title=payload.get("title"),
            description=payload.get("description"),
            url=payload.get("url"),
            timestamp=timestamp,
            color=payload.get("color"),
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


@dataclasses.dataclass(init=False)
class ReceivedEmbed(BaseEmbed):
    """
    A special implementation of Embed that is used for embeds received from messages by other users.

    This provides read-only access to several extra fields, such as provider information and any embedded videos. All
    fields that an embed you are constructing to send in your own message cannot normally include.

    **You should never need to create one of these directly. Use the Embed class instead for that.**
    """

    __slots__ = (
        "_video",
        "_provider",
    )

    _video: typing.Optional[EmbedVideo]
    _provider: typing.Optional[EmbedProvider]

    @typing.overload
    def __init__(
        self,
        *,
        type: str = "rich",
        title: str = None,
        description: str = None,
        url: str = None,
        timestamp: datetime.datetime = None,
        color: typing.Union[int, colors.Color] = None,
    ) -> None:
        ...

    def __init__(self, **kwargs):
        self._video = None
        self._provider = None
        super().__init__(**kwargs)

    @property
    def video(self) -> typing.Optional[EmbedVideo]:
        """
        An optional video for this embed.

        Note:
            This is a :class:`weakref.proxy`. It will only exist while the embed
            itself exists. Assigning it and passing it around once the embed is no longer
            accessible **will not work**.
        """
        return weakref.proxy(self._video) if self._video is not None else None

    @property
    def provider(self) -> typing.Optional[EmbedProvider]:
        """
        An optional provider for the embed.

        Note:
            This is a :class:`weakref.proxy`. It will only exist while the embed
            itself exists. Assigning it and passing it around once the embed is no longer
            accessible **will not work**.
        """
        return weakref.proxy(self._provider) if self._provider is not None else None


FileOrUrlT = typing.Union[str]


def _extract_url(url: FileOrUrlT) -> typing.Tuple[typing.Optional[str], typing.Optional[media.AbstractFile]]:
    if url is None:
        return None, None
    if isinstance(url, media.AbstractFile):
        return f"attachment://{url.name}", url
    return url, None


@dataclasses.dataclass(init=False)
class Embed(BaseEmbed):
    """
    An embed that you can send in a message. Contains a few extra helper methods and allows the functionality to enable
    uploading of images within embeds easily.

    Warning:
        An embed may contain no more than 6,000 characters of textual content, and only up to 25 fields. Additionally,
        specific attributes of an embed have their own size constraints which are documented per field. If you exceed
        any of these limits, you will receive a :class:`hikari.core.errors.BadRequest` from the API upon sending the
        embed.
    """

    __slots__ = ("_assets_to_upload",)

    @typing.overload
    def __init__(
        self,
        *,
        title: str = None,
        description: str = None,
        url: str = None,
        timestamp: datetime.datetime = None,
        color: typing.Union[int, colors.Color] = None,
    ) -> None:
        ...

    def __init__(self, **kwargs):
        # If we want to upload images in an embed, we need to store their file objects
        # locally so we can upload them later. We use a WeakValueDictionary to refer to the
        # components that use that url. By doing this, if a component gets overwritten, we
        # automatically pop the related file object from this mapping.
        #
        # This has a second benefit that it will only upload duplicated files once! Since the
        # file objects get identified by their name, they will be hashed by the name, and thus
        # if you set the same file object twice, it will only upload it once, which is a nice
        # side effect!
        #
        # This makes the assumption that the user isn't messing around with the internals
        # of this object or it will misbehave, but that is their problem if they do that,
        # not mine.
        kwargs.pop("type", None)  # should never be allowed to be specified as it has to be `rich`
        self._assets_to_upload = weakref.WeakValueDictionary()

        super().__init__(**kwargs)

    @property
    def assets_to_upload(self) -> typing.Iterable[media.AbstractFile]:
        """
        A sequence of zero or more items to upload as part of this embed. These are
        always going to be attached images, and the likes.

        Note:
            This is a view of the files that will be uploaded. If you change your
            embed's attachments at all or overwrite anything with attachments,
            then use this property to obtain a fresh view of the attachments again.
        """
        return set(self._assets_to_upload)

    def set_footer(self: EmbedT, *, icon: FileOrUrlT = None, text: str = None) -> EmbedT:
        """
        Set the footer.

        Args:
            icon: optional icon_url to set.
            text: optional text to set.

        If you call this and do not specify a value for a field, it will clear the existing value.

        Returns:
            This embed to allow method chaining.

        Warning:
            The text must not exceed 2048 characters.

        """
        assertions.assert_that(
            text is None or len(text.strip()) > 0, "footer.text must not be empty or purely whitespace"
        )
        assertions.assert_that(text is None or len(text) < 2048, "footer.text must not exceed 2048 characters")
        icon, file = _extract_url(icon)
        self._footer = EmbedFooter(icon, text)
        self._maybe_ref_file_obj(self._footer, file)
        return self

    def set_image(self: EmbedT, *, image: FileOrUrlT = None) -> EmbedT:
        """
        Set the image.

        Args:
            image: the optional file or URL to the image to set.

        If you call this and do not specify a value for a field, it will clear the existing value. This will clear any
        existing thumbnail, additionally.

        Returns:
            This embed to allow method chaining.

        """
        image, file = _extract_url(image)
        self._image = EmbedImage(url=image)
        self._thumbnail = None
        self._maybe_ref_file_obj(self._image, file)
        return self

    def set_thumbnail(self: EmbedT, *, image: FileOrUrlT = None) -> EmbedT:
        """
        Set the thumbnail image.

        Args:
            image: the optional file or URL to the image to set.

        If you call this and do not specify a value for a field, it will clear the existing value. This will clear any
        existing image, additionally.

        Returns:
            This embed to allow method chaining.
        """
        image, file = _extract_url(image)
        self._thumbnail = EmbedImage(url=image)
        self._image = None
        self._maybe_ref_file_obj(self._thumbnail, file)
        return self

    def set_author(self: EmbedT, *, name: str = None, url: str = None, icon: FileOrUrlT = None,) -> EmbedT:
        """
        Set the author of this embed.

        Args:
            name:
                the optional author name.
            url:
                the optional URL to make the author text link to.
            icon:
                the optional file or URL to the icon to use.

        If you call this and do not specify a value for a field, it will clear the existing value.

        Returns:
            This embed to allow method chaining.

        Warning:
            The name must not exceed 256 characters.
        """
        assertions.assert_that(
            name is None or len(name.strip()) > 0, "author.name must not be empty or purely whitespace"
        )
        assertions.assert_that(name is None or len(name) <= 256, "author.name must not exceed 256 characters")
        icon, icon_file = _extract_url(icon)
        self._author = EmbedAuthor(name=name, url=url, icon_url=icon)
        self._maybe_ref_file_obj(self._author, icon_file)
        return self

    def add_field(self: EmbedT, *, name: str, value: str, inline: bool = False, index: int = None) -> EmbedT:
        """
        Add a field to this embed.

        Args:
            name:
                the field name (title).
            value:
                the field value.
            inline:
                whether to set the field to behave as if it were inline or not.
            index:
                optional index to insert the field at. If unspecified, it will append to the end.

        Returns:
            This embed to allow method chaining.

        Warning:
            The name must not exceed 256 characters and the value must not exceed 2048 characters.
            Both the name and value must not consist purely of whitespace, or be zero characters in size.
            No more than 25 fields can be present in an embed before it becomes invalid.
        """
        index = index if index is not None else len(self._fields)
        assertions.assert_that(len(self._fields) <= 25 and index < 25, "no more than 25 fields can be stored")
        assertions.assert_that(len(name.strip()) > 0, "field.name must not be empty or purely whitespace")
        assertions.assert_that(len(value.strip()) > 0, "field.value must not be empty or purely whitespace")
        assertions.assert_that(len(name.strip()) <= 256, "field.name must not exceed 256 characters")
        assertions.assert_that(len(value) <= 2048, "field.value must not exceed 2048 characters")

        self._fields.insert(index, EmbedField(name=name, value=value, inline=inline))
        return self

    def remove_field(self: EmbedT, index: int) -> EmbedT:
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

    def _maybe_ref_file_obj(self, component, file_obj):
        if file_obj is not None:
            self._assets_to_upload[file_obj] = component
