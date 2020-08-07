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
"""Events that fire when something occurs within a guild."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "GuildVisibilityEvent",
    "GuildAvailableEvent",
    "GuildUnavailableEvent",
    "GuildLeaveEvent",
    "GuildUpdateEvent",
    "BanEvent",
    "BanCreateEvent",
    "BanDeleteEvent",
    "EmojisUpdateEvent",
    "IntegrationsUpdateEvent",
    "PresenceUpdateEvent",
    "MemberChunkEvent",
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
    from hikari.models import channels as channels_
    from hikari.models import emojis as emojis_
    from hikari.models import guilds
    from hikari.models import presences as presences_
    from hikari.models import users
    from hikari.models import voices
    from hikari.utilities import snowflake


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(
    intents.Intent.GUILDS, intents.Intent.GUILD_BANS, intents.Intent.GUILD_EMOJIS, intents.Intent.GUILD_PRESENCES
)
class GuildEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any guild-bound event."""

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflake.Snowflake:
        """ID of the guild that this event relates to.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The ID of the guild that relates to this event.
        """


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILDS)
class GuildVisibilityEvent(GuildEvent, abc.ABC):
    """Event base for any event that changes the visibility of a guild.

    This includes when a guild becomes available after an outage, when a
    guild becomes available on startup, when a guild becomes unavailable due
    to an outage, when the user is kicked/banned/leaves a guild, or when
    the user joins a new guild.
    """


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILDS)
class GuildAvailableEvent(GuildVisibilityEvent):
    """Event fired when a guild becomes available.

    This will occur on startup, after outages, and if the bot joins a new guild.

    !!! note
        Some fields like `members` and `presences` are included here but not on
        the other `GuildUpdateEvent` and `GuildUnavailableEvent` guild visibility
        event models.
    """

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild: guilds.GatewayGuild = attr.ib()
    """Guild that just became available.

    Returns
    -------
    hikari.models.guilds.Guild
        The guild that relates to this event.
    """

    emojis: typing.Mapping[snowflake.Snowflake, emojis_.KnownCustomEmoji] = attr.ib(repr=False)
    """Mapping of emoji IDs to the emojis in the guild.

    Returns
    -------
    typing.Mapping[hikari.utilities.snowflake.Snowflake, hikari.models.emojis.KnownCustomEmoji]
        The emojis in the guild.
    """

    roles: typing.Mapping[snowflake.Snowflake, guilds.Role] = attr.ib(repr=False)
    """Mapping of role IDs to the roles in the guild.

    Returns
    -------
    typing.Mapping[hikari.utilities.snowflake.Snowflake, hikari.models.guilds.Role]
        The roles in the guild.
    """

    channels: typing.Mapping[snowflake.Snowflake, channels_.GuildChannel] = attr.ib(repr=False)
    """Mapping of channel IDs to the channels in the guild.

    Returns
    -------
    typing.Mapping[hikari.utilities.snowflake.Snowflake, hikari.models.channels.GuildChannel]
        The channels in the guild.
    """

    members: typing.Mapping[snowflake.Snowflake, guilds.Member] = attr.ib(repr=False)
    """Mapping of user IDs to the members in the guild.

    Returns
    -------
    typing.Mapping[hikari.utilities.snowflake.Snowflake, hikari.models.guilds.Member]
        The members in the guild.
    """

    presences: typing.Mapping[snowflake.Snowflake, presences_.MemberPresence] = attr.ib(repr=False)
    """Mapping of user IDs to the presences for the guild.

    Returns
    -------
    typing.Mapping[hikari.utilities.snowflake.Snowflake, hikari.models.presences.MemberPresence]
        The member presences in the guild.
    """

    voice_states: typing.Mapping[snowflake.Snowflake, voices.VoiceState] = attr.ib(repr=False)
    """Mapping of user IDs to the voice states active in this guild.

    Returns
    -------
    typing.Mapping[hikari.utilities.snowflake.Snowflake, hikari.models.voices.VoiceState]
        The voice states active in the guild.
    """

    @property
    def guild_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from GuildEvent>>.
        return self.guild.id


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILDS)
class GuildLeaveEvent(GuildVisibilityEvent):
    """Event fired when the bot is banned/kicked/leaves a guild.

    This will also fire if the guild was deleted.
    """

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from GuildEvent>>.


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILDS)
class GuildUnavailableEvent(GuildVisibilityEvent):
    """Event fired when a guild becomes unavailable because of an outage."""

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from GuildEvent>>.


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILDS)
class GuildUpdateEvent(GuildEvent):
    """Event fired when an existing guild is updated."""

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild: guilds.GatewayGuild = attr.ib()
    """Guild that was just updated.

    Returns
    -------
    hikari.models.guilds.Guild
        The guild that relates to this event.
    """

    emojis: typing.Mapping[snowflake.Snowflake, emojis_.KnownCustomEmoji] = attr.ib(repr=False)
    """Mapping of emoji IDs to the emojis in the guild.

    Returns
    -------
    typing.Mapping[hikari.utilities.snowflake.Snowflake, hikari.models.emojis.KnownCustomEmoji]
        The emojis in the guild.
    """

    roles: typing.Mapping[snowflake.Snowflake, guilds.Role] = attr.ib(repr=False)
    """Mapping of role IDs to the roles in the guild.

    Returns
    -------
    typing.Mapping[hikari.utilities.snowflake.Snowflake, hikari.models.guilds.Role]
        The roles in the guild.
    """

    @property
    def guild_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from GuildEvent>>.
        return self.guild.id


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_BANS)
class BanEvent(GuildEvent, abc.ABC):
    """Event base for any guild ban or unban."""

    @property
    @abc.abstractmethod
    def user(self) -> users.User:
        """User that this ban event affects.

        Returns
        -------
        hikari.models.users.User
            The user that this event concerns.
        """


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_BANS)
class BanCreateEvent(BanEvent):
    """Event that is fired when a user is banned from a guild."""

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from GuildEvent>>.

    user: users.User = attr.ib()
    # <<inherited docstring from BanEvent>>.


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_BANS)
class BanDeleteEvent(BanEvent):
    """Event that is fired when a user is unbanned from a guild."""

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from GuildEvent>>.

    user: users.User = attr.ib()
    # <<inherited docstring from BanEvent>>.


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_EMOJIS)
class EmojisUpdateEvent(GuildEvent):
    """Event that is fired when the emojis in a guild are updated."""

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from GuildEvent>>.

    emojis: typing.Sequence[emojis_.KnownCustomEmoji] = attr.ib()
    """Sequence of all emojis in this guild.

    Returns
    -------
    typing.Sequence[emojis_.KnownCustomEmoji]
        All emojis in the guild.
    """


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_EMOJIS)
class IntegrationsUpdateEvent(GuildEvent):
    """Event that is fired when the integrations in a guild are changed.

    This may occur when integrations are created, updated, or deleted.

    !!! note
        This event is similar to
        `hikari.events.channel_events.WebhookUpdateEvent` in that Discord
        does not provide any information on what was actually changed, nor
        how it was changed. The only way you will be able to determine this is
        to keep a cache of this information manually up to date by fetching
        it using REST API calls. This is a limitation of Discord's design.
        We agree that it is not overly helpful to you.
    """

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ShardEvent>>.


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_PRESENCES)
class PresenceUpdateEvent(shard_events.ShardEvent):
    """Event fired when a user in a guild updates their presence in a guild.

    Sent when a guild member changes their presence in a specific guild.

    If the user is changed (e.g. new username), then this may fire many times
    (once for every guild the bot is part of). This is a limitation of how
    Discord implements their event system, unfortunately.

    Furthermore, if the target user is a bot and the bot only updates their
    presence on specific shards, this will only fire for the corresponding
    shards that saw the presence update.
    """

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    presence: presences_.MemberPresence = attr.ib()
    """Member presence.

    Returns
    -------
    hikari.models.presences.MemberPresence
        Presence for the user in this guild.
    """

    user: typing.Optional[users.PartialUser] = attr.ib()
    """User that was updated.

    This is a partial user object that only contains the fields that were
    updated on the user profile.

    Will be `builtins.None` if the user itself did not change.
    This is always the case if the user only updated their member
    representation and did not change their user profile directly.

    Returns
    -------
    hikari.models.users.PartialUser or builtins.None
        The partial user containing the updated fields.
    """

    @property
    def user_id(self) -> snowflake.Snowflake:
        """User ID of the user that updated their presence.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            ID of the user the event concerns.
        """
        return self.presence.user_id

    @property
    def guild_id(self) -> snowflake.Snowflake:
        """Guild ID that the presence was updated in.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            ID of the guild the event occurred in.
        """
        return self.presence.guild_id


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class MemberChunkEvent(shard_events.ShardEvent):
    """Used to represent the response to Guild Request Members."""

    shard: gateway_shard.IGatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<docstring inherited from ShardEvent>>.

    guild_id: snowflake.Snowflake = attr.ib(repr=True)
    # <<docstring inherited from ShardEvent>>.

    members: typing.Mapping[snowflake.Snowflake, guilds.Member] = attr.ib(repr=False)
    """Mapping of user IDs to the objects of the members in this chunk.

    Returns
    -------
    typing.Mapping[hikari.utilities.snowflake.Snowflake, hikari.models.guilds.Member]
        Mapping of user IDs to corresponding member objects.
    """

    index: int = attr.ib(repr=True)
    """Zero-indexed position of this within the queued up chunks for this request.

    Returns
    -------
    builtins.int
        The sequence index for this chunk.
    """

    count: int = attr.ib(repr=True)
    """Total number of expected chunks for the request this is associated with.

    Returns
    -------
    builtins.int
        Total number of chunks to be expected.
    """

    not_found: typing.Sequence[snowflake.Snowflake] = attr.ib(repr=True)
    """Sequence of the snowflakes that were not found while making this request.

    This is only applicable when user IDs are specified while making the
    member request the chunk is associated with.

    Returns
    -------
    typing.Sequence[hikari.utilities.snowflake.Snowflake]
        Sequence of user IDs that were not found.
    """

    presences: typing.Mapping[snowflake.Snowflake, presences_.MemberPresence] = attr.ib(repr=False)
    """Mapping of user IDs to found member presence objects.

    This will be empty if no presences are found or `presences` is not passed as
    `True` while requesting the member chunks.

    Returns
    -------
    typing.Mapping[hikari.utilities.snowflake.Snowflake, hikari.models.presences.MemberPresence]
        Mapping of user IDs to corresponding presences.
    """

    nonce: typing.Optional[str] = attr.ib(repr=True)
    """String nonce used to identify the request member chunks are associated with.

    This is the nonce value passed while requesting member chunks.

    Returns
    -------
    builtins.str or builtins.None
        The request nonce if specified, or `builtins.None` otherwise.
    """
