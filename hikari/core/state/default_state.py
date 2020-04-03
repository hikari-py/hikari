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
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
"""Basic single-application state manager."""
__all__ = ["DefaultState"]

from hikari.core.state import dispatcher
from hikari.core import entities
from hikari.core import events
from hikari.core.state import base_state


class DefaultState(base_state.BaseState):
    def __init__(self, event_dispatcher: dispatcher.EventDispatcher):
        super().__init__()
        self.event_dispatcher: dispatcher.EventDispatcher = event_dispatcher

    @base_state.register_state_event_handler("MESSAGE_CREATE")
    async def _on_message_create(self, _, payload: entities.RawEntityT) -> None:
        self.dispatch(events.MessageCreateEvent.deserialize(payload))

    def dispatch(self, event: events.HikariEvent) -> None:
        self.event_dispatcher.dispatch_event(event)
