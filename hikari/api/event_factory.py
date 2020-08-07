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
"""Component that provides the ability to generate event models."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["IEventFactoryComponent"]

import abc
import datetime
import typing

from hikari.api import component

if typing.TYPE_CHECKING:
    from hikari.api import event_consumer
    from hikari.api import shard as gateway_shard
    from hikari.events import channel_events
    from hikari.events import guild_events
    from hikari.events import member_events
    from hikari.events import message_events
    from hikari.events import reaction_events
    from hikari.events import role_events
    from hikari.events import shard_events
    from hikari.events import typing_events
    from hikari.events import user_events
    from hikari.events import voice_events
    from hikari.models import channels as channel_models
    from hikari.models import guilds
    from hikari.models import presences as presence_models
    from hikari.utilities import data_binding
    from hikari.utilities import snowflake


class IEventFactoryComponent(component.IComponent):
    """Interface for components that deserialize JSON events."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def app(self) -> event_consumer.IEventConsumerApp:
        """Return the event dispatcher-compatible app this object is bound to.

        Returns
        -------
        hikari.api.event_dispatcher.IEventDispatcherApp
            The event dispatcher-compatible app that this object is bound to.
        """

    ##################
    # CHANNEL EVENTS #
    ##################

    @abc.abstractmethod
    def deserialize_channel_create_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.ChannelCreateEvent:
        """Parse a raw payload from Discord into a channel create event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel_events.ChannelCreateEvent
            The parsed channel create event object.
        """

    @abc.abstractmethod
    def deserialize_channel_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.ChannelUpdateEvent:
        """Parse a raw payload from Discord into a channel update event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel_events.ChannelUpdateEvent
            The parsed  event object.
        """

    @abc.abstractmethod
    def deserialize_channel_delete_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.ChannelDeleteEvent:
        """Parse a raw payload from Discord into a channel delete event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel_events.ChannelDeleteEvent
            The parsed channel delete event object.
        """

    @abc.abstractmethod
    def deserialize_channel_pins_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.PinsUpdateEvent:
        """Parse a raw payload from Discord into a channel pins update event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel_events.PinsUpdateEvent
            The parsed channel pins update event object.
        """

    @abc.abstractmethod
    def deserialize_webhook_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.WebhookUpdateEvent:
        """Parse a raw payload from Discord into a webhook update event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel_events.WebhookUpdateEvent
            The parsed webhook update event object.
        """

    @abc.abstractmethod
    def deserialize_typing_start_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> typing_events.TypingEvent:
        """Parse a raw payload from Discord into a typing start event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.typing_events.TypingEvent
            The parsed typing start event object.
        """

    @abc.abstractmethod
    def deserialize_invite_create_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.InviteCreateEvent:
        """Parse a raw payload from Discord into an invite create event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel_events.InviteCreateEvent
            The parsed invite create event object.
        """

    @abc.abstractmethod
    def deserialize_invite_delete_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.InviteDeleteEvent:
        """Parse a raw payload from Discord into an invite delete event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel_events.InviteDeleteEvent
            The parsed invite delete event object.
        """

    ################
    # GUILD EVENTS #
    ################

    @abc.abstractmethod
    def deserialize_guild_create_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildAvailableEvent:
        """Parse a raw payload from Discord into a guild create event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.GuildAvailableEvent
            The parsed guild create event object.
        """

    @abc.abstractmethod
    def deserialize_guild_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildUpdateEvent:
        """Parse a raw payload from Discord into a guild update event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.GuildUpdateEvent
            The parsed guild update event object.
        """

    @abc.abstractmethod
    def deserialize_guild_leave_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildLeaveEvent:
        """Parse a raw payload from Discord into a guild leave event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.GuildLeaveEvent
            The parsed guild leave event object.
        """

    @abc.abstractmethod
    def deserialize_guild_unavailable_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildUnavailableEvent:
        """Parse a raw payload from Discord into a guild unavailable event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.GuildUnavailableEvent
            The parsed guild unavailable event object.
        """

    @abc.abstractmethod
    def deserialize_guild_ban_add_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.BanCreateEvent:
        """Parse a raw payload from Discord into a guild ban add event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.BanCreateEvent
            The parsed guild ban add event object.
        """

    @abc.abstractmethod
    def deserialize_guild_ban_remove_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.BanDeleteEvent:
        """Parse a raw payload from Discord into a guild ban remove event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.BanDeleteEvent
            The parsed guild ban remove event object.
        """

    @abc.abstractmethod
    def deserialize_guild_emojis_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.EmojisUpdateEvent:
        """Parse a raw payload from Discord into a guild emojis update event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.EmojiUpdateEvent
            The parsed guild emojis update event object.
        """

    @abc.abstractmethod
    def deserialize_guild_integrations_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.IntegrationsUpdateEvent:
        """Parse a raw payload from Discord into a guilds integrations update event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.IntegrationsUpdateEvent
            The parsed guilds integrations update event object.
        """

    @abc.abstractmethod
    def deserialize_guild_member_add_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> member_events.MemberCreateEvent:
        """Parse a raw payload from Discord into a guild member add event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.member_events.MemberCreateEvent
            The parsed guild member add event object.
        """

    @abc.abstractmethod
    def deserialize_guild_member_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> member_events.MemberUpdateEvent:
        """Parse a raw payload from Discord into a guild member update event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.member_events.MemberUpdateEvent
            The parsed guild member update event object.
        """

    @abc.abstractmethod
    def deserialize_guild_member_remove_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> member_events.MemberDeleteEvent:
        """Parse a raw payload from Discord into a guild member remove event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.member_events.MemberDeleteEvent
            The parsed guild member remove event object.
        """

    @abc.abstractmethod
    def deserialize_guild_role_create_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> role_events.RoleCreateEvent:
        """Parse a raw payload from Discord into a guild role create event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.role_events.RoleCreateEvent
            The parsed guild role create event object.
        """

    @abc.abstractmethod
    def deserialize_guild_role_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> role_events.RoleUpdateEvent:
        """Parse a raw payload from Discord into a guild role update event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.role_events.RoleUpdateEvent
            The parsed guild role update event object.
        """

    @abc.abstractmethod
    def deserialize_guild_role_delete_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> role_events.RoleDeleteEvent:
        """Parse a raw payload from Discord into a guild role delete event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.role_events.RoleDeleteEvent
            The parsed guild role delete event object.
        """

    @abc.abstractmethod
    def deserialize_presence_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.PresenceUpdateEvent:
        """Parse a raw payload from Discord into a presence update event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.PresenceUpdateEvent
            The parsed presence update event object.
        """

    ##################
    # MESSAGE EVENTS #
    ##################

    @abc.abstractmethod
    def deserialize_message_create_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> message_events.MessageCreateEvent:
        """Parse a raw payload from Discord into a message create event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.message_events.MessageCreateEvent
            The parsed message create event object.
        """

    @abc.abstractmethod
    def deserialize_message_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> message_events.MessageUpdateEvent:
        """Parse a raw payload from Discord into a message update event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.message_events.MessageUpdateEvent
            The parsed message update event object.
        """

    @abc.abstractmethod
    def deserialize_message_delete_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> message_events.MessageDeleteEvent:
        """Parse a raw payload from Discord into a message delete event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.message_events.MessageDeleteEvent
            The parsed message delete event object.
        """

    @abc.abstractmethod
    def deserialize_message_delete_bulk_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> message_events.MessageBulkDeleteEvent:
        """Parse a raw payload from Discord into a message delete bulk event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.message_events.MessageBulkDeleteEvent
            The parsed message delete bulk event object.
        """

    @abc.abstractmethod
    def deserialize_message_reaction_add_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionAddEvent:
        """Parse a raw payload from Discord into a message reaction add event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.reaction_events.ReactionAddEvent
            The parsed message reaction add event object.
        """

    @abc.abstractmethod
    def deserialize_message_reaction_remove_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteEvent:
        """Parse a raw payload from Discord into a message reaction remove event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.reaction_events.ReactionDeleteEvent
            The parsed message reaction remove event object.
        """

    @abc.abstractmethod
    def deserialize_message_reaction_remove_all_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteAllEvent:
        """Parse a raw payload from Discord into a message reaction remove all event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.reaction_events.ReactionDeleteAllEvent
            The parsed message reaction remove all event object.
        """

    @abc.abstractmethod
    def deserialize_message_reaction_remove_emoji_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteEmojiEvent:
        """Parse a raw payload from Discord into a message reaction remove emoji event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.reaction_events.ReactionDeleteEmojiEvent
            The parsed message reaction remove emoji event object.
        """

    ################
    # OTHER EVENTS #
    ################

    @abc.abstractmethod
    def deserialize_ready_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject,
    ) -> shard_events.ShardReadyEvent:
        """Parse a raw payload from Discord into a ready event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.shard_events.ShardReadyEvent
            The parsed ready event object.
        """

    @abc.abstractmethod
    def deserialize_own_user_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> user_events.OwnUserUpdateEvent:
        """Parse a raw payload from Discord into a own user update event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.user_events.OwnUserUpdateEvent
            The parsed own user update event object.
        """

    @abc.abstractmethod
    def deserialize_guild_member_chunk_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.MemberChunkEvent:
        """Parse a raw payload from Discord into a member chunk event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.shard_events.MemberChunkEvent
            The parsed member chunk object.
        """

    ################
    # VOICE EVENTS #
    ################

    @abc.abstractmethod
    def deserialize_voice_state_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> voice_events.VoiceStateUpdateEvent:
        """Parse a raw payload from Discord into a voice state update event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.voice_events.VoiceStateUpdateEvent
            The parsed voice state update event object.
        """

    @abc.abstractmethod
    def deserialize_voice_server_update_event(
        self, shard: gateway_shard.IGatewayShard, payload: data_binding.JSONObject
    ) -> voice_events.VoiceServerUpdateEvent:
        """Parse a raw payload from Discord into a voice server update event object.

        Parameters
        ----------
        shard : hikari.api.shard.IGatewayShard
            The shard that emitted this event.
        payload : hikari.utilities.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.voice_events.VoiceServerUpdateEvent
            The parsed voice server update event object.
        """

    ###############################
    # GATEWAY-SPECIFIC UTILITIES. #
    ###############################

    @abc.abstractmethod
    def serialize_gateway_presence(
        self,
        idle_since: typing.Optional[datetime.datetime],
        afk: bool,
        status: presence_models.Status,
        activity: typing.Optional[presence_models.Activity],
    ) -> data_binding.JSONObject:
        """Serialize a set of presence parameters into a raw gateway payload.

        Parameters
        ----------
        idle_since : builtins.None or datetime.datetime
            The time that the user should appear to be idle since. If
            `builtins.None`, then the user is marked as not being idle.
        afk : builtins.bool
            If `builtins.True`, the user becomes AFK. This will move them to
            the guild's AFK channel if there is one set.
        status : hikari.models.presences.Status
            The status to display.
        activity : builtins.None or hikari.models.presences.Activity
            The activity to display, or `builtins.None` if no activity should
            be shown.

        Returns
        -------
        hikari.utilities.data_binding.JSONObject
            The serialized presence.
        """

    @abc.abstractmethod
    def serialize_gateway_voice_state_update(
        self,
        guild: snowflake.SnowflakeishOr[guilds.PartialGuild],
        channel: typing.Optional[snowflake.SnowflakeishOr[channel_models.GuildVoiceChannel]],
        self_mute: bool,
        self_deaf: bool,
    ) -> data_binding.JSONObject:
        """Serialize a voice state update payload into a raw gateway payload.

        Parameters
        ----------
        guild : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.guilds.Guild]
            The guild to update the voice state in.
        channel : hikari.utilities.snowflake.SnowflakeishOr[hikari.models.channels.GuildVoiceChannel] or builtins.None
            The voice channel to change to, or `builtins.None` if attempting to
            leave a voice channel and disconnect entirely.
        self_mute : builtins.bool
            `builtins.True` if the user should be muted, `builtins.False` if
            they should be unmuted.
        self_deaf : builtins.bool
            `builtins.True` if the user should be deafened, `builtins.False`
            if they should be able to hear other users.

        Returns
        -------
        hikari.utilities.data_binding.JSONObject
            The serialized payload.
        """
