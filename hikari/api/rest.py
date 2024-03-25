# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
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

__all__: typing.Sequence[str] = ("RESTClient", "TokenStrategy")

import abc
import datetime
import typing

from hikari import scheduled_events
from hikari import traits
from hikari import undefined

if typing.TYPE_CHECKING:
    from hikari import applications
    from hikari import audit_logs
    from hikari import channels as channels_
    from hikari import colors
    from hikari import commands
    from hikari import embeds as embeds_
    from hikari import emojis
    from hikari import files
    from hikari import guilds
    from hikari import invites
    from hikari import iterators
    from hikari import locales
    from hikari import messages as messages_
    from hikari import permissions as permissions_
    from hikari import sessions
    from hikari import snowflakes
    from hikari import stickers as stickers_
    from hikari import templates
    from hikari import users
    from hikari import voices
    from hikari import webhooks
    from hikari.api import entity_factory as entity_factory_
    from hikari.api import special_endpoints
    from hikari.interactions import base_interactions
    from hikari.internal import time


class TokenStrategy(abc.ABC):
    """Interface of an object used for managing OAuth2 access."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def token_type(self) -> typing.Union[applications.TokenType, str]:
        """Type of token this strategy returns."""

    @abc.abstractmethod
    async def acquire(self, client: RESTClient) -> str:
        """Acquire an authorization token (including the prefix).

        Parameters
        ----------
        client : hikari.api.rest.RESTClient
            The rest client to use to acquire the token.

        Returns
        -------
        str
            The current authorization token to use for this client and it's
            prefix.
        """

    @abc.abstractmethod
    def invalidate(self, token: typing.Optional[str]) -> None:
        """Invalidate the cached token in this handler.

        !!! note
            [`token`][] may be provided in-order to avoid newly generated tokens
            from being invalidated due to multiple calls being made by separate
            subroutines which are handling the same token.

        Parameters
        ----------
        token : typing.Optional[str]
            The token to specifically invalidate. If provided then this will only
            invalidate the cached token if it matches this, otherwise it'll be
            invalidated regardless.
        """


class RESTClient(traits.NetworkSettingsAware, abc.ABC):
    """Interface for functionality that a REST API implementation provides."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def is_alive(self) -> bool:
        """Whether this component is alive."""

    @property
    @abc.abstractmethod
    def entity_factory(self) -> entity_factory_.EntityFactory:
        """Entity factory used by this REST client."""

    @property
    @abc.abstractmethod
    def token_type(self) -> typing.Union[str, applications.TokenType, None]:
        """Type of token this client is using for most requests.

        If this is [`None`][] then this client will likely only work
        for some endpoints such as public and webhook ones.
        """

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
            [`hikari.channels.PartialChannel`][], depending on the type of
            channel you request for.

            This means that you may get one of
            [`hikari.channels.DMChannel`][],
            [`hikari.channels.GroupDMChannel`][],
            [`hikari.channels.GuildTextChannel`][],
            [`hikari.channels.GuildVoiceChannel`][],
            [`hikari.channels.GuildNewsChannel`][].

            Likewise, the [`hikari.channels.GuildChannel`][] can be used to
            determine if a channel is guild-bound, and
            [`hikari.channels.TextableChannel`][] can be used to determine
            if the channel provides textual functionality to the application.

            You can check for these using the [`isinstance`][]
            builtin function.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.VIEW_CHANNEL`][] permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        flags: undefined.UndefinedOr[channels_.ChannelFlag] = undefined.UNDEFINED,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        video_quality_mode: undefined.UndefinedOr[typing.Union[channels_.VideoQualityMode, int]] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        region: undefined.UndefinedNoneOr[typing.Union[voices.VoiceRegion, str]] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        parent_category: undefined.UndefinedOr[
            snowflakes.SnowflakeishOr[channels_.GuildCategory]
        ] = undefined.UNDEFINED,
        default_auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_thread_rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_forum_layout: undefined.UndefinedOr[typing.Union[channels_.ForumLayoutType, int]] = undefined.UNDEFINED,
        default_sort_order: undefined.UndefinedOr[
            typing.Union[channels_.ForumSortOrderType, int]
        ] = undefined.UNDEFINED,
        available_tags: undefined.UndefinedOr[typing.Sequence[channels_.ForumTag]] = undefined.UNDEFINED,
        default_reaction_emoji: typing.Union[
            str, emojis.Emoji, undefined.UndefinedType, snowflakes.Snowflake, None
        ] = undefined.UNDEFINED,
        archived: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        locked: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        invitable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        applied_tags: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[channels_.ForumTag]] = undefined.UNDEFINED,
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
        name : hikari.undefined.UndefinedOr[str]
            If provided, the new name for the channel.
        flags : hikari.undefined.UndefinedOr[hikari.channels.ChannelFlag]
            If provided, the new channel flags to use for the channel. This can
            only be used on a forum channel to apply [`hikari.channels.ChannelFlag.REQUIRE_TAG`][], or
            on a forum thread to apply [`hikari.channels.ChannelFlag.PINNED`][].
        position : hikari.undefined.UndefinedOr[int]
            If provided, the new position for the channel.
        topic : hikari.undefined.UndefinedOr[str]
            If provided, the new topic for the channel.
        nsfw : hikari.undefined.UndefinedOr[bool]
            If provided, whether the channel should be marked as NSFW or not.
        bitrate : hikari.undefined.UndefinedOr[int]
            If provided, the new bitrate for the channel.
        video_quality_mode : hikari.undefined.UndefinedOr[typing.Union[hikari.channels.VideoQualityMode, int]]
            If provided, the new video quality mode for the channel.
        user_limit : hikari.undefined.UndefinedOr[int]
            If provided, the new user limit in the channel.
        rate_limit_per_user : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the new rate limit per user in the channel.
        region : hikari.undefined.UndefinedNoneOr[typing.Union[str, hikari.voices.VoiceRegion]]
            If provided, the voice region to set for this channel. Passing
            [`None`][] here will set it to "auto" mode where the used
            region will be decided based on the first person who connects to it
            when it's empty.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the new permission overwrites for the channel.
        parent_category : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildCategory]]
            If provided, the new guild category for the channel.
        default_auto_archive_duration : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the auto archive duration Discord's end user client
            should default to when creating threads in this channel.

            This should be either 60, 1440, 4320 or 10080 minutes and, as of
            writing, ignores the parent channel's set default_auto_archive_duration
            when passed as [`hikari.undefined.UNDEFINED`][].
        default_thread_rate_limit_per_user : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the ratelimit that should be set in threads derived
            from this channel.

            This only applies to forum channels.
        default_forum_layout : hikari.undefined.UndefinedOr[typing.Union[hikari.channels.ForumLayoutType, int]]
            If provided, the default forum layout to show in the client.
        default_sort_order : hikari.undefined.UndefinedOr[typing.Union[hikari.channels.ForumSortOrderType, int]]
            If provided, the default sort order to show in the client.
        available_tags : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.ForumTag]]
            If provided, the new available tags to select from when creating a thread.

            This only applies to forum channels.
        default_reaction_emoji : typing.Union[str, hikari.emojis.Emoji, hikari.undefined.UndefinedType, hikari.snowflakes.Snowflake]
            If provided, the new default reaction emoji for threads created in a forum channel.

            This only applies to forum channels.
        archived : hikari.undefined.UndefinedOr[bool]
            If provided, the new archived state for the thread. This only
            applies to threads.
        locked : hikari.undefined.UndefinedOr[bool]
            If provided, the new locked state for the thread. This only applies
            to threads.

            If it's locked then only people with [`hikari.permissions.Permissions.MANAGE_THREADS`][] can unarchive it.
        invitable : undefined.UndefinedOr[bool]
            If provided, the new setting for whether non-moderators can invite
            new members to a private thread. This only applies to threads.
        auto_archive_duration : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the new auto archive duration for this thread. This
            only applies to threads.

            This should be either 60, 1440, 4320 or 10080 minutes, as of
            writing.
        applied_tags : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.channels.ForumTag]]
            If provided, the new tags to apply to the thread. This only applies
            to threads in a forum channel.
        reason : hikari.undefined.UndefinedOr[str]
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_WEBHOOKS`][] permission in the target
            channel or are missing the [`hikari.permissions.Permissions.VIEW_CHANNEL`][] permission in the origin
            channel.
        hikari.errors.NotFoundError
            If the origin or target channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_channel(
        self, channel: snowflakes.SnowflakeishOr[channels_.PartialChannel]
    ) -> channels_.PartialChannel:
        """Delete a channel in a guild, or close a DM.

        !!! note
            For Public servers, the set 'Rules' or 'Guidelines' channels and the
            'Public Server Updates' channel cannot be deleted.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            The channel to delete. This may be the object or the ID of an
            existing channel.

        Returns
        -------
        hikari.channels.PartialChannel
            Object of the channel that was deleted.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_my_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels_.GuildStageChannel],
        *,
        suppress: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        request_to_speak: typing.Union[undefined.UndefinedType, bool, datetime.datetime] = undefined.UNDEFINED,
    ) -> None:
        """Edit the current user's voice state in a stage channel.

        !!! note
            The current user has to have already joined the target stage channel
            before any calls can be made to this endpoint.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or Id of the guild to edit a voice state in.
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildStageChannel]
            Object or Id of the channel to edit a voice state in.

        Other Parameters
        ----------------
        suppress : hikari.undefined.UndefinedOr[bool]
            If specified, whether the user should be allowed to become a speaker
            in the target stage channel with [`True`][] suppressing them from
            becoming one.
        request_to_speak : typing.Union[hikari.undefined.UndefinedType, bool, datetime.datetime]
            Whether to request to speak. This may be one of the following:

            * [`True`][] to indicate that the bot wants to speak.
            * [`False`][] to remove any previously set request to speak.
            * [`datetime.datetime`][] to specify when they want their request to
                speak timestamp to be set to. If a datetime from the past is
                passed then Discord will use the current time instead.

        Raises
        ------
        hikari.errors.BadRequestError
            If you try to target a non-staging channel.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MUTE_MEMBERS`][] permission in the channel.
        hikari.errors.NotFoundError
            If the channel, message or voice state is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels_.GuildStageChannel],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        suppress: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> None:
        """Edit an existing voice state in a stage channel.

        !!! note
            The target user must already be present in the stage channel before
            any calls are made to this endpoint.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to edit a voice state in.
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildStageChannel]
            Object or ID of the channel to edit a voice state in.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user to edit the voice state of.

        Other Parameters
        ----------------
        suppress : hikari.undefined.UndefinedOr[bool]
            If defined, whether the user should be allowed to become a speaker
            in the target stage channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If you try to target a non-staging channel.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MUTE_MEMBERS`][] permission in the channel.
        hikari.errors.NotFoundError
            If the channel, message or voice state is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @typing.overload
    @abc.abstractmethod
    async def edit_permission_overwrite(
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
    async def edit_permission_overwrite(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
        target: snowflakes.Snowflakeish,
        *,
        target_type: typing.Union[channels_.PermissionOverwriteType, int],
        allow: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        deny: undefined.UndefinedOr[permissions_.Permissions] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Edit permissions for a given entity ID and type."""

    @abc.abstractmethod
    async def edit_permission_overwrite(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
        target: typing.Union[
            snowflakes.Snowflakeish, users.PartialUser, guilds.PartialRole, channels_.PermissionOverwrite
        ],
        *,
        target_type: undefined.UndefinedOr[typing.Union[channels_.PermissionOverwriteType, int]] = undefined.UNDEFINED,
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
        target_type : hikari.undefined.UndefinedOr[typing.Union[hikari.channels.PermissionOverwriteType, int]]
            If provided, the type of the target to update. If unset, will attempt to get
            the type from `target`.
        allow : hikari.undefined.UndefinedOr[hikari.permissions.Permissions]
            If provided, the new value of all allowed permissions.
        deny : hikari.undefined.UndefinedOr[hikari.permissions.Permissions]
            If provided, the new value of all disallowed permissions.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        TypeError
            If `target_type` is unset and we were unable to determine the type
            from `target`.
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`MANAGE_PERMISSIONS`][hikari.permissions.Permissions.MANAGE_ROLES]
            permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found or the target is not found if it is
            a role.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def delete_permission_overwrite(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildChannel],
        target: typing.Union[
            channels_.PermissionOverwrite, guilds.PartialRole, users.PartialUser, snowflakes.Snowflakeish
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
            If you are missing the [`MANAGE_PERMISSIONS`][hikari.permissions.Permissions.MANAGE_ROLES]
            permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found or the target is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission in the channel.
        hikari.errors.NotFoundError
            If the channel is not found in any guilds you are a member of.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        target_type: undefined.UndefinedOr[invites.TargetType] = undefined.UNDEFINED,
        target_user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        target_application: undefined.UndefinedOr[
            snowflakes.SnowflakeishOr[guilds.PartialApplication]
        ] = undefined.UNDEFINED,
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
        max_age : hikari.undefined.UndefinedOr[typing.Union[datetime.timedelta, float, int]]
            If provided, the duration of the invite before expiry.
        max_uses : hikari.undefined.UndefinedOr[int]
            If provided, the max uses the invite can have.
        temporary : hikari.undefined.UndefinedOr[bool]
            If provided, whether the invite only grants temporary membership.
        unique : hikari.undefined.UndefinedOr[bool]
            If provided, whether the invite should be unique.
        target_type : hikari.undefined.UndefinedOr[hikari.invites.TargetType]
            If provided, the target type of this invite.
        target_user : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]]
            If provided, the target user id for this invite. This may be the
            object or the ID of an existing user.

            !!! note
                This is required if `target_type` is [`hikari.invites.TargetType.STREAM`][] and the targeted
                user must be streaming into the channel.
        target_application : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]]
            If provided, the target application id for this invite. This may be
            the object or the ID of an existing application.

            !!! note
                This is required if `target_type` is [`hikari.invites.TargetType.EMBEDDED_APPLICATION`][] and
                the targeted application must have the [`hikari.applications.ApplicationFlags.EMBEDDED`][] flag.
        reason : hikari.undefined.UndefinedOr[str]
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission.
        hikari.errors.NotFoundError
            If the channel is not found, or if the target user does not exist,
            if provided.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def trigger_typing(
        self, channel: snowflakes.SnowflakeishOr[channels_.TextableChannel]
    ) -> special_endpoints.TypingIndicator:
        """Trigger typing in a text channel.

        !!! note
            The result of this call can be awaited to trigger typing once, or
            can be used as an async context manager to continually type until the
            context manager is left. Any errors documented below will happen then.

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
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
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
            If you are missing the [`hikari.permissions.Permissions.SEND_MESSAGES`][] in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_pins(
        self, channel: snowflakes.SnowflakeishOr[channels_.TextableChannel]
    ) -> typing.Sequence[messages_.Message]:
        """Fetch the pinned messages in this text channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
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
            If you are missing the [`hikari.permissions.Permissions.VIEW_CHANNEL`][] in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def pin_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        """Pin an existing message in the given text channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_MESSAGES`][] in the channel.
        hikari.errors.NotFoundError
            If the channel is not found, or if the message does not exist in
            the given channel.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def unpin_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        """Unpin a given message from a given text channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_MESSAGES`][] permission.
        hikari.errors.NotFoundError
            If the channel is not found or the message is not a pinned message
            in the given channel.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_messages(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        *,
        before: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        after: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        around: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[messages_.Message]:
        """Browse the message history for a given text channel.

        !!! note
            This call is not a coroutine function, it returns a special type of
            lazy iterator that will perform API calls as you iterate across it,
            thus any errors documented below will happen then.

            See [`hikari.iterators`][] for the full API for this iterator type.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
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

        Raises
        ------
        TypeError
            If you specify more than one of `before`, `after`, `about`.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.READ_MESSAGE_HISTORY`][] in the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> messages_.Message:
        """Fetch a specific message in the given text channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
            The channel to fetch messages in. This may be the object or
            the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to fetch. This may be the object or the ID of an
            existing message.

        Returns
        -------
        hikari.messages.Message
            The requested message.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.READ_MESSAGE_HISTORY`][] in the channel.
        hikari.errors.NotFoundError
            If the channel is not found or the message is not found in the
            given text channel.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        sticker: undefined.UndefinedOr[snowflakes.SnowflakeishOr[stickers_.PartialSticker]] = undefined.UNDEFINED,
        stickers: undefined.UndefinedOr[
            snowflakes.SnowflakeishSequence[stickers_.PartialSticker]
        ] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        reply: undefined.UndefinedOr[snowflakes.SnowflakeishOr[messages_.PartialMessage]] = undefined.UNDEFINED,
        reply_must_exist: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
        flags: typing.Union[undefined.UndefinedType, int, messages_.MessageFlag] = undefined.UNDEFINED,
    ) -> messages_.Message:
        """Create a message in the given channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
            The channel to create the message in.
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message contents. If
            [`hikari.undefined.UNDEFINED`][], then nothing will be sent
            in the content. Any other value here will be cast to a
            [`str`][].

            If this is a [`hikari.embeds.Embed`][] and no `embed` nor `embeds` kwarg
            is provided, then this will instead update the embed. This allows
            for simpler syntax when sending an embed alone.

            Likewise, if this is a [`hikari.files.Resource`][], then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.

        Other Parameters
        ----------------
        attachment : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            If provided, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.

            Attachments can be passed as many different things, to aid in
            convenience.

            - If a [`pathlib.PurePath`][] or [`str`][] to a valid URL, the
                resource at the given URL will be streamed to Discord when
                sending the message. Subclasses of
                [`hikari.files.WebResource`][] such as
                [`hikari.files.URL`][],
                [`hikari.messages.Attachment`][],
                [`hikari.emojis.Emoji`][],
                [`hikari.embeds.EmbedResource`][], etc will also be uploaded this way.
                This will use bit-inception, so only a small percentage of the
                resource will remain in memory at any one time, thus aiding in
                scalability.
            - If a [`hikari.files.Bytes`][] is passed, or a [`str`][]
                that contains a valid data URI is passed, then this is uploaded
                with a randomized file name if not provided.
            - If a [`hikari.files.File`][], [`pathlib.PurePath`][] or
                [`str`][] that is an absolute or relative path to a file
                on your file system is passed, then this resource is uploaded
                as an attachment using non-blocking code internally and streamed
                using bit-inception where possible. This depends on the
                type of [`concurrent.futures.Executor`][] that is being used for
                the application (default is a thread pool which supports this
                behaviour).
        attachments : hikari.undefined.UndefinedOr[typing.Sequence[hikari.files.Resourceish]]
            If provided, the message attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        component : hikari.undefined.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder]
            If provided, builder object of the component to include in this message.
        components : hikari.undefined.UndefinedOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            If provided, a sequence of the component builder objects to include
            in this message.
        embed : hikari.undefined.UndefinedOr[hikari.embeds.Embed]
            If provided, the message embed.
        embeds : hikari.undefined.UndefinedOr[typing.Sequence[hikari.embeds.Embed]]
            If provided, the message embeds.
        sticker : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.stickers.PartialSticker]]
            If provided, the object or ID of a sticker to send on the message.

            As of writing, bots can only send custom stickers from the current guild.
        stickers : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.stickers.PartialSticker]]
            If provided, a sequence of the objects and IDs of up to 3 stickers
            to send on the message.

            As of writing, bots can only send custom stickers from the current guild.
        tts : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message will be read out by a screen
            reader using Discord's TTS (text-to-speech) system.
        reply : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]]
            If provided, the message to reply to.
        reply_must_exist : hikari.undefined.UndefinedOr[bool]
            If provided, whether to error if the message being replied to does
            not exist instead of sending as a normal (non-reply) message.

            This will not do anything if not being used with `reply`.
        mentions_everyone : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message should parse @everyone/@here
            mentions.
        mentions_reply : hikari.undefined.UndefinedOr[bool]
            If provided, whether to mention the author of the message
            that is being replied to.

            This will not do anything if not being used with `reply`.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], bool]]
            If provided, and [`True`][], all user mentions will be detected.
            If provided, and [`False`][], all user mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.users.PartialUser`][] derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], bool]]
            If provided, and [`True`][], all role mentions will be detected.
            If provided, and [`False`][], all role mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.guilds.PartialRole`][] derivatives to enforce mentioning
            specific roles.
        flags : hikari.undefined.UndefinedOr[hikari.messages.MessageFlag]
            If provided, optional flags to set on the message. If
            [`hikari.undefined.UNDEFINED`][], then nothing is changed.

            Note that some flags may not be able to be set. Currently the only
            flags that can be set are [hikari.messages.MessageFlag.SUPPRESS_NOTIFICATIONS] and
            [hikari.messages.MessageFlag.SUPPRESS_EMBEDS].

        Returns
        -------
        hikari.messages.Message
            The created message.

        Raises
        ------
        ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions` or if both `attachment` and
            `attachments`, `component` and `components` or `embed` and `embeds`
            are specified.
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no attachments or embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; too many attachments; attachments that are too large;
            invalid image URLs in embeds; if `reply` is not found or not in the
            same channel as `channel`; too many components.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [hikari.permissions.Permissions.SEND_MESSAGES]
            in the channel or the person you are trying to message has the DM's
            disabled.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
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
            [`hikari.permissions.Permissions.SEND_MESSAGES`][] permission for the
            target news channel or try to crosspost a message by another user
            without both the [`hikari.permissions.Permissions.SEND_MESSAGES`][]
            and [`hikari.permissions.Permissions.MANAGE_MESSAGES`][] permissions
            for the target channel.
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedNoneOr[
            typing.Union[files.Resourceish, messages_.Attachment]
        ] = undefined.UNDEFINED,
        attachments: undefined.UndefinedNoneOr[
            typing.Sequence[typing.Union[files.Resourceish, messages_.Attachment]]
        ] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
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

        !!! warning
            If the message was not sent by your user, the only parameter
            you may provide to this call is the `flags` parameter. Anything
            else will result in a [`hikari.errors.ForbiddenError`][] being raised.

        !!! note
            Mentioning everyone, roles, or users in message edits currently
            will not send a push notification showing a new mention to people
            on Discord. It will still highlight in their chat as if they
            were mentioned, however.

            Also important to note that if you specify a text `content`, `mentions_everyone`,
            `mentions_reply`, `user_mentions`, and `role_mentions` will default
            to [`False`][] as the message will be re-parsed for mentions. This will
            also occur if only one of the four are specified

            This is a limitation of Discord's design. If in doubt, specify all
            four of them each time.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
            The channel to create the message in. This may be
            the object or the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to edit. This may be the object or the ID
            of an existing message.
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message content to update with. If
            [`hikari.undefined.UNDEFINED`][], then the content will not
            be changed. If [`None`][], then the content will be removed.

            Any other value will be cast to a [`str`][] before sending.

            If this is a [`hikari.embeds.Embed`][] and neither the `embed` or
            `embeds` kwargs are provided or if this is a
            [`hikari.files.Resourceish`][] and neither the
            `attachment` or `attachments` kwargs are provided, the values will
            be overwritten. This allows for simpler syntax when sending an
            embed or an attachment alone.

        Other Parameters
        ----------------
        attachment : hikari.undefined.UndefinedNoneOr[typing.Union[hikari.files.Resourceish, hikari.messages.Attachment]]
            If provided, the attachment to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous attachment, if
            present, is not changed. If this is [`None`][], then the
            attachment is removed, if present. Otherwise, the new attachment
            that was provided will be attached.
        attachments : hikari.undefined.UndefinedNoneOr[typing.Sequence[typing.Union[hikari.files.Resourceish, hikari.messages.Attachment]]]
            If provided, the attachments to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous attachments, if
            present, are not changed. If this is [`None`][], then the
            attachments is removed, if present. Otherwise, the new attachments
            that were provided will be attached.
        component : hikari.undefined.UndefinedNoneOr[hikari.api.special_endpoints.ComponentBuilder]
            If provided, builder object of the component to set for this message.
            This component will replace any previously set components and passing
            [`None`][] will remove all components.
        components : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            If provided, a sequence of the component builder objects set for
            this message. These components will replace any previously set
            components and passing [`None`][] or an empty sequence will
            remove all components.
        embed : hikari.undefined.UndefinedNoneOr[hikari.embeds.Embed]
            If provided, the embed to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous embed(s) are not changed.
            If this is [`None`][] then any present embeds are removed.
            Otherwise, the new embed that was provided will be used as the
            replacement.
        embeds : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.embeds.Embed]]
            If provided, the embeds to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous embed(s) are not changed.
            If this is [`None`][] then any present embeds are removed.
            Otherwise, the new embeds that were provided will be used as the
            replacement.
        mentions_everyone : hikari.undefined.UndefinedOr[bool]
            If provided, sanitation for `@everyone` mentions. If
            [`hikari.undefined.UNDEFINED`][], then the previous setting is
            not changed. If [`True`][], then `@everyone`/`@here` mentions
            in the message content will show up as mentioning everyone that can
            view the chat.
        mentions_reply : hikari.undefined.UndefinedOr[bool]
            If provided, whether to mention the author of the message
            that is being replied to.

            This will not do anything if `message` is not a reply message.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], bool]]
            If provided, sanitation for user mentions. If
            [`hikari.undefined.UNDEFINED`][], then the previous setting is
            not changed. If [`True`][], all valid user mentions will behave
            as mentions. If [`False`][], all valid user mentions will not
            behave as mentions.

            You may alternatively pass a collection of
            [`hikari.snowflakes.Snowflake`][] user IDs, or
            [`hikari.users.PartialUser`][]-derived objects.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], bool]]
            If provided, sanitation for role mentions. If
            [`hikari.undefined.UNDEFINED`][], then the previous setting is
            not changed. If [`True`][], all valid role mentions will behave
            as mentions. If [`False`][], all valid role mentions will not
            behave as mentions.

            You may alternatively pass a collection of
            [hikari.snowflakes.Snowflake] role IDs, or
            [hikari.guilds.PartialRole]-derived objects.
        flags : hikari.undefined.UndefinedOr[hikari.messages.MessageFlag]
            If provided, optional flags to set on the message. If
            [`hikari.undefined.UNDEFINED`][], then nothing is changed.

            Note that some flags may not be able to be set. Currently the only
            flags that can be set are [`hikari.messages.MessageFlag.NONE`][] and
            [`hikari.messages.MessageFlag.SUPPRESS_EMBEDS`][]. If you
            have [`hikari.permissions.Permissions.MANAGE_MESSAGES`][] permissions, you
            can use this call to suppress embeds on another user's message.

        Returns
        -------
        hikari.messages.Message
            The edited message.

        Raises
        ------
        ValueError
            If both `attachment` and `attachments`, `component` and `components`
            or `embed` and `embeds` are specified.
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no embeds; messages with more than 2000 characters
            in them, embeds that exceed one of the many embed
            limits; invalid image URLs in embeds.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.SEND_MESSAGES`][] in the channel; if you try to
            change the contents of another user's message; or if you try to edit
            the flags on another user's message without the [`hikari.permissions.Permissions.MANAGE_MESSAGES`][]
            permission.
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def delete_message(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        """Delete a given message in a given channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_MESSAGES`][], and the message is
            not sent by you.
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_messages(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        messages: typing.Union[
            snowflakes.SnowflakeishOr[messages_.PartialMessage],
            typing.Iterable[snowflakes.SnowflakeishOr[messages_.PartialMessage]],
            typing.AsyncIterable[snowflakes.SnowflakeishOr[messages_.PartialMessage]],
        ],
        /,
        *other_messages: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        """Bulk-delete messages from the channel.

        !!! note
            This API endpoint will only be able to delete 100 messages
            at a time. For anything more than this, multiple requests will
            be executed one-after-the-other, since the rate limits for this
            endpoint do not favour more than one request per bucket.

            If one message is left over from chunking per 100 messages, or
            only one message is passed to this coroutine function, then the
            logic is expected to defer to `delete_message`. The implication
            of this is that the `delete_message` endpoint is rate limited
            by a different bucket with different usage rates.

        !!! warning
            This endpoint is not atomic. If an error occurs midway through
            a bulk delete, you will **not** be able to revert any changes made
            up to this point.

        !!! warning
            Specifying any messages more than 14 days old will cause the call
            to fail, potentially with partial completion.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
            The channel to bulk delete the messages in. This may be
            the object or the ID of an existing channel.
        messages
            Either the object/ID of an existing message to delete or an iterable
            (sync or async) of the objects and/or IDs of existing messages to delete.

        Other Parameters
        ----------------
        *other_messages : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The objects and/or IDs of other existing messages to delete.

        Raises
        ------
        hikari.errors.BulkDeleteError
            An error containing the messages successfully deleted, and the
            messages that were not removed. The
            [`BaseException.__cause__`][] of the exception will be the
            original error that terminated this process.
        """

    @abc.abstractmethod
    async def add_reaction(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        emoji: typing.Union[str, emojis.Emoji],
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis.CustomEmoji]] = undefined.UNDEFINED,
    ) -> None:
        """Add a reaction emoji to a message in a given channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
            The channel where the message to add the reaction to is. This
            may be a [`hikari.channels.TextableChannel`][] or the ID of an existing
            channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to add a reaction to. This may be the
            object or the ID of an existing message.
        emoji : typing.Union[str, hikari.emojis.Emoji]
            Object or name of the emoji to react with.

        Other Parameters
        ----------------
        emoji_id : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]]
            ID of the custom emoji to react with.
            This should only be provided when a custom emoji's name is passed
            for `emoji`.

        Raises
        ------
        hikari.errors.BadRequestError
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.ADD_REACTIONS`][] (this is only necessary if you
            are the first person to add the reaction).
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_my_reaction(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        emoji: typing.Union[str, emojis.Emoji],
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis.CustomEmoji]] = undefined.UNDEFINED,
    ) -> None:
        """Delete a reaction that your application user created.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
            The channel where the message to delete the reaction from is.
            This may be the object or the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to delete a reaction from. This may be the
            object or the ID of an existing message.
        emoji : typing.Union[str, hikari.emojis.Emoji]
            Object or name of the emoji to remove your reaction for.

        Other Parameters
        ----------------
        emoji_id : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]]
            ID of the custom emoji to remove your reaction for.
            This should only be provided when a custom emoji's name is passed
            for `emoji`.

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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_all_reactions_for_emoji(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        emoji: typing.Union[str, emojis.Emoji],
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis.CustomEmoji]] = undefined.UNDEFINED,
    ) -> None:
        """Delete all reactions for a single emoji on a given message.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
            The channel where the message to delete the reactions from is.
            This may be the object or the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to delete a reactions from. This may be the
            object or the ID of an existing message.
        emoji : typing.Union[str, hikari.emojis.Emoji]
            Object or name of the emoji to remove all the reactions for.

        Other Parameters
        ----------------
        emoji_id : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]]
            ID of the custom emoji to remove all the reactions for.
            This should only be provided when a custom emoji's name is passed
            for `emoji`.

        Raises
        ------
        hikari.errors.BadRequestError
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_MESSAGES`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_reaction(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        emoji: typing.Union[str, emojis.Emoji],
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis.CustomEmoji]] = undefined.UNDEFINED,
    ) -> None:
        """Delete a reaction from a message.

        If you are looking to delete your own applications reaction, use
        `delete_my_reaction`.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
            The channel where the message to delete the reaction from is.
            This may be the object or the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to delete a reaction from. This may be the
            object or the ID of an existing message.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user to remove the reaction of.
        emoji : typing.Union[str, hikari.emojis.Emoji]
            Object or name of the emoji to react with.

        Other Parameters
        ----------------
        emoji_id : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]]
            ID of the custom emoji to react with.
            This should only be provided when a custom emoji's name is passed
            for `emoji`.

        Raises
        ------
        hikari.errors.BadRequestError
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_MESSAGES`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_all_reactions(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
    ) -> None:
        """Delete all reactions from a message.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_MESSAGES`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the channel or message is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_reactions_for_emoji(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.TextableChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        emoji: typing.Union[str, emojis.Emoji],
        emoji_id: undefined.UndefinedOr[snowflakes.SnowflakeishOr[emojis.CustomEmoji]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[users.User]:
        """Fetch reactions for an emoji from a message.

        !!! note
            This call is not a coroutine function, it returns a special type of
            lazy iterator that will perform API calls as you iterate across it,
            thus any errors documented below will happen then.

            See [`hikari.iterators`][] for the full API for this iterator type.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.TextableChannel]
            The channel where the message to delete all reactions from is.
            This may be the object or the ID of an existing channel.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to delete all reaction from. This may be the
            object or the ID of an existing message.
        emoji : typing.Union[str, hikari.emojis.Emoji]
            Object or name of the emoji to get the reactions for.

        Other Parameters
        ----------------
        emoji_id : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]]
            ID of the custom emoji to get the reactions for.
            This should only be provided when a custom emoji's name is passed
            for `emoji`.

        Returns
        -------
        hikari.iterators.LazyIterator[hikari.users.User]
            An iterator to fetch the users.

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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_webhook(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.WebhookChannelT],
        name: str,
        *,
        avatar: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.IncomingWebhook:
        """Create webhook in a channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.WebhookChannelT]
            The channel where the webhook will be created. This may be
            the object or the ID of an existing channel.
        name : str
            The name for the webhook. This cannot be `clyde`.

        Other Parameters
        ----------------
        avatar : typing.Optional[hikari.files.Resourceish]
            If provided, the avatar for the webhook.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.webhooks.IncomingWebhook
            The created webhook.

        Raises
        ------
        hikari.errors.BadRequestError
            If `name` doesn't follow the restrictions enforced by discord.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_WEBHOOKS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_webhook(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.PartialWebhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.PartialWebhook:
        """Fetch an existing webhook.

        Parameters
        ----------
        webhook : hikari.snowflakes.SnowflakeishOr[hikari.webhooks.PartialWebhook]
            The webhook to fetch. This may be the object or the ID
            of an existing webhook.

        Other Parameters
        ----------------
        token : hikari.undefined.UndefinedOr[str]
            If provided, the webhook token that will be used to fetch
            the webhook instead of the token the client was initialized with.

        Returns
        -------
        hikari.webhooks.PartialWebhook
            The requested webhook.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_WEBHOOKS`][] permission when not
            using a token.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_channel_webhooks(
        self, channel: snowflakes.SnowflakeishOr[channels_.WebhookChannelT]
    ) -> typing.Sequence[webhooks.PartialWebhook]:
        """Fetch all channel webhooks.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.WebhookChannelT]
            The channel to fetch the webhooks for. This may be an instance of any
            of the classes which are valid for [`hikari.channels.WebhookChannelT`][]
            or the ID of an existing channel.

        Returns
        -------
        typing.Sequence[hikari.webhooks.PartialWebhook]
            The fetched webhooks.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_WEBHOOKS`][] permission.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_guild_webhooks(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[webhooks.PartialWebhook]:
        """Fetch all guild webhooks.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the webhooks for. This may be the object
            or the ID of an existing guild.

        Returns
        -------
        typing.Sequence[hikari.webhooks.PartialWebhook]
            The fetched webhooks.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_WEBHOOKS`][] permission.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_webhook(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.PartialWebhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        channel: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.WebhookChannelT]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> webhooks.PartialWebhook:
        """Edit a webhook.

        Parameters
        ----------
        webhook : hikari.snowflakes.SnowflakeishOr[hikari.webhooks.PartialWebhook]
            The webhook to edit. This may be the object or the
            ID of an existing webhook.

        Other Parameters
        ----------------
        token : hikari.undefined.UndefinedOr[str]
            If provided, the webhook token that will be used to edit
            the webhook instead of the token the client was initialized with.
        name : hikari.undefined.UndefinedOr[str]
            If provided, the new webhook name.
        avatar : hikari.undefined.UndefinedNoneOr[hikari.files.Resourceish]
            If provided, the new webhook avatar. If [`None`][], will
            remove the webhook avatar.
        channel : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.WebhookChannelT]]
            If provided, the text channel to move the webhook to.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.webhooks.PartialWebhook
            The edited webhook.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_WEBHOOKS`][] permission when not
            using a token.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_webhook(
        self,
        webhook: snowflakes.SnowflakeishOr[webhooks.PartialWebhook],
        *,
        token: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Delete a webhook.

        Parameters
        ----------
        webhook : hikari.snowflakes.SnowflakeishOr[hikari.webhooks.PartialWebhook]
            The webhook to delete. This may be the object or the
            ID of an existing webhook.

        Other Parameters
        ----------------
        token : hikari.undefined.UndefinedOr[str]
            If provided, the webhook token that will be used to delete
            the webhook instead of the token the client was initialized with.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_WEBHOOKS`][] permission when not
            using a token.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def execute_webhook(
        self,
        # MyPy might not say this but SnowflakeishOr[ExecutableWebhook] isn't valid as ExecutableWebhook isn't Unique
        webhook: typing.Union[webhooks.ExecutableWebhook, snowflakes.Snowflakeish],
        token: str,
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        thread: typing.Union[
            undefined.UndefinedType, snowflakes.SnowflakeishOr[channels_.GuildThreadChannel]
        ] = undefined.UNDEFINED,
        username: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        avatar_url: typing.Union[undefined.UndefinedType, str, files.URL] = undefined.UNDEFINED,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
        flags: typing.Union[undefined.UndefinedType, int, messages_.MessageFlag] = undefined.UNDEFINED,
    ) -> messages_.Message:
        """Execute a webhook.

        !!! warning
            At the time of writing, `username` and `avatar_url` are ignored for
            interaction webhooks.

            Additionally, [`hikari.messages.MessageFlag.SUPPRESS_EMBEDS`][], [`hikari.messages.MessageFlag.SUPPRESS_NOTIFICATIONS`][] and [`hikari.messages.MessageFlag.EPHEMERAL`][]
            are the only flags that can be set, with [`hikari.messages.MessageFlag.EPHEMERAL`][] limited to
            interaction webhooks.

        Parameters
        ----------
        webhook : typing.Union[hikari.snowflakes.Snowflakeish, hikari.webhooks.ExecutableWebhook]
            The webhook to execute. This may be the object
            or the ID of an existing webhook.
        token : str
            The webhook token.
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message contents. If
            [`hikari.undefined.UNDEFINED`][], then nothing will be sent
            in the content. Any other value here will be cast to a
            [`str`][].

            If this is a [`hikari.embeds.Embed`][] and no `embed` nor
            no `embeds` kwarg is provided, then this will instead
            update the embed. This allows for simpler syntax when
            sending an embed alone.

            Likewise, if this is a [`hikari.files.Resource`][], then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.

        Other Parameters
        ----------------
        thread : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildThreadChannel]]
            If provided then the message will be created in the target thread
            within the webhook's channel, otherwise it will be created in
            the webhook's target channel.

            This is required when trying to create a thread message.
        username : hikari.undefined.UndefinedOr[str]
            If provided, the username to override the webhook's username
            for this request.
        avatar_url : typing.Union[hikari.undefined.UndefinedType, hikari.files.URL, str]
            If provided, the url of an image to override the webhook's
            avatar with for this request.
        attachment : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            If provided, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.

            Attachments can be passed as many different things, to aid in
            convenience.

            - If a [`pathlib.PurePath`][] or [`str`][] to a valid URL, the
                resource at the given URL will be streamed to Discord when
                sending the message. Subclasses of
                [`hikari.files.WebResource`][] such as
                [`hikari.files.URL`][],
                [`hikari.messages.Attachment`][],
                [`hikari.emojis.Emoji`][],
                [`hikari.embeds.EmbedResource`][], etc. will also be uploaded this way.
                This will use bit-inception, so only a small percentage of the
                resource will remain in memory at any one time, thus aiding in
                scalability.
            - If a [hikari.files.Bytes] is passed, or a [`str`][]
                that contains a valid data URI is passed, then this is uploaded
                with a randomized file name if not provided.
            - If a [hikari.files.File], [`pathlib.PurePath`][] or
                [`str`][] that is an absolute or relative path to a file
                on your file system is passed, then this resource is uploaded
                as an attachment using non-blocking code internally and streamed
                using bit-inception where possible. This depends on the
                type of [`concurrent.futures.Executor`][] that is being used for
                the application (default is a thread pool which supports this
                behaviour).
        attachments : hikari.undefined.UndefinedOr[typing.Sequence[hikari.files.Resourceish]]
            If provided, the message attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        component : hikari.undefined.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder]
            If provided, builder object of the component to include in this message.
        components : hikari.undefined.UndefinedOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            If provided, a sequence of the component builder objects to include
            in this message.
        embed : hikari.undefined.UndefinedOr[hikari.embeds.Embed]
            If provided, the message embed.
        embeds : hikari.undefined.UndefinedOr[typing.Sequence[hikari.embeds.Embed]]
            If provided, the message embeds.
        tts : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message will be read out by a screen
            reader using Discord's TTS (text-to-speech) system.
        mentions_everyone : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message should parse @everyone/@here
            mentions.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], bool]]
            If provided, and [`True`][], all user mentions will be detected.
            If provided, and [`False`][], all user mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.users.PartialUser`][] derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], bool]]
            If provided, and [`True`][], all role mentions will be detected.
            If provided, and [`False`][], all role mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.guilds.PartialRole`][] derivatives to enforce mentioning
            specific roles.
        flags : typing.Union[hikari.undefined.UndefinedType, int, hikari.messages.MessageFlag]
            The flags to set for this webhook message.

        Returns
        -------
        hikari.messages.Message
            The created message.

        Raises
        ------
        ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions` or if both `attachment` and
            `attachments` or `embed` and `embeds` are specified.
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no attachments or embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; too many attachments; attachments that are too large;
            invalid image URLs in embeds; too many components.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def fetch_webhook_message(
        self,
        # MyPy might not say this but SnowflakeishOr[ExecutableWebhook] isn't valid as ExecutableWebhook isn't Unique
        webhook: typing.Union[webhooks.ExecutableWebhook, snowflakes.Snowflakeish],
        token: str,
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        *,
        thread: typing.Union[
            undefined.UndefinedType, snowflakes.SnowflakeishOr[channels_.GuildThreadChannel]
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        """Fetch an old message sent by the webhook.

        Parameters
        ----------
        webhook : typing.Union[hikari.snowflakes.Snowflakeish, hikari.webhooks.ExecutableWebhook]
            The webhook to execute. This may be the object
            or the ID of an existing webhook.
        token : str
            The webhook token.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to fetch. This may be the object or the ID of an
            existing channel.

        Other Parameters
        ----------------
        thread : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildThreadChannel]]
            If provided then the message will be fetched from the target thread
            within the webhook's channel, otherwise it will be fetched from
            the webhook's target channel.

            This is required when trying to fetch a thread message.

        Returns
        -------
        hikari.messages.Message
            The requested message.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook is not found or the webhook's message wasn't found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_webhook_message(
        self,
        # MyPy might not say this but SnowflakeishOr[ExecutableWebhook] isn't valid as ExecutableWebhook isn't Unique
        webhook: typing.Union[webhooks.ExecutableWebhook, snowflakes.Snowflakeish],
        token: str,
        message: snowflakes.SnowflakeishOr[messages_.Message],
        content: undefined.UndefinedNoneOr[typing.Any] = undefined.UNDEFINED,
        *,
        thread: typing.Union[
            undefined.UndefinedType, snowflakes.SnowflakeishOr[channels_.GuildThreadChannel]
        ] = undefined.UNDEFINED,
        attachment: undefined.UndefinedNoneOr[
            typing.Union[files.Resourceish, messages_.Attachment]
        ] = undefined.UNDEFINED,
        attachments: undefined.UndefinedNoneOr[
            typing.Sequence[typing.Union[files.Resourceish, messages_.Attachment]]
        ] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
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

         !!! note
            Mentioning everyone, roles, or users in message edits currently
            will not send a push notification showing a new mention to people
            on Discord. It will still highlight in their chat as if they
            were mentioned, however.

            Also important to note that if you specify a text `content`, `mentions_everyone`,
            `mentions_reply`, `user_mentions`, and `role_mentions` will default
            to [`False`][] as the message will be re-parsed for mentions. This will
            also occur if only one of the four are specified

            This is a limitation of Discord's design. If in doubt, specify all
            four of them each time.

        Parameters
        ----------
        webhook : typing.Union[hikari.snowflakes.Snowflakeish, hikari.webhooks.ExecutableWebhook]
            The webhook to execute. This may be the object
            or the ID of an existing webhook.
        token : str
            The webhook token.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to delete. This may be the object or the ID of
            an existing message.
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message content to update with. If
            [`hikari.undefined.UNDEFINED`][], then the content will not
            be changed. If [`None`][], then the content will be removed.

            Any other value will be cast to a [`str`][] before sending.

            If this is a [`hikari.embeds.Embed`][] and neither the
            `embed` or `embeds` kwargs are provided or if this is a
            [`hikari.files.Resourceish`][] and neither the `attachment` or
            `attachments` kwargs are provided, the values will be overwritten.
            This allows for simpler syntax when sending an embed or an
            attachment alone.

        Other Parameters
        ----------------
        thread : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildThreadChannel]]
            If provided then the message will be edited in the target thread
            within the webhook's channel, otherwise it will be edited in
            the webhook's target channel.

            This is required when trying to edit a thread message.
        attachment : hikari.undefined.UndefinedNoneOr[typing.Union[hikari.files.Resourceish, hikari.messages.Attachment]]
            If provided, the attachment to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous attachment, if
            present, is not changed. If this is [`None`][], then the
            attachment is removed, if present. Otherwise, the new attachment
            that was provided will be attached.
        attachments : hikari.undefined.UndefinedNoneOr[typing.Sequence[typing.Union[hikari.files.Resourceish, hikari.messages.Attachment]]]
            If provided, the attachments to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous attachments, if
            present, are not changed. If this is [`None`][], then the
            attachments is removed, if present. Otherwise, the new attachments
            that were provided will be attached.
        component : hikari.undefined.UndefinedNoneOr[hikari.api.special_endpoints.ComponentBuilder]
            If provided, builder object of the component to set for this message.
            This component will replace any previously set components and passing
            [`None`][] will remove all components.
        components : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            If provided, a sequence of the component builder objects set for
            this message. These components will replace any previously set
            components and passing [`None`][] or an empty sequence will
            remove all components.
        embed : hikari.undefined.UndefinedNoneOr[hikari.embeds.Embed]
            If provided, the embed to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous embed(s) are not changed.
            If this is [`None`][] then any present embeds are removed.
            Otherwise, the new embed that was provided will be used as the
            replacement.
        embeds : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.embeds.Embed]]
            If provided, the embeds to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous embed(s) are not changed.
            If this is [`None`][] then any present embeds are removed.
            Otherwise, the new embeds that were provided will be used as the
            replacement.
        mentions_everyone : hikari.undefined.UndefinedOr[bool]
            If provided, sanitation for `@everyone` mentions. If
            [`hikari.undefined.UNDEFINED`][], then the previous setting is
            not changed. If [`True`][], then `@everyone`/`@here` mentions
            in the message content will show up as mentioning everyone that can
            view the chat.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], bool]]
            If provided, and [`True`][], all user mentions will be detected.
            If provided, and [`False`][], all user mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.users.PartialUser`][] derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], bool]]
            If provided, and [`True`][], all role mentions will be detected.
            If provided, and [`False`][], all role mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.guilds.PartialRole`][] derivatives to enforce mentioning
            specific roles.

        Returns
        -------
        hikari.messages.Message
            The edited message.

        Raises
        ------
        ValueError
            If both `attachment` and `attachments`, `component` and `components`
            or `embed` and `embeds` are specified.
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no attachments or embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; too many attachments; attachments that are too large;
            invalid image URLs in embeds; too many components.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook or the message are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def delete_webhook_message(
        self,
        # MyPy might not say this but SnowflakeishOr[ExecutableWebhook] isn't valid as ExecutableWebhook isn't Unique
        webhook: typing.Union[webhooks.ExecutableWebhook, snowflakes.Snowflakeish],
        token: str,
        message: snowflakes.SnowflakeishOr[messages_.Message],
        *,
        thread: typing.Union[
            undefined.UndefinedType, snowflakes.SnowflakeishOr[channels_.GuildThreadChannel]
        ] = undefined.UNDEFINED,
    ) -> None:
        """Delete a given message in a given channel.

        Parameters
        ----------
        webhook : typing.Union[hikari.snowflakes.Snowflakeish, hikari.webhooks.ExecutableWebhook]
            The webhook to execute. This may be the object
            or the ID of an existing webhook.
        token : str
            The webhook token.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            The message to delete. This may be the object or the ID of
            an existing message.

        Other Parameters
        ----------------
        thread : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildThreadChannel]]
            If provided then the message will be deleted from the target thread
            within the webhook's channel, otherwise it will be deleted from
            the webhook's target channel.

            This is required when trying to delete a thread message.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the webhook or the message are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_gateway_bot_info(self) -> sessions.GatewayBotInfo:
        """Fetch the gateway info for the bot.

        Returns
        -------
        hikari.sessions.GatewayBotInfo
            The gateway bot information.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_invite(
        self, invite: typing.Union[invites.InviteCode, str], with_counts: bool = True, with_expiration: bool = True
    ) -> invites.Invite:
        """Fetch an existing invite.

        Parameters
        ----------
        invite : typing.Union[hikari.invites.InviteCode, str]
            The invite to fetch. This may be an invite object or
            the code of an existing invite.
        with_counts : bool
            Whether the invite should contain the approximate member counts.
        with_expiration: bool
            Whether the invite should contain the expiration date.

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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_invite(self, invite: typing.Union[invites.InviteCode, str]) -> invites.Invite:
        """Delete an existing invite.

        Parameters
        ----------
        invite : typing.Union[hikari.invites.InviteCode, str]
            The invite to delete. This may be an invite object or
            the code of an existing invite.

        Returns
        -------
        hikari.invites.Invite
            Object of the invite that was deleted.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][] permission in the guild
            the invite is from or if you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][]
            permission in the channel the invite is from.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the invite is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        username : undefined.UndefinedOr[str]
            If provided, the new username.
        avatar : undefined.UndefinedNoneOr[hikari.files.Resourceish]
            If provided, the new avatar. If [`None`][],
            the avatar will be removed.

        Returns
        -------
        hikari.users.OwnUser
            The edited token's associated user.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.

            Discord also returns this on a rate limit:
            <https://github.com/discord/discord-api-docs/issues/1462>
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

        !!! note
            This call is not a coroutine function, it returns a special type of
            lazy iterator that will perform API calls as you iterate across it,
            thus any errors documented below will happen then.

            See [`hikari.iterators`][] for the full API for this iterator type.

        Other Parameters
        ----------------
        newest_first : bool
            Whether to fetch the newest first or the oldest first.
        start_at : hikari.undefined.UndefinedOr[hikari.snowflakes.SearchableSnowflakeishOr[hikari.guilds.PartialGuild]]
            If provided, will start at this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake. This
            may also be a guild object. In this case, the
            date the object was first created will be used.

        Returns
        -------
        hikari.iterators.LazyIterator[hikari.applications.OwnGuild]
            The token's associated guilds.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_my_user_application_role_connection(
        self, application: snowflakes.SnowflakeishOr[guilds.PartialApplication]
    ) -> applications.OwnApplicationRoleConnection:
        """Fetch the token's associated role connections.

        !!! note
            This requires the token to have the
            [`hikari.applications.OAuth2Scope.ROLE_CONNECTIONS_WRITE`][] scope enabled.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.applications.PartialApplication]
            The application to fetch the application role connections for.

        Returns
        -------
        hikari.applications.OwnApplicationRoleConnection
            The requested role connection.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the application is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def set_my_user_application_role_connection(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        platform_name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        platform_username: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        metadata: undefined.UndefinedOr[
            typing.Mapping[str, typing.Union[str, int, bool, datetime.datetime]]
        ] = undefined.UNDEFINED,
    ) -> applications.OwnApplicationRoleConnection:
        """Set the token's associated role connections.

        !!! note
            This requires the token to have the
            [`hikari.applications.OAuth2Scope.ROLE_CONNECTIONS_WRITE`][] scope enabled.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.applications.PartialApplication]
            The application to set the application role connections for.

        Other Parameters
        ----------------
        platform_name : hikari.undefined.UndefinedOr[str]
            If provided, the name of the platform that will be connected.
        platform_username : hikari.undefined.UndefinedOr[str]
            If provided, the name of the user in the platform.
        metadata : hikari.undefined.UndefinedOr[typing.Mapping[str, typing.Union[str, int, bool, datetime.datetime]]
            If provided, the role connection metadata.

            Depending on the time of the previously created application role
            records through `set_application_role_connection_metadata_records`,
            this mapping should contain those keys to the valid type of the record:

                - `INTEGER_X`: An [`int`][].
                - `DATETIME_X`: A [`datetime.datetime`][] object.
                - `BOOLEAN_X`: A [`bool`][].

        Returns
        -------
        hikari.applications.OwnApplicationRoleConnection
            The set role connection.

        Raises
        ------
        hikari.errors.BadRequestError
            If incorrect values are provided or unknown keys are provided in the metadata.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the application is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    # THIS IS AN OAUTH2 FLOW BUT CAN ALSO BE USED BY BOTS
    @abc.abstractmethod
    async def fetch_application(self) -> applications.Application:
        """Fetch the token's associated application.

        !!! warning
            This endpoint can only be used with a Bot token. Using this with a
            Bearer token will result in a [`hikari.errors.UnauthorizedError`][].

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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    # THIS IS AN OAUTH2 FLOW ONLY
    @abc.abstractmethod
    async def fetch_authorization(self) -> applications.AuthorizationInformation:
        """Fetch the token's authorization information.

        !!! warning
            This endpoint can only be used with a Bearer token. Using this
            with a Bot token will result in a [`hikari.errors.UnauthorizedError`][].

        Returns
        -------
        hikari.applications.AuthorizationInformation
            The token's authorization information.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_application_role_connection_metadata_records(
        self, application: snowflakes.SnowflakeishOr[guilds.PartialApplication]
    ) -> typing.Sequence[applications.ApplicationRoleConnectionMetadataRecord]:
        """Fetch the application role connection metadata records.

        !!! note
            This requires the token to have the
            [`hikari.applications.OAuth2Scope.ROLE_CONNECTIONS_WRITE`][] scope enabled.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.applications.PartialApplication]
            The application to fetch the application role connection metadata records for.

        Returns
        -------
        typing.Sequence[hikari.applications.ApplicationRoleConnectionMetadataRecord]
            The requested application role connection metadata records.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the application is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def set_application_role_connection_metadata_records(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        records: typing.Sequence[applications.ApplicationRoleConnectionMetadataRecord],
    ) -> typing.Sequence[applications.ApplicationRoleConnectionMetadataRecord]:
        """Set the application role connection metadata records.

        !!! note
            This requires the token to have the
            [`hikari.applications.OAuth2Scope.ROLE_CONNECTIONS_WRITE`][] scope enabled.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.applications.PartialApplication]
            The application to set the application role connection metadata records for.
        records : typing.Sequence[hikari.applications.ApplicationRoleConnectionMetadataRecord]
            The records to set for the application.

        Returns
        -------
        typing.Sequence[hikari.applications.ApplicationRoleConnectionMetadataRecord]
            The set application role connection metadata records.

        Raises
        ------
        hikari.errors.BadRequestError
            If incorrect values are provided for the records.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the application is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def authorize_client_credentials_token(
        self,
        client: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        client_secret: str,
        # While according to the spec scopes are optional here, Discord requires that "valid" scopes are passed.
        scopes: typing.Sequence[typing.Union[applications.OAuth2Scope, str]],
    ) -> applications.PartialOAuth2Token:
        """Authorize a client credentials token for an application.

        Parameters
        ----------
        client : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to authorize as.
        client_secret : str
            Secret of the application to authorize as.
        scopes : typing.Sequence[typing.Union[hikari.applications.OAuth2Scope, str]]
            The scopes to authorize for.

        Returns
        -------
        hikari.applications.PartialOAuth2Token
            Object of the authorized partial OAuth2 token.

        Raises
        ------
        hikari.errors.BadRequestError
            If invalid any invalid or malformed scopes are passed.
        hikari.errors.UnauthorizedError
            When an client or client secret is passed.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def authorize_access_token(
        self,
        client: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        client_secret: str,
        code: str,
        redirect_uri: str,
    ) -> applications.OAuth2AuthorizationToken:
        """Authorize an OAuth2 token using the authorize code grant type.

        Parameters
        ----------
        client : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to authorize with.
        client_secret : str
            Secret of the application to authorize with.
        code : str
            The authorization code to exchange for an OAuth2 access token.
        redirect_uri : str
            The redirect uri that was included in the authorization request.

        Returns
        -------
        hikari.applications.OAuth2AuthorizationToken
            Object of the authorized OAuth2 token.

        Raises
        ------
        hikari.errors.BadRequestError
            If an invalid redirect uri or code is passed.
        hikari.errors.UnauthorizedError
            When an client or client secret is passed.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def refresh_access_token(
        self,
        client: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        client_secret: str,
        refresh_token: str,
        *,
        scopes: undefined.UndefinedOr[
            typing.Sequence[typing.Union[applications.OAuth2Scope, str]]
        ] = undefined.UNDEFINED,
    ) -> applications.OAuth2AuthorizationToken:
        """Refresh an access token.

        !!! warning
            As of writing this Discord currently ignores any passed scopes,
            therefore you should use
            [`hikari.applications.OAuth2AuthorizationToken.scopes`][] to validate
            that the expected scopes were actually authorized here.

        Parameters
        ----------
        client : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to authorize with.
        client_secret : str
            Secret of the application to authorize with.
        refresh_token : str
            The refresh token to use.

        Other Parameters
        ----------------
        scopes : typing.Sequence[typing.Union[hikari.applications.OAuth2Scope, str]]
            The scope of the access request.

        Returns
        -------
        hikari.applications.OAuth2AuthorizationToken
            Object of the authorized OAuth2 token.

        Raises
        ------
        hikari.errors.BadRequestError
            If an invalid redirect uri or refresh_token is passed.
        hikari.errors.UnauthorizedError
            When an client or client secret is passed.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def revoke_access_token(
        self,
        client: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        client_secret: str,
        token: typing.Union[str, applications.PartialOAuth2Token],
    ) -> None:
        """Revoke an OAuth2 token.

        Parameters
        ----------
        client : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to authorize with.
        client_secret : str
            Secret of the application to authorize with.
        token : typing.Union[str, hikari.applications.PartialOAuth2Token]
            Object or string of the access token to revoke.

        Raises
        ------
        hikari.errors.UnauthorizedError
            When an client or client secret is passed.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    # THIS IS AN OAUTH2 FLOW ONLY
    @abc.abstractmethod
    async def add_user_to_guild(
        self,
        access_token: typing.Union[str, applications.PartialOAuth2Token],
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        nickname: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
        mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> typing.Optional[guilds.Member]:
        """Add a user to a guild.

        !!! note
            This requires the `access_token` to have the
            [`hikari.applications.OAuth2Scope.GUILDS_JOIN`][] scope enabled along
            with the authorization of a Bot which has [`hikari.permissions.Permissions.CREATE_INSTANT_INVITE`][]
            permission within the target guild.

        Parameters
        ----------
        access_token : typing.Union[str, hikari.applications.PartialOAuth2Token]
            Object or string of the access token to use for this request.
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to add the user to. This may be the object
            or the ID of an existing guild.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The user to add to the guild. This may be the object
            or the ID of an existing user.

        Other Parameters
        ----------------
        nickname : hikari.undefined.UndefinedOr[str]
            If provided, the nick to add to the user when he joins the guild.

            Requires the [`hikari.permissions.Permissions.MANAGE_NICKNAMES`][] permission on the guild.
        roles : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole]]
            If provided, the roles to add to the user when he joins the guild.
            This may be a collection objects or IDs of existing roles.

            Requires the [`hikari.permissions.Permissions.MANAGE_ROLES`][] permission on the guild.
        mute : hikari.undefined.UndefinedOr[bool]
            If provided, the mute state to add the user when he joins the guild.

            Requires the [`hikari.permissions.Permissions.MUTE_MEMBERS`][] permission on the guild.
        deaf : hikari.undefined.UndefinedOr[bool]
            If provided, the deaf state to add the user when he joins the guild.

            Requires the [`hikari.permissions.Permissions.DEAFEN_MEMBERS`][] permission on the guild.

        Returns
        -------
        typing.Optional[hikari.guilds.Member]
            [`None`][] if the user was already part of the guild, else
            [`hikari.guilds.Member`][].

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are not part of the guild you want to add the user to,
            if you are missing permissions to do one of the things you specified,
            if you are using an access token for another user, if the token is
            bound to another bot or if the access token doesn't have the
            [`hikari.applications.OAuth2Scope.GUILDS_JOIN`][] scope enabled.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If you own the guild or the user is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_voice_regions(self) -> typing.Sequence[voices.VoiceRegion]:
        """Fetch available voice regions.

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
            The requested user.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the user is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_audit_log(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        before: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[snowflakes.Unique]] = undefined.UNDEFINED,
        user: undefined.UndefinedOr[snowflakes.SnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
        event_type: undefined.UndefinedOr[typing.Union[audit_logs.AuditLogEventType, int]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[audit_logs.AuditLog]:
        """Fetch pages of the guild's audit log.

        !!! note
            This call is not a coroutine function, it returns a special type of
            lazy iterator that will perform API calls as you iterate across it,
            thus any errors documented below will happen then.

            See [`hikari.iterators`][] for the full API for this iterator type.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the audit logs from. This can be a
            guild object or the ID of an existing guild.

        Other Parameters
        ----------------
        before : hikari.undefined.UndefinedOr[hikari.snowflakes.SearchableSnowflakeishOr[hikari.snowflakes.Unique]]
            If provided, filter to only actions before this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake. This
            may be any other Discord entity that has an ID. In this case, the
            date the object was first created will be used.
        user : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]]
            If provided, the user to filter for.
        event_type : hikari.undefined.UndefinedOr[typing.Union[hikari.audit_logs.AuditLogEventType, int]]
            If provided, the event type to filter for.

        Returns
        -------
        hikari.iterators.LazyIterator[hikari.audit_logs.AuditLog]
            The guild's audit log.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.VIEW_AUDIT_LOG`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
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
            The emoji to fetch. This can be a [`hikari.emojis.CustomEmoji`][]
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
        name : str
            The name for the emoji.
        image : hikari.files.Resourceish
            The 128x128 image for the emoji. Maximum upload size is 256kb.
            This can be a still or an animated image.

        Other Parameters
        ----------------
        roles : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole]]
            If provided, a collection of the roles that will be able to
            use this emoji. This can be a [`hikari.guilds.PartialRole`][] or
            the ID of an existing role.
        reason : hikari.undefined.UndefinedOr[str]
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
            If you are missing [`hikari.permissions.Permissions.MANAGE_GUILD_EXPRESSIONS`][]
            in the server.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
            The emoji to edit. This can be a [`hikari.emojis.CustomEmoji`][]
            or the ID of an existing emoji.

        Other Parameters
        ----------------
        name : hikari.undefined.UndefinedOr[str]
            If provided, the new name for the emoji.
        roles : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole]]
            If provided, the new collection of roles that will be able to
            use this emoji. This can be a [`hikari.guilds.PartialRole`][] or
            the ID of an existing role.
        reason : hikari.undefined.UndefinedOr[str]
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
            If you are missing [`hikari.permissions.Permissions.MANAGE_GUILD_EXPRESSIONS`][]
            in the server.
        hikari.errors.NotFoundError
            If the guild or the emoji are not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_emoji(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        emoji: snowflakes.SnowflakeishOr[emojis.CustomEmoji],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Delete an emoji in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to delete the emoji on. This can be a guild object or the
            ID of an existing guild.
        emoji : hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]
            The emoji to delete. This can be a [`hikari.emojis.CustomEmoji`][]
            or the ID of an existing emoji.

        Other Parameters
        ----------------
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing [`hikari.permissions.Permissions.MANAGE_GUILD_EXPRESSIONS`][]
            in the server.
        hikari.errors.NotFoundError
            If the guild or the emoji are not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_available_sticker_packs(self) -> typing.Sequence[stickers_.StickerPack]:
        """Fetch the available sticker packs.

        Returns
        -------
        typing.Sequence[hikari.stickers.StickerPack]
            The available sticker packs.

        Raises
        ------
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_sticker(
        self, sticker: snowflakes.SnowflakeishOr[stickers_.PartialSticker]
    ) -> typing.Union[stickers_.GuildSticker, stickers_.StandardSticker]:
        """Fetch a sticker.

        Parameters
        ----------
        sticker : hikari.snowflakes.SnowflakeishOr[hikari.stickers.PartialSticker]
            The sticker to fetch. This can be a sticker object or the
            ID of an existing sticker.

        Returns
        -------
        typing.Union[hikari.stickers.GuildSticker, hikari.stickers.StandardSticker]
            The requested sticker.

        Raises
        ------
        hikari.errors.NotFoundError
            If the sticker is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_guild_stickers(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[stickers_.GuildSticker]:
        """Fetch a standard sticker.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.stickers.PartialGuild]
            The guild to request stickers for. This can be a guild object or the
            ID of an existing guild.

        Returns
        -------
        typing.Sequence[hikari.stickers.GuildSticker]
            The requested stickers.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the server.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_guild_sticker(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        sticker: snowflakes.SnowflakeishOr[stickers_.PartialSticker],
    ) -> stickers_.GuildSticker:
        """Fetch a guild sticker.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.stickers.PartialGuild]
            The guild the sticker is in. This can be a guild object or the
            ID of an existing guild.
        sticker : hikari.snowflakes.SnowflakeishOr[hikari.stickers.PartialSticker]
            The sticker to fetch. This can be a sticker object or the
            ID of an existing sticker.

        Returns
        -------
        hikari.stickers.GuildSticker
            The requested sticker.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the server.
        hikari.errors.NotFoundError
            If the guild or the sticker are not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_sticker(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        tag: str,
        image: files.Resourceish,
        *,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> stickers_.GuildSticker:
        """Create a sticker in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the sticker on. This can be a guild object or the
            ID of an existing guild.
        name : str
            The name for the sticker.
        tag : str
            The tag for the sticker.
        image : hikari.files.Resourceish
            The 320x320 image for the sticker. Maximum upload size is 500kb.
            This can be a still PNG, an animated PNG, a Lottie, or a GIF.

            !!! note
                Lottie support is only available for verified and partnered
                servers.

        Other Parameters
        ----------------
        description : hikari.undefined.UndefinedOr[str]
            If provided, the description of the sticker.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.stickers.GuildSticker
            The created sticker.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value or
            if there are no more spaces for the sticker in the guild.
        hikari.errors.ForbiddenError
            If you are missing [`hikari.permissions.Permissions.MANAGE_GUILD_EXPRESSIONS`][]
            in the server.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_sticker(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        sticker: snowflakes.SnowflakeishOr[stickers_.PartialSticker],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        tag: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> stickers_.GuildSticker:
        """Edit a sticker in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to edit the sticker on. This can be a guild object or the
            ID of an existing guild.
        sticker : hikari.snowflakes.SnowflakeishOr[hikari.stickers.PartialSticker]
            The sticker to edit. This can be a sticker object or the ID of an
            existing sticker.

        Other Parameters
        ----------------
        name : hikari.undefined.UndefinedOr[str]
            If provided, the new name for the sticker.
        description : hikari.undefined.UndefinedOr[str]
            If provided, the new description for the sticker.
        tag : hikari.undefined.UndefinedOr[str]
            If provided, the new sticker tag.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.stickers.GuildSticker
            The edited sticker.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing [`hikari.permissions.Permissions.MANAGE_GUILD_EXPRESSIONS`][]
            in the server.
        hikari.errors.NotFoundError
            If the guild or the sticker are not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_sticker(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        sticker: snowflakes.SnowflakeishOr[stickers_.PartialSticker],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Delete a sticker in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to delete the sticker on. This can be a guild object or
            the ID of an existing guild.
        sticker : hikari.snowflakes.SnowflakeishOr[hikari.stickers.PartialSticker]
            The sticker to delete. This can be a sticker object or the ID
            of an existing sticker.

        Other Parameters
        ----------------
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing [`hikari.permissions.Permissions.MANAGE_GUILD_EXPRESSIONS`][]
            in the server.
        hikari.errors.NotFoundError
            If the guild or the sticker are not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def guild_builder(self, name: str, /) -> special_endpoints.GuildBuilder:
        """Make a guild builder to create a guild with.

        !!! note
            This endpoint can only be used by bots in less than 10 guilds.

        !!! note
            This call is not a coroutine function, it returns a special type of
            lazy iterator that will perform API calls as you iterate across it,
            thus any errors documented below will happen then.

            See [`hikari.iterators`][] for the full API for this iterator type.

        Parameters
        ----------
        name : str
            The new guilds name.

        Returns
        -------
        hikari.api.special_endpoints.GuildBuilder
            The guild builder to use. This will allow to create a guild
            later with [`hikari.api.special_endpoints.GuildBuilder.create`][].

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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.

        See Also
        --------
        GuildBuilder : [`hikari.api.special_endpoints.GuildBuilder`][].
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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_guild_preview(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> guilds.GuildPreview:
        """Fetch a guild preview.

        !!! note
            This will only work for guilds you are a part of or are public.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the preview of. This can be a
            guild object or the ID of an existing guild.

        Returns
        -------
        hikari.guilds.GuildPreview
            The requested guild preview.

        Raises
        ------
        hikari.errors.NotFoundError
            If the guild is not found or you are not part of the guild.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_guild(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
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
        preferred_locale: undefined.UndefinedOr[typing.Union[str, locales.Locale]] = undefined.UNDEFINED,
        features: undefined.UndefinedOr[typing.Sequence[guilds.GuildFeature]] = undefined.UNDEFINED,
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
        name : hikari.undefined.UndefinedOr[str]
            If provided, the new name for the guild.
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
            an animated gif when the guild has the [`hikari.guilds.GuildFeature.ANIMATED_ICON`][] feature.
        owner : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]]]
            If provided, the new guild owner.

            !!! warning
                You need to be the owner of the server to use this.
        splash : hikari.undefined.UndefinedNoneOr[hikari.files.Resourceish]
            If provided, the new guild splash. Must be a 16:9 image and the
            guild must have the [`hikari.guilds.GuildFeature.INVITE_SPLASH`][] feature.
        banner : hikari.undefined.UndefinedNoneOr[hikari.files.Resourceish]
            If provided, the new guild banner. Must be a 16:9 image and the
            guild must have the [`hikari.guilds.GuildFeature.BANNER`][] feature.
        system_channel : hikari.undefined.UndefinedNoneOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]]
            If provided, the new system channel.
        rules_channel : hikari.undefined.UndefinedNoneOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]]
            If provided, the new rules channel.
        public_updates_channel : hikari.undefined.UndefinedNoneOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]]
            If provided, the new public updates channel.
        preferred_locale : hikari.undefined.UndefinedNoneOr[str]
            If provided, the new preferred locale.
        features : hikari.undefined.UndefinedOr[typing.Sequence[hikari.guilds.GuildFeature]]
            If provided, the guild features to be enabled. Features not provided will be disabled.

            .. warning::
                At the time of writing, Discord ignores non-`mutable features
                <https://discord.com/developers/docs/resources/guild#guild-object-mutable-guild-features>`_.
                This behaviour can change in the future. You should refer to the
                aforementioned link for the most up-to-date information, and
                only supply mutable features.
        reason : hikari.undefined.UndefinedOr[str]
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][] permission or if you tried to
            pass ownership without being the server owner.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        default_auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildTextChannel:
        """Create a text channel in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the channel in. This may be the
            object or the ID of an existing guild.
        name : str
            The channels name. Must be between 2 and 1000 characters.

        Other Parameters
        ----------------
        position : hikari.undefined.UndefinedOr[int]
            If provided, the position of the channel (relative to the
            category, if any).
        topic : hikari.undefined.UndefinedOr[str]
            If provided, the channels topic. Maximum 1024 characters.
        nsfw : hikari.undefined.UndefinedOr[bool]
            If provided, whether to mark the channel as NSFW.
        rate_limit_per_user : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the amount of seconds a user has to wait
            before being able to send another message in the channel.
            Maximum 21600 seconds.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the permission overwrites for the channel.
        category : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildCategory]]
            The category to create the channel under. This may be the
            object or the ID of an existing category.
        default_auto_archive_duration : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the auto archive duration Discord's end user client
            should default to when creating threads in this channel.

            This should be either 60, 1440, 4320 or 10080 minutes and, as of
            writing, ignores the parent channel's set default_auto_archive_duration
            when passed as [`hikari.undefined.UNDEFINED`][].
        reason : hikari.undefined.UndefinedOr[str]
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        default_auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildNewsChannel:
        """Create a news channel in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the channel in. This may be the
            object or the ID of an existing guild.
        name : str
            The channels name. Must be between 2 and 1000 characters.

        Other Parameters
        ----------------
        position : hikari.undefined.UndefinedOr[int]
            If provided, the position of the channel (relative to the
            category, if any).
        topic : hikari.undefined.UndefinedOr[str]
            If provided, the channels topic. Maximum 1024 characters.
        nsfw : hikari.undefined.UndefinedOr[bool]
            If provided, whether to mark the channel as NSFW.
        rate_limit_per_user : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the amount of seconds a user has to wait
            before being able to send another message in the channel.
            Maximum 21600 seconds.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the permission overwrites for the channel.
        category : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildCategory]]
            The category to create the channel under. This may be the
            object or the ID of an existing category.
        default_auto_archive_duration : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the auto archive duration Discord's end user client
            should default to when creating threads in this channel.

            This should be either 60, 1440, 4320 or 10080 minutes and, as of
            writing, ignores the parent channel's set default_auto_archive_duration
            when passed as [`hikari.undefined.UNDEFINED`][].
        reason : hikari.undefined.UndefinedOr[str]
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_guild_forum_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        topic: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_thread_rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        default_forum_layout: undefined.UndefinedOr[typing.Union[channels_.ForumLayoutType, int]] = undefined.UNDEFINED,
        default_sort_order: undefined.UndefinedOr[
            typing.Union[channels_.ForumSortOrderType, int]
        ] = undefined.UNDEFINED,
        available_tags: undefined.UndefinedOr[typing.Sequence[channels_.ForumTag]] = undefined.UNDEFINED,
        default_reaction_emoji: typing.Union[
            str, emojis.Emoji, undefined.UndefinedType, snowflakes.Snowflake
        ] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildForumChannel:
        """Create a forum channel in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the channel in. This may be the
            object or the ID of an existing guild.
        name : str
            The channels name. Must be between 2 and 1000 characters.

        Other Parameters
        ----------------
        position : hikari.undefined.UndefinedOr[int]
            If provided, the position of the category.
        category : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildCategory]]
            The category to create the channel under. This may be the
            object or the ID of an existing category.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the permission overwrites for the category.
        topic : hikari.undefined.UndefinedOr[str]
            If provided, the channels topic. Maximum 1024 characters.
        nsfw : hikari.undefined.UndefinedOr[bool]
            If provided, whether to mark the channel as NSFW.
        rate_limit_per_user : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the amount of seconds a user has to wait
            before being able to send another message in the channel.
            Maximum 21600 seconds.
        default_auto_archive_duration : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the auto archive duration Discord's end user client
            should default to when creating threads in this channel.

            This should be either 60, 1440, 4320 or 10080 minutes and, as of
            writing, ignores the parent channel's set default_auto_archive_duration
            when passed as [`hikari.undefined.UNDEFINED`][].
        default_thread_rate_limit_per_user : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the ratelimit that should be set in threads created
            from the forum.
        default_forum_layout : hikari.undefined.UndefinedOr[typing.Union[hikari.channels.ForumLayoutType, int]]
            If provided, the default forum layout to show in the client.
        default_sort_order : hikari.undefined.UndefinedOr[typing.Union[hikari.channels.ForumSortOrderType, int]]
            If provided, the default sort order to show in the client.
        available_tags : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.ForumTag]]
            If provided, the available tags to select from when creating a thread.
        default_reaction_emoji : typing.Union[str, hikari.emojis.Emoji, hikari.undefined.UndefinedType, hikari.snowflakes.Snowflake]
            If provided, the new default reaction emoji for threads created in a forum channel.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.GuildForumChannel
            The created forum channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def create_guild_voice_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        *,
        position: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        user_limit: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        bitrate: undefined.UndefinedOr[int] = undefined.UNDEFINED,
        video_quality_mode: undefined.UndefinedOr[typing.Union[channels_.VideoQualityMode, int]] = undefined.UNDEFINED,
        permission_overwrites: undefined.UndefinedOr[
            typing.Sequence[channels_.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        region: undefined.UndefinedOr[typing.Union[voices.VoiceRegion, str]] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildVoiceChannel:
        """Create a voice channel in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the channel in. This may be the
            object or the ID of an existing guild.
        name : str
            The channels name. Must be between 2 and 1000 characters.

        Other Parameters
        ----------------
        position : hikari.undefined.UndefinedOr[int]
            If provided, the position of the channel (relative to the
            category, if any).
        user_limit : hikari.undefined.UndefinedOr[int]
            If provided, the maximum users in the channel at once.
            Must be between 0 and 99 with 0 meaning no limit.
        bitrate : hikari.undefined.UndefinedOr[int]
            If provided, the bitrate for the channel. Must be
            between 8000 and 96000 or 8000 and 128000 for VIP
            servers.
        video_quality_mode : hikari.undefined.UndefinedOr[typing.Union[hikari.channels.VideoQualityMode, int]]
            If provided, the new video quality mode for the channel.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the permission overwrites for the channel.
        region : hikari.undefined.UndefinedOr[typing.Union[hikari.voices.VoiceRegion, str]]
            If provided, the voice region to for this channel. Passing
            [`None`][] here will set it to "auto" mode where the used
            region will be decided based on the first person who connects to it
            when it's empty.
        category : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildCategory]]
            The category to create the channel under. This may be the
            object or the ID of an existing category.
        reason : hikari.undefined.UndefinedOr[str]
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_guild_stage_channel(
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
        region: undefined.UndefinedOr[typing.Union[voices.VoiceRegion, str]] = undefined.UNDEFINED,
        category: undefined.UndefinedOr[snowflakes.SnowflakeishOr[channels_.GuildCategory]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildStageChannel:
        """Create a stage channel in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the channel in. This may be the
            object or the ID of an existing guild.
        name : str
            The channel's name. Must be between 2 and 1000 characters.

        Other Parameters
        ----------------
        position : hikari.undefined.UndefinedOr[int]
            If provided, the position of the channel (relative to the
            category, if any).
        user_limit : hikari.undefined.UndefinedOr[int]
            If provided, the maximum users in the channel at once.
            Must be between 0 and 99 with 0 meaning no limit.
        bitrate : hikari.undefined.UndefinedOr[int]
            If provided, the bitrate for the channel. Must be
            between 8000 and 96000 or 8000 and 128000 for VIP
            servers.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the permission overwrites for the channel.
        region : hikari.undefined.UndefinedOr[typing.Union[hikari.voices.VoiceRegion, str]]
            If provided, the voice region to for this channel. Passing
            [`None`][] here will set it to "auto" mode where the used
            region will be decided based on the first person who connects to it
            when it's empty.
        category : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildCategory]]
            The category to create the channel under. This may be the
            object or the ID of an existing category.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.GuildStageChannel
            The created channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        name : str
            The channels name. Must be between 2 and 1000 characters.

        Other Parameters
        ----------------
        position : hikari.undefined.UndefinedOr[int]
            If provided, the position of the category.
        permission_overwrites : hikari.undefined.UndefinedOr[typing.Sequence[hikari.channels.PermissionOverwrite]]
            If provided, the permission overwrites for the category.
        reason : hikari.undefined.UndefinedOr[str]
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_message_thread(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.PermissibleGuildChannel],
        message: snowflakes.SnowflakeishOr[messages_.PartialMessage],
        name: str,
        /,
        *,
        # While there is a "default archive duration" setting this doesn't seem to effect this context
        # since it always defaults to 1440 minutes if auto_archive_duration is left undefined.
        auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = datetime.timedelta(days=1),
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> typing.Union[channels_.GuildPublicThread, channels_.GuildNewsThread]:
        """Create a public or news thread on a message in a guild channel.

        !!! note
            This call may create a public or news thread dependent on the
            target channel's type and cannot create private threads.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PermissibleGuildChannel]
            Object or ID of the guild news or text channel to create a public thread in.
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            Object or ID of the message to attach the created thread to.
        name : str
            Name of the thread channel.

        Other Parameters
        ----------------
        auto_archive_duration : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, how long the thread should remain inactive until it's archived.

            This should be either 60, 1440, 4320 or 10080 minutes and, as of
            writing, ignores the parent channel's set default_auto_archive_duration
            when passed as [`hikari.undefined.UNDEFINED`][].
        rate_limit_per_user : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the amount of seconds a user has to wait
            before being able to send another message in the channel.
            Maximum 21600 seconds.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        typing.Union[hikari.channels.GuildPublicThread, hikari.channels.GuildNewsThread]
            The created public or news thread channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.CREATE_PUBLIC_THREADS`][] permission or if you
            can't send messages in the target channel.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_thread(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.PermissibleGuildChannel],
        type: typing.Union[channels_.ChannelType, int],
        name: str,
        /,
        *,
        # While there is a "default archive duration" setting this doesn't seem to effect this context
        # since it always defaults to 1440 minutes if auto_archive_duration is left undefined.
        auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = datetime.timedelta(days=1),
        invitable: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildThreadChannel:
        """Create a thread in a guild channel.

        !!! warning
            Private and public threads can only be made in guild text channels,
            and news threads can only be made in guild news channels.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PermissibleGuildChannel]
            Object or ID of the guild news or text channel to create a thread in.
        type : typing.Union[hikari.channels.ChannelType, int]
            The thread type to create.
        name : str
            Name of the thread channel.

        Other Parameters
        ----------------
        auto_archive_duration : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, how long the thread should remain inactive until it's archived.

            This should be either 60, 1440, 4320 or 10080 minutes and, as of
            writing, ignores the parent channel's set default_auto_archive_duration
            when passed as [`hikari.undefined.UNDEFINED`][].
        invitable : undefined.UndefinedOr[bool]
            If provided, whether non-moderators should be able to add other non-moderators to the thread.

            This only applies to private threads.
        rate_limit_per_user : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the amount of seconds a user has to wait
            before being able to send another message in the channel.
            Maximum 21600 seconds.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.GuildThreadChannel
            The created thread channel.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.CREATE_PUBLIC_THREADS`][] permission or if you
            can't send messages in the target channel.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_forum_post(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.PermissibleGuildChannel],
        name: str,
        /,
        # Message arguments
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
        embed: undefined.UndefinedOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        sticker: undefined.UndefinedOr[snowflakes.SnowflakeishOr[stickers_.PartialSticker]] = undefined.UNDEFINED,
        stickers: undefined.UndefinedOr[
            snowflakes.SnowflakeishSequence[stickers_.PartialSticker]
        ] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        mentions_reply: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
        flags: typing.Union[undefined.UndefinedType, int, messages_.MessageFlag] = undefined.UNDEFINED,
        # Channel arguments
        auto_archive_duration: undefined.UndefinedOr[time.Intervalish] = datetime.timedelta(days=1),
        rate_limit_per_user: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        tags: undefined.UndefinedOr[typing.Sequence[snowflakes.Snowflake]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> channels_.GuildPublicThread:
        """Create a post in a forum channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PermissibleGuildChannel]
            Object or ID of the forum channel to create a post in.
        name : str
            Name of the post.
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message contents. If
            [`hikari.undefined.UNDEFINED`][], then nothing will be sent
            in the content. Any other value here will be cast to a
            [`str`][].

            If this is a [`hikari.embeds.Embed`][] and no `embed` nor `embeds` kwarg
            is provided, then this will instead update the embed. This allows
            for simpler syntax when sending an embed alone.

            Likewise, if this is a [`hikari.files.Resource`][], then the
            content is instead treated as an attachment if no `attachment` and
            no `attachments` kwargs are provided.

        Other Parameters
        ----------------
        attachment : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            If provided, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.

            Attachments can be passed as many different things, to aid in
            convenience.

            - If a [`pathlib.PurePath`][] or [`str`][] to a valid URL, the
                resource at the given URL will be streamed to Discord when
                sending the message. Subclasses of
                [`hikari.files.WebResource`][] such as
                [`hikari.files.URL`][],
                [`hikari.messages.Attachment`][],
                [`hikari.emojis.Emoji`][],
                [`hikari.embeds.EmbedResource`][], etc will also be uploaded this way.
                This will use bit-inception, so only a small percentage of the
                resource will remain in memory at any one time, thus aiding in
                scalability.
            - If a [`hikari.files.Bytes`][] is passed, or a [`str`][]
                that contains a valid data URI is passed, then this is uploaded
                with a randomized file name if not provided.
            - If a [`hikari.files.File`][], [`pathlib.PurePath`][] or
                [`str`][] that is an absolute or relative path to a file
                on your file system is passed, then this resource is uploaded
                as an attachment using non-blocking code internally and streamed
                using bit-inception where possible. This depends on the
                type of [`concurrent.futures.Executor`][] that is being used for
                the application (default is a thread pool which supports this
                behaviour).
        attachments : hikari.undefined.UndefinedOr[typing.Sequence[hikari.files.Resourceish]]
            If provided, the message attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        component : hikari.undefined.UndefinedOr[hikari.api.special_endpoints.ComponentBuilder]
            If provided, builder object of the component to include in this message.
        components : hikari.undefined.UndefinedOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            If provided, a sequence of the component builder objects to include
            in this message.
        embed : hikari.undefined.UndefinedOr[hikari.embeds.Embed]
            If provided, the message embed.
        embeds : hikari.undefined.UndefinedOr[typing.Sequence[hikari.embeds.Embed]]
            If provided, the message embeds.
        sticker : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.stickers.PartialSticker]]
            If provided, the object or ID of a sticker to send on the message.

            As of writing, bots can only send custom stickers from the current guild.
        stickers : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.stickers.PartialSticker]]
            If provided, a sequence of the objects and IDs of up to 3 stickers
            to send on the message.

            As of writing, bots can only send custom stickers from the current guild.
        tts : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message will be read out by a screen
            reader using Discord's TTS (text-to-speech) system.
        mentions_everyone : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message should parse @everyone/@here
            mentions.
        mentions_reply : hikari.undefined.UndefinedOr[bool]
            If provided, whether to mention the author of the message
            that is being replied to.

            This will not do anything if not being used with `reply`.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], bool]]
            If provided, and [`True`][], all user mentions will be detected.
            If provided, and [`False`][], all user mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.users.PartialUser`][] derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], bool]]
            If provided, and [`True`][], all role mentions will be detected.
            If provided, and [`False`][], all role mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.guilds.PartialRole`][] derivatives to enforce mentioning
            specific roles.
        flags : hikari.undefined.UndefinedOr[hikari.messages.MessageFlag]
            If provided, optional flags to set on the message. If
            [`hikari.undefined.UNDEFINED`][], then nothing is changed.

            Note that some flags may not be able to be set. Currently the only
            flags that can be set are [`hikari.messages.MessageFlag.NONE`][] and [`hikari.messages.MessageFlag.SUPPRESS_EMBEDS`][].
        auto_archive_duration : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, how long the post should remain inactive until it's archived.

            This should be either 60, 1440, 4320 or 10080 minutes and, as of
            writing, ignores the parent channel's set default_auto_archive_duration
            when passed as [`hikari.undefined.UNDEFINED`][].
        rate_limit_per_user : hikari.undefined.UndefinedOr[hikari.internal.time.Intervalish]
            If provided, the amount of seconds a user has to wait
            before being able to send another message in the channel.
            Maximum 21600 seconds.
        tags : hikari.undefined.UndefinedOr[typing.Sequence[hikari.snowflakes.SnowflakeishOr[hikari.channels.ForumTag]]]
            If provided, the tags to add to the created post.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.channels.GuildPublicThread
            The created post.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.SEND_MESSAGES`][] permission in the channel.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def join_thread(self, channel: snowflakes.SnowflakeishOr[channels_.GuildTextChannel], /) -> None:
        """Join a thread channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]
            Object or ID of the thread channel to join.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you cannot join this thread.
        hikari.errors.NotFoundError
            If the thread channel does not exist.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def add_thread_member(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildThreadChannel],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> None:
        """Add a user to a thread channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]
            Object or ID of the thread channel to add a member to.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user to add to the thread.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you cannot add a user to this thread.
        hikari.errors.NotFoundError
            If the thread channel doesn't exist.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def leave_thread(self, channel: snowflakes.SnowflakeishOr[channels_.GuildThreadChannel], /) -> None:
        """Leave a thread channel.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]
            Object or ID of the thread channel to leave.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.NotFoundError
            If you're not in the thread or it doesn't exist.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def remove_thread_member(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildThreadChannel],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> None:
        """Remove a user from a thread.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]
            Object or ID of the thread channel to remove a user from.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user to remove from the thread.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you cannot remove this user from the thread.
        hikari.errors.NotFoundError
            If the thread channel or member doesn't exist.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_thread_member(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.GuildThreadChannel],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> channels_.ThreadMember:
        """Fetch a thread member.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]
            Object or ID of the thread channel to fetch the member of.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user to fetch the thread member of.

        Returns
        -------
        hikari.channels.ThreadMember
            The thread member.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you access the thread.
        hikari.errors.NotFoundError
            If the thread channel or member doesn't exist.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_thread_members(
        self, channel: snowflakes.SnowflakeishOr[channels_.GuildThreadChannel], /
    ) -> typing.Sequence[channels_.ThreadMember]:
        """Fetch a thread's members.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildTextChannel]
            Object or ID of the thread channel to fetch the members of.

        Returns
        -------
        typing.Sequence[hikari.channels.ThreadMember]
            A sequence of the thread's members.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you access the thread.
        hikari.errors.NotFoundError
            If the thread channel doesn't exist.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_active_threads(
        self, guild: snowflakes.SnowflakeishOr[guilds.Guild], /
    ) -> typing.Sequence[channels_.GuildThreadChannel]:
        """Fetch a guild's active threads.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.Guild]
            Object or ID of the guild to fetch the active threads of.

        Returns
        -------
        typing.Sequence[hikari.channels.GuildThreadChannel]
            A sequence of the guild's active threads.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you access the guild's active threads.
        hikari.errors.NotFoundError
            If the guild doesn't exist.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_public_archived_threads(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.PermissibleGuildChannel],
        /,
        *,
        before: undefined.UndefinedOr[datetime.datetime] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[typing.Union[channels_.GuildNewsThread, channels_.GuildPublicThread]]:
        """Fetch a channel's public archived threads.

        !!! note
            The exceptions on this endpoint will only be raised once the
            result is awaited or iterated over. Invoking this function
            itself will not raise anything.

        Parameters
        ----------
        channel : hikari.undefined.UndefinedOr[hikari.channels.PermissibleGuildChannel]
            Object or ID of the channel to fetch the archived threads of.

        Other Parameters
        ----------------
        before : hikari.undefined.UndefinedOr[datetime.datetime]
            The date to fetch threads before.

            This is based on the thread's `archive_timestamp` field.

        Returns
        -------
        hikari.iterators.LazyIterator[typing.Union[hikari.channels.GuildNewsChannel, hikari.channels.GuildPublicThread]]
            An iterator to fetch the threads.

            !!! note
                This call is not a coroutine function, it returns a special type of
                lazy iterator that will perform API calls as you iterate across it.
                See [`hikari.iterators`][] for the full API for this iterator type.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you cannot access the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_private_archived_threads(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.PermissibleGuildChannel],
        /,
        *,
        before: undefined.UndefinedOr[datetime.datetime] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[channels_.GuildPrivateThread]:
        """Fetch a channel's private archived threads.

        !!! note
            The exceptions on this endpoint will only be raised once the
            result is awaited or iterated over. Invoking this function
            itself will not raise anything.

        Parameters
        ----------
        channel : hikari.undefined.UndefinedOr[hikari.channels.PermissibleGuildChannel]
            Object or ID of the channel to fetch the private archived threads of.

        Other Parameters
        ----------------
        before : hikari.undefined.UndefinedOr[datetime.datetime]
            The date to fetch threads before.

            This is based on the thread's `archive_timestamp` field.

        Returns
        -------
        hikari.iterators.LazyIterator[hikari.channels.GuildPrivateThread]
            An iterator to fetch the threads.

            !!! note
                This call is not a coroutine function, it returns a special type of
                lazy iterator that will perform API calls as you iterate across it.
                See [`hikari.iterators`][] for the full API for this iterator type.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you do not have [`hikari.permissions.Permissions.MANAGE_THREADS`][] in the target channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_joined_private_archived_threads(
        self,
        channel: snowflakes.SnowflakeishOr[channels_.PermissibleGuildChannel],
        /,
        *,
        before: undefined.UndefinedOr[
            snowflakes.SearchableSnowflakeishOr[channels_.GuildThreadChannel]
        ] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[channels_.GuildPrivateThread]:
        """Fetch the private archived threads you have joined in a channel.

        !!! note
            The exceptions on this endpoint will only be raised once the
            result is awaited or iterated over. Invoking this function
            itself will not raise anything.

        Parameters
        ----------
        channel : hikari.undefined.UndefinedOr[hikari.channels.PermissibleGuildChannel]
            Object or ID of the channel to fetch the private archived threads of.

        Other Parameters
        ----------------
        before : hikari.undefined.UndefinedOr[hikari.snowflakes.SearchableSnowflakeishOr[hikari.channels.GuildThreadChannel]]
            If provided, fetch joined threads before this snowflake. If you
            provide a datetime object, it will be transformed into a snowflake.

        Returns
        -------
        hikari.iterators.LazyIterator[hikari.channels.GuildPrivateThread]
            An iterator to fetch the threads.

            !!! note
                This call is not a coroutine function, it returns a special type of
                lazy iterator that will perform API calls as you iterate across it.
                See [`hikari.iterators`][] for the full API for this iterator type.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you cannot access the channel.
        hikari.errors.NotFoundError
            If the channel is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        positions : typing.Mapping[int, hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildChannel]]
            A mapping of of the object or the ID of an existing channel to
            the new position, relative to their parent category, if any.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_CHANNELS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_member(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], user: snowflakes.SnowflakeishOr[users.PartialUser]
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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_members(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> iterators.LazyIterator[guilds.Member]:
        """Fetch the members from a guild.

        !!! warning
            This endpoint requires the [hikari.intents.Intents.GUILD_MEMBERS] intent
            to be enabled in the dashboard, not necessarily authenticated with it
            if using the gateway. If you don't have the intents you can use
            [`hikari.api.rest.RESTClient.search_members`][] which doesn't require
            any intents.

        !!! note
            This call is not a coroutine function, it returns a special type of
            lazy iterator that will perform API calls as you iterate across it,
            thus any errors documented below will happen then.

            See [`hikari.iterators`][] for the full API for this iterator type.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the members of. This may be the
            object or the ID of an existing guild.

        Returns
        -------
        hikari.iterators.LazyIterator[hikari.guilds.Member]
            An iterator to fetch the members.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_my_member(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> guilds.Member:
        """Fetch the Oauth token's associated member in a guild.

        !!! warning
            This endpoint can only be used with a Bearer token. Using this
            with a Bot token will result in a [`hikari.errors.UnauthorizedError`][].

        Returns
        -------
        hikari.guilds.Member
            The associated guild member.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def search_members(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], name: str
    ) -> typing.Sequence[guilds.Member]:
        """Search the members in a guild by nickname and username.

        !!! note
            Unlike [`hikari.api.rest.RESTClient.fetch_members`][] this endpoint isn't paginated and
            therefore will return all the members in one go rather than needing
            to be asynchronously iterated over.

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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        nickname: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        roles: undefined.UndefinedOr[snowflakes.SnowflakeishSequence[guilds.PartialRole]] = undefined.UNDEFINED,
        mute: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        deaf: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        voice_channel: undefined.UndefinedNoneOr[
            snowflakes.SnowflakeishOr[channels_.GuildVoiceChannel]
        ] = undefined.UNDEFINED,
        communication_disabled_until: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.Member:
        """Edit a guild member.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to edit. This may be the object
            or the ID of an existing guild.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            The user to edit. This may be the object
            or the ID of an existing user.

        Other Parameters
        ----------------
        nickname : hikari.undefined.UndefinedNoneOr[str]
            If provided, the new nick for the member. If [`None`][],
            will remove the members nick.

            Requires the [`hikari.permissions.Permissions.MANAGE_NICKNAMES`][] permission.
        roles : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole]]
            If provided, the new roles for the member.

            Requires the [`hikari.permissions.Permissions.MANAGE_ROLES`][] permission.
        mute : hikari.undefined.UndefinedOr[bool]
            If provided, the new server mute state for the member.

            Requires the [`hikari.permissions.Permissions.MUTE_MEMBERS`][] permission.
        deaf : hikari.undefined.UndefinedOr[bool]
            If provided, the new server deaf state for the member.

            Requires the [`hikari.permissions.Permissions.DEAFEN_MEMBERS`][] permission.
        voice_channel : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.GuildVoiceChannel]]]
            If provided, [`None`][] or the object or the ID of
            an existing voice channel to move the member to.
            If [`None`][], will disconnect the member from voice.

            Requires the [`hikari.permissions.Permissions.MOVE_MEMBERS`][] permission
            and the [`hikari.permissions.Permissions.CONNECT`][] permission in the
            original voice channel and the target voice channel.

            !!! note
                If the member is not in a voice channel, this will
                take no effect.
        communication_disabled_until : hikari.undefined.UndefinedNoneOr[datetime.datetime]
            If provided, the datetime when the timeout (disable communication)
            of the member expires, up to 28 days in the future, or [`None`][]
            to remove the timeout from the member.

            Requires the [`hikari.permissions.Permissions.MODERATE_MEMBERS`][] permission.
        reason : hikari.undefined.UndefinedOr[str]
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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_my_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        *,
        nickname: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> guilds.Member:
        """Edit the current user's member in a guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to edit the member in. This may be the object
            or the ID of an existing guild.

        Other Parameters
        ----------------
        nickname : hikari.undefined.UndefinedNoneOr[str]
            If provided, the new nickname for the member. If
            [`None`][], will remove the members nickname.

            Requires the [`hikari.permissions.Permissions.CHANGE_NICKNAME`][] permission.
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.
        reason : hikari.undefined.UndefinedOr[str]
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
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_ROLES`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild, user or role are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_ROLES`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild, user or role are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.KICK_MEMBERS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def kick_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Alias of [`hikari.api.rest.RESTClient.kick_user`][]."""

    @abc.abstractmethod
    async def ban_user(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        delete_message_seconds: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Ban the given user from this guild.

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
        delete_message_seconds : hikari.undefined.UndefinedNoneOr[hikari.internal.time.Intervalish]
            If provided, the number of seconds to delete messages for.
            This can be represented as either an int/float between 0 and 604800 (7 days), or
            a [`datetime.timedelta`][] object.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.BAN_MEMBERS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def ban_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        delete_message_seconds: undefined.UndefinedOr[time.Intervalish] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Alias of [`hikari.api.rest.RESTClient.ban_user`][]."""

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
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.BAN_MEMBERS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def unban_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        *,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> None:
        """Alias of [`hikari.api.rest.RESTClient.unban_user`][]."""

    @abc.abstractmethod
    async def fetch_ban(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], user: snowflakes.SnowflakeishOr[users.PartialUser]
    ) -> guilds.GuildBan:
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
        hikari.guilds.GuildBan
            The requested ban info.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.BAN_MEMBERS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or user are not found or if the user
            is not banned.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_bans(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        /,
        *,
        newest_first: bool = False,
        start_at: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[guilds.GuildBan]:
        """Fetch the bans of a guild.

        !!! note
            This call is not a coroutine function, it returns a special type of
            lazy iterator that will perform API calls as you iterate across it.
            See [`hikari.iterators`][] for the full API for this iterator type.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the bans from. This may be the
            object or the ID of an existing guild.

        Other Parameters
        ----------------
        newest_first : bool
            Whether to fetch the newest first or the oldest first.
        start_at : undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[users.PartialUser]]
            If provided, will start at this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake. This
            may also be a scheduled event object object. In this case, the
            date the object was first created will be used.

        Returns
        -------
        hikari.iterators.LazyIterator[hikari.guilds.GuildBan]
            The requested bans.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.BAN_MEMBERS`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_roles(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]) -> typing.Sequence[guilds.Role]:
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
        icon: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        unicode_emoji: undefined.UndefinedOr[str] = undefined.UNDEFINED,
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
        name : hikari.undefined.UndefinedOr[str]
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
        hoist : hikari.undefined.UndefinedOr[bool]
            If provided, whether to hoist the role.
        icon : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            If provided, the role icon. Must be a 64x64 image under 256kb.
        unicode_emoji : hikari.undefined.UndefinedOr[str]
            If provided, the standard emoji to set as the role icon.
        mentionable : hikari.undefined.UndefinedOr[bool]
            If provided, whether to make the role mentionable.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.guilds.Role
            The created role.

        Raises
        ------
        TypeError
            If both `color` and `colour` are specified or if both `icon` and
            `unicode_emoji` are specified.
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_ROLES`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        positions : typing.Mapping[int, hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialRole]]
            A mapping of the position to the role.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_ROLES`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        icon: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        unicode_emoji: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
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
        name : hikari.undefined.UndefinedOr[str]
            If provided, the new name for the role.
        permissions : hikari.undefined.UndefinedOr[hikari.permissions.Permissions]
            If provided, the new permissions for the role.
        color : hikari.undefined.UndefinedOr[hikari.colors.Colorish]
            If provided, the new color for the role.
        colour : hikari.undefined.UndefinedOr[hikari.colors.Colorish]
            An alias for `color`.
        hoist : hikari.undefined.UndefinedOr[bool]
            If provided, whether to hoist the role.
        icon : hikari.undefined.UndefinedNoneOr[hikari.files.Resourceish]
            If provided, the new role icon. Must be a 64x64 image
            under 256kb.
        unicode_emoji : hikari.undefined.UndefinedNoneOr[str]
            If provided, the new unicode emoji to set as the role icon.
        mentionable : hikari.undefined.UndefinedOr[bool]
            If provided, whether to make the role mentionable.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.guilds.Role
            The edited role.

        Raises
        ------
        TypeError
            If both `color` and `colour` are specified or if both `icon` and
            `unicode_emoji` are specified.
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_ROLES`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or role are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_role(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], role: snowflakes.SnowflakeishOr[guilds.PartialRole]
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_ROLES`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or role are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        days : hikari.undefined.UndefinedOr[int]
            If provided, number of days to count prune for.
        include_roles : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole]]]
            If provided, the role(s) to include. By default, this endpoint will
            not count users with roles. Providing roles using this attribute
            will make members with the specified roles also get included into
            the count.

        Returns
        -------
        int
            The estimated guild prune count.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.KICK_MEMBERS`][] permission.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

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
        days : hikari.undefined.UndefinedOr[int]
            If provided, number of days to count prune for.
        compute_prune_count : hikari.snowflakes.SnowflakeishOr[bool]
            If provided, whether to return the prune count. This is discouraged
            for large guilds.
        include_roles : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole]]
            If provided, the role(s) to include. By default, this endpoint will
            not count users with roles. Providing roles using this attribute
            will make members with the specified roles also get included into
            the count.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        typing.Optional[int]
            If `compute_prune_count` is not provided or [`True`][], the
            number of members pruned. Else [`None`][].

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.KICK_MEMBERS`][] permission.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_guild_voice_regions(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
    ) -> typing.Sequence[voices.VoiceRegion]:
        """Fetch the available voice regions for a guild.

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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_guild_invites(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_integrations(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild]
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][] permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][] permission.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
            If provided, the channel to set the widget to. If [`None`][],
            will not set to any.
        enabled : hikari.undefined.UndefinedOr[bool]
            If provided, whether to enable the widget.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.guilds.GuildWidget
            The edited guild widget.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][] permission.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        hikari.guilds.WelcomeScreen
            The requested welcome screen.

        Raises
        ------
        hikari.errors.NotFoundError
            If the guild is not found or the welcome screen has never been set
            for this guild (if the welcome screen has been set for a guild
            before and then disabled you should still be able to fetch it).
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        description : undefined.UndefinedNoneOr[str]
            If provided, the description to set for the guild's welcome screen.
            This may be [`None`][] to unset the description.
        enabled : undefined.UndefinedOr[bool]
            If provided, Whether the guild's welcome screen should be enabled.
        channels : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.guilds.WelcomeChannel]]
            If provided, a sequence of up to 5 public channels to set in this
            guild's welcome screen. This may be passed as [`None`][] to
            remove all welcome channels

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
            If you are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][] permission, are not part of
            the guild or the guild doesn't have access to the community welcome
            screen feature.
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
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
        description : hikari.undefined.UndefinedNoneOr[str]
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
            If the guild is not found or you are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][]
            permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_guild_from_template(
        self,
        template: typing.Union[str, templates.Template],
        name: str,
        *,
        icon: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
    ) -> guilds.RESTGuild:
        """Make a guild from a template.

        !!! note
            This endpoint can only be used by bots in less than 10 guilds.

        Parameters
        ----------
        template : typing.Union[str, hikari.templates.Template]
            The object or string code of the template to create a guild based on.
        name : str
            The new guilds name.

        Other Parameters
        ----------------
        icon : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            If provided, the guild icon to set. Must be a 1024x1024 image or can
            be an animated gif when the guild has the [`hikari.guilds.GuildFeature.ANIMATED_ICON`][] feature.

        Returns
        -------
        hikari.guilds.RESTGuild
            Object of the created guild.

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
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_template(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], template: typing.Union[str, templates.Template]
    ) -> templates.Template:
        """Delete a guild template.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to delete a template in.
        template : typing.Union[str, hikari.templates.Template]
            Object or string code of the template to delete.

        Returns
        -------
        hikari.templates.Template
            The deleted template's object.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild.
        hikari.errors.NotFoundError
            If the guild is not found or you are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][]
            permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_template(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        template: typing.Union[templates.Template, str],
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        description: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
    ) -> templates.Template:
        """Modify a guild template.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to edit a template in.
        template : typing.Union[str, hikari.templates.Template]
            Object or string code of the template to modify.

        Other Parameters
        ----------------
        name : hikari.undefined.UndefinedOr[str]
            The name to set for this template.
        description : hikari.undefined.UndefinedNoneOr[str]
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
            If the guild is not found or you are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][]
            permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_template(self, template: typing.Union[str, templates.Template]) -> templates.Template:
        """Fetch a guild template.

        Parameters
        ----------
        template : typing.Union[str, hikari.templates.Template]
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
            If the guild is not found or are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][]
            permission.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def sync_guild_template(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], template: typing.Union[str, templates.Template]
    ) -> templates.Template:
        """Create a guild template.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to sync a template in.
        template : typing.Union[str, hikari.templates.Template]
            Object or code of the template to sync.

        Returns
        -------
        hikari.templates.Template
            The object of the synced template.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you are not part of the guild or are missing the [`hikari.permissions.Permissions.MANAGE_GUILD`][]
            permission.
        hikari.errors.NotFoundError
            If the guild or template is not found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def slash_command_builder(self, name: str, description: str) -> special_endpoints.SlashCommandBuilder:
        r"""Create a command builder to use in [`hikari.api.rest.RESTClient.set_application_commands`][].

        Parameters
        ----------
        name : str
            The command's name. This should match the regex `^[-_\p{L}\p{N}\p{sc=Deva}\p{sc=Thai}]{1,32}$` in
            Unicode mode and be lowercase.
        description : str
            The description to set for the command if this is a slash command.
            This should be inclusively between 1-100 characters in length.

        Returns
        -------
        hikari.api.special_endpoints.SlashCommandBuilder
            The created command builder object.
        """

    @abc.abstractmethod
    def context_menu_command_builder(
        self, type: typing.Union[commands.CommandType, int], name: str
    ) -> special_endpoints.ContextMenuCommandBuilder:
        r"""Create a command builder to use in [`hikari.api.rest.RESTClient.set_application_commands`][].

        Parameters
        ----------
        type : commands.CommandType
            The commands's type.
        name : str
            The command's name.

        Returns
        -------
        hikari.api.special_endpoints.ContextMenuCommandBuilder
            The created command builder object.
        """

    @abc.abstractmethod
    async def fetch_application_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        command: snowflakes.SnowflakeishOr[commands.PartialCommand],
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> commands.PartialCommand:
        """Fetch a command set for an application.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to fetch a command for.
        command : hikari.snowflakes.SnowflakeishOr[hikari.commands.PartialCommand]
            Object or ID of the command to fetch.

        Other Parameters
        ----------------
        guild : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to fetch the command for. If left as
            [`hikari.undefined.UNDEFINED`][] then this will return a global command,
            otherwise this will return a command made for the specified guild.

        Returns
        -------
        hikari.commands.PartialCommand
            Object of the fetched command.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the target command.
        hikari.errors.NotFoundError
            If the command isn't found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_application_commands(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> typing.Sequence[commands.PartialCommand]:
        """Fetch the commands set for an application.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to fetch the commands for.

        Other Parameters
        ----------------
        guild : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to fetch the commands for. If left as
            [`hikari.undefined.UNDEFINED`][] then this will only return the global
            commands, otherwise this will only return the commands set exclusively
            for the specific guild.

        Returns
        -------
        typing.Sequence[hikari.commands.PartialCommand]
            A sequence of the commands declared for the provided application.
            This will exclusively either contain the commands set for a specific
            guild if `guild` is provided or the global commands if not.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the target guild.
        hikari.errors.NotFoundError
            If the provided application isn't found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_slash_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        name: str,
        description: str,
        *,
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
        options: undefined.UndefinedOr[typing.Sequence[commands.CommandOption]] = undefined.UNDEFINED,
        name_localizations: undefined.UndefinedOr[
            typing.Mapping[typing.Union[locales.Locale, str], str]
        ] = undefined.UNDEFINED,
        description_localizations: undefined.UndefinedOr[
            typing.Mapping[typing.Union[locales.Locale, str], str]
        ] = undefined.UNDEFINED,
        default_member_permissions: typing.Union[
            undefined.UndefinedType, int, permissions_.Permissions
        ] = undefined.UNDEFINED,
        dm_enabled: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> commands.SlashCommand:
        r"""Create an application command.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to create a command for.
        name : str
            The command's name. This should match the regex `^[\w-]{1,32}$` in
            Unicode mode and be lowercase.
        description : str
            The description to set for the command.
            This should be inclusively between 1-100 characters in length.

        Other Parameters
        ----------------
        guild : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the specific guild this should be made for.
            If left as [`hikari.undefined.UNDEFINED`][] then this call will create
            a global command rather than a guild specific one.
        options : hikari.undefined.UndefinedOr[typing.Sequence[hikari.commands.CommandOption]]
            A sequence of up to 10 options for this command.
        name_localizations : hikari.undefined.UndefinedOr[typing.Mapping[typing.Union[hikari.locales.Locale, str], str]]
            The name localizations for this command.
        description_localizations : hikari.undefined.UndefinedOr[typing.Mapping[typing.Union[hikari.locales.Locale, str], str]]
            The description localizations for this command.
        default_member_permissions : typing.Union[hikari.undefined.UndefinedType, int, hikari.permissions.Permissions]
            Member permissions necessary to utilize this command by default.

            If `0`, then it will be available for all members. Note that this doesn't affect
            administrators of the guild and overwrites.
        dm_enabled : hikari.undefined.UndefinedOr[bool]
            Whether this command is enabled in DMs with the bot.

            This can only be applied to non-guild commands.
        nsfw : hikari.undefined.UndefinedOr[bool]
            Whether this command should be age-restricted.

        Returns
        -------
        hikari.commands.SlashCommand
            Object of the created command.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the provided application's commands.
        hikari.errors.NotFoundError
            If the provided application isn't found.
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_context_menu_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        type: typing.Union[commands.CommandType, int],
        name: str,
        *,
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
        name_localizations: undefined.UndefinedOr[
            typing.Mapping[typing.Union[locales.Locale, str], str]
        ] = undefined.UNDEFINED,
        default_member_permissions: typing.Union[
            undefined.UndefinedType, int, permissions_.Permissions
        ] = undefined.UNDEFINED,
        dm_enabled: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        nsfw: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> commands.ContextMenuCommand:
        r"""Create an application command.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to create a command for.
        type : typing.Union[hikari.commands.CommandType, int]
            The type of menu command to make.

            Only USER and MESSAGE are valid here.
        name : str
            The command's name. This should match the regex `^[-_\p{L}\p{N}\p{sc=Deva}\p{sc=Thai}]{1,32}$` in
            Unicode mode and be lowercase.

        Other Parameters
        ----------------
        guild : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the specific guild this should be made for.
            If left as [`hikari.undefined.UNDEFINED`][] then this call will create
            a global command rather than a guild specific one.
        name_localizations : hikari.undefined.UndefinedOr[typing.Mapping[typing.Union[hikari.locales.Locale, str], str]]
            The name localizations for this command.
        default_member_permissions : typing.Union[hikari.undefined.UndefinedType, int, hikari.permissions.Permissions]
            Member permissions necessary to utilize this command by default.

            If `0`, then it will be available for all members. Note that this doesn't affect
            administrators of the guild and overwrites.
        dm_enabled : hikari.undefined.UndefinedOr[bool]
            Whether this command is enabled in DMs with the bot.

            This can only be applied to non-guild commands.
        nsfw : hikari.undefined.UndefinedOr[bool]
            Whether this command should be age-restricted.

        Returns
        -------
        hikari.commands.ContextMenuCommand
            Object of the created command.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the provided application's commands.
        hikari.errors.NotFoundError
            If the provided application isn't found.
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def set_application_commands(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        commands: typing.Sequence[special_endpoints.CommandBuilder],
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> typing.Sequence[commands.PartialCommand]:
        """Set the commands for an application.

        !!! warning
            Any existing commands not included in the provided commands array
            will be deleted.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to create a command for.
        commands : typing.Sequence[hikari.api.special_endpoints.CommandBuilder]
            A sequence of up to 100 initialised command builder objects of the
            commands to set for this the application.

        Other Parameters
        ----------------
        guild : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the specific guild to set the commands for.
            If left as [`hikari.undefined.UNDEFINED`][] then this set the global
            commands rather than guild specific commands.

        Returns
        -------
        typing.Sequence[hikari.commands.PartialCommand]
            A sequence of the set command objects.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the provided application's commands.
        hikari.errors.NotFoundError
            If the provided application isn't found.
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_application_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        command: snowflakes.SnowflakeishOr[commands.PartialCommand],
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
        *,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        options: undefined.UndefinedOr[typing.Sequence[commands.CommandOption]] = undefined.UNDEFINED,
        default_member_permissions: typing.Union[
            undefined.UndefinedType, int, permissions_.Permissions
        ] = undefined.UNDEFINED,
        dm_enabled: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
    ) -> commands.PartialCommand:
        """Edit a registered application command.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to edit a command for.
        command : hikari.snowflakes.SnowflakeishOr[hikari.commands.PartialCommand]
            Object or ID of the command to modify.

        Other Parameters
        ----------------
        guild : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]]
            Object or ID of the guild to edit a command for if this is a guild
            specific command. Leave this as [`hikari.undefined.UNDEFINED`][] to delete
            a global command.
        name : hikari.undefined.UndefinedOr[str]
            The name to set for the command. Leave as [`hikari.undefined.UNDEFINED`][]
            to not change.
        description : hikari.undefined.UndefinedOr[str]
            The description to set for the command. Leave as [`hikari.undefined.UNDEFINED`][]
            to not change.
        options : hikari.undefined.UndefinedOr[typing.Sequence[hikari.commands.CommandOption]]
            A sequence of up to 10 options to set for this command. Leave this as
            [`hikari.undefined.UNDEFINED`][] to not change.
        default_member_permissions : typing.Union[hikari.undefined.UndefinedType, int, hikari.permissions.Permissions]
            Member permissions necessary to utilize this command by default.

            If `0`, then it will be available for all members. Note that this doesn't affect
            administrators of the guild and overwrites.
        dm_enabled : hikari.undefined.UndefinedOr[bool]
            Whether this command is enabled in DMs with the bot.

            This can only be applied to non-guild commands.

        Returns
        -------
        hikari.commands.PartialCommand
            The edited command object.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the provided application's commands.
        hikari.errors.NotFoundError
            If the provided application or command isn't found.
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_application_command(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        command: snowflakes.SnowflakeishOr[commands.PartialCommand],
        guild: undefined.UndefinedOr[snowflakes.SnowflakeishOr[guilds.PartialGuild]] = undefined.UNDEFINED,
    ) -> None:
        """Delete a registered application command.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to delete a command for.
        command : hikari.snowflakes.SnowflakeishOr[hikari.commands.PartialCommand]
            Object or ID of the command to delete.

        Other Parameters
        ----------------
        guild : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]]
            Object or ID of the guild to delete a command for if this is a guild
            specific command. Leave this as [`hikari.undefined.UNDEFINED`][] to
            delete a global command.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the provided application's commands.
        hikari.errors.NotFoundError
            If the provided application or command isn't found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_application_guild_commands_permissions(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
    ) -> typing.Sequence[commands.GuildCommandPermissions]:
        """Fetch the command permissions registered in a guild.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to fetch the command permissions for.
        guild : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]]
            Object or ID of the guild to fetch the command permissions for.

        Returns
        -------
        typing.Sequence[hikari.commands.GuildCommandPermissions]
            Sequence of the guild command permissions set for the specified guild.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the provided application's commands or guild.
        hikari.errors.NotFoundError
            If the provided application isn't found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_application_command_permissions(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        command: snowflakes.SnowflakeishOr[commands.PartialCommand],
    ) -> commands.GuildCommandPermissions:
        """Fetch the permissions registered for a specific command in a guild.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to fetch the command permissions for.
        guild : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]]
            Object or ID of the guild to fetch the command permissions for.
        command : hikari.snowflakes.SnowflakeishOr[hikari.commands.PartialCommand]
            Object or ID of the command to fetch the command permissions for.

        Returns
        -------
        hikari.commands.GuildCommandPermissions
            Object of the command permissions set for the specified command.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the provided application's commands or guild.
        hikari.errors.NotFoundError
            If the provided application or command isn't found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    # THIS IS AN OAUTH2 FLOW ONLY
    @abc.abstractmethod
    async def set_application_command_permissions(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        command: snowflakes.SnowflakeishOr[commands.PartialCommand],
        permissions: typing.Sequence[commands.CommandPermission],
    ) -> commands.GuildCommandPermissions:
        """Set permissions for a specific command.

        !!! note
            This requires the `access_token` to have the
            [`hikari.applications.OAuth2Scope.APPLICATIONS_COMMANDS_PERMISSION_UPDATE`][]
            scope enabled along with the authorization of a Bot which has
            [`hikari.permissions.Permissions.CREATE_INSTANT_INVITE`][] permission
            within the target guild.

        !!! note
            This overwrites any previously set permissions.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to set the command permissions for.
        guild : hikari.undefined.UndefinedOr[hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]]
            Object or ID of the guild to set the command permissions for.
        command : hikari.snowflakes.SnowflakeishOr[hikari.commands.PartialCommand]
            Object or ID of the command to set the permissions for.
        permissions : typing.Sequence[hikari.commands.CommandPermission]
            Sequence of up to 10 of the permission objects to set.

        Returns
        -------
        hikari.commands.GuildCommandPermissions
            Object of the set permissions.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the provided application's commands or guild.
        hikari.errors.NotFoundError
            If the provided application or command isn't found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def interaction_deferred_builder(
        self, type: typing.Union[base_interactions.ResponseType, int], /
    ) -> special_endpoints.InteractionDeferredBuilder:
        """Create a builder for a deferred message interaction response.

        Parameters
        ----------
        type : typing.Union[hikari.interactions.base_interactions.ResponseType, int]
            The type of deferred message response this builder is for.

        Returns
        -------
        hikari.api.special_endpoints.InteractionDeferredBuilder
            The deferred message interaction response builder object.
        """

    @abc.abstractmethod
    def interaction_autocomplete_builder(
        self, choices: typing.Sequence[special_endpoints.AutocompleteChoiceBuilder]
    ) -> special_endpoints.InteractionAutocompleteBuilder:
        """Create a builder for an autocomplete interaction response.

        Parameters
        ----------
        choices : typing.Sequence[hikari.api.special_endpoints.AutocompleteChoiceBuilder]
            The autocomplete choices.

        Returns
        -------
        hikari.api.special_endpoints.InteractionAutocompleteBuilder
            The autocomplete interaction response builder object.
        """

    @abc.abstractmethod
    def interaction_message_builder(
        self, type: typing.Union[base_interactions.ResponseType, int], /
    ) -> special_endpoints.InteractionMessageBuilder:
        """Create a builder for a message interaction response.

        Parameters
        ----------
        type : typing.Union[hikari.interactions.base_interactions.ResponseType, int]
            The type of message response this builder is for.

        Returns
        -------
        hikari.api.special_endpoints.InteractionMessageBuilder
            The interaction message response builder object.
        """

    @abc.abstractmethod
    def interaction_modal_builder(self, title: str, custom_id: str) -> special_endpoints.InteractionModalBuilder:
        """Create a builder for a modal interaction response.

        Parameters
        ----------
        title : str
            The title that will show up in the modal.
        custom_id : str
            Developer set custom ID used for identifying interactions with this modal.

        Returns
        -------
        hikari.api.special_endpoints.InteractionModalBuilder
            The interaction modal response builder object.
        """

    @abc.abstractmethod
    async def fetch_interaction_response(
        self, application: snowflakes.SnowflakeishOr[guilds.PartialApplication], token: str
    ) -> messages_.Message:
        """Fetch the initial response for an interaction.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to fetch a command for.
        token : str
            Token of the interaction to get the initial response for.

        Returns
        -------
        hikari.messages.Message
            Message object of the initial response.

        Raises
        ------
        hikari.errors.ForbiddenError
            If you cannot access the target interaction.
        hikari.errors.NotFoundError
            If the initial response isn't found.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_interaction_response(
        self,
        interaction: snowflakes.SnowflakeishOr[base_interactions.PartialInteraction],
        token: str,
        response_type: typing.Union[int, base_interactions.ResponseType],
        content: undefined.UndefinedOr[typing.Any] = undefined.UNDEFINED,
        *,
        flags: typing.Union[int, messages_.MessageFlag, undefined.UndefinedType] = undefined.UNDEFINED,
        tts: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        attachment: undefined.UndefinedNoneOr[files.Resourceish] = undefined.UNDEFINED,
        attachments: undefined.UndefinedNoneOr[typing.Sequence[files.Resourceish]] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
        embed: undefined.UndefinedNoneOr[embeds_.Embed] = undefined.UNDEFINED,
        embeds: undefined.UndefinedNoneOr[typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        mentions_everyone: undefined.UndefinedOr[bool] = undefined.UNDEFINED,
        user_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[users.PartialUser], bool]
        ] = undefined.UNDEFINED,
        role_mentions: undefined.UndefinedOr[
            typing.Union[snowflakes.SnowflakeishSequence[guilds.PartialRole], bool]
        ] = undefined.UNDEFINED,
    ) -> None:
        """Create the initial response for a interaction.

        !!! warning
            Calling this with an interaction which already has an initial
            response will result in this raising a [`hikari.errors.NotFoundError`][].
            This includes if the REST interaction server has already responded
            to the request.

        Parameters
        ----------
        interaction : hikari.snowflakes.SnowflakeishOr[hikari.interactions.base_interactions.PartialInteraction]
            Object or ID of the interaction this response is for.
        token : str
            The command interaction's token.
        response_type : typing.Union[int, hikari.interactions.base_interactions.ResponseType]
            The type of interaction response this is.

        Other Parameters
        ----------------
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message contents. If
            [`hikari.undefined.UNDEFINED`][], then nothing will be sent
            in the content. Any other value here will be cast to a
            [`str`][].

            If this is a [`hikari.embeds.Embed`][] and no `embed` nor
            no `embeds` kwarg is provided, then this will instead
            update the embed. This allows for simpler syntax when
            sending an embed alone.
        attachment : hikari.undefined.UndefinedNoneOr[typing.Union[hikari.files.Resourceish, hikari.messages.Attachment]]
            If provided, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.
        attachments : hikari.undefined.UndefinedNoneOr[typing.Sequence[typing.Union[hikari.files.Resourceish, hikari.messages.Attachment]]]
            If provided, the message attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        component : hikari.undefined.UndefinedNoneOr[hikari.api.special_endpoints.ComponentBuilder]
            If provided, builder object of the component to include in this message.
        components : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            If provided, a sequence of the component builder objects to include
            in this message.
        embed : hikari.undefined.UndefinedNoneOr[hikari.embeds.Embed]
            If provided, the message embed.
        embeds : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.embeds.Embed]]
            If provided, the message embeds.
        flags : typing.Union[int, hikari.messages.MessageFlag, hikari.undefined.UndefinedType]
            If provided, the message flags this response should have.

            As of writing the only message flags which can be set here are
            [`hikari.messages.MessageFlag.EPHEMERAL`][], [`hikari.messages.MessageFlag.SUPPRESS_NOTIFICATIONS`][]
            and [`hikari.messages.MessageFlag.SUPPRESS_EMBEDS`][].
        tts : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message will be read out by a screen
            reader using Discord's TTS (text-to-speech) system.
        mentions_everyone : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message should parse @everyone/@here
            mentions.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], bool]]
            If provided, and [`True`][], all user mentions will be detected.
            If provided, and [`False`][], all user mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.users.PartialUser`][] derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], bool]]
            If provided, and [`True`][], all role mentions will be detected.
            If provided, and [`False`][], all role mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.guilds.PartialRole`][] derivatives to enforce mentioning
            specific roles.

        Raises
        ------
        ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        TypeError
            If both `embed` and `embeds` are specified.
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no embeds; messages with more than 2000 characters
            in them, embeds that exceed one of the many embed limits
            invalid image URLs in embeds.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the interaction is not found or if the interaction's initial
            response has already been created.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def edit_interaction_response(
        self,
        application: snowflakes.SnowflakeishOr[guilds.PartialApplication],
        token: str,
        content: undefined.UndefinedNoneOr[typing.Any] = undefined.UNDEFINED,
        *,
        attachment: undefined.UndefinedNoneOr[
            typing.Union[files.Resourceish, messages_.Attachment]
        ] = undefined.UNDEFINED,
        attachments: undefined.UndefinedNoneOr[
            typing.Sequence[typing.Union[files.Resourceish, messages_.Attachment]]
        ] = undefined.UNDEFINED,
        component: undefined.UndefinedNoneOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedNoneOr[
            typing.Sequence[special_endpoints.ComponentBuilder]
        ] = undefined.UNDEFINED,
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
        """Edit the initial response to a command interaction.

        !!! note
            Mentioning everyone, roles, or users in message edits currently
            will not send a push notification showing a new mention to people
            on Discord. It will still highlight in their chat as if they
            were mentioned, however.

            Also important to note that if you specify a text `content`, `mentions_everyone`,
            `mentions_reply`, `user_mentions`, and `role_mentions` will default
            to [`False`][] as the message will be re-parsed for mentions. This will
            also occur if only one of the four are specified

            This is a limitation of Discord's design. If in doubt, specify all
            four of them each time.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to edit a command response for.
        token : str
            The interaction's token.

        Other Parameters
        ----------------
        content : hikari.undefined.UndefinedOr[typing.Any]
            If provided, the message content to update with. If
            [`hikari.undefined.UNDEFINED`][], then the content will not
            be changed. If [`None`][], then the content will be removed.

            Any other value will be cast to a [`str`][] before sending.

            If this is a [`hikari.embeds.Embed`][] and neither the
            `embed` or `embeds` kwargs are provided or if this is a
            [`hikari.files.Resourceish`][] and neither the `attachment` or
            `attachments` kwargs are provided, the values will be overwritten.
            This allows for simpler syntax when sending an embed or an
            attachment alone.
        attachment : hikari.undefined.UndefinedNoneOr[typing.Union[hikari.files.Resourceish, hikari.messages.Attachment]]
            If provided, the attachment to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous attachment, if
            present, is not changed. If this is [`None`][], then the
            attachment is removed, if present. Otherwise, the new attachment
            that was provided will be attached.
        attachments : hikari.undefined.UndefinedNoneOr[typing.Sequence[typing.Union[hikari.files.Resourceish, hikari.messages.Attachment]]]
            If provided, the attachments to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous attachments, if
            present, are not changed. If this is [`None`][], then the
            attachments is removed, if present. Otherwise, the new attachments
            that were provided will be attached.
        component : hikari.undefined.UndefinedNoneOr[hikari.api.special_endpoints.ComponentBuilder]
            If provided, builder object of the component to set for this message.
            This component will replace any previously set components and passing
            [`None`][] will remove all components.
        components : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            If provided, a sequence of the component builder objects set for
            this message. These components will replace any previously set
            components and passing [`None`][] or an empty sequence will
            remove all components.
        embed : hikari.undefined.UndefinedNoneOr[hikari.embeds.Embed]
            If provided, the embed to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous embed(s) are not changed.
            If this is [`None`][] then any present embeds are removed.
            Otherwise, the new embed that was provided will be used as the
            replacement.
        embeds : hikari.undefined.UndefinedNoneOr[typing.Sequence[hikari.embeds.Embed]]
            If provided, the embeds to set on the message. If
            [`hikari.undefined.UNDEFINED`][], the previous embed(s) are not changed.
            If this is [`None`][] then any present embeds are removed.
            Otherwise, the new embeds that were provided will be used as the
            replacement.
        mentions_everyone : hikari.undefined.UndefinedOr[bool]
            If provided, whether the message should parse @everyone/@here
            mentions.
        user_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.users.PartialUser], bool]]
            If provided, and [`True`][], all user mentions will be detected.
            If provided, and [`False`][], all user mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.users.PartialUser`][] derivatives to enforce mentioning
            specific users.
        role_mentions : hikari.undefined.UndefinedOr[typing.Union[hikari.snowflakes.SnowflakeishSequence[hikari.guilds.PartialRole], bool]]
            If provided, and [`True`][], all role mentions will be detected.
            If provided, and [`False`][], all role mentions will be ignored
            if appearing in the message body.
            Alternatively this may be a collection of
            [`hikari.snowflakes.Snowflake`][], or
            [`hikari.guilds.PartialRole`][] derivatives to enforce mentioning
            specific roles.

        Returns
        -------
        hikari.messages.Message
            The edited message.

        Raises
        ------
        ValueError
            If both `attachment` and `attachments`, `component` and `components`
            or `embed` and `embeds` are specified.
        hikari.errors.BadRequestError
            This may be raised in several discrete situations, such as messages
            being empty with no attachments or embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; too many attachments; attachments that are too large;
            invalid image URLs in embeds; too many components.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the interaction or the message are not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def delete_interaction_response(
        self, application: snowflakes.SnowflakeishOr[guilds.PartialApplication], token: str
    ) -> None:
        """Delete the initial response of an interaction.

        Parameters
        ----------
        application : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialApplication]
            Object or ID of the application to delete a command response for.
        token : str
            The interaction's token.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the interaction or response is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_autocomplete_response(
        self,
        interaction: snowflakes.SnowflakeishOr[base_interactions.PartialInteraction],
        token: str,
        choices: typing.Sequence[special_endpoints.AutocompleteChoiceBuilder],
    ) -> None:
        """Create the initial response for an autocomplete interaction.

        Parameters
        ----------
        interaction : hikari.snowflakes.SnowflakeishOr[hikari.interactions.base_interactions.PartialInteraction]
            Object or ID of the interaction this response is for.
        token : str
            The command interaction's token.
        choices : typing.Sequence[hikari.api.special_endpoints.AutocompleteChoiceBuilder]
            The autocomplete choices themselves.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the interaction is not found or if the interaction's initial
            response has already been created.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    async def create_modal_response(
        self,
        interaction: snowflakes.SnowflakeishOr[base_interactions.PartialInteraction],
        token: str,
        *,
        title: str,
        custom_id: str,
        component: undefined.UndefinedOr[special_endpoints.ComponentBuilder] = undefined.UNDEFINED,
        components: undefined.UndefinedOr[typing.Sequence[special_endpoints.ComponentBuilder]] = undefined.UNDEFINED,
    ) -> None:
        """Create a response by sending a modal.

        Parameters
        ----------
        interaction : hikari.snowflakes.SnowflakeishOr[hikari.interactions.base_interactions.PartialInteraction]
            Object or ID of the interaction this response is for.
        token : str
            The command interaction's token.
        title : str
            The title that will show up in the modal.
        custom_id : str
            Developer set custom ID used for identifying interactions with this modal.

        Other Parameters
        ----------------
        component : hikari.undefined.UndefinedOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            A component builders to send in this modal.
        components : hikari.undefined.UndefinedOr[typing.Sequence[hikari.api.special_endpoints.ComponentBuilder]]
            A sequence of component builders to send in this modal.

        Raises
        ------
        ValueError
            If both `component` and `components` are specified or if none are specified.
        """

    @abc.abstractmethod
    def build_message_action_row(self) -> special_endpoints.MessageActionRowBuilder:
        """Build a message action row message component for use in message create and REST calls.

        Returns
        -------
        hikari.api.special_endpoints.MessageActionRowBuilder
            The initialised action row builder.
        """

    @abc.abstractmethod
    def build_modal_action_row(self) -> special_endpoints.ModalActionRowBuilder:
        """Build an action row modal component for use in interactions and REST calls.

        Returns
        -------
        hikari.api.special_endpoints.ModalActionRowBuilder
            The initialised action row builder.
        """

    @abc.abstractmethod
    async def fetch_scheduled_event(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        event: snowflakes.SnowflakeishOr[scheduled_events.ScheduledEvent],
        /,
    ) -> scheduled_events.ScheduledEvent:
        """Fetch a scheduled event.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialGuild]
            The guild the event bellongs to. This may be the object or the
            ID of an existing guild.
        event : hikari.snowflakes.SnowflakeishOr[hikari.scheduled_events.ScheduledEvent]
            The event to fetch. This may be the object or the
            ID of an existing event.

        Returns
        -------
        hikari.scheduled_events.ScheduledEvent
            The scheduled event.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the permission needed to view this event.

            For `VOICE` and `STAGE_CHANNEL` events, [`hikari.permissions.Permissions.VIEW_CHANNEL`][]
            is required in their associated guild to see the event.
        hikari.errors.NotFoundError
            If the guild or event is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def fetch_scheduled_events(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> typing.Sequence[scheduled_events.ScheduledEvent]:
        """Fetch the scheduled events for a guild.

        !!! note
            `VOICE` and `STAGE_CHANNEL` events are only included if the bot has
            `VOICE` or `STAGE_CHANNEL` permissions in the associated channel.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to fetch scheduled events for.

        Returns
        -------
        typing.Sequence[hikari.scheduled_events.ScheduledEvent]
            Sequence of the scheduled events.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_stage_event(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels_.PartialChannel],
        name: str,
        /,
        start_time: datetime.datetime,
        *,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        end_time: undefined.UndefinedOr[datetime.datetime] = undefined.UNDEFINED,
        image: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        privacy_level: typing.Union[
            int, scheduled_events.EventPrivacyLevel
        ] = scheduled_events.EventPrivacyLevel.GUILD_ONLY,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> scheduled_events.ScheduledStageEvent:
        """Create a scheduled stage event.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the event in.
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            The stage channel to create the event in.
        name : str
            The name of the event.
        start_time : datetime.datetime
            When the event is scheduled to start.

        Other Parameters
        ----------------
        description : hikari.undefined.UndefinedOr[str]
            The event's description.
        end_time : hikari.undefined.UndefinedOr[datetime.datetime]
            When the event should be scheduled to end.
        image : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            The event's display image.
        privacy_level : hikari.undefined.UndefinedOr[hikari.scheduled_events.EventPrivacyLevel]
            The event's privacy level.

            This effects who can view and subscribe to the event.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.scheduled_events.ScheduledStageEvent
            The created scheduled stage event.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing permissions to create the scheduled event.

            You need the following permissions in the target stage channel:
            [`hikari.permissions.Permissions.MANAGE_EVENTS`][],
            [`hikari.permissions.Permissions.VIEW_CHANNEL`][],
            and [`hikari.permissions.Permissions.CONNECT`][].
        hikari.errors.NotFoundError
            If the guild or event is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_voice_event(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels_.PartialChannel],
        name: str,
        /,
        start_time: datetime.datetime,
        *,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        end_time: undefined.UndefinedOr[datetime.datetime] = undefined.UNDEFINED,
        image: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        privacy_level: typing.Union[
            int, scheduled_events.EventPrivacyLevel
        ] = scheduled_events.EventPrivacyLevel.GUILD_ONLY,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> scheduled_events.ScheduledVoiceEvent:
        """Create a scheduled voice event.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the event in.
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            The voice channel to create the event in.
        name : str
            The name of the event.
        start_time : datetime.datetime
            When the event is scheduled to start.

        Other Parameters
        ----------------
        description : hikari.undefined.UndefinedOr[str]
            The event's description.
        end_time : hikari.undefined.UndefinedOr[datetime.datetime]
            When the event should be scheduled to end.
        image : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            The event's display image.
        privacy_level : hikari.undefined.UndefinedOr[hikari.scheduled_events.EventPrivacyLevel]
            The event's privacy level.

            This effects who can view and subscribe to the event.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.scheduled_events.ScheduledVoiceEvent
            The created scheduled voice event.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing permissions to create the scheduled event.

            You need the following permissions in the target voice channel:
            [`hikari.permissions.Permissions.MANAGE_EVENTS`][],
            [`hikari.permissions.Permissions.VIEW_CHANNEL`][],
            and [`hikari.permissions.Permissions.CONNECT`][].
        hikari.errors.NotFoundError
            If the guild or event is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_external_event(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        name: str,
        /,
        location: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        *,
        description: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        image: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        privacy_level: typing.Union[
            int, scheduled_events.EventPrivacyLevel
        ] = scheduled_events.EventPrivacyLevel.GUILD_ONLY,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> scheduled_events.ScheduledExternalEvent:
        """Create a scheduled external event.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to create the event in.
        name : str
            The name of the event.
        location : str
            The location the event.
        start_time : datetime.datetime
            When the event is scheduled to start.
        end_time : datetime.datetime
            When the event is scheduled to end.

        Other Parameters
        ----------------
        description : hikari.undefined.UndefinedOr[str]
            The event's description.
        image : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            The event's display image.
        privacy_level : hikari.undefined.UndefinedOr[hikari.scheduled_events.EventPrivacyLevel]
            The event's privacy level.

            This effects who can view and subscribe to the event.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.scheduled_events.ScheduledExternalEvent
            The created scheduled external event.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_EVENTS`][] permission.
        hikari.errors.NotFoundError
            If the guild or event is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_scheduled_event(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        event: snowflakes.SnowflakeishOr[scheduled_events.ScheduledEvent],
        /,
        *,
        channel: undefined.UndefinedNoneOr[snowflakes.SnowflakeishOr[channels_.PartialChannel]] = undefined.UNDEFINED,
        description: undefined.UndefinedNoneOr[str] = undefined.UNDEFINED,
        entity_type: undefined.UndefinedOr[
            typing.Union[int, scheduled_events.ScheduledEventType]
        ] = undefined.UNDEFINED,
        image: undefined.UndefinedOr[files.Resourceish] = undefined.UNDEFINED,
        location: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        name: undefined.UndefinedOr[str] = undefined.UNDEFINED,
        privacy_level: undefined.UndefinedOr[
            typing.Union[int, scheduled_events.EventPrivacyLevel]
        ] = undefined.UNDEFINED,
        start_time: undefined.UndefinedOr[datetime.datetime] = undefined.UNDEFINED,
        end_time: undefined.UndefinedNoneOr[datetime.datetime] = undefined.UNDEFINED,
        status: undefined.UndefinedOr[typing.Union[int, scheduled_events.ScheduledEventStatus]] = undefined.UNDEFINED,
        reason: undefined.UndefinedOr[str] = undefined.UNDEFINED,
    ) -> scheduled_events.ScheduledEvent:
        """Edit a scheduled event.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to edit the event in.
        event : hikari.snowflakes.SnowflakeishOr[hikari.scheduled_events.ScheduledEvent]
            The scheduled event to edit.

        Other Parameters
        ----------------
        channel : hikari.undefined.UndefinedNoneOr[hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]]
            The channel a `VOICE` or `STAGE` event should be associated with.
        description : hikari.undefined.UndefinedNoneOr[str]
            The event's description.
        entity_type : hikari.undefined.UndefinedOr[hikari.scheduled_events.ScheduledEventType]
            The type of entity the event should target.
        image : hikari.undefined.UndefinedOr[hikari.files.Resourceish]
            The event's display image.
        location : hikari.undefined.UndefinedOr[str]
            The location of an `EXTERNAL` event.

            Must be passed when changing an event to `EXTERNAL`.
        name : hikari.undefined.UndefinedOr[str]
            The event's name.
        privacy_level : hikari.undefined.UndefinedOr[hikari.scheduled_events.EventPrivacyLevel]
            The event's privacy level.

            This effects who can view and subscribe to the event.
        start_time : hikari.undefined.UndefinedOr[datetime.datetime]
            When the event should be scheduled to start.
        end_time : hikari.undefined.UndefinedNoneOr[datetime.datetime]
            When the event should be scheduled to end.

            This can only be set to [`None`][] for `STAGE` and `VOICE` events.
            Must be provided when changing an event to `EXTERNAL`.
        status : hikari.undefined.UndefinedOr[hikari.scheduled_events.ScheduledEventStatus]
            The event's new status.

            `SCHEDULED` events can be set to `ACTIVE` and `CANCELED`.
            `ACTIVE` events can only be set to `COMPLETED`.
        reason : hikari.undefined.UndefinedOr[str]
            If provided, the reason that will be recorded in the audit logs.
            Maximum of 512 characters.

        Returns
        -------
        hikari.scheduled_events.ScheduledEvent
            The edited scheduled event.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing permissions to edit the scheduled event.

            For `VOICE` and `STAGE_INSTANCE` events, you need the following
            permissions in the event's associated channel: [`hikari.permissions.Permissions.MANAGE_EVENTS`][],
            [`hikari.permissions.Permissions.VIEW_CHANNEL`][] and [`hikari.permissions.Permissions.CONNECT`][].

            For `EXTERNAL` events you just need the [`hikari.permissions.Permissions.MANAGE_EVENTS`][] permission.
        hikari.errors.NotFoundError
            If the guild or event is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_scheduled_event(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        event: snowflakes.SnowflakeishOr[scheduled_events.ScheduledEvent],
        /,
    ) -> None:
        """Delete a scheduled event.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to delete the event from.
        event : hikari.snowflakes.SnowflakeishOr[hikari.scheduled_events.ScheduledEvent]
            The scheduled event to delete.

        Raises
        ------
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.ForbiddenError
            If you are missing the [`hikari.permissions.Permissions.MANAGE_EVENTS`][] permission.
        hikari.errors.NotFoundError
            If the guild or event is not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_scheduled_event_users(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        event: snowflakes.SnowflakeishOr[scheduled_events.ScheduledEvent],
        /,
        *,
        newest_first: bool = False,
        start_at: undefined.UndefinedOr[snowflakes.SearchableSnowflakeishOr[users.PartialUser]] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[scheduled_events.ScheduledEventUser]:
        """Asynchronously iterate over the users who're subscribed to a scheduled event.

        !!! note
            This call is not a coroutine function, it returns a special type of
            lazy iterator that will perform API calls as you iterate across it,
            thus any errors documented below will happen then.

            See [`hikari.iterators`][] for the full API for this iterator type.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            The guild to fetch the scheduled event users from.
        event : hikari.snowflakes.SnowflakeishOr[hikari.scheduled_events.ScheduledEvent]
            The scheduled event to fetch the subscribed users for.

        Other Parameters
        ----------------
        newest_first : bool
            Whether to fetch the newest first or the oldest first.
        start_at : hikari.undefined.UndefinedOr[hikari.snowflakes.SearchableSnowflakeishOr[hikari.guilds.PartialGuild]]
            If provided, will start at this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake. This
            may also be a scheduled event object object. In this case, the
            date the object was first created will be used.

        Returns
        -------
        hikari.iterators.LazyIterator[hikari.scheduled_events.ScheduledEventUser]
            The token's associated guilds.

        Raises
        ------
        hikari.errors.BadRequestError
            If any of the fields that are passed have an invalid value.
        hikari.errors.UnauthorizedError
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFoundError
            If the guild or event was not found.
        hikari.errors.RateLimitTooLongError
            Raised in the event that a rate limit occurs that is
            longer than `max_rate_limit` when making a request.
        hikari.errors.InternalServerError
            If an internal error occurs on Discord while handling the request.
        """
