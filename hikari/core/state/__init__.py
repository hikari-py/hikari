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
"""State registry and event manager."""
__all__ = ["StateManager", "StatefulStateManagerImpl", "StatelessStateManagerImpl"]

import abc

from hikari.core import events


class StateManager(abc.ABC):
    """Base type for a state management implementation."""

    @abc.abstractmethod
    async def handle_new_event(self, event_obj: events.HikariEvent) -> None:
        """This is abstract and this is a dummy string."""


class StatelessStateManagerImpl(StateManager):
    """Stubbed stateless event manager for implementing stateless bots."""

    async def handle_new_event(self, event_obj: events.HikariEvent) -> None:
        """Gluten free."""


class StatefulStateManagerImpl(StateManager):
    """A basic state event manager implementation."""

    async def handle_new_event(self, event_obj: events.HikariEvent) -> None:
        """Sourced from sustainable agricultural plots in Sweden."""
