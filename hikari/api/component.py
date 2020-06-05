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
"""Base interface for any internal components of an application."""

from __future__ import annotations

__all__ = ["IComponent"]

import abc
import typing

if typing.TYPE_CHECKING:
    from hikari.api import app


class IComponent(abc.ABC):
    """A component that makes up part of the application.

    Objects that derive from this should usually be attributes on the
    `hikari.api.app.IApp` object.

    Examples
    --------
    See the source code for `hikari.api.entity_factory.IEntityFactory`,
    `hikari.api.cache.ICache`, and
    `hikari.api.event_dispatcher.IEventDispatcher` for examples of usage.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def app(self) -> app.IApp:
        """Return the Application that owns this component.

        Returns
        -------
        hikari.api.app.IApp
            The application implementation that owns this component.
        """
