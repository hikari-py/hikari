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
"""Application and entities that are used to describe stickers on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "StickerType",
    "StickerFormatType",
    "PartialSticker",
    "GuildSticker",
    "StandardSticker",
    "StickerPack",
)

import typing

import attrs

from hikari import snowflakes
from hikari import urls
from hikari.internal import attrs_extensions
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


_STICKER_EXTENSIONS: typing.Dict[typing.Union[StickerFormatType, int], str] = {
    StickerFormatType.LOTTIE: "json",
    StickerFormatType.GIF: "gif",
}


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class StickerPack(snowflakes.Unique):
    """Represents a sticker pack on Discord."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    name: str = attrs.field(eq=False, hash=False, repr=False)
    """The name of the pack."""

    description: str = attrs.field(eq=False, hash=False, repr=False)
    """The description of the pack."""

    cover_sticker_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The ID of a sticker in the pack which is shown as the pack's icon."""

    stickers: typing.Sequence[StandardSticker] = attrs.field(eq=False, hash=False, repr=False)
    """The stickers that belong to this pack."""

    sku_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the packs SKU."""

    banner_asset_id: typing.Optional[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """ID of the sticker pack's banner image, if set."""

    @property
    def banner_url(self) -> typing.Optional[files.URL]:
        """Banner URL for the pack, if set."""
        return self.make_banner_url()

    def make_banner_url(self, *, ext: str = "png", size: int = 4096) -> typing.Optional[files.URL]:
        """Generate the pack's banner image URL, if set.

        Parameters
        ----------
        ext : str
            The extension to use for this URL.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : int
            The size to set for the URL.
            Can be any power of two between `16` and `4096`.

        Returns
        -------
        typing.Optional[hikari.files.URL]
            The URL of the banner, if set.

        Raises
        ------
        ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        if self.banner_asset_id is not None:
            return routes.CDN_STICKER_PACK_BANNER.compile_to_file(
                urls.CDN_URL, hash=self.banner_asset_id, file_format=ext, size=size
            )

        return None


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class PartialSticker(snowflakes.Unique):
    """Represents the partial stickers found attached to messages on Discord."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    name: str = attrs.field(eq=False, hash=False, repr=False)
    """The name of the sticker."""

    format_type: typing.Union[StickerFormatType, int] = attrs.field(eq=False, hash=False, repr=True)
    """The format of this sticker's asset."""

    @property
    def image_url(self) -> files.URL:
        """URL for the image.

        The extension will be based on `format_type`. If `format_type` is [`hikari.stickers.StickerFormatType.LOTTIE`][],
        then the extension will be `.json`, if it's [`hikari.stickers.StickerFormatType.GIF`][] it will be `.gif`.
        Otherwise, it will be `.png`.
        """
        ext = _STICKER_EXTENSIONS.get(self.format_type, "png")

        return routes.CDN_STICKER.compile_to_file(urls.CDN_URL, sticker_id=self.id, file_format=ext)


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class StandardSticker(PartialSticker):
    """Represents a standard Discord sticker that belongs to a pack."""

    type: StickerType = attrs.field(eq=False, hash=False, repr=False, init=False, default=StickerType.STANDARD)
    """The sticker type."""

    description: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """The description of this sticker."""

    pack_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the package this sticker belongs to."""

    sort_value: int = attrs.field(eq=False, hash=False, repr=False)
    """The sort value for the sticker in its pack."""

    tags: typing.Sequence[str] = attrs.field(eq=False, hash=False, repr=True)
    """A sequence of this sticker's tags."""


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class GuildSticker(PartialSticker):
    """Represents a Discord sticker that belongs to a guild."""

    type: StickerType = attrs.field(eq=False, hash=False, repr=False, init=False, default=StickerType.GUILD)
    """The sticker type."""

    description: typing.Optional[str] = attrs.field(eq=False, hash=False, repr=False)
    """The description of this sticker."""

    guild_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False)
    """The guild this sticker belongs to."""

    is_available: bool = attrs.field(eq=False, hash=False)
    """Whether the sticker can be used."""

    tag: str = attrs.field(eq=False, hash=False)
    """This sticker's tag."""

    user: typing.Optional[users.User] = attrs.field(eq=False, hash=False, repr=False)
    """The user that uploaded this sticker.

    This will only be available if you have the [`hikari.permissions.Permissions.MANAGE_GUILD_EXPRESSIONS`][] permission.
    """
