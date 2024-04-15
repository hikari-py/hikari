# -*- coding: utf-8 -*-
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
import pytest

from hikari import emojis
from hikari import snowflakes


class TestEmoji:
    @pytest.mark.parametrize(
        ("input", "output"),
        [
            ("<:foo:12345>", emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name="foo", is_animated=False)),
            ("<bar:foo:12345>", emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name="foo", is_animated=False)),
            ("<a:foo:12345>", emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name="foo", is_animated=True)),
            ("\N{OK HAND SIGN}", emojis.UnicodeEmoji("\N{OK HAND SIGN}")),
            (
                "\N{REGIONAL INDICATOR SYMBOL LETTER G}\N{REGIONAL INDICATOR SYMBOL LETTER B}",
                emojis.UnicodeEmoji("\N{REGIONAL INDICATOR SYMBOL LETTER G}\N{REGIONAL INDICATOR SYMBOL LETTER B}"),
            ),
        ],
    )
    def test_parse(self, input, output):
        assert emojis.Emoji.parse(input) == output


class TestUnicodeEmoji:
    @pytest.fixture
    def emoji(self):
        return emojis.UnicodeEmoji("\N{OK HAND SIGN}")

    def test_name_property(self, emoji):
        assert emoji.name == emoji

    def test_url_name_property(self, emoji):
        assert emoji.url_name == emoji

    def test_mention_property(self, emoji):
        assert emoji.mention == emoji

    def test_codepoints_property(self, emoji):
        assert emoji.codepoints == [128076]

    @pytest.mark.parametrize(
        ("codepoints", "expected_filename"),
        [
            # Normal tests
            ([0x1F44C], "1f44c"),
            ([0x1F44C, 0x1F44C, 0x1F44C, 0x1F44C], "1f44c-1f44c-1f44c-1f44c"),
            # Outliers tests
            # 1. Second codepoint is not 0xFE0F => Nothing
            ([0xFE0F, 0x1F44C], "fe0f-1f44c"),
            # 2. More than 4 codepoints => Nothing
            ([0x1F44C, 0xFE0F, 0x1F44C, 0x1F44C, 0x1F44C], "1f44c-fe0f-1f44c-1f44c-1f44c"),
            # 3. Third codepoint is 0x200D => Nothing
            ([0x1F44C, 0xFE0F, 0x200D], "1f44c-fe0f-200d"),
            # 4. None of above apply => Remove second codepoint
            ([0x200D, 0xFE0F, 0x1F44C, 0x1F44C], "200d-1f44c-1f44c"),
        ],
    )
    def test_filename_property(self, codepoints, expected_filename):
        emoji = emojis.UnicodeEmoji.parse_codepoints(*codepoints)
        assert emoji.filename == f"{expected_filename}.png"

    def test_url_property(self, emoji):
        assert emoji.url == "https://raw.githubusercontent.com/discord/twemoji/master/assets/72x72/1f44c.png"

    def test_unicode_escape_property(self, emoji):
        assert emoji.unicode_escape == "\\U0001f44c"

    def test_parse_codepoints(self, emoji):
        assert emojis.UnicodeEmoji.parse_codepoints(128076) == emoji

    def test_parse_unicode_escape(self, emoji):
        assert emojis.UnicodeEmoji.parse_unicode_escape("\\U0001f44c") == emoji

    def test_str_operator(self, emoji):
        assert str(emoji) == emoji

    @pytest.mark.parametrize(
        ("input", "output"),
        [
            ("\N{OK HAND SIGN}", emojis.UnicodeEmoji("\N{OK HAND SIGN}")),
            (
                "\N{REGIONAL INDICATOR SYMBOL LETTER G}\N{REGIONAL INDICATOR SYMBOL LETTER B}",
                emojis.UnicodeEmoji("\N{REGIONAL INDICATOR SYMBOL LETTER G}\N{REGIONAL INDICATOR SYMBOL LETTER B}"),
            ),
        ],
    )
    def test_parse(self, input, output):
        assert emojis.UnicodeEmoji.parse(input) == output


class TestCustomEmoji:
    @pytest.fixture
    def emoji(self):
        return emojis.CustomEmoji(id=3213452, name="ok", is_animated=False)

    def test_filename_property(self, emoji):
        assert emoji.filename == "3213452.png"

    def test_filename_property_when_animated(self, emoji):
        emoji.is_animated = True
        assert emoji.filename == "3213452.gif"

    def test_url_name_property(self, emoji):
        assert emoji.url_name == "ok:3213452"

    def test_mention_property(self, emoji):
        assert emoji.mention == "<:ok:3213452>"

    def test_mention_property_when_animated(self, emoji):
        emoji.is_animated = True

        assert emoji.mention == "<a:ok:3213452>"

    def test_url_property(self, emoji):
        assert emoji.url == "https://cdn.discordapp.com/emojis/3213452.png"

    def test_str_operator_when_populated_name(self):
        emoji = emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name="peepoSad", is_animated=True)
        assert str(emoji) == emoji.mention

    @pytest.mark.parametrize(
        ("input", "output"),
        [
            ("<:foo:12345>", emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name="foo", is_animated=False)),
            ("<bar:foo:12345>", emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name="foo", is_animated=False)),
            ("<a:foo:12345>", emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name="foo", is_animated=True)),
        ],
    )
    def test_parse(self, input, output):
        assert emojis.CustomEmoji.parse(input) == output

    def test_parse_unhappy_path(self):
        with pytest.raises(ValueError, match="Expected an emoji mention"):
            emojis.CustomEmoji.parse("xxx")
