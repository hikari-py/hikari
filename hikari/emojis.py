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

__all__: typing.Sequence[str] = ("CustomEmoji", "Emoji", "KnownCustomEmoji", "UnicodeEmoji")

import abc
import re
import typing

import attrs

from hikari import files
from hikari import snowflakes
from hikari import urls
from hikari.internal import attrs_extensions
from hikari.internal import routes
from hikari.internal import typing_extensions

if typing.TYPE_CHECKING:
    from hikari import traits
    from hikari import users

_TWEMOJI_PNG_BASE_URL: typing.Final[str] = "https://raw.githubusercontent.com/discord/twemoji/master/assets/72x72/"
_CUSTOM_EMOJI_REGEX: typing.Final[typing.Pattern[str]] = re.compile(r"<(?P<flags>[^:]*):(?P<name>[^:]*):(?P<id>\d+)>")


class Emoji(files.WebResource, abc.ABC):
    """Base class for all emojis.

    Any emoji implementation supports being used as a
    [`hikari.files.Resource`][] when uploading an attachment to the API.
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
    def parse(cls, string: str) -> "UnicodeEmoji | CustomEmoji":
        """Parse a given string into an emoji object.

        Returns a [`CustomEmoji`][] if a custom emoji mention, or a [`UnicodeEmoji`][] otherwise.

        Raises
        ------
        ValueError
            If a mention is given that has an invalid format.
        """
        if string.startswith("<") and string.endswith(">"):
            return CustomEmoji.parse(string)
        return UnicodeEmoji.parse(string)


class UnicodeEmoji(str, Emoji):
    """Represents a unicode emoji."""

    __slots__: typing.Sequence[str] = ()

    @property
    def name(self) -> str:
        """Return the code points which form the emoji."""
        return self

    @property
    def url_name(self) -> str:
        return self

    @property
    def mention(self) -> str:
        return self

    @property
    def codepoints(self) -> typing.Sequence[int]:
        """Integer codepoints that make up this emoji, as UTF-8."""
        return [ord(c) for c in self]

    @property
    def filename(self) -> str:
        """Filename to use if re-uploading this emoji's PNG."""
        codepoints = self.codepoints
        # Remove 0xfe0f if present as the second character and not followed by 0x200D
        if codepoints[1:2] == [0xFE0F] and len(codepoints) <= 4 and codepoints[2:3] != [0x200D]:
            codepoints = [codepoints[0], *codepoints[2:]]
        return "-".join(f"{c:x}" for c in codepoints) + ".png"

    @property
    def url(self) -> str:
        """Get the URL of the PNG rendition of this emoji."""
        return f"{_TWEMOJI_PNG_BASE_URL}{self.filename}"

    @property
    def unicode_escape(self) -> str:
        """Get the unicode escape string for this emoji."""
        return bytes(self, "unicode_escape").decode("utf-8")

    @classmethod
    def parse_codepoints(cls, codepoint: int, *codepoints: int) -> "UnicodeEmoji":
        """Create a unicode emoji from one or more UTF-32 codepoints."""
        return cls("".join(map(chr, (codepoint, *codepoints))))

    @classmethod
    def parse_unicode_escape(cls, escape: str) -> "UnicodeEmoji":
        """Create a unicode emoji from a unicode escape string."""
        return cls(escape.encode("utf-8"), "unicode_escape")

    @classmethod
    def parse(cls, string: str) -> "UnicodeEmoji":
        """Parse a given string into a unicode emoji object."""
        # TODO: Add validity check here (maybe use optional discord_emojis package)
        return cls(string)


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class CustomEmoji(snowflakes.Unique, Emoji):
    """Represents a custom emoji."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    name: str = attrs.field(eq=False, hash=False, repr=True)
    is_animated: bool = attrs.field(eq=False, hash=False, repr=True)

    def __str__(self) -> str:
        return self.mention

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CustomEmoji):
            return self.id == other.id
        return False

    @property
    def filename(self) -> str:
        return f"{self.id}.{'gif' if self.is_animated else 'png'}"

    @property
    def url_name(self) -> str:
        return f"{self.name}:{self.id}"

    @property
    def mention(self) -> str:
        return f"<{'a' if self.is_animated else ''}:{self.url_name}>"

    @property
    def url(self) -> str:
        ext = "gif" if self.is_animated else "png"
        return routes.CDN_CUSTOM_EMOJI.compile(urls.CDN_URL, emoji_id=self.id, file_format=ext)

    @classmethod
    def parse(cls, string: str) -> "CustomEmoji":
        """Parse a given emoji mention string into a custom emoji object."""
        if emoji_match := _CUSTOM_EMOJI_REGEX.match(string):
            return CustomEmoji(
                id=snowflakes.Snowflake(emoji_match.group("id")),
                name=emoji_match.group("name"),
                is_animated=emoji_match.group("flags").lower() == "a",
            )
        raise ValueError("Expected an emoji mention")


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class KnownCustomEmoji(CustomEmoji):
    """Represents a known emoji.

    The Emoji could be either known because the bot is part of the emoji's guild or
    because the emoji is an application emoji.

    This is a specialization of [`hikari.emojis.CustomEmoji`][] that is _known_ as mentioned before.
    As a result, it contains a lot more information with it.
    """

    app: traits.RESTAware = attrs.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """Client application that models may use for procedures."""

    guild_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=False)
    """The ID of the guild this emoji belongs to, if applicable.

    This will be [`None`][] if the emoji is an application emoji.
    """

    role_ids: typing.Sequence[snowflakes.Snowflake] = attrs.field(eq=False, hash=False, repr=False)
    """The IDs of the roles that are whitelisted to use this emoji.

    If this is empty then any user can use this emoji regardless of their roles.
    """

    user: users.User | None = attrs.field(eq=False, hash=False, repr=False)
    """The user that created the emoji.

    !!! note
        This will be [`None`][] if you are missing the [`hikari.permissions.Permissions.MANAGE_GUILD_EXPRESSIONS`][]
        permission in the server the emoji is from.
    """

    is_colons_required: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this emoji must be wrapped in colons."""

    is_managed: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether the emoji is managed by an integration."""

    is_available: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether this emoji can currently be used.

    May be [`False`][] due to a loss of Sever Boosts on the emoji's guild.
    """
