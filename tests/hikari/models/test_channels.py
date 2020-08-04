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
    class StubPrivateChannel(channels.PrivateTextChannel):
        def __init__(self):
            ...

    assert StubPrivateChannel().shard_id == 0


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
    overwrite = channels.PermissionOverwrite(type=channels.PermissionOverwriteType.MEMBER)
    overwrite.allow = permissions.Permission.CREATE_INSTANT_INVITE
    overwrite.deny = permissions.Permission.CHANGE_NICKNAME
    assert overwrite.unset == permissions.Permission(-67108866)


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

    mock_channel.app.rest.create_message.assert_called_once_with(
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

    mock_channel.app.rest.fetch_messages.assert_called_once_with(
        123,
        before=datetime.datetime(2020, 4, 1, 1, 0, 0),
        after=datetime.datetime(2020, 4, 1, 0, 0, 0),
        around=datetime.datetime(2020, 4, 1, 0, 30, 0),
    )


def test_GroupDMChannel_icon():
    class StubGroupPrivateTextChannel(channels.GroupPrivateTextChannel):
        def __init__(self):
            pass

    channel = StubGroupPrivateTextChannel()
    channel.format_icon = mock.Mock(return_value="icon")

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


class StubGuildChannel(channels.GuildChannel):
    def __init__(self):
        pass


def test_GuildChannel_shard_id_property_when_guild_id_is_None():
    channel = StubGuildChannel()
    channel.guild_id = None

    assert channel.shard_id is None


@pytest.mark.parametrize("error", (TypeError, AttributeError, NameError))
def test_GuildChannel_shard_id_property_when_guild_id_error_raised(error):
    channel = StubGuildChannel()
    channel.guild_id = mock.Mock(side_effect=error)

    assert channel.shard_id is None


def test_GuildChannel_shard_id_property_when_guild_id_is_not_None():
    channel = StubGuildChannel()
    channel.guild_id = 123456789
    channel.app = mock.Mock(shard_count=3)

    assert channel.shard_id == 2
