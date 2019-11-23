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
Audit Log models.
"""
from __future__ import annotations

import enum
import typing

from hikari.internal_utilities import data_structures
from hikari.internal_utilities import transformations
from hikari.orm import fabric
from hikari.orm.models import channels
from hikari.orm.models import colors
from hikari.orm.models import guilds
from hikari.orm.models import interfaces
from hikari.orm.models import overwrites
from hikari.orm.models import permissions
from hikari.orm.models import roles
from hikari.orm.models import users
from hikari.orm.models import webhooks
from hikari.orm.models import integrations


class AuditLog(interfaces.IModel):
    """
    Implementation of an Audit Log.
    """

    __slots__ = ("webhooks", "users", "integrations", "audit_log_entries")

    #: Set of the webhooks found in the audit log.
    #:
    #: :type: :class:`set` of :class:`hikari.orm.models.webhooks.Webhook`
    webhooks: typing.Set[webhooks.Webhook]

    #: Set of the users found in the audit log.
    #:
    #: :type: :class:`set` of :class:`hikari.orm.models.users.IUser`
    users: typing.Set[users.IUser]

    #: Set of the integrations found in the audit log.
    #:
    #: :type: :class:`set` of :class:`hikari.orm.models.integrations.PartialIntegration`
    integrations: typing.Set[integrations.PartialIntegration]

    #: Sequence of audit log entries.
    #:
    #: :type: :class:`typing.Sequence` of :class:`hikari.orm.models.audit_logs.AuditLogEntry`
    audit_log_entries: typing.Sequence[AuditLogEntry]

    def __init__(self, fabric_obj: fabric.Fabric, payload: data_structures.DiscordObjectT) -> None:
        self.webhooks = {
            fabric_obj.state_registry.parse_webhook(wh)
            for wh in payload.get("webhooks", data_structures.EMPTY_SEQUENCE)
        }
        self.users = {
            fabric_obj.state_registry.parse_user(u) for u in payload.get("users", data_structures.EMPTY_SEQUENCE)
        }
        self.integrations = {
            integrations.PartialIntegration(i) for i in payload.get("integrations", data_structures.EMPTY_SEQUENCE)
        }
        self.audit_log_entries = [
            AuditLogEntry(audit_log_entry)
            for audit_log_entry in payload.get("audit_log_entries", data_structures.EMPTY_SEQUENCE)
        ]


class AuditLogEntry(interfaces.ISnowflake):
    """
    Implementation of an Audit Log Entry.
    """

    __slots__ = ("id", "target_id", "changes", "user_id", "action_type", "options", "reason")

    #: The id of the effected entity.
    #:
    #: :type: :class:`int`
    target_id: typing.Optional[int]

    #: Sequence of changes made to the target entity.
    #:
    #: :type: :class:`typing.Sequence` of :class:`hikari.orm.models.audit_logs.AuditLogChange`
    changes: typing.Sequence[AuditLogChange]

    #: The id of the user who made the changes.
    #:
    #: :type: :class:`int`
    user_id: int

    #: The type of action for this entry.
    #:
    #: :type: :class:`hikari.orm.models.audit_logs.AuditLogEvent`
    action_type: AuditLogEvent

    #: Extra information provided for certain audit log events.
    #:
    #: :type: implementation of :class:`hikari.orm.models.audit_logs.IAuditLogEntryInfo` or `None`
    options: typing.Optional[IAuditLogEntryInfo]

    #: The reason for these changes.
    #:
    #: :type: :class:`str` or `None`
    reason: typing.Optional[str]

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.target_id = transformations.nullable_cast(payload.get("target_id"), int)
        self.changes = [AuditLogChange(change) for change in payload.get("changes", data_structures.EMPTY_SEQUENCE)]
        self.user_id = int(payload["user_id"])
        self.id = int(payload["id"])
        self.action_type = AuditLogEvent.get_best_effort_from_value(payload["action_type"])
        self.options = parse_audit_log_entry_info(payload.get("options"), self.action_type)
        self.reason = payload.get("reason")


class AuditLogEvent(interfaces.BestEffortEnumMixin, enum.IntEnum):
    """The type of event that occurred."""

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
    MEMBER_MOVE = 26
    MEMBER_DISCONNECT = 27
    BOT_ADD = 28
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
    MESSAGE_BULK_DELETE = 73
    MESSAGE_PIN = 74
    MESSAGE_UNPIN = 75
    INTEGRATION_CREATE = 80
    INTEGRATION_UPDATE = 81
    INTEGRATION_DELETE = 82


class IAuditLogEntryInfo(interfaces.IModel, interface=True):
    """An interface that all audit log entry option models inherit from."""

    _implementations: typing.ClassVar[typing.Dict[int, IAuditLogEntryInfo]] = {}

    __slots__ = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        for event_type in kwargs["event_types"]:
            cls._implementations[event_type.value] = cls


class AuditLogEntryCountInfo(
    IAuditLogEntryInfo, event_types=[AuditLogEvent.MESSAGE_BULK_DELETE, AuditLogEvent.MEMBER_DISCONNECT]
):
    """
    Extra information for MESSAGE_BULK_DELETE and MEMBER_DISCONNECT entries.
    """

    __slots__ = ("count",)

    #: The amount of entities targeted.
    #:
    #: :type: :class:`int`
    count: int

    def __init__(self, payload) -> None:
        self.count = int(payload["count"])


class MemberMoveAuditLogEntryInfo(IAuditLogEntryInfo, event_types=[AuditLogEvent.MEMBER_MOVE]):
    """
    Extra information for MEMBER_MOVE entries.
    """

    __slots__ = ("channel_id", "count")

    #: The amount of members moved.
    #:
    #: :type: :class:`int`
    count: int

    #: The id of the channel that the members were moved to.
    #:
    #: :type: :class:`int`
    channel_id: int

    def __init__(self, payload) -> None:
        self.count = int(payload["count"])
        self.channel_id = int(payload["channel_id"])


class MemberPruneAuditLogEntryInfo(IAuditLogEntryInfo, event_types=[AuditLogEvent.MEMBER_PRUNE]):
    """
    Extra information for MEMBER_PRUNE entries.
    """

    __slots__ = ("delete_member_days", "members_removed")

    #: The number of days after which inactive members were pruned.
    #:
    #: :type: :class:`int`
    delete_member_days: int

    #: The amount of members removed.
    #:
    #: :type: :class:`int`
    members_removed: int

    def __init__(self, payload) -> None:
        self.delete_member_days = int(payload["delete_member_days"])
        self.members_removed = int(payload["members_removed"])


class MessageDeleteAuditLogEntryInfo(IAuditLogEntryInfo, event_types=[AuditLogEvent.MESSAGE_DELETE]):
    """
    Extra information for MESSAGE_DELETE entries
    """

    __slots__ = ("channel_id", "count")

    #: The amount of messages deleted.
    #:
    #: :type: :class:`int`
    count: int

    #: The id of the channel where the messages were deleted.
    #:
    #: :type: :class:`int`
    channel_id: int

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.count = int(payload["count"])
        self.channel_id = int(payload["channel_id"])


class MessagePinAuditLogEntryInfo(
    IAuditLogEntryInfo, event_types=[AuditLogEvent.MESSAGE_PIN, AuditLogEvent.MESSAGE_UNPIN]
):
    """
    Extra information for Message Pin related entries.
    """

    __slots__ = ("channel_id", "message_id")

    #: The id of the channel where the message was pinned.
    #:
    #: :type: :class:`int`
    channel_id: int

    #: The id of the message that was pinned.
    #:
    #: :type: :class:`int`
    message_id: int

    def __init__(self, payload) -> None:
        self.channel_id = int(payload["channel_id"])
        self.message_id = int(payload["message_id"])


class ChannelOverwriteAuditLogEntryInfo(
    IAuditLogEntryInfo,
    event_types=[
        AuditLogEvent.CHANNEL_OVERWRITE_CREATE,
        AuditLogEvent.CHANNEL_OVERWRITE_UPDATE,
        AuditLogEvent.CHANNEL_OVERWRITE_DELETE,
    ],
):
    """
    Extra information for Channel Overwrite related entries.
    """

    __slots__ = ("id", "type")

    #: The id of the entity that was overwritten.
    #:
    #: :type: :class:`int`
    id: int

    #: The type of entity that was overwritten.
    #:
    #: :type: :class:`hikari.orm.models.overwrites.OverwriteEntityType`
    type: overwrites.OverwriteEntityType

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.id = int(payload["id"])
        self.type = overwrites.OverwriteEntityType.from_discord_name(payload["type"])


def parse_audit_log_entry_info(
    audit_log_entry_info_payload: data_structures.DiscordObjectT, event_type: int
) -> typing.Optional[IAuditLogEntryInfo]:
    """
    Parses a specific type of audit log entry info based on the given event type. If nothing corresponds
    to the additional info passed or the event_type given, then `None` is returned instead.
    """
    try:
        # noinspection PyProtectedMember
        return transformations.nullable_cast(
            audit_log_entry_info_payload, IAuditLogEntryInfo._implementations[event_type]
        )
    except KeyError:
        return None


class AuditLogChangeKey(str, interfaces.BestEffortEnumMixin, enum.Enum):
    """
    Commonly known and documented keys for audit log change objects.

    Others may exist. These should be expected to default to the raw string Discord provided us.

    When handling these, always use :meth:`str` to cast these to a readable format for safety.

    See https://discordapp.com/developers/docs/resources/audit-log#audit-log-change-object-audit-log-change-key
    for a full description.
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
    INVITE_CODE = "code"
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
    ACCOUNT_ID = "account_id"
    ENABLE_EMOTICONS = "enable_emoticons"
    EXPIRE_BEHAVIOR = "expire_behavior"
    EXPIRE_GRACE_PERIOD = "expire_grace_period"

    #: |undocumented|
    RATE_LIMIT_PER_USER = "rate_limit_per_user"

    #: Alias for "COLOR"
    COLOUR = COLOR

    def __str__(self):
        return self.name


def _new_id_map_of(converter):
    return lambda items: transformations.id_map((converter(item) for item in items))


def _new_sequence_of(converter):
    return lambda items: [converter(item) for item in items]


def _type_converter(type_entity):
    # Discord says if this is an int, it is probably a channel type, otherwise it is a name.
    # Try to parse the channel type, returning an int if it is unrecognised, or if we get a string,
    # then just return that instead.
    if isinstance(type_entity, int):
        return channels.Channel.get_channel_class_from_type(type_entity) or type_entity
    return type_entity


AUDIT_LOG_ENTRY_CONVERTERS = {
    AuditLogChangeKey.OWNER_ID: int,
    AuditLogChangeKey.AFK_CHANNEL_ID: int,
    AuditLogChangeKey.MFA_LEVEL: guilds.MFALevel,
    AuditLogChangeKey.VERIFICATION_LEVEL: guilds.VerificationLevel,
    AuditLogChangeKey.EXPLICIT_CONTENT_FILTER: guilds.ExplicitContentFilterLevel,
    AuditLogChangeKey.DEFAULT_MESSAGE_NOTIFICATIONS: guilds.DefaultMessageNotificationsLevel,
    AuditLogChangeKey.ADD_ROLE_TO_MEMBER: _new_id_map_of(roles.PartialRole),
    AuditLogChangeKey.REMOVE_ROLE_FROM_MEMBER: _new_id_map_of(roles.PartialRole),
    AuditLogChangeKey.WIDGET_CHANNEL_ID: int,
    AuditLogChangeKey.PERMISSION_OVERWRITES: _new_sequence_of(overwrites.Overwrite),
    AuditLogChangeKey.APPLICATION_ID: int,
    AuditLogChangeKey.PERMISSIONS: permissions.Permission,
    AuditLogChangeKey.COLOR: colors.Color,
    AuditLogChangeKey.ALLOW: permissions.Permission,
    AuditLogChangeKey.DENY: permissions.Permission,
    AuditLogChangeKey.CHANNEL_ID: int,
    AuditLogChangeKey.INVITER_ID: int,
    AuditLogChangeKey.ID: int,
    AuditLogChangeKey.TYPE: _type_converter,
    AuditLogChangeKey.ACCOUNT_ID: int,
    AuditLogChangeKey.ENABLE_EMOTICONS: bool,
    AuditLogChangeKey.EXPIRE_BEHAVIOR: int,
    AuditLogChangeKey.EXPIRE_GRACE_PERIOD: int,
}


class AuditLogChange(interfaces.IModel):
    """
    Implementation of the Audit Log Change Object.
    """

    __slots__ = ("key", "old_value", "new_value")

    #: The name of the audit log change key.
    #:
    #: :type: :class:`str`
    key: str

    #: The old value of the key.
    #:
    #: :type: :class:`typing.Any` or `None`
    old_value: typing.Optional[typing.Any]

    #: The new value of the key.
    #:
    #: :type: :class:`typing.Any` or `None`
    new_value: typing.Optional[typing.Any]

    def __init__(self, payload: data_structures.DiscordObjectT) -> None:
        self.key = AuditLogChangeKey.get_best_effort_from_value(payload["key"])
        converter = AUDIT_LOG_ENTRY_CONVERTERS.get(self.key, lambda x: x)
        self.old_value = transformations.nullable_cast(payload.get("old_value"), converter)
        self.new_value = transformations.nullable_cast(payload.get("new_value"), converter)
