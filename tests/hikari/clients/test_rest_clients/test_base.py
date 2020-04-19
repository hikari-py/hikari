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

from hikari.clients.rest_clients import base
from hikari.net import rest_sessions


class TestBaseRESTComponent:
    @pytest.fixture()
    def low_level_rest_impl(self) -> rest_sessions.LowLevelRestfulClient:
        return mock.MagicMock(rest_sessions.LowLevelRestfulClient)

    @pytest.fixture()
    def rest_clients_impl(self, low_level_rest_impl) -> base.BaseRESTComponent:
        class RestClientImpl(base.BaseRESTComponent):
            def __init__(self):
                super().__init__(low_level_rest_impl)

        return RestClientImpl()

    @pytest.mark.asyncio
    async def test___aenter___and___aexit__(self, rest_clients_impl):
        rest_clients_impl.close = mock.AsyncMock()
        async with rest_clients_impl as client:
            assert client is rest_clients_impl
        rest_clients_impl.close.assert_called_once_with()
