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
"""Events that fire if messages are reacted to."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = [
    "ReactionEvent",
    "GuildReactionEvent",
    "PrivateReactionEvent",
    "ReactionAddEvent",
    "ReactionDeleteEvent",
    "ReactionDeleteEmojiEvent",
    "ReactionDeleteAllEvent",
    "GuildReactionAddEvent",
    "GuildReactionDeleteEvent",
    "GuildReactionDeleteEmojiEvent",
    "GuildReactionDeleteAllEvent",
    "PrivateReactionAddEvent",
    "PrivateReactionDeleteEvent",
    "PrivateReactionDeleteEmojiEvent",
    "PrivateReactionDeleteAllEvent",
]

import abc
import typing

import attr

from hikari.events import base_events
from hikari.events import shard_events
from hikari.models import intents

if typing.TYPE_CHECKING:
    from hikari.api import shard as gateway_shard
    from hikari.models import emojis
    from hikari.models import guilds
    from hikari.utilities import snowflake


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.PRIVATE_MESSAGE_REACTIONS)
class ReactionEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any message reaction event."""

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
    def message_id(self) -> snowflake.Snowflake:
        """ID of the message that this event concerns.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The ID of the message that this event concerns.
        """


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS)
class GuildReactionEvent(ReactionEvent, abc.ABC):
    """Event base for any reaction-bound event in guild messages."""

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflake.Snowflake:
        """ID of the guild that this event concerns.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The ID of the guild that this event concerns.
        """


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.PRIVATE_MESSAGE_REACTIONS)
class PrivateReactionEvent(ReactionEvent, abc.ABC):
    """Event base for any reaction-bound event in private messages."""


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.PRIVATE_MESSAGE_REACTIONS)
class ReactionAddEvent(ReactionEvent, abc.ABC):
    """Event base for any reaction that is added to a message."""

    @property
    @abc.abstractmethod
    def user_id(self) -> snowflake.Snowflake:
        """ID of the user that added this reaction.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The ID of the user that added this reaction.
        """

    @property
    @abc.abstractmethod
    def emoji(self) -> emojis.Emoji:
        """Emoji that was added.

        Returns
        -------
        hikari.models.emojis.Emoji
            The `hikari.models.emojis.UnicodeEmoji` or
            `hikari.models.emojis.CustomEmoji` that was added to the message.
        """


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.PRIVATE_MESSAGE_REACTIONS)
class ReactionDeleteEvent(ReactionEvent, abc.ABC):
    """Event base for any single reaction that is removed from a message."""

    @property
    @abc.abstractmethod
    def user_id(self) -> snowflake.Snowflake:
        """User ID for the user that added this reaction initially.

        Returns
        -------
        hikari.utilities.snowflake.Snowflake
            The ID of the user that removed this reaction.
        """

    @property
    @abc.abstractmethod
    def emoji(self) -> emojis.Emoji:
        """Emoji that was removed.

        Returns
        -------
        hikari.models.emojis.Emoji
            The `hikari.models.emojis.UnicodeEmoji` or
            `hikari.models.emojis.CustomEmoji` that was removed from the
            message.
        """


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.PRIVATE_MESSAGE_REACTIONS)
class ReactionDeleteAllEvent(ReactionEvent, abc.ABC):
    """Event base fired when all reactions are removed from a message."""


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.PRIVATE_MESSAGE_REACTIONS)
class ReactionDeleteEmojiEvent(ReactionEvent, abc.ABC):
    """Event base fired when all reactions are removed for one emoji."""

    @property
    @abc.abstractmethod
    def emoji(self) -> emojis.Emoji:
        """Emoji that was removed.

        Returns
        -------
        hikari.models.emojis.Emoji
            The `hikari.models.emojis.UnicodeEmoji` or
            `hikari.models.emojis.CustomEmoji` that was removed from the
            message.
        """


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS)
class GuildReactionAddEvent(GuildReactionEvent, ReactionAddEvent):
    """Event fired when a reaction is added to a guild message."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    member: guilds.Member = attr.ib()
    """Member that added the reaction.

    Returns
    -------
    hikari.models.guilds.Member
        The member which added this reaction.
    """

    channel_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.

    emoji: emojis.Emoji = attr.ib()
    # <<inherited docstring from ReactionAddEvent>>.

    @property
    def guild_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from GuildReactionEvent>>.
        return self.member.guild_id

    @property
    def user_id(self) -> snowflake.Snowflake:
        # <<inherited docstring from ReactionAddEvent>>.
        return self.member.user.id


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS)
class GuildReactionDeleteEvent(GuildReactionEvent, ReactionDeleteEvent):
    """Event fired when a reaction is removed from a guild message."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    user_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionAddEvent>>.

    guild_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from GuildReactionEvent>>.

    channel_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.

    emoji: emojis.Emoji = attr.ib()
    # <<inherited docstring from ReactionDeleteEvent>>.


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS)
class GuildReactionDeleteEmojiEvent(GuildReactionEvent, ReactionDeleteEmojiEvent):
    """Event fired when an emoji is removed from a guild message's reactions."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from GuildReactionEvent>>.

    channel_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.

    emoji: emojis.Emoji = attr.ib()
    # <<inherited docstring from ReactionDeleteEmojiEvent>>.


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS)
class GuildReactionDeleteAllEvent(GuildReactionEvent, ReactionDeleteAllEvent):
    """Event fired when all of a guild message's reactions are removed."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from GuildReactionEvent>>.

    channel_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.PRIVATE_MESSAGE_REACTIONS)
class PrivateReactionAddEvent(PrivateReactionEvent, ReactionAddEvent):
    """Event fired when a reaction is added to a guild message."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    user_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionAddEvent>>.

    channel_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.

    emoji: emojis.Emoji = attr.ib()
    # <<inherited docstring from ReactionAddEvent>>.


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.PRIVATE_MESSAGE_REACTIONS)
class PrivateReactionDeleteEvent(PrivateReactionEvent, ReactionDeleteEvent):
    """Event fired when a reaction is removed from a private message."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    user_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionAddEvent>>.

    channel_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.

    emoji: emojis.Emoji = attr.ib()
    # <<inherited docstring from ReactionDeleteEvent>>.


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.PRIVATE_MESSAGE_REACTIONS)
class PrivateReactionDeleteEmojiEvent(PrivateReactionEvent, ReactionDeleteEmojiEvent):
    """Event fired when an emoji is removed from a private message's reactions."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.

    emoji: emojis.Emoji = attr.ib()
    # <<inherited docstring from ReactionDeleteEmojiEvent>>.


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intent.PRIVATE_MESSAGE_REACTIONS)
class PrivateReactionDeleteAllEvent(PrivateReactionEvent, ReactionDeleteAllEvent):
    """Event fired when all of a private message's reactions are removed."""

    shard: gateway_shard.IGatewayShard = attr.ib()
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflake.Snowflake = attr.ib()
    # <<inherited docstring from ReactionEvent>>.
