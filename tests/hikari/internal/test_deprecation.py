# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
import pytest

from hikari.internal import deprecation


class TestWarnDeprecated:
    def test_when_function(self):
        def test():
            ...

        with pytest.warns(
            DeprecationWarning,
            match=(
                r"Call to deprecated function/method "
                r"'tests.hikari.internal.test_deprecation.TestWarnDeprecated.test_when_function.<locals>.test' "
                r"\(Too cool\)"
            ),
        ):
            deprecation.warn_deprecated(test, "Too cool")

    def test_when_class(self):
        class Test:
            ...

        with pytest.warns(
            DeprecationWarning,
            match=(
                r"Instantiation of deprecated class "
                r"'tests.hikari.internal.test_deprecation.TestWarnDeprecated.test_when_class.<locals>.Test' \(Too old\)"
            ),
        ):
            deprecation.warn_deprecated(Test, "Too old")

    def test_when_str(self):
        with pytest.warns(
            DeprecationWarning,
            match=r"Call to deprecated function/method 'testing' \(Use 'foo.bar' instead\)",
        ):
            deprecation.warn_deprecated("testing", "Use 'foo.bar' instead")
