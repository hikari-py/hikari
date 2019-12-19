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

import asyncmock as mock
import pytest

from hikari.internal_utilities import unspecified
from hikari.net import http_api
from hikari.orm import fabric
from hikari.orm import http_adapter_impl as _http_adapter_impl
from hikari.orm import state_registry
from hikari.orm.models import audit_logs
from hikari.orm.models import channels
from hikari.orm.models import gateway_bot
from hikari.orm.models import guilds
from hikari.orm.models import users
from tests.hikari import _helpers


# noinspection PyDunderSlots
@pytest.mark.orm
class TestHTTPAdapterImpl:
    @pytest.fixture()
    def fabric_impl(self):
        fabric_impl = fabric.Fabric()

        http_client_impl = mock.MagicMock(spec_set=http_api.HTTPAPI)
        state_registry_impl = mock.MagicMock(spec_set=state_registry.IStateRegistry)
        http_adapter_impl = _http_adapter_impl.HTTPAdapterImpl(fabric_impl)

        fabric_impl.state_registry = state_registry_impl
        fabric_impl.http_api = http_client_impl
        fabric_impl.http_adapter = http_adapter_impl

        return fabric_impl

    @pytest.mark.asyncio
    async def test_gateway_url(self, fabric_impl):
        fabric_impl.http_api.get_gateway = mock.AsyncMock(return_value="wss://some-site.com")

        for _ in range(15):
            assert await fabric_impl.http_adapter.gateway_url == "wss://some-site.com"

        fabric_impl.http_api.get_gateway.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_gateway_bot(self, fabric_impl):
        mock_model = _helpers.mock_model(gateway_bot.GatewayBot)
        mock_payload = mock.MagicMock(spec_set=dict)
        fabric_impl.http_api.get_gateway_bot = mock.AsyncMock(return_value=mock_payload)
        fabric_impl.state_registry.parse_gateway_bot = mock.MagicMock(return_value=mock_model)

        result = await fabric_impl.http_adapter.fetch_gateway_bot()

        assert result is mock_model
        fabric_impl.http_api.get_gateway_bot.assert_called_once_with()
        fabric_impl.state_registry.parse_gateway_bot.assert_called_once_with(mock_payload)

    @pytest.mark.asyncio
    @_helpers.parameterize_valid_id_formats_for_models("guild", 112233, guilds.Guild)
    async def test_fetch_audit_log_with_default_args(self, fabric_impl, guild):
        mock_audit_log = _helpers.mock_model(audit_logs.AuditLog)
        mock_payload = mock.MagicMock(spec_set=dict)

        fabric_impl.http_api.get_guild_audit_log = mock.AsyncMock(return_value=mock_payload)
        fabric_impl.state_registry.parse_audit_log = mock.MagicMock(return_value=mock_audit_log)

        result = await fabric_impl.http_adapter.fetch_audit_log(guild)

        fabric_impl.http_api.get_guild_audit_log.assert_called_once_with(
            guild_id="112233",
            user_id=unspecified.UNSPECIFIED,
            action_type=unspecified.UNSPECIFIED,
            limit=unspecified.UNSPECIFIED,
        )

        fabric_impl.state_registry.parse_audit_log.assert_called_once_with(mock_payload)

        assert result is mock_audit_log

    @pytest.mark.asyncio
    @_helpers.parameterize_valid_id_formats_for_models("guild", 112233, guilds.Guild)
    @_helpers.parameterize_valid_id_formats_for_models("user", 334455, users.User, users.OAuth2User)
    async def test_fetch_audit_log_with_optional_args_specified(self, fabric_impl, guild, user):
        mock_audit_log = _helpers.mock_model(audit_logs.AuditLog)
        mock_payload = mock.MagicMock(spec_set=dict)

        fabric_impl.http_api.get_guild_audit_log = mock.AsyncMock(return_value=mock_payload)
        fabric_impl.state_registry.parse_audit_log = mock.MagicMock(return_value=mock_audit_log)

        result = await fabric_impl.http_adapter.fetch_audit_log(
            guild, user=user, action_type=audit_logs.AuditLogEvent.CHANNEL_OVERWRITE_CREATE, limit=69,
        )

        fabric_impl.http_api.get_guild_audit_log.assert_called_once_with(
            guild_id="112233",
            user_id="334455",
            action_type=int(audit_logs.AuditLogEvent.CHANNEL_OVERWRITE_CREATE),
            limit=69,
        )

        fabric_impl.state_registry.parse_audit_log.assert_called_once_with(mock_payload)

        assert result is mock_audit_log

    @_helpers.todo_implement
    @pytest.mark.asyncio
    @_helpers.parameterize_valid_id_formats_for_models("channel", 112233, channels.Channel)
    async def test_fetch_channel(self, fabric_impl, channel):
        mock_channel = _helpers.mock_model(channels.Channel)
        mock_payload = mock.MagicMock(spec_set=dict)

        fabric_impl.http_api.get_channel = mock.AsyncMock(return_value=mock_payload)
        fabric_impl.state_registry.parse_channel = mock.MagicMock(return_value=mock_channel)

        result = await fabric_impl.http_adapter.fetch_channel(channel)

        fabric_impl.http_api.get_guild_audit_log.assert_called_once_with(channel_id="112233")
        fabric_impl.state_registry.parse_channel.assert_called_once_with(mock_payload)
        assert result is mock_channel
