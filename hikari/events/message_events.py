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
"""Events that fire if messages are sent/updated/deleted."""

from __future__ import annotations

__all__: typing.List[str] = [
    "MessagesEvent",
    "MessageEvent",
    "GuildMessageEvent",
    "PrivateMessageEvent",
    "MessageCreateEvent",
    "GuildMessageCreateEvent",
    "PrivateMessageCreateEvent",
    "MessageUpdateEvent",
    "GuildMessageUpdateEvent",
    "PrivateMessageUpdateEvent",
    "MessageDeleteEvent",
    "GuildMessageDeleteEvent",
    "PrivateMessageDeleteEvent",
    "MessageBulkDeleteEvent",
    "GuildMessageBulkDeleteEvent",
]

import abc
import typing

import attr

from hikari import channels
from hikari import guilds
from hikari import intents
from hikari import snowflakes
from hikari import undefined
from hikari import users
from hikari.events import base_events
from hikari.events import shard_events
from hikari.utilities import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import messages
    from hikari import traits
    from hikari.api import shard as gateway_shard


@base_events.requires_intents(intents.Intents.GUILD_MESSAGES, intents.Intents.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class MessagesEvent(shard_events.ShardEvent, abc.ABC):
    """Event base for any message-bound event."""

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
    def channel(self) -> typing.Optional[channels.TextChannel]:
        """Get the cached channel that this event concerns, if known.

        Returns
        -------
        typing.Optional[hikari.channels.TextChannel]
            The cached channel, if known.
        """


@base_events.requires_intents(intents.Intents.GUILD_MESSAGES, intents.Intents.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class MessageEvent(MessagesEvent, abc.ABC):
    """Event base for any event that concerns a single message."""

    @property
    @abc.abstractmethod
    def message_id(self) -> snowflakes.Snowflake:
        """ID of the message that this event concerns.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the message that this event concerns.
        """


@base_events.requires_intents(intents.Intents.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class PrivateMessageEvent(MessageEvent, abc.ABC):
    """Event base for any message-bound event in private messages."""


@base_events.requires_intents(intents.Intents.GUILD_MESSAGES)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class GuildMessageEvent(MessageEvent, abc.ABC):
    """Event base for any message-bound event in guild messages."""

    @property
    @abc.abstractmethod
    def guild_id(self) -> snowflakes.Snowflake:
        """ID of the guild that this event concerns.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the guild that this event concerns.
        """

    @property
    def channel(self) -> typing.Union[None, channels.GuildTextChannel, channels.GuildNewsChannel]:
        """Channel that the message was sent in, if known.

        Returns
        -------
        typing.Union[builtins.None, hikari.channels.GuildTextChannel, hikari.channels.GuildNewsChannel]
            The channel the message was sent in, or `builtins.None` if not
            known/cached.

            This otherwise will always be a `hikari.channels.GuildTextChannel`
            if it is a normal message, or `hikari.channels.GuildNewsChannel` if
            sent in an announcement channel.
        """
        channel = self.app.cache.get_guild_channel(self.channel_id)
        assert channel is None or isinstance(
            channel, (channels.GuildTextChannel, channels.GuildNewsChannel)
        ), f"expected cached channel to be None or a GuildTextChannel/GuildNewsChannel, not {channel}"
        return channel

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
        return self.app.cache.get_available_guild(self.guild_id) or self.app.cache.get_unavailable_guild(self.guild_id)


@base_events.requires_intents(intents.Intents.GUILD_MESSAGES, intents.Intents.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class MessageCreateEvent(MessageEvent, abc.ABC):
    """Event base for any message creation event."""

    @property
    def message_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from MessageEvent>>.
        return self.message.id

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
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from MessageEvent>>.
        return self.message.channel_id

    @property
    def author_id(self) -> snowflakes.Snowflake:
        """ID of the author that triggered this event.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the author that triggered this event concerns.
        """
        return self.message.author.id

    @property
    @abc.abstractmethod
    def author(self) -> users.User:
        """User that sent the message.

        Returns
        -------
        hikari.users.User
            The user that sent the message.
        """

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
    def is_webhook(self) -> bool:
        """Return `builtins.True` if the message was created by a webhook.

        Returns
        -------
        builtins.bool
            `builtins.True` if from a webhook, or `builtins.False` otherwise.
        """
        return self.message.webhook_id is not None

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


@base_events.requires_intents(intents.Intents.GUILD_MESSAGES, intents.Intents.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class MessageUpdateEvent(MessageEvent, abc.ABC):
    """Event base for any message update event."""

    @property
    @abc.abstractmethod
    def message(self) -> messages.PartialMessage:
        """Partial message that was sent in the event.

        !!! warning
            Unlike `MessageCreateEvent`, `MessageUpdateEvent.message` is an
            arbitrarily partial version of `hikari.messages.Message`
            where any field except `id` and `channel_id` may be set to
            `hikari.undefined.UndefinedType` (a singleton) to indicate
            that it has not been changed.

        Returns
        -------
        hikari.messages.PartialMessage
            The partially populated message object that was sent with this
            event.
        """

    @property
    def message_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from MessageEvent>>.
        return self.message.id

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from MessageEvent>>.
        return self.message.channel_id

    @property
    @abc.abstractmethod
    def channel(self) -> typing.Optional[channels.TextChannel]:
        """Channel that the message was sent in, if known.

        Returns
        -------
        typing.Optional[hikari.channels.TextChannel]
            The text channel that the message was sent in, if known and cached,
            otherwise, `builtins.None`.
        """

    @property
    def author_id(self) -> snowflakes.Snowflake:
        """ID of the author that triggered this event.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the author that triggered this event concerns.
        """
        # Looks like `author` is always present in this event variant.
        author = self.message.author
        assert isinstance(author, users.User), "message.author was expected to be present"
        return author.id

    @property
    @abc.abstractmethod
    def author(self) -> typing.Optional[users.User]:
        """User that sent the message.

        Returns
        -------
        typing.Optional[hikari.users.User]
            The user that sent the message, if known and cached, otherwise
            `builtins.None`.
        """
        author = self.message.author
        assert isinstance(author, users.User), "message.author was expected to be present"
        return author


@base_events.requires_intents(intents.Intents.GUILD_MESSAGES, intents.Intents.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class MessageDeleteEvent(MessageEvent, abc.ABC):
    """Event base for any message delete event."""

    @property
    @abc.abstractmethod
    def message(self) -> messages.PartialMessage:
        """Partial message that was sent in the event.

        !!! warning
            Unlike `MessageCreateEvent`, `message` is a severely limited partial
            version of `hikari.messages.Message`. The only attributes
            that will not be `hikari.undefined.UNDEFINED` will be
            `id`, `channel_id`, and `guild_id` if the message was in a guild.
            This is a limitation of Discord.

            Furthermore, this partial message will represent a message that no
            longer exists. Thus, attempting to edit/delete/react or un-react to
            this message or attempting to fetch the full version will result
            in a `hikari.errors.NotFoundError` being raised.

        Returns
        -------
        hikari.messages.PartialMessage
            The partially populated message object that was sent with this
            event.
        """

    @property
    def message_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from MessageEvent>>.
        return self.message.id

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from MessagesEvent>>.
        return self.message.channel_id

    @property
    @abc.abstractmethod
    def channel(self) -> typing.Optional[channels.TextChannel]:
        """Channel that the message was sent in, if known.

        Returns
        -------
        typing.Optional[hikari.channels.TextChannel]
            The text channel that the message was sent in, if known and cached,
            otherwise, `builtins.None`.
        """


@base_events.requires_intents(intents.Intents.GUILD_MESSAGES)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class GuildMessageCreateEvent(GuildMessageEvent, MessageCreateEvent):
    """Event triggered when a message is sent to a guild channel."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    message: messages.Message = attr.ib()
    # <<inherited docstring from MessageCreateEvent>>.

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildMessageEvent>>.
        # Always present in this event.
        guild_id = self.message.guild_id
        assert isinstance(guild_id, snowflakes.Snowflake)
        return guild_id

    @property
    def author(self) -> users.User:
        """Member that sent the message.

        !!! note
            For webhooks, this will be a `hikari.users.User`.

            Any code relying on this being a `hikari.guilds.Member` directly
            should use an `isinstance` assertion to determine if member info
            is available or not.

        Returns
        -------
        hikari.users.User
            The member that sent the message, if known. This is a specialised
            implementation of `hikari.users.User`.

            If the author was a webhook, then a `hikari.users.User` will be
            returned instead, as webhooks do not have member objects.
        """
        member = self.message.member
        if member is not None:
            return member
        return self.message.author


@base_events.requires_intents(intents.Intents.PRIVATE_MESSAGES)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class PrivateMessageCreateEvent(PrivateMessageEvent, MessageCreateEvent):
    """Event triggered when a message is sent to a private channel."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    message: messages.Message = attr.ib()
    # <<inherited docstring from MessageCreateEvent>>.

    @property
    def channel(self) -> typing.Optional[channels.DMChannel]:
        """Channel that the message was sent in, if known.

        Returns
        -------
        typing.Optional[hikari.channels.DMChannel]
            The DM channel that the message was sent in, if known and cached,
            otherwise, `builtins.None`.
        """
        return self.app.cache.get_dm_channel(self.author_id)

    @property
    def author(self) -> users.User:
        # <<inherited from MessageCreateEvent>>.
        return self.message.author


@base_events.requires_intents(intents.Intents.GUILD_MESSAGES)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class GuildMessageUpdateEvent(GuildMessageEvent, MessageUpdateEvent):
    """Event triggered when a message is updated in a guild channel."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    message: messages.PartialMessage = attr.ib()
    # <<inherited docstring from MessageUpdateEvent>>.

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildMessageEvent>>.
        # Always present in this event.
        guild_id = self.message.guild_id
        assert isinstance(guild_id, snowflakes.Snowflake)
        return guild_id

    @property
    def author(self) -> typing.Union[guilds.Member, users.User]:
        # <<inherited from GuildMessageUpdateEvent>>.
        member = self.message.member
        if member is not undefined.UNDEFINED and member is not None:
            return member
        member = self.app.cache.get_member(self.guild_id, self.author_id)
        if member is not None:
            return member

        # This should always be present.
        author = self.message.author
        assert isinstance(author, users.User), "expected author to be present"
        return author


@base_events.requires_intents(intents.Intents.PRIVATE_MESSAGES)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class PrivateMessageUpdateEvent(PrivateMessageEvent, MessageUpdateEvent):
    """Event triggered when a message is updated in a private channel."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    message: messages.PartialMessage = attr.ib()
    # <<inherited docstring from MessageUpdateEvent>>.

    @property
    def channel(self) -> typing.Optional[channels.DMChannel]:
        # <<inherited docstring from MessagesEvent>>.
        return self.app.cache.get_dm_channel(self.author_id)

    @property
    def author(self) -> typing.Optional[users.User]:
        # Always present on an update event.
        author = self.message.author
        assert isinstance(author, users.User), "expected author to be present on PartialMessage"
        return author


@base_events.requires_intents(intents.Intents.GUILD_MESSAGES)
@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class GuildMessageDeleteEvent(GuildMessageEvent, MessageDeleteEvent):
    """Event triggered when a message is deleted from a guild channel."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    message: messages.PartialMessage = attr.ib()
    # <<inherited docstring from MessageDeleteEvent>>.

    @property
    def guild_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from GuildMessageEvent>>.
        # Always present in this event.
        guild_id = self.message.guild_id
        assert isinstance(guild_id, snowflakes.Snowflake), f"expected guild_id to be snowflake, not {guild_id}"
        return guild_id


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.PRIVATE_MESSAGES)
class PrivateMessageDeleteEvent(PrivateMessageEvent, MessageDeleteEvent):
    """Event triggered when a message is deleted from a private channel."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    message: messages.PartialMessage = attr.ib()
    # <<inherited docstring from MessageDeleteEvent>>.

    @property
    def channel(self) -> typing.Optional[channels.DMChannel]:
        # <<inherited from MessageEvent>>.
        # TODO: implement when we can find cached private channel by ID
        return None


# NOTE: if this ever has a private channel equivalent implemented, this intents
# constraint should be relaxed.
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGES)
class MessageBulkDeleteEvent(MessagesEvent, abc.ABC):
    """Event triggered when messages are bulk-deleted from a channel.

    !!! note
        There is only a guild equivalent of this event at the time of writing.
        However, Discord appear to not be ruling out that this ability may
        be implemented for private channels in the future. Thus, this base
        exists for future compatibility and consistency.

        If you care about the event occurring in a guild specifically, you
        should use the `GuildMessageBulkDeleteEvent`. Otherwise, using this
        event base is acceptable.

        See https://github.com/discord/discord-api-docs/issues/1633 for
        Discord's response.
    """


@attr_extensions.with_copy
@attr.s(kw_only=True, slots=True, weakref_slot=False)
@base_events.requires_intents(intents.Intents.GUILD_MESSAGES)
class GuildMessageBulkDeleteEvent(MessageBulkDeleteEvent):
    """Event triggered when messages are bulk-deleted from a guild channel."""

    app: traits.RESTAware = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from Event>>.

    shard: gateway_shard.GatewayShard = attr.ib(metadata={attr_extensions.SKIP_DEEP_COPY: True})
    # <<inherited docstring from ShardEvent>>.

    channel_id: snowflakes.Snowflake = attr.ib()
    # <<inherited docstring from MessagesEvent>>.

    guild_id: snowflakes.Snowflake = attr.ib()
    """ID of the guild that this event concerns.

    Returns
    -------
    hikari.snowflakes.Snowflake
        The ID of the guild that this event concerns.
    """

    message_ids: typing.Sequence[snowflakes.Snowflake] = attr.ib()
    """Sequence of message IDs that were bulk deleted.

    Returns
    -------
    typing.Sequence[hikari.snowflakes.Snowflake]
        A sequence of message IDs that were bulk deleted.
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
        channel = self.app.cache.get_guild_channel(self.channel_id)
        assert channel is None or isinstance(
            channel, (channels.GuildTextChannel, channels.GuildNewsChannel)
        ), f"expected cached channel to be None or a GuildTextChannel/GuildNewsChannel, not {channel}"
        return channel

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
        return self.app.cache.get_available_guild(self.guild_id) or self.app.cache.get_unavailable_guild(self.guild_id)
