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
"""Basic implementation of a cache for general bots and gateway apps."""

from __future__ import annotations

__all__ = ["CacheImpl"]

import typing

from hikari.api import cache
from hikari.utilities import data_binding

if typing.TYPE_CHECKING:
    from hikari.api import app as app_
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
    def __init__(self, app: app_.IApp) -> None:
        self._app = app

    @property
    def app(self) -> app_.IApp:
        return self._app

    async def create_application(self, payload: data_binding.JSONObject) -> applications.Application:
        pass

    async def create_own_guild(self, payload: data_binding.JSONObject) -> applications.OwnGuild:
        pass

    async def create_own_connection(self, payload: data_binding.JSONObject) -> applications.OwnConnection:
        pass

    async def create_audit_log_change(self, payload: data_binding.JSONObject) -> audit_logs.AuditLogChange:
        pass

    async def create_audit_log_entry_info(self, payload: data_binding.JSONObject) -> audit_logs.BaseAuditLogEntryInfo:
        pass

    async def create_audit_log_entry(self, payload: data_binding.JSONObject) -> audit_logs.AuditLogEntry:
        pass

    async def create_audit_log(self, payload: data_binding.JSONObject) -> audit_logs.AuditLog:
        pass

    async def create_channel(
        self, payload: data_binding.JSONObject, can_cache: bool = False
    ) -> channels.PartialChannel:
        pass

    async def update_channel(
        self, channel: channels.PartialChannel, payload: data_binding.JSONObject
    ) -> channels.PartialChannel:
        pass

    async def get_channel(self, channel_id: int) -> typing.Optional[channels.PartialChannel]:
        pass

    async def delete_channel(self, channel_id: int) -> typing.Optional[channels.PartialChannel]:
        pass

    async def create_embed(self, payload: data_binding.JSONObject) -> embeds.Embed:
        pass

    async def create_emoji(self, payload: data_binding.JSONObject, can_cache: bool = False) -> emojis.Emoji:
        pass

    async def update_emoji(self, payload: data_binding.JSONObject) -> emojis.Emoji:
        pass

    async def get_emoji(self, emoji_id: int) -> typing.Optional[emojis.KnownCustomEmoji]:
        pass

    async def delete_emoji(self, emoji_id: int) -> typing.Optional[emojis.KnownCustomEmoji]:
        pass

    async def create_gateway_bot(self, payload: data_binding.JSONObject) -> gateway.GatewayBot:
        pass

    async def create_member(self, payload: data_binding.JSONObject, can_cache: bool = False) -> guilds.Member:
        pass

    async def update_member(self, member: guilds.Member, payload: data_binding.JSONObject) -> guilds.Member:
        pass

    async def get_member(self, guild_id: int, user_id: int) -> typing.Optional[guilds.Member]:
        pass

    async def delete_member(self, guild_id: int, user_id: int) -> typing.Optional[guilds.Member]:
        pass

    async def create_role(self, payload: data_binding.JSONObject, can_cache: bool = False) -> guilds.PartialRole:
        pass

    async def update_role(self, role: guilds.PartialRole, payload: data_binding.JSONObject) -> guilds.PartialRole:
        pass

    async def get_role(self, guild_id: int, role_id: int) -> typing.Optional[guilds.PartialRole]:
        pass

    async def delete_role(self, guild_id: int, role_id: int) -> typing.Optional[guilds.PartialRole]:
        pass

    async def create_presence(self, payload: data_binding.JSONObject, can_cache: bool = False) -> guilds.MemberPresence:
        pass

    async def update_presence(
        self, role: guilds.MemberPresence, payload: data_binding.JSONObject
    ) -> guilds.MemberPresence:
        pass

    async def get_presence(self, guild_id: int, user_id: int) -> typing.Optional[guilds.MemberPresence]:
        pass

    async def delete_presence(self, guild_id: int, user_id: int) -> typing.Optional[guilds.MemberPresence]:
        pass

    async def create_guild_ban(self, payload: data_binding.JSONObject) -> guilds.GuildMemberBan:
        pass

    async def create_integration(self, payload: data_binding.JSONObject) -> guilds.PartialIntegration:
        pass

    async def create_guild(self, payload: data_binding.JSONObject, can_cache: bool = False) -> guilds.PartialGuild:
        pass

    async def update_guild(self, guild: guilds.PartialGuild, payload: data_binding.JSONObject) -> guilds.PartialGuild:
        pass

    async def get_guild(self, guild_id: int) -> typing.Optional[guilds.PartialGuild]:
        pass

    async def delete_guild(self, guild_id: int) -> typing.Optional[guilds.PartialGuild]:
        pass

    async def create_guild_preview(self, payload: data_binding.JSONObject) -> guilds.GuildPreview:
        pass

    async def create_invite(self, payload: data_binding.JSONObject) -> invites.Invite:
        pass

    async def create_reaction(self, payload: data_binding.JSONObject) -> messages.Reaction:
        pass

    async def create_message(self, payload: data_binding.JSONObject, can_cache: bool = False) -> messages.Message:
        pass

    async def update_message(self, message: messages.Message, payload: data_binding.JSONObject) -> messages.Message:
        pass

    async def get_message(self, channel_id: int, message_id: int) -> typing.Optional[messages.Message]:
        pass

    async def delete_message(self, channel_id: int, message_id: int) -> typing.Optional[messages.Message]:
        pass

    async def create_user(self, payload: data_binding.JSONObject, can_cache: bool = False) -> users.User:
        pass

    async def update_user(self, user: users.User, payload: data_binding.JSONObject) -> users.User:
        pass

    async def get_user(self, user_id: int) -> typing.Optional[users.User]:
        pass

    async def delete_user(self, user_id: int) -> typing.Optional[users.User]:
        pass

    async def create_my_user(self, payload: data_binding.JSONObject, can_cache: bool = False) -> users.OwnUser:
        pass

    async def update_my_user(self, my_user: users.OwnUser, payload: data_binding.JSONObject) -> users.OwnUser:
        pass

    async def get_my_user(self) -> typing.Optional[users.User]:
        pass

    async def create_voice_state(self, payload: data_binding.JSONObject, can_cache: bool = False) -> voices.VoiceState:
        pass

    async def update_voice_state(self, payload: data_binding.JSONObject) -> voices.VoiceState:
        pass

    async def get_voice_state(self, guild_id: int, channel_id: int) -> typing.Optional[voices.VoiceState]:
        pass

    async def delete_voice_state(self, guild_id: int, channel_id: int) -> typing.Optional[voices.VoiceState]:
        pass

    async def create_voice_region(self, payload: data_binding.JSONObject) -> voices.VoiceRegion:
        pass
