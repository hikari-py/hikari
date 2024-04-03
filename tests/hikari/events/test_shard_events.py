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

from hikari import snowflakes
from hikari.events import shard_events


class TestShardReadyEvent:
    @pytest.fixture
    def event(self):
        return shard_events.ShardReadyEvent(
            my_user=mock.Mock(),
            resume_gateway_url="testing",
            shard=None,
            actual_gateway_version=1,
            session_id="ok",
            application_id=1,
            application_flags=1,
            unavailable_guilds=[],
        )

    def test_app_property(self, event):
        assert event.app is event.my_user.app


class TestMemberChunkEvent:
    @pytest.fixture
    def event(self):
        return shard_events.MemberChunkEvent(
            app=mock.Mock(),
            shard=mock.Mock(),
            guild_id=snowflakes.Snowflake(69420),
            members={
                snowflakes.Snowflake(1): mock.Mock(),
                snowflakes.Snowflake(55): mock.Mock(),
                snowflakes.Snowflake(99): mock.Mock(),
                snowflakes.Snowflake(455): mock.Mock(),
            },
            chunk_count=1,
            chunk_index=1,
            not_found=(),
            presences={},
            nonce="blah",
        )

    def test___getitem___with_slice(self, event):
        mock_member_0 = object()
        mock_member_1 = object()
        event.members = {1: object(), 55: object(), 99: mock_member_0, 455: object(), 5444: mock_member_1}

        assert event[2:5:2] == (mock_member_0, mock_member_1)

    def test___getitem___with_valid_index(self, event):
        mock_member = object()
        event.members[snowflakes.Snowflake(99)] = mock_member
        assert event[2] is mock_member

        with pytest.raises(IndexError):
            assert event[55]

    def test___getitem___with_invalid_index(self, event):
        with pytest.raises(IndexError):
            assert event[123]

    def test___iter___(self, event):
        member_0 = mock.Mock()
        member_1 = mock.Mock()
        member_2 = mock.Mock()

        event.members = {
            snowflakes.Snowflake(1): member_0,
            snowflakes.Snowflake(2): member_1,
            snowflakes.Snowflake(3): member_2,
        }

        assert list(event) == [member_0, member_1, member_2]

    def test___len___(self, event):
        assert len(event) == 4
