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
"""Components and entities that are used to describe audit logs on Discord.

.. inheritance-diagram::
    hikari.audit_logs
    :parts: 1
"""
__all__ = [
    "AuditLog",
    "AuditLogChange",
    "AuditLogChangeKey",
    "AuditLogEntry",
    "AuditLogEventType",
    "BaseAuditLogEntryInfo",
    "ChannelOverwriteEntryInfo",
    "get_entry_info_entity",
    "MemberDisconnectEntryInfo",
    "MemberMoveEntryInfo",
    "MemberPruneEntryInfo",
    "MessageBulkDeleteEntryInfo",
    "MessageDeleteEntryInfo",
    "MessagePinEntryInfo",
]

import abc
import datetime
import enum
import typing

from hikari import channels
from hikari import colors
from hikari import entities
from hikari import guilds
from hikari import permissions
from hikari import snowflakes
from hikari import users as _users
from hikari import webhooks as _webhooks
from hikari.internal import conversions
from hikari.internal import marshaller
from hikari.internal import more_collections


class AuditLogChangeKey(str, enum.Enum):
    """Commonly known and documented keys for audit log change objects.

    Others may exist. These should be expected to default to the raw string
    Discord provided us.
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
    ENABLE_EMOTICONS = "enable_emoticons"
    EXPIRE_BEHAVIOR = "expire_behavior"
    EXPIRE_GRACE_PERIOD = "expire_grace_period"
    RATE_LIMIT_PER_USER = "rate_limit_per_user"
    SYSTEM_CHANNEL_ID = "system_channel_id"

    #: Alias for "COLOR"
    COLOUR = COLOR

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


AUDIT_LOG_ENTRY_CONVERTERS = {
    AuditLogChangeKey.OWNER_ID: snowflakes.Snowflake.deserialize,
    AuditLogChangeKey.AFK_CHANNEL_ID: snowflakes.Snowflake.deserialize,
    AuditLogChangeKey.AFK_TIMEOUT: lambda payload: datetime.timedelta(seconds=payload),
    AuditLogChangeKey.MFA_LEVEL: guilds.GuildMFALevel,
    AuditLogChangeKey.VERIFICATION_LEVEL: guilds.GuildVerificationLevel,
    AuditLogChangeKey.EXPLICIT_CONTENT_FILTER: guilds.GuildExplicitContentFilterLevel,
    AuditLogChangeKey.DEFAULT_MESSAGE_NOTIFICATIONS: guilds.GuildMessageNotificationsLevel,
    AuditLogChangeKey.ADD_ROLE_TO_MEMBER: lambda payload: {
        role.id: role for role in map(guilds.PartialGuildRole.deserialize, payload)
    },
    AuditLogChangeKey.REMOVE_ROLE_FROM_MEMBER: lambda payload: {
        role.id: role for role in map(guilds.PartialGuildRole.deserialize, payload)
    },
    AuditLogChangeKey.PRUNE_DELETE_DAYS: lambda payload: datetime.timedelta(days=int(payload)),
    AuditLogChangeKey.WIDGET_CHANNEL_ID: snowflakes.Snowflake.deserialize,
    AuditLogChangeKey.POSITION: int,
    AuditLogChangeKey.BITRATE: int,
    AuditLogChangeKey.PERMISSION_OVERWRITES: lambda payload: {
        overwrite.id: overwrite for overwrite in map(channels.PermissionOverwrite.deserialize, payload)
    },
    AuditLogChangeKey.APPLICATION_ID: snowflakes.Snowflake.deserialize,
    AuditLogChangeKey.PERMISSIONS: permissions.Permission,
    AuditLogChangeKey.COLOR: colors.Color,
    AuditLogChangeKey.ALLOW: permissions.Permission,
    AuditLogChangeKey.DENY: permissions.Permission,
    AuditLogChangeKey.CHANNEL_ID: snowflakes.Snowflake.deserialize,
    AuditLogChangeKey.INVITER_ID: snowflakes.Snowflake.deserialize,
    AuditLogChangeKey.MAX_USES: lambda payload: int(payload) if payload > 0 else float("inf"),
    AuditLogChangeKey.USES: int,
    AuditLogChangeKey.MAX_AGE: lambda payload: datetime.timedelta(seconds=payload) if payload > 0 else None,
    AuditLogChangeKey.ID: snowflakes.Snowflake.deserialize,
    AuditLogChangeKey.TYPE: str,
    AuditLogChangeKey.ENABLE_EMOTICONS: bool,
    AuditLogChangeKey.EXPIRE_BEHAVIOR: guilds.IntegrationExpireBehaviour,
    AuditLogChangeKey.EXPIRE_GRACE_PERIOD: lambda payload: datetime.timedelta(days=payload),
    AuditLogChangeKey.RATE_LIMIT_PER_USER: lambda payload: datetime.timedelta(seconds=payload),
    AuditLogChangeKey.SYSTEM_CHANNEL_ID: snowflakes.Snowflake.deserialize,
}


@marshaller.attrs(slots=True)
class AuditLogChange(entities.HikariEntity, entities.Deserializable):
    """Represents a change made to an audit log entry's target entity."""

    #: The new value of the key, if something was added or changed.
    #:
    #: :type: :obj:`typing.Any`, optional
    new_value: typing.Optional[typing.Any] = marshaller.attrib()

    #: The old value of the key, if something was removed or changed.
    #:
    #: :type: :obj:`typing.Any`, optional
    old_value: typing.Optional[typing.Any] = marshaller.attrib()

    #: The name of the audit log change's key.
    #:
    #: :type: :obj:`typing.Union` [ :obj:`AuditLogChangeKey`, :obj:`str` ]
    key: typing.Union[AuditLogChangeKey, str] = marshaller.attrib()

    @classmethod
    def deserialize(cls, payload: entities.RawEntityT) -> "AuditLogChange":
        """Deserialize this model from a raw payload."""
        key = conversions.try_cast(payload["key"], AuditLogChangeKey, payload["key"])
        new_value = payload.get("new_value")
        old_value = payload.get("old_value")
        if value_converter := AUDIT_LOG_ENTRY_CONVERTERS.get(key):
            new_value = value_converter(new_value) if new_value is not None else None
            old_value = value_converter(old_value) if old_value is not None else None

        return cls(key=key, new_value=new_value, old_value=old_value)


@enum.unique
class AuditLogEventType(enum.IntEnum):
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


# Ignore docstring not starting in an imperative mood
def register_audit_log_entry_info(
    type_: AuditLogEventType, *additional_types: AuditLogEventType
) -> typing.Callable[[typing.Type["BaseAuditLogEntryInfo"]], typing.Type["BaseAuditLogEntryInfo"]]:  # noqa: D401
    """Generates a decorator for defined audit log entry info entities.

    Allows them to be associated with given entry type(s).

    Parameters
    ----------
    type_ : :obj:`AuditLogEventType`
        An entry types to associate the entity with.
    *additional_types : :obj:`AuditLogEventType`
        Extra entry types to associate the entity with.

    Returns
    -------
    ``decorator(cls: T) -> T``
        The decorator to decorate the class with.
    """

    def decorator(cls):
        mapping = getattr(register_audit_log_entry_info, "types", {})
        for t in [type_, *additional_types]:
            mapping[t] = cls
        setattr(register_audit_log_entry_info, "types", mapping)
        return cls

    return decorator


@marshaller.attrs(slots=True)
class BaseAuditLogEntryInfo(abc.ABC, entities.HikariEntity, entities.Deserializable):
    """A base object that all audit log entry info objects will inherit from."""


@register_audit_log_entry_info(
    AuditLogEventType.CHANNEL_OVERWRITE_CREATE,
    AuditLogEventType.CHANNEL_OVERWRITE_UPDATE,
    AuditLogEventType.CHANNEL_OVERWRITE_DELETE,
)
@marshaller.attrs(slots=True)
class ChannelOverwriteEntryInfo(BaseAuditLogEntryInfo):
    """Represents the extra information for overwrite related audit log entries.

    Will be attached to the overwrite create, update and delete audit log
    entries.
    """

    #: The ID of the overwrite being updated, added or removed (and the entity
    #: it targets).
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`
    id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake.deserialize)

    #: The type of entity this overwrite targets.
    #:
    #: :type: :obj:`hikari.channels.PermissionOverwriteType`
    type: channels.PermissionOverwriteType = marshaller.attrib(deserializer=channels.PermissionOverwriteType)

    #: The name of the role this overwrite targets, if it targets a role.
    #:
    #: :type: :obj:`str`, optional
    role_name: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None)


@register_audit_log_entry_info(AuditLogEventType.MESSAGE_PIN, AuditLogEventType.MESSAGE_UNPIN)
@marshaller.attrs(slots=True)
class MessagePinEntryInfo(BaseAuditLogEntryInfo):
    """The extra information for message pin related audit log entries.

    Will be attached to the message pin and message unpin audit log entries.
    """

    #: The ID of the guild text based channel where this pinned message is
    #: being added or removed.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`
    channel_id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake.deserialize)

    #: The ID of the message that's being pinned or unpinned.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`
    message_id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake.deserialize)


@register_audit_log_entry_info(AuditLogEventType.MEMBER_PRUNE)
@marshaller.attrs(slots=True)
class MemberPruneEntryInfo(BaseAuditLogEntryInfo):
    """Represents the extra information attached to guild prune log entries."""

    #: The timedelta of how many days members were pruned for inactivity based
    #: on.
    #:
    #: :type: :obj:`datetime.timedelta`
    delete_member_days: datetime.timedelta = marshaller.attrib(
        deserializer=lambda payload: datetime.timedelta(days=int(payload))
    )

    #: The number of members who were removed by this prune.
    #:
    #: :type: :obj:`int`
    members_removed: int = marshaller.attrib(deserializer=int)


@register_audit_log_entry_info(AuditLogEventType.MESSAGE_BULK_DELETE)
@marshaller.attrs(slots=True)
class MessageBulkDeleteEntryInfo(BaseAuditLogEntryInfo):
    """Represents extra information for the message bulk delete audit entry."""

    #: The amount of messages that were deleted.
    #:
    #: :type: :obj:`int`
    count: int = marshaller.attrib(deserializer=int)


@register_audit_log_entry_info(AuditLogEventType.MESSAGE_DELETE)
@marshaller.attrs(slots=True)
class MessageDeleteEntryInfo(MessageBulkDeleteEntryInfo):
    """Represents extra information attached to the message delete audit entry."""

    #: The guild text based channel where these message(s) were deleted.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`
    channel_id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake.deserialize)


@register_audit_log_entry_info(AuditLogEventType.MEMBER_DISCONNECT)
@marshaller.attrs(slots=True)
class MemberDisconnectEntryInfo(BaseAuditLogEntryInfo):
    """Represents extra information for the voice chat member disconnect entry."""

    #: The amount of members who were disconnected from voice in this entry.
    #:
    #: :type: :obj:`int`
    count: int = marshaller.attrib(deserializer=int)


@register_audit_log_entry_info(AuditLogEventType.MEMBER_MOVE)
@marshaller.attrs(slots=True)
class MemberMoveEntryInfo(MemberDisconnectEntryInfo):
    """Represents extra information for the voice chat based member move entry."""

    #: The channel these member(s) were moved to.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`
    channel_id: snowflakes.Snowflake = marshaller.attrib(deserializer=snowflakes.Snowflake.deserialize)


class UnrecognisedAuditLogEntryInfo(BaseAuditLogEntryInfo):
    """Represents any audit log entry options that haven't been implemented."""

    def __init__(self, payload: entities.RawEntityT) -> None:
        self.__dict__.update(payload)

    @classmethod
    def deserialize(cls, payload: entities.RawEntityT) -> "UnrecognisedAuditLogEntryInfo":
        return cls(payload)


def get_entry_info_entity(type_: int) -> typing.Type[BaseAuditLogEntryInfo]:
    """Get the entity that's registered for an entry's options.

    Parameters
    ----------
    :obj:`int`
        The int

    Returns
    -------
    :obj:`typing.Type` [ :obj:`BaseAuditLogEntryInfo` ]
        The associated options entity. If not implemented then this will be
        :obj:`UnrecognisedAuditLogEntryInfo`
    """
    return register_audit_log_entry_info.types.get(type_) or UnrecognisedAuditLogEntryInfo


@marshaller.attrs(slots=True)
class AuditLogEntry(snowflakes.UniqueEntity, entities.Deserializable):
    """Represents an entry in a guild's audit log."""

    #: The ID of the entity affected by this change, if applicable.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`, optional
    target_id: typing.Optional[snowflakes.Snowflake] = marshaller.attrib()

    #: A sequence of the changes made to :attr:`target_id`
    #:
    #: :type: :obj:`typing.Sequence` [ :obj:`AuditLogChange` ]
    changes: typing.Sequence[AuditLogChange] = marshaller.attrib()

    #: The ID of the user who made this change.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`
    user_id: snowflakes.Snowflake = marshaller.attrib()

    #: The ID of this entry.
    #:
    #: :type: :obj:`hikari.snowflakes.Snowflake`
    id: snowflakes.Snowflake = marshaller.attrib()

    #: The type of action this entry represents.
    #:
    #: :type: :obj:`typing.Union` [ :obj:`AuditLogEventType`, :obj:`str` ]
    action_type: typing.Union[AuditLogEventType, str] = marshaller.attrib()

    #: Extra information about this entry. Will only be provided for certain
    #: :attr:`action_type`.
    #:
    #: :type: :obj:`BaseAuditLogEntryInfo`, optional
    options: typing.Optional[BaseAuditLogEntryInfo] = marshaller.attrib()

    #: The reason for this change, if set (between 0-512 characters).
    #:
    #: :type: :obj:`str`
    reason: typing.Optional[str] = marshaller.attrib()

    @classmethod
    def deserialize(cls, payload: entities.RawEntityT) -> "AuditLogEntry":
        """Deserialize this model from a raw payload."""
        action_type = conversions.try_cast(payload["action_type"], AuditLogEventType, payload["action_type"])
        if target_id := payload.get("target_id"):
            target_id = snowflakes.Snowflake.deserialize(target_id)

        if (options := payload.get("options")) is not None:
            if option_converter := get_entry_info_entity(action_type):
                options = option_converter.deserialize(options)

        return cls(
            target_id=target_id,
            changes=[
                AuditLogChange.deserialize(payload)
                for payload in payload.get("changes", more_collections.EMPTY_SEQUENCE)
            ],
            user_id=snowflakes.Snowflake.deserialize(payload["user_id"]),
            id=snowflakes.Snowflake.deserialize(payload["id"]),
            action_type=action_type,
            options=options,
            reason=payload.get("reason"),
        )


@marshaller.attrs(slots=True)
class AuditLog(entities.HikariEntity, entities.Deserializable):
    """Represents a guilds audit log."""

    #: A sequence of the audit log's entries.
    #:
    #: :type: :obj:`typing.Mapping` [ :obj:`hikari.snowflakes.Snowflake`, :obj:`AuditLogEntry` ]
    entries: typing.Mapping[snowflakes.Snowflake, AuditLogEntry] = marshaller.attrib(
        raw_name="audit_log_entries",
        deserializer=lambda payload: {entry.id: entry for entry in map(AuditLogEntry.deserialize, payload)},
    )

    #: A mapping of the partial objects of integrations found in this audit log.
    #:
    #: :type: :obj:`typing.Mapping` [ :obj:`hikari.snowflakes.Snowflake`, :obj:`hikari.guilds.GuildIntegration` ]
    integrations: typing.Mapping[snowflakes.Snowflake, guilds.GuildIntegration] = marshaller.attrib(
        deserializer=lambda payload: {
            integration.id: integration for integration in map(guilds.PartialGuildIntegration.deserialize, payload)
        }
    )

    #: A mapping of the objects of users found in this audit log.
    #:
    #: :type: :obj:`typing.Mapping` [ :obj:`hikari.snowflakes.Snowflake`, :obj:`hikari.users.User` ]
    users: typing.Mapping[snowflakes.Snowflake, _users.User] = marshaller.attrib(
        deserializer=lambda payload: {user.id: user for user in map(_users.User.deserialize, payload)}
    )

    #: A mapping of the objects of webhooks found in this audit log.
    #:
    #: :type: :obj:`typing.Mapping` [ :obj:`hikari.snowflakes.Snowflake`, :obj:`hikari.webhooks.Webhook` ]
    webhooks: typing.Mapping[snowflakes.Snowflake, _webhooks.Webhook] = marshaller.attrib(
        deserializer=lambda payload: {webhook.id: webhook for webhook in map(_webhooks.Webhook.deserialize, payload)}
    )
