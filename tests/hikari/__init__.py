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

import asyncio
import inspect
import sys
import typing
import warnings

import pytest


#####################
# Enable loop debug #
#####################
class TestingPolicy(asyncio.DefaultEventLoopPolicy):
    def set_event_loop(self, loop: typing.Optional[asyncio.AbstractEventLoop]) -> None:
        # Close any old event loops to prevent them from raising warnings
        if self._local._loop:
            self._local._loop.close()

        if loop is not None:
            loop.set_debug(True)

        super().set_event_loop(loop)


asyncio.set_event_loop_policy(TestingPolicy())
sys.set_coroutine_origin_tracking_depth(100)

################################################################################
# Force ids in parametrize to be stringified by default for better readability #
################################################################################
_pytest_parametrize = pytest.mark.parametrize


def parametrize(*args, **kwargs):
    kwargs.setdefault("ids", repr)
    return _pytest_parametrize(*args, **kwargs)


pytest.mark.parametrize = parametrize

#################################################
# Filter out deprecation warnings emitted by us #
#################################################

_warn = warnings.warn


def warn(*args, **kwargs):
    frame = inspect.currentframe().f_back

    if frame.f_globals.get("__name__") == "hikari.internal.deprecation" and frame.f_code.co_name == "warn_deprecated":
        # Ignore this specific DeprecationWarning
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            _warn(*args, **kwargs)

    else:
        _warn(*args, **kwargs)


warnings.warn = warn
