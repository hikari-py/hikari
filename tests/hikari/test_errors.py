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
import inspect

import mock
import pytest

from hikari import errors
from hikari import intents


class TestShardCloseCode:
    @pytest.mark.parametrize(("code", "expected"), [(1000, True), (1001, True), (4000, False), (4014, False)])
    def test_is_standard_property(self, code, expected):
        assert errors.ShardCloseCode(code).is_standard is expected


class TestComponentStateConflictError:
    @pytest.fixture()
    def error(self):
        return errors.ComponentStateConflictError("some reason")

    def test_str(self, error):
        assert str(error) == "some reason"


class TestUnrecognisedEntityError:
    @pytest.fixture()
    def error(self):
        return errors.UnrecognisedEntityError("some reason")

    def test_str(self, error):
        assert str(error) == "some reason"


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
        return errors.HTTPResponseError(
            "https://some.url", http.HTTPStatus.BAD_REQUEST, {}, "raw body", "message", 12345
        )

    def test_str(self, error):
        assert str(error) == "Bad Request 400: (12345) 'message' for https://some.url"

    def test_str_when_int_status_code(self, error):
        error.status = 699
        assert str(error) == "Unknown Status 699: (12345) 'message' for https://some.url"

    def test_str_when_message_is_None(self, error):
        error.message = None
        assert str(error) == "Bad Request 400: (12345) 'raw body' for https://some.url"

    def test_str_when_code_is_zero(self, error):
        error.code = 0
        assert str(error) == "Bad Request 400: 'message' for https://some.url"

    def test_str_when_code_is_not_zero(self, error):
        error.code = 100
        assert str(error) == "Bad Request 400: (100) 'message' for https://some.url"


class TestBadRequestError:
    @pytest.fixture()
    def error(self):
        return errors.BadRequestError(
            "https://some.url",
            http.HTTPStatus.BAD_REQUEST,
            {},
            "raw body",
            errors={
                "": [{"code": "012", "message": "test error"}],
                "components": {
                    "0": {
                        "_errors": [
                            {"code": "123", "message": "something went wrong"},
                            {"code": "456", "message": "but more things too!"},
                        ]
                    }
                },
                "attachments": {"1": {"_errors": [{"code": "789", "message": "at this point, all wrong!"}]}},
            },
        )

    def test_str(self, error):
        assert str(error) == inspect.cleandoc(
            """
            Bad Request 400: 'raw body' for https://some.url

            root:
             - test error

            components.0:
             - something went wrong
             - but more things too!

            attachments.1:
             - at this point, all wrong!
            """
        )

    def test_str_when_dump_error_errors(self, error):
        with mock.patch.object(errors, "_dump_errors", side_effect=KeyError):
            string = str(error)

        assert string == inspect.cleandoc(
            """
            Bad Request 400: 'raw body' for https://some.url

            {
              "": [
                {
                  "code": "012",
                  "message": "test error"
                }
              ],
              "components": {
                "0": {
                  "_errors": [
                    {
                      "code": "123",
                      "message": "something went wrong"
                    },
                    {
                      "code": "456",
                      "message": "but more things too!"
                    }
                  ]
                }
              },
              "attachments": {
                "1": {
                  "_errors": [
                    {
                      "code": "789",
                      "message": "at this point, all wrong!"
                    }
                  ]
                }
              }
            }
            """
        )

    def test_str_when_cached(self, error):
        error._cached_str = "ok"

        with mock.patch.object(errors, "_dump_errors") as dump_errors:
            assert str(error) == "ok"

        dump_errors.assert_not_called()

    def test_str_when_no_errors(self, error):
        error.errors = None

        with mock.patch.object(errors, "_dump_errors") as dump_errors:
            assert str(error) == "Bad Request 400: 'raw body' for https://some.url"

        dump_errors.assert_not_called()


class TestRateLimitTooLongError:
    @pytest.fixture()
    def error(self):
        return errors.RateLimitTooLongError(
            route="some route", is_global=False, retry_after=0, max_retry_after=60, reset_at=0, limit=0, period=0
        )

    def test_remaining(self, error):
        assert error.remaining == 0

    def test_str(self, error):
        assert str(error) == (
            "The request has been rejected, as you would be waiting for more than "
            "the max retry-after (60) on route 'some route' [is_global=False]"
        )


class TestBulkDeleteError:
    @pytest.fixture()
    def error(self):
        return errors.BulkDeleteError(range(10))

    def test_str(self, error):
        assert str(error) == "Error encountered when bulk deleting messages (10 messages deleted)"


class TestMissingIntentError:
    @pytest.fixture()
    def error(self):
        return errors.MissingIntentError(intents.Intents.GUILD_MEMBERS | intents.Intents.GUILD_EMOJIS)

    def test_str(self, error):
        assert str(error) == "You are missing the following intent(s): GUILD_EMOJIS, GUILD_MEMBERS"
