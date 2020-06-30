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
"""General bits and pieces that are reused between components."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = ["generate_error_response"]

import http
import typing

import aiohttp

from hikari import errors


async def generate_error_response(response: aiohttp.ClientResponse) -> errors.HTTPError:
    """Given an erroneous HTTP response, return a corresponding exception."""
    real_url = str(response.real_url)
    raw_body = await response.read()

    if response.status == http.HTTPStatus.BAD_REQUEST:
        return errors.BadRequest(real_url, response.headers, raw_body)
    if response.status == http.HTTPStatus.UNAUTHORIZED:
        return errors.Unauthorized(real_url, response.headers, raw_body)
    if response.status == http.HTTPStatus.FORBIDDEN:
        return errors.Forbidden(real_url, response.headers, raw_body)
    if response.status == http.HTTPStatus.NOT_FOUND:
        return errors.NotFound(real_url, response.headers, raw_body)

    # noinspection PyArgumentList
    status = http.HTTPStatus(response.status)

    cls: typing.Type[errors.HikariError]
    if 400 <= status < 500:
        cls = errors.ClientHTTPErrorResponse
    elif 500 <= status < 600:
        cls = errors.ServerHTTPErrorResponse
    else:
        cls = errors.HTTPErrorResponse

    return cls(real_url, status, response.headers, raw_body)
