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
"""Application and entities that are used to describe message embeds on Discord."""

from __future__ import annotations

__all__: typing.List[str] = [
    "Embed",
    "EmbedResource",
    "EmbedVideo",
    "EmbedImage",
    "EmbedProvider",
    "EmbedAuthor",
    "EmbedFooter",
    "EmbedField",
]

import contextlib
import datetime
import typing

import attr

from hikari.models import colors
from hikari.utilities import files


@attr.s(slots=True, kw_only=True, init=False)
class EmbedResource(files.Resource):
    """A base type for any resource provided in an embed.

    Resources can be downloaded and uploaded, and may also be provided from
    Discord with an additional proxy URL internally.
    """

    resource: files.Resource = attr.ib(repr=True)
    """The resource this object wraps around."""

    proxy_resource: typing.Optional[files.Resource] = attr.ib(default=None, repr=False)
    """The proxied version of the resource, or `None` if not present.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed
        and will be ignored during serialization. Expect this to be
        populated on any received embed attached to a message event.
    """

    @property
    def url(self) -> str:
        return self.resource.url

    @property
    def filename(self) -> typing.Optional[str]:
        return self.resource.filename

    @contextlib.asynccontextmanager
    async def stream(self) -> files.AsyncReader:
        async with self.resource.stream() as stream:
            yield stream


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class EmbedFooter:
    """Represents an embed footer."""

    text: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The footer text, or `None` if not present."""

    icon: typing.Optional[EmbedResource] = attr.ib(default=None, repr=False)
    """The URL of the footer icon, or `None` if not present."""


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class EmbedImage(EmbedResource):
    """Represents an embed image."""

    height: typing.Optional[int] = attr.ib(default=None, repr=False)
    """The height of the image, if present and known, otherwise `None`.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event.
    """

    width: typing.Optional[int] = attr.ib(default=None, repr=False)
    """The width of the image, if present and known, otherwise `None`.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event.
    """


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class EmbedVideo(EmbedResource):
    """Represents an embed video.

    !!! note
        This object cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event with a video attached.
    """

    height: typing.Optional[int] = attr.ib(default=None, repr=False)
    """The height of the video."""

    width: typing.Optional[int] = attr.ib(default=None, repr=False)
    """The width of the video."""


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class EmbedProvider:
    """Represents an embed provider.

    !!! note
        This object cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event provided by an external
        source.
    """

    name: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The name of the provider."""

    url: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The URL of the provider."""


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class EmbedAuthor:
    """Represents an author of an embed."""

    name: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The name of the author, or `None` if not specified."""

    url: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The URL that the author's name should act as a hyperlink to.

    This may be `None` if no hyperlink on the author's name is specified.
    """

    icon: typing.Optional[EmbedResource] = attr.ib(default=None, repr=False)
    """The author's icon, or `None` if not present."""


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class EmbedField:
    """Represents a field in a embed."""

    name: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The name of the field, or `None` if not present."""

    value: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The value of the field, or `None` if not present."""

    is_inline: bool = attr.ib(default=False, repr=True)
    """`True` if the field should display inline. Defaults to `False`."""


@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True)
class Embed:
    """Represents an embed."""

    color: typing.Optional[colors.Color] = attr.ib(
        default=None, repr=False, converter=lambda c: colors.Color.of(c) if c is not None else None,
    )
    """The colour of the embed, or `None` to use the default."""

    colour: typing.Optional[colors.Color] = property(
        lambda self: self.color, lambda self, colour: setattr(self, "color", colour)
    )

    title: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The title of the embed, or `None` if not present."""

    description: typing.Optional[str] = attr.ib(default=None, repr=False)
    """The description of the embed, or `None` if not present."""

    url: typing.Optional[str] = attr.ib(default=None, repr=False)
    """The URL of the embed, or `None` if not present."""

    timestamp: typing.Optional[datetime.datetime] = attr.ib(default=None, repr=True)
    """The timestamp of the embed, or `None` if not present.

    !!! note
        If specified, this should be treated as a UTC timestamp. Ensure any
        values you set here are either generated using
        `datetime.datetime.utcnow`, or are treated as timezone-aware timestamps.

        You can generate a timezone-aware timestamp instead of a timezone-naive
        one by specifying a timezone. Hikari will detect any difference in
        timezone if the timestamp is non timezone-naive and fix it for you.

            # I am British, and it is June, so we are in daylight saving
            # (UTC+1 or GMT+1, specifically).
            >>> import datetime

            # This is timezone naive, notice no timezone in the repr that
            # gets printed. This is no good to us, as Discord will interpret it
            # as being in the future!
            >>> datetime.datetime.now()
            datetime.datetime(2020, 6, 5, 19, 29, 48, 281716)

            # Instead, this is a timezone-aware timestamp, and we can use this
            # correctly. This will always return the current time in UTC.
            >>> datetime.datetime.now(tz=datetime.timezone.utc)
            datetime.datetime(2020, 6, 5, 18, 29, 56, 424744, tzinfo=datetime.timezone.utc)

            # We could instead use a custom timezone. Since the timezone is
            # explicitly specified, Hikari will convert it to UTC for you when
            # you send the embed.
            >>> ...

        A library on PyPI called [tzlocal](...) also exists that may be useful
        to you if you need to get your local timezone for any reason.

            >>> import datetime
            >>> import tzlocal

            # Naive datetime that will show the wrong time on Discord.
            >>> datetime.datetime.now()
            datetime.datetime(2020, 6, 5, 19, 33, 21, 329950)

            # Timezone-aware datetime that uses my local timezone correctly.
            >>> datetime.datetime.now(tz=tzlocal.get_localzone())
            datetime.datetime(2020, 6, 5, 19, 33, 40, 967939, tzinfo=<DstTzInfo 'Europe/London' BST+1:00:00 DST>)

            # Changing timezones.
            >>> dt = datetime.datetime.now(tz=datetime.timezone.utc)
            >>> print(dt)
            datetime.datetime(2020, 6, 5, 18, 38, 27, 863990, tzinfo=datetime.timezone.utc)
            >>> dt.astimezone(tzlocal.get_localzone())
            datetime.datetime(2020, 6, 5, 19, 38, 27, 863990, tzinfo=<DstTzInfo 'Europe/London' BST+1:00:00 DST>)

        ...this is not required, but you may find it more useful if using the
        timestamps in debug logs, for example.
    """

    footer: typing.Optional[EmbedFooter] = attr.ib(default=None, repr=False)
    """The footer of the embed, if present, otherwise `None`."""

    image: typing.Optional[EmbedImage] = attr.ib(default=None, repr=False)
    """The image to display in the embed, or `None` if not present."""

    thumbnail: typing.Optional[EmbedImage] = attr.ib(default=None, repr=False)
    """The thumbnail to show in the embed, or `None` if not present."""

    video: typing.Optional[EmbedVideo] = attr.ib(default=None, repr=False)
    """The video to show in the embed, or `None` if not present.

    !!! note
        This object cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event with a video attached.
    """

    provider: typing.Optional[EmbedProvider] = attr.ib(default=None, repr=False)
    """The provider of the embed, or `None if not present.

    !!! note
        This object cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event with a custom provider
        set.
    """

    author: typing.Optional[EmbedAuthor] = attr.ib(default=None, repr=False)
    """The author of the embed, or `None if not present."""

    fields: typing.MutableSequence[EmbedField] = attr.ib(factory=list, repr=False)
    """The fields in the embed."""

    def set_author(
        self,
        *,
        name: typing.Optional[str] = None,
        url: typing.Optional[str] = None,
        icon: typing.Union[None, str, files.Resource] = None,
    ) -> Embed:
        if name is None and url is None and icon is None:
            self.author = None
        else:
            self.author = EmbedAuthor()
            self.author.name = name
            self.author.url = url
            if icon is not None:
                self.author.icon = EmbedResource()
                self.author.icon.resource = files.ensure_resource(icon)
            else:
                self.author.icon = None
        return self

    def set_footer(
        self, *, text: typing.Optional[str] = None, icon: typing.Union[None, str, files.Resource] = None,
    ) -> Embed:
        if text is None and icon is None:
            self.footer = None
        else:
            self.footer = EmbedFooter()
            self.footer.text = text
            if icon is not None:
                self.footer.icon = EmbedResource()
                self.footer.icon.resource = files.ensure_resource(icon)
            else:
                self.footer.icon = None
        return self

    def set_image(self, image: typing.Union[None, str, files.Resource] = None, /) -> Embed:
        if image is None:
            self.image = None
        else:
            self.image = EmbedImage()
            self.image.resource = files.ensure_resource(image)
        return self

    def set_thumbnail(self, image: typing.Union[None, str, files.Resource] = None, /) -> Embed:
        if image is None:
            self.thumbnail = None
        else:
            self.thumbnail = EmbedImage()
            self.thumbnail.resource = files.ensure_resource(image)
        return self

    def add_field(self, name: str, value: str, *, inline: bool = False) -> Embed:
        field = EmbedField()
        field.name = name
        field.value = value
        field.is_inline = inline
        self.fields.append(field)
        return self

    def edit_field(self, index: int, name: str, value: str, /, *, inline: bool = False) -> Embed:
        field = self.fields[index]
        field.name = name
        field.value = value
        field.is_inline = inline
        return self

    def remove_field(self, index: int, /) -> Embed:
        del self.fields[index]
        return self
