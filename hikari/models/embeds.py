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

import copy
import datetime
import typing
import warnings
import weakref

import attr

from hikari import errors
from hikari.models import colors
from hikari.models import files

if typing.TYPE_CHECKING:
    from hikari.utilities import data_binding

_MAX_FOOTER_TEXT: typing.Final[int] = 2048
_MAX_AUTHOR_NAME: typing.Final[int] = 256
_MAX_FIELD_NAME: typing.Final[int] = 256
_MAX_FIELD_VALUE: typing.Final[int] = 1024
_MAX_EMBED_TITLE: typing.Final[int] = 256
_MAX_EMBED_DESCRIPTION: typing.Final[int] = 2048
_MAX_EMBED_FIELDS: typing.Final[int] = 25
_MAX_EMBED_SIZE: typing.Final[int] = 6000


@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True)
class EmbedFooter:
    """Represents an embed footer."""

    text: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The footer text, or `None` if not present."""

    icon_url: typing.Optional[str] = attr.ib(default=None)
    """The URL of the footer icon, or `None` if not present."""

    proxy_icon_url: typing.Optional[str] = attr.ib(default=None)
    """The proxied URL of the footer icon, or `None` if not present.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event.
    """


@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True)
class EmbedImage:
    """Represents an embed image."""

    url: typing.Optional[str] = attr.ib(
        default=None, repr=True,
    )
    """The URL of the image to show, or `None` if not present."""

    proxy_url: typing.Optional[str] = attr.ib(default=None,)
    """The proxied URL of the image, or `None` if not present.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event.
    """

    height: typing.Optional[int] = attr.ib(default=None)
    """The height of the image, if present and known, otherwise `None`.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event.
    """

    width: typing.Optional[int] = attr.ib(default=None)
    """The width of the image, if present and known, otherwise `None`.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event.
    """


@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True)
class EmbedThumbnail:
    """Represents an embed thumbnail."""

    url: typing.Optional[str] = attr.ib(
        default=None, repr=True,
    )
    """The URL of the thumbnail to display, or `None` if not present."""

    proxy_url: typing.Optional[str] = attr.ib(default=None,)
    """The proxied URL of the thumbnail, if present and known, otherwise `None`.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event.
    """

    height: typing.Optional[int] = attr.ib(default=None)
    """The height of the thumbnail, if present and known, otherwise `None`.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event.
    """

    width: typing.Optional[int] = attr.ib(default=None)
    """The width of the thumbnail, if present and known, otherwise `None`.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event.
    """


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=True)
class EmbedVideo:
    """Represents an embed video.

    !!! note
        This object cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event with a video attached.
    """

    url: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The URL of the video."""

    height: typing.Optional[int] = attr.ib(default=None)
    """The height of the video."""

    width: typing.Optional[int] = attr.ib(default=None)
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


@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True)
class EmbedAuthor:
    """Represents an author of an embed."""

    name: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The name of the author, or `None` if not specified."""

    url: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The URL that the author's name should act as a hyperlink to.

    This may be `None` if no hyperlink on the author's name is specified.
    """

    icon_url: typing.Optional[str] = attr.ib(default=None)
    """The URL of the author's icon, or `None` if not present."""

    proxy_icon_url: typing.Optional[str] = attr.ib(default=None)
    """The proxied URL of the author icon, or `None` if not present.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event.
    """


@attr.s(eq=True, hash=False, init=True, kw_only=True, slots=True)
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

    title: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The title of the embed, or `None` if not present."""

    @title.validator
    def _title_check(self, _, value):  # pylint:disable=unused-argument
        if value is not None and len(value) > _MAX_EMBED_TITLE:
            warnings.warn(
                f"title must not exceed {_MAX_EMBED_TITLE} characters", category=errors.HikariWarning,
            )

    description: typing.Optional[str] = attr.ib(default=None)
    """The description of the embed, or `None` if not present."""

    @description.validator
    def _description_check(self, _, value):  # pylint:disable=unused-argument
        if value is not None and len(value) > _MAX_EMBED_DESCRIPTION:
            warnings.warn(
                f"description must not exceed {_MAX_EMBED_DESCRIPTION} characters", category=errors.HikariWarning,
            )

    url: typing.Optional[str] = attr.ib(default=None)
    """The URL of the embed, or `None` if not present."""

    timestamp: typing.Optional[datetime.datetime] = attr.ib(
        default=None, repr=True,
    )
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

    color: typing.Optional[colors.Color] = attr.ib(
        converter=attr.converters.optional(colors.Color.of), default=None,
    )
    """The colour of this embed.

    If `None`, the default is used for the user's colour-scheme when viewing it
    (off-white on light-theme and off-black on dark-theme).

    !!! warning
        Various bugs exist in the desktop client at the time of writing where
        `#FFFFFF` is treated as as the default colour for your colour-scheme
        rather than white. The current workaround appears to be using a slightly
        off-white, such as `#DDDDDD` or `#FFFFFE` instead.
    """

    footer: typing.Optional[EmbedFooter] = attr.ib(default=None)
    """The footer of the embed, if present, otherwise `None`."""

    image: typing.Optional[EmbedImage] = attr.ib(default=None)
    """The image to display in the embed, or `None` if not present."""

    thumbnail: typing.Optional[EmbedThumbnail] = attr.ib(default=None)
    """The thumbnail to show in the embed, or `None` if not present."""

    video: typing.Optional[EmbedVideo] = attr.ib(default=None)
    """The video to show in the embed, or `None` if not present.

    !!! note
        This object cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event with a video attached.
    """

    provider: typing.Optional[EmbedProvider] = attr.ib(default=None)
    """The provider of the embed, or `None if not present.

    !!! note
        This object cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event with a custom provider
        set.
    """

    author: typing.Optional[EmbedAuthor] = attr.ib(default=None)
    """The author of the embed, or `None if not present."""

    fields: typing.MutableSequence[EmbedField] = attr.ib(factory=list)
    """The fields in the embed."""

    # Use a weakref so that clearing an image can pop the reference.
    _assets_to_upload = attr.attrib(factory=weakref.WeakSet, repr=False)

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
            # Store a _copy_ so weakreffing works properly.
            obj_copy = copy.copy(file_obj)
            self._assets_to_upload.add(obj_copy)

    def set_footer(self, *, text: typing.Optional[str], icon: typing.Optional[str, files.BaseStream] = None) -> Embed:
        """Set the embed footer.

        Parameters
        ----------
        text : str or None
            The optional text to set for the footer. If `None`, the content is
            cleared.
        icon : hikari.models.files.BaseStream or str or None
            The optional `hikari.models.files.BaseStream` or URL to the image to
            set.

        Returns
        -------
        Embed
            This embed to allow method chaining.
        """
        if text is not None:
            # FIXME: move these validations to the dataclass.
            if not text.strip():
                warnings.warn("footer.text must not be empty or purely of whitespaces", category=errors.HikariWarning)
            elif len(text) > _MAX_FOOTER_TEXT:
                warnings.warn(
                    f"footer.text must not exceed {_MAX_FOOTER_TEXT} characters", category=errors.HikariWarning
                )

        if icon is not None:
            icon, file = self._extract_url(icon)
            self.footer = EmbedFooter(text=text, icon_url=icon)
            self._maybe_ref_file_obj(file)
        elif self.footer is not None:
            self.footer.icon_url = None

        return self

    def set_image(self, image: typing.Optional[str, files.BaseStream] = None) -> Embed:
        """Set the embed image.

        Parameters
        ----------
        image : hikari.models.files.BaseStream or str or None
            The optional `hikari.models.files.BaseStream` or URL to the image
            to set. If `None`, the image is removed.

        Returns
        -------
        Embed
            This embed to allow method chaining.
        """
        if image is None:
            self.image = None
        else:
            image, file = self._extract_url(image)
            self.image = EmbedImage(url=image)
            self._maybe_ref_file_obj(file)
        return self

    def set_thumbnail(self, image: typing.Optional[str, files.BaseStream] = None) -> Embed:
        """Set the thumbnail image.

        Parameters
        ----------
        image: hikari.models.files.BaseStream or str or None
            The optional `hikari.models.files.BaseStream` or URL to the image
            to set. If `None`, the thumbnail is removed.

        Returns
        -------
        Embed
            This embed to allow method chaining.
        """
        if image is None:
            self.thumbnail = None
        else:
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
        name: str or None
            The optional authors name to display.
        url: str or None
            The optional URL to make the author text link to.
        icon: hikari.models.files.BaseStream or str or None
            The optional `hikari.models.files.BaseStream` or URL to the icon
            to set.

        Returns
        -------
        Embed
            This embed to allow method chaining.
        """
        if name is not None:
            # TODO: move validation to dataclass
            if name is not None and not name.strip():
                warnings.warn("author.name must not be empty or purely of whitespaces", category=errors.HikariWarning)
            if name is not None and len(name) > _MAX_AUTHOR_NAME:
                warnings.warn(
                    f"author.name must not exceed {_MAX_AUTHOR_NAME} characters", category=errors.HikariWarning
                )

        if icon is not None:
            icon, icon_file = self._extract_url(icon)
            self.author = EmbedAuthor(name=name, url=url, icon_url=icon)
            self._maybe_ref_file_obj(icon_file)
        elif self.author is not None:
            self.author.icon_url = None

        return self

    def add_field(self, *, name: str, value: str, inline: bool = False, index: typing.Optional[int] = None) -> Embed:
        """Add a field to this embed.

        Parameters
        ----------
        name: str
            The field name (title).
        value: str
            The field value.
        inline: bool
            If `True`, multiple consecutive fields may be displayed on the same
            line. This is not guaranteed behaviour and only occurs if viewing
            on desktop clients. Defaults to `False`.
        index: int or None
            The optional index to insert the field at. If `None`, it will append
            to the end.

        Returns
        -------
        Embed
            This embed to allow method chaining.
        """
        index = index if index is not None else len(self.fields)
        if len(self.fields) >= _MAX_EMBED_FIELDS:
            warnings.warn(f"no more than {_MAX_EMBED_FIELDS} fields can be stored", category=errors.HikariWarning)

        # TODO: move to dataclass.
        if not name.strip():
            warnings.warn("field.name must not be empty or purely of whitespaces", category=errors.HikariWarning)
        if len(name) > _MAX_FIELD_NAME:
            warnings.warn(f"field.name must not exceed {_MAX_FIELD_NAME} characters", category=errors.HikariWarning)

        if not value.strip():
            warnings.warn("field.value must not be empty or purely of whitespaces", category=errors.HikariWarning)
        if len(value) > _MAX_FIELD_VALUE:
            warnings.warn(f"field.value must not exceed {_MAX_FIELD_VALUE} characters", category=errors.HikariWarning)

        self.fields.insert(index, EmbedField(name=name, value=value, is_inline=inline))
        return self

    # FIXME: use undefined.Undefined rather than `...`
    def edit_field(self, index: int, /, *, name: str = ..., value: str = ..., inline: bool = ...) -> Embed:
        """Edit a field in this embed at the given index.

        Unless you specify the attribute to change, it will not be changed. For
        example, you can change a field value but not the field name
        by simply specifying that parameter only.

        ```py
        >>> embed = Embed()
        >>> embed.add_field(name="foo", value="bar")
        >>> embed.edit_field(0, value="baz")
        >>> print(embed.fields[0].name)
        foo
        >>> print(embed.fields[0].value)
        baz
        ```

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
        """
        # TODO: remove these checks entirely, they will be covered by the validation in the data class.
        if name is not ... and not name.strip():
            warnings.warn("field.name must not be empty or purely of whitespaces", category=errors.HikariWarning)
        if name is not ... and len(name.strip()) > _MAX_FIELD_NAME:
            warnings.warn(f"field.name must not exceed {_MAX_FIELD_NAME} characters", category=errors.HikariWarning)

        if value is not ... and not value.strip():
            warnings.warn("field.value must not be empty or purely of whitespaces", category=errors.HikariWarning)
        if value is not ... and len(value) > _MAX_FIELD_VALUE:
            warnings.warn(f"field.value must not exceed {_MAX_FIELD_VALUE} characters", category=errors.HikariWarning)

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
