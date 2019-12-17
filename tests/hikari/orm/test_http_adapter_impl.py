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

import asynctest
import pytest

from hikari.internal_utilities import unspecified
from hikari.net import http_api
from hikari.orm import fabric
from hikari.orm import http_adapter_impl as _http_adapter_impl
from hikari.orm import state_registry
from hikari.orm.models import audit_logs

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

        http_client_impl = asynctest.MagicMock(spec_set=http_api.HTTPAPI)
        state_registry_impl = mock.MagicMock(spec_set=state_registry.IStateRegistry)
        http_adapter_impl = _http_adapter_impl.HTTPAdapterImpl(fabric_impl)

        fabric_impl.state_registry = state_registry_impl
        fabric_impl.http_api = http_client_impl
        fabric_impl.http_adapter = http_adapter_impl

        return fabric_impl

    @pytest.mark.asyncio
    async def test_gateway_url(self, fabric_impl):
        fabric_impl.http_api.get_gateway = asynctest.CoroutineMock(
            return_value="wss://some-site.com", spec_set=fabric_impl.http_api.get_gateway
        )

        for _ in range(15):
            assert await fabric_impl.http_adapter.gateway_url == "wss://some-site.com"

        fabric_impl.http_api.get_gateway.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_fetch_gateway_bot(self, fabric_impl):
        mock_gateway_bot = _helpers.mock_model(gateway_bot.GatewayBot)
        with _helpers.mock_patch(gateway_bot.GatewayBot, return_value=mock_gateway_bot):
            mock_payload = mock.MagicMock(spec_set=dict)
            fabric_impl.http_api.get_gateway_bot = asynctest.CoroutineMock(
                return_value=mock_payload, spec_set=fabric_impl.http_api.get_gateway_bot
            )

            result = await fabric_impl.http_adapter.fetch_gateway_bot()

            fabric_impl.http_api.get_gateway_bot.assert_awaited_once_with()
            assert result is mock_gateway_bot

    @pytest.mark.asyncio
    @_helpers.parameterize_valid_id_formats_for_models("guild", 112233, guilds.Guild)
    async def test_fetch_audit_log_with_default_args(self, fabric_impl, guild):
        mock_audit_log = _helpers.mock_model(audit_logs.AuditLog)
        with _helpers.mock_patch(audit_logs.AuditLog, return_value=mock_audit_log):
            mock_payload = mock.MagicMock(spec_set=dict)
            fabric_impl.http_api.get_guild_audit_log = asynctest.CoroutineMock(
                return_value=mock_payload, spec_set=fabric_impl.http_api.get_guild_audit_log
            )

            result = await fabric_impl.http_adapter.fetch_audit_log(guild)

            fabric_impl.http_api.get_guild_audit_log.assert_awaited_once_with(
                guild_id="112233",
                user_id=unspecified.UNSPECIFIED,
                action_type=unspecified.UNSPECIFIED,
                limit=unspecified.UNSPECIFIED,
            )
            assert result is mock_audit_log

    @pytest.mark.asyncio
    @_helpers.parameterize_valid_id_formats_for_models("guild", 112233, guilds.Guild)
    @_helpers.parameterize_valid_id_formats_for_models("user", 334455, users.User, users.OAuth2User)
    async def test_fetch_audit_log_with_optional_args_specified(self, fabric_impl, guild, user):
        mock_audit_log = _helpers.mock_model(audit_logs.AuditLog)
        with _helpers.mock_patch(audit_logs.AuditLog, return_value=mock_audit_log):
            mock_payload = mock.MagicMock(spec_set=dict)
            fabric_impl.http_api.get_guild_audit_log = asynctest.CoroutineMock(
                return_value=mock_payload, spec_set=fabric_impl.http_api.get_guild_audit_log
            )

            result = await fabric_impl.http_adapter.fetch_audit_log(
                guild, user=user, action_type=audit_logs.AuditLogEvent.CHANNEL_OVERWRITE_CREATE, limit=69,
            )

            fabric_impl.http_api.get_guild_audit_log.assert_awaited_once_with(
                guild_id="112233",
                user_id="334455",
                action_type=int(audit_logs.AuditLogEvent.CHANNEL_OVERWRITE_CREATE),
                limit=69,
            )
            assert result is mock_audit_log
