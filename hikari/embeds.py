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
"""Components and entities that are used to describe message embeds on Discord."""

from __future__ import annotations

__all__ = [
    "Embed",
    "EmbedThumbnail",
    "EmbedVideo",
    "EmbedImage",
    "EmbedProvider",
    "EmbedAuthor",
    "EmbedFooter",
    "EmbedField",
]

import datetime
import typing

import attr

from hikari import bases
from hikari import colors
from hikari import files
from hikari.internal import conversions
from hikari.internal import marshaller

if typing.TYPE_CHECKING:
    from hikari.internal import more_typing

_MAX_FOOTER_TEXT: typing.Final[int] = 2048
_MAX_AUTHOR_NAME: typing.Final[int] = 256
_MAX_FIELD_NAME: typing.Final[int] = 256
_MAX_FIELD_VALUE: typing.Final[int] = 1024
_MAX_EMBED_TITLE: typing.Final[int] = 256
_MAX_EMBED_DESCRIPTION: typing.Final[int] = 2048
_MAX_EMBED_FIELDS: typing.Final[int] = 25
_MAX_EMBED_SIZE: typing.Final[int] = 6000


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class EmbedFooter(bases.Entity, marshaller.Deserializable, marshaller.Serializable):
    """Represents an embed footer."""

    text: str = marshaller.attrib(deserializer=str, serializer=str, repr=True)
    """The footer text."""

    icon_url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=str, if_undefined=None, default=None
    )
    """The URL of the footer icon."""

    proxy_icon_url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=None, if_undefined=None, default=None
    )
    """The proxied URL of the footer icon.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class EmbedImage(bases.Entity, marshaller.Deserializable, marshaller.Serializable):
    """Represents an embed image."""

    url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=str, if_undefined=None, default=None, repr=True,
    )
    """The URL of the image."""

    proxy_url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=None, if_undefined=None, default=None,
    )
    """The proxied URL of the image.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """

    height: typing.Optional[int] = marshaller.attrib(deserializer=int, serializer=None, if_undefined=None, default=None)
    """The height of the image.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """

    width: typing.Optional[int] = marshaller.attrib(deserializer=int, serializer=None, if_undefined=None, default=None)
    """The width of the image.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class EmbedThumbnail(bases.Entity, marshaller.Deserializable, marshaller.Serializable):
    """Represents an embed thumbnail."""

    url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=str, if_undefined=None, default=None, repr=True,
    )
    """The URL of the thumbnail."""

    proxy_url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=None, if_undefined=None, default=None,
    )
    """The proxied URL of the thumbnail.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """

    height: typing.Optional[int] = marshaller.attrib(deserializer=int, serializer=None, if_undefined=None, default=None)
    """The height of the thumbnail.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """

    width: typing.Optional[int] = marshaller.attrib(deserializer=int, serializer=None, if_undefined=None, default=None)
    """The width of the thumbnail.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class EmbedVideo(bases.Entity, marshaller.Deserializable):
    """Represents an embed video.

    !!! note
        This embed attached object cannot be sent by bots or webhooks while
        sending an embed and therefore shouldn't be initiated like the other
        embed objects.
    """

    url: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, default=None, repr=True)
    """The URL of the video."""

    height: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None, default=None)
    """The height of the video."""

    width: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None, default=None)
    """The width of the video."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class EmbedProvider(bases.Entity, marshaller.Deserializable):
    """Represents an embed provider.

    !!! note
        This embed attached object cannot be sent by bots or webhooks while
        sending an embed and therefore shouldn't be sent by your application.
        You should still expect to receive these objects where appropriate.
    """

    name: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, default=None, repr=True)
    """The name of the provider."""

    url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, if_undefined=None, if_none=None, default=None, repr=True
    )
    """The URL of the provider."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class EmbedAuthor(bases.Entity, marshaller.Deserializable, marshaller.Serializable):
    """Represents an embed author."""

    name: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=str, if_undefined=None, default=None, repr=True
    )
    """The name of the author."""

    url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=str, if_undefined=None, default=None, repr=True
    )
    """The URL of the author."""

    icon_url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=str, if_undefined=None, default=None
    )
    """The URL of the author icon."""

    proxy_icon_url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=None, if_undefined=None, default=None
    )
    """The proxied URL of the author icon.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class EmbedField(bases.Entity, marshaller.Deserializable, marshaller.Serializable):
    """Represents a field in a embed."""

    name: str = marshaller.attrib(deserializer=str, serializer=str, repr=True)
    """The name of the field."""

    value: str = marshaller.attrib(deserializer=str, serializer=str, repr=True)
    """The value of the field."""

    is_inline: bool = marshaller.attrib(
        raw_name="inline", deserializer=bool, serializer=bool, if_undefined=False, default=False, repr=True
    )
    """Whether the field should display inline. Defaults to `False`."""


def _serialize_timestamp(timestamp: datetime.datetime) -> str:
    return timestamp.replace(tzinfo=datetime.timezone.utc).isoformat()


def _deserialize_fields(payload: more_typing.JSONArray, **kwargs: typing.Any) -> typing.Sequence[EmbedField]:
    return [EmbedField.deserialize(field, **kwargs) for field in payload]


def _serialize_fields(fields: typing.Sequence[EmbedField]) -> more_typing.JSONArray:
    return [field.serialize() for field in fields]


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class Embed(bases.Entity, marshaller.Deserializable, marshaller.Serializable):
    """Represents an embed."""

    title: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=str, if_undefined=None, default=None, repr=True
    )
    """The title of the embed."""

    @title.validator
    def _title_check(self, _, value):  # pylint:disable=unused-argument
        if value is not None and len(value) > _MAX_EMBED_TITLE:
            raise ValueError(f"title must not exceed {_MAX_EMBED_TITLE} characters")

    description: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=str, if_undefined=None, default=None
    )
    """The description of the embed."""

    @description.validator
    def _description_check(self, _, value):  # pylint:disable=unused-argument
        if value is not None and len(value) > _MAX_EMBED_DESCRIPTION:
            raise ValueError(f"description must not exceed {_MAX_EMBED_DESCRIPTION} characters")

    url: typing.Optional[str] = marshaller.attrib(deserializer=str, serializer=str, if_undefined=None, default=None)
    """The URL of the embed."""

    timestamp: typing.Optional[datetime.datetime] = marshaller.attrib(
        deserializer=conversions.parse_iso_8601_ts,
        serializer=_serialize_timestamp,
        if_undefined=None,
        default=None,
        repr=True,
    )
    """The timestamp of the embed."""

    color: typing.Optional[colors.Color] = marshaller.attrib(
        deserializer=colors.Color,
        serializer=int,
        converter=attr.converters.optional(colors.Color.of),
        if_undefined=None,
        default=None,
    )
    """The colour of this embed's sidebar."""

    footer: typing.Optional[EmbedFooter] = marshaller.attrib(
        deserializer=EmbedFooter.deserialize,
        serializer=EmbedFooter.serialize,
        if_undefined=None,
        default=None,
        inherit_kwargs=True,
    )
    """The footer of the embed."""

    image: typing.Optional[EmbedImage] = marshaller.attrib(
        deserializer=EmbedImage.deserialize,
        serializer=EmbedImage.serialize,
        if_undefined=None,
        default=None,
        inherit_kwargs=True,
    )
    """The image of the embed."""

    thumbnail: typing.Optional[EmbedThumbnail] = marshaller.attrib(
        deserializer=EmbedThumbnail.deserialize,
        serializer=EmbedThumbnail.serialize,
        if_undefined=None,
        default=None,
        inherit_kwargs=True,
    )
    """The thumbnail of the embed."""

    video: typing.Optional[EmbedVideo] = marshaller.attrib(
        deserializer=EmbedVideo.deserialize, serializer=None, if_undefined=None, default=None, inherit_kwargs=True
    )
    """The video of the embed.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """

    provider: typing.Optional[EmbedProvider] = marshaller.attrib(
        deserializer=EmbedProvider.deserialize, serializer=None, if_undefined=None, default=None, inherit_kwargs=True,
    )
    """The provider of the embed.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """

    author: typing.Optional[EmbedAuthor] = marshaller.attrib(
        deserializer=EmbedAuthor.deserialize,
        serializer=EmbedAuthor.serialize,
        if_undefined=None,
        default=None,
        inherit_kwargs=True,
    )
    """The author of the embed."""

    fields: typing.Sequence[EmbedField] = marshaller.attrib(
        deserializer=_deserialize_fields,
        serializer=_serialize_fields,
        if_undefined=list,
        factory=list,
        inherit_kwargs=True,
    )
    """The fields of the embed."""

    _assets_to_upload = attr.attrib(factory=list)

    @property
    def assets_to_upload(self):
        """File assets that need to be uploaded when sending the embed."""
        return self._assets_to_upload

    @staticmethod
    def _extract_url(url) -> typing.Tuple[typing.Optional[str], typing.Optional[files.BaseStream]]:
        if url is None:
            return None, None
        if isinstance(url, files.BaseStream):
            return f"attachment://{url.filename}", url
        return url, None

    def _maybe_ref_file_obj(self, file_obj) -> None:
        if file_obj is not None:
            self._assets_to_upload.append(file_obj)

    def set_footer(self, *, text: str, icon: typing.Optional[str, files.BaseStream] = None) -> Embed:
        """Set the embed footer.

        Parameters
        ----------
        text: str
            The optional text to set for the footer.
        icon: typing.Union[str, hikari.files.BaseStream], optional
            The optional `hikari.files.BaseStream` or URL to the image to set.

        Returns
        -------
        Embed
            This embed to allow method chaining.

        Raises
        ------
        ValueError
            If `text` exceeds 2048 characters or consists purely of whitespaces.
        """
        if not text.strip():
            raise ValueError("footer.text must not be empty or purely of whitespaces")
        if len(text) > _MAX_FOOTER_TEXT:
            raise ValueError(f"footer.text must not exceed {_MAX_FOOTER_TEXT} characters")

        icon, file = self._extract_url(icon)
        self.footer = EmbedFooter(text=text, icon_url=icon)
        self._maybe_ref_file_obj(file)
        return self

    def set_image(self, image: typing.Optional[str, files.BaseStream] = None) -> Embed:
        """Set the embed image.

        Parameters
        ----------
        image: typing.Union[str, hikari.files.BaseStream], optional
            The optional `hikari.files.BaseStream` or URL to the image to set.

        Returns
        -------
        Embed
            This embed to allow method chaining.
        """
        image, file = self._extract_url(image)
        self.image = EmbedImage(url=image)
        self._maybe_ref_file_obj(file)
        return self

    def set_thumbnail(self, image: typing.Optional[str, files.BaseStream] = None) -> Embed:
        """Set the thumbnail image.

        Parameters
        ----------
        image: typing.Union[str, hikari.files.BaseStream], optional
            The optional `hikari.files.BaseStream` or URL to the image to set.

        Returns
        -------
        Embed
            This embed to allow method chaining.
        """
        image, file = self._extract_url(image)
        self.thumbnail = EmbedThumbnail(url=image)
        self._maybe_ref_file_obj(file)
        return self

    def set_author(
        self,
        *,
        name: typing.Optional[str] = None,
        url: typing.Optional[str] = None,
        icon: typing.Optional[str, files.BaseStream] = None,
    ) -> Embed:
        """Set the author of this embed.

        Parameters
        ----------
        name: str, optional
            The optional authors name.
        url: str, optional
            The optional URL to make the author text link to.
        icon: typing.Union[str, hikari.files.BaseStream], optional
            The optional `hikari.files.BaseStream` or URL to the icon to set.

        Returns
        -------
        Embed
            This embed to allow method chaining.

        Raises
        ------
        ValueError
            If `name` exceeds 256 characters or consists purely of whitespaces.
        """
        if name is not None and not name.strip():
            raise ValueError("author.name must not be empty or purely of whitespaces")
        if name is not None and len(name) > _MAX_AUTHOR_NAME:
            raise ValueError(f"author.name must not exceed {_MAX_AUTHOR_NAME} characters")

        icon, icon_file = self._extract_url(icon)
        self.author = EmbedAuthor(name=name, url=url, icon_url=icon)
        self._maybe_ref_file_obj(icon_file)
        return self

    def add_field(self, *, name: str, value: str, inline: bool = False, index: typing.Optional[int] = None) -> Embed:
        """Add a field to this embed.

        Parameters
        ----------
        name: str
            The fields name (title).
        value: str
            The fields value.
        inline: bool
            Whether to set the field to behave as if it were inline or not. Defaults to `False`.
        index: int, optional
            The optional index to insert the field at. If `None`, it will append to the end.

        Returns
        -------
        Embed
            This embed to allow method chaining.

        Raises
        ------
        ValueError
            If `title` exceeds 256 characters or `value` exceeds 2048 characters; if
            the `name` or `value` consist purely of whitespace, or be zero characters in size;
            25 fields are present in the embed.
        """
        index = index if index is not None else len(self.fields)
        if len(self.fields) >= _MAX_EMBED_FIELDS:
            raise ValueError(f"no more than {_MAX_EMBED_FIELDS} fields can be stored")

        if not name.strip():
            raise ValueError("field.name must not be empty or purely of whitespaces")
        if len(name) > _MAX_FIELD_NAME:
            raise ValueError(f"field.name must not exceed {_MAX_FIELD_NAME} characters")

        if not value.strip():
            raise ValueError("field.value must not be empty or purely of whitespaces")
        if len(value) > _MAX_FIELD_VALUE:
            raise ValueError(f"field.value must not exceed {_MAX_FIELD_VALUE} characters")

        self.fields.insert(index, EmbedField(name=name, value=value, is_inline=inline))
        return self

    def edit_field(self, index: int, *, name: str = ..., value: str = ..., inline: bool = ...) -> Embed:
        """Edit a field in this embed at the given index.

        Parameters
        ----------
        index: int
            The index to edit the field at.
        name: str
            If specified, the new fields name (title).
        value: str
            If specified, the new fields value.
        inline: bool
            If specified, the whether to set the field to behave as if it were
            inline or not.

        Returns
        -------
        Embed
            This embed to allow method chaining.

        Raises
        ------
        IndexError
            If you referred to an index that doesn't exist.
        ValueError
            If `title` exceeds 256 characters or `value` exceeds 2048 characters; if
            the `name` or `value` consist purely of whitespace, or be zero characters in size.
        """
        if name is not ... and not name.strip():
            raise ValueError("field.name must not be empty or purely of whitespaces")
        if name is not ... and len(name.strip()) > _MAX_FIELD_NAME:
            raise ValueError(f"field.name must not exceed {_MAX_FIELD_NAME} characters")

        if value is not ... and not value.strip():
            raise ValueError("field.value must not be empty or purely of whitespaces")
        if value is not ... and len(value) > _MAX_FIELD_VALUE:
            raise ValueError(f"field.value must not exceed {_MAX_FIELD_VALUE} characters")

        field = self.fields[index]

        field.name = name if name is not ... else field.name
        field.value = value if value is not ... else field.value
        field.is_inline = inline if value is not ... else field.is_inline
        return self

    def remove_field(self, index: int) -> Embed:
        """Remove a field from this embed at the given index.

        Parameters
        ----------
        index: int
            The index of the field to remove.

        Returns
        -------
        Embed
            This embed to allow method chaining.

        Raises
        ------
        IndexError
            If you referred to an index that doesn't exist.
        """
        del self.fields[index]
        return self

    @staticmethod
    def _safe_len(item) -> int:
        return len(item) if item is not None else 0

    def _check_total_length(self) -> None:
        total_size = self._safe_len(self.title)
        total_size += self._safe_len(self.description)
        total_size += self._safe_len(self.author.name) if self.author is not None else 0
        total_size += len(self.footer.text) if self.footer is not None else 0

        for field in self.fields:
            total_size += len(field.name)
            total_size += len(field.value)

        if total_size > _MAX_EMBED_SIZE:
            raise ValueError("Total characters in an embed can not exceed {_MAX_EMBED_SIZE}")

    def serialize(self) -> more_typing.JSONObject:
        self._check_total_length()
        return super().serialize()
