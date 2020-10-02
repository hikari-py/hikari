# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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
            ("12345", emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name=None, is_animated=None)),
            ("<:foo:12345>", emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name="foo", is_animated=False)),
            ("<bar:foo:12345>", emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name="foo", is_animated=False)),
            ("<a:foo:12345>", emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name="foo", is_animated=True)),
            ("\N{OK HAND SIGN}", emojis.UnicodeEmoji(name="\N{OK HAND SIGN}")),
            (
                "\N{REGIONAL INDICATOR SYMBOL LETTER G}\N{REGIONAL INDICATOR SYMBOL LETTER B}",
                emojis.UnicodeEmoji(
                    name="\N{REGIONAL INDICATOR SYMBOL LETTER G}\N{REGIONAL INDICATOR SYMBOL LETTER B}"
                ),
            ),
        ],
    )
    def test_parse(self, input, output):
        assert emojis.Emoji.parse(input) == output


class TestUnicodeEmoji:
    def test_str_operator(self):
        assert emojis.UnicodeEmoji(name="\N{OK HAND SIGN}") == "\N{OK HAND SIGN}"

    @pytest.mark.parametrize(
        ("input", "output"),
        [
            ("\N{OK HAND SIGN}", emojis.UnicodeEmoji(name="\N{OK HAND SIGN}")),
            (
                "\N{REGIONAL INDICATOR SYMBOL LETTER G}\N{REGIONAL INDICATOR SYMBOL LETTER B}",
                emojis.UnicodeEmoji(
                    name="\N{REGIONAL INDICATOR SYMBOL LETTER G}\N{REGIONAL INDICATOR SYMBOL LETTER B}"
                ),
            ),
        ],
    )
    def test_parse(self, input, output):
        assert emojis.UnicodeEmoji.parse(input) == output


class TestCustomEmoji:
    def test_str_operator_when_populated_name(self):
        emoji = emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name="peepoSad", is_animated=True)
        assert str(emoji) == "peepoSad"

    def test_str_operator_when_name_is_None(self):
        emoji = emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name=None, is_animated=True)
        assert str(emoji) == "Unnamed emoji ID 12345"

    @pytest.mark.parametrize(
        ("input", "output"),
        [
            ("12345", emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name=None, is_animated=None)),
            ("<:foo:12345>", emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name="foo", is_animated=False)),
            ("<bar:foo:12345>", emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name="foo", is_animated=False)),
            ("<a:foo:12345>", emojis.CustomEmoji(id=snowflakes.Snowflake(12345), name="foo", is_animated=True)),
        ],
    )
    def test_parse(self, input, output):
        assert emojis.CustomEmoji.parse(input) == output

    def test_parse_unhappy_path(self):
        with pytest.raises(ValueError, match="Expected an emoji ID or emoji mention"):
            emojis.CustomEmoji.parse("xxx")
