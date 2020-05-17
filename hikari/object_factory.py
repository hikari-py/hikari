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
"""Utilities to handle cache management and object deserialization."""
from __future__ import annotations

import abc
import typing

from hikari.models import bases

if typing.TYPE_CHECKING:
    from hikari.models import applications
    from hikari.models import audit_logs
    from hikari.models import channels
    from hikari.models import embeds
    from hikari.models import emojis
    from hikari.models import gateway
    from hikari.models import guilds
    from hikari.models import invites
    from hikari.models import messages
    from hikari.models import users
    from hikari.models import voices
    from hikari.models import webhooks
    from hikari.internal import more_typing


class ObjectFactory:
    """Class that handles deserialization and cache operations.

    This is designed to be interfaced with using the event manager.
    """

    def __init__(self, app):
        self.app = app

    ################
    # APPLICATIONS #
    ################
    async def create_application(self, payload: more_typing.JSONObject) -> applications.Application:
        application = applications.Application()

        application.name = payload["name"]
        application.description = payload["description"]
        application.is_bot_public = payload.get("bot_public")
        application.is_bot_code_grant_required = payload.get("bot_require_code_grant")
        application.summary = payload["summary"]
        application.slug = payload.get("slug")
        application.cover_image_hash = payload.get("cover_image")

        if "guild_id" in payload:
            application.guild_id = bases.Snowflake(application["guild_id"])

        if "primary_sku_id" in payload:
            application.primary_sku_id = bases.Snowflake(application["primary_sku_id"])

        if "rpc_origins" in payload:
            application.rpc_origins = set(payload.get("rpc_origins"))

        if "verify_key" in payload:
            application.verify_key = bytes(payload["verify_key"], "utf-8")

        if "owner" in payload:
            application.owner = self._make_user(payload["owner"])

        if (raw_team := payload.get("team")) is not None:
            team = applications.Team()
            team.id = bases.Snowflake(raw_team["id"])
            team.icon_hash = raw_team.get("icon_hash")
            team.owner_user_id = bases.Snowflake(raw_team["owner_user_id"])

            team.members = {}
            for raw_member in raw_team["members"]:
                member = applications.TeamMember()
                member.team_id = team.id
                member.user = self._make_user(raw_member["user"])
                member.permissions = set(raw_member["permissions"])
                member.membership_state = applications.TeamMembershipState(raw_member["membership_state"])

        return application

    async def create_own_guild(self, payload: more_typing.JSONObject) -> applications.OwnGuild:
        ...

    async def create_own_connection(self, payload: more_typing.JSONObject) -> applications.OwnConnection:
        ...

    ##############
    # AUDIT LOGS #
    ##############

    async def create_audit_log_change(self, payload: more_typing.JSONObject) -> audit_logs.AuditLogChange:
        ...

    async def create_audit_log_entry_info(self, payload: more_typing.JSONObject) -> audit_logs.BaseAuditLogEntryInfo:
        ...

    async def create_audit_log_entry(self, payload: more_typing.JSONObject) -> audit_logs.AuditLogEntry:
        ...

    async def create_audit_log(self, payload: more_typing.JSONObject) -> audit_logs.AuditLog:
        ...

    ############
    # CHANNELS #
    ############

    async def create_channel(self, payload: more_typing.JSONObject, can_cache: bool = False) -> channels.PartialChannel:
        ...

    async def update_channel(
        self, channel: channels.PartialChannel, payload: more_typing.JSONObject,
    ) -> channels.PartialChannel:
        ...

    async def get_channel(self, channel_id: int) -> typing.Optional[channels.PartialChannel]:
        ...

    async def delete_channel(self, channel_id: int) -> typing.Optional[channels.PartialChannel]:
        ...

    ##########
    # EMBEDS #
    ##########

    async def create_embed(self, payload: more_typing.JSONObject) -> embeds.Embed:
        ...

    ##########
    # EMOJIS #
    ##########

    async def create_emoji(self, payload: more_typing.JSONObject, can_cache: bool = False) -> emojis.Emoji:
        ...

    async def update_emoji(self, payload: more_typing.JSONObject) -> emojis.Emoji:
        ...

    async def get_emoji(self, emoji_id: int) -> typing.Optional[emojis.KnownCustomEmoji]:
        ...

    async def delete_emoji(self, emoji_id: int) -> typing.Optional[emojis.KnownCustomEmoji]:
        ...

    ###########
    # GATEWAY #
    ###########

    async def create_gateway_bot(self, payload: more_typing.JSONObject) -> gateway.GatewayBot:
        ...

    ##########
    # GUILDS #
    ##########

    async def create_member(self, payload: more_typing.JSONObject, can_cache: bool = False) -> guilds.GuildMember:
        # TODO: revisit for the voodoo to make a member into a special user.
        ...

    async def update_member(self, member: guilds.GuildMember, payload: more_typing.JSONObject) -> guilds.GuildMember:
        ...

    async def get_member(self, guild_id: int, user_id: int) -> typing.Optional[guilds.GuildMember]:
        ...

    async def delete_member(self, guild_id: int, user_id: int) -> typing.Optional[guilds.GuildMember]:
        ...

    async def create_role(self, payload: more_typing.JSONObject, can_cache: bool = False) -> guilds.PartialGuildRole:
        ...

    async def update_role(
        self, role: guilds.PartialGuildRole, payload: more_typing.JSONObject
    ) -> guilds.PartialGuildRole:
        ...

    async def get_role(self, guild_id: int, role_id: int) -> typing.Optional[guilds.PartialGuildRole]:
        ...

    async def delete_role(self, guild_id: int, role_id: int) -> typing.Optional[guilds.PartialGuildRole]:
        ...

    async def create_presence(
        self, payload: more_typing.JSONObject, can_cache: bool = False
    ) -> guilds.GuildMemberPresence:
        ...

    async def update_presence(
        self, role: guilds.GuildMemberPresence, payload: more_typing.JSONObject
    ) -> guilds.GuildMemberPresence:
        ...

    async def get_presence(self, guild_id: int, user_id: int) -> typing.Optional[guilds.GuildMemberPresence]:
        ...

    async def delete_presence(self, guild_id: int, user_id: int) -> typing.Optional[guilds.GuildMemberPresence]:
        ...

    async def create_guild_ban(self, payload: more_typing.JSONObject) -> guilds.GuildMemberBan:
        ...

    async def create_guild_integration(self, payload: more_typing.JSONObject) -> guilds.PartialGuildIntegration:
        ...

    async def create_guild(self, payload: more_typing.JSONObject, can_cache: bool = False) -> guilds.PartialGuild:
        ...

    async def update_guild(self, guild: guilds.PartialGuild, payload: more_typing.JSONObject) -> guilds.PartialGuild:
        ...

    async def get_guild(self, guild_id: int) -> typing.Optional[guilds.PartialGuild]:
        ...

    async def delete_guild(self, guild_id: int) -> typing.Optional[guilds.PartialGuild]:
        ...

    async def create_guild_preview(self, payload: more_typing.JSONObject) -> guilds.GuildPreview:
        ...

    ###########
    # INVITES #
    ###########
    async def create_invite(self, payload: more_typing.JSONObject) -> invites.Invite:
        ...

    ############
    # MESSAGES #
    ############
    async def create_reaction(self, payload: more_typing.JSONObject) -> messages.Reaction:
        ...

    async def create_message(self, payload: more_typing.JSONObject, can_cache: bool = False) -> messages.Message:
        ...

    async def update_message(self, message: messages.Message, payload: more_typing.JSONObject) -> messages.Message:
        ...

    async def get_message(self, channel_id: int, message_id: int) -> typing.Optional[messages.Message]:
        ...

    async def delete_message(self, channel_id: int, message_id: int) -> typing.Optional[messages.Message]:
        ...

    #########
    # USERS #
    #########
    async def create_user(self, payload: more_typing.JSONObject, can_cache: bool = False) -> users.User:
        return self._make_user(payload)

    @abc.abstractmethod
    async def update_user(self, user: users.User, payload: more_typing.JSONObject) -> users.User:
        ...

    @abc.abstractmethod
    async def get_user(self, user_id: int) -> typing.Optional[users.User]:
        ...

    @abc.abstractmethod
    async def delete_user(self, user_id: int) -> typing.Optional[users.User]:
        ...

    @abc.abstractmethod
    async def create_my_user(self, payload: more_typing.JSONObject, can_cache: bool = False) -> users.MyUser:
        ...

    @abc.abstractmethod
    async def update_my_user(self, my_user: users.MyUser, payload: more_typing.JSONObject) -> users.MyUser:
        ...

    @abc.abstractmethod
    async def get_my_user(self) -> typing.Optional[users.User]:
        ...

    ##########
    # VOICES #
    ##########
    @abc.abstractmethod
    async def create_voice_state(self, payload: more_typing.JSONObject, can_cache: bool = False) -> voices.VoiceState:
        ...

    @abc.abstractmethod
    async def update_voice_state(self, payload: more_typing.JSONObject) -> voices.VoiceState:
        ...

    @abc.abstractmethod
    async def get_voice_state(self, guild_id: int, channel_id: int) -> typing.Optional[voices.VoiceState]:
        ...

    @abc.abstractmethod
    async def delete_voice_state(self, guild_id: int, channel_id: int) -> typing.Optional[voices.VoiceState]:
        ...

    @abc.abstractmethod
    async def create_voice_region(self, payload: more_typing.JSONObject) -> voices.VoiceRegion:
        ...

    ############
    # WEBHOOKS #
    ############
    @abc.abstractmethod
    async def create_webhook(self, payload: more_typing.JSONObject) -> webhooks.Webhook:
        ...

    def _make_user(self, payload):
        user_obj = users.User(app=self.app)
        user_obj.id = bases.Snowflake(payload["id"])
        user_obj.discriminator = payload["discriminator"]
        user_obj.username = payload["username"]
        user_obj.avatar_hash = payload["avatar"]
        user_obj.is_bot = payload.get("bot", False)
        user_obj.is_system = payload.get("system", False)
        user_obj.flags = payload.get("bot", False)
        return user_obj
