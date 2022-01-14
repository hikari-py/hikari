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
import mock
import pytest

from hikari.internal import deprecation


class TestWarnDeprecated:
    def test_when_obj(self):
        def test():
            ...

        with pytest.warns(
            DeprecationWarning,
            match=(
                r"'tests.hikari.internal.test_deprecation.TestWarnDeprecated.test_when_obj.<locals>.test'"
                r" is deprecated and will be removed in a following version."
            ),
        ):
            deprecation.warn_deprecated(test)

    def test_when_alternative(self):
        with pytest.warns(
            DeprecationWarning,
            match=r"'test' is deprecated and will be removed in a following version. You can use 'foo.bar' instead.",
        ):
            deprecation.warn_deprecated("test", alternative="foo.bar")

    def test_when_version(self):
        with pytest.warns(DeprecationWarning, match=r"'test' is deprecated and will be removed in version 0.0.1"):
            deprecation.warn_deprecated("test", version="0.0.1")


class TestDeprecated:
    def test_on_function(self):
        call_mock = mock.Mock()

        @deprecation.deprecated("0.0.0", "other")
        def test():
            return call_mock()

        with mock.patch.object(deprecation, "warn_deprecated") as warn_deprecated:
            assert test() is call_mock.return_value

        warn_deprecated.assert_called_once_with(test.__wrapped__, version="0.0.0", alternative="other", stack_level=3)

    def test_on_class(self):
        called = False

        @deprecation.deprecated("0.0.0", "other")
        class Test:
            def __init__(self):
                nonlocal called
                called = True

        with mock.patch.object(deprecation, "warn_deprecated") as warn_deprecated:
            Test()

        assert called is True
        warn_deprecated.assert_called_once_with(Test.__wrapped__, version="0.0.0", alternative="other", stack_level=3)
