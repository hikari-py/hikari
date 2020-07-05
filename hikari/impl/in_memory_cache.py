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
"""Basic implementation of a cache for general bots and gateway apps."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["InMemoryCacheComponentImpl"]

import logging
import typing
import weakref

import attr

from hikari import errors
from hikari.api import cache
from hikari.models import channels
from hikari.models import emojis
from hikari.models import guilds
from hikari.models import intents as intents_
from hikari.models import presences

if typing.TYPE_CHECKING:
    from hikari.api import rest as rest_app
    from hikari.models import users
    from hikari.utilities import snowflake


_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.cache")


class InMemoryCacheComponentImpl(cache.ICacheComponent):
    """In-memory cache implementation."""

    def __init__(self, app: rest_app.IRESTApp, intents: typing.Optional[intents_.Intent]) -> None:
        self._me: typing.Optional[users.OwnUser] = None
        self._dm_channel_entries: typing.MutableMapping[snowflake.Snowflake, channels.DMChannel] = {}

        # Points to guild record objects.
        self._guild_entries: typing.MutableMapping[snowflake.Snowflake, GuildRecord] = {}
        self._user_entries: typing.MutableMapping[snowflake.Snowflake, users.User] = weakref.WeakValueDictionary()

        self._app = app
        self._intents = intents

    @property
    @typing.final
    def app(self) -> rest_app.IRESTApp:
        return self._app

    def _assert_has_intent(self, intents: intents_.Intent, /) -> None:
        if self._intents is not None and self._intents ^ intents:
            raise errors.MissingIntentError(intents)

    def _is_intent_enabled(self, intents: intents_.Intent, /) -> bool:
        return self._intents is None or self._intents & intents

    def delete_guild(self, guild_id: snowflake.Snowflake) -> typing.Optional[guilds.Guild]:
        if guild_id not in self._guild_entries:
            return None

        guild_record = self._guild_entries[guild_id]
        del self._guild_entries[guild_id]
        return guild_record.guild

    def get_me(self) -> typing.Optional[users.OwnUser]:
        return self._me

    def get_guild(self, guild_id: snowflake.Snowflake) -> typing.Optional[guilds.GatewayGuild]:
        if (entry := self._guild_entries.get(guild_id)) is not None:
            if not entry.is_available:
                raise errors.UnavailableGuildError(entry.guild)
            return entry.guild
        return None

    def get_guild_channel(
        self, guild_id: snowflake.Snowflake, channel_id: snowflake.Snowflake
    ) -> typing.Optional[channels.GuildChannel]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None and guild_record.channels is not None:
            return guild_record.channels.get(channel_id)

    def get_guild_emoji(
        self, guild_id: snowflake.Snowflake, emoji_id: snowflake.Snowflake
    ) -> typing.Optional[emojis.KnownCustomEmoji]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None:
            return guild_record.emojis.get(emoji_id)

    def get_guild_member(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return None
        return guild_record.members.get(user_id)

    def get_guild_presence(
        self, guild_id: snowflake.Snowflake, user_id: snowflake.Snowflake
    ) -> typing.Optional[presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return None
        return guild_record.presences.get(user_id)

    def get_guild_role(
        self, guild_id: snowflake.Snowflake, role_id: snowflake.Snowflake
    ) -> typing.Optional[guilds.Role]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record.emojis is None or guild_record.roles is None:
            return None
        return guild_record.roles[role_id]

    def iter_guilds(self) -> typing.Iterator[guilds.GatewayGuild]:
        for record in self._guild_entries.values():
            if record.guild is not None:
                yield record.guild

    def iter_guild_channels(self, guild_id: snowflake.Snowflake) -> typing.Iterator[channels.GuildChannel]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None and guild_record.channels is not None:
            yield from guild_record.channels.values()

    def iter_guild_emojis(self, guild_id: snowflake.Snowflake) -> typing.Iterator[emojis.KnownCustomEmoji]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None and guild_record.emojis is not None:
            yield from guild_record.emojis.values()

    def iter_guild_members(self, guild_id: snowflake.Snowflake) -> typing.Iterator[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None and guild_record.members is not None:
            yield from guild_record.members.values()

    def iter_guild_presences(self, guild_id: snowflake.Snowflake) -> typing.Iterator[presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None and guild_record.presences is not None:
            yield from guild_record.presences

    def iter_guild_roles(self, guild_id: snowflake.Snowflake) -> typing.Iterator[guilds.Role]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None and guild_record.roles is not None:
            yield from guild_record.roles.values()

    def set_initial_unavailable_guilds(self, guild_ids: typing.Collection[snowflake.Snowflake]) -> None:
        # Invoked when we receive ON_READY, assume all of these are unavailable on startup.
        self._guild_entries = {guild_id: GuildRecord(guild_id, is_available=False) for guild_id in guild_ids}

    def set_guild(self, new: guilds.GatewayGuild) -> typing.Optional[guilds.GatewayGuild]:
        if new.id not in self._guild_entries:
            self._guild_entries[new.id] = GuildRecord(new.id, guild=new, is_available=True)
            return None

        guild_record = self._guild_entries[new.id]
        old = guild_record.guild

        # We have to manually update these because inconsistency by Discord.
        if old is not None:
            new.member_count = old.member_count
            new.joined_at = old.joined_at
            new.is_large = old.is_large

        guild_record.guild = new
        guild_record.is_available = True
        return old

    def set_guild_availability(self, guild_id: snowflake.Snowflake, is_available: bool) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = GuildRecord(guild_id)

        self._guild_entries[guild_id].is_available = is_available

    def set_me(self, new: users.OwnUser, /) -> typing.Optional[users.OwnUser]:
        _LOGGER.debug("setting my user to %s", new)
        old = self._me
        self._me = new
        return old

    def replace_all_guild_channels(
        self, guild_id: snowflake.Snowflake, channel_objs: typing.Collection[channels.GuildChannel]
    ) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = GuildRecord(guild_id)

        self._guild_entries[guild_id].channels = sorted(channel_objs, key=lambda c: c.position)

    def replace_all_guild_emojis(
        self, guild_id: snowflake.Snowflake, emoji_objs: typing.Collection[emojis.KnownCustomEmoji]
    ) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = GuildRecord(guild_id)

        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None:
            guild_record.emojis = {emoji_obj.id: emoji_obj for emoji_obj in emoji_objs}

    def replace_all_guild_members(
        self, guild_id: snowflake.Snowflake, member_objs: typing.Collection[guilds.Member]
    ) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = GuildRecord(guild_id)

        self._guild_entries[guild_id].members = {}

        for member in member_objs:
            if member.id in self._user_entries:
                member.user = self._user_entries[member.id]
            else:
                self._user_entries[member.id] = member.user
            self._guild_entries[guild_id].members[member.id] = member

    def replace_all_guild_presences(
        self, guild_id: snowflake.Snowflake, presence_objs: typing.Collection[presences.MemberPresence]
    ) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = GuildRecord(guild_id)

        self._guild_entries[guild_id].presences = {presence_obj.user_id: presence_obj for presence_obj in presence_objs}

    def replace_all_guild_roles(self, guild_id: snowflake.Snowflake, roles: typing.Collection[guilds.Role]) -> None:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = GuildRecord(guild_id)

        # Top role first!
        self._guild_entries[guild_id].roles = {
            role.id: role for role in sorted(roles, key=lambda r: r.position, reverse=True)
        }


@attr.s(slots=True, repr=False, hash=False, auto_attribs=True)
class GuildRecord:
    id: snowflake.Snowflake
    is_available: typing.Optional[bool] = False
    guild: typing.Optional[guilds.GatewayGuild] = None

    # TODO: some of these will be iterated across more than they will searched by a specific ID...
    # ... identify these cases and convert to lists.
    roles: typing.Optional[typing.MutableMapping[snowflake.Snowflake, guilds.Role]] = None
    members: typing.Optional[typing.MutableMapping[snowflake.Snowflake, guilds.Member]] = None
    presences: typing.Optional[typing.MutableMapping[snowflake.Snowflake, presences.MemberPresence]] = None
    channels: typing.Optional[typing.MutableMapping[snowflake.Snowflake, channels.GuildChannel]] = None
    emojis: typing.Optional[typing.MutableMapping[snowflake.Snowflake, emojis.KnownCustomEmoji]] = None

    def __hash__(self) -> int:
        return hash(self.id)
