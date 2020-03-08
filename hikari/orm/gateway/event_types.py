#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""
Expected events that this framework can dispatch.
"""
__all__ = ["EventType"]

import enum


class EventType(str, enum.Enum):
    """
    Events that the standard gateway event adapter can provide.
    """

    #: A special event that should have a handler that consumes a
    #: :class:`hikari.internal_utilities.aio.EventExceptionContext` as the sole
    #: parameter.
    EXCEPTION = "exception"

    CONNECT = "connect"
    DISCONNECT = "disconnect"
    DM_CHANNEL_CREATE = "dm_channel_create"
    DM_CHANNEL_DELETE = "dm_channel_delete"
    DM_CHANNEL_PIN_ADDED = "dm_channel_pin_added"
    DM_CHANNEL_PIN_REMOVED = "dm_channel_pin_removed"
    DM_CHANNEL_UPDATE = "dm_channel_update"
    GUILD_AVAILABLE = "guild_available"
    GUILD_BAN_ADD = "guild_ban_add"
    GUILD_BAN_REMOVE = "guild_ban_remove"
    GUILD_CHANNEL_CREATE = "guild_channel_create"
    GUILD_CHANNEL_DELETE = "guild_channel_delete"
    GUILD_CHANNEL_PIN_ADDED = "guild_channel_pin_added"
    GUILD_CHANNEL_PIN_REMOVED = "guild_channel_pin_removed"
    GUILD_CHANNEL_UPDATE = "guild_channel_update"
    GUILD_CREATE = "guild_create"
    GUILD_EMOJIS_UPDATE = "guild_emojis_update"
    GUILD_INTEGRATIONS_UPDATE = "guild_integrations_update"
    GUILD_LEAVE = "guild_leave"
    GUILD_MEMBER_ADD = "guild_member_add"
    GUILD_MEMBER_REMOVE = "guild_member_remove"
    GUILD_MEMBER_UPDATE = "guild_member_update"
    GUILD_ROLE_CREATE = "guild_role_create"
    GUILD_ROLE_DELETE = "guild_role_delete"
    GUILD_ROLE_UPDATE = "guild_role_update"
    GUILD_UNAVAILABLE = "guild_unavailable"
    GUILD_UPDATE = "guild_update"
    INVALID_SESSION = "invalid_session"
    INVITE_CREATE = "invite_create"
    INVITE_DELETE = "invite_delete"
    MESSAGE_CREATE = "message_create"
    MESSAGE_DELETE = "message_delete"
    MESSAGE_DELETE_BULK = "message_delete_bulk"
    MESSAGE_REACTION_ADD = "message_reaction_add"
    MESSAGE_REACTION_REMOVE = "message_reaction_remove"
    MESSAGE_REACTION_REMOVE_ALL = "message_reaction_remove_all"
    MESSAGE_REACTION_REMOVE_EMOJI = "message_reaction_remove_emoji"
    MESSAGE_UPDATE = "message_update"
    POST_SHUTDOWN = "post_shutdown"
    POST_STARTUP = "post_startup"
    PRE_SHUTDOWN = "pre_shutdown"
    PRE_STARTUP = "pre_startup"
    PRESENCE_UPDATE = "presence_update"
    RAW_GUILD_MEMBERS_CHUNK = "raw_guild_members_chunk"
    READY = "ready"
    RECONNECT = "reconnect"
    RESUME = "resume"
    TYPING_START = "typing_start"
    USER_UPDATE = "user_update"
    VOICE_SERVER_UPDATE = "voice_server_update"
    VOICE_STATE_UPDATE = "voice_state_update"
    WEBHOOKS_UPDATE = "webhooks_update"

    def __str__(self):
        return str(self.value)
