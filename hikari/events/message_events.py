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

__all__: typing.Final[typing.List[str]] = [
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

from hikari import intents
from hikari.events import base_events
from hikari.events import shard_events
from hikari.utilities import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import messages
    from hikari import snowflakes
    from hikari import traits
    from hikari import users
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


@base_events.requires_intents(intents.Intents.GUILD_MESSAGES, intents.Intents.PRIVATE_MESSAGES)
@attr.s(kw_only=True, slots=True, weakref_slot=False)
class MessageCreateEvent(MessageEvent, abc.ABC):
    """Event base for any message creation event."""

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
        # <<inherited docstring from MessageEvent>>.
        return self.message.id

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
    def author_id(self) -> snowflakes.Snowflake:
        """ID of the author that triggered this event.

        Returns
        -------
        hikari.snowflakes.Snowflake
            The ID of the author that triggered this event concerns.
        """
        # Looks like `author` is always present in this event variant.
        return typing.cast("users.PartialUser", self.message.author).id

    @property
    def channel_id(self) -> snowflakes.Snowflake:
        # <<inherited docstring from MessageEvent>>.
        return self.message.channel_id


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
            in a `hikari.errors.NotFound` being raised.

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
        return typing.cast("snowflakes.Snowflake", self.message.guild_id)


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
        return typing.cast("snowflakes.Snowflake", self.message.guild_id)


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
        return typing.cast("snowflakes.Snowflake", self.message.guild_id)


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
