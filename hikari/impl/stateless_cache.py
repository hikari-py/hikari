# -*- coding: utf-8 -*-
# cython: language_level=3
# Copyright (c) 2020 Nekokatt
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
"""Bare-bones implementation of a cache that never stores anything.

This is used to enable compatibility with HTTP applications and stateless
bots where desired.
"""
from __future__ import annotations

__all__: typing.List[str] = ["StatelessCacheImpl"]

import typing

from hikari.api import cache
from hikari.internal import cache as cache_utilities

if typing.TYPE_CHECKING:
    from hikari import channels
    from hikari import emojis
    from hikari import guilds
    from hikari import invites
    from hikari import messages
    from hikari import presences
    from hikari import snowflakes
    from hikari import users
    from hikari import voices


@typing.final
class StatelessCacheImpl(cache.MutableCache):
    """Stateless cache.

    A stateless cache implementation that implements dummy operations for
    each of the required attributes of a functional cache implementation.R
    Any descriptors will always return `builtins.NotImplemented`, and any
    methods will always raise `hikari.errors.HikariError` when being invoked.

    The only state that _is_ stored will be the bot user, as this is generally
    useful information to always know about, and is required for some
    functionality such as voice support.
    """

    __slots__: typing.Sequence[str] = ("_app", "_me")

    def __init__(self) -> None:
        self._me: typing.Optional[users.OwnUser] = None

    @staticmethod
    def _no_cache() -> NotImplementedError:
        return NotImplementedError("This application is stateless, cache operations are not implemented.")

    def clear_emojis(self) -> cache.CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        raise self._no_cache()

    def clear_emojis_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        raise self._no_cache()

    def delete_emoji(self, emoji_id: snowflakes.Snowflake, /) -> typing.Optional[emojis.KnownCustomEmoji]:
        raise self._no_cache()

    def get_emoji(self, emoji_id: snowflakes.Snowflake, /) -> typing.Optional[emojis.KnownCustomEmoji]:
        return None

    def get_emojis_view(self) -> cache.CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        return cache_utilities.EmptyCacheView()

    def get_emojis_view_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        return cache_utilities.EmptyCacheView()

    def set_emoji(self, emoji: emojis.KnownCustomEmoji, /) -> None:
        raise self._no_cache()

    def update_emoji(
        self, emoji: emojis.KnownCustomEmoji, /
    ) -> typing.Tuple[typing.Optional[emojis.KnownCustomEmoji], typing.Optional[emojis.KnownCustomEmoji]]:
        raise self._no_cache()

    def clear_guilds(self) -> cache.CacheView[snowflakes.Snowflake, guilds.GatewayGuild]:
        raise self._no_cache()

    def delete_guild(self, guild_id: snowflakes.Snowflake, /) -> typing.Optional[guilds.GatewayGuild]:
        raise self._no_cache()

    def get_guild(self, guild_id: snowflakes.Snowflake, /) -> typing.Optional[guilds.GatewayGuild]:
        return None

    def get_available_guild(self, guild_id: snowflakes.Snowflake, /) -> typing.Optional[guilds.GatewayGuild]:
        return None

    def get_unavailable_guild(self, guild_id: snowflakes.Snowflake) -> typing.Optional[guilds.GatewayGuild]:
        return None

    def get_available_guilds_view(self) -> cache.CacheView[snowflakes.Snowflake, guilds.GatewayGuild]:
        return cache_utilities.EmptyCacheView()

    def get_unavailable_guilds_view(self) -> cache.CacheView[snowflakes.Snowflake, guilds.GatewayGuild]:
        return cache_utilities.EmptyCacheView()

    def set_guild(self, guild: guilds.GatewayGuild, /) -> None:
        raise self._no_cache()

    def set_guild_availability(self, guild_id: snowflakes.Snowflake, is_available: bool, /) -> None:
        raise self._no_cache()

    def update_guild(
        self, guild: guilds.GatewayGuild, /
    ) -> typing.Tuple[typing.Optional[guilds.GatewayGuild], typing.Optional[guilds.GatewayGuild]]:
        raise self._no_cache()

    def clear_guild_channels(self) -> cache.CacheView[snowflakes.Snowflake, channels.GuildChannel]:
        raise self._no_cache()

    def clear_guild_channels_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, channels.GuildChannel]:
        raise self._no_cache()

    def delete_guild_channel(self, channel_id: snowflakes.Snowflake, /) -> typing.Optional[channels.GuildChannel]:
        raise self._no_cache()

    def get_guild_channel(self, channel_id: snowflakes.Snowflake, /) -> typing.Optional[channels.GuildChannel]:
        return None

    def get_guild_channels_view(self) -> cache.CacheView[snowflakes.Snowflake, channels.GuildChannel]:
        return cache_utilities.EmptyCacheView()

    def get_guild_channels_view_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, channels.GuildChannel]:
        return cache_utilities.EmptyCacheView()

    def set_guild_channel(self, channel: channels.GuildChannel, /) -> None:
        raise self._no_cache()

    def update_guild_channel(
        self, channel: channels.GuildChannel, /
    ) -> typing.Tuple[typing.Optional[channels.GuildChannel], typing.Optional[channels.GuildChannel]]:
        raise self._no_cache()

    def clear_invites(self) -> cache.CacheView[str, invites.InviteWithMetadata]:
        raise self._no_cache()

    def clear_invites_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[str, invites.InviteWithMetadata]:
        raise self._no_cache()

    def clear_invites_for_channel(
        self, guild_id: snowflakes.Snowflake, channel_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[str, invites.InviteWithMetadata]:
        raise self._no_cache()

    def delete_invite(self, code: str, /) -> typing.Optional[invites.InviteWithMetadata]:
        raise self._no_cache()

    def get_invite(self, code: str, /) -> typing.Optional[invites.InviteWithMetadata]:
        return None

    def get_invites_view(self) -> cache.CacheView[str, invites.InviteWithMetadata]:
        return cache_utilities.EmptyCacheView()

    def get_invites_view_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[str, invites.InviteWithMetadata]:
        return cache_utilities.EmptyCacheView()

    def get_invites_view_for_channel(
        self, guild_id: snowflakes.Snowflake, channel_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[str, invites.InviteWithMetadata]:
        return cache_utilities.EmptyCacheView()

    def set_invite(self, invite: invites.InviteWithMetadata, /) -> None:
        raise self._no_cache()

    def update_invite(
        self, invite: invites.InviteWithMetadata, /
    ) -> typing.Tuple[typing.Optional[invites.InviteWithMetadata], typing.Optional[invites.InviteWithMetadata]]:
        raise self._no_cache()

    def delete_me(self) -> typing.Optional[users.OwnUser]:
        cached_me = self._me
        self._me = None
        return cached_me

    def get_me(self) -> typing.Optional[users.OwnUser]:
        return self._me

    def set_me(self, user: users.OwnUser, /) -> None:
        self._me = user

    def update_me(
        self, user: users.OwnUser, /
    ) -> typing.Tuple[typing.Optional[users.OwnUser], typing.Optional[users.OwnUser]]:
        cached_me = self.get_me()
        self.set_me(user)
        return cached_me, self.get_me()

    def clear_members(
        self,
    ) -> cache.CacheView[snowflakes.Snowflake, cache.CacheView[snowflakes.Snowflake, guilds.Member]]:
        raise self._no_cache()

    def clear_members_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, guilds.Member]:
        raise self._no_cache()

    def delete_member(
        self, guild_id: snowflakes.Snowflake, user_id: snowflakes.Snowflake, /
    ) -> typing.Optional[guilds.Member]:
        raise self._no_cache()

    def get_member(
        self, guild_id: snowflakes.Snowflake, user_id: snowflakes.Snowflake, /
    ) -> typing.Optional[guilds.Member]:
        return None

    def get_members_view(
        self,
    ) -> cache.CacheView[snowflakes.Snowflake, cache.CacheView[snowflakes.Snowflake, guilds.Member]]:
        return cache_utilities.EmptyCacheView()

    def get_members_view_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, guilds.Member]:
        return cache_utilities.EmptyCacheView()

    def set_member(self, member: guilds.Member, /) -> None:
        raise self._no_cache()

    def update_member(
        self, member: guilds.Member, /
    ) -> typing.Tuple[typing.Optional[guilds.Member], typing.Optional[guilds.Member]]:
        raise self._no_cache()

    def clear_presences(
        self,
    ) -> cache.CacheView[snowflakes.Snowflake, cache.CacheView[snowflakes.Snowflake, presences.MemberPresence]]:
        raise self._no_cache()

    def clear_presences_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, presences.MemberPresence]:
        raise self._no_cache()

    def delete_presence(
        self, guild_id: snowflakes.Snowflake, user_id: snowflakes.Snowflake, /
    ) -> typing.Optional[presences.MemberPresence]:
        raise self._no_cache()

    def get_presence(
        self, guild_id: snowflakes.Snowflake, user_id: snowflakes.Snowflake, /
    ) -> typing.Optional[presences.MemberPresence]:
        return None

    def get_presences_view(
        self,
    ) -> cache.CacheView[snowflakes.Snowflake, cache.CacheView[snowflakes.Snowflake, presences.MemberPresence]]:
        return cache_utilities.EmptyCacheView()

    def get_presences_view_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, presences.MemberPresence]:
        return cache_utilities.EmptyCacheView()

    def set_presence(self, presence: presences.MemberPresence, /) -> None:
        raise self._no_cache()

    def update_presence(
        self, presence: presences.MemberPresence, /
    ) -> typing.Tuple[typing.Optional[presences.MemberPresence], typing.Optional[presences.MemberPresence]]:
        raise self._no_cache()

    def clear_roles(self) -> cache.CacheView[snowflakes.Snowflake, guilds.Role]:
        raise self._no_cache()

    def clear_roles_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, guilds.Role]:
        raise self._no_cache()

    def delete_role(self, role_id: snowflakes.Snowflake, /) -> typing.Optional[guilds.Role]:
        raise self._no_cache()

    def get_role(self, role_id: snowflakes.Snowflake, /) -> typing.Optional[guilds.Role]:
        return None

    def get_roles_view(self) -> cache.CacheView[snowflakes.Snowflake, guilds.Role]:
        return cache_utilities.EmptyCacheView()

    def get_roles_view_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, guilds.Role]:
        return cache_utilities.EmptyCacheView()

    def set_role(self, role: guilds.Role, /) -> None:
        raise self._no_cache()

    def update_role(
        self, role: guilds.Role, /
    ) -> typing.Tuple[typing.Optional[guilds.Role], typing.Optional[guilds.Role]]:
        raise self._no_cache()

    def clear_users(self) -> cache.CacheView[snowflakes.Snowflake, users.User]:
        raise self._no_cache()

    def delete_user(self, user_id: snowflakes.Snowflake, /) -> typing.Optional[users.User]:
        raise self._no_cache()

    def get_user(self, user_id: snowflakes.Snowflake, /) -> typing.Optional[users.User]:
        return None

    def get_users_view(self) -> cache.CacheView[snowflakes.Snowflake, users.User]:
        return cache_utilities.EmptyCacheView()

    def set_user(self, user: users.User, /) -> None:
        raise self._no_cache()

    def update_user(
        self, user: users.User, /
    ) -> typing.Tuple[typing.Optional[users.User], typing.Optional[users.User]]:
        raise self._no_cache()

    def clear_voice_states(
        self,
    ) -> cache.CacheView[snowflakes.Snowflake, cache.CacheView[snowflakes.Snowflake, voices.VoiceState]]:
        raise self._no_cache()

    def clear_voice_states_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, voices.VoiceState]:
        raise self._no_cache()

    def clear_voice_states_for_channel(
        self, guild_id: snowflakes.Snowflake, channel_id: snowflakes.Snowflake
    ) -> cache.CacheView[snowflakes.Snowflake, voices.VoiceState]:
        raise self._no_cache()

    def delete_voice_state(
        self, guild_id: snowflakes.Snowflake, user_id: snowflakes.Snowflake, /
    ) -> typing.Optional[voices.VoiceState]:
        raise self._no_cache()

    def get_voice_state(
        self, guild_id: snowflakes.Snowflake, user_id: snowflakes.Snowflake, /
    ) -> typing.Optional[voices.VoiceState]:
        return None

    def get_voice_states_view(
        self,
    ) -> cache.CacheView[snowflakes.Snowflake, cache.CacheView[snowflakes.Snowflake, voices.VoiceState]]:
        return cache_utilities.EmptyCacheView()

    def get_voice_states_view_for_channel(
        self, guild_id: snowflakes.Snowflake, channel_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, voices.VoiceState]:
        return cache_utilities.EmptyCacheView()

    def get_voice_states_view_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, voices.VoiceState]:
        return cache_utilities.EmptyCacheView()

    def set_voice_state(self, voice_state: voices.VoiceState, /) -> None:
        raise self._no_cache()

    def update_voice_state(
        self, voice_state: voices.VoiceState, /
    ) -> typing.Tuple[typing.Optional[voices.VoiceState], typing.Optional[voices.VoiceState]]:
        raise self._no_cache()

    def clear_messages(self) -> cache.CacheView[snowflakes.Snowflake, messages.Message]:
        raise self._no_cache()

    def delete_message(self, message_id: snowflakes.Snowflake, /) -> typing.Optional[messages.Message]:
        raise self._no_cache()

    def get_message(self, message_id: snowflakes.Snowflake, /) -> typing.Optional[messages.Message]:
        return None

    def get_messages_view(self) -> cache.CacheView[snowflakes.Snowflake, messages.Message]:
        return cache_utilities.EmptyCacheView()

    def set_message(self, message: messages.Message, /) -> None:
        raise self._no_cache()

    def update_message(
        self, message: typing.Union[messages.PartialMessage, messages.Message], /
    ) -> typing.Tuple[typing.Optional[messages.Message], typing.Optional[messages.Message]]:
        raise self._no_cache()
