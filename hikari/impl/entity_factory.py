# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Basic implementation of an entity factory for general bots and HTTP apps."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["EntityFactoryImpl"]

import datetime
import typing

import attr

from hikari import applications as application_models
from hikari import audit_logs as audit_log_models
from hikari import channels as channel_models
from hikari import colors as color_models
from hikari import embeds as embed_models
from hikari import emojis as emoji_models
from hikari import files
from hikari import guilds as guild_models
from hikari import invites as invite_models
from hikari import messages as message_models
from hikari import permissions as permission_models
from hikari import presences as presence_models
from hikari import sessions as gateway_models
from hikari import snowflakes
from hikari import traits
from hikari import undefined
from hikari import users as user_models
from hikari import voices as voice_models
from hikari import webhooks as webhook_models
from hikari.api import entity_factory
from hikari.utilities import attr_extensions
from hikari.utilities import data_binding
from hikari.utilities import date


def _deserialize_seconds_timedelta(seconds: typing.Union[str, int]) -> datetime.timedelta:
    return datetime.timedelta(seconds=int(seconds))


def _deserialize_day_timedelta(days: typing.Union[str, int]) -> datetime.timedelta:
    return datetime.timedelta(days=int(days))


def _deserialize_max_uses(age: int) -> typing.Optional[int]:
    return age if age > 0 else None


def _deserialize_max_age(seconds: int) -> typing.Optional[datetime.timedelta]:
    return datetime.timedelta(seconds=seconds) if seconds > 0 else None


@attr_extensions.with_copy
@attr.s(init=True, kw_only=True, repr=False, slots=True, weakref_slot=False)
class _PartialGuildFields:
    id: snowflakes.Snowflake = attr.ib()
    name: str = attr.ib()
    icon_hash: str = attr.ib()
    features: typing.Sequence[typing.Union[guild_models.GuildFeature, str]] = attr.ib()


@attr_extensions.with_copy
@attr.s(init=True, kw_only=True, repr=False, slots=True, weakref_slot=False)
class _GuildChannelFields:
    id: snowflakes.Snowflake = attr.ib()
    name: typing.Optional[str] = attr.ib()
    type: channel_models.ChannelType = attr.ib()
    guild_id: snowflakes.Snowflake = attr.ib()
    position: int = attr.ib()
    permission_overwrites: typing.Mapping[snowflakes.Snowflake, channel_models.PermissionOverwrite] = attr.ib()
    is_nsfw: typing.Optional[bool] = attr.ib()
    parent_id: typing.Optional[snowflakes.Snowflake] = attr.ib()


@attr_extensions.with_copy
@attr.s(init=True, kw_only=True, repr=False, slots=True, weakref_slot=False)
class _IntegrationFields:
    id: snowflakes.Snowflake = attr.ib()
    name: str = attr.ib()
    type: str = attr.ib()
    account: guild_models.IntegrationAccount = attr.ib()


@attr_extensions.with_copy
@attr.s(init=True, kw_only=True, repr=False, slots=True, weakref_slot=False)
class _GuildFields(_PartialGuildFields):
    splash_hash: typing.Optional[str] = attr.ib()
    discovery_splash_hash: typing.Optional[str] = attr.ib()
    owner_id: snowflakes.Snowflake = attr.ib()
    region: str = attr.ib()
    afk_channel_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    afk_timeout: datetime.timedelta = attr.ib()
    verification_level: guild_models.GuildVerificationLevel = attr.ib()
    default_message_notifications: guild_models.GuildMessageNotificationsLevel = attr.ib()
    explicit_content_filter: guild_models.GuildExplicitContentFilterLevel = attr.ib()
    mfa_level: guild_models.GuildMFALevel = attr.ib()
    application_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    widget_channel_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    system_channel_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    is_widget_enabled: typing.Optional[bool] = attr.ib()
    system_channel_flags: guild_models.GuildSystemChannelFlag = attr.ib()
    rules_channel_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    max_presences: typing.Optional[int] = attr.ib()
    max_members: typing.Optional[int] = attr.ib()
    max_video_channel_users: typing.Optional[int] = attr.ib()
    vanity_url_code: typing.Optional[str] = attr.ib()
    description: typing.Optional[str] = attr.ib()
    banner_hash: typing.Optional[str] = attr.ib()
    premium_tier: guild_models.GuildPremiumTier = attr.ib()
    premium_subscription_count: typing.Optional[int] = attr.ib()
    preferred_locale: str = attr.ib()
    public_updates_channel_id: typing.Optional[snowflakes.Snowflake] = attr.ib()


@attr_extensions.with_copy
@attr.s(init=True, kw_only=True, repr=False, slots=True, weakref_slot=False)
class _InviteFields:
    code: str = attr.ib()
    guild: typing.Optional[invite_models.InviteGuild] = attr.ib()
    guild_id: typing.Optional[snowflakes.Snowflake] = attr.ib()
    channel: typing.Optional[channel_models.PartialChannel] = attr.ib()
    channel_id: snowflakes.Snowflake = attr.ib()
    inviter: typing.Optional[user_models.User] = attr.ib()
    target_user: typing.Optional[user_models.User] = attr.ib()
    target_user_type: typing.Optional[invite_models.TargetUserType] = attr.ib()
    approximate_presence_count: typing.Optional[int] = attr.ib()
    approximate_member_count: typing.Optional[int] = attr.ib()


@attr_extensions.with_copy
@attr.s(init=True, kw_only=True, repr=False, slots=True, weakref_slot=False)
class _UserFields:
    id: snowflakes.Snowflake = attr.ib()
    discriminator: str = attr.ib()
    username: str = attr.ib()
    avatar_hash: str = attr.ib()
    is_bot: bool = attr.ib()
    is_system: bool = attr.ib()


class EntityFactoryImpl(entity_factory.EntityFactory):
    """Standard implementation for a serializer/deserializer.

    This will convert objects to/from JSON compatible representations.
    """

    __slots__: typing.Sequence[str] = (
        "_app",
        "_audit_log_entry_converters",
        "_audit_log_event_mapping",
        "_dm_channel_type_mapping",
        "_guild_channel_type_mapping",
    )

    def __init__(self, app: traits.RESTAware) -> None:
        self._app = app
        self._audit_log_entry_converters: typing.Mapping[str, typing.Callable[[typing.Any], typing.Any]] = {
            audit_log_models.AuditLogChangeKey.OWNER_ID: snowflakes.Snowflake,
            audit_log_models.AuditLogChangeKey.AFK_CHANNEL_ID: snowflakes.Snowflake,
            audit_log_models.AuditLogChangeKey.AFK_TIMEOUT: _deserialize_seconds_timedelta,
            audit_log_models.AuditLogChangeKey.MFA_LEVEL: guild_models.GuildMFALevel,
            audit_log_models.AuditLogChangeKey.VERIFICATION_LEVEL: guild_models.GuildVerificationLevel,
            audit_log_models.AuditLogChangeKey.EXPLICIT_CONTENT_FILTER: guild_models.GuildExplicitContentFilterLevel,
            audit_log_models.AuditLogChangeKey.DEFAULT_MESSAGE_NOTIFICATIONS: guild_models.GuildMessageNotificationsLevel,
            # noqa: E501 - Line too long
            audit_log_models.AuditLogChangeKey.PRUNE_DELETE_DAYS: _deserialize_day_timedelta,
            audit_log_models.AuditLogChangeKey.WIDGET_CHANNEL_ID: snowflakes.Snowflake,
            audit_log_models.AuditLogChangeKey.POSITION: int,
            audit_log_models.AuditLogChangeKey.BITRATE: int,
            audit_log_models.AuditLogChangeKey.APPLICATION_ID: snowflakes.Snowflake,
            audit_log_models.AuditLogChangeKey.PERMISSIONS: permission_models.Permissions,
            audit_log_models.AuditLogChangeKey.COLOR: color_models.Color,
            audit_log_models.AuditLogChangeKey.ALLOW: permission_models.Permissions,
            audit_log_models.AuditLogChangeKey.DENY: permission_models.Permissions,
            audit_log_models.AuditLogChangeKey.CHANNEL_ID: snowflakes.Snowflake,
            audit_log_models.AuditLogChangeKey.INVITER_ID: snowflakes.Snowflake,
            audit_log_models.AuditLogChangeKey.MAX_USES: _deserialize_max_uses,
            audit_log_models.AuditLogChangeKey.USES: int,
            audit_log_models.AuditLogChangeKey.MAX_AGE: _deserialize_max_age,
            audit_log_models.AuditLogChangeKey.ID: snowflakes.Snowflake,
            audit_log_models.AuditLogChangeKey.TYPE: str,
            audit_log_models.AuditLogChangeKey.ENABLE_EMOTICONS: bool,
            audit_log_models.AuditLogChangeKey.EXPIRE_BEHAVIOR: guild_models.IntegrationExpireBehaviour,
            audit_log_models.AuditLogChangeKey.EXPIRE_GRACE_PERIOD: _deserialize_day_timedelta,
            audit_log_models.AuditLogChangeKey.RATE_LIMIT_PER_USER: _deserialize_seconds_timedelta,
            audit_log_models.AuditLogChangeKey.SYSTEM_CHANNEL_ID: snowflakes.Snowflake,
            audit_log_models.AuditLogChangeKey.ADD_ROLE_TO_MEMBER: self._deserialize_audit_log_change_roles,
            audit_log_models.AuditLogChangeKey.REMOVE_ROLE_FROM_MEMBER: self._deserialize_audit_log_change_roles,
            audit_log_models.AuditLogChangeKey.PERMISSION_OVERWRITES: self._deserialize_audit_log_overwrites,
        }
        self._audit_log_event_mapping: typing.Mapping[
            typing.Union[int, audit_log_models.AuditLogEventType],
            typing.Callable[[data_binding.JSONObject], audit_log_models.BaseAuditLogEntryInfo],
        ] = {
            audit_log_models.AuditLogEventType.CHANNEL_OVERWRITE_CREATE: self._deserialize_channel_overwrite_entry_info,
            audit_log_models.AuditLogEventType.CHANNEL_OVERWRITE_UPDATE: self._deserialize_channel_overwrite_entry_info,
            audit_log_models.AuditLogEventType.CHANNEL_OVERWRITE_DELETE: self._deserialize_channel_overwrite_entry_info,
            audit_log_models.AuditLogEventType.MESSAGE_PIN: self._deserialize_message_pin_entry_info,
            audit_log_models.AuditLogEventType.MESSAGE_UNPIN: self._deserialize_message_pin_entry_info,
            audit_log_models.AuditLogEventType.MEMBER_PRUNE: self._deserialize_member_prune_entry_info,
            audit_log_models.AuditLogEventType.MESSAGE_BULK_DELETE: self._deserialize_message_bulk_delete_entry_info,
            audit_log_models.AuditLogEventType.MESSAGE_DELETE: self._deserialize_message_delete_entry_info,
            audit_log_models.AuditLogEventType.MEMBER_DISCONNECT: self._deserialize_member_disconnect_entry_info,
            audit_log_models.AuditLogEventType.MEMBER_MOVE: self._deserialize_member_move_entry_info,
        }
        self._dm_channel_type_mapping = {
            channel_models.ChannelType.PRIVATE_TEXT: self.deserialize_private_text_channel,
            channel_models.ChannelType.PRIVATE_GROUP_TEXT: self.deserialize_private_group_text_channel,
        }
        self._guild_channel_type_mapping = {
            channel_models.ChannelType.GUILD_CATEGORY: self.deserialize_guild_category,
            channel_models.ChannelType.GUILD_TEXT: self.deserialize_guild_text_channel,
            channel_models.ChannelType.GUILD_NEWS: self.deserialize_guild_news_channel,
            channel_models.ChannelType.GUILD_STORE: self.deserialize_guild_store_channel,
            channel_models.ChannelType.GUILD_VOICE: self.deserialize_guild_voice_channel,
        }

    ######################
    # APPLICATION MODELS #
    ######################

    def deserialize_own_connection(self, payload: data_binding.JSONObject) -> application_models.OwnConnection:
        if (integration_payloads := payload.get("integrations")) is not None:
            integrations = [self.deserialize_partial_integration(integration) for integration in integration_payloads]
        else:
            integrations = []

        return application_models.OwnConnection(
            id=payload["id"],
            name=payload["name"],
            type=payload["type"],
            is_revoked=payload["revoked"],
            integrations=integrations,
            is_verified=payload["verified"],
            is_friend_sync_enabled=payload["friend_sync"],
            is_activity_visible=payload["show_activity"],
            visibility=application_models.ConnectionVisibility(payload["visibility"]),
        )

    def deserialize_own_guild(self, payload: data_binding.JSONObject) -> application_models.OwnGuild:
        guild_fields = self._set_partial_guild_attributes(payload)
        return application_models.OwnGuild(
            app=self._app,
            id=guild_fields.id,
            name=guild_fields.name,
            icon_hash=guild_fields.icon_hash,
            features=guild_fields.features,
            is_owner=bool(payload["owner"]),
            my_permissions=permission_models.Permissions(int(payload["permissions_new"])),
        )

    def deserialize_application(self, payload: data_binding.JSONObject) -> application_models.Application:
        team: typing.Optional[application_models.Team] = None
        if (team_payload := payload.get("team")) is not None:
            members = {}
            for member_payload in team_payload["members"]:
                team_member = application_models.TeamMember(
                    app=self._app,
                    membership_state=application_models.TeamMembershipState(member_payload["membership_state"]),
                    permissions=member_payload["permissions"],
                    team_id=snowflakes.Snowflake(member_payload["team_id"]),
                    user=self.deserialize_user(member_payload["user"]),
                )
                members[team_member.user.id] = team_member

            team = application_models.Team(
                app=self._app,
                id=snowflakes.Snowflake(team_payload["id"]),
                icon_hash=team_payload["icon"],
                members=members,
                owner_id=snowflakes.Snowflake(team_payload["owner_user_id"]),
            )

        primary_sku_id = snowflakes.Snowflake(payload["primary_sku_id"]) if "primary_sku_id" in payload else None

        return application_models.Application(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            name=payload["name"],
            description=payload["description"],
            is_bot_public=payload.get("bot_public"),
            is_bot_code_grant_required=payload.get("bot_require_code_grant"),
            owner=self.deserialize_user(payload["owner"]) if "owner" in payload else None,
            rpc_origins=payload["rpc_origins"] if "rpc_origins" in payload else None,
            summary=payload["summary"],
            verify_key=bytes(payload["verify_key"], "utf-8") if "verify_key" in payload else None,
            icon_hash=payload.get("icon"),
            team=team,
            guild_id=snowflakes.Snowflake(payload["guild_id"]) if "guild_id" in payload else None,
            primary_sku_id=primary_sku_id,
            slug=payload.get("slug"),
            cover_image_hash=payload.get("cover_image"),
        )

    #####################
    # AUDIT LOGS MODELS #
    #####################

    def _deserialize_audit_log_change_roles(
        self, payload: data_binding.JSONArray
    ) -> typing.Mapping[snowflakes.Snowflake, guild_models.PartialRole]:
        roles = {}
        for role_payload in payload:
            role = guild_models.PartialRole(
                app=self._app, id=snowflakes.Snowflake(role_payload["id"]), name=role_payload["name"]
            )
            roles[role.id] = role

        return roles

    def _deserialize_audit_log_overwrites(
        self, payload: data_binding.JSONArray
    ) -> typing.Mapping[snowflakes.Snowflake, channel_models.PermissionOverwrite]:
        return {
            snowflakes.Snowflake(overwrite["id"]): self.deserialize_permission_overwrite(overwrite)
            for overwrite in payload
        }

    @staticmethod
    def _deserialize_channel_overwrite_entry_info(
        payload: data_binding.JSONObject,
    ) -> audit_log_models.ChannelOverwriteEntryInfo:
        return audit_log_models.ChannelOverwriteEntryInfo(
            id=snowflakes.Snowflake(payload["id"]),
            type=channel_models.PermissionOverwriteType(payload["type"]),
            role_name=payload.get("role_name"),
        )

    @staticmethod
    def _deserialize_message_pin_entry_info(payload: data_binding.JSONObject) -> audit_log_models.MessagePinEntryInfo:
        return audit_log_models.MessagePinEntryInfo(
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            message_id=snowflakes.Snowflake(payload["message_id"]),
        )

    @staticmethod
    def _deserialize_member_prune_entry_info(payload: data_binding.JSONObject) -> audit_log_models.MemberPruneEntryInfo:
        return audit_log_models.MemberPruneEntryInfo(
            delete_member_days=datetime.timedelta(days=int(payload["delete_member_days"])),
            members_removed=int(payload["members_removed"]),
        )

    @staticmethod
    def _deserialize_message_bulk_delete_entry_info(
        payload: data_binding.JSONObject,
    ) -> audit_log_models.MessageBulkDeleteEntryInfo:
        return audit_log_models.MessageBulkDeleteEntryInfo(count=int(payload["count"]))

    @staticmethod
    def _deserialize_message_delete_entry_info(
        payload: data_binding.JSONObject,
    ) -> audit_log_models.MessageDeleteEntryInfo:
        return audit_log_models.MessageDeleteEntryInfo(
            channel_id=snowflakes.Snowflake(payload["channel_id"]), count=int(payload["count"])
        )

    @staticmethod
    def _deserialize_member_disconnect_entry_info(
        payload: data_binding.JSONObject,
    ) -> audit_log_models.MemberDisconnectEntryInfo:
        return audit_log_models.MemberDisconnectEntryInfo(count=int(payload["count"]))

    @staticmethod
    def _deserialize_member_move_entry_info(payload: data_binding.JSONObject) -> audit_log_models.MemberMoveEntryInfo:
        return audit_log_models.MemberMoveEntryInfo(
            channel_id=snowflakes.Snowflake(payload["channel_id"]), count=int(payload["count"])
        )

    @staticmethod
    def _deserialize_unrecognised_audit_log_entry_info(
        payload: data_binding.JSONObject,
    ) -> audit_log_models.UnrecognisedAuditLogEntryInfo:
        return audit_log_models.UnrecognisedAuditLogEntryInfo(payload)

    def deserialize_audit_log(self, payload: data_binding.JSONObject) -> audit_log_models.AuditLog:
        entries = {}
        for entry_payload in payload["audit_log_entries"]:
            entry_id = snowflakes.Snowflake(entry_payload["id"])

            changes = []
            if (change_payloads := entry_payload.get("changes")) is not None:
                for change_payload in change_payloads:
                    key: typing.Union[audit_log_models.AuditLogChangeKey, str]
                    try:
                        # noinspection PyArgumentList
                        key = audit_log_models.AuditLogChangeKey(change_payload["key"])
                    except ValueError:
                        key = change_payload["key"]

                    new_value: typing.Any = change_payload.get("new_value")
                    old_value: typing.Any = change_payload.get("old_value")
                    if value_converter := self._audit_log_entry_converters.get(key):
                        new_value = value_converter(new_value) if new_value is not None else None
                        old_value = value_converter(old_value) if old_value is not None else None

                    changes.append(audit_log_models.AuditLogChange(key=key, new_value=new_value, old_value=old_value))

            target_id: typing.Optional[snowflakes.Snowflake] = None
            if (raw_target_id := entry_payload["target_id"]) is not None:
                target_id = snowflakes.Snowflake(raw_target_id)

            user_id: typing.Optional[snowflakes.Snowflake] = None
            if (raw_user_id := entry_payload["user_id"]) is not None:
                user_id = snowflakes.Snowflake(raw_user_id)

            action_type: typing.Union[audit_log_models.AuditLogEventType, int]
            try:
                # noinspection PyArgumentList
                action_type = audit_log_models.AuditLogEventType(entry_payload["action_type"])
            except ValueError:
                action_type = entry_payload["action_type"]

            options: typing.Optional[audit_log_models.BaseAuditLogEntryInfo] = None
            if (raw_option := entry_payload.get("options")) is not None:
                option_converter = (
                    self._audit_log_event_mapping.get(action_type)
                    or self._deserialize_unrecognised_audit_log_entry_info  # noqa: W503
                )
                options = option_converter(raw_option)

            entries[entry_id] = audit_log_models.AuditLogEntry(
                app=self._app,
                id=entry_id,
                target_id=target_id,
                changes=changes,
                user_id=user_id,
                action_type=action_type,
                options=options,
                reason=entry_payload.get("reason"),
            )

        integrations = {
            snowflakes.Snowflake(integration["id"]): self.deserialize_partial_integration(integration)
            for integration in payload["integrations"]
        }
        users = {snowflakes.Snowflake(user["id"]): self.deserialize_user(user) for user in payload["users"]}
        webhooks = {
            snowflakes.Snowflake(webhook["id"]): self.deserialize_webhook(webhook) for webhook in payload["webhooks"]
        }
        return audit_log_models.AuditLog(entries=entries, integrations=integrations, users=users, webhooks=webhooks)

    ##################
    # CHANNEL MODELS #
    ##################

    def deserialize_permission_overwrite(self, payload: data_binding.JSONObject) -> channel_models.PermissionOverwrite:
        # noinspection PyArgumentList
        return channel_models.PermissionOverwrite(
            id=snowflakes.Snowflake(payload["id"]),
            type=channel_models.PermissionOverwriteType(payload["type"]),
            allow=permission_models.Permissions(int(payload["allow_new"])),
            deny=permission_models.Permissions(int(payload["deny_new"])),
        )

    def serialize_permission_overwrite(self, overwrite: channel_models.PermissionOverwrite) -> data_binding.JSONObject:
        # https://github.com/discord/discord-api-docs/pull/1843/commits/470677363ba88fbc1fe79228821146c6d6b488b9
        # allow and deny can be strings instead now.
        return {
            "id": str(overwrite.id),
            "type": overwrite.type,
            "allow": str(int(overwrite.allow)),
            "deny": str(int(overwrite.deny)),
        }

    def deserialize_partial_channel(self, payload: data_binding.JSONObject) -> channel_models.PartialChannel:
        return channel_models.PartialChannel(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            name=payload.get("name"),
            type=channel_models.ChannelType(payload["type"]),
        )

    def deserialize_private_text_channel(self, payload: data_binding.JSONObject) -> channel_models.PrivateTextChannel:
        last_message_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_last_message_id := payload["last_message_id"]) is not None:
            last_message_id = snowflakes.Snowflake(raw_last_message_id)

        return channel_models.PrivateTextChannel(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            name=payload.get("name"),
            type=channel_models.ChannelType(payload["type"]),
            last_message_id=last_message_id,
            recipient=self.deserialize_user(payload["recipients"][0]),
        )

    def deserialize_private_group_text_channel(
        self, payload: data_binding.JSONObject
    ) -> channel_models.GroupPrivateTextChannel:
        last_message_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_last_message_id := payload["last_message_id"]) is not None:
            last_message_id = snowflakes.Snowflake(raw_last_message_id)

        if (raw_nicks := payload.get("nicks")) is not None:
            nicknames = {snowflakes.Snowflake(entry["id"]): entry["nick"] for entry in raw_nicks}
        else:
            nicknames = {}

        recipients = {snowflakes.Snowflake(user["id"]): self.deserialize_user(user) for user in payload["recipients"]}

        return channel_models.GroupPrivateTextChannel(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            name=payload.get("name"),
            type=channel_models.ChannelType(payload["type"]),
            last_message_id=last_message_id,
            owner_id=snowflakes.Snowflake(payload["owner_id"]),
            icon_hash=payload["icon"],
            nicknames=nicknames,
            application_id=snowflakes.Snowflake(payload["application_id"]) if "application_id" in payload else None,
            recipients=recipients,
        )

    def _set_guild_channel_attributes(
        self, payload: data_binding.JSONObject, *, guild_id: undefined.UndefinedOr[snowflakes.Snowflake],
    ) -> _GuildChannelFields:
        if guild_id is undefined.UNDEFINED:
            guild_id = snowflakes.Snowflake(payload["guild_id"])

        permission_overwrites = {
            snowflakes.Snowflake(overwrite["id"]): self.deserialize_permission_overwrite(overwrite)
            for overwrite in payload["permission_overwrites"]
        }  # TODO: while snowflakes are guaranteed to be unique within their own resource, there is no guarantee for
        # across between resources (user and role in this case); while in practice we will not get overlap there is a
        # chance that this may happen in the future, would it be more sensible to use a Sequence here?

        parent_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_parent_id := payload.get("parent_id")) is not None:
            parent_id = snowflakes.Snowflake(raw_parent_id)

        return _GuildChannelFields(
            id=snowflakes.Snowflake(payload["id"]),
            name=payload.get("name"),
            type=channel_models.ChannelType(payload["type"]),
            guild_id=guild_id,
            position=int(payload["position"]),
            permission_overwrites=permission_overwrites,
            is_nsfw=payload.get("nsfw"),
            parent_id=parent_id,
        )

    def deserialize_guild_category(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.GuildCategory:
        channel_fields = self._set_guild_channel_attributes(payload, guild_id=guild_id)
        return channel_models.GuildCategory(
            app=self._app,
            id=channel_fields.id,
            name=channel_fields.name,
            type=channel_fields.type,
            guild_id=channel_fields.guild_id,
            position=channel_fields.position,
            permission_overwrites=channel_fields.permission_overwrites,
            is_nsfw=channel_fields.is_nsfw,
            parent_id=channel_fields.parent_id,
        )

    def deserialize_guild_text_channel(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.GuildTextChannel:
        channel_fields = self._set_guild_channel_attributes(payload, guild_id=guild_id)

        last_message_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_last_message_id := payload["last_message_id"]) is not None:
            last_message_id = snowflakes.Snowflake(raw_last_message_id)

        last_pin_timestamp: typing.Optional[datetime.datetime] = None
        if (raw_last_pin_timestamp := payload.get("last_pin_timestamp")) is not None:
            last_pin_timestamp = date.iso8601_datetime_string_to_datetime(raw_last_pin_timestamp)

        return channel_models.GuildTextChannel(
            app=self._app,
            id=channel_fields.id,
            name=channel_fields.name,
            type=channel_fields.type,
            guild_id=channel_fields.guild_id,
            position=channel_fields.position,
            permission_overwrites=channel_fields.permission_overwrites,
            is_nsfw=channel_fields.is_nsfw,
            parent_id=channel_fields.parent_id,
            topic=payload["topic"],
            last_message_id=last_message_id,
            # Usually this is 0 if unset, but some old channels made before the
            # rate_limit_per_user field was implemented will not have this field
            # at all if they have never had the rate limit changed...
            rate_limit_per_user=datetime.timedelta(seconds=payload.get("rate_limit_per_user", 0)),
            last_pin_timestamp=last_pin_timestamp,
        )

    def deserialize_guild_news_channel(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.GuildNewsChannel:
        channel_fields = self._set_guild_channel_attributes(payload, guild_id=guild_id)

        last_message_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_last_message_id := payload["last_message_id"]) is not None:
            last_message_id = snowflakes.Snowflake(raw_last_message_id)

        last_pin_timestamp: typing.Optional[datetime.datetime] = None
        if (raw_last_pin_timestamp := payload.get("last_pin_timestamp")) is not None:
            last_pin_timestamp = date.iso8601_datetime_string_to_datetime(raw_last_pin_timestamp)

        return channel_models.GuildNewsChannel(
            app=self._app,
            id=channel_fields.id,
            name=channel_fields.name,
            type=channel_fields.type,
            guild_id=channel_fields.guild_id,
            position=channel_fields.position,
            permission_overwrites=channel_fields.permission_overwrites,
            is_nsfw=channel_fields.is_nsfw,
            parent_id=channel_fields.parent_id,
            topic=payload["topic"],
            last_message_id=last_message_id,
            last_pin_timestamp=last_pin_timestamp,
        )

    def deserialize_guild_store_channel(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.GuildStoreChannel:
        channel_fields = self._set_guild_channel_attributes(payload, guild_id=guild_id)
        return channel_models.GuildStoreChannel(
            app=self._app,
            id=channel_fields.id,
            name=channel_fields.name,
            type=channel_fields.type,
            guild_id=channel_fields.guild_id,
            position=channel_fields.position,
            permission_overwrites=channel_fields.permission_overwrites,
            is_nsfw=channel_fields.is_nsfw,
            parent_id=channel_fields.parent_id,
        )

    def deserialize_guild_voice_channel(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.GuildVoiceChannel:
        channel_fields = self._set_guild_channel_attributes(payload, guild_id=guild_id)
        return channel_models.GuildVoiceChannel(
            app=self._app,
            id=channel_fields.id,
            name=channel_fields.name,
            type=channel_fields.type,
            guild_id=channel_fields.guild_id,
            position=channel_fields.position,
            permission_overwrites=channel_fields.permission_overwrites,
            is_nsfw=channel_fields.is_nsfw,
            parent_id=channel_fields.parent_id,
            bitrate=int(payload["bitrate"]),
            user_limit=int(payload["user_limit"]),
        )

    def deserialize_channel(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.PartialChannel:
        channel_type = payload["type"]
        if channel_model := self._guild_channel_type_mapping.get(channel_type):
            # noinspection PyArgumentList
            return channel_model(payload, guild_id=guild_id)

        # noinspection PyArgumentList
        return self._dm_channel_type_mapping[channel_type](payload)

    ################
    # EMBED MODELS #
    ################

    def deserialize_embed(self, payload: data_binding.JSONObject) -> embed_models.Embed:
        # Keep these separate to aid debugging later.
        title = payload.get("title")
        description = payload.get("description")
        url = payload.get("url")
        color = color_models.Color(payload["color"]) if "color" in payload else None
        timestamp = date.iso8601_datetime_string_to_datetime(payload["timestamp"]) if "timestamp" in payload else None
        fields: typing.Optional[typing.MutableSequence[embed_models.EmbedField]] = None

        image: typing.Optional[embed_models.EmbedImage[files.AsyncReader]] = None
        if image_payload := payload.get("image"):
            image = embed_models.EmbedImage(
                resource=files.ensure_resource(image_payload.get("url")),
                proxy_resource=files.ensure_resource(image_payload.get("proxy_url")),
                height=image_payload.get("height"),
                width=image_payload.get("width"),
            )

        thumbnail: typing.Optional[embed_models.EmbedImage[files.AsyncReader]] = None
        if thumbnail_payload := payload.get("thumbnail"):
            thumbnail = embed_models.EmbedImage(
                resource=files.ensure_resource(thumbnail_payload.get("url")),
                proxy_resource=files.ensure_resource(thumbnail_payload.get("proxy_url")),
                height=thumbnail_payload.get("height"),
                width=thumbnail_payload.get("width"),
            )

        video: typing.Optional[embed_models.EmbedVideo[files.AsyncReader]] = None
        if video_payload := payload.get("video"):
            video = embed_models.EmbedVideo(
                resource=files.ensure_resource(video_payload.get("url")),
                height=video_payload.get("height"),
                width=video_payload.get("width"),
            )

        provider: typing.Optional[embed_models.EmbedProvider] = None
        if provider_payload := payload.get("provider"):
            provider = embed_models.EmbedProvider(name=provider_payload.get("name"), url=provider_payload.get("url"))

        icon: typing.Optional[embed_models.EmbedResourceWithProxy[files.AsyncReader]]
        author: typing.Optional[embed_models.EmbedAuthor] = None
        if author_payload := payload.get("author"):
            icon = None
            if "icon_url" in author_payload:
                icon = embed_models.EmbedResourceWithProxy(
                    resource=files.ensure_resource(author_payload.get("icon_url")),
                    proxy_resource=files.ensure_resource(author_payload.get("proxy_icon_url")),
                )

            author = embed_models.EmbedAuthor(
                name=author_payload.get("name"), url=author_payload.get("url"), icon=icon,
            )

        footer: typing.Optional[embed_models.EmbedFooter] = None
        if footer_payload := payload.get("footer"):
            icon = None
            if "icon_url" in footer_payload:
                icon = embed_models.EmbedResourceWithProxy(
                    resource=files.ensure_resource(footer_payload.get("icon_url")),
                    proxy_resource=files.ensure_resource(footer_payload.get("proxy_icon_url")),
                )

            footer = embed_models.EmbedFooter(text=footer_payload.get("text"), icon=icon)

        if fields_array := payload.get("fields"):
            fields = []
            for field_payload in fields_array:
                field = embed_models.EmbedField(
                    name=field_payload["name"], value=field_payload["value"], inline=field_payload.get("inline", False),
                )
                fields.append(field)

        return embed_models.Embed.from_received_embed(
            title=title,
            description=description,
            url=url,
            color=color,
            timestamp=timestamp,
            image=image,
            thumbnail=thumbnail,
            video=video,
            provider=provider,
            author=author,
            footer=footer,
            fields=fields,
        )

    def serialize_embed(  # noqa: C901
        self, embed: embed_models.Embed,
    ) -> typing.Tuple[data_binding.JSONObject, typing.List[files.Resource[files.AsyncReader]]]:

        payload: data_binding.JSONObject = {}
        uploads: typing.List[files.Resource[files.AsyncReader]] = []

        if embed.title is not None:
            payload["title"] = embed.title

        if embed.description is not None:
            payload["description"] = embed.description

        if embed.url is not None:
            payload["url"] = embed.url

        if embed.timestamp is not None:
            payload["timestamp"] = embed.timestamp.isoformat()

        if embed.color is not None:
            payload["color"] = int(embed.color)

        if embed.footer is not None:
            footer_payload: data_binding.JSONObject = {}

            if embed.footer.text is not None:
                footer_payload["text"] = embed.footer.text

            if embed.footer.icon is not None:
                if not isinstance(embed.footer.icon.resource, files.WebResource):
                    uploads.append(embed.footer.icon.resource)

                footer_payload["icon_url"] = embed.footer.icon.url

            payload["footer"] = footer_payload

        if embed.image is not None:
            image_payload: data_binding.JSONObject = {}

            if not isinstance(embed.image.resource, files.WebResource):
                uploads.append(embed.image.resource)

            image_payload["url"] = embed.image.url
            payload["image"] = image_payload

        if embed.thumbnail is not None:
            thumbnail_payload: data_binding.JSONObject = {}

            if not isinstance(embed.thumbnail.resource, files.WebResource):
                uploads.append(embed.thumbnail.resource)

            thumbnail_payload["url"] = embed.thumbnail.url
            payload["thumbnail"] = thumbnail_payload

        if embed.author is not None:
            author_payload: data_binding.JSONObject = {}

            if embed.author.name is not None:
                author_payload["name"] = embed.author.name

            if embed.author.url is not None:
                author_payload["url"] = embed.author.url

            if embed.author.icon is not None:
                if not isinstance(embed.author.icon.resource, files.WebResource):
                    uploads.append(embed.author.icon.resource)
                author_payload["icon_url"] = embed.author.icon.url

            payload["author"] = author_payload

        if embed.fields:
            field_payloads: data_binding.JSONArray = []
            for i, field in enumerate(embed.fields):

                # Yep, this is technically two unreachable branches. However, this is an incredibly
                # common mistake to make when working with embeds and not using a static type
                # checker, so I have added these as additional safeguards for UX and ease
                # of debugging. The case that there are `None` should be detected immediately by
                # static type checkers, regardless.

                name = str(field.name) if field.name is not None else None  # type: ignore[unreachable]
                value = str(field.value) if field.value is not None else None  # type: ignore[unreachable]

                if name is None:
                    raise TypeError(f"in embed.fields[{i}].name - cannot have `None`")
                if not name:
                    raise TypeError(f"in embed.fields[{i}].name - cannot have empty string")
                if not name.strip():
                    raise TypeError(f"in embed.fields[{i}].name - cannot have only whitespace")

                if value is None:
                    raise TypeError(f"in embed.fields[{i}].value - cannot have `None`")
                if not value:
                    raise TypeError(f"in embed.fields[{i}].value - cannot have empty string")
                if not value.strip():
                    raise TypeError(f"in embed.fields[{i}].value - cannot have only whitespace")

                # Name and value always have to be specified; we can always
                # send a default `inline` value also just to keep this simpler.
                field_payloads.append({"name": name, "value": value, "inline": field.is_inline})
            payload["fields"] = field_payloads

        return payload, uploads

    ################
    # EMOJI MODELS #
    ################

    def deserialize_unicode_emoji(self, payload: data_binding.JSONObject) -> emoji_models.UnicodeEmoji:
        return emoji_models.UnicodeEmoji(name=payload["name"])

    def deserialize_custom_emoji(self, payload: data_binding.JSONObject) -> emoji_models.CustomEmoji:
        return emoji_models.CustomEmoji(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            name=payload["name"],
            is_animated=payload.get("animated", False),
        )

    def deserialize_known_custom_emoji(
        self, payload: data_binding.JSONObject, *, guild_id: snowflakes.Snowflake
    ) -> emoji_models.KnownCustomEmoji:
        role_ids = [snowflakes.Snowflake(role_id) for role_id in payload["roles"]] if "roles" in payload else []

        user: typing.Optional[user_models.User] = None
        if (raw_user := payload.get("user")) is not None:
            user = self.deserialize_user(raw_user)

        return emoji_models.KnownCustomEmoji(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            name=payload["name"],
            is_animated=payload.get("animated", False),
            guild_id=guild_id,
            role_ids=role_ids,
            user=user,
            is_colons_required=payload["require_colons"],
            is_managed=payload["managed"],
            is_available=payload["available"],
        )

    def deserialize_emoji(
        self, payload: data_binding.JSONObject
    ) -> typing.Union[emoji_models.UnicodeEmoji, emoji_models.CustomEmoji]:
        if payload.get("id") is not None:
            return self.deserialize_custom_emoji(payload)

        return self.deserialize_unicode_emoji(payload)

    ##################
    # GATEWAY MODELS #
    ##################

    def deserialize_gateway_bot(self, payload: data_binding.JSONObject) -> gateway_models.GatewayBot:
        session_start_limit_payload = payload["session_start_limit"]
        session_start_limit = gateway_models.SessionStartLimit(
            total=int(session_start_limit_payload["total"]),
            remaining=int(session_start_limit_payload["remaining"]),
            reset_after=datetime.timedelta(milliseconds=session_start_limit_payload["reset_after"]),
            # I do not trust that this may never be zero for some unknown reason. If it was 0, it
            # would hang the application on start up, so I enforce it is at least 1.
            max_concurrency=max(session_start_limit_payload.get("max_concurrency", 0), 1),
        )
        return gateway_models.GatewayBot(
            url=payload["url"], shard_count=int(payload["shards"]), session_start_limit=session_start_limit,
        )

    ################
    # GUILD MODELS #
    ################

    def deserialize_guild_widget(self, payload: data_binding.JSONObject) -> guild_models.GuildWidget:
        channel_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_channel_id := payload["channel_id"]) is not None:
            channel_id = snowflakes.Snowflake(raw_channel_id)

        return guild_models.GuildWidget(app=self._app, channel_id=channel_id, is_enabled=payload["enabled"])

    def deserialize_member(
        self,
        payload: data_binding.JSONObject,
        *,
        user: undefined.UndefinedOr[user_models.User] = undefined.UNDEFINED,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> guild_models.Member:
        if user is undefined.UNDEFINED:
            user = self.deserialize_user(payload["user"])

        if guild_id is undefined.UNDEFINED:
            guild_id = snowflakes.Snowflake(payload["guild_id"])

        role_ids = [snowflakes.Snowflake(role_id) for role_id in payload["roles"]]

        joined_at = date.iso8601_datetime_string_to_datetime(payload["joined_at"])

        premium_since: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED
        if "premium_since" in payload:
            raw_premium_since = payload["premium_since"]
            premium_since = (
                date.iso8601_datetime_string_to_datetime(raw_premium_since) if raw_premium_since is not None else None
            )

        return guild_models.Member(
            user=user,
            guild_id=guild_id,
            role_ids=role_ids,
            joined_at=joined_at,
            nickname=payload["nick"] if "nick" in payload else undefined.UNDEFINED,
            premium_since=premium_since,
            is_deaf=payload["deaf"] if "deaf" in payload else undefined.UNDEFINED,
            is_mute=payload["mute"] if "mute" in payload else undefined.UNDEFINED,
        )

    def deserialize_role(
        self, payload: data_binding.JSONObject, *, guild_id: snowflakes.Snowflake,
    ) -> guild_models.Role:
        return guild_models.Role(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            guild_id=guild_id,
            name=payload["name"],
            color=color_models.Color(payload["color"]),
            is_hoisted=payload["hoist"],
            position=int(payload["position"]),
            # https://github.com/discord/discord-api-docs/pull/1843/commits/470677363ba88fbc1fe79228821146c6d6b488b9
            permissions=permission_models.Permissions(int(payload["permissions_new"])),
            is_managed=payload["managed"],
            is_mentionable=payload["mentionable"],
        )

    @staticmethod
    def _set_partial_integration_attributes(payload: data_binding.JSONObject) -> _IntegrationFields:
        account_payload = payload["account"]
        account = guild_models.IntegrationAccount(id=account_payload["id"], name=account_payload["name"])
        return _IntegrationFields(
            id=snowflakes.Snowflake(payload["id"]), name=payload["name"], type=payload["type"], account=account,
        )

    def deserialize_partial_integration(self, payload: data_binding.JSONObject) -> guild_models.PartialIntegration:
        integration_fields = self._set_partial_integration_attributes(payload)
        return guild_models.PartialIntegration(
            id=integration_fields.id,
            name=integration_fields.name,
            type=integration_fields.type,
            account=integration_fields.account,
        )

    def deserialize_integration(self, payload: data_binding.JSONObject) -> guild_models.Integration:
        integration_fields = self._set_partial_integration_attributes(payload)

        role_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_role_id := payload.get("role_id")) is not None:
            role_id = snowflakes.Snowflake(raw_role_id)

        last_synced_at: typing.Optional[datetime.datetime] = None
        if (raw_last_synced_at := payload.get("synced_at")) is not None:
            last_synced_at = date.iso8601_datetime_string_to_datetime(raw_last_synced_at)

        return guild_models.Integration(
            id=integration_fields.id,
            name=integration_fields.name,
            type=integration_fields.type,
            account=integration_fields.account,
            is_enabled=payload["enabled"],
            is_syncing=payload["syncing"],
            role_id=role_id,
            is_emojis_enabled=payload.get("enable_emoticons"),
            expire_behavior=guild_models.IntegrationExpireBehaviour(payload["expire_behavior"]),
            expire_grace_period=datetime.timedelta(days=payload["expire_grace_period"]),
            user=self.deserialize_user(payload["user"]),
            last_synced_at=last_synced_at,
        )

    def deserialize_guild_member_ban(self, payload: data_binding.JSONObject) -> guild_models.GuildMemberBan:
        return guild_models.GuildMemberBan(reason=payload["reason"], user=self.deserialize_user(payload["user"]))

    def deserialize_unavailable_guild(self, payload: data_binding.JSONObject) -> guild_models.UnavailableGuild:
        return guild_models.UnavailableGuild(id=snowflakes.Snowflake(payload["id"]))

    @staticmethod
    def _set_partial_guild_attributes(payload: data_binding.JSONObject) -> _PartialGuildFields:
        features = []
        for feature in payload["features"]:
            try:
                # noinspection PyArgumentList
                features.append(guild_models.GuildFeature(feature))
            except ValueError:
                features.append(feature)

        return _PartialGuildFields(
            id=snowflakes.Snowflake(payload["id"]), name=payload["name"], icon_hash=payload["icon"], features=features,
        )

    def deserialize_guild_preview(self, payload: data_binding.JSONObject) -> guild_models.GuildPreview:
        guild_fields = self._set_partial_guild_attributes(payload)
        emojis = {
            snowflakes.Snowflake(emoji["id"]): self.deserialize_known_custom_emoji(emoji, guild_id=guild_fields.id)
            for emoji in payload["emojis"]
        }
        return guild_models.GuildPreview(
            app=self._app,
            id=guild_fields.id,
            name=guild_fields.name,
            icon_hash=guild_fields.icon_hash,
            features=guild_fields.features,
            splash_hash=payload["splash"],
            discovery_splash_hash=payload["discovery_splash"],
            emojis=emojis,
            approximate_presence_count=int(payload["approximate_presence_count"]),
            approximate_member_count=int(payload["approximate_member_count"]),
            description=payload["description"],
        )

    def _set_guild_attributes(self, payload: data_binding.JSONObject) -> _GuildFields:
        guild_fields = self._set_partial_guild_attributes(payload)
        afk_channel_id = payload["afk_channel_id"]
        default_message_notifications = guild_models.GuildMessageNotificationsLevel(
            payload["default_message_notifications"]
        )
        application_id = payload["application_id"]
        widget_channel_id = payload.get("widget_channel_id")
        system_channel_id = payload["system_channel_id"]
        rules_channel_id = payload["rules_channel_id"]
        max_presences = payload.get("max_presences")
        max_video_channel_users = (
            int(payload["max_video_channel_users"]) if "max_video_channel_users" in payload else None
        )
        public_updates_channel_id = payload["public_updates_channel_id"]
        public_updates_channel_id = (
            snowflakes.Snowflake(public_updates_channel_id) if public_updates_channel_id is not None else None
        )
        return _GuildFields(
            id=guild_fields.id,
            name=guild_fields.name,
            icon_hash=guild_fields.icon_hash,
            features=guild_fields.features,
            splash_hash=payload["splash"],
            discovery_splash_hash=payload["discovery_splash"],
            owner_id=snowflakes.Snowflake(payload["owner_id"]),
            region=payload["region"],
            afk_channel_id=snowflakes.Snowflake(afk_channel_id) if afk_channel_id is not None else None,
            afk_timeout=datetime.timedelta(seconds=payload["afk_timeout"]),
            verification_level=guild_models.GuildVerificationLevel(payload["verification_level"]),
            default_message_notifications=default_message_notifications,
            explicit_content_filter=guild_models.GuildExplicitContentFilterLevel(payload["explicit_content_filter"]),
            mfa_level=guild_models.GuildMFALevel(payload["mfa_level"]),
            application_id=snowflakes.Snowflake(application_id) if application_id is not None else None,
            widget_channel_id=snowflakes.Snowflake(widget_channel_id) if widget_channel_id is not None else None,
            system_channel_id=snowflakes.Snowflake(system_channel_id) if system_channel_id is not None else None,
            is_widget_enabled=payload["widget_enabled"] if "widget_enabled" in payload else None,
            system_channel_flags=guild_models.GuildSystemChannelFlag(payload["system_channel_flags"]),
            rules_channel_id=snowflakes.Snowflake(rules_channel_id) if rules_channel_id is not None else None,
            max_presences=int(max_presences) if max_presences is not None else None,
            max_members=int(payload["max_members"]) if "max_members" in payload else None,
            max_video_channel_users=max_video_channel_users,
            vanity_url_code=payload["vanity_url_code"],
            description=payload["description"],
            banner_hash=payload["banner"],
            premium_tier=guild_models.GuildPremiumTier(payload["premium_tier"]),
            premium_subscription_count=payload.get("premium_subscription_count"),
            preferred_locale=payload["preferred_locale"],
            public_updates_channel_id=public_updates_channel_id,
        )

    def deserialize_rest_guild(self, payload: data_binding.JSONObject) -> guild_models.RESTGuild:
        guild_fields = self._set_guild_attributes(payload)
        approximate_member_count = (
            int(payload["approximate_member_count"]) if "approximate_member_count" in payload else None
        )
        approximate_active_member_count = (
            int(payload["approximate_presence_count"]) if "approximate_presence_count" in payload else None
        )

        roles = {
            snowflakes.Snowflake(role["id"]): self.deserialize_role(role, guild_id=guild_fields.id)
            for role in payload["roles"]
        }
        emojis = {
            snowflakes.Snowflake(emoji["id"]): self.deserialize_known_custom_emoji(emoji, guild_id=guild_fields.id)
            for emoji in payload["emojis"]
        }
        guild = guild_models.RESTGuild(
            app=self._app,
            id=guild_fields.id,
            name=guild_fields.name,
            icon_hash=guild_fields.icon_hash,
            features=guild_fields.features,
            splash_hash=guild_fields.splash_hash,
            discovery_splash_hash=guild_fields.discovery_splash_hash,
            owner_id=guild_fields.owner_id,
            region=guild_fields.region,
            afk_channel_id=guild_fields.afk_channel_id,
            afk_timeout=guild_fields.afk_timeout,
            verification_level=guild_fields.verification_level,
            default_message_notifications=guild_fields.default_message_notifications,
            explicit_content_filter=guild_fields.explicit_content_filter,
            mfa_level=guild_fields.mfa_level,
            application_id=guild_fields.application_id,
            widget_channel_id=guild_fields.widget_channel_id,
            system_channel_id=guild_fields.system_channel_id,
            is_widget_enabled=guild_fields.is_widget_enabled,
            system_channel_flags=guild_fields.system_channel_flags,
            rules_channel_id=guild_fields.rules_channel_id,
            max_presences=guild_fields.max_presences,
            max_members=guild_fields.max_members,
            max_video_channel_users=guild_fields.max_video_channel_users,
            vanity_url_code=guild_fields.vanity_url_code,
            description=guild_fields.description,
            banner_hash=guild_fields.banner_hash,
            premium_tier=guild_fields.premium_tier,
            premium_subscription_count=guild_fields.premium_subscription_count,
            preferred_locale=guild_fields.preferred_locale,
            public_updates_channel_id=guild_fields.public_updates_channel_id,
            approximate_member_count=approximate_member_count,
            approximate_active_member_count=approximate_active_member_count,
            roles=roles,
            emojis=emojis,
        )
        return guild

    def deserialize_gateway_guild(self, payload: data_binding.JSONObject) -> entity_factory.GatewayGuildDefinition:
        guild_fields = self._set_guild_attributes(payload)
        my_permissions = permission_models.Permissions(payload["permissions"]) if "permissions" in payload else None
        is_large = payload["large"] if "large" in payload else None
        joined_at = date.iso8601_datetime_string_to_datetime(payload["joined_at"]) if "joined_at" in payload else None
        member_count = int(payload["member_count"]) if "member_count" in payload else None

        guild = guild_models.GatewayGuild(
            app=self._app,
            id=guild_fields.id,
            name=guild_fields.name,
            icon_hash=guild_fields.icon_hash,
            features=guild_fields.features,
            splash_hash=guild_fields.splash_hash,
            discovery_splash_hash=guild_fields.discovery_splash_hash,
            owner_id=guild_fields.owner_id,
            region=guild_fields.region,
            afk_channel_id=guild_fields.afk_channel_id,
            afk_timeout=guild_fields.afk_timeout,
            verification_level=guild_fields.verification_level,
            default_message_notifications=guild_fields.default_message_notifications,
            explicit_content_filter=guild_fields.explicit_content_filter,
            mfa_level=guild_fields.mfa_level,
            application_id=guild_fields.application_id,
            widget_channel_id=guild_fields.widget_channel_id,
            system_channel_id=guild_fields.system_channel_id,
            is_widget_enabled=guild_fields.is_widget_enabled,
            system_channel_flags=guild_fields.system_channel_flags,
            rules_channel_id=guild_fields.rules_channel_id,
            max_presences=guild_fields.max_presences,
            max_members=guild_fields.max_members,
            max_video_channel_users=guild_fields.max_video_channel_users,
            vanity_url_code=guild_fields.vanity_url_code,
            description=guild_fields.description,
            banner_hash=guild_fields.banner_hash,
            premium_tier=guild_fields.premium_tier,
            premium_subscription_count=guild_fields.premium_subscription_count,
            preferred_locale=guild_fields.preferred_locale,
            public_updates_channel_id=guild_fields.public_updates_channel_id,
            my_permissions=my_permissions,
            is_large=is_large,
            joined_at=joined_at,
            member_count=member_count,
        )

        members: typing.Optional[typing.MutableMapping[snowflakes.Snowflake, guild_models.Member]] = None
        if "members" in payload:
            members = {}

            for member_payload in payload["members"]:
                member = self.deserialize_member(member_payload, guild_id=guild.id)
                members[member.user.id] = member

        channels: typing.Optional[typing.MutableMapping[snowflakes.Snowflake, channel_models.GuildChannel]] = None
        if "channels" in payload:
            channels = {}

            for channel_payload in payload["channels"]:
                channel = typing.cast(
                    "channel_models.GuildChannel", self.deserialize_channel(channel_payload, guild_id=guild.id)
                )
                channels[channel.id] = channel

        presences: typing.Optional[typing.MutableMapping[snowflakes.Snowflake, presence_models.MemberPresence]] = None
        if "presences" in payload:
            presences = {}

            for presence_payload in payload["presences"]:
                presence = self.deserialize_member_presence(presence_payload, guild_id=guild.id)
                presences[presence.user_id] = presence

        voice_states: typing.Optional[typing.MutableMapping[snowflakes.Snowflake, voice_models.VoiceState]] = None
        if "voice_states" in payload:
            voice_states = {}
            assert members is not None

            for voice_state_payload in payload["voice_states"]:
                member = members[snowflakes.Snowflake(voice_state_payload["user_id"])]
                voice_state = self.deserialize_voice_state(voice_state_payload, guild_id=guild.id, member=member)
                voice_states[voice_state.user_id] = voice_state

        roles = {
            snowflakes.Snowflake(role["id"]): self.deserialize_role(role, guild_id=guild.id)
            for role in payload["roles"]
        }
        emojis = {
            snowflakes.Snowflake(emoji["id"]): self.deserialize_known_custom_emoji(emoji, guild_id=guild.id)
            for emoji in payload["emojis"]
        }

        return entity_factory.GatewayGuildDefinition(guild, channels, members, presences, roles, emojis, voice_states)

    #################
    # INVITE MODELS #
    #################

    def deserialize_vanity_url(self, payload: data_binding.JSONObject) -> invite_models.VanityURL:
        return invite_models.VanityURL(app=self._app, code=payload["code"], uses=int(payload["uses"]))

    def _set_invite_attributes(self, payload: data_binding.JSONObject) -> _InviteFields:
        guild: typing.Optional[invite_models.InviteGuild] = None
        guild_id: typing.Optional[snowflakes.Snowflake] = None
        if "guild" in payload:
            guild_payload = payload["guild"]
            guild_fields = self._set_partial_guild_attributes(guild_payload)
            guild = invite_models.InviteGuild(
                app=self._app,
                id=guild_fields.id,
                name=guild_fields.name,
                features=guild_fields.features,
                icon_hash=guild_fields.icon_hash,
                splash_hash=guild_payload["splash"],
                banner_hash=guild_payload["banner"],
                description=guild_payload["description"],
                verification_level=guild_models.GuildVerificationLevel(guild_payload["verification_level"]),
                vanity_url_code=guild_payload["vanity_url_code"],
            )
            guild_id = guild.id
        elif "guild_id" in payload:
            guild_id = snowflakes.Snowflake(payload["guild_id"])

        channel: typing.Optional[channel_models.PartialChannel] = None
        if (raw_channel := payload.get("channel")) is not None:
            channel = self.deserialize_partial_channel(raw_channel)
            channel_id = channel.id
        else:
            channel_id = snowflakes.Snowflake(payload["channel_id"])

        # noinspection PyArgumentList
        target_user_type = (
            invite_models.TargetUserType(payload["target_user_type"]) if "target_user_type" in payload else None
        )
        approximate_presence_count = (
            int(payload["approximate_presence_count"]) if "approximate_presence_count" in payload else None
        )
        approximate_member_count = (
            int(payload["approximate_member_count"]) if "approximate_member_count" in payload else None
        )
        return _InviteFields(
            code=payload["code"],
            guild=guild,
            guild_id=guild_id,
            channel=channel,
            channel_id=channel_id,
            inviter=self.deserialize_user(payload["inviter"]) if "inviter" in payload else None,
            target_user=self.deserialize_user(payload["target_user"]) if "target_user" in payload else None,
            target_user_type=target_user_type,
            approximate_presence_count=approximate_presence_count,
            approximate_member_count=approximate_member_count,
        )

    def deserialize_invite(self, payload: data_binding.JSONObject) -> invite_models.Invite:
        invite_fields = self._set_invite_attributes(payload)
        return invite_models.Invite(
            app=self._app,
            code=invite_fields.code,
            guild=invite_fields.guild,
            guild_id=invite_fields.guild_id,
            channel=invite_fields.channel,
            channel_id=invite_fields.channel_id,
            inviter=invite_fields.inviter,
            target_user=invite_fields.target_user,
            target_user_type=invite_fields.target_user_type,
            approximate_member_count=invite_fields.approximate_member_count,
            approximate_presence_count=invite_fields.approximate_presence_count,
        )

    def deserialize_invite_with_metadata(self, payload: data_binding.JSONObject) -> invite_models.InviteWithMetadata:
        invite_fields = self._set_invite_attributes(payload)
        max_age = payload["max_age"]
        return invite_models.InviteWithMetadata(
            app=self._app,
            code=invite_fields.code,
            guild=invite_fields.guild,
            guild_id=invite_fields.guild_id,
            channel=invite_fields.channel,
            channel_id=invite_fields.channel_id,
            inviter=invite_fields.inviter,
            target_user=invite_fields.target_user,
            target_user_type=invite_fields.target_user_type,
            approximate_member_count=invite_fields.approximate_member_count,
            approximate_presence_count=invite_fields.approximate_presence_count,
            uses=int(payload["uses"]),
            max_uses=int(payload["max_uses"]),
            max_age=datetime.timedelta(seconds=max_age) if max_age > 0 else None,
            is_temporary=payload["temporary"],
            created_at=date.iso8601_datetime_string_to_datetime(payload["created_at"]),
        )

    ##################
    # MESSAGE MODELS #
    ##################

    def deserialize_partial_message(self, payload: data_binding.JSONObject) -> message_models.PartialMessage:
        author: undefined.UndefinedOr[user_models.User] = undefined.UNDEFINED
        if "author" in payload:
            author = self.deserialize_user(payload["author"])

        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED
        if "guild_id" in payload:
            guild_id = snowflakes.Snowflake(payload["guild_id"])

        member: undefined.UndefinedOr[guild_models.Member] = undefined.UNDEFINED
        if "member" in payload:
            assert author is not undefined.UNDEFINED
            assert guild_id is not undefined.UNDEFINED
            member = self.deserialize_member(payload["member"], user=author, guild_id=guild_id)

        timestamp: undefined.UndefinedOr[datetime.datetime] = undefined.UNDEFINED
        if "timestamp" in payload:
            timestamp = date.iso8601_datetime_string_to_datetime(payload["timestamp"])

        edited_timestamp: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED
        if "edited_timestamp" in payload:
            if (raw_edited_timestamp := payload["edited_timestamp"]) is not None:
                edited_timestamp = date.iso8601_datetime_string_to_datetime(raw_edited_timestamp)
            else:
                edited_timestamp = None

        is_mentioning_everyone = payload["mention_everyone"] if "mention_everyone" in payload else undefined.UNDEFINED

        user_mentions: undefined.UndefinedOr[typing.Sequence[snowflakes.Snowflake]] = undefined.UNDEFINED
        if "mentions" in payload:
            user_mentions = [snowflakes.Snowflake(mention["id"]) for mention in payload["mentions"]]

        role_mentions: undefined.UndefinedOr[typing.Sequence[snowflakes.Snowflake]] = undefined.UNDEFINED
        if "mention_roles" in payload:
            role_mentions = [snowflakes.Snowflake(mention) for mention in payload["mention_roles"]]

        channel_mentions: undefined.UndefinedOr[typing.Sequence[snowflakes.Snowflake]] = undefined.UNDEFINED
        if "mention_channels" in payload:
            channel_mentions = [snowflakes.Snowflake(mention["id"]) for mention in payload["mention_channels"]]

        attachments: undefined.UndefinedOr[typing.MutableSequence[message_models.Attachment]] = undefined.UNDEFINED
        if "attachments" in payload:
            attachments = []
            for attachment_payload in payload["attachments"]:
                attachment = message_models.Attachment(
                    id=snowflakes.Snowflake(attachment_payload["id"]),
                    filename=attachment_payload["filename"],
                    size=int(attachment_payload["size"]),
                    url=attachment_payload["url"],
                    proxy_url=attachment_payload["proxy_url"],
                    height=attachment_payload.get("height"),
                    width=attachment_payload.get("width"),
                )
                attachments.append(attachment)

        embeds: undefined.UndefinedOr[typing.Sequence[embed_models.Embed]] = undefined.UNDEFINED
        if "embeds" in payload:
            embeds = [self.deserialize_embed(embed) for embed in payload["embeds"]]

        reactions: undefined.UndefinedOr[typing.MutableSequence[message_models.Reaction]] = undefined.UNDEFINED
        if "reactions" in payload:
            reactions = []
            for reaction_payload in payload["reactions"]:
                reaction = message_models.Reaction(
                    count=int(reaction_payload["count"]),
                    emoji=self.deserialize_emoji(reaction_payload["emoji"]),
                    is_me=reaction_payload["me"],
                )
                reactions.append(reaction)

        activity: undefined.UndefinedOr[message_models.MessageActivity] = undefined.UNDEFINED
        if "activity" in payload:
            activity_payload = payload["activity"]
            activity = message_models.MessageActivity(
                type=message_models.MessageActivityType(activity_payload["type"]),
                party_id=activity_payload.get("party_id"),
            )

        application: undefined.UndefinedOr[application_models.Application] = undefined.UNDEFINED
        if "application" in payload:
            application = self.deserialize_application(payload["application"])

        message_reference: undefined.UndefinedOr[message_models.MessageCrosspost] = undefined.UNDEFINED
        if "message_reference" in payload:
            crosspost_payload = payload["message_reference"]
            message_reference = message_models.MessageCrosspost(
                app=self._app,
                id=snowflakes.Snowflake(crosspost_payload["message_id"]) if "message_id" in crosspost_payload else None,
                channel_id=snowflakes.Snowflake(crosspost_payload["channel_id"]),
                guild_id=snowflakes.Snowflake(crosspost_payload["guild_id"])
                if "guild_id" in crosspost_payload
                else None,
            )

        return message_models.PartialMessage(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            guild_id=guild_id,
            author=author,
            member=member,
            content=payload["content"] if "content" in payload else undefined.UNDEFINED,
            timestamp=timestamp,
            edited_timestamp=edited_timestamp,
            is_tts=payload["tts"] if "tts" in payload else undefined.UNDEFINED,
            is_mentioning_everyone=is_mentioning_everyone,
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            channel_mentions=channel_mentions,
            attachments=attachments,
            embeds=embeds,
            reactions=reactions,
            is_pinned=payload["pinned"] if "pinned" in payload else undefined.UNDEFINED,
            webhook_id=snowflakes.Snowflake(payload["webhook_id"]) if "webhook_id" in payload else undefined.UNDEFINED,
            type=message_models.MessageType(payload["type"]) if "type" in payload else undefined.UNDEFINED,
            activity=activity,
            application=application,
            message_reference=message_reference,
            flags=message_models.MessageFlag(payload["flags"]) if "flags" in payload else undefined.UNDEFINED,
            nonce=payload["nonce"] if "nonce" in payload else undefined.UNDEFINED,
        )

    def deserialize_message(self, payload: data_binding.JSONObject) -> message_models.Message:
        guild_id = snowflakes.Snowflake(payload["guild_id"]) if "guild_id" in payload else None
        author = self.deserialize_user(payload["author"])

        member: typing.Optional[guild_models.Member] = None
        if "member" in payload:
            assert guild_id is not None
            member = self.deserialize_member(payload["member"], guild_id=guild_id, user=author)

        edited_timestamp: typing.Optional[datetime.datetime] = None
        if (raw_edited_timestamp := payload["edited_timestamp"]) is not None:
            edited_timestamp = date.iso8601_datetime_string_to_datetime(raw_edited_timestamp)

        user_mentions = [snowflakes.Snowflake(mention["id"]) for mention in payload["mentions"]]
        role_mentions = [snowflakes.Snowflake(mention) for mention in payload["mention_roles"]]
        channel_mentions = (
            [snowflakes.Snowflake(mention["id"]) for mention in payload["mention_channels"]]
            if "mention_channels" in payload
            else []
        )

        attachments = []
        for attachment_payload in payload["attachments"]:
            attachment = message_models.Attachment(
                id=snowflakes.Snowflake(attachment_payload["id"]),
                filename=attachment_payload["filename"],
                size=int(attachment_payload["size"]),
                url=attachment_payload["url"],
                proxy_url=attachment_payload["proxy_url"],
                height=attachment_payload.get("height"),
                width=attachment_payload.get("width"),
            )
            attachments.append(attachment)

        embeds = [self.deserialize_embed(embed) for embed in payload["embeds"]]

        reactions = []
        if "reactions" in payload:
            for reaction_payload in payload["reactions"]:
                reaction = message_models.Reaction(
                    count=int(reaction_payload["count"]),
                    emoji=self.deserialize_emoji(reaction_payload["emoji"]),
                    is_me=reaction_payload["me"],
                )
                reactions.append(reaction)

        activity: typing.Optional[message_models.MessageActivity] = None
        if "activity" in payload:
            activity_payload = payload["activity"]
            activity = message_models.MessageActivity(
                type=message_models.MessageActivityType(activity_payload["type"]),
                party_id=activity_payload.get("party_id"),
            )

        crosspost: typing.Optional[message_models.MessageCrosspost] = None
        if "message_reference" in payload:
            crosspost_payload = payload["message_reference"]
            crosspost_id = (
                snowflakes.Snowflake(crosspost_payload["message_id"]) if "message_id" in crosspost_payload else None
            )
            crosspost = message_models.MessageCrosspost(
                app=self._app,
                id=crosspost_id,
                channel_id=snowflakes.Snowflake(crosspost_payload["channel_id"]),
                guild_id=snowflakes.Snowflake(crosspost_payload["guild_id"])
                if "guild_id" in crosspost_payload
                else None,
            )

        return message_models.Message(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            guild_id=guild_id,
            author=author,
            member=member,
            content=payload["content"],
            timestamp=date.iso8601_datetime_string_to_datetime(payload["timestamp"]),
            edited_timestamp=edited_timestamp,
            is_tts=payload["tts"],
            is_mentioning_everyone=payload["mention_everyone"],
            user_mentions=user_mentions,
            role_mentions=role_mentions,
            channel_mentions=channel_mentions,
            attachments=attachments,
            embeds=embeds,
            reactions=reactions,
            is_pinned=payload["pinned"],
            webhook_id=snowflakes.Snowflake(payload["webhook_id"]) if "webhook_id" in payload else None,
            type=message_models.MessageType(payload["type"]),
            activity=activity,
            application=self.deserialize_application(payload["application"]) if "application" in payload else None,
            message_reference=crosspost,
            flags=message_models.MessageFlag(payload["flags"]) if "flags" in payload else None,
            nonce=payload.get("nonce"),
        )

    ###################
    # PRESENCE MODELS #
    ###################

    def deserialize_member_presence(  # noqa: CFQ001  # TODO: what's CFQ001?
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> presence_models.MemberPresence:
        role_ids = [snowflakes.Snowflake(role_id) for role_id in payload["roles"]] if "roles" in payload else None

        activities = []
        for activity_payload in payload["activities"]:
            timestamps: typing.Optional[presence_models.ActivityTimestamps] = None
            if "timestamps" in activity_payload:
                timestamps_payload = activity_payload["timestamps"]
                start = (
                    date.unix_epoch_to_datetime(timestamps_payload["start"]) if "start" in timestamps_payload else None
                )
                end = date.unix_epoch_to_datetime(timestamps_payload["end"]) if "end" in timestamps_payload else None
                timestamps = presence_models.ActivityTimestamps(start=start, end=end)

            application_id = (
                snowflakes.Snowflake(activity_payload["application_id"])
                if "application_id" in activity_payload
                else None
            )

            party: typing.Optional[presence_models.ActivityParty] = None
            if "party" in activity_payload:
                party_payload = activity_payload["party"]

                current_size: typing.Optional[int]
                max_size: typing.Optional[int]
                if "size" in party_payload:
                    raw_current_size, raw_max_size = party_payload["size"]
                    current_size = int(raw_current_size)
                    max_size = int(raw_max_size)
                else:
                    current_size = max_size = None

                party = presence_models.ActivityParty(
                    id=party_payload.get("id"), current_size=current_size, max_size=max_size
                )

            assets: typing.Optional[presence_models.ActivityAssets] = None
            if "assets" in activity_payload:
                assets_payload = activity_payload["assets"]
                assets = presence_models.ActivityAssets(
                    large_image=assets_payload.get("large_image"),
                    large_text=assets_payload.get("large_text"),
                    small_image=assets_payload.get("small_image"),
                    small_text=assets_payload.get("small_text"),
                )

            secrets: typing.Optional[presence_models.ActivitySecret] = None
            if "secrets" in activity_payload:
                secrets_payload = activity_payload["secrets"]
                secrets = presence_models.ActivitySecret(
                    join=secrets_payload.get("join"),
                    spectate=secrets_payload.get("spectate"),
                    match=secrets_payload.get("match"),
                )

            emoji: typing.Optional[emoji_models.Emoji] = None
            raw_emoji = activity_payload.get("emoji")
            if raw_emoji is not None:
                emoji = self.deserialize_emoji(raw_emoji)

            activity = presence_models.RichActivity(
                name=activity_payload["name"],
                type=presence_models.ActivityType(activity_payload["type"]),
                url=activity_payload.get("url"),
                created_at=date.unix_epoch_to_datetime(activity_payload["created_at"]),
                timestamps=timestamps,
                application_id=application_id,
                details=activity_payload.get("details"),
                state=activity_payload.get("state"),
                emoji=emoji,
                party=party,
                assets=assets,
                secrets=secrets,
                is_instance=activity_payload.get("instance"),  # TODO: can we safely default this to False?
                flags=presence_models.ActivityFlag(activity_payload["flags"]) if "flags" in activity_payload else None,
            )
            activities.append(activity)

        client_status_payload = payload["client_status"]
        desktop = (
            presence_models.Status(client_status_payload["desktop"])
            if "desktop" in client_status_payload
            else presence_models.Status.OFFLINE
        )
        mobile = (
            presence_models.Status(client_status_payload["mobile"])
            if "mobile" in client_status_payload
            else presence_models.Status.OFFLINE
        )
        web = (
            presence_models.Status(client_status_payload["web"])
            if "web" in client_status_payload
            else presence_models.Status.OFFLINE
        )
        client_status = presence_models.ClientStatus(desktop=desktop, mobile=mobile, web=web)
        # TODO: do we want to differentiate between undefined and null here?
        premium_since = payload.get("premium_since")
        premium_since = date.iso8601_datetime_string_to_datetime(premium_since) if premium_since is not None else None
        return presence_models.MemberPresence(
            app=self._app,
            user_id=snowflakes.Snowflake(payload["user"]["id"]),
            role_ids=role_ids,
            guild_id=guild_id if guild_id is not undefined.UNDEFINED else snowflakes.Snowflake(payload["guild_id"]),
            visible_status=presence_models.Status(payload["status"]),
            activities=activities,
            client_status=client_status,
            premium_since=premium_since,
            # TODO: do we want to differentiate between undefined and null here?
            nickname=payload.get("nick"),
        )

    ###############
    # USER MODELS #
    ###############

    @staticmethod
    def _set_user_attributes(payload: data_binding.JSONObject) -> _UserFields:
        return _UserFields(
            id=snowflakes.Snowflake(payload["id"]),
            discriminator=payload["discriminator"],
            username=payload["username"],
            avatar_hash=payload["avatar"],
            is_bot=payload.get("bot", False),
            is_system=payload.get("system", False),
        )

    def deserialize_user(self, payload: data_binding.JSONObject) -> user_models.User:
        user_fields = self._set_user_attributes(payload)
        flags = (
            user_models.UserFlag(payload["public_flags"]) if "public_flags" in payload else user_models.UserFlag.NONE
        )
        return user_models.UserImpl(
            app=self._app,
            id=user_fields.id,
            discriminator=user_fields.discriminator,
            username=user_fields.username,
            avatar_hash=user_fields.avatar_hash,
            is_bot=user_fields.is_bot,
            is_system=user_fields.is_system,
            flags=flags,
        )

    def deserialize_my_user(self, payload: data_binding.JSONObject) -> user_models.OwnUser:
        user_fields = self._set_user_attributes(payload)
        return user_models.OwnUser(
            app=self._app,
            id=user_fields.id,
            discriminator=user_fields.discriminator,
            username=user_fields.username,
            avatar_hash=user_fields.avatar_hash,
            is_bot=user_fields.is_bot,
            is_system=user_fields.is_system,
            is_mfa_enabled=payload["mfa_enabled"],
            locale=payload.get("locale"),
            is_verified=payload.get("verified"),
            email=payload.get("email"),
            flags=user_models.UserFlag(payload["flags"]),
            premium_type=user_models.PremiumType(payload["premium_type"]) if "premium_type" in payload else None,
        )

    ################
    # VOICE MODELS #
    ################

    def deserialize_voice_state(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
        member: undefined.UndefinedOr[guild_models.Member] = undefined.UNDEFINED,
    ) -> voice_models.VoiceState:
        if guild_id is undefined.UNDEFINED:
            guild_id = snowflakes.Snowflake(payload["guild_id"])

        channel_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_channel_id := payload["channel_id"]) is not None:
            channel_id = snowflakes.Snowflake(raw_channel_id)

        if member is undefined.UNDEFINED:
            member = self.deserialize_member(payload["member"], guild_id=guild_id)

        return voice_models.VoiceState(
            app=self._app,
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=snowflakes.Snowflake(payload["user_id"]),
            member=member,
            session_id=payload["session_id"],
            is_guild_deafened=payload["deaf"],
            is_guild_muted=payload["mute"],
            is_self_deafened=payload["self_deaf"],
            is_self_muted=payload["self_mute"],
            is_streaming=payload.get("self_stream", False),
            is_video_enabled=payload["self_video"],
            is_suppressed=payload["suppress"],
        )

    def deserialize_voice_region(self, payload: data_binding.JSONObject) -> voice_models.VoiceRegion:
        return voice_models.VoiceRegion(
            id=payload["id"],
            name=payload["name"],
            is_vip=payload["vip"],
            is_optimal_location=payload["optimal"],
            is_deprecated=payload["deprecated"],
            is_custom=payload["custom"],
        )

    ##################
    # WEBHOOK MODELS #
    ##################

    def deserialize_webhook(self, payload: data_binding.JSONObject) -> webhook_models.Webhook:
        return webhook_models.Webhook(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            type=webhook_models.WebhookType(payload["type"]),
            guild_id=snowflakes.Snowflake(payload["guild_id"]) if "guild_id" in payload else None,
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            author=self.deserialize_user(payload["user"]) if "user" in payload else None,
            name=payload["name"],
            avatar_hash=payload["avatar"],
            token=payload.get("token"),
        )
