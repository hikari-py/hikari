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
"""Provides an interface for REST API implementations to follow."""
from __future__ import annotations

__all__: typing.List[str] = ["ConnectorFactory", "RESTClient"]

import abc
import typing

from hikari import traits
from hikari import undefined

if typing.TYPE_CHECKING:

    import aiohttp

    from hikari import applications
    from hikari import audit_logs
    from hikari import channels as channels_
    from hikari import colors
    from hikari import embeds as embeds_
    from hikari import emojis
    from hikari import files
    from hikari import guilds
    from hikari import invites
    from hikari import iterators
    from hikari import messages as messages_
    from hikari import permissions as permissions_
    from hikari import sessions
    from hikari import snowflakes
    from hikari import templates
    from hikari import users
    from hikari import voices
    from hikari import webhooks
    from hikari.api import special_endpoints
    from hikari.internal import time


class ConnectorFactory(abc.ABC):
    """Provider of a connector."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    async def close(self) -> None:
        """Close any resources if they exist."""

    @abc.abstractmethod
    def acquire(self) -> aiohttp.BaseConnector:
        """Acquire the connector."""


class RESTClient(traits.NetworkSettingsAware, abc.ABC):
    """Interface for functionality that a REST API implementation provides."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the client session."""

    @abc.abstractmethod
    async def fetch_channel(
        self, channel: snowflakes.SnowflakeishOr[channels_.PartialChannel]
    ) -> channels_.PartialChannel:
        """Fetch a channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            The channel to fetch. This may be the object or the ID of an
            existing channel.

        Returns
        -------
        hikari.channels.PartialChannel
            The channel. This will be a _derivative_ of
            `hikari.channels.PartialChannel`, depending on the type of
            channel you request for.

            This means that you may get one of
            `hikari.channels.DMChannel`,
            `hikari.channels.GroupDMChannel`,
            `hikari.channels.GuildTextChannel`,
            `hikari.channels.GuildVoiceChannel`,
            `hikari.channels.GuildStoreChannel`,
            `hikari.channels.GuildNewsChannel`.

            Likewise, the `hikari.channels.GuildChannel` can be used to
            determine if a channel is guild-bound, and
            `hikari.channels.TextChannel` can be used to determine
            if the channel provides textual functionality to the application.

            You can check for these using the `builtins.isinstance`
            builtin function.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `READ_MESSAGES` permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_channel(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
        /,
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        parent_category: undefined.UndefinedOr[
            snowflakes.SnowflakeishOr[channels_.GuildCategory]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.PartialChannel:
        """Edit a channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildChannel]
            The channel to edit. This may be the object or the ID of an
            existing channel.

        Other Parameters
        ----------------
        name : hikari.undefined.UndefinedOr[[builtins.str]
            If provided, the new name for the channel.
        position : hikari.undefined.UndefinedOr[[builtins.int]
            If provided, the new position for the channel.
        topic : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the new topic for the channel.
        nsfw : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the channel should be marked as NSFW or not.
        bitrate : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the new bitrate for the channel.
        user_limit : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the new user limit in the channel.
        rate_limit_per_user : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the new rate limit per user in the channel.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the new permission overwrites for the channel.
        parent_category : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildCategory]]
            If provided, the new guild category for the channel.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.PartialChannel
            The edited channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing permissions to edit the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def follow_channel(
        self,
        news_channel: snowflakes.SnowflakeishOr[channels_.GuildNewsChannel],
        target_channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
    ) -> channels_.ChannelFollow:
        """Follow a news channel to send messages to a target channel.

        Parameters
        ----------
        news_channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildNewsChannel]
            The object or ID of the news channel to follow.
        target_channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildChannel]
            The object or ID of the channel to target.

        Returns
        -------
        hikari.channels.ChannelFollow
            Information about the new relationship that was made.

        Raises
        ------
        hikari.errors.BadRequestError
            If you try to follow a channel that's not a news channel or if the
            target channel has reached it's webhook limit, which is 10 at the
            time of writing.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_WEBHOOKS` permission in the target
            channel or are missing the `VIEW_CHANNEL` permission in the origin
            channel.
        hikari.errors.NotFoundError
            If the origin or target channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_channel(self, channel: snowflakes.SnowflakeishOr[channels_.PartialChannel]) -> None:
        """Delete a channel in a guild, or close a DM.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            The channel to delete. This may be the object or the ID of an
            existing channel.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_CHANNEL` permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.

        !!! note
            For Public servers, the set 'Rules' or 'Guidelines' channels and the
            'Public Server Updates' channel cannot be deleted.
        """

    @typing.overload
    @abc.abstractmethod
    async def edit_permission_overwrites(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
        target: typing.Union[channels_.PermissionOverwrite, users.PartialUser, guilds.PartialRole],
        *,
        allow: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        deny: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Edit permissions for a target entity."""

    @typing.overload
    @abc.abstractmethod
    async def edit_permission_overwrites(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
        target: snowflakes.Snowflakeish,
        *,
        target_type: channels_.PermissionOverwriteType,
        allow: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        deny: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Edit permissions for a given entity ID and type."""

    @abc.abstractmethod
    async def edit_permission_overwrites(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
        target: typing.Union[
            snowflakes.Snowflakeish, users.PartialUser, guilds.PartialRole, channels_.PermissionOverwrite
        ],
        *,
        target_type: undefined.UndefinedOr[channels_.PermissionOverwriteType] = undefined.UNDEFINED,
        allow: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        deny: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Edit permissions for a specific entity in the given guild channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildChannel]
            The channel to edit a permission overwrite in. This may be the
            object, or the ID of an existing channel.
        target : typing.Union[hikari.users.PartialUser, hikari.guilds.PartialRole, hikari.channels.PermissionOverwrite, hikari.snowflakes.Snowflakeish]
            The channel overwrite to edit. This may be the object or the ID of an
            existing overwrite.

        Other Parameters
        ----------------
        target_type : hikari.undefined.UndefinedOr[hikari.channels.PermissionOverwriteType]
            If provided, the type of the target to update. If unset, will attempt to get
            the type from `target`.
        allow : hikari.undefined.UndefinedOr[hikari.permissions.Permissions]
            If provided, the new vale of all allowed permissions.
        deny : hikari.undefined.UndefinedOr[hikari.permissions.Permissions]
            If provided, the new vale of all disallowed permissions.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        builtins.TypeError
            If `target_type` is unset and we were unable to determine the type
            from `target`.
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_PERMISSIONS` permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found or the target is not found if it is
            a role.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def delete_permission_overwrite(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
        target: snowflakes.SnowflakeishOr[
            typing.Union[channels_.PermissionOverwrite, guilds.PartialRole, users.PartialUser, snowflakes.Snowflakeish]
        ],
    ) -> None:
        """Delete a custom permission for an entity in a given guild channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildChannel]
            The channel to delete a permission overwrite in. This may be the
            object, or the ID of an existing channel.
        target : typing.Union[hikari.users.PartialUser, hikari.guilds.PartialRole, hikari.channels.PermissionOverwrite, hikari.snowflakes.Snowflakeish]
            The channel overwrite to delete.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_PERMISSIONS` permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found or the target is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def fetch_channel_invites(
        self, channel: snowflakes.SnowflakeishOr[channels_.GuildChannel]
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        """Fetch all invites pointing to the given guild channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildChannel]
            The channel to fetch the invites from. This may be a channel
            object, or the ID of an existing channel.

        Returns
        -------
        typing.Sequence[hikari.invites.InviteWithMetadata]
            The invites pointing to the given guild channel.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_CHANNEL` permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found in any guilds you are a member of.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_invite(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
        *,
        max_age: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        max_uses: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        temporary: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        unique: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        target_user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        target_user_type: undefined.UndefinedOr[invites.TargetUserType] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> invites.InviteWithMetadata:
        """Create an invite to the given guild channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildChannel]
            The channel to create a invite for. This may be the object
            or the ID of an existing channel.

        Other Parameters
        ----------------
        max_age : hikari.undefined.UndefinedOr[typing.Union[datetime.timedelta, builtins.float, builtins.int]]
            If provided, the duration of the invite before expiry.
        max_uses : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the max uses the invite can have.
        temporary : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the invite only grants temporary membership.
        unique : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the invite should be unique.
        target_user : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]]
            If provided, the target user id for this invite. This may be the
            object or the ID of an existing user.
        target_user_type : hikari.undefined.UndefinedOr[hikari.invites.TargetUserType]
            If provided, the type of target user for this invite.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.invites.InviteWithMetadata
            The invite to the given guild channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_CHANNELS` permission.
        hikari.errors.NotFoundError
            If the channel is not found, or if the target user does not exist,
            if provided.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    def trigger_typing(
        self, channel: snowflakes.SnowflakeishOr[channels_.TextChannel]
    ) -> special_endpoints.TypingIndicator:
        """Trigger typing in a text channel.

        The result of this call can be awaited to trigger typing once, or
        can be used as an async context manager to continually type until the
        context manager is left.

        Examples
        --------
        ```py
        # Trigger typing just once.
        await rest.trigger_typing(channel)

        # Trigger typing repeatedly for 1 minute.
        async with rest.trigger_typing(channel):
            await asyncio.sleep(60)
        ```

        !!! warning
            Sending a message to the channel will cause the typing indicator
            to disappear until it is re-triggered.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel to trigger typing in. This may be the object or
            the ID of an existing channel.

        Returns
        -------
        hikari.api.special_endpoints.TypingIndicator
            A typing indicator to use.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `SEND_MESSAGES` in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.

        !!! note
            The exceptions on this endpoint will only be raised once the result
            is awaited or iterated over. Invoking this function itself will
            not raise any of the above types.
        """

    @abc.abstractmethod
    async def fetch_pins(
        self, channel: snowflakes.SnowflakeishOr[channels_.TextChannel]
    ) -> typing.Sequence[messages_.Message]:
        """Fetch the pinned messages in this text channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel to fetch pins from. This may be the object or
            the ID of an existing channel.

        Returns
        -------
        typing.Sequence[hikari.messages.Message]
            The pinned messages in this text channel.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `READ_MESSAGES` in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def pin_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        """Pin an existing message in the given text channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel to pin a message in. This may be the object or
            the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to pin. This may be the object or the ID
            of an existing message.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_MESSAGES` in the channel.
        hikari.errors.NotFoundError
            If the channel is not found, or if the message does not exist in
            the given channel.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def unpin_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        """Unpin a given message from a given text channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel to unpin a message in. This may be the object or
            the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to unpin. This may be the object or the ID of an
            existing message.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_MESSAGES` permission.
        hikari.errors.NotFoundError
            If the channel is not found or the message is not a pinned message
            in the given channel.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_messages(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        *,
        before: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        after: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        around: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[messages_.Message]:
        """Browse the message history for a given text channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel to fetch messages in. This may be the object or
            the ID of an existing channel.

        Other Parameters
        ----------------
        before : hikari.undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[hikari.snowflakes.Unique]]
            If provided, fetch messages before this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake. This
            may be any other Discord entity that has an ID. In this case, the
            date the object was first created will be used.
        after : hikari.undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[hikari.snowflakes.Unique]]
            If provided, fetch messages after this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake. This
            may be any other Discord entity that has an ID. In this case, the
            date the object was first created will be used.
        around : hikari.undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[hikari.snowflakes.Unique]]
            If provided, fetch messages around this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake. This
            may be any other Discord entity that has an ID. In this case, the
            date the object was first created will be used.

        Returns
        -------
        hikari.iterators.LazyIterator[hikari.messages.Message]
            An iterator to fetch the messages.

        !!! note
            This call is not a coroutine function, it returns a special type of
            lazy iterator that will perform API calls as you iterate across it.
            See `hikari.iterators` for the full API for this iterator type.

        Raises
        ------
        builtins.TypeError
            If you specify more than one of `before`, `after`, `about`.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `READ_MESSAGE_HISTORY` in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.

        !!! note
            The exceptions on this endpoint (other than `builtins.TypeError`) will only
            be raised once the result is awaited or iterated over. Invoking
            this function itself will not raise anything (other than
            `builtins.TypeError`).
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def fetch_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> messages_.Message:
        """Fetch a specific message in the given text channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel to fetch messages in. This may be the object or
            the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to fetch. This may be the object or the ID of an
            existing channel.

        Returns
        -------
        hikari.messages.Message
            The requested message.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `READ_MESSAGE_HISTORY` in the channel.
        hikari.errors.NotFoundError
            If the channel is not found or the message is not found in the
            given text channel.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        nonce: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reply: undefined.UndefinedOr[snowflakes.SnowflakeishOr[messages_.PartialMessage]] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        """Create a message in the given channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel to create the message in.
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message contents. If
            `hikari.undefined.UNDEFINED`, then nothing will be sent
            in the content. Any other value here will be cast to a
            `builtins.str`.

            If this is a `hikari.embeds.Embed` and no `embed` kwarg is
            provided, then this will instead update the embed. This allows for
            simpler syntax when sending an embed alone.

            Likewise, if this is a `hikari.files.Resource`, then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.

        Other Parameters
        ----------------
        embed : hikari.undefined.UndefinedOr[hikari.embeds.Embed]
            If provided, the message embed.
        attachment : hikari.undefined.UndefinedOr[hikari.files.Resourceish],
            If provided, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.
        attachments : hikari.undefined.UndefinedOr[typing.Sequence[hikari.files.Resourceish]],
            If provided, the message attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        tts : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the message will be read out by a screen
            reader using Discord's TTS (text-to-speech) system.
        nonce : hikari.undefined.UndefinedOr[builtins.str]
            An arbitrary identifier to associate with the message. This
            can be used to identify it later in received events. If provided,
            this must be less than 32 bytes. If not provided, then
            a null value is placed on the message instead. All users can
            see this value.
        reply : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]]
            If provided, the message to reply to.
        mentions_everyone : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the message should parse @everyone/@here
            mentions.
        mentions_reply : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to mention the author of the message
            that is being replied to.

            This will not do anything if not being used with `reply`.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], builtins.bool]]
            If provided, and `builtins.True`, all user mentions will be detected.
            If provided, and `builtins.False`, all user mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            `hikari.snowflakes.Snowflake`, or
            `hikari.users.PartialUser` derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], builtins.bool]]
            If provided, and `builtins.True`, all role mentions will be detected.
            If provided, and `builtins.False`, all role mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            `hikari.snowflakes.Snowflake`, or
            `hikari.guilds.PartialRole` derivatives to enforce mentioning
            specific roles.

        !!! note
            Attachments can be passed as many different things, to aid in
            convenience.

            - If a `pathlib.PurePath` or `builtins.str` to a valid URL, the
                resource at the given URL will be streamed to Discord when
                sending the message. Subclasses of
                `hikari.files.WebResource` such as
                `hikari.files.URL`,
                `hikari.messages.Attachment`,
                `hikari.emojis.Emoji`,
                `EmbedResource`, etc will also be uploaded this way.
                This will use bit-inception, so only a small percentage of the
                resource will remain in memory at any one time, thus aiding in
                scalability.
            - If a `hikari.files.Bytes` is passed, or a `builtins.str`
                that contains a valid data URI is passed, then this is uploaded
                with a randomized file name if not provided.
            - If a `hikari.files.File`, `pathlib.PurePath` or
                `builtins.str` that is an absolute or relative path to a file
                on your file system is passed, then this resource is uploaded
                as an attachment using non-blocking code internally and streamed
                using bit-inception where possible. This depends on the
                type of `concurrent.futures.Executor` that is being used for
                the application (default is a thread pool which supports this
                behaviour).

        Returns
        -------
        hikari.messages.Message
            The created message.

        Raises
        ------
        builtins.ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        builtins.TypeError
            If both `attachment` and `attachments` are specified.
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no attachments or embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; too many attachments; attachments that are too large;
            invalid image URLs in embeds; users in `user_mentions` not being
            mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content; if `reply` is
            not found or not in the same channel as `channel`.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `SEND_MESSAGES` in the channel or the
            person you are trying to message has the DM's disabled.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.

        !!! warning
            You are expected to make a connection to the gateway and identify
            once before being able to use this endpoint for a bot.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def crosspost_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildNewsChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> messages_.Message:
        """Broadcast an announcement message.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildNewsChannel]
            The object or ID of the news channel to crosspost a message in.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The object or ID of the message to crosspost.

        Returns
        -------
        hikari.messages.Message
            The message object that was crossposted.

        Raises
        ------
        hikari.errors.BadRequestError
            If you tried to crosspost a message that has already been broadcast.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you try to crosspost a message by the current user without the
            `SEND_MESSAGES` permission for the target news channel or try to
            crosspost a message by another user without both the `SEND_MESSAGES`
            and `MANAGE_MESSAGES` permissions for the target channel.
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
        flags: undefined.UndefinedOr[messages_.MessageFlag] = undefined.UNDEFINED,
    ) -> messages_.Message:
        """Edit an existing message in a given channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel to create the message in. This may be
            the object or the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to edit. This may be the object or the ID
            of an existing message.
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message content to update with. If
            `hikari.undefined.UNDEFINED`, then the content will not
            be changed. If `builtins.None`, then the content will be removed.

            Any other value will be cast to a `builtins.str` before sending.

            If this is a `hikari.embeds.Embed` and no `embed` kwarg is
            provided, then this will instead update the embed. This allows for
            simpler syntax when sending an embed alone.

        Other Parameters
        ----------------
        embed : hikari.undefined.UndefinedNoneOr[hikari.embeds.Embed]
            If provided, the embed to set on the message. If
            `hikari.undefined.UNDEFINED`, the previous embed if
            present is not changed. If this is `builtins.None`, then the embed
            is removed if present. Otherwise, the new embed value that was
            provided will be used as the replacement.
        mentions_everyone : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, sanitation for `@everyone` mentions. If
            `hikari.undefined.UNDEFINED`, then the previous setting is
            not changed. If `builtins.True`, then `@everyone`/`@here` mentions
            in the message content will show up as mentioning everyone that can
            view the chat.
        mentions_reply : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to mention the author of the message
            that is being replied to.

            This will not do anything if `message` is not a reply message.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], builtins.bool]]
            If provided, sanitation for user mentions. If
            `hikari.undefined.UNDEFINED`, then the previous setting is
            not changed. If `builtins.True`, all valid user mentions will behave
            as mentions. If `builtins.False`, all valid user mentions will not
            behave as mentions.

            You may alternatively pass a collection of
            `hikari.snowflakes.Snowflake` user IDs, or
            `hikari.users.PartialUser`-derived objects.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], builtins.bool]]
            If provided, sanitation for role mentions. If
            `hikari.undefined.UNDEFINED`, then the previous setting is
            not changed. If `builtins.True`, all valid role mentions will behave
            as mentions. If `builtins.False`, all valid role mentions will not
            behave as mentions.

            You may alternatively pass a collection of
            `hikari.snowflakes.Snowflake` role IDs, or
            `hikari.guilds.PartialRole`-derived objects.
        flags : hikari.undefined.UndefinedOr[hikari.messages.MessageFlag]
            If provided, optional flags to set on the message. If
            `hikari.undefined.UNDEFINED`, then nothing is changed.

            Note that some flags may not be able to be set. Currently the only
            flags that can be set are `NONE` and `SUPPRESS_EMBEDS`. If you
            have `MANAGE_MESSAGES` permissions, you can use this call to
            suppress embeds on another user's message.

        !!! note
            Mentioning everyone, roles, or users in message edits currently
            will not send a push notification showing a new mention to people
            on Discord. It will still highlight in their chat as if they
            were mentioned, however.

        !!! note
            There is currently no documented way to clear attachments or edit
            attachments from a previously sent message on Discord's API. To
            do this, delete the message and re-send it. This also applies
            to embed attachments.

        !!! warning
            If you specify one of `mentions_everyone`, `user_mentions`, or
            `role_mentions`, then all others will default to `builtins.False`,
            even if they were enabled previously.

            This is a limitation of Discord's design. If in doubt, specify all three of
            them each time.

        !!! warning
            If the message was not sent by your user, the only parameter
            you may provide to this call is the `flags` parameter. Anything
            else will result in a `hikari.errors.ForbiddenError` being raised.

        Returns
        -------
        hikari.messages.Message
            The edited message.

        Raises
        ------
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no embeds; messages with more than 2000 characters
            in them, embeds that exceed one of the many embed
            limits; invalid image URLs in embeds; users in `user_mentions` not
            being mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `SEND_MESSAGES` in the channel; if you try to
            change the contents of another user's message; or if you try to edit
            the flags on another user's message without the `MANAGE_MESSAGES`
            permission.
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def delete_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        """Delete a given message in a given channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel to delete the message in. This may be
            the object or the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to delete. This may be the object or the ID of
            an existing message.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_MESSAGES`, and the message is
            not sent by you.
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_messages(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        /,
        *messages: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        """Bulk-delete messages from the channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel to bulk delete the messages in. This may be
            the object or the ID of an existing channel.
        *messages : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The messages to delete. This may be one or more
            objects or IDs of existing messages.

        !!! note
            This API endpoint will only be able to delete 100 messages
            at a time. For anything more than this, multiple requests will
            be executed one-after-the-other, since the rate limits for this
            endpoint do not favour more than one request per bucket.

            If one message is left over from chunking per 100 messages, or
            only one message is passed to this coroutine function, then the
            logic is expected to defer to `delete_message`. The implication
            of this is that the `delete_message` endpoint is ratelimited
            by a different bucket with different usage rates.

        !!! warning
            This endpoint is not atomic. If an error occurs midway through
            a bulk delete, you will **not** be able to revert any changes made
            up to this point.

        !!! warning
            Specifying any messages more than 14 days old will cause the call
            to fail, potentially with partial completion.

        Raises
        ------
        hikari.errors.BulkDeleteError
            An error containing the messages successfully deleted, and the
            messages that were not removed. The
            `builtins.BaseException.__cause__` of the exception will be the
            original error that terminated this process.
        """

    @abc.abstractmethod
    async def add_reaction(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        emoji: emojis.Emojiish,
    ) -> None:
        """Add a reaction emoji to a message in a given channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel where the message to add the reaction to is. This
            may be a `hikari.channels.TextChannel` or the ID of an existing
            channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to add a reaction to. This may be the
            object or the ID of an existing message.
        emoji : hikari.emojis.Emojiish
            The emoji to react to the message with.

        Raises
        ------
        hikari.errors.BadRequestError
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `ADD_REACTIONS` (this is only necessary if you
            are the first person to add the reaction).
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_my_reaction(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        emoji: emojis.Emojiish,
    ) -> None:
        """Delete a reaction that your application user created.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel where the message to delete the reaction from is.
            This may be the object or the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to delete a reaction from. This may be the
            object or the ID of an existing message.
        emoji : hikari.emojis.Emojiish
            The emoji to remove your reaction from.

        Raises
        ------
        hikari.errors.BadRequestError
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_all_reactions_for_emoji(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        emoji: emojis.Emojiish,
    ) -> None:
        """Delete all reactions for a single emoji on a given message.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel where the message to delete the reactions from is.
            This may be the object or the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to delete a reactions from. This may be the
            object or the ID of an existing message.
        emoji : hikari.emojis.Emojiish
            The emoji to delete all reactions from.

        Raises
        ------
        hikari.errors.BadRequestError
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_MESSAGES` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_reaction(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        emoji: emojis.Emojiish,
        user: snowflakes.SnowflakeishOr[users.PartialUser],
    ) -> None:
        """Delete a reaction from a message.

        If you are looking to delete your own applications reaction, use
        `delete_my_reaction`.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel where the message to delete the reaction from is.
            This may be the object or the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to delete a reaction from. This may be the
            object or the ID of an existing message.
        emoji : hikari.emojis.Emojiish
            The emoji to delete all reactions from.

        Raises
        ------
        hikari.errors.BadRequestError
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_MESSAGES` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_all_reactions(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        """Delete all reactions from a message.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel where the message to delete all reactions from is.
            This may be the object or the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to delete all reaction from. This may be the
            object or the ID of an existing message.

        Raises
        ------
        hikari.errors.BadRequestError
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_MESSAGES` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_reactions_for_emoji(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        emoji: emojis.Emojiish,
    ) -> iterators.LazyIterator[users.User]:
        """Fetch reactions for an emoji from a message.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel where the message to delete all reactions from is.
            This may be the object or the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to delete all reaction from. This may be the
            object or the ID of an existing message.
        emoji : hikari.emojis.Emojiish
            The emoji to filter reactions by.

        Returns
        -------
        hikari.iterators.LazyIterator[hikari.users.User]
            An iterator to fetch the users.

        !!! note
            This call is not a coroutine function, it returns a special type of
            lazy iterator that will perform API calls as you iterate across it.
            See `hikari.iterators` for the full API for this iterator type.

        Raises
        ------
        hikari.errors.BadRequestError
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.

        !!! note
            The exceptions on this endpoint will only be raised once the
            result is awaited or iterated over. Invoking this function
            itself will not raise anything.
        """

    @abc.abstractmethod
    async def create_webhook(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
        name: str,
        *,
        avatar: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.Webhook:
        """Create webhook in a channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel where the webhook will be created. This may be
            the object or the ID of an existing channel.
        name : str
            The name for the webhook. This cannnot be `clyde`.

        Other Parameters
        ----------------
        avatar : typing.Optional[hikari.files.Resourceish]
            If provided, the avatar for the webhook.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.webhooks.Webhook
            The created webhook.

        Raises
        ------
        hikari.errors.BadRequestError
            If `name` doesnt follow the restrictions enforced by discord.
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_WEBHOOKS` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_webhook(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.Webhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.Webhook:
        """Fetch an existing webhook.

        Parameters
        ----------
        webhook : hikari.snowflakes.SnowflakeishOr[hikari.webhooks.Webhook]
            The webhook to fetch. This may be the object or the ID
            of an existing webhook.

        Other Parameters
        ----------------
        token : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the webhoook token that will be used to fetch
            the webhook instead of the token the client was initialized with.

        Returns
        -------
        hikari.webhooks.Webhook
            The requested webhook.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_WEBHOOKS` permission when not
            using a token.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_channel_webhooks(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextChannel],
    ) -> typing.Sequence[webhooks.Webhook]:
        """Fetch all channel webhooks.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]
            The channel to fetch the webhooks for. This
            may be a `hikari.channels.TextChannel` or the ID of an
            existing channel.

        Returns
        -------
        typing.Sequence[hikari.webhooks.Webhook]
            The fetched webhooks.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_WEBHOOKS` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_guild_webhooks(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[webhooks.Webhook]:
        """Fetch all guild webhooks.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the webhooks for. This may be the object
            or the ID of an existing guild.

        Returns
        -------
        typing.Sequence[hikari.webhooks.Webhook]
            The fetched webhooks.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_WEBHOOKS` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_webhook(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.Webhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        channel: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.TextChannel]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.Webhook:
        """Edit a webhook.

        Parameters
        ----------
        webhook : hikari.snowflakes.SnowflakeishOr[hikari.webhooks.Webhook]
            The webhook to edit. This may be the object or the
            ID of an existing webhook.

        Other Parameters
        ----------------
        token : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the webhoook token that will be used to edit
            the webhook instead of the token the client was initialized with.
        name : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the new webhook name.
        avatar : hikari.undefined.UndefinedNoneOr[hikari.files.Resourceish]
            If provided, the new webhook avatar. If `builtins.None`, will
            remove the webhook avatar.
        channel : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.TextChannel]]
            If provided, the text channel to move the webhook to.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.webhooks.Webhook
            The edited webhook.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_WEBHOOKS` permission when not
            using a token.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_webhook(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.Webhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Delete a webhook.

        Parameters
        ----------
        webhook : hikari.snowflakes.SnowflakeishOr[hikari.webhooks.Webhook]
            The webhook to delete. This may be the object or the
            ID of an existing webhook.

        Other Parameters
        ----------------
        token : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the webhoook token that will be used to delete
            the webhook instead of the token the client was initialized with.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_WEBHOOKS` permission when not
            using a token.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhoook is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def execute_webhook(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.Webhook],
        token: str,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        username: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar_url: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        """Execute a webhook.

        Parameters
        ----------
        webhook : hikari.snowflakes.SnowflakeishOr[hikari.webhooks.Webhook]
            The webhook to execute. This may be the object
            or the ID of an existing webhook.
        token: builtins.str
            The webhook token.
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message contents. If
            `hikari.undefined.UNDEFINED`, then nothing will be sent
            in the content. Any other value here will be cast to a
            `builtins.str`.

            If this is a `hikari.embeds.Embed` and no `embed` nor
            no `embeds` kwarg is provided, then this will instead
            update the embed. This allows for simpler syntax when
            sending an embed alone.

            Likewise, if this is a `hikari.files.Resource`, then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.

        Other Parameters
        ----------------
        embed : hikari.undefined.UndefinedOr[hikari.embeds.Embed]
            If provided, the message embed.
        embeds : hikari.undefined.UndefinedOr[hikari.embeds.Embed]
            If provided, the message embeds.
        attachment : hikari.undefined.UndefinedOr[hikari.files.Resourceish],
            If provided, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.
        attachments : hikari.undefined.UndefinedOr[typing.Sequence[hikari.files.Resourceish]],
            If provided, the message attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        tts : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the message will be read out by a screen
            reader using Discord's TTS (text-to-speech) system.
        nonce : hikari.undefined.UndefinedOr[builtins.str]
            An arbitrary identifier to associate with the message. This
            can be used to identify it later in received events. If provided,
            this must be less than 32 bytes. If not provided, then
            a null value is placed on the message instead. All users can
            see this value.
        mentions_everyone : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the message should parse @everyone/@here
            mentions.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], builtins.bool]]
            If provided, and `builtins.True`, all user mentions will be detected.
            If provided, and `builtins.False`, all user mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            `hikari.snowflakes.Snowflake`, or
            `hikari.users.PartialUser` derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], builtins.bool]]
            If provided, and `builtins.True`, all role mentions will be detected.
            If provided, and `builtins.False`, all role mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            `hikari.snowflakes.Snowflake`, or
            `hikari.guilds.PartialRole` derivatives to enforce mentioning
            specific roles.

        !!! note
            Attachments can be passed as many different things, to aid in
            convenience.

            - If a `pathlib.PurePath` or `builtins.str` to a valid URL, the
                resource at the given URL will be streamed to Discord when
                sending the message. Subclasses of
                `hikari.files.WebResource` such as
                `hikari.files.URL`,
                `hikari.messages.Attachment`,
                `hikari.emojis.Emoji`,
                `EmbedResource`, etc will also be uploaded this way.
                This will use bit-inception, so only a small percentage of the
                resource will remain in memory at any one time, thus aiding in
                scalability.
            - If a `hikari.files.Bytes` is passed, or a `builtins.str`
                that contains a valid data URI is passed, then this is uploaded
                with a randomized file name if not provided.
            - If a `hikari.files.File`, `pathlib.PurePath` or
                `builtins.str` that is an absolute or relative path to a file
                on your file system is passed, then this resource is uploaded
                as an attachment using non-blocking code internally and streamed
                using bit-inception where possible. This depends on the
                type of `concurrent.futures.Executor` that is being used for
                the application (default is a thread pool which supports this
                behaviour).

        Returns
        -------
        hikari.messages.Message
            The created message.

        Raises
        ------
        builtins.ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        builtins.TypeError
            If both `attachment` and `attachments` are specified or if both
            `embed` and `embeds` are specified.
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no attachments or embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; too many attachments; attachments that are too large;
            invalid image URLs in embeds; users in `user_mentions` not being
            mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def edit_webhook_message(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.Webhook],
        token: str,
        message: snowflakes.SnowflakeishOr[messages_.Message],
        content: undefined.UndefinedNoneOr[typing.Any] = undefined.UNDEFINED,
        *,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        """Edit a message sent by a webhook.

        Parameters
        ----------
        webhook : hikari.snowflakes.SnowflakeishOr[hikari.webhooks.Webhook]
            The webhook to execute. This may be the object
            or the ID of an existing webhook.
        token: builtins.str
            The webhook token.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to delete. This may be the object or the ID of
            an existing message.
        content : hikari.undefined.UndefinedNoneOr[typing.Any]
            If provided, the message contents. If
            `hikari.undefined.UNDEFINED`, then nothing will be sent
            in the content. Any other value here will be cast to a
            `builtins.str`.

            If this is a `hikari.embeds.Embed` and no `embed` nor
            no `embeds` kwarg is provided, then this will instead
            update the embed. This allows for simpler syntax when
            sending an embed alone.

            Likewise, if this is a `hikari.files.Resource`, then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.

        Other Parameters
        ----------------
        embed : hikari.undefined.UndefinedNoneOr[hikari.embeds.Embed]
            If provided, the message embed.
        embeds : hikari.undefined.UndefinedNoneOr[hikari.embeds.Embed]
            If provided, the message embeds.
        mentions_everyone : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether the message should parse @everyone/@here
            mentions.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], builtins.bool]]
            If provided, and `builtins.True`, all user mentions will be detected.
            If provided, and `builtins.False`, all user mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            `hikari.snowflakes.Snowflake`, or
            `hikari.users.PartialUser` derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], builtins.bool]]
            If provided, and `builtins.True`, all role mentions will be detected.
            If provided, and `builtins.False`, all role mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            `hikari.snowflakes.Snowflake`, or
            `hikari.guilds.PartialRole` derivatives to enforce mentioning
            specific roles.

        !!! note
            Mentioning everyone, roles, or users in message edits currently
            will not send a push notification showing a new mention to people
            on Discord. It will still highlight in their chat as if they
            were mentioned, however.

        !!! note
            There is currently no documented way to clear attachments or edit
            attachments from a previously sent message on Discord's API. To
            do this, delete the message and re-send it. This also applies
            to embed attachments.

        !!! warning
            If you specify one of `mentions_everyone`, `user_mentions`, or
            `role_mentions`, then all others will default to `builtins.False`,
            even if they were enabled previously.

            This is a limitation of Discord's design. If in doubt, specify all three of
            them each time.

        Returns
        -------
        hikari.messages.Message
            The edited message.

        Raises
        ------
        builtins.ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        builtins.TypeError
            If both `attachment` and `attachments` are specified or if both
            `embed` and `embeds` are specified.
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no attachments or embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; too many attachments; attachments that are too large;
            invalid image URLs in embeds; users in `user_mentions` not being
            mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook or the message are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def delete_webhook_message(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.Webhook],
        token: str,
        message: snowflakes.SnowflakeishOr[messages_.Message],
    ) -> None:
        """Delete a given message in a given channel.

        Parameters
        ----------
        webhook : hikari.snowflakes.SnowflakeishOr[hikari.webhooks.Webhook]
            The webhook to execute. This may be the object
            or the ID of an existing webhook.
        token: builtins.str
            The webhook token.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to delete. This may be the object or the ID of
            an existing message.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook or the message are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_gateway_url(self) -> str:
        """Fetch the gateway url.

        !!! note
            This endpoint does not require any valid authorization.

        Raises
        ------
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_gateway_bot(self) -> sessions.GatewayBot:
        """Fetch the gateway gateway info for the bot.

        Returns
        -------
        hikari.sessions.GatewayBot
            The gateway bot.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_invite(self, invite: invites.Inviteish) -> invites.Invite:
        """Fetch an existing invite.

        Parameters
        ----------
        invite : hikari.invites.Inviteish
            The invite to fetch. This may be an invite object or
            the code of an existing invite.

        Returns
        -------
        hikari.invites.Invite
            The requested invite.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the invite is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_invite(self, invite: invites.Inviteish) -> None:
        """Delete an existing invite.

        Parameters
        ----------
        invite : hikari.invites.Inviteish
            The invite to delete. This may be an invite object or
            the code of an existing invite.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_GUILD` permission in the guild
            the invite is from or if you are missing the `MANAGE_CHANNELS`
            permission in the channel the invite is from.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the invite is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_my_user(self) -> users.OwnUser:
        """Fetch the token's associated user.

        Returns
        -------
        hikari.users.OwnUser
            The token's associated user.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_my_user(
        self,
        *,
        username: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
    ) -> users.OwnUser:
        """Edit the token's associated user.

        Other Parameters
        ----------------
        username : undefined.UndefinedOr[builtins.str]
            If provided, the new username.
        avatar : undefined.UndefinedNoneOr[hikari.files.Resourceish]
            If provided, the new avatar. If `builtins.None`,
            the avatar will be removed.

        Returns
        -------
        hikari.users.OwnUser
            The edited token's associated user.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.

            Discord also returns this on a ratelimit:
            https://github.com/discord/discord-api-docs/issues/1462
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_my_connections(self) -> typing.Sequence[applications.OwnConnection]:
        """Fetch the token's associated connections.

        Returns
        -------
        hikari.applications.OwnConnection
            The token's associated connections.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_my_guilds(
        self,
        *,
        newest_first: bool = False,
        start_at: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[applications.OwnGuild]:
        """Fetch the token's associated guilds.

        Other Parameters
        ----------------
        newest_first : builtins.bool
            Whether to fetch the newest first or the olders first.
            Defaults to `builtins.False`.
        start_at : hikari.undefined.UndefinedOr[hikari.snowflakes.SearchableSnowflakeishOr[hikari.guilds.PartialGuild]]
            If provided, will start at this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake. This
            may also be a guild object. In this case, the
            date the object was first created will be used.

        Returns
        -------
        hikari.iterators.LazyIterator[hikari.applications.OwnGuild]
            The token's associated guilds.

        !!! note
            This call is not a coroutine function, it returns a special type of
            lazy iterator that will perform API calls as you iterate across it.
            See `hikari.iterators` for the full API for this iterator type.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.

        !!! note
            The exceptions on this endpoint will only be raised once the
            result is awaited or iterated over. Invoking this function
            itself will not raise anything.
        """

    @abc.abstractmethod
    async def leave_guild(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /) -> None:
        """Leave a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to leave. This may be the object or
            the ID of an existing guild.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found or you own the guild.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_dm_channel(self, user: snowflakes.SnowflakeishOr[users.PartialUser], /) -> channels_.DMChannel:
        """Create a DM channel with a user.

        Parameters
        ----------
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The user to create the DM channel with. This may be the
            object or the ID of an existing user.

        Returns
        -------
        hikari.channels.DMChannel
            The created DM channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If the user is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    # THIS IS AN OAUTH2 FLOW BUT CAN BE USED BY BOTS ALSO
    @abc.abstractmethod
    async def fetch_application(self) -> applications.Application:
        """Fetch the token's associated application.

        Returns
        -------
        hikari.applications.Application
            The token's associated application.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    # THIS IS AN OAUTH2 FLOW ONLY
    @abc.abstractmethod
    async def add_user_to_guild(
        self,
        access_token: str,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        nick: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
        mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> typing.Optional[guilds.Member]:
        """Add a user to a guild.

        !!! note
            This requires the `access_token` to have the
            `hikari.applications.OAuth2Scope.GUILDS_JOIN` scope enabled.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to add the user to. This may be the object
            or the ID of an existing guild.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The user to add to the guild. This may be the object
            or the ID of an existing user.

        Other Parameters
        ----------------
        nick : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the nick to add to the user when he joins the guild.

            Requires the `MANAGE_NICKNAMES` permission on the guild.
        roles : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole]]
            If provided, the roles to add to the user when he joins the guild.
            This may be a collection objects or IDs of existing roles.

            Requires the `MANAGE_ROLES` permission on the guild.
        mute : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, the mute state to add the user when he joins the guild.

            Requires the `MUTE_MEMBERS` permission on the guild.
        deaf : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, the deaf state to add the user when he joins the guild.

            Requires the `DEAFEN_MEMBERS` permission on the guild.

        Returns
        -------
        typing.Optional[hikari.guilds.Member]
            `builtins.None` if the user was already part of the guild, else
            `hikari.guilds.Member`.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are not part of the guild you want to add the user to,
            if you are missing permissions to do one of the things you specified,
            if you are using an access token for another user, if the token is
            bound to annother bot or if the access token doesnt have the
            `hikari.applications.OAuth2Scope.GUILDS_JOIN` scope enabled.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If you own the guild or the user is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_voice_regions(self) -> typing.Sequence[voices.VoiceRegion]:
        """Fetch available voice regions.

        !!! note
            This endpoint doesn't return VIP voice regions.

        Returns
        -------
        typing.Sequence[hikari.voices.VoiceRegion]
            The available voice regions.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_user(self, user: snowflakes.SnowflakeishOr[users.PartialUser]) -> users.User:
        """Fetch a user.

        Parameters
        ----------
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The user to fetch. This can be the object
            or the ID of an existing user.

        Returns
        -------
        hikari.users.User
            The requested user

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the user is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    def fetch_audit_log(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        before: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        event_type: undefined.UndefinedOr[audit_logs.AuditLogEventType] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[audit_logs.AuditLog]:
        """Fetch the guild's audit log.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the audit logs from. This can be a
            guild object or the ID of an existing guild.

        Other Parameters
        ----------------
        before : hikari.undefined.UndefinedOr[hikari.snowflakes.SearchableSnowflakeishOr[hikari.snowflakes.Unique]]
            If provided, filter to only actions after this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake. This
            may be any other Discord entity that has an ID. In this case, the
            date the object was first created will be used.
        user : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]]
            If provided, the user to filter for.
        event_type : hikari.undefined.UndefinedOr[hikari.audit_logs.AuditLogEventType]
            If provided, the event type to filter for.

        Returns
        -------
        hikari.iterators.LazyIterator[hikari.audit_logs.AuditLog]
            The guild's audit log.

        !!! note
            This call is not a coroutine function, it returns a special type of
            lazy iterator that will perform API calls as you iterate across it.
            See `hikari.iterators` for the full API for this iterator type.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the `VIEW_AUDIT_LOG` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.

        !!! note
            The exceptions on this endpoint will only be raised once the
            result is awaited or iterated over. Invoking this function
            itself will not raise anything.
        """

    @abc.abstractmethod
    async def fetch_emoji(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        emoji: snowflakes.SnowflakeishOr[emojis.CustomEmoji],
    ) -> emojis.KnownCustomEmoji:
        """Fetch a guild emoji.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the emoji from. This can be a
            guild object or the ID of an existing guild.
        emoji : hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]
            The emoji to fetch. This can be a `hikari.emojis.CustomEmoji`
            or the ID of an existing emoji.

        Returns
        -------
        hikari.emojis.KnownCustomEmoji
            The requested emoji.

        Raises
        ------
        hikari.errors.NotFoundError
            If the guild or the emoji are not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_guild_emojis(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[emojis.KnownCustomEmoji]:
        """Fetch the emojis of a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the emojis from. This can be a
            guild object or the ID of an existing guild.

        Returns
        -------
        typing.Sequence[hikari.emojis.KnownCustomEmoji]
            The requested emojis.

        Raises
        ------
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_emoji(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        image: files.Resourceish,
        *,
        roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> emojis.KnownCustomEmoji:
        """Create an emoji in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the emoji on. This can be a
            guild object or the ID of an existing guild.
        name : builtins.str
            The name for the emoji.
        image : hikari.files.Resourceish
            The 128x128 image for the emoji. Maximum upload size is 256kb.
            This can be a still or an animated image.

        Other Parameters
        ----------------
        roles : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole]]
            If provided, a collection of the roles that will be able to
            use this emoji. This can be a `hikari.guilds.PartialRole` or
            the ID of an existing role.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.emojis.KnownCustomEmoji
            The created emoji.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value or
            if there are no more spaces for the type of emoji in the guild.
        hikari.errors.ForbiddenError
            If you are missing `MANAGE_EMOJIS` in the server.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_emoji(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        emoji: snowflakes.SnowflakeishOr[emojis.CustomEmoji],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> emojis.KnownCustomEmoji:
        """Edit an emoji in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to edit the emoji on. This can be a
            guild object or the ID of an existing guild.
        emoji : hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]
            The emoji to edit. This can be a `hikari.emojis.CustomEmoji`
            or the ID of an existing emoji.

        Other Parameters
        ----------------
        name : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the new name for the emoji.
        roles : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole]]
            If provided, the new collection of roles that will be able to
            use this emoji. This can be a `hikari.guilds.PartialRole` or
            the ID of an existing role.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.emojis.KnownCustomEmoji
            The edited emoji.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing `MANAGE_EMOJIS` in the server.
        hikari.errors.NotFoundError
            If the guild or the emoji are not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_emoji(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        emoji: snowflakes.SnowflakeishOr[emojis.CustomEmoji],
        # Reason is not currently supported for some reason.
    ) -> None:
        """Delete an emoji in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to delete the emoji on. This can be a
            guild object or the ID of an existing guild.
        emoji : hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]
            The emoji to delete. This can be a `hikari.emojis.CustomEmoji`
            or the ID of an existing emoji.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing `MANAGE_EMOJIS` in the server.
        hikari.errors.NotFoundError
            If the guild or the emoji are not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def guild_builder(self, name: str, /) -> special_endpoints.GuildBuilder:
        """Make a guild builder to create a guild with.

        Parameters
        ----------
        name : builtins.str
            The new guilds name.

        Returns
        -------
        hikari.api.special_endpoints.GuildBuilder
            The guild builder to use. This will allow to create a guild
            later with `hikari.api.special_endpoints.GuildBuilder.create`.

        !!! note
            This endpoint can only be used by bots in less than 10 guilds.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value or if you
            call this as a bot that's in more than 10 guilds.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.

        !!! note
            The exceptions on this endpoint will only be raised once
            `hikari.api.special_endpoints.GuildBuilder.create` is called.
            Invoking this function itself will not raise any of
            the above types.

        See Also
        --------
        Guild builder: `hikari.api.special_endpoints.GuildBuilder`
        """

    @abc.abstractmethod
    async def fetch_guild(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> guilds.RESTGuild:
        """Fetch a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch. This can be the object
            or the ID of an existing guild.

        Returns
        -------
        hikari.guilds.RESTGuild
            The requested guild.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_guild_preview(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> guilds.GuildPreview:
        """Fetch a guild preview.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the preview of. This can be a
            guild object or the ID of an existing guild.

        Returns
        -------
        hikari.guilds.GuildPreview
            The requested guild preview.

        !!! note
            This will only work for guilds you are a part of or are public.

        Raises
        ------
        hikari.errors.NotFoundError
            If the guild is not found or you are not part of the guild.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_guild(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        region: undefined.UndefinedOr[voices.VoiceRegionish] = undefined.UNDEFINED,
        verification_level: undefined.UndefinedOr[guilds.GuildVerificationLevel] = undefined.UNDEFINED,
        default_message_notifications: undefined.UndefinedOr[
            guilds.GuildMessageNotificationsLevel
        ] = undefined.UNDEFINED,
        explicit_content_filter_level: undefined.UndefinedOr[
            guilds.GuildExplicitContentFilterLevel
        ] = undefined.UNDEFINED,
        afk_channel: undefined.UndefinedOr[
            snowflakes.SnowflakeishOr[channels_.GuildVoiceChannel]
        ] = undefined.UNDEFINED,
        afk_timeout: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        icon: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        owner: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        splash: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        banner: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        system_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels_.GuildTextChannel]
        ] = undefined.UNDEFINED,
        rules_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels_.GuildTextChannel]
        ] = undefined.UNDEFINED,
        public_updates_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels_.GuildTextChannel]
        ] = undefined.UNDEFINED,
        preferred_locale: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.RESTGuild:
        """Edit a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to edit. This may be the object
            or the ID of an existing guild.

        Other Parameters
        ----------------
        name : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the new name for the guild.
        region : hikari.undefined.UndefinedOr[hikari.voices.VoiceRegionish]
            If provided, the new voice region for the guild.
        verification_level : hikari.undefined.UndefinedOr[hikari.guilds.GuildVerificationLevel]
            If provided, the new verification level.
        default_message_notifications : hikari.undefined.UndefinedOr[hikari.guilds.GuildMessageNotificationsLevel]
            If provided, the new default message notifications level.
        explicit_content_filter_level : hikari.undefined.UndefinedOr[hikari.guilds.GuildExplicitContentFilterLevel]
            If provided, the new explicit content filter level.
        afk_channel : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildVoiceChannel]]
            If provided, the new afk channel. Requires `afk_timeout` to
            be set to work.
        afk_timeout : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the new afk timeout.
        icon : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            If provided, the new guild icon. Must be a 1024x1024 image or can be
            an animated gif when the guild has the `ANIMATED_ICON` feature.
        owner : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]]]
            If provided, the new guild owner.

            !!! warning
                You need to be the owner of the server to use this.
        splash : hikari.undefined.UndefinedNoneOr[hikari.files.Resourceish]
            If provided, the new guild splash. Must be a 16:9 image and the
            guild must have the `INVITE_SPLASH` feature.
        banner : hikari.undefined.UndefinedNoneOr[hikari.files.Resourceish]
            If provided, the new guild banner. Must be a 16:9 image and the
            guild must have the `BANNER` feature.
        system_channel : hikari.undefined.UndefinedNoneOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]]
            If provided, the new system channel.
        rules_channel : hikari.undefined.UndefinedNoneOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]]
            If provided, the new rules channel.
        public_updates_channel : hikari.undefined.UndefinedNoneOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]]
            If provided, the new public updates channel.
        preferred_locale : hikari.undefined.UndefinedNoneOr[builtins.str]
            If provided, the new preferred locale.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.guilds.RESTGuild
            The edited guild.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value. Or
            you are missing the
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_GUILD` permission or if you tried to
            pass ownership without being the server owner.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def delete_guild(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> None:
        """Delete a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to delete. This may be the object or
            the ID of an existing guild.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not the owner of the guild.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If you own the guild or if you are not in it.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_guild_channels(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[channels_.GuildChannel]:
        """Fetch the channels in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the channels from. This may be the
            object or the ID of an existing guild.

        Returns
        -------
        typing.Sequence[hikari.channels.GuildChannel]
            The requested channels.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_guild_text_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildTextChannel:
        """Create a text channel in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the channel in. This may be the
            object or the ID of an existing guild.
        name : builtins.str
            The channels name. Must be between 2 and 1000 characters.

        Other Parameters
        ----------------
        position : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the position of the channel (relative to the
            category, if any).
        topic : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the channels topic. Maximum 1024 characters.
        nsfw : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to mark the channel as NSFW.
        rate_limit_per_user : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the ammount of seconds a user has to wait
            before being able to send another message in the channel.
            Maximum 21600 seconds.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the permission overwrites for the channel.
        category : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildCategory]]
            The category to create the channel under. This may be the
            object or the ID of an existing category.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.GuildTextChannel
            The created channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_CHANNEL` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_guild_news_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildNewsChannel:
        """Create a news channel in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the channel in. This may be the
            object or the ID of an existing guild.
        name : builtins.str
            The channels name. Must be between 2 and 1000 characters.

        Other Parameters
        ----------------
        position : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the position of the channel (relative to the
            category, if any).
        topic : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the channels topic. Maximum 1024 characters.
        nsfw : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to mark the channel as NSFW.
        rate_limit_per_user : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the ammount of seconds a user has to wait
            before being able to send another message in the channel.
            Maximum 21600 seconds.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the permission overwrites for the channel.
        category : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildCategory]]
            The category to create the channel under. This may be the
            object or the ID of an existing category.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.GuildNewsChannel
            The created channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_CHANNEL` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_guild_voice_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildVoiceChannel:
        """Create a voice channel in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the channel in. This may be the
            object or the ID of an existing guild.
        name : builtins.str
            The channels name. Must be between 2 and 1000 characters.

        Other Parameters
        ----------------
        position : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the position of the channel (relative to the
            category, if any).
        user_limit : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the maximum users in the channel at once.
            Must be between 0 and 99 with 0 meaning no limit.
        bitrate : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the bitrate for the channel. Must be
            between 8000 and 96000 or 8000 and 128000 for VIP
            servers.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the permission overwrites for the channel.
        category : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildCategory]]
            The category to create the channel under. This may be the
            object or the ID of an existing category.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.GuildVoiceChannel
            The created channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_CHANNEL` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_guild_category(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildCategory:
        """Create a category in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the channel in. This may be the
            object or the ID of an existing guild.
        name : builtins.str
            The channels name. Must be between 2 and 1000 characters.

        Other Parameters
        ----------------
        position : hikari.undefined.UndefinedOr[builtins.int]
            If provided, the position of the category.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the permission overwrites for the category.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.GuildCategory
            The created category.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_CHANNEL` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def reposition_channels(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        positions: typing.Mapping[int, snowflakes.SnowflakeishOr[channels_.GuildChannel]],
    ) -> None:
        """Reposition the channels in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to reposition the channels in. This may be the
            object or the ID of an existing guild.
        positions : typing.Mapping[builtins.int, hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildChannel]]
            A mapping of of the object or the ID of an existing channel to
            the new position, relative to their parent category, if any.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_CHANNEL` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
    ) -> guilds.Member:
        """Fetch a guild member.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to get the member from. This may be the
            object or the ID of an existing guild.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The user to get the member for. This may be the
            object or the ID of an existing user.

        Returns
        -------
        hikari.guilds.Member
            The requested member.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or the user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_members(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> iterators.LazyIterator[guilds.Member]:
        """Fetch the members from a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the members of. This may be the
            object or the ID of an existing guild.

        Returns
        -------
        hikari.iterators.LazyIterator[hikari.guilds.Member]
            An iterator to fetch the members.

        !!! note
            This call is not a coroutine function, it returns a special type of
            lazy iterator that will perform API calls as you iterate across it.
            See `hikari.iterators` for the full API for this iterator type.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.

        !!! note
            The exceptions on this endpoint will only be raised once the
            result is awaited or iterated over. Invoking this function
            itself will not raise anything.

        !!! warning
            This endpoint requires the `GUILD_MEMBERS` intent. Alternatively,
            you can use `search_members` which doesn't require any intents.
        """

    @abc.abstractmethod
    async def search_members(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
    ) -> typing.Sequence[guilds.Member]:
        """Search the members in a guild by nickname and username.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The object or ID of the guild to search members in.
        name : str
            The query to match username(s) and nickname(s) against.

        Returns
        -------
        typing.Sequence[hikari.guilds.Member]
            A sequence of the members who matched the provided `name`.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.

        !!! note
            Unlike `RESTClient.fetch_members` this endpoint isn't paginated and
            therefore will return all the members in one go rather than needing
            to be asynchronously iterated over.
        """

    @abc.abstractmethod
    async def edit_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        nick: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
        mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        voice_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels_.GuildVoiceChannel]
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.Member:
        """Edit a guild member.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to edit. This may be the object
            or the ID of an existing guild.
        user : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to edit. This may be the object
            or the ID of an existing guild.

        Other Parameters
        ----------------
        nick : hikari.undefined.UndefinedNoneOr[builtins.str]
            If provided, the new nick for the member. If `builtins.None`,
            will remove the members nick.

            Requires the `MANAGE_NICKNAMES` permission.
        roles : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole]]
            If provided, the new roles for the member.

            Requires the `MANAGE_ROLES` permission.
        mute : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, the new server mute state for the member.

            Requires the `MUTE_MEMBERS` permission.
        deaf : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, the new server deaf state for the member.

            Requires the `DEAFEN_MEMBERS` permission.
        voice_channel : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildVoiceChannel]]]
            If provided, `builtins.None` or the object or the ID of
            an existing voice channel to move the member to.
            If `builtins.None`, will disconnect the member from voice.

            Requires the `MOVE_MEMBERS` permission and the `CONNECT`
            permission in the original voice channel and the target
            voice channel.

            !!! note
                If the member is not in a voice channel, this will
                take no effect.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.guilds.Member
            Object of the member that was updated.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing a permission to do an action.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or the user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_my_nick(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.Guild],
        nick: typing.Optional[str],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Edit the associated token's member nick.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to edit. This may be the object
            or the ID of an existing guild.
        nick : typing.Optional[builtins.str]
            The new nick. If `builtins.None`,
            will remove the nick.

        Other Parameters
        ----------------
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `CHANGE_NICKNAME` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def add_role_to_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        role: snowflakes.SnowflakeishOr[guilds.PartialRole],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Add a role to a member.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild where the member is in. This may be the
            object or the ID of an existing guild.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The user to add the role to. This may be the
            object or the ID of an existing user.
        role : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialRole]
            The role to add. This may be the object or the
            ID of an existing role.

        Other Parameters
        ----------------
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_ROLES` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild, user or role are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def remove_role_from_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        role: snowflakes.SnowflakeishOr[guilds.PartialRole],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Remove a role from a member.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild where the member is in. This may be the
            object or the ID of an existing guild.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The user to remove the role from. This may be the
            object or the ID of an existing user.
        role : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialRole]
            The role to remove. This may be the object or the
            ID of an existing role.

        Other Parameters
        ----------------
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_ROLES` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild, user or role are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def kick_user(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Kick a member from a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to kick the member from. This may be the
            object or the ID of an existing guild.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The user to kick. This may be the object
            or the ID of an existing user.

        Other Parameters
        ----------------
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `KICK_MEMBERS` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    kick_member = kick_user
    """This is simply an alias for readability."""

    @abc.abstractmethod
    async def ban_user(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        delete_message_days: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Ban a member from a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to ban the member from. This may be the
            object or the ID of an existing guild.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The user to kick. This may be the object
            or the ID of an existing user.

        Other Parameters
        ----------------
        delete_message_days : hikari.undefined.UndefinedNoneOr[builtins.int]
            If provided, the number of days to delete messages for.
            This must be between 0 and 7.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the `BAN_MEMBERS` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    ban_member = ban_user
    """This is simply an alias for readability."""

    @abc.abstractmethod
    async def unban_user(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Unban a member from a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to unban the member from. This may be the
            object or the ID of an existing guild.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The user to unban. This may be the object
            or the ID of an existing user.

        Other Parameters
        ----------------
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `BAN_MEMBERS` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    unban_member = unban_user
    """This is simply an alias for readability."""

    @abc.abstractmethod
    async def fetch_ban(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
    ) -> guilds.GuildMemberBan:
        """Fetch the guild's ban info for a user.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the ban from. This may be the
            object or the ID of an existing guild.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The user to fetch the ban of. This may be the
            object or the ID of an existing user.

        Returns
        -------
        hikari.guilds.GuildMemberBan
            The requested ban info.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `BAN_MEMBERS` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found or if the user
            is not banned.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_bans(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[guilds.GuildMemberBan]:
        """Fetch the bans of a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the bans from. This may be the
            object or the ID of an existing guild.

        Returns
        -------
        typing.Sequence[hikari.guilds.GuildMemberBan]
            The requested bans.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `BAN_MEMBERS` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_roles(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[guilds.Role]:
        """Fetch the roles of a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the roles from. This may be the
            object or the ID of an existing guild.

        Returns
        -------
        typing.Sequence[hikari.guilds.Role]
            The requested roles.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_role(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        permissions: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        color: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        colour: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        hoist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentionable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.Role:
        """Create a role.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the role in. This may be the
            object or the ID of an existing guild.

        Other Parameters
        ----------------
        name : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the name for the role.
        permissions : hikari.undefined.UndefinedOr[hikari.permissions.Permissions]
            The permissions to give the role. This will default to setting
            NO roles if left to the default value. This is in contrast to
            default behaviour on Discord where some random permissions will
            be set by default.
        color : hikari.undefined.UndefinedOr[hikari.colors.Colorish]
            If provided, the role's color.
        colour : hikari.undefined.UndefinedOr[hikari.colors.Colorish]
            An alias for `color`.
        hoist : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to hoist the role.
        mentionable : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to make the role mentionable.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.guilds.Role
            The created role.

        Raises
        ------
        builtins.TypeError
            If both `color` and `colour` are specified.
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_ROLES` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def reposition_roles(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        positions: typing.Mapping[int, snowflakes.SnowflakeishOr[guilds.PartialRole]],
    ) -> None:
        """Reposition the roles in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to reposition the roles in. This may be
            the object or the ID of an existing guild.
        positions : typing.Mapping[builtins.int, hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialRole]]
            A mapping of the position to the role.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_ROLES` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_role(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        role: snowflakes.SnowflakeishOr[guilds.PartialRole],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        permissions: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        color: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        colour: undefined.UndefinedOr[colors.Colorish] = undefined.UNDEFINED,
        hoist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentionable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.Role:
        """Edit a role.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to edit the role in. This may be the
            object or the ID of an existing guild.
        role : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialRole]
            The role to edit. This may be the object or the
            ID of an existing role.

        Other Parameters
        ----------------
        name : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the new name for the role.
        permissions : hikari.undefined.UndefinedOr[hikari.permissions.Permissions]
            If provided, the new permissions for the role.
        color : hikari.undefined.UndefinedOr[hikari.colors.Colorish]
            If provided, the new color for the role.
        colour : hikari.undefined.UndefinedOr[hikari.colors.Colorish]
            An alias for `color`.
        hoist : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to hoist the role.
        mentionable : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to make the role mentionable.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.guilds.Role
            The edited role.

        Raises
        ------
        builtins.TypeError
            If both `color` and `colour` are specified.
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_ROLES` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or role are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_role(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        role: snowflakes.SnowflakeishOr[guilds.PartialRole],
    ) -> None:
        """Delete a role.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to delete the role in. This may be the
            object or the ID of an existing guild.
        role : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialRole]
            The role to delete. This may be the object or the
            ID of an existing role.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_ROLES` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or role are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def estimate_guild_prune_count(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        days: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        include_roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
    ) -> int:
        """Estimate the guild prune count.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to estimate the guild prune count for. This may be the object
            or the ID of an existing guild.

        Other Parameters
        ----------------
        days : hikari.undefined.UndefinedOr[builtins.int]
            If provided, number of days to count prune for.
        include_roles : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole]]]
            If provided, the role(s) to include. By default, this endpoint will
            not count users with roles. Providing roles using this attribute
            will make members with the specified roles also get included into
            the count.

        Returns
        -------
        builtins.int
            The estimated guild prune count.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `KICK_MEMBERS` permission.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def begin_guild_prune(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        days: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        compute_prune_count: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        include_roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> typing.Optional[int]:
        """Begin the guild prune.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to begin the guild prune in. This may be the object
            or the ID of an existing guild.

        Other Parameters
        ----------------
        days : hikari.undefined.UndefinedOr[builtins.int]
            If provided, number of days to count prune for.
        compute_prune_count: hikari.snowflakes.SnowflakeishOr[builtins.bool]
            If provided, whether to return the prune count. This is discouraged
            for large guilds.
        include_roles : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole]]
            If provided, the role(s) to include. By default, this endpoint will
            not count users with roles. Providing roles using this attribute
            will make members with the specified roles also get included into
            the count.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        typing.Optional[builtins.int]
            If `compute_prune_count` is not provided or `builtins.True`, the
            number of members pruned. Else `builtins.None`.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the `KICK_MEMBERS` permission.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def fetch_guild_voice_regions(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[voices.VoiceRegion]:
        """Fetch the available voice regions for a guild.

        !!! note
            Unlike `RESTClient.fetch_voice_regions`, this will
            return the VIP regions if the guild has access to them.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the voice regions for. This may be the object
            or the ID of an existing guild.

        Returns
        -------
        typing.Sequence[hikari.voices.VoiceRegion]
            The available voice regions for the guild.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_guild_invites(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        """Fetch the guild's invites.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the invites for. This may be the object
            or the ID of an existing guild.

        Returns
        -------
        typing.Sequence[hikari.invites.InviteWithMetadata]
            The invites for the guild.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_GUILD` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_integrations(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[guilds.Integration]:
        """Fetch the guild's integrations.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the integrations for. This may be the object
            or the ID of an existing guild.

        Returns
        -------
        typing.Sequence[hikari.guilds.Integration]
            The integrations for the guild.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_GUILD` permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_widget(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> guilds.GuildWidget:
        """Fetch a guilds's widget.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the widget from. This can be the object
            or the ID of an existing guild.

        Returns
        -------
        hikari.guilds.GuildWidget
            The requested guild widget.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_GUILD` permission.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_widget(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        channel: undefined.UndefinedNoneOr[snowflakes.SnowflakeishOr[channels_.GuildChannel]] = undefined.UNDEFINED,
        enabled: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.GuildWidget:
        """Fetch a guilds's widget.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to edit the widget in. This can be the object
            or the ID of an existing guild.

        Other Parameters
        ----------------
        channel : hikari.undefined.UndefinedNoneOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildChannel]]
            If provided, the channel to set the widget to. If `builtins.None`,
            will not set to any.
        enabled : hikari.undefined.UndefinedOr[builtins.bool]
            If provided, whether to enable the widget.
        reason : hikari.undefined.UndefinedOr[builtins.str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.guilds.GuildWidget
            The edited guild widget.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_GUILD` permission.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_welcome_screen(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> guilds.WelcomeScreen:
        """Fetch a guild's welcome screen.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to fetch the welcome screen for.

        Returns
        -------
        hikari.invites.WelcomeScreen
            The requested welcome screen.

        Raises
        ------
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_welcome_screen(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        description: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        enabled: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        channels: undefined.UndefinedNoneOr[typing.Sequence[guilds.WelcomeChannel]] = undefined.UNDEFINED,
    ) -> guilds.WelcomeScreen:
        """Edit the welcome screen of a community guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            ID or object of the guild to edit the welcome screen for.

        Other Parameters
        ----------------
        description : undefined.UndefinedNoneOr[builtins.str]
            The description to set for the guild's welcome screen. This may be
            `builtins.None` to unset the description or left as
            `hikari.undefined.UNDEFINED` to leave the description unchanged.
        enabled : undefined.UndefinedOr[builtins.bool]
            Whether the guild's welcome screen should be enabled. Leave as
            `hikari.undefined.UNDEFINED` to leave this unchanged.
        channels : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.guilds.WelcomeChanne;]]
            A sequence of up to 5 public channels to set in this guild's welcome
            screen. This may be passed as `builtins.None` to remove all welcome
            channels or left as `hikari.undefined.UNDEFINED` to leave unchanged.

            !!! note
                Custom emojis may only be included in a guild's welcome channels
                if it's boost status is tier 2 or above.

        Returns
        -------
        hikari.guilds.WelcomeScreen
            The edited guild welcome screen.

        Raises
        ------
        hikari.errors.BadRequestError
            If more than 5 welcome channels are provided or if a custom emoji
            is included on a welcome channel in a guild that doesn't have tier
            2 of above boost status or if a private channel is included as a
            welcome channel.
        hikari.errors.ForbiddenError
            If you are missing the `MANAGE_GUILD` permission, are not part of
            the guild or the guild doesn't have access to the community welcome
            screen feature.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_vanity_url(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> invites.VanityURL:
        """Fetch a guild's vanity url.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the vanity url from. This can
            be the object or the ID of an existing guild.

        Returns
        -------
        hikari.invites.VanityURL
            The requested invite.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_template(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        description: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
    ) -> templates.Template:
        """Create a guild template.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create a template from.
        name : str
            The name to use for the created template.

        Other Parameters
        ----------------
        description : hikari.undefined.UndefinedNoneOr[builtins.str]
            The description to set for the template.

        Returns
        -------
        hikari.templates.Template
            The object of the created template.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found or you are missing the `MANAGE_GUILD`
            permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_guild_from_template(
        self,
        template: templates.Templateish,
        name: str,
        *,
        icon: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
    ) -> guilds.RESTGuild:
        """Make a guild from a template.

        Parameters
        ----------
        template: hikari.templates.Templateish
            The objecr or code of the template to create a guild based on.
        name : builtins.str
            The new guilds name.

        Other Parameters
        ----------------
        icon : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            If provided, the guild icon to set. Must be a 1024x1024 image or can
            be an animated gif when the guild has the `ANIMATED_ICON` feature.

        Returns
        -------
        hikari.guilds.RESTGuild
            Object of the created guild.

        !!! note
            This endpoint can only be used by bots in less than 10 guilds.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value or if you
            call this as a bot that's in more than 10 guilds.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_template(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        template: templates.Templateish,
    ) -> templates.Template:
        """Delete a guild template.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to delete a template in.
        template : hikari.templates.Templateish
            Object or ID of the template to delete.

        Returns
        -------
        hikari.templates.Template
            The deleted template's object.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found or you are missing the `MANAGE_GUILD`
            permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_template(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        template: templates.Templateish,
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        description: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
    ) -> templates.Template:
        """Modify a guild template.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to edit a template in.
        template : hikari.templates.Templateish
            Object or ID of the template to modify.

        Other Parameters
        ----------------
        name : hikari.undefined.UndefinedOr[builtins.str]
            The name to set for this template.
        description : hikari.undefined.UndefinedNoneOr[builtins.str]
            The description to set for the template.

        Returns
        -------
        hikari.templates.Template
            The object of the edited template.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found or you are missing the `MANAGE_GUILD`
            permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_template(self, template: templates.Templateish) -> templates.Template:
        """Fetch a guild template.

        Parameters
        ----------
        template : hikari.templates.Templateish
            The object or string code of the template to fetch.

        Returns
        -------
        hikari.templates.Template
            The object of the found template.

        Raises
        ------
        hikari.errors.NotFoundError
            If the template was not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_guild_templates(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[templates.Template]:
        """Fetch the templates for a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The object or ID of the guild to get the templates for.

        Returns
        -------
        typing.Sequence[hikari.templates.Template]
            A sequence of the found template objects.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found or are missing the `MANAGE_GUILD`
            permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def sync_guild_template(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        template: templates.Templateish,
    ) -> templates.Template:
        """Create a guild template.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to sync a template in
        template : hikari.templates.Templateish
            Object or ID of the template to sync.

        Returns
        -------
        hikari.templates.Template
            The object of the synced template.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild or are missing the `MANAGE_GUILD`
            permission.
        hikari.errors.NotFoundError
            If the guild or template is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.RateLimitedError
            Usually, Hikari will handle and retry on hitting
            rate-limits automatically. This includes most bucket-specific
            rate-limits and global rate-limits. In some rare edge cases,
            however, Discord implements other undocumented rules for
            rate-limiting, such as limits per attribute. These cannot be
            detected or handled normally by Hikari due to their undocumented
            nature, and will trigger this exception if they occur.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
