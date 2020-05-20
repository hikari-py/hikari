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

from hikari import application
from hikari.models import users
from hikari.net.rest import session
from hikari.net.rest import user
from tests.hikari import _helpers


class TestRESTUserLogic:
    @pytest.fixture()
    def rest_user_logic_impl(self):
        mock_app = mock.MagicMock(application.Application)
        mock_low_level_restful_client = mock.MagicMock(session.RESTSession)

        class RESTUserLogicImpl(user.RESTUserComponent):
            def __init__(self):
                super().__init__(mock_app, mock_low_level_restful_client)

        return RESTUserLogicImpl()

    @pytest.mark.asyncio
    @_helpers.parametrize_valid_id_formats_for_models("user", 123123123, users.User)
    async def test_fetch_user(self, rest_user_logic_impl, user):
        mock_user_payload = {"id": "123", "username": "userName"}
        mock_user_obj = mock.MagicMock(users.User)
        rest_user_logic_impl._session.get_user.return_value = mock_user_payload
        with mock.patch.object(users.User, "deserialize", return_value=mock_user_obj):
            assert await rest_user_logic_impl.fetch_user(user) is mock_user_obj
            rest_user_logic_impl._session.get_user.assert_called_once_with(user_id="123123123")
            users.User.deserialize.assert_called_once_with(mock_user_payload, app=rest_user_logic_impl._app)
