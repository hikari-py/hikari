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
from hikari import intents


class TestShardCloseCode:
    @pytest.mark.parametrize(("code", "expected"), [(1000, True), (1001, True), (4000, False), (4014, False)])
    def test_is_standard_property(self, code, expected):
        assert errors.ShardCloseCode(code).is_standard is expected


class TestGatewayError:
    @pytest.fixture()
    def error(self):
        return errors.GatewayError("some reason")

    def test_str(self, error):
        assert str(error) == "some reason"


class TestGatewayServerClosedConnectionError:
    @pytest.fixture()
    def error(self):
        return errors.GatewayServerClosedConnectionError("some reason", 123)

    def test_str(self, error):
        assert str(error) == "Server closed connection with code 123 (some reason)"


class TestHTTPResponseError:
    @pytest.fixture()
    def error(self):
        return errors.HTTPResponseError("https://some.url", http.HTTPStatus.BAD_REQUEST, {}, "raw body")

    def test_str(self, error):
        assert str(error) == "Bad Request 400: 'raw body' for https://some.url"

    def test_str_when_status_is_not_HTTPStatus(self, error):
        error.status = "SOME STATUS"
        assert str(error) == "Some Status: 'raw body' for https://some.url"

    def test_str_when_message_is_not_None(self, error):
        error.status = "SOME STATUS"
        error.message = "Some message"
        assert str(error) == "Some Status: 'Some message' for https://some.url"


class TestBulkDeleteError:
    @pytest.fixture()
    def error(self):
        return errors.BulkDeleteError(range(10), range(10))

    def test_percentage_completion_property(self, error):
        assert error.percentage_completion == 50


class TestMissingIntentError:
    @pytest.fixture()
    def error(self):
        return errors.MissingIntentError(intents.Intents.GUILD_BANS | intents.Intents.GUILD_EMOJIS)

    def test_str(self, error):
        assert str(error) == "You are missing the following intent(s): GUILD_BANS, GUILD_EMOJIS"
