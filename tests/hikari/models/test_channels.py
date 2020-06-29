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

import pytest
import mock

from hikari.models import channels
from hikari.models import users
from hikari.models import permissions
from hikari.utilities import files
from tests.hikari import hikari_test_helpers


def test_ChannelType_str_operator():
    channel_type = channels.ChannelType(1)
    assert str(channel_type) == "DM"


def test_PermissionOverwriteType_str_operator():
    overwrite_type = channels.PermissionOverwriteType("role")
    assert str(overwrite_type) == "ROLE"


def test_PartialChannel_str_operator():
    channel = channels.PartialChannel()
    channel.name = "foo"
    assert str(channel) == "foo"


def test_PartialChannel_str_operator_when_name_is_None():
    channel = channels.PartialChannel()
    channel.id = 1234567
    channel.name = None
    assert str(channel) == "Unnamed channel ID 1234567"


def test_DMChannel_str_operator():
    channel = channels.DMChannel()
    user = users.User()
    user.discriminator = "0420"
    user.username = "snoop"
    channel.recipients = {1: user}
    assert str(channel) == "DMChannel with: snoop#0420"


def test_GroupDMChannel_str_operator():
    channel = channels.GroupDMChannel()
    channel.name = "super cool group dm"
    assert str(channel) == "super cool group dm"


def test_GroupDMChannel_str_operator_when_name_is_None():
    channel = channels.GroupDMChannel()
    channel.name = None
    user, other_user = users.User(), users.User()
    user.discriminator = "0420"
    user.username = "snoop"
    other_user.discriminator = "6969"
    other_user.username = "nice"
    channel.recipients = {1: user, 2: other_user}
    assert str(channel) == "GroupDMChannel with: snoop#0420, nice#6969"


def test_PermissionOverwrite_unset():
    overwrite = channels.PermissionOverwrite(type=channels.PermissionOverwriteType.MEMBER)
    overwrite.allow = permissions.Permission.CREATE_INSTANT_INVITE
    overwrite.deny = permissions.Permission.CHANGE_NICKNAME
    assert overwrite.unset == permissions.Permission(-67108866)


@pytest.mark.asyncio
async def test_TextChannel_send():
    channel = channels.TextChannel()
    channel.id = 123
    channel.app = mock.Mock()
    channel.app.rest.create_message = mock.AsyncMock()
    mock_attachment = mock.Mock()
    mock_embed = mock.Mock()
    mock_attachments = [mock.Mock(), mock.Mock(), mock.Mock()]

    await channel.send(
        text="test content",
        nonce="abc123",
        tts=True,
        attachment=mock_attachment,
        attachments=mock_attachments,
        embed=mock_embed,
        mentions_everyone=False,
        user_mentions=[123, 456],
        role_mentions=[789, 567],
    )

    channel.app.rest.create_message.assert_called_once_with(
        channel=123,
        text="test content",
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
    channel = channels.TextChannel()
    channel.id = 123
    channel.app = mock.Mock()
    channel.app.rest.fetch_messages = mock.AsyncMock()

    await channel.history(
        before=datetime.datetime(2020, 4, 1, 1, 0, 0),
        after=datetime.datetime(2020, 4, 1, 0, 0, 0),
        around=datetime.datetime(2020, 4, 1, 0, 30, 0),
    )

    channel.app.rest.fetch_messages.assert_called_once_with(
        123,
        before=datetime.datetime(2020, 4, 1, 1, 0, 0),
        after=datetime.datetime(2020, 4, 1, 0, 0, 0),
        around=datetime.datetime(2020, 4, 1, 0, 30, 0),
    )


def test_GroupDMChannel_icon():
    channel = hikari_test_helpers.unslot_class(channels.GroupDMChannel)()
    channel.format_icon = mock.Mock(return_value="icon")

    assert channel.icon == "icon"
    channel.format_icon.assert_called_once()


def test_GroupDMChannel_format_icon():
    channel = channels.GroupDMChannel()
    channel.id = 123
    channel.icon_hash = "456abc"

    assert channel.format_icon(format="jpeg", size=16) == files.URL(
        "https://cdn.discordapp.com/channel-icons/123/456abc.jpeg?size=16"
    )


def test_GroupDMChannel_format_icon_without_optionals():
    channel = channels.GroupDMChannel()
    channel.id = 123
    channel.icon_hash = "456abc"

    assert channel.format_icon() == files.URL("https://cdn.discordapp.com/channel-icons/123/456abc.png?size=4096")


def test_GroupDMChannel_format_icon_when_hash_is_None():
    channel = channels.GroupDMChannel()
    channel.icon_hash = None

    assert channel.format_icon() is None
