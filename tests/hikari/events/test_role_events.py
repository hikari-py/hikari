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
from hikari.events import role_events


class TestRoleCreateEvent:
    @pytest.fixture
    def event(self):
        return role_events.RoleCreateEvent(shard=object(), role=mock.Mock(guilds.Role))

    def test_app_property(self, event):
        assert event.app is event.role.app

    def test_guild_id_property(self, event):
        event.role.guild_id = 123
        assert event.guild_id == 123

    def test_role_id_property(self, event):
        event.role.id = 123
        assert event.role_id == 123


class TestRoleUpdateEvent:
    @pytest.fixture
    def event(self):
        return role_events.RoleUpdateEvent(shard=object(), role=mock.Mock(guilds.Role), old_role=mock.Mock(guilds.Role))

    def test_app_property(self, event):
        assert event.app is event.role.app

    def test_guild_id_property(self, event):
        event.role.guild_id = 123
        assert event.guild_id == 123

    def test_role_id_property(self, event):
        event.role.id = 123
        assert event.role_id == 123

    def test_old_role(self, event):
        event.old_role.guild_id = 123
        event.old_role.id = 456

        assert event.old_role.guild_id == 123
        assert event.old_role.id == 456
