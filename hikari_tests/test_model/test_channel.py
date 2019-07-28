#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
from unittest import mock

import pytest

from hikari.model import channel


@pytest.mark.model
class TestChannel:
    def test_GuildTextChannel_from_dict(self):
        gtc = channel.GuildTextChannel.from_dict(
            {
                "id": "1234567",
                "guild_id": "696969",
                "position": 100,
                "permission_overwrites": [],
                "nsfw": True,
                "parent_id": None,
                "rate_limit_per_user": 420,
                "topic": "nsfw stuff",
                "name": "shh!",
            },
            NotImplemented,
        )

        assert gtc.id == 1234567
        assert gtc.guild_id == 696969
        assert gtc.position == 100
        assert gtc.permission_overwrites == []
        assert gtc.nsfw is True
        assert gtc.parent_id is None
        assert gtc.rate_limit_per_user == 420
        assert gtc.topic == "nsfw stuff"
        assert gtc.name == "shh!"

    def test_DMChannel_from_dict(self):
        dmc = channel.DMChannel.from_dict({
            "id": "929292",
            "last_message_id": "12345",
            "recipients": []
        }, NotImplemented)

        assert dmc.id == 929292
        assert dmc.last_message_id == 12345
        assert dmc.recipients == []

    def test_GuildVoiceChannel_from_dict(self):
        gvc = channel.GuildVoiceChannel.from_dict(
            {
                "id": "9292929",
                "guild_id": "929",
                "position": 66,
                "permission_overwrites": [],
                "name": "roy rodgers mc freely",
                "bitrate": 999,
                "user_limit": 0,
                "parent_id": "42",
            },
            NotImplemented,
        )

        assert gvc.id == 9292929
        assert gvc.guild_id == 929
        assert gvc.position == 66
        assert gvc.permission_overwrites == []
        assert gvc.name == "roy rodgers mc freely"
        assert gvc.bitrate == 999
        assert gvc.user_limit is None
        assert gvc.parent_id == 42

    def test_GroupDMChannel_from_dict(self):
        gdmc = channel.GroupDMChannel.from_dict(
            {
                "id": "99999999999",
                "last_message_id": None,
                "recipients": [],
                "icon": "1a2b3c4d",
                "name": "shitposting 101",
                "owner_application_id": "111111",
                "owner_id": "111111",
            },
            NotImplemented,
        )

        assert gdmc.id == 99999999999
        assert gdmc.last_message_id is None
        assert gdmc.recipients == []
        assert gdmc.icon_hash == "1a2b3c4d"
        assert gdmc.name == "shitposting 101"
        assert gdmc.owner_application_id == 111111
        assert gdmc.owner_id == 111111

    def test_GuildCategory_from_dict(self):
        gc = channel.GuildCategory.from_dict({
            "id": "123456",
            "guild_id": "54321",
            "position": 69,
            "permission_overwrites": [],
            "name": "dank category",
        }, NotImplemented)

        assert gc.name == "dank category"
        assert gc.position == 69
        assert gc.guild_id == 54321
        assert gc.id == 123456
        assert gc.permission_overwrites == []

    def test_GuildNewsChannel_from_dict(self):
        gnc = channel.GuildNewsChannel.from_dict(
            {
                "id": "4444",
                "guild_id": "1111",
                "position": 24,
                "permission_overwrites": [],
                "name": "oylumo",
                "nsfw": False,
                "parent_id": "3232",
                "topic": "crap and stuff",
                "last_message_id": None,
            },
            NotImplemented,
        )

        assert gnc.id == 4444
        assert gnc.guild_id == 1111
        assert gnc.position == 24
        assert gnc.permission_overwrites == []
        assert gnc.name
        assert gnc.nsfw is False
        assert gnc.parent_id == 3232
        assert gnc.topic == "crap and stuff"
        assert gnc.last_message_id is None

    def test_GuildStoreChannel_from_dict(self):
        gsc = channel.GuildStoreChannel.from_dict(
            {
                "id": "9876",
                "guild_id": "7676",
                "position": 9,
                "permission_overwrites": [],
                "name": "a",
                "parent_id": "32",
            },
            NotImplemented,
        )

        assert gsc.id == 9876
        assert gsc.guild_id == 7676
        assert gsc.position == 9
        assert gsc.permission_overwrites == []
        assert gsc.name == "a"
        assert gsc.parent_id == 32

    @pytest.mark.parametrize(
        ["type_field", "expected_class"],
        [
            (0, channel.GuildTextChannel),
            (1, channel.DMChannel),
            (2, channel.GuildVoiceChannel),
            (3, channel.GroupDMChannel),
            (4, channel.GuildCategory),
            (5, channel.GuildNewsChannel),
            (6, channel.GuildStoreChannel),
        ],
    )
    def test_channel_from_dict_success_case(self, type_field, expected_class):
        fqn = expected_class.__module__ + "." + expected_class.__qualname__ + ".from_dict"
        with mock.patch(fqn) as m:
            channel.channel_from_dict({"type": type_field}, NotImplemented)
            m.assert_called_once_with({"type": type_field}, NotImplemented)

    def test_channel_from_dict_failure_case(self):
        try:
            channel.channel_from_dict({"type": -999}, NotImplemented)
            assert False
        except TypeError:
            pass
