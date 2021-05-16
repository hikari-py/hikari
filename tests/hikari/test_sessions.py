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

import datetime

from hikari import sessions
from tests.hikari import hikari_test_helpers


def test_SessionStartLimit_used_property():
    obj = sessions.SessionStartLimit(
        total=100, remaining=12, reset_after=datetime.timedelta(seconds=1), max_concurrency=1
    )
    assert obj.used == 88


def test_SessionStartLimit_reset_at_property():
    obj = hikari_test_helpers.mock_class_namespace(
        sessions.SessionStartLimit,
        init_=False,
        _created_at=datetime.datetime(2020, 7, 22, 22, 22, 36, 988017, tzinfo=datetime.timezone.utc),
        reset_after=datetime.timedelta(hours=1, days=10),
    )()
    assert obj.reset_at == datetime.datetime(2020, 8, 1, 23, 22, 36, 988017, tzinfo=datetime.timezone.utc)
