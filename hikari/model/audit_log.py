#!/usr/bin/env python
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

from hikari import utils
from hikari.compat import typing
from hikari.model import base

from hikari.model import overwrite
from hikari.model import user
from hikari.model import webhook


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
    """

    NAME = enum.auto()
    ICON_HASH = enum.auto()
    SPLASH_HASH = enum.auto()
    OWNER_ID = enum.auto()
    REGION = enum.auto()
    AFK_CHANNEL_ID = enum.auto()
    AFK_TIMEOUT = enum.auto()
    MFA_LEVEL = enum.auto()
    VERIFICATION_LEVEL = enum.auto()
    EXPLICIT_CONTENT_FILTER = enum.auto()
    DEFAULT_MESSAGE_NOTIFICATIONS = enum.auto()
    VANITY_URL_CODE = enum.auto()
    ADD_ROLE = enum.auto()
    REMOVE_ROLE = enum.auto()
    PRUNE_DELETE_DAYS = enum.auto()
    WIDGET_ENABLED = enum.auto()
    WIDGET_CHANNEL_ID = enum.auto()
    POSITION = enum.auto()
    TOPIC = enum.auto()
    BITRATE = enum.auto()
    PERMISSION_OVERWRITES = enum.auto()
    NSFW = enum.auto()
    APPLICATION_ID = enum.auto()
    PERMISSIONS = enum.auto()
    COLOR = enum.auto()
    COLOUR = COLOR
    MENTIONABLE = enum.auto()
    CHANNEL_ID = enum.auto()
    INVITER_ID = enum.auto()
    MAX_USES = enum.auto()
    TEMPORARY = enum.auto()
    DEAF = enum.auto()
    MUTE = enum.auto()
    NICK = enum.auto()
    AVATAR_HASH = enum.auto()
    ID = enum.auto()
    TYPE = enum.auto()

    @classmethod
    def from_discord_name(cls: AuditLogChangeKey, name: str) -> AuditLogChangeKey:
        if name == "$add":
            return cls.ADD_ROLE
        if name == "$remove":
            return cls.REMOVE_ROLE
        # noinspection PyTypeChecker
        return super().from_discord_name(name)


@dataclasses.dataclass()
class AuditLog(base.Model):
    """
    An Audit Log.
    """

    __slots__ = ("webhooks", "users", "audit_log_entries")

    webhooks: typing.List[webhook.Webhook]
    users: typing.List[user.User]
    audit_log_entries: typing.List[AuditLogEntry]

    @classmethod
    def from_dict(cls: AuditLog, payload: utils.DiscordObject, state) -> AuditLog:
        """
        Create an AuditLog object from a dict payload.

        Args:
            payload: the payload to parse.
            state: the state to associate with the object.

        Returns:
            An AuditLog object.
        """
        return AuditLog(
            state,
            webhooks=[webhook.Webhook.from_dict(webhook, state) for webhook in payload["webhooks"]],
            users=[user.User.from_dict(user, state) for user in payload["users"]],
            audit_log_entries=[AuditLogEntry.from_dict(entry, state) for entry in payload["audit_log_entries"]],
        )


@dataclasses.dataclass()
class MemberPrunedAuditLogEntryInfo(base.Model):
    """
    Additional audit log info for member pruning.
    """

    __slots__ = ("delete_member_days", "members_removed")

    delete_member_days: int
    members_removed: int

    @classmethod
    def from_dict(cls: MemberPrunedAuditLogEntryInfo, payload: utils.DiscordObject, state) -> MemberPrunedAuditLogEntryInfo:
        """
        Create a MemberPrunedAuditLogEntryInfo object from a dict payload.

        Args:
            payload: the payload to parse.
            state: the state to associate with the object.

        Returns:
            A MemberPrunedAuditLogEntryInfo object.
        """
        return cls(
            state,
            delete_member_days=int(payload["delete_member_days"]),
            members_removed=int(payload["members_removed"]),
        )


@dataclasses.dataclass()
class MessageDeletedAuditLogEntryInfo(base.Model):
    """
    Additional audit log info for message deletions.
    """

    __slots__ = ("channel_id", "count")

    channel_id: int
    count: int

    @classmethod
    def from_dict(cls: MessageDeletedAuditLogEntryInfo, payload: utils.DiscordObject, state) -> MessageDeletedAuditLogEntryInfo:
        """
        Create an MessageDeletedAuditLogEntryInfo object from a dict payload.

        Args:
            payload: the payload to parse.
            state: the state to associate with the object.

        Returns:
            A MessageDeletedAuditLogEntryInfo object.
        """
        return cls(
            state, channel_id=int(payload["channel_id"]), count=int(payload["count"])
        )


@dataclasses.dataclass()
class ChannelOverwriteAuditLogEntryInfo(base.Model):
    """
    Additional audit log info for channel overwrites that changed.
    """

    __slots__ = ("id", "type", "role_name")

    id: int
    type: overwrite.OverwriteEntityType
    role_name: str

    @classmethod
    def from_dict(cls: ChannelOverwriteAuditLogEntryInfo, payload: utils.DiscordObject, state) -> ChannelOverwriteAuditLogEntryInfo:
        """
        Create a ChannelOverwriteAuditLogEntryInfo object from a dict payload.

        Args:
            payload: the payload to parse.
            state: the state to associate with the object.

        Returns:
            An ChannelOverwriteAuditLogEntryInfo object.
        """
        return cls(
            state,
            id=int(payload["id"]),
            type=overwrite.OverwriteEntityType.from_discord_name(payload["type"]),
            role_name=payload["role_name"],
        )


@dataclasses.dataclass()
class AuditLogChange(base.Model):
    """
    Represents a change that was recorded in the audit log.

    Warning:
        Currently `new_value` and `old_value` will be the raw types handed from Discord rather than the friendly type.
        This will be addressed in the future.
    """

    __slots__ = ("new_value", "old_value", "key")

    new_value: typing.Any
    old_value: typing.Any
    key: AuditLogChangeKey

    @classmethod
    def from_dict(cls: AuditLogChange, payload: utils.DiscordObject, state) -> AuditLogChange:
        """
        Create an AuditLogChange object from a dict payload.

        Args:
            payload: the payload to parse.
            state: the state to associate with the object.

        Returns:
            An AuditLogChange object.
        """

        key = AuditLogChangeKey.from_discord_name(payload["key"])
        return cls(state, new_value=payload["new_value"], old_value=payload["old_value"], key=key)


#: Valid types of additional Audit Log entry information.
AuditLogEntryInfo = typing.Union[
    MemberPrunedAuditLogEntryInfo, MessageDeletedAuditLogEntryInfo, ChannelOverwriteAuditLogEntryInfo, None
]


@dataclasses.dataclass()
class AuditLogEntry(base.Snowflake):
    """
    An entry within an Audit Log.
    """

    __slots__ = ("target_id", "changes", "user_id", "action_type", "options", "reason")

    target_id: typing.Optional[int]
    changes: typing.List[AuditLogChange]
    user_id: int
    action_type: AuditLogEvent
    options: AuditLogEntryInfo
    reason: typing.Optional[str]

    @classmethod
    def from_dict(cls: AuditLogEntry, payload: utils.DiscordObject, state) -> AuditLogEntry:
        """
        Create an AuditLogEntry object from a dict payload.

        Args:
            payload: the payload to parse.
            state: the state to associate with the object.

        Returns:
            An AuditLogEntry object.
        """
        action_type = AuditLogEvent[payload["action_type"]]
        options = payload.get("options")

        if action_type.name.startswith("CHANNEL_OVERWRITE_"):
            options = ChannelOverwriteAuditLogEntryInfo.from_dict(options, state)
        elif action_type is AuditLogEvent.MEMBER_PRUNE:
            options = MemberPrunedAuditLogEntryInfo.from_dict(options, state)
        elif action_type is AuditLogEvent.MESSAGE_DELETE:
            options = MessageDeletedAuditLogEntryInfo.from_dict(options, state)
        else:
            options = None

        return cls(
            state,
            target_id=utils.get_from_map_as(payload, "target_id", int, None),
            changes=[AuditLogChange.from_dict(change, state) for change in payload.get("changes", [])],
            user_id=utils.get_from_map_as(payload, "user_id", int),
            action_type=action_type,
            options=options,
            reason=utils.get_from_map_as(payload, "reason", str, None),
            id=utils.get_from_map_as(payload, "id", int),
        )
