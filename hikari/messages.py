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

from __future__ import annotations

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

import typing

import attr

from hikari import applications
from hikari import bases
from hikari import embeds as _embeds
from hikari import emojis as _emojis
from hikari import guilds
from hikari import users
from hikari.internal import conversions
from hikari.internal import marshaller
from hikari.internal import more_enums

if typing.TYPE_CHECKING:
    import datetime

    from hikari import channels
    from hikari import files as _files
    from hikari.internal import more_typing


@more_enums.must_be_unique
class MessageType(int, more_enums.Enum):
    """The type of a message."""

    DEFAULT = 0
    """A normal message."""

    RECIPIENT_ADD = 1
    """A message to denote a new recipient in a group."""

    RECIPIENT_REMOVE = 2
    """A message to denote that a recipient left the group."""

    CALL = 3
    """A message to denote a VoIP call."""

    CHANNEL_NAME_CHANGE = 4
    """A message to denote that the name of a channel changed."""

    CHANNEL_ICON_CHANGE = 5
    """A message to denote that the icon of a channel changed."""

    CHANNEL_PINNED_MESSAGE = 6
    """A message to denote that a message was pinned."""

    GUILD_MEMBER_JOIN = 7
    """A message to denote that a member joined the guild."""

    USER_PREMIUM_GUILD_SUBSCRIPTION = 8
    """A message to denote a Nitro subscription."""

    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_1 = 9
    """A message to denote a tier 1 Nitro subscription."""

    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_2 = 10
    """A message to denote a tier 2 Nitro subscription."""

    USER_PREMIUM_GUILD_SUBSCRIPTION_TIER_3 = 11
    """A message to denote a tier 3 Nitro subscription."""

    CHANNEL_FOLLOW_ADD = 12
    """Channel follow add."""


@more_enums.must_be_unique
class MessageFlag(more_enums.IntFlag):
    """Additional flags for message options."""

    NONE = 0
    """None"""

    CROSSPOSTED = 1 << 0
    """This message has been published to subscribed channels via channel following."""

    IS_CROSSPOST = 1 << 1
    """This message originated from a message in another channel via channel following."""

    SUPPRESS_EMBEDS = 1 << 2
    """Any embeds on this message should be omitted when serializing the message."""

    SOURCE_MESSAGE_DELETED = 1 << 3
    """The message this crosspost originated from was deleted via channel following."""

    URGENT = 1 << 4
    """This message came from the urgent message system."""


@more_enums.must_be_unique
class MessageActivityType(int, more_enums.Enum):
    """The type of a rich presence message activity."""

    NONE = 0
    """No activity."""

    JOIN = 1
    """Join an activity."""

    SPECTATE = 2
    """Spectating something."""

    LISTEN = 3
    """Listening to something."""

    JOIN_REQUEST = 5
    """Request to join an activity."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class Attachment(bases.UniqueEntity, marshaller.Deserializable):
    """Represents a file attached to a message."""

    filename: str = marshaller.attrib(deserializer=str)
    """The name of the file."""

    size: int = marshaller.attrib(deserializer=int)
    """The size of the file in bytes."""

    url: str = marshaller.attrib(deserializer=str)
    """The source URL of file."""

    proxy_url: str = marshaller.attrib(deserializer=str)
    """The proxied URL of file."""

    height: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None, default=None)
    """The height of the image (if the file is an image)."""

    width: typing.Optional[int] = marshaller.attrib(deserializer=int, if_undefined=None, default=None)
    """The width of the image (if the file is an image)."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class Reaction(bases.HikariEntity, marshaller.Deserializable):
    """Represents a reaction in a message."""

    count: int = marshaller.attrib(deserializer=int)
    """The amount of times the emoji has been used to react."""

    emoji: typing.Union[_emojis.UnicodeEmoji, _emojis.UnknownEmoji] = marshaller.attrib(
        deserializer=_emojis.deserialize_reaction_emoji, inherit_kwargs=True
    )
    """The emoji used to react."""

    is_reacted_by_me: bool = marshaller.attrib(raw_name="me", deserializer=bool)
    """Whether the current user reacted using this emoji."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageActivity(bases.HikariEntity, marshaller.Deserializable):
    """Represents the activity of a rich presence-enabled message."""

    type: MessageActivityType = marshaller.attrib(deserializer=MessageActivityType)
    """The type of message activity."""

    party_id: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, default=None)
    """The party ID of the message activity."""


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageCrosspost(bases.HikariEntity, marshaller.Deserializable):
    """Represents information about a cross-posted message and the origin of the original message."""

    message_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the original message.

    !!! warning
        This may be `None` in some cases according to the Discord API
        documentation, but the situations that cause this to occur are not
        currently documented.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel that the message originated from."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild that the message originated from.

    !!! warning
        This may be `None` in some cases according to the Discord API
        documentation, but the situations that cause this to occur are not
        currently documented.
    """


def _deserialize_object_mentions(payload: more_typing.JSONArray) -> typing.Set[bases.Snowflake]:
    return {bases.Snowflake(mention["id"]) for mention in payload}


def _deserialize_mentions(payload: more_typing.JSONArray) -> typing.Set[bases.Snowflake]:
    return {bases.Snowflake(mention) for mention in payload}


def _deserialize_attachments(payload: more_typing.JSONArray, **kwargs: typing.Any) -> typing.Sequence[Attachment]:
    return [Attachment.deserialize(attachment, **kwargs) for attachment in payload]


def _deserialize_embeds(payload: more_typing.JSONArray, **kwargs: typing.Any) -> typing.Sequence[_embeds.Embed]:
    return [_embeds.Embed.deserialize(embed, **kwargs) for embed in payload]


def _deserialize_reactions(payload: more_typing.JSONArray, **kwargs: typing.Any) -> typing.Sequence[Reaction]:
    return [Reaction.deserialize(reaction, **kwargs) for reaction in payload]


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class Message(bases.UniqueEntity, marshaller.Deserializable):
    """Represents a message."""

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake.deserialize)
    """The ID of the channel that the message was sent in."""

    guild_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """The ID of the guild that the message was sent in."""

    author: users.User = marshaller.attrib(deserializer=users.User.deserialize, inherit_kwargs=True)
    """The author of this message."""

    member: typing.Optional[guilds.GuildMember] = marshaller.attrib(
        deserializer=guilds.GuildMember.deserialize, if_undefined=None, default=None, inherit_kwargs=True
    )
    """The member properties for the message's author."""

    content: str = marshaller.attrib(deserializer=str)
    """The content of the message."""

    timestamp: datetime.datetime = marshaller.attrib(deserializer=conversions.parse_iso_8601_ts)
    """The timestamp that the message was sent at."""

    edited_timestamp: typing.Optional[datetime.datetime] = marshaller.attrib(
        deserializer=conversions.parse_iso_8601_ts, if_none=None
    )
    """The timestamp that the message was last edited at.

    Will be `None` if it wasn't ever edited.
    """

    is_tts: bool = marshaller.attrib(raw_name="tts", deserializer=bool)
    """Whether the message is a TTS message."""

    is_mentioning_everyone: bool = marshaller.attrib(raw_name="mention_everyone", deserializer=bool)
    """Whether the message mentions `@everyone` or `@here`."""

    user_mentions: typing.Set[bases.Snowflake] = marshaller.attrib(
        raw_name="mentions", deserializer=_deserialize_object_mentions,
    )
    """The users the message mentions."""

    role_mentions: typing.Set[bases.Snowflake] = marshaller.attrib(
        raw_name="mention_roles", deserializer=_deserialize_mentions,
    )
    """The roles the message mentions."""

    channel_mentions: typing.Set[bases.Snowflake] = marshaller.attrib(
        raw_name="mention_channels", deserializer=_deserialize_object_mentions, if_undefined=set, factory=set,
    )
    """The channels the message mentions."""

    attachments: typing.Sequence[Attachment] = marshaller.attrib(
        deserializer=_deserialize_attachments, inherit_kwargs=True
    )
    """The message attachments."""

    embeds: typing.Sequence[_embeds.Embed] = marshaller.attrib(deserializer=_deserialize_embeds, inherit_kwargs=True)
    """The message embeds."""

    reactions: typing.Sequence[Reaction] = marshaller.attrib(
        deserializer=_deserialize_reactions, if_undefined=list, factory=list, inherit_kwargs=True,
    )
    """The message reactions."""

    is_pinned: bool = marshaller.attrib(raw_name="pinned", deserializer=bool)
    """Whether the message is pinned."""

    webhook_id: typing.Optional[bases.Snowflake] = marshaller.attrib(
        deserializer=bases.Snowflake.deserialize, if_undefined=None, default=None
    )
    """If the message was generated by a webhook, the webhook's id."""

    type: MessageType = marshaller.attrib(deserializer=MessageType)
    """The message type."""

    activity: typing.Optional[MessageActivity] = marshaller.attrib(
        deserializer=MessageActivity.deserialize, if_undefined=None, default=None, inherit_kwargs=True,
    )
    """The message activity."""

    application: typing.Optional[applications.Application] = marshaller.attrib(
        deserializer=applications.Application.deserialize, if_undefined=None, default=None, inherit_kwargs=True,
    )
    """The message application."""

    message_reference: typing.Optional[MessageCrosspost] = marshaller.attrib(
        deserializer=MessageCrosspost.deserialize, if_undefined=None, default=None, inherit_kwargs=True,
    )
    """The message crossposted reference data."""

    flags: typing.Optional[MessageFlag] = marshaller.attrib(deserializer=MessageFlag, if_undefined=None, default=None)
    """The message flags."""

    nonce: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, default=None)
    """The message nonce. This is a string used for validating a message was sent."""

    def fetch_channel(self) -> typing.Coroutine[channels.Channel]:
        """Fetch the channel this message was created in.

        Returns
        -------
        typing.Coroutine[hikari.channels.Channel]
            The object of the channel this message belongs to.

        Raises
        ------
        hikari.errors.BadRequestHTTPError
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
        hikari.errors.ForbiddenHTTPError
            If you don't have access to the channel this message belongs to.
        hikari.errors.NotFoundHTTPError
            If the channel this message was created in does not exist.
        """
        return self._components.rest.fetch_channel(channel=self.channel_id)

    def reply(
        self,
        *,
        content: str = ...,
        nonce: str = ...,
        tts: bool = ...,
        files: typing.Sequence[_files.File] = ...,
        embed: _embeds.Embed = ...,
        mentions_everyone: bool = True,
        user_mentions: typing.Union[typing.Collection[bases.Hashable[users.User]], bool] = True,
        role_mentions: typing.Union[typing.Collection[bases.Hashable[guilds.GuildRole]], bool] = True,
    ) -> typing.Coroutine[Message]:
        """Create a message in the channel this message belongs to.

        Parameters
        ----------
        content : str
            If specified, the message content to send with the message.
        nonce : str
            If specified, an optional ID to send for opportunistic message
            creation. This doesn't serve any real purpose for general use,
            and can usually be ignored.
        tts : bool
            If specified, whether the message will be sent as a TTS message.
        files : typing.Sequence[hikari.files.File]
            If specified, a sequence of files to upload, if desired. Should be
            between 1 and 10 objects in size (inclusive), also including embed
            attachments.
        embed : hikari.embeds.Embed
            If specified, the embed object to send with the message.
        mentions_everyone : bool
            Whether `@everyone` and `@here` mentions should be resolved by
            discord and lead to actual pings, defaults to `True`.
        user_mentions : typing.Collection[typing.Union[hikari.users.User, hikari.bases.Snowflake, int]] OR bool
            Either an array of user objects/IDs to allow mentions for,
            `True` to allow all user mentions or `False` to block all
            user mentions from resolving, defaults to `True`.
        role_mentions: typing.Collection[typing.Union[hikari.guilds.GuildRole, hikari.bases.Snowflake, int]] OR bool
            Either an array of guild role objects/IDs to allow mentions for,
            `True` to allow all role mentions or `False` to block all
            role mentions from resolving, defaults to `True`.

        Returns
        -------
        typing.Coroutine[hikari.messages.Message]
            The created message object.

        Raises
        ------
        hikari.errors.NotFoundHTTPError
            If the channel this message was created in is not found.
        hikari.errors.BadRequestHTTPError
            This can be raised if the file is too large; if the embed exceeds
            the defined limits; if the message content is specified only and
            empty or greater than `2000` characters; if neither content, files
            or embed are specified.
            If any invalid snowflake IDs are passed; a snowflake may be invalid
            due to it being outside of the range of a 64 bit integer.
            If you are trying to upload more than 10 files in total (including
            embed attachments).
        hikari.errors.ForbiddenHTTPError
            If you lack permissions to send to the channel this message belongs
            to.
        ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        """
        return self._components.rest.create_message(
            channel=self.channel_id,
            content=content,
            nonce=nonce,
            tts=tts,
            files=files,
            embed=embed,
            mentions_everyone=mentions_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
        )
