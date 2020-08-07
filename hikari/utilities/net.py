# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""General bits and pieces that are reused between components."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["generate_error_response"]

import http
import typing

from hikari import errors

if typing.TYPE_CHECKING:
    import aiohttp


async def generate_error_response(response: aiohttp.ClientResponse) -> errors.HTTPError:
    """Given an erroneous HTTP response, return a corresponding exception."""
    real_url = str(response.real_url)
    raw_body = await response.read()

    if response.status == http.HTTPStatus.BAD_REQUEST:
        return errors.BadRequestError(real_url, response.headers, raw_body)
    if response.status == http.HTTPStatus.UNAUTHORIZED:
        return errors.UnauthorizedError(real_url, response.headers, raw_body)
    if response.status == http.HTTPStatus.FORBIDDEN:
        return errors.ForbiddenError(real_url, response.headers, raw_body)
    if response.status == http.HTTPStatus.NOT_FOUND:
        return errors.NotFoundError(real_url, response.headers, raw_body)

    # noinspection PyArgumentList
    status = http.HTTPStatus(response.status)

    cls: typing.Type[errors.HikariError]
    if 400 <= status < 500:
        cls = errors.ClientHTTPResponseError
    elif 500 <= status < 600:
        cls = errors.InternalServerError
    else:
        cls = errors.HTTPResponseError

    return cls(real_url, status, response.headers, raw_body)
