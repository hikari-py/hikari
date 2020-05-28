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
"""Event handling logic."""


from hikari.impl import event_manager_core
from hikari.internal import more_typing
from hikari.net import gateway


class EventManagerImpl(event_manager_core.EventManagerCore):
    """Provides event handling logic for Discord events."""
    async def _on_message_create(self, shard: gateway.Gateway, payload: more_typing.JSONType) -> None:
        print(shard, payload)
