# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Events pertaining to manipulation of roles within guilds."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "RoleEvent",
    "RoleCreateEvent",
    "RoleUpdateEvent",
    "RoleDeleteEvent",
]

import abc
import typing

import attr

from hikari.events import base_events
from hikari.events import shard_events
from hikari.models import intents

if typing.TYPE_CHECKING:
    from hikari.api import shard as gateway_shard
    from hikari.models import guilds
    from hikari.utilities import snowflake


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILDS)
class RoleEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any event that involves guild roles."""

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflake.Snowflake:
        """ID of the guild that this event relates to.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The ID of the guild that relates to this event.
        """

    @property
    @abc.abstractmethod
    def role_id(self) -> snowflake.Snowflake:
        """ID of the role that this event relates to.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The ID of the role that relates to this event.
        """


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILDS)
class RoleCreateEvent(RoleEvent):
    """Event fired when a role is created."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    role: guilds.Role = attr.ib()
    """Role that was created.

    Returns
    -------
    hikari.models.guilds.Role
        The created role.
    """

    @property
    def guild_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from RoleEvent>>.
        return self.role.guild_id

    @property
    def role_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from RoleEvent>>.
        return self.role.id


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILDS)
class RoleUpdateEvent(RoleEvent):
    """Event fired when a role is updated."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    role: guilds.Role = attr.ib()
    """Role that was updated.

    Returns
    -------
    hikari.models.guilds.Role
        The created role.
    """

    @property
    def guild_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from RoleEvent>>.
        return self.role.guild_id

    @property
    def role_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from RoleEvent>>.
        return self.role.id


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILDS)
class RoleDeleteEvent(RoleEvent):
    """Event fired when a role is deleted."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from RoleEvent>>.

    role_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from RoleEvent>>.
