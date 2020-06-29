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
"""Core interface for an object that serializes/deserializes API objects."""
from __future__ import annotations

__all__: typing.Final[typing.Sequence[str]] = ["IEntityFactoryComponent"]

import abc
import typing

from hikari.api import component
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import datetime

    from hikari.events import channel as channel_events
    from hikari.events import guild as guild_events
    from hikari.events import message as message_events
    from hikari.events import other as other_events
    from hikari.events import voice as voice_events
    from hikari.models import applications as application_models
    from hikari.models import audit_logs as audit_log_models
    from hikari.models import channels as channel_models
    from hikari.models import embeds as embed_models
    from hikari.models import emojis as emoji_models
    from hikari.models import gateway as gateway_models
    from hikari.models import guilds as guild_models
    from hikari.models import invites as invite_models
    from hikari.models import messages as message_models
    from hikari.models import presences as presence_models
    from hikari.models import users as user_models
    from hikari.models import voices as voice_models
    from hikari.models import webhooks as webhook_models
    from hikari.net import gateway
    from hikari.utilities import data_binding
    from hikari.utilities import files
    from hikari.utilities import snowflake


class IEntityFactoryComponent(component.IComponent, abc.ABC):
    """Interface for components that serialize and deserialize JSON payloads."""

    __slots__: typing.Sequence[str] = ()

    ######################
    # APPLICATION MODELS #
    ######################

    @abc.abstractmethod
    def deserialize_own_connection(self, payload: data_binding.JSONObject) -> application_models.OwnConnection:
        """Parse a raw payload from Discord into an own connection object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.applications.OwnConnection
            The deserialized own connection object.
        """

    @abc.abstractmethod
    def deserialize_own_guild(self, payload: data_binding.JSONObject) -> application_models.OwnGuild:
        """Parse a raw payload from Discord into an own guild object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.applications.OwnGuild
            The deserialized own guild object.
        """

    @abc.abstractmethod
    def deserialize_application(self, payload: data_binding.JSONObject) -> application_models.Application:
        """Parse a raw payload from Discord into an application object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.applications.Application
            The deserialized application object.
        """

    #####################
    # AUDIT LOGS MODELS #
    #####################

    @abc.abstractmethod
    def deserialize_audit_log(self, payload: data_binding.JSONObject) -> audit_log_models.AuditLog:
        """Parse a raw payload from Discord into an audit log object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.audit_logs.AuditLog
            The deserialized audit log object.
        """

    ##################
    # CHANNEL MODELS #
    ##################

    @abc.abstractmethod
    def deserialize_permission_overwrite(self, payload: data_binding.JSONObject) -> channel_models.PermissionOverwrite:
        """Parse a raw payload from Discord into a permission overwrite object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.channels.PermissionOverwrite
            The deserialized permission overwrite object.
        """

    @abc.abstractmethod
    def serialize_permission_overwrite(self, overwrite: channel_models.PermissionOverwrite) -> data_binding.JSONObject:
        """Serialize a permission overwrite object to a json serializable dict.

        Parameters
        ----------
        overwrite : hikari.models.channels.PermissionOverwrite
            The permission overwrite object to serialize.

        Returns
        -------
        hikari.utilities.data_binding.JSONObject
            The serialized representation.
        """

    @abc.abstractmethod
    def deserialize_partial_channel(self, payload: data_binding.JSONObject) -> channel_models.PartialChannel:
        """Parse a raw payload from Discord into a partial channel object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.channels.PartialChannel
            The deserialized partial channel object.
        """

    @abc.abstractmethod
    def deserialize_dm_channel(self, payload: data_binding.JSONObject) -> channel_models.DMChannel:
        """Parse a raw payload from Discord into a DM channel object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.channels.DMChannel
            The deserialized DM channel object.
        """

    @abc.abstractmethod
    def deserialize_group_dm_channel(self, payload: data_binding.JSONObject) -> channel_models.GroupDMChannel:
        """Parse a raw payload from Discord into a group DM channel object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.channels.GroupDMChannel
            The deserialized group DM channel object.
        """

    @abc.abstractmethod
    def deserialize_guild_category(self, payload: data_binding.JSONObject) -> channel_models.GuildCategory:
        """Parse a raw payload from Discord into a guild category object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.channels.GuildCategory
            The deserialized partial channel object.
        """

    @abc.abstractmethod
    def deserialize_guild_text_channel(self, payload: data_binding.JSONObject) -> channel_models.GuildTextChannel:
        """Parse a raw payload from Discord into a guild text channel object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.channels.GuildTextChannel
            The deserialized guild text channel object.
        """

    @abc.abstractmethod
    def deserialize_guild_news_channel(self, payload: data_binding.JSONObject) -> channel_models.GuildNewsChannel:
        """Parse a raw payload from Discord into a guild news channel object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.channels.GuildNewsChannel
            The deserialized guild news channel object.
        """

    @abc.abstractmethod
    def deserialize_guild_store_channel(self, payload: data_binding.JSONObject) -> channel_models.GuildStoreChannel:
        """Parse a raw payload from Discord into a guild store channel object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.channels.GuildStoreChannel
            The deserialized guild store channel object.
        """

    @abc.abstractmethod
    def deserialize_guild_voice_channel(self, payload: data_binding.JSONObject) -> channel_models.GuildVoiceChannel:
        """Parse a raw payload from Discord into a guild voice channel object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.channels.GuildVoiceChannel
            The deserialized guild voice channel object.
        """

    @abc.abstractmethod
    def deserialize_channel(self, payload: data_binding.JSONObject) -> channel_models.PartialChannel:
        """Parse a raw payload from Discord into a channel object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.channels.PartialChannel
            The deserialized partial channel-derived object.
        """

    ################
    # EMBED MODELS #
    ################

    @abc.abstractmethod
    def deserialize_embed(self, payload: data_binding.JSONObject) -> embed_models.Embed:
        """Parse a raw payload from Discord into an embed object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.embeds.Embed
            The deserialized embed object.
        """

    @abc.abstractmethod
    def serialize_embed(
        self, embed: embed_models.Embed
    ) -> typing.Tuple[data_binding.JSONObject, typing.List[files.Resource]]:
        """Serialize an embed object to a json serializable dict.

        Parameters
        ----------
        embed : hikari.models.embeds.Embed
            The embed object to serialize.

        Returns
        -------
        typing.Tuple[hikari.utilities.data_binding.JSONObject, typing.List[hikari.utilities.files.Resource]]
            A tuple with two items in it. The first item will be the serialized
            embed representation. The second item will be a list of resources
            to upload with the embed.
        """

    ################
    # EMOJI MODELS #
    ################

    @abc.abstractmethod
    def deserialize_unicode_emoji(self, payload: data_binding.JSONObject) -> emoji_models.UnicodeEmoji:
        """Parse a raw payload from Discord into a unicode emoji object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.emojis.UnicodeEmoji
            The deserialized unicode emoji object.
        """

    @abc.abstractmethod
    def deserialize_custom_emoji(self, payload: data_binding.JSONObject) -> emoji_models.CustomEmoji:
        """Parse a raw payload from Discord into a custom emoji object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.emojis.CustomEmoji
            The deserialized custom emoji object.
        """

    @abc.abstractmethod
    def deserialize_known_custom_emoji(self, payload: data_binding.JSONObject) -> emoji_models.KnownCustomEmoji:
        """Parse a raw payload from Discord into a known custom emoji object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.emojis.KnownCustomEmoji
            The deserialized known custom emoji object.
        """

    @abc.abstractmethod
    def deserialize_emoji(
        self, payload: data_binding.JSONObject
    ) -> typing.Union[emoji_models.UnicodeEmoji, emoji_models.CustomEmoji]:
        """Parse a raw payload from Discord into an emoji object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.emojis.UnicodeEmoji | hikari.models.emoji.CustomEmoji
            The deserialized custom or unicode emoji object.
        """

    ##################
    # GATEWAY MODELS #
    ##################

    @abc.abstractmethod
    def deserialize_gateway_bot(self, payload: data_binding.JSONObject) -> gateway_models.GatewayBot:
        """Parse a raw payload from Discord into a gateway bot object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.gateway.GatewayBot
            The deserialized gateway bot object.
        """

    ################
    # GUILD MODELS #
    ################

    @abc.abstractmethod
    def deserialize_guild_widget(self, payload: data_binding.JSONObject) -> guild_models.GuildWidget:
        """Parse a raw payload from Discord into a guild widget object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.guilds.GuildWidget
            The deserialized guild widget object.
        """

    @abc.abstractmethod
    def deserialize_member(
        self,
        payload: data_binding.JSONObject,
        *,
        user: typing.Union[undefined.UndefinedType, user_models.User] = undefined.UNDEFINED,
    ) -> guild_models.Member:
        """Parse a raw payload from Discord into a member object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.
        user : hikari.models.users.User or hikari.utilities.undefined.UndefinedType
            The user to attach to this member, should only be passed in
            situations where "user" is not included in the payload.

        Returns
        -------
        hikari.models.guilds.Member
            The deserialized member object.
        """

    @abc.abstractmethod
    def deserialize_role(self, payload: data_binding.JSONObject) -> guild_models.Role:
        """Parse a raw payload from Discord into a role object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.guilds.Role
            The deserialized role object.
        """

    @abc.abstractmethod
    def deserialize_partial_integration(self, payload: data_binding.JSONObject) -> guild_models.PartialIntegration:
        """Parse a raw payload from Discord into a partial integration object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.guilds.PartialIntegration
            The deserialized partial integration object.
        """

    @abc.abstractmethod
    def deserialize_integration(self, payload: data_binding.JSONObject) -> guild_models.Integration:
        """Parse a raw payload from Discord into an integration object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.guilds.Integration
            The deserialized integration object.
        """

    @abc.abstractmethod
    def deserialize_guild_member_ban(self, payload: data_binding.JSONObject) -> guild_models.GuildMemberBan:
        """Parse a raw payload from Discord into a guild member ban object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.guilds.GuildMemberBan
            The deserialized guild member ban object.
        """

    @abc.abstractmethod
    def deserialize_unavailable_guild(self, payload: data_binding.JSONObject) -> guild_models.UnavailableGuild:
        """Parse a raw payload from Discord into a unavailable guild object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.guilds.UnavailableGuild
            The deserialized unavailable guild object.
        """

    @abc.abstractmethod
    def deserialize_guild_preview(self, payload: data_binding.JSONObject) -> guild_models.GuildPreview:
        """Parse a raw payload from Discord into a guild preview object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.guilds.GuildPreview
            The deserialized guild preview object.
        """

    @abc.abstractmethod
    def deserialize_guild(self, payload: data_binding.JSONObject) -> guild_models.Guild:
        """Parse a raw payload from Discord into a guild object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.guilds.Guild
            The deserialized guild object.
        """

    #################
    # INVITE MODELS #
    #################

    @abc.abstractmethod
    def deserialize_vanity_url(self, payload: data_binding.JSONObject) -> invite_models.VanityURL:
        """Parse a raw payload from Discord into a vanity url object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.invites.VanityURL
            The deserialized vanity url object.
        """

    @abc.abstractmethod
    def deserialize_invite(self, payload: data_binding.JSONObject) -> invite_models.Invite:
        """Parse a raw payload from Discord into an invite object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.invites.Invite
            The deserialized invite object.
        """

    @abc.abstractmethod
    def deserialize_invite_with_metadata(self, payload: data_binding.JSONObject) -> invite_models.InviteWithMetadata:
        """Parse a raw payload from Discord into a invite with metadata object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.invites.InviteWithMetadata
            The deserialized invite with metadata object.
        """

    ##################
    # MESSAGE MODELS #
    ##################

    @abc.abstractmethod
    @abc.abstractmethod
    def deserialize_message(self, payload: data_binding.JSONObject) -> message_models.Message:
        """Parse a raw payload from Discord into a message object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.messages.Message
            The deserialized message object.
        """

    ###################
    # PRESENCE MODELS #
    ###################

    @abc.abstractmethod
    def deserialize_member_presence(self, payload: data_binding.JSONObject) -> presence_models.MemberPresence:
        """Parse a raw payload from Discord into a member presence object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.presences.MemberPresence
            The deserialized member presence object.
        """

    ###############
    # USER MODELS #
    ###############

    @abc.abstractmethod
    def deserialize_user(self, payload: data_binding.JSONObject) -> user_models.User:
        """Parse a raw payload from Discord into a user object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.users.User
            The deserialized user object.
        """

    @abc.abstractmethod
    def deserialize_my_user(self, payload: data_binding.JSONObject) -> user_models.OwnUser:
        """Parse a raw payload from Discord into a user object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.users.OwnUser
            The deserialized user object.
        """

    ################
    # VOICE MODELS #
    ################

    @abc.abstractmethod
    def deserialize_voice_state(self, payload: data_binding.JSONObject) -> voice_models.VoiceState:
        """Parse a raw payload from Discord into a voice state object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.voices.VoiceState
            The deserialized voice state object.
        """

    @abc.abstractmethod
    def deserialize_voice_region(self, payload: data_binding.JSONObject) -> voice_models.VoiceRegion:
        """Parse a raw payload from Discord into a voice region object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.voices.VoiceRegion
            The deserialized voice region object.
        """

    ##################
    # WEBHOOK MODELS #
    ##################

    @abc.abstractmethod
    def deserialize_webhook(self, payload: data_binding.JSONObject) -> webhook_models.Webhook:
        """Parse a raw payload from Discord into a webhook object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.webhooks.Webhook
            The deserialized webhook object.
        """

    ##################
    # CHANNEL EVENTS #
    ##################

    @abc.abstractmethod
    def deserialize_channel_create_event(self, payload: data_binding.JSONObject) -> channel_events.ChannelCreateEvent:
        """Parse a raw payload from Discord into a channel create event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel.ChannelCreateEvent
            The parsed channel create event object.
        """

    @abc.abstractmethod
    def deserialize_channel_update_event(self, payload: data_binding.JSONObject) -> channel_events.ChannelUpdateEvent:
        """Parse a raw payload from Discord into a channel update event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel.ChannelUpdateEvent
            The parsed  event object.
        """

    @abc.abstractmethod
    def deserialize_channel_delete_event(self, payload: data_binding.JSONObject) -> channel_events.ChannelDeleteEvent:
        """Parse a raw payload from Discord into a channel delete event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel.ChannelDeleteEvent
            The parsed channel delete event object.
        """

    @abc.abstractmethod
    def deserialize_channel_pins_update_event(
        self, payload: data_binding.JSONObject
    ) -> channel_events.ChannelPinsUpdateEvent:
        """Parse a raw payload from Discord into a channel pins update event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel.ChannelPinsUpdateEvent
            The parsed channel pins update event object.
        """

    @abc.abstractmethod
    def deserialize_webhook_update_event(self, payload: data_binding.JSONObject) -> channel_events.WebhookUpdateEvent:
        """Parse a raw payload from Discord into a webhook update event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel.WebhookUpdateEvent
            The parsed webhook update event object.
        """

    @abc.abstractmethod
    def deserialize_typing_start_event(self, payload: data_binding.JSONObject) -> channel_events.TypingStartEvent:
        """Parse a raw payload from Discord into a typing start event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel.TypingStartEvent
            The parsed typing start event object.
        """

    @abc.abstractmethod
    def deserialize_invite_create_event(self, payload: data_binding.JSONObject) -> channel_events.InviteCreateEvent:
        """Parse a raw payload from Discord into an invite create event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel.InviteCreateEvent
            The parsed invite create event object.
        """

    @abc.abstractmethod
    def deserialize_invite_delete_event(self, payload: data_binding.JSONObject) -> channel_events.InviteDeleteEvent:
        """Parse a raw payload from Discord into an invite delete event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.channel.InviteDeleteEvent
            The parsed invite delete event object.
        """

    ################
    # GUILD EVENTS #
    ################

    @abc.abstractmethod
    def deserialize_guild_create_event(self, payload: data_binding.JSONObject) -> guild_events.GuildCreateEvent:
        """Parse a raw payload from Discord into a guild create event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild.GuildCreateEvent
            The parsed guild create event object.
        """

    @abc.abstractmethod
    def deserialize_guild_update_event(self, payload: data_binding.JSONObject) -> guild_events.GuildUpdateEvent:
        """Parse a raw payload from Discord into a guild update event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild.GuildUpdateEvent
            The parsed guild update event object.
        """

    @abc.abstractmethod
    def deserialize_guild_leave_event(self, payload: data_binding.JSONObject) -> guild_events.GuildLeaveEvent:
        """Parse a raw payload from Discord into a guild leave event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild.GuildLeaveEvent
            The parsed guild leave event object.
        """

    @abc.abstractmethod
    def deserialize_guild_unavailable_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildUnavailableEvent:
        """Parse a raw payload from Discord into a guild unavailable event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.
            The parsed guild unavailable event object.
        """

    @abc.abstractmethod
    def deserialize_guild_ban_add_event(self, payload: data_binding.JSONObject) -> guild_events.GuildBanAddEvent:
        """Parse a raw payload from Discord into a guild ban add event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild.GuildBanAddEvent
            The parsed guild ban add event object.
        """

    @abc.abstractmethod
    def deserialize_guild_ban_remove_event(self, payload: data_binding.JSONObject) -> guild_events.GuildBanRemoveEvent:
        """Parse a raw payload from Discord into a guild ban remove event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild.GuildBanRemoveEvent
            The parsed guild ban remove event object.
        """

    @abc.abstractmethod
    def deserialize_guild_emojis_update_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildEmojisUpdateEvent:
        """Parse a raw payload from Discord into a guild emojis update event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild.GuildEmojisUpdateEvent
            The parsed guild emojis update event object.
        """

    @abc.abstractmethod
    def deserialize_guild_integrations_update_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildIntegrationsUpdateEvent:
        """Parse a raw payload from Discord into a guilds integrations update event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild.GuildIntegrationsUpdateEvent
            The parsed guilds integrations update event object.
        """

    @abc.abstractmethod
    def deserialize_guild_member_add_event(self, payload: data_binding.JSONObject) -> guild_events.GuildMemberAddEvent:
        """Parse a raw payload from Discord into a guild member add event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild.GuildMemberAddEvent
            The parsed guild member add event object.
        """

    @abc.abstractmethod
    def deserialize_guild_member_update_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildMemberUpdateEvent:
        """Parse a raw payload from Discord into a guild member update event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild.GuildMemberUpdateEvent
            The parsed guild member update event object.
        """

    @abc.abstractmethod
    def deserialize_guild_member_remove_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildMemberRemoveEvent:
        """Parse a raw payload from Discord into a guild member remove event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild.GuildMemberRemoveEvent
            The parsed guild member remove event object.
        """

    @abc.abstractmethod
    def deserialize_guild_role_create_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildRoleCreateEvent:
        """Parse a raw payload from Discord into a guild role create event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild.GuildRoleCreateEvent
            The parsed guild role create event object.
        """

    @abc.abstractmethod
    def deserialize_guild_role_update_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildRoleUpdateEvent:
        """Parse a raw payload from Discord into a guild role update event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild.GuildRoleUpdateEvent
            The parsed guild role update event object.
        """

    @abc.abstractmethod
    def deserialize_guild_role_delete_event(
        self, payload: data_binding.JSONObject
    ) -> guild_events.GuildRoleDeleteEvent:
        """Parse a raw payload from Discord into a guild role delete event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild.GuildRoleDeleteEvent
            The parsed guild role delete event object.
        """

    @abc.abstractmethod
    def deserialize_presence_update_event(self, payload: data_binding.JSONObject) -> guild_events.PresenceUpdateEvent:
        """Parse a raw payload from Discord into a presence update event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.guild.PresenceUpdateEvent
            The parsed presence update event object.
        """

    ##################
    # MESSAGE EVENTS #
    ##################

    @abc.abstractmethod
    def deserialize_message_create_event(self, payload: data_binding.JSONObject) -> message_events.MessageCreateEvent:
        """Parse a raw payload from Discord into a message create event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.message.MessageCreateEvent
            The parsed message create event object.
        """

    @abc.abstractmethod
    def deserialize_message_update_event(self, payload: data_binding.JSONObject) -> message_events.MessageUpdateEvent:
        """Parse a raw payload from Discord into a message update event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.message.MessageUpdateEvent
            The parsed message update event object.
        """

    @abc.abstractmethod
    def deserialize_message_delete_event(self, payload: data_binding.JSONObject) -> message_events.MessageDeleteEvent:
        """Parse a raw payload from Discord into a message delete event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.message.MessageDeleteEvent
            The parsed message delete event object.
        """

    @abc.abstractmethod
    def deserialize_message_delete_bulk_event(
        self, payload: data_binding.JSONObject
    ) -> message_events.MessageDeleteBulkEvent:
        """Parse a raw payload from Discord into a message delete bulk event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.message.MessageDeleteBulkEvent
            The parsed message delete bulk event object.
        """

    @abc.abstractmethod
    def deserialize_message_reaction_add_event(
        self, payload: data_binding.JSONObject
    ) -> message_events.MessageReactionAddEvent:
        """Parse a raw payload from Discord into a message reaction add event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.message.MessageReactionAddEvent
            The parsed message reaction add event object.
        """

    @abc.abstractmethod
    def deserialize_message_reaction_remove_event(
        self, payload: data_binding.JSONObject
    ) -> message_events.MessageReactionRemoveEvent:
        """Parse a raw payload from Discord into a message reaction remove event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.message.MessageReactionRemoveEvent
            The parsed message reaction remove event object.
        """

    @abc.abstractmethod
    def deserialize_message_reaction_remove_all_event(
        self, payload: data_binding.JSONObject
    ) -> message_events.MessageReactionRemoveAllEvent:
        """Parse a raw payload from Discord into a message reaction remove all event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.message.MessageReactionRemoveAllEvent
            The parsed message reaction remove all event object.
        """

    @abc.abstractmethod
    def deserialize_message_reaction_remove_emoji_event(
        self, payload: data_binding.JSONObject
    ) -> message_events.MessageReactionRemoveEmojiEvent:
        """Parse a raw payload from Discord into a message reaction remove emoji event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.message.MessageReactionRemoveEmojiEvent
            The parsed message reaction remove emoji event object.
        """

    ################
    # OTHER EVENTS #
    ################

    @abc.abstractmethod
    def deserialize_ready_event(
        self, shard: gateway.Gateway, payload: data_binding.JSONObject,
    ) -> other_events.ReadyEvent:
        """Parse a raw payload from Discord into a ready event object.

        Parameters
        ----------
        shard : hikari.net.gateway.Gateway
            The shard that was ready.
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.other.ReadyEvent
            The parsed ready event object.
        """

    @abc.abstractmethod
    def deserialize_own_user_update_event(self, payload: data_binding.JSONObject) -> other_events.OwnUserUpdateEvent:
        """Parse a raw payload from Discord into a own user update event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.other.OwnUserUpdateEvent
            The parsed own user update event object.
        """

    ################
    # VOICE EVENTS #
    ################

    @abc.abstractmethod
    def deserialize_voice_state_update_event(
        self, payload: data_binding.JSONObject
    ) -> voice_events.VoiceStateUpdateEvent:
        """Parse a raw payload from Discord into a voice state update event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.voice.VoiceStateUpdateEvent
            The parsed voice state update event object.
        """

    @abc.abstractmethod
    def deserialize_voice_server_update_event(
        self, payload: data_binding.JSONObject
    ) -> voice_events.VoiceServerUpdateEvent:
        """Parse a raw payload from Discord into a voice server update event object.

        Parameters
        ----------
        payload : typing.Mapping[str, typing.Any]
            The dict payload to parse.

        Returns
        -------
        hikari.events.voice.VoiceServerUpdateEvent
            The parsed voice server update event object.
        """

    ###############################
    # GATEWAY-SPECIFIC UTILITIES. #
    ###############################

    @abc.abstractmethod
    def serialize_gateway_presence(
        self,
        idle_since: typing.Union[undefined.UndefinedType, None, datetime.datetime] = undefined.UNDEFINED,
        afk: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        status: typing.Union[undefined.UndefinedType, presence_models.Status] = undefined.UNDEFINED,
        activity: typing.Union[undefined.UndefinedType, None, presence_models.Activity] = undefined.UNDEFINED,
    ) -> data_binding.JSONObject:
        """Serialize a set of presence parameters into a raw gateway payload.

        Any parameters that are left to be unspecified are omitted from the
        generated payload.

        Parameters
        ----------
        idle_since : hikari.utilities.undefined.UndefinedType or None or datetime.datetime
            The time that the user should appear to be idle since. If `None`,
            then the user is marked as not being idle.
        afk : hikari.utilities.undefined.UndefinedType or bool
            If `True`, the user becomes AFK. This will move them

        status : hikari.utilities.undefined.UndefinedType or hikari.models.presences.Status
        activity : hikari.utilities.undefined.UndefinedType or None or hikari.models.presences.Activity

        Returns
        -------
        hikari.utilities.data_binding.JSONObject
            The serialized presence.
        """

    @abc.abstractmethod
    def serialize_gateway_voice_state_update(
        self,
        guild: typing.Union[guild_models.Guild, snowflake.UniqueObject],
        channel: typing.Union[channel_models.GuildVoiceChannel, snowflake.UniqueObject, None],
        self_mute: bool,
        self_deaf: bool,
    ) -> data_binding.JSONObject:
        """Serialize a voice state update payload into a raw gateway payload.

        Parameters
        ----------
        guild : hikari.models.guilds.Guild or hikari.utilities.snowflake.UniqueObject
            The guild to update the voice state in.
        channel : hikari.models.channels.GuildVoiceChannel or hikari.utilities.snowflake.UniqueObject or None
            The voice channel to change to, or `None` if attempting to leave a
            voice channel and disconnect entirely.
        self_mute : bool
            `True` if the user should be muted, `False` if they should be
            unmuted.
        self_deaf : bool
            `True` if the user should be deafened, `False` if they should be
            able to hear other users.

        Returns
        -------
        hikari.utilities.data_binding.JSONObject
            The serialized payload.
        """
