#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
"""
Messages and attachments.
"""
from __future__ import annotations

import dataclasses
import datetime
import enum
import typing

from hikari.core.model import base
from hikari.core.model import channel
from hikari.core.model import embed
from hikari.core.model import guild
from hikari.core.model import media
from hikari.core.model import abstract_state_registry
from hikari.core.model import user
from hikari.core.utils import date_utils
from hikari.core.utils import transform


class MessageType(enum.IntEnum):
    """
    The type of a message.
    """

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


class MessageActivityType(enum.IntEnum):
    """
    The type of a rich presence message activity.
    """

    #: Join an activity.
    JOIN = 1
    #: Spectating something.
    SPECTATE = 2
    #: Listening to something.
    LISTEN = 3
    #: Request to join an activity.
    JOIN_REQUEST = 5


class MessageFlag(enum.IntFlag):
    """
    Additional flags for message options.
    """

    #: This message has been published to subscribed channels via channel following.
    CROSSPOSTED = 0x1
    #: This message originated from a message in another channel via channel following.
    IS_CROSSPOST = 0x2
    #: Any embeds on this message should be omitted when serializing the message.
    SUPPRESS_EMBEDS = 0x4


# Note: a lot of fields exist in the Message implementation that are not included here. Much of this information is
# able to be inferred from the information we are provided with, or is just unnecessary. For example, Nonce is omitted
# as there is no general use for it. Mentions can be found by scanning the message with a regular expression. Call
# information is not documented. Timestamp is pointless as it is able to be found from the ID anyway.


@dataclasses.dataclass()
class Message(base.Snowflake):
    """
    A message that was sent on Discord.
    """

    __slots__ = (
        "_state",
        "_channel_id",
        "_guild_id",
        "_author_id",
        "id",
        "edited_at",
        "reactions",
        "content",
        "tts",
        "mentions_everyone",
        "attachments",
        "embeds",
        "pinned",
        "application",
        "activity",
        "type",
        "flags",
    )

    _state: abstract_state_registry.AbstractStateRegistry
    _channel_id: int
    _guild_id: typing.Optional[int]
    _author_id: int

    #: The ID of the message.
    #:
    #: :type: :class:`int`
    id: int

    #: The actual textual content of the message.
    #:
    #: :type: :class:`str`
    content: str

    #: The timestamp that the message was last edited at, or `None` if not ever edited.
    #:
    #: :type: :class:`datetime.datetime` or `None`
    edited_at: typing.Optional[datetime.datetime]

    #: True if this message was a TTS message, False otherwise.
    #:
    #: :type: :class:`bool`
    tts: bool

    #: Whether this message mentions @everyone/@here or not.
    #:
    #: :type: :class:`bool`
    mentions_everyone: bool

    #: List of attachments on this message, if any.
    #:
    #: :type: :class:`list` of :class:`hikari.core.model.media.Attachment`
    attachments: typing.List[media.Attachment]

    #: List of embeds on this message, if any.
    #:
    #: :type: :class:`list` of :class:`hikari.core.model.embed.Embed`
    embeds: typing.List[embed.Embed]

    #: Whether this message is pinned or not.
    #:
    #: :type: :class:`bool`
    pinned: bool

    #: The application associated with this message (applicable for rich presence-related chat embeds only).
    #:
    #: :type: :class:`hikari.core.model.message.MessageApplication` or `None`
    application: typing.Optional[MessageApplication]

    #: The activity associated with this message (applicable for rich presence-related chat embeds only).
    #:
    #: :type: :class:`hikari.core.model.message.MessageActivity` or `None`
    activity: typing.Optional[MessageActivity]

    #: The type of message.
    #:
    #: :type: :class:`hikari.core.model.message.MessageType`
    type: MessageType

    #: Flags applied to the message.
    #:
    #: :type: :class:`hikari.core.model.message.MessageFlag`
    flags: MessageFlag

    def __init__(self, global_state: abstract_state_registry.AbstractStateRegistry, payload):
        self._state = global_state
        self.id = int(payload["id"])
        # FixMe: how does this work with webhooks?
        self._author_id = global_state.parse_user(payload["author"]).id
        self._channel_id = int(payload["channel_id"])
        self._guild_id = transform.nullable_cast(payload.get("guild_id"), int)
        self.edited_at = transform.nullable_cast(payload.get("edited_timestamp"), date_utils.parse_iso_8601_datetime)
        self.tts = payload["tts"]
        self.mentions_everyone = payload["mention_everyone"]
        self.attachments = [media.Attachment(a) for a in payload["attachments"]]
        self.embeds = [embed.Embed.from_dict(e) for e in payload["embeds"]]
        self.pinned = payload["pinned"]
        self.application = transform.nullable_cast(payload.get("application"), MessageApplication)
        self.activity = transform.nullable_cast(payload.get("activity"), MessageActivity)
        self.type = transform.try_cast(payload.get("type"), MessageType)
        self.content = payload.get("content")
        self.flags = transform.try_cast(payload.get("flags"), MessageFlag, 0)

    @property
    def guild(self) -> typing.Optional[guild.Guild]:
        return self._state.get_guild_by_id(self._guild_id) if self._guild_id else None

    @property
    def channel(
        self
    ) -> typing.Union[
        channel.GuildTextChannel,
        channel.GuildNewsChannel,
        channel.GuildStoreChannel,
        channel.DMChannel,
        channel.GroupDMChannel,
    ]:
        # We may as well just use this to get it. It is pretty much as fast, but it reduces the amount of testing
        # needed for code that is essentially the same.
        # noinspection PyTypeChecker
        return self._state.get_channel_by_id(self._channel_id)

    @property
    def author(self) -> typing.Union[user.User, user.Member, user.BotUser]:
        return self._state.get_user_by_id(self._author_id)


@dataclasses.dataclass()
class MessageActivity:
    """
    Represents the activity of a rich presence-enabled message.
    """

    __slots__ = ("type", "party_id")

    #: The activity type of the message.
    #:
    #: :type: :class:`hikari.core.model.message.MessageActivityType`
    type: MessageActivityType

    #: The optional party ID associated with the message.
    #:
    #: :type: :class:`int` or `None`
    party_id: typing.Optional[int]

    def __init__(self, payload):
        self.type = transform.try_cast(payload.get("type"), MessageActivityType)
        self.party_id = transform.nullable_cast(payload.get("party_id"), int)


@dataclasses.dataclass()
class MessageApplication(base.Snowflake):
    """
    Description of a rich presence application that created a rich presence message in a channel.
    """

    __slots__ = ("id", "cover_image_id", "description", "icon_image_id", "name")

    #: The ID of the application.
    #:
    #: :type: :class:`int`
    id: int

    #: The optional ID for the cover image of the application.
    #:
    #: :type: :class:`int` or `None`
    cover_image_id: typing.Optional[int]

    #: The application description
    #:
    #: :type: :class:`str`
    description: str

    #: The optional ID of the application's icon
    #:
    #: :type: :class:`str` or `None`
    icon_image_id: typing.Optional[int]

    #: The application name
    #:
    #: :type: :class:`str`
    name: str

    def __init__(self, payload):
        self.id = int(payload["id"])
        self.cover_image_id = transform.nullable_cast(payload.get("cover_image"), int)
        self.description = payload["description"]
        self.icon_image_id = transform.nullable_cast(payload.get("icon"), int)
        self.name = payload.get("name")


__all__ = ["MessageType", "MessageActivityType", "Message", "MessageActivity", "MessageApplication"]
