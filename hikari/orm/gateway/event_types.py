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
import enum


class EventType(str, enum.Enum):
    """
    Events that the standard gateway event adapter can provide.
    """

    #: Triggered when Discord notifies the gateway of some channel being created.
    #:
    #: |rawEvent|
    #:
    #: Args:
    #:    channel:
    #:        a :class:`hikari.internal_utilities.data_structures.ObjectProxy` corresponding to
    #:        the definition at https://discordapp.com/developers/docs/resources/channel#channel-object
    RAW_CHANNEL_CREATE = "raw_channel_create"

    #: Fired when a DM channel is created.
    #:
    #: Args:
    #:     channel:
    #           the :class:`hikari.orm.models.channels.DMChannel` or :class:`hikari.orm.models.channels.GroupDMChannel`
    #           that was created.
    DM_CHANNEL_CREATE = "dm_channel_create"

    #: Fired when a guild channel or category is created.
    #:
    #: Args:
    #:     channel:
    #:         the :class:`hikari.orm.models.channels.GuildChannel` derivative that was created.
    #:
    #: Note:
    #:     If the guild of a channel that was created was not cached, then this event will not fire. See
    #:     :attr:`RAW_CHANNEL_CREATE` for all events.
    GUILD_CHANNEL_CREATE = "guild_channel_create"

    RAW_CHANNEL_UPDATE = "raw_channel_update"
    DM_CHANNEL_UPDATE = "dm_channel_update"
    GUILD_CHANNEL_UPDATE = "guild_channel_update"

    RAW_CHANNEL_DELETE = "raw_channel_delete"
    DM_CHANNEL_DELETE = "dm_channel_delete"
    GUILD_CHANNEL_DELETE = "guild_channel_delete"

    RAW_CHANNEL_PINS_UPDATE = "raw_channel_pins_update"
    DM_CHANNEL_PIN_ADDED = "dm_channel_pin_added"
    DM_CHANNEL_PIN_REMOVED = "dm_channel_pin_removed"
    GUILD_CHANNEL_PIN_ADDED = "guild_channel_pin_added"
    GUILD_CHANNEL_PIN_REMOVED = "guild_channel_pin_removed"

    RAW_GUILD_CREATE = "raw_guild_create"
    GUILD_CREATE = "guild_create"
    GUILD_AVAILABLE = "guild_available"

    RAW_GUILD_UPDATE = "raw_guild_update"
    GUILD_UPDATE = "guild_update"

    RAW_GUILD_DELETE = "raw_guild_delete"
    GUILD_UNAVAILABLE = "guild_unavailable"
    GUILD_LEAVE = "guild_leave"

    RAW_GUILD_BAN_ADD = "raw_guild_ban_add"
    GUILD_BAN_ADD = "guild_ban_add"

    RAW_GUILD_BAN_REMOVE = "raw_guild_ban_remove"
    GUILD_BAN_REMOVE = "guild_ban_remove"

    RAW_GUILD_EMOJIS_UPDATE = "raw_guild_emojis_update"
    GUILD_EMOJIS_UPDATE = "guild_emojis_update"

    RAW_GUILD_INTEGRATIONS_UPDATE = "raw_guild_integrations_update"
    GUILD_INTEGRATIONS_UPDATE = "guild_integrations_update"

    RAW_GUILD_MEMBER_ADD = "raw_guild_member_add"
    GUILD_MEMBER_ADD = "guild_member_add"

    RAW_GUILD_MEMBER_UPDATE = "raw_guild_member_update"
    GUILD_MEMBER_UPDATE = "guild_member_update"

    RAW_GUILD_MEMBER_REMOVE = "raw_guild_member_remove"
    GUILD_MEMBER_REMOVE = "guild_member_remove"

    RAW_GUILD_MEMBERS_CHUNK = "raw_guild_members_chunk"

    RAW_GUILD_ROLE_CREATE = "raw_guild_role_create"
    GUILD_ROLE_CREATE = "guild_role_create"

    RAW_GUILD_ROLE_UPDATE = "raw_guild_role_update"
    GUILD_ROLE_UPDATE = "guild_role_update"

    RAW_GUILD_ROLE_DELETE = "raw_guild_role_delete"
    GUILD_ROLE_DELETE = "guild_role_delete"

    RAW_MESSAGE_CREATE = "raw_message_create"
    MESSAGE_CREATE = "message_create"

    RAW_MESSAGE_UPDATE = "raw_message_update"
    MESSAGE_UPDATE = "message_update"

    RAW_MESSAGE_DELETE = "raw_message_delete"
    MESSAGE_DELETE = "message_delete"

    RAW_MESSAGE_DELETE_BULK = "raw_message_delete_bulk"
    MESSAGE_DELETE_BULK = "message_delete_bulk"

    RAW_MESSAGE_REACTION_ADD = "raw_message_reaction_add"
    MESSAGE_REACTION_ADD = "message_reaction_add"

    RAW_MESSAGE_REACTION_REMOVE = "raw_message_reaction_remove"
    MESSAGE_REACTION_REMOVE = "message_reaction_remove"

    RAW_MESSAGE_REACTION_REMOVE_ALL = "raw_message_reaction_remove_all"
    MESSAGE_REACTION_REMOVE_ALL = "message_reaction_remove_all"

    RAW_PRESENCE_UPDATE = "raw_presence_update"
    PRESENCE_UPDATE = "presence_update"

    RAW_TYPING_START = "raw_typing_start"
    TYPING_START = "typing_start"

    RAW_USER_UPDATE = "raw_user_update"
    USER_UPDATE = "user_update"

    RAW_VOICE_STATE_UPDATE = "raw_voice_state_update"
    VOICE_STATE_UPDATE = "voice_state_update"

    RAW_VOICE_SERVER_UPDATE = "raw_voice_server_update"
    VOICE_SERVER_UPDATE = "voice_server_update"

    RAW_WEBHOOKS_UPDATE = "raw_webhooks_update"
    WEBHOOKS_UPDATE = "webhooks_update"

    CONNECT = "connect"
    READY = "ready"
    DISCONNECT = "disconnect"
    INVALID_SESSION = "invalid_session"
    RECONNECT = "reconnect"
    RESUME = "resume"

    STARTUP = "startup"
    SHUTDOWN = "shutdown"

    #: Should be implemented in the future. For now, will never get fired.
    INVITE_CREATE = "invite_create"
    #: Should be implemented in the future. For now, will never get fired.
    INVITE_DELETE = "invite_delete"
    #: Should be implemented in the future. For now, will never get fired.
    MESSAGE_REACTION_REMOVE_EMOJI = "message_reaction_remove_emoji"
