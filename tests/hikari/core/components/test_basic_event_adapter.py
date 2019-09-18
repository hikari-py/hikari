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

import asynctest
import pytest

from hikari.core.components import basic_event_adapter
from hikari.core.net import gateway as _gateway


@pytest.mark.asyncio
async def test_unrecognised_events_only_get_warned_once():
    adapter = basic_event_adapter.BasicEventAdapter(asynctest.MagicMock(), asynctest.MagicMock())
    adapter.logger.warning = mock.MagicMock()

    await adapter.handle_unrecognised_event(asynctest.MagicMock(), "no_idea", {})
    assert adapter.logger.warning.call_args[0][1] == "no_idea"

    adapter.logger.warning.reset_mock()

    await adapter.handle_unrecognised_event(asynctest.MagicMock(), "no_idea", {})
    assert adapter.logger.warning.call_count == 0


@pytest.fixture
def gateway():
    return mock.MagicMock(spec_set=_gateway.GatewayClient)


@pytest.fixture
def state_registry():
    return mock.MagicMock()


@pytest.fixture
def dispatch():
    return mock.MagicMock()


@pytest.fixture
def event_adapter(state_registry, dispatch):
    return basic_event_adapter.BasicEventAdapter(state_registry, dispatch)


@pytest.mark.asyncio
async def test_handle_disconnect_signature_invoked_correctly(event_adapter, dispatch, gateway):
    await event_adapter.handle_disconnect(gateway, {"code": 123, "reason": "server on fire"})
    dispatch.assert_called_with(
        basic_event_adapter.BasicEventNames.DISCONNECT,
        gateway,
        123,
        "server on fire"
    )
