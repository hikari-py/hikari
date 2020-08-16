# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import http

import pytest

from hikari import errors
from hikari.utilities import net


@pytest.mark.parametrize(
    ("status_", "expected_return"),
    [
        (http.HTTPStatus.BAD_REQUEST, errors.BadRequestError),
        (http.HTTPStatus.UNAUTHORIZED, errors.UnauthorizedError),
        (http.HTTPStatus.FORBIDDEN, errors.ForbiddenError),
        (http.HTTPStatus.NOT_FOUND, errors.NotFoundError),
        (http.HTTPStatus.PAYMENT_REQUIRED, errors.ClientHTTPResponseError),
        (http.HTTPStatus.SERVICE_UNAVAILABLE, errors.InternalServerError),
        (http.HTTPStatus.PERMANENT_REDIRECT, errors.HTTPResponseError),
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
