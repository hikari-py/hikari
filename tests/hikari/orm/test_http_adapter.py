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

from hikari.net import http_client
from hikari.orm import fabric
from hikari.orm import http_adapter
from hikari.orm import state_registry

from hikari.orm.models import gateway_bot

from tests.hikari import _helpers


# noinspection PyDunderSlots
@pytest.mark.orm
class TestHTTPAdapter:
    @pytest.fixture()
    def fabric_impl(self):
        fabric_impl = fabric.Fabric()

        http_client_impl = asynctest.MagicMock(spec_set=http_client.HTTPClient)
        state_registry_impl = mock.MagicMock(spec_set=state_registry.IStateRegistry)
        http_adapter_impl = http_adapter.HTTPAdapter(fabric_impl)

        fabric_impl.state_registry = state_registry_impl
        fabric_impl.http_client = http_client_impl
        fabric_impl.http_adapter = http_adapter_impl

        return fabric_impl

    @pytest.mark.asyncio
    async def test_get_gateway(self, fabric_impl):
        # noinspection PyUnresolvedReferences
        fabric_impl.http_client.get_gateway = asynctest.CoroutineMock(return_value="wss://some-site.com")

        for _ in range(15):
            assert await fabric_impl.http_adapter.get_gateway() == "wss://some-site.com"

        fabric_impl.http_client.get_gateway.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_gateway_bot(self, fabric_impl):
        mock_gateway_bot = _helpers.mock_model(gateway_bot.GatewayBot)
        with _helpers.mock_patch(gateway_bot.GatewayBot, return_value=mock_gateway_bot):
            mock_payload = mock.MagicMock(spec_set=dict)
            # noinspection PyUnresolvedReferences
            fabric_impl.http_client.get_gateway_bot = asynctest.CoroutineMock(return_value=mock_payload)

            result = await fabric_impl.http_adapter.get_gateway_bot()

            assert result is mock_gateway_bot
