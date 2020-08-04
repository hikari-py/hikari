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
from hikari.models import messages
from tests.hikari import hikari_test_helpers


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
    attachment = messages.Attachment(
        id=123, filename="super_cool_file.cool", height=222, width=555, proxy_url="htt", size=543, url="htttt"
    )
    assert str(attachment) == "super_cool_file.cool"


def test_Reaction_str_operator():
    reaction = messages.Reaction(emoji=emojis.UnicodeEmoji("\N{OK HAND SIGN}"), count=42, is_me=True)
    assert str(reaction) == "\N{OK HAND SIGN}"


class TestMessage:
    def test_link_property_when_guild_is_not_none(self):
        mock_message = hikari_test_helpers.stub_class(messages.Message, id=23432, channel_id=562134, guild_id=54123)
        assert mock_message.link == "https://discord.com/channels/54123/562134/23432"

    def test_link_property_when_guild_is_none(self):
        mock_message = hikari_test_helpers.stub_class(messages.Message, id=33333, guild_id=None, channel_id=65234)
        assert mock_message.link == "https://discord.com/channels/@me/65234/33333"
