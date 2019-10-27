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

from hikari.core.internal import state_registry
from hikari.core.models import base, reactions, webhooks
from hikari.core.models import channels
from hikari.core.models import embeds
from hikari.core.models import guilds
from hikari.core.models import media
from hikari.core.models import users
from hikari.core.utils import date_utils, auto_repr, custom_types
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
    #: Channel follow add
    CHANNEL_FOLLOW_ADD = 12


class MessageActivityType(enum.IntEnum):
    """
    The type of a rich presence message activity.
    """

    NONE = 0
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

    NONE = 0x0
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
class Message(base.Snowflake, base.HikariModel):
    """
    A message that was sent on Discord.
    """

    __slots__ = (
        "_state",
        "_channel_id",
        "_guild_id",
        "author",
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
        "crosspost_of",
    )

    __copy_by_ref__ = ("author",)

    _state: state_registry.StateRegistry
    _channel_id: int
    _guild_id: typing.Optional[int]

    #: Either a :type:`user.User`, a :type:`member.Member` or a :type:`webhook.Webhook` depending on what created the
    #: message and where.
    author: typing.Union[users.User, users.Member, webhooks.Webhook]

    #: The ID of the message.
    #:
    #: :type: :class:`int`
    id: int

    #: The actual textual content of the message.
    #:
    #: :type: :class:`str`
    content: typing.Optional[str]

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
    #: :type: :class:`typing.Sequence` of :class:`hikari.core.models.media.Attachment`
    attachments: typing.Sequence[media.Attachment]

    #: List of embeds on this message, if any.
    #:
    #: :type: :class:`typing.Sequence` of :class:`hikari.core.models.embed.Embed`
    embeds: typing.Sequence[embeds.Embed]

    #: Whether this message is pinned or not.
    #:
    #: :type: :class:`bool`
    pinned: bool

    #: The application associated with this message (applicable for rich presence-related chat embeds only).
    #:
    #: :type: :class:`hikari.core.models.message.MessageApplication` or `None`
    application: typing.Optional[MessageApplication]

    #: The activity associated with this message (applicable for rich presence-related chat embeds only).
    #:
    #: :type: :class:`hikari.core.models.message.MessageActivity` or `None`
    activity: typing.Optional[MessageActivity]

    #: The type of message.
    #:
    #: :type: :class:`hikari.core.models.message.MessageType`
    type: MessageType

    #: Flags applied to the message.
    #:
    #: :type: :class:`hikari.core.models.message.MessageFlag`
    flags: MessageFlag

    #: Message reactions, if any.
    #:
    #: :type: :class:`typing.List` of :class:`hikari.core.models.reaction.Reaction`
    reactions: typing.List[reactions.Reaction]

    #: Optional crossposting reference. Only valid if the message is a cross post.
    #:
    #: :type: :class:`hikari.core.models.message.MessageCrossPost` or `None` if not a cross post.
    crosspost_of: typing.Optional[MessageCrosspost]

    __repr__ = auto_repr.repr_of("id", "author", "type", "tts", "created_at", "edited_at")

    def __init__(self, global_state: state_registry.StateRegistry, payload):
        self._state = global_state
        self.id = int(payload["id"])

        self._channel_id = int(payload["channel_id"])
        self._guild_id = transform.nullable_cast(payload.get("guild_id"), int)

        if "webhook_id" in payload:
            self.author = global_state.parse_webhook(payload["author"])
        else:
            self.author = global_state.parse_user(payload["author"])

        self.tts = payload["tts"]
        self.crosspost_of = MessageCrosspost(payload["message_reference"]) if "message_reference" in payload else None
        self.flags = transform.try_cast(payload.get("flags"), MessageFlag, 0)
        self.type = transform.try_cast(payload.get("type"), MessageType)

        # These fields need an initial value, since they may not be specified, and our update state only accounts
        # for changes to the initial state due to Discord being consistently inconsistent in their API behaviour and
        # output... they won't specify what can change so I have to make an educated guess at this until I have
        # something more working that I can try this out with easily...
        self.reactions = []
        self.activity = None
        self.application = None
        self.edited_at = None
        self.mentions_everyone = False
        self.attachments = custom_types.EMPTY_SEQUENCE
        self.embeds = custom_types.EMPTY_SEQUENCE
        self.pinned = False
        self.application = None
        self.activity = None
        self.content = None

        self.update_state(payload)

    def update_state(self, payload: custom_types.DiscordObject) -> None:
        if "member" in payload:
            self.author = self._state.parse_member(payload["member"], self._guild_id)

        if "edited_timestamp" in payload:
            self.edited_at = transform.nullable_cast(payload.get("edited_timestamp"), date_utils.parse_iso_8601_ts)

        if "mention_everyone" in payload:
            self.mentions_everyone = payload["mention_everyone"]

        if "attachments" in payload:
            self.attachments = [media.Attachment(a) for a in payload["attachments"]]

        if "embeds" in payload:
            self.embeds = [embeds.Embed.from_dict(e) for e in payload["embeds"]]

        if "pinned" in payload:
            self.pinned = payload["pinned"]

        if "application" in payload:
            self.application = transform.nullable_cast(payload.get("application"), MessageApplication)

        if "activity" in payload:
            self.activity = transform.nullable_cast(payload.get("activity"), MessageActivity)

        if "content" in payload:
            self.content = payload.get("content")

        if "reactions" in payload:
            self.reactions = []
            for reaction_payload in payload.get("reactions"):
                self._state.parse_reaction(reaction_payload)

    @property
    def guild(self) -> typing.Optional[guilds.Guild]:
        return self._state.get_guild_by_id(self._guild_id) if self._guild_id else None

    @property
    def channel(
        self
    ) -> typing.Union[
        channels.GuildTextChannel,
        channels.GuildNewsChannel,
        channels.GuildStoreChannel,
        channels.DMChannel,
        channels.GroupDMChannel,
    ]:
        # We may as well just use this to get it. It is pretty much as fast, but it reduces the amount of testing
        # needed for code that is essentially the same.
        # noinspection PyTypeChecker
        return self._state.get_channel_by_id(self._channel_id)


@dataclasses.dataclass()
class MessageActivity:
    """
    Represents the activity of a rich presence-enabled message.
    """

    __slots__ = ("type", "party_id")

    #: The activity type of the message.
    #:
    #: :type: :class:`hikari.core.models.message.MessageActivityType`
    type: MessageActivityType

    #: The optional party ID associated with the message.
    #:
    #: :type: :class:`int` or `None`
    party_id: typing.Optional[int]

    __repr__ = auto_repr.repr_of("type", "party_id")

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

    __repr__ = auto_repr.repr_of("id", "name")

    def __init__(self, payload):
        self.id = int(payload["id"])
        self.cover_image_id = transform.nullable_cast(payload.get("cover_image"), int)
        self.description = payload["description"]
        self.icon_image_id = transform.nullable_cast(payload.get("icon"), int)
        self.name = payload.get("name")


@dataclasses.dataclass()
class MessageCrosspost:
    """
    Represents information about a cross-posted message and the origin of the original message.
    """

    __slots__ = ("message_id", "guild_id", "channel_id")

    #: The optional ID of the original message.
    #:
    #: Warning:
    #:     This may be `None` in some cases according to the Discord API
    #:     documentation, but the situations that cause this to occur are not currently documented.
    #:
    #: :type: :class:`int` or `None`.
    message_id: typing.Optional[int]

    #: The ID of the guild that the message originated from.
    #: :type: :class:`int`.
    channel_id: int

    #: The ID of the guild that the message originated from.
    #:
    #: Warning:
    #:     This may be `None` in some cases according to the Discord API
    #:     documentation, but the situations that cause this to occur are not currently documented.
    #:
    #: :type: :class:`int` or `None`.
    guild_id: typing.Optional[int]

    __repr__ = auto_repr.repr_of("message_id", "guild_id", "channel_id")

    def __init__(self, payload: custom_types.DiscordObject) -> None:
        # This is never null for some reason but the other two are... thanks Discord!
        self.channel_id = int(payload["channel_id"])

        self.message_id = transform.nullable_cast(payload.get("message_id"), int)
        self.guild_id = transform.nullable_cast(payload.get("guild_id"), int)


__all__ = [
    "MessageType",
    "MessageActivityType",
    "Message",
    "MessageActivity",
    "MessageApplication",
    "MessageCrosspost",
    "MessageFlag",
]
