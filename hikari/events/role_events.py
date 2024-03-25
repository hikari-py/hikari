# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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

__all__: typing.Sequence[str] = ("RoleEvent", "RoleCreateEvent", "RoleUpdateEvent", "RoleDeleteEvent")

import abc
import typing

import attrs

from hikari import intents
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import attrs_extensions

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import snowflakes
    from hikari import traits
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(intents.Intents.GUILDS)
class RoleEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any event that involves guild roles."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflakes.Snowflake:
        """ID of the guild that this event relates to."""

    @property
    @abc.abstractmethod
    def role_id(self) -> snowflakes.Snowflake:
        """ID of the role that this event relates to."""


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILDS)
class RoleCreateEvent(RoleEvent):
    """Event fired when a role is created."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    role: guilds.Role = attrs.field()
    """Role that was created."""

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.role.app

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from RoleEvent>>.
        return self.role.guild_id

    @property
    def role_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from RoleEvent>>.
        return self.role.id


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILDS)
class RoleUpdateEvent(RoleEvent):
    """Event fired when a role is updated."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    old_role: typing.Optional[guilds.Role] = attrs.field()
    """The old role object.

    This will be [`None`][] if the role missing from the cache.
    """

    role: guilds.Role = attrs.field()
    """Role that was updated."""

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.role.app

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from RoleEvent>>.
        return self.role.guild_id

    @property
    def role_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from RoleEvent>>.
        return self.role.id


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILDS)
class RoleDeleteEvent(RoleEvent):
    """Event fired when a role is deleted."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from RoleEvent>>.

    role_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from RoleEvent>>.

    old_role: typing.Optional[guilds.Role] = attrs.field()
    """The old role object.

    This will be [`None`][] if the role was missing from the cache.
    """
