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
import mock

from hikari import emojis


def test_UnicodeEmoji_str_operator():
    mock_emoji = mock.Mock(emojis.UnicodeEmoji)
    mock_emoji.name = "\N{OK HAND SIGN}"
    assert emojis.UnicodeEmoji.__str__(mock_emoji) == "\N{OK HAND SIGN}"


def test_CustomEmoji_str_operator():
    mock_emoji = mock.Mock(emojis.CustomEmoji, emojis.CustomEmoji)
    mock_emoji.name = "peepoSad"
    assert emojis.CustomEmoji.__str__(mock_emoji) == "peepoSad"


def test_CustomEmoji_str_operator_when_name_is_None():
    mock_emoji = mock.Mock(emojis.CustomEmoji, emojis.CustomEmoji, id=42069)
    mock_emoji.name = None
    assert emojis.CustomEmoji.__str__(mock_emoji) == "Unnamed emoji ID 42069"
