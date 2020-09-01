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
import pytest

from hikari import emojis
from hikari import messages
from tests.hikari import hikari_test_helpers


def test_MessageType_str_operator():
    message_type = messages.MessageType(10)
    assert str(message_type) == "USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_2"


def test_MessageFlag_str_operator():
    flag = messages.MessageFlag(0)
    assert str(flag) == "NONE"


def test_MessageActivityType_str_operator():
    activity_type = messages.MessageActivityType(5)
    assert str(activity_type) == "JOIN_REQUEST"


def test_Attachment_str_operator():
    attachment = messages.Attachment(
        id=123, filename="super_cool_file.cool", height=222, width=555, proxy_url="htt", size=543, url="htttt"
    )
    assert str(attachment) == "super_cool_file.cool"


def test_Reaction_str_operator():
    reaction = messages.Reaction(emoji=emojis.UnicodeEmoji("\N{OK HAND SIGN}"), count=42, is_me=True)
    assert str(reaction) == "\N{OK HAND SIGN}"


@pytest.fixture()
def message():
    return hikari_test_helpers.stub_class(messages.Message, app=mock.Mock(rest=mock.AsyncMock()))


class TestMessage:
    def test_link_property_when_guild_is_not_none(self, message):
        message.id = 789
        message.channel_id = 456
        message.guild_id = 123
        assert message.link == "https://discord.com/channels/123/456/789"

    def test_link_property_when_guild_is_none(self, message):
        message.id = 789
        message.channel_id = 456
        message.guild_id = None
        assert message.link == "https://discord.com/channels/@me/456/789"


@pytest.mark.asyncio
class TestAsyncMessage:
    async def test_fetch_channel(self, message):
        message.channel_id = 123
        await message.fetch_channel()
        message.app.rest.fetch_channel.assert_called_once_with(123)

    async def test_edit(self, message):
        message.id = 123
        message.channel_id = 456
        embed = object()
        roles = [object()]
        await message.edit(
            content="test content",
            embed=embed,
            mentions_everyone=True,
            user_mentions=False,
            role_mentions=roles,
            flags=messages.MessageFlag.URGENT,
        )
        message.app.rest.edit_message.assert_called_once_with(
            message=123,
            channel=456,
            content="test content",
            embed=embed,
            mentions_everyone=True,
            user_mentions=False,
            role_mentions=roles,
            flags=messages.MessageFlag.URGENT,
        )

    async def test_reply(self, message):
        message.id = 123
        message.channel_id = 456
        embed = object()
        roles = [object()]
        attachment = object()
        attachments = [object()]
        await message.reply(
            content="test content",
            embed=embed,
            attachment=attachment,
            attachments=attachments,
            nonce="nonce",
            tts=True,
            mentions_everyone=True,
            user_mentions=False,
            role_mentions=roles,
        )
        message.app.rest.create_message.assert_called_once_with(
            channel=456,
            content="test content",
            embed=embed,
            attachment=attachment,
            attachments=attachments,
            nonce="nonce",
            tts=True,
            mentions_everyone=True,
            user_mentions=False,
            role_mentions=roles,
        )

    async def test_delete(self, message):
        message.id = 123
        message.channel_id = 456
        await message.delete()
        message.app.rest.delete_message.assert_called_once_with(456, 123)

    async def test_add_reaction(self, message):
        message.id = 123
        message.channel_id = 456
        await message.add_reaction("👌")
        message.app.rest.add_reaction.assert_called_once_with(channel=456, message=123, emoji="👌")

    async def test_remove_reaction(self, message):
        message.id = 123
        message.channel_id = 456
        await message.remove_reaction("👌")
        message.app.rest.delete_my_reaction.assert_called_once_with(channel=456, message=123, emoji="👌")

    async def test_remove_reaction_with_user(self, message):
        user = object()
        message.id = 123
        message.channel_id = 456
        await message.remove_reaction("👌", user=user)
        message.app.rest.delete_reaction.assert_called_once_with(channel=456, message=123, emoji="👌", user=user)

    async def test_remove_all_reactions(self, message):
        message.id = 123
        message.channel_id = 456
        await message.remove_all_reactions()
        message.app.rest.delete_all_reactions.assert_called_once_with(channel=456, message=123)

    async def test_remove_all_reactions_with_emoji(self, message):
        message.id = 123
        message.channel_id = 456
        await message.remove_all_reactions("👌")
        message.app.rest.delete_all_reactions_for_emoji.assert_called_once_with(channel=456, message=123, emoji="👌")
