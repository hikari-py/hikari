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

__all__: typing.Final[typing.Sequence[str]] = ["IComponent"]

import abc
import typing

if typing.TYPE_CHECKING:
    from hikari.api import rest


class IComponent(abc.ABC):
    """A component that makes up part of the application.

    Objects that derive from this should usually be attributes on the
    `hikari.api.rest.IRESTClient` object.

    Examples
    --------
    See the source code for `hikari.api.entity_factory.IEntityFactoryComponent`,
    `hikari.api.cache.ICacheComponent`, and
    `hikari.api.event_dispatcher.IEventDispatcherComponent`
    for examples of usage.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def app(self) -> rest.IRESTClient:
        """Return the Application that owns this component.

        Returns
        -------
        hikari.api.rest.IRESTClient
            The application implementation that owns this component.
        """
