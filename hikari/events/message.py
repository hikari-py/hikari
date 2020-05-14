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
from hikari import bases as base_entities
from hikari import embeds as _embeds
from hikari import emojis
from hikari import guilds
from hikari import intents
from hikari import messages
from hikari import unset
from hikari import users
from hikari.events import base as base_events
from hikari.internal import conversions
from hikari.internal import marshaller

if typing.TYPE_CHECKING:
    import datetime

    from hikari.internal import more_typing


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.DIRECT_MESSAGES)
@marshaller.marshallable()
@attr.s(eq=False, hash=False, kw_only=True, slots=True)
class MessageCreateEvent(base_events.HikariEvent, messages.Message):
    """Used to represent Message Create gateway events."""


def _deserialize_object_mentions(payload: more_typing.JSONArray) -> typing.Set[base_entities.Snowflake]:
    return {base_entities.Snowflake(mention["id"]) for mention in payload}


def _deserialize_mentions(payload: more_typing.JSONArray) -> typing.Set[base_entities.Snowflake]:
    return {base_entities.Snowflake(mention) for mention in payload}


def _deserialize_attachments(
    payload: more_typing.JSONArray, **kwargs: typing.Any
) -> typing.Sequence[messages.Attachment]:
    return [messages.Attachment.deserialize(attachment, **kwargs) for attachment in payload]


def _deserialize_embeds(payload: more_typing.JSONArray, **kwargs: typing.Any) -> typing.Sequence[_embeds.Embed]:
    return [_embeds.Embed.deserialize(embed, **kwargs) for embed in payload]


def _deserialize_reaction(payload: more_typing.JSONArray, **kwargs: typing.Any) -> typing.Sequence[messages.Reaction]:
    return [messages.Reaction.deserialize(reaction, **kwargs) for reaction in payload]


# This is an arbitrarily partial version of `messages.Message`
@base_events.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.DIRECT_MESSAGES)
@marshaller.marshallable()
@attr.s(eq=False, hash=False, kw_only=True, slots=True)
class MessageUpdateEvent(base_events.HikariEvent, base_entities.Unique, marshaller.Deserializable):
    """Represents Message Update gateway events.

    !!! note
        All fields on this model except `MessageUpdateEvent.channel_id` and
        `MessageUpdateEvent.id` may be set to `hikari.unset.UNSET` (a singleton)
        we have not received information about their state from Discord
        alongside field nullability.
    """

    # FIXME: the id here is called "id", but in MessageDeleteEvent it is "message_id"...

    channel_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the channel that the message was sent in."""

    guild_id: typing.Union[base_entities.Snowflake, unset.Unset] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=unset.Unset, default=unset.UNSET, repr=True
    )
    """The ID of the guild that the message was sent in."""

    author: typing.Union[users.User, unset.Unset] = marshaller.attrib(
        deserializer=users.User.deserialize, if_undefined=unset.Unset, default=unset.UNSET, repr=True
    )
    """The author of this message."""

    # TODO: can we merge member and author together?
    # We could override deserialize to to this and then reorganise the payload, perhaps?
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

    user_mentions: typing.Union[typing.Set[base_entities.Snowflake], unset.Unset] = marshaller.attrib(
        raw_name="mentions", deserializer=_deserialize_object_mentions, if_undefined=unset.Unset, default=unset.UNSET,
    )
    """The users the message mentions."""

    role_mentions: typing.Union[typing.Set[base_entities.Snowflake], unset.Unset] = marshaller.attrib(
        raw_name="mention_roles", deserializer=_deserialize_mentions, if_undefined=unset.Unset, default=unset.UNSET,
    )
    """The roles the message mentions."""

    channel_mentions: typing.Union[typing.Set[base_entities.Snowflake], unset.Unset] = marshaller.attrib(
        raw_name="mention_channels",
        deserializer=_deserialize_object_mentions,
        if_undefined=unset.Unset,
        default=unset.UNSET,
    )
    """The channels the message mentions."""

    attachments: typing.Union[typing.Sequence[messages.Attachment], unset.Unset] = marshaller.attrib(
        deserializer=_deserialize_attachments, if_undefined=unset.Unset, default=unset.UNSET, inherit_kwargs=True,
    )
    """The message attachments."""

    embeds: typing.Union[typing.Sequence[_embeds.Embed], unset.Unset] = marshaller.attrib(
        deserializer=_deserialize_embeds, if_undefined=unset.Unset, default=unset.UNSET, inherit_kwargs=True,
    )
    """The message's embeds."""

    reactions: typing.Union[typing.Sequence[messages.Reaction], unset.Unset] = marshaller.attrib(
        deserializer=_deserialize_reaction, if_undefined=unset.Unset, default=unset.UNSET, inherit_kwargs=True
    )
    """The message's reactions."""

    is_pinned: typing.Union[bool, unset.Unset] = marshaller.attrib(
        raw_name="pinned", deserializer=bool, if_undefined=unset.Unset, default=unset.UNSET
    )
    """Whether the message is pinned."""

    webhook_id: typing.Union[base_entities.Snowflake, unset.Unset] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=unset.Unset, default=unset.UNSET
    )
    """If the message was generated by a webhook, the webhook's ID."""

    type: typing.Union[messages.MessageType, unset.Unset] = marshaller.attrib(
        deserializer=messages.MessageType, if_undefined=unset.Unset, default=unset.UNSET
    )
    """The message's type."""

    activity: typing.Union[messages.MessageActivity, unset.Unset] = marshaller.attrib(
        deserializer=messages.MessageActivity.deserialize,
        if_undefined=unset.Unset,
        default=unset.UNSET,
        inherit_kwargs=True,
    )
    """The message's activity."""

    application: typing.Optional[applications.Application] = marshaller.attrib(
        deserializer=applications.Application.deserialize,
        if_undefined=unset.Unset,
        default=unset.UNSET,
        inherit_kwargs=True,
    )
    """The message's application."""

    message_reference: typing.Union[messages.MessageCrosspost, unset.Unset] = marshaller.attrib(
        deserializer=messages.MessageCrosspost.deserialize,
        if_undefined=unset.Unset,
        default=unset.UNSET,
        inherit_kwargs=True,
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


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES, intents.Intent.DIRECT_MESSAGES)
@marshaller.marshallable()
@attr.s(eq=False, hash=False, kw_only=True, slots=True)
class MessageDeleteEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent Message Delete gateway events.

    Sent when a message is deleted in a channel we have access to.
    """

    # TODO: common base class for Message events.

    channel_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the channel where this message was deleted."""

    guild_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=None, default=None, repr=True
    )
    """The ID of the guild where this message was deleted.

    This will be `None` if this message was deleted in a DM channel.
    """

    message_id: base_entities.Snowflake = marshaller.attrib(
        raw_name="id", deserializer=base_entities.Snowflake, repr=True
    )
    """The ID of the message that was deleted."""


def _deserialize_message_ids(payload: more_typing.JSONArray) -> typing.Set[base_entities.Snowflake]:
    return {base_entities.Snowflake(message_id) for message_id in payload}


@base_events.requires_intents(intents.Intent.GUILD_MESSAGES)
@marshaller.marshallable()
@attr.s(eq=False, hash=False, kw_only=True, slots=True)
class MessageDeleteBulkEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent Message Bulk Delete gateway events.

    Sent when multiple messages are deleted in a channel at once.
    """

    channel_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the channel these messages have been deleted in."""

    guild_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_none=None, repr=True,
    )
    """The ID of the channel these messages have been deleted in.

    This will be `None` if these messages were bulk deleted in a DM channel.
    """

    message_ids: typing.Set[base_entities.Snowflake] = marshaller.attrib(
        raw_name="ids", deserializer=_deserialize_message_ids
    )
    """A collection of the IDs of the messages that were deleted."""


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@marshaller.marshallable()
@attr.s(eq=False, hash=False, kw_only=True, slots=True)
class MessageReactionAddEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent Message Reaction Add gateway events."""

    # TODO: common base classes!

    user_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the user adding the reaction."""

    channel_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the channel where this reaction is being added."""

    message_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the message this reaction is being added to."""

    guild_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=None, default=None, repr=True
    )
    """The ID of the guild where this reaction is being added.

    This will be `None` if this is happening in a DM channel.
    """

    # TODO: does this contain a user? If not, should it be a PartialGuildMember?
    member: typing.Optional[guilds.GuildMember] = marshaller.attrib(
        deserializer=guilds.GuildMember.deserialize, if_undefined=None, default=None, inherit_kwargs=True
    )
    """The member object of the user who's adding this reaction.

    This will be `None` if this is happening in a DM channel.
    """

    emoji: typing.Union[emojis.CustomEmoji, emojis.UnicodeEmoji] = marshaller.attrib(
        deserializer=emojis.deserialize_reaction_emoji, inherit_kwargs=True, repr=True
    )
    """The object of the emoji being added."""


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@marshaller.marshallable()
@attr.s(eq=False, hash=False, kw_only=True, slots=True)
class MessageReactionRemoveEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent Message Reaction Remove gateway events."""

    user_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the user who is removing their reaction."""

    channel_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the channel where this reaction is being removed."""

    message_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the message this reaction is being removed from."""

    guild_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=None, default=None, repr=True
    )
    """The ID of the guild where this reaction is being removed

    This will be `None` if this event is happening in a DM channel.
    """

    emoji: typing.Union[emojis.UnicodeEmoji, emojis.CustomEmoji] = marshaller.attrib(
        deserializer=emojis.deserialize_reaction_emoji, inherit_kwargs=True, repr=True
    )
    """The object of the emoji being removed."""


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@marshaller.marshallable()
@attr.s(eq=False, hash=False, kw_only=True, slots=True)
class MessageReactionRemoveAllEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Used to represent Message Reaction Remove All gateway events.

    Sent when all the reactions are removed from a message, regardless of emoji.
    """

    channel_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the channel where the targeted message is."""

    message_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the message all reactions are being removed from."""

    guild_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=None, default=None, repr=True,
    )
    """The ID of the guild where the targeted message is, if applicable."""


@base_events.requires_intents(intents.Intent.GUILD_MESSAGE_REACTIONS, intents.Intent.DIRECT_MESSAGE_REACTIONS)
@marshaller.marshallable()
@attr.s(eq=False, hash=False, kw_only=True, slots=True)
class MessageReactionRemoveEmojiEvent(base_events.HikariEvent, marshaller.Deserializable):
    """Represents Message Reaction Remove Emoji events.

    Sent when all the reactions for a single emoji are removed from a message.
    """

    channel_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the channel where the targeted message is."""

    guild_id: typing.Optional[base_entities.Snowflake] = marshaller.attrib(
        deserializer=base_entities.Snowflake, if_undefined=None, default=None, repr=True
    )
    """The ID of the guild where the targeted message is, if applicable."""

    message_id: base_entities.Snowflake = marshaller.attrib(deserializer=base_entities.Snowflake, repr=True)
    """The ID of the message the reactions are being removed from."""

    emoji: typing.Union[emojis.UnicodeEmoji, emojis.CustomEmoji] = marshaller.attrib(
        deserializer=emojis.deserialize_reaction_emoji, inherit_kwargs=True, repr=True
    )
    """The object of the emoji that's being removed."""
