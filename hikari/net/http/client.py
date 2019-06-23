#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the HTTP Client mix of all mixin components.
"""
__all__ = ("HTTPClient",)

import io
import json

import aiohttp

from hikari import _utils
from hikari.compat import typing
from . import base


class HTTPClient(base.BaseHTTPClient):
    """
    Combination of all components for API handling logic for the V7 Discord HTTP API.
    """

    __slots__ = []

    ##############
    # AUDIT LOGS #
    ##############

    @_utils.link_developer_portal(_utils.APIResource.AUDIT_LOG)
    async def get_guild_audit_log(
        self,
        guild_id: str,
        *,
        user_id: str = _utils.unspecified,
        action_type: int = _utils.unspecified,
        limit: int = _utils.unspecified,
    ) -> _utils.DiscordObject:
        """
        Get an audit log object for the given guild.

        Args:
            guild_id:
                The guild ID to look up.
            user_id:
                Optional user ID to filter by.
            action_type:
                Optional action type to look up.
            limit:
                Optional limit to apply to the number of records. Defaults to 50. Must be between 1 and 100 inclusive.

        Returns:
            An audit log object.

        Raises:
            :class:`hikari.errors.Forbidden`:
                if you lack the given permissions to view an audit log.
            :class:`hikari.errors.NotFound`:
                if the guild does not exist.
        """
        query = {}
        _utils.put_if_specified(query, "user_id", user_id)
        _utils.put_if_specified(query, "action_type", action_type)
        _utils.put_if_specified(query, "limit", limit)
        return await self.request("get", "/guilds/{guild_id}/audit-logs", query=query, guild_id=guild_id)

    ############
    # CHANNELS #
    ############

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def get_channel(self, channel_id: str) -> _utils.DiscordObject:
        """
        Get a channel object from a given channel ID.

        Args:
            channel_id:
                the channel ID to look up.

        Returns:
            The channel object that has been found.

        Raises:
            hikari.errors.NotFound:
                if the channel does not exist.
        """
        return await self.request("get", "/channels/{channel_id}", channel_id=channel_id)

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def modify_channel(
        self,
        channel_id: str,
        *,
        position: int = _utils.unspecified,
        topic: str = _utils.unspecified,
        nsfw: bool = _utils.unspecified,
        rate_limit_per_user: int = _utils.unspecified,
        bitrate: int = _utils.unspecified,
        user_limit: int = _utils.unspecified,
        permission_overwrites: typing.List[_utils.DiscordObject] = _utils.unspecified,
        parent_id: str = _utils.unspecified,
    ) -> _utils.DiscordObject:
        """
        Update one or more aspects of a given channel ID.

        Args:
            channel_id:
                The channel ID to update. This must be between 2 and 100 characters in length.
            position:
                An optional position to change to.
            topic:
                An optional topic to set. This is only applicable to text channels. This must be between 0 and 1024
                characters in length.
            nsfw:
                An optional flag to set the channel as NSFW or not. Only applicable to text channels.
            rate_limit_per_user:
                An optional number of seconds the user has to wait before sending another message. This will
                not apply to bots, or to members with `manage_messages` or `manage_channel` permissions. This must be
                between 0 and 21600 seconds. This only applies to text channels.
            bitrate:
                the optional bitrate in bits per second allowable for the channel. This only applies to voice channels
                and must be between 8000 and 96000 or 128000 for VIP servers.
            user_limit:
                the optional max number of users to allow in a voice channel. This must be between 0 and 99 inclusive,
                where 0 implies no limit.
            permission_overwrites:
                an optional list of permission overwrites that are category specific to replace the existing overwrites
                with.
            parent_id:
                The optional parent category ID to set for the channel.

        Raises:
            hikari.errors.NotFound:
                if the channel does not exist.
            hikari.errors.Forbidden:
                if you lack the permission to make the change.
            hikari.errors.BadRequest:
                if you provide incorrect options for the corresponding channel type (e.g. a `bitrate` for a text
                channel).
        """

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL, "deleteclose-channel")
    async def delete_close_channel(self, channel_id: str) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def get_channel_messages(
        self,
        channel_id: str,
        *,
        limit: int = _utils.unspecified,
        after: str = _utils.unspecified,
        before: str = _utils.unspecified,
        around: str = _utils.unspecified,
    ) -> typing.List[_utils.DiscordObject]:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def get_channel_message(self, channel_id: str, message_id: str) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def create_message(
        self,
        channel_id: str,
        *,
        content: str = _utils.unspecified,
        nonce: str = _utils.unspecified,
        tts: bool = False,
        files: typing.List[typing.Tuple[str, _utils.FileLike]] = _utils.unspecified,
        embed: _utils.DiscordObject = _utils.unspecified,
    ) -> _utils.DiscordObject:
        """
        Create a message in the given channel or DM.

        Args:
            channel_id:
                The channel or user ID to send to.
            content:
                The message content to send.
            nonce:
                an optional ID to send for opportunistic message creation. This doesn't serve any real purpose for
                general use, and can usually be ignored.
            tts:
                if specified and `True`, then the message will be sent.
            files:
                if specified, this should be a list of between 1 and 5 tuples. Each tuple should consist of the
                file name, and either raw :class:`bytes` or an :class:`io.IOBase` derived object with a seek that
                points to a buffer containing said file.
            embed:
                if specified, this embed will be sent with the message.

        Raises:
            hikari.errors.NotFound:
                if the channel ID is not found.
            hikari.errors.BadRequest:
                if the file is too large, the embed exceeds the defined limits, if the message content is specified and
                empty or greater than 2000 characters, or if neither of content, file or embed are specified.
            hikari.errors.Forbidden:
                if you lack permissions to send to this channel.

        Returns:
            The created message object.
        """
        form = aiohttp.FormData()

        json_payload = {"tts": tts}
        _utils.put_if_specified(json_payload, "content", content)
        _utils.put_if_specified(json_payload, "nonce", nonce)
        _utils.put_if_specified(json_payload, "embed", embed)

        form.add_field("payload_json", json.dumps(json_payload), content_type="application/json")

        re_seekable_resources = []
        if files is not _utils.unspecified:
            for i, (file_name, file) in enumerate(files):
                if isinstance(file, (bytes, bytearray)):
                    file = io.BytesIO(file)
                elif isinstance(file, memoryview):
                    file = io.BytesIO(file.tobytes())
                elif isinstance(file, str):
                    file = io.StringIO(file)

                re_seekable_resources.append(file)
                form.add_field(f"file{i}", file, filename=file_name, content_type="application/octet-stream")

        return await self.request(
            "post",
            "/channels/{channel_id}/messages",
            channel_id=channel_id,
            re_seekable_resources=re_seekable_resources,
            data=form,
        )

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def create_reaction(self, channel_id: str, message_id: str, emoji: typing.Union[str, str]) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def delete_own_reaction(self, channel_id: str, message_id: str, emoji: typing.Union[str, str]) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def delete_user_reaction(
        self, channel_id: str, message_id: str, emoji: typing.Union[str, str], user_id: str
    ) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def get_reactions(
        self, channel_id: str, message_id: str, emoji: typing.Union[str, str]
    ) -> typing.List[_utils.DiscordObject]:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL, "/resources/channel#delete-all-reactions")
    async def delete_all_reactions(self, channel_id: str, message_id: str) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def edit_message(self, channel_id: str, message_id: str) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def delete_message(self, channel_id: str, message_id: str) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def bulk_delete_messages(self, channel_id: str, messages: typing.List[str]) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def edit_channel_permissions(
        self, channel_id: str, overwrite_id: str, allow: int, deny: int, type: str
    ) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def get_channel_invites(self, channel_id: str) -> typing.List[_utils.DiscordObject]:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def create_channel_invite(
        self,
        channel_id: str,
        *,
        max_age: int = _utils.unspecified,
        max_uses: int = _utils.unspecified,
        temporary: bool = _utils.unspecified,
        unique: bool = _utils.unspecified,
    ) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def delete_channel_permission(self, channel_id: str, overwrite_id: str) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def trigger_typing_indicator(self, channel_id: str) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def get_pinned_messages(self, channel_id: str) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def add_pinned_channel_message(self, channel_id: str, message_id: str) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def delete_pinned_channel_message(self, channel_id: str, message_id: str) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    ##########
    # EMOJIS #
    ##########

    @_utils.link_developer_portal(_utils.APIResource.EMOJI)
    async def list_guild_emojis(self, guild_id: str) -> typing.List[_utils.DiscordObject]:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.EMOJI)
    async def get_guild_emoji(self, guild_id: str, emoji_id: str) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.EMOJI)
    async def create_guild_emoji(
        self, guild_id: str, name: str, image: bytes, roles: typing.List[str]
    ) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.EMOJI)
    async def modify_guild_emoji(
        self, guild_id: str, emoji_id: str, name: str, roles: typing.List[str]
    ) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.EMOJI)
    async def delete_guild_emoji(self, guild_id: str, emoji_id: str) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    ##########
    # GUILDS #
    ##########

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def create_guild(
        self,
        name: str,
        region: str,
        icon: bytes,
        verification_level: int,
        default_message_notifications: int,
        explicit_content_filter: int,
        roles: typing.List[_utils.DiscordObject],
        channels: typing.List[_utils.DiscordObject],
    ) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def get_guild(self, guild_id: str) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def modify_guild(
        self,
        guild_id: str,
        *,
        name: str = _utils.unspecified,
        region: str = _utils.unspecified,
        verification_level: str = _utils.unspecified,
        default_message_notifications: str = _utils.unspecified,
        explicit_content_filter: int = _utils.unspecified,
        afk_channel_id: str = _utils.unspecified,
        icon: bytes = _utils.unspecified,
        owner_id: str = _utils.unspecified,
        splash: bytes = _utils.unspecified,
        system_channel_id: str = _utils.unspecified,
    ) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def delete_guild(self, guild_id: str) -> None:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def get_guild_channels(self, guild_id: str) -> typing.List[_utils.DiscordObject]:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def create_guild_channel(
        self,
        guild_id: str,
        name: str,
        *,
        type: int = _utils.unspecified,
        topic: str = _utils.unspecified,
        bitrate: int = _utils.unspecified,
        user_limit: int = _utils.unspecified,
        rate_limit_per_user: int = _utils.unspecified,
        position: int = _utils.unspecified,
        permission_overwrites: typing.List[_utils.DiscordObject] = _utils.unspecified,
        parent_id: str = _utils.unspecified,
        nsfw: bool = _utils.unspecified,
    ) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def modify_guild_channel_positions(
        self, guild_id: str, channel: typing.Tuple[str, int], *channels: typing.Tuple[str, int]
    ) -> None:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def get_guild_member(self, guild_id: str, user_id: str) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def list_guild_members(
        self, guild_id: str, *, limit: int = _utils.unspecified, after: str = _utils.unspecified
    ) -> typing.List[_utils.DiscordObject]:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def modify_guild_member(
        self,
        guild_id: str,
        user_id: str,
        *,
        nick: typing.Optional[str] = _utils.unspecified,
        roles: typing.List[str] = _utils.unspecified,
        mute: bool = _utils.unspecified,
        deaf: bool = _utils.unspecified,
        channel_id: typing.Optional[str] = _utils.unspecified,
    ) -> None:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def modify_current_user_nick(self, guild_id: str, nick: typing.Optional[str]) -> str:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def add_guild_member_role(self, guild_id: str, user_id: str, role_id: str) -> None:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def remove_guild_member_role(self, guild_id: str, user_id: str, role_id: str) -> None:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def remove_guild_member(self, guild_id: str, user_id: str) -> None:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def get_guild_bans(self, guild_id: str) -> typing.List[_utils.DiscordObject]:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def get_guild_ban(self, guild_id: str, user_id: str) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def create_guild_ban(
        self,
        guild_id: str,
        user_id: str,
        *,
        delete_message_days: int = _utils.unspecified,
        reason: str = _utils.unspecified,
    ) -> None:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def remove_guild_ban(self, guild_id: str, user_id: str) -> None:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def get_guild_roles(self, guild_id: str) -> typing.List[_utils.DiscordObject]:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def create_guild_role(
        self,
        guild_id: str,
        *,
        name: str = _utils.unspecified,
        permissions: int = _utils.unspecified,
        color: int = _utils.unspecified,
        hoist: bool = _utils.unspecified,
        mentionable: bool = _utils.unspecified,
    ) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def delete_guild_role(self, guild_id: str, role_id: str) -> None:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def get_guild_prune_count(self, guild_id: str, days: int) -> int:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def begin_guild_prune(
        self, guild_id: str, days: int, compute_prune_count: bool = False
    ) -> typing.Optional[int]:
        # NOTE: they politely ask to not call compute_prune_count unless necessary.
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def get_guild_voice_regions(self, guild_id: str) -> typing.List[_utils.DiscordObject]:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def get_guild_invites(self, guild_id: str) -> typing.List[_utils.DiscordObject]:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def get_guild_integrations(self, guild_id: str) -> typing.List[_utils.DiscordObject]:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def create_guild_integration(self, guild_id: str, type: str, integration_id: str) -> None:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def modify_guild_integration(
        self,
        guild_id: str,
        integration_id: str,
        *,
        expire_behaviour: int = _utils.unspecified,
        expire_grace_period: int = _utils.unspecified,
        enable_emoticons: bool = _utils.unspecified,
    ) -> None:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def delete_guild_integration(self, guild_id: str, integration_id: str) -> None:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def sync_guild_integration(self, guild_id: str, integration_id: str) -> None:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def get_guild_embed(self, guild_id: str) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def modify_guild_embed(self, guild_id: str, embed: _utils.DiscordObject) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    async def get_guild_vanity_url(self, guild_id: str) -> str:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.GUILD)
    def get_guild_widget_image(self, guild_id: str, style: str) -> str:
        """
        Get the URL for a guild widget.

        Args:
            guild_id:
                The guild ID to use for the widget.
            style:
                One of "shield", "banner1", "banner2", "banner3" or "banner4".

        Returns:
            A URL to retrieve a PNG widget for your guild.

        Note:
            This does not actually make any form of request, and shouldn't be awaited.

        Warning:
            The guild must have the widget enabled in the guild settings for this to be valid.
        """
        return f"{self.base_uri}/guilds/{guild_id}/widget.png?style={style}"

    ###############
    # INVITATIONS #
    ###############

    @_utils.link_developer_portal(_utils.APIResource.INVITE)
    async def get_invite(self, invite_code: str, *, with_counts: bool = _utils.unspecified) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_utils.link_developer_portal(_utils.APIResource.INVITE)
    async def delete_invite(self, invite_code: str) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    ##########
    # OAUTH2 #
    ##########

    @_utils.link_developer_portal(_utils.APIResource.OAUTH2)
    async def get_current_application_info(self) -> _utils.DiscordObject:
        """
        Get the current application information.

        Returns:
             An application info object.
        """
        return await self.request("get", "/oauth2/applications/@me")

    #########
    # USERS #
    #########

    @_utils.link_developer_portal(_utils.APIResource.USER)
    async def get_current_user(self) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.USER)
    async def get_user(self, user_id: str) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.USER)
    async def modify_current_user(
        self, *, username: str = _utils.unspecified, avatar: bytes = _utils.unspecified
    ) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.USER)
    async def get_current_user_guilds(self) -> typing.List[_utils.DiscordObject]:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.USER)
    async def leave_guild(self, guild_id: str) -> None:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.USER)
    async def create_dm(self, recipient_id: str) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    #########
    # VOICE #
    #########

    @_utils.link_developer_portal(_utils.APIResource.VOICE)
    async def list_voice_regions(self) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    ############
    # WEBHOOKS #
    ############

    @_utils.link_developer_portal(_utils.APIResource.WEBHOOK)
    async def create_webhook(
        self, channel_id: str, name: str, *, avatar: bytes = _utils.unspecified
    ) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.WEBHOOK)
    async def get_channel_webhooks(self, channel_id: str) -> typing.List[_utils.DiscordObject]:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.WEBHOOK)
    async def get_guild_webhooks(self, guild_id: str) -> typing.List[_utils.DiscordObject]:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.WEBHOOK)
    async def get_webhook(self, webhook_id: str) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.WEBHOOK)
    async def modify_webhook(self, webhook_id: str) -> _utils.DiscordObject:
        raise NotImplementedError  # TODO: implement this

    @_utils.link_developer_portal(_utils.APIResource.WEBHOOK)
    async def delete_webhook(self, webhook_id: str) -> None:
        raise NotImplementedError  # TODO: implement this
