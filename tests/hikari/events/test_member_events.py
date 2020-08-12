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

import mock
import pytest

from hikari.events import member_events


class TestMemberEvent:
    @pytest.fixture
    def event(self):
        class StubEvent(member_events.MemberEvent):
            guild_id = 123
            user = mock.Mock(id=456)
            shard = None
            app = None

        return StubEvent()

    def test_user_id_property(self, event):
        event.user_id == 456


class TestMemberCreateEvent:
    @pytest.fixture
    def event(self):
        return member_events.MemberCreateEvent(app=None, shard=None, member=mock.Mock())

    def test_guild_property(self, event):
        event.member.guild_id = 123
        event.guild_id == 123

    def test_user_property(self, event):
        user = object()
        event.member.user = user
        event.user == user


class TestMemberUpdateEvent:
    @pytest.fixture
    def event(self):
        return member_events.MemberUpdateEvent(app=None, shard=None, member=mock.Mock())

    def test_guild_property(self, event):
        event.member.guild_id = 123
        event.guild_id == 123

    def test_user_property(self, event):
        user = object()
        event.member.user = user
        event.user == user
