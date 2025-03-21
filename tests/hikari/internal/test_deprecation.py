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

import warnings

import mock
import pytest

from hikari import _about as hikari_about
from hikari.internal import deprecation


class TestWarnDeprecated:
    def test_when_not_past_removal(self):
        with mock.patch.object(hikari_about, "__version__", "2.0.1"):
            with mock.patch.object(warnings, "warn") as warn:
                deprecation.warn_deprecated(
                    "testing", removal_version="2.0.2", additional_info="Some info!", stack_level=100
                )

        warn.assert_called_once_with(
            "'testing' is deprecated and will be removed in `2.0.2`. Some info!",
            category=DeprecationWarning,
            stacklevel=100,
        )

    def test_when_past_removal(self):
        with mock.patch.object(hikari_about, "__version__", "2.0.2"):
            with pytest.raises(DeprecationWarning):
                deprecation.warn_deprecated("testing", removal_version="2.0.2", additional_info="Some info!")
