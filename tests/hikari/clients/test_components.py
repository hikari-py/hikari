#!/usr/bin/env python3
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
# along ith Hikari. If not, see <https://www.gnu.org/licenses/>.
import mock

from hikari.clients import components
from hikari.clients import configs
from hikari.clients import rest
from hikari.clients import shards
from hikari.events import dispatchers
from hikari.events import event_managers


class TestComponents:
    def test___init__(self):
        mock_config = mock.MagicMock(configs.BotConfig)
        mock_event_dispatcher = mock.MagicMock(dispatchers.EventDispatcher)
        mock_event_manager = mock.MagicMock(event_managers.EventManager)
        mock_rest = mock.MagicMock(rest.RESTClient)
        mock_shards = mock.MagicMock(shards.ShardClient)
        component = components.Components(
            config=mock_config,
            event_manager=mock_event_manager,
            event_dispatcher=mock_event_dispatcher,
            rest=mock_rest,
            shards=mock_shards,
        )
        assert component.config is mock_config
        assert component.event_dispatcher is mock_event_dispatcher
        assert component.event_manager is mock_event_manager
        assert component.rest is mock_rest
        assert component.shards is mock_shards
