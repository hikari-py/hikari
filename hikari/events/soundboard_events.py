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
"""Events pertaining to manipulation of roles within guilds."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "SoundboardSoundCreateEvent",
    "SoundboardSoundDeleteEvent",
    "SoundboardSoundEvent",
    "SoundboardSoundUpdateEvent",
    "SoundboardSoundsUpdateEvent",
)

import abc
import typing

import attrs

from hikari import intents
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import attrs_extensions

if typing.TYPE_CHECKING:
    from hikari import emojis
    from hikari import snowflakes
    from hikari import soundboard
    from hikari import traits
    from hikari import undefined
    from hikari import users
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(intents.Intents.GUILD_EMOJIS)
class SoundboardSoundEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any event that involves guild soundboard sounds."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflakes.Snowflake:
        """ID of the guild that this event relates to."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class SoundboardSoundCreateEvent(SoundboardSoundEvent):
    """Event fired when a guild soundboard sound is created."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the sound."""

    name: str = attrs.field(hash=True, repr=True)
    """The name of the sound."""

    volume: float = attrs.field(hash=True, repr=True)
    """The volume of the sound."""

    emoji: emojis.UnicodeEmoji | emojis.CustomEmoji | None = attrs.field(hash=True, repr=True)
    """The emoji of the sound."""

    guild_id: snowflakes.Snowflake = attrs.field(hash=True, repr=False)
    """The guild ID of the stage instance."""

    is_available: bool = attrs.field(hash=True, repr=False)
    """Whether this sound can be used, or lost due to insufficient boosting."""

    user: undefined.UndefinedOr[users.PartialUser] = attrs.field(hash=True, repr=False)
    """The user who created the sound."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class SoundboardSoundUpdateEvent(SoundboardSoundEvent):
    """Event fired when a guild soundboard sound is updated."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the sound."""

    name: str = attrs.field(hash=True, repr=True)
    """The name of the sound."""

    volume: float = attrs.field(hash=True, repr=True)
    """The volume of the sound."""

    emoji: emojis.UnicodeEmoji | emojis.CustomEmoji | None = attrs.field(hash=True, repr=True)
    """The emoji of the sound."""

    guild_id: snowflakes.Snowflake = attrs.field(hash=True, repr=False)
    """The guild ID of the stage instance."""

    is_available: bool = attrs.field(hash=True, repr=False)
    """Whether this sound can be used, or lost due to insufficient boosting."""

    user: undefined.UndefinedOr[users.PartialUser] = attrs.field(hash=True, repr=False)
    """The user who created the sound."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class SoundboardSoundDeleteEvent(SoundboardSoundEvent):
    """Event fired when a guild soundboard sound is deleted."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from SoundboardSoundEvent>>.

    id: snowflakes.Snowflake = attrs.field(eq=False, hash=False, repr=True)
    """ID of the sound."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
class SoundboardSoundsUpdateEvent(SoundboardSoundEvent):
    """Event fired when a guild soundboard sound is created."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    soundboard_sounds: typing.Sequence[soundboard.SoundboardSound] = attrs.field(hash=True, repr=False)
    """The guilds soundboard sounds."""

    guild_id: snowflakes.Snowflake = attrs.field(hash=True, repr=True)
    """The guild ID of the stage instance."""
