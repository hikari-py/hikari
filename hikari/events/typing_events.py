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
"""Events fired when users begin typing in channels."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "TypingEvent",
    "GuildTypingEvent",
    "PrivateTypingEvent",
]

import abc
import typing

import attr

from hikari.events import base_events
from hikari.events import shard_events
from hikari.models import intents

if typing.TYPE_CHECKING:
    import datetime

    from hikari.api import shard as gateway_shard
    from hikari.models import channels
    from hikari.models import guilds
    from hikari.models import users
    from hikari.utilities import snowflake


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_TYPING, intents.Intent.PRIVATE_MESSAGE_TYPING)
class TypingEvent(shard_events.ShardEvent, abc.ABC):
    """Base event fired when a user begins typing in a channel."""

    @property
    @abc.abstractmethod
    def channel_id(self) -> snowflake.Snowflake:
        """ID of the channel that this event concerns.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The ID of the channel that this event concerns.
        """

    @property
    @abc.abstractmethod
    def user_id(self) -> snowflake.Snowflake:
        """ID of the user who triggered this typing event.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            ID of the user who is typing.
        """

    @property
    @abc.abstractmethod
    def timestamp(self) -> datetime.datetime:
        """Timestamp of when this typing event started.

        Returns
        -------
        datetime.datetime
            UTC timestamp of when the user started typing.
        """

    async def fetch_channel(self) -> channels.TextChannel:
        """Perform an API call to fetch an up-to-date image of this channel.

        Returns
        -------
        hikari.models.channels.TextChannel
            The channel.
        """
        return typing.cast("channels.TextChannel", await self.app.rest.fetch_channel(self.channel_id))

    async def fetch_user(self) -> users.User:
        """Perform an API call to fetch an up-to-date image of this user.

        Returns
        -------
        hikari.models.users.user
            The user.
        """
        return await self.app.rest.fetch_user(self.user_id)


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_TYPING)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class GuildTypingEvent(TypingEvent):
    """Event fired when a user starts typing in a guild channel."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from TypingEvent>>.

    user_id: snowflake.Snowflake = attr.ib(repr=True)
    # <<inherited docstring from TypingEvent>>.

    timestamp: datetime.datetime = attr.ib(repr=False)
    # <<inherited docstring from TypingEvent>>.

    guild_id: snowflake.Snowflake = attr.ib()
    """ID of the guild that this event relates to.

    Returns
    -------
    hikari.utilities.snowflake.Snowflake
        The ID of the guild that relates to this event.
    """

    member: guilds.Member = attr.ib(repr=False)
    """Member object of the user who triggered this typing event.

    Returns
    -------
    hikari.models.guilds.Member
        Member of the user who triggered this typing event.
    """

    if typing.TYPE_CHECKING:

        async def fetch_channel(self) -> channels.GuildTextChannel:
            ...

    async def fetch_member(self) -> guilds.Member:
        """Perform an API call to fetch an up-to-date image of this guild.

        Returns
        -------
        hikari.models.guilds.Member
            The member.
        """
        return await self.app.rest.fetch_member(self.guild_id, self.user_id)

    async def fetch_guild(self) -> guilds.Guild:
        """Perform an API call to fetch an up-to-date image of this guild.

        Returns
        -------
        hikari.models.guilds.Guild
            The guild.
        """
        return await self.app.rest.fetch_guild(self.guild_id)

    async def fetch_guild_preview(self) -> guilds.GuildPreview:
        """Perform an API call to fetch an up-to-date preview of this guild.

        Returns
        -------
        hikari.models.guilds.GuildPreview
            The guild.
        """
        return await self.app.rest.fetch_guild_preview(self.guild_id)


@base_events.requires_intents(intents.Intent.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class PrivateTypingEvent(TypingEvent):
    """Event fired when a user starts typing in a guild channel."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from TypingEvent>>.

    user_id: snowflake.Snowflake = attr.ib(repr=True)
    # <<inherited docstring from TypingEvent>>.

    timestamp: datetime.datetime = attr.ib(repr=False)
    # <<inherited docstring from TypingEvent>>.

    if typing.TYPE_CHECKING:

        async def fetch_channel(self) -> channels.PrivateTextChannel:
            ...
