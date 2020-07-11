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
"""Provides an interface for REST API implementations to follow."""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["IRESTClient"]

import abc
import typing

from hikari.api import component
from hikari.utilities import undefined

if typing.TYPE_CHECKING:
    import datetime

    from hikari.api.rest import special_endpoints
    from hikari.models import applications
    from hikari.models import audit_logs
    from hikari.models import channels
    from hikari.models import colors
    from hikari.models import emojis
    from hikari.models import embeds as embeds_
    from hikari.models import gateway
    from hikari.models import guilds
    from hikari.models import invites
    from hikari.models import messages as messages_
    from hikari.models import permissions as permissions_
    from hikari.models import users
    from hikari.models import voices
    from hikari.models import webhooks
    from hikari.utilities import date
    from hikari.utilities import files
    from hikari.utilities import iterators
    from hikari.utilities import snowflake


class IRESTClient(component.IComponent, abc.ABC):
    """Interface for functionality that a REST API implementation provides."""

    __slots__ = ()

    @abc.abstractmethod
    async def close(self) -> None:
        """Close the client session."""

    @abc.abstractmethod
    async def fetch_channel(
        self, channel: typing.Union[channels.PartialChannel, snowflake.UniqueObject]
    ) -> channels.PartialChannel:
        """Fetch a channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to fetch. This may be a channel object, or the ID of an
            existing channel.

        Returns
        -------
        hikari.models.channels.PartialChannel
            The fetched channel.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to access the channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def edit_channel(
        self,
        channel: typing.Union[channels.PartialChannel, snowflake.UniqueObject],
        /,
        *,
        name: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        position: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        topic: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        nsfw: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        bitrate: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        user_limit: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        rate_limit_per_user: typing.Union[undefined.UndefinedType, date.TimeSpan] = undefined.UNDEFINED,
        permission_overwrites: typing.Union[
            undefined.UndefinedType, typing.Sequence[channels.PermissionOverwrite]
        ] = undefined.UNDEFINED,
        parent_category: typing.Union[
            undefined.UndefinedType, channels.GuildCategory, snowflake.UniqueObject
        ] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> channels.PartialChannel:
        """Edit a channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to edit. This may be a channel object, or the ID of an
            existing channel.
        name : hikari.utilities.undefined.UndefinedType or builtins.str
            If provided, the new name for the channel.
        position : hikari.utilities.undefined.UndefinedType or builtins.int
            If provided, the new position for the channel.
        topic : hikari.utilities.undefined.UndefinedType or builtins.str
            If provided, the new topic for the channel.
        nsfw : hikari.utilities.undefined.UndefinedType or builtins.bool
            If provided, whether the channel should be marked as NSFW or not.
        bitrate : hikari.utilities.undefined.UndefinedType or builtins.int
            If provided, the new bitrate for the channel.
        user_limit : hikari.utilities.undefined.UndefinedType or builtins.int
            If provided, the new user limit in the channel.
        rate_limit_per_user : hikari.utilities.undefined.UndefinedType or datetime.timedelta or builtins.float or builtins.int
            If provided, the new rate limit per user in the channel.
        permission_overwrites : hikari.utilities.undefined.UndefinedType or typing.Sequence[hikari.models.channels.PermissionOverwrite]
            If provided, the new permission overwrites for the channel.
        parent_category : hikari.utilities.undefined.UndefinedType or hikari.models.channels.GuildCategory or hikari.utilities.snowflake.UniqueObject
            If provided, the new guild category for the channel. This may be
            a category object, or the ID of an existing category.
        reason : hikari.utilities.undefined.UndefinedType or builtins.str
            If provided, the reason that will be recorded in the audit logs.

        Returns
        -------
        hikari.models.channels.PartialChannel
            The edited channel.

        Raises
        ------
        hikari.errors.BadRequest
            If any of the fields that are passed have an invalid value.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to edit the channel
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def delete_channel(self, channel: typing.Union[channels.PartialChannel, snowflake.UniqueObject]) -> None:
        """Delete a channel in a guild, or close a DM.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to delete. This may be a channel object, or the ID of an
            existing channel.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to delete the channel in a guild.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.

        !!! note
            For Public servers, the set 'Rules' or 'Guidelines' channels and the
            'Public Server Updates' channel cannot be deleted.
        """

    @typing.overload
    @abc.abstractmethod
    async def edit_permission_overwrites(
        self,
        channel: typing.Union[channels.GuildChannel, snowflake.UniqueObject],
        target: typing.Union[channels.PermissionOverwrite, users.UserImpl, guilds.Role],
        *,
        allow: typing.Union[undefined.UndefinedType, permissions_.Permission] = undefined.UNDEFINED,
        deny: typing.Union[undefined.UndefinedType, permissions_.Permission] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> None:
        """Edit permissions for a target entity."""

    @typing.overload
    @abc.abstractmethod
    async def edit_permission_overwrites(
        self,
        channel: typing.Union[channels.GuildChannel, snowflake.UniqueObject],
        target: typing.Union[int, str, snowflake.Snowflake],
        *,
        target_type: typing.Union[channels.PermissionOverwriteType, str],
        allow: typing.Union[undefined.UndefinedType, permissions_.Permission] = undefined.UNDEFINED,
        deny: typing.Union[undefined.UndefinedType, permissions_.Permission] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> None:
        """Edit permissions for a given entity ID and type."""

    @abc.abstractmethod
    async def edit_permission_overwrites(
        self,
        channel: typing.Union[channels.GuildChannel, snowflake.UniqueObject],
        target: typing.Union[snowflake.UniqueObject, users.UserImpl, guilds.Role, channels.PermissionOverwrite],
        *,
        target_type: typing.Union[undefined.UndefinedType, channels.PermissionOverwriteType, str] = undefined.UNDEFINED,
        allow: typing.Union[undefined.UndefinedType, permissions_.Permission] = undefined.UNDEFINED,
        deny: typing.Union[undefined.UndefinedType, permissions_.Permission] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> None:
        """Edit permissions for a specific entity in the given guild channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to edit a permission overwrite in. This may be a channel object, or
            the ID of an existing channel.
        target : hikari.models.users.UserImpl or hikari.models.guilds.Role or hikari.models.channels.PermissionOverwrite or hikari.utilities.snowflake.UniqueObject
            The channel overwrite to edit. This may be a overwrite object, or the ID of an
            existing channel.
        target_type : hikari.utilities.undefined.UndefinedType or hikari.models.channels.PermissionOverwriteType or builtins.str
            If provided, the type of the target to update. If unset, will attempt to get
            the type from `target`.
        allow : hikari.utilities.undefined.UndefinedType or hikari.models.permissions.Permission
            If provided, the new vale of all allowed permissions.
        deny : hikari.utilities.undefined.UndefinedType or hikari.models.permissions.Permission
            If provided, the new vale of all disallowed permissions.
        reason : hikari.utilities.undefined.UndefinedType or builtins.str
            If provided, the reason that will be recorded in the audit logs.

        Raises
        ------
        builtins.TypeError
            If `target_type` is unset and we were unable to determine the type
            from `target`.
        hikari.errors.BadRequest
            If any of the fields that are passed have an invalid value.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to edit the permission overwrites.
        hikari.errors.NotFound
            If the channel is not found or the target is not found if it is
            a role.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def delete_permission_overwrite(
        self,
        channel: typing.Union[channels.GuildChannel, snowflake.UniqueObject],
        target: typing.Union[channels.PermissionOverwrite, guilds.Role, users.UserImpl, snowflake.UniqueObject],
    ) -> None:
        """Delete a custom permission for an entity in a given guild channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to delete a permission overwrite in. This may be a channel
            object, or the ID of an existing channel.
        target : hikari.models.users.UserImpl or hikari.models.guilds.Role or hikari.models.channels.PermissionOverwrite or hikari.utilities.snowflake.UniqueObject
            The channel overwrite to delete.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to delete the permission overwrite.
        hikari.errors.NotFound
            If the channel is not found or the target is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def fetch_channel_invites(
        self, channel: typing.Union[channels.GuildChannel, snowflake.UniqueObject]
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        """Fetch all invites pointing to the given guild channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to fetch the invites from. This may be a channel
            object, or the ID of an existing channel.

        Returns
        -------
        typing.Sequence[hikari.models.invites.InviteWithMetadata]
            The invites pointing to the given guild channel.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to view the invites for the given channel.
        hikari.errors.NotFound
            If the channel is not found in any guilds you are a member of.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_invite(
        self,
        channel: typing.Union[channels.GuildChannel, snowflake.UniqueObject],
        *,
        max_age: typing.Union[undefined.UndefinedType, int, float, datetime.timedelta] = undefined.UNDEFINED,
        max_uses: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        temporary: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        unique: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        target_user: typing.Union[
            undefined.UndefinedType, users.UserImpl, snowflake.UniqueObject
        ] = undefined.UNDEFINED,
        target_user_type: typing.Union[undefined.UndefinedType, invites.TargetUserType] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> invites.InviteWithMetadata:
        """Create an invite to the given guild channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to create a invite for. This may be a channel object,
            or the ID of an existing channel.
        max_age : hikari.utilities.undefined.UndefinedType or datetime.timedelta or builtins.float or builtins.int
            If provided, the duration of the invite before expiry.
        max_uses : hikari.utilities.undefined.UndefinedType or builtins.int
            If provided, the max uses the invite can have.
        temporary : hikari.utilities.undefined.UndefinedType or builtins.bool
            If provided, whether the invite only grants temporary membership.
        unique : hikari.utilities.undefined.UndefinedType or builtins.bool
            If provided, wheter the invite should be unique.
        target_user : hikari.utilities.undefined.UndefinedType or hikari.models.users.UserImpl or hikari.utilities.snowflake.UniqueObject
            If provided, the target user id for this invite. This may be a
            user object, or the ID of an existing user.
        target_user_type : hikari.utilities.undefined.UndefinedType or hikari.models.invites.TargetUserType or builtins.int
            If provided, the type of target user for this invite.
        reason : hikari.utilities.undefined.UndefinedType or builtins.str
            If provided, the reason that will be recorded in the audit logs.

        Returns
        -------
        hikari.models.invites.InviteWithMetadata
            The invite to the given guild channel.

        Raises
        ------
        hikari.errors.BadRequest
            If any of the fields that are passed have an invalid value.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to create the given channel.
        hikari.errors.NotFound
            If the channel is not found, or if the target user does not exist,
            if specified.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    def trigger_typing(
        self, channel: typing.Union[channels.TextChannel, snowflake.UniqueObject]
    ) -> special_endpoints.TypingIndicator:
        """Trigger typing in a text channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to trigger typing in. This may be a channel object, or
            the ID of an existing channel.

        Returns
        -------
        hikari.api.special_endpoints.TypingIndicator
            A typing indicator to use.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to read messages or send messages in the
            text channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.

        !!! note
            The exceptions on this _endpoint will only be raised once the result
            is awaited or interacted with. Invoking this function itself will
            not raise any of the above types.
        """

    @abc.abstractmethod
    async def fetch_pins(
        self, channel: typing.Union[channels.TextChannel, snowflake.UniqueObject]
    ) -> typing.Sequence[messages_.Message]:
        """Fetch the pinned messages in this text channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to fetch pins from. This may be a channel object, or
            the ID of an existing channel.

        Returns
        -------
        typing.Sequence[hikari.models.messages.Message]
            The pinned messages in this text channel.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to read messages or send messages in the
            text channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def pin_message(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        message: typing.Union[messages_.Message, snowflake.UniqueObject],
    ) -> None:
        """Pin an existing message in the given text channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to pin a message in. This may be a channel object, or
            the ID of an existing channel.
        message : hikari.models.messages.Message or hikari.utilities.snowflake.UniqueObject
            The message to pin. This may be a message object,
            or the ID of an existing message.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to pin messages in the given channel.
        hikari.errors.NotFound
            If the channel is not found, or if the message does not exist in
            the given channel.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def unpin_message(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        message: typing.Union[messages_.Message, snowflake.UniqueObject],
    ) -> None:
        """Unpin a given message from a given text channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to unpin a message in. This may be a channel object, or
            the ID of an existing channel.
        message : hikari.models.messages.Message or hikari.utilities.snowflake.UniqueObject
            The message to unpin. This may be a message object, or the ID of an
            existing message.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to pin messages in the given channel.
        hikari.errors.NotFound
            If the channel is not found or the message is not a pinned message
            in the given channel.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    def fetch_messages(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        *,
        before: typing.Union[undefined.UndefinedType, datetime.datetime, snowflake.UniqueObject] = undefined.UNDEFINED,
        after: typing.Union[undefined.UndefinedType, datetime.datetime, snowflake.UniqueObject] = undefined.UNDEFINED,
        around: typing.Union[undefined.UndefinedType, datetime.datetime, snowflake.UniqueObject] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[messages_.Message]:
        """Browse the message history for a given text channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to fetch messages in. This may be a channel object, or
            the ID of an existing channel.
        before : hikari.utilities.undefined.UndefinedType or datetime.datetime or hikari.utilities.snowflake.UniqueObject
            If provided, fetch messages before this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake.
        after : hikari.utilities.undefined.UndefinedType or datetime.datetime or hikari.utilities.snowflake.UniqueObject
            If provided, fetch messages after this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake.
        around : hikari.utilities.undefined.UndefinedType or datetime.datetime or hikari.utilities.snowflake.UniqueObject
            If provided, fetch messages around this snowflake. If you provide
            a datetime object, it will be transformed into a snowflake.

        Returns
        -------
        hikari.utilities.iterators.LazyIterator[hikari.models.messages.Message]
            A iterator to fetch the messages.

        Raises
        ------
        builtins.TypeError
            If you specify more than one of `before`, `after`, `about`.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to read message history in the given
            channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.

        !!! note
            The exceptions on this _endpoint (other than `builtins.TypeError`) will only
            be raised once the result is awaited or interacted with. Invoking
            this function itself will not raise anything (other than
            `builtins.TypeError`).
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def fetch_message(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        message: typing.Union[messages_.Message, snowflake.UniqueObject],
    ) -> messages_.Message:
        """Fetch a specific message in the given text channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to fetch messages in. This may be a channel object, or
            the ID of an existing channel.
        message : hikari.models.messages.Message or hikari.utilities.snowflake.UniqueObject
            The message to fetch. This may be a channel object, or the ID of an
            existing channel.

        Returns
        -------
        hikari.models.messages.Message
            The requested message.

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to read message history in the given
            channel.
        hikari.errors.NotFound
            If the channel is not found or the message is not found in the
            given text channel.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def create_message(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        text: typing.Union[undefined.UndefinedType, typing.Any] = undefined.UNDEFINED,
        *,
        embed: typing.Union[undefined.UndefinedType, embeds_.Embed] = undefined.UNDEFINED,
        attachment: typing.Union[undefined.UndefinedType, str, files.Resource] = undefined.UNDEFINED,
        attachments: typing.Union[
            undefined.UndefinedType, typing.Sequence[typing.Union[str, files.Resource]]
        ] = undefined.UNDEFINED,
        tts: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        nonce: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        mentions_everyone: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        user_mentions: typing.Union[
            typing.Collection[typing.Union[users.UserImpl, snowflake.UniqueObject]], bool, undefined.UndefinedType
        ] = undefined.UNDEFINED,
        role_mentions: typing.Union[
            typing.Collection[typing.Union[guilds.Role, snowflake.UniqueObject]], bool, undefined.UndefinedType
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        """Create a message in the given channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to create the message in. This may be a channel object, or
            the ID of an existing channel.
        text : hikari.utilities.undefined.UndefinedType or builtins.str
            If specified, the message contents.
        embed : hikari.utilities.undefined.UndefinedType or hikari.models.embeds.Embed
            If specified, the message embed.
        attachment : hikari.utilities.undefined.UndefinedType or builtins.str or hikari.utilities.files.Resource
            If specified, the message attachment. This can be a resource,
            or string of a path on your computer or a URL.
        attachments : hikari.utilities.undefined.UndefinedType or typing.Sequence[builtins.str or hikari.utilities.files.Resource]
            If specified, the message attachments. These can be resources, or
            strings consisting of paths on your computer or URLs.
        tts : hikari.utilities.undefined.UndefinedType or builtins.bool
            If specified, whether the message will be TTS (Text To Speech).
        nonce : hikari.utilities.undefined.UndefinedType or builtins.str
            If specified, a nonce that can be used for optimistic message sending.
        mentions_everyone : builtins.bool or hikari.utilities.undefined.UndefinedType
            If specified, whether the message should parse @everyone/@here mentions.
        user_mentions : typing.Collection[hikari.models.users.UserImpl or hikari.utilities.snowflake.UniqueObject] or builtins.bool or hikari.utilities.undefined.UndefinedType
            If specified, and a `builtins.bool`, whether to parse user mentions.
            If specified and a `builtins.list`, the users to parse the mention
            for. This may be a user object, or the ID of an existing user.
        role_mentions : typing.Collection[hikari.models.guilds.Role or hikari.utilities.snowflake.UniqueObject] or builtins.bool or hikari.utilities.undefined.UndefinedType
            If specified and `builtins.bool`, whether to parse role mentions. If specified and
            `builtins.list`, the roles to parse the mention for. This may be a role object, or
            the ID of an existing role.

        Returns
        -------
        hikari.models.messages.Message
            The created message.

        Raises
        ------
        hikari.errors.BadRequest
            This may be raised in several discrete situations, such as messages
            being empty with no attachments or embeds; messages with more than
            2000 characters in them, embeds that exceed one of the many embed
            limits; too many attachments; attachments that are too large;
            invalid image URLs in embeds; users in `user_mentions` not being
            mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to send messages in the given channel.
        hikari.errors.NotFound
            If the channel is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        builtins.ValueError
            If more than 100 unique objects/entities are passed for
            `role_mentions` or `user_mentions`.
        builtins.TypeError
            If both `attachment` and `attachments` are specified.

        !!! warning
            You are expected to make a connection to the gateway and identify
            once before being able to use this _endpoint for a bot.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def edit_message(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        message: typing.Union[messages_.Message, snowflake.UniqueObject],
        text: typing.Union[undefined.UndefinedType, None, typing.Any] = undefined.UNDEFINED,
        *,
        embed: typing.Union[undefined.UndefinedType, None, embeds_.Embed] = undefined.UNDEFINED,
        mentions_everyone: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        user_mentions: typing.Union[
            undefined.UndefinedType, typing.Collection[typing.Union[users.UserImpl, snowflake.UniqueObject]], bool
        ] = undefined.UNDEFINED,
        role_mentions: typing.Union[
            undefined.UndefinedType, typing.Collection[typing.Union[snowflake.UniqueObject, guilds.Role]], bool
        ] = undefined.UNDEFINED,
        flags: typing.Union[undefined.UndefinedType, messages_.MessageFlag] = undefined.UNDEFINED,
    ) -> messages_.Message:
        """Edit an existing message in a given channel.

        Parameters
        ----------
        channel : hikari.models.channels.PartialChannel or hikari.utilities.snowflake.UniqueObject
            The channel to edit the message in. This may be a channel object, or
            the ID of an existing channel.
        message : hikari.models.messages.Message or hikari.utilities.snowflake.UniqueObject
            The message to fetch.
        text
        embed
        mentions_everyone
        user_mentions
        role_mentions
        flags

        Returns
        -------
        hikari.models.messages.Message
            The edited message.

        Raises
        ------
        hikari.errors.BadRequest
            This may be raised in several discrete situations, such as messages
            being empty with no embeds; messages with more than 2000 characters
            in them, embeds that exceed one of the many embed
            limits; invalid image URLs in embeds; users in `user_mentions` not
            being mentioned in the message content; roles in `role_mentions` not
            being mentioned in the message content.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to send messages in the given channel; if
            you try to change the contents of another user's message; or if you
            try to edit the flags on another user's message without the
            permissions to manage messages_.
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_message(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        message: typing.Union[messages_.Message, snowflake.UniqueObject],
    ) -> None:
        """Delete a given message in a given channel.

        Parameters
        ----------
        channel
        message

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack the permissions to manage messages, and the message is
            not composed by your associated user.
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_messages(
        self,
        channel: typing.Union[channels.GuildTextChannel, snowflake.UniqueObject],
        /,
        *messages: typing.Union[messages_.Message, snowflake.UniqueObject],
    ) -> None:
        """Bulk-delete between 2 and 100 messages from the given guild channel.

        Parameters
        ----------
        channel
        *messages

        Raises
        ------
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack the permissions to manage messages, and the message is
            not composed by your associated user.
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        TypeError
            If you do not provide between 2 and 100 messages (inclusive).
        """

    @abc.abstractmethod
    async def add_reaction(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        message: typing.Union[messages_.Message, snowflake.UniqueObject],
        emoji: typing.Union[str, emojis.Emoji],
    ) -> None:
        """Add a reaction emoji to a message in a given channel.

        Parameters
        ----------
        channel
        message
        emoji

        Raises
        ------
        hikari.errors.BadRequest
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack permissions to add reactions to messages.
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_my_reaction(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        message: typing.Union[messages_.Message, snowflake.UniqueObject],
        emoji: typing.Union[str, emojis.Emoji],
    ) -> None:
        """Delete a reaction that your application user created.

        Parameters
        ----------
        channel
        message
        emoji

        Raises
        ------
        hikari.errors.BadRequest
            If an invalid unicode emoji is given, or if the given custom emoji
            does not exist.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.NotFound
            If the channel or message is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """

    @abc.abstractmethod
    async def delete_all_reactions_for_emoji(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        message: typing.Union[messages_.Message, snowflake.UniqueObject],
        emoji: typing.Union[str, emojis.Emoji],
    ) -> None:
        ...

    @abc.abstractmethod
    async def delete_reaction(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        message: typing.Union[messages_.Message, snowflake.UniqueObject],
        emoji: typing.Union[str, emojis.Emoji],
        user: typing.Union[users.UserImpl, snowflake.UniqueObject],
    ) -> None:
        ...

    @abc.abstractmethod
    async def delete_all_reactions(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        message: typing.Union[messages_.Message, snowflake.UniqueObject],
    ) -> None:
        ...

    @abc.abstractmethod
    def fetch_reactions_for_emoji(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        message: typing.Union[messages_.Message, snowflake.UniqueObject],
        emoji: typing.Union[str, emojis.Emoji],
    ) -> iterators.LazyIterator[users.UserImpl]:
        ...

    @abc.abstractmethod
    async def create_webhook(
        self,
        channel: typing.Union[channels.TextChannel, snowflake.UniqueObject],
        name: str,
        *,
        avatar: typing.Union[undefined.UndefinedType, files.Resource, str] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> webhooks.Webhook:
        ...

    @abc.abstractmethod
    async def fetch_webhook(
        self,
        webhook: typing.Union[webhooks.Webhook, snowflake.UniqueObject],
        *,
        token: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> webhooks.Webhook:
        ...

    @abc.abstractmethod
    async def fetch_channel_webhooks(
        self, channel: typing.Union[channels.TextChannel, snowflake.UniqueObject]
    ) -> typing.Sequence[webhooks.Webhook]:
        ...

    @abc.abstractmethod
    async def fetch_guild_webhooks(
        self, guild: typing.Union[guilds.Guild, snowflake.UniqueObject]
    ) -> typing.Sequence[webhooks.Webhook]:
        ...

    @abc.abstractmethod
    async def edit_webhook(
        self,
        webhook: typing.Union[webhooks.Webhook, snowflake.UniqueObject],
        *,
        token: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        name: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        avatar: typing.Union[None, undefined.UndefinedType, files.Resource, str] = undefined.UNDEFINED,
        channel: typing.Union[
            undefined.UndefinedType, channels.TextChannel, snowflake.UniqueObject
        ] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> webhooks.Webhook:
        ...

    @abc.abstractmethod
    async def delete_webhook(
        self,
        webhook: typing.Union[webhooks.Webhook, snowflake.UniqueObject],
        *,
        token: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def execute_webhook(
        self,
        webhook: typing.Union[webhooks.Webhook, snowflake.UniqueObject],
        token: str,
        text: typing.Union[undefined.UndefinedType, typing.Any] = undefined.UNDEFINED,
        *,
        username: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        avatar_url: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        embeds: typing.Union[undefined.UndefinedType, typing.Sequence[embeds_.Embed]] = undefined.UNDEFINED,
        attachment: typing.Union[undefined.UndefinedType, str, files.Resource] = undefined.UNDEFINED,
        attachments: typing.Union[
            undefined.UndefinedType, typing.Sequence[typing.Union[str, files.Resource]]
        ] = undefined.UNDEFINED,
        tts: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        mentions_everyone: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        user_mentions: typing.Union[
            typing.Collection[typing.Union[users.UserImpl, snowflake.UniqueObject]], bool, undefined.UndefinedType,
        ] = undefined.UNDEFINED,
        role_mentions: typing.Union[
            typing.Collection[typing.Union[snowflake.UniqueObject, guilds.Role]], bool, undefined.UndefinedType,
        ] = undefined.UNDEFINED,
    ) -> messages_.Message:
        ...

    @abc.abstractmethod
    async def fetch_gateway_url(self) -> str:
        ...

    @abc.abstractmethod
    async def fetch_gateway_bot(self) -> gateway.GatewayBot:
        ...

    @abc.abstractmethod
    async def fetch_invite(self, invite: typing.Union[invites.Invite, str]) -> invites.Invite:
        ...

    @abc.abstractmethod
    async def delete_invite(self, invite: typing.Union[invites.Invite, str]) -> None:
        ...

    @abc.abstractmethod
    async def fetch_my_user(self) -> users.OwnUser:
        ...

    @abc.abstractmethod
    async def edit_my_user(
        self,
        *,
        username: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        avatar: typing.Union[undefined.UndefinedType, None, files.Resource, str] = undefined.UNDEFINED,
    ) -> users.OwnUser:
        ...

    @abc.abstractmethod
    async def fetch_my_connections(self) -> typing.Sequence[applications.OwnConnection]:
        ...

    @abc.abstractmethod
    def fetch_my_guilds(
        self,
        *,
        newest_first: bool = False,
        start_at: typing.Union[
            undefined.UndefinedType, guilds.PartialGuild, snowflake.UniqueObject, datetime.datetime
        ] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[applications.OwnGuild]:
        ...

    @abc.abstractmethod
    async def leave_guild(self, guild: typing.Union[guilds.Guild, snowflake.UniqueObject], /) -> None:
        ...

    @abc.abstractmethod
    async def create_dm_channel(
        self, user: typing.Union[users.UserImpl, snowflake.UniqueObject], /
    ) -> channels.DMChannel:
        ...

    @abc.abstractmethod
    async def fetch_application(self) -> applications.Application:
        ...

    @abc.abstractmethod
    async def add_user_to_guild(
        self,
        access_token: str,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        user: typing.Union[users.UserImpl, snowflake.UniqueObject],
        *,
        nick: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        roles: typing.Union[
            undefined.UndefinedType, typing.Collection[typing.Union[guilds.Role, snowflake.UniqueObject]]
        ] = undefined.UNDEFINED,
        mute: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        deaf: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
    ) -> typing.Optional[guilds.Member]:
        ...

    @abc.abstractmethod
    async def fetch_voice_regions(self) -> typing.Sequence[voices.VoiceRegion]:
        ...

    @abc.abstractmethod
    async def fetch_user(self, user: typing.Union[users.UserImpl, snowflake.UniqueObject]) -> users.UserImpl:
        ...

    def fetch_audit_log(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        *,
        before: typing.Union[undefined.UndefinedType, datetime.datetime, snowflake.UniqueObject] = undefined.UNDEFINED,
        user: typing.Union[undefined.UndefinedType, users.UserImpl, snowflake.UniqueObject] = undefined.UNDEFINED,
        event_type: typing.Union[undefined.UndefinedType, audit_logs.AuditLogEventType] = undefined.UNDEFINED,
    ) -> iterators.LazyIterator[audit_logs.AuditLog]:
        ...

    @abc.abstractmethod
    async def fetch_emoji(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        emoji: typing.Union[emojis.CustomEmoji, snowflake.UniqueObject],
    ) -> emojis.KnownCustomEmoji:
        ...

    @abc.abstractmethod
    async def fetch_guild_emojis(
        self, guild: typing.Union[guilds.Guild, snowflake.UniqueObject]
    ) -> typing.Set[emojis.KnownCustomEmoji]:
        ...

    @abc.abstractmethod
    async def create_emoji(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        name: str,
        image: typing.Union[files.Resource, str],
        *,
        roles: typing.Union[
            undefined.UndefinedType, typing.Collection[typing.Union[guilds.Role, snowflake.UniqueObject]]
        ] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> emojis.KnownCustomEmoji:
        ...

    @abc.abstractmethod
    async def edit_emoji(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        emoji: typing.Union[emojis.CustomEmoji, snowflake.UniqueObject],
        *,
        name: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        roles: typing.Union[
            undefined.UndefinedType, typing.Collection[typing.Union[guilds.Role, snowflake.UniqueObject]]
        ] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> emojis.KnownCustomEmoji:
        ...

    @abc.abstractmethod
    async def delete_emoji(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        # This is an emoji ID, which is the URL-safe emoji name, not the snowflake alone.
        emoji: typing.Union[emojis.CustomEmoji, snowflake.UniqueObject],
        # Reason is not currently supported for some reason. See
    ) -> None:
        ...

    @abc.abstractmethod
    def guild_builder(self, name: str, /) -> special_endpoints.GuildBuilder:
        ...

    @abc.abstractmethod
    async def fetch_guild(self, guild: typing.Union[guilds.Guild, snowflake.UniqueObject]) -> guilds.Guild:
        ...

    @abc.abstractmethod
    async def fetch_guild_preview(
        self, guild: typing.Union[guilds.PartialGuild, snowflake.UniqueObject]
    ) -> guilds.GuildPreview:
        ...

    @abc.abstractmethod
    async def edit_guild(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        *,
        name: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        region: typing.Union[undefined.UndefinedType, voices.VoiceRegion, str] = undefined.UNDEFINED,
        verification_level: typing.Union[undefined.UndefinedType, guilds.GuildVerificationLevel] = undefined.UNDEFINED,
        default_message_notifications: typing.Union[
            undefined.UndefinedType, guilds.GuildMessageNotificationsLevel
        ] = undefined.UNDEFINED,
        explicit_content_filter_level: typing.Union[
            undefined.UndefinedType, guilds.GuildExplicitContentFilterLevel
        ] = undefined.UNDEFINED,
        afk_channel: typing.Union[
            undefined.UndefinedType, channels.GuildVoiceChannel, snowflake.UniqueObject
        ] = undefined.UNDEFINED,
        afk_timeout: typing.Union[undefined.UndefinedType, date.TimeSpan] = undefined.UNDEFINED,
        icon: typing.Union[undefined.UndefinedType, None, files.Resource, str] = undefined.UNDEFINED,
        owner: typing.Union[undefined.UndefinedType, users.UserImpl, snowflake.UniqueObject] = undefined.UNDEFINED,
        splash: typing.Union[undefined.UndefinedType, None, files.Resource, str] = undefined.UNDEFINED,
        banner: typing.Union[undefined.UndefinedType, None, files.Resource, str] = undefined.UNDEFINED,
        system_channel: typing.Union[undefined.UndefinedType, channels.GuildTextChannel] = undefined.UNDEFINED,
        rules_channel: typing.Union[undefined.UndefinedType, channels.GuildTextChannel] = undefined.UNDEFINED,
        public_updates_channel: typing.Union[undefined.UndefinedType, channels.GuildTextChannel] = undefined.UNDEFINED,
        preferred_locale: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> guilds.Guild:
        ...

    @abc.abstractmethod
    async def delete_guild(self, guild: typing.Union[guilds.Guild, snowflake.UniqueObject]) -> None:
        ...

    @abc.abstractmethod
    async def fetch_guild_channels(
        self, guild: typing.Union[guilds.Guild, snowflake.UniqueObject]
    ) -> typing.Sequence[channels.GuildChannel]:
        ...

    @abc.abstractmethod
    async def create_guild_text_channel(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        name: str,
        *,
        position: typing.Union[int, undefined.UndefinedType] = undefined.UNDEFINED,
        topic: typing.Union[str, undefined.UndefinedType] = undefined.UNDEFINED,
        nsfw: typing.Union[bool, undefined.UndefinedType] = undefined.UNDEFINED,
        rate_limit_per_user: typing.Union[int, undefined.UndefinedType] = undefined.UNDEFINED,
        permission_overwrites: typing.Union[
            typing.Sequence[channels.PermissionOverwrite], undefined.UndefinedType
        ] = undefined.UNDEFINED,
        category: typing.Union[
            channels.GuildCategory, snowflake.UniqueObject, undefined.UndefinedType
        ] = undefined.UNDEFINED,
        reason: typing.Union[str, undefined.UndefinedType] = undefined.UNDEFINED,
    ) -> channels.GuildTextChannel:
        ...

    @abc.abstractmethod
    async def create_guild_news_channel(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        name: str,
        *,
        position: typing.Union[int, undefined.UndefinedType] = undefined.UNDEFINED,
        topic: typing.Union[str, undefined.UndefinedType] = undefined.UNDEFINED,
        nsfw: typing.Union[bool, undefined.UndefinedType] = undefined.UNDEFINED,
        rate_limit_per_user: typing.Union[int, undefined.UndefinedType] = undefined.UNDEFINED,
        permission_overwrites: typing.Union[
            typing.Sequence[channels.PermissionOverwrite], undefined.UndefinedType
        ] = undefined.UNDEFINED,
        category: typing.Union[
            channels.GuildCategory, snowflake.UniqueObject, undefined.UndefinedType
        ] = undefined.UNDEFINED,
        reason: typing.Union[str, undefined.UndefinedType] = undefined.UNDEFINED,
    ) -> channels.GuildNewsChannel:
        ...

    @abc.abstractmethod
    async def create_guild_voice_channel(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        name: str,
        *,
        position: typing.Union[int, undefined.UndefinedType] = undefined.UNDEFINED,
        nsfw: typing.Union[bool, undefined.UndefinedType] = undefined.UNDEFINED,
        user_limit: typing.Union[int, undefined.UndefinedType] = undefined.UNDEFINED,
        bitrate: typing.Union[int, undefined.UndefinedType] = undefined.UNDEFINED,
        permission_overwrites: typing.Union[
            typing.Sequence[channels.PermissionOverwrite], undefined.UndefinedType
        ] = undefined.UNDEFINED,
        category: typing.Union[
            channels.GuildCategory, snowflake.UniqueObject, undefined.UndefinedType
        ] = undefined.UNDEFINED,
        reason: typing.Union[str, undefined.UndefinedType] = undefined.UNDEFINED,
    ) -> channels.GuildVoiceChannel:
        ...

    @abc.abstractmethod
    async def create_guild_category(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        name: str,
        *,
        position: typing.Union[int, undefined.UndefinedType] = undefined.UNDEFINED,
        nsfw: typing.Union[bool, undefined.UndefinedType] = undefined.UNDEFINED,
        permission_overwrites: typing.Union[
            typing.Sequence[channels.PermissionOverwrite], undefined.UndefinedType
        ] = undefined.UNDEFINED,
        reason: typing.Union[str, undefined.UndefinedType] = undefined.UNDEFINED,
    ) -> channels.GuildCategory:
        ...

    @abc.abstractmethod
    async def reposition_channels(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        positions: typing.Mapping[int, typing.Union[channels.GuildChannel, snowflake.UniqueObject]],
    ) -> None:
        ...

    @abc.abstractmethod
    async def fetch_member(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        user: typing.Union[users.UserImpl, snowflake.UniqueObject],
    ) -> guilds.Member:
        ...

    @abc.abstractmethod
    def fetch_members(
        self, guild: typing.Union[guilds.Guild, snowflake.UniqueObject]
    ) -> iterators.LazyIterator[guilds.Member]:
        ...

    @abc.abstractmethod
    async def edit_member(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        user: typing.Union[users.UserImpl, snowflake.UniqueObject],
        *,
        nick: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        roles: typing.Union[
            undefined.UndefinedType, typing.Collection[typing.Union[guilds.Role, snowflake.UniqueObject]]
        ] = undefined.UNDEFINED,
        mute: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        deaf: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        voice_channel: typing.Union[
            undefined.UndefinedType, channels.GuildVoiceChannel, snowflake.UniqueObject, None
        ] = undefined.UNDEFINED,
        reason: typing.Union[str, undefined.UndefinedType] = undefined.UNDEFINED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def edit_my_nick(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        nick: typing.Optional[str],
        *,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def add_role_to_member(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        user: typing.Union[users.UserImpl, snowflake.UniqueObject],
        role: typing.Union[guilds.Role, snowflake.UniqueObject],
        *,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def remove_role_from_member(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        user: typing.Union[users.UserImpl, snowflake.UniqueObject],
        role: typing.Union[guilds.Role, snowflake.UniqueObject],
        *,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def kick_user(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        user: typing.Union[users.UserImpl, snowflake.UniqueObject],
        *,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> None:
        ...

    kick_member = kick_user
    """This is simply an alias for readability."""

    @abc.abstractmethod
    async def ban_user(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        user: typing.Union[users.UserImpl, snowflake.UniqueObject],
        *,
        delete_message_days: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> None:
        ...

    ban_member = ban_user
    """This is simply an alias for readability."""

    @abc.abstractmethod
    async def unban_user(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        user: typing.Union[users.UserImpl, snowflake.UniqueObject],
        *,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> None:
        ...

    unban_member = unban_user
    """This is simply an alias for readability."""

    @abc.abstractmethod
    async def fetch_ban(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        user: typing.Union[users.UserImpl, snowflake.UniqueObject],
    ) -> guilds.GuildMemberBan:
        ...

    @abc.abstractmethod
    async def fetch_bans(
        self, guild: typing.Union[guilds.Guild, snowflake.UniqueObject]
    ) -> typing.Sequence[guilds.GuildMemberBan]:
        ...

    @abc.abstractmethod
    async def fetch_roles(
        self, guild: typing.Union[guilds.Guild, snowflake.UniqueObject]
    ) -> typing.Sequence[guilds.Role]:
        ...

    @abc.abstractmethod
    async def create_role(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        *,
        name: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        permissions: typing.Union[undefined.UndefinedType, permissions_.Permission] = undefined.UNDEFINED,
        color: typing.Union[undefined.UndefinedType, colors.Color] = undefined.UNDEFINED,
        colour: typing.Union[undefined.UndefinedType, colors.Color] = undefined.UNDEFINED,
        hoist: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        mentionable: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> guilds.Role:
        ...

    @abc.abstractmethod
    async def reposition_roles(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        positions: typing.Mapping[int, typing.Union[guilds.Role, snowflake.UniqueObject]],
    ) -> None:
        ...

    @abc.abstractmethod
    async def edit_role(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        role: typing.Union[guilds.Role, snowflake.UniqueObject],
        *,
        name: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
        permissions: typing.Union[undefined.UndefinedType, permissions_.Permission] = undefined.UNDEFINED,
        color: typing.Union[undefined.UndefinedType, colors.Color] = undefined.UNDEFINED,
        colour: typing.Union[undefined.UndefinedType, colors.Color] = undefined.UNDEFINED,
        hoist: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        mentionable: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> guilds.Role:
        ...

    @abc.abstractmethod
    async def delete_role(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        role: typing.Union[guilds.Role, snowflake.UniqueObject],
    ) -> None:
        ...

    @abc.abstractmethod
    async def estimate_guild_prune_count(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        *,
        days: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        include_roles: typing.Union[
            undefined.UndefinedType, typing.Collection[typing.Union[guilds.Role, snowflake.UniqueObject]]
        ] = undefined.UNDEFINED,
    ) -> int:
        """Estimate the guild prune count.

        Parameters
        ----------
        guild : hikari.models.guilds.Guild or hikari.utilities.snowflake.UniqueObject
            The guild to estimate the guild prune count for. This may be a guild object,
            or the ID of an existing channel.
        days : hikari.utilities.undefined.UndefinedType or builtins.int
            If provided, number of days to count prune for.
        include_roles : hikari.utilities.undefined.UndefinedType or typing.Collection[hikari.models.guilds.Role or hikari.utilities.snowflake.UniqueObject]
            If provided, the role(s) to include. By default, this _endpoint will
            not count users with roles. Providing roles using this attribute
            will make members with the specified roles also get included into
            the count.

        Returns
        -------
        builtins.int
            The estimated guild prune count.

        Raises
        ------
        hikari.errors.BadRequest
            If any of the fields that are passed have an invalid value.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack the `KICK_MEMBERS` permission.
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def begin_guild_prune(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        *,
        days: typing.Union[undefined.UndefinedType, int] = undefined.UNDEFINED,
        compute_prune_count: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        include_roles: typing.Union[
            undefined.UndefinedType, typing.Collection[typing.Union[guilds.Role, snowflake.UniqueObject]]
        ] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> typing.Optional[int]:
        """Begin the guild prune.

        Parameters
        ----------
        guild : hikari.models.guilds.Guild or hikari.utilities.snowflake.UniqueObject
            The guild to begin the guild prune in. This may be a guild object,
            or the ID of an existing channel.
        days : hikari.utilities.undefined.UndefinedType or builtins.int
            If provided, number of days to count prune for.
        compute_prune_count: hikari.utilities.undefined.UndefinedType or builtins.bool
            If provided, whether to return the prune count. This is discouraged
            for large guilds.
        include_roles : hikari.utilities.undefined.UndefinedType or typing.Collection[hikari.models.guilds.Role or hikari.utilities.snowflake.UniqueObject]
            If provided, the role(s) to include. By default, this _endpoint will
            not count users with roles. Providing roles using this attribute
            will make members with the specified roles also get included into
            the count.
        reason : hikari.utilities.undefined.UndefinedType or builtins.str
            If provided, the reason that will be recorded in the audit logs.

        Returns
        -------
        builtins.int or builtins.None
            If `compute_prune_count` is not provided or `builtins.True`, the
            number of members pruned.

        Raises
        ------
        hikari.errors.BadRequest
            If any of the fields that are passed have an invalid value.
        hikari.errors.Unauthorized
            If you are unauthorized to make the request (invalid/missing token).
        hikari.errors.Forbidden
            If you lack the `KICK_MEMBERS` permission.
        hikari.errors.NotFound
            If the guild is not found.
        hikari.errors.ServerHTTPErrorResponse
            If an internal error occurs on Discord while handling the request.
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    async def fetch_guild_voice_regions(
        self, guild: typing.Union[guilds.Guild, snowflake.UniqueObject]
    ) -> typing.Sequence[voices.VoiceRegion]:
        ...

    @abc.abstractmethod
    async def fetch_guild_invites(
        self, guild: typing.Union[guilds.Guild, snowflake.UniqueObject]
    ) -> typing.Sequence[invites.InviteWithMetadata]:
        ...

    @abc.abstractmethod
    async def fetch_integrations(
        self, guild: typing.Union[guilds.Guild, snowflake.UniqueObject]
    ) -> typing.Sequence[guilds.Integration]:
        ...

    @abc.abstractmethod
    async def edit_integration(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        integration: typing.Union[guilds.Integration, snowflake.UniqueObject],
        *,
        expire_behaviour: typing.Union[
            undefined.UndefinedType, guilds.IntegrationExpireBehaviour
        ] = undefined.UNDEFINED,
        expire_grace_period: typing.Union[undefined.UndefinedType, date.TimeSpan] = undefined.UNDEFINED,
        enable_emojis: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def delete_integration(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        integration: typing.Union[guilds.Integration, snowflake.UniqueObject],
        *,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def sync_integration(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        integration: typing.Union[guilds.Integration, snowflake.UniqueObject],
    ) -> None:
        ...

    @abc.abstractmethod
    async def fetch_widget(self, guild: typing.Union[guilds.Guild, snowflake.UniqueObject]) -> guilds.GuildWidget:
        ...

    @abc.abstractmethod
    async def edit_widget(
        self,
        guild: typing.Union[guilds.Guild, snowflake.UniqueObject],
        *,
        channel: typing.Union[
            undefined.UndefinedType, channels.GuildChannel, snowflake.UniqueObject, None
        ] = undefined.UNDEFINED,
        enabled: typing.Union[undefined.UndefinedType, bool] = undefined.UNDEFINED,
        reason: typing.Union[undefined.UndefinedType, str] = undefined.UNDEFINED,
    ) -> guilds.GuildWidget:
        ...

    @abc.abstractmethod
    async def fetch_vanity_url(self, guild: typing.Union[guilds.Guild, snowflake.UniqueObject]) -> invites.VanityURL:
        ...
