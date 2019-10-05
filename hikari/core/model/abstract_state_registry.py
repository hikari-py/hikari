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
Handles managing the state of the bot, and the cache.
"""
from __future__ import annotations

import abc
import datetime
import typing

from hikari.core.model import channel
from hikari.core.model import emoji
from hikari.core.model import guild
from hikari.core.model import message
from hikari.core.model import presence
from hikari.core.model import role
from hikari.core.model import user
from hikari.core.model import webhook
from hikari.core.utils import types


class AbstractStateRegistry(abc.ABC):
    """
    Provides the relational interface between different types of objects and the overall cache.

    This class provides abstract definitions only to enable a user to implement their own cache system if they prefer.
    """

    __slots__ = ()

    @abc.abstractmethod
    def delete_channel(self, channel_id: int) -> channel.Channel:
        """
        Delete the given channel from the cache. This may be either a channel from a guild or a DM channel.

        Args:
            channel_id:
                the channel ID to delete.

        Returns:
            The channel that was deleted.

        Raises:
            KeyError:
                if the channel is not in the cache.
        """

    @abc.abstractmethod
    def delete_emoji(self, emoji_id: int) -> emoji.GuildEmoji:
        """
        Delete the given emoji ID from the cache.
        
        Args:
            emoji_id:
                the ID of the emoji to delete.

        Returns:
            The :class:`emoji.GuildEmoji` that was deleted.

        Raises:
            KeyError:
                If the emoji didn't exist.
        """

    @abc.abstractmethod
    def delete_guild(self, guild_id: int) -> guild.Guild:
        """
        Delete the given guild ID from the cache.

        Args:
            guild_id:
                the guild ID to delete.

        Returns:
            the :class:`guild.Guild` that was deleted.

        Raises:
            KeyError:
                If the guild does not exist in cache.
        """

    @abc.abstractmethod
    def delete_member_from_guild(self, user_id: int, guild_id: int) -> user.Member:
        """
        Delete the member with the given user ID from the given guild ID's member list.

        Args:
            user_id:
                the user ID to delete
            guild_id:
                the guild ID to delete from

        Returns:
            the :class:`user.Member` that was deleted.

        Raises:
            KeyError:
                If the member is not in the given guild or the given guild does not exist.
        """

    @abc.abstractmethod
    def delete_role(self, role_id: int) -> role.Role:
        """
        Delete the given role ID from the cache.

        Args:
            role_id:
                the ID of the role to delete.

        Returns:
            The :class:`role.Role` that was deleted.

        Raises:
            KeyError:
                If the role didn't exist.
        """

    @abc.abstractmethod
    def get_channel_by_id(self, channel_id: int) -> typing.Optional[channel.Channel]:
        """
        Find a channel by a given ID. Guilds are searched first. If no match is found in a guild, then any open DM
        channels are also checked. If nothing is found still, we return `None`.

        Args:
            channel_id:
                the channel ID.

        Returns:
            a :class:`channel.Channel` derivative, or `None` if nothing is found.
        """

    @abc.abstractmethod
    def get_guild_by_id(self, guild_id: int) -> typing.Optional[guild.Guild]:
        """
        Find a guild by an ID.

        Args:
            guild_id:
                the ID of the guild to look up.

        Returns:
            a :class:`guild.Guild` object, or `None` if one was not found.
        """

    @abc.abstractmethod
    def get_message_by_id(self, message_id: int) -> typing.Optional[message.Message]:
        """
        Find a message by an ID.

        Args:
            message_id:
                the ID of the message to look up.

        Returns:
            a :class:`message.Message` object, or `None` if one was not found.
        """

    @abc.abstractmethod
    def get_role_by_id(self, role_id: int) -> typing.Optional[role.Role]:
        """
        Find a cached role by an ID.

        Args:
            role_id:
                the ID of the role to look up.

        Returns:
            a :class:`role.Role` object, or `None` if one was not found.
        """

    @abc.abstractmethod
    def get_user_by_id(self, user_id: int) -> typing.Optional[user.User]:
        """
        Find a user by an ID.

        Args:
            user_id:
                the ID of the user to look up.

        Returns:
            a :class:`user.User` object, or `None` if one was not found.
        """

    @abc.abstractmethod
    def parse_bot_user(self, bot_user_payload: types.DiscordObject) -> user.BotUser:
        """
        Parses a bot user payload into a workable object

        Args:
            bot_user_payload:
                the payload of the bot user.

        Returns:
            a :class:`user.BotUser` object.
        """

    @abc.abstractmethod
    def parse_channel(self, channel_payload: types.DiscordObject) -> channel.Channel:
        """
        Parses a channel payload into a workable object

        Args:
            channel_payload:
                the payload of the channel.

        Returns:
            a :class:`channel.Channel` object.
        """

    @abc.abstractmethod
    def parse_emoji(self, emoji_payload: types.DiscordObject, guild_id: typing.Optional[int]) -> emoji.AbstractEmoji:
        """
        Parses a emoji payload into a workable object

        Args:
            emoji_payload:
                the payload of the emoji.
            guild_id:
                the ID of the guild the emoji is from.

        Returns:
            a :class:`emoji.AbstractEmoji` object.
        """

    @abc.abstractmethod
    def parse_guild(self, guild_payload: types.DiscordObject) -> guild.Guild:
        """
        Parses a guild payload into a workable object

        Args:
            guild_payload:
                the payload of the guild.

        Returns:
            a :class:`guild.Guild` object.
        """

    @abc.abstractmethod
    def parse_member(self, member_payload: types.DiscordObject, guild_id: int) -> user.Member:
        """
        Parses a member payload into a workable object

        Args:
            member_payload:
                the payload of the member.
            guild_id:
                the ID of the guild the member is from.

        Returns:
            a :class:`user.Member` object.
        """

    @abc.abstractmethod
    def parse_message(self, message_payload: types.DiscordObject) -> message.Message:
        """
        Parses a message payload into a workable object

        Args:
            message_payload:
                the payload of the message.

        Returns:
            a :class:`message.Message` object.
        """

    @abc.abstractmethod
    def parse_presence(self, guild_id: int, user_id: int, presence_payload: types.DiscordObject) -> presence.Presence:
        """
        Parse a presence for a given guild and user, and attempt to update the member corresponding to the presence
        if it can be found.

        Args:
            guild_id:
                the ID of the guild.
            user_id:
                the ID of the user.
            presence_payload:
                the payload containing the presence.

        Returns:
            a :class:`presence.Presence` object.
        """

    @abc.abstractmethod
    def parse_role(self, role_payload: types.DiscordObject, guild_id: int) -> role.Role:
        """
        Parses a role payload into a workable object

        Args:
            role_payload:
                the payload of the role.
            guild_id:
                the ID of the owning guild.

        Returns:
            a :class:`role.Role` object.
        """

    @abc.abstractmethod
    def parse_user(self, user_payload: types.DiscordObject) -> user.User:
        """
        Parses a user payload into a workable object

        Args:
            user_payload:
                the payload of the user.

        Returns:
            a :class:`user.User` object.
        """

    @abc.abstractmethod
    def parse_webhook(self, webhook_payload: types.DiscordObject) -> webhook.Webhook:
        """
        Parses a webhook payload into a workable object

        Args:
            webhook_payload:
                the payload of the webhook.

        Returns:
            a :class:`webhook.Webhook` object.
        """

    @abc.abstractmethod
    def update_channel(
        self, channel_payload: types.DiscordObject
    ) -> typing.Optional[typing.Tuple[channel.Channel, channel.Channel]]:
        """
        Update the given channel represented by the channel payload.

        Args:
            channel_payload:
                The raw payload to update the channel with. This contains the ID of the channel also.

        Returns:
            A :class:`tuple` of two :class:`channel.Channel` objects. The first represents the old channel state, and
            the second represents the new channel state. If no channel was cached, this returns `None`.
        """

    @abc.abstractmethod
    def update_guild(
        self, guild_payload: types.DiscordObject
    ) -> typing.Optional[typing.Tuple[guild.Guild, guild.Guild]]:
        """

        Update the given guild represented by the guild payload.

        Args:
            guild_payload:
                The raw guild payload to update. This contains the ID of the guild also.

        Returns:
            A :class:`tuple` of two :class:`guild.Guild` objects. The first represents the old guild state, and
            the second represents the new guild state. If no guild was cached, this returns `None`.
        """

    @abc.abstractmethod
    def update_guild_emojis(
        self, emoji_list: typing.List[types.DiscordObject], guild_id: int
    ) -> typing.Optional[typing.Tuple[typing.FrozenSet[emoji.GuildEmoji], typing.FrozenSet[emoji.GuildEmoji]]]:
        """
        Update the emojis in a given guild.

        Args:
            emoji_list:
                the list of the new unparsed emojis.
            guild_id:
                the ID of the guild the emojis were updated in.

        Returns:
            A :class:`tuple` of two :class:`frozenset` of :class:`hikari.core.model.emoji.GuildEmoji` objects.
            The first set contains all the old emojis. The second set contains all the new emojis. If the guild was
            not cached, this will just return `None`

            Note that this is not ordered.
        """

    @abc.abstractmethod
    def update_last_pinned_timestamp(self, channel_id: int, timestamp: typing.Optional[datetime.datetime]) -> None:
        """
        Update the last pinned timestamp time for the given channel.

        Args:
            channel_id:
                the ID of the channel to update.
            timestamp:
                the timestamp of the last pinned message, or `None` if it was just removed.
        """

    @abc.abstractmethod
    def update_member(
        self, guild_id: int, role_ids: typing.List[int], nick: typing.Optional[str], user_id: int
    ) -> typing.Optional[typing.Tuple[user.Member, user.Member]]:
        """
        Update a member in a given guild. If the member is not already registered, nothing is returned.

        Args:
            guild_id:
                the ID of the guild the member is in.
            role_ids:
                the list of roles the member should have.
            nick:
                the nickname of the member.
            user_id:
                the ID of the member to update.

        Returns:
            a :class:`tuple` of two :class:`user.Member` objects: first being the old state of the member and the
            second being the new state (if the member exists). If it does not exist in that guild, or the guild itself
            is not cached, then `None` is returned instead.
        """

    def update_member_presence(
        self, guild_id: int, user_id: int, presence_payload: types.DiscordObject
    ) -> typing.Optional[typing.Tuple[user.Member, presence.Presence, presence.Presence]]:
        """
        Update the presence for a given user in a given guild.

        Args:
            guild_id:
                The guild of the member.
            user_id:
                The ID of the member.
            presence_payload:
                The new presence to set.

        Returns:
            a :class:`tuple` of three items: the first being the :class:`user.Member` that was updated, the second
            being the :class:`presence.Presence` before, and the third being the :class:`presence.Presence` now.
            If the user, member, or guild does not exist in the cache, then `None` is returned instead.
        """


__all__ = ["AbstractStateRegistry"]
