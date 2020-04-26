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
"""Event management for stateless bots."""

from __future__ import annotations

__all__ = ["StatelessEventManagerImpl"]

from hikari.events import channels
from hikari.events import guilds
from hikari.events import messages
from hikari.events import other
from hikari.state import dispatchers
from hikari.state import event_managers


# pylint: disable=too-many-public-methods
class StatelessEventManagerImpl(event_managers.EventManager[dispatchers.EventDispatcher]):
    """Stateless event manager implementation for stateless bots.

    This is an implementation that does not rely on querying prior information to
    operate. The implementation details of this are much simpler than a stateful
    version, and are not immediately affected by the use of intents.
    """

    @event_managers.raw_event_mapper("CONNECTED")
    def on_connect(self, shard, _) -> None:
        """Handle CONNECTED events."""
        event = other.ConnectedEvent(shard=shard)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("DISCONNECTED")
    def on_disconnect(self, shard, _) -> None:
        """Handle DISCONNECTED events."""
        event = other.DisconnectedEvent(shard=shard)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("RESUME")
    def on_resume(self, shard, _) -> None:
        """Handle RESUME events."""
        event = other.ResumedEvent(shard=shard)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("READY")
    def on_ready(self, _, payload) -> None:
        """Handle READY events."""
        event = other.ReadyEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("CHANNEL_CREATE")
    def on_channel_create(self, _, payload) -> None:
        """Handle CHANNEL_CREATE events."""
        event = channels.ChannelCreateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("CHANNEL_UPDATE")
    def on_channel_update(self, _, payload) -> None:
        """Handle CHANNEL_UPDATE events."""
        event = channels.ChannelUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("CHANNEL_DELETE")
    def on_channel_delete(self, _, payload) -> None:
        """Handle CHANNEL_DELETE events."""
        event = channels.ChannelDeleteEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("CHANNEL_PIN_UPDATE")
    def on_channel_pin_update(self, _, payload) -> None:
        """Handle CHANNEL_PIN_UPDATE events."""
        event = channels.ChannelPinUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_CREATE")
    def on_guild_create(self, _, payload) -> None:
        """Handle GUILD_CREATE events."""
        event = guilds.GuildCreateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_UPDATE")
    def on_guild_update(self, _, payload) -> None:
        """Handle GUILD_UPDATE events."""
        event = guilds.GuildUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_DELETE")
    def on_guild_delete(self, _, payload) -> None:
        """Handle GUILD_DELETE events."""
        if payload.get("unavailable", False):
            event = guilds.GuildUnavailableEvent.deserialize(payload)
        else:
            event = guilds.GuildLeaveEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_BAN_ADD")
    def on_guild_ban_add(self, _, payload) -> None:
        """Handle GUILD_BAN_ADD events."""
        event = guilds.GuildBanAddEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_BAN_REMOVE")
    def on_guild_ban_remove(self, _, payload) -> None:
        """Handle GUILD_BAN_REMOVE events."""
        event = guilds.GuildBanRemoveEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_EMOJIS_UPDATE")
    def on_guild_emojis_update(self, _, payload) -> None:
        """Handle GUILD_EMOJIS_UPDATE events."""
        event = guilds.GuildEmojisUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_INTEGRATIONS_UPDATE")
    def on_guild_integrations_update(self, _, payload) -> None:
        """Handle GUILD_INTEGRATIONS_UPDATE events."""
        event = guilds.GuildIntegrationsUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_MEMBER_ADD")
    def on_guild_member_add(self, _, payload) -> None:
        """Handle GUILD_MEMBER_ADD events."""
        event = guilds.GuildMemberAddEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_MEMBER_UPDATE")
    def on_guild_member_update(self, _, payload) -> None:
        """Handle GUILD_MEMBER_UPDATE events."""
        event = guilds.GuildMemberUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_MEMBER_REMOVE")
    def on_guild_member_remove(self, _, payload) -> None:
        """Handle GUILD_MEMBER_REMOVE events."""
        event = guilds.GuildMemberRemoveEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_ROLE_CREATE")
    def on_guild_role_create(self, _, payload) -> None:
        """Handle GUILD_ROLE_CREATE events."""
        event = guilds.GuildRoleCreateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_ROLE_UPDATE")
    def on_guild_role_update(self, _, payload) -> None:
        """Handle GUILD_ROLE_UPDATE events."""
        event = guilds.GuildRoleUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_ROLE_DELETE")
    def on_guild_role_delete(self, _, payload) -> None:
        """Handle GUILD_ROLE_DELETE events."""
        event = guilds.GuildRoleDeleteEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("INVITE_CREATE")
    def on_invite_create(self, _, payload) -> None:
        """Handle INVITE_CREATE events."""
        event = channels.InviteCreateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("INVITE_DELETE")
    def on_invite_delete(self, _, payload) -> None:
        """Handle INVITE_DELETE events."""
        event = channels.InviteDeleteEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_CREATE")
    def on_message_create(self, _, payload) -> None:
        """Handle MESSAGE_CREATE events."""
        event = messages.MessageCreateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_UPDATE")
    def on_message_update(self, _, payload) -> None:
        """Handle MESSAGE_UPDATE events."""
        event = messages.MessageUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_DELETE")
    def on_message_delete(self, _, payload) -> None:
        """Handle MESSAGE_DELETE events."""
        event = messages.MessageDeleteEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_DELETE_BULK")
    def on_message_delete_bulk(self, _, payload) -> None:
        """Handle MESSAGE_DELETE_BULK events."""
        event = messages.MessageDeleteBulkEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_REACTION_ADD")
    def on_message_reaction_add(self, _, payload) -> None:
        """Handle MESSAGE_REACTION_ADD events."""
        event = messages.MessageReactionAddEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_REACTION_REMOVE")
    def on_message_reaction_remove(self, _, payload) -> None:
        """Handle MESSAGE_REACTION_REMOVE events."""
        payload["emoji"].setdefault("animated", None)

        event = messages.MessageReactionRemoveEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_REACTION_REMOVE_EMOJI")
    def on_message_reaction_remove_emoji(self, _, payload) -> None:
        """Handle MESSAGE_REACTION_REMOVE_EMOJI events."""
        payload["emoji"].setdefault("animated", None)

        event = messages.MessageReactionRemoveEmojiEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("PRESENCE_UPDATE")
    def on_presence_update(self, _, payload) -> None:
        """Handle PRESENCE_UPDATE events."""
        event = guilds.PresenceUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("TYPING_START")
    def on_typing_start(self, _, payload) -> None:
        """Handle TYPING_START events."""
        event = channels.TypingStartEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("USER_UPDATE")
    def on_user_update(self, _, payload) -> None:
        """Handle USER_UPDATE events."""
        event = other.UserUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("VOICE_STATE_UPDATE")
    def on_voice_state_update(self, _, payload) -> None:
        """Handle VOICE_STATE_UPDATE events."""
        event = channels.VoiceStateUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("VOICE_SERVER_UPDATE")
    def on_voice_server_update(self, _, payload) -> None:
        """Handle VOICE_SERVER_UPDATE events."""
        event = channels.VoiceStateUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("WEBHOOK_UPDATE")
    def on_webhook_update(self, _, payload) -> None:
        """Handle WEBHOOK_UPDATE events."""
        event = channels.WebhookUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)


# pylint: enable=too-many-public-methods
