# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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

__all__: typing.List[str] = ["EntityFactoryImpl"]

import datetime
import logging
import typing

import attr

from hikari import applications as application_models
from hikari import audit_logs as audit_log_models
from hikari import channels as channel_models
from hikari import colors as color_models
from hikari import commands
from hikari import embeds as embed_models
from hikari import emojis as emoji_models
from hikari import errors
from hikari import files
from hikari import guilds as guild_models
from hikari import invites as invite_models
from hikari import messages as message_models
from hikari import permissions as permission_models
from hikari import presences as presence_models
from hikari import sessions as gateway_models
from hikari import snowflakes
from hikari import stickers as sticker_models
from hikari import templates as template_models
from hikari import traits
from hikari import undefined
from hikari import users as user_models
from hikari import voices as voice_models
from hikari import webhooks as webhook_models
from hikari.api import entity_factory
from hikari.interactions import base_interactions
from hikari.interactions import command_interactions
from hikari.interactions import component_interactions
from hikari.internal import attr_extensions
from hikari.internal import data_binding
from hikari.internal import time

_ValueT = typing.TypeVar("_ValueT")
_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.entity_factory")

_interaction_option_type_mapping: typing.Dict[int, typing.Callable[[typing.Any], typing.Any]] = {
    commands.OptionType.USER: snowflakes.Snowflake,
    commands.OptionType.CHANNEL: snowflakes.Snowflake,
    commands.OptionType.ROLE: snowflakes.Snowflake,
    commands.OptionType.MENTIONABLE: snowflakes.Snowflake,
}


def _with_int_cast(cast: typing.Callable[[int], _ValueT]) -> typing.Callable[[typing.Any], _ValueT]:
    """Wrap a cast to ensure the value passed to it will first be cast to int."""
    return lambda value: cast(int(value))


def _deserialize_seconds_timedelta(seconds: typing.Union[str, int]) -> datetime.timedelta:
    return datetime.timedelta(seconds=int(seconds))


def _deserialize_day_timedelta(days: typing.Union[str, int]) -> datetime.timedelta:
    return datetime.timedelta(days=int(days))


def _deserialize_max_uses(age: int) -> typing.Optional[int]:
    return age if age > 0 else None


def _deserialize_max_age(seconds: int) -> typing.Optional[datetime.timedelta]:
    return datetime.timedelta(seconds=seconds) if seconds > 0 else None


@attr_extensions.with_copy
@attr.define(kw_only=True, repr=False, weakref_slot=False)
class _GuildChannelFields:
    id: snowflakes.Snowflake = attr.field()
    name: typing.Optional[str] = attr.field()
    type: typing.Union[channel_models.ChannelType, int] = attr.field()
    guild_id: snowflakes.Snowflake = attr.field()
    position: int = attr.field()
    permission_overwrites: typing.Dict[snowflakes.Snowflake, channel_models.PermissionOverwrite] = attr.field()
    is_nsfw: typing.Optional[bool] = attr.field()
    parent_id: typing.Optional[snowflakes.Snowflake] = attr.field()


@attr_extensions.with_copy
@attr.define(kw_only=True, repr=False, weakref_slot=False)
class _IntegrationFields:
    id: snowflakes.Snowflake = attr.field()
    name: str = attr.field()
    type: typing.Union[guild_models.IntegrationType, str] = attr.field()
    account: guild_models.IntegrationAccount = attr.field()


@attr_extensions.with_copy
@attr.define(kw_only=True, repr=False, weakref_slot=False)
class _GuildFields:
    id: snowflakes.Snowflake = attr.field()
    name: str = attr.field()
    icon_hash: str = attr.field()
    features: typing.List[typing.Union[guild_models.GuildFeature, str]] = attr.field()
    splash_hash: typing.Optional[str] = attr.field()
    discovery_splash_hash: typing.Optional[str] = attr.field()
    owner_id: snowflakes.Snowflake = attr.field()
    afk_channel_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    afk_timeout: datetime.timedelta = attr.field()
    verification_level: typing.Union[guild_models.GuildVerificationLevel, int] = attr.field()
    default_message_notifications: typing.Union[guild_models.GuildMessageNotificationsLevel, int] = attr.field()
    explicit_content_filter: typing.Union[guild_models.GuildVerificationLevel, int] = attr.field()
    mfa_level: typing.Union[guild_models.GuildMFALevel, int] = attr.field()
    application_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    widget_channel_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    system_channel_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    is_widget_enabled: typing.Optional[bool] = attr.field()
    system_channel_flags: guild_models.GuildSystemChannelFlag = attr.field()
    rules_channel_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    max_video_channel_users: typing.Optional[int] = attr.field()
    vanity_url_code: typing.Optional[str] = attr.field()
    description: typing.Optional[str] = attr.field()
    banner_hash: typing.Optional[str] = attr.field()
    premium_tier: typing.Union[guild_models.GuildPremiumTier, int] = attr.field()
    premium_subscription_count: typing.Optional[int] = attr.field()
    preferred_locale: str = attr.field()
    public_updates_channel_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    nsfw_level: guild_models.GuildNSFWLevel = attr.field()


@attr_extensions.with_copy
@attr.define(kw_only=True, repr=False, weakref_slot=False)
class _InviteFields:
    code: str = attr.field()
    guild: typing.Optional[invite_models.InviteGuild] = attr.field()
    guild_id: typing.Optional[snowflakes.Snowflake] = attr.field()
    channel: typing.Optional[channel_models.PartialChannel] = attr.field()
    channel_id: snowflakes.Snowflake = attr.field()
    inviter: typing.Optional[user_models.User] = attr.field()
    target_user: typing.Optional[user_models.User] = attr.field()
    target_application: typing.Optional[application_models.InviteApplication] = attr.field()
    target_type: typing.Union[invite_models.TargetType, int, None] = attr.field()
    approximate_active_member_count: typing.Optional[int] = attr.field()
    approximate_member_count: typing.Optional[int] = attr.field()


@attr_extensions.with_copy
@attr.define(kw_only=True, repr=False, weakref_slot=False)
class _UserFields:
    id: snowflakes.Snowflake = attr.field()
    discriminator: str = attr.field()
    username: str = attr.field()
    avatar_hash: str = attr.field()
    banner_hash: typing.Optional[str] = attr.field()
    accent_color: typing.Optional[color_models.Color] = attr.field()
    is_bot: bool = attr.field()
    is_system: bool = attr.field()


class EntityFactoryImpl(entity_factory.EntityFactory):
    """Standard implementation for a serializer/deserializer.

    This will convert objects to/from JSON compatible representations.
    """

    __slots__: typing.Sequence[str] = (
        "_app",
        "_audit_log_entry_converters",
        "_audit_log_event_mapping",
        "_component_type_mapping",
        "_dm_channel_type_mapping",
        "_guild_channel_type_mapping",
        "_interaction_type_mapping",
        "_webhook_type_mapping",
    )

    def __init__(self, app: traits.RESTAware) -> None:
        self._app = app
        self._audit_log_entry_converters: typing.Dict[str, typing.Callable[[typing.Any], typing.Any]] = {
            audit_log_models.AuditLogChangeKey.OWNER_ID: snowflakes.Snowflake,
            audit_log_models.AuditLogChangeKey.AFK_CHANNEL_ID: snowflakes.Snowflake,
            audit_log_models.AuditLogChangeKey.AFK_TIMEOUT: _deserialize_seconds_timedelta,
            audit_log_models.AuditLogChangeKey.RULES_CHANNEL_ID: snowflakes.Snowflake,
            audit_log_models.AuditLogChangeKey.PUBLIC_UPDATES_CHANNEL_ID: snowflakes.Snowflake,
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
            audit_log_models.AuditLogChangeKey.PERMISSIONS: _with_int_cast(permission_models.Permissions),
            audit_log_models.AuditLogChangeKey.COLOR: color_models.Color,
            audit_log_models.AuditLogChangeKey.ALLOW: _with_int_cast(permission_models.Permissions),
            audit_log_models.AuditLogChangeKey.DENY: _with_int_cast(permission_models.Permissions),
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
            audit_log_models.AuditLogChangeKey.FORMAT_TYPE: sticker_models.StickerFormatType,
            audit_log_models.AuditLogChangeKey.GUILD_ID: snowflakes.Snowflake,
            audit_log_models.AuditLogChangeKey.ADD_ROLE_TO_MEMBER: self._deserialize_audit_log_change_roles,
            audit_log_models.AuditLogChangeKey.REMOVE_ROLE_FROM_MEMBER: self._deserialize_audit_log_change_roles,
            audit_log_models.AuditLogChangeKey.PERMISSION_OVERWRITES: self._deserialize_audit_log_overwrites,
        }
        self._audit_log_event_mapping: typing.Dict[
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
        self._component_type_mapping = {
            message_models.ComponentType.ACTION_ROW: self.deserialize_action_row,
            message_models.ComponentType.BUTTON: self.deserialize_button,
            message_models.ComponentType.SELECT_MENU: self.deserialize_select_menu,
        }
        self._dm_channel_type_mapping = {
            channel_models.ChannelType.DM: self.deserialize_dm,
            channel_models.ChannelType.GROUP_DM: self.deserialize_group_dm,
        }
        self._guild_channel_type_mapping = {
            channel_models.ChannelType.GUILD_CATEGORY: self.deserialize_guild_category,
            channel_models.ChannelType.GUILD_TEXT: self.deserialize_guild_text_channel,
            channel_models.ChannelType.GUILD_NEWS: self.deserialize_guild_news_channel,
            channel_models.ChannelType.GUILD_STORE: self.deserialize_guild_store_channel,
            channel_models.ChannelType.GUILD_VOICE: self.deserialize_guild_voice_channel,
            channel_models.ChannelType.GUILD_STAGE: self.deserialize_guild_stage_channel,
        }
        self._interaction_type_mapping: typing.Dict[
            int, typing.Callable[[data_binding.JSONObject], base_interactions.PartialInteraction]
        ] = {
            base_interactions.InteractionType.APPLICATION_COMMAND: self.deserialize_command_interaction,
            base_interactions.InteractionType.MESSAGE_COMPONENT: self.deserialize_component_interaction,
        }
        self._webhook_type_mapping = {
            webhook_models.WebhookType.INCOMING: self.deserialize_incoming_webhook,
            webhook_models.WebhookType.CHANNEL_FOLLOWER: self.deserialize_channel_follower_webhook,
            webhook_models.WebhookType.APPLICATION: self.deserialize_application_webhook,
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
        return application_models.OwnGuild(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            name=payload["name"],
            icon_hash=payload["icon"],
            features=[guild_models.GuildFeature(feature) for feature in payload["features"]],
            is_owner=bool(payload["owner"]),
            my_permissions=permission_models.Permissions(int(payload["permissions"])),
        )

    def deserialize_application(self, payload: data_binding.JSONObject) -> application_models.Application:
        team: typing.Optional[application_models.Team] = None
        if (team_payload := payload.get("team")) is not None:
            members = {}
            for member_payload in team_payload["members"]:
                team_member = application_models.TeamMember(
                    membership_state=application_models.TeamMembershipState(member_payload["membership_state"]),
                    permissions=member_payload["permissions"],
                    team_id=snowflakes.Snowflake(member_payload["team_id"]),
                    user=self.deserialize_user(member_payload["user"]),
                )
                members[team_member.user.id] = team_member

            team = application_models.Team(
                app=self._app,
                id=snowflakes.Snowflake(team_payload["id"]),
                name=team_payload["name"],
                icon_hash=team_payload["icon"],
                members=members,
                owner_id=snowflakes.Snowflake(team_payload["owner_user_id"]),
            )

        primary_sku_id = snowflakes.Snowflake(payload["primary_sku_id"]) if "primary_sku_id" in payload else None
        return application_models.Application(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            name=payload["name"],
            description=payload["description"] or None,
            is_bot_public=payload["bot_public"],
            is_bot_code_grant_required=payload["bot_require_code_grant"],
            owner=self.deserialize_user(payload["owner"]),
            rpc_origins=payload.get("rpc_origins"),
            summary=payload["summary"] or None,
            public_key=bytes.fromhex(payload["verify_key"]),
            flags=application_models.ApplicationFlags(payload["flags"]),
            icon_hash=payload.get("icon"),
            team=team,
            guild_id=snowflakes.Snowflake(payload["guild_id"]) if "guild_id" in payload else None,
            primary_sku_id=primary_sku_id,
            slug=payload.get("slug"),
            cover_image_hash=payload.get("cover_image"),
            privacy_policy_url=payload.get("privacy_policy_url"),
            terms_of_service_url=payload.get("terms_of_service_url"),
        )

    def deserialize_authorization_information(
        self, payload: data_binding.JSONObject
    ) -> application_models.AuthorizationInformation:
        application_payload = payload["application"]
        application = application_models.AuthorizationApplication(
            id=snowflakes.Snowflake(application_payload["id"]),
            name=application_payload["name"],
            description=application_payload["description"] or None,
            icon_hash=application_payload.get("icon"),
            summary=application_payload["summary"] or None,
            is_bot_public=application_payload.get("bot_public"),
            is_bot_code_grant_required=application_payload.get("bot_require_code_grant"),
            public_key=bytes.fromhex(application_payload["verify_key"]),
            terms_of_service_url=application_payload.get("terms_of_service_url"),
            privacy_policy_url=application_payload.get("privacy_policy_url"),
        )

        return application_models.AuthorizationInformation(
            application=application,
            scopes=[application_models.OAuth2Scope(scope) for scope in payload["scopes"]],
            expires_at=time.iso8601_datetime_string_to_datetime(payload["expires"]),
            user=self.deserialize_user(payload["user"]) if "user" in payload else None,
        )

    def deserialize_partial_token(self, payload: data_binding.JSONObject) -> application_models.PartialOAuth2Token:
        return application_models.PartialOAuth2Token(
            access_token=payload["access_token"],
            token_type=application_models.TokenType(payload["token_type"]),
            expires_in=datetime.timedelta(seconds=int(payload["expires_in"])),
            scopes=[application_models.OAuth2Scope(scope) for scope in payload["scope"].split(" ")],
        )

    def deserialize_authorization_token(
        self, payload: data_binding.JSONObject
    ) -> application_models.OAuth2AuthorizationToken:
        return application_models.OAuth2AuthorizationToken(
            access_token=payload["access_token"],
            token_type=application_models.TokenType(payload["token_type"]),
            expires_in=datetime.timedelta(seconds=int(payload["expires_in"])),
            scopes=[application_models.OAuth2Scope(scope) for scope in payload["scope"].split(" ")],
            refresh_token=payload["refresh_token"],
            webhook=self.deserialize_incoming_webhook(payload["webhook"]) if "webhook" in payload else None,
            guild=self.deserialize_rest_guild(payload["guild"]) if "guild" in payload else None,
        )

    def deserialize_implicit_token(self, query: data_binding.Query) -> application_models.OAuth2ImplicitToken:
        return application_models.OAuth2ImplicitToken(
            access_token=query["access_token"],
            token_type=application_models.TokenType(query["token_type"]),
            expires_in=datetime.timedelta(seconds=int(query["expires_in"])),
            scopes=[application_models.OAuth2Scope(scope) for scope in query["scope"].split(" ")],
            state=query.get("state"),
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

    def _deserialize_channel_overwrite_entry_info(
        self, payload: data_binding.JSONObject
    ) -> audit_log_models.ChannelOverwriteEntryInfo:
        return audit_log_models.ChannelOverwriteEntryInfo(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            type=channel_models.PermissionOverwriteType(payload["type"]),
            role_name=payload.get("role_name"),
        )

    def _deserialize_message_pin_entry_info(
        self, payload: data_binding.JSONObject
    ) -> audit_log_models.MessagePinEntryInfo:
        return audit_log_models.MessagePinEntryInfo(
            app=self._app,
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            message_id=snowflakes.Snowflake(payload["message_id"]),
        )

    def _deserialize_member_prune_entry_info(
        self, payload: data_binding.JSONObject
    ) -> audit_log_models.MemberPruneEntryInfo:
        return audit_log_models.MemberPruneEntryInfo(
            app=self._app,
            delete_member_days=datetime.timedelta(days=int(payload["delete_member_days"])),
            members_removed=int(payload["members_removed"]),
        )

    def _deserialize_message_bulk_delete_entry_info(
        self, payload: data_binding.JSONObject
    ) -> audit_log_models.MessageBulkDeleteEntryInfo:
        return audit_log_models.MessageBulkDeleteEntryInfo(app=self._app, count=int(payload["count"]))

    def _deserialize_message_delete_entry_info(
        self, payload: data_binding.JSONObject
    ) -> audit_log_models.MessageDeleteEntryInfo:
        return audit_log_models.MessageDeleteEntryInfo(
            app=self._app, channel_id=snowflakes.Snowflake(payload["channel_id"]), count=int(payload["count"])
        )

    def _deserialize_member_disconnect_entry_info(
        self, payload: data_binding.JSONObject
    ) -> audit_log_models.MemberDisconnectEntryInfo:
        return audit_log_models.MemberDisconnectEntryInfo(app=self._app, count=int(payload["count"]))

    def _deserialize_member_move_entry_info(
        self, payload: data_binding.JSONObject
    ) -> audit_log_models.MemberMoveEntryInfo:
        return audit_log_models.MemberMoveEntryInfo(
            app=self._app, channel_id=snowflakes.Snowflake(payload["channel_id"]), count=int(payload["count"])
        )

    def deserialize_audit_log(self, payload: data_binding.JSONObject) -> audit_log_models.AuditLog:
        entries = {}
        for entry_payload in payload["audit_log_entries"]:
            entry_id = snowflakes.Snowflake(entry_payload["id"])

            changes = []
            if (change_payloads := entry_payload.get("changes")) is not None:
                for change_payload in change_payloads:
                    key: typing.Union[audit_log_models.AuditLogChangeKey, str] = audit_log_models.AuditLogChangeKey(
                        change_payload["key"]
                    )

                    new_value = change_payload.get("new_value")
                    old_value = change_payload.get("old_value")
                    if value_converter := self._audit_log_entry_converters.get(key):
                        new_value = value_converter(new_value) if new_value is not None else None
                        old_value = value_converter(old_value) if old_value is not None else None

                    elif not isinstance(key, audit_log_models.AuditLogChangeKey):
                        _LOGGER.debug("Unknown audit log change key found %r", key)

                    changes.append(audit_log_models.AuditLogChange(key=key, new_value=new_value, old_value=old_value))

            target_id: typing.Optional[snowflakes.Snowflake] = None
            if (raw_target_id := entry_payload["target_id"]) is not None:
                target_id = snowflakes.Snowflake(raw_target_id)

            user_id: typing.Optional[snowflakes.Snowflake] = None
            if (raw_user_id := entry_payload["user_id"]) is not None:
                user_id = snowflakes.Snowflake(raw_user_id)

            action_type: typing.Union[audit_log_models.AuditLogEventType, int]
            action_type = audit_log_models.AuditLogEventType(entry_payload["action_type"])

            options: typing.Optional[audit_log_models.BaseAuditLogEntryInfo] = None
            if (raw_option := entry_payload.get("options")) is not None:
                if option_converter := self._audit_log_event_mapping.get(action_type):
                    options = option_converter(raw_option)

                else:
                    _LOGGER.debug("Unknown audit log action type found %r", action_type)
                    continue

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

        webhooks: typing.Dict[snowflakes.Snowflake, webhook_models.PartialWebhook] = {}
        for webhook_payload in payload["webhooks"]:
            try:
                webhook = self.deserialize_webhook(webhook_payload)

            except errors.UnrecognisedEntityError:
                continue

            webhooks[webhook.id] = webhook

        return audit_log_models.AuditLog(entries=entries, integrations=integrations, users=users, webhooks=webhooks)

    ##################
    # CHANNEL MODELS #
    ##################

    def deserialize_channel_follow(self, payload: data_binding.JSONObject) -> channel_models.ChannelFollow:
        return channel_models.ChannelFollow(
            app=self._app,
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            webhook_id=snowflakes.Snowflake(payload["webhook_id"]),
        )

    def deserialize_permission_overwrite(self, payload: data_binding.JSONObject) -> channel_models.PermissionOverwrite:
        return channel_models.PermissionOverwrite(
            # PermissionOverwrite's init has converters set for these fields which will handle casting
            id=payload["id"],
            type=payload["type"],
            # Permissions still have to be cast to int before they can be cast to Permission typing wise.
            allow=int(payload["allow"]),
            deny=int(payload["deny"]),
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

    def deserialize_dm(self, payload: data_binding.JSONObject) -> channel_models.DMChannel:
        last_message_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_last_message_id := payload.get("last_message_id")) is not None:
            last_message_id = snowflakes.Snowflake(raw_last_message_id)

        return channel_models.DMChannel(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            name=payload.get("name"),
            type=channel_models.ChannelType(payload["type"]),
            last_message_id=last_message_id,
            recipient=self.deserialize_user(payload["recipients"][0]),
        )

    def deserialize_group_dm(self, payload: data_binding.JSONObject) -> channel_models.GroupDMChannel:
        last_message_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_last_message_id := payload.get("last_message_id")) is not None:
            last_message_id = snowflakes.Snowflake(raw_last_message_id)

        if (raw_nicks := payload.get("nicks")) is not None:
            nicknames = {snowflakes.Snowflake(entry["id"]): entry["nick"] for entry in raw_nicks}
        else:
            nicknames = {}

        recipients = {snowflakes.Snowflake(user["id"]): self.deserialize_user(user) for user in payload["recipients"]}

        return channel_models.GroupDMChannel(
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
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake],
    ) -> _GuildChannelFields:
        if guild_id is undefined.UNDEFINED:
            guild_id = snowflakes.Snowflake(payload["guild_id"])

        permission_overwrites = {
            snowflakes.Snowflake(overwrite["id"]): self.deserialize_permission_overwrite(overwrite)
            for overwrite in payload["permission_overwrites"]
        }

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
        if (raw_last_message_id := payload.get("last_message_id")) is not None:
            last_message_id = snowflakes.Snowflake(raw_last_message_id)

        last_pin_timestamp: typing.Optional[datetime.datetime] = None
        if (raw_last_pin_timestamp := payload.get("last_pin_timestamp")) is not None:
            last_pin_timestamp = time.iso8601_datetime_string_to_datetime(raw_last_pin_timestamp)

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
        if (raw_last_message_id := payload.get("last_message_id")) is not None:
            last_message_id = snowflakes.Snowflake(raw_last_message_id)

        last_pin_timestamp: typing.Optional[datetime.datetime] = None
        if (raw_last_pin_timestamp := payload.get("last_pin_timestamp")) is not None:
            last_pin_timestamp = time.iso8601_datetime_string_to_datetime(raw_last_pin_timestamp)

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
        # Discord seems to be only returning this after it's been initially PATCHed in for older channels.
        video_quality_mode = payload.get("video_quality_mode", channel_models.VideoQualityMode.AUTO)
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
            # There seems to be an edge case where rtc_region won't be included in gateway events (e.g. GUILD_CREATE)
            # for a voice channel that just hasn't been touched since this was introduced (e.g. has been archived).
            region=payload.get("rtc_region"),
            bitrate=int(payload["bitrate"]),
            user_limit=int(payload["user_limit"]),
            video_quality_mode=channel_models.VideoQualityMode(int(video_quality_mode)),
        )

    def deserialize_guild_stage_channel(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.GuildStageChannel:
        channel_fields = self._set_guild_channel_attributes(payload, guild_id=guild_id)
        return channel_models.GuildStageChannel(
            app=self._app,
            id=channel_fields.id,
            name=channel_fields.name,
            type=channel_fields.type,
            guild_id=channel_fields.guild_id,
            position=channel_fields.position,
            permission_overwrites=channel_fields.permission_overwrites,
            is_nsfw=channel_fields.is_nsfw,
            parent_id=channel_fields.parent_id,
            region=payload["rtc_region"],
            bitrate=int(payload["bitrate"]),
            user_limit=int(payload["user_limit"]),
        )

    def deserialize_channel(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.PartialChannel:
        channel_type = channel_models.ChannelType(payload["type"])
        if guild_channel_model := self._guild_channel_type_mapping.get(channel_type):
            return guild_channel_model(payload, guild_id=guild_id)

        if dm_channel_model := self._dm_channel_type_mapping.get(channel_type):
            return dm_channel_model(payload)

        _LOGGER.debug(f"Unrecognised channel type {channel_type}")
        raise errors.UnrecognisedEntityError(f"Unrecognised channel type {channel_type}")

    ################
    # EMBED MODELS #
    ################

    def deserialize_embed(self, payload: data_binding.JSONObject) -> embed_models.Embed:
        # Keep these separate to aid debugging later.
        title = payload.get("title")
        description = payload.get("description")
        url = payload.get("url")
        color = color_models.Color(payload["color"]) if "color" in payload else None
        timestamp = time.iso8601_datetime_string_to_datetime(payload["timestamp"]) if "timestamp" in payload else None
        fields: typing.Optional[typing.List[embed_models.EmbedField]] = None

        image: typing.Optional[embed_models.EmbedImage[files.AsyncReader]] = None
        if (image_payload := payload.get("image")) and "url" in image_payload:
            proxy = files.ensure_resource(image_payload["proxy_url"]) if "proxy_url" in image_payload else None
            image = embed_models.EmbedImage(
                resource=files.ensure_resource(image_payload["url"]),
                proxy_resource=proxy,
                height=image_payload.get("height"),
                width=image_payload.get("width"),
            )

        thumbnail: typing.Optional[embed_models.EmbedImage[files.AsyncReader]] = None
        if (thumbnail_payload := payload.get("thumbnail")) and "url" in thumbnail_payload:
            proxy = files.ensure_resource(thumbnail_payload["proxy_url"]) if "proxy_url" in thumbnail_payload else None
            thumbnail = embed_models.EmbedImage(
                resource=files.ensure_resource(thumbnail_payload["url"]),
                proxy_resource=proxy,
                height=thumbnail_payload.get("height"),
                width=thumbnail_payload.get("width"),
            )

        video: typing.Optional[embed_models.EmbedVideo[files.AsyncReader]] = None
        if (video_payload := payload.get("video")) and "url" in video_payload:
            raw_proxy_url = video_payload.get("proxy_url")
            video = embed_models.EmbedVideo(
                resource=files.ensure_resource(video_payload["url"]),
                proxy_resource=files.ensure_resource(raw_proxy_url) if raw_proxy_url else None,
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
                raw_proxy_url = author_payload.get("proxy_icon_url")
                icon = embed_models.EmbedResourceWithProxy(
                    resource=files.ensure_resource(author_payload["icon_url"]),
                    proxy_resource=files.ensure_resource(raw_proxy_url) if raw_proxy_url else None,
                )

            author = embed_models.EmbedAuthor(
                name=author_payload.get("name"),
                url=author_payload.get("url"),
                icon=icon,
            )

        footer: typing.Optional[embed_models.EmbedFooter] = None
        if footer_payload := payload.get("footer"):
            icon = None
            if "icon_url" in footer_payload:
                raw_proxy_url = footer_payload.get("proxy_icon_url")
                icon = embed_models.EmbedResourceWithProxy(
                    resource=files.ensure_resource(footer_payload["icon_url"]),
                    proxy_resource=files.ensure_resource(raw_proxy_url) if raw_proxy_url else None,
                )

            footer = embed_models.EmbedFooter(text=footer_payload.get("text"), icon=icon)

        if fields_array := payload.get("fields"):
            fields = []
            for field_payload in fields_array:
                field = embed_models.EmbedField(
                    name=field_payload["name"],
                    value=field_payload["value"],
                    inline=field_payload.get("inline", False),
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

    def serialize_embed(  # noqa: C901 - Function too complex
        self,
        embed: embed_models.Embed,
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

                # Yep, these are technically two unreachable branches. However, this is an incredibly
                # common mistake to make when working with embeds and not using a static type
                # checker, so I have added these as additional safeguards for UX and ease
                # of debugging. The case that there are `None` should be detected immediately by
                # static type checkers, regardless.
                name = str(field.name) if field.name is not None else None
                value = str(field.value) if field.value is not None else None

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
        return emoji_models.UnicodeEmoji(payload["name"])

    def deserialize_custom_emoji(self, payload: data_binding.JSONObject) -> emoji_models.CustomEmoji:
        return emoji_models.CustomEmoji(
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

    def deserialize_gateway_bot_info(self, payload: data_binding.JSONObject) -> gateway_models.GatewayBotInfo:
        session_start_limit_payload = payload["session_start_limit"]
        session_start_limit = gateway_models.SessionStartLimit(
            total=int(session_start_limit_payload["total"]),
            remaining=int(session_start_limit_payload["remaining"]),
            reset_after=datetime.timedelta(milliseconds=session_start_limit_payload["reset_after"]),
            # I do not trust that this may never be zero for some unknown reason. If it was 0, it
            # would hang the application on start up, so I enforce it is at least 1.
            max_concurrency=max(session_start_limit_payload.get("max_concurrency", 0), 1),
        )
        return gateway_models.GatewayBotInfo(
            url=payload["url"],
            shard_count=int(payload["shards"]),
            session_start_limit=session_start_limit,
        )

    ################
    # GUILD MODELS #
    ################

    def deserialize_guild_widget(self, payload: data_binding.JSONObject) -> guild_models.GuildWidget:
        channel_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_channel_id := payload["channel_id"]) is not None:
            channel_id = snowflakes.Snowflake(raw_channel_id)

        return guild_models.GuildWidget(app=self._app, channel_id=channel_id, is_enabled=payload["enabled"])

    def deserialize_welcome_screen(self, payload: data_binding.JSONObject) -> guild_models.WelcomeScreen:
        channels: typing.List[guild_models.WelcomeChannel] = []

        for channel_payload in payload["welcome_channels"]:
            raw_emoji_id = channel_payload["emoji_id"]
            emoji_id = snowflakes.Snowflake(raw_emoji_id) if raw_emoji_id else None

            emoji_name: typing.Union[None, emoji_models.UnicodeEmoji, str]
            if (emoji_name := channel_payload["emoji_name"]) and not emoji_id:
                emoji_name = emoji_models.UnicodeEmoji(emoji_name)

            channels.append(
                guild_models.WelcomeChannel(
                    channel_id=snowflakes.Snowflake(channel_payload["channel_id"]),
                    description=channel_payload["description"],
                    emoji_id=emoji_id,
                    emoji_name=emoji_name,
                )
            )

        return guild_models.WelcomeScreen(description=payload["description"], channels=channels)

    def serialize_welcome_channel(self, welcome_channel: guild_models.WelcomeChannel) -> data_binding.JSONObject:
        payload: data_binding.JSONObject = {
            "channel_id": str(welcome_channel.channel_id),
            "description": welcome_channel.description,
        }

        if welcome_channel.emoji_id is not None:
            payload["emoji_id"] = str(welcome_channel.emoji_id)

        elif welcome_channel.emoji_name is not None:
            payload["emoji_name"] = str(welcome_channel.emoji_name)

        return payload

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
        # If Discord ever does start including this here without warning we don't want to duplicate the entry.
        if guild_id not in role_ids:
            role_ids.append(guild_id)

        joined_at = time.iso8601_datetime_string_to_datetime(payload["joined_at"])

        raw_premium_since = payload.get("premium_since")
        premium_since = (
            time.iso8601_datetime_string_to_datetime(raw_premium_since) if raw_premium_since is not None else None
        )

        if raw_communication_disabled_until := payload.get("communication_disabled_until"):
            communication_disabled_until = time.iso8601_datetime_string_to_datetime(raw_communication_disabled_until)
        else:
            communication_disabled_until = None

        return guild_models.Member(
            user=user,
            guild_id=guild_id,
            role_ids=role_ids,
            joined_at=joined_at,
            nickname=payload.get("nick"),
            guild_avatar_hash=payload.get("avatar"),
            premium_since=premium_since,
            is_deaf=payload.get("deaf", undefined.UNDEFINED),
            is_mute=payload.get("mute", undefined.UNDEFINED),
            is_pending=payload.get("pending", undefined.UNDEFINED),
            raw_communication_disabled_until=communication_disabled_until,
        )

    def deserialize_role(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: snowflakes.Snowflake,
    ) -> guild_models.Role:
        bot_id: typing.Optional[snowflakes.Snowflake] = None
        integration_id: typing.Optional[snowflakes.Snowflake] = None
        is_premium_subscriber_role: bool = False
        if "tags" in payload:
            tags_payload = payload["tags"]
            if "bot_id" in tags_payload:
                bot_id = snowflakes.Snowflake(tags_payload["bot_id"])
            if "integration_id" in tags_payload:
                integration_id = snowflakes.Snowflake(tags_payload["integration_id"])
            if "premium_subscriber" in tags_payload:
                is_premium_subscriber_role = True

        emoji: typing.Optional[emoji_models.UnicodeEmoji] = None
        if (raw_emoji := payload.get("unicode_emoji")) is not None:
            emoji = emoji_models.UnicodeEmoji(raw_emoji)

        return guild_models.Role(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            guild_id=guild_id,
            name=payload["name"],
            color=color_models.Color(payload["color"]),
            is_hoisted=payload["hoist"],
            icon_hash=payload.get("icon"),
            unicode_emoji=emoji,
            position=int(payload["position"]),
            permissions=permission_models.Permissions(int(payload["permissions"])),
            is_managed=payload["managed"],
            is_mentionable=payload["mentionable"],
            bot_id=bot_id,
            integration_id=integration_id,
            is_premium_subscriber_role=is_premium_subscriber_role,
        )

    @staticmethod
    def _set_partial_integration_attributes(payload: data_binding.JSONObject) -> _IntegrationFields:
        account_payload = payload["account"]
        account = guild_models.IntegrationAccount(id=account_payload["id"], name=account_payload["name"])
        return _IntegrationFields(
            id=snowflakes.Snowflake(payload["id"]),
            name=payload["name"],
            type=guild_models.IntegrationType(payload["type"]),
            account=account,
        )

    def deserialize_partial_integration(self, payload: data_binding.JSONObject) -> guild_models.PartialIntegration:
        integration_fields = self._set_partial_integration_attributes(payload)
        return guild_models.PartialIntegration(
            id=integration_fields.id,
            name=integration_fields.name,
            type=integration_fields.type,
            account=integration_fields.account,
        )

    def deserialize_integration(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> guild_models.Integration:
        integration_fields = self._set_partial_integration_attributes(payload)

        role_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_role_id := payload.get("role_id")) is not None:
            role_id = snowflakes.Snowflake(raw_role_id)

        last_synced_at: typing.Optional[datetime.datetime] = None
        if (raw_last_synced_at := payload.get("synced_at")) is not None:
            last_synced_at = time.iso8601_datetime_string_to_datetime(raw_last_synced_at)

        expire_grace_period: typing.Optional[datetime.timedelta] = None
        if (raw_expire_grace_period := payload.get("expire_grace_period")) is not None:
            expire_grace_period = datetime.timedelta(days=raw_expire_grace_period)

        expire_behavior: typing.Union[guild_models.IntegrationExpireBehaviour, int, None] = None
        if (raw_expire_behavior := payload.get("expire_behavior")) is not None:
            expire_behavior = guild_models.IntegrationExpireBehaviour(raw_expire_behavior)

        user: typing.Optional[user_models.User] = None
        if (raw_user := payload.get("user")) is not None:
            user = self.deserialize_user(raw_user)

        application: typing.Optional[guild_models.IntegrationApplication] = None
        if (raw_application := payload.get("application")) is not None:
            bot: typing.Optional[user_models.User] = None
            if (raw_application_bot := raw_application.get("bot")) is not None:
                bot = self.deserialize_user(raw_application_bot)

            application = guild_models.IntegrationApplication(
                id=snowflakes.Snowflake(raw_application["id"]),
                name=raw_application["name"],
                icon_hash=raw_application["icon"],
                summary=raw_application["summary"] or None,
                description=raw_application["description"] or None,
                bot=bot,
            )

        return guild_models.Integration(
            id=integration_fields.id,
            guild_id=guild_id if guild_id is not undefined.UNDEFINED else snowflakes.Snowflake(payload["guild_id"]),
            name=integration_fields.name,
            type=integration_fields.type,
            account=integration_fields.account,
            is_enabled=payload["enabled"],
            is_syncing=payload.get("syncing"),
            is_revoked=payload.get("revoked"),
            role_id=role_id,
            is_emojis_enabled=payload.get("enable_emoticons"),
            expire_behavior=expire_behavior,
            expire_grace_period=expire_grace_period,
            user=user,
            last_synced_at=last_synced_at,
            subscriber_count=payload.get("subscriber_count"),
            application=application,
        )

    def deserialize_guild_member_ban(self, payload: data_binding.JSONObject) -> guild_models.GuildBan:
        return guild_models.GuildBan(reason=payload["reason"], user=self.deserialize_user(payload["user"]))

    def deserialize_guild_preview(self, payload: data_binding.JSONObject) -> guild_models.GuildPreview:
        guild_id = snowflakes.Snowflake(payload["id"])
        emojis = {
            snowflakes.Snowflake(emoji["id"]): self.deserialize_known_custom_emoji(emoji, guild_id=guild_id)
            for emoji in payload["emojis"]
        }
        return guild_models.GuildPreview(
            app=self._app,
            id=guild_id,
            name=payload["name"],
            icon_hash=payload["icon"],
            features=[guild_models.GuildFeature(feature) for feature in payload["features"]],
            splash_hash=payload["splash"],
            discovery_splash_hash=payload["discovery_splash"],
            emojis=emojis,
            approximate_active_member_count=int(payload["approximate_presence_count"]),
            approximate_member_count=int(payload["approximate_member_count"]),
            description=payload["description"],
        )

    def _set_guild_attributes(self, payload: data_binding.JSONObject) -> _GuildFields:
        afk_channel_id = payload["afk_channel_id"]
        default_message_notifications = guild_models.GuildMessageNotificationsLevel(
            payload["default_message_notifications"]
        )
        application_id = payload["application_id"]
        widget_channel_id = payload.get("widget_channel_id")
        system_channel_id = payload["system_channel_id"]
        rules_channel_id = payload["rules_channel_id"]
        max_video_channel_users = (
            int(payload["max_video_channel_users"]) if "max_video_channel_users" in payload else None
        )
        public_updates_channel_id = payload["public_updates_channel_id"]
        public_updates_channel_id = (
            snowflakes.Snowflake(public_updates_channel_id) if public_updates_channel_id is not None else None
        )
        return _GuildFields(
            id=snowflakes.Snowflake(payload["id"]),
            name=payload["name"],
            icon_hash=payload["icon"],
            features=[guild_models.GuildFeature(feature) for feature in payload["features"]],
            splash_hash=payload["splash"],
            # This is documented as always being present, but we have found old guilds where this is
            # not present. Quicker to just assume the documentation is wrong at this point than try
            # to contest whether this is right or not with Discord.
            discovery_splash_hash=payload.get("discovery_splash"),
            owner_id=snowflakes.Snowflake(payload["owner_id"]),
            afk_channel_id=snowflakes.Snowflake(afk_channel_id) if afk_channel_id is not None else None,
            afk_timeout=datetime.timedelta(seconds=payload["afk_timeout"]),
            verification_level=guild_models.GuildVerificationLevel(payload["verification_level"]),
            default_message_notifications=default_message_notifications,
            explicit_content_filter=guild_models.GuildExplicitContentFilterLevel(payload["explicit_content_filter"]),
            mfa_level=guild_models.GuildMFALevel(payload["mfa_level"]),
            application_id=snowflakes.Snowflake(application_id) if application_id is not None else None,
            widget_channel_id=snowflakes.Snowflake(widget_channel_id) if widget_channel_id is not None else None,
            system_channel_id=snowflakes.Snowflake(system_channel_id) if system_channel_id is not None else None,
            is_widget_enabled=payload.get("widget_enabled"),
            system_channel_flags=guild_models.GuildSystemChannelFlag(payload["system_channel_flags"]),
            rules_channel_id=snowflakes.Snowflake(rules_channel_id) if rules_channel_id is not None else None,
            max_video_channel_users=max_video_channel_users,
            vanity_url_code=payload["vanity_url_code"],
            description=payload["description"],
            banner_hash=payload["banner"],
            premium_tier=guild_models.GuildPremiumTier(payload["premium_tier"]),
            premium_subscription_count=payload.get("premium_subscription_count"),
            preferred_locale=payload["preferred_locale"],
            public_updates_channel_id=public_updates_channel_id,
            nsfw_level=guild_models.GuildNSFWLevel(payload["nsfw_level"]),
        )

    def deserialize_rest_guild(self, payload: data_binding.JSONObject) -> guild_models.RESTGuild:
        guild_fields = self._set_guild_attributes(payload)

        approximate_member_count: typing.Optional[int] = None
        if "approximate_member_count" in payload:
            approximate_member_count = int(payload["approximate_member_count"])

        approximate_active_member_count: typing.Optional[int] = None
        if "approximate_presence_count" in payload:
            approximate_active_member_count = int(payload["approximate_presence_count"])

        max_members = int(payload["max_members"])

        raw_max_presences = payload["max_presences"]
        max_presences = int(raw_max_presences) if raw_max_presences is not None else None

        roles = {
            snowflakes.Snowflake(role["id"]): self.deserialize_role(role, guild_id=guild_fields.id)
            for role in payload["roles"]
        }
        emojis = {
            snowflakes.Snowflake(emoji["id"]): self.deserialize_known_custom_emoji(emoji, guild_id=guild_fields.id)
            for emoji in payload["emojis"]
        }
        return guild_models.RESTGuild(
            app=self._app,
            id=guild_fields.id,
            name=guild_fields.name,
            icon_hash=guild_fields.icon_hash,
            features=guild_fields.features,
            splash_hash=guild_fields.splash_hash,
            discovery_splash_hash=guild_fields.discovery_splash_hash,
            owner_id=guild_fields.owner_id,
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
            max_presences=max_presences,
            max_members=max_members,
            max_video_channel_users=guild_fields.max_video_channel_users,
            vanity_url_code=guild_fields.vanity_url_code,
            description=guild_fields.description,
            banner_hash=guild_fields.banner_hash,
            premium_tier=guild_fields.premium_tier,
            nsfw_level=guild_fields.nsfw_level,
            premium_subscription_count=guild_fields.premium_subscription_count,
            preferred_locale=guild_fields.preferred_locale,
            public_updates_channel_id=guild_fields.public_updates_channel_id,
            approximate_member_count=approximate_member_count,
            approximate_active_member_count=approximate_active_member_count,
            roles=roles,
            emojis=emojis,
        )

    def deserialize_gateway_guild(self, payload: data_binding.JSONObject) -> entity_factory.GatewayGuildDefinition:
        guild_fields = self._set_guild_attributes(payload)
        is_large = payload.get("large")
        joined_at = time.iso8601_datetime_string_to_datetime(payload["joined_at"]) if "joined_at" in payload else None
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
            max_video_channel_users=guild_fields.max_video_channel_users,
            vanity_url_code=guild_fields.vanity_url_code,
            description=guild_fields.description,
            banner_hash=guild_fields.banner_hash,
            premium_tier=guild_fields.premium_tier,
            premium_subscription_count=guild_fields.premium_subscription_count,
            preferred_locale=guild_fields.preferred_locale,
            public_updates_channel_id=guild_fields.public_updates_channel_id,
            nsfw_level=guild_fields.nsfw_level,
            is_large=is_large,
            joined_at=joined_at,
            member_count=member_count,
        )

        members: typing.Optional[typing.Dict[snowflakes.Snowflake, guild_models.Member]] = None
        if "members" in payload:
            members = {}

            for member_payload in payload["members"]:
                member = self.deserialize_member(member_payload, guild_id=guild.id)
                members[member.user.id] = member

        channels: typing.Optional[typing.Dict[snowflakes.Snowflake, channel_models.GuildChannel]] = None
        if "channels" in payload:
            channels = {}

            for channel_payload in payload["channels"]:
                try:
                    channel = self.deserialize_channel(channel_payload, guild_id=guild.id)
                except errors.UnrecognisedEntityError:
                    # Ignore the channel, this has already been logged
                    continue

                assert isinstance(channel, channel_models.GuildChannel)
                channels[channel.id] = channel

        presences: typing.Optional[typing.Dict[snowflakes.Snowflake, presence_models.MemberPresence]] = None
        if "presences" in payload:
            presences = {}

            for presence_payload in payload["presences"]:
                presence = self.deserialize_member_presence(presence_payload, guild_id=guild.id)
                presences[presence.user_id] = presence

        voice_states: typing.Optional[typing.Dict[snowflakes.Snowflake, voice_models.VoiceState]] = None
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
            raw_welcome_screen = guild_payload.get("welcome_screen")

            guild = invite_models.InviteGuild(
                app=self._app,
                id=snowflakes.Snowflake(guild_payload["id"]),
                name=guild_payload["name"],
                features=[guild_models.GuildFeature(feature) for feature in guild_payload["features"]],
                icon_hash=guild_payload["icon"],
                splash_hash=guild_payload["splash"],
                banner_hash=guild_payload["banner"],
                description=guild_payload["description"],
                verification_level=guild_models.GuildVerificationLevel(guild_payload["verification_level"]),
                vanity_url_code=guild_payload["vanity_url_code"],
                welcome_screen=self.deserialize_welcome_screen(raw_welcome_screen) if raw_welcome_screen else None,
                nsfw_level=guild_models.GuildNSFWLevel(guild_payload["nsfw_level"]),
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

        target_application: typing.Optional[application_models.InviteApplication] = None
        if (invite_payload := payload.get("target_application")) is not None:
            target_application = application_models.InviteApplication(
                app=self._app,
                id=snowflakes.Snowflake(invite_payload["id"]),
                name=invite_payload["name"],
                description=invite_payload["description"] or None,
                summary=invite_payload["summary"] or None,
                public_key=bytes.fromhex(invite_payload["verify_key"]),
                icon_hash=invite_payload.get("icon"),
                cover_image_hash=invite_payload.get("cover_image"),
            )

        approximate_active_member_count = (
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
            target_type=invite_models.TargetType(payload["target_type"]) if "target_type" in payload else None,
            target_user=self.deserialize_user(payload["target_user"]) if "target_user" in payload else None,
            target_application=target_application,
            approximate_active_member_count=approximate_active_member_count,
            approximate_member_count=approximate_member_count,
        )

    def deserialize_invite(self, payload: data_binding.JSONObject) -> invite_models.Invite:
        invite_fields = self._set_invite_attributes(payload)

        expires_at: typing.Optional[datetime.datetime] = None
        if raw_expires_at := payload.get("expires_at"):
            expires_at = time.iso8601_datetime_string_to_datetime(raw_expires_at)

        return invite_models.Invite(
            app=self._app,
            code=invite_fields.code,
            guild=invite_fields.guild,
            guild_id=invite_fields.guild_id,
            channel=invite_fields.channel,
            channel_id=invite_fields.channel_id,
            inviter=invite_fields.inviter,
            target_type=invite_fields.target_type,
            target_user=invite_fields.target_user,
            target_application=invite_fields.target_application,
            approximate_member_count=invite_fields.approximate_member_count,
            approximate_active_member_count=invite_fields.approximate_active_member_count,
            expires_at=expires_at,
        )

    def deserialize_invite_with_metadata(self, payload: data_binding.JSONObject) -> invite_models.InviteWithMetadata:
        invite_fields = self._set_invite_attributes(payload)
        created_at = time.iso8601_datetime_string_to_datetime(payload["created_at"])
        max_uses = int(payload["max_uses"])

        expires_at: typing.Optional[datetime.datetime] = None
        max_age: typing.Optional[datetime.timedelta] = None
        if (raw_max_age := payload["max_age"]) > 0:
            max_age = datetime.timedelta(seconds=raw_max_age)
            expires_at = created_at + max_age

        return invite_models.InviteWithMetadata(
            app=self._app,
            code=invite_fields.code,
            guild=invite_fields.guild,
            guild_id=invite_fields.guild_id,
            channel=invite_fields.channel,
            channel_id=invite_fields.channel_id,
            inviter=invite_fields.inviter,
            target_type=invite_fields.target_type,
            target_user=invite_fields.target_user,
            target_application=invite_fields.target_application,
            approximate_member_count=invite_fields.approximate_member_count,
            approximate_active_member_count=invite_fields.approximate_active_member_count,
            uses=int(payload["uses"]),
            max_uses=max_uses if max_uses > 0 else None,
            max_age=max_age,
            is_temporary=payload["temporary"],
            created_at=created_at,
            expires_at=expires_at,
        )

    ######################
    # INTERACTION MODELS #
    ######################

    def _deserialize_command_option(self, payload: data_binding.JSONObject) -> commands.CommandOption:
        choices: typing.Optional[typing.List[commands.CommandChoice]] = None
        if raw_choices := payload.get("choices"):
            choices = [commands.CommandChoice(name=choice["name"], value=choice["value"]) for choice in raw_choices]

        suboptions: typing.Optional[typing.List[commands.CommandOption]] = None
        if raw_options := payload.get("options"):
            suboptions = [self._deserialize_command_option(option) for option in raw_options]

        channel_types: typing.Optional[typing.Sequence[typing.Union[channel_models.ChannelType, int]]] = None
        if raw_channel_types := payload.get("channel_types"):
            channel_types = [channel_models.ChannelType(channel_type) for channel_type in raw_channel_types]

        return commands.CommandOption(
            type=commands.OptionType(payload["type"]),
            name=payload["name"],
            description=payload["description"],
            is_required=payload.get("required", False),
            choices=choices,
            options=suboptions,
            channel_types=channel_types,
            min_value=payload.get("min_value"),
            max_value=payload.get("max_value"),
        )

    def deserialize_command(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedNoneOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> commands.Command:
        if guild_id is undefined.UNDEFINED:
            raw_guild_id = payload["guild_id"]
            guild_id = snowflakes.Snowflake(raw_guild_id) if raw_guild_id is not None else None

        options: typing.Optional[typing.List[commands.CommandOption]] = None
        if raw_options := payload.get("options"):
            options = [self._deserialize_command_option(option) for option in raw_options]

        return commands.Command(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            application_id=snowflakes.Snowflake(payload["application_id"]),
            name=payload["name"],
            description=payload["description"],
            options=options,
            default_permission=payload.get("default_permission", True),
            guild_id=guild_id,
            version=snowflakes.Snowflake(payload["version"]),
        )

    def deserialize_guild_command_permissions(
        self, payload: data_binding.JSONObject
    ) -> commands.GuildCommandPermissions:
        permissions = [
            commands.CommandPermission(
                id=snowflakes.Snowflake(perm["id"]),
                type=commands.CommandPermissionType(perm["type"]),
                has_access=perm["permission"],
            )
            for perm in payload["permissions"]
        ]
        return commands.GuildCommandPermissions(
            application_id=snowflakes.Snowflake(payload["application_id"]),
            command_id=snowflakes.Snowflake(payload["id"]),
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
            permissions=permissions,
        )

    def serialize_command_permission(self, permission: commands.CommandPermission) -> data_binding.JSONObject:
        return {"id": str(permission.id), "type": permission.type, "permission": permission.has_access}

    def deserialize_partial_interaction(self, payload: data_binding.JSONObject) -> base_interactions.PartialInteraction:
        return base_interactions.PartialInteraction(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            type=base_interactions.InteractionType(payload["type"]),
            token=payload["token"],
            version=payload["version"],
            application_id=snowflakes.Snowflake(payload["application_id"]),
        )

    def _deserialize_interaction_command_option(
        self, payload: data_binding.JSONObject
    ) -> command_interactions.CommandInteractionOption:
        suboptions: typing.Optional[typing.List[command_interactions.CommandInteractionOption]] = None
        if raw_suboptions := payload.get("options"):
            suboptions = [self._deserialize_interaction_command_option(suboption) for suboption in raw_suboptions]

        option_type = commands.OptionType(payload["type"])
        value = payload.get("value")
        if modifier := _interaction_option_type_mapping.get(option_type):
            value = modifier(value)

        return command_interactions.CommandInteractionOption(
            name=payload["name"],
            type=option_type,
            value=value,
            options=suboptions,
        )

    def _deserialize_interaction_member(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: snowflakes.Snowflake,
        user: typing.Optional[user_models.User] = None,
    ) -> base_interactions.InteractionMember:
        if not user:
            user = self.deserialize_user(payload["user"])

        role_ids = [snowflakes.Snowflake(role_id) for role_id in payload["roles"]]
        # If Discord ever does start including this here without warning we don't want to duplicate the entry.
        if guild_id not in role_ids:
            role_ids.append(guild_id)

        premium_since: typing.Optional[datetime.datetime] = None
        if (raw_premium_since := payload.get("premium_since")) is not None:
            premium_since = time.iso8601_datetime_string_to_datetime(raw_premium_since)

        if raw_disabled_until := payload.get("communication_disabled_until"):
            disabled_until = time.iso8601_datetime_string_to_datetime(raw_disabled_until)
        else:
            disabled_until = None

        # TODO: deduplicate member unmarshalling logic
        return base_interactions.InteractionMember(
            user=user,
            guild_id=guild_id,
            role_ids=role_ids,
            joined_at=time.iso8601_datetime_string_to_datetime(payload["joined_at"]),
            premium_since=premium_since,
            guild_avatar_hash=payload.get("avatar"),
            nickname=payload.get("nick"),
            is_deaf=payload.get("deaf", undefined.UNDEFINED),
            is_mute=payload.get("mute", undefined.UNDEFINED),
            is_pending=payload.get("pending", undefined.UNDEFINED),
            permissions=permission_models.Permissions(int(payload["permissions"])),
            raw_communication_disabled_until=disabled_until,
        )

    def deserialize_command_interaction(
        self, payload: data_binding.JSONObject
    ) -> command_interactions.CommandInteraction:
        data_payload = payload["data"]

        guild_id: typing.Optional[snowflakes.Snowflake] = None
        if raw_guild_id := payload.get("guild_id"):
            guild_id = snowflakes.Snowflake(raw_guild_id)

        options: typing.Optional[typing.List[command_interactions.CommandInteractionOption]] = None
        if raw_options := data_payload.get("options"):
            options = [self._deserialize_interaction_command_option(option) for option in raw_options]

        member: typing.Optional[base_interactions.InteractionMember]
        if member_payload := payload.get("member"):
            assert guild_id is not None
            member = self._deserialize_interaction_member(member_payload, guild_id=guild_id)
            # See https://github.com/discord/discord-api-docs/pull/2568
            user = member.user

        else:
            member = None
            user = self.deserialize_user(payload["user"])

        resolved: typing.Optional[command_interactions.ResolvedOptionData] = None
        if resolved_payload := data_payload.get("resolved"):
            channels: typing.Dict[snowflakes.Snowflake, command_interactions.InteractionChannel] = {}
            if raw_channels := resolved_payload.get("channels"):
                for channel_payload in raw_channels.values():
                    channel_id = snowflakes.Snowflake(channel_payload["id"])
                    channels[channel_id] = command_interactions.InteractionChannel(
                        app=self._app,
                        id=channel_id,
                        type=channel_models.ChannelType(channel_payload["type"]),
                        name=channel_payload["name"],
                        permissions=permission_models.Permissions(int(channel_payload["permissions"])),
                    )

            if raw_users := resolved_payload.get("users"):
                users = {u.id: u for u in map(self.deserialize_user, raw_users.values())}

            else:
                users = {}

            members: typing.Dict[snowflakes.Snowflake, base_interactions.InteractionMember] = {}
            if raw_members := resolved_payload.get("members"):
                for user_id, member_payload in raw_members.items():
                    assert guild_id is not None
                    user_id = snowflakes.Snowflake(user_id)
                    members[user_id] = self._deserialize_interaction_member(
                        member_payload, user=users[user_id], guild_id=guild_id
                    )

            if raw_roles := resolved_payload.get("roles"):
                assert guild_id is not None
                roles_iter = (self.deserialize_role(role, guild_id=guild_id) for role in raw_roles.values())
                roles = {r.id: r for r in roles_iter}

            else:
                roles = {}

            resolved = command_interactions.ResolvedOptionData(
                channels=channels,
                members=members,
                users=users,
                roles=roles,
            )

        return command_interactions.CommandInteraction(
            app=self._app,
            application_id=snowflakes.Snowflake(payload["application_id"]),
            id=snowflakes.Snowflake(payload["id"]),
            type=base_interactions.InteractionType(payload["type"]),
            guild_id=guild_id,
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            member=member,
            user=user,
            token=payload["token"],
            version=payload["version"],
            command_id=snowflakes.Snowflake(data_payload["id"]),
            command_name=data_payload["name"],
            options=options,
            resolved=resolved,
        )

    def deserialize_interaction(self, payload: data_binding.JSONObject) -> base_interactions.PartialInteraction:
        interaction_type = base_interactions.InteractionType(payload["type"])

        if deserialize := self._interaction_type_mapping.get(interaction_type):
            return deserialize(payload)

        _LOGGER.debug("Unknown interaction type %s", interaction_type)
        raise errors.UnrecognisedEntityError(f"Unrecognised interaction type {interaction_type}")

    def serialize_command_option(self, option: commands.CommandOption) -> data_binding.JSONObject:
        payload: data_binding.JSONObject = {
            "type": option.type,
            "name": option.name,
            "description": option.description,
            "required": option.is_required,
        }

        if option.channel_types is not None:
            payload["channel_types"] = option.channel_types

        if option.choices is not None:
            payload["choices"] = [{"name": choice.name, "value": choice.value} for choice in option.choices]

        if option.options is not None:
            payload["options"] = [self.serialize_command_option(suboption) for suboption in option.options]

        if option.min_value is not None:
            payload["min_value"] = option.min_value
        if option.max_value is not None:
            payload["max_value"] = option.max_value

        return payload

    def deserialize_component_interaction(
        self, payload: data_binding.JSONObject
    ) -> component_interactions.ComponentInteraction:
        data_payload = payload["data"]

        guild_id = None
        if raw_guild_id := payload.get("guild_id"):
            guild_id = snowflakes.Snowflake(raw_guild_id)

        member: typing.Optional[base_interactions.InteractionMember]
        if member_payload := payload.get("member"):
            assert guild_id is not None
            member = self._deserialize_interaction_member(member_payload, guild_id=guild_id)
            # See https://github.com/discord/discord-api-docs/pull/2568
            user = member.user

        else:
            member = None
            user = self.deserialize_user(payload["user"])

        return component_interactions.ComponentInteraction(
            app=self._app,
            application_id=snowflakes.Snowflake(payload["application_id"]),
            id=snowflakes.Snowflake(payload["id"]),
            type=base_interactions.InteractionType(payload["type"]),
            guild_id=guild_id,
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            member=member,
            user=user,
            token=payload["token"],
            values=data_payload.get("values") or (),
            version=payload["version"],
            custom_id=data_payload["custom_id"],
            component_type=message_models.ComponentType(data_payload["component_type"]),
            message=self.deserialize_message(payload["message"]),
        )

    ##################
    # STICKER MODELS #
    ##################

    def deserialize_sticker_pack(self, payload: data_binding.JSONObject) -> sticker_models.StickerPack:
        pack_stickers: typing.List[sticker_models.StandardSticker] = []
        for sticker_payload in payload["stickers"]:
            pack_stickers.append(self.deserialize_standard_sticker(sticker_payload))

        return sticker_models.StickerPack(
            id=snowflakes.Snowflake(payload["id"]),
            name=payload["name"],
            description=payload["description"],
            cover_sticker_id=snowflakes.Snowflake(payload["cover_sticker_id"]),
            stickers=pack_stickers,
            sku_id=snowflakes.Snowflake(payload["sku_id"]),
            banner_hash=payload["banner_asset_id"],
        )

    def deserialize_partial_sticker(self, payload: data_binding.JSONObject) -> sticker_models.PartialSticker:
        return sticker_models.PartialSticker(
            id=snowflakes.Snowflake(payload["id"]),
            name=payload["name"],
            format_type=sticker_models.StickerFormatType(payload["format_type"]),
        )

    def deserialize_standard_sticker(self, payload: data_binding.JSONObject) -> sticker_models.StandardSticker:
        return sticker_models.StandardSticker(
            id=snowflakes.Snowflake(payload["id"]),
            name=payload["name"],
            description=payload["description"],
            format_type=sticker_models.StickerFormatType(payload["format_type"]),
            pack_id=snowflakes.Snowflake(payload["pack_id"]),
            sort_value=payload["sort_value"],
            tags=[tag.strip() for tag in payload["tags"].split(",")],
        )

    def deserialize_guild_sticker(self, payload: data_binding.JSONObject) -> sticker_models.GuildSticker:
        return sticker_models.GuildSticker(
            id=snowflakes.Snowflake(payload["id"]),
            name=payload["name"],
            description=payload["description"],
            format_type=sticker_models.StickerFormatType(payload["format_type"]),
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
            is_available=payload["available"],
            tag=payload["tags"],
            user=self.deserialize_user(payload["user"]) if "user" in payload else None,
        )

    ##################
    # MESSAGE MODELS #
    ##################

    def deserialize_action_row(self, payload: data_binding.JSONObject) -> message_models.ActionRowComponent:
        components: typing.List[message_models.PartialComponent] = []

        for component_payload in payload["components"]:
            try:
                components.append(self.deserialize_component(component_payload))

            except errors.UnrecognisedEntityError:
                pass

        return message_models.ActionRowComponent(
            type=message_models.ComponentType(payload["type"]), components=components
        )

    def deserialize_button(self, payload: data_binding.JSONObject) -> message_models.ButtonComponent:
        emoji_payload = payload.get("emoji")
        return message_models.ButtonComponent(
            type=message_models.ComponentType(payload["type"]),
            style=message_models.ButtonStyle(payload["style"]),
            label=payload.get("label"),
            emoji=self.deserialize_emoji(emoji_payload) if emoji_payload else None,
            custom_id=payload.get("custom_id"),
            url=payload.get("url"),
            is_disabled=payload.get("disabled", False),
        )

    def deserialize_select_menu(self, payload: data_binding.JSONObject) -> message_models.SelectMenuComponent:
        options: typing.List[message_models.SelectMenuOption] = []
        for option_payload in payload["options"]:
            emoji = None
            if emoji_payload := option_payload.get("emoji"):
                emoji = self.deserialize_emoji(emoji_payload)

            options.append(
                message_models.SelectMenuOption(
                    label=option_payload["label"],
                    value=option_payload["value"],
                    description=option_payload.get("description"),
                    emoji=emoji,
                    is_default=option_payload.get("default", False),
                )
            )

        return message_models.SelectMenuComponent(
            type=message_models.ComponentType(payload["type"]),
            custom_id=payload["custom_id"],
            options=options,
            placeholder=payload.get("placeholder"),
            min_values=payload.get("min_values", 1),
            max_values=payload.get("max_values", 1),
            is_disabled=payload.get("disabled", False),
        )

    def deserialize_component(self, payload: data_binding.JSONObject) -> message_models.PartialComponent:
        component_type = message_models.ComponentType(payload["type"])

        if deserialize := self._component_type_mapping.get(component_type):
            return deserialize(payload)

        _LOGGER.debug("Unknown component type %s", component_type)
        raise errors.UnrecognisedEntityError(f"Unrecognised component type {component_type}")

    def _deserialize_message_activity(self, payload: data_binding.JSONObject) -> message_models.MessageActivity:
        return message_models.MessageActivity(
            type=message_models.MessageActivityType(payload["type"]), party_id=payload.get("party_id")
        )

    def _deserialize_message_application(self, payload: data_binding.JSONObject) -> message_models.MessageApplication:
        primary_sku_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_primary_sku_id := payload.get("primary_sku_id")) is not None:
            primary_sku_id = snowflakes.Snowflake(raw_primary_sku_id)

        return message_models.MessageApplication(
            id=snowflakes.Snowflake(payload["id"]),
            name=payload["name"],
            description=payload["description"] or None,
            icon_hash=payload["icon"],
            summary=payload["summary"] or None,
            cover_image_hash=payload.get("cover_image"),
            primary_sku_id=primary_sku_id,
        )

    def _deserialize_message_attachment(self, payload: data_binding.JSONObject) -> message_models.Attachment:
        return message_models.Attachment(
            id=snowflakes.Snowflake(payload["id"]),
            filename=payload["filename"],
            media_type=payload.get("content_type"),
            size=int(payload["size"]),
            url=payload["url"],
            proxy_url=payload["proxy_url"],
            height=payload.get("height"),
            width=payload.get("width"),
            is_ephemeral=payload.get("ephemeral", False),
        )

    def _deserialize_message_reaction(self, payload: data_binding.JSONObject) -> message_models.Reaction:
        return message_models.Reaction(
            count=int(payload["count"]), emoji=self.deserialize_emoji(payload["emoji"]), is_me=payload["me"]
        )

    def _deserialize_message_reference(self, payload: data_binding.JSONObject) -> message_models.MessageReference:
        message_reference_message_id: typing.Optional[snowflakes.Snowflake] = None
        if "message_id" in payload:
            message_reference_message_id = snowflakes.Snowflake(payload["message_id"])

        message_reference_guild_id: typing.Optional[snowflakes.Snowflake] = None
        if "guild_id" in payload:
            message_reference_guild_id = snowflakes.Snowflake(payload["guild_id"])

        return message_models.MessageReference(
            app=self._app,
            id=message_reference_message_id,
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            guild_id=message_reference_guild_id,
        )

    def _deserialize_message_interaction(self, payload: data_binding.JSONObject) -> message_models.MessageInteraction:
        return message_models.MessageInteraction(
            id=snowflakes.Snowflake(payload["id"]),
            type=base_interactions.InteractionType(payload["type"]),
            name=payload["name"],
            user=self.deserialize_user(payload["user"]),
        )

    def deserialize_partial_message(  # noqa CFQ001 - Function too long
        self, payload: data_binding.JSONObject
    ) -> message_models.PartialMessage:
        author: undefined.UndefinedOr[user_models.User] = undefined.UNDEFINED
        if author_pl := payload.get("author"):
            author = self.deserialize_user(author_pl)

        guild_id: typing.Optional[snowflakes.Snowflake] = None
        member: undefined.UndefinedNoneOr[guild_models.Member] = None
        if "guild_id" in payload:
            guild_id = snowflakes.Snowflake(payload["guild_id"])

            # Webhook messages will never have a member attached to them
            if member_pl := payload.get("member"):
                assert author is not undefined.UNDEFINED, "received message with a member object without a user object"
                member = self.deserialize_member(member_pl, user=author, guild_id=guild_id)
            elif author is not undefined.UNDEFINED:
                member = undefined.UNDEFINED

        timestamp: undefined.UndefinedOr[datetime.datetime] = undefined.UNDEFINED
        if "timestamp" in payload:
            timestamp = time.iso8601_datetime_string_to_datetime(payload["timestamp"])

        edited_timestamp: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED
        if "edited_timestamp" in payload:
            if (raw_edited_timestamp := payload["edited_timestamp"]) is not None:
                edited_timestamp = time.iso8601_datetime_string_to_datetime(raw_edited_timestamp)
            else:
                edited_timestamp = None

        attachments: undefined.UndefinedOr[typing.List[message_models.Attachment]] = undefined.UNDEFINED
        if "attachments" in payload:
            attachments = [self._deserialize_message_attachment(attachment) for attachment in payload["attachments"]]

        embeds: undefined.UndefinedOr[typing.List[embed_models.Embed]] = undefined.UNDEFINED
        if "embeds" in payload:
            embeds = [self.deserialize_embed(embed) for embed in payload["embeds"]]

        reactions: undefined.UndefinedOr[typing.List[message_models.Reaction]] = undefined.UNDEFINED
        if "reactions" in payload:
            reactions = [self._deserialize_message_reaction(reaction) for reaction in payload["reactions"]]

        activity: undefined.UndefinedOr[message_models.MessageActivity] = undefined.UNDEFINED
        if "activity" in payload:
            activity = self._deserialize_message_activity(payload["activity"])

        application: undefined.UndefinedOr[message_models.MessageApplication] = undefined.UNDEFINED
        if "application" in payload:
            application = self._deserialize_message_application(payload["application"])

        message_reference: undefined.UndefinedOr[message_models.MessageReference] = undefined.UNDEFINED
        if "message_reference" in payload:
            message_reference = self._deserialize_message_reference(payload["message_reference"])

        referenced_message: undefined.UndefinedNoneOr[message_models.Message] = undefined.UNDEFINED
        if "referenced_message" in payload:
            if (referenced_message_payload := payload["referenced_message"]) is not None:
                referenced_message = self.deserialize_message(referenced_message_payload)
            else:
                referenced_message = None

        stickers: undefined.UndefinedOr[typing.Sequence[sticker_models.PartialSticker]] = undefined.UNDEFINED
        if "sticker_items" in payload:
            stickers = [self.deserialize_partial_sticker(sticker) for sticker in payload["sticker_items"]]
        # This is only here for backwards compatibility as old messages still return this field
        elif "stickers" in payload:
            stickers = [self.deserialize_partial_sticker(sticker) for sticker in payload["stickers"]]

        content = payload.get("content", undefined.UNDEFINED)
        if content is not undefined.UNDEFINED:
            content = content or None  # Default to None if content is an empty string

        application_id: undefined.UndefinedNoneOr[snowflakes.Snowflake] = undefined.UNDEFINED
        if raw_application_id := payload.get("application_id"):
            application_id = snowflakes.Snowflake(raw_application_id)

        interaction: undefined.UndefinedNoneOr[message_models.MessageInteraction] = undefined.UNDEFINED
        if interaction_payload := payload.get("interaction"):
            interaction = self._deserialize_message_interaction(interaction_payload)

        components: undefined.UndefinedOr[typing.List[message_models.PartialComponent]] = undefined.UNDEFINED
        if component_payloads := payload.get("components"):
            components = []
            for component_payload in component_payloads:
                try:
                    components.append(self.deserialize_component(component_payload))

                except errors.UnrecognisedEntityError:
                    pass

        message = message_models.PartialMessage(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            guild_id=guild_id,
            author=author,
            member=member,
            content=content,
            timestamp=timestamp,
            edited_timestamp=edited_timestamp,
            is_tts=payload.get("tts", undefined.UNDEFINED),
            attachments=attachments,
            embeds=embeds,
            reactions=reactions,
            is_pinned=payload.get("pinned", undefined.UNDEFINED),
            webhook_id=snowflakes.Snowflake(payload["webhook_id"]) if "webhook_id" in payload else undefined.UNDEFINED,
            type=message_models.MessageType(payload["type"]) if "type" in payload else undefined.UNDEFINED,
            activity=activity,
            application=application,
            message_reference=message_reference,
            referenced_message=referenced_message,
            flags=message_models.MessageFlag(payload["flags"]) if "flags" in payload else undefined.UNDEFINED,
            stickers=stickers,
            nonce=payload.get("nonce", undefined.UNDEFINED),
            application_id=application_id,
            interaction=interaction,
            components=components,
            # We initialize these next.
            mentions=NotImplemented,
        )

        channels: undefined.UndefinedOr[typing.Dict[snowflakes.Snowflake, channel_models.PartialChannel]]
        channels = undefined.UNDEFINED
        if raw_channels := payload.get("mention_channels"):
            channels = {c.id: c for c in map(self.deserialize_partial_channel, raw_channels)}

        users: undefined.UndefinedOr[typing.Dict[snowflakes.Snowflake, user_models.User]]
        users = undefined.UNDEFINED
        if raw_users := payload.get("mentions"):
            users = {u.id: u for u in map(self.deserialize_user, raw_users)}

        role_ids: undefined.UndefinedOr[typing.List[snowflakes.Snowflake]] = undefined.UNDEFINED
        if raw_role_ids := payload.get("mention_roles"):
            role_ids = [snowflakes.Snowflake(i) for i in raw_role_ids]

        everyone = payload.get("mention_everyone", undefined.UNDEFINED)

        message.mentions = message_models.Mentions(
            message=message,
            users=users,
            role_ids=role_ids,
            channels=channels,
            everyone=everyone,
        )

        return message

    def deserialize_message(  # noqa CFQ001 - Function too long
        self, payload: data_binding.JSONObject
    ) -> message_models.Message:
        author = self.deserialize_user(payload["author"])

        guild_id: typing.Optional[snowflakes.Snowflake] = None
        member: typing.Optional[guild_models.Member] = None
        if "guild_id" in payload:
            guild_id = snowflakes.Snowflake(payload["guild_id"])

            if member_pl := payload.get("member"):
                member = self.deserialize_member(member_pl, user=author, guild_id=guild_id)

        edited_timestamp: typing.Optional[datetime.datetime] = None
        if (raw_edited_timestamp := payload["edited_timestamp"]) is not None:
            edited_timestamp = time.iso8601_datetime_string_to_datetime(raw_edited_timestamp)

        attachments = [self._deserialize_message_attachment(attachment) for attachment in payload["attachments"]]

        embeds = [self.deserialize_embed(embed) for embed in payload["embeds"]]

        if "reactions" in payload:
            reactions = [self._deserialize_message_reaction(reaction) for reaction in payload["reactions"]]
        else:
            reactions = []

        activity: typing.Optional[message_models.MessageActivity] = None
        if "activity" in payload:
            activity = self._deserialize_message_activity(payload["activity"])

        message_reference: typing.Optional[message_models.MessageReference] = None
        if "message_reference" in payload:
            message_reference = self._deserialize_message_reference(payload["message_reference"])

        referenced_message: typing.Optional[message_models.Message] = None
        if referenced_message_payload := payload.get("referenced_message"):
            referenced_message = self.deserialize_message(referenced_message_payload)

        application: typing.Optional[message_models.MessageApplication] = None
        if "application" in payload:
            application = self._deserialize_message_application(payload["application"])

        if "sticker_items" in payload:
            stickers = [self.deserialize_partial_sticker(sticker) for sticker in payload["sticker_items"]]
        elif "stickers" in payload:
            stickers = [self.deserialize_partial_sticker(sticker) for sticker in payload["stickers"]]
        else:
            stickers = []

        interaction: typing.Optional[message_models.MessageInteraction] = None
        if interaction_payload := payload.get("interaction"):
            interaction = self._deserialize_message_interaction(interaction_payload)

        components: typing.List[message_models.PartialComponent] = []
        if component_payloads := payload.get("components"):
            for component_payload in component_payloads:
                try:
                    components.append(self.deserialize_component(component_payload))

                except errors.UnrecognisedEntityError:
                    pass

        message = message_models.Message(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            guild_id=guild_id,
            author=author,
            member=member,
            content=payload["content"] or None,
            timestamp=time.iso8601_datetime_string_to_datetime(payload["timestamp"]),
            edited_timestamp=edited_timestamp,
            is_tts=payload["tts"],
            attachments=attachments,
            embeds=embeds,
            reactions=reactions,
            is_pinned=payload["pinned"],
            webhook_id=snowflakes.Snowflake(payload["webhook_id"]) if "webhook_id" in payload else None,
            type=message_models.MessageType(payload["type"]),
            activity=activity,
            application=application,
            message_reference=message_reference,
            referenced_message=referenced_message,
            flags=message_models.MessageFlag(payload["flags"]),
            stickers=stickers,
            nonce=payload.get("nonce"),
            application_id=snowflakes.Snowflake(payload["application_id"]) if "application_id" in payload else None,
            interaction=interaction,
            components=components,
            # We initialize these next.
            mentions=NotImplemented,
        )

        if raw_channels := payload.get("mention_channels"):
            channels = {c.id: c for c in map(self.deserialize_partial_channel, raw_channels)}

        else:
            channels = {}

        if raw_users := payload.get("mentions"):
            users = {u.id: u for u in map(self.deserialize_user, raw_users)}

        else:
            users = {}

        if raw_role_ids := payload.get("mention_roles"):
            role_ids = [snowflakes.Snowflake(i) for i in raw_role_ids]

        else:
            role_ids = []

        everyone = payload.get("mention_everyone", False)

        message.mentions = message_models.Mentions(
            message=message,
            users=users,
            role_ids=role_ids,
            channels=channels,
            everyone=everyone,
        )

        return message

    ###################
    # PRESENCE MODELS #
    ###################

    def deserialize_member_presence(  # noqa: CFQ001 - Max function length
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> presence_models.MemberPresence:
        activities = []
        for activity_payload in payload["activities"]:
            timestamps: typing.Optional[presence_models.ActivityTimestamps] = None
            if "timestamps" in activity_payload:
                timestamps_payload = activity_payload["timestamps"]
                start = (
                    time.unix_epoch_to_datetime(timestamps_payload["start"]) if "start" in timestamps_payload else None
                )
                end = time.unix_epoch_to_datetime(timestamps_payload["end"]) if "end" in timestamps_payload else None
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
                # RichActivity's generated init already declares a converter for the "type" field
                type=activity_payload["type"],
                url=activity_payload.get("url"),
                created_at=time.unix_epoch_to_datetime(activity_payload["created_at"]),
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
                buttons=activity_payload.get("buttons") or [],
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

        return presence_models.MemberPresence(
            app=self._app,
            user_id=snowflakes.Snowflake(payload["user"]["id"]),
            guild_id=guild_id if guild_id is not undefined.UNDEFINED else snowflakes.Snowflake(payload["guild_id"]),
            visible_status=presence_models.Status(payload["status"]),
            activities=activities,
            client_status=client_status,
        )

    ###################
    # TEMPLATE MODELS #
    ###################

    def deserialize_template(self, payload: data_binding.JSONObject) -> template_models.Template:
        source_guild_payload = payload["serialized_source_guild"]
        # For some reason the guild ID isn't on the actual guild object in this special case.
        guild_id = snowflakes.Snowflake(payload["source_guild_id"])
        default_message_notifications = guild_models.GuildMessageNotificationsLevel(
            source_guild_payload["default_message_notifications"]
        )
        explicit_content_filter = guild_models.GuildExplicitContentFilterLevel(
            source_guild_payload["explicit_content_filter"]
        )

        roles: typing.Dict[snowflakes.Snowflake, template_models.TemplateRole] = {}
        for role_payload in source_guild_payload["roles"]:
            role = template_models.TemplateRole(
                app=self._app,
                id=snowflakes.Snowflake(role_payload["id"]),
                name=role_payload["name"],
                permissions=permission_models.Permissions(int(role_payload["permissions"])),
                color=color_models.Color(role_payload["color"]),
                is_hoisted=role_payload["hoist"],
                is_mentionable=role_payload["mentionable"],
            )
            roles[role.id] = role

        channels = {}
        for channel_payload in source_guild_payload["channels"]:
            channel = self.deserialize_channel(channel_payload, guild_id=guild_id)
            assert isinstance(channel, channel_models.GuildChannel)
            channels[channel.id] = channel

        afk_channel_id = source_guild_payload["afk_channel_id"]
        system_channel_id = source_guild_payload["system_channel_id"]

        source_guild = template_models.TemplateGuild(
            app=self._app,
            id=guild_id,
            # For some reason in this case they use the key "icon_hash" rather than "icon".
            # Cause Discord:TM:
            icon_hash=source_guild_payload["icon_hash"],
            name=source_guild_payload["name"],
            description=source_guild_payload["description"],
            verification_level=guild_models.GuildVerificationLevel(source_guild_payload["verification_level"]),
            default_message_notifications=default_message_notifications,
            explicit_content_filter=explicit_content_filter,
            preferred_locale=source_guild_payload["preferred_locale"],
            afk_timeout=datetime.timedelta(seconds=source_guild_payload["afk_timeout"]),
            roles=roles,
            channels=channels,
            afk_channel_id=snowflakes.Snowflake(afk_channel_id) if afk_channel_id is not None else None,
            system_channel_id=snowflakes.Snowflake(system_channel_id) if system_channel_id is not None else None,
            system_channel_flags=guild_models.GuildSystemChannelFlag(source_guild_payload["system_channel_flags"]),
        )

        return template_models.Template(
            code=payload["code"],
            name=payload["name"],
            description=payload["description"],
            usage_count=payload["usage_count"],
            creator=self.deserialize_user(payload["creator"]),
            created_at=time.iso8601_datetime_string_to_datetime(payload["created_at"]),
            updated_at=time.iso8601_datetime_string_to_datetime(payload["updated_at"]),
            source_guild=source_guild,
            is_unsynced=bool(payload["is_dirty"]),
        )

    ###############
    # USER MODELS #
    ###############

    @staticmethod
    def _set_user_attributes(payload: data_binding.JSONObject) -> _UserFields:
        accent_color = payload.get("accent_color")
        return _UserFields(
            id=snowflakes.Snowflake(payload["id"]),
            discriminator=payload["discriminator"],
            username=payload["username"],
            avatar_hash=payload["avatar"],
            banner_hash=payload.get("banner", None),
            accent_color=color_models.Color(accent_color) if accent_color is not None else None,
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
            banner_hash=user_fields.banner_hash,
            accent_color=user_fields.accent_color,
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
            banner_hash=user_fields.banner_hash,
            accent_color=user_fields.accent_color,
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

        requested_to_speak_at: typing.Optional[datetime.datetime] = None
        if raw_requested_to_speak_at := payload.get("request_to_speak_timestamp"):
            requested_to_speak_at = time.iso8601_datetime_string_to_datetime(raw_requested_to_speak_at)

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
            requested_to_speak_at=requested_to_speak_at,
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

    def deserialize_incoming_webhook(self, payload: data_binding.JSONObject) -> webhook_models.IncomingWebhook:
        application_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_application_id := payload.get("application_id")) is not None:
            application_id = snowflakes.Snowflake(raw_application_id)

        return webhook_models.IncomingWebhook(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            type=webhook_models.WebhookType(payload["type"]),
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            author=self.deserialize_user(payload["user"]) if "user" in payload else None,
            name=payload["name"],
            avatar_hash=payload["avatar"],
            token=payload.get("token"),
            application_id=application_id,
        )

    def deserialize_channel_follower_webhook(
        self, payload: data_binding.JSONObject
    ) -> webhook_models.ChannelFollowerWebhook:
        application_id: typing.Optional[snowflakes.Snowflake] = None
        if (raw_application_id := payload.get("application_id")) is not None:
            application_id = snowflakes.Snowflake(raw_application_id)

        raw_source_channel = payload["source_channel"]
        # In this case the channel type isn't provided as we can safely
        # assume it's a news channel.
        raw_source_channel["type"] = channel_models.ChannelType.GUILD_NEWS
        source_channel = self.deserialize_partial_channel(raw_source_channel)
        source_guild_payload = payload["source_guild"]
        source_guild = guild_models.PartialGuild(
            app=self._app,
            id=snowflakes.Snowflake(source_guild_payload["id"]),
            name=source_guild_payload["name"],
            icon_hash=source_guild_payload.get("icon"),
        )

        return webhook_models.ChannelFollowerWebhook(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            type=webhook_models.WebhookType(payload["type"]),
            guild_id=snowflakes.Snowflake(payload["guild_id"]),
            channel_id=snowflakes.Snowflake(payload["channel_id"]),
            author=self.deserialize_user(payload["user"]) if "user" in payload else None,
            name=payload["name"],
            avatar_hash=payload["avatar"],
            application_id=application_id,
            source_channel=source_channel,
            source_guild=source_guild,
        )

    def deserialize_application_webhook(self, payload: data_binding.JSONObject) -> webhook_models.ApplicationWebhook:
        return webhook_models.ApplicationWebhook(
            app=self._app,
            id=snowflakes.Snowflake(payload["id"]),
            type=webhook_models.WebhookType(payload["type"]),
            name=payload["name"],
            avatar_hash=payload["avatar"],
            application_id=snowflakes.Snowflake(payload["application_id"]),
        )

    def deserialize_webhook(self, payload: data_binding.JSONObject) -> webhook_models.PartialWebhook:
        webhook_type = webhook_models.WebhookType(payload["type"])

        if converter := self._webhook_type_mapping.get(webhook_type):
            return converter(payload)

        _LOGGER.debug(f"Unrecognised webhook type {webhook_type}")
        raise errors.UnrecognisedEntityError(f"Unrecognised webhook type {webhook_type}")
