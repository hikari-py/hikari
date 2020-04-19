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

from hikari import oauth2
from hikari.clients.rest_clients import oauth2_component
from hikari.net import rest_sessions


class TestRESTReactionLogic:
    @pytest.fixture()
    def rest_oauth2_logic_impl(self):
        mock_low_level_restful_client = mock.MagicMock(rest_sessions.LowLevelRestfulClient)

        class RESTOauth2LogicImpl(oauth2_component.RESTOauth2Component):
            def __init__(self):
                super().__init__(mock_low_level_restful_client)

        return RESTOauth2LogicImpl()

    @pytest.mark.asyncio
    async def test_fetch_my_application_info(self, rest_oauth2_logic_impl):
        mock_application_payload = {"id": "2929292", "name": "blah blah", "description": "an app"}
        mock_application_obj = mock.MagicMock(oauth2.Application)
        rest_oauth2_logic_impl._session.get_current_application_info.return_value = mock_application_payload
        with mock.patch.object(oauth2.Application, "deserialize", return_value=mock_application_obj):
            assert await rest_oauth2_logic_impl.fetch_my_application_info() is mock_application_obj
            rest_oauth2_logic_impl._session.get_current_application_info.assert_called_once_with()
            oauth2.Application.deserialize.assert_called_once_with(mock_application_payload)
