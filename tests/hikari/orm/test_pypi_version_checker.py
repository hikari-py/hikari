#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
import asyncio
from unittest import mock

import pytest

from hikari.orm import pypi_version_checker


@pytest.fixture
def client_session():
    class Response:
        async def json(self):
            return {"info": {"version": "0.0.75"}}

        def __call__(self, *args, **kwargs):
            return self

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class ClientSession:
        def __init__(self):
            self.get = mock.MagicMock(return_value=Response())

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return ClientSession


@mock.patch("hikari._about.__version__", new="0.0.75.dev")
@pytest.mark.asyncio
async def test_check_package_version_logs_if_lower_version(client_session):
    with mock.patch("aiohttp.ClientSession", new=client_session):
        with mock.patch("logging.Logger.warning") as warning:
            await pypi_version_checker.check_package_version()
            warning.assert_called()


@mock.patch("hikari._about.__version__", new="0.0.75")
@pytest.mark.asyncio
async def test_check_package_version_doesnt_log_if_equal_version(client_session):
    with mock.patch("aiohttp.ClientSession", new=client_session):
        with mock.patch("logging.Logger.warning") as warning:
            await pypi_version_checker.check_package_version()
            warning.assert_not_called()


@mock.patch("hikari._about.__version__", new="0.0.76.dev")
@pytest.mark.asyncio
async def test_check_package_version_doesnt_log_if_higher_version(client_session):
    with mock.patch("aiohttp.ClientSession", new=client_session):
        with mock.patch("logging.Logger.warning") as warning:
            await pypi_version_checker.check_package_version()
            warning.assert_not_called()
