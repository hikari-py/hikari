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
"""Application and entities that are used to describe soundboard sounds on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("SoundboardSound",)

import typing

import attrs

from hikari import files
from hikari import snowflakes
from hikari import urls
from hikari.internal import attrs_extensions

if typing.TYPE_CHECKING:
    from hikari import emojis
    from hikari import users


@attrs_extensions.with_copy
@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class SoundboardSound(snowflakes.Unique):
    """Represents a soundboard sound."""

    id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """ID of the sound."""

    name: str = attrs.field(eq=False, hash=False, repr=True)
    """Name of the sound."""

    volume: float = attrs.field(eq=False, hash=False, repr=False)
    """Volume of the sound, from 0 to 1."""

    emoji: emojis.UnicodeEmoji | emojis.CustomEmoji | None = attrs.field(eq=False, hash=False, repr=False)
    """Emoji of the sound, if set."""

    guild_id: snowflakes.Snowflake | None = attrs.field(eq=False, hash=False, repr=True)
    """ID of the guild the sound belongs to.

    This will be [`None`][] for Discord's default sounds.
    """

    is_available: bool = attrs.field(eq=False, hash=False, repr=False)
    """Whether the sound can be used. This may be [`False`][] after the guild lost server boosts."""

    user: users.User | None = attrs.field(eq=False, hash=False, repr=False)
    """User who created the sound.

    Only included with the `CREATE_GUILD_EXPRESSIONS` or `MANAGE_GUILD_EXPRESSIONS` permission.
    """

    @property
    def url(self) -> files.URL:
        """URL of the sound file, served as MP3 or Ogg."""
        return files.URL(f"{urls.CDN_URL}/soundboard-sounds/{self.id}")
