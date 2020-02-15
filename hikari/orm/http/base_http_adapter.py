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

import abc
import typing

from hikari.internal_utilities import containers
from hikari.internal_utilities import unspecified

if typing.TYPE_CHECKING:
    from hikari.internal_utilities import storage
    from hikari.internal_utilities import type_hints
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


class BaseHTTPAdapter(abc.ABC):
    """
    Component that bridges the basic HTTP API exposed by :mod:`hikari.net.http_client` and
    wraps it in a unit of processing that can handle parsing API objects into Hikari ORM objects,
    and can handle keeping the state up to date as required.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    async def gateway_url(self) -> str:
        """
        Returns:
            A static URL to use to connect to the gateway with.

        Note:
            This call is cached after the first invocation. This does not require authorization
            to work.
        """

    @abc.abstractmethod
    async def fetch_gateway_bot(self) -> _gateway_bot.GatewayBot:
        """
        Returns:
            The gateway bot details to use as a recommendation for sharding and bot initialization.

        Note:
            Unlike :meth:`get_gateway`, this requires valid Bot authorization to work.
        """

    @abc.abstractmethod
    async def fetch_audit_log(
        self,
        guild: _guilds.GuildLikeT,
        *,
        user: type_hints.NotRequired[_users.BaseUserLikeT] = unspecified.UNSPECIFIED,
        action_type: type_hints.NotRequired[_audit_logs.AuditLogEventLikeT] = unspecified.UNSPECIFIED,
        limit: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
    ) -> _audit_logs.AuditLog:
        """
        Fetch the audit log for a given guild.
        
        Args:
            guild:
                The guild object or guild snowflake to retrieve the audit logs for.
            user:
                Filter the audit log entries by a specific user object or user snowflake. Leave unspecified to not
                perform filtering.
            action_type:
                Filter the audit log entries by a specific action type. Leave unspecified to not perform
                filtering.
            limit:
                The limit of the number of entries to return. Leave unspecified to return the maximum
                number allowed.
                
        Returns:
            An :class:`hikari.orm.models.audit_logs.AuditLog` object.

        Raises:
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the given permissions to view an audit log.
            hikari.net.errors.NotFoundHTTPError:
                If the guild does not exist.
        """

    @abc.abstractmethod
    async def fetch_channel(self, channel: _channels.ChannelLikeT) -> _channels.Channel:
        """
        Get a channel object from a given channel ID.

        Args:
            channel:
                The object or ID of the channel to look up.

        Returns:
            The :class:`hikari.orm.models.channels.Channel` object that has been found.

        Raises:
            hikari.net.errors.ForbiddenHTTPError:
                If the current token doesn't have access to the channel.
            hikari.net.errors.NotFoundHTTPError:
                If the channel does not exist.
        """

    @abc.abstractmethod
    async def update_channel(
        self,
        channel: _channels.ChannelLikeT,
        *,
        position: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        topic: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
        nsfw: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        rate_limit_per_user: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        bitrate: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        user_limit: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        permission_overwrites: type_hints.NotRequired[
            typing.Collection[_overwrites.Overwrite]
        ] = unspecified.UNSPECIFIED,
        parent_category: type_hints.NullableNotRequired[_channels.GuildCategoryLikeT] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> _channels.Channel:
        """
        Update one or more aspects of a given channel ID.

        Args:
            channel:
                The object or ID of the channel to update.
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
                The optional bitrate in bits per second allowable for the channel. This only applies to voice channels
                and must be between 8000 and 96000 or 128000 for VIP servers.
            user_limit:
                The optional max number of users to allow in a voice channel. This must be between 0 and 99 inclusive,
                where 0 implies no limit.
            permission_overwrites:
                An optional list of :class:`hikari.orm.models.overwrites.Overwrite` that are category specific to
                replace the existing overwrites with.
            parent_category:
                The optional object or ID of the parent category to set for the channel.
            reason:
                An optional audit log reason explaining why the change was made.

        Returns:
            The :class:`hikari.orm.models.channels.Channel` object that has been modified.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the channel does not exist.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the permission to make the change.
            hikari.net.errors.BadRequestHTTPError:
                If you provide incorrect options for the corresponding channel type (e.g. a `bitrate` for a text
                channel).
        """

    @abc.abstractmethod
    async def delete_channel(self, channel: _channels.ChannelLikeT) -> None:
        """
        Delete the given channel ID, or if it is a DM, close it.
        Args:
            channel:
                The object or ID of the channel to delete, or DM channel to close..

        Returns:
            Nothing, unlike what the API specifies. This is done to maintain consistency with other calls of a similar
            nature in this API wrapper.

        Warning:
            Deleted channels cannot be un-deleted. Deletion of DMs is able to be undone by reopening the DM.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the channel does not exist
            hikari.net.errors.ForbiddenHTTPError:
                If you do not have permission to delete the channel.
        """

    @abc.abstractmethod
    async def fetch_messages(
        self,
        channel: _channels.TextChannelLikeT,
        *,
        limit: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        after: type_hints.NotRequired[_messages.MessageLikeT] = unspecified.UNSPECIFIED,
        before: type_hints.NotRequired[_messages.MessageLikeT] = unspecified.UNSPECIFIED,
        around: type_hints.NotRequired[_messages.MessageLikeT] = unspecified.UNSPECIFIED,
        in_order: bool = False,
    ) -> typing.AsyncIterator[_messages.Message]:
        ...

    @abc.abstractmethod
    @typing.overload
    async def fetch_message(self, message: _messages.Message) -> _messages.Message:
        ...

    @abc.abstractmethod
    @typing.overload
    async def fetch_message(
        self, message: bases.SnowflakeLikeT, channel: _channels.TextChannelLikeT,
    ) -> _messages.Message:
        ...

    @abc.abstractmethod
    async def fetch_message(self, message, channel=unspecified.UNSPECIFIED):
        """
        Get the message with the given message ID from the channel with the given channel ID.

        Args:
            message:
                The object or ID of the message to retrieve.
            channel:
                The object or ID of the channel to look in, only required when `message` is an ID.

        Returns:
            A :class:`hikari.orm.models.messages.Message` object.

        Note:
            This requires the `READ_MESSAGE_HISTORY` permission to be set.

        Raises:
            hikari.net.errors.ForbiddenHTTPError:
                If you lack permission to see the message.
            hikari.net.errors.NotFoundHTTPError:
                If the message ID or channel ID is not found.
        """

    @abc.abstractmethod
    async def create_message(
        self,
        channel: _channels.TextChannelLikeT,
        *,
        content: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
        tts: bool = False,
        files: type_hints.NotRequired[typing.Collection[_media.AbstractFile]] = unspecified.UNSPECIFIED,
        embed: type_hints.NotRequired[_embeds.Embed] = unspecified.UNSPECIFIED,
    ) -> _messages.Message:
        """
        Create a message in the given channel or DM.

        Args:
            channel:
                The ID or object of the channel or dm channel to send to.
            content:
                The message content to send.
            tts:
                If specified and `True`, then the message will be sent as a TTS message.
            files:
                If specified, this should be a list of between 1 and 5 :class:`hikari.orm.models.media.AbstractFile`
                derived objects
            embed:
                if specified, this embed will be sent with the message.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the channel ID is not found.
            hikari.net.errors.BadRequestHTTPError:
                If the file is too large, the embed exceeds the defined limits, if the message content is specified and
                empty or greater than 2000 characters, or if neither of content, file or embed are specified.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack permissions to send to this channel.

        Returns:
            The created :class:`hikari.orm.models.messages.Message` object.
        """

    @abc.abstractmethod
    @typing.overload
    async def create_reaction(self, message: _messages.Message, emoji: _emojis.KnownEmojiLikeT) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def create_reaction(
        self, message: bases.SnowflakeLikeT, emoji: _emojis.KnownEmojiLikeT, channel: _channels.ChannelLikeT,
    ) -> None:
        ...

    @abc.abstractmethod
    async def create_reaction(
        self, message, emoji, channel=unspecified.UNSPECIFIED,
    ):
        """
        Add a reaction to the given message in the given channel or user DM.

        Args:
            message:
                The object or ID of the message to add the reaction in.
            emoji:
                The emoji to add. This can either be a series of unicode characters making up a valid Discord emoji,
                a :class:`hikari.orm.modes.emojis.KnownEmojiT` like object or in the form of name:id for a custom emoji.
            channel:
                The object or ID of the channel to add the reaction in, only required when `message` is an ID.

        Raises:
            hikari.net.errors.ForbiddenHTTPError:
                If this is the first reaction using this specific emoji on this message and you lack the `ADD_REACTIONS`
                permission. If you lack `READ_MESSAGE_HISTORY`, this may also raise this error.
            hikari.net.errors.NotFoundHTTPError:
                If the channel or message is not found, or if the emoji is not found.
            hikari.net.errors.BadRequestHTTPError:
                If the emoji is not valid, unknown, or formatted incorrectly
        """

    @abc.abstractmethod
    @typing.overload
    async def delete_reaction(
        self,
        reaction: _emojis.EmojiLikeT,
        user: _users.BaseUserLikeT,
        message: bases.SnowflakeLikeT,
        channel: _channels.ChannelLikeT,
    ) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def delete_reaction(
        self, reaction: _emojis.EmojiLikeT, user: _users.BaseUserLikeT, message: _messages.Message,
    ) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def delete_reaction(self, reaction: _reactions.Reaction, user: _users.BaseUserLikeT) -> None:
        ...

    @abc.abstractmethod
    async def delete_reaction(
        self, reaction, user, message=unspecified.UNSPECIFIED, channel=unspecified.UNSPECIFIED,
    ):
        """
        Remove a reaction made by a given user using a given emoji on a given message in a given channel or user DM.

        Args:
            reaction:
                The reaction object or emoji to delete. This can be a :class:`hikari.orm.models.reactions.Reaction`,
                a series of unicode characters making up a valid Discord emoji, or a custom emoji object or ID.
            user:
                The object or ID of the user who made the reaction that you wish to remove.
            channel:
                The object or ID of the channel to remove from, only required when `reaction` is emoji like,
                rather than a reaction object and `message` is an ID.
            message:
                The object or ID of the message to remove from, only required when `reaction` is emoji like,
                rather than a reaction object.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the channel or message or emoji or user is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_MESSAGES` permission, or are in DMs.
        """

    @abc.abstractmethod
    @typing.overload
    async def delete_all_reactions(self, message: bases.SnowflakeLikeT, channel: _channels.GuildChannelLikeT,) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def delete_all_reactions(self, message: _messages.Message) -> None:
        ...

    @abc.abstractmethod
    async def delete_all_reactions(
        self, message, channel=unspecified.UNSPECIFIED,
    ):
        """
        Deletes all reactions from a given message in a given channel.

        Args:
            message:
                The object or ID of the message to remove reactions from.
            channel:
                The object or ID of the channel to remove reactions within, only required when `message` is an ID.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the channel_id or message_id was not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_MESSAGES` permission.
        """

    @abc.abstractmethod
    @typing.overload
    async def fetch_reactors(
        self,
        reaction: _reactions.Reaction,
        *,
        after: type_hints.NotRequired[_users.BaseUserLikeT] = unspecified.UNSPECIFIED,
        limit: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
    ) -> typing.AsyncIterator[_users.BaseUser]:
        ...

    @abc.abstractmethod
    @typing.overload
    async def fetch_reactors(
        self,
        reaction: _emojis.EmojiLikeT,
        message: _messages.Message,
        *,
        after: type_hints.NotRequired[_users.BaseUserLikeT] = unspecified.UNSPECIFIED,
        limit: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
    ) -> typing.AsyncIterator[_users.BaseUser]:
        ...

    @abc.abstractmethod
    @typing.overload
    async def fetch_reactors(
        self,
        reaction: _emojis.EmojiLikeT,
        message: bases.SnowflakeLikeT,
        channel: _channels.ChannelLikeT,
        *,
        after: type_hints.NotRequired[_users.BaseUserLikeT] = unspecified.UNSPECIFIED,
        limit: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
    ) -> typing.AsyncIterator[_users.BaseUser]:
        ...

    @abc.abstractmethod
    async def fetch_reactors(
        self,
        reaction,
        message=unspecified.UNSPECIFIED,
        channel=unspecified.UNSPECIFIED,
        *,
        after=unspecified.UNSPECIFIED,
        limit=unspecified.UNSPECIFIED,
    ):
        ...

    @abc.abstractmethod
    @typing.overload
    async def update_message(
        self,
        message: bases.SnowflakeLikeT,
        channel: _channels.ChannelLikeT,
        *,
        content: type_hints.NullableNotRequired[str] = unspecified.UNSPECIFIED,
        embed: type_hints.NullableNotRequired[_embeds.Embed] = unspecified.UNSPECIFIED,
        flags: type_hints.NotRequired[_messages.MessageFlagLikeT] = unspecified.UNSPECIFIED,
    ) -> _messages.Message:
        ...

    @abc.abstractmethod
    @typing.overload
    async def update_message(
        self,
        message: _messages.Message,
        *,
        content: type_hints.NullableNotRequired[str] = unspecified.UNSPECIFIED,
        embed: type_hints.NullableNotRequired[_embeds.Embed] = unspecified.UNSPECIFIED,
        flags: type_hints.NotRequired[_messages.MessageFlagLikeT] = unspecified.UNSPECIFIED,
    ) -> _messages.Message:
        ...

    @abc.abstractmethod
    async def update_message(
        self,
        message,
        channel=unspecified.UNSPECIFIED,
        *,
        content=unspecified.UNSPECIFIED,
        embed=unspecified.UNSPECIFIED,
        flags=unspecified.UNSPECIFIED,
    ):
        """
        Update the given message.

        Args:
            message:
                The object or ID of the message to edit.
            channel:
                The object of ID of the channel to operate in, only required when `message` is an ID.
            content:
                Optional string content to replace with in the message. If unspecified, it is not changed.
            embed:
                Optional embed object to replace with in the message. If unspecified, it is not changed.
            flags:
                Optional integer to replace the message's current flags. If unspecified, it is not changed.

        Returns:
            The new :class:`hikari.orm.messages.Message` object.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the channel_id or message_id is not found.
            hikari.net.errors.BadRequestHTTPError:
                If the embed exceeds any of the embed limits if specified, or the content is specified and consists
                only of whitespace, is empty, or is more than 2,000 characters in length.
            hikari.net.errors.ForbiddenHTTPError:
                If you try to edit content or embed on a message you did not author or try to edit the flags
                on a message you did not author without the `MANAGE_MESSAGES` permission.
        """

    @abc.abstractmethod
    async def delete_messages(
        self,
        first_message: _messages.MessageLikeT,
        *additional_messages: _messages.MessageLikeT,
        channel: type_hints.NotRequired[_channels.ChannelLikeT] = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Delete between 1 and 100 messages in a single request.

        Args:
            first_message:
                The object or ID of the first message to delete (will be used to decide the channel if is an object).
            *additional_messages:
                Up to 99 additional unique message objects or IDs to delete in the same channel.
            channel:
                The object or ID of the channel to delete messages from, only required when `first_message` is an ID.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the channel is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_MESSAGES` permission in the channel.
            hikari.net.errors.BadRequestHTTPError:
                If any of the messages passed are older than 2 weeks in age.
            ValueError:
                If more than 100 messages are passed.

        Notes:
            This can only be used on guild text channels.

            Any message IDs that do not exist or are invalid add towards the total 100 max messages to remove.

            This can only delete messages that are newer than 2 weeks in age. If any of the messages are older than 2
            weeks then this call will fail.
        """

    @abc.abstractmethod
    async def update_channel_overwrite(
        self,
        channel: _channels.GuildChannelLikeT,
        overwrite: _overwrites.OverwriteLikeT,
        *,
        allow: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        deny: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        overwrite_type: type_hints.NotRequired[_overwrites.OverwriteEntityTypeLikeT] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Edit permissions for a given channel.

        Args:
            channel:
                The channel object or ID to edit permissions for.
            overwrite:
                The overwrite object or ID to edit.
            allow:
                The bitwise value of all permissions to set to be allowed.
            deny:
                The bitwise value of all permissions to set to be denied.
            overwrite_type:
                The type of entity this overwrite targets (member or role).
            reason:
                An optional audit log reason explaining why the change was made.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the target channel or overwrite doesn't exist.
            hikari.net.errors.ForbiddenHTTPError:
                If the current token lacks permission to do this.
        """

    @abc.abstractmethod
    async def fetch_invites_for_channel(self, channel: _channels.GuildChannelLikeT) -> typing.Sequence[_invites.Invite]:
        """
        Get invites for a given channel.

        Args:
            channel:
                The channel object or ID to get invites for.

        Returns:
            A sequence of :class:`hikari.orm.models.invites.Invite` objects.

        Raises:
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_CHANNELS` permission.
            hikari.net.errors.NotFoundHTTPError:
                If the channel does not exist.
        """

    @abc.abstractmethod
    async def create_invite_for_channel(
        self,
        channel: _channels.GuildChannelLikeT,
        *,
        max_age: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        max_uses: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        temporary: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        unique: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        target_user: type_hints.NotRequired[_users.BaseUserLikeT] = unspecified.UNSPECIFIED,
        target_user_type: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> _invites.Invite:
        """
        Create a new invite for the given channel.

        Args:
            channel:
                The object or ID of the channel to create the invite for.
            max_age:
                The max age of the invite in seconds, defaults to 86400 (24 hours). Set to 0 to never expire.
            max_uses:
                The max number of uses this invite can have, or 0 for unlimited (as per the default).
            temporary:
                If `True`, grant temporary membership, meaning the user is kicked when their session ends unless they
                are given a role. Defaults to `False`.
            unique:
                If `True`, never reuse a similar invite. Defaults to `False`.
            reason:
                An optional audit log reason explaining why the change was made.

        Returns:
            An :class:`hikari.orm.models.invites.Invite` object.

        Raises:
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `CREATE_INSTANT_MESSAGES` permission.
            hikari.net.errors.NotFoundHTTPError:
                If the channel does not exist.
            hikari.net.errors.BadRequestHTTPError:
                If the arguments provided are not valid (e.g. negative age, etc).
        """

    @abc.abstractmethod
    async def delete_channel_overwrite(
        self, channel: _channels.GuildChannelLikeT, overwrite: _overwrites.OverwriteLikeT,
    ) -> None:
        """
        Delete a channel permission overwrite for a user or a role in a channel.

        Args:
            channel:
                The object or ID of the channel to delete from.
            overwrite:
                The object or ID of the overwrite to remove.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the overwrite or channel ID does not exist.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_ROLES` permission for that channel.
        """

    @abc.abstractmethod
    async def trigger_typing(self, channel: _channels.TextChannelLikeT) -> None:
        """
        Trigger the account to appear to be typing for the next 10 seconds in the given channel.

        Args:
            channel:
                The object or ID of the channel to appear to be typing in.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the channel is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you are not in the guild the channel belongs to.
        """

    @abc.abstractmethod
    async def fetch_pins(self, channel: _channels.TextChannelLikeT) -> typing.Sequence[_messages.Message]:
        """
        Get pinned messages for a given channel.

        Args:
            channel:
                The object or ID of the channel to get messages for.

        Returns:
            A sequence of :class:`hikari.orm.models.messages.Message`.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If no channel matching the ID exists.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack permission to do this.
        """

    @abc.abstractmethod
    @typing.overload
    async def pin_message(self, message: bases.SnowflakeLikeT, channel: _channels.TextChannelLikeT) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def pin_message(self, message: _messages.Message) -> None:
        ...

    @abc.abstractmethod
    async def pin_message(self, message, channel=unspecified.UNSPECIFIED):
        """
        Add a pinned message to the channel.

        Args:
            message:
                The object or ID of the message in the channel to pin.
            channel:
                The object or ID of the channel to add a pin to, only required when `message` is an ID.

        Raises:
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_MESSAGES` permission.
            hikari.net.errors.NotFoundHTTPError:
                If the message or channel does not exist.
        """

    @abc.abstractmethod
    @typing.overload
    async def unpin_message(self, message: bases.SnowflakeLikeT, channel: _channels.TextChannelLikeT) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def unpin_message(self, message: _messages.Message) -> None:
        ...

    @abc.abstractmethod
    async def unpin_message(self, message, channel=unspecified.UNSPECIFIED):
        """
        Remove a pinned message from the channel. This will only unpin the message. It will not delete it.

        Args:
            message:
                The object or ID of the message in the channel to unpin.
            channel:
                The object or ID of the channel to remove a pin from, only required when `message` is an ID.

        Raises:
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_MESSAGES` permission.
            hikari.net.errors.NotFoundHTTPError:
                If the message or channel does not exist.
        """

    @abc.abstractmethod
    @typing.overload
    async def fetch_guild_emoji(self, emoji: bases.SnowflakeLikeT, guild: _guilds.GuildLikeT) -> _emojis.GuildEmoji:
        ...

    @abc.abstractmethod
    @typing.overload
    async def fetch_guild_emoji(self, emoji: _emojis.GuildEmoji) -> _emojis.GuildEmoji:
        ...

    @abc.abstractmethod
    async def fetch_guild_emoji(self, emoji, guild=unspecified.UNSPECIFIED):
        """
        Gets an emoji from a given guild and emoji IDs

        Args:
            emoji:
                The object or ID of the emoji to get.
            guild:
                The object or ID of the guild to get the emoji from, only required when `emoji` is an ID.

        Returns:
            A :class:`hikari.orm.models.emojis.GuildEmoji` object.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild or the emoji aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you aren't a member of said guild.
        """

    @abc.abstractmethod
    async def fetch_guild_emojis(self, guild: _guilds.GuildLikeT) -> typing.Collection[_emojis.GuildEmoji]:
        """
        Gets emojis for a given guild ID.

        Args:
            guild:
                The ID or object of the guild to get the emojis for.

        Returns:
            A list of :class:`hikari.orm.models.emojis.GuildEmoji` objects.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you aren't a member of said guild.
        """

    @abc.abstractmethod
    async def create_guild_emoji(
        self,
        guild: _guilds.GuildLikeT,
        name: str,
        image_data: storage.FileLikeT,
        *,
        roles: typing.Collection[_roles.RoleLikeT] = containers.EMPTY_COLLECTION,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> _emojis.GuildEmoji:
        """
         Creates a new emoji for a given guild.

         Args:
             guild:
                 The object or ID of the guild to create the emoji in.
             name:
                 The new emoji's name.
             image_data:
                 The 128x128 image a file like object.
             roles:
                 A list of role objects or IDs for which the emoji will be whitelisted.
                 If empty, all roles are whitelisted.
             reason:
                 An optional audit log reason explaining why the change was made.

         Returns:
             The newly created emoji object.

         Raises:
             hikari.net.errors.NotFoundHTTPError:
                 If the guild is not found.
             hikari.net.errors.ForbiddenHTTPError:
                 If you either lack the `MANAGE_EMOJIS` permission or aren't a member of said guild.
             hikari.net.errors.BadRequestHTTPError:
                 If you attempt to upload an image larger than 256kb, an empty image or an invalid image format.
         """

    @abc.abstractmethod
    @typing.overload
    async def update_guild_emoji(
        self,
        emoji: bases.SnowflakeLikeT,
        guild: _guilds.GuildLikeT,
        *,
        name: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
        roles: type_hints.NotRequired[typing.Collection[_roles.RoleLikeT]] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def update_guild_emoji(
        self,
        emoji: _emojis.GuildEmoji,
        *,
        name: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
        roles: type_hints.NotRequired[typing.Collection[_roles.RoleLikeT]] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def update_guild_emoji(
        self,
        emoji,
        guild=unspecified.UNSPECIFIED,
        *,
        name=unspecified.UNSPECIFIED,
        roles=unspecified.UNSPECIFIED,
        reason=unspecified.UNSPECIFIED,
    ):
        """
        Edits an emoji of a given guild

        Args:
            emoji:
                The object or ID of the edited emoji.
            guild:
                The object or ID of the guild to which the edited emoji belongs to, only required when `emoji` is an ID.
            name:
                The new emoji name string. Keep unspecified to keep the name the same.
            roles:
                A list of objects or IDs for the new whitelisted roles.
                Set to an empty list to whitelist all roles.
                Keep unspecified to leave the same roles already set.
            reason:
                An optional audit log reason explaining why the change was made.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild or the emoji aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you either lack the `MANAGE_EMOJIS` permission or are not a member of the given guild.
        """

    @abc.abstractmethod
    @typing.overload
    async def delete_guild_emoji(self, emoji: bases.SnowflakeLikeT, guild: _guilds.GuildLikeT) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def delete_guild_emoji(self, emoji: _emojis.GuildEmoji) -> None:
        ...

    @abc.abstractmethod
    async def delete_guild_emoji(self, emoji, guild=unspecified.UNSPECIFIED):
        """
        Deletes an emoji from a given guild

        Args:
            emoji:
                The object or ID of the emoji to be deleted.
            guild:
                The ID of the guild to delete the emoji from, only required when `emoji` is an ID.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild or the emoji aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you either lack the `MANAGE_EMOJIS` permission or aren't a member of said guild.
        """

    @abc.abstractmethod
    async def create_guild(
        self,
        name: str,
        *,
        region: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
        icon_data: type_hints.NotRequired[storage.FileLikeT] = unspecified.UNSPECIFIED,
        verification_level: type_hints.NotRequired[_guilds.VerificationLevelLikeT] = unspecified.UNSPECIFIED,
        default_message_notifications: type_hints.NotRequired[
            _guilds.DefaultMessageNotificationsLevelLikeT
        ] = unspecified.UNSPECIFIED,
        explicit_content_filter: type_hints.NotRequired[
            _guilds.ExplicitContentFilterLevelLikeT
        ] = unspecified.UNSPECIFIED,
        roles: type_hints.NotRequired[typing.Collection[_roles.Role]] = unspecified.UNSPECIFIED,
        channels: type_hints.NotRequired[typing.Collection[_channels.GuildChannel]] = unspecified.UNSPECIFIED,
    ) -> _guilds.Guild:
        """
        Creates a new guild. Can only be used by bots in less than 10 guilds.

        Args:
            name:
                The name string for the new guild (2-100 characters).
            region:
                The voice region ID for new guild. You can use `list_voice_regions` to see which region IDs are
                available.
            icon_data:
                The guild icon image as a file like object.
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
            The newly created :class:`hikari.orm.models.guilds.Guild` object.

        Raises:
            hikari.net.errors.ForbiddenHTTPError:
                If your bot is on 10 or more guilds.
            hikari.net.errors.BadRequestHTTPError:
                If you provide unsupported fields like `parent_id` in channel objects.
        """

    @abc.abstractmethod
    async def fetch_guild(self, guild: _guilds.GuildLikeT) -> _guilds.Guild:
        """
        Gets a given guild's object.

        Args:
            guild:
                The object or ID of the guild to get.

        Returns:
            The requested :class:`hikari.orm.models.guilds.Guild` object.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If the current token doesn't have access to the guild.
        """

    @abc.abstractmethod
    async def update_guild(
        self,
        guild: _guilds.GuildLikeT,
        *,
        name: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
        region: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
        verification_level: type_hints.NotRequired[_guilds.VerificationLevelLikeT] = unspecified.UNSPECIFIED,
        default_message_notifications: type_hints.NotRequired[
            _guilds.DefaultMessageNotificationsLevelLikeT
        ] = unspecified.UNSPECIFIED,
        explicit_content_filter: type_hints.NotRequired[
            _guilds.ExplicitContentFilterLevelLikeT
        ] = unspecified.UNSPECIFIED,
        afk_channel: type_hints.NotRequired[_channels.GuildVoiceChannelLikeT] = unspecified.UNSPECIFIED,
        afk_timeout: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        icon_data: type_hints.NotRequired[storage.FileLikeT] = unspecified.UNSPECIFIED,
        #: TODO: While this will always be a member of the guild for it to work, do I want to allow any user here too?
        owner: type_hints.NotRequired[_members.MemberLikeT] = unspecified.UNSPECIFIED,
        splash_data: type_hints.NotRequired[storage.FileLikeT] = unspecified.UNSPECIFIED,
        #: TODO: Can this be an announcement (news) channel also?
        system_channel: type_hints.NotRequired[_channels.GuildTextChannelLikeT] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Edits a given guild.

        Args:
            guild:
                The object or ID of the guild to be edited.
            name:
                The new name string.
            region:
                The voice region ID for new guild. You can use `list_voice_regions` to see which region IDs are
                available.
            verification_level:
                A :class:`hikari.orm.models.guilds.VerificationLevel` or :class:`int` equivalent.
            default_message_notifications:
                A :class:`hikari.orm.models.guilds.DefaultMessageNotificationsLevel` or :class:`int` equivalent.
            explicit_content_filter:
                A :class:`hikari.orm.models.guilds.ExplicitContentFilterLevel` or :class:`int` equivalent.
            afk_channel:
                The ID or channel object for the AFK voice channel.
            afk_timeout:
                The AFK timeout period in seconds
            icon_data:
                The guild icon image as a file like object.
            owner:
                The ID or member object of the new guild owner.
            splash_data:
                The new splash image as a file like object.
            system_channel:
                The ID or channel object of the new system channel.
            reason:
                Optional reason to apply to the audit log.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """

    @abc.abstractmethod
    async def delete_guild(self, guild: _guilds.GuildLikeT) -> None:
        """
        Permanently deletes the given guild. You must be owner.

        Args:
            guild:
                The object or ID of the guild to be deleted.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you're not the guild owner.
        """

    @abc.abstractmethod
    async def fetch_guild_channels(self, guild: _guilds.GuildLikeT) -> typing.Sequence[_channels.GuildChannel]:
        # Sequence as it should be in channel positional order...
        """
        Gets all the channels for a given guild.

        Args:
            guild:
                The object or ID of the guild to get the channels from.

        Returns:
            A list of :class:`hikari.orm.models.channels.GuildChannel` objects.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you're not in the guild.
        """

    @abc.abstractmethod
    async def create_guild_channel(  # lgtm [py/similar-function]
        self,
        guild: _guilds.GuildLikeT,
        name: str,
        channel_type: _channels.ChannelTypeLikeT,
        *,
        topic: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
        bitrate: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        user_limit: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        rate_limit_per_user: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        position: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        permission_overwrites: type_hints.NotRequired[
            typing.Collection[_overwrites.Overwrite]
        ] = unspecified.UNSPECIFIED,
        parent_category: type_hints.NullableNotRequired[_channels.GuildCategoryLikeT] = unspecified.UNSPECIFIED,
        nsfw: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> _channels.GuildChannel:
        """
        Creates a channel in a given guild.

        Args:
            guild:
                The object or ID of the guild to create the channel in.
            name:
                The new channel name string (2-100 characters).
            channel_type:
                A :class:`hikari.orm.models.channels.ChannelType` or :class:`int` equivalent.
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
                A list of :class:`hikari.orm.models.overwrites.Overwrite` objects to apply to the channel.
            parent_category:
                The object or ID of the parent category.
            nsfw:
                Marks the channel as NSFW if `True`.
            reason:
                The optional reason for the operation being performed.

        Returns:
            The newly created channel object.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_CHANNEL` permission or are not in the target guild or are not in the guild.
            hikari.net.errors.BadRequestHTTPError:
                If you omit the `name` argument.
        """

    @abc.abstractmethod
    @typing.overload
    async def reposition_guild_channels(
        self,
        first_channel: typing.Tuple[int, bases.SnowflakeLikeT],
        *additional_channels: typing.Tuple[int, _channels.GuildChannelLikeT],
        guild: _guilds.GuildLikeT,
    ) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def reposition_guild_channels(
        self,
        first_channel: typing.Tuple[int, _channels.GuildChannel],
        *additional_channels: typing.Tuple[int, _channels.GuildChannelLikeT],
    ) -> None:
        ...

    @abc.abstractmethod
    async def reposition_guild_channels(
        self, first_channel, *additional_channels, guild=unspecified.UNSPECIFIED,
    ):
        """
        Edits the position of one or more given channels.

        Args:
            first_channel:
                The first channel to change the position of. As a :class:`tuple` of :class:`int` and
                :class:`hikari.orm.models.channels.GuildChannel` or :class:`int`
            additional_channels:
                Optional additional channels to change the position of. Each as a :class:`tuple` of :class:`int`
                and :class:`hikari.orm.models.channels.GuildChannel` or :class:`int`
            guild:
                The object or ID of the guild in which to edit the channels, only required when `first_channel` is a 
                tuple of int, int (rather than int, GuildChannel).

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild or any of the channels aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you either lack the `MANAGE_CHANNELS` permission or are not a member of said guild or are not in
                The guild.
            hikari.net.errors.BadRequestHTTPError:
                If you provide anything other than the `id` and `position` fields for the channels.
        """

    @abc.abstractmethod
    @typing.overload
    async def fetch_member(self, user: _users.BaseUserLikeT, guild: _guilds.GuildLikeT) -> _members.Member:
        ...

    @abc.abstractmethod
    @typing.overload
    async def fetch_member(self, user: _members.Member) -> _members.Member:
        ...

    @abc.abstractmethod
    async def fetch_member(self, user, guild=unspecified.UNSPECIFIED):
        """
        Gets a given guild member.

        Args:
            user:
                The object or ID of the member to get.
            guild:
                The object or ID of the guild to get the member from, only required when `user` is an ID or user object
                rather than a member object.

        Returns:
            The requested :class:`hikari.orm.models.members.Member` object.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild or the member aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you don't have access to the target guild.
        """

    @abc.abstractmethod
    async def fetch_members(
        self, guild: _guilds.GuildLikeT, *, limit: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
    ) -> typing.AsyncIterator[_members.Member]:
        ...

    @abc.abstractmethod
    @typing.overload
    async def update_member(
        self,
        member: bases.SnowflakeLikeT,
        guild: _guilds.GuildLikeT,
        *,
        nick: type_hints.NullableNotRequired[str] = unspecified.UNSPECIFIED,
        roles: type_hints.NotRequired[typing.Collection[_roles.RoleLikeT]] = unspecified.UNSPECIFIED,
        mute: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        deaf: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        current_voice_channel: type_hints.NullableNotRequired[
            _channels.GuildVoiceChannelLikeT
        ] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def update_member(
        self,
        member: _members.Member,
        *,
        nick: type_hints.NullableNotRequired[str] = unspecified.UNSPECIFIED,
        roles: type_hints.NotRequired[typing.Collection[_roles.RoleLikeT]] = unspecified.UNSPECIFIED,
        mute: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        deaf: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        current_voice_channel: type_hints.NullableNotRequired[
            _channels.GuildVoiceChannelLikeT
        ] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def update_member(
        self,
        member,
        guild=unspecified.UNSPECIFIED,
        *,
        nick=unspecified.UNSPECIFIED,
        roles=unspecified.UNSPECIFIED,
        mute=unspecified.UNSPECIFIED,
        deaf=unspecified.UNSPECIFIED,
        current_voice_channel=unspecified.UNSPECIFIED,
        reason=unspecified.UNSPECIFIED,
    ):
        """
        Edits a member of a given guild.

        Args:
            member:
                The object or ID of the member to edit.
            guild:
                The object or ID of the guild to edit the member from, only required when `member` is an ID
                or user object.
            nick:
                The new nickname string. Setting it to None explicitly will clear the nickname.
            roles:
                A list of role objects or IDs the member should have.
            mute:
                Whether the user should be muted in the voice channel or not, if applicable.
            deaf:
                Whether the user should be deafen in the voice channel or not, if applicable.
            current_voice_channel:
                The object or ID of the channel to move the member to, if applicable. Pass None to disconnect the user.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.
        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild, user, channel or any of the roles aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack any of the applicable permissions
                (`MANAGE_NICKNAMES`, `MANAGE_ROLES`, `MUTE_MEMBERS`, `DEAFEN_MEMBERS` or `MOVE_MEMBERS`).
                Note that to move a member you must also have permission to connect to the end channel.
                This will also be raised if you're not in the guild.
            hikari.net.errors.BadRequestHTTPError:
                If you pass `mute`, `deaf` or `current_voice_channel` while the member is not connected
                to a voice channel.
        """

    async def update_my_nickname(
        self,
        nick: type_hints.Nullable[str],
        guild: _guilds.GuildLikeT,
        *,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Edits the current user's nickname for a given guild.

        Args:
            guild:
                The object or ID of the guild you want to change the nick on.
            nick:
                The new nick string. Setting this to `None` clears the nickname.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `CHANGE_NICKNAME` permission or are not in the guild.
            hikari.net.errors.BadRequestHTTPError:
                If you provide a disallowed nickname, one that is too long, or one that is empty.
        """

    @abc.abstractmethod
    @typing.overload
    async def add_role_to_member(
        self,
        role: _roles.RoleLikeT,
        member: bases.SnowflakeLikeT,
        guild: _guilds.GuildLikeT,
        *,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def add_role_to_member(
        self,
        role: _roles.RoleLikeT,
        member: _members.Member,
        *,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def add_role_to_member(
        self, role, member, guild=unspecified.UNSPECIFIED, *, reason=unspecified.UNSPECIFIED,
    ):
        """
        Adds a role to a given member.

        Args:
            member:
                The object or ID of the member you want to add the role to.
            role:
                The object or ID of the role you want to add.
            guild:
                The object or ID of the guild the member belongs to, only required when `member` is an ID
                or user object.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild, member or role aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_ROLES` permission or are not in the guild.
        """

    @abc.abstractmethod
    @typing.overload
    async def remove_role_from_member(
        self,
        role: _roles.RoleLikeT,
        member: bases.SnowflakeLikeT,
        guild: _guilds.GuildLikeT,
        *,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def remove_role_from_member(
        self,
        role: _roles.RoleLikeT,
        member: _members.Member,
        *,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def remove_role_from_member(
        self, role, member, guild=unspecified.UNSPECIFIED, *, reason=unspecified.UNSPECIFIED,
    ):
        """
        Removed a role from a given member.

        Args:
            member:
                The object or ID of the member you want to remove the role from.
            role:
                The object or ID of the role you want to remove.
            guild:
                The object or ID of the guild the member belongs to, only required when `member` is an ID
                or user object.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild, member or role aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_ROLES` permission or are not in the guild.
        """

    @abc.abstractmethod
    @typing.overload
    async def kick_member(
        self,
        member: bases.SnowflakeLikeT,
        guild: _guilds.GuildLikeT,
        *,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def kick_member(
        self, member: _members.Member, *, reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def kick_member(
        self, member, guild=unspecified.UNSPECIFIED, *, reason=unspecified.UNSPECIFIED,
    ):
        """
        Kicks a user from a given guild.

        Args:
            member:
                The object or ID of the member you want to kick.
            guild:
                The object or ID of the guild the member belongs to, only required when `member` is an ID
                or user object.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild or member aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `KICK_MEMBERS` permission or are not in the guild.
        """

    @abc.abstractmethod
    async def fetch_ban(self, guild: _guilds.GuildLikeT, user: _users.BaseUserLikeT) -> _guilds.Ban:
        """
        Gets a ban from a given guild.

        Args:
            guild:
                The object or ID of the guild you want to get the ban from.
            user:
                The object or ID of the user to get the ban information for.

        Returns:
            A :class:`hikari.orm.models.guilds.Ban` object for the requested user.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild or the user aren't found, or if the user is not banned.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `BAN_MEMBERS` permission or are not in the guild.
        """

    @abc.abstractmethod
    async def fetch_bans(self, guild: _guilds.GuildLikeT) -> typing.Collection[_guilds.Ban]:
        """
        Gets the bans for a given guild.

        Args:
            guild:
                The object or ID of the guild you want to get the bans from.

        Returns:
            A list of :class:`hikari.orm.models.guilds.Ban` objects.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `BAN_MEMBERS` permission or are not in the guild.
        """

    @abc.abstractmethod
    @typing.overload
    async def ban_member(
        self,
        member: bases.SnowflakeLikeT,
        guild: _guilds.GuildLikeT,
        *,
        delete_message_days: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def ban_member(
        self,
        member: _members.Member,
        *,
        delete_message_days: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def ban_member(
        self,
        member,
        guild=unspecified.UNSPECIFIED,
        *,
        delete_message_days=unspecified.UNSPECIFIED,
        reason=unspecified.UNSPECIFIED,
    ):
        """
        Bans a user from a given guild.

        Args:
            member:
                The object or ID of the member you want to ban.
            guild:
                The object or ID of the guild the member belongs to, only required when `member` is an ID
                or user object.
            delete_message_days:
                How many days of messages from the user should be removed. Default is to not delete anything.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild or member aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `BAN_MEMBERS` permission or are not in the guild.
        """

    @abc.abstractmethod
    async def unban_member(
        self,
        guild: _guilds.GuildLikeT,
        user: _users.BaseUserLikeT,
        *,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Un-bans a user from a given guild.

        Args:
            guild:
                The object or ID of the guild to un-ban the user from.
            user:
                The object or ID of the user you want to un-ban.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild or member aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `BAN_MEMBERS` permission or are not a in the guild.
        """

    @abc.abstractmethod
    async def fetch_roles(self, guild: _guilds.GuildLikeT) -> typing.Sequence[_roles.Role]:
        """
        Gets the roles for a given guild.

        Args:
            guild:
                The object or ID of the guild you want to get the roles from.

        Returns:
            A list of :class:`hikari.orm.models.roles.Role` objects.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you're not in the guild.
        """

    @abc.abstractmethod
    async def create_role(  # lgtm [py/similar-function]
        self,
        guild: _guilds.GuildLikeT,
        *,
        name: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
        permissions: type_hints.NotRequired[_permissions.PermissionLikeT] = unspecified.UNSPECIFIED,
        color: type_hints.NotRequired[_colors.ColorCompatibleT] = unspecified.UNSPECIFIED,
        hoist: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        mentionable: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> _roles.Role:
        """
        Creates a new role for a given guild.

        Args:
            guild:
                The object or ID of the guild you want to create the role on.
            name:
                The new role name string.
            permissions:
                A :class:`hikari.orm.models.permissions.Permission` or :class:`int` equivalent for the role.
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
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_ROLES` permission or you're not in the guild.
            hikari.net.errors.BadRequestHTTPError:
                If you provide invalid values for the role attributes.
        """

    @abc.abstractmethod
    @typing.overload
    async def reposition_roles(
        self, first_role: typing.Tuple[int, _roles.Role], *additional_roles: typing.Tuple[int, _roles.RoleLikeT],
    ) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def reposition_roles(
        self,
        first_role: typing.Tuple[int, bases.SnowflakeLikeT],
        *additional_roles: typing.Tuple[int, _roles.RoleLikeT],
        guild: _guilds.GuildLikeT,
    ) -> None:
        ...

    @abc.abstractmethod
    async def reposition_roles(
        self, first_role, *additional_roles, guild=unspecified.UNSPECIFIED,
    ):
        """
        Edits the position of two or more roles in a given guild.

        Args:
            first_role:
                The first role to move as a :class:`tuple` of :class:`int` and
                :class:`hikari.orm.models.roles.Role` or :class:`int`
            additional_roles:
                Optional extra roles to move. Each as a :class:`tuple` of :class:`int` and
                :class:`hikari.orm.models.roles.Role` or :class:`int`
            guild:
                The object or ID of the guild the roles belong to, only required when `first_role` is an ID or
                partial role object.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild or any of the roles aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_ROLES` permission or you're not in the guild.
            hikari.net.errors.BadRequestHTTPError:
                If you provide invalid values for the `position` fields.
        """

    @abc.abstractmethod
    @typing.overload
    async def update_role(
        self,
        role: _roles.PartialRoleLikeT,
        guild: _guilds.GuildLikeT,
        *,
        name: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
        permissions: type_hints.NotRequired[_permissions.PermissionLikeT] = unspecified.UNSPECIFIED,
        color: type_hints.NotRequired[_colors.ColorCompatibleT] = unspecified.UNSPECIFIED,
        hoist: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        mentionable: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def update_role(
        self,
        role: _roles.Role,
        *,
        name: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
        permissions: type_hints.NotRequired[_permissions.PermissionLikeT] = unspecified.UNSPECIFIED,
        color: type_hints.NotRequired[_colors.ColorCompatibleT] = unspecified.UNSPECIFIED,
        hoist: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        mentionable: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        ...

    @abc.abstractmethod
    async def update_role(
        self,
        role: _roles.PartialRoleLikeT,
        guild=unspecified.UNSPECIFIED,
        *,
        name=unspecified.UNSPECIFIED,
        permissions=unspecified.UNSPECIFIED,
        color=unspecified.UNSPECIFIED,
        hoist=unspecified.UNSPECIFIED,
        mentionable=unspecified.UNSPECIFIED,
        reason=unspecified.UNSPECIFIED,
    ):
        """
        Edits a role in a given guild.

        Args:

            role:
                The object or ID of the role you want to edit.
            guild:
                The object or ID of the guild the role belong to, only required when `role` is an ID or
                partial role object.
            name:
                THe new role's name string.
            permissions:
                The new :class:`hikari.orm.models.permissions.Permission` or :class:`int` equivalent for the role.
            color:
                The new color for the new role.
            hoist:
                Whether the role should hoist or not.
            mentionable:
                Whether the role should be mentionable or not.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild or role aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_ROLES` permission or you're not in the guild.
            hikari.net.errors.BadRequestHTTPError:
                If you provide invalid values for the role attributes.
        """

    @abc.abstractmethod
    @typing.overload
    async def delete_role(self, role: _roles.PartialRoleLikeT, guild: _guilds.GuildLikeT) -> None:
        ...

    @abc.abstractmethod
    @typing.overload
    async def delete_role(self, role: _roles.Role) -> None:
        ...

    @abc.abstractmethod
    async def delete_role(self, role, guild=unspecified.UNSPECIFIED):
        """
         Deletes a role from a given guild.

         Args:
             role:
                 The object or ID of the role you want to delete.
             guild:
                 The object or ID of the guild you want to remove the role from, only required when role is an ID or
                 partial role object.

         Raises:
             hikari.net.errors.NotFoundHTTPError:
                 If either the guild or the role aren't found.
             hikari.net.errors.ForbiddenHTTPError:
                 If you lack the `MANAGE_ROLES` permission or are not in the guild.
         """

    @abc.abstractmethod
    async def estimate_guild_prune_count(self, guild: _guilds.GuildLikeT, days: int) -> int:
        """
         Gets the estimated prune count for a given guild.

         Args:
             guild:
                 The object or ID of the guild you want to get the count for.
             days:
                 The number of days to count prune for (at least 1).

         Returns:
             the number of members estimated to be pruned.

         Raises:
             hikari.net.errors.NotFoundHTTPError:
                 If the guild is not found.
             hikari.net.errors.ForbiddenHTTPError:
                 If you lack the `KICK_MEMBERS` or you are not in the guild.
             hikari.net.errors.BadRequestHTTPError:
                 If you pass an invalid amount of days.
         """

    @abc.abstractmethod
    async def begin_guild_prune(
        self,
        guild: _guilds.GuildLikeT,
        days: int,
        *,
        compute_prune_count: bool = False,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> type_hints.Nullable[int]:
        """
        Prunes members of a given guild based on the number of inactive days.

        Args:
            guild:
                The object or ID of the guild you want to prune member of.
            days:
                The number of inactivity days you want to use as filter.
            compute_prune_count:
                Whether a count of pruned members is returned or not. Discouraged for large guilds.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Returns:
            `None` if `compute_prune_count` is `False`, or an :class:`int` representing the number
            of members who were kicked.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found:
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `KICK_MEMBER` permission or are not in the guild.
            hikari.net.errors.BadRequestHTTPError:
                If you provide invalid values for the `days` and `compute_prune_count` fields.
        """

    @abc.abstractmethod
    async def fetch_guild_voice_regions(self, guild: _guilds.GuildLikeT) -> typing.Collection[_voices.VoiceRegion]:
        """
        Gets the voice regions for a given guild.

        Args:
            guild:
                The object or ID of the guild to get the voice regions for.

        Returns:
            A list of :class:`hikari.orm.models.voices.VoiceRegion` objects.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found:
            hikari.net.errors.ForbiddenHTTPError:
                If you are not in the guild.
        """

    @abc.abstractmethod
    async def fetch_guild_invites(self, guild: _guilds.GuildLikeT) -> typing.Collection[_invites.Invite]:
        """
        Gets the invites for a given guild.

        Args:
            guild:
                The object or ID of the guild to get the invites for.

        Returns:
            A list of :class:`hikari.orm.models.invites.InviteWithMetadata` objects.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """

    @abc.abstractmethod
    async def fetch_integrations(self, guild: _guilds.GuildLikeT) -> typing.Collection[_integrations.Integration]:
        """
        Gets the integrations for a given guild.

        Args:
            guild:
                The object or ID of the guild to get the integrations for.

        Returns:
            A list of :class:`hikari.orm.models.integrations.Integration`  objects.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """

    @abc.abstractmethod
    async def create_guild_integration(
        self,
        guild: _guilds.GuildLikeT,
        integration_type: str,
        integration_id: bases.RawSnowflakeT,
        *,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> _integrations.Integration:
        """
        Creates an integrations for a given guild.

        Args:
            guild:
                The object or ID of the guild to create the integrations in.
            integration_type:
                The integration type string (e.g. "twitch" or "youtube").
            integration_id:
                The ID for the new integration.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Returns:
            The newly created :class:`hikari.orm.models.integrations.Integration` object.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """

    @abc.abstractmethod
    async def update_integration(
        self,
        guild: _guilds.GuildLikeT,
        integration: _integrations.IntegrationLikeT,
        *,
        expire_behaviour: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,  # TODO: is this documented?
        expire_grace_period: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,  #: TODO: is this days or seconds?
        enable_emojis: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Edits an integrations for a given guild.

        Args:
            guild:
                The object or ID of the guild to which the integration belongs to.
            integration:
                The object or ID of the integration.
            expire_behaviour:
                The behaviour for when an integration subscription lapses.
            expire_grace_period:
                Time interval in seconds in which the integration will ignore lapsed subscriptions.
            enable_emojis:
                Whether emojis should be synced for this integration.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild or the integration aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """

    @abc.abstractmethod
    async def delete_integration(self, guild: _guilds.GuildLikeT, integration: _integrations.IntegrationLikeT) -> None:
        """
        Deletes an integration for the given guild.

        Args:
            guild:
                The object or ID of the guild from which to delete an integration.
            integration:
                The object or ID of the integration to delete.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild or the integration aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """

    @abc.abstractmethod
    async def sync_guild_integration(
        self, guild: _guilds.GuildLikeT, integration: _integrations.IntegrationLikeT
    ) -> None:
        """
        Syncs the given integration.

        Args:
            guild:
                The object or ID of the guild to which the integration belongs to.
            integration:
                The object or ID of the integration to sync.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the guild or the integration aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you lack the `MANAGE_GUILD` permission or are not in the guild.
        """

    @abc.abstractmethod
    async def fetch_guild_embed(self, guild: _guilds.GuildLikeT) -> _guilds.GuildEmbed:
        """
          Gets the embed for a given guild.

          Args:
              guild:
                  The object or ID of the guild to get the embed for.

          Returns:
              A :class:`hikari.orm.models.guilds.GuildEmbed` object.

          Raises:
              hikari.net.errors.NotFoundHTTPError:
                  If the guild is not found.
              hikari.net.errors.ForbiddenHTTPError:
                  If you either lack the `MANAGE_GUILD` permission or are not in the guild.
        """

    @abc.abstractmethod
    async def modify_guild_embed(
        self,
        guild: _guilds.GuildLikeT,
        embed: _guilds.GuildEmbed,
        *,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Edits the embed for a given guild.

        Args:
            guild:
                The object or ID of the guild to edit the embed for.
            embed:
                The new embed object to be set.
            reason:
                Optional reason to add to audit logs for the guild explaining why the operation was performed.

        Returns:
            The updated :class:`hikari.orm.models.guilds.GuildEmbed` object.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you either lack the `MANAGE_GUILD` permission or are not in the guild.
        """

    @abc.abstractmethod
    async def fetch_guild_vanity_url(self, guild: _guilds.GuildLikeT) -> _invites.VanityURL:
        """
        Gets the vanity URL for a given guild.

        Args:
            guild:
                The object or ID of the guild to get the vanity URL for.

        Returns:
            A :class:`hikari.orm.models.invites.VanityURL` object.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you either lack the `MANAGE_GUILD` permission or are not in the guild.
        """

    @abc.abstractmethod
    def fetch_guild_widget_image(
        self, guild: _guilds.GuildLikeT, *, style: type_hints.NotRequired[_guilds.WidgetStyle] = unspecified.UNSPECIFIED
    ) -> str:
        """
         Get the URL for a guild widget.

         Args:
             guild:
                 The guild object or ID to use for the widget.
             style:
                 Optional and one of "shield", "banner1", "banner2", "banner3" or "banner4".

         Returns:
             A URL to retrieve a PNG widget for your guild.

         Note:
             This does not actually make any form of request, and shouldn't be awaited. Thus, it doesn't have rate
             limits either.

         Warning:
             The guild must have the widget enabled in the guild settings for this to be valid.
         """

    @abc.abstractmethod
    async def fetch_invite(
        self, invite: _invites.InviteLikeT, with_counts: type_hints.NotRequired[bool] = unspecified.UNSPECIFIED
    ) -> _invites.Invite:
        """
        Gets the given invite.

        Args:
            invite:
                The object or ID for wanted invite.
            with_counts:
                If `True`, attempt to count the number of times the invite has been used, otherwise (and as the
                default), do not try to track this information.

        Returns:
            The requested :class:`hikari.orm.models.invites.Invite` object.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the invite is not found.
        """

    @abc.abstractmethod
    async def delete_invite(self, invite: _invites.InviteLikeT) -> None:
        """
        Deletes a given invite.

        Args:
            invite:
                The object or ID for the invite to be deleted.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the invite is not found.
            hikari.net.errors.ForbiddenHTTPError
                If you lack either `MANAGE_CHANNELS` on the channel the invite belongs to or `MANAGE_GUILD` for
                guild-global delete.
        """

    @abc.abstractmethod
    async def fetch_user(self, user: _users.BaseUserLikeT) -> typing.Union[_users.User, _users.OAuth2User]:
        """
        Gets a given user.

        Args:
            user:
                The object or ID of the user to get.

        Returns:
            The requested :class:`hikari.orm.models.users.IUser` derivative object.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the user is not found.
        """

    @abc.abstractmethod
    async def fetch_application_info(self) -> _applications.Application:
        """
        Get the current application information.

        Returns:
            The current :class:`hikari.orm.models.applications.Application` object.
        """

    @abc.abstractmethod
    async def fetch_me(self) -> _users.OAuth2User:
        """
        Gets the current user that is represented by token given to the client.

        Returns:
            The current :class:`hikari.orm.models.users.OAuth2User` object.
        """

    @abc.abstractmethod
    async def update_me(
        self,
        *,
        username: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
        avatar_data: type_hints.NotRequired[storage.FileLikeT] = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Edits the current user. If any arguments are unspecified, then that subject is not changed on Discord.

        Args:
            username:
                The new username string.
            avatar_data:
                The new avatar image as a filek like object.

        Raises:
            hikari.net.errors.BadRequestHTTPError:
                If you pass username longer than the limit (2-32) or an invalid image.
        """

    @abc.abstractmethod
    async def fetch_my_connections(self) -> typing.Sequence[_connections.Connection]:
        """
        Gets the current user's connections. This endpoint can be used with both Bearer and Bot tokens
        but will usually return an empty list for bots (with there being some exceptions to this
        like user accounts that have been converted to bots).

        Returns:
            A list of :class:`hikari.orm.models.connections.Connection` objects.
        """

    @abc.abstractmethod
    async def fetch_my_guilds(
        self,
        before: type_hints.NotRequired[_guilds.GuildLikeT] = unspecified.UNSPECIFIED,
        after: type_hints.NotRequired[_guilds.GuildLikeT] = unspecified.UNSPECIFIED,
        limit: type_hints.NotRequired[int] = unspecified.UNSPECIFIED,
    ) -> typing.AsyncIterator[_guilds.Guild]:
        ...

    @abc.abstractmethod
    async def leave_guild(self, guild: _guilds.GuildLikeT) -> None:
        """
        Makes the current user leave a given guild.

        Args:
            guild:
                The object or ID of the guild to leave.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
        """

    @abc.abstractmethod
    async def create_dm_channel(self, recipient: _users.BaseUserLikeT) -> _channels.DMChannel:
        """
         Creates a new DM channel with a given user.

         Args:
             recipient:
                 The object or ID of the user to create the new DM channel with.

         Returns:
             The newly created :class:`hikari.orm.models.channels.DMChannel` object.

         Raises:
             hikari.net.errors.NotFoundHTTPError:
                 If the recipient is not found.
         """

    @abc.abstractmethod
    async def fetch_voice_regions(self) -> typing.Collection[_voices.VoiceRegion]:
        """
        Get the voice regions that are available.

        Returns:
            A list of available :class:`hikari.orm.models.voices.VoiceRegion` objects.

        Note:
            This does not include VIP servers.
        """

    @abc.abstractmethod
    async def create_webhook(
        self,
        #: TODO: Can we make webhooks to announcement channels/store channels?
        channel: _channels.GuildTextChannelLikeT,
        name: str,
        *,
        avatar_data: type_hints.NotRequired[storage.FileLikeT] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> _webhooks.Webhook:
        """
        Creates a webhook for a given channel.

        Args:
            channel:
                The object or ID of the channel for webhook to be created in.
            name:
                The webhook's name string.
            avatar_data:
                The avatar image as a file like object.
            reason:
                An optional audit log reason explaining why the change was made.

        Returns:
            The newly created :class:`hikari.orm.models.webhooks.Webhook` object.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the channel is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you either lack the `MANAGE_WEBHOOKS` permission or can not see the given channel.
            hikari.net.errors.BadRequestHTTPError:
                If the avatar image is too big or the format is invalid.
        """

    @abc.abstractmethod
    async def fetch_channel_webhooks(
        #: TODO: Can we make webhooks to announcement channels/store channels?
        self,
        channel: _channels.GuildTextChannelLikeT,
    ) -> typing.Collection[_webhooks.Webhook]:
        """
        Gets all webhooks from a given channel.

        Args:
            channel:
                The object or ID of the channel tp get the webhooks from.

        Returns:
            A list of :class:`hikari.orm.models.webhooks.Webhook` objects for the give channel.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the channel is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you either lack the `MANAGE_WEBHOOKS` permission or can not see the given channel.
        """

    @abc.abstractmethod
    async def fetch_guild_webhooks(self, guild: _guilds.GuildLikeT) -> typing.Collection[_webhooks.Webhook]:
        """
        Gets all webhooks for a given guild.

        Args:
            guild:
                The object or ID of the guild to get the webhooks from.

        Returns:
            A list of :class:`hikari.orm.models.webhooks.Webhook` objects for the given guild.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the guild is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you either lack the `MANAGE_WEBHOOKS` permission or aren't a member of the given guild.
        """

    @abc.abstractmethod
    async def fetch_webhook(self, webhook: _webhooks.WebhookLikeT) -> _webhooks.Webhook:
        """
        Gets a given webhook.

        Args:
            webhook:
                The ID of the webhook to get.

        Returns:
            The requested :class:`hikari.orm.models.webhooks.Webhook` object.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the webhook is not found.
            ForbiddenHTTPError:
                If you're not in the guild that owns this webhook or lack the `MANAGE_WEBHOOKS` permission.
        """

    @abc.abstractmethod
    async def update_webhook(
        self,
        webhook: _webhooks.WebhookLikeT,
        *,
        name: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
        avatar_data: type_hints.NotRequired[storage.FileLikeT] = unspecified.UNSPECIFIED,
        #: TODO: Can we make webhooks to announcement channels/store channels?
        channel: type_hints.NotRequired[_channels.GuildTextChannelLikeT] = unspecified.UNSPECIFIED,
        reason: type_hints.NotRequired[str] = unspecified.UNSPECIFIED,
    ) -> None:
        """
        Edits a given webhook.

        Args:
            webhook:
                The object or ID of the webhook to edit.
            name:
                The new name string.
            avatar_data:
                The new avatar image as a file like object.
            channel:
                The object or ID of the new channel the given webhook should be moved to.
            reason:
                An optional audit log reason explaining why the change was made.

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If either the webhook or the channel aren't found.
            hikari.net.errors.ForbiddenHTTPError:
                If you either lack the `MANAGE_WEBHOOKS` permission or aren't a member of the guild this webhook belongs
                to.
        """

    @abc.abstractmethod
    async def delete_webhook(self, webhook: _webhooks.WebhookLikeT) -> None:
        """
        Deletes a given webhook.

        Args:
            webhook:
                The object or ID of the webhook to delete

        Raises:
            hikari.net.errors.NotFoundHTTPError:
                If the webhook is not found.
            hikari.net.errors.ForbiddenHTTPError:
                If you either lack the `MANAGE_WEBHOOKS` permission or aren't a member of the guild this webhook belongs
                to.
        """
