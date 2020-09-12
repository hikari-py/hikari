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
    return mock.Mock(bot.BotApp)


def test_ChannelType_str_operator():
    channel_type = channels.ChannelType(1)
    assert str(channel_type) == "DM"


class TestChannelFollow:
    @pytest.mark.asyncio
    async def test_fetch_channel(self, mock_app):
        mock_channel = mock.MagicMock(spec=channels.GuildNewsChannel)
        mock_app.rest.fetch_channel = mock.AsyncMock(return_value=mock_channel)
        follow = channels.ChannelFollow(channel_id=snowflakes.Snowflake(9459234123), app=mock_app, webhook_id=3123123)

        result = await follow.fetch_channel()

        assert result is mock_channel
        mock_app.rest.fetch_channel.assert_awaited_once_with(9459234123)

    @pytest.mark.asyncio
    async def test_fetch_webhook(self, mock_app):
        mock_webhook = object()
        mock_app.rest.fetch_webhook = mock.AsyncMock(return_value=mock_webhook)
        follow = channels.ChannelFollow(webhook_id=snowflakes.Snowflake(54123123), app=mock_app, channel_id=94949494)

        result = await follow.fetch_webhook()

        assert result is mock_webhook
        mock_app.rest.fetch_webhook.assert_awaited_once_with(54123123)

    @pytest.mark.asyncio
    async def test_channel(self, mock_app):
        mock_channel = mock.MagicMock(spec=channels.GuildNewsChannel)
        mock_app.cache.get_guild_channel = mock.Mock(return_value=mock_channel)
        follow = channels.ChannelFollow(webhook_id=993883, app=mock_app, channel_id=snowflakes.Snowflake(696969))

        result = follow.channel

        assert result is mock_channel
        mock_app.cache.get_guild_channel.assert_called_once_with(696969)


@pytest.mark.parametrize(("type", "expect_name"), [(0, "ROLE"), (1, "MEMBER")])
def test_PermissionOverwriteType_str_operator(type, expect_name):
    overwrite_type = channels.PermissionOverwriteType(type)
    assert str(overwrite_type) == expect_name


def test_PartialChannel_str_operator():
    mock_channel = mock.Mock(channels.PartialChannel)
    mock_channel.name = "foo"
    assert channels.PartialChannel.__str__(mock_channel) == "foo"


def test_PartialChannel_str_operator_when_name_is_None():
    mock_channel = mock.Mock(channels.PartialChannel, id=1234567)
    mock_channel.name = None
    assert channels.PartialChannel.__str__(mock_channel) == "Unnamed PartialChannel ID 1234567"


def test_DMChannel_str_operator():
    mock_user = mock.Mock(users.UserImpl, __str__=mock.Mock(return_value="snoop#0420"))
    mock_user.discriminator = "0420"
    mock_user.username = "snoop"
    mock_channel = mock.Mock(channels.DMChannel, recipient=mock_user)
    assert channels.DMChannel.__str__(mock_channel) == "DMChannel with: snoop#0420"


def test_DMChannel_shard_id():
    assert hikari_test_helpers.stub_class(channels.DMChannel).shard_id == 0


def test_GroupDMChannel_str_operator():
    mock_channel = mock.Mock(channels.GroupDMChannel)
    mock_channel.name = "super cool group dm"
    assert channels.GroupDMChannel.__str__(mock_channel) == "super cool group dm"


def test_GroupDMChannel_str_operator_when_name_is_None():
    user = mock.Mock(users.UserImpl, __str__=mock.Mock(return_value="snoop#0420"))
    other_user = mock.Mock(users.UserImpl, __str__=mock.Mock(return_value="nice#6969"))
    mock_channel = mock.Mock(channels.GroupDMChannel, recipients={1: user, 2: other_user})
    mock_channel.name = None
    assert channels.GroupDMChannel.__str__(mock_channel) == "GroupDMChannel with: snoop#0420, nice#6969"


def test_PermissionOverwrite_unset():
    overwrite = channels.PermissionOverwrite(type=channels.PermissionOverwriteType.MEMBER, id=1234321)
    overwrite._allow = permissions.Permissions.CREATE_INSTANT_INVITE
    overwrite._deny = permissions.Permissions.CHANGE_NICKNAME
    assert overwrite.unset == permissions.Permissions(-67108866)


@pytest.mark.asyncio
async def test_TextChannel_send():
    app = mock.Mock()
    app.rest.create_message = mock.AsyncMock()
    mock_channel = mock.Mock(channels.TextChannel, id=123, app=app)
    mock_attachment = object()
    mock_embed = object()
    mock_attachments = [object(), object(), object()]

    await channels.TextChannel.send(
        mock_channel,
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

    mock_channel.app.rest.create_message.assert_awaited_once_with(
        channel=123,
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


@pytest.mark.asyncio
async def test_TextChannel_history():
    app = mock.Mock()
    app.rest.fetch_messages = mock.AsyncMock()
    mock_channel = mock.Mock(channels.TextChannel, id=123, app=app)

    await channels.TextChannel.history(
        mock_channel,
        before=datetime.datetime(2020, 4, 1, 1, 0, 0),
        after=datetime.datetime(2020, 4, 1, 0, 0, 0),
        around=datetime.datetime(2020, 4, 1, 0, 30, 0),
    )

    mock_channel.app.rest.fetch_messages.assert_awaited_once_with(
        123,
        before=datetime.datetime(2020, 4, 1, 1, 0, 0),
        after=datetime.datetime(2020, 4, 1, 0, 0, 0),
        around=datetime.datetime(2020, 4, 1, 0, 30, 0),
    )


def test_GroupDMChannel_icon_url():
    channel = hikari_test_helpers.mock_class_namespace(
        channels.GroupDMChannel, init=False, format_icon=mock.Mock(return_value="icon")
    )()
    assert channel.icon_url == "icon"
    channel.format_icon.assert_called_once()


def test_GroupDMChannel_format_icon():
    mock_channel = mock.Mock(channels.GroupDMChannel, id=123, icon_hash="456abc")
    assert channels.GroupDMChannel.format_icon(mock_channel, ext="jpeg", size=16) == files.URL(
        "https://cdn.discordapp.com/channel-icons/123/456abc.jpeg?size=16"
    )


def test_GroupDMChannel_format_icon_without_optionals():
    mock_channel = mock.Mock(channels.GroupDMChannel, id=123, icon_hash="456abc")
    assert channels.GroupDMChannel.format_icon(mock_channel) == files.URL(
        "https://cdn.discordapp.com/channel-icons/123/456abc.png?size=4096"
    )


def test_GroupDMChannel_format_icon_when_hash_is_None():
    mock_channel = mock.Mock(channels.GroupDMChannel, icon_hash=None)
    assert channels.GroupDMChannel.format_icon(mock_channel) is None


def test_GuildChannel_shard_id_property_when_guild_id_is_None():
    channel = hikari_test_helpers.stub_class(channels.GuildChannel, guild_id=None)
    assert channel.shard_id is None


@pytest.mark.parametrize("error", [TypeError, AttributeError, NameError])
def test_GuildChannel_shard_id_property_when_guild_id_error_raised(error):
    channel = hikari_test_helpers.stub_class(channels.GuildChannel, guild_id=mock.Mock(side_effect=error))
    assert channel.shard_id is None


def test_GuildChannel_shard_id_property_when_guild_id_is_not_None():
    channel = hikari_test_helpers.stub_class(channels.GuildChannel, guild_id=123456789, app=mock.Mock(shard_count=3))
    assert channel.shard_id == 2
