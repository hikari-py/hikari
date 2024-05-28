# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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
            return '{"message": "raw message", "code": 123}'

    with mock.patch.object(errors, expected_error) as error:
        returned = await net.generate_error_response(StubResponse())

    if status_ in (
        http.HTTPStatus.BAD_REQUEST,
        http.HTTPStatus.UNAUTHORIZED,
        http.HTTPStatus.FORBIDDEN,
        http.HTTPStatus.NOT_FOUND,
    ):
        error.assert_called_once_with(
            "https://some.url", {}, '{"message": "raw message", "code": 123}', "raw message", 123
        )
    else:
        error.assert_called_once_with("https://some.url", status_, {}, '{"message": "raw message", "code": 123}')

    assert returned is error()


@pytest.mark.parametrize(
    ("status_", "expected_error"),
    [
        # The following internal server non-conforming status codes are used by cloudflare.
        # Source I made it up...
        # jk https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
        (520, "InternalServerError"),
        (521, "InternalServerError"),
        (522, "InternalServerError"),
        (523, "InternalServerError"),
        (524, "InternalServerError"),
        (525, "InternalServerError"),
        (526, "InternalServerError"),
        (527, "InternalServerError"),
        (530, "InternalServerError"),
        # These non-conforming bad requests status codes are sent by NGINX.
        # Same source as cloudflare status codes.
        (494, "ClientHTTPResponseError"),
        (495, "ClientHTTPResponseError"),
        (496, "ClientHTTPResponseError"),
        (497, "ClientHTTPResponseError"),
        # This non-conforming status code is made up.
        (694, "HTTPResponseError"),
    ],
)
@pytest.mark.asyncio
async def test_generate_error_response_with_non_conforming_status_code(status_, expected_error):
    class StubResponse:
        real_url = "https://some.url"
        status = status_
        headers = {}

        async def read(self):
            return '{"message": "raw message", "code": 123}'

    with mock.patch.object(errors, expected_error) as error:
        returned = await net.generate_error_response(StubResponse())

    error.assert_called_once_with("https://some.url", status_, {}, '{"message": "raw message", "code": 123}')

    assert returned is error()


@pytest.mark.parametrize(
    ("status_", "expected_error"),
    [
        (http.HTTPStatus.UNAUTHORIZED, "UnauthorizedError"),
        (http.HTTPStatus.FORBIDDEN, "ForbiddenError"),
        (http.HTTPStatus.NOT_FOUND, "NotFoundError"),
    ],
)
@pytest.mark.asyncio
async def test_generate_error_when_error_without_json(status_, expected_error):
    class StubResponse:
        real_url = "https://some.url"
        status = status_
        headers = {}

        async def read(self):
            return "some raw body"

    with mock.patch.object(errors, expected_error) as error:
        returned = await net.generate_error_response(StubResponse())

    error.assert_called_once_with("https://some.url", {}, "some raw body")
    assert returned is error()


@pytest.mark.asyncio
async def test_generate_bad_request_error_without_json_response():
    class StubResponse:
        real_url = "https://some.url"
        status = http.HTTPStatus.BAD_REQUEST
        headers = {}
        json = mock.AsyncMock(side_effect=aiohttp.ContentTypeError(None, None))

        async def read(self):
            return "some raw body"

    with mock.patch.object(errors, "BadRequestError", errors=None) as error:
        returned = await net.generate_error_response(StubResponse())

    error.assert_called_once_with("https://some.url", {}, "some raw body", errors=None)
    assert returned is error()


@pytest.mark.parametrize(
    ("data", "expected_errors"),
    [
        ('{"message": "raw message", "code": 123, "errors": {"component": []}}', {"component": []}),
        ('{"message": "raw message", "code": 123, "errors": {}}', {}),
        ('{"message": "raw message", "code": 123}', None),
    ],
)
@pytest.mark.asyncio
async def test_generate_bad_request_error_with_json_response(data, expected_errors):
    class StubResponse:
        real_url = "https://some.url"
        status = http.HTTPStatus.BAD_REQUEST
        headers = {}

        async def read(self):
            return data

    with mock.patch.object(errors, "BadRequestError", errors=None) as error:
        returned = await net.generate_error_response(StubResponse())

    error.assert_called_once_with("https://some.url", {}, data, "raw message", 123, errors=expected_errors)
    assert returned is error()
