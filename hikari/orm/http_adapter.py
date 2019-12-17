#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""
Bridges the HTTP API and the state registry to provide an object-oriented interface
to use to interact with the HTTP API.
"""
from __future__ import annotations

import typing

from hikari.internal_utilities import cache
from hikari.internal_utilities import data_structures
from hikari.internal_utilities import io_helpers
from hikari.internal_utilities import unspecified
from hikari.orm import fabric as _fabric
from hikari.orm.models import applications as _applications
from hikari.orm.models import audit_logs as _audit_logs
from hikari.orm.models import channels as _channels
from hikari.orm.models import colors as _colors
from hikari.orm.models import connections as _connections
from hikari.orm.models import embeds as _embeds
from hikari.orm.models import emojis as _emojis
from hikari.orm.models import gateway_bot as _gateway_bot
from hikari.orm.models import guilds as _guilds
from hikari.orm.models import integrations as _integrations
from hikari.orm.models import interfaces
from hikari.orm.models import invites as _invites
from hikari.orm.models import media as _media
from hikari.orm.models import members as _members
from hikari.orm.models import messages as _messages
from hikari.orm.models import overwrites as _overwrites
from hikari.orm.models import permissions as _permissions
from hikari.orm.models import reactions as _reactions
from hikari.orm.models import roles as _roles
from hikari.orm.models import users as _users
from hikari.orm.models import voices as _voices
from hikari.orm.models import webhooks as _webhooks


class HTTPAdapter:
    """
    Component that bridges the basic HTTP API exposed by :mod:`hikari.net.http_client` and
    wraps it in a unit of processing that can handle parsing API objects into Hikari ORM objects,
    and can handle keeping the state up to date as required.
    """

    __slots__ = ("fabric", "_cp_gateway_url")

    def __init__(self, fabric: _fabric.Fabric) -> None:
        #: The fabric of this application.
        self.fabric: _fabric.Fabric = fabric

    @cache.cached_property()
    async def gateway_url(self) -> str:
        """
        Returns:
            A static URL to use to connect to the gateway with.

        Note:
            This call is cached after the first invocation. This does not require authorization
            to work.
        """
        return await self.fabric.http_api.get_gateway()

    async def fetch_gateway_bot(self) -> _gateway_bot.GatewayBot:
        """
        Returns:
            The gateway bot details to use as a recommendation for sharding and bot initialization.

        Note:
            Unlike :meth:`get_gateway`, this requires valid Bot authorization to work.
        """
        gateway_bot_payload = await self.fabric.http_api.get_gateway_bot()
        return _gateway_bot.GatewayBot(gateway_bot_payload)

    async def fetch_audit_log(
        self,
        guild: _guilds.GuildLikeT,
        *,
        user: _users.IUserLikeT = unspecified.UNSPECIFIED,
        action_type: _audit_logs.AuditLogEvent = unspecified.UNSPECIFIED,
        limit: int = unspecified.UNSPECIFIED,
    ) -> _audit_logs.AuditLog:
        audit_payload = await self.fabric.http_api.get_guild_audit_log(
            guild_id=str(int(guild)),
            user_id=str(int(user)) if user is not unspecified.UNSPECIFIED else unspecified.UNSPECIFIED,
            action_type=int(action_type) if action_type is not unspecified.UNSPECIFIED else unspecified.UNSPECIFIED,
            limit=limit,
        )
        return _audit_logs.AuditLog(self.fabric, audit_payload)

    async def fetch_channel(self, channel_id: _channels.ChannelLikeT) -> _channels.Channel:
        raise NotImplementedError

    async def update_channel(
        self,
        channel: _channels.ChannelLikeT,
        *,
        position: int = unspecified.UNSPECIFIED,
        topic: str = unspecified.UNSPECIFIED,
        nsfw: bool = unspecified.UNSPECIFIED,
        rate_limit_per_user: int = unspecified.UNSPECIFIED,
        bitrate: int = unspecified.UNSPECIFIED,
        user_limit: int = unspecified.UNSPECIFIED,
        permission_overwrites: typing.Collection[_overwrites.Overwrite] = unspecified.UNSPECIFIED,
        parent_category: typing.Optional[_channels.GuildCategoryLikeT] = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> _channels.Channel:
        raise NotImplementedError

    async def delete_channel(self, channel: _channels.ChannelLikeT) -> None:
        raise NotImplementedError

    async def fetch_messages(
        self,
        channel: _channels.TextChannelLikeT,
        *,
        limit: int = unspecified.UNSPECIFIED,
        after: _messages.MessageLikeT = unspecified.UNSPECIFIED,
        before: _messages.MessageLikeT = unspecified.UNSPECIFIED,
        around: _messages.MessageLikeT = unspecified.UNSPECIFIED,
        in_order: bool = False,
    ) -> typing.AsyncIterator[_messages.Message]:
        raise NotImplementedError

    async def fetch_message(
        self, channel: _channels.TextChannelLikeT, message: _messages.MessageLikeT
    ) -> _messages.Message:
        raise NotImplementedError

    async def create_message(
        self,
        channel: _channels.TextChannelLikeT,
        *,
        content: str = unspecified.UNSPECIFIED,
        tts: bool = False,
        files: typing.Collection[_media.AbstractFile] = unspecified.UNSPECIFIED,
        embed: _embeds.Embed = unspecified.UNSPECIFIED,
    ) -> _messages.Message:
        raise NotImplementedError

    async def create_reaction(
        self, message: _messages.MessageLikeT, emoji: _emojis.KnownEmojiLikeT
    ) -> _reactions.Reaction:
        raise NotImplementedError

    async def delete_reaction(self, reaction: _reactions.Reaction, user: _users.IUserLikeT) -> None:
        raise NotImplementedError

    async def delete_all_reactions(self, message: _messages.MessageLikeT) -> None:
        raise NotImplementedError

    async def update_message(
        self,
        message: _messages.MessageLikeT,
        content: typing.Optional[str] = unspecified.UNSPECIFIED,
        embed: typing.Optional[_embeds.Embed] = unspecified.UNSPECIFIED,
        flags: int = unspecified.UNSPECIFIED,
    ) -> _messages.Message:
        raise NotImplementedError

    async def delete_messages(
        self, first_message: _messages.MessageLikeT, *additional_messages: _messages.MessageLikeT
    ) -> None:
        raise NotImplementedError

    async def update_channel_overwrite(
        self,
        channel: _channels.GuildChannelLikeT,
        overwrite: _overwrites.OverwriteLikeT,
        *,
        allow: int = unspecified.UNSPECIFIED,
        deny: int = unspecified.UNSPECIFIED,
        type_: _overwrites.OverwriteEntityType = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        raise NotImplementedError

    async def fetch_invites_for_channel(self, channel: _channels.GuildChannelLikeT) -> typing.Sequence[_invites.Invite]:
        raise NotImplementedError

    async def create_invite_for_channel(
        self,
        channel: _channels.GuildChannelLikeT,
        *,
        max_age: int = unspecified.UNSPECIFIED,
        max_uses: int = unspecified.UNSPECIFIED,
        temporary: bool = unspecified.UNSPECIFIED,
        unique: bool = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> _invites.Invite:
        raise NotImplementedError

    async def delete_channel_overwrite(
        self, channel: _channels.GuildChannelLikeT, overwrite: _overwrites.OverwriteLikeT,
    ) -> None:
        raise NotImplementedError

    async def trigger_typing(self, channel: _channels.TextChannelLikeT) -> _channels.TypingIndicator:
        raise NotImplementedError

    async def fetch_pins(
        self, channel: _channels.TextChannelLikeT, *, in_order: bool = False
    ) -> typing.AsyncIterator[_messages.Message]:
        raise NotImplementedError

    async def pin_message(self, message: _messages.MessageLikeT) -> None:
        raise NotImplementedError

    async def unpin_message(self, message: _messages.MessageLikeT) -> None:
        raise NotImplementedError

    async def fetch_guild_emoji(
        self, emoji: _emojis.GuildEmojiLikeT, guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED
    ) -> _emojis.GuildEmoji:
        raise NotImplementedError

    async def fetch_guild_emojis(self, guild: _guilds.GuildLikeT) -> typing.Collection[_emojis.GuildEmoji]:
        raise NotImplementedError

    async def create_guild_emoji(
        self,
        guild: _guilds.GuildLikeT,
        name: str,
        image_data: io_helpers.FileLikeT,
        *,
        roles: typing.Collection[_roles.RoleLikeT] = data_structures.EMPTY_COLLECTION,
        reason: str = unspecified.UNSPECIFIED,
    ) -> _emojis.GuildEmoji:
        raise NotImplementedError

    async def update_guild_emoji(
        self,
        emoji: _emojis.GuildEmojiLikeT,
        *,
        name: str = unspecified.UNSPECIFIED,
        roles: typing.Collection[_roles.RoleLikeT] = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        raise NotImplementedError

    async def delete_guild_emoji(self, emoji: _emojis.GuildEmojiLikeT) -> None:
        raise NotImplementedError

    #: FIXME: refine what this call allows and consumes...
    create_guild = NotImplemented

    async def fetch_guild(self, guild: _guilds.GuildLikeT) -> _guilds.Guild:
        raise NotImplementedError

    async def update_guild(
        self,
        guild: _guilds.GuildLikeT,
        *,
        name: str = unspecified.UNSPECIFIED,
        region: str = unspecified.UNSPECIFIED,
        verification_level: _guilds.VerificationLevel = unspecified.UNSPECIFIED,
        default_message_notifications: _guilds.DefaultMessageNotificationsLevel = unspecified.UNSPECIFIED,
        explicit_content_filter: _guilds.ExplicitContentFilterLevel = unspecified.UNSPECIFIED,
        afk_channel: _channels.GuildVoiceChannel = unspecified.UNSPECIFIED,
        afk_timeout: int = unspecified.UNSPECIFIED,
        icon_data: io_helpers.FileLikeT = unspecified.UNSPECIFIED,
        #: TODO: While this will always be a member of the guild for it to work, do I want to allow any user here too?
        owner: _members.MemberLikeT = unspecified.UNSPECIFIED,
        splash: io_helpers.FileLikeT = unspecified.UNSPECIFIED,
        #: TODO: Can this be an announcement (news) channel also?
        system_channel: _channels.GuildTextChannelLikeT = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        raise NotImplementedError

    async def delete_guild(self, guild: _guilds.GuildLikeT) -> None:
        raise NotImplementedError

    async def fetch_guild_channels(self, guild: _guilds.GuildLikeT) -> typing.Sequence[_channels.GuildChannel]:
        # Sequence as it should be in channel positional order...
        raise NotImplementedError

    async def create_guild_channel(
        self,
        guild: _guilds.GuildLikeT,
        name: str,
        channel_type: _channels.ChannelType,
        *,
        topic: str = unspecified.UNSPECIFIED,
        bitrate: int = unspecified.UNSPECIFIED,
        user_limit: int = unspecified.UNSPECIFIED,
        rate_limit_per_user: int = unspecified.UNSPECIFIED,
        position: int = unspecified.UNSPECIFIED,
        permission_overwrites: typing.Collection[_overwrites.Overwrite] = unspecified.UNSPECIFIED,
        parent_category: typing.Optional[_channels.GuildCategoryLikeT] = None,
        nsfw: bool = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> _channels.GuildChannel:
        raise NotImplementedError

    async def reposition_guild_channels(
        self,
        guild: _guilds.GuildLikeT,
        first_channel: typing.Tuple[int, _channels.GuildChannelLikeT],
        *additional_channels: typing.Tuple[int, _channels.GuildChannelLikeT],
    ) -> None:
        raise NotImplementedError

    async def fetch_member(
        self,
        user: typing.Union[_users.IUserLikeT, _members.MemberLikeT],
        guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
    ) -> _members.Member:
        raise NotImplementedError

    async def fetch_members(
        self, guild: _guilds.GuildLikeT, *, limit: int = unspecified.UNSPECIFIED,
    ) -> typing.Collection[_members.Member]:
        raise NotImplementedError

    async def update_member(
        self,
        member: _members.MemberLikeT,
        *,
        nick: typing.Optional[str] = unspecified.UNSPECIFIED,
        roles: typing.Collection[_roles.RoleLikeT] = unspecified.UNSPECIFIED,
        mute: bool = unspecified.UNSPECIFIED,
        deaf: bool = unspecified.UNSPECIFIED,
        current_voice_channel: typing.Optional[_channels.GuildVoiceChannelLikeT] = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        raise NotImplementedError

    async def update_member_nickname(self, member: _members.MemberLikeT, nick: typing.Optional[str]) -> None:
        raise NotImplementedError

    async def add_role_to_member(
        self, role: _roles.RoleLikeT, member: _members.MemberLikeT, *, reason: str = unspecified.UNSPECIFIED
    ) -> None:
        raise NotImplementedError

    async def remove_role_from_member(
        self, role: _roles.RoleLikeT, member: _members.MemberLikeT, *, reason: str = unspecified.UNSPECIFIED
    ) -> None:
        raise NotImplementedError

    async def kick_member(self, member: _members.MemberLikeT, *, reason: str = unspecified.UNSPECIFIED) -> None:
        raise NotImplementedError

    async def fetch_ban(self, guild: _guilds.GuildLikeT, user: _users.IUserLikeT) -> _guilds.Ban:
        raise NotImplementedError

    async def fetch_bans(self, guild: _guilds.GuildLikeT) -> typing.Collection[_guilds.Ban]:
        raise NotImplementedError

    async def ban_member(
        self,
        guild: _guilds.GuildLikeT,
        user: _users.IUserLikeT,
        *,
        delete_message_days: typing.Optional[int] = None,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        raise NotImplementedError

    async def unban_member(
        self, guild: _guilds.GuildLikeT, user: _users.IUserLikeT, *, reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        raise NotImplementedError

    async def fetch_roles(self, guild: _guilds.GuildLikeT) -> typing.Sequence[_roles.Role]:
        raise NotImplementedError

    async def create_role(
        self,
        guild: _guilds.GuildLikeT,
        *,
        name: str = unspecified.UNSPECIFIED,
        permissions: _permissions.PermissionLikeT = unspecified.UNSPECIFIED,
        color: _colors.ColorCompatibleT = unspecified.UNSPECIFIED,
        hoist: bool = unspecified.UNSPECIFIED,
        mentionable: bool = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> _roles.Role:
        raise NotImplementedError

    async def reposition_roles(
        self,
        guild: _guilds.GuildLikeT,
        first_role: typing.Tuple[int, _roles.RoleLikeT],
        *additional_roles: typing.Tuple[int, _roles.RoleLikeT],
    ) -> None:
        raise NotImplementedError

    async def update_role(
        self,
        guild: _guilds.GuildLikeT,
        role: _roles.RoleLikeT,
        *,
        name: str = unspecified.UNSPECIFIED,
        permissions: _permissions.PermissionLikeT = unspecified.UNSPECIFIED,
        color: _colors.ColorCompatibleT = unspecified.UNSPECIFIED,
        hoist: bool = unspecified.UNSPECIFIED,
        mentionable: bool = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        raise NotImplementedError

    async def delete_role(self, guild: _guilds.GuildLikeT, role: _roles.RoleLikeT) -> None:
        raise NotImplementedError

    async def estimate_guild_prune_count(self, guild: _guilds.GuildLikeT, days: int) -> int:
        raise NotImplementedError

    async def begin_guild_prune(
        self,
        guild: _guilds.GuildLikeT,
        days: int,
        *,
        compute_prune_count: bool = False,
        reason: str = unspecified.UNSPECIFIED,
    ) -> typing.Optional[int]:
        raise NotImplementedError

    async def fetch_guild_voice_regions(self, guild: _guilds.GuildLikeT) -> typing.Collection[_voices.VoiceRegion]:
        raise NotImplementedError

    async def fetch_guild_invites(self, guild: _guilds.GuildLikeT) -> typing.Collection[_invites.Invite]:
        raise NotImplementedError

    async def fetch_integrations(self, guild: _guilds.GuildLikeT) -> typing.Collection[_integrations.Integration]:
        raise NotImplementedError

    async def create_guild_integration(
        self,
        guild: _guilds.GuildLikeT,
        type_: str,
        integration_id: interfaces.RawSnowflakeT,
        *,
        reason: str = unspecified.UNSPECIFIED,
    ) -> _integrations.Integration:
        raise NotImplementedError

    async def update_integration(
        self,
        guild: _guilds.GuildLikeT,
        integration: _integrations.IntegrationLikeT,
        *,
        expire_behaviour: int = unspecified.UNSPECIFIED,  # TODO: is this documented?
        expire_grace_period: int = unspecified.UNSPECIFIED,  #: TODO: is this days or seconds?
        enable_emojis: bool = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        raise NotImplementedError

    async def delete_integration(self, guild: _guilds.GuildLikeT, integration: _integrations.IntegrationLikeT) -> None:
        raise NotImplementedError

    async def sync_guild_integration(
        self, guild: _guilds.GuildLikeT, integration: _integrations.IntegrationLikeT
    ) -> None:
        raise NotImplementedError

    async def fetch_guild_embed(self, guild: _guilds.GuildLikeT) -> _embeds.ReceivedEmbed:
        raise NotImplementedError

    async def modify_guild_embed(
        self, guild: _guilds.GuildLikeT, embed: _embeds.Embed, *, reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        raise NotImplementedError

    async def fetch_guild_vanity_url(self, guild: _guilds.GuildLikeT) -> str:
        raise NotImplementedError

    def fetch_guild_widget_image(
        self, guild: _guilds.GuildLikeT, *, style: _guilds.WidgetStyle = unspecified.UNSPECIFIED
    ) -> str:
        raise NotImplementedError

    async def fetch_invite(self, invite_code: _invites.InviteLikeT) -> _invites.Invite:
        raise NotImplementedError

    async def delete_invite(self, invite_code: _invites.InviteLikeT) -> None:
        raise NotImplementedError

    async def fetch_user(self, user: _users.IUserLikeT) -> typing.Union[_users.User, _users.OAuth2User]:
        raise NotImplementedError

    async def fetch_application_info(self) -> _applications.Application:
        raise NotImplementedError

    async def fetch_me(self) -> _users.OAuth2User:
        raise NotImplementedError

    async def update_me(
        self, *, username: str = unspecified.UNSPECIFIED, avatar: io_helpers.FileLikeT = unspecified.UNSPECIFIED,
    ) -> None:
        raise NotImplementedError

    async def fetch_my_connections(self) -> typing.Sequence[_connections.Connection]:
        raise NotImplementedError

    async def fetch_my_guilds(
        self,
        before: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
        after: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
        limit: int = unspecified.UNSPECIFIED,
    ) -> typing.AsyncIterator[_guilds.Guild]:
        raise NotImplementedError

    async def leave_guild(self, guild: _guilds.GuildLikeT) -> None:
        raise NotImplementedError

    async def create_dm_channel(self, recipient: _users.IUserLikeT) -> _channels.DMChannel:
        raise NotImplementedError

    async def fetch_voice_regions(self) -> typing.Collection[_voices.VoiceRegion]:
        raise NotImplementedError

    async def create_webhook(
        self,
        #: TODO: Can we make webhooks to announcement channels/store channels?
        channel: _channels.GuildTextChannelLikeT,
        name: str,
        *,
        avatar: io_helpers.FileLikeT = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> _webhooks.Webhook:
        raise NotImplementedError

    async def fetch_channel_webhooks(
        #: TODO: Can we make webhooks to announcement channels/store channels?
        self,
        channel: _channels.GuildTextChannelLikeT,
    ) -> typing.Collection[_webhooks.Webhook]:
        raise NotImplementedError

    async def fetch_guild_webhooks(self, guild: _guilds.GuildLikeT) -> typing.Collection[_webhooks.Webhook]:
        raise NotImplementedError

    async def fetch_webhook(self, webhook: _webhooks.WebhookLikeT) -> _webhooks.Webhook:
        raise NotImplementedError

    async def update_webhook(
        self,
        webhook: _webhooks.WebhookLikeT,
        *,
        name: str = unspecified.UNSPECIFIED,
        avatar: bytes = unspecified.UNSPECIFIED,
        #: TODO: Can we make webhooks to announcement channels/store channels?
        channel: _channels.GuildTextChannelLikeT = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        raise NotImplementedError

    async def delete_webhook(self, webhook: _webhooks.WebhookLikeT) -> None:
        raise NotImplementedError
