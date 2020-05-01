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
import contextlib

import mock
import pytest

from hikari import guilds
from hikari import users
from hikari.events import other
from tests.hikari import _helpers


# Synthetic event, is not deserialized
class TestConnectedEvent:
    ...


# Synthetic event, is not deserialized
class TestDisconnectedEvent:
    ...


# Synthetic event, is not deserialized
class TestReconnectedEvent:
    ...


# Synthetic event, is not deserialized
class TestStartedEvent:
    ...


# Synthetic event, is not deserialized
class TestStoppingEvent:
    ...


# Synthetic event, is not deserialized
class TestStoppedEvent:
    ...


class TestReadyEvent:
    @pytest.fixture()
    def test_guild_payload(self):
        return {"id": "40404040", "name": "electric guild boogaloo"}

    @pytest.fixture()
    def test_user_payload(self):
        return {"id": "2929292", "username": "agent 69", "discriminator": "4444", "avatar": "9292929292929292"}

    @pytest.fixture()
    def test_read_event_payload(self, test_guild_payload, test_user_payload):
        return {
            "v": 69420,
            "user": test_user_payload,
            "private_channels": [],
            "guilds": [test_guild_payload],
            "session_id": "osdkoiiodsaooeiwio9",
            "shard": [42, 80],
        }

    def test_deserialize(self, test_read_event_payload, test_guild_payload, test_user_payload):
        mock_guild = mock.MagicMock(guilds.Guild, id=40404040)
        mock_user = mock.MagicMock(users.MyUser)
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(guilds.UnavailableGuild, "deserialize", return_value=mock_guild))
        patched_user_deserialize = stack.enter_context(
            _helpers.patch_marshal_attr(
                other.ReadyEvent, "my_user", deserializer=users.MyUser.deserialize, return_value=mock_user
            )
        )
        with stack:
            ready_obj = other.ReadyEvent.deserialize(test_read_event_payload)
            patched_user_deserialize.assert_called_once_with(test_user_payload)
            guilds.UnavailableGuild.deserialize.assert_called_once_with(test_guild_payload)
        assert ready_obj.gateway_version == 69420
        assert ready_obj.my_user is mock_user
        assert ready_obj.unavailable_guilds == {40404040: mock_guild}
        assert ready_obj.session_id == "osdkoiiodsaooeiwio9"
        assert ready_obj._shard_information == (42, 80)

    @pytest.fixture()
    def mock_ready_event_obj(self):
        return other.ReadyEvent(
            gateway_version=None, my_user=None, unavailable_guilds=None, session_id=None, shard_information=(42, 80)
        )

    def test_shard_id_when_information_set(self, mock_ready_event_obj):
        assert mock_ready_event_obj.shard_id == 42

    def test_shard_count_when_information_set(self, mock_ready_event_obj):
        assert mock_ready_event_obj.shard_count == 80

    def test_shard_id_when_information_not_set(self, mock_ready_event_obj):
        mock_ready_event_obj._shard_information = None
        assert mock_ready_event_obj.shard_id is None

    def test_shard_count_when_information_not_set(self, mock_ready_event_obj):
        mock_ready_event_obj._shard_information = None
        assert mock_ready_event_obj.shard_count is None


# Synthetic event, is not deserialized
class TestResumedEvent:
    ...


# Doesn't declare any new fields.
class TestUserUpdateEvent:
    ...
