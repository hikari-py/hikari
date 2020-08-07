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
