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

from hikari.models import channels
from hikari.models import permissions
from hikari.models import users
from hikari.utilities import files
from tests.hikari import hikari_test_helpers


def test_ChannelType_str_operator():
    channel_type = channels.ChannelType(1)
    assert str(channel_type) == "PRIVATE_TEXT"


def test_PermissionOverwriteType_str_operator():
    overwrite_type = channels.PermissionOverwriteType("role")
    assert str(overwrite_type) == "ROLE"


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
    mock_channel = mock.Mock(channels.PrivateTextChannel, recipient=mock_user)
    assert channels.PrivateTextChannel.__str__(mock_channel) == "PrivateTextChannel with: snoop#0420"


def test_DMChannel_shard_id():
    assert hikari_test_helpers.stub_class(channels.PrivateTextChannel).shard_id == 0


def test_GroupDMChannel_str_operator():
    mock_channel = mock.Mock(channels.GroupPrivateTextChannel)
    mock_channel.name = "super cool group dm"
    assert channels.GroupPrivateTextChannel.__str__(mock_channel) == "super cool group dm"


def test_GroupDMChannel_str_operator_when_name_is_None():
    user = mock.Mock(users.UserImpl, __str__=mock.Mock(return_value="snoop#0420"))
    other_user = mock.Mock(users.UserImpl, __str__=mock.Mock(return_value="nice#6969"))
    mock_channel = mock.Mock(channels.GroupPrivateTextChannel, recipients={1: user, 2: other_user})
    mock_channel.name = None
    assert (
        channels.GroupPrivateTextChannel.__str__(mock_channel) == "GroupPrivateTextChannel with: snoop#0420, nice#6969"
    )


def test_PermissionOverwrite_unset():
    overwrite = channels.PermissionOverwrite(type=channels.PermissionOverwriteType.MEMBER, id=1234321)
    overwrite.allow = permissions.Permissions.CREATE_INSTANT_INVITE
    overwrite.deny = permissions.Permissions.CHANGE_NICKNAME
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

    mock_channel._rest.rest.create_message.assert_called_once_with(
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

    mock_channel._rest.rest.fetch_messages.assert_called_once_with(
        123,
        before=datetime.datetime(2020, 4, 1, 1, 0, 0),
        after=datetime.datetime(2020, 4, 1, 0, 0, 0),
        around=datetime.datetime(2020, 4, 1, 0, 30, 0),
    )


def test_GroupDMChannel_icon():
    channel = hikari_test_helpers.mock_class_namespace(
        channels.GroupPrivateTextChannel, init=False, format_icon=mock.Mock(return_value="icon")
    )()
    assert channel.icon == "icon"
    channel.format_icon.assert_called_once()


def test_GroupDMChannel_format_icon():
    mock_channel = mock.Mock(channels.GroupPrivateTextChannel, id=123, icon_hash="456abc")
    assert channels.GroupPrivateTextChannel.format_icon(mock_channel, format="jpeg", size=16) == files.URL(
        "https://cdn.discordapp.com/channel-icons/123/456abc.jpeg?size=16"
    )


def test_GroupDMChannel_format_icon_without_optionals():
    mock_channel = mock.Mock(channels.GroupPrivateTextChannel, id=123, icon_hash="456abc")
    assert channels.GroupPrivateTextChannel.format_icon(mock_channel) == files.URL(
        "https://cdn.discordapp.com/channel-icons/123/456abc.png?size=4096"
    )


def test_GroupDMChannel_format_icon_when_hash_is_None():
    mock_channel = mock.Mock(channels.GroupPrivateTextChannel, icon_hash=None)
    assert channels.GroupPrivateTextChannel.format_icon(mock_channel) is None


def test_GuildChannel_shard_id_property_when_guild_id_is_None():
    channel = hikari_test_helpers.stub_class(channels.GuildChannel, guild_id=None)
    assert channel.shard_id is None


@pytest.mark.parametrize("error", (TypeError, AttributeError, NameError))
def test_GuildChannel_shard_id_property_when_guild_id_error_raised(error):
    channel = hikari_test_helpers.stub_class(channels.GuildChannel, guild_id=mock.Mock(side_effect=error))
    assert channel.shard_id is None


def test_GuildChannel_shard_id_property_when_guild_id_is_not_None():
    channel = hikari_test_helpers.stub_class(channels.GuildChannel, guild_id=123456789, app=mock.Mock(shard_count=3))
    assert channel.shard_id == 2
