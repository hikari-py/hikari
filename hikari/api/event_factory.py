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
"""Component that provides the ability to generate event models."""

from __future__ import annotations

__all__: typing.List[str] = ["EventFactory"]

import abc
import typing

if typing.TYPE_CHECKING:
    from hikari import channels as channel_models
    from hikari import emojis as emojis_models
    from hikari import guilds as guild_models
    from hikari import invites as invite_models
    from hikari import messages as messages_models
    from hikari import presences as presences_models
    from hikari import snowflakes
    from hikari import users as user_models
    from hikari import voices as voices_models
    from hikari.api import shard as gateway_shard
    from hikari.events import channel_events
    from hikari.events import guild_events
    from hikari.events import interaction_events
    from hikari.events import lifetime_events
    from hikari.events import member_events
    from hikari.events import message_events
    from hikari.events import reaction_events
    from hikari.events import role_events
    from hikari.events import shard_events
    from hikari.events import typing_events
    from hikari.events import user_events
    from hikari.events import voice_events
    from hikari.internal import data_binding


class EventFactory(abc.ABC):
    """Interface for components that deserialize JSON events."""

    __slots__: typing.Sequence[str] = ()

    ##################
    # CHANNEL EVENTS #
    ##################

    @abc.abstractmethod
    def deserialize_guild_channel_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.GuildChannelCreateEvent:
        """Parse a raw payload from Discord into a channel create event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel_events.GuildChannelCreateEvent
            The parsed channel create event object.
        """

    @abc.abstractmethod
    def deserialize_guild_channel_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_channel: typing.Optional[channel_models.GuildChannel],
    ) -> channel_events.GuildChannelUpdateEvent:
        """Parse a raw payload from Discord into a channel update event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_channel : typing.Optional[hikari.channels.GuildChannel]
            The guild channel object or `builtins.None`.

        Returns
        -------
        hikari.events.channel_events.GuildChannelUpdateEvent
            The parsed  event object.
        """

    @abc.abstractmethod
    def deserialize_guild_channel_delete_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.GuildChannelDeleteEvent:
        """Parse a raw payload from Discord into a channel delete event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel_events.GuildChannelDeleteEvent
            The parsed channel delete event object.
        """

    @abc.abstractmethod
    def deserialize_channel_pins_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.PinsUpdateEvent:
        """Parse a raw payload from Discord into a channel pins update event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel_events.PinsUpdateEvent
            The parsed channel pins update event object.
        """

    @abc.abstractmethod
    def deserialize_webhook_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.WebhookUpdateEvent:
        """Parse a raw payload from Discord into a webhook update event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel_events.WebhookUpdateEvent
            The parsed webhook update event object.
        """

    @abc.abstractmethod
    def deserialize_invite_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> channel_events.InviteCreateEvent:
        """Parse a raw payload from Discord into an invite create event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel_events.InviteCreateEvent
            The parsed invite create event object.
        """

    @abc.abstractmethod
    def deserialize_invite_delete_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_invite: typing.Optional[invite_models.InviteWithMetadata],
    ) -> channel_events.InviteDeleteEvent:
        """Parse a raw payload from Discord into an invite delete event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_invite: typing.Optional[hikari.invites.InviteWithMetadata]
            The invite object or `builtins.None`.

        Returns
        -------
        hikari.events.channel_events.InviteDeleteEvent
            The parsed invite delete event object.
        """

    #################
    # TYPING EVENTS #
    ##################

    @abc.abstractmethod
    def deserialize_typing_start_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> typing_events.TypingEvent:
        """Parse a raw payload from Discord into a typing start event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.typing_events.TypingEvent
            The parsed typing start event object.
        """

    ################
    # GUILD EVENTS #
    ################

    @abc.abstractmethod
    def deserialize_guild_available_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildAvailableEvent:
        """Parse a raw payload from Discord into a guild available event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.GuildAvailableEvent
            The parsed guild create event object.
        """

    @abc.abstractmethod
    def deserialize_guild_join_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildJoinEvent:
        """Parse a raw payload from Discord into a guild join event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.GuildJoinEvent
            The parsed guild join event object.
        """

    @abc.abstractmethod
    def deserialize_guild_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_guild: typing.Optional[guild_models.GatewayGuild],
    ) -> guild_events.GuildUpdateEvent:
        """Parse a raw payload from Discord into a guild update event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_guild : typing.Optional[hikari.guilds.GatewayGuild]
            The guild object or `builtins.None`.

        Returns
        -------
        hikari.events.guild_events.GuildUpdateEvent
            The parsed guild update event object.
        """

    @abc.abstractmethod
    def deserialize_guild_leave_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_guild: typing.Optional[guild_models.GatewayGuild],
    ) -> guild_events.GuildLeaveEvent:
        """Parse a raw payload from Discord into a guild leave event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_guild : typing.Optional[hikari.guilds.GatewayGuild]
            The guild object or `builtins.None`.

        Returns
        -------
        hikari.events.guild_events.GuildLeaveEvent
            The parsed guild leave event object.
        """

    @abc.abstractmethod
    def deserialize_guild_unavailable_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.GuildUnavailableEvent:
        """Parse a raw payload from Discord into a guild unavailable event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.GuildUnavailableEvent
            The parsed guild unavailable event object.
        """

    @abc.abstractmethod
    def deserialize_guild_ban_add_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.BanCreateEvent:
        """Parse a raw payload from Discord into a guild ban add event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.BanCreateEvent
            The parsed guild ban add event object.
        """

    @abc.abstractmethod
    def deserialize_guild_ban_remove_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.BanDeleteEvent:
        """Parse a raw payload from Discord into a guild ban remove event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.BanDeleteEvent
            The parsed guild ban remove event object.
        """

    @abc.abstractmethod
    def deserialize_guild_emojis_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_emojis: typing.Optional[typing.Sequence[emojis_models.KnownCustomEmoji]],
    ) -> guild_events.EmojisUpdateEvent:
        """Parse a raw payload from Discord into a guild emojis update event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_emojis : typing.Optional[typing.Sequence[hikari.emojis.KnownCustomEmoji]]
            The sequence of emojis or `builtins.None`.

        Returns
        -------
        hikari.events.guild_events.EmojisUpdateEvent
            The parsed guild emojis update event object.
        """

    @abc.abstractmethod
    def deserialize_integration_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.IntegrationCreateEvent:
        """Parse a raw payload from Discord into an integration create event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.IntegrationCreateEvent
            The parsed integration create event object.
        """

    @abc.abstractmethod
    def deserialize_integration_delete_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.IntegrationDeleteEvent:
        """Parse a raw payload from Discord into an integration delete event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.IntegrationDeleteEvent
            The parsed integration delete event object.
        """

    @abc.abstractmethod
    def deserialize_integration_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> guild_events.IntegrationUpdateEvent:
        """Parse a raw payload from Discord into an integration update event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild_events.IntegrationUpdateEvent
            The parsed integration update event object.
        """

    @abc.abstractmethod
    def deserialize_presence_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_presence: typing.Optional[presences_models.MemberPresence],
    ) -> guild_events.PresenceUpdateEvent:
        """Parse a raw payload from Discord into a presence update event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_presence: typing.Optional[hikari.presences.MemberPresence]
            The presence object or `builtins.None`.

        Returns
        -------
        hikari.events.guild_events.PresenceUpdateEvent
            The parsed presence update event object.
        """

    ######################
    # INTERACTION EVENTS #
    ######################

    @abc.abstractmethod
    def deserialize_interaction_create_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
    ) -> interaction_events.InteractionCreateEvent:
        """Parse a raw payload from Discord into a interaction create event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.interaction_events.InteractionCreateEvent
            The parsed interaction create event object.
        """

    #################
    # MEMBER EVENTS #
    #################

    @abc.abstractmethod
    def deserialize_guild_member_add_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> member_events.MemberCreateEvent:
        """Parse a raw payload from Discord into a guild member add event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.member_events.MemberCreateEvent
            The parsed guild member add event object.
        """

    @abc.abstractmethod
    def deserialize_guild_member_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_member: typing.Optional[guild_models.Member],
    ) -> member_events.MemberUpdateEvent:
        """Parse a raw payload from Discord into a guild member update event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_member: typing.Optional[hikari.guilds.Member]
            The member object or `builtins.None`.

        Returns
        -------
        hikari.events.member_events.MemberUpdateEvent
            The parsed guild member update event object.
        """

    @abc.abstractmethod
    def deserialize_guild_member_remove_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_member: typing.Optional[guild_models.Member],
    ) -> member_events.MemberDeleteEvent:
        """Parse a raw payload from Discord into a guild member remove event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_member: typing.Optional[hikari.guilds.Member]
            The member object or `builtins.None`.

        Returns
        -------
        hikari.events.member_events.MemberDeleteEvent
            The parsed guild member remove event object.
        """

    ###############
    # ROLE EVENTS #
    ###############

    @abc.abstractmethod
    def deserialize_guild_role_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> role_events.RoleCreateEvent:
        """Parse a raw payload from Discord into a guild role create event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.role_events.RoleCreateEvent
            The parsed guild role create event object.
        """

    @abc.abstractmethod
    def deserialize_guild_role_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_role: typing.Optional[guild_models.Role],
    ) -> role_events.RoleUpdateEvent:
        """Parse a raw payload from Discord into a guild role update event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_role: typing.Optional[hikari.guilds.Role]
            The role object or `builtins.None`.

        Returns
        -------
        hikari.events.role_events.RoleUpdateEvent
            The parsed guild role update event object.
        """

    @abc.abstractmethod
    def deserialize_guild_role_delete_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_role: typing.Optional[guild_models.Role],
    ) -> role_events.RoleDeleteEvent:
        """Parse a raw payload from Discord into a guild role delete event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_role: typing.Optional[hikari.guilds.Role]
            The role object or `builtins.None`.

        Returns
        -------
        hikari.events.role_events.RoleDeleteEvent
            The parsed guild role delete event object.
        """

    ###################
    # LIFETIME EVENTS #
    ###################

    @abc.abstractmethod
    def deserialize_starting_event(self) -> lifetime_events.StartingEvent:
        """Build a starting event object.

        Returns
        -------
        hikari.events.lifetime_events.StartingEvent
            The built starting event object.
        """

    @abc.abstractmethod
    def deserialize_started_event(self) -> lifetime_events.StartedEvent:
        """Build a started event object.

        Returns
        -------
        hikari.events.lifetime_events.StartingEvent
            The built started event object.
        """

    @abc.abstractmethod
    def deserialize_stopping_event(self) -> lifetime_events.StoppingEvent:
        """Build a starting event object.

        Returns
        -------
        hikari.events.lifetime_events.StartingEvent
            The built starting event object.
        """

    @abc.abstractmethod
    def deserialize_stopped_event(self) -> lifetime_events.StoppedEvent:
        """Build a stopped event object.

        Returns
        -------
        hikari.events.lifetime_events.StartingEvent
            The built starting event object.
        """

    ##################
    # MESSAGE EVENTS #
    ##################

    @abc.abstractmethod
    def deserialize_message_create_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> message_events.MessageCreateEvent:
        """Parse a raw payload from Discord into a message create event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.message_events.MessageCreateEvent
            The parsed message create event object.
        """

    @abc.abstractmethod
    def deserialize_message_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_message: typing.Optional[messages_models.PartialMessage],
    ) -> message_events.MessageUpdateEvent:
        """Parse a raw payload from Discord into a message update event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_message: typing.Optional[hikari.messages.PartialMessage]
            The message object or `builtins.None`.

        Returns
        -------
        hikari.events.message_events.MessageUpdateEvent
            The parsed message update event object.
        """

    @abc.abstractmethod
    def deserialize_message_delete_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_message: typing.Optional[messages_models.Message],
    ) -> message_events.MessageDeleteEvent:
        """Parse a raw payload from Discord into a message delete event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_message : typing.Optional[hikari.messages.Message]
            The old message object.

        Returns
        -------
        hikari.events.message_events.MessageDeleteEvent
            The parsed message delete event object.
        """

    @abc.abstractmethod
    def deserialize_guild_message_delete_bulk_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_messages: typing.Mapping[snowflakes.Snowflake, messages_models.Message],
    ) -> message_events.GuildBulkMessageDeleteEvent:
        """Parse a raw payload from Discord into a guild message delete bulk event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_messages : typing.Mapping[hikari.snowflakes.Snowflake, hikari.messages.Message]
            A mapping of the old message objects.

        Returns
        -------
        hikari.events.message_events.GuildBulkMessageDeleteEvent
            The parsed guild message delete bulk event object.
        """

    ###################
    # REACTION EVENTS #
    ###################

    @abc.abstractmethod
    def deserialize_message_reaction_add_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionAddEvent:
        """Parse a raw payload from Discord into a message reaction add event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.reaction_events.ReactionAddEvent
            The parsed message reaction add event object.
        """

    @abc.abstractmethod
    def deserialize_message_reaction_remove_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteEvent:
        """Parse a raw payload from Discord into a message reaction remove event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.reaction_events.ReactionDeleteEvent
            The parsed message reaction remove event object.
        """

    @abc.abstractmethod
    def deserialize_message_reaction_remove_all_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteAllEvent:
        """Parse a raw payload from Discord into a message reaction remove all event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.reaction_events.ReactionDeleteAllEvent
            The parsed message reaction remove all event object.
        """

    @abc.abstractmethod
    def deserialize_message_reaction_remove_emoji_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> reaction_events.ReactionDeleteEmojiEvent:
        """Parse a raw payload from Discord into a message reaction remove emoji event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.reaction_events.ReactionDeleteEmojiEvent
            The parsed message reaction remove emoji event object.
        """

    ################
    # SHARD EVENTS #
    ################

    @abc.abstractmethod
    def deserialize_shard_payload_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject, *, name: str
    ) -> shard_events.ShardPayloadEvent:
        """Parse a raw payload from Discord into a shard payload event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        name : builtins.str
            Name of the event.

        Returns
        -------
        hikari.events.shard_events.ShardPayloadEvent
            The parsed shard payload event object.
        """

    @abc.abstractmethod
    def deserialize_ready_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
    ) -> shard_events.ShardReadyEvent:
        """Parse a raw payload from Discord into a ready event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.shard_events.ShardReadyEvent
            The parsed ready event object.
        """

    @abc.abstractmethod
    def deserialize_connected_event(self, shard: gateway_shard.GatewayShard) -> shard_events.ShardConnectedEvent:
        """Build a shard connected event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.

        Returns
        -------
        hikari.events.shard_events.ShardReadyEvent
            The built shard connected event object.
        """

    @abc.abstractmethod
    def deserialize_disconnected_event(self, shard: gateway_shard.GatewayShard) -> shard_events.ShardDisconnectedEvent:
        """Build a shard disconnected event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.

        Returns
        -------
        hikari.events.shard_events.ShardReadyEvent
            The built shard disconnected event object.
        """

    @abc.abstractmethod
    def deserialize_resumed_event(self, shard: gateway_shard.GatewayShard) -> shard_events.ShardResumedEvent:
        """Build a shard resumed event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.

        Returns
        -------
        hikari.events.shard_events.ShardReadyEvent
            The built shard resumed event object.
        """

    @abc.abstractmethod
    def deserialize_guild_member_chunk_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> shard_events.MemberChunkEvent:
        """Parse a raw payload from Discord into a member chunk event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.shard_events.MemberChunkEvent
            The parsed member chunk object.
        """

    ###############
    # USER EVENTS #
    ###############

    @abc.abstractmethod
    def deserialize_own_user_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_user: typing.Optional[user_models.OwnUser],
    ) -> user_events.OwnUserUpdateEvent:
        """Parse a raw payload from Discord into a own user update event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_user: typing.Optional[hikari.users.OwnUser]
            The OwnUser object or `builtins.None`.

        Returns
        -------
        hikari.events.user_events.OwnUserUpdateEvent
            The parsed own user update event object.
        """

    ################
    # VOICE EVENTS #
    ################

    @abc.abstractmethod
    def deserialize_voice_state_update_event(
        self,
        shard: gateway_shard.GatewayShard,
        payload: data_binding.JSONObject,
        *,
        old_state: typing.Optional[voices_models.VoiceState],
    ) -> voice_events.VoiceStateUpdateEvent:
        """Parse a raw payload from Discord into a voice state update event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.
        old_state: typing.Optional[hikari.voices.VoiceState]
            The VoiceState object or `builtins.None`.

        Returns
        -------
        hikari.events.voice_events.VoiceStateUpdateEvent
            The parsed voice state update event object.
        """

    @abc.abstractmethod
    def deserialize_voice_server_update_event(
        self, shard: gateway_shard.GatewayShard, payload: data_binding.JSONObject
    ) -> voice_events.VoiceServerUpdateEvent:
        """Parse a raw payload from Discord into a voice server update event object.

        Parameters
        ----------
        shard : hikari.api.shard.GatewayShard
            The shard that emitted this event.
        payload : hikari.internal.data_binding.JSONObject
            The dict payload to parse.

        Returns
        -------
        hikari.events.voice_events.VoiceServerUpdateEvent
            The parsed voice server update event object.
        """
