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
import pytest

from hikari.events import shard_events
from tests.hikari import hikari_test_helpers


class TestMemberChunkEvent:
    def test___getitem___with_slice(self):
        mock_member_0 = object()
        mock_member_1 = object()
        event = hikari_test_helpers.stub_class(
            shard_events.MemberChunkEvent,
            members={1: object(), 55: object(), 99: mock_member_0, 455: object(), 5444: mock_member_1},
        )
        assert event[2:5:2] == (mock_member_0, mock_member_1)

    def test___getitem___with_valid_index(self):
        mock_member = object()
        event = hikari_test_helpers.stub_class(
            shard_events.MemberChunkEvent, members={1: object(), 55: object(), 99: mock_member, 455: object()}
        )
        assert event[2] is mock_member

        with pytest.raises(IndexError):
            assert event[55]

    def test___getitem___with_invalid_index(self):
        event = hikari_test_helpers.stub_class(
            shard_events.MemberChunkEvent, members={1: object(), 55: object(), 99: object(), 455: object()}
        )

        with pytest.raises(IndexError):
            assert event[55]

    def test___iter___(self):
        member_0 = object()
        member_1 = object()
        member_2 = object()

        event = hikari_test_helpers.stub_class(
            shard_events.MemberChunkEvent, members={234: member_0, 76: member_1, 999: member_2}
        )
        assert list(event) == [member_0, member_1, member_2]

    def test___len___(self):
        event = hikari_test_helpers.stub_class(
            shard_events.MemberChunkEvent, members={1: object(), 55: object(), 99: object(), 455: object()}
        )
        assert len(event) == 4
