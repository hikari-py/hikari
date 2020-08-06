# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
import mock

from hikari.models import emojis


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
