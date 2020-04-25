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
# along ith Hikari. If not, see <https://www.gnu.org/licenses/>.
import datetime
import contextlib

import mock
import pytest

from hikari import users
from hikari import emojis
from hikari import unset
from hikari import guilds as _guilds
from hikari.events import guilds
from hikari.internal import conversions
from tests.hikari import _helpers


@pytest.fixture()
def test_user_payload():
    return {"id": "2929292", "username": "agent 69", "discriminator": "4444", "avatar": "9292929292929292"}


@pytest.fixture()
def test_guild_payload():
    return {"id": "40404040", "name": "electric guild boogaloo"}


@pytest.fixture()
def test_member_payload(test_user_payload):
    return {
        "user": test_user_payload,
        "nick": "Agent 42",
        "roles": [],
        "joined_at": "2015-04-26T06:26:56.936000+00:00",
        "premium_since": "2019-05-17T06:26:56.936000+00:00",
        "deaf": True,
        "mute": False,
    }


# Doesn't declare any new fields.
class TestGuildCreateEvent:
    ...


# Doesn't declare any new fields.
class TestGuildUpdateEvent:
    ...


# Doesn't declare any new fields.
class GuildLeaveEvent:
    ...


# Doesn't declare any new fields.
class GuildUnavailableEvent:
    ...


class TestBaseGuildBanEvent:
    @pytest.fixture()
    def test_guild_ban_payload(self, test_user_payload):
        return {"user": test_user_payload, "guild_id": "5959"}

    def test_deserialize(self, test_guild_ban_payload, test_user_payload):
        mock_user = mock.MagicMock(users.User)
        with _helpers.patch_marshal_attr(
            guilds.BaseGuildBanEvent, "user", deserializer=users.User.deserialize, return_value=mock_user
        ) as patched_user_deserializer:
            base_guild_ban_object = guilds.BaseGuildBanEvent.deserialize(test_guild_ban_payload)
            patched_user_deserializer.assert_called_once_with(test_user_payload)
        assert base_guild_ban_object.user is mock_user
        assert base_guild_ban_object.guild_id == 5959


# Doesn't declare any new fields.
class TestGuildBanAddEvent:
    ...


# Doesn't declare any new fields.
class TestGuildBanRemoveEvent:
    ...


class TestGuildEmojisUpdateEvent:
    @pytest.fixture()
    def test_emoji_payload(self):
        return {"id": "4242", "name": "blahblah", "animated": True}

    @pytest.fixture()
    def test_guild_emojis_update_payload(self, test_emoji_payload):
        return {"emojis": [test_emoji_payload], "guild_id": "696969"}

    def test_deserialize(self, test_guild_emojis_update_payload, test_emoji_payload):
        mock_emoji = _helpers.mock_model(emojis.GuildEmoji, id=240)
        with mock.patch.object(emojis.GuildEmoji, "deserialize", return_value=mock_emoji):
            guild_emojis_update_obj = guilds.GuildEmojisUpdateEvent.deserialize(test_guild_emojis_update_payload)
            emojis.GuildEmoji.deserialize.assert_called_once_with(test_emoji_payload)
        assert guild_emojis_update_obj.emojis == {mock_emoji.id: mock_emoji}
        assert guild_emojis_update_obj.guild_id == 696969


class TestGuildIntegrationsUpdateEvent:
    def test_deserialize(self):
        assert guilds.GuildIntegrationsUpdateEvent.deserialize({"guild_id": "1234"}).guild_id == 1234


class TestGuildMemberAddEvent:
    @pytest.fixture()
    def test_guild_member_add_payload(self, test_member_payload):
        return {**test_member_payload, "guild_id": "292929"}

    def test_deserialize(self, test_guild_member_add_payload):
        guild_member_add_obj = guilds.GuildMemberAddEvent.deserialize(test_guild_member_add_payload)
        assert guild_member_add_obj.guild_id == 292929


class TestGuildMemberRemoveEvent:
    @pytest.fixture()
    def test_guild_member_remove_payload(self, test_user_payload):
        return {"guild_id": "9494949", "user": test_user_payload}

    def test_deserialize(self, test_guild_member_remove_payload, test_user_payload):
        mock_user = mock.MagicMock(users.User)
        with _helpers.patch_marshal_attr(
            guilds.GuildMemberRemoveEvent, "user", deserializer=users.User.deserialize, return_value=mock_user
        ) as patched_user_deseializer:
            guild_member_remove_payload = guilds.GuildMemberRemoveEvent.deserialize(test_guild_member_remove_payload)
            patched_user_deseializer.assert_called_once_with(test_user_payload)
        assert guild_member_remove_payload.guild_id == 9494949
        assert guild_member_remove_payload.user is mock_user


class TestGuildMemberUpdateEvent:
    @pytest.fixture()
    def guild_member_update_payload(self, test_user_payload):
        return {
            "guild_id": "292929",
            "roles": ["213", "412"],
            "user": test_user_payload,
            "nick": "konnichiwa",
            "premium_since": "2019-05-17T06:26:56.936000+00:00",
        }

    def test_deserialize(self, guild_member_update_payload, test_user_payload):
        mock_user = mock.MagicMock(users.User)
        mock_premium_since = mock.MagicMock(datetime.datetime)
        stack = contextlib.ExitStack()
        patched_user_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                guilds.GuildMemberUpdateEvent, "user", deserializer=users.User.deserialize, return_value=mock_user
            )
        )
        patched_premium_since_deserializer = stack.enter_context(
            _helpers.patch_marshal_attr(
                guilds.GuildMemberUpdateEvent,
                "premium_since",
                deserializer=conversions.parse_iso_8601_ts,
                return_value=mock_premium_since,
            )
        )
        with stack:
            guild_member_update_obj = guilds.GuildMemberUpdateEvent.deserialize(guild_member_update_payload)
            patched_premium_since_deserializer.assert_called_once_with("2019-05-17T06:26:56.936000+00:00")
            patched_user_deserializer.assert_called_once_with(test_user_payload)
        assert guild_member_update_obj.guild_id == 292929
        assert guild_member_update_obj.role_ids == [213, 412]
        assert guild_member_update_obj.user is mock_user
        assert guild_member_update_obj.nickname == "konnichiwa"
        assert guild_member_update_obj.premium_since is mock_premium_since

    def test_partial_deserializer(self, guild_member_update_payload):
        del guild_member_update_payload["nick"]
        del guild_member_update_payload["premium_since"]
        with _helpers.patch_marshal_attr(guilds.GuildMemberUpdateEvent, "user", deserializer=users.User.deserialize):
            guild_member_update_obj = guilds.GuildMemberUpdateEvent.deserialize(guild_member_update_payload)
        assert guild_member_update_obj.nickname is unset.UNSET
        assert guild_member_update_obj.premium_since is unset.UNSET


@pytest.fixture()
def test_guild_role_create_update_payload(test_guild_payload):
    return {"guild_id": "69240", "role": test_guild_payload}


class TestGuildRoleCreateEvent:
    def test_deserialize(self, test_guild_role_create_update_payload, test_guild_payload):
        mock_role = mock.MagicMock(_guilds.GuildRole)
        with _helpers.patch_marshal_attr(
            guilds.GuildRoleCreateEvent, "role", deserializer=_guilds.GuildRole.deserialize, return_value=mock_role
        ) as patched_role_deserializer:
            guild_role_create_obj = guilds.GuildRoleCreateEvent.deserialize(test_guild_role_create_update_payload)
            patched_role_deserializer.assert_called_once_with(test_guild_payload)
        assert guild_role_create_obj.role is mock_role
        assert guild_role_create_obj.guild_id == 69240


class TestGuildRoleUpdateEvent:
    @pytest.fixture()
    def test_guild_role_create_fixture(self, test_guild_payload):
        return {"guild_id": "69240", "role": test_guild_payload}

    def test_deserialize(self, test_guild_role_create_update_payload, test_guild_payload):
        mock_role = mock.MagicMock(_guilds.GuildRole)
        with _helpers.patch_marshal_attr(
            guilds.GuildRoleUpdateEvent, "role", deserializer=_guilds.GuildRole.deserialize, return_value=mock_role
        ) as patched_role_deserializer:
            guild_role_create_obj = guilds.GuildRoleUpdateEvent.deserialize(test_guild_role_create_update_payload)
            patched_role_deserializer.assert_called_once_with(test_guild_payload)
        assert guild_role_create_obj.role is mock_role
        assert guild_role_create_obj.guild_id == 69240


class TestGuildRoleDeleteEvent:
    @pytest.fixture()
    def test_guild_role_delete_payload(self):
        return {"guild_id": "424242", "role_id": "94595959"}

    def test_deserialize(self, test_guild_role_delete_payload):
        guild_role_delete_payload = guilds.GuildRoleDeleteEvent.deserialize(test_guild_role_delete_payload)
        assert guild_role_delete_payload.guild_id == 424242
        assert guild_role_delete_payload.role_id == 94595959


# Doesn't declare any new fields.
class TestPresenceUpdateEvent:
    ...
