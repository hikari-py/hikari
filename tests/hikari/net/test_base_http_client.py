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
import logging
import cymock as mock

import pytest

from hikari.net import base_http_client


@pytest.mark.asyncio
async def test_http_client___aenter___and___aexit__():
    class HTTPClientImpl(base_http_client.BaseHTTPClient):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.close = mock.AsyncMock()

    inst = HTTPClientImpl()

    async with inst as client:
        assert client is inst

    inst.close.assert_called_once_with()


@pytest.mark.asyncio
async def test_http_client_close_calls_client_session_close():
    class HTTPClientImpl(base_http_client.BaseHTTPClient):
        def __init__(self, *args, **kwargs):
            self.client_session = mock.MagicMock()
            self.client_session.close = mock.AsyncMock()
            self.logger = logging.getLogger(__name__)

    inst = HTTPClientImpl()

    await inst.close()

    inst.client_session.close.assert_called_with()
