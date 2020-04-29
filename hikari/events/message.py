#!/usr/bin/env python3
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
"""Components and entities that are used to describe Discord gateway message events."""

from __future__ import annotations

__all__ = [
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

from hikari import applications
from hikari import bases
from hikari import embeds as _embeds
from hikari import emojis
from hikari import guilds
from hikari import intents
from hikari import messages
from hikari import unset
from hikari import users
from hikari.events import base
from hikari.internal import conversions
from hikari.internal import marshaller

if typing.TYPE_CHECKING:
    import datetime


@base.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.DIRECT_MESSAGES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageCreateEvent(base.HikariEvent, messages.Message):
    """Used to represent Message Create gateway events."""


# This is an arbitrarily partial version of `messages.Message`
@base.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.DIRECT_MESSAGES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageUpdateEvent(base.HikariEvent, bases.UniqueEntity, marshaller.Deserializable):
    """Represents Message Update gateway events.

    !!! note
        All fields on this model except `MessageUpdateEvent.channel_id` and
        `MessageUpdateEvent.id` may be set to `hikari.unset.UNSET` (a singleton)
        we have not received information about their state from Discord
        alongside field nullability.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel that the message was sent in."""

    guild_id: typing.Union[bases.Snowflake, unset.Unset] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The ID of the guild that the message was sent in."""

    author: typing.Union[users.User, unset.Unset] = marshaller.attrib(
        deserializer=users.User.deserialize, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The author of this message."""

    member: typing.Union[guilds.GuildMember, unset.Unset] = marshaller.attrib(
        deserializer=guilds.GuildMember.deserialize, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The member properties for the message's author."""

    content: typing.Union[str, unset.Unset] = marshaller.attrib(
        deserializer=str, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The content of the message."""

    timestamp: typing.Union[datetime.datetime, unset.Unset] = marshaller.attrib(
        deserializer=conversions.parse_iso_8601_ts, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The timestamp that the message was sent at."""

    edited_timestamp: typing.Union[datetime.datetime, unset.Unset, None] = marshaller.attrib(
        deserializer=conversions.parse_iso_8601_ts, if_none=None, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The timestamp that the message was last edited at.

    Will be `None` if the message wasn't ever edited.
    """

    is_tts: typing.Union[bool, unset.Unset] = marshaller.attrib(
        raw_name="tts", deserializer=bool, if_undefined=unset.Unset, default=unset.UNSET
    )
    """Whether the message is a TTS message."""

    is_mentioning_everyone: typing.Union[bool, unset.Unset] = marshaller.attrib(
        raw_name="mention_everyone", deserializer=bool, if_undefined=unset.Unset, default=unset.UNSET
    )
    """Whether the message mentions `@everyone` or `@here`."""

    user_mentions: typing.Union[typing.Set[bases.Snowflake], unset.Unset] = marshaller.attrib(
        raw_name="mentions",
        deserializer=lambda user_mentions: {bases.Snowflake.deserialize(u["id"]) for u in user_mentions},
        if_undefined=unset.Unset,
        default=unset.UNSET,
    )
    """The users the message mentions."""

    role_mentions: typing.Union[typing.Set[bases.Snowflake], unset.Unset] = marshaller.attrib(
        raw_name="mention_roles",
        deserializer=lambda role_mentions: {bases.Snowflake.deserialize(r) for r in role_mentions},
        if_undefined=unset.Unset,
        default=unset.UNSET,
    )
    """The roles the message mentions."""

    channel_mentions: typing.Union[typing.Set[bases.Snowflake], unset.Unset] = marshaller.attrib(
        raw_name="mention_channels",
        deserializer=lambda channel_mentions: {bases.Snowflake.deserialize(c["id"]) for c in channel_mentions},
        if_undefined=unset.Unset,
        default=unset.UNSET,
    )
    """The channels the message mentions."""

    attachments: typing.Union[typing.Sequence[messages.Attachment], unset.Unset] = marshaller.attrib(
        deserializer=lambda attachments: [messages.Attachment.deserialize(a) for a in attachments],
        if_undefined=unset.Unset,
        default=unset.UNSET,
    )
    """The message attachments."""

    embeds: typing.Union[typing.Sequence[_embeds.Embed], unset.Unset] = marshaller.attrib(
        deserializer=lambda embed_objs: [_embeds.Embed.deserialize(e) for e in embed_objs],
        if_undefined=unset.Unset,
        default=unset.UNSET,
    )
    """The message's embeds."""

    reactions: typing.Union[typing.Sequence[messages.Reaction], unset.Unset] = marshaller.attrib(
        deserializer=lambda reactions: [messages.Reaction.deserialize(r) for r in reactions],
        if_undefined=unset.Unset,
        default=unset.UNSET,
    )
    """The message's reactions."""

    is_pinned: typing.Union[bool, unset.Unset] = marshaller.attrib(
        raw_name="pinned", deserializer=bool, if_undefined=unset.Unset, default=unset.UNSET
    )
    """Whether the message is pinned."""

    webhook_id: typing.Union[bases.Snowflake, unset.Unset] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=unset.Unset, default=unset.UNSET
    )
    """If the message was generated by a webhook, the webhook's ID."""

    type: typing.Union[messages.MessageType, unset.Unset] = marshaller.attrib(
        deserializer=messages.MessageType, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The message's type."""

    activity: typing.Union[messages.MessageActivity, unset.Unset] = marshaller.attrib(
        deserializer=messages.MessageActivity.deserialize, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The message's activity."""

    application: typing.Optional[applications.Application] = marshaller.attrib(
        deserializer=applications.Application.deserialize, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The message's application."""

    message_reference: typing.Union[messages.MessageCrosspost, unset.Unset] = marshaller.attrib(
        deserializer=messages.MessageCrosspost.deserialize, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The message's cross-posted reference data."""

    flags: typing.Union[messages.MessageFlag, unset.Unset] = marshaller.attrib(
        deserializer=messages.MessageFlag, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The message's flags."""

    nonce: typing.Union[str, unset.Unset] = marshaller.attrib(
        deserializer=str, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The message nonce.

    This is a string used for validating a message was sent.
    """


@base.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.DIRECT_MESSAGES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageDeleteEvent(base.HikariEvent, marshaller.Deserializable):
    """Used to represent Message Delete gateway events.

    Sent when a message is deleted in a channel we have access to.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel where this message was deleted."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild where this message was deleted.

    This will be `None` if this message was deleted in a DM channel.
    """

    message_id: bases.Snowflake = marshaller.attrib(raw_name="id", deserializer=bases.Snowflake.deserialize)
    """The ID of the message that was deleted."""


@base.requires_intents(intents.Intent.GUILD_MESSAGES)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageDeleteBulkEvent(base.HikariEvent, marshaller.Deserializable):
    """Used to represent Message Bulk Delete gateway events.

    Sent when multiple messages are deleted in a channel at once.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel these messages have been deleted in."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_none=None
    )
    """The ID of the channel these messages have been deleted in.

    This will be `None` if these messages were bulk deleted in a DM channel.
    """

    message_ids: typing.Set[bases.Snowflake] = marshaller.attrib(
        raw_name="ids", deserializer=lambda msgs: {bases.Snowflake.deserialize(m) for m in msgs}
    )
    """A collection of the IDs of the messages that were deleted."""


@base.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageReactionAddEvent(base.HikariEvent, marshaller.Deserializable):
    """Used to represent Message Reaction Add gateway events."""

    user_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the user adding the reaction."""

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel where this reaction is being added."""

    message_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the message this reaction is being added to."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild where this reaction is being added.

    This will be `None` if this is happening in a DM channel.
    """

    member: typing.Optional[guilds.GuildMember] = marshaller.attrib(
        deserializer=guilds.GuildMember.deserialize, if_undefined=None, default=None
    )
    """The member object of the user who's adding this reaction.

    This will be `None` if this is happening in a DM channel.
    """

    emoji: typing.Union[emojis.UnknownEmoji, emojis.UnicodeEmoji] = marshaller.attrib(
        deserializer=emojis.deserialize_reaction_emoji,
    )
    """The object of the emoji being added."""


@base.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageReactionRemoveEvent(base.HikariEvent, marshaller.Deserializable):
    """Used to represent Message Reaction Remove gateway events."""

    user_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the user who is removing their reaction."""

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel where this reaction is being removed."""

    message_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the message this reaction is being removed from."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild where this reaction is being removed

    This will be `None` if this event is happening in a DM channel.
    """

    emoji: typing.Union[emojis.UnicodeEmoji, emojis.UnknownEmoji] = marshaller.attrib(
        deserializer=emojis.deserialize_reaction_emoji,
    )
    """The object of the emoji being removed."""


@base.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageReactionRemoveAllEvent(base.HikariEvent, marshaller.Deserializable):
    """Used to represent Message Reaction Remove All gateway events.

    Sent when all the reactions are removed from a message, regardless of emoji.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel where the targeted message is."""

    message_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the message all reactions are being removed from."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild where the targeted message is, if applicable."""


@base.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageReactionRemoveEmojiEvent(base.HikariEvent, marshaller.Deserializable):
    """Represents Message Reaction Remove Emoji events.

    Sent when all the reactions for a single emoji are removed from a message.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel where the targeted message is."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild where the targeted message is, if applicable."""

    message_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the message the reactions are being removed from."""

    emoji: typing.Union[emojis.UnicodeEmoji, emojis.UnknownEmoji] = marshaller.attrib(
        deserializer=emojis.deserialize_reaction_emoji,
    )
    """The object of the emoji that's being removed."""
