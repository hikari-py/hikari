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

DELETE = "delete"
PATCH = "patch"
GET = "get"
POST = "post"
PUT = "put"


class HTTPClient(base.BaseHTTPClient):
    """
    Combination of all components for API handling logic for the V7 Discord HTTP API.
    """

    __slots__ = []

    @_utils.link_developer_portal(_utils.APIResource.GATEWAY)
    async def get_gateway(self) -> str:
        """
        Returns:
            A static URL to use to connect to the gateway with.
        """
        result = await self.request(GET, "/gateway")
        return result["url"]

    @_utils.link_developer_portal(_utils.APIResource.GATEWAY)
    async def get_gateway_bot(self) -> _utils.DiscordObject:
        """
        Returns:
            An object containing a `url` to connect to, an :class:`int` number of shards recommended to use
            for connecting, and a `session_start_limit` object.

        Note:
            Unlike `get_gateway`, this requires a valid token to work.
        """
        return await self.request(GET, "/gateway/bot")

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
            hikari.errors.Forbidden:
                if you lack the given permissions to view an audit log.
            hikari.errors.NotFound:
                if the guild does not exist.
        """
        query = {}
        _utils.put_if_specified(query, "user_id", user_id)
        _utils.put_if_specified(query, "action_type", action_type)
        _utils.put_if_specified(query, "limit", limit)
        return await self.request(GET, "/guilds/{guild_id}/audit-logs", query=query, guild_id=guild_id)

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
        return await self.request(GET, "/channels/{channel_id}", channel_id=channel_id)

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
        payload = {}
        _utils.put_if_specified(payload, "position", position)
        _utils.put_if_specified(payload, "topic", topic)
        _utils.put_if_specified(payload, "nsfw", nsfw)
        _utils.put_if_specified(payload, "rate_limit_per_user", rate_limit_per_user)
        _utils.put_if_specified(payload, "bitrate", bitrate)
        _utils.put_if_specified(payload, "user_limit", user_limit)
        _utils.put_if_specified(payload, "permission_overwrites", permission_overwrites)
        _utils.put_if_specified(payload, "parent_id", parent_id)
        return await self.request(PATCH, "/channels/{channel_id}", json=payload, channel_id=channel_id)

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL, "deleteclose-channel")  # nonstandard spelling in URI
    async def delete_close_channel(self, channel_id: str) -> None:
        """
        Delete the given channel ID, or if it is a DM, close it.

        Args:
            channel_id:
                The channel ID to delete, or the user ID of the direct message to close.

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
        await self.request(DELETE, "/channels/{channel_id}", channel_id=channel_id)

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
        _utils.put_if_specified(payload, "limit", limit)
        _utils.put_if_specified(payload, "before", before)
        _utils.put_if_specified(payload, "after", after)
        _utils.put_if_specified(payload, "around", around)
        return await self.request(GET, "/channels/{channel_id}/messages", channel_id=channel_id, json=payload)

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def get_channel_message(self, channel_id: str, message_id: str) -> _utils.DiscordObject:
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
            POST,
            "/channels/{channel_id}/messages",
            channel_id=channel_id,
            re_seekable_resources=re_seekable_resources,
            data=form,
        )

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
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
                emoji, or it can be a snowflake ID for a custom emoji.

        Raises:
            hikari.errors.Forbidden:
                if this is the first reaction using this specific emoji on this message and you lack the `ADD_REACTIONS`
                permission. If you lack `READ_MESSAGE_HISTORY`, this may also raise this error.
            hikari.errors.NotFound:
                if the channel or message is not found, or if the emoji is not found.
        """
        await self.request(
            PUT,
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me",
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
        )

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
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

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
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

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def get_reactions(
        self,
        channel_id: str,
        message_id: str,
        emoji: str,
        *,
        before: str = _utils.unspecified,
        after: str = _utils.unspecified,
        limit: int = _utils.unspecified,
    ) -> typing.List[_utils.DiscordObject]:
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
        _utils.put_if_specified(payload, "before", before)
        _utils.put_if_specified(payload, "after", after)
        _utils.put_if_specified(payload, "limit", limit)
        return await self.request(
            GET,
            "/channels/{channel_id}/messages/{message_id}/reactions/{emoji}",
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
            json=payload,
        )

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL, "/resources/channel#delete-all-reactions")
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

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        *,
        content: str = _utils.unspecified,
        embed: _utils.DiscordObject = _utils.unspecified,
    ) -> _utils.DiscordObject:
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
        _utils.put_if_specified(payload, "content", content)
        _utils.put_if_specified(payload, "embed", embed)
        return await self.request(
            PATCH,
            "/channels/{channel_id}/messages/{message_id}",
            channel_id=channel_id,
            message_id=message_id,
            json=payload,
        )

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
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

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
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

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def edit_channel_permissions(
        self, channel_id: str, overwrite_id: str, allow: int, deny: int, type_: str
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
        """
        payload = {"allow": allow, "deny": deny, "type": type_}
        await self.request(
            PUT,
            "/channels/{channel_id}/permissions/{overwrite_id}",
            channel_id=channel_id,
            overwrite_id=overwrite_id,
            json=payload,
        )

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def get_channel_invites(self, channel_id: str) -> typing.List[_utils.DiscordObject]:
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
        _utils.put_if_specified(payload, "max_age", max_age)
        _utils.put_if_specified(payload, "max_uses", max_uses)
        _utils.put_if_specified(payload, "temporary", temporary)
        _utils.put_if_specified(payload, "unique", unique)
        return await self.request(POST, "/channels/{channel_id}/invites", json=payload, channel_id=channel_id)

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
    async def delete_channel_permission(self, channel_id: str, overwrite_id: str) -> None:
        """
        Delete a channel permission overwrite for a user or a role in a channel.

        Args:
            channel_id:
                the channel ID to delete from.
            overwrite_id:
                the override ID to remove.

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
        )

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
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
                if you are not in the guild the channel is in; TODO: confirm this.
        """
        await self.request(POST, "/channels/{channel_id}/typing", channel_id=channel_id)

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
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

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
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

    @_utils.link_developer_portal(_utils.APIResource.CHANNEL)
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

    @_utils.link_developer_portal(_utils.APIResource.EMOJI)
    async def list_guild_emojis(self, guild_id: str) -> typing.List[_utils.DiscordObject]:
        """
        Gets emojis for a given guild ID.

        Args:
            guild_id:
                The guild ID to get the emojis for.

        Returns:
            A list of emoji objects.

        Raises:
            hikari.errors.NotFound:
                If the guild isn't found.
            hikari.errors.Forbidden:
                If you aren't a member of said guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/emojis", guild_id=guild_id)

    @_utils.link_developer_portal(_utils.APIResource.EMOJI)
    async def get_guild_emoji(self, guild_id: str, emoji_id: str) -> _utils.DiscordObject:
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

    @_utils.link_developer_portal(_utils.APIResource.EMOJI)
    async def create_guild_emoji(
        self, guild_id: str, name: str, image: bytes, roles: typing.List[str]
    ) -> _utils.DiscordObject:
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

        Returns:
            The newly created emoji object.

        Raises:
            hikari.errors.NotFound:
                If the guild isn't found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_EMOJIS` permission or aren't a member of said guild.
            hikari.errors.BadRequest:
                If you attempt to upload an image larger than 256kb, an empty image or an invalid image format.
        """
        payload = {"name": name, "image": image, "roles": roles}
        return await self.request(POST, "/guilds/{guild_id}/emojis", guild_id=guild_id, json=payload)

    @_utils.link_developer_portal(_utils.APIResource.EMOJI)
    async def modify_guild_emoji(
        self, guild_id: str, emoji_id: str, name: str, roles: typing.List[str]
    ) -> _utils.DiscordObject:
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
            PATCH, "/guilds/{guild_id}/emojis/{emoji_id}", guild_id=guild_id, emoji_id=emoji_id, json=payload
        )

    @_utils.link_developer_portal(_utils.APIResource.EMOJI)
    async def delete_guild_emoji(self, guild_id: str, emoji_id: str) -> None:
        """
        Deletes an emoji from a given guild

        Args:
            guild_id:
                The ID of the guild to delete the emoji from
            emoji_id:
                The ID of the emoji to be deleted

        Returns:
            None

        Raises:
            hikari.errors.NotFound:
                If either the guild or the emoji aren't found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_EMOJIS` permission or aren't a member of said guild.
        """
        return await self.request(DELETE, "/guilds/{guild_id}/emojis/{emoji_id}", guild_id=guild_id, emoji_id=emoji_id)

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
        type_: int = _utils.unspecified,
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
    async def create_guild_integration(self, guild_id: str, type_: str, integration_id: str) -> None:
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
            This does not actually make any form of request, and shouldn't be awaited. Thus, it doesn't have rate limits
            either.

        Warning:
            The guild must have the widget enabled in the guild settings for this to be valid.
        """
        return f"{self.base_uri}/guilds/{guild_id}/widget.png?style={style}"

    @_utils.link_developer_portal(_utils.APIResource.INVITE)
    async def get_invite(self, invite_code: str, *, with_counts: bool = _utils.unspecified) -> _utils.DiscordObject:
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
                If the invite isn't found.
        """
        payload = {}
        _utils.put_if_specified(payload, "with_counts", with_counts)
        return await self.request(GET, "/invites/{invite_code}", invite_code=invite_code, query=payload)

    @_utils.link_developer_portal(_utils.APIResource.INVITE)
    async def delete_invite(self, invite_code: str) -> _utils.DiscordObject:
        """
        Deletes a given invite.

        Args:
            invite_code:
                The ID for the invite to be deleted.

        Returns:
            The deleted invite object.

        Raises:
            hikari.errors.NotFound:
                If the invite isn't found.
            hikari.errors.Forbidden
                If you lack either `MANAGE_CHANNELS` on the channel the invite belongs to or `MANAGE_GUILD` for 
                guild-global delete.
        """
        return await self.request(DELETE, "/invites/{invite_code}", invite_code=invite_code)

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
        return await self.request(GET, "/oauth2/applications/@me")

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

    @_utils.link_developer_portal(_utils.APIResource.VOICE)
    async def list_voice_regions(self) -> typing.List[_utils.DiscordObject]:
        """
        Get the voice regions that are available.

        Returns:
            A list of voice regions available

        Note:
            This does not include VIP servers.
        """

        return await self.request(GET, "/voice/regions")

    @_utils.link_developer_portal(_utils.APIResource.WEBHOOK)
    async def create_webhook(
        self, channel_id: str, name: str, *, avatar: bytes = _utils.unspecified
    ) -> _utils.DiscordObject:
        """
        Creates a webhook for a given channel.

        Args:
            channel_id:
                The ID of the channel for webhook to be created in.
            name:
                The webhook's name string.
            avatar:
                The avatar image in bytes form.

        Returns:
            The newly created webhook object.

        Raises:
            hikari.errors.NotFound:
                If the channel isn't found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_WEBHOOKS` permission or can't see the given channel.
            hikari.errors.BadRequest:
                If the avatar image is too big or the format is invaid.
        """
        payload = {"name": name}
        _utils.put_if_specified(payload, "avatar", avatar)
        return await self.request(POST, "/channels/{channel_id}/webhooks", channel_id=channel_id, json=payload)

    @_utils.link_developer_portal(_utils.APIResource.WEBHOOK)
    async def get_channel_webhooks(self, channel_id: str) -> typing.List[_utils.DiscordObject]:
        """
        Gets all webhooks from a given channel.

        Args:
            channel_id:
                The ID of the channel to get the webhooks from.

        Returns:
            A list of webhook objects for the give channel.

        Raises:
            hikari.errors.NotFound:
                If the channel isn't found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_WEBHOOKS` permission or can't see the given channel.
        """
        return await self.request(GET, "/channels/{channel_id}/webhooks", channel_id=channel_id)

    @_utils.link_developer_portal(_utils.APIResource.WEBHOOK)
    async def get_guild_webhooks(self, guild_id: str) -> typing.List[_utils.DiscordObject]:
        """
        Gets all webhooks for a given guild.

        Args:
            guild_id:
                The ID for the guild to get the webhooks from.

        Returns:
            A list of webhook objects for the given guild.

        Raises:
            hikari.errors.NotFound:
                If the guild isn't found.
            hikari.errors.Forbidden:
                If you either lack the `MANAGE_WEBHOOKS` permission or aren't a member of the given guild.
        """
        return await self.request(GET, "/guilds/{guild_id}/webhooks", guild_id=guild_id)

    @_utils.link_developer_portal(_utils.APIResource.WEBHOOK)
    async def get_webhook(self, webhook_id: str) -> _utils.DiscordObject:
        """
        Gets a given webhook.

        Args:
            webhook_id:
                The ID of the webhook to get.

        Returns:
            The requested webhook object.

        Raises:
            hikari.errors.NotFound:
                If the webhook isn't found.
        """
        return await self.request(GET, "/webhooks/{webhook_id}", webhook_id=webhook_id)

    @_utils.link_developer_portal(_utils.APIResource.WEBHOOK)
    async def modify_webhook(self, webhook_id: str, name: str, avatar: bytes, channel_id: str) -> _utils.DiscordObject:
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
        _utils.put_if_specified(payload, "name", name)
        _utils.put_if_specified(payload, "avatar", avatar)
        _utils.put_if_specified(payload, "channel_id", channel_id)
        return await self.request(PATCH, "/webhooks/{webhook_id}", webhook_id=webhook_id, json=payload)

    @_utils.link_developer_portal(_utils.APIResource.WEBHOOK)
    async def delete_webhook(self, webhook_id: str) -> None:
        """
        Deletes a given webhook.

        Args:
            webhook_id:
                The ID of the webhook to delete.

        Returns:
            None

        Raises:
            hikari.errors.NotFound:
                If the webhook isn't found.
            hikari.errors.Forbidden:
                If you're not the webhook owner.
        """
        return await self.request(DELETE, "/webhooks/{webhook_id}", webhook_id=webhook_id)
