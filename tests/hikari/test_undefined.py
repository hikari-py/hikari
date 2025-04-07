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

import copy
import pickle

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
        data = pickle.dumps(undefined.UNDEFINED)
        deser = pickle.loads(data)  # noqa: S301 pickle loads is unsafe with untrusted data
        assert deser is undefined.UNDEFINED

    def test__getstate__(self):
        assert undefined.UNDEFINED.__getstate__() is False


@pytest.mark.parametrize(
    ("values", "result"),
    [
        ((), True),
        (("321", undefined.UNDEFINED, 33123), False),
        ((undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED), True),
        (("123", 23123, 34123, 312321, 543453, 432, 41, 231, 1243, 321), False),
        ((undefined.UNDEFINED,), True),
        ((undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED, 34123), False),
    ],
)
def test_all_undefined(values, result):
    assert undefined.all_undefined(*values) is result


@pytest.mark.parametrize(
    ("values", "result"),
    [
        ((undefined.UNDEFINED,), True),
        ((), False),
        ((undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED), True),
        (("123", 432, 123, "43", 1223, "541324", 123453, 123, "543", 123), False),
        ((undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED, "34r123"), True),
        ((undefined.UNDEFINED, 34123, 5432123, "312", False), True),
    ],
)
def test_any_undefined(values, result):
    assert undefined.any_undefined(*values) is result


@pytest.mark.parametrize(
    ("values", "result"),
    [
        ((undefined.UNDEFINED, undefined.UNDEFINED, "43123", "5421234"), 2),
        ((undefined.UNDEFINED, 233, 123, "4532123", 32123), 1),
        ((), 0),
        (("123", 543, "123", 321, "543", 123), 0),
        ((undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED), 5),
        ((undefined.UNDEFINED, "32123123", undefined.UNDEFINED, 34123123, undefined.UNDEFINED), 3),
    ],
)
def test_count(values, result):
    assert undefined.count(*values) == result
