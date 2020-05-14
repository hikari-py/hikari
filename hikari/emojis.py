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
"""Components and entities that are used to describe both custom and Unicode emojis on Discord."""

from __future__ import annotations

__all__ = ["Emoji", "UnicodeEmoji", "CustomEmoji", "KnownCustomEmoji"]

import abc
import typing
import unicodedata

import attr

from hikari import bases
from hikari import files
from hikari import users
from hikari.internal import marshaller
from hikari.internal import urls

if typing.TYPE_CHECKING:
    from hikari.internal import more_typing


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class Emoji(bases.Entity, marshaller.Deserializable, files.BaseStream, abc.ABC):
    """Base class for all emojis.

    Any emoji implementation supports being used as a `hikari.files.BaseStream`
    when uploading an attachment to the API. This is achieved in the same
    way as using a `hikari.files.WebResourceStream` would achieve this.
    """

    @property
    @abc.abstractmethod
    def url(self) -> str:
        """URL of the emoji image to display in clients."""

    @property
    @abc.abstractmethod
    def url_name(self) -> str:
        """Name of the part of the emoji to use in requests."""

    @property
    def is_mentionable(self) -> bool:
        """Whether the emoji can be mentioned or not."""
        return True

    @property
    @abc.abstractmethod
    def mention(self) -> str:
        """Mention string to use to mention the emoji with."""

    def __aiter__(self) -> typing.AsyncIterator[bytes]:
        return files.WebResourceStream(self.filename, self.url).__aiter__()


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class UnicodeEmoji(Emoji):
    """Represents a unicode emoji.

    !!! warn
        A word of warning if you try to upload this emoji as a file attachment.

        While this emoji type can be used to upload the Twemoji representations
        of this emoji as a PNG, this is NOT foolproof. The mapping between
        Discord's implementation and official Twemoji bindings is very flaky.
        Responsible implementations relying on this behaviour will be
        implemented to expect this behaviour in the form of
        `hikari.errors.NotFound` exceptions being raised when a mismatch may
        occur. It is also likely that this will change in the future without
        notice, so you will likely be relying on flaky behaviour.

        If this is proven to be too unstable, this functionality will be
        removed in a future release after a deprecation period.
    """

    name: str = marshaller.attrib(deserializer=str, eq=True, hash=True, repr=True)
    """The code points that form the emoji."""

    @property
    def url_name(self) -> str:
        return self.name

    @property
    def mention(self) -> str:
        return self.name

    @property
    def codepoints(self) -> typing.Sequence[int]:
        """Integer codepoints that make up this emoji, as UTF-8."""
        return [ord(c) for c in self.name]

    @property
    def filename(self) -> str:
        """Filename to use if re-uploading this emoji's PNG."""
        codepoints = self.codepoints
        # It looks like the rule is to delete character #2 if the value
        # of this is 0xfe0f and the character is 4 characters long.
        # Other than that, the mapping is 1-to-1. I'll set up a CI task to
        # double check this each day so we know when Discord breaks it again.
        # The gay-pride flag is an outlier, for god knows what reason. I don't
        # care that much but if Discord start breaking this regularly I might
        # need to ask for a more permanent solution.
        # This is provisionally provided. If we find it breaks in other ways, I
        # will just revoke this functionality in a future update.
        if codepoints[1:2] == [0xFE0F] and len(codepoints) <= 4 and codepoints != [0x1F3F3, 0xFE0F, 0x200D, 0x1F308]:
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

        Example
        -------
            https://github.com/twitter/twemoji/raw/master/assets/72x72/1f004.png
        """
        return urls.TWEMOJI_PNG_BASE_URL + self.filename

    @property
    def unicode_names(self) -> typing.Sequence[str]:
        """Get the unicode name of the emoji as a sequence.

        This returns the name of each codepoint. If only one codepoint exists,
        then this will only have one item in the resulting sequence.
        """
        return [unicodedata.name(c) for c in self.name]

    @property
    def unicode_escape(self) -> str:
        """Get the unicode escape string for this emoji."""
        return bytes(self.name, "unicode_escape").decode("utf-8")

    @classmethod
    def from_codepoints(cls, codepoint: int, *codepoints: int) -> UnicodeEmoji:
        """Create a unicode emoji from one or more UTF-32 codepoints."""
        return UnicodeEmoji(name="".join(map(chr, (codepoint, *codepoints))))

    @classmethod
    def from_emoji(cls, emoji: str) -> UnicodeEmoji:
        """Create a unicode emoji from a raw emoji."""
        return cls(name=emoji)

    @classmethod
    def from_unicode_escape(cls, escape: str) -> UnicodeEmoji:
        """Create a unicode emoji from a unicode escape string."""
        return cls(name=str(escape.encode("utf-8"), "unicode_escape"))


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class CustomEmoji(Emoji, bases.Unique):
    """Represents a custom emoji.

    This is a custom emoji that is from a guild you might not be part of.

    All CustomEmoji objects and their derivatives act as valid
    `hikari.files.BaseStream` objects. This means you can use them as a
    file when sending a message.

        >>> emojis = await bot.rest.fetch_guild_emojis(12345)
        >>> picks = random.choices(emojis, 5)
        >>> await event.reply(files=picks)

    !!! warning
        Discord will not provide information on whether these emojis are
        animated or not when a reaction is removed and an event is fired. This
        is problematic if you need to try and determine the emoji that was
        removed. The side effect of this means that mentions for animated emojis
        will not be correct.

        Track this issue here:
        https://github.com/discord/discord-api-docs/issues/1614
    """

    name: typing.Optional[str] = marshaller.attrib(deserializer=str, if_none=None, eq=False, hash=False, repr=True)
    """The name of the emoji."""

    is_animated: typing.Optional[bool] = marshaller.attrib(
        raw_name="animated",
        deserializer=bool,
        if_undefined=False,
        if_none=None,
        default=False,
        eq=False,
        hash=False,
        repr=True,
    )
    """Whether the emoji is animated.

    Will be `None` when received in Message Reaction Remove and Message
    Reaction Remove Emoji events.
    """

    @property
    def filename(self) -> str:
        return str(self.id) + (".gif" if self.is_animated else ".png")

    @property
    def url_name(self) -> str:
        return f"{self.name}:{self.id}"

    @property
    def mention(self) -> str:
        return f"<{'a' if self.is_animated else ''}:{self.url_name}>"

    @property
    def is_mentionable(self) -> bool:
        return self.is_animated is not None

    @property
    def url(self) -> str:
        return urls.generate_cdn_url("emojis", str(self.id), format_="gif" if self.is_animated else "png", size=None)


def _deserialize_role_ids(payload: more_typing.JSONArray) -> typing.Set[bases.Snowflake]:
    return {bases.Snowflake(role_id) for role_id in payload}


@marshaller.marshallable()
@attr.s(eq=True, hash=True, kw_only=True, slots=True)
class KnownCustomEmoji(CustomEmoji):
    """Represents an emoji that is known from a guild the bot is in.

    This is a specialization of `CustomEmoji` that is from a guild that you
    _are_ part of. Ass a result, it contains a lot more information with it.
    """

    role_ids: typing.Set[bases.Snowflake] = marshaller.attrib(
        raw_name="roles", deserializer=_deserialize_role_ids, if_undefined=set, eq=False, hash=False, factory=set,
    )
    """The IDs of the roles that are whitelisted to use this emoji.

    If this is empty then any user can use this emoji regardless of their roles.
    """

    user: typing.Optional[users.User] = marshaller.attrib(
        deserializer=users.User.deserialize,
        if_none=None,
        if_undefined=None,
        inherit_kwargs=True,
        default=None,
        eq=False,
        hash=False,
    )
    """The user that created the emoji.

    !!! note
        This will be `None` if you are missing the `MANAGE_EMOJIS`
        permission in the server the emoji is from.
    """

    is_animated: bool = marshaller.attrib(
        raw_name="animated", deserializer=bool, if_undefined=False, default=False, eq=False, hash=False, repr=True
    )
    """Whether the emoji is animated.

    Unlike in `CustomEmoji`, this information is always known, and will thus never be `None`.
    """

    is_colons_required: bool = marshaller.attrib(raw_name="require_colons", deserializer=bool, eq=False, hash=False)
    """Whether this emoji must be wrapped in colons."""

    is_managed: bool = marshaller.attrib(raw_name="managed", deserializer=bool, eq=False, hash=False)
    """Whether the emoji is managed by an integration."""

    is_available: bool = marshaller.attrib(raw_name="available", deserializer=bool, eq=False, hash=False)
    """Whether this emoji can currently be used.

    May be `False` due to a loss of Sever Boosts on the emoji's guild.
    """


def deserialize_reaction_emoji(payload: typing.Dict, **kwargs: typing.Any) -> typing.Union[UnicodeEmoji, CustomEmoji]:
    """Deserialize a reaction emoji into an emoji."""
    if payload.get("id"):
        return CustomEmoji.deserialize(payload, **kwargs)

    return UnicodeEmoji.deserialize(payload, **kwargs)
