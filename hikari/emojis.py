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
"""Application and entities that are used to describe emojis on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("Emoji", "UnicodeEmoji", "CustomEmoji", "KnownCustomEmoji")

import abc
import re
import typing

import attrs

from hikari import files
from hikari import snowflakes
from hikari import urls
from hikari.internal import attrs_extensions
from hikari.internal import routes

# import unicodedata


if typing.TYPE_CHECKING:
    from hikari import traits
    from hikari import users

_TWEMOJI_PNG_BASE_URL: typing.Final[str] = "https://raw.githubusercontent.com/discord/twemoji/master/assets/72x72/"
_CUSTOM_EMOJI_REGEX: typing.Final[typing.Pattern[str]] = re.compile(r"<(?P<flags>[^:]*):(?P<name>[^:]*):(?P<id>\d+)>")


class Emoji(files.WebResource, abc.ABC):
    """Base class for all emojis.

    Any emoji implementation supports being used as a
    [hikari.files.Resource][] when uploading an attachment to the API.
    This is achieved in the same way as using a
    [hikari.files.WebResource][] would achieve this.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the generic name/representation for this emoji."""

    @property
    @abc.abstractmethod
    def url(self) -> str:
        """URL of the emoji image to display in clients."""

    @property
    @abc.abstractmethod
    def url_name(self) -> str:
        """Name of the part of the emoji to use in requests."""

    @property
    @abc.abstractmethod
    def mention(self) -> str:
        """Mention string to use to mention the emoji with."""

    @classmethod
    def parse(cls, string: str, /) -> Emoji:
        """Parse a given string into an emoji object.

        Parameters
        ----------
        string : str
            The emoji object to parse.

        Returns
        -------
        Emoji
            The parsed emoji object. This will be a [hikari.emojis.CustomEmoji][] if a custom
            emoji mention, or a [hikari.emojis.UnicodeEmoji][] otherwise.

        Raises
        ------
        ValueError
            If a mention is given that has an invalid format.
        """
        if string.startswith("<") and string.endswith(">"):
            return CustomEmoji.parse(string)
        return UnicodeEmoji.parse(string)


class UnicodeEmoji(str, Emoji):
    """Represents a unicode emoji.

    !!! warning
        A word of warning if you try to upload this emoji as a file attachment.

        While this emoji type can be used to upload the Twemoji representations
        of this emoji as a PNG, this is NOT foolproof. The mapping between
        Discord's implementation and official Twemoji bindings is very flaky.
        Responsible implementations relying on this behaviour will be
        implemented to expect this behaviour in the form of
        [hikari.errors.NotFoundError][] exceptions being raised when a mismatch may
        occur. It is also likely that this will change in the future without
        notice, so you will likely be relying on flaky behaviour.

        If this is proven to be too unstable, this functionality will be
        removed in a future release after a deprecation period.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    def name(self) -> str:
        """Return the code points which form the emoji."""
        return self

    @property
    @typing.final
    def url_name(self) -> str:
        return self

    @property
    def mention(self) -> str:
        return self

    @property
    @typing.final
    def codepoints(self) -> typing.Sequence[int]:
        """Integer codepoints that make up this emoji, as UTF-8."""
        return [ord(c) for c in self]

    @property
    def filename(self) -> str:
        """Filename to use if re-uploading this emoji's PNG."""
        codepoints = self.codepoints
        # It looks like the rule is to delete character #2 if the value
        # of this is 0xfe0f and the character is up to 4 characters long.
        # Other than that, the mapping is 1-to-1. There's a couple of outliers
        # to this 0xfe0f rule and they seem to follow a pattern where the
        # codepoint after 0xfe0f is 0x200D but this might be a coincidence and
        # if Discord start breaking this regularly I might need to ask for a
        # more permanent solution. This is provisionally provided. If we find it
        # breaks in other ways, I will just revoke this functionality in a
        # future update.
        if codepoints[1:2] == [0xFE0F] and len(codepoints) <= 4 and codepoints[2:3] != [0x200D]:
            codepoints = [codepoints[0], *codepoints[2:]]

        return "-".join(hex(c)[2:] for c in codepoints) + ".png"

    @property
    def url(self) -> str:
        """Get the URL of the PNG rendition of this emoji.

        This will use the official Twitter "twemoji" repository to fetch
        this information, as Discord only stores this in a hashed format
        that uses SVG files, which is not usually of any use.

        Since this uses "twemoji" directly, the emojis may not directly
        match what is on Discord if Discord have failed to keep their emoji
        packs up-to-date with this repository.

        Examples
        --------
        ```py
            >>> emoji = hikari.UnicodeEmoji("\N{OK HAND SIGN}")
            >>> emoji.url
            'https://raw.githubusercontent.com/discord/twemoji/master/assets/72x72/1f44c.png'
        ```
        """
        return _TWEMOJI_PNG_BASE_URL + self.filename

    # @property
    # @typing.final
    # def unicode_names(self) -> typing.Sequence[str]:
    #     """Get the unicode name of the emoji as a sequence.
    #
    #     This returns the name of each codepoint. If only one codepoint exists,
    #     then this will only have one item in the resulting sequence.
    #     """
    #     return [unicodedata.name(c) for c in self]

    @property
    @typing.final
    def unicode_escape(self) -> str:
        """Get the unicode escape string for this emoji."""
        return bytes(self, "unicode_escape").decode("utf-8")

    @classmethod
    @typing.final
    def parse_codepoints(cls, codepoint: int, *codepoints: int) -> UnicodeEmoji:
        """Create a unicode emoji from one or more UTF-32 codepoints."""
        return cls("".join(map(chr, (codepoint, *codepoints))))

    @classmethod
    @typing.final
    def parse_unicode_escape(cls, escape: str) -> UnicodeEmoji:
        """Create a unicode emoji from a unicode escape string."""
        return cls(escape.encode("utf-8"), "unicode_escape")

    @classmethod
    @typing.final
    def parse(cls, string: str, /) -> UnicodeEmoji:
        """Parse a given string into a unicode emoji object.

        Parameters
        ----------
        string : str
            The emoji object to parse.

        Returns
        -------
        UnicodeEmoji
            The parsed UnicodeEmoji object.
        """
        # TODO: Re-add validity
        # Ensure validity.
        # for i, codepoint in enumerate(string, start=1):
        #     unicodedata.name(codepoint)

        return cls(string)


@attrs_extensions.with_copy
@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class CustomEmoji(snowflakes.Unique, Emoji):
    """Represents a custom emoji.

    This is a custom emoji that is from a guild you might not be part of.

    All CustomEmoji objects and their derivatives act as valid
    [hikari.files.Resource][] objects. This means you can use them as a
    file when sending a message.

        >>> emojis = await bot.rest.fetch_guild_emojis(12345)
        >>> picks = random.choices(emojis, 5)
        >>> await event.respond(files=picks)

    !!! warning
        Discord will not provide information on whether these emojis are
        animated or not when a reaction is removed and an event is fired. This
        is problematic if you need to try and determine the emoji that was
        removed. The side effect of this means that mentions for animated emojis
        will not be correct.

        This will not be changed as stated here:
        <https://github.com/discord/discord-api-docs/issues/1614#issuecomment-628548913>
    """

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The ID of this entity."""

    name: str = attrs.field(eq=False, hash=False, repr=True)
    """The name of the emoji."""

    is_animated: bool = attrs.field(eq=False, hash=False, repr=True)
    """Whether the emoji is animated."""

    def __str__(self) -> str:
        return self.mention

    @property
    def filename(self) -> str:
        return str(self.id) + (".gif" if self.is_animated else ".png")

    @property
    @typing.final
    def url_name(self) -> str:
        return f"{self.name}:{self.id}"

    @property
    @typing.final
    def mention(self) -> str:
        return f"<{'a' if self.is_animated else ''}:{self.url_name}>"

    @property
    @typing.final
    def url(self) -> str:
        ext = "gif" if self.is_animated else "png"

        return routes.CDN_CUSTOM_EMOJI.compile(urls.CDN_URL, emoji_id=self.id, file_format=ext)

    @classmethod
    def parse(cls, string: str, /) -> CustomEmoji:
        """Parse a given emoji mention string into a custom emoji object.

        Parameters
        ----------
        string : str
            The emoji mention to parse.

        Returns
        -------
        CustomEmoji
            The parsed emoji object.

        Raises
        ------
        ValueError
            If a mention is given that has an invalid format.
        """
        if emoji_match := _CUSTOM_EMOJI_REGEX.match(string):
            return CustomEmoji(
                id=snowflakes.Snowflake(emoji_match.group("id")),
                name=emoji_match.group("name"),
                is_animated=emoji_match.group("flags").lower() == "a",
            )

        raise ValueError("Expected an emoji mention")


@attrs.define(hash=True, kw_only=True, weakref_slot=False)
class KnownCustomEmoji(CustomEmoji):
    """Represents an emoji that is known from a guild the bot is in.

    This is a specialization of [hikari.emojis.CustomEmoji][] that is from a guild that you
    _are_ part of. As a result, it contains a lot more information with it.
    """

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    guild_id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the guild this emoji belongs to."""

    role_ids: typing.Sequence[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The IDs of the roles that are whitelisted to use this emoji.

    If this is empty then any user can use this emoji regardless of their roles.
    """

    user: typing.Optional[users.User] = attrs.field(eq=False, hash=False, repr=False)
    """The user that created the emoji.

    !!! note
        This will be [None][] if you are missing the `MANAGE_EMOJIS_AND_STICKERS`
        permission in the server the emoji is from.
    """

    is_colons_required: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this emoji must be wrapped in colons."""

    is_managed: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether the emoji is managed by an integration."""

    is_available: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this emoji can currently be used.

    May be [False][] due to a loss of Sever Boosts on the emoji's guild.
    """
