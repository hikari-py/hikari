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
"""Core interface for an object that serializes/deserializes API objects."""
from __future__ import annotations

__all__ = ["IEntityFactory"]

import abc
import typing

from hikari.api import component
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    from hikari.models import applications
    from hikari.models import audit_logs
    from hikari.models import channels
    from hikari.models import embeds
    from hikari.models import emojis
    from hikari.models import gateway
    from hikari.models import guilds
    from hikari.models import invites
    from hikari.models import messages
    from hikari.models import presences
    from hikari.models import users
    from hikari.models import voices
    from hikari.models import webhooks

    from hikari.utilities import data_binding


class IEntityFactory(component.IComponent, abc.ABC):
    """Interface for components that serialize and deserialize JSON payloads."""

    __slots__ = ()

    ################
    # APPLICATIONS #
    ################

    @abc.abstractmethod
    def deserialize_own_connection(self, payload: data_binding.JSONObject) -> applications.OwnConnection:
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
    def deserialize_own_guild(self, payload: data_binding.JSONObject) -> applications.OwnGuild:
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
    def deserialize_application(self, payload: data_binding.JSONObject) -> applications.Application:
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

    ##############
    # AUDIT_LOGS #
    ##############

    @abc.abstractmethod
    def deserialize_audit_log(self, payload: data_binding.JSONObject) -> audit_logs.AuditLog:
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

    ############
    # CHANNELS #
    ############

    @abc.abstractmethod
    def deserialize_permission_overwrite(self, payload: data_binding.JSONObject) -> channels.PermissionOverwrite:
        """Parse a raw payload from Discord into a permission overwrite object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.channels.PermissionOverwrote
            The deserialized permission overwrite object.
        """

    @abc.abstractmethod
    def serialize_permission_overwrite(self, overwrite: channels.PermissionOverwrite) -> data_binding.JSONObject:
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
    def deserialize_partial_channel(self, payload: data_binding.JSONObject) -> channels.PartialChannel:
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
    def deserialize_dm_channel(self, payload: data_binding.JSONObject) -> channels.DMChannel:
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
    def deserialize_group_dm_channel(self, payload: data_binding.JSONObject) -> channels.GroupDMChannel:
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
    def deserialize_guild_category(self, payload: data_binding.JSONObject) -> channels.GuildCategory:
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
    def deserialize_guild_text_channel(self, payload: data_binding.JSONObject) -> channels.GuildTextChannel:
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
    def deserialize_guild_news_channel(self, payload: data_binding.JSONObject) -> channels.GuildNewsChannel:
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
    def deserialize_guild_store_channel(self, payload: data_binding.JSONObject) -> channels.GuildStoreChannel:
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
    def deserialize_guild_voice_channel(self, payload: data_binding.JSONObject) -> channels.GuildVoiceChannel:
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
    def deserialize_channel(self, payload: data_binding.JSONObject) -> channels.PartialChannel:
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

    ##########
    # EMBEDS #
    ##########

    @abc.abstractmethod
    def deserialize_embed(self, payload: data_binding.JSONObject) -> embeds.Embed:
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
    def serialize_embed(self, embed: embeds.Embed) -> data_binding.JSONObject:
        """Serialize an embed object to a json serializable dict.

        Parameters
        ----------
        embed : hikari.models.embeds.Embed
            The embed object to serialize.

        Returns
        -------
        hikari.utilities.data_binding.JSONObject
            The serialized object representation.
        """

    ##########
    # EMOJIS #
    ##########

    @abc.abstractmethod
    def deserialize_unicode_emoji(self, payload: data_binding.JSONObject) -> emojis.UnicodeEmoji:
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
    def deserialize_custom_emoji(self, payload: data_binding.JSONObject) -> emojis.CustomEmoji:
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
    def deserialize_known_custom_emoji(self, payload: data_binding.JSONObject) -> emojis.KnownCustomEmoji:
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
    ) -> typing.Union[emojis.UnicodeEmoji, emojis.CustomEmoji]:
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

    ###########
    # GATEWAY #
    ###########

    @abc.abstractmethod
    def deserialize_gateway_bot(self, payload: data_binding.JSONObject) -> gateway.GatewayBot:
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

    ##########
    # GUILDS #
    ##########

    @abc.abstractmethod
    def deserialize_guild_widget(self, payload: data_binding.JSONObject) -> guilds.GuildWidget:
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
        user: typing.Union[undefined.Undefined, users.User] = undefined.Undefined()
    ) -> guilds.Member:
        """Parse a raw payload from Discord into a member object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.
        user : hikari.models.users.User or hikari.utilities.undefined.Undefined
            The user to attach to this member, should only be passed in 
            situations where "user" is not included in the payload.

        Returns
        -------
        hikari.models.guilds.Member
            The deserialized member object.
        """

    @abc.abstractmethod
    def deserialize_role(self, payload: data_binding.JSONObject) -> guilds.Role:
        """Parse a raw payload from Discord into a role object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.guilds.GuildRole
            The deserialized role object.
        """

    @abc.abstractmethod
    def deserialize_partial_integration(self, payload: data_binding.JSONObject) -> guilds.PartialIntegration:
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
    def deserialize_integration(self, payload: data_binding.JSONObject) -> guilds.Integration:
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
    def deserialize_guild_member_ban(self, payload: data_binding.JSONObject) -> guilds.GuildMemberBan:
        """Parse a raw payload from Discord into a guild member ban object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.GuildMemberBan
            The deserialized guild member ban object.
        """

    @abc.abstractmethod
    def deserialize_unavailable_guild(self, payload: data_binding.JSONObject) -> guilds.UnavailableGuild:
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
    def deserialize_guild_preview(self, payload: data_binding.JSONObject) -> guilds.GuildPreview:
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
    def deserialize_guild(self, payload: data_binding.JSONObject) -> guilds.Guild:
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

    ###########
    # INVITES #
    ###########

    @abc.abstractmethod
    def deserialize_vanity_url(self, payload: data_binding.JSONObject) -> invites.VanityURL:
        """Parse a raw payload from Discord into a vanity url object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.invites.VanityUrl
            The deserialized vanity url object.
        """

    @abc.abstractmethod
    def deserialize_invite(self, payload: data_binding.JSONObject) -> invites.Invite:
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
    def deserialize_invite_with_metadata(self, payload: data_binding.JSONObject) -> invites.InviteWithMetadata:
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

    ############
    # MESSAGES #
    ############

    @abc.abstractmethod
    def deserialize_message(self, payload: data_binding.JSONObject) -> messages.Message:
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

    #############
    # PRESENCES #
    #############

    @abc.abstractmethod
    def deserialize_member_presence(self, payload: data_binding.JSONObject) -> presences.MemberPresence:
        """Parse a raw payload from Discord into a member presence object.

        Parameters
        ----------
        payload : hikari.utilities.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.models.guilds.MemberPresence
            The deserialized member presence object.
        """

    #########
    # USERS #
    #########

    @abc.abstractmethod
    def deserialize_user(self, payload: data_binding.JSONObject) -> users.User:
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
    def deserialize_my_user(self, payload: data_binding.JSONObject) -> users.OwnUser:
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

    ##########
    # Voices #
    ##########

    @abc.abstractmethod
    def deserialize_voice_state(self, payload: data_binding.JSONObject) -> voices.VoiceState:
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
    def deserialize_voice_region(self, payload: data_binding.JSONObject) -> voices.VoiceRegion:
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

    ############
    # WEBHOOKS #
    ############

    @abc.abstractmethod
    def deserialize_webhook(self, payload: data_binding.JSONObject) -> webhooks.Webhook:
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
