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
import pytest

from hikari import errors
from hikari.net import codes
from hikari.net import routes


class TestGatewayError:
    def test_init(self):
        err = errors.GatewayError("boom")
        assert err.reason == "boom"

    def test_str(self):
        err = errors.GatewayError("boom")
        assert str(err) == "boom"


class TestGatewayClientClosedError:
    def test_init(self):
        err = errors.GatewayClientClosedError("blah")
        assert err.reason == "blah"


class TestGatewayConnectionClosedError:
    def test_init_valid_reason(self):
        err = errors.GatewayServerClosedConnectionError(codes.GatewayCloseCode.UNKNOWN_OPCODE, "foo")
        assert err.close_code == codes.GatewayCloseCode.UNKNOWN_OPCODE.value
        assert err.reason == "foo"

    def test_init_valid_close_code(self):
        err = errors.GatewayServerClosedConnectionError(codes.GatewayCloseCode.UNKNOWN_OPCODE)
        assert err.close_code == codes.GatewayCloseCode.UNKNOWN_OPCODE.value
        assert err.reason.endswith(f" ({codes.GatewayCloseCode.UNKNOWN_OPCODE.name})")

    def test_init_invalid_close_code(self):
        err = errors.GatewayServerClosedConnectionError(69)
        assert err.close_code == 69
        assert err.reason.endswith(" (69)")

    def test_init_no_close_code(self):
        err = errors.GatewayServerClosedConnectionError()
        assert err.close_code is None
        assert err.reason.endswith(" (no reason)")


class TestGatewayInvalidTokenError:
    def test_init(self):
        err = errors.GatewayInvalidTokenError()
        assert err.close_code == codes.GatewayCloseCode.AUTHENTICATION_FAILED


class TestGatewayInvalidSessionError:
    @pytest.mark.parametrize("can_resume", (True, False))
    def test_init(self, can_resume):
        err = errors.GatewayInvalidSessionError(can_resume)
        assert err.close_code is None


class TestGatewayMustReconnectError:
    def test_init(self):
        err = errors.GatewayMustReconnectError()
        assert err.close_code is None


class TestGatewayNeedsShardingError:
    def test_init(self):
        err = errors.GatewayNeedsShardingError()
        assert err.close_code == codes.GatewayCloseCode.SHARDING_REQUIRED


class TestGatewayZombiedError:
    def test_init(self):
        err = errors.GatewayZombiedError()
        assert err.reason.startswith("No heartbeat was received")


class TestHTTPError:
    def test_init(self):
        err = errors.HTTPError("ree")
        assert err.reason == "ree"

    def test_str(self):
        assert str(errors.HTTPError("ree")) == "ree"


@pytest.mark.parametrize("type", [errors.CodedHTTPError, errors.ServerHTTPError, errors.ClientHTTPError])
class TestCodedHTTPErrors:
    def test_init(self, type):
        # Garbage test case, doesn't matter really.
        http = codes.HTTPStatusCode.BAD_GATEWAY if "server" in type.__name__.lower() else codes.HTTPStatusCode.FORBIDDEN
        route = routes.GATEWAY.compile("GET")
        message = "you done screwed up son"
        code = codes.JSONErrorCode.CANNOT_PIN_A_MESSAGE_IN_A_DIFFERENT_CHANNEL

        ex = type(http, route, message, code)

        assert ex.status == http
        assert ex.route == route
        assert ex.message == message
        assert ex.json_code == code
        assert ex.reason == str(http)

    def test_str(self, type):
        http = codes.HTTPStatusCode.BAD_GATEWAY if "server" in type.__name__.lower() else codes.HTTPStatusCode.FORBIDDEN
        route = routes.GATEWAY.compile("GET")
        message = "you done screwed up son"
        code = codes.JSONErrorCode.CANNOT_PIN_A_MESSAGE_IN_A_DIFFERENT_CHANNEL

        ex = type(http, route, message, code)

        assert str(ex) == f"{ex.reason}: ({code}) {message}"


@pytest.mark.parametrize(
    ("type", "expected_status"),
    [
        (errors.BadRequestHTTPError, 400),
        (errors.UnauthorizedHTTPError, 401),
        (errors.ForbiddenHTTPError, 403),
        (errors.NotFoundHTTPError, 404),
    ],
)
class TestHTTPClientErrors:
    def test_init(self, type, expected_status):
        route = routes.GATEWAY.compile("GET")
        message = "you done screwed up son"
        code = codes.JSONErrorCode.CANNOT_PIN_A_MESSAGE_IN_A_DIFFERENT_CHANNEL

        ex = type(route, message, code)

        assert ex.status == expected_status
        assert ex.reason == str(ex.status)
        assert ex.route == route
        assert ex.message == message
        assert ex.json_code == code

    def test_str(self, type, expected_status):
        route = routes.GATEWAY.compile("GET")
        message = "you done screwed up son"
        code = codes.JSONErrorCode.CANNOT_PIN_A_MESSAGE_IN_A_DIFFERENT_CHANNEL

        ex = type(route, message, code)

        assert str(ex) == f"{ex.reason}: ({code}) {message}"
