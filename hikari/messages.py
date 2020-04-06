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
"""Components and entities that are used to describe messages on Discord."""
__all__ = [
    "MessageType",
    "MessageFlag",
    "MessageActivityType",
    "Attachment",
    "Reaction",
    "MessageActivity",
    "MessageCrosspost",
    "Message",
]

import datetime
import enum
import typing

import hikari.internal.conversions
from hikari import embeds as _embeds
from hikari import emojis as _emojis
from hikari import entities
from hikari import guilds
from hikari import oauth2
from hikari import snowflakes
from hikari import users
from hikari.internal import marshaller


@enum.unique
class MessageType(enum.IntEnum):
    """The type of a message."""

    #: A normal message.
    DEFAULT = 0
    #: A message to denote a new recipient in a group.
    RECIPIENT_ADD = 1
    #: A message to denote that a recipient left the group.
    RECIPIENT_REMOVE = 2
    #: A message to denote a VoIP call.
    CALL = 3
    #: A message to denote that the name of a channel changed.
    CHANNEL_NAME_CHANGE = 4
    #: A message to denote that the icon of a channel changed.
    CHANNEL_ICON_CHANGE = 5
    #: A message to denote that a message was pinned.
    CHANNEL_PINNED_MESSAGE = 6
    #: A message to denote that a member joined the guild.
    GUILD_MEMBER_JOIN = 7
    #: A message to denote a Nitro subscription.
    USER_PREMIUM_GUILD_SUBSCRIPTION = 8
    #: A message to denote a tier 1 Nitro subscription.
    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_1 = 9
    #: A message to denote a tier 2 Nitro subscription.
    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_2 = 10
    #: A message to denote a tier 3 Nitro subscription.
    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_3 = 11
    #: Channel follow add
    CHANNEL_FOLLOW_ADD = 12


class MessageFlag(enum.IntFlag):
    """Additional flags for message options."""

    NONE = 0x0
    #: This message has been published to subscribed channels via channel following.
    CROSSPOSTED = 0x1
    #: This message originated from a message in another channel via channel following.
    IS_CROSSPOST = 0x2
    #: Any embeds on this message should be omitted when serializing the message.
    SUPPRESS_EMBEDS = 0x4
    #: The message this crosspost originated from was deleted via channel following.
    SOURCE_MESSAGE_DELETED = 0x8
    #: This message came from the urgent message system.
    URGENT = 0x10


@enum.unique
class MessageActivityType(enum.IntEnum):
    """The type of a rich presence message activity."""

    NONE = 0
    #: Join an activity.
    JOIN = 1
    #: Spectating something.
    SPECTATE = 2
    #: Listening to something.
    LISTEN = 3
    #: Request to join an activity.
    JOIN_REQUEST = 5


@marshaller.attrs(slots=True)
class Attachment(snowflakes.UniqueEntity, entities.Deserializable):
    """Represents a file attached to a message."""

    #: The name of the file.
    #:
    #: :type: :obj:`str`
    filename: str = marshaller.attrib(deserializer=str)

    #: The size of the file in bytes.
    #:
    #: :type: :obj:`int`
    size: int = marshaller.attrib(deserializer=int)

    #: The source URL of file.
    #:
    #: :type: :obj:`str`
    url: str = marshaller.attrib(deserializer=str)

    #: The proxied URL of file.
    #:
    #: :type: :obj:`str`
    proxy_url: str = marshaller.attrib(deserializer=str)

    #: The height of the image (if the file is an image).
    #:
    #: :type: :obj:`int`, optional
    height: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None)

    #: The width of the image (if the file is an image).
    #:
    #: :type: :obj:`int`, optional
    width: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None)


@marshaller.attrs(slots=True)
class Reaction(entities.HikariEntity, entities.Deserializable):
    """Represents a reaction in a message."""

    #: The amount of times the emoji has been used to react.
    #:
    #: :type: :obj:`int`
    count: int = marshaller.attrib(deserializer=int)

    #: The emoji used to react.
    #:
    #: :type: :obj:`typing.Union` [ :obj:`hikari.emojis.UnicodeEmoji`, :obj:`hikari.emojis.UnknownEmoji`]
    emoji: typing.Union[_emojis.UnicodeEmoji, _emojis.UnknownEmoji] = marshaller.attrib(
        deserializer=_emojis.deserialize_reaction_emoji
    )

    #: Whether the current user reacted using this emoji.
    #:
    #: :type: :obj:`bool`
    is_reacted_by_me: bool = marshaller.attrib(raw_name="me", deserializer=bool)


@marshaller.attrs(slots=True)
class MessageActivity(entities.HikariEntity, entities.Deserializable):
    """Represents the activity of a rich presence-enabled message."""

    #: The type of message activity.
    #:
    #: :type: :obj:`MessageActivityType`
    type: MessageActivityType = marshaller.attrib(deserializer=MessageActivityType)

    #: The party ID of the message activity.
    #:
    #: :type: :obj:`str`, optional
    party_id: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None)


@marshaller.attrs(slots=True)
class MessageCrosspost(entities.HikariEntity, entities.Deserializable):
    """Represents information about a cross-posted message and the origin of the original message."""

    #: The ID of the original message.
    #:
    #: Warning
    #: -------
    #: This may be ``None`` in some cases according to the Discord API
    #: documentation, but the situations that cause this to occur are not currently documented.
    #:
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`, optional
    message_id: typing.Optional[snowflakes.Snowflake] = marshaller.attrib(
        deserializer=snowflakes.Snowflake.deserialize, if_undefined=None
    )

    #: The ID of the channel that the message originated from.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`
    channel_id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake.deserialize)

    #: The ID of the guild that the message originated from.
    #:
    #: Warning
    #: -------
    #: This may be ``None`` in some cases according to the Discord API
    #: documentation, but the situations that cause this to occur are not currently documented.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`, optional
    guild_id: typing.Optional[snowflakes.Snowflake] = marshaller.attrib(
        deserializer=snowflakes.Snowflake.deserialize, if_undefined=None
    )


@marshaller.attrs(slots=True)
class Message(snowflakes.UniqueEntity, entities.Deserializable):
    """Represents a message."""

    #: The ID of the channel that the message was sent in.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`
    channel_id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake.deserialize)

    #: The ID of the guild that the message was sent in.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`, optional
    guild_id: typing.Optional[snowflakes.Snowflake] = marshaller.attrib(
        deserializer=snowflakes.Snowflake.deserialize, if_undefined=None
    )

    #: The author of this message.
    #:
    #: :type: :obj:`hikari.users.User`
    author: users.User = marshaller.attrib(deserializer=users.User.deserialize)

    #: The member properties for the message's author.
    #:
    #: :type: :obj:`hikari.guilds.GuildMember`, optional
    member: typing.Optional[guilds.GuildMember] = marshaller.attrib(
        deserializer=guilds.GuildMember.deserialize, if_undefined=None
    )

    #: The content of the message.
    #:
    #: :type: :obj:`str`
    content: str = marshaller.attrib(deserializer=str)

    #: The timestamp that the message was sent at.
    #:
    #: :type: :obj:`datetime.datetime`
    timestamp: datetime.datetime = marshaller.attrib(deserializer=hikari.internal.conversions.parse_iso_8601_ts)

    #: The timestamp that the message was last edited at, or ``None`` if not ever edited.
    #:
    #: :type: :obj:`datetime.datetime`, optional
    edited_timestamp: typing.Optional[datetime.datetime] = marshaller.attrib(
        deserializer=hikari.internal.conversions.parse_iso_8601_ts, if_none=None
    )

    #: Whether the message is a TTS message.
    #:
    #: :type: :obj:`bool`
    is_tts: bool = marshaller.attrib(raw_name="tts", deserializer=bool)

    #: Whether the message mentions ``@everyone`` or ``@here``.
    #:
    #: :type: :obj:`bool`
    is_mentioning_everyone: bool = marshaller.attrib(raw_name="mention_everyone", deserializer=bool)

    #: The users the message mentions.
    #:
    #: :type: :obj:`typing.Set` [ :obj:`hikari.snowflakes.Snowflake` ]
    user_mentions: typing.Set[snowflakes.Snowflake] = marshaller.attrib(
        raw_name="mentions",
        deserializer=lambda user_mentions: {snowflakes.Snowflake.deserialize(u["id"]) for u in user_mentions},
    )

    #: The roles the message mentions.
    #:
    #: :type: :obj:`typing.Set` [ :obj:`hikari.snowflakes.Snowflake` ]
    role_mentions: typing.Set[snowflakes.Snowflake] = marshaller.attrib(
        raw_name="mention_roles",
        deserializer=lambda role_mentions: {snowflakes.Snowflake.deserialize(mention) for mention in role_mentions},
    )

    #: The channels the message mentions.
    #:
    #: :type: :obj:`typing.Set` [ :obj:`hikari.snowflakes.Snowflake` ]
    channel_mentions: typing.Set[snowflakes.Snowflake] = marshaller.attrib(
        raw_name="mention_channels",
        deserializer=lambda channel_mentions: {snowflakes.Snowflake.deserialize(c["id"]) for c in channel_mentions},
        if_undefined=dict,
    )

    #: The message attachments.
    #:
    #: :type: :obj:`typing.Sequence` [ :obj:`Attachment` ]
    attachments: typing.Sequence[Attachment] = marshaller.attrib(
        deserializer=lambda attachments: [Attachment.deserialize(a) for a in attachments]
    )

    #: The message embeds.
    #:
    #: :type: :obj:`typing.Sequence` [ :obj:`hikari.embeds.Embed` ]
    embeds: typing.Sequence[_embeds.Embed] = marshaller.attrib(
        deserializer=lambda embeds: [_embeds.Embed.deserialize(e) for e in embeds]
    )

    #: The message reactions.
    #:
    #: :type: :obj:`typing.Sequence` [ :obj:`Reaction` ]
    reactions: typing.Sequence[Reaction] = marshaller.attrib(
        deserializer=lambda reactions: [Reaction.deserialize(r) for r in reactions], if_undefined=dict
    )

    #: Whether the message is pinned.
    #:
    #: :type: :obj:`bool`
    is_pinned: bool = marshaller.attrib(raw_name="pinned", deserializer=bool)

    #: If the message was generated by a webhook, the webhook's id.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`, optional
    webhook_id: typing.Optional[snowflakes.Snowflake] = marshaller.attrib(
        deserializer=snowflakes.Snowflake.deserialize, if_undefined=None
    )

    #: The message type.
    #:
    #: :type: :obj:`MessageType`
    type: MessageType = marshaller.attrib(deserializer=MessageType)

    #: The message activity.
    #:
    #: :type: :obj:`MessageActivity`, optional
    activity: typing.Optional[MessageActivity] = marshaller.attrib(
        deserializer=MessageActivity.deserialize, if_undefined=None
    )

    #: The message application.
    #:
    #: :type: :obj:`hikari.oauth2.Application`, optional
    application: typing.Optional[oauth2.Application] = marshaller.attrib(
        deserializer=oauth2.Application.deserialize, if_undefined=None
    )

    #: The message crossposted reference data.
    #:
    #: :type: :obj:`MessageCrosspost`, optional
    message_reference: typing.Optional[MessageCrosspost] = marshaller.attrib(
        deserializer=MessageCrosspost.deserialize, if_undefined=None
    )

    #: The message flags.
    #:
    #: :type: :obj:`MessageFlag`, optional
    flags: typing.Optional[MessageFlag] = marshaller.attrib(deserializer=MessageFlag, if_undefined=None)
