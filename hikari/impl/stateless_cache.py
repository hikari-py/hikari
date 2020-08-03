# -*- coding: utf-8 -*-
# cython: language_level=3
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
"""Barebones implementation of a cache that never stores anything.

This is used to enable compatibility with HTTP applications and stateless
bots where desired.
"""
from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["StatelessCacheImpl"]

import typing

from hikari.api import cache
from hikari.api import rest

if typing.TYPE_CHECKING:
    from hikari.models import channels
    from hikari.models import emojis
    from hikari.models import guilds
    from hikari.models import invites
    from hikari.models import presences
    from hikari.models import users
    from hikari.models import voices
    from hikari.utilities import snowflake


@typing.final
class StatelessCacheImpl(cache.ICacheComponent):
    """Stateless cache.

    A stateless cache implementation that implements dummy operations for
    each of the required attributes of a functional cache implementation.
    Any descriptors will always return `builtins.NotImplemented`, and any
    methods will always raise `hikari.errors.HikariError` when being invoked.

    The only state that _is_ stored will be the bot user, as this is generally
    useful information to always know about, and is required for some
    functionality such as voice support.
    """

    __slots__: typing.Sequence[str] = ("_app", "_me")

    def __init__(self, app: rest.IRESTApp) -> None:
        self._app = app
        self._me: typing.Optional[users.OwnUser] = None

    @property
    def app(self) -> rest.IRESTApp:
        return self._app

    def get_me(self) -> typing.Optional[users.OwnUser]:
        return self._me

    def set_me(self, user: users.OwnUser, /) -> None:
        self._me = user

    @staticmethod
    def _no_cache() -> NotImplementedError:
        return NotImplementedError("This application is stateless, cache operations are not implemented.")

    def clear_private_text_channels(self) -> cache.ICacheView[snowflake.Snowflake, channels.PrivateTextChannel]:
        raise self._no_cache()

    def delete_private_text_channel(
        self, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[channels.PrivateTextChannel]:
        raise self._no_cache()

    def get_private_text_channel(self, user_id: snowflake.Snowflake, /) -> typing.Optional[channels.PrivateTextChannel]:
        raise self._no_cache()

    def get_private_text_channels_view(self) -> cache.ICacheView[snowflake.Snowflake, channels.PrivateTextChannel]:
        raise self._no_cache()

    def set_private_text_channel(self, channel: channels.PrivateTextChannel, /) -> None:
        raise self._no_cache()

    def update_private_text_channel(
        self, channel: channels.PrivateTextChannel, /
    ) -> typing.Tuple[typing.Optional[channels.PrivateTextChannel], typing.Optional[channels.PrivateTextChannel]]:
        raise self._no_cache()

    def clear_emojis(self) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        raise self._no_cache()

    def clear_emojis_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        raise self._no_cache()

    def delete_emoji(self, emoji_id: snowflake.Snowflake, /) -> typing.Optional[emojis.KnownCustomEmoji]:
        raise self._no_cache()

    def get_emoji(self, emoji_id: snowflake.Snowflake, /) -> typing.Optional[emojis.KnownCustomEmoji]:
        raise self._no_cache()

    def get_emojis_view(self) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        raise self._no_cache()

    def get_emojis_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, emojis.KnownCustomEmoji]:
        raise self._no_cache()

    def set_emoji(self, emoji: emojis.KnownCustomEmoji, /) -> None:
        raise self._no_cache()

    def update_emoji(
        self, emoji: emojis.KnownCustomEmoji, /
    ) -> typing.Tuple[typing.Optional[emojis.KnownCustomEmoji], typing.Optional[emojis.KnownCustomEmoji]]:
        raise self._no_cache()

    def clear_guilds(self) -> cache.ICacheView[snowflake.Snowflake, guilds.GatewayGuild]:
        raise self._no_cache()

    def delete_guild(self, guild_id: snowflake.Snowflake, /) -> typing.Optional[guilds.GatewayGuild]:
        raise self._no_cache()

    def get_guild(self, guild_id: snowflake.Snowflake, /) -> typing.Optional[guilds.GatewayGuild]:
        raise self._no_cache()

    def get_guilds_view(self) -> cache.ICacheView[snowflake.Snowflake, guilds.GatewayGuild]:
        raise self._no_cache()

    def set_guild(self, guild: guilds.GatewayGuild, /) -> None:
        raise self._no_cache()

    def set_guild_availability(self, guild_id: snowflake.Snowflake, is_available: bool, /) -> None:
        raise self._no_cache()

    def set_initial_unavailable_guilds(self, guild_ids: typing.Collection[snowflake.Snowflake], /) -> None:
        raise self._no_cache()

    def update_guild(
        self, guild: guilds.GatewayGuild, /
    ) -> typing.Tuple[typing.Optional[guilds.GatewayGuild], typing.Optional[guilds.GatewayGuild]]:
        raise self._no_cache()

    def clear_guild_channels(self) -> cache.ICacheView[snowflake.Snowflake, channels.GuildChannel]:
        raise self._no_cache()

    def clear_guild_channels_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, channels.GuildChannel]:
        raise self._no_cache()

    def delete_guild_channel(self, channel_id: snowflake.Snowflake, /) -> typing.Optional[channels.GuildChannel]:
        raise self._no_cache()

    def get_guild_channel(self, channel_id: snowflake.Snowflake, /) -> typing.Optional[channels.GuildChannel]:
        raise self._no_cache()

    def get_guild_channels_view(self) -> cache.ICacheView[snowflake.Snowflake, channels.GuildChannel]:
        raise self._no_cache()

    def get_guild_channels_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, channels.GuildChannel]:
        raise self._no_cache()

    def set_guild_channel(self, channel: channels.GuildChannel, /) -> None:
        raise self._no_cache()

    def update_guild_channel(
        self, channel: channels.GuildChannel, /
    ) -> typing.Tuple[typing.Optional[channels.GuildChannel], typing.Optional[channels.GuildChannel]]:
        raise self._no_cache()

    def clear_invites(self) -> cache.ICacheView[str, invites.InviteWithMetadata]:
        raise self._no_cache()

    def clear_invites_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[str, invites.InviteWithMetadata]:
        raise self._no_cache()

    def clear_invites_for_channel(
        self, guild_id: snowflake.Snowflake, channel_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[str, invites.InviteWithMetadata]:
        raise self._no_cache()

    def delete_invite(self, code: str, /) -> typing.Optional[invites.InviteWithMetadata]:
        raise self._no_cache()

    def get_invite(self, code: str, /) -> typing.Optional[invites.InviteWithMetadata]:
        raise self._no_cache()

    def get_invites_view(self) -> cache.ICacheView[str, invites.InviteWithMetadata]:
        raise self._no_cache()

    def get_invites_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[str, invites.InviteWithMetadata]:
        raise self._no_cache()

    def get_invites_view_for_channel(
        self, guild_id: snowflake.Snowflake, channel_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[str, invites.InviteWithMetadata]:
        raise self._no_cache()

    def set_invite(self, invite: invites.InviteWithMetadata, /) -> None:
        raise self._no_cache()

    def update_invite(
        self, invite: invites.InviteWithMetadata, /
    ) -> typing.Tuple[typing.Optional[invites.InviteWithMetadata], typing.Optional[invites.InviteWithMetadata]]:
        raise self._no_cache()

    def delete_me(self) -> typing.Optional[users.OwnUser]:
        raise self._no_cache()

    def update_me(
        self, user: users.OwnUser, /
    ) -> typing.Tuple[typing.Optional[users.OwnUser], typing.Optional[users.OwnUser]]:
        raise self._no_cache()

    def clear_members(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, guilds.Member]]:
        raise self._no_cache()

    def clear_members_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, guilds.Member]:
        raise self._no_cache()

    def delete_member(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[guilds.Member]:
        raise self._no_cache()

    def get_member(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[guilds.Member]:
        raise self._no_cache()

    def get_members_view(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, guilds.Member]]:
        raise self._no_cache()

    def get_members_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, guilds.Member]:
        raise self._no_cache()

    def set_member(self, member: guilds.Member, /) -> None:
        raise self._no_cache()

    def update_member(
        self, member: guilds.Member, /
    ) -> typing.Tuple[typing.Optional[guilds.Member], typing.Optional[guilds.Member]]:
        raise self._no_cache()

    def clear_presences(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, presences.MemberPresence]]:
        raise self._no_cache()

    def clear_presences_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, presences.MemberPresence]:
        raise self._no_cache()

    def delete_presence(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[presences.MemberPresence]:
        raise self._no_cache()

    def get_presence(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[presences.MemberPresence]:
        raise self._no_cache()

    def get_presences_view(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, presences.MemberPresence]]:
        raise self._no_cache()

    def get_presences_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, presences.MemberPresence]:
        raise self._no_cache()

    def set_presence(self, presence: presences.MemberPresence, /) -> None:
        raise self._no_cache()

    def update_presence(
        self, presence: presences.MemberPresence, /
    ) -> typing.Tuple[typing.Optional[presences.MemberPresence], typing.Optional[presences.MemberPresence]]:
        raise self._no_cache()

    def clear_roles(self) -> cache.ICacheView[snowflake.Snowflake, guilds.Role]:
        raise self._no_cache()

    def clear_roles_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, guilds.Role]:
        raise self._no_cache()

    def delete_role(self, role_id: snowflake.Snowflake, /) -> typing.Optional[guilds.Role]:
        raise self._no_cache()

    def get_role(self, role_id: snowflake.Snowflake, /) -> typing.Optional[guilds.Role]:
        raise self._no_cache()

    def get_roles_view(self) -> cache.ICacheView[snowflake.Snowflake, guilds.Role]:
        raise self._no_cache()

    def get_roles_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, guilds.Role]:
        raise self._no_cache()

    def set_role(self, role: guilds.Role, /) -> None:
        raise self._no_cache()

    def update_role(
        self, role: guilds.Role, /
    ) -> typing.Tuple[typing.Optional[guilds.Role], typing.Optional[guilds.Role]]:
        raise self._no_cache()

    def clear_users(self) -> cache.ICacheView[snowflake.Snowflake, users.User]:
        raise self._no_cache()

    def delete_user(self, user_id: snowflake.Snowflake, /) -> typing.Optional[users.User]:
        raise self._no_cache()

    def get_user(self, user_id: snowflake.Snowflake, /) -> typing.Optional[users.User]:
        raise self._no_cache()

    def get_users_view(self) -> cache.ICacheView[snowflake.Snowflake, users.User]:
        raise self._no_cache()

    def set_user(self, user: users.User, /) -> None:
        raise self._no_cache()

    def update_user(
        self, user: users.User, /
    ) -> typing.Tuple[typing.Optional[users.User], typing.Optional[users.User]]:
        raise self._no_cache()

    def clear_voice_states(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, voices.VoiceState]]:
        raise self._no_cache()

    def clear_voice_states_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, voices.VoiceState]:
        raise self._no_cache()

    def clear_voice_states_for_channel(
        self, guild_id: snowflake.Snowflake, channel_id: snowflake.Snowflake
    ) -> cache.ICacheView[snowflake.Snowflake, voices.VoiceState]:
        raise self._no_cache()

    def delete_voice_state(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[voices.VoiceState]:
        raise self._no_cache()

    def get_voice_state(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake, /
    ) -> typing.Optional[voices.VoiceState]:
        raise self._no_cache()

    def get_voice_states_view(
        self,
    ) -> cache.ICacheView[snowflake.Snowflake, cache.ICacheView[snowflake.Snowflake, voices.VoiceState]]:
        raise self._no_cache()

    def get_voice_states_view_for_channel(
        self, guild_id: snowflake.Snowflake, channel_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, voices.VoiceState]:
        raise self._no_cache()

    def get_voice_states_view_for_guild(
        self, guild_id: snowflake.Snowflake, /
    ) -> cache.ICacheView[snowflake.Snowflake, voices.VoiceState]:
        raise self._no_cache()

    def set_voice_state(self, voice_state: voices.VoiceState, /) -> None:
        raise self._no_cache()

    def update_voice_state(
        self, voice_state: voices.VoiceState, /
    ) -> typing.Tuple[typing.Optional[voices.VoiceState], typing.Optional[voices.VoiceState]]:
        raise self._no_cache()
