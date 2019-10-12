#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
Implementation of the HTTP Client mix of all mixin components.
"""
from __future__ import annotations

import json
import typing

import aiohttp

from hikari.core.net import http_base
from hikari.core.utils import custom_types
from hikari.core.utils import io_utils
from hikari.core.utils import meta
from hikari.core.utils import transform
from hikari.core.utils import unspecified

__all__ = ("HTTPClient",)

DELETE = "delete"
PATCH = "patch"
GET = "get"
POST = "post"
PUT = "put"


class HTTPClient(http_base.BaseHTTPClient):
    """
    Combination of all components for API handling logic for the V7 Discord HTTP API.
    """

    __slots__ = []

    @meta.link_developer_portal(meta.APIResource.GATEWAY)
    async def get_gateway(self) -> str:
        """
        Returns:
            A static URL to use to connect to the gateway with.
        """
        result = await self.request(GET, "/gateway")
        return result["url"]

    @meta.link_developer_portal(meta.APIResource.GATEWAY)
    async def get_gateway_bot(self) -> custom_types.DiscordObject:
        """
        Returns:
            An object containing a `url` to connect to, an :class:`int` number of shards recommended to use
            for connecting, and a `session_start_limit` object.

        Note:
            Unlike `get_gateway`, this requires a valid token to work.
        """
        return await self.request(GET, "/gateway/bot")

    @meta.link_developer_portal(meta.APIResource.AUDIT_LOG)
    async def get_guild_audit_log(
        self,
        guild_id: str,
        *,
        user_id: str = unspecified.UNSPECIFIED,
        action_type: int = unspecified.UNSPECIFIED,
        limit: int = unspecified.UNSPECIFIED,
    ) -> custom_types.DiscordObject:
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
            hikari.errors.Forbidden:
                if you lack the given permissions to view an audit log.
            hikari.errors.NotFound:
                if the guild does not exist.
        """
        query = {}
        transform.put_if_specified(query, "user_id", user_id)
        transform.put_if_specified(query, "action_type", action_type)
        transform.put_if_specified(query, "limit", limit)
        return await self.request(GET, "/guilds/{guild_id}/audit-logs", query=query, guild_id=guild_id)

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def get_channel(self, channel_id: str) -> custom_types.DiscordObject:
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
        return await self.request(GET, "/channels/{channel_id}", channel_id=channel_id)

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def modify_channel(
        self,
        channel_id: str,
        *,
        position: int = unspecified.UNSPECIFIED,
        topic: str = unspecified.UNSPECIFIED,
        nsfw: bool = unspecified.UNSPECIFIED,
        rate_limit_per_user: int = unspecified.UNSPECIFIED,
        bitrate: int = unspecified.UNSPECIFIED,
        user_limit: int = unspecified.UNSPECIFIED,
        permission_overwrites: typing.List[custom_types.DiscordObject] = unspecified.UNSPECIFIED,
        parent_id: str = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> custom_types.DiscordObject:
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
            reason:
                an optional audit log reason explaining why the change was made.

        Raises:
            hikari.errors.NotFound:
                if the channel does not exist.
            hikari.errors.Forbidden:
                if you lack the permission to make the change.
            hikari.errors.BadRequest:
                if you provide incorrect options for the corresponding channel type (e.g. a `bitrate` for a text
                channel).
        """
        payload = {}
        transform.put_if_specified(payload, "position", position)
        transform.put_if_specified(payload, "topic", topic)
        transform.put_if_specified(payload, "nsfw", nsfw)
        transform.put_if_specified(payload, "rate_limit_per_user", rate_limit_per_user)
        transform.put_if_specified(payload, "bitrate", bitrate)
        transform.put_if_specified(payload, "user_limit", user_limit)
        transform.put_if_specified(payload, "permission_overwrites", permission_overwrites)
        transform.put_if_specified(payload, "parent_id", parent_id)
        return await self.request(PATCH, "/channels/{channel_id}", json=payload, channel_id=channel_id, reason=reason)

    @meta.link_developer_portal(meta.APIResource.CHANNEL, "deleteclose-channel")  # nonstandard spelling in URI
    async def delete_close_channel(self, channel_id: str, *, reason: str = unspecified.UNSPECIFIED) -> None:
        """
        Delete the given channel ID, or if it is a DM, close it.

        Args:
            channel_id:
                The channel ID to delete, or the user ID of the direct message to close.
            reason:
                an optional audit log reason explaining why the change was made.

        Returns:
            Nothing, unlike what the API specifies. This is done to maintain consistency with other calls of a similar
            nature in this API wrapper.

        Warning:
            Deleted channels cannot be un-deleted. Deletion of DMs is able to be undone by reopening the DM.

        Raises:
            hikari.errors.NotFound:
                if the channel does not exist
            hikari.errors.Forbidden:
                if you do not have permission to delete the channel.
        """
        await self.request(DELETE, "/channels/{channel_id}", channel_id=channel_id, reason=reason)

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def get_channel_messages(
        self,
        channel_id: str,
        *,
        limit: int = unspecified.UNSPECIFIED,
        after: str = unspecified.UNSPECIFIED,
        before: str = unspecified.UNSPECIFIED,
        around: str = unspecified.UNSPECIFIED,
    ) -> typing.List[custom_types.DiscordObject]:
        """
        Retrieve message history for a given channel. If a user is provided, retrieve the DM history.

        Args:
            channel_id:
                The channel ID to retrieve messages from.
            limit:
                Optional number of messages to return. Must be between 1 and 100 inclusive, and defaults to 50 if
                unspecified.
            after:
                A message ID. If provided, only return messages sent AFTER this message.
            before:
                A message ID. If provided, only return messages sent BEFORE this message.
            around:
                A message ID. If provided, only return messages sent AROUND this message.

        Warning:
            You can only specify a maximum of one from `before`, `after`, and `around`. Specifying more than one will
            cause a :class:`hikari.errors.BadRequest` to be raised.

        Note:
            If you are missing the `VIEW_CHANNEL` permission, you will receive a :class:`hikari.errors.Forbidden`.
            If you are instead missing the `READ_MESSAGE_HISTORY` permission, you will always receive zero results, and
            thus an empty list will be returned instead.

        Returns:
            A list of message objects.

        Raises:
            hikari.errors.Forbidden:
                If you lack permission to read the channel.
            hikari.errors.BadRequest:
                If your query is malformed, has an invalid value for `limit`, or contains more than one of `after`,
                `before` and `around`.
            hikari.errors.NotFound:
                If the given `channel_id` was not found, or the message ID provided for one of the filter arguments
                is not found.
        """
        payload = {}
        transform.put_if_specified(payload, "limit", limit)
        transform.put_if_specified(payload, "before", before)
        transform.put_if_specified(payload, "after", after)
        transform.put_if_specified(payload, "around", around)
        return await self.request(GET, "/channels/{channel_id}/messages", channel_id=channel_id, json=payload)

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def get_channel_message(self, channel_id: str, message_id: str) -> custom_types.DiscordObject:
        """
        Get the message with the given message ID from the channel with the given channel ID.

        Args:
            channel_id:
                The channel to look in.
            message_id:
                The message to retrieve.

        Returns:
            A message object.

        Note:
            This requires the `READ_MESSAGE_HISTORY` permission to be set.

        Raises:
            hikari.errors.Forbidden:
                If you lack permission to see the message.
            hikari.errors.NotFound:
                If the message ID or channel ID is not found.
        """
        return await self.request(
            GET, "/channels/{channel_id}/messages/{message_id}", channel_id=channel_id, message_id=message_id
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    @meta.unofficial
    async def suppress_embeds(self, channel_id: str, message_id: str, *, suppress=True) -> None:
        """
        Either suppresses or un-suppresses any embeds on the given message in the given channel.

        Args:
            channel_id:
                The channel to look in.
            message_id:
                The message to retrieve.
            suppress:
                `True` (default) to suppress any embeds, and `False` to un-suppress embeds.

        Returns:
            A message object.

        Note:
            This requires the `READ_MESSAGE_HISTORY` and `MANAGE_MESSAGES` permission to be set.

        Raises:
            hikari.errors.Forbidden:
                If you lack permission to see the message, are not in the guild, or lack the latter-mentioned
                permissions in the target channel.
            hikari.errors.NotFound:
                If the message ID or channel ID is not found.
        """
        return await self.request(
            POST,
            "/channels/{channel_id}/messages/{message_id}/suppress-embeds",
            channel_id=channel_id,
            message_id=message_id,
            json={"suppress": suppress},
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def create_message(
        self,
        channel_id: str,
        *,
        content: str = unspecified.UNSPECIFIED,
        nonce: str = unspecified.UNSPECIFIED,
        tts: bool = False,
        files: typing.List[io_utils.FileLike] = unspecified.UNSPECIFIED,
        embed: custom_types.DiscordObject = unspecified.UNSPECIFIED,
    ) -> custom_types.DiscordObject:
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
        transform.put_if_specified(json_payload, "content", content)
        transform.put_if_specified(json_payload, "nonce", nonce)
        transform.put_if_specified(json_payload, "embed", embed)

        form.add_field("payload_json", json.dumps(json_payload), content_type="application/json")

        re_seekable_resources = []
        if files is not unspecified.UNSPECIFIED:
            for i, (file_name, file) in enumerate(files):
                file = io_utils.make_resource_seekable(file)
                re_seekable_resources.append(file)
                form.add_field(f"file{i}", file, filename=file_name, content_type="application/octet-stream")

        return await self.request(
            POST,
            "/channels/{channel_id}/messages",
            channel_id=channel_id,
            re_seekable_resources=re_seekable_resources,
            data=form,
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def create_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        """
        Add a reaction to the given message in the given channel or user DM.

        Args:
            channel_id:
                The ID of the channel to add the reaction in.
            message_id:
                The ID of the message to add the reaction in.
            emoji:
                The emoji to add. This can either be a series of unicode characters making up a valid Discord
                emoji, or it can be in the form of name:id for a custom emoji.

        Raises:
            hikari.errors.Forbidden:
                if this is the first reaction using this specific emoji on this message and you lack the `ADD_REACTIONS`
                permission. If you lack `READ_MESSAGE_HISTORY`, this may also raise this error.
            hikari.errors.NotFound:
                if the channel or message is not found, or if the emoji is not found.
            hikari.core.errors.BadRequest:
                if the emoji is not valid, unknown, or formatted incorrectly
        """
        await self.request(
            PUT,
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def delete_own_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        """
        Remove a reaction you made using a given emoji from a given message in a given channel or user DM.

        Args:
            channel_id:
                The ID of the channel to delete the reaction from.
            message_id:
                The ID of the message to delete the reaction from.
            emoji:
                The emoji to delete. This can either be a series of unicode characters making up a valid Discord
                emoji, or it can be a snowflake ID for a custom emoji.

        Raises:
            hikari.errors.NotFound:
                if the channel or message or emoji is not found.
        """
        await self.request(
            DELETE,
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def delete_user_reaction(self, channel_id: str, message_id: str, emoji: str, user_id: str) -> None:
        """
        Remove a reaction made by a given user using a given emoji on a given message in a given channel or user DM.

        Args:
            channel_id:
                the channel ID to remove from.
            message_id:
                the message ID to remove from.
            emoji:
                The emoji to delete. This can either be a series of unicode characters making up a valid Discord
                emoji, or it can be a snowflake ID for a custom emoji.
            user_id:
                The ID of the user who made the reaction that you wish to remove.

        Raises:
            hikari.errors.NotFound:
                if the channel or message or emoji or user is not found.
            hikari.errors.Forbidden:
                if you lack the `MANAGE_MESSAGES` permission, or are in DMs.
        """
        await self.request(
            DELETE,
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/{user_id}",
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
            user_id=user_id,
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def get_reactions(
        self,
        channel_id: str,
        message_id: str,
        emoji: str,
        *,
        before: str = unspecified.UNSPECIFIED,
        after: str = unspecified.UNSPECIFIED,
        limit: int = unspecified.UNSPECIFIED,
    ) -> typing.List[custom_types.DiscordObject]:
        """
        Get a list of users who reacted with the given emoji on the given message in the given channel or user DM.

        Args:
            channel_id:
                the channel to get the message from.
            message_id:
                the ID of the message to retrieve.
            emoji:
                The emoji to get. This can either be a series of unicode characters making up a valid Discord
                emoji, or it can be a snowflake ID for a custom emoji.
            before:
                An optional user ID. If specified, only users with a snowflake that is lexicographically less than the
                value will be returned.
            after:
                An optional user ID. If specified, only users with a snowflake that is lexicographically greater than
                the value will be returned.
            limit:
                An optional limit of the number of values to return. Must be between 1 and 100 inclusive. If
                unspecified, it defaults to 25.

        Returns:
            A list of user objects.
        """
        payload = {}
        transform.put_if_specified(payload, "before", before)
        transform.put_if_specified(payload, "after", after)
        transform.put_if_specified(payload, "limit", limit)
        return await self.request(
            GET,
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
            json=payload,
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL, "/resources/channel#delete-all-reactions")
    async def delete_all_reactions(self, channel_id: str, message_id: str) -> None:
        """
        Deletes all reactions from a given message in a given channel.

        Args:
            channel_id:
                The channel ID to remove reactions within.
            message_id:
                The message ID to remove reactions from.

        Raises:
            hikari.errors.NotFound:
                if the channel_id or message_id was not found.
            hikari.errors.Forbidden:
                if you lack the `MANAGE_MESSAGES` permission.
        """
        await self.request(
            DELETE,
            "/channels/{channel_id}/messages/{message_id}/reactions",
            channel_id=channel_id,
            message_id=message_id,
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        *,
        content: str = unspecified.UNSPECIFIED,
        embed: custom_types.DiscordObject = unspecified.UNSPECIFIED,
    ) -> custom_types.DiscordObject:
        """
        Update the given message.

        Args:
            channel_id:
                The channel ID (or user ID if a direct message) to operate in.
            message_id:
                The message ID to edit.
            content:
                Optional string content to replace with in the message. If unspecified, it is not changed.
            embed:
                Optional embed to replace with in the message. If unspecified, it is not changed.

        Returns:
            A replacement message object.

        Raises:
            hikari.errors.NotFound:
                if the channel_id or message_id is not found.
            hikari.errors.BadRequest:
                if the embed exceeds any of the embed limits if specified, or the content is specified and consists
                only of whitespace, is empty, or is more than 2,000 characters in length.
            hikari.errors.Forbidden:
                if you did not author the message.
        """
        payload = {}
        transform.put_if_specified(payload, "content", content)
        transform.put_if_specified(payload, "embed", embed)
        return await self.request(
            PATCH,
            "/channels/{channel_id}/messages/{message_id}",
            channel_id=channel_id,
            message_id=message_id,
            json=payload,
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def delete_message(self, channel_id: str, message_id: str) -> None:
        """
        Delete a message in a given channel.

        Args:
            channel_id:
                the channel ID or user ID that the message was sent to.
            message_id:
                the message ID that was sent.

        Raises:
            hikari.errors.Forbidden:
                if you did not author the message and are in a DM, or if you did not author the message and lack the
                `MANAGE_MESSAGES` permission in a guild channel.
            hikari.errors.NotFound:
                if the channel or message was not found.
        """
        await self.request(
            DELETE, "/channels/{channel_id}/messages/{message_id}", channel_id=channel_id, message_id=message_id
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def bulk_delete_messages(self, channel_id: str, messages: typing.List[str]) -> None:
        """
        Delete multiple messages in one request.

        Args:
            channel_id:
                the channel_id to delete from.
            messages:
                a list of 2-100 message IDs to remove in the channel.

        Raises:
            hikari.errors.NotFound:
                if the channel_id is not found.
            hikari.errors.Forbidden:
                if you lack the `MANAGE_MESSAGES` permission in the channel.

        Notes:
            This can only be used on guild text channels.

            Any message IDs that do not exist or are invalid add towards the total 100 max messages to remove.
            Duplicate IDs are only counted once in this count.

            This can only delete messages that are newer than 2 weeks in age. If all messages are older than 2 weeks
            then this call will fail.
        """
        await self.request(
            POST, "/channels/{channel_id}/messages/bulk-delete", channel_id=channel_id, json={"messages": messages}
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def edit_channel_permissions(
        self,
        channel_id: str,
        overwrite_id: str,
        allow: int,
        deny: int,
        type_: str,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Edit permissions for a given channel.

        Args:
            channel_id:
                the channel to edit permissions for.
            overwrite_id:
                the overwrite ID to edit.
            allow:
                the bitwise value of all permissions to set to be allowed.
            deny:
                the bitwise value of all permissions to set to be denied.
            type_:
                "member" if it is for a member, or "role" if it is for a role.
            reason:
                an optional audit log reason explaining why the change was made.
        """
        payload = {"allow": allow, "deny": deny, "type": type_}
        await self.request(
            PUT,
            "/channels/{channel_id}/permissions/{overwrite_id}",
            channel_id=channel_id,
            overwrite_id=overwrite_id,
            json=payload,
            reason=reason,
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def get_channel_invites(self, channel_id: str) -> typing.List[custom_types.DiscordObject]:
        """
        Get invites for a given channel.

        Args:
            channel_id:
                the channel to get invites for.

        Returns:
            a list of invite objects.

        Raises:
            hikari.errors.Forbidden:
                if you lack the `MANAGE_CHANNELS` permission.
            hikari.errors.NotFound:
                if the channel does not exist.
        """
        return await self.request(GET, "/channels/{channel_id}/invites", channel_id=channel_id)

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def create_channel_invite(
        self,
        channel_id: str,
        *,
        max_age: int = unspecified.UNSPECIFIED,
        max_uses: int = unspecified.UNSPECIFIED,
        temporary: bool = unspecified.UNSPECIFIED,
        unique: bool = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> custom_types.DiscordObject:
        """
        Create a new invite for the given channel.

        Args:
            channel_id:
                the channel ID to create the invite for.
            max_age:
                the max age of the invite in seconds, defaults to 86400 (24 hours). Set to 0 to never expire.
            max_uses:
                the max number of uses this invite can have, or 0 for unlimited (as per the default).
            temporary:
                if `True`, grant temporary membership, meaning the user is kicked when their session ends unless they
                are given a role. Defaults to `False`.
            unique:
                if `True`, never reuse a similar invite. Defaults to `False`.
            reason:
                an optional audit log reason explaining why the change was made.

        Returns:
            An invite object.

        Raises:
            hikari.errors.Forbidden:
                if you lack the `CREATE_INSTANT_MESSAGES` permission.
            hikari.errors.NotFound:
                if the channel does not exist.
            hikari.errors.BadRequest:
                if the arguments provided are not valid (e.g. negative age, etc).
        """
        payload = {}
        transform.put_if_specified(payload, "max_age", max_age)
        transform.put_if_specified(payload, "max_uses", max_uses)
        transform.put_if_specified(payload, "temporary", temporary)
        transform.put_if_specified(payload, "unique", unique)
        return await self.request(
            POST, "/channels/{channel_id}/invites", json=payload, channel_id=channel_id, reason=reason
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def delete_channel_permission(
        self, channel_id: str, overwrite_id: str, *, reason: str = unspecified.UNSPECIFIED
    ) -> None:
        """
        Delete a channel permission overwrite for a user or a role in a channel.

        Args:
            channel_id:
                the channel ID to delete from.
            overwrite_id:
                the override ID to remove.
            reason:
                an optional audit log reason explaining why the change was made.

        Raises:
            hikari.errors.NotFound:
                if the overwrite or channel ID does not exist.
            hikari.errors.Forbidden:
                if you lack the `MANAGE_ROLES` permission for that channel.
        """
        await self.request(
            DELETE,
            "/channels/{channel_id}/permissions/{overwrite_id}",
            channel_id=channel_id,
            overwrite_id=overwrite_id,
            reason=reason,
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def trigger_typing_indicator(self, channel_id: str) -> None:
        """
        Trigger the account to appear to be typing for the next 10 seconds in the given channel.

        Args:
            channel_id:
                the channel ID to appear to be typing in. This may be a user ID if you wish to appear to be typing
                in DMs.

        Raises:
            hikari.errors.NotFound:
                if the channel is not found.
            hikari.errors.Forbidden:
                if you are not in the guild the channel is in
        """
        await self.request(POST, "/channels/{channel_id}/typing", channel_id=channel_id)

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def get_pinned_messages(self, channel_id: str) -> None:
        """
        Get pinned messages for a given channel.

        Args:
            channel_id:
                the channel ID to get messages for.

        Returns:
            A list of messages.

        Raises:
            hikari.errors.NotFound:
                if no channel matching the ID exists.
        """
        return await self.request(GET, "/channels/{channel_id}/pins", channel_id=channel_id)

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def add_pinned_channel_message(self, channel_id: str, message_id: str) -> None:
        """
        Add a pinned message to the channel.

        Args:
            channel_id:
                the channel ID to add a pin to.
            message_id:
                the message in the channel to pin.

        Raises:
            hikari.errors.Forbidden:
                if you lack the `MANAGE_MESSAGES` permission.
            hikari.errors.NotFound:
                if the message or channel does not exist.
        """
        await self.request(
            PUT, "/channels/{channel_id}/pins/{message_id}", channel_id=channel_id, message_id=message_id
        )

    @meta.link_developer_portal(meta.APIResource.CHANNEL)
    async def delete_pinned_channel_message(self, channel_id: str, message_id: str) -> None:
        """
        Remove a pinned message to the channel. This will only unpin the message. It will not delete it.

        Args:
            channel_id:
                the channel ID to remove a pin from.
            message_id:
                the message in the channel to unpin.

        Raises:
            hikari.errors.Forbidden:
                if you lack the `MANAGE_MESSAGES` permission.
            hikari.errors.NotFound:
                if the message or channel does not exist.
        """
        await self.request(
            DELETE, "/channels/{channel_id}/pins/{message_id}", channel_id=channel_id, message_id=message_id
        )

    @meta.link_developer_portal(meta.APIResource.EMOJI)
    async def list_guild_emojis(self, guild_id: str) -> typing.List[custom_types.DiscordObject]:
        """
        Gets emojis for a given guild ID.

        Args:
            guild_id:
                The guild ID to get the emojis for.

        Returns:
            A list of emoji objects.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you aren't a member of said guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/emojis", guild_id=guild_id)

    @meta.link_developer_portal(meta.APIResource.EMOJI)
    async def get_guild_emoji(self, guild_id: str, emoji_id: str) -> custom_types.DiscordObject:
        """
        Gets an emoji from a given guild and emoji IDs

        Args:
            guild_id:
                The ID of the guild to get the emoji from.
            emoji_id:
                The ID of the emoji to get.

        Returns:
            An emoji object.

        Raises:
            hikari.errors.NotFound:
                If either the guild or the emoji aren't found.
            hikari.errors.Forbidden:
                If you aren't a member of said guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/emojis/{emoji_id}", guild_id=guild_id, emoji_id=emoji_id)

    @meta.link_developer_portal(meta.APIResource.EMOJI)
    async def create_guild_emoji(
        self, guild_id: str, name: str, image: bytes, roles: typing.List[str], *, reason: str = unspecified.UNSPECIFIED
    ) -> custom_types.DiscordObject:
        """
        Creates a new emoji for a given guild.

        Args:
            guild_id:
                The ID of the guild to create the emoji in.
            name:
                The new emoji's name.
            image:
                The 128x128 image in bytes form.
            roles:
                A list of roles for which the emoji will be whitelisted.
            reason:
                An optional audit log reason explaining why the change was made.

        Returns:
            The newly created emoji object.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_EMOJIS` permission or aren't a member of said guild.
            hikari.errors.BadRequest:
                If you attempt to upload an image larger than 256kb, an empty image or an invalid image format.
        """
        payload = {"name": name, "image": image, "roles": roles}
        return await self.request(POST, "/guilds/{guild_id}/emojis", guild_id=guild_id, json=payload, reason=reason)

    @meta.link_developer_portal(meta.APIResource.EMOJI)
    async def modify_guild_emoji(
        self, guild_id: str, emoji_id: str, name: str, roles: typing.List[str], reason: str = unspecified.UNSPECIFIED
    ) -> custom_types.DiscordObject:
        """
        Edits an emoji of a given guild

        Args:
            guild_id:
                The ID of the guild to which the edited emoji belongs to.
            emoji_id:
                The ID of the edited emoji.
            name:
                The new emoji name string.
            roles:
                A list of IDs for the new whitelisted roles.
            reason:
                an optional audit log reason explaining why the change was made.

        Returns:
            The updated emoji object.

        Raises:
            hikari.errors.NotFound:
                If either the guild or the emoji aren't found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_EMOJIS` permission or are not a member of the given guild.
        """
        payload = {"name": name, "roles": roles}
        return await self.request(
            PATCH,
            "/guilds/{guild_id}/emojis/{emoji_id}",
            guild_id=guild_id,
            emoji_id=emoji_id,
            json=payload,
            reason=reason,
        )

    @meta.link_developer_portal(meta.APIResource.EMOJI)
    async def delete_guild_emoji(self, guild_id: str, emoji_id: str, *, reason: str = unspecified.UNSPECIFIED) -> None:
        """
        Deletes an emoji from a given guild

        Args:
            guild_id:
                The ID of the guild to delete the emoji from
            emoji_id:
                The ID of the emoji to be deleted
            reason:
                an optional audit log reason explaining why the change was made.

         Raises:
            hikari.errors.NotFound:
                If either the guild or the emoji aren't found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_EMOJIS` permission or aren't a member of said guild.
        """
        return await self.request(
            DELETE, "/guilds/{guild_id}/emojis/{emoji_id}", guild_id=guild_id, emoji_id=emoji_id, reason=reason
        )

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def create_guild(
        self,
        name: str,
        region: str,
        icon: bytes,
        verification_level: int,
        default_message_notifications: int,
        explicit_content_filter: int,
        roles: typing.List[custom_types.DiscordObject],
        channels: typing.List[custom_types.DiscordObject],
    ) -> custom_types.DiscordObject:
        """
        Creates a new guild. Can only be used by bots in less than 10 guilds.

        Args:
            name:
                The name string for the new guild (2-100 characters).
            region:
                The voice region ID for new guild. You can use `list_voice_regions` to see which region IDs are
                available.
            icon:
                The guild icon image in bytes form.
            verification_level:
                The verification level integer (0-5).
            default_message_notifications:
                The default notification level integer (0-1).
            explicit_content_filter:
                The explicit content filter integer (0-2).
            roles:
                An array of role objects to be created alongside the guild. First element changes the `@everyone` role.
            channels:
                An array of channel objects to be created alongside the guild.

        Returns:
            The newly created guild object.

        Raises:
            hikari.errors.Forbidden:
                If your bot is on 10 or more guilds.
            hikari.errors.BadRequest:
                If you provide unsupported fields like `parent_id` in channel objects.
        """
        payload = {
            "name": name,
            "region": region,
            "icon": icon,
            "verification_level": verification_level,
            "default_message_notifications": default_message_notifications,
            "explicit_content_filter": explicit_content_filter,
            "roles": roles,
            "channels": channels,
        }
        return await self.request(POST, "/guilds", json=payload)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def get_guild(self, guild_id: str) -> custom_types.DiscordObject:
        """
        Gets a given guild's object.

        Args:
            guild_id:
                The ID of the guild to get.

        Returns:
            The requested guild object.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
        """
        return await self.request(GET, "/guilds/{guild_id}", guild_id=guild_id)

    # pylint: disable=too-many-locals
    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def modify_guild(
        self,
        guild_id: str,
        *,
        name: str = unspecified.UNSPECIFIED,
        region: str = unspecified.UNSPECIFIED,
        verification_level: str = unspecified.UNSPECIFIED,
        default_message_notifications: str = unspecified.UNSPECIFIED,
        explicit_content_filter: int = unspecified.UNSPECIFIED,
        afk_channel_id: str = unspecified.UNSPECIFIED,
        afk_timeout: int = unspecified.UNSPECIFIED,
        icon: bytes = unspecified.UNSPECIFIED,
        owner_id: str = unspecified.UNSPECIFIED,
        splash: bytes = unspecified.UNSPECIFIED,
        system_channel_id: str = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> custom_types.DiscordObject:
        """
        Edits a given guild.

        Args:
            guild_id:
                The ID of the guild to be edited.
            name:
                The new name string.
            region:
                The voice region ID for new guild. You can use `list_voice_regions` to see which region IDs are
                available.
            verification_level:
                The verification level integer (0-5).
            default_message_notifications:
                The default notification level integer (0-1).
            explicit_content_filter:
                The explicit content filter integer (0-2).
            afk_channel_id:
                The ID for the AFK voice channel.
            afk_timeout:
                The AFK timeout period in seconds
            icon:
                The guild icon image in bytes form.
            owner_id:
                The ID of the new guild owner.
            splash:
                The new splash image in bytes form.
            system_channel_id:
                The ID of the new system channel.
            reason:
                Optional reason to apply to the audit log.

        Returns:
            The edited guild object.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        payload = {}
        transform.put_if_specified(payload, "name", name)
        transform.put_if_specified(payload, "region", region)
        transform.put_if_specified(payload, "verification_level", verification_level)
        transform.put_if_specified(payload, "default_message_notifications", default_message_notifications)
        transform.put_if_specified(payload, "explicit_content_filter", explicit_content_filter)
        transform.put_if_specified(payload, "afk_channel_id", afk_channel_id)
        transform.put_if_specified(payload, "afk_timeout", afk_timeout)
        transform.put_if_specified(payload, "icon", icon)
        transform.put_if_specified(payload, "owner_id", owner_id)
        transform.put_if_specified(payload, "splash", splash)
        transform.put_if_specified(payload, "system_channel_id", system_channel_id)
        return await self.request(PATCH, "/guilds/{guild_id}", guild_id=guild_id, json=payload, reason=reason)

    # pylint: enable=too-many-locals

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def delete_guild(self, guild_id: str) -> None:
        """
        Permanently deletes the given guild. You must be owner.

        Args:
            guild_id:
                The ID of the guild to be deleted.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you're not the guild owner.
        """
        return await self.request(DELETE, "/guilds/{guild_id}", guild_id=guild_id)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def get_guild_channels(self, guild_id: str) -> typing.List[custom_types.DiscordObject]:
        """
        Gets all the channels for a given guild.

        Args:
            guild_id:
                The ID of the guild to get the channels from.

        Returns:
            A list of channel objects.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you're not in the guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/channels", guild_id=guild_id)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def create_guild_channel(
        self,
        guild_id: str,
        name: str,
        *,
        type_: int = unspecified.UNSPECIFIED,
        topic: str = unspecified.UNSPECIFIED,
        bitrate: int = unspecified.UNSPECIFIED,
        user_limit: int = unspecified.UNSPECIFIED,
        rate_limit_per_user: int = unspecified.UNSPECIFIED,
        position: int = unspecified.UNSPECIFIED,
        permission_overwrites: typing.List[custom_types.DiscordObject] = unspecified.UNSPECIFIED,
        parent_id: str = unspecified.UNSPECIFIED,
        nsfw: bool = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> custom_types.DiscordObject:
        """
        Creates a channel in a given guild.

        Args:
            guild_id:
                The ID of the guild to create the channel in.
            name:
                The new channel name string (2-100 characters).
            type_:
                The channel type integer (0-6).
            topic:
                The string for the channel topic (0-1024 characters).
            bitrate:
                The bitrate integer (in bits) for the voice channel, if applicable.
            user_limit:
                The maximum user count for the voice channel, if applicable.
            rate_limit_per_user:
                The seconds a user has to wait before posting another message (0-21600).
                Having the `MANAGE_MESSAGES` or `MANAGE_CHANNELS` permissions gives you immunity.
            position:
                The sorting position for the channel.
            permission_overwrites:
                A list of overwrite objects to apply to the channel.
            parent_id:
                The ID of the parent category/
            nsfw:
                Marks the channel as NSFW if `True`.
            reason:
                The optional reason for the operation being performed.

        Returns:
            The newly created channel object.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you lack the `MANAGE_CHANNEL` permission or are not in the target guild or are not in the guild.
            hikari.errors.BadRequest:
                If you omit the `name` argument.
        """
        payload = {"name": name}
        transform.put_if_specified(payload, "type", type_)
        transform.put_if_specified(payload, "topic", topic)
        transform.put_if_specified(payload, "bitrate", bitrate)
        transform.put_if_specified(payload, "user_limit", user_limit)
        transform.put_if_specified(payload, "rate_limit_per_user", rate_limit_per_user)
        transform.put_if_specified(payload, "position", position)
        transform.put_if_specified(payload, "permission_overwrites", permission_overwrites)
        transform.put_if_specified(payload, "parent_id", parent_id)
        transform.put_if_specified(payload, "nsfw", nsfw)
        return await self.request(POST, "/guilds/{guild_id}/channels", guild_id=guild_id, json=payload, reason=reason)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def modify_guild_channel_positions(
        self,
        guild_id: str,
        channel: typing.Tuple[str, int],
        *channels: typing.Tuple[str, int],
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Edits the position of one or more given channels.

        Args:
            guild_id:
                The ID of the guild in which to edit the channels.
            channel:
                the first channel to change the position of. This is a tuple of the channel ID and the integer position.
            channels:
                optional additional channels to change the position of. These must be tuples of the channel ID and the
                integer positions to change to.
            reason:
                optional reason to add to the audit log for making this change.

        Raises:
            hikari.errors.NotFound:
                If either the guild or any of the channels aren't found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_CHANNELS` permission or are not a member of said guild or are not in
                the guild.
            hikari.errors.BadRequest:
                If you provide anything other than the `id` and `position` fields for the channels.
        """
        payload = [{"id": ch[0], "position": ch[1]} for ch in (channel, *channels)]
        return await self.request(PATCH, "/guilds/{guild_id}/channels", guild_id=guild_id, json=payload, reason=reason)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def get_guild_member(self, guild_id: str, user_id: str) -> custom_types.DiscordObject:
        """
        Gets a given guild member.

        Args:
            guild_id:
                The ID of the guild to get the member from.
            user_id:
                The ID of the member to get.

        Returns:
            The requested member object.

        Raises:
            hikari.errors.NotFound:
                If either the guild or the member aren't found or are not in the guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/members/{user_id}", guild_id=guild_id, user_id=user_id)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def list_guild_members(
        self, guild_id: str, *, limit: int = unspecified.UNSPECIFIED, after: str = unspecified.UNSPECIFIED
    ) -> typing.List[custom_types.DiscordObject]:
        """
        Lists all members of a given guild.

        Args:
            guild_id:
                The ID of the guild to get the members from.
            limit:
                The maximum number of members to return (1-1000).
            after:
                The highest ID in the previous page. This is used for retrieving more than 1000 members in a server
                using consecutive requests.
                
        Example:
            .. code-block:: python
                
                members = []
                last_id = 0
                
                while True:
                    next_members = await client.list_guild_members(1234567890, limit=1000, after=last_id)
                    members += next_members
                    
                    if len(next_members) == 1000:
                        last_id = max(m["id"] for m in next_members)
                    else:
                        break                  

        Returns:
            A list of member objects.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you are not in the guild.
            hikari.errors.BadRequest:
                If you provide invalid values for the `limit` and `after` fields.
        """
        payload = {}
        transform.put_if_specified(payload, "limit", limit)
        transform.put_if_specified(payload, "after", after)
        return await self.request(GET, "/guilds/{guild_id}/members", guild_id=guild_id, json=payload)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def modify_guild_member(
        self,
        guild_id: str,
        user_id: str,
        *,
        nick: typing.Optional[str] = unspecified.UNSPECIFIED,
        roles: typing.List[str] = unspecified.UNSPECIFIED,
        mute: bool = unspecified.UNSPECIFIED,
        deaf: bool = unspecified.UNSPECIFIED,
        channel_id: typing.Optional[str] = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Edits a member of a given guild.

        Args:
            guild_id:
                The ID of the guild to edit the member from.
            user_id:
                The ID of the member to edit.
            nick:
                The new nickname string.
            roles:
                A list of role IDs the member should have.
            mute:
                Whether the user should be muted in the voice channel or not, if applicable.
            deaf:
                Whether the user should be deafen in the voice channel or not, if applicable.
            channel_id:
                The ID of the channel to move the member to, if applicable. Pass None to disconnect the user.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.
        Raises:
            hikari.errors.NotFound:
                If either the guild, user, channel or any of the roles aren't found.
            hikari.errors.Forbidden:
                If you lack any of the applicable permissions
                (`MANAGE_NICKNAMES`, `MANAGE_ROLES`, `MUTE_MEMBERS`, `DEAFEN_MEMBERS` or `MOVE_MEMBERS`).
                Note that to move a member you must also have permission to connect to the end channel.
                This will also be raised if you're not in the guild.
            hikari.errors.BadRequest:
                If you pass `mute`, `deaf` or `channel_id` while the member is not connected to a voice channel.
        """
        payload = {}
        transform.put_if_specified(payload, "nick", nick)
        transform.put_if_specified(payload, "roles", roles)
        transform.put_if_specified(payload, "mute", mute)
        transform.put_if_specified(payload, "deaf", deaf)
        transform.put_if_specified(payload, "channel_id", channel_id)
        return await self.request(
            PATCH,
            "/guilds/{guild_id}/members/{user_id}",
            guild_id=guild_id,
            user_id=user_id,
            json=payload,
            reason=reason,
        )

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def modify_current_user_nick(
        self, guild_id: str, nick: typing.Optional[str], *, reason: str = unspecified.UNSPECIFIED
    ) -> str:
        """
        Edits the current user's nickname for a given guild.

        Args:
            guild_id:
                The ID of the guild you want to change the nick on.
            nick:
                The new nick string.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.
                
        Returns:
            The new nickname.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you lack the `CHANGE_NICKNAME` permission or are not in the guild.
            hikari.errors.BadRequest:
                If you provide a disallowed nickname, one that is too long, or one that is empty.
        """
        return await self.request(
            PATCH, "/guilds/{guild_id}/members/@me/nick", guild_id=guild_id, json={"nick": nick}, reason=reason
        )

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def add_guild_member_role(
        self, guild_id: str, user_id: str, role_id: str, *, reason: str = unspecified.UNSPECIFIED
    ) -> None:
        """
        Adds a role to a given member.

        Args:
            guild_id:
                The ID of the guild the member belongs to.
            user_id:
                The ID of the member you want to add the role to.
            role_id:
                The ID of the role you want to add.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.errors.NotFound:
                If either the guild, member or role aren't found.
            hikari.errors.Forbidden:
                If you lack the `MANAGE_ROLES` permission or are not in the guild.
        """
        return await self.request(
            PUT,
            "/guilds/{guild_id}/members/{user_id}/roles/{role_id}",
            guild_id=guild_id,
            user_id=user_id,
            role_id=role_id,
            reason=reason,
        )

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def remove_guild_member_role(
        self, guild_id: str, user_id: str, role_id: str, *, reason: str = unspecified.UNSPECIFIED
    ) -> None:
        """
        Removed a role from a given member.

        Args:
            guild_id:
                The ID of the guild the member belongs to.
            user_id:
                The ID of the member you want to remove the role from.
            role_id:
                The ID of the role you want to remove.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.errors.NotFound:
                If either the guild, member or role aren't found.
            hikari.errors.Forbidden:
                If you lack the `MANAGE_ROLES` permission or are not in the guild.
        """
        return await self.request(
            DELETE,
            "/guilds/{guild_id}/members/{user_id}/roles/{role_id}",
            guild_id=guild_id,
            user_id=user_id,
            role_id=role_id,
            reason=reason,
        )

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def remove_guild_member(self, guild_id: str, user_id: str, *, reason: str = unspecified.UNSPECIFIED) -> None:
        """
        Kicks a user from a given guild.

        Args:
            guild_id:
                The ID of the guild the member belongs to.
            user_id:
                The ID of the member you want to kick.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.errors.NotFound:
                If either the guild or member aren't found.
            hikari.errors.Forbidden:
                If you lack the `KICK_MEMBERS` permission or are not in the guild.
        """
        return await self.request(
            DELETE, "/guilds/{guild_id}/members/{user_id}", guild_id=guild_id, user_id=user_id, reason=reason
        )

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def get_guild_bans(self, guild_id: str) -> typing.List[custom_types.DiscordObject]:
        """
        Gets the bans for a given guild.

        Args:
            guild_id:
                The ID of the guild you want to get the bans from.

        Returns:
            A list of ban objects.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you lack the `BAN_MEMBERS` permission or are not in the guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/bans", guild_id=guild_id)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def get_guild_ban(self, guild_id: str, user_id: str) -> custom_types.DiscordObject:
        """
        Gets a ban from a given guild.

        Args:
            guild_id:
                The ID of the guild you want to get the ban from.
            user_id:
                The ID of the user to get the ban information for.

        Returns:
            A ban object for the requested user.

        Raises:
            hikari.errors.NotFound:
                If either the guild or the user aren't found, or if the user is not banned.
            hikari.errors.Forbidden:
                If you lack the `BAN_MEMBERS` permission or are not in the guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/bans/{user_id}", guild_id=guild_id, user_id=user_id)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def create_guild_ban(
        self,
        guild_id: str,
        user_id: str,
        *,
        delete_message_days: int = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Bans a user from a given guild.

        Args:
            guild_id:
                The ID of the guild the member belongs to.
            user_id:
                The ID of the member you want to ban.
            delete_message_days:
                How many days of messages from the user should be removed. Default is to not delete anything.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.errors.NotFound:
                If either the guild or member aren't found.
            hikari.errors.Forbidden:
                If you lack the `BAN_MEMBERS` permission or are not in the guild.
        """
        query = {}
        transform.put_if_specified(query, "delete_message_days", delete_message_days)
        transform.put_if_specified(query, "reason", reason)
        return await self.request(
            PUT, "/guilds/{guild_id}/bans/{user_id}", guild_id=guild_id, user_id=user_id, query=query
        )

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def remove_guild_ban(self, guild_id: str, user_id: str, *, reason: str = unspecified.UNSPECIFIED) -> None:
        """
        Un-bans a user from a given guild.

        Args:
            guild_id:
                The ID of the guild the member belongs to.
            user_id:
                The ID of the member you want to un-ban.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.errors.NotFound:
                If either the guild or member aren't found.
            hikari.errors.Forbidden:
                If you lack the `BAN_MEMBERS` permission or are not a in the guild.
        """
        return await self.request(
            DELETE, "/guilds/{guild_id}/bans/{user_id}", guild_id=guild_id, user_id=user_id, reason=reason
        )

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def get_guild_roles(self, guild_id: str) -> typing.List[custom_types.DiscordObject]:
        """
        Gets the roles for a given guild.

        Args:
            guild_id:
                The ID of the guild you want to get the roles from.

        Returns:
            A list of role objects.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you're not in the guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/roles", guild_id=guild_id)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def create_guild_role(
        self,
        guild_id: str,
        *,
        name: str = unspecified.UNSPECIFIED,
        permissions: int = unspecified.UNSPECIFIED,
        color: int = unspecified.UNSPECIFIED,
        hoist: bool = unspecified.UNSPECIFIED,
        mentionable: bool = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> custom_types.DiscordObject:
        """
        Creates a new role for a given guild.

        Args:
            guild_id:
                The ID of the guild you want to create the role on.
            name:
                The new role name string.
            permissions:
                The permissions integer for the role.
            color:
                The color for the new role.
            hoist:
                Whether the role should hoist or not.
            mentionable:
                Whether the role should be able to be mentioned by users or not.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Returns:
            The newly created role object.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you lack the `MANAGE_ROLES` permission or you're not in the guild.
            hikari.errors.BadRequest:
                If you provide invalid values for the role attributes.
        """
        payload = {}
        transform.put_if_specified(payload, "name", name)
        transform.put_if_specified(payload, "permissions", permissions)
        transform.put_if_specified(payload, "color", color)
        transform.put_if_specified(payload, "hoist", hoist)
        transform.put_if_specified(payload, "mentionable", mentionable)
        return await self.request(POST, "/guilds/{guild_id}/roles", guild_id=guild_id, json=payload, reason=reason)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def modify_guild_role_positions(
        self,
        guild_id: str,
        role: typing.Tuple[str, int],
        *roles: typing.Tuple[str, int],
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Edits the position of two or more roles in a given guild.

        Args:
            guild_id:
                The ID of the guild the roles belong to.
            role:
                The first role to move.
            roles:
                Optional extra roles to move.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Returns:
            A list of all the guild roles.

        Raises:
            hikari.errors.NotFound:
                If either the guild or any of the roles aren't found.
            hikari.errors.Forbidden:
                If you lack the `MANAGE_ROLES` permission or you're not in the guild.
            hikari.errors.BadRequest:
                If you provide invalid values for the `position` fields.
        """
        payload = [{"id": r[0], "position": r[1]} for r in (role, *roles)]
        return await self.request(PATCH, "/guilds/{guild_id}/roles", guild_id=guild_id, json=payload, reason=reason)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def modify_guild_role(
        self,
        guild_id: str,
        role_id: str,
        *,
        name: str = unspecified.UNSPECIFIED,
        permissions: int = unspecified.UNSPECIFIED,
        color: int = unspecified.UNSPECIFIED,
        hoist: bool = unspecified.UNSPECIFIED,
        mentionable: bool = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Edits a role in a given guild.

        Args:
            guild_id:
                The ID of the guild the role belong to.
            role_id:
                The ID of the role you want to edit.
            name:
                THe new role's name string.
            permissions:
                The new permissions integer for the role.
            color:
                The new color for the new role.
            hoist:
                Whether the role should hoist or not.
            mentionable:
                Whether the role should be mentionable or not.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.
                
        Returns:
            The edited role object.

        Raises:
            hikari.errors.NotFound:
                If either the guild or role aren't found.
            hikari.errors.Forbidden:
                If you lack the `MANAGE_ROLES` permission or you're not in the guild.
            hikari.errors.BadRequest:
                If you provide invalid values for the role attributes.
        """
        payload = {}
        transform.put_if_specified(payload, "name", name)
        transform.put_if_specified(payload, "permissions", permissions)
        transform.put_if_specified(payload, "color", color)
        transform.put_if_specified(payload, "hoist", hoist)
        transform.put_if_specified(payload, "mentionable", mentionable)
        return await self.request(
            PATCH, "/guilds/{guild_id}/roles/{role_id}", guild_id=guild_id, role_id=role_id, json=payload, reason=reason
        )

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def delete_guild_role(self, guild_id: str, role_id: str, *, reason: str = unspecified.UNSPECIFIED) -> None:
        """
        Deletes a role from a given guild.

        Args:
            guild_id:
                The ID of the guild you want to remove the role from.
            role_id:
                The ID of the role you want to delete.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.errors.NotFound:
                If either the guild or the role aren't found.
            hikari.errors.Forbidden:
                If you lack the `MANAGE_ROLES` permission or are not in the guild.
        """
        return await self.request(
            DELETE, "/guilds/{guild_id}/roles/{role_id}", guild_id=guild_id, role_id=role_id, reason=reason
        )

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def get_guild_prune_count(self, guild_id: str, days: int) -> int:
        """
        Gets the estimated prune count for a given guild.

        Args:
            guild_id:
                The ID of the guild you want to get the count for.
            days:
                The number of days to count prune for (at least 1).

        Returns:
            A dict containing a `pruned` key which holds the estimated prune count.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you lack the `KICK_MEMBERS` or you are not in the guild.
            hikari.errors.BadRequest:
                If you pass an invalid amount of days.
        """
        return await self.request(GET, "/guilds/{guild_id}/prune", guild_id=guild_id, query={"days": days})

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def begin_guild_prune(
        self, guild_id: str, days: int, compute_prune_count: bool = False, reason: str = unspecified.UNSPECIFIED
    ) -> typing.Optional[int]:
        """
        Prunes members of a given guild based on the number of inactive days.

        Args:
            guild_id:
                The ID of the guild you want to prune member of.
            days:
                The number of inactivity days you want to use as filter.
            compute_prune_count:
                Whether a count of pruned members is returned or not. Discouraged for large guilds.
            reason:|
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Returns:
            Either None or an object containing a `pruned` key which holds the pruned member count.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found:
            hikari.errors.Forbidden:
                If you lack the `KICK_MEMBER` permission or are not in the guild.
            hikari.errors.BadRequest:
                If you provide invalid values for the `days` and `compute_prune_count` fields.
        """
        query = {"days": days, "compute_prune_count": compute_prune_count}
        return await self.request(POST, "/guilds/{guild_id}/prune", guild_id=guild_id, query=query, reason=reason)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def get_guild_voice_regions(self, guild_id: str) -> typing.List[custom_types.DiscordObject]:
        """
        Gets the voice regions for a given guild.

        Args:
            guild_id:
                The ID of the guild to get the voice regions for.

        Returns:
            A list of voice region objects.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found:
            hikari.errors.Forbidden:
                If you are not in the guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/regions", guild_id=guild_id)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def get_guild_invites(self, guild_id: str) -> typing.List[custom_types.DiscordObject]:
        """
        Gets the invites for a given guild.

        Args:
            guild_id:
                The ID of the guild to get the invites for.

        Returns:
            A list of invite objects (with metadata).

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/invites", guild_id=guild_id)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def get_guild_integrations(self, guild_id: str) -> typing.List[custom_types.DiscordObject]:
        """
        Gets the integrations for a given guild.

        Args:
            guild_id:
                The ID of the guild to get the integrations for.

        Returns:
            A list of integration objects.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/integrations", guild_id=guild_id)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def create_guild_integration(
        self, guild_id: str, type_: str, integration_id: str, reason: str = unspecified.UNSPECIFIED
    ) -> None:
        """
        Creates an integrations for a given guild.

        Args:
            guild_id:
                The ID of the guild to create the integrations in.
            type_:
                The integration type string (e.g. "twitch").
            integration_id:
                The ID for the new integration.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Returns:
            The newly created integration object.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        payload = {"type": type_, "id": integration_id}
        return await self.request(
            POST, "/guilds/{guild_id}/integrations", guild_id=guild_id, json=payload, reason=reason
        )

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def modify_guild_integration(
        self,
        guild_id: str,
        integration_id: str,
        *,
        expire_behaviour: int = unspecified.UNSPECIFIED,
        expire_grace_period: int = unspecified.UNSPECIFIED,
        enable_emoticons: bool = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Edits an integrations for a given guild.

        Args:
            guild_id:
                The ID of the guild to which the integration belongs to.
            integration_id:
                The ID of the integration.
            expire_behaviour:
                The behaviour for when an integration subscription lapses.
            expire_grace_period:
                Time interval in seconds in which the integration will ignore lapsed subscriptions.
            enable_emoticons:
                Whether emoticons should be synced for this integration.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.errors.NotFound:
                If either the guild or the integration aren't found.
            hikari.errors.Forbidden:
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        payload = {
            "expire_behaviour": expire_behaviour,
            "expire_grace_period": expire_grace_period,
            "enable_emoticons": enable_emoticons,
        }
        return await self.request(
            PATCH,
            "/guilds/{guild_id}/integrations/{integration_id}",
            guild_id=guild_id,
            integration_id=integration_id,
            json=payload,
            reason=reason,
        )

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def delete_guild_integration(
        self, guild_id: str, integration_id: str, *, reason: str = unspecified.UNSPECIFIED
    ) -> None:
        """
        Deletes an integration for the given guild.

        Args:
            guild_id:
                The ID of the guild from which to delete an integration.
            integration_id:
                The ID of the integration to delete.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.errors.NotFound:
                If either the guild or the integration aren't found.
            hikari.errors.Forbidden:
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        return await self.request(
            DELETE,
            "/guilds/{guild_id}/integrations/{integration_id}",
            guild_id=guild_id,
            integration_id=integration_id,
            reason=reason,
        )

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def sync_guild_integration(self, guild_id: str, integration_id: str) -> None:
        """
        Syncs the given integration.

        Args:
            guild_id:
                The ID of the guild to which the integration belongs to.
            integration_id:
                The ID of the integration to sync.

         Raises:
            hikari.errors.NotFound:
                If either the guild or the integration aren't found.
            hikari.errors.Forbidden:
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        return await self.request(
            POST,
            "/guilds/{guild_id}/integrations/{integration_id}/sync",
            guild_id=guild_id,
            integration_id=integration_id,
        )

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def get_guild_embed(self, guild_id: str) -> custom_types.DiscordObject:
        """
        Gets the embed for a given guild.

        Args:
            guild_id:
                The ID of the guild to get the embed for.

        Returns:
            A guild embed object.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/embed", guild_id=guild_id)

    #: TODO: does this take a reason header?
    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def modify_guild_embed(
        self, guild_id: str, embed: custom_types.DiscordObject, reason: str = unspecified.UNSPECIFIED
    ) -> custom_types.DiscordObject:
        """
        Edits the embed for a given guild.

        Args:
            guild_id:
                The ID of the guild to edit the embed for.
            embed:
                The new embed object to be set.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Returns:
            The updated embed object.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        return await self.request(PATCH, "/guilds/{guild_id}/embed", guild_id=guild_id, json=embed, reason=reason)

    @meta.link_developer_portal(meta.APIResource.GUILD)
    async def get_guild_vanity_url(self, guild_id: str) -> str:
        """
        Gets the vanity URL for a given guild.

        Args:
            guild_id:
                The ID of the guild to get the vanity URL for.

        Returns:
            A partial invite object containing the vanity URL in the `code` field.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_GUILD` permission or are not in the guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/vanity-url", guild_id=guild_id)

    @meta.link_developer_portal(meta.APIResource.GUILD)
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
            This does not actually make any form of request, and shouldn't be awaited. Thus, it doesn't have rate limits
            either.

        Warning:
            The guild must have the widget enabled in the guild settings for this to be valid.
        """
        return f"{self.base_uri}/guilds/{guild_id}/widget.png?style={style}"

    @meta.link_developer_portal(meta.APIResource.INVITE)
    async def get_invite(
        self, invite_code: str, *, with_counts: bool = unspecified.UNSPECIFIED
    ) -> custom_types.DiscordObject:
        """
        Gets the given invite.

        Args:
            invite_code:
                The ID for wanted invite.
            with_counts:
                If `True`, attempt to count the number of times the invite has been used, otherwise (and as the
                default), do not try to track this information.

        Returns:
            The requested invite object.

        Raises:
            hikari.errors.NotFound:
                If the invite is not found.
        """
        payload = {}
        transform.put_if_specified(payload, "with_counts", with_counts)
        return await self.request(GET, "/invites/{invite_code}", invite_code=invite_code, query=payload)

    @meta.link_developer_portal(meta.APIResource.INVITE)
    async def delete_invite(
        self, invite_code: str, *, reason: str = unspecified.UNSPECIFIED
    ) -> custom_types.DiscordObject:
        """
        Deletes a given invite.

        Args:
            invite_code:
                The ID for the invite to be deleted.
            reason:
                an optional audit log reason explaining why the change was made.

        Returns:
            The deleted invite object.

        Raises:
            hikari.errors.NotFound:
                If the invite is not found.
            hikari.errors.Forbidden
                If you lack either `MANAGE_CHANNELS` on the channel the invite belongs to or `MANAGE_GUILD` for
                guild-global delete.
        """
        return await self.request(DELETE, "/invites/{invite_code}", invite_code=invite_code, reason=reason)

    ##########
    # OAUTH2 #
    ##########

    @meta.link_developer_portal(meta.APIResource.OAUTH2)
    async def get_current_application_info(self) -> custom_types.DiscordObject:
        """
        Get the current application information.

        Returns:
             An application info object.
        """
        return await self.request(GET, "/oauth2/applications/@me")

    ##########
    # USERS  #
    ##########

    @meta.link_developer_portal(meta.APIResource.USER)
    async def get_current_user(self) -> custom_types.DiscordObject:
        """
        Gets the currently the user that is represented by token given to the client.

        Returns:
            The current user object.
        """
        return await self.request(GET, "/users/@me")

    @meta.link_developer_portal(meta.APIResource.USER)
    async def get_user(self, user_id: str) -> custom_types.DiscordObject:
        """
        Gets a given user.

        Args:
            user_id:
                The ID of the user to get.

        Returns:
            The requested user object.

        Raises:
            hikari.errors.NotFound:
                If the user is not found.
        """
        return await self.request(GET, "/users/{user_id}", user_id=user_id)

    @meta.link_developer_portal(meta.APIResource.USER)
    async def modify_current_user(
        self, *, username: str = unspecified.UNSPECIFIED, avatar: bytes = unspecified.UNSPECIFIED
    ) -> custom_types.DiscordObject:
        """
        Edits the current user. If any arguments are unspecified, then that subject is not changed on Discord.

        Args:
            username:
                The new username string.
            avatar:
                The new avatar image in bytes form.

        Returns:
            The updated user object.

        Raises:
            hikari.errors.BadRequest:
                If you pass username longer than the limit (2-32) or an invalid image.
        """
        payload = {}
        transform.put_if_specified(payload, "username", username)
        transform.put_if_specified(payload, "avatar", avatar)
        return await self.request(PATCH, "/users/@me", json=payload)

    @meta.link_developer_portal(meta.APIResource.USER)
    async def get_current_user_guilds(
        self,
        *,
        before: str = unspecified.UNSPECIFIED,
        after: str = unspecified.UNSPECIFIED,
        limit: int = unspecified.UNSPECIFIED,
    ) -> typing.List[custom_types.DiscordObject]:
        """
        Gets the guilds the current user is in.

        Returns:
            A list of partial guild objects.

        Raises:
            hikari.errors.BadRequest:
                If you pass both `before` and `after`.
        """
        query = {}
        transform.put_if_specified(query, "before", before)
        transform.put_if_specified(query, "after", after)
        transform.put_if_specified(query, "limit", limit)
        return await self.request(GET, "/users/@me/guilds", query=query)

    @meta.link_developer_portal(meta.APIResource.USER)
    async def leave_guild(self, guild_id: str) -> None:
        """
        Makes the current user leave a given guild.

        Args:
            guild_id:
                The ID of the guild to leave.

         Raises:
            hikari.errors.NotFound:
                If the guild is not found.
        """
        return await self.request(DELETE, "/users/@me/guilds/{guild_id}", guild_id=guild_id)

    @meta.link_developer_portal(meta.APIResource.USER)
    async def create_dm(self, recipient_id: str) -> custom_types.DiscordObject:
        """
        Creates a new DM channel with a given user.

        Args:
            recipient_id:
                The ID of the user to create the new DM channel with.

        Returns:
            The newly created DM channel object.

        Raises:
            hikari.errors.NotFound:
                If the recipient is not found.
        """
        return await self.request(POST, "/users/@me/channels", json={"recipient_id": recipient_id})

    @meta.link_developer_portal(meta.APIResource.VOICE)
    async def list_voice_regions(self) -> typing.List[custom_types.DiscordObject]:
        """
        Get the voice regions that are available.

        Returns:
            A list of voice regions available

        Note:
            This does not include VIP servers.
        """

        return await self.request(GET, "/voice/regions")

    @meta.link_developer_portal(meta.APIResource.WEBHOOK)
    async def create_webhook(
        self,
        channel_id: str,
        name: str,
        *,
        avatar: bytes = unspecified.UNSPECIFIED,
        reason: str = unspecified.UNSPECIFIED,
    ) -> custom_types.DiscordObject:
        """
        Creates a webhook for a given channel.

        Args:
            channel_id:
                The ID of the channel for webhook to be created in.
            name:
                The webhook's name string.
            avatar:
                The avatar image in bytes form.
            reason:
                an optional audit log reason explaining why the change was made.

        Returns:
            The newly created webhook object.

        Raises:
            hikari.errors.NotFound:
                If the channel is not found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_WEBHOOKS` permission or can not see the given channel.
            hikari.errors.BadRequest:
                If the avatar image is too big or the format is invalid.
        """
        payload = {"name": name}
        transform.put_if_specified(payload, "avatar", avatar)
        return await self.request(
            POST, "/channels/{channel_id}/webhooks", channel_id=channel_id, json=payload, reason=reason
        )

    @meta.link_developer_portal(meta.APIResource.WEBHOOK)
    async def get_channel_webhooks(self, channel_id: str) -> typing.List[custom_types.DiscordObject]:
        """
        Gets all webhooks from a given channel.

        Args:
            channel_id:
                The ID of the channel to get the webhooks from.

        Returns:
            A list of webhook objects for the give channel.

        Raises:
            hikari.errors.NotFound:
                If the channel is not found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_WEBHOOKS` permission or can not see the given channel.
        """
        return await self.request(GET, "/channels/{channel_id}/webhooks", channel_id=channel_id)

    @meta.link_developer_portal(meta.APIResource.WEBHOOK)
    async def get_guild_webhooks(self, guild_id: str) -> typing.List[custom_types.DiscordObject]:
        """
        Gets all webhooks for a given guild.

        Args:
            guild_id:
                The ID for the guild to get the webhooks from.

        Returns:
            A list of webhook objects for the given guild.

        Raises:
            hikari.errors.NotFound:
                If the guild is not found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_WEBHOOKS` permission or aren't a member of the given guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/webhooks", guild_id=guild_id)

    @meta.link_developer_portal(meta.APIResource.WEBHOOK)
    async def get_webhook(self, webhook_id: str) -> custom_types.DiscordObject:
        """
        Gets a given webhook.

        Args:
            webhook_id:
                The ID of the webhook to get.

        Returns:
            The requested webhook object.

        Raises:
            hikari.errors.NotFound:
                If the webhook is not found.
        """
        return await self.request(GET, "/webhooks/{webhook_id}", webhook_id=webhook_id)

    @meta.link_developer_portal(meta.APIResource.WEBHOOK)
    async def modify_webhook(
        self, webhook_id: str, name: str, avatar: bytes, channel_id: str, reason: str = unspecified.UNSPECIFIED
    ) -> custom_types.DiscordObject:
        """
        Edits a given webhook.

        Args:
            webhook_id:
                The ID of the webhook to edit.
            name:
                The new name string.
            avatar:
                The new avatar image in bytes form.
            channel_id:
                The ID of the new channel the given webhook should be moved to.
            reason:
                an optional audit log reason explaining why the change was made.

        Returns:
            The updated webhook object.

        Raises:
            hikari.errors.NotFound:
                If either the webhook or the channel aren't found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_WEBHOOKS` permission or aren't a member of the guild this webhook belongs
                to.
        """
        payload = {}
        transform.put_if_specified(payload, "name", name)
        transform.put_if_specified(payload, "avatar", avatar)
        transform.put_if_specified(payload, "channel_id", channel_id)
        return await self.request(PATCH, "/webhooks/{webhook_id}", webhook_id=webhook_id, json=payload, reason=reason)

    @meta.link_developer_portal(meta.APIResource.WEBHOOK)
    async def delete_webhook(self, webhook_id: str, *, reason: str = unspecified.UNSPECIFIED) -> None:
        """
        Deletes a given webhook.

        Args:
            webhook_id:
                The ID of the webhook to delete
            reason:
                an optional audit log reason explaining why the change was made.

        Raises:
            hikari.errors.NotFound:
                If the webhook is not found.
            hikari.errors.Forbidden:
                If you're not the webhook owner.
        """
        return await self.request(DELETE, "/webhooks/{webhook_id}", webhook_id=webhook_id, reason=reason)
