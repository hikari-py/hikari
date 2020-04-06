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
"""Event management for stateless bots."""

__all__ = ["StatelessEventManagerImpl"]

from hikari.state import event_dispatchers
from hikari.state import event_managers


class StatelessEventManagerImpl(event_managers.EventManager[event_dispatchers.EventDispatcher]):
    """Stateless event manager implementation for stateless bots.

    This is an implementation that does not rely on querying prior information to
    operate. The implementation details of this are much simpler than a stateful
    version, and are not immediately affected by the use of intents.
    """

    # @event_managers.raw_event_mapper("CONNECT")
