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
"""Core interface for components that consume raw API event payloads."""
from __future__ import annotations

__all__ = ["IEventConsumer"]

import abc
import typing

from hikari.api import component

if typing.TYPE_CHECKING:
    from hikari.net import gateway
    from hikari.utilities import data_binding


class IEventConsumer(component.IComponent, abc.ABC):
    """Interface describing a component that can consume raw gateway events.

    Implementations will usually want to combine this with a
    `hikari.api.event_dispatcher.IEventDispatcher` for a basic in-memory
    single-app event management system. You may in some cases implement this
    separately if you are passing events onto a system such as a message queue.
    """

    __slots__ = ()

    @abc.abstractmethod
    async def consume_raw_event(
        self, shard: gateway.Gateway, event_name: str, payload: data_binding.JSONObject
    ) -> None:
        """Process a raw event from a gateway shard and process it.

        Parameters
        ----------
        shard : hikari.net.gateway.Gateway
            The gateway shard that emitted the event.
        event_name : str
            The event name.
        payload : hikari.utility.data_binding.JSONObject
            The payload provided with the event.
        """
