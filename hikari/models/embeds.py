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

__all__: typing.Final[typing.List[str]] = [
    "Embed",
    "EmbedResource",
    "EmbedVideo",
    "EmbedImage",
    "EmbedProvider",
    "EmbedAuthor",
    "EmbedFooter",
    "EmbedField",
]

import datetime
import textwrap
import typing
import warnings

import attr

from hikari import errors
from hikari.models import colors
from hikari.utilities import files
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import concurrent.futures


@attr.s(eq=True, slots=True, kw_only=True)
class EmbedResource(files.Resource):
    """A base type for any resource provided in an embed.

    Resources can be downloaded and uploaded.
    """

    resource: files.Resource = attr.ib(repr=True)
    """The resource this object wraps around."""

    @property
    @typing.final
    def url(self) -> str:
        return self.resource.url

    @property
    def filename(self) -> str:
        return self.resource.filename

    def stream(
        self, *, executor: typing.Optional[concurrent.futures.Executor] = None, head_only: bool = False,
    ) -> files.AsyncReaderContextManager[files.ReaderImplT]:
        """Produce a stream of data for the resource.

        Parameters
        ----------
        executor : concurrent.futures.Executor or builtins.None
            The executor to run in for blocking operations.
            If `builtins.None`, then the default executor is used for the
            current event loop.
        head_only : builtins.bool
            Defaults to `builtins.False`. If `builtins.True`, then the
            implementation may only retrieve HEAD information if supported.
            This currently only has any effect for web requests.
        """
        return self.resource.stream(executor=executor, head_only=head_only)


@attr.s(eq=True, slots=True, kw_only=True)
class EmbedResourceWithProxy(EmbedResource):
    """Resource with a corresponding proxied element."""

    proxy_resource: typing.Optional[files.Resource] = attr.ib(default=None, repr=False)
    """The proxied version of the resource, or `builtins.None` if not present.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed
        and will be ignored during serialization. Expect this to be
        populated on any received embed attached to a message event.
    """


@attr.s(eq=True, hash=False, kw_only=True, slots=True)
class EmbedFooter:
    """Represents an embed footer."""

    # Discord says this is never None. We know that is invalid because Discord.py
    # sets it to None. Seems like undocumented behaviour again.
    text: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The footer text, or `builtins.None` if not present."""

    icon: typing.Optional[EmbedResourceWithProxy] = attr.ib(default=None, repr=False)
    """The URL of the footer icon, or `builtins.None` if not present."""


@attr.s(eq=True, hash=False, kw_only=True, slots=True)
class EmbedImage(EmbedResourceWithProxy):
    """Represents an embed image."""

    height: typing.Optional[int] = attr.ib(default=None, repr=False)
    """The height of the image, if present and known, otherwise `builtins.None`.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event.
    """

    width: typing.Optional[int] = attr.ib(default=None, repr=False)
    """The width of the image, if present and known, otherwise `builtins.None`.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event.
    """


@attr.s(eq=True, hash=False, kw_only=True, slots=True)
class EmbedVideo(EmbedResource):
    """Represents an embed video.

    !!! note
        This object cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event with a video attached.

        **Therefore, you should never need to initialize an instance of this
        class yourself.**
    """

    height: typing.Optional[int] = attr.ib(default=None, repr=False)
    """The height of the video."""

    width: typing.Optional[int] = attr.ib(default=None, repr=False)
    """The width of the video."""


@attr.s(eq=True, hash=False, kw_only=True, slots=True)
class EmbedProvider:
    """Represents an embed provider.

    !!! note
        This object cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event provided by an external
        source.

        **Therefore, you should never need to initialize an instance of this
        class yourself.**
    """

    name: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The name of the provider."""

    url: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The URL of the provider."""


@attr.s(eq=True, hash=False, kw_only=True, slots=True)
class EmbedAuthor:
    """Represents an author of an embed."""

    name: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The name of the author, or `builtins.None` if not specified."""

    url: typing.Optional[str] = attr.ib(default=None, repr=True)
    """The URL that the author's name should act as a hyperlink to.

    This may be `builtins.None` if no hyperlink on the author's name is specified.
    """

    icon: typing.Optional[EmbedResourceWithProxy] = attr.ib(default=None, repr=False)
    """The author's icon, or `builtins.None` if not present."""


@attr.s(eq=True, hash=False, kw_only=True, slots=True)
class EmbedField:
    """Represents a field in a embed."""

    name: str = attr.ib(repr=True)
    """The name of the field."""

    value: str = attr.ib(repr=True)
    """The value of the field."""

    _inline: bool = attr.ib(default=False, repr=True)

    # Use a property since we then keep the consistency of not using `is_`
    # in the constructor for `_inline`.
    @property
    def is_inline(self) -> bool:
        """Return `builtins.True` if the field should display inline.

        Defaults to False.
        """
        return self._inline

    @is_inline.setter
    def is_inline(self, value: bool) -> None:
        self._inline = value


class Embed:
    """Represents an embed."""

    __slots__: typing.Sequence[str] = (
        "_title",
        "_description",
        "_url",
        "_color",
        "_timestamp",
        "_footer",
        "_image",
        "_thumbnail",
        "_video",
        "_provider",
        "_author",
        "_fields",
    )

    # Don't document this.
    __pdoc__: typing.Final[typing.ClassVar[typing.Mapping[str, typing.Any]]] = {"from_received_embed": False}

    @classmethod
    def from_received_embed(
        cls,
        *,
        title: typing.Optional[str],
        description: typing.Optional[str],
        url: typing.Optional[str],
        color: typing.Optional[colors.Color],
        timestamp: typing.Optional[datetime.datetime],
        image: typing.Optional[EmbedImage],
        thumbnail: typing.Optional[EmbedImage],
        video: typing.Optional[EmbedVideo],
        author: typing.Optional[EmbedAuthor],
        provider: typing.Optional[EmbedProvider],
        footer: typing.Optional[EmbedFooter],
        fields: typing.Optional[typing.MutableSequence[EmbedField]],
    ) -> Embed:
        """Generate an embed from the given attributes.

        You should never call this.
        """
        # Create an empty instance without the overhead of invoking the regular
        # constructor.
        embed = super().__new__(cls)  # type: Embed
        embed._title = title
        embed._description = description
        embed._url = url
        embed._color = color
        embed._timestamp = timestamp
        embed._image = image
        embed._thumbnail = thumbnail
        embed._video = video
        embed._author = author
        embed._provider = provider
        embed._footer = footer
        embed._fields = fields
        return embed

    def __init__(
        self,
        *,
        title: typing.Any = None,
        description: typing.Any = None,
        url: typing.Optional[str] = None,
        color: typing.Optional[colors.ColorLike] = None,
        colour: typing.Optional[colors.ColorLike] = None,
        timestamp: typing.Optional[datetime.datetime] = None,
    ) -> None:
        if color is not None and colour is not None:
            raise TypeError("Please provide one of color or colour to Embed(). Do not pass both.")

        # MyPy doesn't like me "phrasing" this in a different way... annoyingly.
        # Probably a MyPy bug.
        if color is None:
            if colour is None:
                self._color = None
            else:
                self._color = colors.Color.of(colour)
        else:
            self._color = colors.Color.of(color)

        if timestamp is not None and timestamp.tzinfo is None:
            self.__warn_naive_datetime()
            timestamp = timestamp.astimezone()

        self._timestamp = timestamp

        self.title = title
        self.description = description
        self.url = url
        self._author: typing.Optional[EmbedAuthor] = None
        self._image: typing.Optional[EmbedImage] = None
        self._video: typing.Optional[EmbedVideo] = None
        self._provider: typing.Optional[EmbedProvider] = None
        self._thumbnail: typing.Optional[EmbedImage] = None
        self._footer: typing.Optional[EmbedFooter] = None

        # More boilerplate to allow this to be optional, but saves a useless list on every embed
        # when we don't always need it.
        self._fields: typing.Optional[typing.MutableSequence[EmbedField]] = None

    @property
    def title(self) -> typing.Optional[str]:
        """Return the title of the embed.

        This will be `builtins.None` if not set.

        Returns
        -------
        builtins.str or bultins.None
            The title of the embed.
        """
        return self._title

    @title.setter
    def title(self, value: typing.Any) -> None:
        self._title = str(value) if value is not None else None

    @property
    def description(self) -> typing.Optional[str]:
        """Return the description of the embed.

        This will be `builtins.None` if not set.

        Returns
        -------
        builtins.str or bultins.None
            The description of the embed.
        """
        return self._description

    @description.setter
    def description(self, value: typing.Any) -> None:
        self._description = str(value) if value is not None else None

    @property
    def url(self) -> typing.Optional[str]:
        """Return the URL of the embed title.

        This will be `builtins.None` if not set.

        Returns
        -------
        builtins.str or bultins.None
            The URL of the embed title
        """
        return self._url

    @url.setter
    def url(self, value: typing.Optional[str]) -> None:
        self._url = value

    @property
    def color(self) -> typing.Optional[colors.Color]:
        """Return the colour of the embed.

        This will be `builtins.None` if not set.

        Returns
        -------
        hikari.models.colors.Color or builtins.None
            The colour that is set.
        """
        return self._color

    @color.setter
    def color(self, value: typing.Optional[colors.ColorLike]) -> None:
        self._color = colors.Color.of(value) if value is not None else None

    # Alias.
    colour = color

    @property
    def timestamp(self) -> typing.Optional[datetime.datetime]:
        """Return the timestamp of the embed.

        This will be `builtins.None` if not set.

        Returns
        -------
        datetime.datetime or builtins.None
            The timestamp set on the embed.

        !!! warning
            Setting a non-timezone-aware datetime will result in a warning
            being raised. This is done due to potential confusion caused by
            Discord requiring a UTC timestamp for this field. Any non-timezone
            aware timestamp is interpreted as using the system's current
            timezone instead. Thus, using `datetime.datetime.utcnow` will
            result in a potentially incorrect timezone being set.

            To generate a timezone aware timestamp, use one of the following
            snippets:

                # Use UTC.
                >>> datetime.datetime.now(tz=datetime.timezone.utc)
                datetime.datetime(2020, 6, 5, 18, 29, 56, 424744, tzinfo=datetime.timezone.utc)

                # Use your current timezone.
                >>> datetime.datetime.now().astimezone()
                datetime.datetime(2020, 7, 7, 8, 57, 9, 775328, tzinfo=..., 'BST'))

            By specifying a timezone, Hikari can automatically adjust the given
            time to UTC without you needing to think about it.

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
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: typing.Optional[datetime.datetime]) -> None:
        if value is not None and value.tzinfo is None:
            self.__warn_naive_datetime()
            value = value.astimezone()

        self._timestamp = value

    @staticmethod
    def __warn_naive_datetime() -> None:
        message = textwrap.dedent(
            """
            You forgot to set a timezone on the timestamp you just set in an embed!

            Hikari converts all datetime objects to UTC (GMT+0) internally, since
            Discord expects all timestamps to be provided using UTC. This means
            that failing to set a timezone may result in bugs where the time appears
            to be incorrectly offset by several hours.

            To avoid this, you should tell the datetime to use the system timezone
            explicitly, or specify a timezone when creating your datetime object.
            Hikari will detect this and perform the correct conversion for you.

              timestamp = datetime.datetime.now().astimezone()
              # or
              timestamp = datetime.datetime.now(tz=datetime.timezone.utc)

            Relying on timezone-naive datetimes may be deprecated and result in
            an error in future releases.

            The offending line of code causing this warning was:"""
        )

        warnings.warn(
            message, category=errors.HikariWarning, stacklevel=3,
        )

    @property
    def footer(self) -> typing.Optional[EmbedFooter]:
        """Return the footer of the embed.

        Will be `builtins.None` if not set.

        EmbedFooter or builtins.None
            The footer of the embed.
        """
        return self._footer

    @property
    def image(self) -> typing.Optional[EmbedImage]:
        """Return the image set in the embed.

        Will be `builtins.None` if not set.

        EmbedImage or builtins.None
            The image of the embed.

        !!! note
            Use `set_image` to update this value.
        """
        return self._image

    @property
    def thumbnail(self) -> typing.Optional[EmbedImage]:
        """Return the thumbnail set in the embed.

        Will be `builtins.None` if not set.

        EmbedImage or builtins.None
            The thumbnail of the embed.

        !!! note
            Use `set_thumbnail` to update this value.
        """
        return self._thumbnail

    @property
    def video(self) -> typing.Optional[EmbedVideo]:
        """Return the video to show in the embed.

        Will be `builtins.None` if not set.

        Returns
        -------
        EmbedVideo or builtins.None
            The video of the embed.

        !!! note
            This object cannot be set by bots or webhooks while sending an embed
            and will be ignored during serialization. Expect this to be
            populated on any received embed attached to a message event with a
            video attached.
        """
        return self._video

    @property
    def provider(self) -> typing.Optional[EmbedProvider]:
        """Return the provider to show in the embed.

        Will be `builtins.None` if not set.

        Returns
        -------
        EmbedProvider or builtins.None
            The provider of the embed.

        !!! note
            This object cannot be set by bots or webhooks while sending an embed
            and will be ignored during serialization. Expect this to be
            populated on any received embed attached to a message event with a
            custom provider set.
        """
        return self._provider

    @property
    def author(self) -> typing.Optional[EmbedAuthor]:
        """Return the author to show in the embed.

        Will be `builtins.None` if not set.

        Returns
        -------
        EmbedAuthor or builtins.None
            The author of the embed.

        !!! note
            Use `set_author` to update this value.
        """
        return self._author

    @property
    def fields(self) -> typing.Sequence[EmbedField]:
        """Return the sequence of fields in the embed.

        !!! note
            Use `add_field` to add a new field, `edit_field` to edit an existing
            field, or `remove_field` to remove a field.
        """
        return self._fields if self._fields else []

    def set_author(
        self,
        *,
        name: typing.Optional[str] = None,
        url: typing.Optional[str] = None,
        icon: typing.Union[None, str, files.Resource] = None,
    ) -> Embed:
        """Set the author of this embed.

        Parameters
        ----------
        name : builtins.str or builtins.None
            The optional name of the author.
        url : builtins.str or builtins.None
            The optional URL of the author.
        icon : hikari.utilities.files.Resource or builtins.str or builtins.None
            The optional resource to show next to the embed author. Can be set
            to a string URL alternatively, or `None` to clear it.
            Setting a `hikari.utilities.files.Bytes` or
            `hikari.utilities.files.File` will result in the image being
            uploaded as an attachment with the message when sent. Setting a
            `hikari.utilities.files.WebResource` or `hikari.utilities.files.URL`
            will simply link to that URL from Discord rather than re-uploading
            it.

        Returns
        -------
        Embed
            This embed. Allows for call chaining.
        """
        if name is None and url is None and icon is None:
            self._author = None
        else:
            self._author = EmbedAuthor()
            self._author.name = name
            self._author.url = url
            if icon is not None:
                self._author.icon = EmbedResourceWithProxy(resource=files.ensure_resource(icon))
            else:
                self._author.icon = None
        return self

    def set_footer(self, *, text: typing.Optional[str], icon: typing.Union[None, str, files.Resource] = None) -> Embed:
        """Set the footer of this embed.

        Parameters
        ----------
        text : str or builtins.None
            The mandatory text string to set in the footer.
            If `builtins.None`, the footer is removed.
        icon : hikari.utilities.files.Resource or builtins.str or builtins.None
            The optional resource to show next to the embed footer. Can be set
            to a string URL alternatively, or `None` to clear it.
            Setting a `hikari.utilities.files.Bytes` or
            `hikari.utilities.files.File` will result in the image being
            uploaded as an attachment with the message when sent. Setting a
            `hikari.utilities.files.WebResource` or `hikari.utilities.files.URL`
            will simply link to that URL from Discord rather than re-uploading
            it.

        Returns
        -------
        Embed
            This embed. Allows for call chaining.
        """
        if text is None:
            if icon is not None:
                raise TypeError(
                    "Cannot specify footer text in embed to be None while setting a non-None icon. "
                    "Set some textual content in order to use a footer icon."
                )

            self._footer = None
        else:
            self._footer = EmbedFooter()
            self._footer.text = text
            if icon is not None:
                self._footer.icon = EmbedResourceWithProxy(resource=files.ensure_resource(icon))
            else:
                self._footer.icon = None
        return self

    def set_image(self, image: typing.Union[None, str, files.Resource] = None, /) -> Embed:
        """Set the image on this embed.

        Parameters
        ----------
        image : hikari.utilities.files.Resource or builtins.str or builtins.None
            The optional resource to show for the embed image. Can be set
            to a string URL alternatively, or `None` to clear it.
            Setting a `hikari.utilities.files.Bytes` or
            `hikari.utilities.files.File` will result in the image being
            uploaded as an attachment with the message when sent. Setting a
            `hikari.utilities.files.WebResource` or `hikari.utilities.files.URL`
            will simply link to that URL from Discord rather than re-uploading
            it.

        Returns
        -------
        Embed
            This embed. Allows for call chaining.
        """
        self._image = EmbedImage(resource=files.ensure_resource(image)) if image is not None else None
        return self

    def set_thumbnail(self, image: typing.Union[None, str, files.Resource] = None, /) -> Embed:
        """Set the image on this embed.

        Parameters
        ----------
        image : hikari.utilities.files.Resource or builtins.str or builtins.None
            The optional resource to show for the embed thumbnail. Can be set
            to a string URL alternatively, or `None` to clear it.
            Setting a `hikari.utilities.files.Bytes` or
            `hikari.utilities.files.File` will result in the image being
            uploaded as an attachment with the message when sent. Setting a
            `hikari.utilities.files.WebResource` or `hikari.utilities.files.URL`
            will simply link to that URL from Discord rather than re-uploading
            it.

        Returns
        -------
        Embed
            This embed. Allows for call chaining.
        """
        self._thumbnail = EmbedImage(resource=files.ensure_resource(image)) if image is not None else None
        return self

    def add_field(self, name: str, value: str, *, inline: bool = False) -> Embed:
        """Add a new field to this embed.

        Parameters
        ----------
        name : str
            The mandatory non-empty field name. This must contain at least one
            non-whitespace character to be valid.
        value : str
            The mandatory non-empty field value. This must contain at least one
            non-whitespace character to be valid.
        inline : bool
            If `builtins.True`, the embed field may be shown "inline" on some
            Discord clients with other fields. If `builtins.False`, it is always placed
            on a separate line. This will default to `builtins.False`.

        Returns
        -------
        Embed
            This embed. Allows for call chaining.
        """
        if self._fields is None:
            self._fields = []
        self._fields.append(EmbedField(name=name, value=value, inline=inline))
        return self

    def edit_field(
        self,
        index: int,
        name: typing.Union[str, undefined.UndefinedType] = undefined.UNDEFINED,
        value: typing.Union[str, undefined.UndefinedType] = undefined.UNDEFINED,
        /,
        *,
        inline: typing.Union[bool, undefined.UndefinedType] = undefined.UNDEFINED,
    ) -> Embed:
        """Edit an existing field on this embed.

        Parameters
        ----------
        index : int
            The index of the field to edit.
        name : str or hikari.utilities.undefined.UndefinedType
            The new field name to use. If left to the default (`undefined`),
            then it will not be changed.
        value : str or hikari.utilities.undefined.UndefinedType
            The new field value to use. If left to the default (`undefined`),
            then it will not be changed.
        inline : bool or hikari.utilities.undefined.UndefinedType
            `builtins.True` to inline the field, or `builtins.False` to force
            it to be on a separate line. If left to the default (`undefined`),
            then it will not be changed.

        Returns
        -------
        Embed
            This embed. Allows for call chaining.

        Raises
        ------
        builtins.IndexError
            Raised if the index is greater than `len(embed.fields) - 1` or
            less than `-len(embed.fields)`
        """
        if not self._fields:
            raise IndexError(index)

        field = self._fields[index]
        if name is not undefined.UNDEFINED:
            field.name = name
        if value is not undefined.UNDEFINED:
            field.value = value
        if inline is not undefined.UNDEFINED:
            field.is_inline = inline
        return self

    def remove_field(self, index: int, /) -> Embed:
        """Remove an existing field from this embed.

        Parameters
        ----------
        index : int
            The index of the embed field to remove.

        Returns
        -------
        Embed
            This embed. Allows for call chaining.

        Raises
        ------
        builtins.IndexError
            Raised if the index is greater than `len(embed.fields) - 1` or
            less than `-len(embed.fields)`
        """
        if self._fields:
            del self._fields[index]
        if not self._fields:
            self._fields = None
        return self

    def __repr__(self) -> str:
        return f"Embed(title={self.title}, color={self.color}, timestamp={self.timestamp})"

    def __eq__(self, other: typing.Any) -> bool:
        if isinstance(other, type(self)):
            for attrib in self.__slots__:
                if getattr(self, attrib) != getattr(other, attrib):
                    break
            else:
                return True
        return False
