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

__all__: typing.Sequence[str] = ("Cache", "CacheView", "MutableCache")

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

    This can be treated as a normal [`typing.Mapping`][] but with some special methods.
    """

    __slots__: typing.Sequence[str] = ()

    @typing.overload
    @abc.abstractmethod
    def get_item_at(self, index: int, /) -> _ValueT: ...

    @typing.overload
    @abc.abstractmethod
    def get_item_at(self, index: slice, /) -> typing.Sequence[_ValueT]: ...

    @abc.abstractmethod
    def get_item_at(self, index: slice | int, /) -> _ValueT | typing.Sequence[_ValueT]:
        """Get an item at a specific position or slice."""


class Cache(abc.ABC):
    """Interface describing the operations a cache component should provide.

    This will be used by the gateway to cache specific types of
    objects that the application should attempt to remember for later, depending
    on how this is implemented. The requirement for this stems from the
    assumption by Discord that gateway bot applications will maintain some form of
    "memory" of the events that occur.

    The implementation may choose to use a simple in-memory collection of
    objects, or may decide to use a distributed system such as a Redis or Valkey cache
    for cross-process bots.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def settings(self) -> config.CacheSettings:
        """Get the configured settings for this cache."""

    @abc.abstractmethod
    def get_dm_channel_id(self, user: snowflakes.SnowflakeishOr[users.PartialUser], /) -> snowflakes.Snowflake | None:
        """Get the DM channel ID for a user from the cache.

        Parameters
        ----------
        user
            Object or ID of the user to get the DM channel ID for.

        Returns
        -------
        typing.Optional[hikari.snowflakes.Snowflake]
            The DM channel ID for the specified user if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_dm_channel_ids_view(self) -> CacheView[snowflakes.Snowflake, snowflakes.Snowflake]:
        """Get a view of the DM channel IDs in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.snowflakes.Snowflake]
            A view of user IDs to DM channel IDs.
        """

    @abc.abstractmethod
    def get_emoji(self, emoji: snowflakes.SnowflakeishOr[emojis.CustomEmoji], /) -> emojis.KnownCustomEmoji | None:
        """Get a known custom emoji from the cache.

        Parameters
        ----------
        emoji
            Object or ID of the emoji to get.

        Returns
        -------
        typing.Optional[hikari.emojis.KnownCustomEmoji]
            The known custom emoji object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_emojis_view(self) -> CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        """Get a view of the known custom emojis in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.emojis.KnownCustomEmoji]
            A view of known custom emoji IDs to objects.
        """

    @abc.abstractmethod
    def get_emojis_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        """Get a view of the known custom emojis in the cache for a specific guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to get the emojis for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.emojis.KnownCustomEmoji]
            A view of known custom emoji IDs to objects for the specified guild.
        """

    @abc.abstractmethod
    def get_sticker(self, sticker: snowflakes.SnowflakeishOr[stickers.GuildSticker], /) -> stickers.GuildSticker | None:
        """Get a guild sticker from the cache.

        Parameters
        ----------
        sticker
            Object or ID of the sticker to get.

        Returns
        -------
        typing.Optional[hikari.stickers.GuildSticker]
            The guild sticker object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_stickers_view(self) -> CacheView[snowflakes.Snowflake, stickers.GuildSticker]:
        """Get a view of the guild stickers in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.stickers.GuildSticker]
            A view of guild sticker IDs to objects.
        """

    @abc.abstractmethod
    def get_stickers_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, stickers.GuildSticker]:
        """Get a view of the guild stickers in the cache for a specific guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to get the stickers for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.stickers.GuildSticker]
            A view of guild sticker IDs to objects for the specified guild.
        """

    @abc.abstractmethod
    def get_guild(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /) -> guilds.GatewayGuild | None:
        """Get a guild from the cache.

        !!! warning
            This may return a guild regardless of whether it is available or
            not. To only query available guilds, use [`hikari.api.cache.Cache.get_available_guild`][]
            instead. Likewise, to only query unavailable guilds, use
            [`hikari.api.cache.Cache.get_unavailable_guild`][].

        Parameters
        ----------
        guild
            Object or ID of the guild to get.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The guild object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_available_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> guilds.GatewayGuild | None:
        """Get an available guild from the cache.

        Parameters
        ----------
        guild
            Object or ID of the guild to get.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The guild object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_unavailable_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> guilds.GatewayGuild | None:
        """Get an unavailable guild from the cache.

        !!! note
            Unlike [`hikari.api.cache.Cache.get_available_guild`][], any object returned by this
            method will likely be out of date and inaccurate as they are
            considered unavailable, meaning that we are not receiving gateway
            events for this guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to get.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The guild object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_guilds_view(self) -> CacheView[snowflakes.Snowflake, guilds.GatewayGuild]:
        """Get a view of the guilds in the cache (regardless of availability).

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.GatewayGuild]
            A view of guild IDs to objects.
        """

    @abc.abstractmethod
    def get_available_guilds_view(self) -> CacheView[snowflakes.Snowflake, guilds.GatewayGuild]:
        """Get a view of the available guilds in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.GatewayGuild]
            A view of guild IDs to objects.
        """

    @abc.abstractmethod
    def get_unavailable_guilds_view(self) -> CacheView[snowflakes.Snowflake, guilds.GatewayGuild]:
        """Get a view of the unavailable guilds in the cache.

        !!! note
            Unlike [`hikari.api.cache.Cache.get_available_guilds_view`][], any objects returned by
            this method will likely be out of date and inaccurate as they are
            considered unavailable, meaning that we are not receiving gateway
            events for this guild.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.GatewayGuild]
            A view of guild IDs to objects.
        """

    @abc.abstractmethod
    def get_guild_channel(
        self, channel: snowflakes.SnowflakeishOr[channels.PartialChannel], /
    ) -> channels.PermissibleGuildChannel | None:
        """Get a guild channel from the cache.

        Parameters
        ----------
        channel
            Object or ID of the guild channel to get.

        Returns
        -------
        typing.Optional[hikari.channels.PermissibleGuildChannel]
            The guild channel object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_guild_channels_view(self) -> CacheView[snowflakes.Snowflake, channels.PermissibleGuildChannel]:
        """Get a view of the guild channels in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.PermissibleGuildChannel]
            A view of guild channel IDs to objects.
        """

    @abc.abstractmethod
    def get_guild_channels_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, channels.PermissibleGuildChannel]:
        """Get a view of the guild channels in the cache for a specific guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to get the channels for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.PermissibleGuildChannel]
            A view of guild channel IDs to objects for the specified guild.
        """

    @abc.abstractmethod
    def get_thread(
        self, thread: snowflakes.SnowflakeishOr[channels.PartialChannel], /
    ) -> channels.GuildThreadChannel | None:
        """Get a thread channel from the cache.

        Parameters
        ----------
        thread
            Object or ID of the thread to get.

        Returns
        -------
        typing.Optional[hikari.channels.GuildThreadChannel]
            The thread channel object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_threads_view(self) -> CacheView[snowflakes.Snowflake, channels.GuildThreadChannel]:
        """Get a view of the thread channels in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.GuildThreadChannel]
            A view of thread channel IDs to objects.
        """

    @abc.abstractmethod
    def get_threads_view_for_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels.PartialChannel],
        /,
    ) -> CacheView[snowflakes.Snowflake, channels.GuildThreadChannel]:
        """Get a view of the thread channels in the cache for a specific guild channel.

        Parameters
        ----------
        guild
            Object or ID of the guild to get the thread channels for.
        channel
            Object or ID of the guild channel to get the thread channels for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.GuildThreadChannel]
            A view of thread channel IDs to objects for the specified guild channel.
        """

    @abc.abstractmethod
    def get_threads_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, channels.GuildThreadChannel]:
        """Get a view of the thread channels in the cache for a specific guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to get the thread channels for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.GuildThreadChannel]
            A view of thread channel IDs to objects for the specified guild.
        """

    @abc.abstractmethod
    def get_invite(self, code: invites.InviteCode | str, /) -> invites.InviteWithMetadata | None:
        """Get an invite from the cache.

        Parameters
        ----------
        code
            Object or string code of the invite to get.

        Returns
        -------
        typing.Optional[hikari.invites.InviteWithMetadata]
            The invite object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_invites_view(self) -> CacheView[str, invites.InviteWithMetadata]:
        """Get a view of the invites in the cache.

        Returns
        -------
        CacheView[str, hikari.invites.InviteWithMetadata]
            A view of invite string codes to objects.
        """

    @abc.abstractmethod
    def get_invites_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[str, invites.InviteWithMetadata]:
        """Get a view of the invites in the cache for a specific guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to get the invites for.

        Returns
        -------
        CacheView[str, hikari.invites.InviteWithMetadata]
            A view of invite string codes to objects for the specified guild.
        """

    @abc.abstractmethod
    def get_invites_view_for_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels.PartialChannel],
        /,
    ) -> CacheView[str, invites.InviteWithMetadata]:
        """Get a view of the invites in the cache for a specific channel.

        Parameters
        ----------
        guild
            Object or ID of the guild to get the invites for.
        channel
            Object or ID of the channel to get the invites for.

        Returns
        -------
        CacheView[str, invites.InviteWithMetadata]
            A view of invite string codes to objects for the specified channel.
        """

    @abc.abstractmethod
    def get_me(self) -> users.OwnUser | None:
        """Get the own user from the cache.

        Returns
        -------
        typing.Optional[hikari.users.OwnUser]
            The own user object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> guilds.Member | None:
        """Get a member from the cache.

        Parameters
        ----------
        guild
            Object or ID of the guild to get the member for.
        user
            Object or ID of the user to get the member for.

        Returns
        -------
        typing.Optional[hikari.guilds.Member]
            The member object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_members_view(self) -> CacheView[snowflakes.Snowflake, CacheView[snowflakes.Snowflake, guilds.Member]]:
        """Get a view of the members in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Member]]
            A view of guild IDs to views of user IDs to member objects.
        """

    @abc.abstractmethod
    def get_members_view_for_guild(
        self, guild_id: snowflakes.Snowflakeish, /
    ) -> CacheView[snowflakes.Snowflake, guilds.Member]:
        """Get a view of the members in the cache for a specific guild.

        Parameters
        ----------
        guild_id
            The ID of the guild to get the members for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Member]
            A view of user IDs to member objects for the specified guild.
        """

    @abc.abstractmethod
    def get_message(self, message: snowflakes.SnowflakeishOr[messages.PartialMessage], /) -> messages.Message | None:
        """Get a message from the cache.

        Parameters
        ----------
        message
            Object or ID of the message to get.

        Returns
        -------
        typing.Optional[hikari.messages.Message]
            The message object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_messages_view(self) -> CacheView[snowflakes.Snowflake, messages.Message]:
        """Get a view of the messages in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.messages.Message]
            A view of message IDs to objects.
        """

    @abc.abstractmethod
    def get_presence(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> presences.MemberPresence | None:
        """Get a presence from the cache.

        Parameters
        ----------
        guild
            Object or ID of the guild to get the presence for.
        user
            Object or ID of the user to get the presence for.

        Returns
        -------
        typing.Optional[hikari.presences.MemberPresence]
            The presence object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_presences_view(
        self,
    ) -> CacheView[snowflakes.Snowflake, CacheView[snowflakes.Snowflake, presences.MemberPresence]]:
        """Get a view of the presences in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, CacheView[hikari.snowflakes.Snowflake]]
            A view of guild IDs to views of user IDs to presence objects.
        """

    @abc.abstractmethod
    def get_presences_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, presences.MemberPresence]:
        """Get a view of the presences in the cache for a specific guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to get the presences for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.presences.MemberPresence]
            A view of user IDs to presence objects for the specified guild.
        """

    @abc.abstractmethod
    def get_role(self, role: snowflakes.SnowflakeishOr[guilds.PartialRole], /) -> guilds.Role | None:
        """Get a role from the cache.

        Parameters
        ----------
        role
            Object or ID of the role to get.

        Returns
        -------
        typing.Optional[hikari.guilds.Role]
            The role object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_roles_view(self) -> CacheView[snowflakes.Snowflake, guilds.Role]:
        """Get a view of the roles in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Role]
            A view of role IDs to objects.
        """

    @abc.abstractmethod
    def get_roles_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, guilds.Role]:
        """Get a view of the roles in the cache for a specific guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to get the roles for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Role]
            A view of role IDs to objects for the specified guild.
        """

    @abc.abstractmethod
    def get_user(self, user: snowflakes.SnowflakeishOr[users.PartialUser], /) -> users.User | None:
        """Get a user from the cache.

        Parameters
        ----------
        user
            Object or ID of the user to get.

        Returns
        -------
        typing.Optional[hikari.users.User]
            The user object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_users_view(self) -> CacheView[snowflakes.Snowflake, users.User]:
        """Get a view of the users in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.users.User]
            A view of user IDs to objects.
        """

    @abc.abstractmethod
    def get_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> voices.VoiceState | None:
        """Get a voice state from the cache.

        Parameters
        ----------
        guild
            Object or ID of the guild to get the voice state for.
        user
            Object or ID of the user to get the voice state for.

        Returns
        -------
        typing.Optional[hikari.voices.VoiceState]
            The voice state object if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def get_voice_states_view(
        self,
    ) -> CacheView[snowflakes.Snowflake, CacheView[snowflakes.Snowflake, voices.VoiceState]]:
        """Get a view of all voice states in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, CacheView[hikari.snowflakes.Snowflake, hikari.voices.VoiceState]]
            A view of guild IDs to views of user IDs to voice state objects.
        """

    @abc.abstractmethod
    def get_voice_states_view_for_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels.PartialChannel],
        /,
    ) -> CacheView[snowflakes.Snowflake, voices.VoiceState]:
        """Get a view of the voice states for a specific channel.

        Parameters
        ----------
        guild
            Object or ID of the guild to get the voice states for.
        channel
            Object or ID of the channel to get the voice states for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.voices.VoiceState]
            A view of user IDs to voice state objects for the specified channel.
        """

    @abc.abstractmethod
    def get_voice_states_view_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, voices.VoiceState]:
        """Get a view of the voice states for a specific guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to get the voice states for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.voices.VoiceState]
            A view of user IDs to voice state objects for the specified guild.
        """


class MutableCache(Cache, abc.ABC):
    """Cache that exposes read-only operations as well as mutation operations.

    This is only exposed to internal components. There is no guarantee the
    user-facing cache will provide these methods or not.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def clear(self) -> None:
        """Clear the entire cache."""

    @abc.abstractmethod
    def clear_dm_channel_ids(self) -> CacheView[snowflakes.Snowflake, snowflakes.Snowflake]:
        """Remove all the DM channel IDs from the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.snowflakes.Snowflake]
            A view of user IDs to DM channel IDs that were removed.
        """

    @abc.abstractmethod
    def delete_dm_channel_id(
        self, user: snowflakes.SnowflakeishOr[users.PartialUser], /
    ) -> snowflakes.Snowflake | None:
        """Remove a DM channel ID from the cache.

        Parameters
        ----------
        user
            Object or ID of the user to remove the DM channel ID for.

        Returns
        -------
        typing.Optional[hikari.snowflakes.Snowflake]
            The DM channel ID that was removed if found, otherwise [`None`][].
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
        user
            Object or ID of the user to add a DM channel ID for.
        channel
            Object or ID of the DM channel to add.
        """

    @abc.abstractmethod
    def clear_emojis(self) -> CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        """Remove all the known custom emojis from the cache.

        !!! note
            This will not remove emojis that are being kept alive by a reference
            on a presence entry.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.emojis.KnownCustomEmoji]
            A view of known custom emoji IDs to objects that were removed.
        """

    @abc.abstractmethod
    def clear_emojis_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        """Remove all the known custom emojis from the cache for a specific guild.

        !!! note
            This will not remove emojis that are being kept alive by a reference
            on a presence entry.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove the emojis for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.emojis.KnownCustomEmoji]
            A view of known custom emoji IDs to objects that were removed.
        """

    @abc.abstractmethod
    def delete_emoji(self, emoji: snowflakes.SnowflakeishOr[emojis.CustomEmoji], /) -> emojis.KnownCustomEmoji | None:
        """Remove a known custom emoji from the cache.

        !!! note
            This will not remove emojis that are being kept alive by a reference
            on a presence entry.

        Parameters
        ----------
        emoji
            Object or ID of the emoji to remove.

        Returns
        -------
        typing.Optional[hikari.emojis.KnownCustomEmoji]
            The known custom emoji object that was removed if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def set_emoji(self, emoji: emojis.KnownCustomEmoji, /) -> None:
        """Add a known custom emoji to the cache.

        Parameters
        ----------
        emoji
            The emoji object to add.
        """

    @abc.abstractmethod
    def update_emoji(
        self, emoji: emojis.KnownCustomEmoji, /
    ) -> tuple[emojis.KnownCustomEmoji | None, emojis.KnownCustomEmoji | None]:
        """Update a known custom emoji in the cache.

        Parameters
        ----------
        emoji
            The emoji object to update.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.emojis.KnownCustomEmoji], typing.Optional[hikari.emojis.KnownCustomEmoji]]
            A tuple of the old emoji object that was cached if found (otherwise [`None`][])
            and the new emoji object if it could be cached (otherwise [`None`][]).
        """

    @abc.abstractmethod
    def clear_stickers(self) -> CacheView[snowflakes.Snowflake, stickers.GuildSticker]:
        """Remove all the stickers from the cache.

        !!! note
            This will not remove stickers that are being kept alive by a reference.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.stickers.GuildSticker]
            A view of sticker IDs to objects that were removed.
        """

    @abc.abstractmethod
    def clear_stickers_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, stickers.GuildSticker]:
        """Remove all the known custom emojis from the cache for a specific guild.

        !!! note
            This will not remove stickers that are being kept alive by a reference.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove the stickers for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.stickers.GuildSticker]
            A view of sticker IDs to objects that were removed.
        """

    @abc.abstractmethod
    def delete_sticker(
        self, sticker: snowflakes.SnowflakeishOr[stickers.GuildSticker], /
    ) -> stickers.GuildSticker | None:
        """Remove a sticker from the cache.

        !!! note
            This will not remove stickers that are being kept alive by a reference.

        Parameters
        ----------
        sticker
            Object or ID of the sticker to remove.

        Returns
        -------
        typing.Optional[hikari.stickers.GuildSticker]
            The sticker object that was removed if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def set_sticker(self, sticker: stickers.GuildSticker, /) -> None:
        """Add a sticker to the cache.

        Parameters
        ----------
        sticker
            The sticker object to add.
        """

    @abc.abstractmethod
    def clear_guilds(self) -> CacheView[snowflakes.Snowflake, guilds.GatewayGuild]:
        """Remove all the guilds from the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.GatewayGuild]
            A view of guild IDs to objects that were removed.
        """

    @abc.abstractmethod
    def delete_guild(self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /) -> guilds.GatewayGuild | None:
        """Remove a guild from the cache.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove.

        Returns
        -------
        typing.Optional[hikari.guilds.GatewayGuild]
            The guild object that was removed from the cache if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def set_guild(self, guild: guilds.GatewayGuild, /) -> None:
        """Add a guild to the cache.

        Parameters
        ----------
        guild
            The guild object to add.
        """

    @abc.abstractmethod
    def set_guild_availability(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        is_available: bool,  # noqa: FBT001 - Boolean-typed positional argument
        /,
    ) -> None:
        """Set whether a guild is available or not in the cache.

        Parameters
        ----------
        guild
            Object or ID of the guild to set the availability for.
        is_available
            The availability to set for the guild.
        """

    @abc.abstractmethod
    def update_guild(
        self, guild: guilds.GatewayGuild, /
    ) -> tuple[guilds.GatewayGuild | None, guilds.GatewayGuild | None]:
        """Update a guild in the cache.

        Parameters
        ----------
        guild
            The guild object to update.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.guilds.GatewayGuild], typing.Optional[hikari.guilds.GatewayGuild]]
            A tuple of the old guild object that was cached if found (otherwise [`None`][])
            and the new guild object if it could be cached (otherwise [`None`][]).
        """

    @abc.abstractmethod
    def clear_guild_channels(self) -> CacheView[snowflakes.Snowflake, channels.PermissibleGuildChannel]:
        """Remove all the guild channels from the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.PermissibleGuildChannel]
            A view of guild channel IDs to objects that were removed.
        """

    @abc.abstractmethod
    def clear_guild_channels_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, channels.PermissibleGuildChannel]:
        """Remove all the guild channels from the cache for a specific guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove the channels for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.PermissibleGuildChannel]
            A view of guild channel IDs to objects that were removed.
        """

    @abc.abstractmethod
    def delete_guild_channel(
        self, channel: snowflakes.SnowflakeishOr[channels.PartialChannel], /
    ) -> channels.PermissibleGuildChannel | None:
        """Remove a guild channel from the cache.

        Parameters
        ----------
        channel
            Object or ID of the guild channel to remove.

        Returns
        -------
        typing.Optional[hikari.channels.PermissibleGuildChannel]
            The guild channel object that was removed if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def set_guild_channel(self, channel: channels.PermissibleGuildChannel, /) -> None:
        """Add a guild channel to the cache.

        Parameters
        ----------
        channel
            The guild channel object to add.
        """

    @abc.abstractmethod
    def update_guild_channel(
        self, channel: channels.PermissibleGuildChannel, /
    ) -> tuple[channels.PermissibleGuildChannel | None, channels.PermissibleGuildChannel | None]:
        """Update a guild channel in the cache.

        Parameters
        ----------
        channel
            The guild channel object to update.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.channels.PermissibleGuildChannel], typing.Optional[hikari.channels.PermissibleGuildChannel]]
            A tuple of the old guild channel object that was cached if found (otherwise [`None`][])
            and the new guild channel object if it could be cached (otherwise [`None`][]).
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    def clear_threads(self) -> CacheView[snowflakes.Snowflake, channels.GuildThreadChannel]:
        """Remove all the thread channels from the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.GuildThreadChannel]
            A view of thread channel IDs to objects that were removed.
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
        guild
            Object or ID of the guild to remove the threads for.
        channel
            Object or ID of the channel to remove the threads for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.GuildThreadChannel]
            A view of thread channel IDs to objects that were removed.
        """

    @abc.abstractmethod
    def clear_threads_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, channels.GuildThreadChannel]:
        """Remove thread channels from the cache for a specific guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove the threads for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.channels.GuildThreadChannel]
            A view of thread channel IDs to objects that were removed.
        """

    @abc.abstractmethod
    def delete_thread(
        self, thread: snowflakes.SnowflakeishOr[channels.PartialChannel], /
    ) -> channels.GuildThreadChannel | None:
        """Remove a thread channel from the cache.

        Parameters
        ----------
        thread
            Object or ID of the thread to remove.

        Returns
        -------
        typing.Optional[hikari.channels.GuildThreadChannel]
            The thread object removed if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def set_thread(self, channel: channels.GuildThreadChannel, /) -> None:
        """Add a thread channel to the cache.

        Parameters
        ----------
        channel
            The thread channel object to add.
        """

    @abc.abstractmethod
    def update_thread(
        self, thread: channels.GuildThreadChannel, /
    ) -> tuple[channels.GuildThreadChannel | None, channels.GuildThreadChannel | None]:
        """Update a thread channel in the cache.

        Parameters
        ----------
        thread
            The object of the thread channel to update.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.channels.GuildThreadChannel], typing.Optional[hikari.channels.GuildThreadChannel]]
            A tuple of the old thread channel object that was cached if found (otherwise [`None`][])
            and the new thread channel object if it could be cached (otherwise [`None`][]).
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    def clear_invites(self) -> CacheView[str, invites.InviteWithMetadata]:
        """Remove all the invites from the cache.

        Returns
        -------
        CacheView[str, hikari.invites.InviteWithMetadata]
            A view of invite code strings to objects that were removed.
        """

    @abc.abstractmethod
    def clear_invites_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[str, invites.InviteWithMetadata]:
        """Remove all the invites from the cache for a specific guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove invites for.

        Returns
        -------
        CacheView[str, hikari.invites.InviteWithMetadata]
            A view of invite code strings to objects that were removed for the specified guild.
        """

    @abc.abstractmethod
    def clear_invites_for_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels.PartialChannel],
        /,
    ) -> CacheView[str, invites.InviteWithMetadata]:
        """Remove all the invites from the cache for a specific channel.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove invites for.
        channel
            Object or ID of the channel to remove invites for.

        Returns
        -------
        CacheView[str, hikari.invites.InviteWithMetadata]
            A view of invite code strings to objects that were removed for the specified channel.
        """

    @abc.abstractmethod
    def delete_invite(self, code: invites.InviteCode | str, /) -> invites.InviteWithMetadata | None:
        """Remove an invite from the cache.

        Parameters
        ----------
        code
            Object or string code of the invite to remove.

        Returns
        -------
        typing.Optional[hikari.invites.InviteWithMetadata]
            The invite object removed from the cache if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def set_invite(self, invite: invites.InviteWithMetadata, /) -> None:
        """Add an invite to the cache.

        Parameters
        ----------
        invite
            The object of the invite to add.
        """

    @abc.abstractmethod
    def update_invite(
        self, invite: invites.InviteWithMetadata, /
    ) -> tuple[invites.InviteWithMetadata | None, invites.InviteWithMetadata | None]:
        """Update an invite in the cache.

        Parameters
        ----------
        invite
            The object of the invite to update.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.invites.InviteWithMetadata], typing.Optional[hikari.invites.InviteWithMetadata]]
            A tuple of the old invite object that was cached if found (otherwise [`None`][])
            and the new  invite object if it could be cached (otherwise [`None`][]).
        """  # noqa: E501 - Line too long

    @abc.abstractmethod
    def delete_me(self) -> users.OwnUser | None:
        """Remove the own user from the cache.

        Returns
        -------
        typing.Optional[hikari.users.OwnUser]
            The own user object that was removed if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def set_me(self, user: users.OwnUser, /) -> None:
        """Set the own user in the cache.

        Parameters
        ----------
        user
            The own user object to set.
        """

    @abc.abstractmethod
    def update_me(self, user: users.OwnUser, /) -> tuple[users.OwnUser | None, users.OwnUser | None]:
        """Update the own user in the cache.

        Parameters
        ----------
        user
            The own user object to update.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.users.OwnUser], typing.Optional[hikari.users.OwnUser]]
            A tuple of the old own user object that was cached if found (otherwise [`None`][])
            and the new own user object if it could be cached, otherwise [`None`][].
        """

    @abc.abstractmethod
    def clear_members(self) -> CacheView[snowflakes.Snowflake, CacheView[snowflakes.Snowflake, guilds.Member]]:
        """Remove all the guild members in the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Member]]
            A view of guild IDs to views of user IDs to member objects that were removed from the cache.
        """

    @abc.abstractmethod
    def clear_members_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, guilds.Member]:
        """Remove all the members from the cache for a specific guild.

        !!! note
            This will not remove members that are being referenced by other entries in
            the cache; a matching voice state will keep a member entry alive.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove the members for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Member]
            A view of user IDs to the member objects that were removed.
        """

    @abc.abstractmethod
    def delete_member(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> guilds.Member | None:
        """Remove a member from the cache.

        !!! note
            This will not remove a member that is being referenced by other entries in
            the cache; a matching voice state will keep a member entry alive.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove a member for.
        user
            Object or ID of the user to remove a member for.

        Returns
        -------
        typing.Optional[hikari.guilds.Member]
            The member object that was removed if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def set_member(self, member: guilds.Member, /) -> None:
        """Add a member to the cache.

        Parameters
        ----------
        member
            The object of the member to add.
        """

    @abc.abstractmethod
    def update_member(self, member: guilds.Member, /) -> tuple[guilds.Member | None, guilds.Member | None]:
        """Update a member in the cache.

        Parameters
        ----------
        member
            The object of the member to update.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.guilds.Member], typing.Optional[hikari.guilds.Member]]
            A tuple of the old member object that was cached if found (otherwise [`None`][])
            and the new member object if it could be cached (otherwise [`None`][]).
        """

    @abc.abstractmethod
    def clear_presences(
        self,
    ) -> CacheView[snowflakes.Snowflake, CacheView[snowflakes.Snowflake, presences.MemberPresence]]:
        """Remove all the presences from the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, CacheView[hikari.snowflakes.Snowflake, hikari.presences.MemberPresence]]
            A view of guild IDs to views of user IDs to presence objects that were removed.
        """

    @abc.abstractmethod
    def clear_presences_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, presences.MemberPresence]:
        """Remove all the presences in the cache for a specific guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove presences for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.presences.MemberPresence]
            A view of user IDs to presence objects that were removed for the specified guild.
        """

    @abc.abstractmethod
    def delete_presence(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> presences.MemberPresence | None:
        """Remove a presence from the cache.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove a presence for.
        user
            Object or ID of the user to remove a presence for.

        Returns
        -------
        typing.Optional[hikari.presences.MemberPresence]
            The presence object that was removed if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def set_presence(self, presence: presences.MemberPresence, /) -> None:
        """Add a presence to the cache.

        Parameters
        ----------
        presence
            The object of the presence to add.
        """

    @abc.abstractmethod
    def update_presence(
        self, presence: presences.MemberPresence, /
    ) -> tuple[presences.MemberPresence | None, presences.MemberPresence | None]:
        """Update a presence in the cache.

        Parameters
        ----------
        presence
            The object of the presence to update.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.presences.MemberPresence], typing.Optional[hikari.presences.MemberPresence]]
            A tuple of the old invite object that was cached if found (otherwise [`None`][]
            and the new invite object if it could be cached (otherwise [`None`][]).
        """

    @abc.abstractmethod
    def clear_roles(self) -> CacheView[snowflakes.Snowflake, guilds.Role]:
        """Remove all the roles from the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Role]
            A view of role IDs to objects that were removed.
        """

    @abc.abstractmethod
    def clear_roles_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, guilds.Role]:
        """Remove all the roles from the cache for a specific guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove roles for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.guilds.Role]
            A view of role IDs to objects that were removed for the specific guild.
        """

    @abc.abstractmethod
    def delete_role(self, role: snowflakes.SnowflakeishOr[guilds.PartialRole], /) -> guilds.Role | None:
        """Remove a role from the cache.

        Parameters
        ----------
        role
            Object or ID of the role to remove.

        Returns
        -------
        typing.Optional[hikari.guilds.Role]
            The role object that was removed if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def set_role(self, role: guilds.Role, /) -> None:
        """Add a role to the cache.

        Parameters
        ----------
        role
            Object of the role to add.
        """

    @abc.abstractmethod
    def update_role(self, role: guilds.Role, /) -> tuple[guilds.Role | None, guilds.Role | None]:
        """Update a role in the cache.

        Parameters
        ----------
        role
            Object of the role to update.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.guilds.Role], typing.Optional[hikari.guilds.Role]]
            A tuple of the old role object that was cached if found (otherwise [`None`][]
            and the new role object if it could be cached (otherwise [`None`][]).
        """

    @abc.abstractmethod
    def clear_voice_states(self) -> CacheView[snowflakes.Snowflake, CacheView[snowflakes.Snowflake, voices.VoiceState]]:
        """Remove all the voice states from the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, CacheView[hikari.snowflakes.Snowflake, hikari.voices.VoiceState]]
            A view of guild IDs to views of user IDs to voice state objects that were removed.
        """

    @abc.abstractmethod
    def clear_voice_states_for_guild(
        self, guild: snowflakes.SnowflakeishOr[guilds.PartialGuild], /
    ) -> CacheView[snowflakes.Snowflake, voices.VoiceState]:
        """Remove all the voice states from the cache for a specific guild.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove the voice states for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.voices.VoiceState]
            A view of user IDs to voice state objects that were removed.
        """

    @abc.abstractmethod
    def clear_voice_states_for_channel(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        channel: snowflakes.SnowflakeishOr[channels.PartialChannel],
        /,
    ) -> CacheView[snowflakes.Snowflake, voices.VoiceState]:
        """Remove the voice states from the cache for a specific channel.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove voice states for.
        channel
            Object or ID of the channel to remove voice states for.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.voices.VoiceState]
            A view of user IDs to voice state objects that were removed for the specified channel.
        """

    @abc.abstractmethod
    def delete_voice_state(
        self,
        guild: snowflakes.SnowflakeishOr[guilds.PartialGuild],
        user: snowflakes.SnowflakeishOr[users.PartialUser],
        /,
    ) -> voices.VoiceState | None:
        """Remove a voice state from the cache.

        Parameters
        ----------
        guild
            Object or ID of the guild to remove the voice state for.
        user
            Object or ID of the user who to remove the voice state for.

        Returns
        -------
        typing.Optional[hikari.voices.VoiceState]
            The object of the voice state removed if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def set_voice_state(self, voice_state: voices.VoiceState, /) -> None:
        """Add a voice state to the cache.

        Parameters
        ----------
        voice_state
            Object of the voice state to add.
        """

    @abc.abstractmethod
    def update_voice_state(
        self, voice_state: voices.VoiceState, /
    ) -> tuple[voices.VoiceState | None, voices.VoiceState | None]:
        """Update a voice state in the cache.

        Parameters
        ----------
        voice_state
            Object of the voice state to update.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.voices.VoiceState], typing.Optional[hikari.voices.VoiceState]]
            A tuple of the old voice state object that was cached if found (otherwise [`None`][])
            and the new voice state object if it could be cached (otherwise [`None`][]).
        """

    @abc.abstractmethod
    def clear_messages(self) -> CacheView[snowflakes.Snowflake, messages.Message]:
        """Remove all the messages from the cache.

        Returns
        -------
        CacheView[hikari.snowflakes.Snowflake, hikari.messages.Message]
            A view of message IDs to objects that were removed.
        """

    @abc.abstractmethod
    def delete_message(self, message: snowflakes.SnowflakeishOr[messages.PartialMessage], /) -> messages.Message | None:
        """Remove a message from the cache.

        Parameters
        ----------
        message
            Object or ID of the messages to remove the cache.

        Returns
        -------
        typing.Optional[hikari.messages.Message]
            The message object that was removed if found, otherwise [`None`][].
        """

    @abc.abstractmethod
    def set_message(self, message: messages.Message, /) -> None:
        """Add a message to the cache.

        Parameters
        ----------
        message
            Object of the message to add.
        """

    @abc.abstractmethod
    def update_message(
        self, message: messages.PartialMessage | messages.Message, /
    ) -> tuple[messages.Message | None, messages.Message | None]:
        """Update a message in the cache.

        Parameters
        ----------
        message
            Object of the message to update in the cache.

        Returns
        -------
        typing.Tuple[typing.Optional[hikari.messages.Message], typing.Optional[hikari.messages.Message]]
            A tuple of the old message object that was cached if found (otherwise [`None`][])
            and the new message object if it could be cached (otherwise [`None`][]).
        """
