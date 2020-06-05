#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""Datastructure bases."""

from __future__ import annotations

__all__ = ["Entity", "Unique"]

import abc
import typing

import attr

from hikari.utilities import snowflake

if typing.TYPE_CHECKING:
    import datetime

    from hikari.api import app as app_


@attr.s(eq=True, hash=False, init=False, kw_only=True, slots=False)
class Entity(abc.ABC):
    """The base for an entity used in this API.

    An entity is a managed object that contains a binding to the owning
    application instance. This enables it to perform API calls from
    methods directly.
    """

    _app: typing.Union[
        None,
        app_.IApp,
        app_.IGatewayZookeeper,
        app_.IGatewayConsumer,
        app_.IGatewayDispatcher,
        app_.IRESTApp,
        app_.IBot,
    ] = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    def __init__(self, app: app_.IApp) -> None:
        self._app = app


@attr.s(eq=True, hash=True, init=False, kw_only=True, slots=False)
class Unique(typing.SupportsInt):
    """A base for an entity that has an integer ID of some sort.

    Casting an object of this type to an `int` will produce the
    integer ID of the object.
    """

    id: snowflake.Snowflake = attr.ib(converter=snowflake.Snowflake, hash=True, eq=True, repr=True)
    """The ID of this entity."""

    @property
    def created_at(self) -> datetime.datetime:
        """When the object was created."""
        return self.id.created_at

    def __int__(self) -> int:
        return int(self.id)


UniqueObject = typing.Union[Unique, snowflake.Snowflake, int, str]
"""Type hint representing a unique object entity."""
