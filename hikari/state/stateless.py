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

from hikari.events import channel, dispatchers, event_managers
from hikari.events import guild
from hikari.events import message
from hikari.events import other


# pylint: disable=too-many-public-methods
class StatelessEventManagerImpl(event_managers.EventManager[dispatchers.EventDispatcher]):
    """Stateless event manager implementation for stateless bots.

    This is an implementation that does not rely on querying prior information to
    operate. The implementation details of this are much simpler than a stateful
    version, and are not immediately affected by the use of intents.
    """

    @event_managers.raw_event_mapper("CONNECTED")
    async def on_connect(self, shard, _) -> None:
        """Handle CONNECTED events."""
        event = other.ConnectedEvent(shard=shard)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("DISCONNECTED")
    async def on_disconnect(self, shard, _) -> None:
        """Handle DISCONNECTED events."""
        event = other.DisconnectedEvent(shard=shard)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("RESUME")
    async def on_resume(self, shard, _) -> None:
        """Handle RESUME events."""
        event = other.ResumedEvent(shard=shard)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("READY")
    async def on_ready(self, _, payload) -> None:
        """Handle READY events."""
        event = other.ReadyEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("CHANNEL_CREATE")
    async def on_channel_create(self, _, payload) -> None:
        """Handle CHANNEL_CREATE events."""
        event = channel.ChannelCreateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("CHANNEL_UPDATE")
    async def on_channel_update(self, _, payload) -> None:
        """Handle CHANNEL_UPDATE events."""
        event = channel.ChannelUpdateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("CHANNEL_DELETE")
    async def on_channel_delete(self, _, payload) -> None:
        """Handle CHANNEL_DELETE events."""
        event = channel.ChannelDeleteEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("CHANNEL_PIN_UPDATE")
    async def on_channel_pin_update(self, _, payload) -> None:
        """Handle CHANNEL_PIN_UPDATE events."""
        event = channel.ChannelPinUpdateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_CREATE")
    async def on_guild_create(self, _, payload) -> None:
        """Handle GUILD_CREATE events."""
        event = guild.GuildCreateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_UPDATE")
    async def on_guild_update(self, _, payload) -> None:
        """Handle GUILD_UPDATE events."""
        event = guild.GuildUpdateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_DELETE")
    async def on_guild_delete(self, _, payload) -> None:
        """Handle GUILD_DELETE events."""
        if payload.get("unavailable", False):
            event = guild.GuildUnavailableEvent.deserialize(payload, components=self._components)
        else:
            event = guild.GuildLeaveEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_BAN_ADD")
    async def on_guild_ban_add(self, _, payload) -> None:
        """Handle GUILD_BAN_ADD events."""
        event = guild.GuildBanAddEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_BAN_REMOVE")
    async def on_guild_ban_remove(self, _, payload) -> None:
        """Handle GUILD_BAN_REMOVE events."""
        event = guild.GuildBanRemoveEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_EMOJIS_UPDATE")
    async def on_guild_emojis_update(self, _, payload) -> None:
        """Handle GUILD_EMOJIS_UPDATE events."""
        event = guild.GuildEmojisUpdateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_INTEGRATIONS_UPDATE")
    async def on_guild_integrations_update(self, _, payload) -> None:
        """Handle GUILD_INTEGRATIONS_UPDATE events."""
        event = guild.GuildIntegrationsUpdateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_MEMBER_ADD")
    async def on_guild_member_add(self, _, payload) -> None:
        """Handle GUILD_MEMBER_ADD events."""
        event = guild.GuildMemberAddEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_MEMBER_UPDATE")
    async def on_guild_member_update(self, _, payload) -> None:
        """Handle GUILD_MEMBER_UPDATE events."""
        event = guild.GuildMemberUpdateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_MEMBER_REMOVE")
    async def on_guild_member_remove(self, _, payload) -> None:
        """Handle GUILD_MEMBER_REMOVE events."""
        event = guild.GuildMemberRemoveEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_ROLE_CREATE")
    async def on_guild_role_create(self, _, payload) -> None:
        """Handle GUILD_ROLE_CREATE events."""
        event = guild.GuildRoleCreateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_ROLE_UPDATE")
    async def on_guild_role_update(self, _, payload) -> None:
        """Handle GUILD_ROLE_UPDATE events."""
        event = guild.GuildRoleUpdateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("GUILD_ROLE_DELETE")
    async def on_guild_role_delete(self, _, payload) -> None:
        """Handle GUILD_ROLE_DELETE events."""
        event = guild.GuildRoleDeleteEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("INVITE_CREATE")
    async def on_invite_create(self, _, payload) -> None:
        """Handle INVITE_CREATE events."""
        event = channel.InviteCreateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("INVITE_DELETE")
    async def on_invite_delete(self, _, payload) -> None:
        """Handle INVITE_DELETE events."""
        event = channel.InviteDeleteEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_CREATE")
    async def on_message_create(self, _, payload) -> None:
        """Handle MESSAGE_CREATE events."""
        # For consistency's sake and to keep Member.user as a non-nullable field, here we inject the attached user
        # payload into the member payload when the member payload is present as discord decided not to duplicate the
        # user object between Message.author and Message.member.user
        if "member" in payload:
            payload["member"]["user"] = payload["author"]
        event = message.MessageCreateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_UPDATE")
    async def on_message_update(self, _, payload) -> None:
        """Handle MESSAGE_UPDATE events."""
        # For consistency's sake and to keep Member.user as a non-nullable field, here we inject the attached user
        # payload into the member payload when the member payload is present as discord decided not to duplicate the
        # user object between Message.author and Message.member.user
        if "member" in payload and "author" in payload:
            payload["member"]["user"] = payload["author"]
        event = message.MessageUpdateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_DELETE")
    async def on_message_delete(self, _, payload) -> None:
        """Handle MESSAGE_DELETE events."""
        event = message.MessageDeleteEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_DELETE_BULK")
    async def on_message_delete_bulk(self, _, payload) -> None:
        """Handle MESSAGE_DELETE_BULK events."""
        event = message.MessageDeleteBulkEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_REACTION_ADD")
    async def on_message_reaction_add(self, _, payload) -> None:
        """Handle MESSAGE_REACTION_ADD events."""
        event = message.MessageReactionAddEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_REACTION_REMOVE")
    async def on_message_reaction_remove(self, _, payload) -> None:
        """Handle MESSAGE_REACTION_REMOVE events."""
        payload["emoji"].setdefault("animated", None)

        event = message.MessageReactionRemoveEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("MESSAGE_REACTION_REMOVE_EMOJI")
    async def on_message_reaction_remove_emoji(self, _, payload) -> None:
        """Handle MESSAGE_REACTION_REMOVE_EMOJI events."""
        payload["emoji"].setdefault("animated", None)

        event = message.MessageReactionRemoveEmojiEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("PRESENCE_UPDATE")
    async def on_presence_update(self, _, payload) -> None:
        """Handle PRESENCE_UPDATE events."""
        event = guild.PresenceUpdateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("TYPING_START")
    async def on_typing_start(self, _, payload) -> None:
        """Handle TYPING_START events."""
        event = channel.TypingStartEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("USER_UPDATE")
    async def on_user_update(self, _, payload) -> None:
        """Handle USER_UPDATE events."""
        event = other.UserUpdateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("VOICE_STATE_UPDATE")
    async def on_voice_state_update(self, _, payload) -> None:
        """Handle VOICE_STATE_UPDATE events."""
        event = channel.VoiceStateUpdateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("VOICE_SERVER_UPDATE")
    async def on_voice_server_update(self, _, payload) -> None:
        """Handle VOICE_SERVER_UPDATE events."""
        event = channel.VoiceStateUpdateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)

    @event_managers.raw_event_mapper("WEBHOOK_UPDATE")
    async def on_webhook_update(self, _, payload) -> None:
        """Handle WEBHOOK_UPDATE events."""
        event = channel.WebhookUpdateEvent.deserialize(payload, components=self._components)
        await self._components.event_dispatcher.dispatch_event(event)


# pylint: enable=too-many-public-methods
