# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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

__all__: typing.List[str] = [
    "StickerType",
    "StickerFormatType",
    "PartialSticker",
    "GuildSticker",
    "StandardSticker",
    "StickerPack",
]

import typing

import attr

from hikari import snowflakes
from hikari import urls
from hikari.internal import attr_extensions
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

    More information can be found here: https://airbnb.io/lottie/
    """


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class StickerPack(snowflakes.Unique):
    """Represents a sticker pack on Discord."""

    id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    """The ID of this entity."""

    name: str = attr.field(eq=False, hash=False, repr=False)
    """The name of the pack."""

    description: str = attr.field(eq=False, hash=False, repr=False)
    """The description of the pack."""

    cover_sticker_id: typing.Optional[snowflakes.Snowflake] = attr.field(eq=False, hash=False, repr=False)
    """The ID of a sticker in the pack which is shown as the pack's icon"""

    stickers: typing.Sequence[StandardSticker] = attr.field(eq=False, hash=False, repr=False)
    """The stickers that belong to this pack."""

    sku_id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=False)
    """The ID of the packs SKU."""

    # This is not exactly how Discord documents it, but we need to keep consistency
    banner_hash: str = attr.field(eq=False, hash=False, repr=False)
    """The hash for the pack's banner."""

    @property
    def banner_url(self) -> files.URL:
        """Banner URL for the pack."""
        return self.make_banner_url()

    def make_banner_url(self, *, ext: str = "png", size: int = 4096) -> files.URL:
        """Generate the pack's banner image URL.

        Parameters
        ----------
        ext : builtins.str
            The extension to use for this URL, defaults to `png`.
            Supports `png`, `jpeg`, `jpg` and `webp`.
        size : builtins.int
            The size to set for the URL, defaults to `4096`.
            Can be any power of two between 16 and 4096.

        Returns
        -------
        hikari.files.URL
            The URL of the banner.

        Raises
        ------
        builtins.ValueError
            If `size` is not a power of two or not between 16 and 4096.
        """
        return routes.CDN_STICKER_PACK_BANNER.compile_to_file(
            urls.CDN_URL, hash=self.banner_hash, file_format=ext, size=size
        )


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class PartialSticker(snowflakes.Unique):
    """Represents the partial stickers found attached to messages on Discord."""

    id: snowflakes.Snowflake = attr.field(hash=True, repr=True)
    """The ID of this entity."""

    name: str = attr.field(eq=False, hash=False, repr=False)
    """The name of the sticker."""

    format_type: typing.Union[StickerFormatType, int] = attr.field(eq=False, hash=False, repr=True)
    """The format of this sticker's asset."""

    @property
    def image_url(self) -> files.URL:
        """URL for the image.

        The extension will be based on `format_type`. If `format_type` is `StickerFormatType.LOTTIE`,
        then the extension will be `.json`. Otherwise, it will be `.png`.
        """
        ext = "json" if self.format_type is StickerFormatType.LOTTIE else "png"

        return routes.CDN_STICKER.compile_to_file(urls.CDN_URL, sticker_id=self.id, file_format=ext)


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class StandardSticker(PartialSticker):
    """Represents a standard Discord sticker that belongs to a pack."""

    type: StickerType = attr.field(eq=False, hash=False, repr=False, init=False, default=StickerType.STANDARD)
    """The sticker type."""

    description: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The description of this sticker."""

    pack_id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """ID of the package this sticker belongs to."""

    sort_value: int = attr.field(eq=False, hash=False, repr=False)
    """The sort value for the sticker in its pack."""

    tags: typing.Sequence[str] = attr.field(eq=False, hash=False, repr=True)
    """A sequence of this sticker's tags."""


@attr_extensions.with_copy
@attr.define(hash=True, kw_only=True, weakref_slot=False)
class GuildSticker(PartialSticker):
    """Represents a Discord sticker that belongs to a guild."""

    type: StickerType = attr.field(eq=False, hash=False, repr=False, init=False, default=StickerType.GUILD)
    """The sticker type."""

    description: typing.Optional[str] = attr.field(eq=False, hash=False, repr=False)
    """The description of this sticker."""

    guild_id: snowflakes.Snowflake = attr.field(eq=False, hash=False)
    """The guild this sticker belongs to"""

    is_available: bool = attr.field(eq=False, hash=False)
    """Whether the sticker can be used."""

    tag: str = attr.field(eq=False, hash=False)
    """This sticker's tag."""

    user: typing.Optional[users.User] = attr.field(eq=False, hash=False, repr=False)
    """The user that uploaded this sticker.

    This will only available if you have the `MANAGE_EMOJIS_AND_STICKERS` permission.
    """
