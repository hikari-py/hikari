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

import typing

from hikari import entity_factory

if typing.TYPE_CHECKING:
    from hikari import app as app_
    from hikari.internal import more_typing
    from hikari.models import applications
    from hikari.models import audit_logs
    from hikari.models import channels
    from hikari.models import embeds
    from hikari.models import emojis
    from hikari.models import gateway
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

    def deserialize_own_connection(self, payload: more_typing.JSONObject) -> applications.OwnConnection:
        pass

    def deserialize_own_guild(self, payload: more_typing.JSONObject) -> applications.OwnGuild:
        pass

    def deserialize_application(self, payload: more_typing.JSONObject) -> applications:
        pass

    def deserialize_audit_log(self, payload: more_typing.JSONObject) -> audit_logs.AuditLog:
        pass

    def deserialize_permission_overwrite(self, payload: more_typing.JSONObject) -> channels.PermissionOverwrite:
        pass

    def serialize_permission_overwrite(self, overwrite: channels.PermissionOverwrite) -> more_typing.JSONObject:
        pass

    def deserialize_partial_channel(self, payload: more_typing.JSONObject) -> channels.PartialChannel:
        pass

    def deserialize_dm_channel(self, payload: more_typing.JSONObject) -> channels.DMChannel:
        pass

    def deserialize_group_dm_channel(self, payload: more_typing.JSONObject) -> channels.GroupDMChannel:
        pass

    def deserialize_guild_category(self, payload: more_typing.JSONObject) -> channels.GuildCategory:
        pass

    def deserialize_guild_text_channel(self, payload: more_typing.JSONObject) -> channels.GuildTextChannel:
        pass

    def deserialize_guild_news_channel(self, payload: more_typing.JSONObject) -> channels.GuildNewsChannel:
        pass

    def deserialize_guild_store_channel(self, payload: more_typing.JSONObject) -> channels.GuildStoreChannel:
        pass

    def deserialize_guild_voice_channel(self, payload: more_typing.JSONObject) -> channels.GuildVoiceChannel:
        pass

    def deserialize_channel(self, payload: more_typing.JSONObject) -> channels.PartialChannel:
        pass

    def deserialize_embed(self, payload: more_typing.JSONObject) -> embeds.Embed:
        pass

    def serialize_embed(self, embed: embeds.Embed) -> more_typing.JSONObject:
        pass

    def deserialize_unicode_emoji(self, payload: more_typing.JSONObject) -> emojis.UnicodeEmoji:
        pass

    def deserialize_custom_emoji(self, payload: more_typing.JSONObject) -> emojis.CustomEmoji:
        pass

    def deserialize_known_custom_emoji(self, payload: more_typing.JSONObject) -> emojis.KnownCustomEmoji:
        pass

    def deserialize_emoji(
        self, payload: more_typing.JSONObject
    ) -> typing.Union[emojis.UnicodeEmoji, emojis.CustomEmoji]:
        pass

    def deserialize_gateway_bot(self, payload: more_typing.JSONObject) -> gateway.GatewayBot:
        pass

    def deserialize_guild_widget(self, payload: more_typing.JSONObject) -> guilds.GuildWidget:
        pass

    def deserialize_guild_member(
        self, payload: more_typing.JSONObject, *, user: typing.Optional[users.User] = None
    ) -> guilds.GuildMember:
        pass

    def deserialize_role(self, payload: more_typing.JSONObject) -> guilds.Role:
        pass

    def deserialize_guild_member_presence(self, payload: more_typing.JSONObject) -> guilds.GuildMemberPresence:
        pass

    def deserialize_partial_guild_integration(self, payload: more_typing.JSONObject) -> guilds.PartialGuildIntegration:
        pass

    def deserialize_guild_integration(self, payload: more_typing.JSONObject) -> guilds.GuildIntegration:
        pass

    def deserialize_guild_member_ban(self, payload: more_typing.JSONObject) -> guilds.GuildMemberBan:
        pass

    def deserialize_unavailable_guild(self, payload: more_typing.JSONObject) -> guilds.UnavailableGuild:
        pass

    def deserialize_guild_preview(self, payload: more_typing.JSONObject) -> guilds.GuildPreview:
        pass

    def deserialize_guild(self, payload: more_typing.JSONObject) -> guilds.Guild:
        pass

    def deserialize_vanity_url(self, payload: more_typing.JSONObject) -> invites.VanityURL:
        pass

    def deserialize_invite(self, payload: more_typing.JSONObject) -> invites.Invite:
        pass

    def deserialize_invite_with_metadata(self, payload: more_typing.JSONObject) -> invites.InviteWithMetadata:
        pass

    def deserialize_user(self, payload: more_typing.JSONObject) -> users.User:
        pass

    def deserialize_my_user(self, payload: more_typing.JSONObject) -> users.MyUser:
        pass

    def deserialize_voice_state(self, payload: more_typing.JSONObject) -> voices.VoiceState:
        pass

    def deserialize_voice_region(self, payload: more_typing.JSONObject) -> voices.VoiceRegion:
        pass

    def deserialize_webhook(self, payload: more_typing.JSONObject) -> webhooks.Webhook:
        pass
