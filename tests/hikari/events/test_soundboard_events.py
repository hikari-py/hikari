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
from __future__ import annotations

import mock

from hikari import intents
from hikari import snowflakes
from hikari import soundboard
from hikari.events import base_events
from hikari.events import soundboard_events


class TestSoundboardSoundCreateEvent:
    def test_guild_id(self):
        sound = mock.Mock(soundboard.SoundboardSound, guild_id=snowflakes.Snowflake(123))
        event = soundboard_events.SoundboardSoundCreateEvent(app=mock.Mock(), shard=mock.Mock(), sound=sound)

        assert event.guild_id == 123


class TestSoundboardSoundUpdateEvent:
    def test_guild_id(self):
        sound = mock.Mock(soundboard.SoundboardSound, guild_id=snowflakes.Snowflake(123))
        event = soundboard_events.SoundboardSoundUpdateEvent(
            app=mock.Mock(), shard=mock.Mock(), sound=sound, old_sound=None
        )

        assert event.guild_id == 123


def test_guild_events_require_guild_emojis_intent():
    for event_type in (
        soundboard_events.SoundboardSoundCreateEvent,
        soundboard_events.SoundboardSoundUpdateEvent,
        soundboard_events.SoundboardSoundDeleteEvent,
        soundboard_events.SoundboardSoundsUpdateEvent,
    ):
        assert base_events.get_required_intents_for(event_type) == [intents.Intents.GUILD_EMOJIS]


def test_sounds_event_requires_no_intent():
    assert base_events.get_required_intents_for(soundboard_events.SoundboardSoundsEvent) == [intents.Intents.NONE]


def test_events_are_exported():
    import hikari

    assert hikari.SoundboardSoundCreateEvent is soundboard_events.SoundboardSoundCreateEvent
    assert hikari.events.SoundboardSoundsEvent is soundboard_events.SoundboardSoundsEvent
