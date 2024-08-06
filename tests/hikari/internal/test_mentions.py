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

import pytest

from hikari import undefined
from hikari.internal import mentions


@pytest.mark.parametrize(
    ("function_input", "expected_output"),
    [
        ((True, True, True, True), {"parse": ["everyone", "users", "roles"], "replied_user": True}),
        ((False, False, False, False), {"parse": []}),
        ((undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED, undefined.UNDEFINED), {"parse": []}),
        ((undefined.UNDEFINED, True, True, True), {"parse": ["roles", "users"], "replied_user": True}),
        ((False, False, [123], [456]), {"parse": [], "users": ["123"], "roles": ["456"]}),
        (
            (True, True, [123, "123", 987], ["213", "456", 456]),
            {"parse": ["everyone"], "users": ["123", "987"], "roles": ["213", "456"], "replied_user": True},
        ),
    ],
)
def test_generate_allowed_mentions(function_input, expected_output):
    returned = mentions.generate_allowed_mentions(*function_input)
    for k, v in expected_output.items():
        if isinstance(v, list):
            returned[k] = sorted(v)

    for k, v in expected_output.items():
        if isinstance(v, list):
            expected_output[k] = sorted(expected_output[k])

    assert returned == expected_output
