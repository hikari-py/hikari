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

import cymock as mock
import pytest

from hikari.core import gateway_bot
from tests.hikari import _helpers


@pytest.fixture()
def test_session_start_limit_payload():
    return {"total": 1000, "remaining": 991, "reset_after": 14170186}


class TestSessionStartLimit:
    def test_deserialize(self, test_session_start_limit_payload):
        session_start_limit_obj = gateway_bot.SessionStartLimit.deserialize(test_session_start_limit_payload)
        assert session_start_limit_obj.total == 1000
        assert session_start_limit_obj.remaining == 991
        assert session_start_limit_obj.reset_after == datetime.timedelta(milliseconds=14170186)


class TestGatewayBot:
    @pytest.fixture()
    def test_gateway_bot_payload(self, test_session_start_limit_payload):
        return {"url": "wss://gateway.discord.gg", "shards": 1, "session_start_limit": test_session_start_limit_payload}

    def test_deserialize(self, test_gateway_bot_payload, test_session_start_limit_payload):
        mock_session_start_limit = mock.MagicMock(gateway_bot.SessionStartLimit)
        with _helpers.patch_marshal_attr(
            gateway_bot.GatewayBot,
            "session_start_limit",
            deserializer=gateway_bot.SessionStartLimit.deserialize,
            return_value=mock_session_start_limit,
        ) as patched_start_limit_deserializer:
            gateway_bot_obj = gateway_bot.GatewayBot.deserialize(test_gateway_bot_payload)
            patched_start_limit_deserializer.assert_called_once_with(test_session_start_limit_payload)
        assert gateway_bot_obj.session_start_limit is mock_session_start_limit
        assert gateway_bot_obj.url == "wss://gateway.discord.gg"
        assert gateway_bot_obj.shard_count == 1
