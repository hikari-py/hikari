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
Models that describe audit logs for guilds.
"""
from __future__ import annotations

__all__ = (
    "AuditLogEvent",
    "AuditLogChangeKey",
    "AuditLog",
    "MemberPrunedAuditLogEntryInfo",
    "MessageDeletedAuditLogEntryInfo",
    "ChannelOverwriteAuditLogEntryInfo",
    "AuditLogChange",
    "AuditLogEntry",
)

import dataclasses
import enum
import typing

from hikari.model import base
from hikari.model import overwrite
from hikari.model import user
from hikari.model import webhook
from hikari.utils import maps


class AuditLogEvent(enum.IntEnum):
    """
    Type of audit log event that occurred.
    """

    GUILD_UPDATE = 1
    CHANNEL_CREATE = 10
    CHANNEL_UPDATE = 11
    CHANNEL_DELETE = 12
    CHANNEL_OVERWRITE_CREATE = 13
    CHANNEL_OVERWRITE_UPDATE = 14
    CHANNEL_OVERWRITE_DELETE = 15
    MEMBER_KICK = 20
    MEMBER_PRUNE = 21
    MEMBER_BAN_ADD = 22
    MEMBER_BAN_REMOVE = 23
    MEMBER_UPDATE = 24
    MEMBER_ROLE_UPDATE = 25
    ROLE_CREATE = 30
    ROLE_UPDATE = 31
    ROLE_DELETE = 32
    INVITE_CREATE = 40
    INVITE_UPDATE = 41
    INVITE_DELETE = 42
    WEBHOOK_CREATE = 50
    WEBHOOK_UPDATE = 51
    WEBHOOK_DELETE = 52
    EMOJI_CREATE = 60
    EMOJI_UPDATE = 61
    EMOJI_DELETE = 62
    MESSAGE_DELETE = 72


class AuditLogChangeKey(base.NamedEnum):
    """
    Describes what was changed in an audit log change.

    Note:
        Discord have failed to actually document this correctly, and as a result, these values are never checked
        to prevent any other undocumented changes from breaking this any further...

        Refer to the documentation for Audit Logs on the developer portal for the supposed "complete list".

        Essentially, attempting to access an entry that doesn't exist will not cause a failure, but just return
        that string instead of a hardcoded entry.
    """

    NAME = "name"
    ICON_HASH = "icon_hash"
    SPLASH_HASH = "splash_hash"
    OWNER_ID = "owner_id"
    REGION = "region"
    AFK_CHANNEL_ID = "afk_channel_id"
    AFK_TIMEOUT = "afk_timeout"
    MFA_LEVEL = "mfa_level"
    VERIFICATION_LEVEL = "verification_level"
    EXPLICIT_CONTENT_FILTER = "explicit_content_filter"
    DEFAULT_MESSAGE_NOTIFICATIONS = "default_message_notifications"
    VANITY_URL_CODE = "vanity_url_code"
    ADD_ROLE_TO_MEMBER = "$add"
    REMOVE_ROLE_FROM_MEMBER = "$remove"
    PRUNE_DELETE_DAYS = "prune_delete_days"
    WIDGET_ENABLED = "widget_enabled"
    WIDGET_CHANNEL_ID = "widget_channel_id"
    POSITION = "position"
    TOPIC = "topic"
    BITRATE = "bitrate"
    PERMISSION_OVERWRITES = "permission_overwrites"
    NSFW = "nsfw"
    APPLICATION_ID = "application_id"
    PERMISSIONS = "permissions"
    COLOR = "color"
    HOIST = "hoist"
    MENTIONABLE = "mentionable"
    ALLOW = "allow"
    DENY = "deny"
    CODE = "code"
    CHANNEL_ID = "channel_id"
    INVITER_ID = "inviter_id"
    MAX_USES = "max_uses"
    USES = "uses"
    MAX_AGE = "max_age"
    TEMPORARY = "temporary"
    DEAF = "deaf"
    MUTE = "mute"
    NICK = "nick"
    AVATAR_HASH = "avatar_hash"
    ID = "id"
    TYPE = "type"
    # Undocumented entries go here, I guess...
    RATE_LIMIT_PER_USER = "rate_limit_per_user"

    @classmethod
    def from_discord_name(cls, item):
        item = str(item)

        # Dumb edge cases, because why the hell not.
        if item == "$add":
            return cls.ADD_ROLE_TO_MEMBER
        if item == "$remove":
            return cls.REMOVE_ROLE_FROM_MEMBER

        try:
            return getattr(cls, item.upper())
        except AttributeError:
            return str(item).upper()

    @staticmethod
    def translate_values(old_value, new_value, key):
        """
        Consumes an old value, new value and key, and returns the correct types.
        
        Idea is to convert ID
        """
        str_key = str(key).lower()
        if old_value is not None and str_key.endswith("id"):
            old_value = int(old_value)
        if new_value is not None and str_key.endswith("id"):
            new_value = int(new_value)
        return old_value, new_value, key


@dataclasses.dataclass()
class AuditLog:
    """
    An Audit Log.
    """

    __slots__ = ("webhooks", "users", "entries")

    webhooks: typing.List[webhook.Webhook]
    users: typing.List[user.User]
    entries: typing.List[AuditLogEntry]

    @staticmethod
    def from_dict(payload):
        """
        Create an AuditLog object from a dict payload.

        Args:
            payload: the payload to parse.

        Returns:
            An AuditLog object.
        """
        return AuditLog(
            webhooks=[NotImplemented for _ in payload["webhooks"]],
            users=[NotImplemented for _ in payload["users"]],
            entries=[AuditLogEntry.from_dict(e) for e in payload["audit_log_entries"]],
        )


@dataclasses.dataclass()
class MemberPrunedAuditLogEntryInfo:
    """
    Additional audit log info for member pruning.
    """

    __slots__ = ("delete_member_days", "members_removed")

    delete_member_days: int
    members_removed: int

    @staticmethod
    def from_dict(payload):
        """
        Create a MemberPrunedAuditLogEntryInfo object from a dict payload.

        Args:
            payload: the payload to parse.

        Returns:
            A MemberPrunedAuditLogEntryInfo object.
        """
        return MemberPrunedAuditLogEntryInfo(
            delete_member_days=int(payload["delete_member_days"]), members_removed=int(payload["members_removed"])
        )


@dataclasses.dataclass()
class MessageDeletedAuditLogEntryInfo:
    """
    Additional audit log info for message deletions.
    """

    __slots__ = ("channel_id", "count")

    channel_id: int
    count: int

    @staticmethod
    def from_dict(payload):
        """
        Create an MessageDeletedAuditLogEntryInfo object from a dict payload.

        Args:
            payload: the payload to parse.

        Returns:
            A MessageDeletedAuditLogEntryInfo object.
        """
        return MessageDeletedAuditLogEntryInfo(channel_id=int(payload["channel_id"]), count=int(payload["count"]))


@dataclasses.dataclass()
class ChannelOverwriteAuditLogEntryInfo:
    """
    Additional audit log info for channel overwrites that changed.
    """

    __slots__ = ("id", "type", "role_name")

    id: int
    type: overwrite.OverwriteEntityType
    role_name: str

    @staticmethod
    def from_dict(payload):
        """
        Create a ChannelOverwriteAuditLogEntryInfo object from a dict payload.

        Args:
            payload: the payload to parse.

        Returns:
            An ChannelOverwriteAuditLogEntryInfo object.
        """
        return ChannelOverwriteAuditLogEntryInfo(
            id=int(payload["id"]),
            type=overwrite.OverwriteEntityType.from_discord_name(payload["type"]),
            role_name=payload["role_name"],
        )


@dataclasses.dataclass()
class AuditLogChange:
    """
    Represents a change that was recorded in the audit log.

    Warning:
        Currently `new_value` and `old_value` will be the raw types handed from Discord rather than the friendly type.
        This will be addressed in the future.
    """

    __slots__ = ("new_value", "old_value", "key")

    #: Note:
    #:      This key is NOT validated due to missing documentation in the Discord API. Instead, it is a pure string
    #:      to prevent further API changes on Discord's behalf breaking logic any further.
    key: typing.Union[AuditLogChangeKey, str]
    new_value: typing.Optional[typing.Any]
    old_value: typing.Optional[typing.Any]

    @staticmethod
    def from_dict(payload):
        """
        Create an AuditLogChange object from a dict payload.

        Args:
            payload: the payload to parse.

        Returns:
            An AuditLogChange object.
        """
        key = AuditLogChangeKey.from_discord_name(payload["key"])
        old_value, new_value, key = payload.get("old_value"), payload.get("new_value"), key
        old_value, new_value, key = AuditLogChangeKey.translate_values(old_value, new_value, key)
        return AuditLogChange(old_value=old_value, new_value=new_value, key=key)


#: Valid types of additional Audit Log entry information.
AuditLogEntryInfo = typing.Union[
    MemberPrunedAuditLogEntryInfo, MessageDeletedAuditLogEntryInfo, ChannelOverwriteAuditLogEntryInfo, None
]


@dataclasses.dataclass()
class AuditLogEntry(base.SnowflakeMixin):
    """
    An entry within an Audit Log.
    """

    __slots__ = ("id", "target_id", "changes", "user_id", "action_type", "options", "reason")

    id: int
    target_id: typing.Optional[int]
    changes: typing.List[AuditLogChange]
    user_id: int
    action_type: AuditLogEvent
    options: AuditLogEntryInfo
    reason: typing.Optional[str]

    @staticmethod
    def from_dict(payload):
        """
        Create an AuditLogEntry object from a dict payload.

        Args:
            payload:
                the payload to parse.

        Returns:
            An AuditLogEntry object.
        """
        action_type = AuditLogEvent(payload["action_type"])
        options = payload.get("options")

        if action_type.name.startswith("CHANNEL_OVERWRITE_"):
            options = ChannelOverwriteAuditLogEntryInfo.from_dict(options)
        elif action_type is AuditLogEvent.MEMBER_PRUNE:
            options = MemberPrunedAuditLogEntryInfo.from_dict(options)
        elif action_type is AuditLogEvent.MESSAGE_DELETE:
            options = MessageDeletedAuditLogEntryInfo.from_dict(options)
        else:
            options = None

        return AuditLogEntry(
            id=maps.get_from_map_as(payload, "id", int),
            target_id=maps.get_from_map_as(payload, "target_id", int, None),
            changes=[AuditLogChange.from_dict(change) for change in payload.get("changes", [])],
            user_id=maps.get_from_map_as(payload, "user_id", int),
            action_type=action_type,
            options=options,
            reason=maps.get_from_map_as(payload, "reason", str, None),
        )
