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
"""Core interface for a cache implementation."""
from __future__ import annotations

__all__: typing.Sequence[str] = ("CacheView", "Cache", "MutableCache")

import abc
import typing

if typing.TYPE_CHECKING:
    from hikari import channels
    from hikari import emojis
    from hikari import guilds
    from hikari import invites
    from hikari import messages
    from hikari import presences
    from hikari import snowflakes
    from hikari import stickers
    from hikari import users
    from hikari import voices
    from hikari.api import config

_KeyT = typing.TypeVar("_KeyT", bound=typing.Hashable)
_ValueT = typing.TypeVar("_ValueT")


class CacheView(typing.Mapping[_KeyT, _ValueT], abc.ABC):
    """Interface describing an immutable snapshot view of part of a cache.

    This can be treated as a normal `typing.Mapping` but with some special methods.
    """

    __slots__: typing.Sequence[str] = ()

    @typing.overload
    @abc.abstractmethod
    def get_item_at(self, index: int, /) -> _ValueT:
        ...

    @typing.overload
    @abc.abstractmethod
    def get_item_at(self, index: slice, /) -> typing.Sequence[_ValueT]:
        ...

    @abc.abstractmethod
    def get_item_at(self, index: typing.Union[slice, int], /) -> typing.Union[_ValueT, typing.Sequence[_ValueT]]:
        """Get an item at a specific position or slice."""


class Cache(abc.ABC):
    """Interface describing the operations a cache component should provide.

    This will be used by the gateway to cache specific types of
    objects that the application should attempt to remember for later, depending
    on how this is implemented. The requirement for this stems from the
    assumption by Discord that bot applications will maintain some form of
    "memory" of the events that occur.

    The implementation may choose to use a simple in-memory collection of
    objects, or may decide to use a distributed system such as a Redis cache
    for cross-process bots.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def settings(self) -> config.CacheSettings:
        """Get the configured settings for this cache."""

    @abc.abstractmethod
    def get_dm_channel_id(
        self, user: snowflakes.SnowflakeishOr[users.PartialUser], /
    ) -> typing.Optional[snowflakes.Snowflake]:
        """Get the DM channel ID for a user.

        Parameters
        ----------
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user to get the DM channel ID for.

        Returns
        -------
        typing.Optional[hikari.snowflakes.Snowflake]
            ID of the DM channel which was found cached for the supplied user or
            `None`.
        """

    @abc.abstractmethod
    def get_dm_channel_ids_view(self) -> CacheView[snowflakes.Snowflake, snowflakes.Snowflake]:
        """Get a view of the cached DM channel IDs.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.snowflakes.Snowflake]
            Cache view of user IDs to DM channel IDs.
        """

    @abc.abstractmethod
    def get_emoji(
        self, emoji: snowflakes.SnowflakeishOr[emojis.CustomEmoji], /
    ) -> typing.Optional[emojis.KnownCustomEmoji]:
        """Get a known custom emoji from the cache.

        Parameters
        ----------
        emoji : hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]
            Object or ID of the emoji to get from the cache.

        Returns
        -------
        typing.Optional[hikari.emojis.KnownCustomEmoji]
            The object of the emoji that was found in the cache or `None`.
        """

    @abc.abstractmethod
    def get_emojis_view(self) -> CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        """Get a view of the known custom emoji objects in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.emojis.KnownCustomEmoji]
            A view of emoji IDs to objects of the known custom emojis found in
            the cache.
        """

    @abc.abstractmethod
    def get_emojis_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        """Get a view of the known custom emojis cached for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get the cached emoji objects for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.emojis.KnownCustomEmoji]
            A view of emoji IDs to objects of emojis found in the cache for the
            specified guild.
        """

    @abc.abstractmethod
    def get_sticker(
        self, sticker: snowflakes.SnowflakeishOr[stickers.GuildSticker], /
    ) -> typing.Optional[stickers.GuildSticker]:
        """Get a sticker from the cache.

        Parameters
        ----------
        sticker : hikari.snowflakes.SnowflakeishOr[hikari.stickers.GuildSticker]
            Object or ID of the sticker to get from the cache.

        Returns
        -------
        typing.Optional[hikari.stickers.GuildSticker]
            The object of the sticker that was found in the cache or `None`.
        """

    @abc.abstractmethod
    def get_stickers_view(self) -> CacheView[snowflakes.Snowflake, stickers.GuildSticker]:
        """Get a view of the sticker objects in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.stickers.GuildSticker]
            A view of sticker IDs to objects of the stickers found in the cache.
        """

    @abc.abstractmethod
    def get_stickers_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, stickers.GuildSticker]:
        """Get a view of the known custom emojis cached for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get the cached sticker objects for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.stickers.GuildSticker]
            A view of sticker IDs to objects of stickers found in the cache for the
            specified guild.
        """

    @abc.abstractmethod
    def get_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> typing.Optional[guilds.GatewayGuild]:
        """Get a guild from the cache.

        .. warning::
            This will return a guild regardless of whether it is available or
            not. To only query available guilds, use `get_available_guild`
            instead. Likewise, to only query unavailable guilds, use
            `get_unavailable_guild`.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get from the cache.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The object of the guild if found, else `None`.
        """

    @abc.abstractmethod
    def get_available_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> typing.Optional[guilds.GatewayGuild]:
        """Get the object of an available guild from the cache.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get from the cache.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The object of the guild if found, else `None`.
        """

    @abc.abstractmethod
    def get_unavailable_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> typing.Optional[guilds.GatewayGuild]:
        """Get the object of a unavailable guild from the cache.

        .. note::
            Unlike `Cache.get_available_guild`, the objects returned by this
            method will likely be out of date and inaccurate as they are
            considered unavailable, meaning that we are not receiving gateway
            events for this guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get from the cache.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The object of the guild if found, else `None`.
        """

    @abc.abstractmethod
    def get_guilds_view(self) -> CacheView[snowflakes.Snowflake, guilds.GatewayGuild]:
        """Get a view of all the guild objects in the cache regardless if availability.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.GatewayGuild]
            A view of guild IDs to the guild objects found in the cache.
        """

    @abc.abstractmethod
    def get_available_guilds_view(self) -> CacheView[snowflakes.Snowflake, guilds.GatewayGuild]:
        """Get a view of the available guild objects in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.GatewayGuild]
            A view of guild IDs to the guild objects found in the cache.
        """

    @abc.abstractmethod
    def get_unavailable_guilds_view(self) -> CacheView[snowflakes.Snowflake, guilds.GatewayGuild]:
        """Get a view of the unavailable guild objects in the cache.

        .. note::
            Unlike `Cache.get_available_guilds_view`, the objects returned by
            this method will likely be out of date and inaccurate as they are
            considered unavailable, meaning that we are not receiving gateway
            events for this guild.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.GatewayGuild]
            A view of guild IDs to the guild objects found in the cache.
        """

    @abc.abstractmethod
    def get_guild_channel(
        self, channel: snowflakes.SnowflakeishOr[channels.PartialChannel], /
    ) -> typing.Optional[channels.PermissibleGuildChannel]:
        """Get a guild channel from the cache.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            Object or ID of the guild channel to get from the cache.

        Returns
        -------
        typing.Optional[hikari.channels.PermissibleGuildChannel]
            The object of the guild channel that was found in the cache or
            `None`.
        """

    @abc.abstractmethod
    def get_guild_channels_view(self) -> CacheView[snowflakes.Snowflake, channels.PermissibleGuildChannel]:
        """Get a view of the guild channels in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.PermissibleGuildChannel]
            A view of channel IDs to objects of the guild channels found in the
            cache.
        """

    @abc.abstractmethod
    def get_guild_channels_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, channels.PermissibleGuildChannel]:
        """Get a view of the guild channels in the cache for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get the cached channels for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.PermissibleGuildChannel]
            A view of channel IDs to objects of the guild channels found in the
            cache for the specified guild.
        """

    @abc.abstractmethod
    def get_thread(
        self, thread: snowflakes.SnowflakeishOr[channels.PartialChannel], /
    ) -> typing.Optional[channels.GuildThreadChannel]:
        """Get a thread channel from the cache.

        Parameters
        ----------
        thread : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            Object or ID of the thread to get from the cache.

        Returns
        -------
        typing.Optional[hikari.channels.GuildThreadChannel]
            The object of the thread that was found in the cache
            or `builtins.None`.
        """

    @abc.abstractmethod
    def get_threads_view(self) -> CacheView[snowflakes.Snowflake, channels.GuildThreadChannel]:
        """Get a view of the thread channels in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.GuildThreadChannel]
            A view of channel IDs to objects of the thread channels found in the
            cache.
        """

    @abc.abstractmethod
    def get_threads_view_for_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels.PartialChannel],
        /,
    ) -> CacheView[snowflakes.Snowflake, channels.GuildThreadChannel]:
        """Get a view of the thread channels in the cache for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get the cached thread channels for.
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            Object or ID of the channel to get the cached thread channels for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.GuildThreadChannel]
            A view of channel IDs to objects of the thread channels found in the
            cache for the specified channel.
        """

    @abc.abstractmethod
    def get_threads_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, channels.GuildThreadChannel]:
        """Get a view of the thread channels in the cache for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get the cached thread channels for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.GuildThreadChannel]
            A view of channel IDs to objects of the thread channels found in the
            cache for the specified guild.
        """

    @abc.abstractmethod
    def get_invite(self, code: typing.Union[invites.InviteCode, str], /) -> typing.Optional[invites.InviteWithMetadata]:
        """Get an invite object from the cache.

        Parameters
        ----------
        code : typing.Union[hikari.invites.InviteCode, str]
            The object or string code of the invite to get from the cache.

        Returns
        -------
        typing.Optional[hikari.invites.InviteWithMetadata]
            The object of the invite that was found in the cache or `None`.
        """

    @abc.abstractmethod
    def get_invites_view(self) -> CacheView[str, invites.InviteWithMetadata]:
        """Get a view of the invite objects in the cache.

        Returns
        -------
        CacheView[str, hikari.invites.InviteWithMetadata]
            A view of string codes to objects of the invites that were found in
            the cache.
        """

    @abc.abstractmethod
    def get_invites_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[str, invites.InviteWithMetadata]:
        """Get a view of the invite objects in the cache for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get invite objects for.

        Returns
        -------
        CacheView[str, hikari.invites.InviteWithMetadata]
            A view of string code to objects of the invites that were found in
            the cache for the specified guild.
        """

    @abc.abstractmethod
    def get_invites_view_for_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels.PartialChannel],
        /,
    ) -> CacheView[str, invites.InviteWithMetadata]:
        """Get a view of the invite objects in the cache for a specified channel.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get invite objects for.
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            Object or ID of the channel to get invite objects for.

        Returns
        -------
        CacheView[str, invites.InviteWithMetadata]
            A view of string codes to objects of the invites there were found in
            the cache for the specified channel.
        """

    @abc.abstractmethod
    def get_me(self) -> typing.Optional[users.OwnUser]:
        """Get the own user object from the cache.

        Returns
        -------
        typing.Optional[hikari.users.OwnUser]
            The own user object that was found in the cache, else `None`.
        """

    @abc.abstractmethod
    def get_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> typing.Optional[guilds.Member]:
        """Get a member object from the cache.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get a cached member for.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user to get a cached member for.

        Returns
        -------
        typing.Optional[hikari.guilds.Member]
            The object of the member found in the cache, else `None`.
        """

    @abc.abstractmethod
    def get_members_view(self) -> CacheView[snowflakes.Snowflake, CacheView[snowflakes.Snowflake, guilds.Member]]:
        """Get a view of all the members objects in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Member]]
            A view of guild IDs to views of user IDs to objects of the members
            that were found from the cache.
        """

    @abc.abstractmethod
    def get_members_view_for_guild(
        self, guild_id: snowflakes.Snowflakeish, /
    ) -> CacheView[snowflakes.Snowflake, guilds.Member]:
        """Get a view of the members cached for a specific guild.

        Parameters
        ----------
        guild_id : hikari.snowflakes.Snowflakeish
            The ID of the guild to get the cached member view for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Member]
            The view of user IDs to the members cached for the specified guild.
        """

    @abc.abstractmethod
    def get_message(
        self, message: snowflakes.SnowflakeishOr[messages.PartialMessage], /
    ) -> typing.Optional[messages.Message]:
        """Get a message object from the cache.

        Parameters
        ----------
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            Object or ID of the message to get from the cache.

        Returns
        -------
        typing.Optional[hikari.messages.Message]
            The object of the message found in the cache or `None`.
        """

    @abc.abstractmethod
    def get_messages_view(self) -> CacheView[snowflakes.Snowflake, messages.Message]:
        """Get a view of all the message objects in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.messages.Message]
            A view of message objects found in the cache.
        """

    @abc.abstractmethod
    def get_presence(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> typing.Optional[presences.MemberPresence]:
        """Get a presence object from the cache.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get a presence for.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user to get a presence for.

        Returns
        -------
        typing.Optional[hikari.presences.MemberPresence]
            The object of the presence that was found in the cache or
            `None`.
        """

    @abc.abstractmethod
    def get_presences_view(
        self,
    ) -> CacheView[snowflakes.Snowflake, CacheView[snowflakes.Snowflake, presences.MemberPresence]]:
        """Get a view of all the presence objects in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, CacheView[hikari.snowflakes.Snowflake]]
            A view of guild IDs to views of user IDs to objects of the presences
            found in the cache.
        """

    @abc.abstractmethod
    def get_presences_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, presences.MemberPresence]:
        """Get a view of the presence objects in the cache for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get the cached presence objects for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.presences.MemberPresence]
            A view of user IDs to objects of the presence found in the cache
            for the specified guild.
        """

    @abc.abstractmethod
    def get_role(self, role: snowflakes.SnowflakeishOr[guilds.PartialRole], /) -> typing.Optional[guilds.Role]:
        """Get a role object from the cache.

        Parameters
        ----------
        role : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialRole]
            Object or ID of the role to get from the cache.

        Returns
        -------
        typing.Optional[hikari.guilds.Role]
            The object of the role found in the cache or `None`.
        """

    @abc.abstractmethod
    def get_roles_view(self) -> CacheView[snowflakes.Snowflake, guilds.Role]:
        """Get a view of all the role objects in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Role]
            A view of role IDs to objects of the roles found in the cache.
        """

    @abc.abstractmethod
    def get_roles_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, guilds.Role]:
        """Get a view of the roles in the cache for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get the cached roles for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Role]
            A view of role IDs to objects of the roles that were found in the
            cache for the specified guild.
        """

    @abc.abstractmethod
    def get_user(self, user: snowflakes.SnowflakeishOr[users.PartialUser], /) -> typing.Optional[users.User]:
        """Get a user object from the cache.

        Parameters
        ----------
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user to get from the cache.

        Returns
        -------
        typing.Optional[hikari.users.User]
            The object of the user that was found in the cache, else
            `None`.
        """

    @abc.abstractmethod
    def get_users_view(self) -> CacheView[snowflakes.Snowflake, users.User]:
        """Get a view of the user objects in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.users.User]
            The view of user IDs to the users found in the cache.
        """

    @abc.abstractmethod
    def get_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> typing.Optional[voices.VoiceState]:
        """Get a voice state object from the cache.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get a voice state for.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user to get a voice state for.

        Returns
        -------
        typing.Optional[hikari.voices.VoiceState]
            The object of the voice state that was found in the cache, or
            `None`.
        """

    @abc.abstractmethod
    def get_voice_states_view(
        self,
    ) -> CacheView[snowflakes.Snowflake, CacheView[snowflakes.Snowflake, voices.VoiceState]]:
        """Get a view of all the voice state objects in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, CacheView[hikari.snowflakes.Snowflake, hikari.voices.VoiceState]]
            A view of guild IDs to views of user IDs to objects of the voice
            states that were found in the cache.
        """

    @abc.abstractmethod
    def get_voice_states_view_for_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels.PartialChannel],
        /,
    ) -> CacheView[snowflakes.Snowflake, voices.VoiceState]:
        """Get a view of the voice states cached for a specific channel.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get the cached voice states for.
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            Object or ID of the channel to get the cached voice states for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.voices.VoiceState]
            A view of user IDs to objects of the voice states found cached for
            the specified channel.
        """

    @abc.abstractmethod
    def get_voice_states_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, voices.VoiceState]:
        """Get a view of the voice states cached for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to get the cached voice states for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.voices.VoiceState]
            A view of user IDs to objects of the voice states found cached for
            the specified guild.
        """


class MutableCache(Cache, abc.ABC):
    """Cache that exposes read-only operations as well as mutation operations.

    This is only exposed to internal components. There is no guarantee the
    user-facing cache will provide these methods or not.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def clear(self) -> None:
        """Clear the full cache."""

    @abc.abstractmethod
    def clear_dm_channel_ids(self) -> CacheView[snowflakes.Snowflake, snowflakes.Snowflake]:
        """Remove all the cached DM channel IDs.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.snowflakes.Snowflake]
            Cache view of user IDs to DM channel IDs which were cleared from
            the cache.
        """

    @abc.abstractmethod
    def delete_dm_channel_id(
        self, user: snowflakes.SnowflakeishOr[users.PartialUser], /
    ) -> typing.Optional[snowflakes.Snowflake]:
        """Remove a DM channel ID from the cache.

        Parameters
        ----------
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user to remove the cached DM channel ID for.

        Returns
        -------
        typing.Optional[hikari.snowflakes.Snowflake]
            The DM channel ID which was removed from the cache if found, else
            `None`.
        """

    @abc.abstractmethod
    def set_dm_channel_id(
        self,
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        channel: snowflakes.SnowflakeishOr[channels.PartialChannel],
        /,
    ) -> None:
        """Add a DM channel ID to the cache.

        Parameters
        ----------
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user to add a DM channel ID to the cache for.
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            Object or ID of the DM channel to add to the cache.
        """

    @abc.abstractmethod
    def clear_emojis(self) -> CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        """Remove all the known custom emoji objects from the cache.

        .. note::
            This will skip emojis that are being kept alive by a reference
            on a presence entry.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.emojis.KnownCustomEmoji]
            A cache view of emoji IDs to objects of the emojis that were
            removed from the cache.
        """

    @abc.abstractmethod
    def clear_emojis_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        """Remove the known custom emoji objects cached for a specific guild.

        .. note::
            This will skip emojis that are being kept alive by a reference
            on a presence entry.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove the cached emoji objects for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.emojis.KnownCustomEmoji]
            A view of emoji IDs to objects of the emojis that were removed
            from the cache.
        """

    @abc.abstractmethod
    def delete_emoji(
        self, emoji: snowflakes.SnowflakeishOr[emojis.CustomEmoji], /
    ) -> typing.Optional[emojis.KnownCustomEmoji]:
        """Remove a known custom emoji from the cache.

        .. note::
            This will not delete emojis that are being kept alive by a reference
            on a presence entry.

        Parameters
        ----------
        emoji : hikari.snowflakes.SnowflakeishOr[hikari.emojis.CustomEmoji]
            Object or ID of the emoji to remove from the cache.

        Returns
        -------
        typing.Optional[hikari.emojis.KnownCustomEmoji]
            The object of the emoji that was removed from the cache or
            `None`.
        """

    @abc.abstractmethod
    def set_emoji(self, emoji: emojis.KnownCustomEmoji, /) -> None:
        """Add a known custom emoji to the cache.

        Parameters
        ----------
        emoji : hikari.emojis.KnownCustomEmoji
            The object of the known custom emoji to add to the cache.
        """

    @abc.abstractmethod
    def update_emoji(
        self, emoji: emojis.KnownCustomEmoji, /
    ) -> typing.Tuple[typing.Optional[emojis.KnownCustomEmoji], typing.Optional[emojis.KnownCustomEmoji]]:
        """Update an emoji object in the cache.

        Parameters
        ----------
        emoji : hikari.emojis.KnownCustomEmoji
            The object of the emoji to update in the cache.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.emojis.KnownCustomEmoji], typing.Optional[hikari.emojis.KnownCustomEmoji]]
            A tuple of the old cached emoji object if found (else `None`)
            and the new cached emoji object if it could be cached (else
            `None`).
        """

    @abc.abstractmethod
    def clear_stickers(self) -> CacheView[snowflakes.Snowflake, stickers.GuildSticker]:
        """Remove all the sticker objects from the cache.

        .. note::
            This will skip stickers that are being kept alive by a reference.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.stickers.GuildSticker]
            A cache view of sticker IDs to objects of the stickers that were
            removed from the cache.
        """

    @abc.abstractmethod
    def clear_stickers_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, stickers.GuildSticker]:
        """Remove the known custom emoji objects cached for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove the cached sticker objects for.

        .. note::
            This will skip stickers that are being kept alive by a reference.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.stickers.GuildSticker]
            A view of sticker IDs to objects of the stickers that were removed
            from the cache.
        """

    @abc.abstractmethod
    def delete_sticker(
        self, sticker: snowflakes.SnowflakeishOr[stickers.GuildSticker], /
    ) -> typing.Optional[stickers.GuildSticker]:
        """Remove a sticker from the cache.

        .. note::
            This will not delete stickers that are being kept alive by a reference.

        Parameters
        ----------
        sticker : hikari.snowflakes.SnowflakeishOr[hikari.stickers.GuildSticker]
            Object or ID of the sticker to remove from the cache.

        Returns
        -------
        typing.Optional[hikari.stickers.GuildSticker]
            The object of the sticker that was removed from the cache or
            `None`.
        """

    @abc.abstractmethod
    def set_sticker(self, sticker: stickers.GuildSticker, /) -> None:
        """Add a sticker to the cache.

        Parameters
        ----------
        sticker : hikari.stickers.GuildSticker
            The object of the sticker to add to the cache.
        """

    @abc.abstractmethod
    def clear_guilds(self) -> CacheView[snowflakes.Snowflake, guilds.GatewayGuild]:
        """Remove all the guild objects from the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.GatewayGuild]
            The cache view of guild IDs to guild objects that were removed from
            the cache.
        """

    @abc.abstractmethod
    def delete_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> typing.Optional[guilds.GatewayGuild]:
        """Remove a guild object from the cache.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove from the cache.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The object of the guild that was removed from the cache, will be
            `None` if not found.
        """

    @abc.abstractmethod
    def set_guild(self, guild: guilds.GatewayGuild, /) -> None:
        """Add a guild object to the cache.

        Parameters
        ----------
        guild : hikari.guilds.GatewayGuild
            The object of the guild to add to the cache.
        """

    @abc.abstractmethod
    def set_guild_availability(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], is_available: bool, /
    ) -> None:
        """Set whether a cached guild is available or not.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to set the availability for.
        is_available : bool
            The availability to set for the guild.
        """

    @abc.abstractmethod
    def update_guild(
        self, guild: guilds.GatewayGuild, /
    ) -> typing.Tuple[typing.Optional[guilds.GatewayGuild], typing.Optional[guilds.GatewayGuild]]:
        """Update a guild in the cache.

        Parameters
        ----------
        guild : hikari.guilds.GatewayGuild
            The object of the guild to update in the cache.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.guilds.GatewayGuild], typing.Optional[hikari.guilds.GatewayGuild]]
            A tuple of the old cached guild object if found (else `None`)
            and the object of the guild that was added to the cache if it could
            be added (else `None`).
        """

    @abc.abstractmethod
    def clear_guild_channels(self) -> CacheView[snowflakes.Snowflake, channels.PermissibleGuildChannel]:
        """Remove all guild channels from the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.PermissibleGuildChannel]
            A view of channel IDs to objects of the guild channels that were
            removed from the cache.
        """

    @abc.abstractmethod
    def clear_guild_channels_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, channels.PermissibleGuildChannel]:
        """Remove guild channels from the cache for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove cached channels for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.PermissibleGuildChannel]
            A view of channel IDs to objects of the guild channels that were
            removed from the cache.
        """

    @abc.abstractmethod
    def delete_guild_channel(
        self, channel: snowflakes.SnowflakeishOr[channels.PartialChannel], /
    ) -> typing.Optional[channels.PermissibleGuildChannel]:
        """Remove a guild channel from the cache.

        Parameters
        ----------
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            Object or ID of the guild channel to remove from the cache.

        Returns
        -------
        typing.Optional[hikari.channels.PermissibleGuildChannel]
            The object of the guild channel that was removed from the cache if
            found, else `None`.
        """

    @abc.abstractmethod
    def set_guild_channel(self, channel: channels.PermissibleGuildChannel, /) -> None:
        """Add a guild channel to the cache.

        Parameters
        ----------
        channel : hikari.channels.PermissibleGuildChannel
            The guild channel based object to add to the cache.
        """

    @abc.abstractmethod
    def update_guild_channel(
        self, channel: channels.PermissibleGuildChannel, /
    ) -> typing.Tuple[
        typing.Optional[channels.PermissibleGuildChannel], typing.Optional[channels.PermissibleGuildChannel]
    ]:
        """Update a guild channel in the cache.

        Parameters
        ----------
        channel : hikari.channels.PermissibleGuildChannel
            The object of the channel to update in the cache.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.channels.PermissibleGuildChannel], typing.Optional[hikari.channels.PermissibleGuildChannel]]
            A tuple of the old cached guild channel if found (else `None`)
            and the new cached guild channel if it could be cached
            (else `None`).
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    def clear_threads(self) -> CacheView[snowflakes.Snowflake, channels.GuildThreadChannel]:
        """Remove all thread channels from the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.GuildThreadChannel]
            A view of channel IDs to objects of the thread channels that were
            removed from the cache.
        """

    @abc.abstractmethod
    def clear_threads_for_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels.PartialChannel],
        /,
    ) -> CacheView[snowflakes.Snowflake, channels.GuildThreadChannel]:
        """Remove thread channels from the cache for a specific channel.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove cached threads for.
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            Object or ID of the channel to remove cached threads for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.GuildThreadChannel]
            A view of channel IDs to objects of the thread channels that were
            removed from the cache.
        """

    @abc.abstractmethod
    def clear_threads_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, channels.GuildThreadChannel]:
        """Remove thread channels from the cache for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove cached threads for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.GuildThreadChannel]
            A view of channel IDs to objects of the thread channels that were
            removed from the cache.
        """

    @abc.abstractmethod
    def delete_thread(
        self, thread: snowflakes.SnowflakeishOr[channels.PartialChannel], /
    ) -> typing.Optional[channels.GuildThreadChannel]:
        """Remove a thread channel from the cache.

        Parameters
        ----------
        thread : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            Object or ID of the thread to remove from the cache.

        Returns
        -------
        typing.Optional[hikari.channels.GuildThreadChannel]
            The object of the thread that was removed from the cache if
            found, else `builtins.None`.
        """

    @abc.abstractmethod
    def set_thread(self, channel: channels.GuildThreadChannel, /) -> None:
        """Add a thread channel to the cache.

        Parameters
        ----------
        channel : hikari.channels.GuildThreadChannel
            The thread channel based object to add to the cache.
        """

    @abc.abstractmethod
    def update_thread(
        self, thread: channels.GuildThreadChannel, /
    ) -> typing.Tuple[typing.Optional[channels.GuildThreadChannel], typing.Optional[channels.GuildThreadChannel]]:
        """Update a thread channel in the cache.

        Parameters
        ----------
        thread : hikari.channels.GuildThreadChannel
            The object of the thread channel to update in the cache.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.channels.GuildThreadChannel], typing.Optional[hikari.channels.GuildThreadChannel]]
            A tuple of the old cached thread channel if found (else `builtins.None`)
            and the new cached thread channel if it could be cached
            (else `builtins.None`).
        """

    @abc.abstractmethod
    def clear_invites(self) -> CacheView[str, invites.InviteWithMetadata]:
        """Remove all the invite objects from the cache.

        Returns
        -------
        CacheView[str, hikari.invites.InviteWithMetadata]
            A view of invite code strings to objects of the invites that were
            removed from the cache.
        """

    @abc.abstractmethod
    def clear_invites_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[str, invites.InviteWithMetadata]:
        """Remove the invite objects in the cache for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove invite objects for.

        Returns
        -------
        CacheView[str, hikari.invites.InviteWithMetadata]
            A view of invite code strings to objects of the invites that were
            removed from the cache for the specified guild.
        """

    @abc.abstractmethod
    def clear_invites_for_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels.PartialChannel],
        /,
    ) -> CacheView[str, invites.InviteWithMetadata]:
        """Remove the invite objects in the cache for a specific channel.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove invite objects for.
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            Object or ID of the channel to remove invite objects for.

        Returns
        -------
        CacheView[str, hikari.invites.InviteWithMetadata]
            A view of invite code strings to objects of the invites that were
            removed from the cache for the specified channel.
        """

    @abc.abstractmethod
    def delete_invite(
        self, code: typing.Union[invites.InviteCode, str], /
    ) -> typing.Optional[invites.InviteWithMetadata]:
        """Remove an invite object from the cache.

        Parameters
        ----------
        code : typing.Union[hikari.invites.InviteCode, str]
            Object or string code of the invite to remove from the cache.

        Returns
        -------
        typing.Optional[hikari.invites.InviteWithMetadata]
            The object of the invite that was removed from the cache if found,
            else `None`.
        """

    @abc.abstractmethod
    def set_invite(self, invite: invites.InviteWithMetadata, /) -> None:
        """Add an invite object to the cache.

        Parameters
        ----------
        invite : hikari.invites.InviteWithMetadata
            The object of the invite to add to the cache.
        """

    @abc.abstractmethod
    def update_invite(
        self, invite: invites.InviteWithMetadata, /
    ) -> typing.Tuple[typing.Optional[invites.InviteWithMetadata], typing.Optional[invites.InviteWithMetadata]]:
        """Update an invite in the cache.

        Parameters
        ----------
        invite : hikari.invites.InviteWithMetadata
            The object of the invite to update in the cache.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.invites.InviteWithMetadata], typing.Optional[hikari.invites.InviteWithMetadata]]
            A tuple of the old cached invite object if found (else
            `None`) and the new cached invite object if it could be
            cached (else `None`).
        """

    @abc.abstractmethod
    def delete_me(self) -> typing.Optional[users.OwnUser]:
        """Remove the own user object from the cache.

        Returns
        -------
        typing.Optional[hikari.users.OwnUser]
            The own user object that was removed from the cache if found,
            else `None`.
        """

    @abc.abstractmethod
    def set_me(self, user: users.OwnUser, /) -> None:
        """Set the own user object in the cache.

        Parameters
        ----------
        user : hikari.users.OwnUser
            The own user object to set in the cache.
        """

    @abc.abstractmethod
    def update_me(
        self, user: users.OwnUser, /
    ) -> typing.Tuple[typing.Optional[users.OwnUser], typing.Optional[users.OwnUser]]:
        """Update the own user entry in the cache.

        Parameters
        ----------
        user : hikari.users.OwnUser
            The own user object to update in the cache.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.users.OwnUser], typing.Optional[hikari.users.OwnUser]]
            A tuple of the old cached own user object if found (else
            `None`) and the new cached own user object if it could be
            cached, else `None`.
        """

    @abc.abstractmethod
    def clear_members(self) -> CacheView[snowflakes.Snowflake, CacheView[snowflakes.Snowflake, guilds.Member]]:
        """Remove all the guild members in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Member]]
            A view of guild IDs to views of user IDs to objects of the members
            that were removed from the cache.
        """

    @abc.abstractmethod
    def clear_members_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, guilds.Member]:
        """Remove the members for a specific guild from the cache.

        .. note::
            This will skip members that are being referenced by other entries in
            the cache; a matching voice state will keep a member entry alive.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove cached members for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Member]
            The view of user IDs to the member objects that were removed from
            the cache.
        """

    @abc.abstractmethod
    def delete_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> typing.Optional[guilds.Member]:
        """Remove a member object from the cache.

        .. note::
            You cannot delete a member entry that's being referenced by other
            entries in the cache; a matching voice state will keep a member
            entry alive.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove a member from the cache for.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user to remove a member from the cache for.

        Returns
        -------
        typing.Optional[hikari.guilds.Member]
            The object of the member that was removed from the cache if found,
            else `None`.
        """

    @abc.abstractmethod
    def set_member(self, member: guilds.Member, /) -> None:
        """Add a member object to the cache.

        Parameters
        ----------
        member : hikari.guilds.Member
            The object of the member to add to the cache.
        """

    @abc.abstractmethod
    def update_member(
        self, member: guilds.Member, /
    ) -> typing.Tuple[typing.Optional[guilds.Member], typing.Optional[guilds.Member]]:
        """Update a member in the cache.

        Parameters
        ----------
        member : hikari.guilds.Member
            The object of the member to update in the cache.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.guilds.Member], typing.Optional[hikari.guilds.Member]]
            A tuple of the old cached member object if found (else `None`)
            and the new cached member object if it could be cached (else
            `None`).
        """

    @abc.abstractmethod
    def clear_presences(
        self,
    ) -> CacheView[snowflakes.Snowflake, CacheView[snowflakes.Snowflake, presences.MemberPresence]]:
        """Remove all the presences in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, CacheView[hikari.snowflakes.Snowflake, hikari.presences.MemberPresence]]
            A view of guild IDs to views of user IDs to objects of the presences
            that were removed from the cache.
        """

    @abc.abstractmethod
    def clear_presences_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, presences.MemberPresence]:
        """Remove the presences in the cache for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove presences for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.presences.MemberPresence]
            A view of user IDs to objects of the presences that were removed
            from the cache for the specified guild.
        """

    @abc.abstractmethod
    def delete_presence(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> typing.Optional[presences.MemberPresence]:
        """Remove a presence from the cache.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove a presence for.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user to remove a presence for.

        Returns
        -------
        typing.Optional[hikari.presences.MemberPresence]
            The object of the presence that was removed from the cache if found,
            else `None`.
        """

    @abc.abstractmethod
    def set_presence(self, presence: presences.MemberPresence, /) -> None:
        """Add a presence object to the cache.

        Parameters
        ----------
        presence : hikari.presences.MemberPresence
            The object of the presence to add to the cache.
        """

    @abc.abstractmethod
    def update_presence(
        self, presence: presences.MemberPresence, /
    ) -> typing.Tuple[typing.Optional[presences.MemberPresence], typing.Optional[presences.MemberPresence]]:
        """Update a presence object in the cache.

        Parameters
        ----------
        presence : hikari.presences.MemberPresence
            The object of the presence to update in the cache.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.presences.MemberPresence], typing.Optional[hikari.presences.MemberPresence]]
            A tuple of the old cached invite object if found (else `None`
            and the new cached invite object if it could be cached ( else
            `None`).
        """

    @abc.abstractmethod
    def clear_roles(self) -> CacheView[snowflakes.Snowflake, guilds.Role]:
        """Remove all role objects from the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Role]
            A view of role IDs to objects of the roles that were removed from
            the cache.
        """

    @abc.abstractmethod
    def clear_roles_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, guilds.Role]:
        """Remove role objects from the cache for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove roles for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Role]
            A view of role IDs to objects of the roles that were removed from
            the cache for the specific guild.
        """

    @abc.abstractmethod
    def delete_role(self, role: snowflakes.SnowflakeishOr[guilds.PartialRole], /) -> typing.Optional[guilds.Role]:
        """Remove a role object form the cache.

        Parameters
        ----------
        role : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialRole]
            Object or ID of the role to remove from the cache.

        Returns
        -------
        typing.Optional[hikari.guilds.Role]
            The object of the role that was removed from the cache if found,
            else `None`.
        """

    @abc.abstractmethod
    def set_role(self, role: guilds.Role, /) -> None:
        """Add a role object to the cache.

        Parameters
        ----------
        role : hikari.guilds.Role
            The object of the role to add to the cache.
        """

    @abc.abstractmethod
    def update_role(
        self, role: guilds.Role, /
    ) -> typing.Tuple[typing.Optional[guilds.Role], typing.Optional[guilds.Role]]:
        """Update a role in the cache.

        Parameters
        ----------
        role : hikari.guilds.Role
            The object of the role to update in the cache.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.guilds.Role], typing.Optional[hikari.guilds.Role]]
            A tuple of the old cached role object if found (else `None`
            and the new cached role object if it could be cached (else
            `None`).
        """

    @abc.abstractmethod
    def clear_voice_states(self) -> CacheView[snowflakes.Snowflake, CacheView[snowflakes.Snowflake, voices.VoiceState]]:
        """Remove all voice state objects from the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, CacheView[hikari.snowflakes.Snowflake, hikari.voices.VoiceState]]
            A view of guild IDs to views of user IDs to objects of the voice
            states that were removed from the states.
        """

    @abc.abstractmethod
    def clear_voice_states_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, voices.VoiceState]:
        """Clear the voice state objects cached for a specific guild.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove cached voice states for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.voices.VoiceState]
            A view of user IDs to the voice state objects that were removed from
            the cache.
        """

    @abc.abstractmethod
    def clear_voice_states_for_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels.PartialChannel],
        /,
    ) -> CacheView[snowflakes.Snowflake, voices.VoiceState]:
        """Remove the voice state objects cached for a specific channel.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild to remove voice states for.
        channel : hikari.snowflakes.SnowflakeishOr[hikari.channels.PartialChannel]
            Object or ID of the channel to remove voice states for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.voices.VoiceState]
            A view of user IDs to objects of the voice state that were removed
            from the cache for the specified channel.
        """

    @abc.abstractmethod
    def delete_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> typing.Optional[voices.VoiceState]:
        """Remove a voice state object from the cache.

        Parameters
        ----------
        guild : hikari.snowflakes.SnowflakeishOr[hikari.guilds.PartialGuild]
            Object or ID of the guild the voice state to remove is related to.
        user : hikari.snowflakes.SnowflakeishOr[hikari.users.PartialUser]
            Object or ID of the user who the voice state to remove belongs to.

        Returns
        -------
        typing.Optional[hikari.voices.VoiceState]
            The object of the voice state that was removed from the cache if
            found, else `None`.
        """

    @abc.abstractmethod
    def set_voice_state(self, voice_state: voices.VoiceState, /) -> None:
        """Add a voice state object to the cache.

        Parameters
        ----------
        voice_state : hikari.voices.VoiceState
            The object of the voice state to add to the cache.
        """

    @abc.abstractmethod
    def update_voice_state(
        self, voice_state: voices.VoiceState, /
    ) -> typing.Tuple[typing.Optional[voices.VoiceState], typing.Optional[voices.VoiceState]]:
        """Update a voice state object in the cache.

        Parameters
        ----------
        voice_state : hikari.voices.VoiceState
            The object of the voice state to update in the cache.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.voices.VoiceState], typing.Optional[hikari.voices.VoiceState]]
            A tuple of the old cached voice state if found (else `None`)
            and the new cached voice state object if it could be cached
            (else `None`).
        """

    @abc.abstractmethod
    def clear_messages(self) -> CacheView[snowflakes.Snowflake, messages.Message]:
        """Remove all message objects from the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.messages.Message]
            A view of message objects that were removed from the cache.
        """

    @abc.abstractmethod
    def delete_message(
        self, message: snowflakes.SnowflakeishOr[messages.PartialMessage], /
    ) -> typing.Optional[messages.Message]:
        """Remove a message object from the cache.

        Parameters
        ----------
        message : hikari.snowflakes.SnowflakeishOr[hikari.messages.PartialMessage]
            Object or ID of the messages to remove the cache.

        Returns
        -------
        typing.Optional[hikari.messages.Message]
            The object of the message that was removed from the cache if found,
            else `None`.
        """

    @abc.abstractmethod
    def set_message(self, message: messages.Message, /) -> None:
        """Add a message object to the cache.

        Parameters
        ----------
        message : hikari.messages.Message
            The object of the message to add to the cache.
        """

    @abc.abstractmethod
    def update_message(
        self, message: typing.Union[messages.PartialMessage, messages.Message], /
    ) -> typing.Tuple[typing.Optional[messages.Message], typing.Optional[messages.Message]]:
        """Update a message in the cache.

        Parameters
        ----------
        message : typing.Union[hikari.messages.PartialMessage, hikari.messages.Message]
            The object of the message to update in the cache.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.messages.Message], typing.Optional[hikari.messages.Message]]
            A tuple of the old cached message object if found (else `None`)
            and the new cached message object if it could be cached (else
            `None`).
        """
