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
"""Basic implementation of an entity factory for general bots and REST apps."""

from __future__ import annotations

__all__ = ["EntityFactoryImpl"]

import datetime
import typing

from hikari import entity_factory
from hikari.models import gateway
from hikari.utilities import binding

if typing.TYPE_CHECKING:
    from hikari import app as app_
    from hikari.models import applications
    from hikari.models import audit_logs
    from hikari.models import channels
    from hikari.models import embeds
    from hikari.models import emojis
    from hikari.models import guilds
    from hikari.models import invites
    from hikari.models import users
    from hikari.models import voices
    from hikari.models import webhooks


class EntityFactoryImpl(entity_factory.IEntityFactory):
    def __init__(self, app: app_.IApp) -> None:
        self._app = app

    @property
    def app(self) -> app_.IApp:
        return self._app

    def deserialize_own_connection(self, payload: binding.JSONObject) -> applications.OwnConnection:
        pass

    def deserialize_own_guild(self, payload: binding.JSONObject) -> applications.OwnGuild:
        pass

    def deserialize_application(self, payload: binding.JSONObject) -> applications:
        pass

    def deserialize_audit_log(self, payload: binding.JSONObject) -> audit_logs.AuditLog:
        pass

    def deserialize_permission_overwrite(self, payload: binding.JSONObject) -> channels.PermissionOverwrite:
        pass

    def serialize_permission_overwrite(self, overwrite: channels.PermissionOverwrite) -> binding.JSONObject:
        pass

    def deserialize_partial_channel(self, payload: binding.JSONObject) -> channels.PartialChannel:
        pass

    def deserialize_dm_channel(self, payload: binding.JSONObject) -> channels.DMChannel:
        pass

    def deserialize_group_dm_channel(self, payload: binding.JSONObject) -> channels.GroupDMChannel:
        pass

    def deserialize_guild_category(self, payload: binding.JSONObject) -> channels.GuildCategory:
        pass

    def deserialize_guild_text_channel(self, payload: binding.JSONObject) -> channels.GuildTextChannel:
        pass

    def deserialize_guild_news_channel(self, payload: binding.JSONObject) -> channels.GuildNewsChannel:
        pass

    def deserialize_guild_store_channel(self, payload: binding.JSONObject) -> channels.GuildStoreChannel:
        pass

    def deserialize_guild_voice_channel(self, payload: binding.JSONObject) -> channels.GuildVoiceChannel:
        pass

    def deserialize_channel(self, payload: binding.JSONObject) -> channels.PartialChannel:
        pass

    def deserialize_embed(self, payload: binding.JSONObject) -> embeds.Embed:
        pass

    def serialize_embed(self, embed: embeds.Embed) -> binding.JSONObject:
        pass

    def deserialize_unicode_emoji(self, payload: binding.JSONObject) -> emojis.UnicodeEmoji:
        pass

    def deserialize_custom_emoji(self, payload: binding.JSONObject) -> emojis.CustomEmoji:
        pass

    def deserialize_known_custom_emoji(self, payload: binding.JSONObject) -> emojis.KnownCustomEmoji:
        pass

    def deserialize_emoji(self, payload: binding.JSONObject) -> typing.Union[emojis.UnicodeEmoji, emojis.CustomEmoji]:
        pass

    def deserialize_gateway_bot(self, payload: binding.JSONObject) -> gateway.GatewayBot:
        gateway_bot = gateway.GatewayBot()
        gateway_bot.url = payload["url"]
        gateway_bot.shard_count = int(payload["shards"])
        session_start_limit_payload = payload["session_start_limit"]
        session_start_limit = gateway.SessionStartLimit()
        session_start_limit.total = int(session_start_limit_payload["total"])
        session_start_limit.remaining = int(session_start_limit_payload["remaining"])
        session_start_limit.reset_after = datetime.timedelta(milliseconds=session_start_limit_payload["reset_after"])
        gateway_bot.session_start_limit = session_start_limit
        return gateway_bot

    def deserialize_guild_widget(self, payload: binding.JSONObject) -> guilds.GuildWidget:
        pass

    def deserialize_guild_member(
        self, payload: binding.JSONObject, *, user: typing.Optional[users.User] = None
    ) -> guilds.GuildMember:
        pass

    def deserialize_role(self, payload: binding.JSONObject) -> guilds.Role:
        pass

    def deserialize_guild_member_presence(self, payload: binding.JSONObject) -> guilds.GuildMemberPresence:
        pass

    def deserialize_partial_guild_integration(self, payload: binding.JSONObject) -> guilds.PartialGuildIntegration:
        pass

    def deserialize_guild_integration(self, payload: binding.JSONObject) -> guilds.GuildIntegration:
        pass

    def deserialize_guild_member_ban(self, payload: binding.JSONObject) -> guilds.GuildMemberBan:
        pass

    def deserialize_unavailable_guild(self, payload: binding.JSONObject) -> guilds.UnavailableGuild:
        pass

    def deserialize_guild_preview(self, payload: binding.JSONObject) -> guilds.GuildPreview:
        pass

    def deserialize_guild(self, payload: binding.JSONObject) -> guilds.Guild:
        pass

    def deserialize_vanity_url(self, payload: binding.JSONObject) -> invites.VanityURL:
        pass

    def deserialize_invite(self, payload: binding.JSONObject) -> invites.Invite:
        pass

    def deserialize_invite_with_metadata(self, payload: binding.JSONObject) -> invites.InviteWithMetadata:
        pass

    def deserialize_user(self, payload: binding.JSONObject) -> users.User:
        pass

    def deserialize_my_user(self, payload: binding.JSONObject) -> users.MyUser:
        pass

    def deserialize_voice_state(self, payload: binding.JSONObject) -> voices.VoiceState:
        pass

    def deserialize_voice_region(self, payload: binding.JSONObject) -> voices.VoiceRegion:
        pass

    def deserialize_webhook(self, payload: binding.JSONObject) -> webhooks.Webhook:
        pass
