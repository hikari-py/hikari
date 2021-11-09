# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021 davfsa
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

__all__: typing.List[str] = ["EventManagerImpl"]

import asyncio
import base64
import random
import typing

from hikari import errors
from hikari import intents as intents_
from hikari import presences
from hikari import snowflakes
from hikari.impl import event_manager_base
from hikari.internal import time

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import invites
    from hikari import voices
    from hikari.api import cache as cache_
    from hikari.api import event_factory as event_factory_
    from hikari.api import shard as gateway_shard
    from hikari.events import guild_events as guild_events
    from hikari.internal import data_binding


def _fixed_size_nonce() -> str:
    # This generates nonces of length 28 for use in member chunking.
    head = time.monotonic_ns().to_bytes(8, "big")
    tail = random.getrandbits(92).to_bytes(12, "big")
    return base64.b64encode(head + tail).decode("ascii")


async def _request_guild_members(
    shard: gateway_shard.GatewayShard,
    guild: guilds.PartialGuild,
    *,
    include_presences: bool,
    nonce: str,
) -> None:
    try:
        await shard.request_guild_members(guild, include_presences=include_presences, nonce=nonce)

    # Ignore errors raised by a shard shutting down
    except errors.ComponentStateConflictError:
        pass


class EventManagerImpl(event_manager_base.EventManagerBase):
    """Provides event handling logic for Discord events."""

    __slots__: typing.Sequence[str] = ("_cache",)

    def __init__(
        self,
        event_factory: event_factory_.EventFactory,
        intents: intents_.Intents,
        /,
        *,
        cache: typing.Optional[cache_.MutableCache] = None,
    ) -> None:
        self._cache = cache
        super().__init__(event_factory=event_factory, intents=intents)

    async def on_ready(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#ready for more info."""
        # TODO: cache unavailable guilds on startup, I didn't bother for the time being.
        event = self._event_factory.deserialize_ready_event(shard, payload)

        if self._cache:
            self._cache.update_me(event.my_user)

        await self.dispatch(event)

    async def on_resumed(self, shard: gateway_shard.GatewayShard, _: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#resumed for more info."""
        await self.dispatch(self._event_factory.deserialize_resumed_event(shard))

    async def on_channel_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-create for more info."""
        event = self._event_factory.deserialize_guild_channel_create_event(shard, payload)

        if self._cache:
            self._cache.set_guild_channel(event.channel)

        await self.dispatch(event)

    async def on_channel_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-update for more info."""
        old = self._cache.get_guild_channel(snowflakes.Snowflake(payload["id"])) if self._cache else None
        event = self._event_factory.deserialize_guild_channel_update_event(shard, payload, old_channel=old)

        if self._cache:
            self._cache.update_guild_channel(event.channel)

        await self.dispatch(event)

    async def on_channel_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-delete for more info."""
        event = self._event_factory.deserialize_guild_channel_delete_event(shard, payload)

        if self._cache:
            self._cache.delete_guild_channel(event.channel.id)

        await self.dispatch(event)

    async def on_channel_pins_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#channel-pins-update for more info."""
        # TODO: we need a method for this specifically
        await self.dispatch(self._event_factory.deserialize_channel_pins_update_event(shard, payload))

    async def on_guild_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-create for more info."""
        event: typing.Union[guild_events.GuildAvailableEvent, guild_events.GuildJoinEvent]

        if "unavailable" in payload:
            event = self._event_factory.deserialize_guild_available_event(shard, payload)
        else:
            event = self._event_factory.deserialize_guild_join_event(shard, payload)

        if self._cache:
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

            self._cache.clear_voice_states_for_guild(event.guild.id)
            for voice_state in event.voice_states.values():
                self._cache.set_voice_state(voice_state)

            members_declared = self._intents & intents_.Intents.GUILD_MEMBERS
            presences_declared = self._intents & intents_.Intents.GUILD_PRESENCES

            # When intents are enabled discord will only send other member objects on the guild create
            # payload if presence intents are also declared, so if this isn't the case then we also want
            # to chunk small guilds.
            if members_declared and (event.guild.is_large or not presences_declared):
                # We create a task here instead of awaiting the result to avoid any rate-limits from delaying dispatch.
                nonce = f"{shard.id}.{_fixed_size_nonce()}"
                event.chunk_nonce = nonce
                coroutine = _request_guild_members(
                    shard, event.guild, include_presences=bool(presences_declared), nonce=nonce
                )
                asyncio.create_task(coroutine, name=f"{shard.id}:{event.guild.id} guild create members request")

        await self.dispatch(event)

    async def on_guild_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-update for more info."""
        old = self._cache.get_guild(snowflakes.Snowflake(payload["id"])) if self._cache else None
        event = self._event_factory.deserialize_guild_update_event(shard, payload, old_guild=old)

        if self._cache:
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
            event = self._event_factory.deserialize_guild_unavailable_event(shard, payload)

            if self._cache:
                self._cache.set_guild_availability(event.guild_id, False)

        else:
            old: typing.Optional[guilds.GatewayGuild] = None
            if self._cache:
                guild_id = snowflakes.Snowflake(payload["id"])
                #  TODO: this doesn't work in all intent scenarios
                old = self._cache.delete_guild(guild_id)
                self._cache.clear_voice_states_for_guild(guild_id)
                self._cache.clear_invites_for_guild(guild_id)
                self._cache.clear_members_for_guild(guild_id)
                self._cache.clear_presences_for_guild(guild_id)
                self._cache.clear_guild_channels_for_guild(guild_id)
                self._cache.clear_emojis_for_guild(guild_id)
                self._cache.clear_roles_for_guild(guild_id)

            event = self._event_factory.deserialize_guild_leave_event(shard, payload, old_guild=old)

        await self.dispatch(event)

    async def on_guild_ban_add(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-ban-add for more info."""
        await self.dispatch(self._event_factory.deserialize_guild_ban_add_event(shard, payload))

    async def on_guild_ban_remove(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-ban-remove for more info."""
        await self.dispatch(self._event_factory.deserialize_guild_ban_remove_event(shard, payload))

    async def on_guild_emojis_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-emojis-update for more info."""
        guild_id = snowflakes.Snowflake(payload["guild_id"])
        old = list(self._cache.clear_emojis_for_guild(guild_id).values()) if self._cache else None

        event = self._event_factory.deserialize_guild_emojis_update_event(shard, payload, old_emojis=old)

        if self._cache:
            for emoji in event.emojis:
                self._cache.set_emoji(emoji)

        await self.dispatch(event)

    async def on_guild_integrations_update(self, _: gateway_shard.GatewayShard, __: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-integrations-update for more info."""
        # This is only here to stop this being logged or dispatched as an "unknown event".
        # This event is made redundant by INTEGRATION_CREATE/DELETE/UPDATE and is thus not parsed or dispatched.
        return None

    async def on_integration_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        event = self._event_factory.deserialize_integration_create_event(shard, payload)
        await self.dispatch(event)

    async def on_integration_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        event = self._event_factory.deserialize_integration_delete_event(shard, payload)
        await self.dispatch(event)

    async def on_integration_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        event = self._event_factory.deserialize_integration_update_event(shard, payload)
        await self.dispatch(event)

    async def on_guild_member_add(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-member-add for more info."""
        event = self._event_factory.deserialize_guild_member_add_event(shard, payload)

        if self._cache:
            self._cache.update_member(event.member)

        await self.dispatch(event)

    async def on_guild_member_remove(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-member-remove for more info."""
        old: typing.Optional[guilds.Member] = None
        if self._cache:
            old = self._cache.delete_member(
                snowflakes.Snowflake(payload["guild_id"]), snowflakes.Snowflake(payload["user"]["id"])
            )

        event = self._event_factory.deserialize_guild_member_remove_event(shard, payload, old_member=old)
        await self.dispatch(event)

    async def on_guild_member_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-member-update for more info."""
        old: typing.Optional[guilds.Member] = None
        if self._cache:
            old = self._cache.get_member(
                snowflakes.Snowflake(payload["guild_id"]), snowflakes.Snowflake(payload["user"]["id"])
            )

        event = self._event_factory.deserialize_guild_member_update_event(shard, payload, old_member=old)

        if self._cache:
            self._cache.update_member(event.member)

        await self.dispatch(event)

    async def on_guild_members_chunk(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-members-chunk for more info."""
        event = self._event_factory.deserialize_guild_member_chunk_event(shard, payload)

        if self._cache:
            for member in event.members.values():
                self._cache.set_member(member)

            for presence in event.presences.values():
                self._cache.set_presence(presence)

        await self.dispatch(event)

    async def on_guild_role_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-role-create for more info."""
        event = self._event_factory.deserialize_guild_role_create_event(shard, payload)

        if self._cache:
            self._cache.set_role(event.role)

        await self.dispatch(event)

    async def on_guild_role_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-role-update for more info."""
        old = self._cache.get_role(snowflakes.Snowflake(payload["role"]["id"])) if self._cache else None
        event = self._event_factory.deserialize_guild_role_update_event(shard, payload, old_role=old)

        if self._cache:
            self._cache.update_role(event.role)

        await self.dispatch(event)

    async def on_guild_role_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#guild-role-delete for more info."""
        old: typing.Optional[guilds.Role] = None
        if self._cache:
            old = self._cache.delete_role(snowflakes.Snowflake(payload["role_id"]))

        event = self._event_factory.deserialize_guild_role_delete_event(shard, payload, old_role=old)

        await self.dispatch(event)

    async def on_invite_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#invite-create for more info."""
        event = self._event_factory.deserialize_invite_create_event(shard, payload)

        if self._cache:
            self._cache.set_invite(event.invite)

        await self.dispatch(event)

    async def on_invite_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#invite-delete for more info."""
        old: typing.Optional[invites.InviteWithMetadata] = None
        if self._cache:
            old = self._cache.delete_invite(payload["code"])

        event = self._event_factory.deserialize_invite_delete_event(shard, payload, old_invite=old)

        await self.dispatch(event)

    async def on_message_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-create for more info."""
        event = self._event_factory.deserialize_message_create_event(shard, payload)

        if self._cache:
            self._cache.set_message(event.message)

        await self.dispatch(event)

    async def on_message_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-update for more info."""
        old = self._cache.get_message(snowflakes.Snowflake(payload["id"])) if self._cache else None
        event = self._event_factory.deserialize_message_update_event(shard, payload, old_message=old)

        if self._cache:
            self._cache.update_message(event.message)

        await self.dispatch(event)

    async def on_message_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-delete for more info."""
        if self._cache:
            message_id = snowflakes.Snowflake(payload["id"])
            old_message = self._cache.delete_message(message_id)
        else:
            old_message = None

        event = self._event_factory.deserialize_message_delete_event(shard, payload, old_message=old_message)

        await self.dispatch(event)

    async def on_message_delete_bulk(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-delete-bulk for more info."""
        old_messages = {}

        if self._cache:
            for message_id in payload["ids"]:
                message_id = snowflakes.Snowflake(message_id)

                if message := self._cache.delete_message(message_id):
                    old_messages[message_id] = message

        await self.dispatch(
            self._event_factory.deserialize_guild_message_delete_bulk_event(shard, payload, old_messages=old_messages)
        )

    async def on_message_reaction_add(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-add for more info."""
        await self.dispatch(self._event_factory.deserialize_message_reaction_add_event(shard, payload))

    # TODO: this is unlikely but reaction cache?

    async def on_message_reaction_remove(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-remove for more info."""
        await self.dispatch(self._event_factory.deserialize_message_reaction_remove_event(shard, payload))

    async def on_message_reaction_remove_all(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-remove-all for more info."""
        await self.dispatch(self._event_factory.deserialize_message_reaction_remove_all_event(shard, payload))

    async def on_message_reaction_remove_emoji(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#message-reaction-remove-emoji for more info."""
        await self.dispatch(self._event_factory.deserialize_message_reaction_remove_emoji_event(shard, payload))

    async def on_presence_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#presence-update for more info."""
        old: typing.Optional[presences.MemberPresence] = None
        if self._cache:
            old = self._cache.get_presence(
                snowflakes.Snowflake(payload["guild_id"]), snowflakes.Snowflake(payload["user"]["id"])
            )

        event = self._event_factory.deserialize_presence_update_event(shard, payload, old_presence=old)

        if self._cache and event.presence.visible_status is presences.Status.OFFLINE:
            self._cache.delete_presence(event.presence.guild_id, event.presence.user_id)
        elif self._cache:
            self._cache.update_presence(event.presence)

        # TODO: update user here when partial_user is set self._cache.update_user(event.partial_user)
        await self.dispatch(event)

    async def on_typing_start(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#typing-start for more info."""
        await self.dispatch(self._event_factory.deserialize_typing_start_event(shard, payload))

    async def on_user_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#user-update for more info."""
        old = self._cache.get_me() if self._cache else None
        event = self._event_factory.deserialize_own_user_update_event(shard, payload, old_user=old)

        if self._cache:
            self._cache.update_me(event.user)

        await self.dispatch(event)

    async def on_voice_state_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#voice-state-update for more info."""
        old: typing.Optional[voices.VoiceState] = None
        if self._cache:
            old = self._cache.get_voice_state(
                snowflakes.Snowflake(payload["guild_id"]), snowflakes.Snowflake(payload["user_id"])
            )

        event = self._event_factory.deserialize_voice_state_update_event(shard, payload, old_state=old)

        if self._cache and event.state.channel_id is None:
            self._cache.delete_voice_state(event.state.guild_id, event.state.user_id)
        elif self._cache:
            self._cache.update_voice_state(event.state)

        await self.dispatch(event)

    async def on_voice_server_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#voice-server-update for more info."""
        await self.dispatch(self._event_factory.deserialize_voice_server_update_event(shard, payload))

    async def on_webhooks_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#webhooks-update for more info."""
        await self.dispatch(self._event_factory.deserialize_webhook_update_event(shard, payload))

    async def on_interaction_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway#interaction-create for more info."""
        await self.dispatch(self._event_factory.deserialize_interaction_create_event(shard, payload))
