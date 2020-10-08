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
import copy
import pickle  # noqa: S403 Consider possible security implications associated with pickle module.

import pytest

from hikari import undefined


class TestUndefined:
    def test_repr(self):
        assert repr(undefined.UNDEFINED) == "UNDEFINED"

    def test_str(self):
        assert str(undefined.UNDEFINED) == "UNDEFINED"

    def test_bool(self):
        assert bool(undefined.UNDEFINED) is False

    def test_singleton_behaviour(self):
        assert undefined.UNDEFINED is undefined.UNDEFINED
        assert undefined.UNDEFINED == undefined.UNDEFINED
        assert undefined.UNDEFINED is not None
        assert undefined.UNDEFINED is not False

    def test_count(self):
        assert undefined.count(9, 18, undefined.UNDEFINED, 36, undefined.UNDEFINED, 54) == 2

    def test_cannot_reinstatiate(self):
        with pytest.raises(TypeError):
            type(undefined.UNDEFINED)()

    def test_copy(self):
        assert copy.copy(undefined.UNDEFINED) is undefined.UNDEFINED

    def test_deepcopy(self):
        assert copy.deepcopy(undefined.UNDEFINED) is undefined.UNDEFINED

    def test_can_pickle(self):
        ser = pickle.dumps(undefined.UNDEFINED)
        deser = pickle.loads(ser)  # noqa: S301 pickle loads is unsafe with untrusted data
        assert deser is undefined.UNDEFINED
