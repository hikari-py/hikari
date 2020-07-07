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

from hikari.models import messages
from hikari.models import emojis


def test_MessageType_str_operator():
    type = messages.MessageType(10)
    assert str(type) == "USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_2"


def test_MessageFlag_str_operator():
    flag = messages.MessageFlag(0)
    assert str(flag) == "NONE"


def test_MessageActivityType_str_operator():
    type = messages.MessageActivityType(5)
    assert str(type) == "JOIN_REQUEST"


def test_Attachment_str_operator():
    attachment = messages.Attachment()
    attachment.filename = "super_cool_file.cool"
    assert str(attachment) == "super_cool_file.cool"


def test_Reaction_str_operator():
    reaction = messages.Reaction()
    emoji = emojis.UnicodeEmoji()
    emoji.name = "\N{OK HAND SIGN}"
    reaction.emoji = emoji
    assert str(reaction) == "\N{OK HAND SIGN}"
