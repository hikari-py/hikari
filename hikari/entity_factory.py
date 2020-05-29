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
"""Contains an interface for components wishing to build entities."""
from __future__ import annotations

__all__ = ["IEntityFactory"]

import abc
import typing

from hikari import component

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

    from hikari.utilities import binding


class IEntityFactory(component.IComponent, abc.ABC):
    """Component that will serialize and deserialize JSON payloads."""

    __slots__ = ()

    ################
    # APPLICATIONS #
    ################

    @abc.abstractmethod
    def deserialize_own_connection(self, payload: binding.JSONObject) -> applications.OwnConnection:
        ...

    @abc.abstractmethod
    def deserialize_own_guild(self, payload: binding.JSONObject) -> applications.OwnGuild:
        ...

    @abc.abstractmethod
    def deserialize_application(self, payload: binding.JSONObject) -> applications:
        ...

    ##############
    # AUDIT_LOGS #
    ##############

    @abc.abstractmethod
    def deserialize_audit_log(self, payload: binding.JSONObject) -> audit_logs.AuditLog:
        ...

    ############
    # CHANNELS #
    ############

    @abc.abstractmethod
    def deserialize_permission_overwrite(self, payload: binding.JSONObject) -> channels.PermissionOverwrite:
        ...

    @abc.abstractmethod
    def serialize_permission_overwrite(self, overwrite: channels.PermissionOverwrite) -> binding.JSONObject:
        ...

    @abc.abstractmethod
    def deserialize_partial_channel(self, payload: binding.JSONObject) -> channels.PartialChannel:
        ...

    @abc.abstractmethod
    def deserialize_dm_channel(self, payload: binding.JSONObject) -> channels.DMChannel:
        ...

    @abc.abstractmethod
    def deserialize_group_dm_channel(self, payload: binding.JSONObject) -> channels.GroupDMChannel:
        ...

    @abc.abstractmethod
    def deserialize_guild_category(self, payload: binding.JSONObject) -> channels.GuildCategory:
        ...

    @abc.abstractmethod
    def deserialize_guild_text_channel(self, payload: binding.JSONObject) -> channels.GuildTextChannel:
        ...

    @abc.abstractmethod
    def deserialize_guild_news_channel(self, payload: binding.JSONObject) -> channels.GuildNewsChannel:
        ...

    @abc.abstractmethod
    def deserialize_guild_store_channel(self, payload: binding.JSONObject) -> channels.GuildStoreChannel:
        ...

    @abc.abstractmethod
    def deserialize_guild_voice_channel(self, payload: binding.JSONObject) -> channels.GuildVoiceChannel:
        ...

    @abc.abstractmethod
    def deserialize_channel(self, payload: binding.JSONObject) -> channels.PartialChannel:
        ...

    ##########
    # EMBEDS #
    ##########

    @abc.abstractmethod
    def deserialize_embed(self, payload: binding.JSONObject) -> embeds.Embed:
        ...

    @abc.abstractmethod
    def serialize_embed(self, embed: embeds.Embed) -> binding.JSONObject:
        ...

    ##########
    # EMOJIS #
    ##########

    @abc.abstractmethod
    def deserialize_unicode_emoji(self, payload: binding.JSONObject) -> emojis.UnicodeEmoji:
        ...

    @abc.abstractmethod
    def deserialize_custom_emoji(self, payload: binding.JSONObject) -> emojis.CustomEmoji:
        ...

    @abc.abstractmethod
    def deserialize_known_custom_emoji(self, payload: binding.JSONObject) -> emojis.KnownCustomEmoji:
        ...

    @abc.abstractmethod
    def deserialize_emoji(self, payload: binding.JSONObject) -> typing.Union[emojis.UnicodeEmoji, emojis.CustomEmoji]:
        ...

    ###########
    # GATEWAY #
    ###########

    @abc.abstractmethod
    def deserialize_gateway_bot(self, payload: binding.JSONObject) -> gateway.GatewayBot:
        ...

    ##########
    # GUILDS #
    ##########

    @abc.abstractmethod
    def deserialize_guild_widget(self, payload: binding.JSONObject) -> guilds.GuildWidget:
        ...

    @abc.abstractmethod
    def deserialize_guild_member(
        self, payload: binding.JSONObject, *, user: typing.Optional[users.User] = None
    ) -> guilds.GuildMember:
        ...

    @abc.abstractmethod
    def deserialize_role(self, payload: binding.JSONObject) -> guilds.Role:
        ...

    @abc.abstractmethod
    def deserialize_guild_member_presence(self, payload: binding.JSONObject) -> guilds.GuildMemberPresence:
        ...

    @abc.abstractmethod
    def deserialize_partial_guild_integration(self, payload: binding.JSONObject) -> guilds.PartialGuildIntegration:
        ...

    @abc.abstractmethod
    def deserialize_guild_integration(self, payload: binding.JSONObject) -> guilds.GuildIntegration:
        ...

    @abc.abstractmethod
    def deserialize_guild_member_ban(self, payload: binding.JSONObject) -> guilds.GuildMemberBan:
        ...

    @abc.abstractmethod
    def deserialize_unavailable_guild(self, payload: binding.JSONObject) -> guilds.UnavailableGuild:
        ...

    @abc.abstractmethod
    def deserialize_guild_preview(self, payload: binding.JSONObject) -> guilds.GuildPreview:
        ...

    @abc.abstractmethod
    def deserialize_guild(self, payload: binding.JSONObject) -> guilds.Guild:
        ...

    ###########
    # INVITES #
    ###########

    @abc.abstractmethod
    def deserialize_vanity_url(self, payload: binding.JSONObject) -> invites.VanityURL:
        ...

    @abc.abstractmethod
    def deserialize_invite(self, payload: binding.JSONObject) -> invites.Invite:
        ...

    @abc.abstractmethod
    def deserialize_invite_with_metadata(self, payload: binding.JSONObject) -> invites.InviteWithMetadata:
        ...

    ############
    # MESSAGES #
    ############

    def deserialize_message(self, payload: binding.JSONObject) -> messages.Message:
        ...

    #########
    # USERS #
    #########

    @abc.abstractmethod
    def deserialize_user(self, payload: binding.JSONObject) -> users.User:
        ...

    @abc.abstractmethod
    def deserialize_my_user(self, payload: binding.JSONObject) -> users.MyUser:
        ...

    ##########
    # Voices #
    ##########

    @abc.abstractmethod
    def deserialize_voice_state(self, payload: binding.JSONObject) -> voices.VoiceState:
        ...

    @abc.abstractmethod
    def deserialize_voice_region(self, payload: binding.JSONObject) -> voices.VoiceRegion:
        ...

    ############
    # WEBHOOKS #
    ############

    @abc.abstractmethod
    def deserialize_webhook(self, payload: binding.JSONObject) -> webhooks.Webhook:
        ...
