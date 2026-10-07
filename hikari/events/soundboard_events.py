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
"""Events pertaining to soundboard sounds within guilds."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "SoundboardSoundCreateEvent",
    "SoundboardSoundDeleteEvent",
    "SoundboardSoundEvent",
    "SoundboardSoundUpdateEvent",
    "SoundboardSoundsEvent",
    "SoundboardSoundsUpdateEvent",
)

import abc
import typing

import attrs

from hikari import intents
from hikari.events import base_events
from hikari.events import guild_events
from hikari.internal import attrs_extensions
from hikari.internal import typing_extensions

if typing.TYPE_CHECKING:
    from hikari import snowflakes
    from hikari import soundboard
    from hikari import traits
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(intents.Intents.GUILD_EMOJIS)
class SoundboardSoundEvent(guild_events.GuildEvent, abc.ABC):
    """Event base for any event that involves guild soundboard sounds."""

    __slots__: typing.Sequence[str] = ()


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_EMOJIS)
class SoundboardSoundCreateEvent(SoundboardSoundEvent):
    """Event fired when a guild soundboard sound is created."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    sound: soundboard.SoundboardSound = attrs.field()
    """The created sound."""

    @property
    @typing_extensions.override
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildEvent>>.
        assert self.sound.guild_id is not None
        return self.sound.guild_id


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_EMOJIS)
class SoundboardSoundUpdateEvent(SoundboardSoundEvent):
    """Event fired when a guild soundboard sound is updated."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    sound: soundboard.SoundboardSound = attrs.field()
    """The sound after the update."""

    old_sound: soundboard.SoundboardSound | None = attrs.field()
    """The sound before the update.

    This will be [`None`][] if it's missing from the cache.
    """

    @property
    @typing_extensions.override
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildEvent>>.
        assert self.sound.guild_id is not None
        return self.sound.guild_id


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_EMOJIS)
class SoundboardSoundDeleteEvent(SoundboardSoundEvent):
    """Event fired when a guild soundboard sound is deleted."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from GuildEvent>>.

    sound_id: snowflakes.Snowflake = attrs.field()
    """ID of the deleted sound."""

    old_sound: soundboard.SoundboardSound | None = attrs.field()
    """The deleted sound.

    This will be [`None`][] if it's missing from the cache.
    """


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_EMOJIS)
class SoundboardSoundsUpdateEvent(SoundboardSoundEvent):
    """Event fired when multiple guild soundboard sounds are updated at once."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from GuildEvent>>.

    sounds: typing.Sequence[soundboard.SoundboardSound] = attrs.field()
    """The updated sounds."""

    old_sounds: typing.Sequence[soundboard.SoundboardSound] | None = attrs.field()
    """The updated sounds as they were before the update.

    This will be [`None`][] if the soundboard sound cache is disabled. Sounds that were not cached are left out.
    """


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.NONE)
class SoundboardSoundsEvent(SoundboardSoundEvent):
    """Event fired with a guild's soundboard sounds after they were requested.

    See [`hikari.api.shard.GatewayShard.request_soundboard_sounds`][].
    """

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from GuildEvent>>.

    sounds: typing.Sequence[soundboard.SoundboardSound] = attrs.field()
    """All soundboard sounds of the guild."""
