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
"""Events that fire when something occurs within a guild."""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "AuditLogEntryCreateEvent",
    "GuildEvent",
    "GuildVisibilityEvent",
    "GuildAvailableEvent",
    "GuildJoinEvent",
    "GuildUnavailableEvent",
    "GuildLeaveEvent",
    "GuildUpdateEvent",
    "BanEvent",
    "BanCreateEvent",
    "BanDeleteEvent",
    "EmojisUpdateEvent",
    "StickersUpdateEvent",
    "IntegrationEvent",
    "IntegrationCreateEvent",
    "IntegrationDeleteEvent",
    "IntegrationUpdateEvent",
    "PresenceUpdateEvent",
)

import abc
import typing

import attrs

from hikari import intents
from hikari import traits
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import attrs_extensions

if typing.TYPE_CHECKING:
    from hikari import audit_logs
    from hikari import channels as channels_
    from hikari import emojis as emojis_
    from hikari import guilds
    from hikari import presences as presences_
    from hikari import snowflakes
    from hikari import stickers as stickers_
    from hikari import users
    from hikari import voices
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(
    intents.Intents.GUILDS,
    intents.Intents.GUILD_MODERATION,
    intents.Intents.GUILD_EMOJIS,
    intents.Intents.GUILD_PRESENCES,
)
class GuildEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any guild-bound event."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflakes.Snowflake:
        """ID of the guild that this event relates to."""

    async def fetch_guild(self) -> guilds.RESTGuild:
        """Perform an API call to get the guild that this event relates to.

        Returns
        -------
        hikari.guilds.RESTGuild
            The guild this event occurred in.
        """
        return await self.app.rest.fetch_guild(self.guild_id)

    async def fetch_guild_preview(self) -> guilds.GuildPreview:
        """Perform an API call to get the preview of the event's guild.

        Returns
        -------
        hikari.guilds.GuildPreview
            The preview of the guild this event occurred in.
        """
        return await self.app.rest.fetch_guild_preview(self.guild_id)

    def get_guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the cached guild that this event relates to, if known.

        If not known, this will return [`None`][] instead.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The guild this event relates to, or [`None`][] if not known.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_available_guild(self.guild_id) or self.app.cache.get_unavailable_guild(self.guild_id)


@base_events.requires_intents(intents.Intents.GUILDS)
class GuildVisibilityEvent(GuildEvent, abc.ABC):
    """Event base for any event that changes the visibility of a guild.

    This includes when a guild becomes available after an outage, when a
    guild becomes available on startup, when a guild becomes unavailable due
    to an outage, when the user is kicked/banned/leaves a guild, or when
    the user joins a new guild.
    """

    __slots__: typing.Sequence[str] = ()


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILDS)
class GuildAvailableEvent(GuildVisibilityEvent):
    """Event fired when a guild becomes available.

    This will occur on startup or after outages.

    !!! note
        Some fields like `members` and `presences` are included here but not on
        the other [`hikari.events.guild_events.GuildUpdateEvent`][] and
        [`hikari.events.guild_events.GuildUnavailableEvent`][] guild visibility event models.
    """

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild: guilds.GatewayGuild = attrs.field()
    """Guild that just became available."""

    emojis: typing.Mapping[snowflakes.Snowflake, emojis_.KnownCustomEmoji] = attrs.field(repr=False)
    """Mapping of emoji IDs to the emojis in the guild."""

    stickers: typing.Mapping[snowflakes.Snowflake, stickers_.GuildSticker] = attrs.field(repr=False)
    """Mapping of sticker IDs to the stickers in the guild."""

    roles: typing.Mapping[snowflakes.Snowflake, guilds.Role] = attrs.field(repr=False)
    """Mapping of role IDs to the roles in the guild."""

    channels: typing.Mapping[snowflakes.Snowflake, channels_.PermissibleGuildChannel] = attrs.field(repr=False)
    """Mapping of channel IDs to the channels in the guild."""

    threads: typing.Mapping[snowflakes.Snowflake, channels_.GuildThreadChannel] = attrs.field(repr=False)
    """Mapping of channel IDs to the threads in the guild."""

    members: typing.Mapping[snowflakes.Snowflake, guilds.Member] = attrs.field(repr=False)
    """Mapping of user IDs to the members in the guild."""

    presences: typing.Mapping[snowflakes.Snowflake, presences_.MemberPresence] = attrs.field(repr=False)
    """Mapping of user IDs to the presences for the guild."""

    voice_states: typing.Mapping[snowflakes.Snowflake, voices.VoiceState] = attrs.field(repr=False)
    """Mapping of user IDs to the voice states active in this guild."""

    chunk_nonce: typing.Optional[str] = attrs.field(repr=False, default=None)
    """Nonce used to request the member chunks for this guild.

    This will be [`None`][] if no chunks were requested.

    !!! note
        This is a synthetic field.
    """

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.guild.app

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildEvent>>.
        return self.guild.id


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILDS)
class GuildJoinEvent(GuildVisibilityEvent):
    """Event fired when the bot joins a new guild.

    !!! note
        Some fields like `members` and `presences` are included here but not on
        the other [`hikari.events.guild_events.GuildUpdateEvent`][]
        and [`hikari.events.guild_events.GuildUnavailableEvent`][] guild visibility event models.
    """

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild: guilds.GatewayGuild = attrs.field()
    """The guild the bot just joined."""

    emojis: typing.Mapping[snowflakes.Snowflake, emojis_.KnownCustomEmoji] = attrs.field(repr=False)
    """Mapping of emoji IDs to the emojis in the guild."""

    stickers: typing.Mapping[snowflakes.Snowflake, stickers_.GuildSticker] = attrs.field(repr=False)
    """Mapping of sticker IDs to the stickers in the guild."""

    roles: typing.Mapping[snowflakes.Snowflake, guilds.Role] = attrs.field(repr=False)
    """Mapping of role IDs to the roles in the guild."""

    channels: typing.Mapping[snowflakes.Snowflake, channels_.PermissibleGuildChannel] = attrs.field(repr=False)
    """Mapping of channel IDs to the channels in the guild."""

    threads: typing.Mapping[snowflakes.Snowflake, channels_.GuildThreadChannel] = attrs.field(repr=False)
    """Mapping of channel IDs to the threads in the guild."""

    members: typing.Mapping[snowflakes.Snowflake, guilds.Member] = attrs.field(repr=False)
    """Mapping of user IDs to the members in the guild."""

    presences: typing.Mapping[snowflakes.Snowflake, presences_.MemberPresence] = attrs.field(repr=False)
    """Mapping of user IDs to the presences for the guild."""

    voice_states: typing.Mapping[snowflakes.Snowflake, voices.VoiceState] = attrs.field(repr=False)
    """Mapping of user IDs to the voice states active in this guild."""

    chunk_nonce: typing.Optional[str] = attrs.field(repr=False, default=None)
    """Nonce used to request the member chunks for this guild.

    This will be [`None`][] if no chunks were requested.

    !!! note
        This is a synthetic field.
    """

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.guild.app

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildEvent>>.
        return self.guild.id


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILDS)
class GuildLeaveEvent(GuildVisibilityEvent):
    """Event fired when the bot is banned/kicked/leaves a guild.

    This will also fire if the guild was deleted.
    """

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from GuildEvent>>.

    old_guild: typing.Optional[guilds.GatewayGuild] = attrs.field()
    """The old guild object.

    This will be [`None`][] if the guild missing from the cache.
    """

    if typing.TYPE_CHECKING:
        # This should always fail.
        async def fetch_guild(self) -> typing.NoReturn: ...


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILDS)
class GuildUnavailableEvent(GuildVisibilityEvent):
    """Event fired when a guild becomes unavailable because of an outage."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from GuildEvent>>.


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILDS)
class GuildUpdateEvent(GuildEvent):
    """Event fired when an existing guild is updated."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    old_guild: typing.Optional[guilds.GatewayGuild] = attrs.field()
    """The old guild object.

    This will be [`None`][] if the guild missing from the cache.
    """

    guild: guilds.GatewayGuild = attrs.field()
    """Guild that was just updated."""

    emojis: typing.Mapping[snowflakes.Snowflake, emojis_.KnownCustomEmoji] = attrs.field(repr=False)
    """Mapping of emoji IDs to the emojis in the guild."""

    stickers: typing.Mapping[snowflakes.Snowflake, stickers_.GuildSticker] = attrs.field(repr=False)
    """Mapping of sticker IDs to the stickers in the guild."""

    roles: typing.Mapping[snowflakes.Snowflake, guilds.Role] = attrs.field(repr=False)
    """Mapping of role IDs to the roles in the guild."""

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.guild.app

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildEvent>>.
        return self.guild.id


@base_events.requires_intents(intents.Intents.GUILD_MODERATION)
class BanEvent(GuildEvent, abc.ABC):
    """Event base for any guild ban or unban."""

    __slots__: typing.Sequence[str] = ()

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.user.app

    @property
    @abc.abstractmethod
    def user(self) -> users.User:
        """User that this ban event affects."""

    @property
    def user_id(self) -> snowflakes.Snowflake:
        """User ID of the user that got banned."""
        return self.user.id

    async def fetch_user(self) -> users.User:
        """Perform an API call to fetch the user this ban event affects.

        Returns
        -------
        hikari.users.User
            The user affected by this event.
        """
        return await self.app.rest.fetch_user(self.user)


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MODERATION)
class BanCreateEvent(BanEvent):
    """Event that is fired when a user is banned from a guild."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from GuildEvent>>.

    user: users.User = attrs.field()
    # <<inherited docstring from BanEvent>>.

    async def fetch_ban(self) -> guilds.GuildBan:
        """Perform an API call to fetch the details about this ban.

        This will include the optionally defined audit log reason for the
        ban.

        Returns
        -------
        hikari.guilds.GuildBan
            The ban details.
        """
        return await self.app.rest.fetch_ban(self.guild_id, self.user)


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MODERATION)
class BanDeleteEvent(BanEvent):
    """Event that is fired when a user is unbanned from a guild."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from GuildEvent>>.

    user: users.User = attrs.field()
    # <<inherited docstring from BanEvent>>.


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_EMOJIS)
class EmojisUpdateEvent(GuildEvent):
    """Event that is fired when the emojis in a guild are updated."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from GuildEvent>>.

    old_emojis: typing.Optional[typing.Sequence[emojis_.KnownCustomEmoji]] = attrs.field()
    """Sequence of all old emojis in this guild.

    This will be [`None`][] if it's missing from the cache.
    """

    emojis: typing.Sequence[emojis_.KnownCustomEmoji] = attrs.field()
    """Sequence of all emojis in this guild."""

    async def fetch_emojis(self) -> typing.Sequence[emojis_.KnownCustomEmoji]:
        """Perform an API call to retrieve an up-to-date view of the emojis.

        Returns
        -------
        typing.Sequence[hikari.emojis.KnownCustomEmoji]
            All emojis in the guild.
        """
        return await self.app.rest.fetch_guild_emojis(self.guild_id)


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_EMOJIS)
class StickersUpdateEvent(GuildEvent):
    """Event that is fired when the emojis in a guild are updated."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from GuildEvent>>.

    old_stickers: typing.Optional[typing.Sequence[stickers_.GuildSticker]] = attrs.field()
    """Sequence of all old stickers in this guild.

    This will be [`None`][] if it's missing from the cache.
    """

    stickers: typing.Sequence[stickers_.GuildSticker] = attrs.field()
    """Sequence of all stickers in this guild."""

    async def fetch_stickers(self) -> typing.Sequence[stickers_.GuildSticker]:
        """Perform an API call to retrieve an up-to-date view of the emojis.

        Returns
        -------
        typing.Sequence[hikari.stickers.GuildSticker]
            All emojis in the guild.
        """
        return await self.app.rest.fetch_guild_stickers(self.guild_id)


@base_events.requires_intents(intents.Intents.GUILD_INTEGRATIONS)
class IntegrationEvent(GuildEvent, abc.ABC):
    """Event base for any integration related events."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def application_id(self) -> typing.Optional[snowflakes.Snowflake]:
        """ID of Discord bot application this integration is connected to."""

    @property
    @abc.abstractmethod
    def id(self) -> snowflakes.Snowflake:
        """ID of the integration."""

    async def fetch_integrations(self) -> typing.Sequence[guilds.Integration]:
        """Perform an API call to fetch some number of guild integrations.

        !!! warning
            The results of this are not clearly defined by Discord. The current
            behaviour appears to be that only the first 50 integrations actually
            get returned. Discord have made it clear that they are not willing
            to fix this in
            <https://github.com/discord/discord-api-docs/issues/1990>.

        Returns
        -------
        typing.Sequence[hikari.guilds.Integration]
            Some possibly random subset of the integrations in a guild,
            probably.
        """
        return await self.app.rest.fetch_integrations(self.guild_id)


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_INTEGRATIONS)
class IntegrationCreateEvent(IntegrationEvent):
    """Event that is fired when an integration is created in a guild."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    integration: guilds.Integration = attrs.field()
    """Integration that was created."""

    @property
    def application_id(self) -> typing.Optional[snowflakes.Snowflake]:
        # <<inherited docstring from IntegrationEvent>>.
        return self.integration.application.id if self.integration.application else None

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ShardEvent>>.
        return self.integration.guild_id

    @property
    def id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from IntegrationEvent>>
        return self.integration.id


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_INTEGRATIONS)
class IntegrationDeleteEvent(IntegrationEvent):
    """Event that is fired when an integration is deleted in a guild."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    application_id: typing.Optional[snowflakes.Snowflake] = attrs.field()
    # <<inherited docstring from IntegrationEvent>>.

    guild_id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from ShardEvent>>.

    id: snowflakes.Snowflake = attrs.field()
    # <<inherited docstring from IntegrationEvent>>


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_INTEGRATIONS)
class IntegrationUpdateEvent(IntegrationEvent):
    """Event that is fired when an integration is updated in a guild."""

    app: traits.RESTAware = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    integration: guilds.Integration = attrs.field()
    """Integration that was updated."""

    @property
    def application_id(self) -> typing.Optional[snowflakes.Snowflake]:
        # <<inherited docstring from IntegrationEvent>>.
        return self.integration.application.id if self.integration.application else None

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildEvent>>.
        return self.integration.guild_id

    @property
    def id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from IntegrationEvent>>
        return self.integration.id


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_PRESENCES)
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

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    old_presence: typing.Optional[presences_.MemberPresence] = attrs.field()
    """The old member presence object.

    This will be [`None`][] if the member presence missing from the cache.
    """

    presence: presences_.MemberPresence = attrs.field()
    """Member presence."""

    user: typing.Optional[users.PartialUser] = attrs.field()
    """User that was updated.

    This is a partial user object that only contains the fields that were
    updated on the user profile.

    Will be [`None`][] if the user itself did not change.
    This is always the case if the user only updated their member
    representation and did not change their user profile directly.
    """

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.presence.app

    @property
    def user_id(self) -> snowflakes.Snowflake:
        """User ID of the user that updated their presence."""
        return self.presence.user_id

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        """Guild ID that the presence was updated in."""
        return self.presence.guild_id

    def get_user(self) -> typing.Optional[users.User]:
        """Get the full cached user, if it is available.

        Returns
        -------
        typing.Optional[hikari.users.User]
            The full cached user, or [`None`][] if not cached.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_user(self.user_id)

    async def fetch_user(self) -> users.User:
        """Perform an API call to fetch the user this event concerns.

        Returns
        -------
        hikari.users.User
            The user affected by this event.
        """
        return await self.app.rest.fetch_user(self.user_id)


@attrs_extensions.with_copy
@attrs.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MODERATION)
class AuditLogEntryCreateEvent(GuildEvent):
    """Event sent when a guild audit log entry was created."""

    shard: gateway_shard.GatewayShard = attrs.field(metadata={attrs_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    entry: audit_logs.AuditLogEntry = attrs.field()
    """The created entry."""

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.entry.app

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildEvent>>.
        return self.entry.guild_id
