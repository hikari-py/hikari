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
"""Utilities to handle cache management."""
from __future__ import annotations

__all__ = ["ICache"]

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

    from hikari.utilities import binding


class ICache(component.IComponent, abc.ABC):
    """Component that implements entity caching facilities.

    This will be used by the gateway and REST API to cache specific types of
    objects that the application should attempt to remember for later, depending
    on how this is implemented.

    The implementation may choose to use a simple in-memory collection of
    objects, or may decide to use a distributed system such as a Redis cache
    for cross-process bots.
    """

    __slots__ = ()

    ################
    # APPLICATIONS #
    ################
    @abc.abstractmethod
    async def create_application(self, payload: binding.JSONObject) -> applications.Application:
        ...

    @abc.abstractmethod
    async def create_own_guild(self, payload: binding.JSONObject) -> applications.OwnGuild:
        ...

    @abc.abstractmethod
    async def create_own_connection(self, payload: binding.JSONObject) -> applications.OwnConnection:
        ...

    ##############
    # AUDIT LOGS #
    ##############

    @abc.abstractmethod
    async def create_audit_log_change(self, payload: binding.JSONObject) -> audit_logs.AuditLogChange:
        ...

    @abc.abstractmethod
    async def create_audit_log_entry_info(self, payload: binding.JSONObject) -> audit_logs.BaseAuditLogEntryInfo:
        ...

    @abc.abstractmethod
    async def create_audit_log_entry(self, payload: binding.JSONObject) -> audit_logs.AuditLogEntry:
        ...

    @abc.abstractmethod
    async def create_audit_log(self, payload: binding.JSONObject) -> audit_logs.AuditLog:
        ...

    ############
    # CHANNELS #
    ############

    @abc.abstractmethod
    async def create_channel(self, payload: binding.JSONObject, can_cache: bool = False) -> channels.PartialChannel:
        ...

    @abc.abstractmethod
    async def update_channel(
        self, channel: channels.PartialChannel, payload: binding.JSONObject,
    ) -> channels.PartialChannel:
        ...

    @abc.abstractmethod
    async def get_channel(self, channel_id: int) -> typing.Optional[channels.PartialChannel]:
        ...

    @abc.abstractmethod
    async def delete_channel(self, channel_id: int) -> typing.Optional[channels.PartialChannel]:
        ...

    ##########
    # EMBEDS #
    ##########

    @abc.abstractmethod
    async def create_embed(self, payload: binding.JSONObject) -> embeds.Embed:
        ...

    ##########
    # EMOJIS #
    ##########

    @abc.abstractmethod
    async def create_emoji(self, payload: binding.JSONObject, can_cache: bool = False) -> emojis.Emoji:
        ...

    @abc.abstractmethod
    async def update_emoji(self, payload: binding.JSONObject) -> emojis.Emoji:
        ...

    @abc.abstractmethod
    async def get_emoji(self, emoji_id: int) -> typing.Optional[emojis.KnownCustomEmoji]:
        ...

    @abc.abstractmethod
    async def delete_emoji(self, emoji_id: int) -> typing.Optional[emojis.KnownCustomEmoji]:
        ...

    ###########
    # GATEWAY #
    ###########

    @abc.abstractmethod
    async def create_gateway_bot(self, payload: binding.JSONObject) -> gateway.GatewayBot:
        ...

    ##########
    # GUILDS #
    ##########

    @abc.abstractmethod
    async def create_member(self, payload: binding.JSONObject, can_cache: bool = False) -> guilds.GuildMember:
        # TODO: revisit for the voodoo to make a member into a special user.
        ...

    @abc.abstractmethod
    async def update_member(self, member: guilds.GuildMember, payload: binding.JSONObject) -> guilds.GuildMember:
        ...

    @abc.abstractmethod
    async def get_member(self, guild_id: int, user_id: int) -> typing.Optional[guilds.GuildMember]:
        ...

    @abc.abstractmethod
    async def delete_member(self, guild_id: int, user_id: int) -> typing.Optional[guilds.GuildMember]:
        ...

    @abc.abstractmethod
    async def create_role(self, payload: binding.JSONObject, can_cache: bool = False) -> guilds.PartialRole:
        ...

    @abc.abstractmethod
    async def update_role(self, role: guilds.PartialRole, payload: binding.JSONObject) -> guilds.PartialRole:
        ...

    @abc.abstractmethod
    async def get_role(self, guild_id: int, role_id: int) -> typing.Optional[guilds.PartialRole]:
        ...

    @abc.abstractmethod
    async def delete_role(self, guild_id: int, role_id: int) -> typing.Optional[guilds.PartialRole]:
        ...

    @abc.abstractmethod
    async def create_presence(self, payload: binding.JSONObject, can_cache: bool = False) -> guilds.GuildMemberPresence:
        ...

    @abc.abstractmethod
    async def update_presence(
        self, role: guilds.GuildMemberPresence, payload: binding.JSONObject
    ) -> guilds.GuildMemberPresence:
        ...

    @abc.abstractmethod
    async def get_presence(self, guild_id: int, user_id: int) -> typing.Optional[guilds.GuildMemberPresence]:
        ...

    @abc.abstractmethod
    async def delete_presence(self, guild_id: int, user_id: int) -> typing.Optional[guilds.GuildMemberPresence]:
        ...

    @abc.abstractmethod
    async def create_guild_ban(self, payload: binding.JSONObject) -> guilds.GuildMemberBan:
        ...

    @abc.abstractmethod
    async def create_guild_integration(self, payload: binding.JSONObject) -> guilds.PartialGuildIntegration:
        ...

    @abc.abstractmethod
    async def create_guild(self, payload: binding.JSONObject, can_cache: bool = False) -> guilds.PartialGuild:
        ...

    @abc.abstractmethod
    async def update_guild(self, guild: guilds.PartialGuild, payload: binding.JSONObject) -> guilds.PartialGuild:
        ...

    @abc.abstractmethod
    async def get_guild(self, guild_id: int) -> typing.Optional[guilds.PartialGuild]:
        ...

    @abc.abstractmethod
    async def delete_guild(self, guild_id: int) -> typing.Optional[guilds.PartialGuild]:
        ...

    @abc.abstractmethod
    async def create_guild_preview(self, payload: binding.JSONObject) -> guilds.GuildPreview:
        ...

    ###########
    # INVITES #
    ###########
    @abc.abstractmethod
    async def create_invite(self, payload: binding.JSONObject) -> invites.Invite:
        ...

    ############
    # MESSAGES #
    ############
    @abc.abstractmethod
    async def create_reaction(self, payload: binding.JSONObject) -> messages.Reaction:
        ...

    @abc.abstractmethod
    async def create_message(self, payload: binding.JSONObject, can_cache: bool = False) -> messages.Message:
        ...

    @abc.abstractmethod
    async def update_message(self, message: messages.Message, payload: binding.JSONObject) -> messages.Message:
        ...

    @abc.abstractmethod
    async def get_message(self, channel_id: int, message_id: int) -> typing.Optional[messages.Message]:
        ...

    @abc.abstractmethod
    async def delete_message(self, channel_id: int, message_id: int) -> typing.Optional[messages.Message]:
        ...

    #########
    # USERS #
    #########
    @abc.abstractmethod
    async def create_user(self, payload: binding.JSONObject, can_cache: bool = False) -> users.User:
        ...

    @abc.abstractmethod
    async def update_user(self, user: users.User, payload: binding.JSONObject) -> users.User:
        ...

    @abc.abstractmethod
    async def get_user(self, user_id: int) -> typing.Optional[users.User]:
        ...

    @abc.abstractmethod
    async def delete_user(self, user_id: int) -> typing.Optional[users.User]:
        ...

    @abc.abstractmethod
    async def create_my_user(self, payload: binding.JSONObject, can_cache: bool = False) -> users.MyUser:
        ...

    @abc.abstractmethod
    async def update_my_user(self, my_user: users.MyUser, payload: binding.JSONObject) -> users.MyUser:
        ...

    @abc.abstractmethod
    async def get_my_user(self) -> typing.Optional[users.User]:
        ...

    ##########
    # VOICES #
    ##########
    @abc.abstractmethod
    async def create_voice_state(self, payload: binding.JSONObject, can_cache: bool = False) -> voices.VoiceState:
        ...

    @abc.abstractmethod
    async def update_voice_state(self, payload: binding.JSONObject) -> voices.VoiceState:
        ...

    @abc.abstractmethod
    async def get_voice_state(self, guild_id: int, channel_id: int) -> typing.Optional[voices.VoiceState]:
        ...

    @abc.abstractmethod
    async def delete_voice_state(self, guild_id: int, channel_id: int) -> typing.Optional[voices.VoiceState]:
        ...

    @abc.abstractmethod
    async def create_voice_region(self, payload: binding.JSONObject) -> voices.VoiceRegion:
        ...
