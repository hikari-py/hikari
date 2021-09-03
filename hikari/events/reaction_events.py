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
"""Events that fire if messages are reacted to."""

from __future__ import annotations

__all__: typing.List[str] = [
    "ReactionEvent",
    "GuildReactionEvent",
    "DMReactionEvent",
    "ReactionAddEvent",
    "ReactionDeleteEvent",
    "ReactionDeleteEmojiEvent",
    "ReactionDeleteAllEvent",
    "GuildReactionAddEvent",
    "GuildReactionDeleteEvent",
    "GuildReactionDeleteEmojiEvent",
    "GuildReactionDeleteAllEvent",
    "DMReactionAddEvent",
    "DMReactionDeleteEvent",
    "DMReactionDeleteEmojiEvent",
    "DMReactionDeleteAllEvent",
]

import abc
import typing

import attr

from hikari import emojis
from hikari import intents
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import snowflakes
    from hikari import traits
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS, intents.Intents.DM_MESSAGE_REACTIONS)
class ReactionEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any message reaction event."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def channel_id(self) -> snowflakes.Snowflake:
        """ID of the channel that this event concerns.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the channel that this event concerns.
        """

    @property
    @abc.abstractmethod
    def message_id(self) -> snowflakes.Snowflake:
        """ID of the message that this event concerns.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the message that this event concerns.
        """


@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS)
class GuildReactionEvent(ReactionEvent, abc.ABC):
    """Event base for any reaction-bound event in guild messages."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflakes.Snowflake:
        """ID of the guild that this event concerns.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the guild that this event concerns.
        """


@base_events.requires_intents(intents.Intents.DM_MESSAGE_REACTIONS)
class DMReactionEvent(ReactionEvent, abc.ABC):
    """Event base for any reaction-bound event in private messages."""

    __slots__: typing.Sequence[str] = ()


@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS, intents.Intents.DM_MESSAGE_REACTIONS)
class ReactionAddEvent(ReactionEvent, abc.ABC):
    """Event base for any reaction that is added to a message."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def user_id(self) -> snowflakes.Snowflake:
        """ID of the user that added this reaction.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the user that added this reaction.
        """

    @property
    @abc.abstractmethod
    def emoji_name(self) -> typing.Union[emojis.UnicodeEmoji, str, None]:
        """Name of the emoji which was added if known.

        !!! note
            This will be `builtins.None` when the relevant custom emoji's data
            is not available (e.g. the emoji has been deleted).

        Returns
        -------
        typing.Union[hikari.emojis.UnicodeEmoji, builtins.str, builtins.None]
            Either the string name of the custom emoji which was added
            or the object of the `hikari.emojis.UnicodeEmoji` which was added.
        """

    @property
    @abc.abstractmethod
    def emoji_id(self) -> typing.Optional[snowflakes.Snowflake]:
        """ID of the emoji which was added if it is custom.

        Returns
        -------
        typing.Optional[hikari.snowflakes.Snowflake]
            ID of the emoji which was added if it was a custom emoji or
            `builtins.None`.
        """

    @property
    @abc.abstractmethod
    def is_animated(self) -> bool:
        """Whether the emoji which was added is animated.

        Returns
        -------
        builtins.bool
            Whether the emoji which was added is animated.
        """

    def is_for_emoji(self, emoji: typing.Union[emojis.Emoji, str], /) -> bool:
        """Get whether the reaction event is for a specific emoji.

        Parameters
        ----------
        emoji : typing.Union[hikari.emojis.Emoji, builtins.str]
            The emoji to check.

            Passing `builtins.str` here indicates a unicode emoji.

        Returns
        -------
        builtins.bool
            Whether the emoji is the one which was added.
        """
        return emoji.id == self.emoji_id if isinstance(emoji, emojis.CustomEmoji) else emoji == self.emoji_name


@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS, intents.Intents.DM_MESSAGE_REACTIONS)
class ReactionDeleteEvent(ReactionEvent, abc.ABC):
    """Event base for any single reaction that is removed from a message."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def user_id(self) -> snowflakes.Snowflake:
        """User ID for the user that added this reaction initially.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the user that removed this reaction.
        """

    @property
    @abc.abstractmethod
    def emoji_name(self) -> typing.Union[emojis.UnicodeEmoji, str, None]:
        """Name of the emoji which was removed.

        !!! note
            This will be `builtins.None` when the relevant custom emoji's data
            is not available (e.g. the emoji has been deleted).

        Returns
        -------
        typing.Union[hikari.emojis.UnicodeEmoji, builtins.str, builtins.None]
            Either the string name of the custom emoji which was removed
            or the object of the `hikari.emojis.UnicodeEmoji` which was removed.
        """

    @property
    @abc.abstractmethod
    def emoji_id(self) -> typing.Optional[snowflakes.Snowflake]:
        """ID of the emoji which was removed if it was custom.

        Returns
        -------
        typing.Optional[hikari.snowflakes.Snowflake]
            ID of the emoji which was removed if it was a custom emoji or
            `builtins.None`.
        """

    def is_for_emoji(self, emoji: typing.Union[emojis.Emoji, str], /) -> bool:
        """Get whether the reaction event is for a specific emoji.

        Parameters
        ----------
        emoji : typing.Union[hikari.emojis.Emoji, builtins.str]
            The emoji to check.

            Passing `builtins.str` here indicates a unicode emoji.

        Returns
        -------
        builtins.bool
            Whether the emoji is the one which was removed.
        """
        return emoji.id == self.emoji_id if isinstance(emoji, emojis.CustomEmoji) else emoji == self.emoji_name


@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS, intents.Intents.DM_MESSAGE_REACTIONS)
class ReactionDeleteAllEvent(ReactionEvent, abc.ABC):
    """Event base fired when all reactions are removed from a message."""

    __slots__: typing.Sequence[str] = ()


@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS, intents.Intents.DM_MESSAGE_REACTIONS)
class ReactionDeleteEmojiEvent(ReactionEvent, abc.ABC):
    """Event base fired when all reactions are removed for one emoji."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def emoji_name(self) -> typing.Union[emojis.UnicodeEmoji, str, None]:
        """Name of the emoji which was removed if known.

        !!! note
            This will be `builtins.None` when the relevant custom emoji's data
            is not available (e.g. the emoji has been deleted).

        Returns
        -------
        typing.Union[hikari.emojis.UnicodeEmoji, builtins.str, builtins.None]
            Either the string name of the custom emoji which was removed
            or the object of the `hikari.emojis.UnicodeEmoji` which was removed.
        """

    @property
    @abc.abstractmethod
    def emoji_id(self) -> typing.Optional[snowflakes.Snowflake]:
        """ID of the emoji which was removed if it was custom.

        Returns
        -------
        typing.Optional[hikari.snowflakes.Snowflake]
            ID of the emoji which was removed if it was a custom emoji or
            `builtins.None`.
        """

    def is_for_emoji(self, emoji: typing.Union[emojis.Emoji, str], /) -> bool:
        """Get whether the reaction event is for a specific emoji.

        Parameters
        ----------
        emoji : typing.Union[hikari.emojis.Emoji, builtins.str]
            The emoji to check.

            Passing `builtins.str` here indicates a unicode emoji.

        Returns
        -------
        builtins.bool
            Whether the emoji is the one which was removed.
        """
        return emoji.id == self.emoji_id if isinstance(emoji, emojis.CustomEmoji) else emoji == self.emoji_name


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS)
class GuildReactionAddEvent(GuildReactionEvent, ReactionAddEvent):
    """Event fired when a reaction is added to a guild message."""

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    member: guilds.Member = attr.field()
    """Member that added the reaction.

    Returns
    -------
    hikari.guilds.Member
        The member which added this reaction.
    """

    channel_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.

    emoji_name: typing.Union[str, emojis.UnicodeEmoji, None] = attr.field()
    # <<inherited docstring from ReactionAddEvent>>.

    emoji_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    # <<inherited docstring from ReactionAddEvent>>.

    is_animated: bool = attr.field()
    # <<inherited docstring from ReactionAddEvent>>.

    @property
    def app(self) -> traits.RESTAware:
        # <<inherited docstring from Event>>.
        return self.member.app

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildReactionEvent>>.
        return self.member.guild_id

    @property
    def user_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from ReactionAddEvent>>.
        return self.member.user.id


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS)
class GuildReactionDeleteEvent(GuildReactionEvent, ReactionDeleteEvent):
    """Event fired when a reaction is removed from a guild message."""

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    user_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionDeleteEvent>>.

    guild_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from GuildReactionEvent>>.

    channel_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.

    emoji_name: typing.Union[str, emojis.UnicodeEmoji, None] = attr.field()
    # <<inherited docstring from ReactionDeleteEvent>>.

    emoji_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    # <<inherited docstring from ReactionDeleteEvent>>.


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS)
class GuildReactionDeleteEmojiEvent(GuildReactionEvent, ReactionDeleteEmojiEvent):
    """Event fired when an emoji is removed from a guild message's reactions."""

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from GuildReactionEvent>>.

    channel_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.

    emoji_name: typing.Union[str, emojis.UnicodeEmoji, None] = attr.field()
    # <<inherited docstring from ReactionDeleteEmojiEvent>>.

    emoji_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    # <<inherited docstring from ReactionDeleteEmojiEvent>>.


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGE_REACTIONS)
class GuildReactionDeleteAllEvent(GuildReactionEvent, ReactionDeleteAllEvent):
    """Event fired when all of a guild message's reactions are removed."""

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    guild_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from GuildReactionEvent>>.

    channel_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.DM_MESSAGE_REACTIONS)
class DMReactionAddEvent(DMReactionEvent, ReactionAddEvent):
    """Event fired when a reaction is added to a private message."""

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    user_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionAddEvent>>.

    channel_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.

    emoji_name: typing.Union[str, emojis.UnicodeEmoji, None] = attr.field()
    # <<inherited docstring from ReactionAddEvent>>.

    emoji_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    # <<inherited docstring from ReactionAddEvent>>.

    is_animated: bool = attr.field()
    # <<inherited docstring from ReactionAddEvent>>.


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.DM_MESSAGE_REACTIONS)
class DMReactionDeleteEvent(DMReactionEvent, ReactionDeleteEvent):
    """Event fired when a reaction is removed from a private message."""

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    user_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionDeleteEvent>>.

    channel_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.

    emoji_name: typing.Union[str, emojis.UnicodeEmoji, None] = attr.field()
    # <<inherited docstring from ReactionDeleteEvent>>.

    emoji_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    # <<inherited docstring from ReactionDeleteEvent>>.


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.DM_MESSAGE_REACTIONS)
class DMReactionDeleteEmojiEvent(DMReactionEvent, ReactionDeleteEmojiEvent):
    """Event fired when an emoji is removed from a private message's reactions."""

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.

    emoji_name: typing.Union[str, emojis.UnicodeEmoji, None] = attr.field()
    # <<inherited docstring from ReactionDeleteEmojiEvent>>.

    emoji_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    # <<inherited docstring from ReactionDeleteEmojiEvent>>.


@attr_extensions.with_copy
@attr.define(kw_only=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.DM_MESSAGE_REACTIONS)
class DMReactionDeleteAllEvent(DMReactionEvent, ReactionDeleteAllEvent):
    """Event fired when all of a private message's reactions are removed."""

    app: traits.RESTAware = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.field(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.

    message_id: snowflakes.Snowflake = attr.field()
    # <<inherited docstring from ReactionEvent>>.
