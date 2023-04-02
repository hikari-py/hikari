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

from hikari import channels
from hikari import files
from hikari import permissions
from hikari import snowflakes
from hikari import users
from hikari import webhooks
from tests.hikari import hikari_test_helpers


@pytest.fixture()
def mock_app():
    return mock.Mock()


class TestChannelFollow:
    @pytest.mark.asyncio()
    async def test_fetch_channel(self, mock_app):
        mock_channel = mock.Mock(spec=channels.GuildNewsChannel)
        mock_app.rest.fetch_channel = mock.AsyncMock(return_value=mock_channel)
        follow = channels.ChannelFollow(
            channel_id=snowflakes.Snowflake(9459234123), app=mock_app, webhook_id=snowflakes.Snowflake(3123123)
        )

        result = await follow.fetch_channel()

        assert result is mock_channel
        mock_app.rest.fetch_channel.assert_awaited_once_with(9459234123)

    @pytest.mark.asyncio()
    async def test_fetch_webhook(self, mock_app):
        mock_app.rest.fetch_webhook = mock.AsyncMock(return_value=mock.Mock(webhooks.ChannelFollowerWebhook))
        follow = channels.ChannelFollow(
            webhook_id=snowflakes.Snowflake(54123123), app=mock_app, channel_id=snowflakes.Snowflake(94949494)
        )

        result = await follow.fetch_webhook()

        assert result is mock_app.rest.fetch_webhook.return_value
        mock_app.rest.fetch_webhook.assert_awaited_once_with(54123123)

    def test_get_channel(self, mock_app):
        mock_channel = mock.Mock(spec=channels.GuildNewsChannel)
        mock_app.cache.get_guild_channel = mock.Mock(return_value=mock_channel)
        follow = channels.ChannelFollow(
            webhook_id=snowflakes.Snowflake(993883), app=mock_app, channel_id=snowflakes.Snowflake(696969)
        )

        result = follow.get_channel()

        assert result is mock_channel
        mock_app.cache.get_guild_channel.assert_called_once_with(696969)

    def test_get_channel_when_no_cache_trait(self):
        follow = channels.ChannelFollow(
            webhook_id=snowflakes.Snowflake(993883), app=object(), channel_id=snowflakes.Snowflake(696969)
        )

        assert follow.get_channel() is None


class TestPermissionOverwrite:
    def test_unset(self):
        overwrite = channels.PermissionOverwrite(
            type=channels.PermissionOverwriteType.MEMBER, id=snowflakes.Snowflake(1234321)
        )
        overwrite.allow = permissions.Permissions.CREATE_INSTANT_INVITE
        overwrite.deny = permissions.Permissions.CHANGE_NICKNAME
        assert overwrite.unset == permissions.Permissions(-67108866)


class TestPartialChannel:
    @pytest.fixture()
    def model(self, mock_app):
        return hikari_test_helpers.mock_class_namespace(channels.PartialChannel, rename_impl_=False)(
            app=mock_app, id=snowflakes.Snowflake(1234567), name="foo", type=channels.ChannelType.GUILD_NEWS
        )

    def test_str_operator(self, model):
        assert str(model) == "foo"

    def test_str_operator_when_name_is_None(self, model):
        model.name = None
        assert str(model) == "Unnamed PartialChannel ID 1234567"

    def test_mention_property(self, model):
        assert model.mention == "<#1234567>"

    @pytest.mark.asyncio()
    async def test_delete(self, model):
        model.app.rest.delete_channel = mock.AsyncMock()

        assert await model.delete() is model.app.rest.delete_channel.return_value

        model.app.rest.delete_channel.assert_called_once_with(1234567)


class TestDMChannel:
    @pytest.fixture()
    def model(self, mock_app):
        return channels.DMChannel(
            id=snowflakes.Snowflake(12345),
            name="steve",
            type=channels.ChannelType.DM,
            last_message_id=snowflakes.Snowflake(12345),
            recipient=mock.Mock(spec_set=users.UserImpl, __str__=mock.Mock(return_value="snoop#0420")),
            app=mock_app,
        )

    def test_str_operator(self, model):
        assert str(model) == "DMChannel with: snoop#0420"

    def test_shard_id(self, model):
        assert model.shard_id == 0


class TestGroupDMChannel:
    @pytest.fixture()
    def model(self, mock_app):
        return channels.GroupDMChannel(
            app=mock_app,
            id=snowflakes.Snowflake(136134),
            name="super cool group dm",
            type=channels.ChannelType.DM,
            last_message_id=snowflakes.Snowflake(3232),
            owner_id=snowflakes.Snowflake(1066),
            icon_hash="1a2b3c",
            nicknames={snowflakes.Snowflake(1): "person 1", snowflakes.Snowflake(2): "person 2"},
            recipients={
                snowflakes.Snowflake(1): mock.Mock(spec_set=users.User, __str__=mock.Mock(return_value="snoop#0420")),
                snowflakes.Snowflake(2): mock.Mock(spec_set=users.User, __str__=mock.Mock(return_value="yeet#1012")),
                snowflakes.Snowflake(3): mock.Mock(spec_set=users.User, __str__=mock.Mock(return_value="nice#6969")),
            },
            application_id=None,
        )

    def test_str_operator(self, model):
        assert str(model) == "super cool group dm"

    def test_str_operator_when_name_is_None(self, model):
        model.name = None
        assert str(model) == "GroupDMChannel with: snoop#0420, yeet#1012, nice#6969"

    def test_icon_url(self):
        channel = hikari_test_helpers.mock_class_namespace(
            channels.GroupDMChannel, init_=False, make_icon_url=mock.Mock(return_value="icon-url-here.com")
        )()
        assert channel.icon_url == "icon-url-here.com"
        channel.make_icon_url.assert_called_once()

    def test_make_icon_url(self, model):
        assert model.make_icon_url(ext="jpeg", size=16) == files.URL(
            "https://cdn.discordapp.com/channel-icons/136134/1a2b3c.jpeg?size=16"
        )

    def test_make_icon_url_without_optional_params(self, model):
        assert model.make_icon_url() == files.URL(
            "https://cdn.discordapp.com/channel-icons/136134/1a2b3c.png?size=4096"
        )

    def test_make_icon_url_when_hash_is_None(self, model):
        model.icon_hash = None
        assert model.make_icon_url() is None


class TestTextChannel:
    @pytest.fixture()
    def model(self, mock_app):
        return hikari_test_helpers.mock_class_namespace(channels.TextableChannel)(
            app=mock_app, id=snowflakes.Snowflake(12345679), name="foo1", type=channels.ChannelType.GUILD_TEXT
        )

    @pytest.mark.asyncio()
    async def test_fetch_history(self, model):
        model.app.rest.fetch_messages = mock.AsyncMock()

        await model.fetch_history(
            before=datetime.datetime(2020, 4, 1, 1, 0, 0),
            after=datetime.datetime(2020, 4, 1, 0, 0, 0),
            around=datetime.datetime(2020, 4, 1, 0, 30, 0),
        )

        model.app.rest.fetch_messages.assert_awaited_once_with(
            12345679,
            before=datetime.datetime(2020, 4, 1, 1, 0, 0),
            after=datetime.datetime(2020, 4, 1, 0, 0, 0),
            around=datetime.datetime(2020, 4, 1, 0, 30, 0),
        )

    @pytest.mark.asyncio()
    async def test_fetch_message(self, model):
        model.app.rest.fetch_message = mock.AsyncMock()

        assert await model.fetch_message(133742069) is model.app.rest.fetch_message.return_value

        model.app.rest.fetch_message.assert_awaited_once_with(12345679, 133742069)

    @pytest.mark.asyncio()
    async def test_fetch_pins(self, model):
        model.app.rest.fetch_pins = mock.AsyncMock()

        await model.fetch_pins()

        model.app.rest.fetch_pins.assert_awaited_once_with(12345679)

    @pytest.mark.asyncio()
    async def test_pin_message(self, model):
        model.app.rest.pin_message = mock.AsyncMock()

        assert await model.pin_message(77790) is model.app.rest.pin_message.return_value

        model.app.rest.pin_message.assert_awaited_once_with(12345679, 77790)

    @pytest.mark.asyncio()
    async def test_unpin_message(self, model):
        model.app.rest.unpin_message = mock.AsyncMock()

        assert await model.unpin_message(77790) is model.app.rest.unpin_message.return_value

        model.app.rest.unpin_message.assert_awaited_once_with(12345679, 77790)

    @pytest.mark.asyncio()
    async def test_delete_messages(self, model):
        model.app.rest.delete_messages = mock.AsyncMock()

        await model.delete_messages([77790, 88890, 1800], 1337)

        model.app.rest.delete_messages.assert_awaited_once_with(12345679, [77790, 88890, 1800], 1337)

    @pytest.mark.asyncio()
    async def test_send(self, model):
        model.app.rest.create_message = mock.AsyncMock()
        mock_attachment = object()
        mock_component = object()
        mock_components = [object(), object()]
        mock_embed = object()
        mock_embeds = object()
        mock_attachments = [object(), object(), object()]
        mock_reply = object()

        await model.send(
            content="test content",
            tts=True,
            attachment=mock_attachment,
            attachments=mock_attachments,
            component=mock_component,
            components=mock_components,
            embed=mock_embed,
            embeds=mock_embeds,
            sticker=543,
            stickers=[132, 65423],
            reply=mock_reply,
            reply_must_exist=False,
            mentions_everyone=False,
            user_mentions=[123, 456],
            role_mentions=[789, 567],
            mentions_reply=True,
            flags=6969,
        )

        model.app.rest.create_message.assert_awaited_once_with(
            channel=12345679,
            content="test content",
            tts=True,
            attachment=mock_attachment,
            attachments=mock_attachments,
            component=mock_component,
            components=mock_components,
            embed=mock_embed,
            embeds=mock_embeds,
            sticker=543,
            stickers=[132, 65423],
            reply=mock_reply,
            reply_must_exist=False,
            mentions_everyone=False,
            user_mentions=[123, 456],
            role_mentions=[789, 567],
            mentions_reply=True,
            flags=6969,
        )

    def test_trigger_typing(self, model):
        model.app.rest.trigger_typing = mock.Mock()

        model.trigger_typing()

        model.app.rest.trigger_typing.assert_called_once_with(12345679)


class TestGuildChannel:
    @pytest.fixture()
    def model(self, mock_app):
        return hikari_test_helpers.mock_class_namespace(channels.GuildChannel)(
            app=mock_app,
            id=snowflakes.Snowflake(69420),
            name="foo1",
            type=channels.ChannelType.GUILD_VOICE,
            guild_id=snowflakes.Snowflake(123456789),
            parent_id=None,
        )

    def test_shard_id_property_when_not_shard_aware(self, model):
        model.app = None

        assert model.shard_id is None

    def test_shard_id_property_when_guild_id_is_not_None(self, model):
        model.app.shard_count = 3
        assert model.shard_id == 2

    @pytest.mark.asyncio()
    async def test_fetch_guild(self, model):
        model.app.rest.fetch_guild = mock.AsyncMock()

        assert await model.fetch_guild() is model.app.rest.fetch_guild.return_value

        model.app.rest.fetch_guild.assert_awaited_once_with(123456789)

    @pytest.mark.asyncio()
    async def test_edit(self, model):
        model.app.rest.edit_channel = mock.AsyncMock()

        result = await model.edit(
            name="Supa fast boike",
            bitrate=420,
            reason="left right",
            default_auto_archive_duration=123312,
            position=4423,
            topic="hi",
            nsfw=True,
            video_quality_mode=channels.VideoQualityMode.AUTO,
            user_limit=123321,
            rate_limit_per_user=54123123,
            region="us-west",
            parent_category=341123123123,
            permission_overwrites={123: "123"},
            flags=12,
            archived=True,
            auto_archive_duration=1234,
            locked=True,
            invitable=True,
            applied_tags=[12345, 54321],
        )

        assert result is model.app.rest.edit_channel.return_value
        model.app.rest.edit_channel.assert_awaited_once_with(
            69420,
            name="Supa fast boike",
            position=4423,
            topic="hi",
            nsfw=True,
            bitrate=420,
            video_quality_mode=channels.VideoQualityMode.AUTO,
            user_limit=123321,
            rate_limit_per_user=54123123,
            region="us-west",
            permission_overwrites={123: "123"},
            parent_category=341123123123,
            default_auto_archive_duration=123312,
            flags=12,
            archived=True,
            auto_archive_duration=1234,
            locked=True,
            invitable=True,
            applied_tags=[12345, 54321],
            reason="left right",
        )


class TestPermissibleGuildChannel:
    @pytest.fixture()
    def model(self, mock_app):
        return hikari_test_helpers.mock_class_namespace(channels.PermissibleGuildChannel)(
            app=mock_app,
            id=snowflakes.Snowflake(69420),
            name="foo1",
            type=channels.ChannelType.GUILD_VOICE,
            guild_id=snowflakes.Snowflake(123456789),
            is_nsfw=True,
            parent_id=None,
            position=54,
            permission_overwrites=[],
        )

    @pytest.mark.asyncio()
    async def test_edit_overwrite(self, model):
        model.app.rest.edit_permission_overwrite = mock.AsyncMock()
        user = mock.Mock(users.PartialUser)
        await model.edit_overwrite(
            333,
            target_type=user,
            allow=permissions.Permissions.BAN_MEMBERS,
            deny=permissions.Permissions.CONNECT,
            reason="vrooom vroom",
        )

        model.app.rest.edit_permission_overwrite.assert_called_once_with(
            69420,
            333,
            target_type=user,
            allow=permissions.Permissions.BAN_MEMBERS,
            deny=permissions.Permissions.CONNECT,
            reason="vrooom vroom",
        )

    @pytest.mark.asyncio()
    async def test_edit_overwrite_target_type_none(self, model):
        model.app.rest.edit_permission_overwrite = mock.AsyncMock()
        user = mock.Mock(users.PartialUser)
        await model.edit_overwrite(
            user, allow=permissions.Permissions.BAN_MEMBERS, deny=permissions.Permissions.CONNECT, reason="vrooom vroom"
        )

        model.app.rest.edit_permission_overwrite.assert_called_once_with(
            69420,
            user,
            allow=permissions.Permissions.BAN_MEMBERS,
            deny=permissions.Permissions.CONNECT,
            reason="vrooom vroom",
        )

    @pytest.mark.asyncio()
    async def test_remove_overwrite(self, model):
        model.app.rest.delete_permission_overwrite = mock.AsyncMock()

        await model.remove_overwrite(333)

        model.app.rest.delete_permission_overwrite.assert_called_once_with(69420, 333)

    def test_get_guild(self, model):
        guild = mock.Mock(id=123456789)
        model.app.cache.get_guild.side_effect = [guild]

        assert model.get_guild() == guild

        model.app.cache.get_guild.assert_called_once_with(123456789)

    def test_get_guild_when_guild_not_in_cache(self, model):
        model.app.cache.get_guild.side_effect = [None]

        assert model.get_guild() is None

        model.app.cache.get_guild.assert_called_once_with(123456789)

    def test_get_guild_when_no_cache_trait(self, model):
        model.app = object()

        assert model.get_guild() is None

    @pytest.mark.asyncio()
    async def test_fetch_guild(self, model):
        model.app.rest.fetch_guild = mock.AsyncMock()

        assert await model.fetch_guild() == model.app.rest.fetch_guild.return_value

        model.app.rest.fetch_guild.assert_awaited_once_with(123456789)


class TestForumTag:
    @pytest.mark.parametrize(
        ("emoji", "expected_unicode_emoji", "expected_emoji_id"),
        [(123, None, 123), ("emoji", "emoji", None), (None, None, None)],
    )
    def test_emoji_parameters(self, emoji, expected_emoji_id, expected_unicode_emoji):
        tag = channels.ForumTag(name="testing", emoji=emoji)

        assert tag.emoji_id == expected_emoji_id
        assert tag.unicode_emoji == expected_unicode_emoji
