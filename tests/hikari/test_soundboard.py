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

from hikari import emojis
from hikari import files
from hikari import snowflakes
from hikari import soundboard
from hikari import urls


def _make_sound(**kwargs):
    fields = {
        "id": snowflakes.Snowflake(1106714396018884649),
        "name": "Yay",
        "volume": 1.0,
        "emoji": emojis.UnicodeEmoji("🦆"),
        "guild_id": snowflakes.Snowflake(613425648685547541),
        "is_available": True,
        "user": None,
    }
    fields.update(kwargs)
    return soundboard.SoundboardSound(**fields)


class TestSoundboardSound:
    def test_url(self):
        sound = _make_sound()

        assert sound.url == files.URL(f"{urls.CDN_URL}/soundboard-sounds/1106714396018884649")

    def test_equality_only_considers_id(self):
        assert _make_sound(name="a", volume=0.1) == _make_sound(name="b", volume=0.9)
        assert hash(_make_sound(name="a")) == hash(_make_sound(name="b"))

    def test_inequality_for_different_ids(self):
        assert _make_sound(id=snowflakes.Snowflake(1)) != _make_sound(id=snowflakes.Snowflake(2))

    @pytest.mark.parametrize("guild_id", [None, snowflakes.Snowflake(613425648685547541)])
    def test_guild_id_may_be_none(self, guild_id):
        assert _make_sound(guild_id=guild_id).guild_id == guild_id
