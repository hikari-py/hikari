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

from hikari.core.models import channels
from hikari.core.models import emojis
from hikari.core.models import guilds
from hikari.core.models import members
from hikari.core.models import messages
from hikari.core.models import presences
from hikari.core.models import reactions
from hikari.core.models import roles
from hikari.core.models import users
from hikari.core.models import webhooks
from hikari.internal_utilities import data_structures


class StateRegistry(abc.ABC):
    """
    Provides the relational interface between different types of objects and the overall cache.

    This class provides abstract definitions only to enable a user to implement their own cache system if they prefer.
    """

    __slots__ = ()

    @property
    @abc.abstractmethod
    def me(self) -> users.BotUser:
        ...

    @property
    @abc.abstractmethod
    def message_cache(self) -> typing.Mapping[int, messages.Message]:
        ...

    @abc.abstractmethod
    def increment_reaction_count(self, message_obj: messages.Message, emoji_obj: emojis.Emoji) -> reactions.Reaction:
        """
        Adds 1 to the count for the reaction.

        Args:
            emoji_obj:
                the emoji of the reaction.
            message_obj:
                the message the reaction was on.

        Returns:
            a :class:`hikari.core.models.reactions.Reaction` object.
        """

    @abc.abstractmethod
    def decrement_reaction_count(
        self, message_obj: messages.Message, emoji_obj: emojis.Emoji
    ) -> typing.Optional[reactions.Reaction]:
        """
        Subtracts 1 from the count for the reaction.

        Args:
            emoji_obj:
                the emoji of the reaction.
            message_obj:
                the message the reaction was on.

        Note:
            If the count reaches zero, the reaction will be removed from the message additionally.

        Returns:
            a :class:`hikari.core.models.reactions.Reaction` object if the reaction existed already in the
            cache, otherwise `None`.
        """

    @abc.abstractmethod
    def delete_channel(self, channel_obj: channels.Channel) -> None:
        """
        Delete the given channel from the cache. This may be either a channel from a guild or a DM channel.

        Args:
            channel_obj:
                the channel to delete.
        """

    @abc.abstractmethod
    def delete_emoji(self, emoji_obj: emojis.GuildEmoji) -> None:
        """
        Delete the given guild emoji from the cache.
        
        Args:
            emoji_obj:
                the emoji to delete.
        """

    @abc.abstractmethod
    def delete_guild(self, guild_obj: guilds.Guild) -> None:
        """
        Delete the given guild from the cache.

        Args:
            guild_obj:
                the guild to delete.
        """

    @abc.abstractmethod
    def delete_message(self, message_obj: messages.Message) -> None:
        """
        Delete the given message from the cache if it exists,

        Args:
            message_obj:
                the message to delete.
        """

    @abc.abstractmethod
    def delete_member(self, member_obj: members.Member) -> None:
        """
        Delete the member with the given user ID from the guilds member list.

        Args:
            member_obj:
                the member to remove.
        """

    @abc.abstractmethod
    def delete_reaction(self, message_obj: messages.Message, user_obj: users.User, emoji_obj: emojis.Emoji) -> None:
        """
        Attempt to remove the given reaction from the given message by the given user..

        Args:
            message_obj:
                the message to remove the reaction from.
            user_obj:
                the user to remove the reaction from.
            emoji_obj:
                the parsed emoji object that the reaction was made as.
        """

    @abc.abstractmethod
    def delete_role(self, role_obj: roles.Role) -> None:
        """
        Delete the given role ID from the cache.

        Args:
            role_obj:
                the role to remove

        Note:
            This will also update all cached members in the owning guild to not have that role anymore.
        """

    @abc.abstractmethod
    def get_channel_by_id(self, channel_id: int) -> typing.Optional[channels.Channel]:
        """
        Find a channel by a given ID. Guilds are searched first. If no match is found in a guild, then any open DM
        channels are also checked. If nothing is found still, we return `None`.

        Args:
            channel_id:
                the channel ID.

        Returns:
            a :class:`hikari.core.models.channels.Channel` derivative, or `None` if nothing is found.
        """

    @abc.abstractmethod
    def get_guild_by_id(self, guild_id: int) -> typing.Optional[guilds.Guild]:
        """
        Find a guild by an ID.

        Args:
            guild_id:
                the ID of the guild to look up.

        Returns:
            a :class:`hikari.core.models.guilds.Guild` object, or `None` if one was not found.
        """

    @abc.abstractmethod
    def get_message_by_id(self, message_id: int) -> typing.Optional[messages.Message]:
        """
        Find a message by an ID.

        Args:
            message_id:
                the ID of the message to look up.

        Returns:
            a :class:`hikari.core.models.messages.Message` object, or `None` if one was not found.
        """

    @abc.abstractmethod
    def get_role_by_id(self, guild_id: int, role_id: int) -> typing.Optional[roles.Role]:
        """
        Find a cached role by an ID.

        Args:
            guild_id:
                the ID of the guild that the role is in.
            role_id:
                the ID of the role to look up.

        Returns:
            a :class:`hikari.core.models.roles.Role` object, or `None` if a role/guild was not found matching the given
            IDs.
        """

    @abc.abstractmethod
    def get_user_by_id(self, user_id: int) -> typing.Optional[users.User]:
        """
        Find a user by an ID.

        Args:
            user_id:
                the ID of the user to look up.

        Returns:
            a :class:`hikari.core.models.users.User` object, or `None` if one was not found.
        """

    @abc.abstractmethod
    def get_member_by_id(self, user_id: int, guild_id: int) -> typing.Optional[members.Member]:
        """
        Find a member in a specific guild by their ID.

        Args:
            user_id:
                the ID of the member to look up.
            guild_id:
                the ID of the guild to look in.

        Returns:
            a :class:`hikari.core.models.members.Member` object, or `None` if one was not found.
        """

    @abc.abstractmethod
    def parse_bot_user(self, bot_user_payload: data_structures.DiscordObjectT) -> users.BotUser:
        """
        Parses a bot user payload into a workable object

        Args:
            bot_user_payload:
                the payload of the bot user.

        Returns:
            a :class:`hikari.core.models.users.BotUser` object.
        """

    @abc.abstractmethod
    def parse_channel(
        self, channel_payload: data_structures.DiscordObjectT, guild_id: typing.Optional[int]
    ) -> channels.Channel:
        """
        Parses a channel payload into a workable object

        Args:
            channel_payload:
                the payload of the channel.
            guild_id:
                the guild ID, if we know it, otherwise None. This is used to resolve missing guild_id information
                due to an inconsistency in the public Discord API when parsing guild channels.

        Returns:
            a :class:`hikari.core.models.channels.Channel` object.
        """

    @abc.abstractmethod
    def parse_emoji(
        self, emoji_payload: data_structures.DiscordObjectT, guild_id: typing.Optional[int]
    ) -> emojis.Emoji:
        """
        Parses a emoji payload into a workable object

        Args:
            emoji_payload:
                the payload of the emoji.
            guild_id:
                the ID of the guild the emoji is from.

        Returns:
            a :class:`hikari.core.models.emojis.AbstractEmoji` object.
        """

    @abc.abstractmethod
    def parse_guild(self, guild_payload: data_structures.DiscordObjectT) -> guilds.Guild:
        """
        Parses a guild payload into a workable object

        Args:
            guild_payload:
                the payload of the guild.

        Returns:
            a :class:`hikari.core.models.guilds.Guild` object.
        """

    @abc.abstractmethod
    def parse_member(self, member_payload: data_structures.DiscordObjectT, guild_obj: guilds.Guild) -> members.Member:
        """
        Parses a member payload into a workable object

        Args:
            member_payload:
                the payload of the member.
            guild_obj:
                the guild the member should be placed in.

        Returns:
            a :class:`hikari.core.models.members.Member` object.
        """

    @abc.abstractmethod
    def parse_message(self, message_payload: data_structures.DiscordObjectT) -> typing.Optional[messages.Message]:
        """
        Parses a message payload into a workable object

        Args:
            message_payload:
                the payload of the message.

        Returns:
            a :class:`hikari.core.models.messages.Message` object. If the channel doesn't exist, it will refuse to
            parse the object and return `None` instead.

        Warning:
            This will not validate whether internal channels and guilds exist. You must do that yourself, as there
            are cases where partially parsed messages may be useful to return. This **will** however update any
            last_message_timestamp objects if the channel is resolvable. If it is not resolvable, that step will be
            skipped.
        """

    @abc.abstractmethod
    def parse_presence(
        self, member_obj: members.Member, presence_payload: data_structures.DiscordObjectT
    ) -> presences.Presence:
        """
        Parse a presence for a given guild and user, and attempt to update the member corresponding to the presence
        if it can be found.

        Args:
            member_obj:
                the member to update the presence for.
            presence_payload:
                the payload containing the presence.

        Returns:
            a :class:`hikari.core.models.presences.Presence` object.
        """

    @abc.abstractmethod
    def parse_reaction(self, reaction_payload: data_structures.DiscordObjectT) -> typing.Optional[reactions.Reaction]:
        """
        Attempt to parse a reaction object and store it on the corresponding message.

        Args:
            reaction_payload:
                the reaction object to parse.

        Returns:
            a :class:`hikari.core.models.reactions.Reaction` object. If message channel doesn't exist, it will refuse to
            parse the object and return `None` instead.
        """

    @abc.abstractmethod
    def parse_role(self, role_payload: data_structures.DiscordObjectT, guild_obj: guilds.Guild) -> roles.Role:
        """
        Parses a role payload into a workable object

        Args:
            role_payload:
                the payload of the role.
            guild_obj:
                the guild the role is in.

        Returns:
            a :class:`hikari.core.models.roles.Role` object.
        """

    @abc.abstractmethod
    def parse_user(self, user_payload: data_structures.DiscordObjectT) -> users.User:
        """
        Parses a user payload into a workable object

        Args:
            user_payload:
                the payload of the user.

        Returns:
            a :class:`hikari.core.models.users.User` object.

        Note:
            If the user is detected to be the bot user for the account you are signed in as, then one can expect
            the :meth:`parse_bot_user` method to be invoked internally instead. This can only occur if the bot's
            user has already been parsed once during the lifetime of this registry, although a conforming gateway
            implementation should ensure this occurs beforehand anyway, since passing the bot user is part of a
            successful handshake.
        """

    @abc.abstractmethod
    def parse_webhook(self, webhook_payload: data_structures.DiscordObjectT) -> webhooks.Webhook:
        """
        Parses a webhook payload into a workable object

        Args:
            webhook_payload:
                the payload of the webhook.

        Returns:
            a :class:`hikari.core.models.webhooks.Webhook` object.
        """

    @abc.abstractmethod
    def delete_all_reactions(self, message_obj: messages.Message) -> None:
        """
        Removes all reactions from a message.

        Args:
            message_obj:
                the message the reaction was on.
        """

    @abc.abstractmethod
    def set_guild_unavailability(self, guild_obj: guilds.Guild, unavailability: bool) -> None:
        """
        Set the availability for the given guild.

        Args:
            guild_obj:
                the guild to update.
            unavailability:
                `True` if unavailable, `False` if available.
        """

    @abc.abstractmethod
    def set_last_pinned_timestamp(
        self, channel_obj: channels.TextChannel, timestamp: typing.Optional[datetime.datetime]
    ) -> None:
        """
        Set the last pinned timestamp time for the given channel.

        Args:
            channel_obj:
                the channel to update.
            timestamp:
                the timestamp of the last pinned message, or `None` if it was just removed.
        """

    @abc.abstractmethod
    def set_roles_for_member(self, role_objs: typing.Sequence[roles.Role], member_obj: members.Member) -> None:
        """
        Set the roles for the given member.

        Args:
            role_objs:
                roles to set on the member.
            member_obj:
                the member to update.
        """

    @abc.abstractmethod
    def update_channel(
        self, channel_payload: data_structures.DiscordObjectT
    ) -> typing.Optional[typing.Tuple[channels.Channel, channels.Channel]]:
        """
        Update the given channel represented by the channel payload.

        Args:
            channel_payload:
                the raw payload to update the channel with. This contains the ID of the channel also.

        Returns:
            Two :class:`hikari.core.models.channels.Channel` objects. The first represents the old channel state, and
            the second represents the new channel state. If no channel was cached, this returns `None`.
        """

    @abc.abstractmethod
    def update_guild(
        self, guild_payload: data_structures.DiscordObjectT
    ) -> typing.Optional[typing.Tuple[guilds.Guild, guilds.Guild]]:
        """

        Update the given guild represented by the guild payload.

        Args:
            guild_payload:
                The raw guild payload to update. This contains the ID of the guild also.

        Returns:
            Two :class:`hikari.core.models.guilds.Guild` objects. The first represents the old guild state, and
            the second represents the new guild state. If no guild was cached, this returns `None`.
        """

    @abc.abstractmethod
    def update_guild_emojis(
        self, emoji_list: typing.List[data_structures.DiscordObjectT], guild_id: int
    ) -> typing.Optional[typing.Tuple[typing.FrozenSet[emojis.GuildEmoji], typing.FrozenSet[emojis.GuildEmoji]]]:
        """
        Update the emojis in a given guild.

        Args:
            emoji_list:
                the list of the new unparsed emojis.
            guild_id:
                the ID of the guild the emojis were updated in.

        Returns:
            Two :class:`frozenset` of :class:`hikari.core.models.emojis.GuildEmoji` objects.
            The first set contains all the old emojis. The second set contains all the new emojis. If the guild was
            not cached, this will just return `None`

            Note that this is not ordered.
        """

    @abc.abstractmethod
    def update_member(
        self, guild_id: int, role_ids: typing.List[int], nick: typing.Optional[str], user_id: int
    ) -> typing.Optional[typing.Tuple[members.Member, members.Member]]:
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
            Two :class:`hikari.core.models.members.Member` objects. The first being the old state of the member and the
            second being the new state (if the member exists). If it does not exist in that guild, or the guild itself
            is not cached, then `None` is returned instead.
        """

    @abc.abstractmethod
    def update_member_presence(
        self, guild_id: int, user_id: int, presence_payload: data_structures.DiscordObjectT
    ) -> typing.Optional[typing.Tuple[members.Member, presences.Presence, presences.Presence]]:
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
            Three items. The first being the :class:`hikari.core.models.members.Member` that was updated, the second
            being the :class:`hikari.core.models.presences.Presence` before, and the third being the
            :class:`hikari.core.models.presences.Presence` now.
            If the user, member, or guild does not exist in the cache, then `None` is returned instead.
        """

    @abc.abstractmethod
    def update_message(
        self, payload: data_structures.DiscordObjectT
    ) -> typing.Optional[typing.Tuple[messages.Message, messages.Message]]:
        """
        Update a message in the cache.

        Args:
            payload:
                The message_update payload to parse.

        Returns:
            Two items. The first being the old :class:`hikari.core.models.messages.Message` and the second being the
            new :class:`hikari.core.models.messages.Message`. If the message was not cached, then `None` is returned
            instead of a tuple.
        """

    @abc.abstractmethod
    def update_role(
        self, guild_id: int, role_payload: data_structures.DiscordObjectT
    ) -> typing.Optional[typing.Tuple[roles.Role, roles.Role]]:
        """
        Update the given role in a given guild.

        Args:
            guild_id:
                The ID of the guild.
            role_payload:
                The role to update.

        Returns:
            A :class:`tuple` of two items: the first being the old :class:`hikari.core.models.roles.Role` state and the
            second being the new :class:`hikari.core.models.roles.Role` state. If the `guild_id` does not correspond to
            a guild in the cache, then `None` is returned instead.
        """


__all__ = ["StateRegistry"]
