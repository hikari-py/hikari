# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Application and entities that are used to describe message embeds on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "Embed",
    "EmbedResource",
    "EmbedResourceWithProxy",
    "EmbedVideo",
    "EmbedImage",
    "EmbedProvider",
    "EmbedAuthor",
    "EmbedFooter",
    "EmbedField",
)

import textwrap
import typing
import warnings

import attrs

from hikari import colors
from hikari import errors
from hikari import files
from hikari import undefined
from hikari.internal import attrs_extensions

if typing.TYPE_CHECKING:
    import concurrent.futures
    import datetime


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class EmbedResource(files.Resource[files.AsyncReader]):
    """A base type for any resource provided in an embed.

    Resources can be downloaded and uploaded.
    """

    resource: files.Resource[files.AsyncReader] = attrs.field(repr=True)
    """The resource this object wraps around."""

    @property
    @typing.final
    def url(self) -> str:
        """URL of this embed resource."""
        return self.resource.url

    @property
    def filename(self) -> str:
        """File name of this embed resource."""
        return self.resource.filename

    def stream(
        self, *, executor: typing.Optional[concurrent.futures.Executor] = None, head_only: bool = False
    ) -> files.AsyncReaderContextManager[files.AsyncReader]:
        """Produce a stream of data for the resource.

        Parameters
        ----------
        executor : typing.Optional[concurrent.futures.Executor]
            The executor to run in for blocking operations.
            If [None][], then the default executor is used for the
            current event loop.
        head_only : bool
            If [True][], then the implementation may only retrieve
            HEAD information if supported. This currently only has
            any effect for web requests.
        """
        return self.resource.stream(executor=executor, head_only=head_only)


@attrs.define(kw_only=True, weakref_slot=False)
class EmbedResourceWithProxy(EmbedResource):
    """Resource with a corresponding proxied element."""

    proxy_resource: typing.Optional[files.Resource[files.AsyncReader]] = attrs.field(default=None, repr=False)
    """The proxied version of the resource, or [None][] if not present.

    !!! note
        This field cannot be set by bots or webhooks while sending an embed
        and will be ignored during serialization. Expect this to be
        populated on any received embed attached to a message event.
    """

    @property
    @typing.final
    def proxy_url(self) -> typing.Optional[str]:
        """Proxied URL of this embed resource if applicable, else [None][]."""
        return self.proxy_resource.url if self.proxy_resource else None

    @property
    @typing.final
    def proxy_filename(self) -> typing.Optional[str]:
        """File name of the proxied version of this embed resource if applicable, else [None][]."""
        return self.proxy_resource.filename if self.proxy_resource else None


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class EmbedFooter:
    """Represents an embed footer."""

    # Discord says this is never None. We know that is invalid because Discord.py
    # sets it to None. Seems like undocumented behaviour again.
    text: typing.Optional[str] = attrs.field(default=None, repr=True)
    """The footer text, or [None][] if not present."""

    icon: typing.Optional[EmbedResourceWithProxy] = attrs.field(default=None, repr=True)
    """The URL of the footer icon, or [None][] if not present."""


@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class EmbedImage(EmbedResourceWithProxy):
    """Represents an embed image."""

    height: typing.Optional[int] = attrs.field(default=None, repr=False)
    """The height of the image, if present and known, otherwise [None][].

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event.
    """

    width: typing.Optional[int] = attrs.field(default=None, repr=False)
    """The width of the image, if present and known, otherwise [None][].

    !!! note
        This field cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event.
    """


@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class EmbedVideo(EmbedResourceWithProxy):
    """Represents an embed video.

    !!! note
        This object cannot be set by bots or webhooks while sending an embed and
        will be ignored during serialization. Expect this to be populated on
        any received embed attached to a message event with a video attached.

        **Therefore, you should never need to initialize an instance of this
        class yourself.**
    """

    height: typing.Optional[int] = attrs.field(default=None, repr=False)
    """The height of the video."""

    width: typing.Optional[int] = attrs.field(default=None, repr=False)
    """The width of the video."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
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

    name: typing.Optional[str] = attrs.field(default=None, repr=True)
    """The name of the provider."""

    url: typing.Optional[str] = attrs.field(default=None, repr=True)
    """The URL of the provider."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class EmbedAuthor:
    """Represents an author of an embed."""

    name: typing.Optional[str] = attrs.field(default=None, repr=True)
    """The name of the author, or [None][] if not specified."""

    url: typing.Optional[str] = attrs.field(default=None, repr=True)
    """The URL that the author's name should act as a hyperlink to.

    This may be [None][] if no hyperlink on the author's name is specified.
    """

    icon: typing.Optional[EmbedResourceWithProxy] = attrs.field(default=None, repr=False)
    """The author's icon, or [None][] if not present."""


@attrs_extensions.with_copy
@attrs.define(hash=False, kw_only=True, weakref_slot=False)
class EmbedField:
    """Represents a field in a embed."""

    name: str = attrs.field(repr=True)
    """The name of the field."""

    value: str = attrs.field(repr=True)
    """The value of the field."""

    _inline: bool = attrs.field(alias="inline", default=False, repr=True)

    # Use a property since we then keep the consistency of not using `is_`
    # in the constructor for `_inline`.
    @property
    def is_inline(self) -> bool:
        """Whether the field should display inline.

        Defaults to [False][].
        """
        return self._inline

    @is_inline.setter
    def is_inline(self, value: bool) -> None:
        self._inline = value


def _ensure_embed_resource(resource: files.Resourceish) -> files.Resource[files.AsyncReader]:
    if isinstance(resource, EmbedResource):
        return resource.resource

    return files.ensure_resource(resource)


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

        !!! warning
            **This function is for internal use only!**
        """
        # Create an empty instance without the overhead of invoking the regular
        # constructor.
        embed: Embed = super().__new__(cls)
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
        color: typing.Optional[colors.Colorish] = None,
        colour: typing.Optional[colors.Colorish] = None,
        timestamp: typing.Optional[datetime.datetime] = None,
    ) -> None:
        if color is not None and colour is not None:
            raise TypeError("Please provide one of color or colour to Embed(). Do not pass both.")

        if colour is not None:
            color = colour

        self._color = colors.Color.of(color) if color is not None else None

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

        This will be [None][] if not set.
        """
        return self._title

    @title.setter
    def title(self, value: typing.Any) -> None:
        self._title = str(value) if value is not None else None

    @property
    def description(self) -> typing.Optional[str]:
        """Return the description of the embed.

        This will be [None][] if not set.
        """
        return self._description

    @description.setter
    def description(self, value: typing.Any) -> None:
        self._description = str(value) if value is not None else None

    @property
    def url(self) -> typing.Optional[str]:
        """Return the URL of the embed title.

        This will be [None][] if not set.
        """
        return self._url

    @url.setter
    def url(self, value: typing.Optional[str]) -> None:
        self._url = value

    @property
    def color(self) -> typing.Optional[colors.Color]:
        """Return the colour of the embed.

        This will be [None][] if not set.
        """
        return self._color

    # As a note, MYPY currently complains about setting embed.color to a Colourish value which isn't explicitly Color.
    # see https://github.com/python/mypy/issues/3004
    @color.setter
    def color(self, value: typing.Optional[colors.Colorish]) -> None:
        self._color = colors.Color.of(value) if value is not None else None

    # Alias.
    @property
    def colour(self) -> typing.Optional[colors.Color]:
        """Alias of [hikari.colors.Color][]."""
        return self._color

    # Alias.
    # As a note, MYPY currently complains about setting embed.color to a Colourish value which isn't explicitly Color.
    # see https://github.com/python/mypy/issues/3004
    @colour.setter
    def colour(self, value: typing.Optional[colors.Colorish]) -> None:
        self._color = colors.Color.of(value) if value is not None else None

    @property
    def timestamp(self) -> typing.Optional[datetime.datetime]:
        """Return the timestamp of the embed.

        This will be [None][] if not set.

        !!! warning
            Setting a non-timezone-aware datetime will result in a warning
            being raised. This is done due to potential confusion caused by
            Discord requiring a UTC timestamp for this field. Any non-timezone
            aware timestamp is interpreted as using the system's current
            timezone instead. Thus, using [datetime.datetime.utcnow][] will
            result in a potentially incorrect timezone being set.

            To generate a timezone aware timestamp, use one of the following
            snippets:

            ```py
                # Use UTC.
                >>> datetime.datetime.now(tz=datetime.timezone.utc)
                datetime.datetime(2020, 6, 5, 18, 29, 56, 424744, tzinfo=datetime.timezone.utc)

                # Use your current timezone.
                >>> datetime.datetime.now().astimezone()
                datetime.datetime(2020, 7, 7, 8, 57, 9, 775328, tzinfo=..., 'BST'))
            ```

            By specifying a timezone, Hikari can automatically adjust the given
            time to UTC without you needing to think about it.

            You can generate a timezone-aware timestamp instead of a timezone-naive
            one by specifying a timezone. Hikari will detect any difference in
            timezone if the timestamp is non timezone-naive and fix it for you:

            ```py
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
            ```

            A library on PyPI called [tzlocal](https://pypi.org/project/tzlocal/)
            also exists that may be useful to you if you need to get your local
            timezone for any reason:

            ```py
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
            ```

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

            NOTE: datetime.utcnow WILL NOT WORK CORRECTLY WITH THIS IMPLEMENTATION.

            Relying on timezone-naive datetimes may be deprecated and result in
            an error in future releases.

            The offending line of code causing this warning was:"""
        )

        warnings.warn(message, category=errors.HikariWarning, stacklevel=3)

    @property
    def footer(self) -> typing.Optional[EmbedFooter]:
        """Return the footer of the embed.

        Will be [None][] if not set.
        """
        return self._footer

    @property
    def image(self) -> typing.Optional[EmbedImage]:
        """Return the image set in the embed.

        Will be [None][] if not set.

        !!! note
            Use [hikari.embeds.Embed.set_image][] to update this value.
        """
        return self._image

    @property
    def thumbnail(self) -> typing.Optional[EmbedImage]:
        """Return the thumbnail set in the embed.

        Will be [None][] if not set.

        !!! note
            Use [hikari.embeds.Embed.set_thumbnail][] to update this value.
        """
        return self._thumbnail

    @property
    def video(self) -> typing.Optional[EmbedVideo]:
        """Return the video to show in the embed.

        Will be [None][] if not set.

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

        Will be [None][] if not set.

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

        Will be [None][] if not set.

        !!! note
            Use [hikari.embeds.Embed.set_author][] to update this value.
        """
        return self._author

    @property
    def fields(self) -> typing.Sequence[EmbedField]:
        """Return the sequence of fields in the embed.

        !!! note
            Use [hikari.embeds.Embed.add_field][] to add a new field, [hikari.embeds.Embed.edit_field][] to edit an existing
            field, or [hikari.embeds.Embed.remove_field][] to remove a field.
        """
        return self._fields if self._fields else []

    def set_author(
        self,
        *,
        name: typing.Optional[str] = None,
        url: typing.Optional[str] = None,
        icon: typing.Optional[files.Resourceish] = None,
    ) -> Embed:
        """Set the author of this embed.

        Parameters
        ----------
        name : typing.Optional[str]
            The optional name of the author.
        url : typing.Optional[str]
            The optional URL of the author.
        icon : typing.Optional[hikari.files.Resourceish]
            The optional image to show next to the embed author.

            This can be many different things, to aid in convenience.

            - If [None][], nothing is set.
            - If a [pathlib.PurePath][] or [str][] to a valid URL, the URL
                is linked to directly.
            - Subclasses of [hikari.files.WebResource][] such as
                [hikari.files.URL][],
                [hikari.messages.Attachment][],
                [hikari.emojis.Emoji][],
                [hikari.embeds.EmbedResource][], etc will have their URL linked to directly.
                this field.
            - If a [hikari.files.Bytes][] is passed, or a [str][]
                that contains a valid data URI is passed, then this is uploaded
                as an attachment and linked into the embed.
            - If a [hikari.files.File][], [pathlib.PurePath][] or
                [str][] that is an absolute or relative path to a file
                on your file system is passed, then this resource is uploaded
                as an attachment using non-blocking code internally and linked
                into the embed.

        Returns
        -------
        Embed
            This embed. Allows for call chaining.
        """
        if name is None and url is None and icon is None:
            self._author = None
        else:
            real_icon = EmbedResourceWithProxy(resource=_ensure_embed_resource(icon)) if icon is not None else None
            self._author = EmbedAuthor(name=name, url=url, icon=real_icon)
        return self

    def set_footer(self, text: typing.Optional[str], *, icon: typing.Optional[files.Resourceish] = None) -> Embed:
        """Set the footer of this embed.

        Parameters
        ----------
        text : typing.Optional[str]
            The mandatory text string to set in the footer.
            If [None][], the footer is removed.
        icon : typing.Optional[hikari.files.Resourceish]
            The optional image to show next to the embed footer.

            This can be many different things, to aid in convenience.

            - If [None][], nothing is set.
            - If a [pathlib.PurePath][] or [str][] to a valid URL, the URL
                is linked to directly.
            - Subclasses of [hikari.files.WebResource][] such as
                [hikari.files.URL][],
                [hikari.messages.Attachment][],
                [hikari.emojis.Emoji][],
                [hikari.embeds.EmbedResource][], etc. will have their URL linked to directly.
                this field.
            - If a [hikari.files.Bytes][] is passed, or a [str][]
                that contains a valid data URI is passed, then this is uploaded
                as an attachment and linked into the embed.
            - If a [hikari.files.File][], [pathlib.PurePath][] or
                [str][] that is an absolute or relative path to a file
                on your file system is passed, then this resource is uploaded
                as an attachment using non-blocking code internally and linked
                into the embed.

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
            real_icon = EmbedResourceWithProxy(resource=_ensure_embed_resource(icon)) if icon is not None else None
            self._footer = EmbedFooter(icon=real_icon, text=text)
        return self

    def set_image(self, image: typing.Optional[files.Resourceish] = None, /) -> Embed:
        """Set the image on this embed.

        Parameters
        ----------
        image : typing.Optional[hikari.files.Resourceish]
            The optional resource to show for the embed image.

            This can be many different things, to aid in convenience.

            - If [None][], nothing is set.
            - If a [pathlib.PurePath][] or [str][] to a valid URL, the URL
                is linked to directly.
            - Subclasses of [hikari.files.WebResource][] such as
                [hikari.files.URL][],
                [hikari.messages.Attachment][],
                [hikari.emojis.Emoji][],
                [hikari.embeds.EmbedResource][], etc will have their URL linked to directly.
                this field.
            - If a [hikari.files.Bytes][] is passed, or a [str][]
                that contains a valid data URI is passed, then this is uploaded
                as an attachment and linked into the embed.
            - If a [hikari.files.File][], [pathlib.PurePath][] or
                [str][] that is an absolute or relative path to a file
                on your file system is passed, then this resource is uploaded
                as an attachment using non-blocking code internally and linked
                into the embed.

        Returns
        -------
        Embed
            This embed. Allows for call chaining.
        """
        if image is not None:
            self._image = EmbedImage(resource=_ensure_embed_resource(image))
        else:
            self._image = None

        return self

    def set_thumbnail(self, image: typing.Optional[files.Resourceish] = None, /) -> Embed:
        """Set the image on this embed.

        Parameters
        ----------
        image : typing.Optional[hikari.files.Resourceish]
            The optional resource to show for the embed thumbnail.

            This can be many different things, to aid in convenience.

            - If [None][], nothing is set.
            - If a [pathlib.PurePath][] or [str][] to a valid URL, the URL
                is linked to directly.
            - Subclasses of [hikari.files.WebResource][] such as
                [hikari.files.URL][],
                [hikari.messages.Attachment][],
                [hikari.emojis.Emoji][],
                [hikari.embeds.EmbedResource][], etc will have their URL linked to directly.
            - If a [hikari.files.Bytes][] is passed, or a [str][]
                that contains a valid data URI is passed, then this is uploaded
                as an attachment and linked into the embed.
            - If a [hikari.files.File][], [pathlib.PurePath][] or
                [str][] that is an absolute or relative path to a file
                on your file system is passed, then this resource is uploaded
                as an attachment using non-blocking code internally and linked
                into the embed.

        Returns
        -------
        Embed
            This embed. Allows for call chaining.
        """
        if image is not None:
            self._thumbnail = EmbedImage(resource=_ensure_embed_resource(image))
        else:
            self._thumbnail = None

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

        Other Parameters
        ----------------
        inline : bool
            If [True][], the embed field may be shown "inline" on some
            Discord clients with other fields. If [False][], it is always placed
            on a separate line. This will default to [False][].

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
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        value: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        /,
        *,
        inline: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> Embed:
        """Edit an existing field on this embed.

        Parameters
        ----------
        index : int
            The index of the field to edit.

        Other Parameters
        ----------------
        name : hikari.undefined.UndefinedOr[str]
            The new field name to use. If left to the default (`undefined`),
            then it will not be changed.
        value : hikari.undefined.UndefinedOr[str]
            The new field value to use. If left to the default (`undefined`),
            then it will not be changed.
        inline : hikari.undefined.UndefinedOr[bool]
            [True][] to inline the field, or [False][] to force
            it to be on a separate line. If left to the default (`undefined`),
            then it will not be changed.

        Returns
        -------
        Embed
            This embed. Allows for call chaining.

        Raises
        ------
        IndexError
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
        IndexError
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
            for attrsib in self.__slots__:
                if getattr(self, attrsib) != getattr(other, attrsib):
                    break
            else:
                return True
        return False

    def total_length(self) -> int:
        """Get the total character count of the embed.

        Returns
        -------
        int
            The total character count of this embed, including title, description,
            fields, footer, and author combined.
        """
        total = len(self._title or "") + len(self._description or "")

        if self._fields:
            for field in self._fields:
                total += len(field.name) + len(field.value)

        if self._footer and self._footer.text:
            total += len(self._footer.text)

        if self._author and self._author.name:
            total += len(self._author.name)

        return total
