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
Handles consumption of gateway events and converting them to the correct data types.
"""
from __future__ import annotations

import enum
import logging


from hikari.core.components import basic_state_registry as _state
from hikari.core.components import event_adapter


class BasicEventNames(enum.Enum):
    """Event names that the basic event adapter can emit to the dispatcher."""

    CONNECT = enum.auto()
    DISCONNECT = enum.auto()
    INVALID_SESSION = enum.auto()
    REQUEST_TO_RECONNECT = enum.auto()


class BasicEventAdapter(event_adapter.EventAdapter):
    """
    Basic implementation of event management logic.
    """

    def __init__(self, state_registry: _state.BasicStateRegistry, dispatch) -> None:
        self.dispatch = dispatch
        self.logger = logging.getLogger(__name__)
        self.state_registry: _state.BasicStateRegistry = state_registry

    async def handle_disconnect(self, gateway, payload):
        """
        Dispatches a :attr:`BasicEventNames.DISCONNECT` with the gateway object that triggered it as an argument.
        """
        self.dispatch(BasicEventNames.DISCONNECT)

    async def handle_hello(self, gateway, payload):
        """
        Dispatches a :attr:`BasicEventNames.CONNECT` with the gateway object that triggered it as an argument.
        """
        self.dispatch(BasicEventNames.CONNECT, gateway)

    async def handle_invalid_session(self, gateway, payload):
        """
        Dispatches a :attr:`BasicEventNames.INVALID_SESSION` with the gateway object that triggered it
        and a :class:`bool` indicating if the connection is able to be resumed or not as arguments.
        as an argument.
        """
        self.dispatch(BasicEventNames.INVALID_SESSION, gateway, payload)

    async def handle_request_to_reconnect(self, gateway, payload):
        """
        Dispatches a :attr:`BasicEventNames.REQUEST_TO_RECONNECT` with the gateway object that triggered it as
        an argument.
        """
        self.dispatch(BasicEventNames.REQUEST_TO_RECONNECT, gateway)
