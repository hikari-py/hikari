# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Event handling logic for more info."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["StatefulEventManagerImpl"]

import typing

from hikari import channels
from hikari import intents as intents_
from hikari import presences
from hikari import traits
from hikari.events import shard_events
from hikari.impl import event_manager_base

if typing.TYPE_CHECKING:
    from hikari.api import cache as cache_
    from hikari.api import shard as gateway_shard
    from hikari.events import guild_events as guild_events
    from hikari.utilities import data_binding


class StatefulEventManagerImpl(event_manager_base.EventManagerBase):
    """Provides event handling logic for Discord events."""

    __slots__: typing.Sequence[str] = ("_cache",)

    def __init__(
        self, app: traits.BotAware, cache: cache_.MutableCache, intents: typing.Optional[intents_.Intents],
    ) -> None:
        self._cache = cache
        super().__init__(app=app, intents=intents)

    async def on_connected(self, shard: gateway_shard.GatewayShard, _: data_binding.JSONObject) -> None:
        """Handle connection events.

        This is a synthetic event produced by the gateway implementation in
        Hikari.
        """
        # TODO: this should be in entity factory
        await self.dispatch(shard_events.ShardConnectedEvent(app=self._app, shard=shard))

    async def on_disconnected(self, shard: gateway_shard.GatewayShard, _: data_binding.JSONObject) -> None:
        """Handle disconnection events.

        This is a synthetic event produced by the gateway implementation in
        Hikari.
        """
        # TODO: this should be in entity factory
        await self.dispatch(shard_events.ShardDisconnectedEvent(app=self._app, shard=shard))

    async def on_ready(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#ready for more info."""
        # TODO: cache unavailable guilds on startup, I didn't bother for the time being.
        event = self._app.event_factory.deserialize_ready_event(shard, payload)
        self._cache.update_me(event.my_user)
        self._cache.set_initial_unavailable_guilds(event.unavailable_guilds)
        await self.dispatch(event)

    async def on_resumed(self, shard: gateway_shard.GatewayShard, _: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#resumed for more info."""
        # TODO: this should be in entity factory
        await self.dispatch(shard_events.ShardResumedEvent(app=self._app, shard=shard))

    async def on_channel_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-create for more info."""
        event = self._app.event_factory.deserialize_channel_create_event(shard, payload)

        if isinstance(event.channel, channels.GuildChannel):
            self._cache.set_guild_channel(event.channel)
        else:
            self._cache.set_private_text_channel(typing.cast(channels.PrivateTextChannel, event.channel))

        await self.dispatch(event)

    async def on_channel_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-update for more info."""
        event = self._app.event_factory.deserialize_channel_update_event(shard, payload)

        if isinstance(event.channel, channels.GuildChannel):
            self._cache.update_guild_channel(event.channel)
        else:
            self._cache.update_private_text_channel(typing.cast(channels.PrivateTextChannel, event.channel))

        await self.dispatch(event)

    async def on_channel_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-delete for more info."""
        event = self._app.event_factory.deserialize_channel_delete_event(shard, payload)

        if isinstance(event.channel, channels.GuildChannel):
            self._cache.delete_guild_channel(event.channel.id)
        else:
            self._cache.delete_private_text_channel(
                typing.cast(channels.PrivateTextChannel, event.channel).recipient.id
            )

        await self.dispatch(event)

    async def on_channel_pins_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-pins-update for more info."""
        # TODO: we need a method for this specifically
        await self.dispatch(self._app.event_factory.deserialize_channel_pins_update_event(shard, payload))

    async def on_guild_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-create for more info."""
        event = self._app.event_factory.deserialize_guild_create_event(shard, payload)
        self._cache.update_guild(event.guild)

        self._cache.clear_guild_channels_for_guild(event.guild.id)
        for channel in event.channels.values():
            self._cache.set_guild_channel(channel)

        self._cache.clear_emojis_for_guild(event.guild.id)
        for emoji in event.emojis.values():
            self._cache.set_emoji(emoji)

        self._cache.clear_roles_for_guild(event.guild.id)
        for role in event.roles.values():
            self._cache.set_role(role)

        # TODO: do we really want to invalidate these all after an outage.
        self._cache.clear_members_for_guild(event.guild.id)
        for member in event.members.values():
            self._cache.set_member(member)

        self._cache.clear_presences_for_guild(event.guild.id)
        for presence in event.presences.values():
            self._cache.set_presence(presence)

        for voice_state in event.voice_states.values():
            self._cache.set_voice_state(voice_state)

        if event.guild.is_large and (self._intents is None or self._intents & intents_.Intents.GUILD_MEMBERS):
            await self._app.chunker.request_guild_chunk(event.guild)

        await self.dispatch(event)

    async def on_guild_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-update for more info."""
        event = self._app.event_factory.deserialize_guild_update_event(shard, payload)
        self._cache.update_guild(event.guild)

        self._cache.clear_roles_for_guild(event.guild.id)
        for role in event.roles.values():  # TODO: do we actually get this here?
            self._cache.set_role(role)

        self._cache.clear_emojis_for_guild(event.guild.id)  # TODO: do we actually get this here?
        for emoji in event.emojis.values():
            self._cache.set_emoji(emoji)

        await self.dispatch(event)

    async def on_guild_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-delete for more info."""
        event: typing.Union[guild_events.GuildUnavailableEvent, guild_events.GuildLeaveEvent]
        if payload.get("unavailable", False):
            event = self._app.event_factory.deserialize_guild_unavailable_event(shard, payload)
            self._cache.set_guild_availability(event.guild_id, False)

        else:
            event = self._app.event_factory.deserialize_guild_leave_event(shard, payload)
            #  TODO: this doesn't work in all intent scenarios
            self._cache.delete_guild(event.guild_id)
            self._cache.clear_voice_states_for_guild(event.guild_id)
            self._cache.clear_invites_for_guild(event.guild_id)
            self._cache.clear_members_for_guild(event.guild_id)
            self._cache.clear_presences_for_guild(event.guild_id)
            self._cache.clear_guild_channels_for_guild(event.guild_id)
            self._cache.clear_emojis_for_guild(event.guild_id)
            self._cache.clear_roles_for_guild(event.guild_id)

        await self.dispatch(event)

    async def on_guild_ban_add(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-ban-add for more info."""
        await self.dispatch(self._app.event_factory.deserialize_guild_ban_add_event(shard, payload))

    async def on_guild_ban_remove(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-ban-remove for more info."""
        await self.dispatch(self._app.event_factory.deserialize_guild_ban_remove_event(shard, payload))

    async def on_guild_emojis_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-emojis-update for more info."""
        event = self._app.event_factory.deserialize_guild_emojis_update_event(shard, payload)
        self._cache.clear_emojis_for_guild(event.guild_id)

        for emoji in event.emojis:
            self._cache.set_emoji(emoji)

        await self.dispatch(event)

    async def on_guild_integrations_update(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-integrations-update for more info."""
        await self.dispatch(self._app.event_factory.deserialize_guild_integrations_update_event(shard, payload))

    async def on_guild_member_add(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-member-add for more info."""
        event = self._app.event_factory.deserialize_guild_member_add_event(shard, payload)
        self._cache.update_user(event.user)  # TODO: do we still need this here if user is set in set member?
        # or should those be switched?
        self._cache.update_member(event.member)
        await self.dispatch(event)

    async def on_guild_member_remove(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-member-remove for more info."""
        event = self._app.event_factory.deserialize_guild_member_remove_event(shard, payload)
        self._cache.update_user(event.user)
        self._cache.delete_member(event.guild_id, event.user.id)
        await self.dispatch(event)

    async def on_guild_member_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-member-update for more info."""
        event = self._app.event_factory.deserialize_guild_member_update_event(shard, payload)
        self._cache.update_member(event.member)
        await self.dispatch(event)

    async def on_guild_members_chunk(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-members-chunk for more info."""
        event = self._app.event_factory.deserialize_guild_member_chunk_event(shard, payload)

        for member in event.members.values():
            self._cache.set_member(member)

        for presence in event.presences.values():
            self._cache.set_presence(presence)

        await self.dispatch(event)

    async def on_guild_role_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-role-create for more info."""
        event = self._app.event_factory.deserialize_guild_role_create_event(shard, payload)
        self._cache.set_role(event.role)
        await self.dispatch(event)

    async def on_guild_role_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-role-update for more info."""
        event = self._app.event_factory.deserialize_guild_role_update_event(shard, payload)
        self._cache.update_role(event.role)
        await self.dispatch(event)

    async def on_guild_role_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-role-delete for more info."""
        event = self._app.event_factory.deserialize_guild_role_delete_event(shard, payload)
        self._cache.delete_role(event.role_id)
        await self.dispatch(event)

    async def on_invite_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#invite-create for more info."""
        event = self._app.event_factory.deserialize_invite_create_event(shard, payload)
        self._cache.set_invite(event.invite)
        await self.dispatch(event)

    async def on_invite_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#invite-delete for more info."""
        event = self._app.event_factory.deserialize_invite_delete_event(shard, payload)
        self._cache.delete_invite(event.code)
        await self.dispatch(event)

    async def on_message_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-create for more info."""
        await self.dispatch(self._app.event_factory.deserialize_message_create_event(shard, payload))

    # TODO: message cache.

    async def on_message_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-update for more info."""
        await self.dispatch(self._app.event_factory.deserialize_message_update_event(shard, payload))

    async def on_message_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-delete for more info."""
        await self.dispatch(self._app.event_factory.deserialize_message_delete_event(shard, payload))

    async def on_message_delete_bulk(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-delete-bulk for more info."""
        await self.dispatch(self._app.event_factory.deserialize_message_delete_bulk_event(shard, payload))

    async def on_message_reaction_add(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-add for more info."""
        await self.dispatch(self._app.event_factory.deserialize_message_reaction_add_event(shard, payload))

    # TODO: this is unlikely but reaction cache?

    async def on_message_reaction_remove(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-remove for more info."""
        await self.dispatch(self._app.event_factory.deserialize_message_reaction_remove_event(shard, payload))

    async def on_message_reaction_remove_all(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-remove-all for more info."""
        await self.dispatch(self._app.event_factory.deserialize_message_reaction_remove_all_event(shard, payload))

    async def on_message_reaction_remove_emoji(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-remove-emoji for more info."""
        await self.dispatch(self._app.event_factory.deserialize_message_reaction_remove_emoji_event(shard, payload))

    async def on_presence_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#presence-update for more info."""
        event = self._app.event_factory.deserialize_presence_update_event(shard, payload)

        if event.presence.visible_status is presences.Status.OFFLINE:
            self._cache.delete_presence(event.presence.guild_id, event.presence.user_id)
        else:
            self._cache.update_presence(event.presence)

        # TODO: update user here when partial_user is set self._cache.update_user(event.partial_user)
        await self.dispatch(event)

    async def on_typing_start(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#typing-start for more info."""
        await self.dispatch(self._app.event_factory.deserialize_typing_start_event(shard, payload))

    async def on_user_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#user-update for more info."""
        event = self._app.event_factory.deserialize_own_user_update_event(shard, payload)
        self._cache.update_me(event.user)
        await self.dispatch(event)

    async def on_voice_state_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#voice-state-update for more info."""
        event = self._app.event_factory.deserialize_voice_state_update_event(shard, payload)

        if event.state.channel_id is None:
            self._cache.delete_voice_state(event.state.guild_id, event.state.user_id)
        else:
            self._cache.update_voice_state(event.state)

        await self.dispatch(event)

    async def on_voice_server_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#voice-server-update for more info."""
        await self.dispatch(self._app.event_factory.deserialize_voice_server_update_event(shard, payload))

    async def on_webhooks_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#webhooks-update for more info."""
        await self.dispatch(self._app.event_factory.deserialize_webhook_update_event(shard, payload))
