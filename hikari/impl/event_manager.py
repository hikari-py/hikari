# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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

__all__: typing.Sequence[str] = ("EventManagerImpl",)

import asyncio
import base64
import logging
import random
import typing

from hikari import errors
from hikari import intents as intents_
from hikari import presences as presences_
from hikari import snowflakes
from hikari.api import config
from hikari.events import application_events
from hikari.events import auto_mod_events
from hikari.events import channel_events
from hikari.events import guild_events
from hikari.events import interaction_events
from hikari.events import member_events
from hikari.events import message_events
from hikari.events import monetization_events
from hikari.events import poll_events
from hikari.events import reaction_events
from hikari.events import role_events
from hikari.events import scheduled_events
from hikari.events import shard_events
from hikari.events import stage_events
from hikari.events import typing_events
from hikari.events import user_events
from hikari.events import voice_events
from hikari.impl import event_manager_base
from hikari.internal import time
from hikari.internal import ux

if typing.TYPE_CHECKING:
    from hikari import guilds
    from hikari import invites
    from hikari import voices
    from hikari.api import cache as cache_
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import event_factory as event_factory_
    from hikari.api import shard as gateway_shard
    from hikari.internal import data_binding


_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.event_manager")


def _fixed_size_nonce() -> str:
    # This generates nonces of length 28 for use in member chunking.
    head = time.time_ns().to_bytes(8, "big")
    tail = random.getrandbits(92).to_bytes(12, "big")
    return base64.b64encode(head + tail).decode("ascii")


async def _request_guild_members(
    shard: gateway_shard.GatewayShard,
    guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
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

    __slots__: typing.Sequence[str] = (
        "_auto_chunk_members",
        "_cache",
        "_entity_factory",
        "_guild_member_request_tasks",
    )

    def __init__(
        self,
        entity_factory: entity_factory_.EntityFactory,
        event_factory: event_factory_.EventFactory,
        intents: intents_.Intents,
        /,
        *,
        auto_chunk_members: bool = True,
        cache: cache_.MutableCache | None = None,
    ) -> None:
        self._cache = cache
        self._auto_chunk_members = auto_chunk_members
        self._entity_factory = entity_factory
        self._guild_member_request_tasks: set[asyncio.Task[None]] = set()

        components = cache.settings.components if cache else config.CacheComponents.NONE
        super().__init__(event_factory=event_factory, intents=intents, cache_components=components)

    def _cache_enabled_for(self, components: config.CacheComponents, /) -> bool:
        return self._cache is not None and (self._cache.settings.components & components) == components

    @event_manager_base.filtered(shard_events.ShardReadyEvent, config.CacheComponents.ME)
    def on_ready(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#ready for more info."""
        # TODO: cache unavailable guilds on startup, I didn't bother for the time being.
        event = self._event_factory.deserialize_ready_event(shard, payload)

        if self._cache:
            self._cache.update_me(event.my_user)

        self.dispatch(event)

    @event_manager_base.filtered(shard_events.ShardResumedEvent)
    def on_resumed(self, shard: gateway_shard.GatewayShard, _: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#resumed for more info."""
        self.dispatch(self._event_factory.deserialize_resumed_event(shard))

    @event_manager_base.filtered(application_events.ApplicationCommandPermissionsUpdateEvent)
    def on_application_command_permissions_update(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        self.dispatch(self._event_factory.deserialize_application_command_permission_update_event(shard, payload))

    @event_manager_base.filtered(channel_events.GuildChannelCreateEvent, config.CacheComponents.GUILD_CHANNELS)
    def on_channel_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#channel-create for more info."""
        event = self._event_factory.deserialize_guild_channel_create_event(shard, payload)

        if self._cache:
            self._cache.set_guild_channel(event.channel)

        self.dispatch(event)

    @event_manager_base.filtered(channel_events.GuildChannelUpdateEvent, config.CacheComponents.GUILD_CHANNELS)
    def on_channel_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#channel-update for more info."""
        old = self._cache.get_guild_channel(snowflakes.Snowflake(payload["id"])) if self._cache else None
        event = self._event_factory.deserialize_guild_channel_update_event(shard, payload, old_channel=old)

        if self._cache:
            self._cache.update_guild_channel(event.channel)

        self.dispatch(event)

    @event_manager_base.filtered(
        channel_events.GuildChannelDeleteEvent,
        config.CacheComponents.GUILD_CHANNELS | config.CacheComponents.GUILD_THREADS,
    )
    def on_channel_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#channel-delete for more info."""
        event = self._event_factory.deserialize_guild_channel_delete_event(shard, payload)

        if self._cache:
            self._cache.delete_guild_channel(event.channel.id)
            self._cache.clear_threads_for_channel(event.guild_id, event.channel.id)

        self.dispatch(event)

    @event_manager_base.filtered((channel_events.GuildPinsUpdateEvent, channel_events.DMPinsUpdateEvent))
    def on_channel_pins_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#channel-pins-update for more info."""
        # TODO: we need a method for this specifically
        self.dispatch(self._event_factory.deserialize_channel_pins_update_event(shard, payload))

    @event_manager_base.filtered(
        (channel_events.GuildThreadAccessEvent, channel_events.GuildThreadCreateEvent),
        config.CacheComponents.GUILD_THREADS,
    )
    def on_thread_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#thread-create for more info."""
        event: channel_events.GuildThreadAccessEvent | channel_events.GuildThreadCreateEvent
        if "newly_created" in payload:
            event = self._event_factory.deserialize_guild_thread_create_event(shard, payload)

        else:
            event = self._event_factory.deserialize_guild_thread_access_event(shard, payload)

        if self._cache:
            self._cache.set_thread(event.thread)

        self.dispatch(event)

    @event_manager_base.filtered(channel_events.GuildThreadUpdateEvent, config.CacheComponents.GUILD_THREADS)
    def on_thread_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#thread-update for more info."""
        old = self._cache.get_thread(snowflakes.Snowflake(payload["id"])) if self._cache else None
        event = self._event_factory.deserialize_guild_thread_update_event(shard, payload, old_thread=old)

        if self._cache:
            self._cache.update_thread(event.thread)

        self.dispatch(event)

    @event_manager_base.filtered(channel_events.GuildThreadDeleteEvent, config.CacheComponents.GUILD_THREADS)
    def on_thread_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#thread-delete for more info."""
        event = self._event_factory.deserialize_guild_thread_delete_event(shard, payload)

        if self._cache:
            self._cache.delete_thread(event.thread_id)

        self.dispatch(event)

    @event_manager_base.filtered(channel_events.ThreadListSyncEvent, config.CacheComponents.GUILD_THREADS)
    def on_thread_list_sync(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#thread-list-sync for more info."""
        event = self._event_factory.deserialize_thread_list_sync_event(shard, payload)

        if self._cache:
            if event.channel_ids:
                for channel_id in event.channel_ids:
                    self._cache.clear_threads_for_channel(event.guild_id, channel_id)

            else:
                self._cache.clear_threads_for_guild(event.guild_id)

            for thread in event.threads.values():
                self._cache.set_thread(thread)

        self.dispatch(event)

    @event_manager_base.filtered(channel_events.ThreadMembersUpdateEvent, config.CacheComponents.GUILD_THREADS)
    def on_thread_members_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#thread-members-update for more info."""
        event = self._event_factory.deserialize_thread_members_update_event(shard, payload)

        if self._cache:
            user_id = event.shard.get_user_id()

            # We only care about us being removed here. When we are added, we will receive a THREAD_CREATE with
            # all the other info.
            if user_id in event.removed_member_ids:
                self._cache.delete_thread(event.thread_id)

        self.dispatch(event)

    # Internal granularity is preferred for GUILD_CREATE over decorator based filtering due to its large scope.
    def on_guild_create(  # noqa: C901, PLR0912, PLR0915 - Function too complex, too many branches and too long
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-create for more info."""
        event: guild_events.GuildAvailableEvent | guild_events.GuildJoinEvent | None

        unavailable = payload.get("unavailable")

        if unavailable:
            # It is possible for GUILD_CREATE to contain unavailable guilds during outages
            # In cases like this, we can just ignore the event and wait for the outage to
            # be resolved, where the correct guild visibility event will be dispatched
            return

        if unavailable is not None and self._enabled_for_event(guild_events.GuildAvailableEvent):
            event = self._event_factory.deserialize_guild_available_event(shard, payload)
        elif unavailable is None and self._enabled_for_event(guild_events.GuildJoinEvent):
            event = self._event_factory.deserialize_guild_join_event(shard, payload)
        else:
            event = None

        if event:
            # We also filter here to prevent iterating over them and calling a function that won't do anything
            channels = event.channels if self._cache_enabled_for(config.CacheComponents.GUILD_CHANNELS) else None
            emojis = event.emojis if self._cache_enabled_for(config.CacheComponents.EMOJIS) else None
            stickers = event.stickers if self._cache_enabled_for(config.CacheComponents.GUILD_STICKERS) else None
            guild = event.guild if self._cache_enabled_for(config.CacheComponents.GUILDS) else None
            guild_id = event.guild.id
            members = event.members if self._cache_enabled_for(config.CacheComponents.MEMBERS) else None
            presences = event.presences if self._cache_enabled_for(config.CacheComponents.PRESENCES) else None
            roles = event.roles if self._cache_enabled_for(config.CacheComponents.ROLES) else None
            voice_states = event.voice_states if self._cache_enabled_for(config.CacheComponents.VOICE_STATES) else None
            threads = event.threads if self._cache_enabled_for(config.CacheComponents.GUILD_THREADS) else None

        elif self._cache:
            _LOGGER.log(ux.TRACE, "Skipping on_guild_create dispatch due to lack of any registered listeners")
            gd = self._entity_factory.deserialize_gateway_guild(payload, user_id=shard.get_user_id())

            channels = gd.channels() if self._cache_enabled_for(config.CacheComponents.GUILD_CHANNELS) else None
            emojis = gd.emojis() if self._cache_enabled_for(config.CacheComponents.EMOJIS) else None
            stickers = gd.stickers() if self._cache_enabled_for(config.CacheComponents.GUILD_STICKERS) else None
            guild = gd.guild() if self._cache_enabled_for(config.CacheComponents.GUILDS) else None
            guild_id = gd.id
            members = gd.members() if self._cache_enabled_for(config.CacheComponents.MEMBERS) else None
            presences = gd.presences() if self._cache_enabled_for(config.CacheComponents.PRESENCES) else None
            roles = gd.roles() if self._cache_enabled_for(config.CacheComponents.ROLES) else None
            voice_states = gd.voice_states() if self._cache_enabled_for(config.CacheComponents.VOICE_STATES) else None
            threads = gd.threads() if self._cache_enabled_for(config.CacheComponents.GUILD_THREADS) else None

        else:
            _LOGGER.log(
                ux.TRACE, "Skipping on_guild_create raw dispatch due to lack of any registered listeners or cache need"
            )

            channels = None
            emojis = None
            stickers = None
            guild = None
            guild_id = snowflakes.Snowflake(payload["id"])
            members = None
            presences = None
            roles = None
            voice_states = None
            threads = None

        if self._cache:
            if guild:
                self._cache.update_guild(guild)

            if channels:
                self._cache.clear_guild_channels_for_guild(guild_id)
                for channel in channels.values():
                    self._cache.set_guild_channel(channel)

            if emojis:
                self._cache.clear_emojis_for_guild(guild_id)
                for emoji in emojis.values():
                    self._cache.set_emoji(emoji)

            if stickers:
                self._cache.clear_stickers_for_guild(guild_id)
                for sticker in stickers.values():
                    self._cache.set_sticker(sticker)

            if roles:
                self._cache.clear_roles_for_guild(guild_id)
                for role in roles.values():
                    self._cache.set_role(role)

            if members:
                # TODO: do we really want to invalidate these all after an outage.
                self._cache.clear_members_for_guild(guild_id)
                if not self._cache.settings.only_my_member:
                    for member in members.values():
                        self._cache.set_member(member)
                else:
                    my_member = members[shard.get_user_id()]
                    self._cache.set_member(my_member)

            if presences:
                self._cache.clear_presences_for_guild(guild_id)
                for presence in presences.values():
                    self._cache.set_presence(presence)

            if voice_states:
                self._cache.clear_voice_states_for_guild(guild_id)
                for voice_state in voice_states.values():
                    self._cache.set_voice_state(voice_state)

            if threads:
                self._cache.clear_threads_for_guild(guild_id)
                for thread in threads.values():
                    self._cache.set_thread(thread)

        # We only want to chunk if we are allowed and need to:
        #   Allowed?
        #       All the following must be true:
        #           1. [`auto_chunk_members`][] is true (the user wants us to).
        #           2. We have the necessary intents ([`GUILD_MEMBERS`][]).
        #           3. The guild is marked as "large" or we do not have [`GUILD_PRESENCES`][] intent
        #              Discord will only send every other member objects on the `GUILD_CREATE`
        #              payload if presence intents are also declared, so if this isn't the case then we also
        #              want to chunk small guilds.
        #
        #   Need to?
        #       One of the following must be true:
        #           1. We have a cache, and it requires it (it is enabled for [`MEMBERS`][]), but we are
        #              not limited to only our own member (which is included in the `GUILD_CREATE` payload).
        #           2. The user is waiting for the member chunks (there is an event listener for it).
        presences_declared = bool(self._intents & intents_.Intents.GUILD_PRESENCES)

        if (
            self._auto_chunk_members
            and self._intents & intents_.Intents.GUILD_MEMBERS
            and (payload.get("large") or not presences_declared)
            and (
                (
                    self._cache
                    and self._cache_enabled_for(config.CacheComponents.MEMBERS)
                    and not self._cache.settings.only_my_member
                )
                # This call is a bit expensive, so best to do it last
                or self._enabled_for_event(shard_events.MemberChunkEvent)
            )
        ):
            nonce = f"{shard.id}.{_fixed_size_nonce()}"

            if event:
                event.chunk_nonce = nonce

            # We create a task here instead of awaiting the result to avoid any rate-limits from delaying dispatch.
            task = asyncio.create_task(
                _request_guild_members(shard, guild_id, include_presences=presences_declared, nonce=nonce),
                name=f"{shard.id}:{guild_id} guild create members request",
            )

            self._guild_member_request_tasks.add(task)
            task.add_done_callback(self._guild_member_request_tasks.discard)

        if event:
            self.dispatch(event)

    # Internal granularity is preferred for GUILD_UPDATE over decorator based filtering due to its large scope.
    def on_guild_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-update for more info."""
        event: guild_events.GuildUpdateEvent | None
        if self._enabled_for_event(guild_events.GuildUpdateEvent):
            guild_id = snowflakes.Snowflake(payload["id"])
            old = self._cache.get_guild(guild_id) if self._cache else None
            event = self._event_factory.deserialize_guild_update_event(shard, payload, old_guild=old)

            # We also filter here to prevent iterating over them and calling a function that won't do anything
            emojis = event.emojis if self._cache_enabled_for(config.CacheComponents.EMOJIS) else None
            stickers = event.stickers if self._cache_enabled_for(config.CacheComponents.GUILD_STICKERS) else None
            guild = event.guild if self._cache_enabled_for(config.CacheComponents.GUILDS) else None
            roles = event.roles if self._cache_enabled_for(config.CacheComponents.ROLES) else None

        elif self._cache:
            _LOGGER.log(ux.TRACE, "Skipping on_guild_update raw dispatch due to lack of any registered listeners")
            event = None

            gd = self._entity_factory.deserialize_gateway_guild(payload, user_id=shard.get_user_id())
            emojis = gd.emojis() if self._cache_enabled_for(config.CacheComponents.EMOJIS) else None
            stickers = gd.stickers() if self._cache_enabled_for(config.CacheComponents.GUILD_STICKERS) else None
            guild = gd.guild() if self._cache_enabled_for(config.CacheComponents.GUILDS) else None
            guild_id = gd.id
            roles = gd.roles() if self._cache_enabled_for(config.CacheComponents.ROLES) else None

        else:
            _LOGGER.log(
                ux.TRACE, "Skipping on_guild_update raw dispatch due to lack of any registered listeners or cache need"
            )
            return

        if self._cache:
            if guild:
                self._cache.update_guild(guild)

            if emojis:
                self._cache.clear_emojis_for_guild(guild_id)
                for emoji in emojis.values():
                    self._cache.set_emoji(emoji)

            if stickers:
                self._cache.clear_stickers_for_guild(guild_id)
                for sticker in stickers.values():
                    self._cache.set_sticker(sticker)

            if roles:
                self._cache.clear_roles_for_guild(guild_id)
                for role in roles.values():
                    self._cache.set_role(role)

        if event:
            self.dispatch(event)

    @event_manager_base.filtered(
        (guild_events.GuildLeaveEvent, guild_events.GuildUnavailableEvent),
        config.CacheComponents.GUILDS
        | config.CacheComponents.GUILD_CHANNELS
        | config.CacheComponents.EMOJIS
        | config.CacheComponents.GUILD_STICKERS
        | config.CacheComponents.ROLES
        | config.CacheComponents.PRESENCES
        | config.CacheComponents.VOICE_STATES
        | config.CacheComponents.MEMBERS
        | config.CacheComponents.GUILD_THREADS,
    )
    def on_guild_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-delete for more info."""
        event: guild_events.GuildUnavailableEvent | guild_events.GuildLeaveEvent
        if payload.get("unavailable"):
            event = self._event_factory.deserialize_guild_unavailable_event(shard, payload)

            if self._cache:
                self._cache.set_guild_availability(event.guild_id, False)

        else:
            old: guilds.GatewayGuild | None = None
            if self._cache:
                guild_id = snowflakes.Snowflake(payload["id"])
                #  TODO: this doesn't work in all intent scenarios
                old = self._cache.delete_guild(guild_id)
                self._cache.clear_voice_states_for_guild(guild_id)
                self._cache.clear_invites_for_guild(guild_id)
                self._cache.clear_members_for_guild(guild_id)
                self._cache.clear_presences_for_guild(guild_id)
                self._cache.clear_guild_channels_for_guild(guild_id)
                self._cache.clear_threads_for_guild(guild_id)
                self._cache.clear_emojis_for_guild(guild_id)
                self._cache.clear_stickers_for_guild(guild_id)
                self._cache.clear_roles_for_guild(guild_id)

            event = self._event_factory.deserialize_guild_leave_event(shard, payload, old_guild=old)

        self.dispatch(event)

    @event_manager_base.filtered(guild_events.BanCreateEvent)
    def on_guild_ban_add(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-ban-add for more info."""
        self.dispatch(self._event_factory.deserialize_guild_ban_add_event(shard, payload))

    @event_manager_base.filtered(guild_events.BanDeleteEvent)
    def on_guild_ban_remove(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-ban-remove for more info."""
        self.dispatch(self._event_factory.deserialize_guild_ban_remove_event(shard, payload))

    @event_manager_base.filtered(guild_events.EmojisUpdateEvent, config.CacheComponents.EMOJIS)
    def on_guild_emojis_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-emojis-update for more info."""
        guild_id = snowflakes.Snowflake(payload["guild_id"])
        old = list(self._cache.clear_emojis_for_guild(guild_id).values()) if self._cache else None

        event = self._event_factory.deserialize_guild_emojis_update_event(shard, payload, old_emojis=old)

        if self._cache:
            for emoji in event.emojis:
                self._cache.set_emoji(emoji)

        self.dispatch(event)

    @event_manager_base.filtered(guild_events.StickersUpdateEvent, config.CacheComponents.EMOJIS)
    def on_guild_stickers_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-stickers-update for more info."""
        guild_id = snowflakes.Snowflake(payload["guild_id"])
        old = list(self._cache.clear_stickers_for_guild(guild_id).values()) if self._cache else None

        event = self._event_factory.deserialize_guild_stickers_update_event(shard, payload, old_stickers=old)

        if self._cache:
            for sticker in event.stickers:
                self._cache.set_sticker(sticker)

        self.dispatch(event)

    @event_manager_base.filtered(())  # An empty sequence here means that this method will always be skipped.
    def on_guild_integrations_update(self, _: gateway_shard.GatewayShard, __: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-integrations-update for more info."""
        # This is only here to stop this being logged or dispatched as an "unknown event".
        # This event is made redundant by INTEGRATION_CREATE/DELETE/UPDATE and is thus not parsed or dispatched.
        raise NotImplementedError

    @event_manager_base.filtered(guild_events.IntegrationCreateEvent)
    def on_integration_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        event = self._event_factory.deserialize_integration_create_event(shard, payload)
        self.dispatch(event)

    @event_manager_base.filtered(guild_events.IntegrationUpdateEvent)
    def on_integration_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        event = self._event_factory.deserialize_integration_update_event(shard, payload)
        self.dispatch(event)

    @event_manager_base.filtered(guild_events.IntegrationDeleteEvent)
    def on_integration_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        event = self._event_factory.deserialize_integration_delete_event(shard, payload)
        self.dispatch(event)

    @event_manager_base.filtered(member_events.MemberCreateEvent, config.CacheComponents.MEMBERS)
    def on_guild_member_add(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-member-add for more info."""
        event = self._event_factory.deserialize_guild_member_add_event(shard, payload)

        if self._cache:
            self._cache.update_member(event.member)

        self.dispatch(event)

    @event_manager_base.filtered(member_events.MemberDeleteEvent, config.CacheComponents.MEMBERS)
    def on_guild_member_remove(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-member-remove for more info."""
        old: guilds.Member | None = None
        if self._cache:
            old = self._cache.delete_member(
                snowflakes.Snowflake(payload["guild_id"]), snowflakes.Snowflake(payload["user"]["id"])
            )

        event = self._event_factory.deserialize_guild_member_remove_event(shard, payload, old_member=old)
        self.dispatch(event)

    @event_manager_base.filtered(member_events.MemberUpdateEvent, config.CacheComponents.MEMBERS)
    def on_guild_member_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-member-update for more info."""
        old: guilds.Member | None = None
        if self._cache:
            old = self._cache.get_member(
                snowflakes.Snowflake(payload["guild_id"]), snowflakes.Snowflake(payload["user"]["id"])
            )

        event = self._event_factory.deserialize_guild_member_update_event(shard, payload, old_member=old)

        if self._cache:
            self._cache.update_member(event.member)

        self.dispatch(event)

    @event_manager_base.filtered(shard_events.MemberChunkEvent, config.CacheComponents.MEMBERS)
    def on_guild_members_chunk(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-members-chunk for more info."""
        event = self._event_factory.deserialize_guild_member_chunk_event(shard, payload)

        if self._cache:
            for member in event.members.values():
                self._cache.set_member(member)

            for presence in event.presences.values():
                self._cache.set_presence(presence)

        self.dispatch(event)

    @event_manager_base.filtered(role_events.RoleCreateEvent, config.CacheComponents.ROLES)
    def on_guild_role_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-role-create for more info."""
        event = self._event_factory.deserialize_guild_role_create_event(shard, payload)

        if self._cache:
            self._cache.set_role(event.role)

        self.dispatch(event)

    @event_manager_base.filtered(role_events.RoleUpdateEvent, config.CacheComponents.ROLES)
    def on_guild_role_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-role-update for more info."""
        old = self._cache.get_role(snowflakes.Snowflake(payload["role"]["id"])) if self._cache else None
        event = self._event_factory.deserialize_guild_role_update_event(shard, payload, old_role=old)

        if self._cache:
            self._cache.update_role(event.role)

        self.dispatch(event)

    @event_manager_base.filtered(role_events.RoleDeleteEvent, config.CacheComponents.ROLES)
    def on_guild_role_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-role-delete for more info."""
        old: guilds.Role | None = None
        if self._cache:
            old = self._cache.delete_role(snowflakes.Snowflake(payload["role_id"]))

        event = self._event_factory.deserialize_guild_role_delete_event(shard, payload, old_role=old)

        self.dispatch(event)

    @event_manager_base.filtered(channel_events.InviteCreateEvent, config.CacheComponents.INVITES)
    def on_invite_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#invite-create for more info."""
        event = self._event_factory.deserialize_invite_create_event(shard, payload)

        if self._cache:
            self._cache.set_invite(event.invite)

        self.dispatch(event)

    @event_manager_base.filtered(channel_events.InviteDeleteEvent, config.CacheComponents.INVITES)
    def on_invite_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#invite-delete for more info."""
        old: invites.InviteWithMetadata | None = None
        if self._cache:
            old = self._cache.delete_invite(payload["code"])

        event = self._event_factory.deserialize_invite_delete_event(shard, payload, old_invite=old)

        self.dispatch(event)

    @event_manager_base.filtered(
        (message_events.GuildMessageCreateEvent, message_events.DMMessageCreateEvent), config.CacheComponents.MESSAGES
    )
    def on_message_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#message-create for more info."""
        event = self._event_factory.deserialize_message_create_event(shard, payload)

        if self._cache:
            self._cache.set_message(event.message)

        self.dispatch(event)

    @event_manager_base.filtered(
        (message_events.GuildMessageUpdateEvent, message_events.DMMessageUpdateEvent), config.CacheComponents.MESSAGES
    )
    def on_message_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#message-update for more info."""
        old = self._cache.get_message(snowflakes.Snowflake(payload["id"])) if self._cache else None
        event = self._event_factory.deserialize_message_update_event(shard, payload, old_message=old)

        if self._cache:
            self._cache.update_message(event.message)

        self.dispatch(event)

    @event_manager_base.filtered(
        (message_events.GuildMessageDeleteEvent, message_events.DMMessageDeleteEvent), config.CacheComponents.MESSAGES
    )
    def on_message_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#message-delete for more info."""
        if self._cache:
            message_id = snowflakes.Snowflake(payload["id"])
            old_message = self._cache.delete_message(message_id)
        else:
            old_message = None

        event = self._event_factory.deserialize_message_delete_event(shard, payload, old_message=old_message)

        self.dispatch(event)

    @event_manager_base.filtered(
        (message_events.GuildMessageDeleteEvent, message_events.DMMessageDeleteEvent), config.CacheComponents.MESSAGES
    )
    def on_message_delete_bulk(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#message-delete-bulk for more info."""
        old_messages = {}

        if self._cache:
            for raw_message_id in payload["ids"]:
                message_id = snowflakes.Snowflake(raw_message_id)

                if message := self._cache.delete_message(message_id):
                    old_messages[message_id] = message

        self.dispatch(
            self._event_factory.deserialize_guild_message_delete_bulk_event(shard, payload, old_messages=old_messages)
        )

    @event_manager_base.filtered((reaction_events.GuildReactionAddEvent, reaction_events.DMReactionAddEvent))
    def on_message_reaction_add(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#message-reaction-add for more info."""
        self.dispatch(self._event_factory.deserialize_message_reaction_add_event(shard, payload))

    # TODO: this is unlikely but reaction cache?

    @event_manager_base.filtered((reaction_events.GuildReactionDeleteEvent, reaction_events.DMReactionDeleteEvent))
    def on_message_reaction_remove(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#message-reaction-remove for more info."""
        self.dispatch(self._event_factory.deserialize_message_reaction_remove_event(shard, payload))

    @event_manager_base.filtered(
        (reaction_events.GuildReactionDeleteAllEvent, reaction_events.DMReactionDeleteAllEvent)
    )
    def on_message_reaction_remove_all(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#message-reaction-remove-all for more info."""
        self.dispatch(self._event_factory.deserialize_message_reaction_remove_all_event(shard, payload))

    @event_manager_base.filtered(
        (reaction_events.GuildReactionDeleteEmojiEvent, reaction_events.DMReactionDeleteEmojiEvent)
    )
    def on_message_reaction_remove_emoji(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#message-reaction-remove-emoji for more info."""
        self.dispatch(self._event_factory.deserialize_message_reaction_remove_emoji_event(shard, payload))

    @event_manager_base.filtered(guild_events.PresenceUpdateEvent, config.CacheComponents.PRESENCES)
    def on_presence_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#presence-update for more info."""
        old: presences_.MemberPresence | None = None

        if self._cache:
            old = self._cache.get_presence(
                snowflakes.Snowflake(payload["guild_id"]), snowflakes.Snowflake(payload["user"]["id"])
            )

        event = self._event_factory.deserialize_presence_update_event(shard, payload, old_presence=old)

        if self._cache and event.presence.visible_status is presences_.Status.OFFLINE:
            self._cache.delete_presence(event.presence.guild_id, event.presence.user_id)
        elif self._cache:
            self._cache.update_presence(event.presence)

        # TODO: update user here when partial_user is set self._cache.update_user(event.partial_user)
        self.dispatch(event)

    @event_manager_base.filtered((typing_events.GuildTypingEvent, typing_events.DMTypingEvent))
    def on_typing_start(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#typing-start for more info."""
        self.dispatch(self._event_factory.deserialize_typing_start_event(shard, payload))

    @event_manager_base.filtered(user_events.OwnUserUpdateEvent, config.CacheComponents.ME)
    def on_user_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#user-update for more info."""
        old = self._cache.get_me() if self._cache else None
        event = self._event_factory.deserialize_own_user_update_event(shard, payload, old_user=old)

        if self._cache:
            self._cache.update_me(event.user)

        self.dispatch(event)

    @event_manager_base.filtered(voice_events.VoiceStateUpdateEvent, config.CacheComponents.VOICE_STATES)
    def on_voice_state_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#voice-state-update for more info."""
        old: voices.VoiceState | None = None
        if self._cache:
            old = self._cache.get_voice_state(
                snowflakes.Snowflake(payload["guild_id"]), snowflakes.Snowflake(payload["user_id"])
            )

        event = self._event_factory.deserialize_voice_state_update_event(shard, payload, old_state=old)

        if self._cache and event.state.channel_id is None:
            self._cache.delete_voice_state(event.state.guild_id, event.state.user_id)
        elif self._cache:
            self._cache.update_voice_state(event.state)

        self.dispatch(event)

    @event_manager_base.filtered(voice_events.VoiceServerUpdateEvent)
    def on_voice_server_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#voice-server-update for more info."""
        self.dispatch(self._event_factory.deserialize_voice_server_update_event(shard, payload))

    @event_manager_base.filtered(channel_events.WebhookUpdateEvent)
    def on_webhooks_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#webhooks-update for more info."""
        self.dispatch(self._event_factory.deserialize_webhook_update_event(shard, payload))

    @event_manager_base.filtered(
        (
            interaction_events.CommandInteractionCreateEvent,
            interaction_events.ComponentInteractionCreateEvent,
            interaction_events.AutocompleteInteractionCreateEvent,
            interaction_events.ModalInteractionCreateEvent,
        )
    )
    def on_interaction_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#interaction-create for more info."""
        self.dispatch(self._event_factory.deserialize_interaction_create_event(shard, payload))

    @event_manager_base.filtered(scheduled_events.ScheduledEventCreateEvent)
    def on_guild_scheduled_event_create(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-scheduled-event-create for more info."""
        self.dispatch(self._event_factory.deserialize_scheduled_event_create_event(shard, payload))

    @event_manager_base.filtered(scheduled_events.ScheduledEventDeleteEvent)
    def on_guild_scheduled_event_delete(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-scheduled-event-delete for more info."""
        self.dispatch(self._event_factory.deserialize_scheduled_event_delete_event(shard, payload))

    @event_manager_base.filtered(scheduled_events.ScheduledEventUpdateEvent)
    def on_guild_scheduled_event_update(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-scheduled-event-update for more info."""
        self.dispatch(self._event_factory.deserialize_scheduled_event_update_event(shard, payload))

    @event_manager_base.filtered(scheduled_events.ScheduledEventUserAddEvent)
    def on_guild_scheduled_event_user_add(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-scheduled-event-user-add for more info."""  # noqa: E501
        self.dispatch(self._event_factory.deserialize_scheduled_event_user_add_event(shard, payload))

    @event_manager_base.filtered(scheduled_events.ScheduledEventUserRemoveEvent)
    def on_guild_scheduled_event_user_remove(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-scheduled-event-user-remove for more info."""  # noqa: E501
        self.dispatch(self._event_factory.deserialize_scheduled_event_user_remove_event(shard, payload))

    @event_manager_base.filtered(guild_events.AuditLogEntryCreateEvent)
    def on_guild_audit_log_entry_create(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#guild-audit-log-entry-create for more info."""
        self.dispatch(self._event_factory.deserialize_audit_log_entry_create_event(shard, payload))

    @event_manager_base.filtered(monetization_events.EntitlementCreateEvent)
    def on_entitlement_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#entitlement-create for more info."""
        self.dispatch(self._event_factory.deserialize_entitlement_create_event(shard, payload))

    @event_manager_base.filtered(monetization_events.EntitlementDeleteEvent)
    def on_entitlement_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#entitlement-delete for more info."""
        self.dispatch(self._event_factory.deserialize_entitlement_delete_event(shard, payload))

    @event_manager_base.filtered(monetization_events.EntitlementUpdateEvent)
    def on_entitlement_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#entitlement-update for more info."""
        self.dispatch(self._event_factory.deserialize_entitlement_update_event(shard, payload))

    @event_manager_base.filtered(stage_events.StageInstanceCreateEvent)
    def on_stage_instance_create(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        self.dispatch(self._event_factory.deserialize_stage_instance_create_event(shard, payload))

    @event_manager_base.filtered(stage_events.StageInstanceUpdateEvent)
    def on_stage_instance_update(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        self.dispatch(self._event_factory.deserialize_stage_instance_update_event(shard, payload))

    @event_manager_base.filtered(stage_events.StageInstanceDeleteEvent)
    def on_stage_instance_delete(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        self.dispatch(self._event_factory.deserialize_stage_instance_delete_event(shard, payload))

    @event_manager_base.filtered(poll_events.PollVoteCreateEvent)
    def on_message_poll_vote_add(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#message-poll-vote-add for more info."""
        self.dispatch(self._event_factory.deserialize_poll_vote_create_event(shard, payload))

    @event_manager_base.filtered(poll_events.PollVoteDeleteEvent)
    def on_message_poll_vote_remove(self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject) -> None:
        """See https://discord.com/developers/docs/topics/gateway-events#message-poll-vote-remove for more info."""
        self.dispatch(self._event_factory.deserialize_poll_vote_delete_event(shard, payload))

    @event_manager_base.filtered(auto_mod_events.AutoModRuleCreateEvent)
    def on_auto_moderation_rule_create(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#auto-moderation-rule-create for more info."""
        self.dispatch(self._event_factory.deserialize_auto_mod_rule_create_event(shard, payload))

    @event_manager_base.filtered(auto_mod_events.AutoModRuleUpdateEvent)
    def on_auto_moderation_rule_update(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#auto-moderation-rule-update for more info."""
        self.dispatch(self._event_factory.deserialize_auto_mod_rule_update_event(shard, payload))

    @event_manager_base.filtered(auto_mod_events.AutoModRuleDeleteEvent)
    def on_auto_moderation_rule_delete(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#auto-moderation-rule-delete for more info."""
        self.dispatch(self._event_factory.deserialize_auto_mod_rule_delete_event(shard, payload))

    @event_manager_base.filtered(auto_mod_events.AutoModActionExecutionEvent)
    def on_auto_moderation_action_execution(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> None:
        """See https://discord.com/developers/docs/topics/gateway#auto-moderation-action-execution for more info."""
        self.dispatch(self._event_factory.deserialize_auto_mod_action_execution_event(shard, payload))
