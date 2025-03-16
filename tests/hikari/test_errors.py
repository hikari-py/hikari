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
from __future__ import annotations

import http
import inspect
import typing

import mock
import pytest

from hikari import errors
from hikari import intents


class TestShardCloseCode:
    @pytest.mark.parametrize(("code", "expected"), [(1000, True), (1001, True), (4000, False), (4014, False)])
    def test_is_standard_property(self, code: int, expected: bool):
        assert errors.ShardCloseCode(code).is_standard is expected


class TestComponentStateConflictError:
    @pytest.fixture
    def error(self) -> errors.ComponentStateConflictError:
        return errors.ComponentStateConflictError("some reason")

    def test_str(self, error: errors.ComponentStateConflictError):
        assert str(error) == "some reason"


class TestUnrecognisedEntityError:
    @pytest.fixture
    def error(self) -> errors.UnrecognisedEntityError:
        return errors.UnrecognisedEntityError("some reason")

    def test_str(self, error: errors.UnrecognisedEntityError):
        assert str(error) == "some reason"


class TestGatewayError:
    @pytest.fixture
    def error(self) -> errors.GatewayError:
        return errors.GatewayError("some reason")

    def test_str(self, error: errors.GatewayError):
        assert str(error) == "some reason"


class TestGatewayServerClosedConnectionError:
    @pytest.fixture
    def error(self) -> errors.GatewayServerClosedConnectionError:
        return errors.GatewayServerClosedConnectionError("some reason", 123)

    def test_str(self, error: errors.GatewayServerClosedConnectionError):
        assert str(error) == "Server closed connection with code 123 (some reason)"


class TestHTTPResponseError:
    @pytest.fixture
    def error(self) -> errors.HTTPResponseError:
        return errors.HTTPResponseError(
            url="https://some.url",
            status=http.HTTPStatus.BAD_REQUEST,
            headers={},
            raw_body="raw body",
            message="message",
            code=12345,
        )

    def test_str(self, error: errors.HTTPResponseError):
        assert str(error) == "Bad Request 400: (12345) 'message' for https://some.url"

    def test_str_when_int_status_code(self, error: errors.HTTPResponseError):
        error.status = 699
        assert str(error) == "Unknown Status 699: (12345) 'message' for https://some.url"

    def test_str_when_message_is_None(self, error: errors.HTTPResponseError):
        with mock.patch.object(error, "message", None):
            assert str(error) == "Bad Request 400: (12345) 'raw body' for https://some.url"

    def test_str_when_code_is_zero(self, error: errors.HTTPResponseError):
        error.code = 0
        assert str(error) == "Bad Request 400: 'message' for https://some.url"

    def test_str_when_code_is_not_zero(self, error: errors.HTTPResponseError):
        error.code = 100
        assert str(error) == "Bad Request 400: (100) 'message' for https://some.url"


class TestBadRequestError:
    @pytest.fixture
    def error(self) -> errors.BadRequestError:
        errors_payload: typing.Mapping[str, typing.Any] = {
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
        }
        return errors.BadRequestError(url="https://some.url", headers={}, raw_body="raw body", errors=errors_payload)

    def test_str(self, error: errors.BadRequestError):
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

    def test_str_when_dump_error_errors(self, error: errors.BadRequestError):
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

    def test_str_when_cached(self, error: errors.BadRequestError):
        with mock.patch.object(error, "_cached_str", "ok"), mock.patch.object(errors, "_dump_errors") as dump_errors:
            assert str(error) == "ok"

        dump_errors.assert_not_called()

    def test_str_when_no_errors(self, error: errors.BadRequestError):
        error.errors = None

        with mock.patch.object(errors, "_dump_errors") as dump_errors:
            assert str(error) == "Bad Request 400: 'raw body' for https://some.url"

        dump_errors.assert_not_called()


class TestRateLimitTooLongError:
    @pytest.fixture
    def error(self) -> errors.RateLimitTooLongError:
        return errors.RateLimitTooLongError(
            route=mock.PropertyMock(return_value="some route"),
            is_global=False,
            retry_after=0,
            max_retry_after=60,
            reset_at=0,
            limit=0,
            period=0,
        )

    def test_remaining(self, error: errors.RateLimitTooLongError):
        assert error.remaining == 0

    def test_str(self, error: errors.RateLimitTooLongError):
        assert str(error) == (
            "The request has been rejected, as you would be waiting for more than "
            f"the max retry-after (60) on route '{error.route}' [is_global=False]"
        )


class TestBulkDeleteError:
    @pytest.fixture
    def error(self) -> errors.BulkDeleteError:
        return errors.BulkDeleteError(range(10))

    def test_str(self, error: errors.BulkDeleteError):
        assert str(error) == "Error encountered when bulk deleting messages (10 messages deleted)"


class TestMissingIntentError:
    @pytest.fixture
    def error(self) -> errors.MissingIntentError:
        return errors.MissingIntentError(intents.Intents.GUILD_MEMBERS | intents.Intents.GUILD_EMOJIS)

    def test_str(self, error: errors.MissingIntentError):
        assert str(error) == "You are missing the following intent(s): GUILD_EMOJIS, GUILD_MEMBERS"
