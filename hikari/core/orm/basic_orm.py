#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
"""
A basic object relational model implementation for use with single sharded and multiple-sharded bots running on
the same process.
"""
import typing

from hikari.core.utils import types
from . import basic_event_adapter
from . import basic_state_registry


class BasicOrm:
    def __init__(self, message_cache_size: int, user_cache_size: int, dispatch) -> None:
        self.state_registry = basic_state_registry.BasicStateRegistry(message_cache_size, user_cache_size)
        self.event_adapter = basic_event_adapter.BasicEventAdapter(self.state_registry, dispatch)

    @property
    def raw_event_sink(self) -> typing.Callable[[str, types.DiscordObject], typing.Awaitable[None]]:
        """
        The inbound event sink that the gateway should send any raw events to.
        """
        return self.event_adapter.consume_raw_event
