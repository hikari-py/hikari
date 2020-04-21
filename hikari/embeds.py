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
from hikari.internal import conversions
from hikari.internal import marshaller


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

    description: typing.Optional[str] = marshaller.attrib(
        deserializer=str, serializer=str, if_undefined=None, default=None
    )
    """The description of the embed."""

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
        deserializer=colors.Color, serializer=int, if_undefined=None, default=None
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
