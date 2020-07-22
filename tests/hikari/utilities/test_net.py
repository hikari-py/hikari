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

import http

import pytest

from hikari import errors
from hikari.utilities import net


@pytest.mark.parametrize(
    ("status_", "expected_return"),
    [
        (http.HTTPStatus.BAD_REQUEST, errors.BadRequest),
        (http.HTTPStatus.UNAUTHORIZED, errors.Unauthorized),
        (http.HTTPStatus.FORBIDDEN, errors.Forbidden),
        (http.HTTPStatus.NOT_FOUND, errors.NotFound),
        (http.HTTPStatus.PAYMENT_REQUIRED, errors.ClientHTTPErrorResponse),
        (http.HTTPStatus.SERVICE_UNAVAILABLE, errors.ServerHTTPErrorResponse),
        (http.HTTPStatus.PERMANENT_REDIRECT, errors.HTTPErrorResponse),
    ],
)
@pytest.mark.asyncio
async def test_generate_error_response(status_, expected_return):
    class StubResponse:
        real_url = "https://some.url"
        status = status_
        headers = {}

        async def read(self):
            return "some raw body"

    assert isinstance(await net.generate_error_response(StubResponse()), expected_return)
