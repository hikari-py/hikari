# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.

import mock
import pytest

from hikari.api import shard
from hikari.events import shard_events


class TestShardEvent:
    @pytest.fixture
    def event(self):
        class ShardEventImpl(shard_events.ShardEvent):
            shard = mock.Mock(shard.IGatewayShard)

        return ShardEventImpl()

    def test_app_property(self, event):
        stub_app = object()
        event.shard.app = stub_app
        assert event.app is stub_app
