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
"""Basic implementation of an entity factory for general bots and REST apps."""

from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = ["EntityFactoryComponentImpl"]

import datetime
import typing

from hikari.api import entity_factory
from hikari.api import rest
from hikari.events import channel as channel_events
from hikari.events import guild as guild_events
from hikari.events import message as message_events
from hikari.events import other as other_events
from hikari.events import voice as voice_events
from hikari.models import applications as application_models
from hikari.models import audit_logs as audit_log_models
from hikari.models import channels as channel_models
from hikari.models import colors as color_models
from hikari.models import embeds as embed_models
from hikari.models import emojis as emoji_models
from hikari.models import gateway as gateway_models
from hikari.models import guilds as guild_models
from hikari.models import invites as invite_models
from hikari.models import messages as message_models
from hikari.models import permissions as permission_models
from hikari.models import presences as presence_models
from hikari.models import users as user_models
from hikari.models import voices as voice_models
from hikari.models import webhooks as webhook_models
from hikari.utilities import files
from hikari.net import gateway
from hikari.utilities import date
from hikari.utilities import snowflake
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.utilities import data_binding


def _deserialize_seconds_timedelta(seconds: typing.Union[str, int]) -> datetime.timedelta:
    return datetime.timedelta(seconds=int(seconds))


def _deserialize_day_timedelta(days: typing.Union[str, int]) -> datetime.timedelta:
    return datetime.timedelta(days=int(days))


def _deserialize_max_uses(age: int) -> typing.Optional[int]:
    return age if age > 0 else None


def _deserialize_max_age(seconds: int) -> typing.Optional[datetime.timedelta]:
    return datetime.timedelta(seconds=seconds) if seconds > 0 else None


class EntityFactoryComponentImpl(entity_factory.IEntityFactoryComponent):
    """Standard implementation for a serializer/deserializer.

    This will convert objects to/from JSON compatible representations.
    """

    def __init__(self, app: rest.IRESTClient) -> None:
        self._app = app
        self._audit_log_entry_converters: typing.Mapping[str, typing.Callable[[typing.Any], typing.Any]] = {
            audit_log_models.AuditLogChangeKey.OWNER_ID: snowflake.Snowflake,
            audit_log_models.AuditLogChangeKey.AFK_CHANNEL_ID: snowflake.Snowflake,
            audit_log_models.AuditLogChangeKey.AFK_TIMEOUT: _deserialize_seconds_timedelta,
            audit_log_models.AuditLogChangeKey.MFA_LEVEL: guild_models.GuildMFALevel,
            audit_log_models.AuditLogChangeKey.VERIFICATION_LEVEL: guild_models.GuildVerificationLevel,
            audit_log_models.AuditLogChangeKey.EXPLICIT_CONTENT_FILTER: guild_models.GuildExplicitContentFilterLevel,
            audit_log_models.AuditLogChangeKey.DEFAULT_MESSAGE_NOTIFICATIONS: guild_models.GuildMessageNotificationsLevel,  # noqa: E501 - Line too long
            audit_log_models.AuditLogChangeKey.PRUNE_DELETE_DAYS: _deserialize_day_timedelta,
            audit_log_models.AuditLogChangeKey.WIDGET_CHANNEL_ID: snowflake.Snowflake,
            audit_log_models.AuditLogChangeKey.POSITION: int,
            audit_log_models.AuditLogChangeKey.BITRATE: int,
            audit_log_models.AuditLogChangeKey.APPLICATION_ID: snowflake.Snowflake,
            audit_log_models.AuditLogChangeKey.PERMISSIONS: permission_models.Permission,
            audit_log_models.AuditLogChangeKey.COLOR: color_models.Color,
            audit_log_models.AuditLogChangeKey.ALLOW: permission_models.Permission,
            audit_log_models.AuditLogChangeKey.DENY: permission_models.Permission,
            audit_log_models.AuditLogChangeKey.CHANNEL_ID: snowflake.Snowflake,
            audit_log_models.AuditLogChangeKey.INVITER_ID: snowflake.Snowflake,
            audit_log_models.AuditLogChangeKey.MAX_USES: _deserialize_max_uses,
            audit_log_models.AuditLogChangeKey.USES: int,
            audit_log_models.AuditLogChangeKey.MAX_AGE: _deserialize_max_age,
            audit_log_models.AuditLogChangeKey.ID: snowflake.Snowflake,
            audit_log_models.AuditLogChangeKey.TYPE: str,
            audit_log_models.AuditLogChangeKey.ENABLE_EMOTICONS: bool,
            audit_log_models.AuditLogChangeKey.EXPIRE_BEHAVIOR: guild_models.IntegrationExpireBehaviour,
            audit_log_models.AuditLogChangeKey.EXPIRE_GRACE_PERIOD: _deserialize_day_timedelta,
            audit_log_models.AuditLogChangeKey.RATE_LIMIT_PER_USER: _deserialize_seconds_timedelta,
            audit_log_models.AuditLogChangeKey.SYSTEM_CHANNEL_ID: snowflake.Snowflake,
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
        self._channel_type_mapping = {
            channel_models.ChannelType.DM: self.deserialize_dm_channel,
            channel_models.ChannelType.GROUP_DM: self.deserialize_group_dm_channel,
            channel_models.ChannelType.GUILD_CATEGORY: self.deserialize_guild_category,
            channel_models.ChannelType.GUILD_TEXT: self.deserialize_guild_text_channel,
            channel_models.ChannelType.GUILD_NEWS: self.deserialize_guild_news_channel,
            channel_models.ChannelType.GUILD_STORE: self.deserialize_guild_store_channel,
            channel_models.ChannelType.GUILD_VOICE: self.deserialize_guild_voice_channel,
        }

    @property
    @typing.final
    def app(self) -> rest.IRESTClient:
        return self._app

    ######################
    # APPLICATION MODELS #
    ######################

    def deserialize_own_connection(self, payload: data_binding.JSONObject) -> application_models.OwnConnection:
        own_connection = application_models.OwnConnection()
        own_connection.id = payload["id"]  # this is not a snowflake!
        own_connection.name = payload["name"]
        own_connection.type = payload["type"]
        own_connection.is_revoked = payload["revoked"]
        own_connection.integrations = [
            self.deserialize_partial_integration(integration) for integration in payload.get("integrations", ())
        ]
        own_connection.is_verified = payload["verified"]
        own_connection.is_friend_sync_enabled = payload["friend_sync"]
        own_connection.is_activity_visible = payload["show_activity"]
        # noinspection PyArgumentList
        own_connection.visibility = application_models.ConnectionVisibility(payload["visibility"])
        return own_connection

    def deserialize_own_guild(self, payload: data_binding.JSONObject) -> application_models.OwnGuild:
        own_guild = application_models.OwnGuild()
        own_guild.app = self._app
        self._set_partial_guild_attributes(payload, own_guild)
        own_guild.is_owner = bool(payload["owner"])
        # noinspection PyArgumentList
        own_guild.my_permissions = permission_models.Permission(payload["permissions"])
        return own_guild

    def deserialize_application(self, payload: data_binding.JSONObject) -> application_models.Application:
        application = application_models.Application()
        application.app = self._app
        application.id = snowflake.Snowflake(payload["id"])
        application.name = payload["name"]
        application.description = payload["description"]
        application.is_bot_public = payload.get("bot_public")
        application.is_bot_code_grant_required = payload.get("bot_require_code_grant")
        application.owner = self.deserialize_user(payload["owner"]) if "owner" in payload else None
        application.rpc_origins = set(payload["rpc_origins"]) if "rpc_origins" in payload else None
        application.summary = payload["summary"]
        application.verify_key = bytes(payload["verify_key"], "utf-8") if "verify_key" in payload else None
        application.icon_hash = payload.get("icon")

        if (team_payload := payload.get("team")) is not None:
            team = application_models.Team()
            team.app = self._app
            team.id = snowflake.Snowflake(team_payload["id"])
            team.icon_hash = team_payload["icon"]

            members = {}
            for member_payload in team_payload["members"]:
                team_member = application_models.TeamMember()
                team_member.app = self.app
                # noinspection PyArgumentList
                team_member.membership_state = application_models.TeamMembershipState(
                    member_payload["membership_state"]
                )
                team_member.permissions = set(member_payload["permissions"])
                team_member.team_id = snowflake.Snowflake(member_payload["team_id"])
                team_member.user = self.deserialize_user(member_payload["user"])
                members[team_member.user.id] = team_member
            team.members = members

            team.owner_id = snowflake.Snowflake(team_payload["owner_user_id"])
            application.team = team
        else:
            application.team = None

        application.guild_id = snowflake.Snowflake(payload["guild_id"]) if "guild_id" in payload else None
        application.primary_sku_id = (
            snowflake.Snowflake(payload["primary_sku_id"]) if "primary_sku_id" in payload else None
        )
        application.slug = payload.get("slug")
        application.cover_image_hash = payload.get("cover_image")
        return application

    #####################
    # AUDIT LOGS MODELS #
    #####################

    def _deserialize_audit_log_change_roles(
        self, payload: data_binding.JSONArray
    ) -> typing.Mapping[snowflake.Snowflake, guild_models.PartialRole]:
        roles = {}
        for role_payload in payload:
            role = guild_models.PartialRole()
            role.app = self._app
            role.id = snowflake.Snowflake(role_payload["id"])
            role.name = role_payload["name"]
            roles[role.id] = role
        return roles

    def _deserialize_audit_log_overwrites(
        self, payload: data_binding.JSONArray
    ) -> typing.Mapping[snowflake.Snowflake, channel_models.PermissionOverwrite]:
        return {
            snowflake.Snowflake(overwrite["id"]): self.deserialize_permission_overwrite(overwrite)
            for overwrite in payload
        }

    @staticmethod
    def _deserialize_channel_overwrite_entry_info(
        payload: data_binding.JSONObject,
    ) -> audit_log_models.ChannelOverwriteEntryInfo:
        channel_overwrite_entry_info = audit_log_models.ChannelOverwriteEntryInfo()
        channel_overwrite_entry_info.id = snowflake.Snowflake(payload["id"])
        # noinspection PyArgumentList
        channel_overwrite_entry_info.type = channel_models.PermissionOverwriteType(payload["type"])
        channel_overwrite_entry_info.role_name = payload.get("role_name")
        return channel_overwrite_entry_info

    @staticmethod
    def _deserialize_message_pin_entry_info(payload: data_binding.JSONObject) -> audit_log_models.MessagePinEntryInfo:
        message_pin_entry_info = audit_log_models.MessagePinEntryInfo()
        message_pin_entry_info.channel_id = snowflake.Snowflake(payload["channel_id"])
        message_pin_entry_info.message_id = snowflake.Snowflake(payload["message_id"])
        return message_pin_entry_info

    @staticmethod
    def _deserialize_member_prune_entry_info(payload: data_binding.JSONObject) -> audit_log_models.MemberPruneEntryInfo:
        member_prune_entry_info = audit_log_models.MemberPruneEntryInfo()
        member_prune_entry_info.delete_member_days = datetime.timedelta(days=int(payload["delete_member_days"]))
        member_prune_entry_info.members_removed = int(payload["members_removed"])
        return member_prune_entry_info

    @staticmethod
    def _deserialize_message_bulk_delete_entry_info(
        payload: data_binding.JSONObject,
    ) -> audit_log_models.MessageBulkDeleteEntryInfo:
        message_bulk_delete_entry_info = audit_log_models.MessageBulkDeleteEntryInfo()
        message_bulk_delete_entry_info.count = int(payload["count"])
        return message_bulk_delete_entry_info

    @staticmethod
    def _deserialize_message_delete_entry_info(
        payload: data_binding.JSONObject,
    ) -> audit_log_models.MessageDeleteEntryInfo:
        message_delete_entry_info = audit_log_models.MessageDeleteEntryInfo()
        message_delete_entry_info.channel_id = snowflake.Snowflake(payload["channel_id"])
        message_delete_entry_info.count = int(payload["count"])
        return message_delete_entry_info

    @staticmethod
    def _deserialize_member_disconnect_entry_info(
        payload: data_binding.JSONObject,
    ) -> audit_log_models.MemberDisconnectEntryInfo:
        member_disconnect_entry_info = audit_log_models.MemberDisconnectEntryInfo()
        member_disconnect_entry_info.count = int(payload["count"])
        return member_disconnect_entry_info

    @staticmethod
    def _deserialize_member_move_entry_info(payload: data_binding.JSONObject) -> audit_log_models.MemberMoveEntryInfo:
        member_move_entry_info = audit_log_models.MemberMoveEntryInfo()
        member_move_entry_info.channel_id = snowflake.Snowflake(payload["channel_id"])
        member_move_entry_info.count = int(payload["count"])
        return member_move_entry_info

    @staticmethod
    def _deserialize_unrecognised_audit_log_entry_info(
        payload: data_binding.JSONObject,
    ) -> audit_log_models.UnrecognisedAuditLogEntryInfo:
        return audit_log_models.UnrecognisedAuditLogEntryInfo(payload)

    def deserialize_audit_log(self, payload: data_binding.JSONObject) -> audit_log_models.AuditLog:
        audit_log = audit_log_models.AuditLog()

        entries = {}
        for entry_payload in payload["audit_log_entries"]:
            entry = audit_log_models.AuditLogEntry()
            entry.app = self._app
            entry.id = snowflake.Snowflake(entry_payload["id"])

            if (target_id := entry_payload["target_id"]) is not None:
                target_id = snowflake.Snowflake(target_id)
            entry.target_id = target_id

            changes = []
            for change_payload in entry_payload.get("changes", ()):
                change = audit_log_models.AuditLogChange()

                try:
                    # noinspection PyArgumentList
                    change.key = audit_log_models.AuditLogChangeKey(change_payload["key"])
                except ValueError:
                    change.key = change_payload["key"]

                new_value = change_payload.get("new_value")
                old_value = change_payload.get("old_value")
                if value_converter := self._audit_log_entry_converters.get(change.key):
                    new_value = value_converter(new_value) if new_value is not None else None
                    old_value = value_converter(old_value) if old_value is not None else None
                change.new_value = new_value
                change.old_value = old_value

                changes.append(change)
            entry.changes = changes

            if (user_id := entry_payload["user_id"]) is not None:
                user_id = snowflake.Snowflake(user_id)
            entry.user_id = user_id

            try:
                # noinspection PyArgumentList
                entry.action_type = audit_log_models.AuditLogEventType(entry_payload["action_type"])
            except ValueError:
                entry.action_type = entry_payload["action_type"]

            if (options := entry_payload.get("options")) is not None:
                option_converter = (
                    self._audit_log_event_mapping.get(entry.action_type)
                    or self._deserialize_unrecognised_audit_log_entry_info  # noqa: W503
                )
                options = option_converter(options)
            entry.options = options

            entry.reason = entry_payload.get("reason")
            entries[entry.id] = entry
        audit_log.entries = entries

        audit_log.integrations = {
            snowflake.Snowflake(integration["id"]): self.deserialize_partial_integration(integration)
            for integration in payload["integrations"]
        }
        audit_log.users = {snowflake.Snowflake(user["id"]): self.deserialize_user(user) for user in payload["users"]}
        audit_log.webhooks = {
            snowflake.Snowflake(webhook["id"]): self.deserialize_webhook(webhook) for webhook in payload["webhooks"]
        }
        return audit_log

    ##################
    # CHANNEL MODELS #
    ##################

    def deserialize_permission_overwrite(self, payload: data_binding.JSONObject) -> channel_models.PermissionOverwrite:
        # noinspection PyArgumentList
        permission_overwrite = channel_models.PermissionOverwrite(
            id=snowflake.Snowflake(payload["id"]), type=channel_models.PermissionOverwriteType(payload["type"]),
        )
        # noinspection PyArgumentList
        permission_overwrite.allow = permission_models.Permission(payload["allow"])
        # noinspection PyArgumentList
        permission_overwrite.deny = permission_models.Permission(payload["deny"])
        return permission_overwrite

    def serialize_permission_overwrite(self, overwrite: channel_models.PermissionOverwrite) -> data_binding.JSONObject:
        return {"id": str(overwrite.id), "type": overwrite.type, "allow": overwrite.allow, "deny": overwrite.deny}

    @staticmethod
    def _set_partial_channel_attributes(
        payload: data_binding.JSONObject, channel: channel_models.PartialChannel
    ) -> None:
        channel.id = snowflake.Snowflake(payload["id"])
        channel.name = payload.get("name")
        # noinspection PyArgumentList
        channel.type = channel_models.ChannelType(payload["type"])

    def deserialize_partial_channel(self, payload: data_binding.JSONObject) -> channel_models.PartialChannel:
        partial_channel = channel_models.PartialChannel()
        partial_channel.app = self._app
        self._set_partial_channel_attributes(payload, partial_channel)
        return partial_channel

    def _set_dm_channel_attributes(
        self, payload: data_binding.JSONObject, dm_channel: channel_models.DMChannel
    ) -> None:
        self._set_partial_channel_attributes(payload, dm_channel)

        if (last_message_id := payload["last_message_id"]) is not None:
            last_message_id = snowflake.Snowflake(last_message_id)

        dm_channel.last_message_id = last_message_id
        dm_channel.recipients = {
            snowflake.Snowflake(user["id"]): self.deserialize_user(user) for user in payload["recipients"]
        }

    def deserialize_dm_channel(self, payload: data_binding.JSONObject) -> channel_models.DMChannel:
        dm_channel = channel_models.DMChannel()
        dm_channel.app = self._app
        self._set_dm_channel_attributes(payload, dm_channel)
        return dm_channel

    def deserialize_group_dm_channel(self, payload: data_binding.JSONObject) -> channel_models.GroupDMChannel:
        group_dm_channel = channel_models.GroupDMChannel()
        group_dm_channel.app = self._app
        self._set_dm_channel_attributes(payload, group_dm_channel)
        group_dm_channel.owner_id = snowflake.Snowflake(payload["owner_id"])
        group_dm_channel.icon_hash = payload["icon"]
        group_dm_channel.nicknames = {
            snowflake.Snowflake(entry["id"]): entry["nick"] for entry in payload.get("nicks", ())
        }
        group_dm_channel.application_id = (
            snowflake.Snowflake(payload["application_id"]) if "application_id" in payload else None
        )
        return group_dm_channel

    def _set_guild_channel_attributes(
        self, payload: data_binding.JSONObject, guild_channel: channel_models.GuildChannel
    ) -> None:
        self._set_partial_channel_attributes(payload, guild_channel)
        guild_channel.guild_id = snowflake.Snowflake(payload["guild_id"]) if "guild_id" in payload else None
        guild_channel.position = int(payload["position"])
        guild_channel.permission_overwrites = {
            snowflake.Snowflake(overwrite["id"]): self.deserialize_permission_overwrite(overwrite)
            for overwrite in payload["permission_overwrites"]
        }  # TODO: while snowflakes are guaranteed to be unique within their own resource, there is no guarantee for
        # across between resources (user and role in this case); while in practice we won't get overlap there is a
        # chance that this may happen in the future, would it be more sensible to use a Sequence here?
        guild_channel.is_nsfw = payload.get("nsfw")

        if (parent_id := payload.get("parent_id")) is not None:
            parent_id = snowflake.Snowflake(parent_id)
        guild_channel.parent_id = parent_id

    def deserialize_guild_category(self, payload: data_binding.JSONObject) -> channel_models.GuildCategory:
        category = channel_models.GuildCategory()
        category.app = self._app
        self._set_guild_channel_attributes(payload, category)
        return category

    def deserialize_guild_text_channel(self, payload: data_binding.JSONObject) -> channel_models.GuildTextChannel:
        guild_text_category = channel_models.GuildTextChannel()
        guild_text_category.app = self._app
        self._set_guild_channel_attributes(payload, guild_text_category)
        guild_text_category.topic = payload["topic"]

        if (last_message_id := payload["last_message_id"]) is not None:
            last_message_id = snowflake.Snowflake(last_message_id)
        guild_text_category.last_message_id = last_message_id

        guild_text_category.rate_limit_per_user = datetime.timedelta(seconds=payload["rate_limit_per_user"])

        if (last_pin_timestamp := payload.get("last_pin_timestamp")) is not None:
            last_pin_timestamp = date.iso8601_datetime_string_to_datetime(last_pin_timestamp)
        guild_text_category.last_pin_timestamp = last_pin_timestamp

        return guild_text_category

    def deserialize_guild_news_channel(self, payload: data_binding.JSONObject) -> channel_models.GuildNewsChannel:
        guild_news_channel = channel_models.GuildNewsChannel()
        guild_news_channel.app = self._app
        self._set_guild_channel_attributes(payload, guild_news_channel)
        guild_news_channel.topic = payload["topic"]

        if (last_message_id := payload["last_message_id"]) is not None:
            last_message_id = snowflake.Snowflake(last_message_id)
        guild_news_channel.last_message_id = last_message_id

        if (last_pin_timestamp := payload.get("last_pin_timestamp")) is not None:
            last_pin_timestamp = date.iso8601_datetime_string_to_datetime(last_pin_timestamp)
        guild_news_channel.last_pin_timestamp = last_pin_timestamp

        return guild_news_channel

    def deserialize_guild_store_channel(self, payload: data_binding.JSONObject) -> channel_models.GuildStoreChannel:
        guild_store_channel = channel_models.GuildStoreChannel()
        guild_store_channel.app = self._app
        self._set_guild_channel_attributes(payload, guild_store_channel)
        return guild_store_channel

    def deserialize_guild_voice_channel(self, payload: data_binding.JSONObject) -> channel_models.GuildVoiceChannel:
        guild_voice_channel = channel_models.GuildVoiceChannel()
        guild_voice_channel.app = self._app
        self._set_guild_channel_attributes(payload, guild_voice_channel)
        guild_voice_channel.bitrate = int(payload["bitrate"])
        guild_voice_channel.user_limit = int(payload["user_limit"])
        return guild_voice_channel

    def deserialize_channel(self, payload: data_binding.JSONObject) -> channel_models.PartialChannel:
        # noinspection PyArgumentList
        return self._channel_type_mapping[payload["type"]](payload)

    ################
    # EMBED MODELS #
    ################

    def deserialize_embed(self, payload: data_binding.JSONObject) -> embed_models.Embed:
        embed = embed_models.Embed()
        embed.title = payload.get("title")
        embed.description = payload.get("description")
        embed.url = payload.get("url")
        embed.timestamp = (
            date.iso8601_datetime_string_to_datetime(payload["timestamp"]) if "timestamp" in payload else None
        )
        embed.color = color_models.Color(payload["color"]) if "color" in payload else None

        if footer_payload := payload.get("footer"):
            footer = embed_models.EmbedFooter()
            footer.text = footer_payload["text"]

            if icon_url := footer_payload.get("icon_url"):
                footer.icon = embed_models.EmbedResource(resource=files.ensure_resource(icon_url))
                footer.icon.proxy_resource = files.ensure_resource(footer_payload.get("proxy_icon_url"))
            else:
                footer.icon = None

            embed.footer = footer
        else:
            embed.footer = None

        if image_payload := payload.get("image"):
            image = embed_models.EmbedImage(resource=files.ensure_resource(image_payload.get("url")))
            image.proxy_resource = files.ensure_resource(image_payload.get("proxy_url"))
            image.height = int(image_payload["height"]) if "height" in image_payload else None
            image.width = int(image_payload["width"]) if "width" in image_payload else None
            embed.image = image
        else:
            embed.image = None

        if thumbnail_payload := payload.get("thumbnail"):
            thumbnail = embed_models.EmbedImage(resource=files.ensure_resource(thumbnail_payload.get("url")))
            thumbnail.proxy_resource = files.ensure_resource(thumbnail_payload.get("proxy_url"))
            thumbnail.height = int(thumbnail_payload["height"]) if "height" in thumbnail_payload else None
            thumbnail.width = int(thumbnail_payload["width"]) if "width" in thumbnail_payload else None
            embed.thumbnail = thumbnail
        else:
            embed.thumbnail = None

        if video_payload := payload.get("video"):
            video = embed_models.EmbedVideo(
                resource=files.ensure_resource(video_payload.get("url")),
                height=int(video_payload["height"]) if "height" in video_payload else None,
                width=int(video_payload["width"]) if "width" in video_payload else None,
            )
            embed.video = video
        else:
            embed.video = None

        if provider_payload := payload.get("provider"):
            provider = embed_models.EmbedProvider()
            provider.name = provider_payload.get("name")
            provider.url = provider_payload.get("url")
            embed.provider = provider
        else:
            embed.provider = None

        if author_payload := payload.get("author"):
            author = embed_models.EmbedAuthor()
            author.name = author_payload.get("name")
            author.url = author_payload.get("url")

            if icon_url := author_payload.get("icon_url"):
                author.icon = embed_models.EmbedResource(resource=files.ensure_resource(icon_url))
                author.icon.proxy_resource = files.ensure_resource(author_payload.get("proxy_icon_url"))
            else:
                author.icon = None

            embed.author = author
        else:
            embed.author = None

        fields = []
        for field_payload in payload.get("fields", ()):
            fields.append(
                embed_models.EmbedField(
                    name=field_payload["name"], value=field_payload["value"], inline=field_payload.get("inline", False)
                )
            )
        embed.fields = fields

        return embed

    def serialize_embed(  # noqa: C901
        self, embed: embed_models.Embed,
    ) -> typing.Tuple[data_binding.JSONObject, typing.List[files.Resource]]:

        payload: data_binding.JSONObject = {}
        uploads: typing.List[files.Resource] = []

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
            for field in embed.fields:
                # Name and value always have to be specified; we can always
                # send a default `inline` value also just to keep this simpler.
                field_payloads.append({"name": field.name, "value": field.value, "inline": field.is_inline})
            payload["fields"] = field_payloads

        return payload, uploads

    ################
    # EMOJI MODELS #
    ################

    def deserialize_unicode_emoji(self, payload: data_binding.JSONObject) -> emoji_models.UnicodeEmoji:
        unicode_emoji = emoji_models.UnicodeEmoji()
        unicode_emoji.name = payload["name"]
        return unicode_emoji

    def deserialize_custom_emoji(self, payload: data_binding.JSONObject) -> emoji_models.CustomEmoji:
        custom_emoji = emoji_models.CustomEmoji()
        custom_emoji.app = self._app
        custom_emoji.id = snowflake.Snowflake(payload["id"])
        custom_emoji.name = payload["name"]
        custom_emoji.is_animated = payload.get("animated", False)
        return custom_emoji

    def deserialize_known_custom_emoji(self, payload: data_binding.JSONObject) -> emoji_models.KnownCustomEmoji:
        known_custom_emoji = emoji_models.KnownCustomEmoji()
        known_custom_emoji.app = self._app
        known_custom_emoji.id = snowflake.Snowflake(payload["id"])
        known_custom_emoji.name = payload["name"]
        known_custom_emoji.is_animated = payload.get("animated", False)
        known_custom_emoji.role_ids = {snowflake.Snowflake(role_id) for role_id in payload.get("roles", ())}

        if (user := payload.get("user")) is not None:
            user = self.deserialize_user(user)
        known_custom_emoji.user = user

        known_custom_emoji.is_colons_required = payload["require_colons"]
        known_custom_emoji.is_managed = payload["managed"]
        known_custom_emoji.is_available = payload["available"]
        return known_custom_emoji

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
        guild_widget = guild_models.GuildWidget()
        guild_widget.app = self._app

        if (channel_id := payload["channel_id"]) is not None:
            channel_id = snowflake.Snowflake(channel_id)
        guild_widget.channel_id = channel_id

        guild_widget.is_enabled = payload["enabled"]
        return guild_widget

    def deserialize_member(
        self,
        payload: data_binding.JSONObject,
        *,
        user: typing.Union[undefined.UndefinedType, user_models.User] = undefined.UNDEFINED,
    ) -> guild_models.Member:
        guild_member = guild_models.Member()
        guild_member.app = self._app
        guild_member.user = user or self.deserialize_user(payload["user"])
        guild_member.role_ids = {snowflake.Snowflake(role_id) for role_id in payload["roles"]}

        joined_at = payload.get("joined_at")
        guild_member.joined_at = (
            date.iso8601_datetime_string_to_datetime(joined_at) if joined_at is not None else undefined.UNDEFINED
        )

        guild_member.nickname = payload["nick"] if "nick" in payload else undefined.UNDEFINED

        if "premium_since" in payload:
            raw_premium_since = payload["premium_since"]
            guild_member.premium_since = (
                date.iso8601_datetime_string_to_datetime(raw_premium_since) if raw_premium_since is not None else None
            )
        else:
            guild_member.premium_since = undefined.UNDEFINED

        guild_member.is_deaf = payload["deaf"] if "deaf" in payload else undefined.UNDEFINED
        guild_member.is_mute = payload["mute"] if "mute" in payload else undefined.UNDEFINED
        return guild_member

    def deserialize_role(self, payload: data_binding.JSONObject) -> guild_models.Role:
        guild_role = guild_models.Role()
        guild_role.app = self._app
        guild_role.id = snowflake.Snowflake(payload["id"])
        guild_role.name = payload["name"]
        guild_role.color = color_models.Color(payload["color"])
        guild_role.is_hoisted = payload["hoist"]
        guild_role.position = int(payload["position"])
        # noinspection PyArgumentList
        guild_role.permissions = permission_models.Permission(payload["permissions"])
        guild_role.is_managed = payload["managed"]
        guild_role.is_mentionable = payload["mentionable"]
        return guild_role

    @staticmethod
    def _set_partial_integration_attributes(
        payload: data_binding.JSONObject, integration: guild_models.PartialIntegration
    ) -> None:
        integration.id = snowflake.Snowflake(payload["id"])
        integration.name = payload["name"]
        integration.type = payload["type"]
        account_payload = payload["account"]
        account = guild_models.IntegrationAccount()
        account.id = account_payload["id"]
        account.name = account_payload["name"]
        integration.account = account

    def deserialize_partial_integration(self, payload: data_binding.JSONObject) -> guild_models.PartialIntegration:
        partial_integration = guild_models.PartialIntegration()
        self._set_partial_integration_attributes(payload, partial_integration)
        return partial_integration

    def deserialize_integration(self, payload: data_binding.JSONObject) -> guild_models.Integration:
        guild_integration = guild_models.Integration()
        self._set_partial_integration_attributes(payload, guild_integration)
        guild_integration.is_enabled = payload["enabled"]
        guild_integration.is_syncing = payload["syncing"]

        if (role_id := payload.get("role_id")) is not None:
            role_id = snowflake.Snowflake(role_id)
        guild_integration.role_id = role_id

        guild_integration.is_emojis_enabled = payload.get("enable_emoticons")
        # noinspection PyArgumentList
        guild_integration.expire_behavior = guild_models.IntegrationExpireBehaviour(payload["expire_behavior"])
        guild_integration.expire_grace_period = datetime.timedelta(days=payload["expire_grace_period"])
        guild_integration.user = self.deserialize_user(payload["user"])

        if (last_synced_at := payload.get("synced_at")) is not None:
            last_synced_at = date.iso8601_datetime_string_to_datetime(last_synced_at)
        guild_integration.last_synced_at = last_synced_at

        return guild_integration

    def deserialize_guild_member_ban(self, payload: data_binding.JSONObject) -> guild_models.GuildMemberBan:
        guild_member_ban = guild_models.GuildMemberBan()
        guild_member_ban.reason = payload["reason"]
        guild_member_ban.user = self.deserialize_user(payload["user"])
        return guild_member_ban

    def deserialize_unavailable_guild(self, payload: data_binding.JSONObject) -> guild_models.UnavailableGuild:
        unavailable_guild = guild_models.UnavailableGuild()
        unavailable_guild.id = snowflake.Snowflake(payload["id"])
        return unavailable_guild

    @staticmethod
    def _set_partial_guild_attributes(payload: data_binding.JSONObject, guild: guild_models.PartialGuild) -> None:
        guild.id = snowflake.Snowflake(payload["id"])
        guild.name = payload["name"]
        guild.icon_hash = payload["icon"]

        features = []
        for feature in payload["features"]:
            try:
                # noinspection PyArgumentList
                features.append(guild_models.GuildFeature(feature))
            except ValueError:
                features.append(feature)
        guild.features = set(features)

    def deserialize_guild_preview(self, payload: data_binding.JSONObject) -> guild_models.GuildPreview:
        guild_preview = guild_models.GuildPreview()
        guild_preview.app = self._app
        self._set_partial_guild_attributes(payload, guild_preview)
        guild_preview.splash_hash = payload["splash"]
        guild_preview.discovery_splash_hash = payload["discovery_splash"]
        guild_preview.emojis = {
            snowflake.Snowflake(emoji["id"]): self.deserialize_known_custom_emoji(emoji) for emoji in payload["emojis"]
        }
        guild_preview.approximate_presence_count = int(payload["approximate_presence_count"])
        guild_preview.approximate_member_count = int(payload["approximate_member_count"])
        guild_preview.description = payload["description"]
        return guild_preview

    def deserialize_guild(self, payload: data_binding.JSONObject) -> guild_models.Guild:  # noqa: CFQ001
        guild = guild_models.Guild()
        self._set_partial_guild_attributes(payload, guild)
        guild.app = self._app
        guild.splash_hash = payload["splash"]
        guild.discovery_splash_hash = payload["discovery_splash"]
        guild.owner_id = snowflake.Snowflake(payload["owner_id"])
        # noinspection PyArgumentList

        guild.my_permissions = (
            permission_models.Permission(payload["permissions"]) if "permissions" in payload else None
        )

        guild.region = payload["region"]

        afk_channel_id = payload["afk_channel_id"]
        guild.afk_channel_id = snowflake.Snowflake(afk_channel_id) if afk_channel_id is not None else None

        guild.afk_timeout = datetime.timedelta(seconds=payload["afk_timeout"])
        guild.is_embed_enabled = payload.get("embed_enabled", False)

        embed_channel_id = payload.get("embed_channel_id")
        guild.embed_channel_id = snowflake.Snowflake(embed_channel_id) if embed_channel_id is not None else None

        # noinspection PyArgumentList
        guild.verification_level = guild_models.GuildVerificationLevel(payload["verification_level"])
        # noinspection PyArgumentList
        guild.default_message_notifications = guild_models.GuildMessageNotificationsLevel(
            payload["default_message_notifications"]
        )
        # noinspection PyArgumentList
        guild.explicit_content_filter = guild_models.GuildExplicitContentFilterLevel(payload["explicit_content_filter"])
        guild.roles = {snowflake.Snowflake(role["id"]): self.deserialize_role(role) for role in payload["roles"]}
        guild.emojis = {
            snowflake.Snowflake(emoji["id"]): self.deserialize_known_custom_emoji(emoji) for emoji in payload["emojis"]
        }
        # noinspection PyArgumentList
        guild.mfa_level = guild_models.GuildMFALevel(payload["mfa_level"])

        application_id = payload["application_id"]
        guild.application_id = snowflake.Snowflake(application_id) if application_id is not None else None

        guild.is_unavailable = payload["unavailable"] if "unavailable" in payload else None
        guild.is_widget_enabled = payload["widget_enabled"] if "widget_enabled" in payload else None

        widget_channel_id = payload.get("widget_channel_id")
        guild.widget_channel_id = snowflake.Snowflake(widget_channel_id) if widget_channel_id is not None else None

        system_channel_id = payload["system_channel_id"]
        guild.system_channel_id = snowflake.Snowflake(system_channel_id) if system_channel_id is not None else None

        # noinspection PyArgumentList
        guild.system_channel_flags = guild_models.GuildSystemChannelFlag(payload["system_channel_flags"])

        rules_channel_id = payload["rules_channel_id"]
        guild.rules_channel_id = snowflake.Snowflake(rules_channel_id) if rules_channel_id is not None else None

        guild.joined_at = (
            date.iso8601_datetime_string_to_datetime(payload["joined_at"]) if "joined_at" in payload else None
        )
        guild.is_large = payload["large"] if "large" in payload else None
        guild.member_count = int(payload["member_count"]) if "member_count" in payload else None

        guild.members = {}
        if "members" in payload:
            for member_payload in payload["members"]:
                member = self.deserialize_member(member_payload)
                # Could be None, so cast to avoid.
                user_id = typing.cast("user_models.User", member.user).id
                guild.members[user_id] = member

        guild.channels = {}
        if "channels" in payload:
            for channel_payload in payload["channels"]:
                channel = typing.cast("channel_models.GuildChannel", self.deserialize_channel(channel_payload))
                guild.channels[channel.id] = channel

        guild.presences = {}
        if "presences" in payload:
            for presence_payload in payload["presences"]:
                presence = self.deserialize_member_presence(presence_payload)
                guild.presences[presence.user.id] = presence

        max_presences = payload.get("max_presences")
        guild.max_presences = int(max_presences) if max_presences is not None else None

        guild.max_members = int(payload["max_members"]) if "max_members" in payload else None
        guild.max_video_channel_users = (
            int(payload["max_video_channel_users"]) if "max_video_channel_users" in payload else None
        )
        guild.vanity_url_code = payload["vanity_url_code"]
        guild.description = payload["description"]
        guild.banner_hash = payload["banner"]
        # noinspection PyArgumentList
        guild.premium_tier = guild_models.GuildPremiumTier(payload["premium_tier"])

        guild.premium_subscription_count = payload.get("premium_subscription_count")

        guild.preferred_locale = payload["preferred_locale"]

        public_updates_channel_id = payload["public_updates_channel_id"]
        guild.public_updates_channel_id = (
            snowflake.Snowflake(public_updates_channel_id) if public_updates_channel_id is not None else None
        )

        guild.approximate_member_count = (
            int(payload["approximate_member_count"]) if "approximate_member_count" in payload else None
        )
        guild.approximate_active_member_count = (
            int(payload["approximate_presence_count"]) if "approximate_presence_count" in payload else None
        )
        return guild

    #################
    # INVITE MODELS #
    #################

    def deserialize_vanity_url(self, payload: data_binding.JSONObject) -> invite_models.VanityURL:
        vanity_url = invite_models.VanityURL()
        vanity_url.app = self._app
        vanity_url.code = payload["code"]
        vanity_url.uses = int(payload["uses"])
        return vanity_url

    def _set_invite_attributes(self, payload: data_binding.JSONObject, invite: invite_models.Invite) -> None:
        invite.code = payload["code"]

        if "guild" in payload:
            guild_payload = payload["guild"]
            guild = invite_models.InviteGuild()
            guild.app = self._app
            self._set_partial_guild_attributes(guild_payload, guild)
            guild.splash_hash = guild_payload["splash"]
            guild.banner_hash = guild_payload["banner"]
            guild.description = guild_payload["description"]
            # noinspection PyArgumentList
            guild.verification_level = guild_models.GuildVerificationLevel(guild_payload["verification_level"])
            guild.vanity_url_code = guild_payload["vanity_url_code"]
            invite.guild = guild
            invite.guild_id = guild.id
        elif "guild_id" in payload:
            invite.guild = None
            invite.guild_id = snowflake.Snowflake(payload["guild_id"])
        else:
            invite.guild = invite.guild_id = None

        if (channel := payload.get("channel")) is not None:
            channel = self.deserialize_partial_channel(channel)
            channel_id = channel.id
        else:
            channel_id = snowflake.Snowflake(payload["channel_id"])
        invite.channel = channel
        invite.channel_id = channel_id

        invite.inviter = self.deserialize_user(payload["inviter"]) if "inviter" in payload else None
        invite.target_user = self.deserialize_user(payload["target_user"]) if "target_user" in payload else None
        # noinspection PyArgumentList
        invite.target_user_type = (
            invite_models.TargetUserType(payload["target_user_type"]) if "target_user_type" in payload else None
        )
        invite.approximate_presence_count = (
            int(payload["approximate_presence_count"]) if "approximate_presence_count" in payload else None
        )
        invite.approximate_member_count = (
            int(payload["approximate_member_count"]) if "approximate_member_count" in payload else None
        )

    def deserialize_invite(self, payload: data_binding.JSONObject) -> invite_models.Invite:
        invite = invite_models.Invite()
        invite.app = self._app
        self._set_invite_attributes(payload, invite)
        return invite

    def deserialize_invite_with_metadata(self, payload: data_binding.JSONObject) -> invite_models.InviteWithMetadata:
        invite_with_metadata = invite_models.InviteWithMetadata()
        invite_with_metadata.app = self._app
        self._set_invite_attributes(payload, invite_with_metadata)
        invite_with_metadata.uses = int(payload["uses"])
        invite_with_metadata.max_uses = int(payload["max_uses"])
        max_age = payload["max_age"]
        invite_with_metadata.max_age = datetime.timedelta(seconds=max_age) if max_age > 0 else None
        invite_with_metadata.is_temporary = payload["temporary"]
        invite_with_metadata.created_at = date.iso8601_datetime_string_to_datetime(payload["created_at"])
        return invite_with_metadata

    ##################
    # MESSAGE MODELS #
    ##################

    def deserialize_message(self, payload: data_binding.JSONObject) -> message_models.Message:
        message = message_models.Message()
        message.app = self._app
        message.id = snowflake.Snowflake(payload["id"])
        message.channel_id = snowflake.Snowflake(payload["channel_id"])
        message.guild_id = snowflake.Snowflake(payload["guild_id"]) if "guild_id" in payload else None
        message.author = self.deserialize_user(payload["author"])
        message.member = (
            self.deserialize_member(payload["member"], user=message.author) if "member" in payload else None
        )
        message.content = payload["content"]
        message.timestamp = date.iso8601_datetime_string_to_datetime(payload["timestamp"])

        if (edited_timestamp := payload["edited_timestamp"]) is not None:
            edited_timestamp = date.iso8601_datetime_string_to_datetime(edited_timestamp)
        message.edited_timestamp = edited_timestamp

        message.is_tts = payload["tts"]
        message.is_mentioning_everyone = payload["mention_everyone"]
        message.user_mentions = {snowflake.Snowflake(mention["id"]) for mention in payload["mentions"]}
        message.role_mentions = {snowflake.Snowflake(mention) for mention in payload["mention_roles"]}
        message.channel_mentions = {
            snowflake.Snowflake(mention["id"]) for mention in payload.get("mention_channels", ())
        }

        attachments = []
        for attachment_payload in payload["attachments"]:
            attachment = message_models.Attachment()
            attachment.id = snowflake.Snowflake(attachment_payload["id"])
            attachment.filename = attachment_payload["filename"]
            attachment.size = int(attachment_payload["size"])
            attachment.url = attachment_payload["url"]
            attachment.proxy_url = attachment_payload["proxy_url"]
            attachment.height = attachment_payload.get("height")
            attachment.width = attachment_payload.get("width")
            attachments.append(attachment)
        message.attachments = attachments

        message.embeds = [self.deserialize_embed(embed) for embed in payload["embeds"]]

        reactions = []
        for reaction_payload in payload.get("reactions", ()):
            reaction = message_models.Reaction()
            reaction.count = int(reaction_payload["count"])
            reaction.emoji = self.deserialize_emoji(reaction_payload["emoji"])
            reaction.is_reacted_by_me = reaction_payload["me"]
            reactions.append(reaction)
        message.reactions = reactions

        message.is_pinned = payload["pinned"]
        message.webhook_id = snowflake.Snowflake(payload["webhook_id"]) if "webhook_id" in payload else None
        # noinspection PyArgumentList
        message.type = message_models.MessageType(payload["type"])

        if "activity" in payload:
            activity_payload = payload["activity"]
            activity = message_models.MessageActivity()
            # noinspection PyArgumentList
            activity.type = message_models.MessageActivityType(activity_payload["type"])
            activity.party_id = activity_payload.get("party_id")
            message.activity = activity
        else:
            message.activity = None

        message.application = self.deserialize_application(payload["application"]) if "application" in payload else None

        if "message_reference" in payload:
            crosspost_payload = payload["message_reference"]
            crosspost = message_models.MessageCrosspost()
            crosspost.app = self._app
            crosspost.id = (
                snowflake.Snowflake(crosspost_payload["message_id"]) if "message_id" in crosspost_payload else None
            )
            crosspost.channel_id = snowflake.Snowflake(crosspost_payload["channel_id"])
            crosspost.guild_id = (
                snowflake.Snowflake(crosspost_payload["guild_id"]) if "guild_id" in crosspost_payload else None
            )
            message.message_reference = crosspost
        else:
            message.message_reference = None

        # noinspection PyArgumentList
        message.flags = message_models.MessageFlag(payload["flags"]) if "flags" in payload else None
        message.nonce = payload.get("nonce")
        return message

    ###################
    # PRESENCE MODELS #
    ###################

    def deserialize_member_presence(  # noqa: CFQ001
        self, payload: data_binding.JSONObject
    ) -> presence_models.MemberPresence:
        guild_member_presence = presence_models.MemberPresence()
        guild_member_presence.app = self._app
        user_payload = payload["user"]
        user = user_models.PartialUser()
        user.app = self._app
        user.id = snowflake.Snowflake(user_payload["id"])
        user.discriminator = user_payload["discriminator"] if "discriminator" in user_payload else undefined.UNDEFINED
        user.username = user_payload["username"] if "username" in user_payload else undefined.UNDEFINED
        user.avatar_hash = user_payload["avatar"] if "avatar" in user_payload else undefined.UNDEFINED
        user.is_bot = user_payload["bot"] if "bot" in user_payload else undefined.UNDEFINED
        user.is_system = user_payload["system"] if "system" in user_payload else undefined.UNDEFINED
        # noinspection PyArgumentList
        user.flags = (
            user_models.UserFlag(user_payload["public_flags"])
            if "public_flags" in user_payload
            else undefined.UNDEFINED
        )
        guild_member_presence.user = user

        guild_member_presence.role_ids = (
            {snowflake.Snowflake(role_id) for role_id in role_ids}
            if (role_ids := payload.get("roles")) is not None
            else None
        )

        guild_member_presence.guild_id = snowflake.Snowflake(payload["guild_id"]) if "guild_id" in payload else None
        # noinspection PyArgumentList
        guild_member_presence.visible_status = presence_models.Status(payload["status"])

        activities = []
        for activity_payload in payload["activities"]:
            # noinspection PyArgumentList
            activity = presence_models.RichActivity(
                name=activity_payload["name"],
                type=presence_models.ActivityType(activity_payload["type"]),
                url=activity_payload.get("url"),
            )

            activity.created_at = date.unix_epoch_to_datetime(activity_payload["created_at"])

            timestamps = None
            if "timestamps" in activity_payload:
                timestamps_payload = activity_payload["timestamps"]
                timestamps = presence_models.ActivityTimestamps()
                timestamps.start = (
                    date.unix_epoch_to_datetime(timestamps_payload["start"]) if "start" in timestamps_payload else None
                )
                timestamps.end = (
                    date.unix_epoch_to_datetime(timestamps_payload["end"]) if "end" in timestamps_payload else None
                )
            activity.timestamps = timestamps

            activity.application_id = (
                snowflake.Snowflake(activity_payload["application_id"])
                if "application_id" in activity_payload
                else None
            )
            activity.details = activity_payload.get("details")
            activity.state = activity_payload.get("state")

            emoji = activity_payload.get("emoji")
            activity.emoji = self.deserialize_emoji(emoji) if emoji is not None else None

            party = None
            if "party" in activity_payload:
                party_payload = activity_payload["party"]
                party = presence_models.ActivityParty()
                party.id = party_payload.get("id")

                if "size" in party_payload:
                    current_size, max_size = party_payload["size"]
                    party.current_size = int(current_size)
                    party.max_size = int(max_size)
                else:
                    party.current_size = party.max_size = None
            activity.party = party

            assets = None
            if "assets" in activity_payload:
                assets_payload = activity_payload["assets"]
                assets = presence_models.ActivityAssets()
                assets.large_image = assets_payload.get("large_image")
                assets.large_text = assets_payload.get("large_text")
                assets.small_image = assets_payload.get("small_image")
                assets.small_text = assets_payload.get("small_text")
            activity.assets = assets

            secrets = None
            if "secrets" in activity_payload:
                secrets_payload = activity_payload["secrets"]
                secrets = presence_models.ActivitySecret()
                secrets.join = secrets_payload.get("join")
                secrets.spectate = secrets_payload.get("spectate")
                secrets.match = secrets_payload.get("match")
            activity.secrets = secrets

            activity.is_instance = activity_payload.get("instance")  # TODO: can we safely default this to False?
            # noinspection PyArgumentList
            activity.flags = (
                presence_models.ActivityFlag(activity_payload["flags"]) if "flags" in activity_payload else None
            )
            activities.append(activity)
        guild_member_presence.activities = activities

        client_status_payload = payload["client_status"]
        client_status = presence_models.ClientStatus()
        # noinspection PyArgumentList
        client_status.desktop = (
            presence_models.Status(client_status_payload["desktop"])
            if "desktop" in client_status_payload
            else presence_models.Status.OFFLINE
        )
        # noinspection PyArgumentList
        client_status.mobile = (
            presence_models.Status(client_status_payload["mobile"])
            if "mobile" in client_status_payload
            else presence_models.Status.OFFLINE
        )
        # noinspection PyArgumentList
        client_status.web = (
            presence_models.Status(client_status_payload["web"])
            if "web" in client_status_payload
            else presence_models.Status.OFFLINE
        )
        guild_member_presence.client_status = client_status

        # TODO: do we want to differentiate between undefined and null here?
        premium_since = payload.get("premium_since")
        guild_member_presence.premium_since = (
            date.iso8601_datetime_string_to_datetime(premium_since) if premium_since is not None else None
        )

        # TODO: do we want to differentiate between undefined and null here?
        guild_member_presence.nickname = payload.get("nick")
        return guild_member_presence

    ###############
    # USER MODELS #
    ###############

    @staticmethod
    def _set_user_attributes(payload: data_binding.JSONObject, user: user_models.User) -> None:
        user.id = snowflake.Snowflake(payload["id"])
        user.discriminator = payload["discriminator"]
        user.username = payload["username"]
        user.avatar_hash = payload["avatar"]
        user.is_bot = payload.get("bot", False)
        user.is_system = payload.get("system", False)

    def deserialize_user(self, payload: data_binding.JSONObject) -> user_models.User:
        user = user_models.User()
        user.app = self._app
        self._set_user_attributes(payload, user)
        # noinspection PyArgumentList
        user.flags = (
            user_models.UserFlag(payload["public_flags"]) if "public_flags" in payload else user_models.UserFlag.NONE
        )
        return user

    def deserialize_my_user(self, payload: data_binding.JSONObject) -> user_models.OwnUser:
        my_user = user_models.OwnUser()
        my_user.app = self._app
        self._set_user_attributes(payload, my_user)
        my_user.is_mfa_enabled = payload["mfa_enabled"]
        my_user.locale = payload.get("locale")
        my_user.is_verified = payload.get("verified")
        my_user.email = payload.get("email")
        # noinspection PyArgumentList
        my_user.flags = user_models.UserFlag(payload["flags"])
        # noinspection PyArgumentList
        my_user.premium_type = user_models.PremiumType(payload["premium_type"]) if "premium_type" in payload else None
        return my_user

    ################
    # VOICE MODELS #
    ################

    def deserialize_voice_state(self, payload: data_binding.JSONObject) -> voice_models.VoiceState:
        voice_state = voice_models.VoiceState()
        voice_state.app = self._app
        voice_state.guild_id = snowflake.Snowflake(payload["guild_id"]) if "guild_id" in payload else None

        if (channel_id := payload["channel_id"]) is not None:
            channel_id = snowflake.Snowflake(channel_id)
        voice_state.channel_id = channel_id

        voice_state.user_id = snowflake.Snowflake(payload["user_id"])
        voice_state.member = self.deserialize_member(payload["member"]) if "member" in payload else None
        voice_state.session_id = payload["session_id"]
        voice_state.is_guild_deafened = payload["deaf"]
        voice_state.is_guild_muted = payload["mute"]
        voice_state.is_self_deafened = payload["self_deaf"]
        voice_state.is_self_muted = payload["self_mute"]
        voice_state.is_streaming = payload.get("self_stream", False)
        voice_state.is_video_enabled = payload["self_video"]
        voice_state.is_suppressed = payload["suppress"]
        return voice_state

    def deserialize_voice_region(self, payload: data_binding.JSONObject) -> voice_models.VoiceRegion:
        voice_region = voice_models.VoiceRegion()
        voice_region.id = payload["id"]
        voice_region.name = payload["name"]
        voice_region.is_vip = payload["vip"]
        voice_region.is_optimal_location = payload["optimal"]
        voice_region.is_deprecated = payload["deprecated"]
        voice_region.is_custom = payload["custom"]
        return voice_region

    ##################
    # WEBHOOK MODELS #
    ##################

    def deserialize_webhook(self, payload: data_binding.JSONObject) -> webhook_models.Webhook:
        webhook = webhook_models.Webhook()
        webhook.app = self._app
        webhook.id = snowflake.Snowflake(payload["id"])
        # noinspection PyArgumentList
        webhook.type = webhook_models.WebhookType(payload["type"])
        webhook.guild_id = snowflake.Snowflake(payload["guild_id"]) if "guild_id" in payload else None
        webhook.channel_id = snowflake.Snowflake(payload["channel_id"])
        webhook.author = self.deserialize_user(payload["user"]) if "user" in payload else None
        webhook.name = payload["name"]
        webhook.avatar_hash = payload["avatar"]
        webhook.token = payload.get("token")
        return webhook

    ##################
    # CHANNEL EVENTS #  # TODO: have event models that just contain one model relay attributes?
    ##################

    def deserialize_channel_create_event(self, payload: data_binding.JSONObject) -> channel_events.ChannelCreateEvent:
        channel_create_event = channel_events.ChannelCreateEvent()
        channel_create_event.channel = self.deserialize_channel(payload)
        return channel_create_event

    def deserialize_channel_update_event(self, payload: data_binding.JSONObject) -> channel_events.ChannelUpdateEvent:
        channel_update_event = channel_events.ChannelUpdateEvent()
        channel_update_event.channel = self.deserialize_channel(payload)
        return channel_update_event

    def deserialize_channel_delete_event(self, payload: data_binding.JSONObject) -> channel_events.ChannelDeleteEvent:
        channel_delete_event = channel_events.ChannelDeleteEvent()
        channel_delete_event.channel = self.deserialize_channel(payload)
        return channel_delete_event

    def deserialize_channel_pins_update_event(
        self, payload: data_binding.JSONObject
    ) -> channel_events.ChannelPinsUpdateEvent:
        channel_pins_update = channel_events.ChannelPinsUpdateEvent()
        channel_pins_update.app = self._app
        channel_pins_update.guild_id = snowflake.Snowflake(payload["guild_id"]) if "guild_id" in payload else None
        channel_pins_update.channel_id = snowflake.Snowflake(payload["channel_id"])

        channel_pins_update.last_pin_timestamp = (
            date.iso8601_datetime_string_to_datetime(payload["last_pin_timestamp"])
            if "last_pin_timestamp" in payload
            else None
        )

        return channel_pins_update

    def deserialize_webhook_update_event(self, payload: data_binding.JSONObject) -> channel_events.WebhookUpdateEvent:
        webhook_update = channel_events.WebhookUpdateEvent()
        webhook_update.app = self._app
        webhook_update.guild_id = snowflake.Snowflake(payload["guild_id"])
        webhook_update.channel_id = snowflake.Snowflake(payload["channel_id"])
        return webhook_update

    def deserialize_typing_start_event(self, payload: data_binding.JSONObject) -> channel_events.TypingStartEvent:
        typing_start = channel_events.TypingStartEvent()
        typing_start.app = self._app
        typing_start.channel_id = snowflake.Snowflake(payload["channel_id"])
        typing_start.guild_id = snowflake.Snowflake(payload["guild_id"]) if "guild_id" in payload else None
        typing_start.user_id = snowflake.Snowflake(payload["user_id"])
        # payload["timestamp"] varies from most unix epoches we see from discord as it is in seconds rather than
        # milliseconds but it's easier to multiple it by 1k than to duplicate the logic in date.unix_epoch_to_datetime.
        typing_start.timestamp = date.unix_epoch_to_datetime(payload["timestamp"] * 1000)
        typing_start.member = self.deserialize_member(payload["member"]) if "member" in payload else None
        return typing_start

    def deserialize_invite_create_event(self, payload: data_binding.JSONObject) -> channel_events.InviteCreateEvent:
        invite_create = channel_events.InviteCreateEvent()
        invite_create.invite = self.deserialize_invite_with_metadata(payload)
        return invite_create

    def deserialize_invite_delete_event(self, payload: data_binding.JSONObject) -> channel_events.InviteDeleteEvent:
        invite_delete = channel_events.InviteDeleteEvent()
        invite_delete.app = self._app
        invite_delete.code = payload["code"]
        invite_delete.channel_id = snowflake.Snowflake(payload["channel_id"])
        invite_delete.guild_id = snowflake.Snowflake(payload["guild_id"]) if "guild_id" in payload else None
        return invite_delete

    ################
    # GUILD EVENTS #
    ################

    def deserialize_guild_create_event(self, payload: data_binding.JSONObject) -> guild_events.GuildCreateEvent:
        guild_create = guild_events.GuildCreateEvent()
        guild_create.guild = self.deserialize_guild(payload)
        return guild_create

    def deserialize_guild_update_event(self, payload: data_binding.JSONObject) -> guild_events.GuildUpdateEvent:
        guild_update = guild_events.GuildUpdateEvent()
        guild_update.guild = self.deserialize_guild(payload)
        return guild_update

    def deserialize_guild_leave_event(self, payload: data_binding.JSONObject) -> guild_events.GuildLeaveEvent:
        guild_leave = guild_events.GuildLeaveEvent()
        guild_leave.id = snowflake.Snowflake(payload["id"])
        return guild_leave

    def deserialize_guild_unavailable_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildUnavailableEvent:
        guild_unavailable = guild_events.GuildUnavailableEvent()
        guild_unavailable.app = self._app
        guild_unavailable.id = snowflake.Snowflake(payload["id"])
        return guild_unavailable

    def _set_base_guild_ban_event_fields(
        self, payload: data_binding.JSONObject, guild_ban: guild_events.GuildBanEvent
    ) -> None:
        guild_ban.guild_id = snowflake.Snowflake(payload["guild_id"])
        guild_ban.user = self.deserialize_user(payload["user"])

    def deserialize_guild_ban_add_event(self, payload: data_binding.JSONObject) -> guild_events.GuildBanAddEvent:
        guild_ban_add_event = guild_events.GuildBanAddEvent()
        guild_ban_add_event.app = self._app
        self._set_base_guild_ban_event_fields(payload, guild_ban_add_event)
        return guild_ban_add_event

    def deserialize_guild_ban_remove_event(self, payload: data_binding.JSONObject) -> guild_events.GuildBanRemoveEvent:
        guild_ban_remove_event = guild_events.GuildBanRemoveEvent()
        guild_ban_remove_event.app = self._app
        self._set_base_guild_ban_event_fields(payload, guild_ban_remove_event)
        return guild_ban_remove_event

    def deserialize_guild_emojis_update_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildEmojisUpdateEvent:
        guild_emojis_update = guild_events.GuildEmojisUpdateEvent()
        guild_emojis_update.app = self._app
        guild_emojis_update.guild_id = snowflake.Snowflake(payload["guild_id"])
        guild_emojis_update.emojis = {
            snowflake.Snowflake(emoji["id"]): self.deserialize_known_custom_emoji(emoji) for emoji in payload["emojis"]
        }
        return guild_emojis_update

    def deserialize_guild_integrations_update_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildIntegrationsUpdateEvent:
        guild_integrations_update = guild_events.GuildIntegrationsUpdateEvent()
        guild_integrations_update.app = self._app
        guild_integrations_update.guild_id = snowflake.Snowflake(payload["guild_id"])
        return guild_integrations_update

    def deserialize_guild_member_add_event(self, payload: data_binding.JSONObject) -> guild_events.GuildMemberAddEvent:
        guild_member_add = guild_events.GuildMemberAddEvent()
        guild_member_add.app = self._app
        guild_member_add.guild_id = snowflake.Snowflake(payload["guild_id"])
        guild_member_add.member = self.deserialize_member(payload)
        return guild_member_add

    def deserialize_guild_member_update_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildMemberUpdateEvent:
        guild_member_update = guild_events.GuildMemberUpdateEvent()
        guild_member_update.member = self.deserialize_member(payload)
        return guild_member_update

    def deserialize_guild_member_remove_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildMemberRemoveEvent:
        guild_member_remove = guild_events.GuildMemberRemoveEvent()
        guild_member_remove.app = self._app
        guild_member_remove.guild_id = snowflake.Snowflake(payload["guild_id"])
        guild_member_remove.user = self.deserialize_user(payload["user"])
        return guild_member_remove

    def deserialize_guild_role_create_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildRoleCreateEvent:
        guild_role_create = guild_events.GuildRoleCreateEvent()
        guild_role_create.app = self._app
        guild_role_create.guild_id = snowflake.Snowflake(payload["guild_id"])
        guild_role_create.role = self.deserialize_role(payload["role"])
        return guild_role_create

    def deserialize_guild_role_update_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildRoleUpdateEvent:
        guild_role_update = guild_events.GuildRoleUpdateEvent()
        guild_role_update.app = self._app
        guild_role_update.guild_id = snowflake.Snowflake(payload["guild_id"])
        guild_role_update.role = self.deserialize_role(payload["role"])
        return guild_role_update

    def deserialize_guild_role_delete_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildRoleDeleteEvent:
        guild_role_delete = guild_events.GuildRoleDeleteEvent()
        guild_role_delete.app = self._app
        guild_role_delete.guild_id = snowflake.Snowflake(payload["guild_id"])
        guild_role_delete.role_id = snowflake.Snowflake(payload["role_id"])
        return guild_role_delete

    def deserialize_presence_update_event(self, payload: data_binding.JSONObject) -> guild_events.PresenceUpdateEvent:
        presence_update = guild_events.PresenceUpdateEvent()
        presence_update.presence = self.deserialize_member_presence(payload)
        return presence_update

    ##################
    # MESSAGE EVENTS #
    ##################

    def deserialize_message_create_event(self, payload: data_binding.JSONObject) -> message_events.MessageCreateEvent:
        message_create = message_events.MessageCreateEvent()
        message_create.message = self.deserialize_message(payload)
        return message_create

    def deserialize_message_update_event(  # noqa: CFQ001
        self, payload: data_binding.JSONObject
    ) -> message_events.MessageUpdateEvent:
        message_update = message_events.MessageUpdateEvent()

        updated_message = message_events.UpdatedMessageFields()
        updated_message.app = self._app
        updated_message.id = snowflake.Snowflake(payload["id"])
        updated_message.channel_id = snowflake.Snowflake(payload["channel_id"])
        updated_message.guild_id = (
            snowflake.Snowflake(payload["guild_id"]) if "guild_id" in payload else undefined.UNDEFINED
        )
        updated_message.author = (
            self.deserialize_user(payload["author"]) if "author" in payload else undefined.UNDEFINED
        )
        updated_message.member = (
            self.deserialize_member(payload["member"], user=updated_message.author)
            if "member" in payload
            else undefined.UNDEFINED
        )
        updated_message.content = payload["content"] if "content" in payload else undefined.UNDEFINED
        updated_message.timestamp = (
            date.iso8601_datetime_string_to_datetime(payload["timestamp"])
            if "timestamp" in payload
            else undefined.UNDEFINED
        )

        if "edited_timestamp" in payload:
            if (edited_timestamp := payload["edited_timestamp"]) is not None:
                edited_timestamp = date.iso8601_datetime_string_to_datetime(edited_timestamp)
            else:
                edited_timestamp = None
        else:
            edited_timestamp = undefined.UNDEFINED

        updated_message.edited_timestamp = edited_timestamp

        updated_message.is_tts = payload["tts"] if "tts" in payload else undefined.UNDEFINED
        updated_message.is_mentioning_everyone = (
            payload["mention_everyone"] if "mention_everyone" in payload else undefined.UNDEFINED
        )
        updated_message.user_mentions = (
            {snowflake.Snowflake(mention["id"]) for mention in payload["mentions"]}
            if "mentions" in payload
            else undefined.UNDEFINED
        )
        updated_message.role_mentions = (
            {snowflake.Snowflake(mention) for mention in payload["mention_roles"]}
            if "mention_roles" in payload
            else undefined.UNDEFINED
        )
        updated_message.channel_mentions = (
            {snowflake.Snowflake(mention["id"]) for mention in payload["mention_channels"]}
            if "mention_channels" in payload
            else undefined.UNDEFINED
        )

        if "attachments" in payload:
            attachments = []
            for attachment_payload in payload["attachments"]:
                attachment = message_models.Attachment()
                attachment.id = snowflake.Snowflake(attachment_payload["id"])
                attachment.filename = attachment_payload["filename"]
                attachment.size = int(attachment_payload["size"])
                attachment.url = attachment_payload["url"]
                attachment.proxy_url = attachment_payload["proxy_url"]
                attachment.height = attachment_payload.get("height")
                attachment.width = attachment_payload.get("width")
                attachments.append(attachment)
            updated_message.attachments = attachments
        else:
            updated_message.attachments = undefined.UNDEFINED

        updated_message.embeds = (
            [self.deserialize_embed(embed) for embed in payload["embeds"]]
            if "embeds" in payload
            else undefined.UNDEFINED
        )

        if "reactions" in payload:
            reactions = []
            for reaction_payload in payload["reactions"]:
                reaction = message_models.Reaction()
                reaction.count = int(reaction_payload["count"])
                reaction.emoji = self.deserialize_emoji(reaction_payload["emoji"])
                reaction.is_reacted_by_me = reaction_payload["me"]
                reactions.append(reaction)
            updated_message.reactions = reactions
        else:
            updated_message.reactions = undefined.UNDEFINED

        updated_message.is_pinned = payload["pinned"] if "pinned" in payload else undefined.UNDEFINED
        updated_message.webhook_id = (
            snowflake.Snowflake(payload["webhook_id"]) if "webhook_id" in payload else undefined.UNDEFINED
        )
        # noinspection PyArgumentList
        updated_message.type = message_models.MessageType(payload["type"]) if "type" in payload else undefined.UNDEFINED

        if "activity" in payload:
            activity_payload = payload["activity"]
            activity = message_models.MessageActivity()
            # noinspection PyArgumentList
            activity.type = message_models.MessageActivityType(activity_payload["type"])
            activity.party_id = activity_payload.get("party_id")
            updated_message.activity = activity
        else:
            updated_message.activity = undefined.UNDEFINED

        updated_message.application = (
            self.deserialize_application(payload["application"]) if "application" in payload else undefined.UNDEFINED
        )

        if "message_reference" in payload:
            crosspost_payload = payload["message_reference"]
            crosspost = message_models.MessageCrosspost()
            crosspost.app = self._app
            crosspost.id = (
                snowflake.Snowflake(crosspost_payload["message_id"]) if "message_id" in crosspost_payload else None
            )
            crosspost.channel_id = snowflake.Snowflake(crosspost_payload["channel_id"])
            crosspost.guild_id = (
                snowflake.Snowflake(crosspost_payload["guild_id"]) if "guild_id" in crosspost_payload else None
            )
            updated_message.message_reference = crosspost
        else:
            updated_message.message_reference = undefined.UNDEFINED

        # noinspection PyArgumentList
        updated_message.flags = (
            message_models.MessageFlag(payload["flags"]) if "flags" in payload else undefined.UNDEFINED
        )
        updated_message.nonce = payload["nonce"] if "nonce" in payload else undefined.UNDEFINED

        message_update.message = updated_message
        return message_update

    def deserialize_message_delete_event(self, payload: data_binding.JSONObject) -> message_events.MessageDeleteEvent:
        message_delete = message_events.MessageDeleteEvent()
        message_delete.app = self._app
        message_delete.channel_id = snowflake.Snowflake(payload["channel_id"])
        message_delete.guild_id = snowflake.Snowflake(payload["guild_id"]) if "guild_id" in payload else None
        message_delete.message_id = snowflake.Snowflake(payload["id"])
        return message_delete

    def deserialize_message_delete_bulk_event(
        self, payload: data_binding.JSONObject
    ) -> message_events.MessageDeleteBulkEvent:
        message_delete_bulk = message_events.MessageDeleteBulkEvent()
        message_delete_bulk.app = self._app
        message_delete_bulk.channel_id = snowflake.Snowflake(payload["channel_id"])
        message_delete_bulk.guild_id = snowflake.Snowflake(payload["guild_id"]) if "guild_id" in payload else None
        message_delete_bulk.message_ids = {snowflake.Snowflake(message_id) for message_id in payload["ids"]}
        return message_delete_bulk

    @staticmethod
    def _set_base_message_reaction_fields(
        payload: data_binding.JSONObject, reaction_event: message_events.MessageReactionEvent
    ) -> None:
        reaction_event.channel_id = snowflake.Snowflake(payload["channel_id"])
        reaction_event.message_id = snowflake.Snowflake(payload["message_id"])
        reaction_event.guild_id = snowflake.Snowflake(payload["guild_id"]) if "guild_id" in payload else None

    def deserialize_message_reaction_add_event(
        self, payload: data_binding.JSONObject
    ) -> message_events.MessageReactionAddEvent:
        message_reaction_add = message_events.MessageReactionAddEvent()
        message_reaction_add.app = self._app
        self._set_base_message_reaction_fields(payload, message_reaction_add)
        message_reaction_add.user_id = snowflake.Snowflake(payload["user_id"])
        message_reaction_add.member = self.deserialize_member(payload["member"]) if "member" in payload else None
        message_reaction_add.emoji = self.deserialize_emoji(payload["emoji"])
        return message_reaction_add

    def deserialize_message_reaction_remove_event(
        self, payload: data_binding.JSONObject
    ) -> message_events.MessageReactionRemoveEvent:
        message_reaction_remove = message_events.MessageReactionRemoveEvent()
        message_reaction_remove.app = self._app
        self._set_base_message_reaction_fields(payload, message_reaction_remove)
        message_reaction_remove.user_id = snowflake.Snowflake(payload["user_id"])
        message_reaction_remove.emoji = self.deserialize_emoji(payload["emoji"])
        return message_reaction_remove

    def deserialize_message_reaction_remove_all_event(
        self, payload: data_binding.JSONObject
    ) -> message_events.MessageReactionRemoveAllEvent:
        message_reaction_event = message_events.MessageReactionRemoveAllEvent()
        message_reaction_event.app = self._app
        self._set_base_message_reaction_fields(payload, message_reaction_event)
        return message_reaction_event

    def deserialize_message_reaction_remove_emoji_event(
        self, payload: data_binding.JSONObject
    ) -> message_events.MessageReactionRemoveEmojiEvent:
        message_reaction_remove_emoji = message_events.MessageReactionRemoveEmojiEvent()
        message_reaction_remove_emoji.app = self._app
        self._set_base_message_reaction_fields(payload, message_reaction_remove_emoji)
        message_reaction_remove_emoji.emoji = self.deserialize_emoji(payload["emoji"])
        return message_reaction_remove_emoji

    ################
    # OTHER EVENTS #
    ################

    def deserialize_ready_event(
        self, shard: gateway.Gateway, payload: data_binding.JSONObject
    ) -> other_events.ReadyEvent:
        ready_event = other_events.ReadyEvent()
        ready_event.shard = shard
        ready_event.gateway_version = int(payload["v"])
        ready_event.my_user = self.deserialize_my_user(payload["user"])
        ready_event.unavailable_guilds = {
            snowflake.Snowflake(guild["id"]): self.deserialize_unavailable_guild(guild) for guild in payload["guilds"]
        }
        ready_event.session_id = payload["session_id"]

        # Shouldn't ever be none, but if it is, we don't care.
        if (shard_data := payload.get("shard")) is not None:
            ready_event.shard_id = int(shard_data[0])
            ready_event.shard_count = int(shard_data[1])
        else:
            ready_event.shard_id = ready_event.shard_count = None

        return ready_event

    def deserialize_own_user_update_event(self, payload: data_binding.JSONObject) -> other_events.OwnUserUpdateEvent:
        my_user_update = other_events.OwnUserUpdateEvent()
        my_user_update.my_user = self.deserialize_my_user(payload)
        return my_user_update

    ################
    # VOICE EVENTS #
    ################

    def deserialize_voice_state_update_event(
        self, payload: data_binding.JSONObject
    ) -> voice_events.VoiceStateUpdateEvent:
        voice_state_update = voice_events.VoiceStateUpdateEvent()
        voice_state_update.state = self.deserialize_voice_state(payload)
        return voice_state_update

    def deserialize_voice_server_update_event(
        self, payload: data_binding.JSONObject
    ) -> voice_events.VoiceServerUpdateEvent:
        voice_server_update = voice_events.VoiceServerUpdateEvent()
        voice_server_update.token = payload["token"]
        voice_server_update.guild_id = snowflake.Snowflake(payload["guild_id"])
        voice_server_update.endpoint = payload["endpoint"]
        return voice_server_update

    def serialize_gateway_presence(
        self,
        idle_since: typing.Union[undefined.UndefinedType, typing.Optional[datetime.datetime]] = undefined.UNDEFINED,
        is_afk: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        status: typing.Union[undefined.UndefinedType, presence_models.Status] = undefined.UNDEFINED,
        activity: typing.Union[
            undefined.UndefinedType, typing.Optional[presence_models.Activity]
        ] = undefined.UNDEFINED,
    ) -> data_binding.JSONObject:
        if activity is not None and activity is not undefined.UNDEFINED:
            game: typing.Union[undefined.UndefinedType, None, data_binding.JSONObject] = {
                "name": activity.name,
                "url": activity.url,
                "type": activity.type,
            }
        else:
            game = activity

        payload = data_binding.JSONObjectBuilder()
        payload.put("since", idle_since, conversion=datetime.datetime.timestamp)
        payload.put("afk", is_afk)
        payload.put("status", status)
        payload.put("game", game)
        return payload

    def serialize_gateway_voice_state_update(
        self,
        guild: typing.Union[guild_models.Guild, snowflake.UniqueObject],
        channel: typing.Union[channel_models.GuildVoiceChannel, snowflake.UniqueObject, None],
        self_mute: bool,
        self_deaf: bool,
    ) -> data_binding.JSONObject:
        return {
            "guild_id": str(int(guild)),
            "channel_id": str(int(channel)) if channel is not None else None,
            "self_mute": self_mute,
            "self_deaf": self_deaf,
        }
