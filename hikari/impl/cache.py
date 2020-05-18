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
import typing

from hikari.api import cache
from hikari.internal import more_typing
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


class CacheImpl(cache.ICache):
    async def create_application(self, payload: more_typing.JSONObject) -> applications.Application:
        pass

    async def create_own_guild(self, payload: more_typing.JSONObject) -> applications.OwnGuild:
        pass

    async def create_own_connection(self, payload: more_typing.JSONObject) -> applications.OwnConnection:
        pass

    async def create_audit_log_change(self, payload: more_typing.JSONObject) -> audit_logs.AuditLogChange:
        pass

    async def create_audit_log_entry_info(self, payload: more_typing.JSONObject) -> audit_logs.BaseAuditLogEntryInfo:
        pass

    async def create_audit_log_entry(self, payload: more_typing.JSONObject) -> audit_logs.AuditLogEntry:
        pass

    async def create_audit_log(self, payload: more_typing.JSONObject) -> audit_logs.AuditLog:
        pass

    async def create_channel(self, payload: more_typing.JSONObject, can_cache: bool = False) -> channels.PartialChannel:
        pass

    async def update_channel(
        self, channel: channels.PartialChannel, payload: more_typing.JSONObject
    ) -> channels.PartialChannel:
        pass

    async def get_channel(self, channel_id: int) -> typing.Optional[channels.PartialChannel]:
        pass

    async def delete_channel(self, channel_id: int) -> typing.Optional[channels.PartialChannel]:
        pass

    async def create_embed(self, payload: more_typing.JSONObject) -> embeds.Embed:
        pass

    async def create_emoji(self, payload: more_typing.JSONObject, can_cache: bool = False) -> emojis.Emoji:
        pass

    async def update_emoji(self, payload: more_typing.JSONObject) -> emojis.Emoji:
        pass

    async def get_emoji(self, emoji_id: int) -> typing.Optional[emojis.KnownCustomEmoji]:
        pass

    async def delete_emoji(self, emoji_id: int) -> typing.Optional[emojis.KnownCustomEmoji]:
        pass

    async def create_gateway_bot(self, payload: more_typing.JSONObject) -> gateway.GatewayBot:
        pass

    async def create_member(self, payload: more_typing.JSONObject, can_cache: bool = False) -> guilds.GuildMember:
        pass

    async def update_member(self, member: guilds.GuildMember, payload: more_typing.JSONObject) -> guilds.GuildMember:
        pass

    async def get_member(self, guild_id: int, user_id: int) -> typing.Optional[guilds.GuildMember]:
        pass

    async def delete_member(self, guild_id: int, user_id: int) -> typing.Optional[guilds.GuildMember]:
        pass

    async def create_role(self, payload: more_typing.JSONObject, can_cache: bool = False) -> guilds.PartialGuildRole:
        pass

    async def update_role(
        self, role: guilds.PartialGuildRole, payload: more_typing.JSONObject
    ) -> guilds.PartialGuildRole:
        pass

    async def get_role(self, guild_id: int, role_id: int) -> typing.Optional[guilds.PartialGuildRole]:
        pass

    async def delete_role(self, guild_id: int, role_id: int) -> typing.Optional[guilds.PartialGuildRole]:
        pass

    async def create_presence(
        self, payload: more_typing.JSONObject, can_cache: bool = False
    ) -> guilds.GuildMemberPresence:
        pass

    async def update_presence(
        self, role: guilds.GuildMemberPresence, payload: more_typing.JSONObject
    ) -> guilds.GuildMemberPresence:
        pass

    async def get_presence(self, guild_id: int, user_id: int) -> typing.Optional[guilds.GuildMemberPresence]:
        pass

    async def delete_presence(self, guild_id: int, user_id: int) -> typing.Optional[guilds.GuildMemberPresence]:
        pass

    async def create_guild_ban(self, payload: more_typing.JSONObject) -> guilds.GuildMemberBan:
        pass

    async def create_guild_integration(self, payload: more_typing.JSONObject) -> guilds.PartialGuildIntegration:
        pass

    async def create_guild(self, payload: more_typing.JSONObject, can_cache: bool = False) -> guilds.PartialGuild:
        pass

    async def update_guild(self, guild: guilds.PartialGuild, payload: more_typing.JSONObject) -> guilds.PartialGuild:
        pass

    async def get_guild(self, guild_id: int) -> typing.Optional[guilds.PartialGuild]:
        pass

    async def delete_guild(self, guild_id: int) -> typing.Optional[guilds.PartialGuild]:
        pass

    async def create_guild_preview(self, payload: more_typing.JSONObject) -> guilds.GuildPreview:
        pass

    async def create_invite(self, payload: more_typing.JSONObject) -> invites.Invite:
        pass

    async def create_reaction(self, payload: more_typing.JSONObject) -> messages.Reaction:
        pass

    async def create_message(self, payload: more_typing.JSONObject, can_cache: bool = False) -> messages.Message:
        pass

    async def update_message(self, message: messages.Message, payload: more_typing.JSONObject) -> messages.Message:
        pass

    async def get_message(self, channel_id: int, message_id: int) -> typing.Optional[messages.Message]:
        pass

    async def delete_message(self, channel_id: int, message_id: int) -> typing.Optional[messages.Message]:
        pass

    async def create_user(self, payload: more_typing.JSONObject, can_cache: bool = False) -> users.User:
        pass

    async def update_user(self, user: users.User, payload: more_typing.JSONObject) -> users.User:
        pass

    async def get_user(self, user_id: int) -> typing.Optional[users.User]:
        pass

    async def delete_user(self, user_id: int) -> typing.Optional[users.User]:
        pass

    async def create_my_user(self, payload: more_typing.JSONObject, can_cache: bool = False) -> users.MyUser:
        pass

    async def update_my_user(self, my_user: users.MyUser, payload: more_typing.JSONObject) -> users.MyUser:
        pass

    async def get_my_user(self) -> typing.Optional[users.User]:
        pass

    async def create_voice_state(self, payload: more_typing.JSONObject, can_cache: bool = False) -> voices.VoiceState:
        pass

    async def update_voice_state(self, payload: more_typing.JSONObject) -> voices.VoiceState:
        pass

    async def get_voice_state(self, guild_id: int, channel_id: int) -> typing.Optional[voices.VoiceState]:
        pass

    async def delete_voice_state(self, guild_id: int, channel_id: int) -> typing.Optional[voices.VoiceState]:
        pass

    async def create_voice_region(self, payload: more_typing.JSONObject) -> voices.VoiceRegion:
        pass
