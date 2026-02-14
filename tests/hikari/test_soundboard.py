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

import pytest
import mock

from hikari import soundboard
from hikari import snowflakes
from hikari import emojis


class TestSoundboardSound:
    @pytest.fixture
    def mock_user(self):
        return mock.Mock()

    @pytest.fixture
    def soundboard_sound(self, mock_user: mock.Mock):
        return soundboard.SoundboardSound(
            id=snowflakes.Snowflake(54),
            name="goomse",
            volume=0.1234,
            emoji=emojis.UnicodeEmoji("🦫"),
            guild_id=snowflakes.Snowflake(123),
            is_available=False,
            user=mock_user,
        )

    def test_id_property(self, soundboard_sound):
        assert soundboard_sound.id == snowflakes.Snowflake(54)

    def test_name_property(self, soundboard_sound):
        assert soundboard_sound.name == "goomse"

    def test_volume_property(self, soundboard_sound):
        assert soundboard_sound.volume == 0.1234

    def test_emoji_property(self, soundboard_sound):
        assert soundboard_sound.emoji == emojis.UnicodeEmoji("🦫")

    def test_guild_id_property(self, soundboard_sound):
        assert soundboard_sound.guild_id == snowflakes.Snowflake(123)

    def test_is_available_property(self, soundboard_sound):
        assert soundboard_sound.is_available is False

    def test_user_property(self, soundboard_sound, mock_user):
        assert soundboard_sound.user == mock_user
