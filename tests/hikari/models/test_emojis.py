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

from hikari.models import emojis


def test_UnicodeEmoji_str_operator():
    emoji = emojis.UnicodeEmoji()
    emoji.name = "\N{OK HAND SIGN}"
    assert str(emoji) == "\N{OK HAND SIGN}"


def test_CustomEmoji_str_operator():
    emoji = emojis.CustomEmoji()
    emoji.name = "peepoSad"
    assert str(emoji) == "peepoSad"


def test_CustomEmoji_str_operator_when_name_is_None():
    emoji = emojis.CustomEmoji()
    emoji.name = None
    emoji.id = 42069
    assert str(emoji) == "Unnamed emoji ID 42069"
