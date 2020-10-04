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
import datetime

import mock
import pytest

from hikari import channels
from hikari import files
from hikari import permissions
from hikari import snowflakes
from hikari import users
from hikari.impl import bot
from tests.hikari import hikari_test_helpers


@pytest.fixture()
def mock_app():
    return mock.Mock(spec_set=bot.BotApp)


class TestChannelType:
    def test_str_operator(self):
        channel_type = channels.ChannelType(1)
        assert str(channel_type) == "DM"


class TestChannelFollow:
    @pytest.mark.asyncio
    async def test_fetch_channel(self, mock_app):
        mock_channel = mock.Mock(spec=channels.GuildNewsChannel)
        mock_app.rest.fetch_channel = mock.AsyncMock(return_value=mock_channel)
        follow = channels.ChannelFollow(
            channel_id=snowflakes.Snowflake(9459234123), app=mock_app, webhook_id=snowflakes.Snowflake(3123123)
        )

        result = await follow.fetch_channel()

        assert result is mock_channel
        mock_app.rest.fetch_channel.assert_awaited_once_with(9459234123)

    @pytest.mark.asyncio
    async def test_fetch_webhook(self, mock_app):
        mock_webhook = object()
        mock_app.rest.fetch_webhook = mock.AsyncMock(return_value=mock_webhook)
        follow = channels.ChannelFollow(
            webhook_id=snowflakes.Snowflake(54123123), app=mock_app, channel_id=snowflakes.Snowflake(94949494)
        )

        result = await follow.fetch_webhook()

        assert result is mock_webhook
        mock_app.rest.fetch_webhook.assert_awaited_once_with(54123123)

    @pytest.mark.asyncio
    async def test_channel(self, mock_app):
        mock_channel = mock.Mock(spec=channels.GuildNewsChannel)
        mock_app.cache.get_guild_channel = mock.Mock(return_value=mock_channel)
        follow = channels.ChannelFollow(
            webhook_id=snowflakes.Snowflake(993883), app=mock_app, channel_id=snowflakes.Snowflake(696969)
        )

        result = follow.channel

        assert result is mock_channel
        mock_app.cache.get_guild_channel.assert_called_once_with(696969)


class TestPermissionOverwrite:
    @pytest.mark.parametrize(("type", "expect_name"), [(0, "ROLE"), (1, "MEMBER")])
    def test_str_operator(self, type, expect_name):
        overwrite_type = channels.PermissionOverwriteType(type)
        assert str(overwrite_type) == expect_name

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
            app=mock_app,
            id=snowflakes.Snowflake(1234567),
            name="foo",
            type=channels.ChannelType.GUILD_NEWS,
        )

    def test_str_operator(self, model):
        assert str(model) == "foo"

    def test_str_operator_when_name_is_None(self, model):
        model.name = None
        assert str(model) == "Unnamed PartialChannel ID 1234567"


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
            nicknames={
                snowflakes.Snowflake(1): "person 1",
                snowflakes.Snowflake(2): "person 2",
            },
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
            channels.GroupDMChannel, init_=False, format_icon=mock.Mock(return_value="icon-url-here.com")
        )()
        assert channel.icon_url == "icon-url-here.com"
        channel.format_icon.assert_called_once()

    def test_format_icon(self, model):
        assert model.format_icon(ext="jpeg", size=16) == files.URL(
            "https://cdn.discordapp.com/channel-icons/136134/1a2b3c.jpeg?size=16"
        )

    def test_format_icon_without_optional_params(self, model):
        assert model.format_icon() == files.URL("https://cdn.discordapp.com/channel-icons/136134/1a2b3c.png?size=4096")

    def test_format_icon_when_hash_is_None(self, model):
        model.icon_hash = None
        assert model.format_icon() is None


@pytest.mark.asyncio
class TestTextChannel:
    @pytest.fixture()
    def model(self, mock_app):
        return hikari_test_helpers.mock_class_namespace(channels.TextChannel)(
            app=mock_app,
            id=snowflakes.Snowflake(12345679),
            name="foo1",
            type=channels.ChannelType.GUILD_TEXT,
        )

    async def test_history(self, model):
        model.app.rest.fetch_messages = mock.AsyncMock()

        await model.history(
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

    async def test_send(self, model):
        model.app.rest.create_message = mock.AsyncMock()
        mock_attachment = object()
        mock_embed = object()
        mock_attachments = [object(), object(), object()]

        await model.send(
            content="test content",
            nonce="abc123",
            tts=True,
            attachment=mock_attachment,
            attachments=mock_attachments,
            embed=mock_embed,
            mentions_everyone=False,
            user_mentions=[123, 456],
            role_mentions=[789, 567],
        )

        model.app.rest.create_message.assert_awaited_once_with(
            channel=12345679,
            content="test content",
            nonce="abc123",
            tts=True,
            attachment=mock_attachment,
            attachments=mock_attachments,
            embed=mock_embed,
            mentions_everyone=False,
            user_mentions=[123, 456],
            role_mentions=[789, 567],
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
            position=12,
            permission_overwrites={},
            is_nsfw=True,
            parent_id=None,
        )

    @pytest.mark.parametrize("error", [TypeError, AttributeError, NameError])
    def test_shard_id_property_when_guild_id_error_raised(self, model, error):
        class BrokenApp:
            def __getattr__(self, name):
                if name == "shard_count":
                    raise error
                return mock.Mock()

        model.app = BrokenApp()

        assert model.shard_id is None

    def test_shard_id_property_when_guild_id_is_not_None(self, model):
        model.app.shard_count = 3
        assert model.shard_id == 2
