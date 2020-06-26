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

from hikari.models import channels
from hikari.models import users


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
