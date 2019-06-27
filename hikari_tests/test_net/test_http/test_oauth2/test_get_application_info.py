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

import asynctest
import pytest


@pytest.fixture()
def http_client(event_loop):
    from hikari_tests.test_net.test_http import ClientMock

    return ClientMock(token="foobarsecret", loop=event_loop)


@pytest.mark.asyncio
async def test_get_current_application_info_returns_a_dict_that_was_the_response_body(http_client):
    resp = {
        "id": "9182736",
        "name": "hikari",
        "icon": "1a2b3c4d",
        "description": "a sane discord api",
        "rpc_origins": ["http://foo", "http://bar", "http://baz"],
        "bot_public": True,
        "bot_require_code_grant": False,
        "owner": {"username": "nekoka.tt", "discriminator": "1234", "id": "123456789", "avatar": None},
    }
    http_client.request = asynctest.CoroutineMock(return_value=resp)

    info = await http_client.get_current_application_info()
    assert info == resp
