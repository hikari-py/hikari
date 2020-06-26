# -*- coding: utf-8 -*-
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
"""Application and entities that are used to describe Discord gateway message events."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = [
    "MessageReactionEvent",
    "MessageCreateEvent",
    "UpdatedMessageFields",
    "MessageUpdateEvent",
    "MessageDeleteEvent",
    "MessageDeleteBulkEvent",
    "MessageReactionAddEvent",
    "MessageReactionRemoveEvent",
    "MessageReactionRemoveAllEvent",
    "MessageReactionRemoveEmojiEvent",
]

import typing

import attr

from hikari.events import base as base_events
from hikari.models import intents
from hikari.models import messages
from hikari.utilities import snowflake

if typing.TYPE_CHECKING:
    import datetime

    from hikari.api import rest
    from hikari.models import applications
    from hikari.models import embeds as embed_models
    from hikari.models import emojis
    from hikari.models import guilds
    from hikari.models import users
    from hikari.utilities import undefined


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.DIRECT_MESSAGES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageCreateEvent(base_events.Event):
    """Used to represent Message Create gateway events."""

    message: messages.Message = attr.ib(repr=True)
    """The message that was sent."""


@attr.s(slots=True, kw_only=True, init=False, repr=True, eq=False)
class UpdatedMessageFields(snowflake.Unique):
    """An arbitrarily partial version of `hikari.models.messages.Message`.

    This contains arbitrary fields that may be updated in a
    `MessageUpdateEvent`, but for all other purposes should be treated as
    being optionally specified.

    !!! warn
        All fields on this model except `channel` and `id` may be set to
        `hikari.utilities.undefined.UndefinedType` (a singleton) if we have not
        received information about their state from Discord alongside field
        nullability.
    """

    id: snowflake.Snowflake = attr.ib(
        converter=snowflake.Snowflake, eq=True, hash=True, repr=True, factory=snowflake.Snowflake,
    )
    """The ID of this entity."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    channel_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the channel that the message was sent in."""

    # So this breaks stuff using inheritance.
    guild_id: typing.Union[snowflake.Snowflake, undefined.UndefinedType] = attr.ib(repr=True)
    """The ID of the guild that the message was sent in."""

    author: typing.Union[users.User, undefined.UndefinedType] = attr.ib(repr=True)
    """The author of this message."""

    member: typing.Union[guilds.Member, undefined.UndefinedType] = attr.ib(repr=False)
    """The member properties for the message's author."""

    content: typing.Union[str, undefined.UndefinedType] = attr.ib(repr=False)
    """The content of the message."""

    timestamp: typing.Union[datetime.datetime, undefined.UndefinedType] = attr.ib(repr=False)
    """The timestamp that the message was sent at."""

    edited_timestamp: typing.Union[datetime.datetime, undefined.UndefinedType, None] = attr.ib(repr=False)
    """The timestamp that the message was last edited at.

    Will be `None` if the message wasn't ever edited, or `undefined` if the
    info is not available.
    """

    is_tts: typing.Union[bool, undefined.UndefinedType] = attr.ib(repr=False)
    """Whether the message is a TTS message."""

    is_mentioning_everyone: typing.Union[bool, undefined.UndefinedType] = attr.ib(repr=False)
    """Whether the message mentions `@everyone` or `@here`."""

    user_mentions: typing.Union[typing.Set[snowflake.Snowflake], undefined.UndefinedType] = attr.ib(repr=False)
    """The users the message mentions."""

    role_mentions: typing.Union[typing.Set[snowflake.Snowflake], undefined.UndefinedType] = attr.ib(repr=False)
    """The roles the message mentions."""

    channel_mentions: typing.Union[typing.Set[snowflake.Snowflake], undefined.UndefinedType] = attr.ib(repr=False)
    """The channels the message mentions."""

    attachments: typing.Union[typing.Sequence[messages.Attachment], undefined.UndefinedType] = attr.ib(repr=False)
    """The message attachments."""

    embeds: typing.Union[typing.Sequence[embed_models.Embed], undefined.UndefinedType] = attr.ib(repr=False)
    """The message's embeds."""

    reactions: typing.Union[typing.Sequence[messages.Reaction], undefined.UndefinedType] = attr.ib(repr=False)
    """The message's reactions."""

    is_pinned: typing.Union[bool, undefined.UndefinedType] = attr.ib(repr=False)
    """Whether the message is pinned."""

    webhook_id: typing.Union[snowflake.Snowflake, undefined.UndefinedType] = attr.ib(repr=False)
    """If the message was generated by a webhook, the webhook's ID."""

    type: typing.Union[messages.MessageType, undefined.UndefinedType] = attr.ib(repr=False)
    """The message's type."""

    activity: typing.Union[messages.MessageActivity, undefined.UndefinedType] = attr.ib(repr=False)
    """The message's activity."""

    application: typing.Union[applications.Application, undefined.UndefinedType] = attr.ib(repr=False)
    """The message's application."""

    message_reference: typing.Union[messages.MessageCrosspost, undefined.UndefinedType] = attr.ib(repr=False)
    """The message's cross-posted reference data."""

    flags: typing.Union[messages.MessageFlag, undefined.UndefinedType] = attr.ib(repr=False)
    """The message's flags."""

    nonce: typing.Union[str, undefined.UndefinedType] = attr.ib(repr=False)
    """The message nonce.

    This is a string used for validating a message was sent.
    """


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.DIRECT_MESSAGES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageUpdateEvent(base_events.Event, snowflake.Unique):
    """Represents Message Update gateway events.

    !!! warn
        Unlike `MessageCreateEvent`, `MessageUpdateEvent.message` is an
        arbitrarily partial version of `hikari.models.messages.Message` where
        any field except `id` may be set to `hikari.utilities.undefined.UndefinedType`
        (a singleton) to indicate that it has not been changed.
    """

    id: snowflake.Snowflake = attr.ib(
        converter=snowflake.Snowflake, eq=True, hash=True, repr=True, factory=snowflake.Snowflake,
    )
    """The ID of this entity."""

    message: UpdatedMessageFields = attr.ib(repr=True)
    """The partial message object with all updated fields."""


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.DIRECT_MESSAGES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageDeleteEvent(base_events.Event):
    """Used to represent Message Delete gateway events.

    Sent when a message is deleted in a channel we have access to.
    """

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    # TODO: common base class for Message events.

    channel_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the channel where this message was deleted."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(repr=True)
    """The ID of the guild where this message was deleted.

    This will be `None` if this message was deleted in a DM channel.
    """

    message_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the message that was deleted."""


# TODO: if this doesn't apply to DMs then does guild_id need to be nullable here?
@base_events.requires_intents(intents.Intent.GUILD_MESSAGES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageDeleteBulkEvent(base_events.Event):
    """Used to represent Message Bulk Delete gateway events.

    Sent when multiple messages are deleted in a channel at once.
    """

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    channel_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the channel these messages have been deleted in."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(repr=True)
    """The ID of the channel these messages have been deleted in.

    This will be `None` if these messages were bulk deleted in a DM channel.
    """

    message_ids: typing.Set[snowflake.Snowflake] = attr.ib(repr=False)
    """A collection of the IDs of the messages that were deleted."""


class MessageReactionEvent(base_events.Event):
    """A base class that all message reaction events will inherit from."""

    app: rest.IRESTClient = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    channel_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the channel where this reaction is happening."""

    message_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the message this reaction event is happening on."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(repr=True)
    """The ID of the guild where this reaction event is happening.

    This will be `None` if this is happening in a DM channel.
    """


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageReactionAddEvent(MessageReactionEvent):
    """Used to represent Message Reaction Add gateway events."""

    user_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the user adding the reaction."""

    # TODO: does this contain a user? If not, should it be a PartialGuildMember?
    member: typing.Optional[guilds.Member] = attr.ib(repr=False)
    """The member object of the user who's adding this reaction.

    This will be `None` if this is happening in a DM channel.
    """

    emoji: typing.Union[emojis.CustomEmoji, emojis.UnicodeEmoji] = attr.ib(repr=True)
    """The object of the emoji being added."""


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageReactionRemoveEvent(MessageReactionEvent):
    """Used to represent Message Reaction Remove gateway events."""

    user_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the user who is removing their reaction."""

    emoji: typing.Union[emojis.UnicodeEmoji, emojis.CustomEmoji] = attr.ib(repr=True)
    """The object of the emoji being removed."""


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageReactionRemoveAllEvent(MessageReactionEvent):
    """Used to represent Message Reaction Remove All gateway events.

    Sent when all the reactions are removed from a message, regardless of emoji.
    """


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageReactionRemoveEmojiEvent(MessageReactionEvent):
    """Represents Message Reaction Remove Emoji events.

    Sent when all the reactions for a single emoji are removed from a message.
    """

    emoji: typing.Union[emojis.UnicodeEmoji, emojis.CustomEmoji] = attr.ib(repr=True)
    """The object of the emoji that's being removed."""
