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
Implementation of a basic HTTP adapter.
"""
from __future__ import annotations

import typing

from hikari.internal_utilities import assertions
from hikari.internal_utilities import cache
from hikari.internal_utilities import containers
from hikari.internal_utilities import storage
from hikari.internal_utilities import transformations
from hikari.internal_utilities import unspecified
from hikari.orm import fabric as _fabric
from hikari.orm.http import base_http_adapter
from hikari.orm.models import applications as _applications
from hikari.orm.models import audit_logs as _audit_logs
from hikari.orm.models import bases
from hikari.orm.models import channels as _channels
from hikari.orm.models import colors as _colors
from hikari.orm.models import connections as _connections
from hikari.orm.models import embeds as _embeds
from hikari.orm.models import emojis as _emojis
from hikari.orm.models import gateway_bot as _gateway_bot
from hikari.orm.models import guilds as _guilds
from hikari.orm.models import integrations as _integrations
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


class HTTPAdapterImpl(base_http_adapter.BaseHTTPAdapter):
    """Implementation of a basic HTTP adapter."""

    __slots__ = ("fabric", "_cp_gateway_url")

    def __init__(self, fabric: _fabric.Fabric) -> None:
        #: The fabric of this application.
        self.fabric: _fabric.Fabric = fabric

    @cache.cached_property()
    async def gateway_url(self) -> str:
        return await self.fabric.http_api.get_gateway()

    async def fetch_gateway_bot(self) -> _gateway_bot.GatewayBot:
        gateway_bot_payload = await self.fabric.http_api.get_gateway_bot()
        return self.fabric.state_registry.parse_gateway_bot(gateway_bot_payload)

    async def fetch_audit_log(
        self,
        guild: _guilds.GuildLikeT,
        *,
        user: _users.BaseUserLikeT = unspecified.UNSPECIFIED,
        action_type: _audit_logs.AuditLogEventLikeT = unspecified.UNSPECIFIED,
        limit: int = unspecified.UNSPECIFIED,
    ) -> _audit_logs.AuditLog:
        audit_log_payload = await self.fabric.http_api.get_guild_audit_log(
            guild_id=transformations.get_id(guild),
            user_id=transformations.cast_if_specified(user, transformations.get_id),
            action_type=transformations.cast_if_specified(action_type, int),
            limit=limit,
        )
        return self.fabric.state_registry.parse_audit_log(audit_log_payload)

    async def fetch_channel(self, channel: _channels.ChannelLikeT) -> _channels.Channel:
        channel_payload = await self.fabric.http_api.get_channel(transformations.get_id(channel))
        guild_id = channel_payload.get("guild_id")
        guild_obj = (
            self.fabric.state_registry.get_mandatory_guild_by_id(int(guild_id)) if guild_id is not None else guild_id
        )
        return self.fabric.state_registry.parse_channel(channel_payload, guild_obj)

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
        channel_obj = await self.fabric.http_api.modify_channel(
            channel_id=transformations.get_id(channel),
            position=position,
            topic=topic,
            nsfw=nsfw,
            rate_limit_per_user=rate_limit_per_user,
            bitrate=bitrate,
            user_limit=user_limit,
            permission_overwrites=transformations.cast_if_specified(
                permission_overwrites, lambda obj: obj.to_dict(), iterable=True
            ),
            parent_id=transformations.cast_if_specified(parent_category, transformations.get_id, nullable=True),
            reason=reason,
        )
        guild_id = channel_obj.get("guild_id")
        guild_obj = (
            self.fabric.state_registry.get_mandatory_guild_by_id(int(guild_id)) if guild_id is not None else guild_id
        )
        return self.fabric.state_registry.parse_channel(channel_obj, guild_obj)

    async def delete_channel(self, channel: _channels.ChannelLikeT) -> None:
        await self.fabric.http_api.delete_close_channel(channel_id=transformations.get_id(channel))

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
        self, message: _messages.MessageLikeT, *, channel: _channels.TextChannelLikeT = unspecified.UNSPECIFIED
    ) -> _messages.Message:
        message_payload = await self.fabric.http_api.get_channel_message(
            message_id=transformations.get_id(message),
            channel_id=transformations.get_parent_id_from_model(message, channel, "channel"),
        )
        return self.fabric.state_registry.parse_message(message_payload)

    async def create_message(
        self,
        channel: _channels.TextChannelLikeT,
        *,
        content: str = unspecified.UNSPECIFIED,
        tts: bool = False,
        files: typing.Collection[_media.AbstractFile] = unspecified.UNSPECIFIED,
        embed: _embeds.Embed = unspecified.UNSPECIFIED,
    ) -> _messages.Message:
        message_payload = await self.fabric.http_api.create_message(
            channel_id=transformations.get_id(channel),
            content=content,
            tts=tts,
            files=transformations.cast_if_specified(files, lambda file: file.open(), iterable=True),
            embed=transformations.cast_if_specified(embed, lambda obj: obj.to_dict()),
        )
        return self.fabric.state_registry.parse_message(message_payload)

    async def create_reaction(
        self,
        message: _messages.MessageLikeT,
        emoji: _emojis.KnownEmojiLikeT,
        *,
        channel: _channels.GuildChannelLikeT = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.create_reaction(
            channel_id=transformations.get_parent_id_from_model(message, channel, "channel"),
            message_id=transformations.get_id(message),
            emoji=getattr(emoji, "url_name", emoji),
        )

    async def delete_reaction(
        self,
        reaction: typing.Union[_reactions.Reaction, _emojis.KnownEmojiLikeT],
        user: _users.BaseUserLikeT,
        *,
        channel: _channels.GuildChannelLikeT = unspecified.UNSPECIFIED,
        message: _messages.MessageLikeT = unspecified.UNSPECIFIED,
    ) -> None:
        emoji = getattr(reaction, "emoji", reaction)
        message = message or getattr(reaction, "message", message)
        await self.fabric.http_api.delete_user_reaction(
            message_id=transformations.get_parent_id_from_model(reaction, message, "message"),
            channel_id=transformations.get_parent_id_from_model(message, channel, "channel"),
            emoji=getattr(emoji, "url_name", emoji),
            user_id=transformations.get_id(user),
        )

    async def delete_all_reactions(
        self, message: _messages.MessageLikeT, *, channel: _channels.GuildChannelLikeT = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.delete_all_reactions(
            message_id=transformations.get_id(message),
            channel_id=transformations.get_parent_id_from_model(message, channel, "channel"),
        )

    async def update_message(
        self,
        message: _messages.MessageLikeT,
        *,
        channel: _channels.ChannelLikeT = unspecified.UNSPECIFIED,
        content: typing.Optional[str] = unspecified.UNSPECIFIED,
        embed: typing.Optional[_embeds.Embed] = unspecified.UNSPECIFIED,
        flags: _messages.MessageFlagLikeT = unspecified.UNSPECIFIED,
    ) -> _messages.Message:
        message_payload = await self.fabric.http_api.edit_message(
            message_id=transformations.get_id(message),
            channel_id=transformations.get_parent_id_from_model(message, channel, "channel"),
            content=content,
            embed=transformations.cast_if_specified(embed, lambda obj: obj.to_dict(), nullable=True),
            flags=transformations.cast_if_specified(flags, int),
        )
        return self.fabric.state_registry.parse_message(message_payload)

    async def delete_messages(
        self,
        first_message: _messages.MessageLikeT,
        *additional_messages: _messages.MessageLikeT,
        channel: _channels.ChannelLikeT = unspecified.UNSPECIFIED,
    ) -> None:
        channel_id = transformations.get_parent_id_from_model(first_message, channel, "channel")
        if additional_messages:
            message_ids = [transformations.get_id(message) for message in (first_message, *additional_messages)]
            assertions.assert_that(
                len(message_ids) <= 100, "Only 100 messages can be bulk deleted in a single request."
            )
            await self.fabric.http_api.bulk_delete_messages(channel_id=channel_id, messages=message_ids)
        else:
            await self.fabric.http_api.delete_message(
                channel_id=channel_id, message_id=transformations.get_id(first_message)
            )

    async def update_channel_overwrite(
        self,
        channel: _channels.GuildChannelLikeT,
        overwrite: _overwrites.OverwriteLikeT,
        *,
        allow: int = unspecified.UNSPECIFIED,
        deny: int = unspecified.UNSPECIFIED,
        overwrite_type: _overwrites.OverwriteEntityTypeLikeT = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.edit_channel_permissions(
            channel_id=transformations.get_id(channel),
            overwrite_id=transformations.get_id(overwrite),
            allow=allow,
            deny=deny,
            type_=transformations.cast_if_specified(overwrite_type, str),
            reason=reason,
        )

    async def fetch_invites_for_channel(self, channel: _channels.GuildChannelLikeT) -> typing.Sequence[_invites.Invite]:
        invites_payload = await self.fabric.http_api.get_channel_invites(channel_id=transformations.get_id(channel))
        return [self.fabric.state_registry.parse_invite(invite) for invite in invites_payload]

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
        invite_payload = await self.fabric.http_api.create_channel_invite(
            channel_id=transformations.get_id(channel),
            max_age=max_age,
            max_uses=max_uses,
            temporary=temporary,
            unique=unique,
            reason=reason,
        )
        return self.fabric.state_registry.parse_invite(invite_payload)

    async def delete_channel_overwrite(
        self, channel: _channels.GuildChannelLikeT, overwrite: _overwrites.OverwriteLikeT
    ) -> None:
        await self.fabric.http_api.delete_channel_permission(
            channel_id=transformations.get_id(channel), overwrite_id=transformations.get_id(overwrite)
        )

    async def trigger_typing(self, channel: _channels.TextChannelLikeT) -> _channels.TypingIndicator:
        raise NotImplementedError

    async def fetch_pins(
        self, channel: _channels.TextChannelLikeT, *, in_order: bool = False
    ) -> typing.AsyncIterator[_messages.Message]:
        raise NotImplementedError

    async def pin_message(
        self, message: _messages.MessageLikeT, *, channel: _channels.TextChannelLikeT = unspecified.UNSPECIFIED
    ) -> None:
        await self.fabric.http_api.add_pinned_channel_message(
            message_id=transformations.get_id(message),
            channel_id=transformations.get_parent_id_from_model(message, channel, "channel"),
        )

    async def unpin_message(
        self, message: _messages.MessageLikeT, *, channel: _channels.TextChannelLikeT = unspecified.UNSPECIFIED
    ) -> None:
        await self.fabric.http_api.delete_pinned_channel_message(
            message_id=transformations.get_id(message),
            channel_id=transformations.get_parent_id_from_model(message, channel, "channel"),
        )

    async def fetch_guild_emoji(
        self, emoji: _emojis.GuildEmojiLikeT, *, guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED
    ) -> _emojis.GuildEmoji:
        guild_id = transformations.get_parent_id_from_model(emoji, guild, "guild")
        emoji_payload = await self.fabric.http_api.get_guild_emoji(
            emoji_id=transformations.get_id(emoji), guild_id=guild_id
        )
        guild_obj = self.fabric.state_registry.get_mandatory_guild_by_id(int(guild_id))
        return self.fabric.state_registry.parse_emoji(emoji_payload, guild_obj)

    async def fetch_guild_emojis(self, guild: _guilds.GuildLikeT) -> typing.Collection[_emojis.GuildEmoji]:
        guild_id = transformations.get_id(guild)
        emojis_payload = await self.fabric.http_api.list_guild_emojis(guild_id=guild_id)
        guild_obj = self.fabric.state_registry.get_mandatory_guild_by_id(int(guild_id))
        return [self.fabric.state_registry.parse_emoji(emoji, guild_obj) for emoji in emojis_payload]

    async def create_guild_emoji(
        self,
        guild: _guilds.GuildLikeT,
        name: str,
        image_data: storage.FileLikeT,
        *,
        roles: typing.Collection[_roles.RoleLikeT] = containers.EMPTY_COLLECTION,
        reason: str = unspecified.UNSPECIFIED,
    ) -> _emojis.GuildEmoji:
        guild_id = transformations.get_id(guild)
        emoji_payload = await self.fabric.http_api.create_guild_emoji(
            guild_id=guild_id,
            name=name,
            image=storage.get_bytes_from_resource(image_data),
            roles=[transformations.get_id(role) for role in roles],
            reason=reason,
        )
        guild_obj = self.fabric.state_registry.get_mandatory_guild_by_id(int(guild_id))
        return self.fabric.state_registry.parse_emoji(emoji_payload, guild_obj)

    async def update_guild_emoji(
        self,
        emoji: _emojis.GuildEmojiLikeT,
        *,
        guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
        name: str = unspecified.UNSPECIFIED,
        roles: typing.Collection[_roles.RoleLikeT] = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.modify_guild_emoji(
            emoji_id=transformations.get_id(emoji),
            guild_id=transformations.get_parent_id_from_model(emoji, guild, "guild"),
            name=name,
            roles=transformations.cast_if_specified(roles, transformations.get_id, iterable=True),
            reason=reason,
        )

    async def delete_guild_emoji(
        self, emoji: _emojis.GuildEmojiLikeT, *, guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED
    ) -> None:
        await self.fabric.http_api.delete_guild_emoji(
            emoji_id=transformations.get_id(emoji),
            guild_id=transformations.get_parent_id_from_model(emoji, guild, "guild"),
        )

    async def create_guild(self) -> None:
        #: TODO: refine what this needs to have in it.
        raise NotImplementedError

    async def fetch_guild(self, guild: _guilds.GuildLikeT) -> _guilds.Guild:
        guild_payload = await self.fabric.http_api.get_guild(guild_id=transformations.get_id(guild))
        return self.fabric.state_registry.parse_guild(guild_payload, None)

    async def update_guild(
        self,
        guild: _guilds.GuildLikeT,
        *,
        name: str = unspecified.UNSPECIFIED,
        region: str = unspecified.UNSPECIFIED,
        verification_level: _guilds.VerificationLevelLikeT = unspecified.UNSPECIFIED,
        default_message_notifications: _guilds.DefaultMessageNotificationsLevelLikeT = unspecified.UNSPECIFIED,
        explicit_content_filter: _guilds.ExplicitContentFilterLevelLikeT = unspecified.UNSPECIFIED,
        afk_channel: _channels.GuildVoiceChannelLikeT = unspecified.UNSPECIFIED,
        afk_timeout: int = unspecified.UNSPECIFIED,
        icon_data: storage.FileLikeT = unspecified.UNSPECIFIED,
        owner: _members.MemberLikeT = unspecified.UNSPECIFIED,
        splash_data: storage.FileLikeT = unspecified.UNSPECIFIED,
        system_channel: _channels.GuildTextChannelLikeT = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.modify_guild(
            guild_id=transformations.get_id(guild),
            name=name,
            region=region,
            verification_level=transformations.cast_if_specified(verification_level, int),
            default_message_notifications=transformations.cast_if_specified(default_message_notifications, int),
            explicit_content_filter=transformations.cast_if_specified(explicit_content_filter, int),
            afk_channel_id=transformations.cast_if_specified(afk_channel, transformations.get_id),
            afk_timeout=afk_timeout,
            icon=transformations.cast_if_specified(icon_data, storage.get_bytes_from_resource),
            owner_id=transformations.cast_if_specified(owner, transformations.get_id),
            splash=transformations.cast_if_specified(splash_data, storage.get_bytes_from_resource),
            system_channel_id=transformations.cast_if_specified(system_channel, transformations.get_id),
            reason=reason,
        )

    async def delete_guild(self, guild: _guilds.GuildLikeT) -> None:
        await self.fabric.http_api.delete_guild(guild_id=transformations.get_id(guild))

    async def fetch_guild_channels(self, guild: _guilds.GuildLikeT) -> typing.Sequence[_channels.GuildChannel]:
        guild_id = transformations.get_id(guild)
        guild_channels_payload = await self.fabric.http_api.get_guild_channels(guild_id=guild_id)
        guild_obj = self.fabric.state_registry.get_mandatory_guild_by_id(int(guild_id))
        return [self.fabric.state_registry.parse_channel(channel, guild_obj) for channel in guild_channels_payload]

    async def create_guild_channel(  # lgtm [py/similar-function]
        self,
        guild: _guilds.GuildLikeT,
        name: str,
        channel_type: _channels.ChannelTypeLikeT,
        *,
        topic: str = unspecified.UNSPECIFIED,
        bitrate: int = unspecified.UNSPECIFIED,
        user_limit: int = unspecified.UNSPECIFIED,
        rate_limit_per_user: int = unspecified.UNSPECIFIED,
        position: int = unspecified.UNSPECIFIED,
        permission_overwrites: typing.Collection[_overwrites.Overwrite] = unspecified.UNSPECIFIED,
        parent_category: _channels.GuildCategoryLikeT = unspecified.UNSPECIFIED,
        nsfw: bool = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> _channels.GuildChannel:
        guild_id = transformations.get_id(guild)
        channel_payload = await self.fabric.http_api.create_guild_channel(
            guild_id=guild_id,
            name=name,
            type_=transformations.cast_if_specified(channel_type, int),
            topic=topic,
            bitrate=bitrate,
            user_limit=user_limit,
            rate_limit_per_user=rate_limit_per_user,
            position=position,
            permission_overwrites=transformations.cast_if_specified(
                permission_overwrites, lambda obj: obj.to_dict(), iterable=True
            ),
            parent_id=transformations.cast_if_specified(parent_category, transformations.get_id),
            nsfw=nsfw,
            reason=reason,
        )
        guild_obj = self.fabric.state_registry.get_mandatory_guild_by_id(int(guild_id))
        return self.fabric.state_registry.parse_channel(channel_payload, guild_obj)

    async def reposition_guild_channels(
        self,
        first_channel: typing.Tuple[int, _channels.GuildChannelLikeT],
        *additional_channels: typing.Tuple[int, _channels.GuildChannelLikeT],
        guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.modify_guild_channel_positions(
            transformations.get_parent_id_from_model(first_channel[1], guild, "guild"),
            *((transformations.get_id(channel[1]), channel[0]) for channel in (first_channel, *additional_channels)),
        )

    async def fetch_member(
        self,
        user: typing.Union[_users.BaseUserLikeT, _members.MemberLikeT],
        *,
        guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
    ) -> _members.Member:
        guild_id = transformations.get_parent_id_from_model(user, guild, "guild")
        member_payload = await self.fabric.http_api.get_guild_member(
            guild_id=guild_id, user_id=transformations.get_id(user)
        )
        guild_obj = self.fabric.state_registry.get_mandatory_guild_by_id(int(guild_id))
        return self.fabric.state_registry.parse_member(member_payload, guild_obj)

    async def fetch_members(
        self, guild: _guilds.GuildLikeT, *, limit: int = unspecified.UNSPECIFIED
    ) -> typing.AsyncIterator[_members.Member]:
        raise NotImplementedError

    async def update_member(
        self,
        member: _members.MemberLikeT,
        *,
        guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
        nick: typing.Optional[str] = unspecified.UNSPECIFIED,
        roles: typing.Collection[_roles.RoleLikeT] = unspecified.UNSPECIFIED,
        mute: bool = unspecified.UNSPECIFIED,
        deaf: bool = unspecified.UNSPECIFIED,
        current_voice_channel: typing.Optional[_channels.GuildVoiceChannelLikeT] = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.modify_guild_member(
            user_id=transformations.get_id(member),
            guild_id=transformations.get_parent_id_from_model(member, guild, "guild"),
            nick=nick,
            roles=transformations.cast_if_specified(roles, transformations.get_id, iterable=True),
            mute=mute,
            deaf=deaf,
            channel_id=transformations.cast_if_specified(current_voice_channel, transformations.get_id, nullable=True),
            reason=reason,
        )

    async def update_my_nickname(
        self, nick: typing.Optional[str], guild: _guilds.GuildLikeT, *, reason: str = unspecified.UNSPECIFIED
    ) -> None:
        await self.fabric.http_api.modify_current_user_nick(
            guild_id=transformations.get_id(guild), nick=nick, reason=reason,
        )

    async def add_role_to_member(
        self,
        role: _roles.RoleLikeT,
        member: _members.MemberLikeT,
        *,
        guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.add_guild_member_role(
            user_id=transformations.get_id(member),
            role_id=transformations.get_id(role),
            guild_id=transformations.get_parent_id_from_model(member, guild, "guild"),
            reason=reason,
        )

    async def remove_role_from_member(
        self,
        role: _roles.RoleLikeT,
        member: _members.MemberLikeT,
        *,
        guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.remove_guild_member_role(
            user_id=transformations.get_id(member),
            role_id=transformations.get_id(role),
            guild_id=transformations.get_parent_id_from_model(member, guild, "guild"),
            reason=reason,
        )

    async def kick_member(
        self,
        member: _members.MemberLikeT,
        *,
        guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.remove_guild_member(
            user_id=transformations.get_id(member),
            guild_id=transformations.get_parent_id_from_model(member, guild, "guild"),
            reason=reason,
        )

    async def fetch_ban(self, guild: _guilds.GuildLikeT, user: _users.BaseUserLikeT) -> _guilds.Ban:
        ban_payload = await self.fabric.http_api.get_guild_ban(
            guild_id=transformations.get_id(guild), user_id=transformations.get_id(user)
        )
        return self.fabric.state_registry.parse_ban(ban_payload)

    async def fetch_bans(self, guild: _guilds.GuildLikeT) -> typing.Collection[_guilds.Ban]:
        bans_payload = await self.fabric.http_api.get_guild_bans(guild_id=transformations.get_id(guild))
        return [self.fabric.state_registry.parse_ban(ban) for ban in bans_payload]

    async def ban_member(
        self,
        member: _members.MemberLikeT,
        *,
        guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
        delete_message_days: int = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.create_guild_ban(
            user_id=transformations.get_id(member),
            guild_id=transformations.get_parent_id_from_model(member, guild, "guild"),
            delete_message_days=delete_message_days,
            reason=reason,
        )

    async def unban_member(
        self, user: _users.BaseUserLikeT, guild: _guilds.GuildLikeT, *, reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.remove_guild_ban(
            user_id=transformations.get_id(user), guild_id=transformations.get_id(guild), reason=reason,
        )

    async def fetch_roles(self, guild: _guilds.GuildLikeT) -> typing.Sequence[_roles.Role]:
        guild_id = transformations.get_id(guild)
        roles_payload = await self.fabric.http_api.get_guild_roles(guild_id=guild_id)
        guild_obj = self.fabric.state_registry.get_mandatory_guild_by_id(int(guild_id))
        return [self.fabric.state_registry.parse_role(role, guild_obj) for role in roles_payload]

    async def create_role(  # lgtm [py/similar-function]
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
        guild_id = transformations.get_id(guild)
        role_payload = await self.fabric.http_api.create_guild_role(
            guild_id=guild_id,
            name=name,
            permissions=transformations.cast_if_specified(permissions, int),
            color=transformations.cast_if_specified(color, int),
            hoist=hoist,
            mentionable=mentionable,
            reason=reason,
        )
        guild_obj = self.fabric.state_registry.get_mandatory_guild_by_id(int(guild_id))
        return self.fabric.state_registry.parse_role(role_payload, guild_obj)

    async def reposition_roles(
        self,
        first_role: typing.Tuple[int, _roles.RoleLikeT],
        *additional_roles: typing.Tuple[int, _roles.RoleLikeT],
        guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.modify_guild_role_positions(
            transformations.get_parent_id_from_model(first_role[1], guild, "guild"),
            *((transformations.get_id(role[1]), role[0]) for role in (first_role, *additional_roles)),
        )

    async def update_role(
        self,
        role: _roles.PartialRoleLikeT,
        *,
        guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
        name: str = unspecified.UNSPECIFIED,
        permissions: _permissions.PermissionLikeT = unspecified.UNSPECIFIED,
        color: _colors.ColorCompatibleT = unspecified.UNSPECIFIED,
        hoist: bool = unspecified.UNSPECIFIED,
        mentionable: bool = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.modify_guild_role(
            guild_id=transformations.get_parent_id_from_model(role, guild, "guild"),
            role_id=transformations.get_id(role),
            name=name,
            permissions=transformations.cast_if_specified(permissions, int),
            color=transformations.cast_if_specified(color, int),
            hoist=hoist,
            mentionable=mentionable,
            reason=reason,
        )

    async def delete_role(self, role: _roles.RoleLikeT, *, guild: _guilds.GuildLikeT = unspecified.UNSPECIFIED) -> None:
        await self.fabric.http_api.delete_guild_role(
            guild_id=transformations.get_parent_id_from_model(role, guild, "guild"),
            role_id=transformations.get_id(role),
        )

    async def estimate_guild_prune_count(self, guild: _guilds.GuildLikeT, days: int) -> int:
        return await self.fabric.http_api.get_guild_prune_count(guild_id=transformations.get_id(guild), days=days)

    async def begin_guild_prune(
        self,
        guild: _guilds.GuildLikeT,
        days: int,
        *,
        compute_prune_count: bool = False,
        reason: str = unspecified.UNSPECIFIED,
    ) -> typing.Optional[int]:
        return await self.fabric.http_api.begin_guild_prune(
            guild_id=transformations.get_id(guild), days=days, compute_prune_count=compute_prune_count, reason=reason,
        )

    async def fetch_guild_voice_regions(self, guild: _guilds.GuildLikeT) -> typing.Collection[_voices.VoiceRegion]:
        voice_regions_payload = await self.fabric.http_api.get_guild_voice_regions(
            guild_id=transformations.get_id(guild)
        )
        return [_voices.VoiceRegion(voice_region) for voice_region in voice_regions_payload]

    async def fetch_guild_invites(self, guild: _guilds.GuildLikeT) -> typing.Collection[_invites.Invite]:
        invites_payload = await self.fabric.http_api.get_guild_invites(guild_id=transformations.get_id(guild))
        return [self.fabric.state_registry.parse_invite(invite) for invite in invites_payload]

    async def fetch_integrations(self, guild: _guilds.GuildLikeT) -> typing.Collection[_integrations.Integration]:
        integrations_payload = await self.fabric.http_api.get_guild_integrations(guild_id=transformations.get_id(guild))
        return [self.fabric.state_registry.parse_integration(integration) for integration in integrations_payload]

    async def create_guild_integration(
        self,
        guild: _guilds.GuildLikeT,
        integration_type: str,
        integration_id: bases.RawSnowflakeT,
        *,
        reason: str = unspecified.UNSPECIFIED,
    ) -> _integrations.Integration:
        integration_payload = await self.fabric.http_api.create_guild_integration(
            guild_id=transformations.get_id(guild),
            type_=integration_type,
            integration_id=integration_id,
            reason=reason,
        )
        return self.fabric.state_registry.parse_integration(integration_payload)

    async def update_integration(
        self,
        guild: _guilds.GuildLikeT,
        integration: _integrations.IntegrationLikeT,
        *,
        expire_behaviour: int = unspecified.UNSPECIFIED,
        expire_grace_period: int = unspecified.UNSPECIFIED,
        enable_emojis: bool = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        await self.fabric.http_api.modify_guild_integration(
            guild_id=transformations.get_id(guild),
            integration_id=transformations.get_id(integration),
            expire_behaviour=expire_behaviour,
            expire_grace_period=expire_grace_period,
            enable_emojis=enable_emojis,
            reason=reason,
        )

    async def delete_integration(self, guild: _guilds.GuildLikeT, integration: _integrations.IntegrationLikeT) -> None:
        await self.fabric.http_api.delete_guild_integration(
            guild_id=transformations.get_id(guild), integration_id=transformations.get_id(integration)
        )

    async def sync_guild_integration(
        self, guild: _guilds.GuildLikeT, integration: _integrations.IntegrationLikeT
    ) -> None:
        await self.fabric.http_api.sync_guild_integration(
            guild_id=transformations.get_id(guild), integration_id=transformations.get_id(integration)
        )

    async def fetch_guild_embed(self, guild: _guilds.Guild) -> _guilds.GuildEmbed:
        embed_payload = await self.fabric.http_api.get_guild_embed(guild_id=transformations.get_id(guild))
        return _guilds.GuildEmbed.from_dict(embed_payload)

    async def modify_guild_embed(
        self, guild: _guilds.GuildLikeT, embed: _guilds.GuildEmbed, *, reason: str = unspecified.UNSPECIFIED
    ) -> None:
        await self.fabric.http_api.modify_guild_embed(
            guild_id=transformations.get_id(guild), embed=embed.to_dict(), reason=reason
        )

    async def fetch_guild_vanity_url(self, guild: _guilds.GuildLikeT) -> str:
        raise NotImplementedError  # TODO: implement partial or vanity invite object.

    def fetch_guild_widget_image(
        self, guild: _guilds.GuildLikeT, *, style: _guilds.WidgetStyleLikeT = unspecified.UNSPECIFIED
    ) -> str:
        return self.fabric.http_api.get_guild_widget_image(
            guild_id=transformations.get_id(guild), style=transformations.cast_if_specified(style, str)
        )

    async def fetch_invite(
        self, invite: _invites.InviteLikeT, *, with_counts: bool = unspecified.UNSPECIFIED
    ) -> _invites.Invite:
        invite_payload = await self.fabric.http_api.get_invite(invite_code=str(invite), with_counts=with_counts)
        return self.fabric.state_registry.parse_invite(invite_payload)

    async def delete_invite(self, invite: _invites.InviteLikeT) -> None:
        await self.fabric.http_api.delete_invite(invite_code=str(invite))

    async def fetch_user(self, user: _users.BaseUserLikeT) -> typing.Union[_users.User, _users.OAuth2User]:
        user_payload = await self.fabric.http_api.get_user(user_id=transformations.get_id(user))
        return self.fabric.state_registry.parse_user(user_payload)

    async def fetch_application_info(self) -> _applications.Application:
        application_info_payload = await self.fabric.http_api.get_current_application_info()
        return self.fabric.state_registry.parse_application(application_info_payload)

    async def fetch_me(self) -> _users.OAuth2User:
        user_payload = await self.fabric.http_api.get_current_user()
        return self.fabric.state_registry.parse_application_user(user_payload)

    async def update_me(
        self, *, username: str = unspecified.UNSPECIFIED, avatar_data: storage.FileLikeT = unspecified.UNSPECIFIED
    ) -> None:
        user_payload = await self.fabric.http_api.modify_current_user(
            username=username, avatar=transformations.cast_if_specified(avatar_data, storage.get_bytes_from_resource)
        )
        self.fabric.state_registry.parse_user(user_payload)

    async def fetch_my_connections(self) -> typing.Sequence[_connections.Connection]:
        connections_payload = await self.fabric.http_api.get_current_user_connections()
        return [self.fabric.state_registry.parse_connection(connection) for connection in connections_payload]

    async def fetch_my_guilds(
        self,
        before: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
        after: _guilds.GuildLikeT = unspecified.UNSPECIFIED,
        limit: int = unspecified.UNSPECIFIED,
    ) -> typing.AsyncIterator[_guilds.Guild]:
        raise NotImplementedError

    async def leave_guild(self, guild: _guilds.GuildLikeT) -> None:
        await self.fabric.http_api.leave_guild(guild_id=transformations.get_id(guild))

    async def create_dm_channel(self, recipient: _users.BaseUserLikeT) -> _channels.DMChannel:
        dm_channel_payload = await self.fabric.http_api.create_dm(recipient_id=transformations.get_id(recipient))
        return self.fabric.state_registry.parse_channel(dm_channel_payload)

    async def fetch_voice_regions(self) -> typing.Collection[_voices.VoiceRegion]:
        voice_regions_payload = await self.fabric.http_api.list_voice_regions()
        return tuple(_voices.VoiceRegion(voice_region) for voice_region in voice_regions_payload)

    async def create_webhook(
        self,
        channel: _channels.GuildTextChannelLikeT,
        name: str,
        *,
        avatar_data: storage.FileLikeT = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> _webhooks.Webhook:
        webhook_payload = await self.fabric.http_api.create_webhook(
            channel_id=transformations.get_id(channel),
            name=name,
            avatar=transformations.cast_if_specified(avatar_data, storage.get_bytes_from_resource),
            reason=reason,
        )
        return self.fabric.state_registry.parse_webhook(webhook_payload)

    async def fetch_channel_webhooks(
        self, channel: _channels.GuildTextChannelLikeT
    ) -> typing.Collection[_webhooks.Webhook]:
        webhooks_payload = await self.fabric.http_api.get_channel_webhooks(channel_id=transformations.get_id(channel))
        return tuple(self.fabric.state_registry.parse_webhook(webhook) for webhook in webhooks_payload)

    async def fetch_guild_webhooks(self, guild: _guilds.GuildLikeT) -> typing.Collection[_webhooks.Webhook]:
        webhooks_payload = await self.fabric.http_api.get_guild_webhooks(guild_id=transformations.get_id(guild))
        return tuple(self.fabric.state_registry.parse_webhook(webhook) for webhook in webhooks_payload)

    async def fetch_webhook(self, webhook: _webhooks.WebhookLikeT) -> _webhooks.Webhook:
        webhook_payload = await self.fabric.http_api.get_webhook(webhook_id=transformations.get_id(webhook))
        return self.fabric.state_registry.parse_webhook(webhook_payload)

    async def update_webhook(
        self,
        webhook: _webhooks.WebhookLikeT,
        *,
        name: str = unspecified.UNSPECIFIED,
        avatar_data: storage.FileLikeT = unspecified.UNSPECIFIED,
        channel: _channels.GuildTextChannelLikeT = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> _webhooks.Webhook:
        webhook_payload = await self.fabric.http_api.modify_webhook(
            webhook_id=transformations.get_id(webhook),
            name=name,
            avatar=transformations.cast_if_specified(avatar_data, storage.get_bytes_from_resource),
            channel_id=transformations.cast_if_specified(channel, transformations.get_id),
            reason=reason,
        )
        return self.fabric.state_registry.parse_webhook(webhook_payload)

    async def delete_webhook(self, webhook: _webhooks.WebhookLikeT) -> None:
        await self.fabric.http_api.delete_webhook(webhook_id=transformations.get_id(webhook))
