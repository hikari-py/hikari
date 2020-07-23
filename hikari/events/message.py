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

__all__: typing.Final[typing.List[str]] = [
    "MessageReactionEvent",
    "MessageCreateEvent",
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
    from hikari.api import rest as rest_app
    from hikari.models import emojis
    from hikari.models import guilds


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.PRIVATE_MESSAGES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageCreateEvent(base_events.Event):
    """Used to represent Message Create gateway events."""

    message: messages.Message = attr.ib(repr=True)
    """The message that was sent."""


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.PRIVATE_MESSAGES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageUpdateEvent(base_events.Event):
    """Represents Message Update gateway events.

    !!! warn
        Unlike `MessageCreateEvent`, `MessageUpdateEvent.message` is an
        arbitrarily partial version of `hikari.models.messages.Message` where
        any field except `id` and `channel_id` may be set to
        `hikari.utilities.undefined.UndefinedType` (a singleton) to indicate
        that it has not been changed.
    """

    message: messages.PartialMessage = attr.ib(repr=True)
    """The partial message object with all updated fields."""


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.PRIVATE_MESSAGES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageDeleteEvent(base_events.Event):
    """Used to represent Message Delete gateway events.

    Sent when a message is deleted in a channel we have access to.

    !!! warn
        Unlike `MessageCreateEvent`, `message` is a severely limited partial
        version of `hikari.models.messages.Message`. The only attributes that
        will not be `hikari.utilities.undefined.UNDEFINED` will be `id`,
        `channel_id`, and `guild_id` if the message was in a guild.
        This is a limitation of Discord.

        Furthermore, this partial message will represent a message that no
        longer exists. Thus, attempting to edit/delete/react or un-react to
        this message or attempting to fetch the full version will result
        in a `hikari.errors.NotFound` being raised.
    """

    message: messages.PartialMessage = attr.ib(repr=True)


# TODO: if this doesn't apply to DMs then does guild_id need to be nullable here?
@base_events.requires_intents(intents.Intent.GUILD_MESSAGES)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageDeleteBulkEvent(base_events.Event):
    """Used to represent Message Bulk Delete gateway events.

    Sent when multiple messages are deleted in a channel at once.
    """

    app: rest_app.IRESTApp = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    channel_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the channel these messages have been deleted in."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(repr=True)
    """The ID of the channel these messages have been deleted in.

    This will be `builtins.None` if these messages were bulk deleted in a DM channel.
    """

    message_ids: typing.Set[snowflake.Snowflake] = attr.ib(repr=False)
    """A collection of the IDs of the messages that were deleted."""


class MessageReactionEvent(base_events.Event):
    """A base class that all message reaction events will inherit from."""

    app: rest_app.IRESTApp = attr.ib(default=None, repr=False, eq=False, hash=False)
    """The client application that models may use for procedures."""

    channel_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the channel where this reaction is happening."""

    message_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the message this reaction event is happening on."""

    guild_id: typing.Optional[snowflake.Snowflake] = attr.ib(repr=True)
    """The ID of the guild where this reaction event is happening.

    This will be `builtins.None` if this is happening in a DM channel.
    """


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.PRIVATE_MESSAGE_REACTIONS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageReactionAddEvent(MessageReactionEvent):
    """Used to represent Message Reaction Add gateway events."""

    user_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the user adding the reaction."""

    # TODO: does this contain a user? If not, should it be a PartialGuildMember?
    member: typing.Optional[guilds.Member] = attr.ib(repr=False)
    """The member object of the user who's adding this reaction.

    This will be `builtins.None` if this is happening in a DM channel.
    """

    emoji: typing.Union[emojis.CustomEmoji, emojis.UnicodeEmoji] = attr.ib(repr=True)
    """The object of the emoji being added."""


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.PRIVATE_MESSAGE_REACTIONS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageReactionRemoveEvent(MessageReactionEvent):
    """Used to represent Message Reaction Remove gateway events."""

    user_id: snowflake.Snowflake = attr.ib(repr=True)
    """The ID of the user who is removing their reaction."""

    emoji: typing.Union[emojis.UnicodeEmoji, emojis.CustomEmoji] = attr.ib(repr=True)
    """The object of the emoji being removed."""


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.PRIVATE_MESSAGE_REACTIONS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageReactionRemoveAllEvent(MessageReactionEvent):
    """Used to represent Message Reaction Remove All gateway events.

    Sent when all the reactions are removed from a message, regardless of emoji.
    """


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.PRIVATE_MESSAGE_REACTIONS)
@attr.s(eq=False, hash=False, init=False, kw_only=True, slots=True)
class MessageReactionRemoveEmojiEvent(MessageReactionEvent):
    """Represents Message Reaction Remove Emoji events.

    Sent when all the reactions for a single emoji are removed from a message.
    """

    emoji: typing.Union[emojis.UnicodeEmoji, emojis.CustomEmoji] = attr.ib(repr=True)
    """The object of the emoji that's being removed."""
