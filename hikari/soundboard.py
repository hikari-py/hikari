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
"""Application and entities that are used to describe stage instances on Discord."""

from __future__ import annotations

__all__: typing.Sequence[str] = ("SoundboardSound",)

import typing

import attrs

from hikari import emojis
from hikari import snowflakes
from hikari import undefined
from hikari import users


@attrs.define(unsafe_hash=True, kw_only=True, weakref_slot=False)
class SoundboardSound(snowflakes.Unique):
    """Represents a soundboard sound."""

    id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the sound."""

    name: str = attrs.field(hash=True, repr=True)
    """The name of the sound."""

    volume: float = attrs.field(hash=True, repr=True)
    """The volume of the sound."""

    emoji: emojis.UnicodeEmoji | emojis.CustomEmoji | None = attrs.field(hash=True, repr=True)
    """The emoji of the sound."""

    guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = attrs.field(hash=True, repr=False)
    """The guild ID of the stage instance."""

    is_available: bool = attrs.field(hash=True, repr=False)
    """Whether this sound can be used, or lost due to insufficient boosting."""

    user: undefined.UndefinedOr[users.PartialUser] = attrs.field(hash=True, repr=False)
    """The user who created the sound."""
