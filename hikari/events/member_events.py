# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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
"""Events concerning manipulation of members within guilds."""
from __future__ import annotations

__all__: typing.List[str] = [
    "MemberEvent",
    "MemberCreateEvent",
    "MemberUpdateEvent",
    "MemberDeleteEvent",
]

import abc
import typing

import attr

from hikari import intents
from hikari import traits
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import snowflakes
    from hikari import users
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(intents.Intents.GUILD_MEMBERS)
class MemberEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any events that concern guild members."""

    __slots__: typing.Sequence[str] = ()

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.user.app

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflakes.Snowflake:
        """ID of the guild that this event relates to.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the guild that relates to this event.
        """

    @property
    @abc.abstractmethod
    def user(self) -> users.User:
        """User object for the member this event concerns.

        Returns
        -------
        hikari.users.User
            User object for the member this event concerns.
        """

    @property
    def user_id(self) -> snowflakes.Snowflake:
        """ID of the user that this event concerns.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the user that this event relates to.
        """
        return self.user.id

    def get_guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the cached view of the guild this member event occurred in.

        If the guild itself is not cached, this will return `builtins.None`.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The guild that this event occurred in, if known, else
            `builtins.None`.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_available_guild(self.guild_id) or self.app.cache.get_unavailable_guild(self.guild_id)


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MEMBERS)
class MemberCreateEvent(MemberEvent):
    """Event that is fired when a member joins a guild."""

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    member: guilds.Member = attr.field()
    """Member object for the member that joined the guild.

    Returns
    -------
    hikari.guilds.Member
        The member object for the member who just joined.
    """

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from MemberEvent>>.
        return self.member.guild_id

    @property
    def user(self) -> users.User:
        # <<inherited docstring from MemberEvent>>.
        return self.member.user


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MEMBERS)
class MemberUpdateEvent(MemberEvent):
    """Event that is fired when a member is updated in a guild.

    This may occur if roles are amended, or if the nickname is changed.
    """

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    old_member: typing.Optional[guilds.Member] = attr.field()
    """The old member object.

    This will be `builtins.None` if the member missing from the cache.
    """

    member: guilds.Member = attr.field()
    """Member object for the member that was updated.

    Returns
    -------
    hikari.guilds.Member
        The member object for the member that was updated.
    """

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from MemberEvent>>.
        return self.member.guild_id

    @property
    def user(self) -> users.User:
        # <<inherited docstring from MemberEvent>>.
        return self.member.user


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MEMBERS)
class MemberDeleteEvent(MemberEvent):
    """Event fired when a member is kicked from or leaves a guild."""

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from MemberEvent>>.

    user: users.User = attr.field()
    # <<inherited docstring from MemberEvent>>.

    old_member: typing.Optional[guilds.Member] = attr.field()
    """The old member object.

    This will be `builtins.None` if the member was missing from the cache.
    """
