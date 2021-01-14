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
"""Events that fire if messages are sent/updated/deleted."""

from __future__ import annotations

__all__: typing.List[str] = [
    "MessageEvent",
    "MessageCreateEvent",
    "MessageUpdateEvent",
    "MessageDeleteEvent",
    "GuildMessageCreateEvent",
    "GuildMessageUpdateEvent",
    "GuildMessageDeleteEvent",
    "DMMessageCreateEvent",
    "DMMessageUpdateEvent",
    "DMMessageDeleteEvent",
]

import abc
import typing

import attr

from hikari import channels
from hikari import intents
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import users
from hikari.events import base_events
from hikari.events import shard_events
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import embeds as embeds_
    from hikari import guilds
    from hikari import messages
    from hikari.api import shard as shard_


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.DM_MESSAGES, intents.Intents.GUILD_MESSAGES)
class MessageEvent(shard_events.ShardEvent, abc.ABC):
    """Any event that concerns manipulation of messages."""

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


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.DM_MESSAGES, intents.Intents.GUILD_MESSAGES)
class MessageCreateEvent(MessageEvent, abc.ABC):
    """Event that is fired when a message is created."""

    @property
    def author(self) -> users.User:
        """User that sent the message.

        Returns
        -------
        hikari.users.User
            The user that sent the message.
        """
        return self.message.author

    @property
    def author_id(self) -> snowflakes.Snowflake:
        """ID of the author of the message this event concerns.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the author.
        """
        return self.author.id

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from MessageEvent>>
        return self.message.channel_id

    @property
    def content(self) -> typing.Optional[str]:
        """Content of the message.

        Returns
        -------
        typing.Optional[builtins.str]
            The content of the message, if present. This may be `builtins.None`
            or an empty string (or any falsy value) if no content is present
            (e.g. if only an embed was sent).
        """
        return self.message.content

    @property
    def embeds(self) -> typing.Sequence[embeds_.Embed]:
        """Sequence of embeds in the message.

        Returns
        -------
        typing.Sequence[hikari.embeds.Embed]
            The embeds in the message.
        """
        return self.message.embeds

    @property
    def is_bot(self) -> bool:
        """Return `builtins.True` if the message is from a bot.

        Returns
        -------
        builtins.bool
            `builtins.True` if from a bot, or `builtins.False` otherwise.
        """
        return self.message.author.is_bot

    @property
    def is_human(self) -> bool:
        """Return `builtins.True` if the message was created by a human.

        Returns
        -------
        builtins.bool
            `builtins.True` if from a human user, or `builtins.False` otherwise.
        """
        # Not second-guessing some weird edge case will occur in the future with this,
        # so I am being safe rather than sorry.
        return not self.message.author.is_bot and self.message.webhook_id is None

    @property
    def is_webhook(self) -> bool:
        """Return `builtins.True` if the message was created by a webhook.

        Returns
        -------
        builtins.bool
            `builtins.True` if from a webhook, or `builtins.False` otherwise.
        """
        return self.message.webhook_id is not None

    @property
    @abc.abstractmethod
    def message(self) -> messages.Message:
        """Message that was sent in the event.

        Returns
        -------
        hikari.messages.Message
            The message object that was sent with this event.
        """

    @property
    def message_id(self) -> snowflakes.Snowflake:
        """ID of the message that this event concerns.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the message that this event concerns.
        """
        return self.message.id


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGES)
class GuildMessageCreateEvent(MessageCreateEvent):
    """Event that is fired when a message is created within a guild.

    This contains the full message in the internal `message` attribute.
    """

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>

    message: messages.Message = attr.ib()
    # <<inherited docstring from MessageCreateEvent>>

    shard: shard_.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>

    @property
    def author(self) -> guilds.Member:
        """Member object of the user that sent the message.

        Returns
        -------
        hikari.guilds.Member
            The member object of the user that sent the message.
        """
        member = self.message.member
        assert member is not None, "no member given for guild message create event!"
        return member

    @property
    def channel(self) -> typing.Union[None, channels.GuildTextChannel, channels.GuildNewsChannel]:
        """Channel that the message was sent in, if known.

        Returns
        -------
        typing.Union[builtins.None, hikari.channels.GuildTextChannel, hikari.channels.GuildNewsChannel]
            The channel that the message was sent in, if known and cached,
            otherwise, `builtins.None`.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        channel = self.app.cache.get_guild_channel(self.channel_id)
        assert channel is None or isinstance(
            channel, (channels.GuildNewsChannel, channels.GuildTextChannel)
        ), f"Cached channel ID is not a GuildNewsChannel or a GuildTextChannel, but a {type(channel).__name__}!"
        return channel

    @property
    def guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the cached guild that this event occurred in, if known.

        !!! note
            This will require the `GUILDS` intent to be specified on start-up
            in order to be known.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The guild that this event occurred in, if cached. Otherwise,
            `builtins.None` instead.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_guild(self.guild_id)

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        """ID of the guild that this event occurred in.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the guild that this event occurred in.
        """
        guild_id = self.message.guild_id
        # Always present on guild events
        assert isinstance(guild_id, snowflakes.Snowflake), "no guild_id attribute set"
        return guild_id


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.DM_MESSAGES)
class DMMessageCreateEvent(MessageCreateEvent):
    """Event that is fired when a message is created within a DM.

    This contains the full message in the internal `message` attribute.
    """

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>

    message: messages.Message = attr.ib()
    # <<inherited docstring from MessageCreateEvent>>

    shard: shard_.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.DM_MESSAGES, intents.Intents.GUILD_MESSAGES)
class MessageUpdateEvent(MessageEvent, abc.ABC):
    """Event that is fired when a message is updated.

    !!! note
        Less information will be available here than in the creation event
        due to Discord limitations.
    """

    @property
    def author(self) -> typing.Optional[users.User]:
        """User that sent the message.

        Returns
        -------
        typing.Optional[hikari.users.User]
            The user that sent the message.

            This will be `builtins.None` in some cases, such as when Discord
            updates a message with an embed for a URL preview.
        """
        return self.message.author

    @property
    def author_id(self) -> typing.Optional[snowflakes.Snowflake]:
        """ID of the author that triggered this event.

        Returns
        -------
        typing.Optional[hikari.snowflakes.Snowflake]
            The ID of the author that triggered this event concerns.

            This will be `builtins.None` in some cases, such as
            when Discord updates a message with an embed for a URL preview.
        """
        author = self.message.author
        return author.id if author is not None else None

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from MessageEvent>>.
        return self.message.channel_id

    @property
    def content(self) -> undefined.UndefinedNoneOr[str]:
        """Content of the message.

        Returns
        -------
        hikari.undefined.UndefinedNoneOr[builtins.str]
            The content of the message, if present. This may be `builtins.None`
            or an empty string (or any falsy value) if no content is present
            (e.g. if only an embed was sent). If not part of the update, then
            this will be `hikari.undefined.UNDEFINED` instead.
        """
        return self.message.content

    @property
    def embeds(self) -> undefined.UndefinedOr[typing.Sequence[embeds_.Embed]]:
        """Sequence of embeds in the message.

        Returns
        -------
        hikari.undefined.UndefinedOr[typing.Sequence[hikari.embeds.Embed]]
            The embeds in the message. If the embeds were not changed in this
            event, then this may instead be `hikari.undefined.UNDEFINED`.
        """
        return self.message.embeds

    @property
    def is_bot(self) -> typing.Optional[bool]:
        """Return `builtins.True` if the message is from a bot.

        Returns
        -------
        typing.Optional[builtins.bool]
            `builtins.True` if from a bot, or `builtins.False` otherwise.

            If the author is not known, due to the update event being caused
            by Discord adding an embed preview to accompany a URL, then this
            will return `builtins.None` instead.
        """
        if (author := self.message.author) is not None:
            return author.is_bot
        return None

    @property
    def is_human(self) -> typing.Optional[bool]:
        """Return `builtins.True` if the message was created by a human.

        Returns
        -------
        typing.Optional[builtins.bool]
            `builtins.True` if from a human user, or `builtins.False` otherwise.

            If the author is not known, due to the update event being caused
            by Discord adding an embed preview to accompany a URL, then this
            may return `builtins.None` instead.
        """
        # Not second-guessing some weird edge case will occur in the future with this,
        # so I am being safe rather than sorry.
        if self.message.webhook_id is not None:
            return False

        if (author := self.message.author) is not None:
            return not author.is_bot

        return None

    @property
    def is_webhook(self) -> bool:
        """Return `builtins.True` if the message was created by a webhook.

        Returns
        -------
        builtins.bool
            `builtins.True` if from a webhook, or `builtins.False` otherwise.
        """
        return self.message.webhook_id is not None

    @property
    @abc.abstractmethod
    def message(self) -> messages.PartialMessage:
        """Partial message that was sent in the event.

        Returns
        -------
        hikari.messages.PartialMessage
            The partial message object that was sent with this event.
        """

    @property
    def message_id(self) -> snowflakes.Snowflake:
        """ID of the message that this event concerns.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the message that this event concerns.
        """
        return self.message.id


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGES)
class GuildMessageUpdateEvent(MessageUpdateEvent):
    """Event that is fired when a message is updated in a guild.

    !!! note
        Less information will be available here than in the creation event
        due to Discord limitations.
    """

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>

    old_message: typing.Optional[messages.PartialMessage] = attr.ib()
    """The old message object.

    This will be `builtins.None` if the message missing from the cache.
    """

    message: messages.PartialMessage = attr.ib()
    # <<inherited docstring from MessageUpdateEvent>>

    shard: shard_.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>

    @property
    def author(self) -> typing.Optional[users.User]:
        """Member or user that sent the message.

        Returns
        -------
        typing.Union[builtins.None, hikari.users.User, hikari.guilds.Member]
            The user that sent the message. If the member is cached
            (the intents are enabled), then this will be the corresponding
            member object instead (which is a specialization of the
            user object you should otherwise expect).

            This will be `builtins.None` in some cases, such as when Discord
            updates a message with an embed for a URL preview.
        """
        member = self.message.member
        if member is not None:
            return member

        author = self.message.author

        if author is not None and isinstance(self.app, traits.CacheAware):
            member = self.app.cache.get_member(self.guild_id, author.id)

            if member is not None:
                return member

        return author

    @property
    def channel(self) -> typing.Union[None, channels.GuildTextChannel, channels.GuildNewsChannel]:
        """Channel that the message was sent in, if known.

        Returns
        -------
        typing.Union[builtins.None, hikari.channels.GuildTextChannel, hikari.channels.GuildNewsChannel]
            The channel that the message was sent in, if known and cached,
            otherwise, `builtins.None`.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        channel = self.app.cache.get_guild_channel(self.channel_id)
        assert channel is None or isinstance(
            channel, (channels.GuildNewsChannel, channels.GuildTextChannel)
        ), f"Cached channel ID is not a GuildNewsChannel or a GuildTextChannel, but a {type(channel).__name__}!"
        return channel

    @property
    def guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the cached guild that this event occurred in, if known.

        !!! note
            This will require the `GUILDS` intent to be specified on start-up
            in order to be known.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The guild that this event occurred in, if cached. Otherwise,
            `builtins.None` instead.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_guild(self.guild_id)

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        """ID of the guild that this event occurred in.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the guild that this event occurred in.
        """
        guild_id = self.message.guild_id
        # Always present on guild events
        assert isinstance(guild_id, snowflakes.Snowflake), f"expected guild_id, got {guild_id}"
        return guild_id


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.DM_MESSAGES)
class DMMessageUpdateEvent(MessageUpdateEvent):
    """Event that is fired when a message is updated in a DM.

    !!! note
        Less information will be available here than in the creation event
        due to Discord limitations.
    """

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>

    old_message: typing.Optional[messages.PartialMessage] = attr.ib()
    """The old message object.

    This will be `builtins.None` if the message missing from the cache.
    """

    message: messages.PartialMessage = attr.ib()
    # <<inherited docstring from MessageUpdateEvent>>

    shard: shard_.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>


@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGES, intents.Intents.DM_MESSAGES)
class MessageDeleteEvent(MessageEvent, abc.ABC):
    """Special event that is triggered when one or more messages get deleted.

    !!! note
        Due to Discord limitations, most message information is unavailable
        during deletion events.

    You can check if the message was in a singular deletion by checking the
    `is_bulk` attribute.
    """

    @property
    def channel(self) -> typing.Union[None, channels.GuildTextChannel, channels.GuildNewsChannel]:
        """Get the cached channel the messages were sent in, if known.

        Returns
        -------
        typing.Union[builtins.None, hikari.channels.GuildTextChannel, hikari.channels.GuildNewsChannel]
            The channel the messages were sent in, or `builtins.None` if not
            known/cached.

            This otherwise will always be a `hikari.channels.GuildTextChannel`
            if it is a normal message, or `hikari.channels.GuildNewsChannel` if
            sent in an announcement channel.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        channel = self.app.cache.get_guild_channel(self.channel_id)
        assert channel is None or isinstance(
            channel, (channels.GuildNewsChannel, channels.GuildTextChannel)
        ), f"Cached channel ID is not a GuildNewsChannel or a GuildTextChannel, but a {type(channel).__name__}!"
        return channel

    @property
    def message_id(self) -> snowflakes.Snowflake:
        """Get the ID of the first deleted message.

        This is contextually useful if you know this is not a bulk deletion
        event. For all other purposes, this is the same as running
        `next(iter(event.message_ids))`.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The first deleted message ID.
        """
        try:
            return next(iter(self.message_ids))
        except StopIteration:
            raise RuntimeError("No messages were sent in a bulk delete! Please shout at Discord to fix this!") from None

    @property
    @abc.abstractmethod
    def message_ids(self) -> typing.AbstractSet[snowflakes.Snowflake]:
        """Set of message IDs that were bulk deleted.

        Returns
        -------
        typing.AbstractSet[hikari.snowflakes.Snowflake]
            A sequence of message IDs that were bulk deleted.
        """

    @property
    @abc.abstractmethod
    def is_bulk(self) -> bool:
        """Flag that determines whether this was a bulk deletion or not.

        Returns
        -------
        builtins.bool
            `builtins.True` if this was a bulk deletion, or `builtins.False`
            if it was a regular message deletion.
        """


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGES)
class GuildMessageDeleteEvent(MessageDeleteEvent):
    """Event that is triggered if messages are deleted in a guild.

    !!! note
        Due to Discord limitations, most message information is unavailable
        during deletion events.

    This is triggered for singular message deletion, and bulk message
    deletion. You can check if the message was in a singular deletion by
    checking the `is_bulk` attribute.
    """

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>

    channel_id: snowflakes.Snowflake = attr.ib()
    # <<inherited docstring from MessageEvent>>

    guild_id: snowflakes.Snowflake = attr.ib()
    """ID of the guild that this event occurred in.

    Returns
    -------
    hikari.snowflakes.Snowflake
        The ID of the guild.
    """

    is_bulk: bool = attr.ib()
    # <<inherited docstring from MessageDeleteEvent>>

    message_ids: typing.AbstractSet[snowflakes.Snowflake] = attr.ib()
    # <<inherited docstring from MessageDeleteEvent>>

    shard: shard_.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>

    @property
    def guild(self) -> typing.Optional[guilds.GatewayGuild]:
        """Get the cached guild this event corresponds to, if known.

        !!! note
            You will need `hikari.intents.Intents.GUILDS` enabled to receive this
            information.

        Returns
        -------
        hikari.guilds.GatewayGuild
            The gateway guild that this event corresponds to, if known and
            cached.
        """
        if not isinstance(self.app, traits.CacheAware):
            return None

        return self.app.cache.get_guild(self.guild_id)


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.DM_MESSAGES)
class DMMessageDeleteEvent(MessageDeleteEvent):
    """Event that is triggered if messages are deleted in a DM.

    !!! note
        Due to Discord limitations, most message information is unavailable
        during deletion events.

    This is triggered for singular message deletion, and bulk message
    deletion, although the latter is not expected to occur in DMs.

    You can check if the message was in a singular deletion by checking the
    `is_bulk` attribute.
    """

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>

    channel_id: snowflakes.Snowflake = attr.ib()
    # <<inherited docstring from MessageEvent>>

    is_bulk: bool = attr.ib()
    # <<inherited docstring from MessageDeleteEvent>>

    message_ids: typing.AbstractSet[snowflakes.Snowflake] = attr.ib()
    # <<inherited docstring from MessageDeleteEvent>>

    shard: shard_.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>
