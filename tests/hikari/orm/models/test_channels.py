#!/usr/bin/env python3
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
from unittest import mock

import pytest

from hikari.orm import fabric
from hikari.orm import state_registry
from hikari.orm.models import channels
from hikari.orm.models import guilds
from tests.hikari import _helpers


@pytest.fixture
def mock_fabric():
    mock_state = mock.MagicMock(spec_set=state_registry.IStateRegistry)
    return fabric.Fabric(NotImplemented, mock_state)


@pytest.fixture
def mock_guild():
    return mock.MagicMock(spec_set=guilds.Guild)


@pytest.fixture
def mock_user():
    return {
        "id": "379953393319542784",
        "username": "OwO Chan",
        "discriminator": "2880",
        "avatar": "7aa35e8df9db77085a1232bd3d99f7ac",
    }


@pytest.mark.model
@pytest.mark.parametrize(
    "expected_type",
    [
        channels.GroupDMChannel,
        channels.DMChannel,
        channels.GuildTextChannel,
        channels.GuildAnnouncementChannel,
        channels.GuildCategory,
        channels.GuildStoreChannel,
        channels.GuildVoiceChannel,
    ],
)
def test_Channel_get_channel_class_from_type(expected_type):
    # Make sure that this will successfully parse from both the enum and raw integer type.
    assert channels.Channel.get_channel_class_from_type(expected_type.type) is expected_type
    assert channels.Channel.get_channel_class_from_type(expected_type.type.value) is expected_type


@pytest.mark.model()
def test_GuildChannel_permission_overwrites_aggregation(mock_fabric, mock_guild):
    mock_fabric.state_registry.get_guild_by_id.return_value = mock_guild
    mock_guild.channels = {1234: mock.MagicMock(spec_set=channels.GuildCategory)}

    guild_text_channel_obj = channels.GuildTextChannel(
        mock_fabric,
        {
            "type": 0,
            "id": "1234567",
            "guild_id": "696969",
            "position": 100,
            "permission_overwrites": [{"id": "123", "allow": 456, "deny": 789, "type": "member"}],
            "nsfw": True,
            "parent_id": "1234",
            "rate_limit_per_user": 420,
            "topic": "nsfw stuff",
            "name": "shh!",
        },
    )

    assert len(guild_text_channel_obj.permission_overwrites) == 1
    assert guild_text_channel_obj.permission_overwrites[0].id == 123
    guild_text_channel_obj.__repr__()
    guild_text_channel_obj.permission_overwrites[0].__repr__()


@pytest.mark.model
def test_GuildChannel_parent_when_specified(mock_fabric, mock_guild):
    mock_fabric.state_registry.get_guild_by_id.return_value = mock_guild
    mock_guild.channels = {1234: mock.MagicMock(spec_set=channels.GuildCategory)}

    guild_text_channel_obj = channels.GuildTextChannel(
        mock_fabric,
        {
            "type": 0,
            "id": "1234567",
            "guild_id": "696969",
            "position": 100,
            "permission_overwrites": [],
            "nsfw": True,
            "parent_id": "1234",
            "rate_limit_per_user": 420,
            "topic": "nsfw stuff",
            "name": "shh!",
        },
    )

    assert guild_text_channel_obj.parent is mock_guild.channels[1234]
    guild_text_channel_obj.__repr__()


@pytest.mark.model
def test_GuildChannel_parent_when_unspecified(mock_fabric, mock_guild):
    mock_fabric.state_registry.get_guild_by_id.return_value = mock_guild
    mock_guild.channels = {1234: mock.MagicMock(spec_set=channels.GuildCategory)}

    guild_text_channel_obj = channels.GuildTextChannel(
        mock_fabric,
        {
            "type": 0,
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
    )

    assert guild_text_channel_obj.parent is None
    guild_text_channel_obj.__repr__()


@pytest.mark.model()
def test_GuildTextChannel(mock_fabric):
    guild_text_channel_obj = channels.GuildTextChannel(
        mock_fabric,
        {
            "type": 0,
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
    )

    assert guild_text_channel_obj.type is channels.ChannelType.GUILD_TEXT
    assert guild_text_channel_obj.id == 1234567
    assert guild_text_channel_obj.guild_id == 696969
    assert guild_text_channel_obj.position == 100
    assert guild_text_channel_obj.permission_overwrites == []
    assert guild_text_channel_obj.is_nsfw is True
    assert guild_text_channel_obj.parent_id is None
    assert guild_text_channel_obj.rate_limit_per_user == 420
    assert guild_text_channel_obj.topic == "nsfw stuff"
    assert guild_text_channel_obj.name == "shh!"
    assert not guild_text_channel_obj.is_dm
    guild_text_channel_obj.__repr__()


@pytest.mark.model()
def test_DMChannel(mock_user, mock_fabric):
    dm_channel_obj = channels.DMChannel(
        mock_fabric, {"type": 1, "id": "929292", "last_message_id": "12345", "recipients": [mock_user]}
    )

    assert dm_channel_obj.type is channels.ChannelType.DM
    assert dm_channel_obj.id == 929292
    assert dm_channel_obj.last_message_id == 12345
    assert len(dm_channel_obj.recipients) == 1
    assert dm_channel_obj.is_dm
    mock_fabric.state_registry.parse_user.assert_called_once_with(mock_user)
    dm_channel_obj.__repr__()


@pytest.mark.model()
def test_GuildVoiceChannel(mock_fabric):
    guild_voice_channel_obj = channels.GuildVoiceChannel(
        mock_fabric,
        {
            "type": 2,
            "id": "9292929",
            "guild_id": "929",
            "position": 66,
            "permission_overwrites": [],
            "name": "roy rodgers mc freely",
            "bitrate": 999,
            "user_limit": 0,
            "parent_id": "42",
        },
    )

    assert guild_voice_channel_obj.type is channels.ChannelType.GUILD_VOICE
    assert guild_voice_channel_obj.id == 9292929
    assert guild_voice_channel_obj.guild_id == 929
    assert guild_voice_channel_obj.position == 66
    assert guild_voice_channel_obj.permission_overwrites == []
    assert guild_voice_channel_obj.name == "roy rodgers mc freely"
    assert guild_voice_channel_obj.bitrate == 999
    assert guild_voice_channel_obj.user_limit is None
    assert guild_voice_channel_obj.parent_id == 42
    assert not guild_voice_channel_obj.is_dm
    guild_voice_channel_obj.__repr__()


@pytest.mark.model()
def test_GroupDMChannel(mock_user, mock_fabric):
    group_dm_channel_obj = channels.GroupDMChannel(
        mock_fabric,
        {
            "type": 3,
            "id": "99999999999",
            "last_message_id": None,
            "recipients": [mock_user],
            "icon": "1a2b3c4d",
            "name": "shitposting 101",
            "application_id": "111111",
            "owner_id": "111111",
        },
    )

    assert group_dm_channel_obj.type is channels.ChannelType.GROUP_DM
    assert group_dm_channel_obj.id == 99999999999
    assert group_dm_channel_obj.last_message_id is None
    assert len(group_dm_channel_obj.recipients) == 1
    assert group_dm_channel_obj.icon_hash == "1a2b3c4d"
    assert group_dm_channel_obj.name == "shitposting 101"
    assert group_dm_channel_obj.owner_application_id == 111111
    assert group_dm_channel_obj.owner_id == 111111
    assert group_dm_channel_obj.is_dm
    mock_fabric.state_registry.parse_user.assert_called_once_with(mock_user)
    group_dm_channel_obj.__repr__()


@pytest.mark.model()
def test_GuildCategory(mock_fabric):
    guild_category_obj = channels.GuildCategory(
        mock_fabric,
        {
            "type": 4,
            "id": "123456",
            "position": 69,
            "permission_overwrites": [],
            "name": "dank category",
            "guild_id": "54321",
        },
    )

    assert guild_category_obj.type is channels.ChannelType.GUILD_CATEGORY
    assert guild_category_obj.name == "dank category"
    assert guild_category_obj.position == 69
    assert guild_category_obj.guild_id == 54321
    assert guild_category_obj.id == 123456
    assert guild_category_obj.permission_overwrites == []
    assert not guild_category_obj.is_dm
    guild_category_obj.__repr__()


@pytest.mark.model()
def test_GuildAnnouncementChannel(mock_fabric):
    guild_announcement_channe_obj = channels.GuildAnnouncementChannel(
        mock_fabric,
        {
            "type": 5,
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
    )

    assert guild_announcement_channe_obj.type is channels.ChannelType.GUILD_ANNOUNCEMENT
    assert guild_announcement_channe_obj.id == 4444
    assert guild_announcement_channe_obj.guild_id == 1111
    assert guild_announcement_channe_obj.position == 24
    assert guild_announcement_channe_obj.permission_overwrites == []
    assert guild_announcement_channe_obj.name
    assert guild_announcement_channe_obj.is_nsfw is False
    assert guild_announcement_channe_obj.parent_id == 3232
    assert guild_announcement_channe_obj.topic == "crap and stuff"
    assert guild_announcement_channe_obj.last_message_id is None
    assert not guild_announcement_channe_obj.is_dm
    guild_announcement_channe_obj.__repr__()


@pytest.mark.model()
def test_GuildStoreChannel(mock_fabric):
    guild_store_channel_obj = channels.GuildStoreChannel(
        mock_fabric,
        {
            "type": 6,
            "id": "9876",
            "position": 9,
            "permission_overwrites": [],
            "name": "a",
            "parent_id": "32",
            "guild_id": "7676",
        },
    )

    assert guild_store_channel_obj.type is channels.ChannelType.GUILD_STORE
    assert guild_store_channel_obj.id == 9876
    assert guild_store_channel_obj.guild_id == 7676
    assert guild_store_channel_obj.position == 9
    assert guild_store_channel_obj.permission_overwrites == []
    assert guild_store_channel_obj.name == "a"
    assert guild_store_channel_obj.parent_id == 32
    assert not guild_store_channel_obj.is_dm
    guild_store_channel_obj.__repr__()


@pytest.mark.model()
def test_partial_channel(mock_fabric):
    partial_channel_obj = channels.PartialChannel(
        mock_fabric, {"id": "455344577423428035", "name": "Neko Zone", "type": 2}
    )
    assert partial_channel_obj.id == 455344577423428035
    assert partial_channel_obj.name == "Neko Zone"
    assert partial_channel_obj.type is channels.ChannelType.GUILD_VOICE
    assert partial_channel_obj.is_dm is False
    partial_channel_obj.__repr__()


@pytest.mark.model()
def test_partial_channel_with_unknown_type(mock_fabric):
    partial_channel_obj = channels.PartialChannel(
        mock_fabric, {"id": "115590097100865541", "name": "Neko Chilla", "type": 6969}
    )
    assert partial_channel_obj.id == 115590097100865541
    assert partial_channel_obj.name == "Neko Chilla"
    assert partial_channel_obj.type == 6969
    assert partial_channel_obj.is_dm is None
    partial_channel_obj.__repr__()


@pytest.mark.model
@pytest.mark.parametrize(
    ["type_field", "expected_class"],
    [
        (0, channels.GuildTextChannel),
        (1, channels.DMChannel),
        (2, channels.GuildVoiceChannel),
        (3, channels.GroupDMChannel),
        (4, channels.GuildCategory),
        (5, channels.GuildAnnouncementChannel),
        (6, channels.GuildStoreChannel),
    ],
)
def test_channel_from_dict_success_case(type_field, expected_class):
    args = NotImplemented, {"type": type_field}
    is_dm = expected_class.is_dm
    if not is_dm:
        # noinspection PyTypeChecker
        args[1]["guild_id"] = "1234"

    with _helpers.mock_patch(expected_class.__init__, wraps=expected_class, return_value=None) as m:
        channels.parse_channel(*args)
        m.assert_called_once_with(*args)


@pytest.mark.model
def test_channel_failure_case():
    try:
        channels.parse_channel(mock.MagicMock(), {"type": -999})
        assert False
    except TypeError:
        pass


@pytest.mark.model()
@pytest.mark.parametrize(
    "impl",
    [
        channels.GuildTextChannel,
        channels.GuildVoiceChannel,
        channels.GuildStoreChannel,
        channels.GuildAnnouncementChannel,
        channels.GuildCategory,
    ],
)
def test_channel_guild(impl, mock_fabric, mock_guild):
    obj = impl(
        mock_fabric, {"id": "1", "position": 2, "permission_overwrites": [], "name": "milfchnl", "guild_id": "91827"}
    )
    mock_fabric.state_registry.get_guild_by_id.return_value = mock_guild

    guild_obj = obj.guild
    assert guild_obj is mock_guild

    mock_fabric.state_registry.get_guild_by_id.assert_called_with(91827)


@pytest.mark.model
@pytest.mark.parametrize(
    ["channel_type", "is_dm"],
    [
        [channels.ChannelType.GUILD_TEXT, False],
        [channels.ChannelType.DM, True],
        [channels.ChannelType.GUILD_VOICE, False],
        [channels.ChannelType.GROUP_DM, True],
        [channels.ChannelType.GUILD_CATEGORY, False],
        [channels.ChannelType.GUILD_ANNOUNCEMENT, False],
        [channels.ChannelType.GUILD_STORE, False],
        [6969, False],
    ],
)
def test_is_channel_type_dm(channel_type, is_dm):
    assert channels.is_channel_type_dm(channel_type) is is_dm
    if hasattr(channel_type, "value"):
        assert channels.is_channel_type_dm(channel_type.value) is is_dm
