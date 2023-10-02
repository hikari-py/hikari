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
"""Application and entities that are used to describe Stage instances on Discord."""
from __future__ import annotations

__all__: typing.List[str] = ["StagePrivacyLevel", "StageInstance"]

import typing

import attr

from hikari import channels
from hikari import scheduled_events
from hikari import snowflakes
from hikari import undefined
from hikari.internal import attrs_extensions
from hikari.internal import enums

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import traits


@typing.final
class StagePrivacyLevel(int, enums.Enum):
    """The privacy level of a Stage instance."""

    PUBLIC = 1
    """The Stage instance is visible publicly. (Deprecated)"""

    GUILD = 2
    """The Stage instance is only visible to the guild members"""


@attr.define(hash=True, kw_only=True, weakref_slot=False)
class StageInstance(snowflakes.Unique):
    """Represents a Stage instance."""

    id: snowflakes.Snowflake = attr.field(eq=False, hash=False, repr=True)
    """ID of the Stage instance."""

    app: traits.RESTAware = attr.field(
        repr=False, eq=False, hash=False, metadata={attrs_extensions.SKIP_DEEP_COPY: True}
    )
    """The client application that models may use for procedures."""

    channel_id: snowflakes.Snowflake = attr.field(hash=True, repr=False)
    """The channel ID of the Stage instance."""

    guild_id: snowflakes.Snowflake = attr.field(hash=True, repr=False)
    """The guild ID of the Stage instance."""

    topic: str = attr.field(eq=False, hash=False, repr=False)
    """The topic of the Stage instance."""

    privacy_level: typing.Union[StagePrivacyLevel, int] = attr.field(eq=False, hash=False, repr=False)
    """The privacy level of the Stage instance."""

    discoverable_disabled: bool = attr.field(eq=False, hash=False, repr=False)
    """Whether or not Stage discovery is disabled."""

    guild_scheduled_event_id: undefined.UndefinedOr[
        snowflakes.SnowflakeishOr[scheduled_events.ScheduledEvent]
    ] = attr.field(eq=False, hash=False, repr=False)
    "The ID of the scheduled event for this Stage instance, if it exists."

    def get_channel(self) -> typing.Optional[channels.GuildStageChannel]:
        """Return the guild stage channel where this stage instance was created.

        This will be empty if the channels are missing from the cache.

        Returns
        -------
        hikari.channels.GuildStageChannel
            The guild stage channel where this stage instance was created.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        channel = self.app.cache.get_guild_channel(self.channel_id)
        assert isinstance(channel, channels.GuildStageChannel)

        return channel

    async def fetch_channel(self) -> channels.GuildStageChannel:
        """Fetch the stage channel where this stage instance was created.

        Returns
        -------
        hikari.channels.GuildStageChannel
            The stage channel where this stage instance was created.

        Raises
        ------
        hikari.errors.BadRequestError
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.ForbiddenError
            If you don't have access to the channel this message belongs to.
        hikari.errors.NotFoundError
            If the channel this message was created in does not exist.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        channel = await self.app.rest.fetch_channel(self.channel_id)
        assert isinstance(channel, channels.GuildStageChannel)

        return channel

    def get_guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the cached guild that this Stage Instance relates to, if known.

        If not known, this will return `builtins.None` instead.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The guild this event relates to, or `builtins.None` if not known.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None
        return self.app.cache.get_guild(self.guild_id)

    async def fetch_guild(self) -> guilds.RESTGuild:
        """Fetch the guild linked to this Stage Instance.

        Returns
        -------
        hikari.guilds.RESTGuild
            The guild linked to this Stage Instance

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        return await self.app.rest.fetch_guild(self.guild_id)

    async def fetch_scheduled_event(self) -> typing.Optional[scheduled_events.ScheduledEvent]:
        """Fetch the scheduled event for this Stage Instance.

        Returns
        -------
        typing.Optional[hikari.scheduled_events.ScheduledEvent]
            The scheduled event for this Stage Instance, if it exists.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
        if self.guild_scheduled_event_id is undefined.UNDEFINED:
            return None

        return await self.app.rest.fetch_scheduled_event(self.guild_id, self.guild_scheduled_event_id)
