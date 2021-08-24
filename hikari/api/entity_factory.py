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
"""Core interface for an object that serializes/deserializes API objects."""
from __future__ import annotations

__all__: typing.List[str] = ["EntityFactory", "GatewayGuildDefinition"]

import abc
import typing

import attr

from hikari import undefined
from hikari.internal import attr_extensions

if typing.TYPE_CHECKING:
    from hikari import applications as application_models
    from hikari import audit_logs as audit_log_models
    from hikari import channels as channel_models
    from hikari import commands
    from hikari import embeds as embed_models
    from hikari import emojis as emoji_models
    from hikari import files
    from hikari import guilds as guild_models
    from hikari import invites as invite_models
    from hikari import messages as message_models
    from hikari import presences as presence_models
    from hikari import sessions as gateway_models
    from hikari import snowflakes
    from hikari import stickers as sticker_models
    from hikari import templates as template_models
    from hikari import users as user_models
    from hikari import voices as voice_models
    from hikari import webhooks as webhook_models
    from hikari.interactions import base_interactions
    from hikari.interactions import command_interactions
    from hikari.interactions import component_interactions
    from hikari.internal import data_binding


@attr_extensions.with_copy
@attr.define(weakref_slot=False)
class GatewayGuildDefinition:
    """A structure for handling entities within guild create and update events."""

    guild: guild_models.GatewayGuild = attr.field()
    """Object of the guild the definition is for."""

    channels: typing.Optional[typing.Mapping[snowflakes.Snowflake, channel_models.GuildChannel]] = attr.field()
    """Mapping of channel IDs to the channels that belong to the guild.

    Will be `builtins.None` when returned by guild update gateway events rather
    than create.
    """

    members: typing.Optional[typing.Mapping[snowflakes.Snowflake, guild_models.Member]] = attr.field()
    """Mapping of user IDs to the members that belong to the guild.

    Will be `builtins.None` when returned by guild update gateway events rather
    than create.

    !!! note
        This may be a partial mapping of members in the guild.
    """

    presences: typing.Optional[typing.Mapping[snowflakes.Snowflake, presence_models.MemberPresence]] = attr.field()
    """Mapping of user IDs to the presences that are active in the guild.

    Will be `builtins.None` when returned by guild update gateway events rather
    than create.

    !!! note
        This may be a partial mapping of presences active in the guild.
    """

    roles: typing.Mapping[snowflakes.Snowflake, guild_models.Role] = attr.field()
    """Mapping of role IDs to the roles that belong to the guild."""

    emojis: typing.Mapping[snowflakes.Snowflake, emoji_models.KnownCustomEmoji] = attr.field()
    """Mapping of emoji IDs to the emojis that belong to the guild."""

    voice_states: typing.Optional[typing.Mapping[snowflakes.Snowflake, voice_models.VoiceState]] = attr.field()
    """Mapping of user IDs to the voice states that are active in the guild.

    !!! note
        This may be a partial mapping of voice states active in the guild.
    """


class EntityFactory(abc.ABC):
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
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.applications.OwnConnection
            The deserialized "own connection" object.
        """

    @abc.abstractmethod
    def deserialize_own_guild(self, payload: data_binding.JSONObject) -> application_models.OwnGuild:
        """Parse a raw payload from Discord into an own guild object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.applications.OwnGuild
            The deserialized "own guild" object.
        """

    @abc.abstractmethod
    def deserialize_application(self, payload: data_binding.JSONObject) -> application_models.Application:
        """Parse a raw payload from Discord into an application object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.applications.Application
            The deserialized application object.
        """

    @abc.abstractmethod
    def deserialize_authorization_information(
        self, payload: data_binding.JSONObject
    ) -> application_models.AuthorizationInformation:
        """Parse a raw payload from Discord into an authorization information object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.applications.AuthorizationInformation
            The deserialized authorization information object.
        """

    @abc.abstractmethod
    def deserialize_partial_token(self, payload: data_binding.JSONObject) -> application_models.PartialOAuth2Token:
        """Parse a raw payload from Discord into a partial OAuth2 token object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.applications.PartialOAuth2Token
            The deserialized partial OAuth2 token object.
        """

    @abc.abstractmethod
    def deserialize_authorization_token(
        self, payload: data_binding.JSONObject
    ) -> application_models.OAuth2AuthorizationToken:
        """Parse a raw payload from Discord into an authorization token object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.applications.OAuth2AuthorizationToken
            The deserialized OAuth2 authorization token object.
        """

    @abc.abstractmethod
    def deserialize_implicit_token(self, query: data_binding.Query) -> application_models.OAuth2ImplicitToken:
        """Parse a query from Discord into an implicit token object.

        Parameters
        ----------
        query : hikari.internal.data_binding.Query
            The query parameters to deserialize.

        Returns
        -------
        hikari.applications.OAuth2ImplicitToken
            The deserialized OAuth2 implicit token object.
        """

    #####################
    # AUDIT LOGS MODELS #
    #####################

    @abc.abstractmethod
    def deserialize_audit_log(self, payload: data_binding.JSONObject) -> audit_log_models.AuditLog:
        """Parse a raw payload from Discord into an audit log object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.audit_logs.AuditLog
            The deserialized audit log object.
        """

    ##################
    # CHANNEL MODELS #
    ##################

    @abc.abstractmethod
    def deserialize_channel_follow(self, payload: data_binding.JSONObject) -> channel_models.ChannelFollow:
        """Parse a raw payload from Discord into a channel follow object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.channels.ChannelFollow
            The deserialized channel follow object.
        """

    @abc.abstractmethod
    def deserialize_permission_overwrite(self, payload: data_binding.JSONObject) -> channel_models.PermissionOverwrite:
        """Parse a raw payload from Discord into a permission overwrite object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.channels.PermissionOverwrite
            The deserialized permission overwrite object.
        """

    @abc.abstractmethod
    def serialize_permission_overwrite(self, overwrite: channel_models.PermissionOverwrite) -> data_binding.JSONObject:
        """Serialize a permission overwrite object to a json serializable dict.

        Parameters
        ----------
        overwrite : hikari.channels.PermissionOverwrite
            The permission overwrite object to serialize.

        Returns
        -------
        hikari.internal.data_binding.JSONObject
            The serialized representation of the permission overwrite.
        """

    @abc.abstractmethod
    def deserialize_partial_channel(self, payload: data_binding.JSONObject) -> channel_models.PartialChannel:
        """Parse a raw payload from Discord into a partial channel object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.channels.PartialChannel
            The deserialized "partial channel" object.
        """

    @abc.abstractmethod
    def deserialize_dm(self, payload: data_binding.JSONObject) -> channel_models.DMChannel:
        """Parse a raw payload from Discord into a DM channel object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.channels.DMChannel
            The deserialized DM channel object.
        """

    @abc.abstractmethod
    def deserialize_group_dm(self, payload: data_binding.JSONObject) -> channel_models.GroupDMChannel:
        """Parse a raw payload from Discord into a group DM channel object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.channels.GroupDMChannel
            The deserialized group DM object.
        """

    @abc.abstractmethod
    def deserialize_guild_category(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.GuildCategory:
        """Parse a raw payload from Discord into a guild category object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Other Parameters
        ----------------
        guild_id : hikari.undefined.UndefinedOr[hikari.snowflakes.Snowflake]
            The ID of the guild this channel belongs to. If passed then this
            will be prioritised over `"guild_id"` in the payload.

        !!! note
            `guild_id` currently only covers the gateway GUILD_CREATE event
            where `"guild_id"` is not included in the channel's payload.

        Returns
        -------
        hikari.channels.GuildCategory
            The deserialized guild category object.

        Raises
        ------
        builtins.KeyError
            If `guild_id` is left as `hikari.undefined.UNDEFINED` when
            `"guild_id"` is not present in the passed payload.
        """

    @abc.abstractmethod
    def deserialize_guild_text_channel(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.GuildTextChannel:
        """Parse a raw payload from Discord into a guild text channel object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Other Parameters
        ----------------
        guild_id : hikari.undefined.UndefinedOr[hikari.snowflakes.Snowflake]
            The ID of the guild this channel belongs to. If passed then this
            will be prioritised over `"guild_id"` in the payload.

        !!! note
            `guild_id` currently only covers the gateway GUILD_CREATE event
            where `"guild_id"` is not included in the channel's payload.

        Returns
        -------
        hikari.channels.GuildTextChannel
            The deserialized guild text channel object.

        Raises
        ------
        builtins.KeyError
            If `guild_id` is left as `hikari.undefined.UNDEFINED` when
            `"guild_id"` is not present in the passed payload.
        """

    @abc.abstractmethod
    def deserialize_guild_news_channel(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.GuildNewsChannel:
        """Parse a raw payload from Discord into a guild news channel object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Other Parameters
        ----------------
        guild_id : hikari.snowflakes.Snowflake
            The ID of the guild this channel belongs to. If passed then this
            will be prioritised over `"guild_id"` in the payload.

        !!! note
            `guild_id` currently only covers the gateway GUILD_CREATE event
            where `"guild_id"` is not included in the channel's payload.

        Returns
        -------
        hikari.channels.GuildNewsChannel
            The deserialized guild news channel object.

        Raises
        ------
        builtins.KeyError
            If `guild_id` is left as `hikari.undefined.UNDEFINED` when
            `"guild_id"` is not present in the passed payload.
        """

    @abc.abstractmethod
    def deserialize_guild_store_channel(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.GuildStoreChannel:
        """Parse a raw payload from Discord into a guild store channel object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Other Parameters
        ----------------
        guild_id : hikari.snowflakes.Snowflake
            The ID of the guild this channel belongs to. If passed then this
            will be prioritised over `"guild_id"` in the payload.

        !!! note
            `guild_id` currently only covers the gateway GUILD_CREATE event
            where `"guild_id"` is not included in the channel's payload.

        Returns
        -------
        hikari.channels.GuildStoreChannel
            The deserialized guild store channel object.

        Raises
        ------
        builtins.KeyError
            If `guild_id` is left as `hikari.undefined.UNDEFINED` when
            `"guild_id"` is not present in the passed payload.
        """

    @abc.abstractmethod
    def deserialize_guild_voice_channel(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.GuildVoiceChannel:
        """Parse a raw payload from Discord into a guild voice channel object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Other Parameters
        ----------------
        guild_id : hikari.snowflakes.Snowflake
            The ID of the guild this channel belongs to. If passed then this
            will be prioritised over `"guild_id"` in the payload.

        !!! note
            `guild_id` currently only covers the gateway GUILD_CREATE event
            where `"guild_id"` is npt included in the channel's payload.

        Returns
        -------
        hikari.channels.GuildVoiceChannel
            The deserialized guild voice channel object.

        Raises
        ------
        builtins.KeyError
            If `guild_id` is left as `hikari.undefined.UNDEFINED` when
            `"guild_id"` is not present in the passed payload.
        """

    @abc.abstractmethod
    def deserialize_guild_stage_channel(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.GuildStageChannel:
        """Parse a raw payload from Discord into a guild stage channel object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Other Parameters
        ----------------
        guild_id : hikari.snowflakes.Snowflake
            The ID of the guild this channel belongs to. If passed then this
            will be prioritised over `"guild_id"` in the payload.

        !!! note
            `guild_id` currently only covers the gateway GUILD_CREATE event
            where `"guild_id"` is npt included in the channel's payload.

        Returns
        -------
        hikari.channels.GuildStageChannel
            The deserialized guild stage channel object.

        Raises
        ------
        builtins.KeyError
            If `guild_id` is left as `hikari.undefined.UNDEFINED` when
            `"guild_id"` is not present in the passed payload.
        """

    @abc.abstractmethod
    def deserialize_channel(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> channel_models.PartialChannel:
        """Parse a raw payload from Discord into a channel object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Other Parameters
        ----------------
        guild_id : hikari.undefined.UndefinedOr[hikari.snowflakes.Snowflake]
            The ID of the guild this channel belongs to. This will be ignored
            for DM and group DM channels and will be prioritised over
            `"guild_id"` in the payload when passed.

        !!! note
            `guild_id` currently only covers the gateway GUILD_CREATE event
            where `"guild_id"` is not included in the channel's payload.

        Returns
        -------
        hikari.channels.PartialChannel
            The deserialized partial channel-derived object.

        Raises
        ------
        builtins.KeyError
            If `guild_id` is left as `hikari.undefined.UNDEFINED` when
            `"guild_id"` is not present in the passed payload of a guild
            channel.
        hikari.errors.UnrecognisedEntityError
            If the channel type is unknown.
        """

    ################
    # EMBED MODELS #
    ################

    @abc.abstractmethod
    def deserialize_embed(self, payload: data_binding.JSONObject) -> embed_models.Embed:
        """Parse a raw payload from Discord into an embed object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.embeds.Embed
            The deserialized embed object.
        """

    @abc.abstractmethod
    def serialize_embed(
        self, embed: embed_models.Embed
    ) -> typing.Tuple[data_binding.JSONObject, typing.List[files.Resource[files.AsyncReader]]]:
        """Serialize an embed object to a json serializable dict.

        Parameters
        ----------
        embed : hikari.embeds.Embed
            The embed object to serialize.

        Returns
        -------
        typing.Tuple[hikari.internal.data_binding.JSONObject, typing.List[hikari.files.Resource]]
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
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.emojis.UnicodeEmoji
            The deserialized unicode emoji object.
        """

    @abc.abstractmethod
    def deserialize_custom_emoji(self, payload: data_binding.JSONObject) -> emoji_models.CustomEmoji:
        """Parse a raw payload from Discord into a custom emoji object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.emojis.CustomEmoji
            The deserialized custom emoji object.
        """

    @abc.abstractmethod
    def deserialize_known_custom_emoji(
        self, payload: data_binding.JSONObject, *, guild_id: snowflakes.Snowflake
    ) -> emoji_models.KnownCustomEmoji:
        """Parse a raw payload from Discord into a known custom emoji object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.
        guild_id : hikari.snowflakes.Snowflake
            The ID of the guild this emoji belongs to. This is used to ensure
            that the guild a known custom emoji belongs to is remembered by
            allowing for a context based artificial `guild_id` attribute.

        Returns
        -------
        hikari.emojis.KnownCustomEmoji
            The deserialized "known custom emoji" object.
        """

    @abc.abstractmethod
    def deserialize_emoji(
        self, payload: data_binding.JSONObject
    ) -> typing.Union[emoji_models.UnicodeEmoji, emoji_models.CustomEmoji]:
        """Parse a raw payload from Discord into an emoji object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.emojis.UnicodeEmoji or hikari.emojis.CustomEmoji
            The deserialized custom or unicode emoji object.
        """

    ##################
    # GATEWAY MODELS #
    ##################

    @abc.abstractmethod
    def deserialize_gateway_bot_info(self, payload: data_binding.JSONObject) -> gateway_models.GatewayBotInfo:
        """Parse a raw payload from Discord into a gateway bot object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.sessions.GatewayBotInfo
            The deserialized gateway bot information object.
        """

    ################
    # GUILD MODELS #
    ################

    @abc.abstractmethod
    def deserialize_guild_widget(self, payload: data_binding.JSONObject) -> guild_models.GuildWidget:
        """Parse a raw payload from Discord into a guild widget object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.guilds.GuildWidget
            The deserialized guild widget object.
        """

    @abc.abstractmethod
    def deserialize_welcome_screen(self, payload: data_binding.JSONObject) -> guild_models.WelcomeScreen:
        """Parse a raw payload from Discord into a guild welcome screen object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.guilds.WelcomeScreen
            The deserialized guild welcome screen object.
        """

    @abc.abstractmethod
    def serialize_welcome_channel(self, welcome_channel: guild_models.WelcomeChannel) -> data_binding.JSONObject:
        """Serialize a welcome channel object to a json serializable dict.

        Parameters
        ----------
        welcome_channel : hikari.guilds.WelcomeChannel
            The guild welcome channel object to serialize.

        Returns
        -------
        hikari.internal.data_binding.JSONObject
            The serialized representation of the welcome channel.
        """

    @abc.abstractmethod
    def deserialize_member(
        self,
        payload: data_binding.JSONObject,
        *,
        user: undefined.UndefinedOr[user_models.User] = undefined.UNDEFINED,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> guild_models.Member:
        """Parse a raw payload from Discord into a member object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Other Parameters
        ----------------
        user : hikari.undefined.UndefinedOr[hikari.users.User]
            The user to attach to this member, should only be passed in
            situations where "user" is not included in the payload.
        guild_id : hikari.undefined.UndefinedOr[hikari.snowflakes.Snowflake]
            The ID of the guild this member belongs to. If this is specified
            then this will be prioritised over `"guild_id"` in the payload.

        !!! note
            `guild_id` covers cases such as the GUILD_CREATE gateway event and
            GET Guild Member where `"guild_id"` is not included in the returned
            payload.

        Returns
        -------
        hikari.guilds.Member
            The deserialized member object.

        Raises
        ------
        builtins.KeyError
            If `guild_id` is left as `hikari.undefined.UNDEFINED` when
            `"guild_id"` is not present in the passed payload.
        """

    @abc.abstractmethod
    def deserialize_role(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: snowflakes.Snowflake,
    ) -> guild_models.Role:
        """Parse a raw payload from Discord into a role object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.
        guild_id : hikari.snowflakes.Snowflake
            The ID of the guild this role belongs to. This is used to ensure
            that the guild a role belongs to is remembered by allowing for a
            context based artificial `guild_id` attribute.

        Returns
        -------
        hikari.guilds.Role
            The deserialized role object.
        """

    @abc.abstractmethod
    def deserialize_partial_integration(self, payload: data_binding.JSONObject) -> guild_models.PartialIntegration:
        """Parse a raw payload from Discord into a partial integration object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.guilds.PartialIntegration
            The deserialized partial integration object.
        """

    @abc.abstractmethod
    def deserialize_integration(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> guild_models.Integration:
        """Parse a raw payload from Discord into an integration object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Other Parameters
        ----------------
        guild_id : hikari.undefined.UndefinedOr[hikari.snowflakes.Snowflake]
            The ID of the guild this integration belongs to. If this is specified
            then this will be prioritised over `"guild_id"` in the payload.

        Returns
        -------
        hikari.guilds.Integration
            The deserialized integration object.

        Raises
        ------
        builtins.KeyError
            If `guild_id` is left as `hikari.undefined.UNDEFINED` when
            `"guild_id"` is not present in the passed payload for the payload of
            the integration.
        """

    @abc.abstractmethod
    def deserialize_guild_member_ban(self, payload: data_binding.JSONObject) -> guild_models.GuildBan:
        """Parse a raw payload from Discord into a guild member ban object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.guilds.GuildBan
            The deserialized guild member ban object.
        """

    @abc.abstractmethod
    def deserialize_guild_preview(self, payload: data_binding.JSONObject) -> guild_models.GuildPreview:
        """Parse a raw payload from Discord into a guild preview object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.guilds.GuildPreview
            The deserialized guild preview object.
        """

    @abc.abstractmethod
    def deserialize_rest_guild(self, payload: data_binding.JSONObject) -> guild_models.RESTGuild:
        """Parse a raw payload from Discord into a guild object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.guilds.RESTGuild
            The deserialized guild object.
        """

    @abc.abstractmethod
    def deserialize_gateway_guild(self, payload: data_binding.JSONObject) -> GatewayGuildDefinition:
        """Parse a raw payload from Discord into a guild object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        GatewayGuildDefinition
            The deserialized guild object and the internal collections as
            maps of `hikari.snowflakes.Snowflake` mapping to
            `hikari.channels.GuildChannel`,
            `hikari.guilds.Member`,
            `hikari.presences.MemberPresence`,
            `hikari.guilds.Role`, and
            `hikari.emojis.KnownCustomEmoji`. This is provided in
            several components to allow separate caching and linking
            between entities in various relational cache implementations
            internally.
        """

    ######################
    # INTERACTION MODELS #
    ######################

    @abc.abstractmethod
    def deserialize_command(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedNoneOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> commands.Command:
        """Parse a raw payload from Discord into a command object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Other Parameters
        ----------------
        guild_id : hikari.undefined.UndefinedNoneOr[hikari.snowflakes.Snowflake]
            The ID of the guild this command belongs to. If this is specified
            then this will be prioritised over `"guild_id"` in the payload.

        Returns
        -------
        hikari.commands.Command
            The deserialized command object.

        Raises
        ------
        builtins.KeyError
            If `guild_id` is left as `hikari.undefined.UNDEFINED` when
            `"guild_id"` is not present in the passed payload for the payload of
            the integration.
        """

    @abc.abstractmethod
    def deserialize_guild_command_permissions(
        self, payload: data_binding.JSONObject
    ) -> commands.GuildCommandPermissions:
        """Parse a raw payload from Discord into guild command permissions object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.commands.GuildCommandPermissions
            The deserialized guild command permissions object.
        """

    @abc.abstractmethod
    def serialize_command_permission(self, permission: commands.CommandPermission) -> data_binding.JSONObject:
        """Serialize a command permission object to a json serializable dict.

        Parameters
        ----------
        permission: hikari.commands.CommandPermission
            The command permission object to serialize.

        Returns
        -------
        hikari.internal.data_binding.JSONObject
            The serialized representation of the command permission.
        """

    @abc.abstractmethod
    def deserialize_partial_interaction(self, payload: data_binding.JSONObject) -> base_interactions.PartialInteraction:
        """Parse a raw payload from Discord into a partial interaction object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.interactions.base_interactions.PartialInteraction
            The deserialized partial interaction object.
        """

    @abc.abstractmethod
    def deserialize_command_interaction(
        self, payload: data_binding.JSONObject
    ) -> command_interactions.CommandInteraction:
        """Parse a raw payload from Discord into a command interaction object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.interactions.command_interactions.CommandInteraction
            The deserialized command interaction object.
        """

    @abc.abstractmethod
    def deserialize_interaction(self, payload: data_binding.JSONObject) -> base_interactions.PartialInteraction:
        """Parse a raw payload from Discord into a interaction object.

        !!! note
            This isn't required to implement logic for deserializing
            PING interactions and if you want to unmarshal those
            `EntityFactory.deserialize_partial_interaction` should be compatible.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.interactions.base_interactions.PartialInteraction
            The deserialized interaction object.

        Raises
        ------
        hikari.errors.UnrecognisedEntityError
            If the integration type is unknown.
        """

    @abc.abstractmethod
    def serialize_command_option(self, option: commands.CommandOption) -> data_binding.JSONObject:
        """Serialize a command option object to a json serializable dict.

        Parameters
        ----------
        option: hikari.commands.CommandOption
            The command option object to serialize.

        Returns
        -------
        hikari.internal.data_binding.JSONObject
            The serialized representation of the command option.
        """

    @abc.abstractmethod
    def deserialize_component_interaction(
        self, payload: data_binding.JSONObject
    ) -> component_interactions.ComponentInteraction:
        """Parser a raw payload from Discord into a component interaction object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.interactions.component_interactions.ComponentInteraction
            The deserialized component interaction.
        """

    #################
    # INVITE MODELS #
    #################

    @abc.abstractmethod
    def deserialize_vanity_url(self, payload: data_binding.JSONObject) -> invite_models.VanityURL:
        """Parse a raw payload from Discord into a vanity url object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.invites.VanityURL
            The deserialized vanity url object.
        """

    @abc.abstractmethod
    def deserialize_invite(self, payload: data_binding.JSONObject) -> invite_models.Invite:
        """Parse a raw payload from Discord into an invite object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.invites.Invite
            The deserialized invite object.
        """

    @abc.abstractmethod
    def deserialize_invite_with_metadata(self, payload: data_binding.JSONObject) -> invite_models.InviteWithMetadata:
        """Parse a raw payload from Discord into a invite with metadata object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.invites.InviteWithMetadata
            The deserialized invite with metadata object.
        """

    ##################
    # STICKER MODELS #
    ##################

    @abc.abstractmethod
    def deserialize_sticker_pack(self, payload: data_binding.JSONObject) -> sticker_models.StickerPack:
        """Parse a raw payload from Discord into a sticker pack object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.stickers.StickerPack
            The deserialized sticker pack object.
        """

    @abc.abstractmethod
    def deserialize_partial_sticker(self, payload: data_binding.JSONObject) -> sticker_models.PartialSticker:
        """Parse a raw payload from Discord into a partial sticker object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.stickers.PartialSticker
            The deserialized partial sticker object.
        """

    @abc.abstractmethod
    def deserialize_standard_sticker(self, payload: data_binding.JSONObject) -> sticker_models.StandardSticker:
        """Parse a raw payload from Discord into a standard sticker object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.stickers.StandardSticker
            The deserialized standard sticker object.
        """

    @abc.abstractmethod
    def deserialize_guild_sticker(self, payload: data_binding.JSONObject) -> sticker_models.GuildSticker:
        """Parse a raw payload from Discord into a guild sticker object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.stickers.GuildSticker
            The deserialized guild sticker object.
        """

    ##################
    # MESSAGE MODELS #
    ##################

    @abc.abstractmethod
    def deserialize_action_row(self, payload: data_binding.JSONObject) -> message_models.ActionRowComponent:
        """Parse a raw payload from Discord into an action row component object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.messages.ActionRowComponent
            The deserialized action row component.
        """

    @abc.abstractmethod
    def deserialize_button(self, payload: data_binding.JSONObject) -> message_models.ButtonComponent:
        """Parse a raw payload from Discord into a button component object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.messages.ButtonComponent
            The deserialized button component.
        """

    @abc.abstractmethod
    def deserialize_select_menu(self, payload: data_binding.JSONObject) -> message_models.SelectMenuComponent:
        """Parse a raw payload from Discord into a select menu component object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.messages.SelectMenuComponent
            The deserialized button component.
        """

    @abc.abstractmethod
    def deserialize_component(self, payload: data_binding.JSONObject) -> message_models.PartialComponent:
        """Parse a raw payload from Discord into a message component object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.messages.PartialComponent
            The deserialized message component.
        hikari.errors.UnrecognisedEntityError
            If the message component type isn't recognised.
        """

    @abc.abstractmethod
    def deserialize_partial_message(self, payload: data_binding.JSONObject) -> message_models.PartialMessage:
        """Parse a raw payload from Discord into a partial message object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.messages.PartialMessage
            The deserialized partial message object.
        """

    @abc.abstractmethod
    def deserialize_message(self, payload: data_binding.JSONObject) -> message_models.Message:
        """Parse a raw payload from Discord into a message object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.messages.Message
            The deserialized message object.
        """

    ###################
    # PRESENCE MODELS #
    ###################

    @abc.abstractmethod
    def deserialize_member_presence(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> presence_models.MemberPresence:
        """Parse a raw payload from Discord into a member presence object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Other Parameters
        ----------------
        guild_id : hikari.undefined.UndefinedOr[hikari.snowflakes.Snowflake]
            The ID of the guild the presence belongs to. If this is specified
            then it is prioritised over `guild_id` in the payload.

        !!! note
            At the time of writing, the only place where `guild_id` will be
            mandatory is when parsing presences sent in a `GUILD_CREATE` event
            from Discord, since the `guild_id` attribute in the payload will
            have been omitted for redundancy.

        Returns
        -------
        hikari.presences.MemberPresence
            The deserialized member presence object.

        Raises
        ------
        builtins.KeyError
            If `guild_id` is not an attribute of the `payload` dict, and no
            guild ID was passed for the `guild_id` parameter.

            If this is raised, no guild ID info was provided anywhere.
        """

    ###################
    # TEMPLATE MODELS #
    ###################

    @abc.abstractmethod
    def deserialize_template(self, payload: data_binding.JSONObject) -> template_models.Template:
        """Parse a raw payload from Discord into a template object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.templates.Template
            The deserialized template object.
        """

    ###############
    # USER MODELS #
    ###############

    @abc.abstractmethod
    def deserialize_user(self, payload: data_binding.JSONObject) -> user_models.User:
        """Parse a raw payload from Discord into a user object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.users.User
            The deserialized user object.
        """

    @abc.abstractmethod
    def deserialize_my_user(self, payload: data_binding.JSONObject) -> user_models.OwnUser:
        """Parse a raw payload from Discord into a user object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.users.OwnUser
            The deserialized user object.
        """

    ################
    # VOICE MODELS #
    ################

    @abc.abstractmethod
    def deserialize_voice_state(
        self,
        payload: data_binding.JSONObject,
        *,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
        member: undefined.UndefinedOr[guild_models.Member] = undefined.UNDEFINED,
    ) -> voice_models.VoiceState:
        """Parse a raw payload from Discord into a voice state object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Other Parameters
        ----------------
        guild_id : hikari.undefined.UndefinedOr[hikari.snowflakes.Snowflake]
            The ID of the guild this voice state belongs to. If this is specified
            then this will be prioritised over `"guild_id"` in the payload.
        member : hikari.undefined.UndefinedOr[hikari.guilds.Member]
            The object of the member this voice state belongs to. If this is
            specified then this will be prioritised over `"member"` in the
            payload.

        !!! note
            At the time of writing, `GUILD_CREATE` events are the only known
            place where neither `guild_id` nor `member` will be keys on the
            payload. In this case, you will need to provide the former
            parameters explicitly.

        Returns
        -------
        hikari.voices.VoiceState
            The deserialized voice state object.

        Raises
        ------
        builtins.KeyError
            If `guild_id` is left as `hikari.undefined.UNDEFINED` when
            `"guild_id"` is not present in the passed payload for the payload of
            the voice state.

            This will also be raised if no `member` data was passed in any
            acceptable place.
        """

    @abc.abstractmethod
    def deserialize_voice_region(self, payload: data_binding.JSONObject) -> voice_models.VoiceRegion:
        """Parse a raw payload from Discord into a voice region object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.voices.VoiceRegion
            The deserialized voice region object.
        """

    ##################
    # WEBHOOK MODELS #
    ##################

    @abc.abstractmethod
    def deserialize_incoming_webhook(self, payload: data_binding.JSONObject) -> webhook_models.IncomingWebhook:
        """Parse a raw payload from Discord into a incoming webhook object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.webhooks.IncomingWebhook
            The parsed incoming webhook object.
        """

    @abc.abstractmethod
    def deserialize_channel_follower_webhook(
        self, payload: data_binding.JSONObject
    ) -> webhook_models.ChannelFollowerWebhook:
        """Parse a raw payload from Discord into a channel follower webhook object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.webhooks.ChannelFollowerWebhook
            The parsed channel follower webhook object.
        """

    @abc.abstractmethod
    def deserialize_application_webhook(self, payload: data_binding.JSONObject) -> webhook_models.ApplicationWebhook:
        """Parse a raw payload from Discord into an application webhook object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.webhooks.ApplicationWebhook
            The parsed application webhook object.
        """

    @abc.abstractmethod
    def deserialize_webhook(self, payload: data_binding.JSONObject) -> webhook_models.PartialWebhook:
        """Parse a raw payload from Discord into a webhook object.

        Parameters
        ----------
        payload : hikari.internal.data_binding.JSONObject
            The JSON payload to deserialize.

        Returns
        -------
        hikari.webhooks.PartialWebhook
            The deserialized webhook object.
        """
