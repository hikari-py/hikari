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
import datetime
from unittest import mock

import pytest

from hikari.orm.models import gateway_bot


@pytest.fixture()
def session_start_payload():
    return {"total": 1000, "remaining": 999, "reset_after": 14400000}


@pytest.fixture()
def gateway_bot_payload(session_start_payload):
    return {"url": "wss://gateway.discord.gg/", "shards": 9, "session_start_limit": session_start_payload}


@pytest.mark.model
def test_GatewayBot(gateway_bot_payload):
    gateway_bot_obj = gateway_bot.GatewayBot(gateway_bot_payload)
    assert gateway_bot_obj.url == "wss://gateway.discord.gg/"
    assert gateway_bot_obj.shards == 9
    assert isinstance(gateway_bot_obj.session_start_limit, gateway_bot.SessionStartLimit)


@pytest.mark.model
def test_SessionStartLimit(session_start_payload):
    current_ts = 1573999956
    expected_reset_date = datetime.datetime.utcfromtimestamp(current_ts + 14400)

    # We cant mock datetime directly as it is a C type by the looks... however... we can replace
    # the reference with a fake class instead.
    datetime_mock = mock.MagicMock()
    datetime_mock.now = mock.MagicMock(return_value=datetime.datetime.utcfromtimestamp(current_ts))
    with mock.patch("datetime.datetime", new=datetime_mock):
        session_start_limit_obj = gateway_bot.SessionStartLimit(session_start_payload)

    assert session_start_limit_obj.total == 1000
    assert session_start_limit_obj.remaining == 999
    assert session_start_limit_obj.reset_at == expected_reset_date
    assert session_start_limit_obj.used == 1
