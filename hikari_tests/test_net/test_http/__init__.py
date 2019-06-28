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

from hikari.net.http import client


class ClientMock(client.HTTPClient):
    """
    Useful for HTTP client calls that need to mock the HTTP connection quickly in a fixture.

    .. code-block::
        @pytest.fixture()
        async def http_client(event_loop):
            from hikari_tests.test_net.test_http import ClientMock
            return ClientMock(token="foobarsecret", loop=event_loop)

        @pytest.mark.asyncio
        async def test_that_something_does_a_thing(http_client):
            http_client.request = asynctest.CoroutineMock(return_value=69)
            assert await http_client.something() == 69

    """

    def __init__(self, *args, **kwargs):
        with asynctest.patch("aiohttp.ClientSession", new=asynctest.MagicMock()):
            super().__init__(*args, **kwargs)

    async def request(self, method, path, params=None, **kwargs):
        pass
