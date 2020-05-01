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

import mock
import pytest

from hikari import gateway_entities
from hikari.clients import components
from hikari.clients.rest import gateway
from hikari.net import rest


class TestRESTReactionLogic:
    @pytest.fixture()
    def rest_gateway_logic_impl(self):
        mock_components = mock.MagicMock(components.Components)
        mock_low_level_restful_client = mock.MagicMock(rest.REST)

        class RESTGatewayLogicImpl(gateway.RESTGatewayComponent):
            def __init__(self):
                super().__init__(mock_components, mock_low_level_restful_client)

        return RESTGatewayLogicImpl()

    @pytest.mark.asyncio
    async def test_fetch_gateway_url(self, rest_gateway_logic_impl):
        mock_url = "wss://gateway.discord.gg/"
        rest_gateway_logic_impl._session.get_gateway.return_value = mock_url
        assert await rest_gateway_logic_impl.fetch_gateway_url() == mock_url
        rest_gateway_logic_impl._session.get_gateway.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_gateway_bot(self, rest_gateway_logic_impl):
        mock_payload = {"url": "wss://gateway.discord.gg/", "shards": 9, "session_start_limit": {}}
        mock_gateway_bot_obj = mock.MagicMock(gateway_entities.GatewayBot)
        rest_gateway_logic_impl._session.get_gateway_bot.return_value = mock_payload
        with mock.patch.object(gateway_entities.GatewayBot, "deserialize", return_value=mock_gateway_bot_obj):
            assert await rest_gateway_logic_impl.fetch_gateway_bot() is mock_gateway_bot_obj
            rest_gateway_logic_impl._session.get_gateway_bot.assert_called_once()
            gateway_entities.GatewayBot.deserialize.assert_called_once_with(
                mock_payload, components=rest_gateway_logic_impl._components
            )
