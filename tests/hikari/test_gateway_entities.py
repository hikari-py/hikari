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
import datetime

import mock
import pytest

from hikari import gateway_entities
from hikari import guilds
from hikari.clients import components
from tests.hikari import _helpers


@pytest.fixture()
def mock_components():
    return mock.MagicMock(components.Components)


@pytest.fixture()
def test_session_start_limit_payload():
    return {"total": 1000, "remaining": 991, "reset_after": 14170186}


class TestSessionStartLimit:
    def test_deserialize(self, test_session_start_limit_payload, mock_components):
        session_start_limit_obj = gateway_entities.SessionStartLimit.deserialize(
            test_session_start_limit_payload, components=mock_components
        )
        assert session_start_limit_obj.total == 1000
        assert session_start_limit_obj.remaining == 991
        assert session_start_limit_obj.reset_after == datetime.timedelta(milliseconds=14170186)


class TestGatewayBot:
    @pytest.fixture()
    def test_gateway_bot_payload(self, test_session_start_limit_payload):
        return {"url": "wss://gateway.discord.gg", "shards": 1, "session_start_limit": test_session_start_limit_payload}

    def test_deserialize(self, test_gateway_bot_payload, test_session_start_limit_payload, mock_components):
        mock_session_start_limit = mock.MagicMock(gateway_entities.SessionStartLimit)
        with _helpers.patch_marshal_attr(
            gateway_entities.GatewayBot,
            "session_start_limit",
            deserializer=gateway_entities.SessionStartLimit.deserialize,
            return_value=mock_session_start_limit,
        ) as patched_start_limit_deserializer:
            gateway_bot_obj = gateway_entities.GatewayBot.deserialize(
                test_gateway_bot_payload, components=mock_components
            )
            patched_start_limit_deserializer.assert_called_once_with(
                test_session_start_limit_payload, components=mock_components
            )
        assert gateway_bot_obj.session_start_limit is mock_session_start_limit
        assert gateway_bot_obj.url == "wss://gateway.discord.gg"
        assert gateway_bot_obj.shard_count == 1


class TestGatewayActivity:
    @pytest.fixture()
    def test_gateway_activity_config(self):
        return {"name": "Presence me baby", "url": "http://a-url-name", "type": 1}

    def test_deserialize_full_config(self, test_gateway_activity_config):
        gateway_activity_obj = gateway_entities.Activity.deserialize(test_gateway_activity_config)
        assert gateway_activity_obj.name == "Presence me baby"
        assert gateway_activity_obj.url == "http://a-url-name"
        assert gateway_activity_obj.type is guilds.ActivityType.STREAMING

    def test_deserialize_partial_config(self):
        gateway_activity_obj = gateway_entities.Activity.deserialize({"name": "Presence me baby"})
        assert gateway_activity_obj.name == "Presence me baby"
        assert gateway_activity_obj.url == None
        assert gateway_activity_obj.type is guilds.ActivityType.PLAYING

    def test_serialize_full_activity(self):
        gateway_activity_obj = gateway_entities.Activity(
            name="Presence me baby", url="http://a-url-name", type=guilds.ActivityType.STREAMING
        )
        assert gateway_activity_obj.serialize() == {
            "name": "Presence me baby",
            "url": "http://a-url-name",
            "type": 1,
        }

    def test_serialize_partial_activity(self):
        gateway_activity_obj = gateway_entities.Activity(name="Presence me baby",)
        assert gateway_activity_obj.serialize() == {
            "name": "Presence me baby",
            "type": 0,
        }
