#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implementation of the HTTP Client mix of all mixin components.
"""
import enum
import inspect

from hikari.compat import typing
from hikari.net import utils

from . import base


class _Scope(enum.Enum):
    AUDIT_LOG = "/resources/audit-log"
    CHANNEL = "/resources/channel"
    EMOJI = "/resources/emoji"
    GUILD = "/resources/guild"
    INVITE = "/resources/invite"
    OAUTH2 = "/topics/oauth2"
    USER = "/resources/user"
    VOICE = "/resources/voice"
    WEBHOOK = "/resources/webhook"


def _rtfm(scope: _Scope, *see):
    """Injects some common documentation into the given member's docstring."""

    def decorator(obj):
        BASE_URL = "https://discordapp.com/developers/docs"
        doc = inspect.cleandoc(inspect.getdoc(obj) or "")
        name, url = scope.name.replace("_", " ").title(), BASE_URL + scope.value
        doc = f"This is part of the `{name} <{url}>`_ API.\n\n{doc}\n\nSee:\n"
        for url in see:
            doc += f"  - {BASE_URL}{url}"

        setattr(obj, "__doc__", doc)
        return obj

    return decorator


class _Unspecified:
    __str__ = lambda s: "unspecified"
    __repr__ = __str__
    

unspecified = _Unspecified()


class HTTPClient(base.BaseHTTPClient):
    """
    Combination of all components for API handling logic for the V7 Discord HTTP API.
    """

    __slots__ = []

    ##############
    # AUDIT LOGS #
    ##############

    @_rtfm(
        _Scope.AUDIT_LOG,
        "/resources/audit-log#get-guild-audit-log",
        "/resources/audit-log#audit-log-entry-object-audit-log-events",
        "/resources/audit-log#audit-log-object",
    )
    async def get_guild_audit_log(
        self,
        guild_id: utils.RawSnowflakeish,
        *,
        user_id: utils.RawSnowflakeish = unspecified,
        action: int = unspecified,
        limit: int = unspecified,
    ) -> utils.ResponseBody:
        """
        Get an audit log object for the given guild.

        Args:
            guild_id:
                The guild ID to look up.
            user_id:
                Optional user ID to filter by.
            action:
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

        if limit is not unspecified:
            query["limit"] = limit
        if user_id is not unspecified:
            query["user_id"] = user_id

        if action is not unspecified:
            query["action_type"] = action

        params = {"guild_id": guild_id}

        _, _, body = await self.request("get", "/guilds/{guild_id}/audit-logs", params=params, query=query)

        return body

    ############
    # CHANNELS #
    ############

    @_rtfm(_Scope.CHANNEL, "/resources/channel#get-channel")
    async def get_channel(self, channel_id: utils.RawSnowflakeish) -> utils.ResponseBody:
        """
        Get a channel object from a given channel ID.

        Args:
            channel_id:
                the channel ID to look up.

        Returns:
            The channel object that has been found.

        Raises:
            :class:`hikari.errors.NotFound` if the channel does not exist.
        """
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#modify-channel")
    async def modify_channel(
        self,
        channel_id: utils.RawSnowflakeish,
        *,
        position: int = unspecified,
        topic: str = unspecified,
        nsfw: bool = unspecified,
        rate_limit_per_user: int = unspecified,
        bitrate: int = unspecified,
        user_limit: int = unspecified,
        permission_overwrites: typing.List[utils.RequestBody] = unspecified,
        parent_id: utils.RawSnowflakeish = unspecified,
    ) -> utils.ResponseBody:
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
            :class:`hikari.errors.NotFound` if the channel does not exist.
            :class:`hikari.errors.Forbidden` if you lack the permission to make the change.
        """
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#deleteclose-channel")
    async def delete_close_channel(self, channel_id: utils.RawSnowflakeish) -> utils.ResponseBody:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#get-channel-messages")
    async def get_channel_messages(
        self,
        channel_id: utils.RawSnowflakeish,
        *,
        limit: int = unspecified,
        after: utils.RawSnowflakeish = unspecified,
        before: utils.RawSnowflakeish = unspecified,
        around: utils.RawSnowflakeish = unspecified,
    ) -> typing.List[utils.ResponseBody]:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#get-channel-message")
    async def get_channel_message(
        self, channel_id: utils.RawSnowflakeish, message_id: utils.RawSnowflakeish
    ) -> utils.ResponseBody:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#create-message")
    async def create_message(
        self,
        channel_id: utils.RawSnowflakeish,
        *,
        content: str = unspecified,
        nonce: utils.RawSnowflakeish = unspecified,
        tts: bool = unspecified,
        file: bytes = unspecified,
        embed: utils.RequestBody = unspecified,
    ) -> utils.ResponseBody:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#create-reaction")
    async def create_reaction(
        self,
        channel_id: utils.RawSnowflakeish,
        message_id: utils.RawSnowflakeish,
        emoji: typing.Union[utils.RawSnowflakeish, str],
    ) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#delete-own-reaction")
    async def delete_own_reaction(
        self,
        channel_id: utils.RawSnowflakeish,
        message_id: utils.RawSnowflakeish,
        emoji: typing.Union[utils.RawSnowflakeish, str],
    ) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#delete-user-reaction")
    async def delete_user_reaction(
        self,
        channel_id: utils.RawSnowflakeish,
        message_id: utils.RawSnowflakeish,
        emoji: typing.Union[utils.RawSnowflakeish, str],
        user_id: utils.RawSnowflakeish,
    ) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#get-reactions")
    async def get_reactions(
        self,
        channel_id: utils.RawSnowflakeish,
        message_id: utils.RawSnowflakeish,
        emoji: typing.Union[utils.RawSnowflakeish, str],
    ) -> typing.List[utils.ResponseBody]:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#delete-all-reactions")
    async def delete_all_reactions(self, channel_id: utils.RawSnowflakeish, message_id: utils.RawSnowflakeish) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#edit-message")
    async def edit_message(
        self, channel_id: utils.RawSnowflakeish, message_id: utils.RawSnowflakeish
    ) -> utils.ResponseBody:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#delete-message")
    async def delete_message(self, channel_id: utils.RawSnowflakeish, message_id: utils.RawSnowflakeish) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#bulk-delete-messages")
    async def bulk_delete_messages(
        self, channel_id: utils.RawSnowflakeish, messages: typing.List[utils.RawSnowflakeish]
    ) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#edit-channel-permissions")
    async def edit_channel_permissions(
        self, channel_id: utils.RawSnowflakeish, overwrite_id: utils.RawSnowflakeish, allow: int, deny: int, type: str
    ) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#get-channel-invites")
    async def get_channel_invites(self, channel_id: utils.RawSnowflakeish) -> typing.List[utils.ResponseBody]:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#create-channel-invite")
    async def create_channel_invite(
        self,
        channel_id: utils.RawSnowflakeish,
        *,
        max_age: int = unspecified,
        max_uses: int = unspecified,
        temporary: bool = unspecified,
        unique: bool = unspecified,
    ) -> utils.ResponseBody:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#delete-channel-permission")
    async def delete_channel_permission(
        self, channel_id: utils.RawSnowflakeish, overwrite_id: utils.RawSnowflakeish
    ) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#trigger-typing-indicator")
    async def trigger_typing_indicator(self, channel_id: utils.RawSnowflakeish) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#get-pinned-messages")
    async def get_pinned_messages(self, channel_id: utils.RawSnowflakeish) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#add-pinned-channel-message")
    async def add_pinned_channel_message(
        self, channel_id: utils.RawSnowflakeish, message_id: utils.RawSnowflakeish
    ) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#delete-pinned-channel-message")
    async def delete_pinned_channel_message(
        self, channel_id: utils.RawSnowflakeish, message_id: utils.RawSnowflakeish
    ) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#group-dm-add-recipient")
    async def group_dm_add_recipient(
        self, channel_id: utils.RawSnowflakeish, user_id: utils.RawSnowflakeish, access_token: str, nick: str
    ) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.CHANNEL, "/resources/channel#group-dm-remove-recipient")
    async def group_dm_remove_recipient(
        self, channel_id: utils.RawSnowflakeish, user_id: utils.RawSnowflakeish
    ) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    ##########
    # EMOJIS #
    ##########

    @_rtfm(_Scope.EMOJI, "/resources/emoji#list-guild-emojis")
    async def list_guild_emojis(self, guild_id: utils.RawSnowflakeish) -> typing.List[utils.ResponseBody]:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.EMOJI, "/resources/emoji#get-guild-emoji")
    async def get_guild_emoji(
        self, guild_id: utils.RawSnowflakeish, emoji_id: utils.RawSnowflakeish
    ) -> utils.ResponseBody:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.EMOJI, "/resources/emoji#create-guild-emoji")
    async def create_guild_emoji(
        self, guild_id: utils.RawSnowflakeish, name: str, image: bytes, roles: typing.List[utils.RawSnowflakeish]
    ) -> utils.ResponseBody:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.EMOJI, "/resources/emoji#modify-guild-emoji")
    async def modify_guild_emoji(
        self,
        guild_id: utils.RawSnowflakeish,
        emoji_id: utils.RawSnowflakeish,
        name: str,
        roles: typing.List[utils.RawSnowflakeish],
    ) -> utils.ResponseBody:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.EMOJI, "/resources/emoji#delete-guild-emoji")
    async def delete_guild_emoji(self, guild_id: utils.RawSnowflakeish, emoji_id: utils.RawSnowflakeish) -> None:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    ##########
    # GUILDS #
    ##########
    
    # TODO: guild endpoints here

    ###############
    # INVITATIONS #
    ###############

    @_rtfm(_Scope.INVITE, "/resources/invite#get-invite")
    async def get_invite(self, invite_code: str, *, with_counts: bool = unspecified) -> utils.ResponseBody:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    @_rtfm(_Scope.INVITE, "/resources/invite#delete-invite")
    async def delete_invite(self, invite_code: str) -> utils.ResponseBody:
        raise NotImplementedError  # TODO: implement this endpoint and write tests

    ##########
    # OAUTH2 #
    ##########

    @_rtfm(_Scope.OAUTH2, "/topics/oauth2#get-current-application-information")
    async def application_info(self) -> utils.ResponseBody:
        """
        Get the current application information.

        Returns:
             An application info object.
        """
        _, _, body = await self.request("get", "/oauth2/applications/@me")
        return body

    #########
    # USERS #
    #########
    
    # TODO: user endpoints here
    
    #########
    # VOICE #
    #########
    
    #: TODO: voice endpoints here

    ############
    # WEBHOOKS #
    ############
    
    #: TODO: webhooks here


del _Scope, _rtfm
