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

from hikari import guilds
from hikari import snowflakes
from hikari.events import member_events
from tests.hikari import hikari_test_helpers


class TestMemberEvent:
    @pytest.fixture()
    def event(self):
        cls = hikari_test_helpers.mock_class_namespace(
            member_events.MemberEvent,
            slots_=False,
            guild_id=mock.PropertyMock(return_value=snowflakes.Snowflake(123)),
            user=mock.Mock(id=456),
        )
        return cls()

    def test_app_property(self, event):
        assert event.app is event.user.app

    def test_user_id_property(self, event):
        event.user_id == 456

    def test_guild_when_no_cache_trait(self):
        event = hikari_test_helpers.mock_class_namespace(member_events.MemberEvent, app=None)()

        assert event.get_guild() is None

    def test_get_guild_when_available(self, event):
        result = event.get_guild()

        assert result is event.app.cache.get_available_guild.return_value
        event.app.cache.get_available_guild.assert_called_once_with(123)
        event.app.cache.get_unavailable_guild.assert_not_called()

    def test_guild_when_unavailable(self, event):
        event.app.cache.get_available_guild.return_value = None
        result = event.get_guild()

        assert result is event.app.cache.get_unavailable_guild.return_value
        event.app.cache.get_unavailable_guild.assert_called_once_with(123)
        event.app.cache.get_available_guild.assert_called_once_with(123)


class TestMemberCreateEvent:
    @pytest.fixture()
    def event(self):
        return member_events.MemberCreateEvent(shard=None, member=mock.Mock())

    def test_guild_property(self, event):
        event.member.guild_id = 123
        event.guild_id == 123

    def test_user_property(self, event):
        user = object()
        event.member.user = user
        event.user == user


class TestMemberUpdateEvent:
    @pytest.fixture()
    def event(self):
        return member_events.MemberUpdateEvent(shard=None, member=mock.Mock(), old_member=mock.Mock(guilds.Member))

    def test_guild_property(self, event):
        event.member.guild_id = 123
        event.guild_id == 123

    def test_user_property(self, event):
        user = object()
        event.member.user = user
        event.user == user

    def test_old_user_property(self, event):
        event.member.guild_id = 123
        event.member.id = 456

        assert event.member.guild_id == 123
        assert event.member.id == 456
