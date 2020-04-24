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
from hikari.internal import assertions
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
class EmbedFooter(bases.HikariEntity, marshaller.Deserializable, marshaller.Serializable):
    """Represents an embed footer."""

    text: str = marshaller.attrib(deserializer=str, serializer=str)
    """The footer text."""

    icon_url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=str, if_undefined=None, default=None
    )
    """The URL of the footer icon."""

    proxy_icon_url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, transient=True, if_undefined=None, default=None
    )
    """The proxied URL of the footer icon.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class EmbedImage(bases.HikariEntity, marshaller.Deserializable, marshaller.Serializable):
    """Represents an embed image."""

    url: typing.Optional[str] = marshaller.attrib(deserializer=str, serializer=str, if_undefined=None, default=None)
    """The URL of the image."""

    proxy_url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, transient=True, if_undefined=None, default=None
    )
    """The proxied URL of the image.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """

    height: typing.Optional[int] = marshaller.attrib(deserializer=int, transient=True, if_undefined=None, default=None)
    """The height of the image.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """

    width: typing.Optional[int] = marshaller.attrib(deserializer=int, transient=True, if_undefined=None, default=None)
    """The width of the image.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class EmbedThumbnail(bases.HikariEntity, marshaller.Deserializable, marshaller.Serializable):
    """Represents an embed thumbnail."""

    url: typing.Optional[str] = marshaller.attrib(deserializer=str, serializer=str, if_undefined=None, default=None)
    """The URL of the thumbnail."""

    proxy_url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, transient=True, if_undefined=None, default=None
    )
    """The proxied URL of the thumbnail.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """

    height: typing.Optional[int] = marshaller.attrib(deserializer=int, transient=True, if_undefined=None, default=None)
    """The height of the thumbnail.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """

    width: typing.Optional[int] = marshaller.attrib(deserializer=int, transient=True, if_undefined=None, default=None)
    """The width of the thumbnail.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class EmbedVideo(bases.HikariEntity, marshaller.Deserializable):
    """Represents an embed video.

    !!! note
        This embed attached object cannot be sent by bots or webhooks while
        sending an embed and therefore shouldn't be initiated like the other
        embed objects.
    """

    url: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, default=None)
    """The URL of the video."""

    height: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None, default=None)
    """The height of the video."""

    width: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None, default=None)
    """The width of the video."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class EmbedProvider(bases.HikariEntity, marshaller.Deserializable):
    """Represents an embed provider.

    !!! note
        This embed attached object cannot be sent by bots or webhooks while
        sending an embed and therefore shouldn't be initiated like the other
        embed objects.
    """

    name: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, default=None)
    """The name of the provider."""

    url: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, if_none=None, default=None)
    """The URL of the provider."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class EmbedAuthor(bases.HikariEntity, marshaller.Deserializable, marshaller.Serializable):
    """Represents an embed author."""

    name: typing.Optional[str] = marshaller.attrib(deserializer=str, serializer=str, if_undefined=None, default=None)
    """The name of the author."""

    url: typing.Optional[str] = marshaller.attrib(deserializer=str, serializer=str, if_undefined=None, default=None)
    """The URL of the author."""

    icon_url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=str, if_undefined=None, default=None
    )
    """The URL of the author icon."""

    proxy_icon_url: typing.Optional[str] = marshaller.attrib(
        deserializer=str, transient=True, if_undefined=None, default=None
    )
    """The proxied URL of the author icon.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class EmbedField(bases.HikariEntity, marshaller.Deserializable, marshaller.Serializable):
    """Represents a field in a embed."""

    name: str = marshaller.attrib(deserializer=str, serializer=str)
    """The name of the field."""

    value: str = marshaller.attrib(deserializer=str, serializer=str)
    """The value of the field."""

    is_inline: bool = marshaller.attrib(
        raw_name="inline", deserializer=bool, serializer=bool, if_undefined=False, default=False
    )
    """Whether the field should display inline. Defaults to `False`."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class Embed(bases.HikariEntity, marshaller.Deserializable, marshaller.Serializable):
    """Represents an embed."""

    title: typing.Optional[str] = marshaller.attrib(deserializer=str, serializer=str, if_undefined=None, default=None)
    """The title of the embed."""

    @title.validator
    def _title_check(self, attribute, value):  # pylint:disable=unused-argument
        if value is not None:
            assertions.assert_that(
                len(value) <= _MAX_EMBED_TITLE, f"title must not exceed {_MAX_EMBED_TITLE} characters"
            )

    description: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=str, if_undefined=None, default=None
    )
    """The description of the embed."""

    @description.validator
    def _description_check(self, attribute, value):  # pylint:disable=unused-argument
        if value is not None:
            assertions.assert_that(
                len(value) <= _MAX_EMBED_DESCRIPTION, f"description must not exceed {_MAX_EMBED_DESCRIPTION} characters"
            )

    url: typing.Optional[str] = marshaller.attrib(deserializer=str, serializer=str, if_undefined=None, default=None)
    """The URL of the embed."""

    timestamp: typing.Optional[datetime.datetime] = marshaller.attrib(
        deserializer=conversions.parse_iso_8601_ts,
        serializer=lambda timestamp: timestamp.replace(tzinfo=datetime.timezone.utc).isoformat(),
        if_undefined=None,
        default=None,
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
        deserializer=EmbedFooter.deserialize, serializer=EmbedFooter.serialize, if_undefined=None, default=None
    )
    """The footer of the embed."""

    image: typing.Optional[EmbedImage] = marshaller.attrib(
        deserializer=EmbedImage.deserialize, serializer=EmbedImage.serialize, if_undefined=None, default=None
    )
    """The image of the embed."""

    thumbnail: typing.Optional[EmbedThumbnail] = marshaller.attrib(
        deserializer=EmbedThumbnail.deserialize, serializer=EmbedThumbnail.serialize, if_undefined=None, default=None
    )
    """The thumbnail of the embed."""

    video: typing.Optional[EmbedVideo] = marshaller.attrib(
        deserializer=EmbedVideo.deserialize, transient=True, if_undefined=None, default=None,
    )
    """The video of the embed.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """

    provider: typing.Optional[EmbedProvider] = marshaller.attrib(
        deserializer=EmbedProvider.deserialize, transient=True, if_undefined=None, default=None
    )
    """The provider of the embed.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization.
    """

    author: typing.Optional[EmbedAuthor] = marshaller.attrib(
        deserializer=EmbedAuthor.deserialize, serializer=EmbedAuthor.serialize, if_undefined=None, default=None
    )
    """The author of the embed."""

    fields: typing.Sequence[EmbedField] = marshaller.attrib(
        deserializer=lambda fields: [EmbedField.deserialize(f) for f in fields],
        serializer=lambda fields: [f.serialize() for f in fields],
        if_undefined=list,
        factory=list,
    )
    """The fields of the embed."""

    _assets_to_upload = marshaller.attrib(if_undefined=list, factory=list, transient=True)

    @property
    def assets_to_upload(self):
        """File assets that need to be uploaded when sending the embed."""
        return self._assets_to_upload

    def _extract_url(self, url) -> typing.Tuple[typing.Optional[str], typing.Optional[files.File]]:
        if url is None:
            return None, None
        if isinstance(url, files.File):
            return f"attachment://{url.name}", url
        return url, None

    def _maybe_ref_file_obj(self, file_obj) -> None:
        if file_obj is not None:
            self._assets_to_upload.append(file_obj)

    def set_footer(self, *, text: str, icon: typing.Optional[str, files.File] = None) -> Embed:
        """Set the embed footer.

        Parameters
        ----------
        text: str
            The optional text to set for the footer.
        icon: typing.Union[str, hikari.files.File], optional
            The optional `hikari.files.File` or URL to the image to set.

        Returns
        -------
        Embed
            This embed to allow method chaining.

        Raises
        ------
        ValueError
            If `text` exceeds 2048 characters or consists purely of whitespaces.
        """
        assertions.assert_that(len(text.strip()) > 0, "footer.text must not be empty or purely of whitespaces")
        assertions.assert_that(
            len(text) <= _MAX_FOOTER_TEXT, f"footer.text must not exceed {_MAX_FOOTER_TEXT} characters"
        )
        icon, file = self._extract_url(icon)
        self.footer = EmbedFooter(text=text, icon_url=icon)
        self._maybe_ref_file_obj(file)
        return self

    def set_image(self, image: typing.Optional[str, files.File] = None) -> Embed:
        """Set the embed image.

        Parameters
        ----------
        image: typing.Union[str, hikari.files.File], optional
            The optional `hikari.files.File` or URL to the image to set.

        Returns
        -------
        Embed
            This embed to allow method chaining.
        """
        image, file = self._extract_url(image)
        self.image = EmbedImage(url=image)
        self._maybe_ref_file_obj(file)
        return self

    def set_thumbnail(self, image: typing.Optional[str, files.File] = None) -> Embed:
        """Set the thumbnail image.

        Parameters
        ----------
        image: typing.Union[str, hikari.files.File], optional
            The optional `hikari.files.File` or URL to the image to set.

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
        icon: typing.Optional[str, files.File] = None,
    ) -> Embed:
        """Set the author of this embed.

        Parameters
        ----------
        name: str, optional
            The optional authors name.
        url: str, optional
            The optional URL to make the author text link to.
        icon: typing.Union[str, hikari.files.File], optional
            The optional `hikari.files.File` or URL to the icon to set.

        Returns
        -------
        Embed
            This embed to allow method chaining.

        Raises
        ------
        ValueError
            If `name` exceeds 256 characters or consists purely of whitespaces.
        """
        assertions.assert_that(
            name is None or len(name.strip()) > 0, "author.name must not be empty or purely of whitespaces"
        )
        assertions.assert_that(
            name is None or len(name) <= _MAX_AUTHOR_NAME, f"author.name must not exceed {_MAX_AUTHOR_NAME} characters"
        )
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
        assertions.assert_that(
            len(self.fields) <= _MAX_EMBED_FIELDS and index < _MAX_EMBED_FIELDS,
            f"no more than {_MAX_EMBED_FIELDS} fields can be stored",
        )
        assertions.assert_that(len(name.strip()) > 0, "field.name must not be empty or purely of whitespaces")
        assertions.assert_that(len(value.strip()) > 0, "field.value must not be empty or purely of whitespaces")
        assertions.assert_that(
            len(name.strip()) <= _MAX_FIELD_NAME, f"field.name must not exceed {_MAX_FIELD_NAME} characters"
        )
        assertions.assert_that(
            len(value) <= _MAX_FIELD_VALUE, f"field.value must not exceed {_MAX_FIELD_VALUE} characters"
        )

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
        if name is not ...:
            assertions.assert_that(len(name.strip()) > 0, "field.name must not be empty or purely of whitespaces")
            assertions.assert_that(
                len(name.strip()) <= _MAX_FIELD_NAME, f"field.name must not exceed {_MAX_FIELD_NAME} characters"
            )
        if value is not ...:
            assertions.assert_that(len(value.strip()) > 0, "field.value must not be empty or purely of whitespaces")
            assertions.assert_that(
                len(value) <= _MAX_FIELD_VALUE, f"field.value must not exceed {_MAX_FIELD_VALUE} characters"
            )

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

    def _safe_len(self, item) -> bool:
        return len(item) if item is not None else 0

    def _check_total_length(self) -> None:
        total_size = self._safe_len(self.title)
        total_size += self._safe_len(self.description)
        total_size += self._safe_len(self.author.name) if self.author is not None else 0
        total_size += len(self.footer.text) if self.footer is not None else 0

        for field in self.fields:
            total_size += len(field.name)
            total_size += len(field.value)

        assertions.assert_that(
            total_size <= _MAX_EMBED_SIZE, f"Total characters in an embed can not exceed {_MAX_EMBED_SIZE}"
        )

    def serialize(self) -> more_typing.JSONObject:
        self._check_total_length()
        return super().serialize()
