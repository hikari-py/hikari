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
"""Application and entities that are used to describe stickers on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "GuildSticker",
    "PartialSticker",
    "StandardSticker",
    "StickerFormatType",
    "StickerPack",
    "StickerType",
)

import typing

import attrs

from hikari import snowflakes
from hikari import undefined
from hikari import urls
from hikari.internal import attrs_extensions
from hikari.internal import deprecation
from hikari.internal import enums
from hikari.internal import routes

if typing.TYPE_CHECKING:
    from hikari import files
    from hikari import users


@typing.final
class StickerType(int, enums.Enum):
    """The sticker type."""

    STANDARD = 1
    """An official sticker in a pack, part of Nitro or in a removed purchasable pack."""

    GUILD = 2
    """A sticker uploaded to a guild."""


@typing.final
class StickerFormatType(int, enums.Enum):
    """The formats types of a sticker's asset."""

    PNG = 1
    """A PNG sticker."""

    APNG = 2
    """A animated PNG sticker."""

    LOTTIE = 3
    """A lottie sticker.

    More information can be found here: <https://airbnb.io/lottie/>
    """

    GIF = 4
    """A GIF sticker."""


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class StickerPack(snowflakes.Unique):
    """Represents a sticker pack on Discord."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    name: str = attrs.field(eq=False, hash=False, repr=False)
    """The name of the pack."""

    description: str = attrs.field(eq=False, hash=False, repr=False)
    """The description of the pack."""

    cover_sticker_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=False)
    """The ID of a sticker in the pack which is shown as the pack's icon."""

    stickers: typing.Sequence[StandardSticker] = attrs.field(eq=False, hash=False, repr=False)
    """The stickers that belong to this pack."""

    sku_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the packs SKU."""

    banner_asset_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=False)
    """ID of the sticker pack's banner image, if set."""

    @property
    @deprecation.deprecated("Use 'make_banner_url' instead.")
    def banner_url(self) -> files.URL | None:
        """Banner URL for the pack, if set."""
        deprecation.warn_deprecated(
            "banner_url", removal_version="2.5.0", additional_info="Use 'make_banner_url' instead."
        )
        return self.make_banner_url()

    def make_banner_url(
        self,
        *,
        file_format: typing.Literal["PNG", "JPEG", "JPG", "WEBP"] = "PNG",
        size: int = 4096,
        lossless: bool = True,
        ext: str | None | undefined.UndefinedType = undefined.UNDEFINED,
    ) -> files.URL | None:
        """Generate the pack's banner image URL, if set.

        If no banner image is set, this returns [`None`][].

        Parameters
        ----------
        file_format
            The format to use for this URL.

            Supports `PNG`, `JPEG`, `JPG`, and `WEBP`.

            If not specified, the format will be `PNG`.
        size
            The size to set for the URL;
            Can be any power of two between `16` and `4096`;
        lossless
            Whether to return a lossless or compressed WEBP image;
            This is ignored if `file_format` is not `WEBP`.
        ext
            The extension to use for this URL.
            Supports `png`, `jpeg`, `jpg` and `webp`.

            !!! deprecated 2.4.0
                This has been replaced with the `file_format` argument.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL, or [`None`][] if no banner image is set.

        Raises
        ------
        TypeError
            If an invalid format is passed for `file_format`.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        """
        if self.banner_asset_id is None:
            return None

        if ext:
            deprecation.warn_deprecated(
                "ext", removal_version="2.5.0", additional_info="Use 'file_format' argument instead."
            )
            file_format = ext.upper()  # type: ignore[assignment]

        return routes.CDN_STICKER_PACK_BANNER.compile_to_file(
            urls.CDN_URL, hash=self.banner_asset_id, size=size, file_format=file_format, lossless=lossless
        )


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class PartialSticker(snowflakes.Unique):
    """Represents the partial stickers found attached to messages on Discord."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    name: str = attrs.field(eq=False, hash=False, repr=False)
    """The name of the sticker."""

    format_type: StickerFormatType | int = attrs.field(eq=False, hash=False, repr=True)
    """The format of this sticker's asset."""

    @property
    @deprecation.deprecated("Use 'make_url' instead.")
    def image_url(self) -> files.URL:
        """Default image URL for this sticker.

        The extension will be based on `format_type`.

        If `format_type` is [`hikari.stickers.StickerFormatType.LOTTIE`][],
        then the extension will be `.json`.

        If it's [`hikari.stickers.StickerFormatType.APNG`][], then it will be `.png`.

        Otherwise, it will be follow the format type as `.gif` or `.png`.
        """
        deprecation.warn_deprecated("image_url", removal_version="2.5.0", additional_info="Use 'make_url' instead.")
        return self.make_url()

    def make_url(  # noqa: PLR0912 - Too many branches
        self,
        *,
        file_format: undefined.UndefinedOr[
            typing.Literal["LOTTIE", "PNG", "JPEG", "JPG", "WEBP", "APNG", "AWEBP", "GIF"]
        ] = undefined.UNDEFINED,
        size: int = 4096,
        lossless: bool = True,
    ) -> files.URL:
        """Generate the image URL for this sticker.

        Parameters
        ----------
        file_format
            The format to use for this URL.

            Supports `LOTTIE`, `PNG`, `JPEG`, `JPG`, `WEBP`, `APNG`, `AWEBP` and `GIF`.

            LOTTIE is only available for [`hikari.stickers.StickerFormatType.LOTTIE`][] stickers;
            If not specified, the format will be based on the format type.
        size
            The size to set for the URL;
            This is ignored for `APNG` and `LOTTIE` formats;
            Can be any power of two between `16` and `4096`.
        lossless
            Whether to return a lossless or compressed WEBP image;
            This is ignored if `file_format` is not `WEBP` or `AWEBP`.

        Returns
        -------
        hikari.files.URL
            The URL of the sticker.

        Raises
        ------
        TypeError
            If an invalid format is passed for `file_format`;
            If an animated format is requested for a static sticker;
            If an APNG sticker is requested as AWEBP or GIF;
            If a GIF sticker is requested as an APNG;
            If a LOTTIE sticker is requested as anything other than LOTTIE;
            If a non-LOTTIE sticker is requested in the LOTTIE format.
        ValueError
            If `size` is specified but is not a power of two or not between 16 and 4096.
        """
        # TODO: in the future, remove unnecessary cast
        sticker_format = StickerFormatType(self.format_type)

        if not file_format:
            if sticker_format == StickerFormatType.LOTTIE:
                file_format = "LOTTIE"
            elif sticker_format == StickerFormatType.APNG:
                file_format = "APNG"
            elif sticker_format == StickerFormatType.GIF:
                file_format = "GIF"
            else:
                file_format = "PNG"

        if sticker_format == StickerFormatType.GIF:
            if file_format == "APNG":
                msg = "This asset is a GIF, which is not available as APNG."
                raise TypeError(msg)
        elif sticker_format == StickerFormatType.APNG:
            if file_format in ("AWEBP", "GIF"):
                msg = "This asset is an APNG, which is not available as AWEBP or GIF."
                raise TypeError(msg)
        elif sticker_format == StickerFormatType.PNG:
            if file_format in {"APNG", "AWEBP", "GIF"}:
                msg = f"This asset is not animated, so it cannot be retrieved as {file_format}."
                raise TypeError(msg)
        elif sticker_format == StickerFormatType.LOTTIE and file_format != "LOTTIE":
            msg = "This asset is a LOTTIE, which is not available in alternative formats."
            raise TypeError(msg)

        if file_format == "LOTTIE" and self.format_type != StickerFormatType.LOTTIE:
            msg = "This asset is not a LOTTIE, so it cannot be retrieved in the LOTTIE format."
            raise TypeError(msg)

        return routes.CDN_STICKER.compile_to_file(
            urls.MEDIA_PROXY_URL if self.format_type != StickerFormatType.LOTTIE else urls.CDN_URL,
            sticker_id=self.id,
            file_format=file_format,
            size=size,
            lossless=lossless,
        )


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class StandardSticker(PartialSticker):
    """Represents a standard Discord sticker that belongs to a pack."""

    type: StickerType = attrs.field(eq=False, hash=False, repr=False, init=False, default=StickerType.STANDARD)
    """The sticker type."""

    description: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The description of this sticker."""

    pack_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the package this sticker belongs to."""

    sort_value: int = attrs.field(eq=False, hash=False, repr=False)
    """The sort value for the sticker in its pack."""

    tags: typing.Sequence[str] = attrs.field(eq=False, hash=False, repr=True)
    """A sequence of this sticker's tags."""


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class GuildSticker(PartialSticker):
    """Represents a Discord sticker that belongs to a guild."""

    type: StickerType = attrs.field(eq=False, hash=False, repr=False, init=False, default=StickerType.GUILD)
    """The sticker type."""

    description: str | None = attrs.field(eq=False, hash=False, repr=False)
    """The description of this sticker."""

    guild_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False)
    """The guild this sticker belongs to."""

    is_available: bool = attrs.field(eq=False, hash=False)
    """Whether the sticker can be used."""

    tag: str = attrs.field(eq=False, hash=False)
    """This sticker's tag."""

    user: users.User | None = attrs.field(eq=False, hash=False, repr=False)
    """The user that uploaded this sticker.

    This will only be available if you have the [`hikari.permissions.Permissions.MANAGE_GUILD_EXPRESSIONS`][]
    permission.
    """
