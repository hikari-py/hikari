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

__all__ = ["StatelessEventManagerImpl"]

from hikari import events
from hikari.state import event_dispatchers
from hikari.state import event_managers


class StatelessEventManagerImpl(event_managers.EventManager[event_dispatchers.EventDispatcher]):
    """Stateless event manager implementation for stateless bots.

    This is an implementation that does not rely on querying prior information to
    operate. The implementation details of this are much simpler than a stateful
    version, and are not immediately affected by the use of intents.
    """

    @event_managers.raw_event_mapper("CONNECTED")
    def on_connect(self, shard, _):
        """Handle CONNECTED events."""
        event = events.ConnectedEvent(shard=shard)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("DISCONNECTED")
    def on_disconnect(self, shard, _):
        """Handle DISCONNECTED events."""
        event = events.DisconnectedEvent(shard=shard)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("RESUME")
    def on_resume(self, shard, _):
        """Handle RESUME events."""
        event = events.ResumedEvent(shard=shard)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("READY")
    def on_ready(self, _, payload):
        """Handle READY events."""
        event = events.ReadyEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("CHANNEL_CREATE")
    def on_channel_create(self, _, payload):
        """Handle CHANNEL_CREATE events."""
        event = events.ChannelCreateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("CHANNEL_UPDATE")
    def on_channel_update(self, _, payload):
        """Handle CHANNEL_UPDATE events."""
        event = events.ChannelUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("CHANNEL_DELETE")
    def on_channel_delete(self, _, payload):
        """Handle CHANNEL_DELETE events."""
        event = events.ChannelDeleteEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("CHANNEL_PIN_UPDATE")
    def on_channel_pin_update(self, _, payload):
        """Handle CHANNEL_PIN_UPDATE events."""
        event = events.ChannelPinUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_CREATE")
    def on_guild_create(self, _, payload):
        """Handle GUILD_CREATE events."""
        event = events.GuildCreateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_UPDATE")
    def on_guild_update(self, _, payload):
        """Handle GUILD_UPDATE events."""
        event = events.GuildUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_LEAVE")
    def on_guild_leave(self, _, payload):
        """Handle GUILD_LEAVE events."""
        event = events.GuildLeaveEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_UNAVAILABLE")
    def on_guild_unavailable(self, _, payload):
        """Handle GUILD_UNAVAILABLE events."""
        event = events.GuildUnavailableEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_BAN_ADD")
    def on_guild_ban_add(self, _, payload):
        """Handle GUILD_BAN_ADD events."""
        event = events.GuildBanAddEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_BAN_REMOVE")
    def on_guild_ban_remove(self, _, payload):
        """Handle GUILD_BAN_REMOVE events."""
        event = events.GuildBanRemoveEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_EMOJIS_UPDATE")
    def on_guild_emojis_update(self, _, payload):
        """Handle GUILD_EMOJIS_UPDATE events."""
        event = events.GuildEmojisUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_INTEGRATIONS_UPDATE")
    def on_guild_integrations_update(self, _, payload):
        """Handle GUILD_INTEGRATIONS_UPDATE events."""
        event = events.GuildIntegrationsUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_MEMBER_ADD")
    def on_guild_member_add(self, _, payload):
        """Handle GUILD_MEMBER_ADD events."""
        event = events.GuildMemberAddEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_MEMBER_UPDATE")
    def on_guild_member_update(self, _, payload):
        """Handle GUILD_MEMBER_UPDATE events."""
        event = events.GuildMemberUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_MEMBER_REMOVE")
    def on_guild_member_remove(self, _, payload):
        """Handle GUILD_MEMBER_REMOVE events."""
        event = events.GuildMemberRemoveEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_ROLE_CREATE")
    def on_guild_role_create(self, _, payload):
        """Handle GUILD_ROLE_CREATE events."""
        event = events.GuildRoleCreateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_ROLE_UPDATE")
    def on_guild_role_update(self, _, payload):
        """Handle GUILD_ROLE_UPDATE events."""
        event = events.GuildRoleUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_ROLE_DELETE")
    def on_guild_role_delete(self, _, payload):
        """Handle GUILD_ROLE_DELETE events."""
        event = events.GuildRoleDeleteEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("INVITE_CREATE")
    def on_invite_create(self, _, payload):
        """Handle INVITE_CREATE events."""
        event = events.InviteCreateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("INVITE_DELETE")
    def on_invite_delete(self, _, payload):
        """Handle INVITE_DELETE events."""
        event = events.InviteDeleteEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_CREATE")
    def on_message_create(self, _, payload):
        """Handle MESSAGE_CREATE events."""
        event = events.MessageCreateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_UPDATE")
    def on_message_update(self, _, payload):
        """Handle MESSAGE_UPDATE events."""
        event = events.MessageUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_DELETE")
    def on_message_delete(self, _, payload):
        """Handle MESSAGE_DELETE events."""
        event = events.MessageDeleteEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_DELETE_BULK")
    def on_message_delete_bulk(self, _, payload):
        """Handle MESSAGE_DELETE_BULK events."""
        event = events.MessageDeleteBulkEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_REACTION_ADD")
    def on_message_reaction_add(self, _, payload):
        """Handle MESSAGE_REACTION_ADD events."""
        event = events.MessageReactionAddEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_REACTION_REMOVE")
    def on_message_reaction_remove(self, _, payload):
        """Handle MESSAGE_REACTION_REMOVE events."""
        payload["emoji"].setdefault("animated", None)

        event = events.MessageReactionRemoveEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_REACTION_REMOVE_EMOJI")
    def on_message_reaction_remove_emoji(self, _, payload):
        """Handle MESSAGE_REACTION_REMOVE_EMOJI events."""
        payload["emoji"].setdefault("animated", None)

        event = events.MessageReactionRemoveEmojiEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("PRESENCE_UPDATE")
    def on_presence_update(self, _, payload):
        """Handle PRESENCE_UPDATE events."""
        event = events.PresenceUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("TYPING_START")
    def on_typing_start(self, _, payload):
        """Handle TYPING_START events."""
        event = events.TypingStartEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("USER_UPDATE")
    def on_user_update(self, _, payload):
        """Handle USER_UPDATE events."""
        event = events.UserUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("VOICE_STATE_UPDATE")
    def on_voice_state_update(self, _, payload):
        """Handle VOICE_STATE_UPDATE events."""
        event = events.VoiceStateUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("VOICE_SERVER_UPDATE")
    def on_voice_server_update(self, _, payload):
        """Handle VOICE_SERVER_UPDATE events."""
        event = events.VoiceStateUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("WEBHOOK_UPDATE")
    def on_webhook_update(self, _, payload):
        """Handle WEBHOOK_UPDATE events."""
        event = events.WebhookUpdateEvent.deserialize(payload)
        self.event_dispatcher.dispatch_event(event)
