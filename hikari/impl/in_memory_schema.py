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
"""Basic implementation of a cache for general bots and gateway apps."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["InMemorySchema"]

import logging
import typing

import attr

from hikari import errors
from hikari.models import emojis
from hikari.models import guilds
from hikari.utilities import data_structures
from hikari.utilities import iterators

if typing.TYPE_CHECKING:
    from hikari.models import channels
    from hikari.models import presences
    from hikari.models import users
    from hikari.utilities import snowflake

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.cache.in_memory_schema")


@attr.s(slots=True, repr=False)
class InMemorySchema:
    _me: typing.Optional[users.OwnUser] = attr.ib(default=None)

    # DIRECT_MESSAGES (1 << 12)
    #   - CHANNEL_CREATE
    #   - MESSAGE_CREATE
    #   - MESSAGE_UPDATE
    #   - MESSAGE_DELETE
    #   - CHANNEL_PINS_UPDATE
    #
    # DIRECT_MESSAGE_REACTIONS (1 << 13)
    #   - MESSAGE_REACTION_ADD
    #   - MESSAGE_REACTION_REMOVE
    #   - MESSAGE_REACTION_REMOVE_ALL
    #   - MESSAGE_REACTION_REMOVE_EMOJI
    #
    # DIRECT_MESSAGE_TYPING (1 << 14)
    #   - TYPING_START
    _dm_channel_entries: data_structures.IDMap[channels.DMChannel] = attr.ib(factory=data_structures.IDMap)

    # Points to guild record objects.
    _guild_entries: data_structures.IDMap[GuildRecord] = attr.ib(factory=data_structures.IDMap)

    # GUILDS (1 << 0)
    #   - GUILD_CREATE
    #   - GUILD_UPDATE
    #   - GUILD_DELETE
    #   - CHANNEL_CREATE
    #   - CHANNEL_UPDATE
    #   - CHANNEL_DELETE
    #   - CHANNEL_PINS_UPDATE
    _guild_channel_entries: data_structures.IDMap[channels.GuildChannel] = attr.ib(factory=data_structures.IDMap)

    # GUILD_EMOJIS (1 << 3)
    #   - GUILD_EMOJIS_UPDATE
    _emoji_entries: data_structures.IDMap[emojis.KnownCustomEmoji] = attr.ib(factory=data_structures.IDMap)

    # GUILD_MEMBERS (1 << 1)
    #   - GUILD_MEMBER_ADD
    #   - GUILD_MEMBER_UPDATE
    #   - GUILD_MEMBER_REMOVE
    _member_entries: data_structures.IDMap[MemberRecord] = attr.ib(factory=data_structures.IDMap)

    # GUILD_MESSAGES (1 << 9)
    #   - MESSAGE_CREATE
    #   - MESSAGE_UPDATE
    #   - MESSAGE_DELETE
    #   - MESSAGE_DELETE_BULK
    #
    # GUILD_MEMBERS (1 << 1)
    #   - GUILD_MEMBER_ADD
    #   - GUILD_MEMBER_UPDATE
    #   - GUILD_MEMBER_REMOVE
    #
    # DIRECT_MESSAGES (1 << 12)
    #   - CHANNEL_CREATE
    #   - MESSAGE_CREATE
    #   - MESSAGE_UPDATE
    #   - MESSAGE_DELETE
    #   - CHANNEL_PINS_UPDATE
    #
    # DIRECT_MESSAGE_REACTIONS (1 << 13)
    #   - MESSAGE_REACTION_ADD
    #   - MESSAGE_REACTION_REMOVE
    #   - MESSAGE_REACTION_REMOVE_ALL
    #   - MESSAGE_REACTION_REMOVE_EMOJI
    #
    # DIRECT_MESSAGE_TYPING (1 << 14)
    #   - TYPING_START
    _user_entries: data_structures.IDMap[UserRecord] = attr.ib(factory=data_structures.IDMap)

    def get_me(self) -> typing.Optional[users.OwnUser]:
        return self._me

    def update_me(self, new: users.OwnUser, /) -> typing.Optional[users.OwnUser]:
        _LOGGER.debug("setting my user to %s", new)
        old = self._me
        self._me = new
        return old

    def get_guild(self, guild_id: snowflake.Snowflake) -> typing.Optional[guilds.GatewayGuild]:
        if (entry := self._guild_entries.get(guild_id)) is not None:
            if not entry.is_available:
                raise errors.UnavailableGuildError(entry.guild)
            return entry.guild
        return None

    def create_initial_guilds(self, *guild_ids: snowflake.Snowflake) -> None:
        # Invoked when we receive ON_READY, assume all of these are unavailable on startup.

        tbl = data_structures.IDTable
        mapping = data_structures.IDMap

        _LOGGER.debug("adding %s initial guilds from READY event", len(guild_ids))

        self._guild_entries.set_many(
            (guild_id, GuildRecord(guild_id, roles=mapping(), channels=tbl(), emojis=tbl(), is_available=False))
            for guild_id in guild_ids
        )

    def update_guild(self, new: guilds.GatewayGuild) -> typing.Optional[guilds.GatewayGuild]:
        if new.id not in self._guild_entries:
            _LOGGER.debug("inserting new guild record for %s", new.id)
            self._guild_entries[new.id] = GuildRecord(
                new.id,
                guild=new,
                is_available=True,
                roles=data_structures.IDMap(),
                channels=data_structures.IDTable(),
                emojis=data_structures.IDTable(),
            )
            return None
        else:
            _LOGGER.debug("updating existing guild record for %s", new.id)

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

    def delete_guild(self, guild_id: snowflake.Snowflake) -> typing.Optional[guilds.Guild]:
        if guild_id not in self._guild_entries:
            return None

        guild_record = self._guild_entries[guild_id]
        self._guild_channel_entries.delete_many(guild_record.channels)
        self._emoji_entries.delete_many(guild_record.emojis)
        self._member_entries.delete_many(guild_record.members)

        user_ids_to_remove: typing.List[int] = []

        for member_id in guild_record.members:
            if member_id in self._user_entries:
                entry = self._user_entries[member_id]
                entry.dec()

                if entry.should_be_destroyed:
                    user_ids_to_remove.append(member_id)

        self._user_entries.delete_many(user_ids_to_remove)

        del self._guild_entries[guild_id]
        return guild_record.guild

    def iter_guilds(self) -> iterators.FlatLazyIterator[guilds.GatewayGuild]:
        return iterators.FlatLazyIterator(
            record.guild for record in self._guild_entries.values() if record.guild is not None
        )

    def get_guild_channel(self, channel_id: snowflake.Snowflake) -> typing.Optional[channels.GuildChannel]:
        return self._guild_channel_entries.get(channel_id)

    def iter_guild_channels(self, guild_id: snowflake.Snowflake) -> iterators.FlatLazyIterator[channels.GuildChannel]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.channels is None:
            return iterators.FlatLazyIterator(())

        return iterators.FlatLazyIterator(
            (self._guild_channel_entries.get(channel_id) for channel_id in guild_record.channels)
        )

    def get_guild_emoji(self, emoji_id: snowflake.Snowflake) -> typing.Optional[emojis.KnownCustomEmoji]:
        return self._emoji_entries.get(emoji_id)

    def iter_guild_emojis(self, guild_id: snowflake.Snowflake) -> iterators.FlatLazyIterator[emojis.KnownCustomEmoji]:
        guild_record = self._guild_entries[guild_id]
        if guild_record.emojis is None:
            return iterators.FlatLazyIterator(())

        return iterators.FlatLazyIterator(
            (self._guild_channel_entries.get(emoji_id) for emoji_id in guild_record.emojis)
        )

    def set_guild_availability(self, guild_id: snowflake.Snowflake, is_available: bool) -> None:
        if guild_id in self._guild_entries:
            self._guild_entries[guild_id].is_available = is_available
        else:
            _LOGGER.debug(
                "guild %s has become %savailable, but it is not cached, so is being ignored",
                guild_id,
                "un" if not is_available else "",
            )


@attr.s(slots=True, repr=False)
class GuildRecord:
    id: snowflake.Snowflake = attr.ib(hash=True)

    # GUILDS(1 << 0)
    #   - GUILD_CREATE
    #   - GUILD_DELETE
    is_available: typing.Optional[bool] = attr.ib(default=None, hash=False)

    # GUILDS (1 << 0)
    #   - GUILD_CREATE
    #   - GUILD_UPDATE
    #   - GUILD_DELETE
    guild: typing.Optional[guilds.GatewayGuild] = attr.ib(default=None, hash=False)

    # GUILDS (1 << 0)
    #   - GUILD_ROLE_CREATE
    #   - GUILD_ROLE_UPDATE
    #   - GUILD_ROLE_DELETE
    roles: typing.Optional[data_structures.IDMap[guilds.Role]] = attr.ib(default=None, hash=False)

    # GUILDS(1 << 0)
    #   - GUILD_CREATE
    #   - CHANNEL_CREATE
    #   - CHANNEL_UPDATE
    #   - CHANNEL_DELETE
    channels: typing.Optional[data_structures.IDTable] = attr.ib(default=None, hash=False)

    # GUILDS (1 << 0)
    #   - GUILD_CREATE
    #   - GUILD_UPDATE ???
    #
    # GUILD_EMOJIS(1 << 3)
    # - GUILD_EMOJIS_UPDATE
    emojis: typing.Optional[data_structures.IDTable] = attr.ib(default=None, hash=False)

    # GUILD_MEMBERS (1 << 1)
    #   - GUILD_MEMBER_ADD
    #   - GUILD_MEMBER_UPDATE
    #   - GUILD_MEMBER_REMOVE
    members: typing.Optional[data_structures.IDTable] = attr.ib(default=None, hash=False)

    # GUILD_PRESENCES (1 << 8)
    #   - PRESENCE_UPDATE
    presences: typing.Optional[data_structures.IDTable] = attr.ib(default=None, hash=False)

    # GUILD_VOICE_STATES (1 << 7)
    #   - VOICE_STATE_UPDATE
    voice_states: typing.Optional[data_structures.IDTable] = attr.ib(default=None, hash=False)


@attr.s(slots=True, repr=False)
class MemberRecord:
    id: snowflake.Snowflake = attr.ib(hash=True)

    # GUILD_MEMBERS (1 << 1)
    #   - GUILD_MEMBER_ADD
    #   - GUILD_MEMBER_UPDATE
    #   - GUILD_MEMBER_REMOVE
    _partial_member: typing.Optional[typing.Any] = attr.ib(default=None, hash=False)

    # GUILD_PRESENCES (1 << 8)
    #   - PRESENCE_UPDATE
    _presence: typing.Optional[presences.MemberPresence] = attr.ib(default=None, hash=False)


@attr.s(slots=True, repr=False)
class UserRecord:
    user: users.User = attr.ib(hash=True)

    # Users can be in more than one guild, so we have to keep a reference count so that we know
    # when to remove the entire object.
    _ref_count: int = attr.ib(hash=False, default=0)

    def inc(self) -> None:
        self._ref_count += 1

    def dec(self) -> None:
        self._ref_count -= 1

    @property
    def should_be_destroyed(self) -> bool:
        return self._ref_count <= 0
