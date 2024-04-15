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
import datetime

import mock
import pytest

from hikari import emojis
from hikari import guilds
from hikari import messages
from hikari import snowflakes
from hikari import undefined
from hikari import urls
from hikari import users
from hikari.internal import routes


class TestAttachment:
    def test_str_operator(self):
        attachment = messages.Attachment(
            id=123,
            filename="super_cool_file.cool",
            media_type="image/png",
            height=222,
            width=555,
            proxy_url="htt",
            size=543,
            url="htttt",
            is_ephemeral=False,
            duration=1,
            waveform="122111",
        )
        assert str(attachment) == "super_cool_file.cool"


class TestReaction:
    def test_str_operator(self):
        reaction = messages.Reaction(emoji=emojis.UnicodeEmoji("\N{OK HAND SIGN}"), count=42, is_me=True)
        assert str(reaction) == "\N{OK HAND SIGN}"


class TestMessageApplication:
    @pytest.fixture
    def message_application(self):
        return messages.MessageApplication(
            id=123, name="test app", description="", icon_hash="123abc", cover_image_hash="abc123"
        )

    def test_cover_image_url(self, message_application):
        with mock.patch.object(messages.MessageApplication, "make_cover_image_url") as mock_cover_image:
            assert message_application.cover_image_url is mock_cover_image()

    def test_make_cover_image_url_when_hash_is_none(self, message_application):
        message_application.cover_image_hash = None

        assert message_application.make_cover_image_url() is None

    def test_make_cover_image_url_when_hash_is_not_none(self, message_application):
        with mock.patch.object(
            routes, "CDN_APPLICATION_COVER", new=mock.Mock(compile_to_file=mock.Mock(return_value="file"))
        ) as route:
            assert message_application.make_cover_image_url(ext="jpeg", size=1000) == "file"

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, application_id=123, hash="abc123", size=1000, file_format="jpeg"
        )


@pytest.fixture
def message():
    return messages.Message(
        app=None,
        id=snowflakes.Snowflake(1234),
        channel_id=snowflakes.Snowflake(5678),
        guild_id=snowflakes.Snowflake(910112),
        author=mock.Mock(spec_set=users.User),
        member=mock.Mock(spec_set=guilds.Member),
        content="blahblahblah",
        timestamp=datetime.datetime.now().astimezone(),
        edited_timestamp=None,
        is_tts=False,
        user_mentions={},
        role_mention_ids=[],
        channel_mentions={},
        mentions_everyone=False,
        attachments=(),
        embeds=(),
        reactions=(),
        is_pinned=True,
        webhook_id=None,
        type=messages.MessageType.DEFAULT,
        activity=None,
        application=None,
        message_reference=None,
        flags=None,
        nonce=None,
        referenced_message=None,
        stickers=[],
        interaction=None,
        application_id=123123,
        components=[],
    )


class TestMessage:
    def test_make_link_when_guild_is_not_none(self, message):
        message.id = 789
        message.channel_id = 456
        assert message.make_link(123) == "https://discord.com/channels/123/456/789"

    def test_make_link_when_guild_is_none(self, message):
        message.app = mock.Mock()
        message.id = 789
        message.channel_id = 456
        assert message.make_link(None) == "https://discord.com/channels/@me/456/789"


@pytest.fixture
def message_reference():
    return messages.MessageReference(
        app=None, guild_id=snowflakes.Snowflake(123), channel_id=snowflakes.Snowflake(456), id=snowflakes.Snowflake(789)
    )


class TestMessageReference:
    def test_make_link_when_guild_is_not_none(self, message_reference):
        assert message_reference.message_link == "https://discord.com/channels/123/456/789"
        assert message_reference.channel_link == "https://discord.com/channels/123/456"

    def test_make_link_when_guild_is_none(self, message_reference):
        message_reference.guild_id = None
        assert message_reference.message_link == "https://discord.com/channels/@me/456/789"
        assert message_reference.channel_link == "https://discord.com/channels/@me/456"

    def test_make_link_when_id_is_none(self, message_reference):
        message_reference.id = None
        assert message_reference.message_link is None
        assert message_reference.channel_link == "https://discord.com/channels/123/456"


@pytest.mark.asyncio
class TestAsyncMessage:
    async def test_fetch_channel(self, message):
        message.app = mock.AsyncMock()
        message.channel_id = 123
        await message.fetch_channel()
        message.app.rest.fetch_channel.assert_awaited_once_with(123)

    async def test_edit(self, message):
        message.app = mock.AsyncMock()
        message.id = 123
        message.channel_id = 456
        embed = object()
        embeds = [object(), object()]
        component = object()
        components = object(), object()
        attachment = object()
        roles = [object()]
        await message.edit(
            content="test content",
            embed=embed,
            embeds=embeds,
            attachment=attachment,
            attachments=[attachment, attachment],
            component=component,
            components=components,
            mentions_everyone=True,
            mentions_reply=False,
            user_mentions=False,
            role_mentions=roles,
            flags=messages.MessageFlag.URGENT,
        )
        message.app.rest.edit_message.assert_awaited_once_with(
            message=123,
            channel=456,
            content="test content",
            embed=embed,
            embeds=embeds,
            attachment=attachment,
            attachments=[attachment, attachment],
            component=component,
            components=components,
            mentions_everyone=True,
            mentions_reply=False,
            user_mentions=False,
            role_mentions=roles,
            flags=messages.MessageFlag.URGENT,
        )

    async def test_respond(self, message):
        message.app = mock.AsyncMock()
        message.id = 123
        message.channel_id = 456
        embed = object()
        embeds = [object(), object()]
        roles = [object()]
        attachment = object()
        attachments = [object()]
        component = object()
        components = object(), object()
        reference_messsage = object()
        await message.respond(
            content="test content",
            embed=embed,
            embeds=embeds,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            sticker=123,
            stickers=[543, 6542],
            tts=True,
            reply=reference_messsage,
            reply_must_exist=False,
            mentions_everyone=True,
            user_mentions=False,
            role_mentions=roles,
            mentions_reply=True,
            flags=321123,
        )
        message.app.rest.create_message.assert_awaited_once_with(
            channel=456,
            content="test content",
            embed=embed,
            embeds=embeds,
            attachment=attachment,
            attachments=attachments,
            component=component,
            components=components,
            sticker=123,
            stickers=[543, 6542],
            tts=True,
            reply=reference_messsage,
            reply_must_exist=False,
            mentions_everyone=True,
            user_mentions=False,
            role_mentions=roles,
            mentions_reply=True,
            flags=321123,
        )

    async def test_respond_when_reply_is_True(self, message):
        message.app = mock.AsyncMock()
        message.id = 123
        message.channel_id = 456
        await message.respond(reply=True)
        message.app.rest.create_message.assert_awaited_once_with(
            channel=456,
            content=undefined.UNDEFINED,
            embed=undefined.UNDEFINED,
            embeds=undefined.UNDEFINED,
            attachment=undefined.UNDEFINED,
            attachments=undefined.UNDEFINED,
            component=undefined.UNDEFINED,
            components=undefined.UNDEFINED,
            sticker=undefined.UNDEFINED,
            stickers=undefined.UNDEFINED,
            tts=undefined.UNDEFINED,
            reply=message,
            reply_must_exist=undefined.UNDEFINED,
            mentions_everyone=undefined.UNDEFINED,
            user_mentions=undefined.UNDEFINED,
            role_mentions=undefined.UNDEFINED,
            mentions_reply=undefined.UNDEFINED,
            flags=undefined.UNDEFINED,
        )

    async def test_respond_when_reply_is_False(self, message):
        message.app = mock.AsyncMock()
        message.id = 123
        message.channel_id = 456
        await message.respond(reply=False)
        message.app.rest.create_message.assert_awaited_once_with(
            channel=456,
            content=undefined.UNDEFINED,
            embed=undefined.UNDEFINED,
            embeds=undefined.UNDEFINED,
            attachment=undefined.UNDEFINED,
            attachments=undefined.UNDEFINED,
            component=undefined.UNDEFINED,
            components=undefined.UNDEFINED,
            sticker=undefined.UNDEFINED,
            stickers=undefined.UNDEFINED,
            tts=undefined.UNDEFINED,
            reply=undefined.UNDEFINED,
            reply_must_exist=undefined.UNDEFINED,
            mentions_everyone=undefined.UNDEFINED,
            user_mentions=undefined.UNDEFINED,
            role_mentions=undefined.UNDEFINED,
            mentions_reply=undefined.UNDEFINED,
            flags=undefined.UNDEFINED,
        )

    async def test_delete(self, message):
        message.app = mock.AsyncMock()
        message.id = 123
        message.channel_id = 456
        await message.delete()
        message.app.rest.delete_message.assert_awaited_once_with(456, 123)

    async def test_add_reaction(self, message):
        message.app = mock.AsyncMock()
        message.id = 123
        message.channel_id = 456
        await message.add_reaction("👌", 123123)
        message.app.rest.add_reaction.assert_awaited_once_with(channel=456, message=123, emoji="👌", emoji_id=123123)

    async def test_remove_reaction(self, message):
        message.app = mock.AsyncMock()
        message.id = 123
        message.channel_id = 456
        await message.remove_reaction("👌", 341231)
        message.app.rest.delete_my_reaction.assert_awaited_once_with(
            channel=456, message=123, emoji="👌", emoji_id=341231
        )

    async def test_remove_reaction_with_user(self, message):
        message.app = mock.AsyncMock()
        user = object()
        message.id = 123
        message.channel_id = 456
        await message.remove_reaction("👌", 31231, user=user)
        message.app.rest.delete_reaction.assert_awaited_once_with(
            channel=456, message=123, emoji="👌", emoji_id=31231, user=user
        )

    async def test_remove_all_reactions(self, message):
        message.app = mock.AsyncMock()
        message.id = 123
        message.channel_id = 456
        await message.remove_all_reactions()
        message.app.rest.delete_all_reactions.assert_awaited_once_with(channel=456, message=123)

    async def test_remove_all_reactions_with_emoji(self, message):
        message.app = mock.AsyncMock()
        message.id = 123
        message.channel_id = 456
        await message.remove_all_reactions("👌", emoji_id=65655)
        message.app.rest.delete_all_reactions_for_emoji.assert_awaited_once_with(
            channel=456, message=123, emoji="👌", emoji_id=65655
        )
