# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
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
from hikari.utilities import attr_extensions

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


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILDS)
class RoleCreateEvent(RoleEvent):
    """Event fired when a role is created."""

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
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


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILDS)
class RoleUpdateEvent(RoleEvent):
    """Event fired when a role is updated."""

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
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


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILDS)
class RoleDeleteEvent(RoleEvent):
    """Event fired when a role is deleted."""

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from RoleEvent>>.

    role_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from RoleEvent>>.
