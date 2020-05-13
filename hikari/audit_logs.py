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
"""Components and entities that are used to describe audit logs on Discord."""

from __future__ import annotations

__all__ = [
    "AuditLog",
    "AuditLogChange",
    "AuditLogChangeKey",
    "AuditLogEntry",
    "AuditLogEventType",
    "AuditLogIterator",
    "BaseAuditLogEntryInfo",
    "ChannelOverwriteEntryInfo",
    "get_entry_info_entity",
    "MemberDisconnectEntryInfo",
    "MemberMoveEntryInfo",
    "MemberPruneEntryInfo",
    "MessageBulkDeleteEntryInfo",
    "MessageDeleteEntryInfo",
    "MessagePinEntryInfo",
    "UnrecognisedAuditLogEntryInfo",
]

import abc
import copy
import datetime
import typing

import attr

from hikari import bases
from hikari import channels
from hikari import colors
from hikari import guilds
from hikari import permissions
from hikari import users as _users
from hikari import webhooks as _webhooks
from hikari.internal import conversions
from hikari.internal import marshaller
from hikari.internal import more_collections
from hikari.internal import more_enums

if typing.TYPE_CHECKING:
    from hikari.clients import components as _components
    from hikari.internal import more_typing


class AuditLogChangeKey(str, more_enums.Enum):
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

    COLOUR = COLOR
    """Alias for "COLOR"""

    def __str__(self) -> str:
        return self.name

    __repr__ = __str__


def _deserialize_seconds_timedelta(seconds: typing.Union[str, int]) -> datetime.timedelta:
    return datetime.timedelta(seconds=int(seconds))


def _deserialize_partial_roles(
    payload: more_typing.JSONArray, **kwargs: typing.Any
) -> typing.Mapping[bases.Snowflake, guilds.GuildRole]:
    return {bases.Snowflake(role["id"]): guilds.PartialGuildRole.deserialize(role, **kwargs) for role in payload}


def _deserialize_day_timedelta(days: typing.Union[str, int]) -> datetime.timedelta:
    return datetime.timedelta(days=int(days))


def _deserialize_overwrites(
    payload: more_typing.JSONArray, **kwargs: typing.Any
) -> typing.Mapping[bases.Snowflake, channels.PermissionOverwrite]:
    return {
        bases.Snowflake(overwrite["id"]): channels.PermissionOverwrite.deserialize(overwrite, **kwargs)
        for overwrite in payload
    }


def _deserialize_max_uses(age: int) -> typing.Union[int, float]:
    return age if age > 0 else float("inf")


def _deserialize_max_age(seconds: int) -> typing.Optional[datetime.timedelta]:
    return datetime.timedelta(seconds=seconds) if seconds > 0 else None


AUDIT_LOG_ENTRY_CONVERTERS = {
    AuditLogChangeKey.OWNER_ID: bases.Snowflake,
    AuditLogChangeKey.AFK_CHANNEL_ID: bases.Snowflake,
    AuditLogChangeKey.AFK_TIMEOUT: _deserialize_seconds_timedelta,
    AuditLogChangeKey.MFA_LEVEL: guilds.GuildMFALevel,
    AuditLogChangeKey.VERIFICATION_LEVEL: guilds.GuildVerificationLevel,
    AuditLogChangeKey.EXPLICIT_CONTENT_FILTER: guilds.GuildExplicitContentFilterLevel,
    AuditLogChangeKey.DEFAULT_MESSAGE_NOTIFICATIONS: guilds.GuildMessageNotificationsLevel,
    AuditLogChangeKey.PRUNE_DELETE_DAYS: _deserialize_day_timedelta,
    AuditLogChangeKey.WIDGET_CHANNEL_ID: bases.Snowflake,
    AuditLogChangeKey.POSITION: int,
    AuditLogChangeKey.BITRATE: int,
    AuditLogChangeKey.APPLICATION_ID: bases.Snowflake,
    AuditLogChangeKey.PERMISSIONS: permissions.Permission,
    AuditLogChangeKey.COLOR: colors.Color,
    AuditLogChangeKey.ALLOW: permissions.Permission,
    AuditLogChangeKey.DENY: permissions.Permission,
    AuditLogChangeKey.CHANNEL_ID: bases.Snowflake,
    AuditLogChangeKey.INVITER_ID: bases.Snowflake,
    AuditLogChangeKey.MAX_USES: _deserialize_max_uses,
    AuditLogChangeKey.USES: int,
    AuditLogChangeKey.MAX_AGE: _deserialize_max_age,
    AuditLogChangeKey.ID: bases.Snowflake,
    AuditLogChangeKey.TYPE: str,
    AuditLogChangeKey.ENABLE_EMOTICONS: bool,
    AuditLogChangeKey.EXPIRE_BEHAVIOR: guilds.IntegrationExpireBehaviour,
    AuditLogChangeKey.EXPIRE_GRACE_PERIOD: _deserialize_day_timedelta,
    AuditLogChangeKey.RATE_LIMIT_PER_USER: _deserialize_seconds_timedelta,
    AuditLogChangeKey.SYSTEM_CHANNEL_ID: bases.Snowflake,
}

COMPONENT_BOUND_AUDIT_LOG_ENTRY_CONVERTERS = {
    AuditLogChangeKey.ADD_ROLE_TO_MEMBER: _deserialize_partial_roles,
    AuditLogChangeKey.REMOVE_ROLE_FROM_MEMBER: _deserialize_partial_roles,
    AuditLogChangeKey.PERMISSION_OVERWRITES: _deserialize_overwrites,
}


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class AuditLogChange(bases.Entity, marshaller.Deserializable):
    """Represents a change made to an audit log entry's target entity."""

    new_value: typing.Optional[typing.Any] = attr.attrib()
    """The new value of the key, if something was added or changed."""

    old_value: typing.Optional[typing.Any] = attr.attrib()
    """The old value of the key, if something was removed or changed."""

    key: typing.Union[AuditLogChangeKey, str] = attr.attrib()
    """The name of the audit log change's key."""

    @classmethod
    def deserialize(cls, payload: typing.Mapping[str, str], **kwargs: typing.Any) -> AuditLogChange:
        """Deserialize this model from a raw payload."""
        key = conversions.try_cast(payload["key"], AuditLogChangeKey, payload["key"])
        new_value = payload.get("new_value")
        old_value = payload.get("old_value")
        if value_converter := AUDIT_LOG_ENTRY_CONVERTERS.get(key):
            new_value = value_converter(new_value) if new_value is not None else None
            old_value = value_converter(old_value) if old_value is not None else None
        elif value_converter := COMPONENT_BOUND_AUDIT_LOG_ENTRY_CONVERTERS.get(key):
            new_value = value_converter(new_value, **kwargs) if new_value is not None else None
            old_value = value_converter(old_value, **kwargs) if old_value is not None else None

        # noinspection PyArgumentList
        return cls(key=key, new_value=new_value, old_value=old_value, **kwargs)


@more_enums.must_be_unique
class AuditLogEventType(int, more_enums.Enum):
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
) -> typing.Callable[[typing.Type[BaseAuditLogEntryInfo]], typing.Type[BaseAuditLogEntryInfo]]:  # noqa: D401
    """Generates a decorator for defined audit log entry info entities.

    Allows them to be associated with given entry type(s).

    Parameters
    ----------
    type_ : AuditLogEventType
        An entry types to associate the entity with.
    *additional_types : AuditLogEventType
        Extra entry types to associate the entity with.

    Returns
    -------
    decorator(T) -> T
        The decorator to decorate the class with.
    """

    def decorator(cls):
        mapping = getattr(register_audit_log_entry_info, "types", {})
        for t in [type_, *additional_types]:
            mapping[t] = cls
        setattr(register_audit_log_entry_info, "types", mapping)
        return cls

    return decorator


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class BaseAuditLogEntryInfo(bases.Entity, marshaller.Deserializable, abc.ABC):
    """A base object that all audit log entry info objects will inherit from."""


@register_audit_log_entry_info(
    AuditLogEventType.CHANNEL_OVERWRITE_CREATE,
    AuditLogEventType.CHANNEL_OVERWRITE_UPDATE,
    AuditLogEventType.CHANNEL_OVERWRITE_DELETE,
)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class ChannelOverwriteEntryInfo(BaseAuditLogEntryInfo):
    """Represents the extra information for overwrite related audit log entries.

    Will be attached to the overwrite create, update and delete audit log
    entries.
    """

    id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake)
    """The ID of the overwrite being updated, added or removed."""

    type: channels.PermissionOverwriteType = marshaller.attrib(deserializer=channels.PermissionOverwriteType)
    """The type of entity this overwrite targets."""

    role_name: typing.Optional[str] = marshaller.attrib(deserializer=str, if_undefined=None, default=None, repr=True)
    """The name of the role this overwrite targets, if it targets a role."""


@register_audit_log_entry_info(AuditLogEventType.MESSAGE_PIN, AuditLogEventType.MESSAGE_UNPIN)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessagePinEntryInfo(BaseAuditLogEntryInfo):
    """The extra information for message pin related audit log entries.

    Will be attached to the message pin and message unpin audit log entries.
    """

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake, repr=True)
    """The ID of the text based channel where a pinned message is being targeted."""

    message_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake, repr=True)
    """The ID of the message that's being pinned or unpinned."""


@register_audit_log_entry_info(AuditLogEventType.MEMBER_PRUNE)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MemberPruneEntryInfo(BaseAuditLogEntryInfo):
    """Represents the extra information attached to guild prune log entries."""

    delete_member_days: datetime.timedelta = marshaller.attrib(deserializer=_deserialize_day_timedelta, repr=True)
    """The timedelta of how many days members were pruned for inactivity based on."""

    members_removed: int = marshaller.attrib(deserializer=int, repr=True)
    """The number of members who were removed by this prune."""


@register_audit_log_entry_info(AuditLogEventType.MESSAGE_BULK_DELETE)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageBulkDeleteEntryInfo(BaseAuditLogEntryInfo):
    """Represents extra information for the message bulk delete audit entry."""

    count: int = marshaller.attrib(deserializer=int, repr=True)
    """The amount of messages that were deleted."""


@register_audit_log_entry_info(AuditLogEventType.MESSAGE_DELETE)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MessageDeleteEntryInfo(MessageBulkDeleteEntryInfo):
    """Represents extra information attached to the message delete audit entry."""

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake, repr=True)
    """The guild text based channel where these message(s) were deleted."""


@register_audit_log_entry_info(AuditLogEventType.MEMBER_DISCONNECT)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MemberDisconnectEntryInfo(BaseAuditLogEntryInfo):
    """Represents extra information for the voice chat member disconnect entry."""

    count: int = marshaller.attrib(deserializer=int, repr=True)
    """The amount of members who were disconnected from voice in this entry."""


@register_audit_log_entry_info(AuditLogEventType.MEMBER_MOVE)
@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class MemberMoveEntryInfo(MemberDisconnectEntryInfo):
    """Represents extra information for the voice chat based member move entry."""

    channel_id: bases.Snowflake = marshaller.attrib(deserializer=bases.Snowflake, repr=True)
    """The amount of members who were disconnected from voice in this entry."""


class UnrecognisedAuditLogEntryInfo(BaseAuditLogEntryInfo):
    """Represents any audit log entry options that haven't been implemented.

    !!! note
        This model has no slots and will have arbitrary undocumented attributes
        (in it's `__dict__` based on the received payload).
    """

    def __init__(self, payload: typing.Mapping[str, str]) -> None:
        self.__dict__.update(payload)

    @classmethod
    def deserialize(cls, payload: typing.Mapping[str, str], **_) -> UnrecognisedAuditLogEntryInfo:
        return cls(payload)


def get_entry_info_entity(type_: int) -> typing.Type[BaseAuditLogEntryInfo]:
    """Get the entity that's registered for an entry's options.

    Parameters
    ----------
    type_ : int
        The identifier for this entry type.

    Returns
    -------
    typing.Type[BaseAuditLogEntryInfo]
        The associated options entity. If not implemented then this will be
        `UnrecognisedAuditLogEntryInfo`.
    """
    types = getattr(register_audit_log_entry_info, "types", more_collections.EMPTY_DICT)
    entry_type = types.get(type_)
    return entry_type if entry_type is not None else UnrecognisedAuditLogEntryInfo


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class AuditLogEntry(bases.Unique, marshaller.Deserializable):
    """Represents an entry in a guild's audit log."""

    target_id: typing.Optional[bases.Snowflake] = attr.attrib()
    """The ID of the entity affected by this change, if applicable."""

    changes: typing.Sequence[AuditLogChange] = attr.attrib(repr=False)
    """A sequence of the changes made to `AuditLogEntry.target_id`."""

    user_id: bases.Snowflake = attr.attrib()
    """The ID of the user who made this change."""

    action_type: typing.Union[AuditLogEventType, str] = attr.attrib()
    """The type of action this entry represents."""

    options: typing.Optional[BaseAuditLogEntryInfo] = attr.attrib(repr=False)
    """Extra information about this entry. Only be provided for certain `action_type`."""

    reason: typing.Optional[str] = attr.attrib(repr=False)
    """The reason for this change, if set (between 0-512 characters)."""

    @classmethod
    def deserialize(cls, payload: more_typing.JSONObject, **kwargs: typing.Any) -> AuditLogEntry:
        """Deserialize this model from a raw payload."""
        action_type = conversions.try_cast(payload["action_type"], AuditLogEventType, payload["action_type"])
        if target_id := payload.get("target_id"):
            target_id = bases.Snowflake(target_id)

        if (options := payload.get("options")) is not None:
            option_converter = get_entry_info_entity(action_type)
            options = option_converter.deserialize(options, **kwargs)

        # noinspection PyArgumentList
        return cls(
            target_id=target_id,
            changes=[
                AuditLogChange.deserialize(payload, **kwargs)
                for payload in payload.get("changes", more_collections.EMPTY_SEQUENCE)
            ],
            user_id=bases.Snowflake(payload["user_id"]),
            id=bases.Snowflake(payload["id"]),
            action_type=action_type,
            options=options,
            reason=payload.get("reason"),
            **kwargs,
        )


def _deserialize_entries(
    payload: more_typing.JSONArray, **kwargs: typing.Any
) -> typing.Mapping[bases.Snowflake, AuditLogEntry]:
    return {bases.Snowflake(entry["id"]): AuditLogEntry.deserialize(entry, **kwargs) for entry in payload}


def _deserialize_integrations(
    payload: more_typing.JSONArray, **kwargs: typing.Any
) -> typing.Mapping[bases.Snowflake, guilds.GuildIntegration]:
    return {
        bases.Snowflake(integration["id"]): guilds.PartialGuildIntegration.deserialize(integration, **kwargs)
        for integration in payload
    }


def _deserialize_users(
    payload: more_typing.JSONArray, **kwargs: typing.Any
) -> typing.Mapping[bases.Snowflake, _users.User]:
    return {bases.Snowflake(user["id"]): _users.User.deserialize(user, **kwargs) for user in payload}


def _deserialize_webhooks(
    payload: more_typing.JSONArray, **kwargs: typing.Any
) -> typing.Mapping[bases.Snowflake, _webhooks.Webhook]:
    return {bases.Snowflake(webhook["id"]): _webhooks.Webhook.deserialize(webhook, **kwargs) for webhook in payload}


@marshaller.marshallable()
@attr.s(slots=True, kw_only=True)
class AuditLog(bases.Entity, marshaller.Deserializable):
    """Represents a guilds audit log."""

    entries: typing.Mapping[bases.Snowflake, AuditLogEntry] = marshaller.attrib(
        raw_name="audit_log_entries", deserializer=_deserialize_entries, inherit_kwargs=True,
    )
    """A sequence of the audit log's entries."""

    integrations: typing.Mapping[bases.Snowflake, guilds.GuildIntegration] = marshaller.attrib(
        deserializer=_deserialize_integrations, inherit_kwargs=True,
    )
    """A mapping of the partial objects of integrations found in this audit log."""

    users: typing.Mapping[bases.Snowflake, _users.User] = marshaller.attrib(
        deserializer=_deserialize_users, inherit_kwargs=True
    )
    """A mapping of the objects of users found in this audit log."""

    webhooks: typing.Mapping[bases.Snowflake, _webhooks.Webhook] = marshaller.attrib(
        deserializer=_deserialize_webhooks, inherit_kwargs=True,
    )
    """A mapping of the objects of webhooks found in this audit log."""


class AuditLogIterator(typing.AsyncIterator[AuditLogEntry]):
    """An async iterator used for iterating through a guild's audit log entries.

    This returns the audit log entries created before a given entry object/ID or
    from the newest audit log entry to the oldest.

    Parameters
    ----------
    components : hikari.clients.components.Components
        The `hikari.clients.components.Components` that this should pass through
        to the generated entities.
    request : typing.Callable[..., typing.Coroutine[typing.Any, typing.Any, typing.Any]]
        The prepared session bound partial function that this iterator should
        use for making Get Guild Audit Log requests.
    limit : int
        If specified, the limit to how many entries this iterator should return
        else unlimited.
    before : str
        If specified, an entry ID to specify where this iterator's returned
        audit log entries should start.

    Yields
    ------
    AuditLogEntry
        The entries found in this audit log.

    !!! note
        This iterator's attributes `AuditLogIterator.integrations`,
        `AuditLogIterator.users` and `AuditLogIterator.webhooks` will be filled
        up as this iterator makes requests to the Get Guild Audit Log endpoint
        with the relevant objects for entities referenced by returned entries.
    """

    __slots__ = (
        "_buffer",
        "_components",
        "_front",
        "_limit",
        "_request",
        "integrations",
        "users",
        "webhooks",
    )

    integrations: typing.MutableMapping[bases.Snowflake, guilds.GuildIntegration]
    """A mapping of the partial integrations objects found in this log so far."""

    users: typing.MutableMapping[bases.Snowflake, _users.User]
    """A mapping of the objects of users found in this audit log so far."""

    webhooks: typing.MutableMapping[bases.Snowflake, _webhooks.Webhook]
    """A mapping of the objects of webhooks found in this audit log so far."""

    def __init__(
        self,
        components: _components.Components,
        request: typing.Callable[..., more_typing.Coroutine[typing.Any]],
        before: typing.Optional[str] = str(bases.Snowflake.max()),
        limit: typing.Optional[int] = None,
    ) -> None:
        self._components = components
        self._limit = limit
        self._buffer = []
        self._request = request
        self._front = before
        self.users = {}
        self.webhooks = {}
        self.integrations = {}

    def __aiter__(self) -> AuditLogIterator:
        return self

    async def __anext__(self) -> AuditLogEntry:
        if not self._buffer and self._limit != 0:
            await self._fill()
        try:
            entry = AuditLogEntry.deserialize(self._buffer.pop(), components=self._components)
            self._front = str(entry.id)
            return entry
        except IndexError:
            raise StopAsyncIteration

    async def _fill(self) -> None:
        """Retrieve entries before `_front` and add to `_buffer`."""
        payload = await self._request(
            before=self._front, limit=100 if self._limit is None or self._limit > 100 else self._limit,
        )
        if self._limit is not None:
            self._limit -= len(payload["audit_log_entries"])

        # Once the resources has been exhausted, discord will return empty lists.
        payload["audit_log_entries"].reverse()
        self._buffer.extend(payload["audit_log_entries"])
        if users := payload.get("users"):
            self.users = copy.copy(self.users)
            self.users.update(
                {bases.Snowflake(u["id"]): _users.User.deserialize(u, components=self._components) for u in users}
            )
        if webhooks := payload.get("webhooks"):
            self.webhooks = copy.copy(self.webhooks)
            self.webhooks.update(
                {
                    bases.Snowflake(w["id"]): _webhooks.Webhook.deserialize(w, components=self._components)
                    for w in webhooks
                }
            )
        if integrations := payload.get("integrations"):
            self.integrations = copy.copy(self.integrations)
            self.integrations.update(
                {
                    bases.Snowflake(i["id"]): guilds.PartialGuildIntegration.deserialize(i, components=self._components)
                    for i in integrations
                }
            )
