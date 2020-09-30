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

import aiohttp
import mock
import pytest

from hikari import errors
from hikari.internal import net


@pytest.mark.parametrize(
    ("status_", "expected_error"),
    [
        (http.HTTPStatus.BAD_REQUEST, "BadRequestError"),
        (http.HTTPStatus.UNAUTHORIZED, "UnauthorizedError"),
        (http.HTTPStatus.FORBIDDEN, "ForbiddenError"),
        (http.HTTPStatus.NOT_FOUND, "NotFoundError"),
        (http.HTTPStatus.PAYMENT_REQUIRED, "ClientHTTPResponseError"),
        (http.HTTPStatus.SERVICE_UNAVAILABLE, "InternalServerError"),
        (http.HTTPStatus.PERMANENT_REDIRECT, "HTTPResponseError"),
    ],
)
@pytest.mark.asyncio
async def test_generate_error_response(status_, expected_error):
    class StubResponse:
        real_url = "https://some.url"
        status = status_
        headers = {}

        async def read(self):
            return "some raw body"

        async def json(self):
            return {"message": "raw message", "code": 123}

    with mock.patch.object(errors, expected_error) as error:
        returned = await net.generate_error_response(StubResponse())

    if status_ in (
        http.HTTPStatus.BAD_REQUEST,
        http.HTTPStatus.UNAUTHORIZED,
        http.HTTPStatus.FORBIDDEN,
        http.HTTPStatus.NOT_FOUND,
    ):
        error.assert_called_once_with("https://some.url", {}, "some raw body", "raw message", 123)
    else:
        error.assert_called_once_with("https://some.url", status_, {}, "some raw body")

    assert returned is error()


@pytest.mark.parametrize(
    ("status_", "expected_error"),
    [
        (http.HTTPStatus.BAD_REQUEST, "BadRequestError"),
        (http.HTTPStatus.UNAUTHORIZED, "UnauthorizedError"),
        (http.HTTPStatus.FORBIDDEN, "ForbiddenError"),
        (http.HTTPStatus.NOT_FOUND, "NotFoundError"),
    ],
)
@pytest.mark.asyncio
async def test_generate_error_when_error_with_json(status_, expected_error):
    json_response = aiohttp.ContentTypeError(None, None)

    class StubResponse:
        real_url = "https://some.url"
        status = status_
        headers = {}
        json = mock.AsyncMock(side_effect=json_response)

        async def read(self):
            return "some raw body"

    with mock.patch.object(errors, expected_error) as error:
        returned = await net.generate_error_response(StubResponse())

    error.assert_called_once_with("https://some.url", {}, "some raw body")
    assert returned is error()
