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
"""Basic implementation of a cache for general bots and gateway apps."""

from __future__ import annotations

__all__: typing.Final[typing.List[str]] = ["StatefulCacheImpl"]

import copy
import datetime
import logging
import typing

from hikari import channels
from hikari import emojis
from hikari import errors
from hikari import guilds
from hikari import intents as intents_
from hikari import invites
from hikari import presences
from hikari import snowflakes
from hikari import undefined
from hikari import users
from hikari import voices
from hikari.api import cache
from hikari.utilities import cache as cache_utility
from hikari.utilities import mapping

if typing.TYPE_CHECKING:
    from hikari import traits


_KeyT = typing.TypeVar("_KeyT", bound=typing.Hashable)
_LOGGER: typing.Final[logging.Logger] = logging.getLogger("hikari.cache")
_ValueT = typing.TypeVar("_ValueT")


class _VoidMapping(typing.MutableMapping[_KeyT, _ValueT]):
    """A mapping object that doesn't store any objects and ignores mutation.

    This is used for cases where we'd otherwise be building a new dict just to
    pass it to a chainable method and then let it fall out of scope.
    """

    __slots__: typing.Sequence[str] = ()

    def __delitem__(self, _: _KeyT) -> None:
        return None

    def __getitem__(self, key: _KeyT) -> typing.NoReturn:
        raise KeyError(key)

    def __iter__(self) -> typing.Iterator[_KeyT]:
        yield from ()

    def __len__(self) -> typing.Literal[0]:
        return 0

    def __setitem__(self, _: _KeyT, __: _ValueT) -> None:
        return None


_VOID_MAPPING: typing.Final[typing.MutableMapping[typing.Any, typing.Any]] = _VoidMapping()
"""A constant instance of `_VoidMapping` used within the cache."""


#  TODO: do we want to hide entities that are marked as "deleted" and being kept alive by references?
class StatefulCacheImpl(cache.MutableCache):
    """In-memory cache implementation."""

    __slots__: typing.Sequence[str] = (
        "_app",
        "_private_text_channel_entries",
        "_emoji_entries",
        "_guild_channel_entries",
        "_guild_entries",
        "_intents",
        "_invite_entries",
        "_me",
        "_role_entries",
        "_unknown_custom_emoji_entries",
        "_user_entries",
    )

    # For the sake of keeping things clean, the annotations are being kept separate from the assignment here.
    _app: traits.RESTAware
    _me: typing.Optional[users.OwnUser]
    _private_text_channel_entries: mapping.MappedCollection[snowflakes.Snowflake, cache_utility.PrivateTextChannelData]
    _emoji_entries: mapping.MappedCollection[snowflakes.Snowflake, cache_utility.KnownCustomEmojiData]
    _guild_channel_entries: mapping.MappedCollection[snowflakes.Snowflake, channels.GuildChannel]
    _guild_entries: mapping.MappedCollection[snowflakes.Snowflake, cache_utility.GuildRecord]
    _invite_entries: mapping.MappedCollection[str, cache_utility.InviteData]
    _role_entries: mapping.MappedCollection[snowflakes.Snowflake, guilds.Role]
    _unknown_custom_emoji_entries: mapping.MappedCollection[
        snowflakes.Snowflake,
        cache_utility.GenericRefWrapper[emojis.CustomEmoji],
    ]
    _user_entries: mapping.MappedCollection[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]]
    _intents: typing.Optional[intents_.Intents]

    def __init__(self, app: traits.RESTAware, intents: typing.Optional[intents_.Intents]) -> None:
        self._app = app
        self._me = None
        # Cached Private Channels channels are a special case as there's no sane way to remove them from cache as we'd
        # have to go through all the guilds the app is in to see if it shares any of them with the channel's owner
        # before removing it from the cache so we use a specific MRU implementation to cover private channel de-caching.
        self._private_text_channel_entries = cache_utility.PrivateTextChannelMRUMutableMapping(
            expiry=datetime.timedelta(minutes=5)
        )
        self._emoji_entries = mapping.DictionaryCollection()
        self._guild_channel_entries = mapping.DictionaryCollection()
        self._guild_entries = mapping.DictionaryCollection()
        self._invite_entries = mapping.DictionaryCollection()
        self._role_entries = mapping.DictionaryCollection()
        # This is a purely internal cache used for handling the caching and de-duplicating of the unknown custom emojis
        # found attached to cached presence activities.
        self._unknown_custom_emoji_entries = mapping.DictionaryCollection()
        self._user_entries = mapping.DictionaryCollection()
        self._intents = intents

    def _assert_has_intent(self, intents: intents_.Intents, /) -> None:
        if self._intents is not None and self._intents ^ intents:
            raise errors.MissingIntentError(intents) from None

    def _is_intent_enabled(self, intents: intents_.Intents, /) -> bool:
        return self._intents is None or (self._intents & intents) == intents

    def _build_private_text_channel(
        self,
        channel_data: cache_utility.PrivateTextChannelData,
        cached_users: typing.Optional[
            typing.Mapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]]
        ] = None,
    ) -> channels.PrivateTextChannel:
        if cached_users:
            recipient = copy.copy(cached_users[channel_data.recipient_id].object)
        else:
            recipient = copy.copy(self._user_entries[channel_data.recipient_id].object)

        return channel_data.build_entity(channels.PrivateTextChannel, app=self._app, recipient=recipient)

    def clear_private_text_channels(self) -> cache.CacheView[snowflakes.Snowflake, channels.PrivateTextChannel]:
        if not self._private_text_channel_entries:
            return cache_utility.EmptyCacheView()

        cached_channels = self._private_text_channel_entries
        self._private_text_channel_entries = mapping.DictionaryCollection()
        cached_users = {}

        for user_id in cached_channels:
            cached_users[user_id] = self._user_entries[user_id]
            self._garbage_collect_user(user_id, decrement=1)

        return cache_utility.StatefulCacheMappingView(
            cached_channels, builder=lambda channel: self._build_private_text_channel(channel, cached_users)
        )

    def delete_private_text_channel(
        self, user_id: snowflakes.Snowflake, /
    ) -> typing.Optional[channels.PrivateTextChannel]:
        channel_data = self._private_text_channel_entries.pop(user_id, None)
        if channel_data is None:
            return None

        channel = self._build_private_text_channel(channel_data)
        self._garbage_collect_user(user_id, decrement=1)
        return channel

    def get_private_text_channel(
        self, user_id: snowflakes.Snowflake, /
    ) -> typing.Optional[channels.PrivateTextChannel]:
        if user_id in self._private_text_channel_entries:
            return self._build_private_text_channel(self._private_text_channel_entries[user_id])

        return None

    def get_private_text_channels_view(self) -> cache.CacheView[snowflakes.Snowflake, channels.PrivateTextChannel]:
        if not self._private_text_channel_entries:
            return cache_utility.EmptyCacheView()

        cached_channels = self._private_text_channel_entries.freeze()
        cached_users = {user_id: self._user_entries[user_id] for user_id in cached_channels}
        return cache_utility.StatefulCacheMappingView(
            cached_channels,
            builder=lambda channel: self._build_private_text_channel(channel, cached_users),
        )

    def set_private_text_channel(self, channel: channels.PrivateTextChannel, /) -> None:
        self.set_user(channel.recipient)

        if channel.recipient.id not in self._private_text_channel_entries:
            self._increment_user_ref_count(channel.recipient.id)

        self._private_text_channel_entries[
            channel.recipient.id
        ] = cache_utility.PrivateTextChannelData.build_from_entity(channel)

    def update_private_text_channel(
        self, channel: channels.PrivateTextChannel, /
    ) -> typing.Tuple[typing.Optional[channels.PrivateTextChannel], typing.Optional[channels.PrivateTextChannel]]:
        cached_channel = self.get_private_text_channel(channel.recipient.id)
        self.set_private_text_channel(channel)
        return cached_channel, self.get_private_text_channel(channel.recipient.id)

    def _build_emoji(
        self,
        emoji_data: cache_utility.KnownCustomEmojiData,
        cached_users: typing.Optional[
            typing.Mapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]]
        ] = None,
    ) -> emojis.KnownCustomEmoji:
        user: typing.Optional[users.User] = None
        if cached_users is not None and emoji_data.user_id is not None:
            user = copy.copy(cached_users[emoji_data.user_id].object)
        elif emoji_data.user_id is not None:
            user = copy.copy(self._user_entries[emoji_data.user_id].object)

        return emoji_data.build_entity(emojis.KnownCustomEmoji, app=self._app, user=user)

    def _increment_emoji_ref_count(self, emoji_id: snowflakes.Snowflake, increment: int = 1) -> None:
        self._emoji_entries[emoji_id].ref_count += increment

    def _garbage_collect_emoji(self, emoji_id: snowflakes.Snowflake, decrement: int = 0) -> None:
        emoji_data = self._emoji_entries.get(emoji_id)

        if emoji_data is None:
            return None

        emoji_data.ref_count -= decrement

        if self._can_remove_emoji(emoji_data):
            del self._emoji_entries[emoji_id]

    @staticmethod
    def _can_remove_emoji(emoji: cache_utility.KnownCustomEmojiData) -> bool:
        return emoji.has_been_deleted is True and emoji.ref_count < 1

    def _clear_emojis(
        self,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> cache.CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        emoji_ids: typing.Iterable[snowflakes.Snowflake]
        if guild_id is undefined.UNDEFINED:
            emoji_ids = self._emoji_entries.freeze()
        else:
            guild_record = self._guild_entries.get(guild_id)
            # TODO: explicit is not None vs implicit if statement consistency.
            if guild_record is None or guild_record.emojis is None:
                return cache_utility.EmptyCacheView()

            emoji_ids = guild_record.emojis
            guild_record.emojis = None
            self._remove_guild_record_if_empty(guild_id)

        cached_emojis = {}
        cached_users = {}

        for emoji_id in emoji_ids:
            emoji_data = self._emoji_entries[emoji_id]
            emoji_data.has_been_deleted = True
            if not self._can_remove_emoji(emoji_data):
                continue

            del self._emoji_entries[emoji_id]
            cached_emojis[emoji_id] = emoji_data

            if emoji_data.user_id is not None:
                cached_users[emoji_data.user_id] = self._user_entries[emoji_data.user_id]
                self._garbage_collect_user(emoji_data.user_id, decrement=1)

        return cache_utility.StatefulCacheMappingView(
            cached_emojis, builder=lambda emoji: self._build_emoji(emoji, cached_users=cached_users)
        )

    def clear_emojis(self) -> cache.CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        result = self._clear_emojis()

        for guild_id, guild_record in self._guild_entries.freeze().items():
            if guild_record.emojis is not None:  # TODO: add test coverage for this.
                guild_record.emojis = None
                self._remove_guild_record_if_empty(guild_id)

        return result

    def clear_emojis_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        return self._clear_emojis(guild_id)

    def delete_emoji(self, emoji_id: snowflakes.Snowflake, /) -> typing.Optional[emojis.KnownCustomEmoji]:
        emoji_data = self._emoji_entries.pop(emoji_id, None)
        if emoji_data is None:
            return None

        emoji_data.has_been_deleted = True
        if not self._can_remove_emoji(emoji_data):
            return None

        emoji = self._build_emoji(emoji_data)

        if emoji_data.user_id is not None:
            self._garbage_collect_user(emoji_data.user_id, decrement=1)

        guild_record = self._guild_entries.get(emoji_data.guild_id)
        if guild_record and guild_record.emojis:  # TODO: should this make assumptions and be flat?
            guild_record.emojis.remove(emoji_id)

            if not guild_record.emojis:
                guild_record.emojis = None

        return emoji

    def get_emoji(self, emoji_id: snowflakes.Snowflake, /) -> typing.Optional[emojis.KnownCustomEmoji]:
        return self._build_emoji(self._emoji_entries[emoji_id]) if emoji_id in self._emoji_entries else None

    def _get_emojis_view(  # TODO: split out the two cases (specific guild vs global)
        self, guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED
    ) -> cache.CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        cached_emojis = {}
        cached_users = {}
        emoji_ids: typing.Iterable[snowflakes.Snowflake]

        if guild_id is undefined.UNDEFINED:
            emoji_ids = self._emoji_entries.freeze()
        else:
            guild_record = self._guild_entries.get(guild_id)
            if guild_record is None or not guild_record.emojis:
                return cache_utility.EmptyCacheView()

            emoji_ids = tuple(guild_record.emojis)

        for emoji_id in emoji_ids:
            emoji_data = self._emoji_entries[emoji_id]
            cached_emojis[emoji_id] = emoji_data

            if emoji_data.user_id is not None:
                cached_users[emoji_data.user_id] = self._user_entries[emoji_data.user_id]

        return cache_utility.StatefulCacheMappingView(
            cached_emojis, builder=lambda emoji: self._build_emoji(emoji, cached_users=cached_users)
        )

    def get_emojis_view(self) -> cache.CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        return self._get_emojis_view()

    def get_emojis_view_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, emojis.KnownCustomEmoji]:
        return self._get_emojis_view(guild_id=guild_id)

    def set_emoji(self, emoji: emojis.KnownCustomEmoji, /) -> None:
        if emoji.user is not None:
            self.set_user(emoji.user)
            if emoji.id not in self._emoji_entries:
                self._increment_user_ref_count(emoji.user.id)

        self._emoji_entries[emoji.id] = cache_utility.KnownCustomEmojiData.build_from_entity(emoji)
        guild_container = self._get_or_create_guild_record(emoji.guild_id)

        if guild_container.emojis is None:  # TODO: add test cases when it is not None?
            guild_container.emojis = cache_utility.IDTable()

        guild_container.emojis.add(emoji.id)

    def update_emoji(
        self, emoji: emojis.KnownCustomEmoji, /
    ) -> typing.Tuple[typing.Optional[emojis.KnownCustomEmoji], typing.Optional[emojis.KnownCustomEmoji]]:
        cached_emoji = self.get_emoji(emoji.id)
        self.set_emoji(emoji)
        return cached_emoji, self.get_emoji(emoji.id)

    def _remove_guild_record_if_empty(self, guild_id: snowflakes.Snowflake) -> None:
        if guild_id in self._guild_entries and not self._guild_entries[guild_id]:
            del self._guild_entries[guild_id]

    def _get_or_create_guild_record(self, guild_id: snowflakes.Snowflake) -> cache_utility.GuildRecord:
        if guild_id not in self._guild_entries:
            self._guild_entries[guild_id] = cache_utility.GuildRecord()

        return self._guild_entries[guild_id]

    def clear_guilds(self) -> cache.CacheView[snowflakes.Snowflake, guilds.GatewayGuild]:
        cached_guilds = {}

        for guild_id, guild_record in self._guild_entries.freeze().items():
            if guild_record.guild is None:
                continue

            cached_guilds[guild_id] = guild_record.guild
            guild_record.guild = None
            guild_record.is_available = None
            self._remove_guild_record_if_empty(guild_id)

        return (
            cache_utility.StatefulCacheMappingView(cached_guilds) if cached_guilds else cache_utility.EmptyCacheView()
        )

    def delete_guild(self, guild_id: snowflakes.Snowflake, /) -> typing.Optional[guilds.GatewayGuild]:
        if guild_id not in self._guild_entries:
            return None

        guild_record = self._guild_entries[guild_id]
        guild = guild_record.guild

        if guild is not None:
            guild_record.guild = None
            guild_record.is_available = None
            self._remove_guild_record_if_empty(guild_id)

        return guild

    def get_guild(self, guild_id: snowflakes.Snowflake, /) -> typing.Optional[guilds.GatewayGuild]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is not None:
            if guild_record.guild and not guild_record.is_available:
                raise errors.UnavailableGuildError(guild_record.guild) from None

            return copy.copy(guild_record.guild)

        return None

    def get_guilds_view(self) -> cache.CacheView[snowflakes.Snowflake, guilds.GatewayGuild]:
        # TODO: do we want to include unavailable guilds here or hide them?
        entries = self._guild_entries.freeze()
        # We may have a guild record without a guild object in cases where we're caching other entities that belong to
        # the guild therefore we want to make sure record.guild isn't None.
        results = {sf: guild_record.guild for sf, guild_record in entries.items() if guild_record.guild}
        return cache_utility.StatefulCacheMappingView(results) if results else cache_utility.EmptyCacheView()

    def set_guild(self, guild: guilds.GatewayGuild, /) -> None:
        guild_record = self._get_or_create_guild_record(guild.id)
        guild_record.guild = copy.copy(guild)
        guild_record.is_available = True

    def set_guild_availability(self, guild_id: snowflakes.Snowflake, is_available: bool, /) -> None:
        guild_record = self._get_or_create_guild_record(guild_id=guild_id)
        guild_record.is_available = is_available  # TODO: only set this if guild object cached?

    # TODO: is this the best way to handle this?
    def set_initial_unavailable_guilds(self, guild_ids: typing.Collection[snowflakes.Snowflake], /) -> None:
        # Invoked when we receive ON_READY, assume all of these are unavailable on startup.
        self._guild_entries = mapping.DictionaryCollection(
            {guild_id: cache_utility.GuildRecord(is_available=False) for guild_id in guild_ids}
        )

    def update_guild(
        self, guild: guilds.GatewayGuild, /
    ) -> typing.Tuple[typing.Optional[guilds.GatewayGuild], typing.Optional[guilds.GatewayGuild]]:
        guild = copy.copy(guild)
        guild_record = self._guild_entries.get(guild.id)
        cached_guild = guild_record.guild if guild_record is not None else None

        # We have to manually update these because inconsistency by Discord.
        if cached_guild is not None:
            guild.member_count = cached_guild.member_count
            guild.joined_at = cached_guild.joined_at
            guild.is_large = cached_guild.is_large

        self.set_guild(guild)
        guild_record = self._guild_entries.get(guild.id)
        return cached_guild, guild_record.guild if guild_record is not None else None

    def clear_guild_channels(self) -> cache.CacheView[snowflakes.Snowflake, channels.GuildChannel]:
        cached_channels = self._guild_channel_entries
        self._guild_channel_entries = mapping.DictionaryCollection()

        for guild_id, guild_record in self._guild_entries.freeze().items():
            if guild_record.channels is not None:
                guild_record.channels = None
                self._remove_guild_record_if_empty(guild_id)

        return cache_utility.StatefulCacheMappingView(cached_channels)

    def clear_guild_channels_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, channels.GuildChannel]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.channels is None:
            return cache_utility.EmptyCacheView()

        # Tuple casts like this avoid edge case issues which would be caused by guild_record.channels being modified
        # while we're iterating over it
        cached_channels = {sf: self._guild_channel_entries.pop(sf) for sf in tuple(guild_record.channels)}
        guild_record.channels = None
        self._remove_guild_record_if_empty(guild_id)
        return cache_utility.StatefulCacheMappingView(cached_channels)

    def delete_guild_channel(self, channel_id: snowflakes.Snowflake, /) -> typing.Optional[channels.GuildChannel]:
        channel = self._guild_channel_entries.pop(channel_id, None)

        if channel is None:
            return None

        # TODO: flat and make assumptions?
        guild_record = self._guild_entries.get(channel.guild_id)
        if guild_record and guild_record.channels is not None:
            guild_record.channels.remove(channel_id)
            if not guild_record.channels:
                guild_record.channels = None
                self._remove_guild_record_if_empty(channel.guild_id)

        return channel

    def get_guild_channel(self, channel_id: snowflakes.Snowflake, /) -> typing.Optional[channels.GuildChannel]:
        channel = self._guild_channel_entries.get(channel_id)
        return cache_utility.copy_guild_channel(channel) if channel is not None else None

    def get_guild_channels_view(self) -> cache.CacheView[snowflakes.Snowflake, channels.GuildChannel]:
        return cache_utility.GuildChannelCacheMappingView(self._guild_channel_entries.freeze())

    def get_guild_channels_view_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, channels.GuildChannel]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or not guild_record.channels:
            return cache_utility.EmptyCacheView()

        # Tuple casts like this avoids edge case issues which would be caused by arrays being modified while we're
        # iterating over them.
        cached_channels = {sf: self._guild_channel_entries[sf] for sf in tuple(guild_record.channels)}

        def sorter(args: typing.Tuple[snowflakes.Snowflake, channels.GuildChannel]) -> typing.Tuple[int, int, int]:
            channel = args[1]
            if isinstance(channel, channels.GuildCategory):
                return channel.position, -1, 0

            parent_position = -1 if channel.parent_id is None else cached_channels[channel.parent_id].position

            if not isinstance(channel, channels.GuildVoiceChannel):
                return parent_position, 0, channel.position

            return parent_position, 1, channel.position

        cached_channels = dict(sorted(cached_channels.items(), key=sorter))
        return cache_utility.GuildChannelCacheMappingView(cached_channels)

    def set_guild_channel(self, channel: channels.GuildChannel, /) -> None:
        self._guild_channel_entries[channel.id] = cache_utility.copy_guild_channel(channel)
        guild_record = self._get_or_create_guild_record(channel.guild_id)

        if guild_record.channels is None:
            guild_record.channels = cache_utility.IDTable()

        guild_record.channels.add(channel.id)

    def update_guild_channel(
        self, channel: channels.GuildChannel, /
    ) -> typing.Tuple[typing.Optional[channels.GuildChannel], typing.Optional[channels.GuildChannel]]:
        cached_channel = self.get_guild_channel(channel.id)
        self.set_guild_channel(channel)
        return cached_channel, self.get_guild_channel(channel.id)

    def _build_invite(
        self,
        invite_data: cache_utility.InviteData,
        cached_users: undefined.UndefinedOr[
            typing.Mapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]]
        ] = undefined.UNDEFINED,
    ) -> invites.InviteWithMetadata:
        inviter: typing.Optional[users.User] = None
        if cached_users is not undefined.UNDEFINED and invite_data.inviter_id is not None:
            inviter = copy.copy(cached_users[invite_data.inviter_id].object)
        elif invite_data.inviter_id is not None:
            inviter = copy.copy(self._user_entries[invite_data.inviter_id].object)

        target_user: typing.Optional[users.User] = None
        if cached_users is not undefined.UNDEFINED and invite_data.target_user_id is not None:
            target_user = copy.copy(cached_users[invite_data.target_user_id].object)
        elif invite_data.target_user_id is not None:
            target_user = copy.copy(self._user_entries[invite_data.target_user_id].object)

        return invite_data.build_entity(
            invites.InviteWithMetadata, app=self._app, inviter=inviter, target_user=target_user
        )

    def _clear_invites(  # TODO: split out into two cases (global and specific guild)
        self,
        guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED,
    ) -> cache.CacheView[str, invites.InviteWithMetadata]:
        invite_codes: typing.Iterable[str]
        if guild_id is not undefined.UNDEFINED:
            guild_record = self._guild_entries.get(guild_id)

            if guild_record is None or guild_record.invites is None:
                return cache_utility.EmptyCacheView()

            # Tuple casts like this avoids edge case issues which would be caused by arrays being modified while we're
            # iterating over them.
            invite_codes = tuple(guild_record.invites)
            guild_record.invites = None
            self._remove_guild_record_if_empty(guild_id)

        else:
            invite_codes = self._invite_entries.freeze()

        cached_invites = {}
        cached_users = {}

        for code in invite_codes:
            invite_data = self._invite_entries.pop(code)
            cached_invites[code] = invite_data

            if invite_data.inviter_id is not None:
                cached_users[invite_data.inviter_id] = self._user_entries[invite_data.inviter_id]
                self._garbage_collect_user(invite_data.inviter_id, decrement=1)

            if invite_data.target_user_id is not None:
                cached_users[invite_data.target_user_id] = self._user_entries[invite_data.target_user_id]
                self._garbage_collect_user(invite_data.target_user_id, decrement=1)

        return cache_utility.StatefulCacheMappingView(
            cached_invites, builder=lambda invite_data: self._build_invite(invite_data, cached_users=cached_users)
        )

    def clear_invites(self) -> cache.CacheView[str, invites.InviteWithMetadata]:
        return self._clear_invites()

    def clear_invites_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[str, invites.InviteWithMetadata]:
        return self._clear_invites(guild_id=guild_id)

    def clear_invites_for_channel(
        self, guild_id: snowflakes.Snowflake, channel_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[str, invites.InviteWithMetadata]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.invites is None:
            return cache_utility.EmptyCacheView()

        cached_invites = {}
        cached_users = {}

        # Tuple casts like this avoids edge case issues which would be caused by arrays being modified while we're
        # iterating over them.
        for code in tuple(guild_record.invites):
            invite_data = self._invite_entries[code]
            if invite_data.channel_id != channel_id:
                continue

            cached_invites[code] = invite_data
            del self._invite_entries[code]
            guild_record.invites.remove(code)

            if invite_data.inviter_id is not None:
                cached_users[invite_data.inviter_id] = self._user_entries[invite_data.inviter_id]
                self._garbage_collect_user(invite_data.inviter_id, decrement=1)

            if invite_data.target_user_id is not None:
                cached_users[invite_data.target_user_id] = self._user_entries[invite_data.target_user_id]
                self._garbage_collect_user(invite_data.target_user_id, decrement=1)

        if not guild_record.invites:
            guild_record.invites = None
            self._remove_guild_record_if_empty(guild_id)

        return cache_utility.StatefulCacheMappingView(
            cached_invites, builder=lambda invite_data: self._build_invite(invite_data, cached_users=cached_users)
        )

    def delete_invite(self, code: str, /) -> typing.Optional[invites.InviteWithMetadata]:
        if code not in self._invite_entries:
            return None

        invite = self._build_invite(self._invite_entries.pop(code))

        if invite.inviter is not None:
            self._garbage_collect_user(invite.inviter.id, decrement=1)

        if invite.target_user is not None:
            self._garbage_collect_user(invite.target_user.id, decrement=1)

        if invite.guild_id is not None:  # TODO: test case when this is None?
            guild_record = self._guild_entries.get(invite.guild_id)
            if guild_record and guild_record.invites is not None:
                guild_record.invites.remove(code)

                if not guild_record.invites:
                    guild_record.invites = None  # TODO: test when this is set to None
                    self._remove_guild_record_if_empty(invite.guild_id)

        return invite

    def get_invite(self, code: str, /) -> typing.Optional[invites.InviteWithMetadata]:
        return self._build_invite(self._invite_entries[code]) if code in self._invite_entries else None

    def _get_invites_view(  # TODO: split out into two separate cases (global and specific guild)
        self, guild_id: undefined.UndefinedOr[snowflakes.Snowflake] = undefined.UNDEFINED
    ) -> cache.CacheView[str, invites.InviteWithMetadata]:
        invite_ids: typing.Iterable[str]
        if guild_id is undefined.UNDEFINED:
            invite_ids = self._invite_entries.freeze()

        else:
            guild_entry = self._guild_entries.get(guild_id)
            if guild_entry is None or guild_entry.invites is None:
                return cache_utility.EmptyCacheView()

            # Tuple casts like this avoids edge case issues which would be caused by arrays being modified while we're
            # iterating over them.
            invite_ids = tuple(guild_entry.invites)

        cached_invites = {}
        cached_users = {}

        for code in invite_ids:
            invite_data = self._invite_entries[code]
            cached_invites[code] = invite_data

            if invite_data.inviter_id is not None:
                cached_users[invite_data.inviter_id] = self._user_entries[invite_data.inviter_id]

            if invite_data.target_user_id is not None:
                cached_users[invite_data.target_user_id] = self._user_entries[invite_data.target_user_id]

        return cache_utility.StatefulCacheMappingView(
            cached_invites, builder=lambda invite_data: self._build_invite(invite_data, cached_users=cached_users)
        )

    def get_invites_view(self) -> cache.CacheView[str, invites.InviteWithMetadata]:
        return self._get_invites_view()

    def get_invites_view_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[str, invites.InviteWithMetadata]:
        return self._get_invites_view(guild_id=guild_id)

    def get_invites_view_for_channel(
        self,
        guild_id: snowflakes.Snowflake,
        channel_id: snowflakes.Snowflake,
        /,
    ) -> cache.CacheView[str, invites.InviteWithMetadata]:
        guild_entry = self._guild_entries.get(guild_id)
        if guild_entry is None or guild_entry.invites is None:
            return cache_utility.EmptyCacheView()

        cached_invites = {}
        cached_users = {}
        invite_ids: typing.Iterable[str]

        # Tuple casts like this avoids edge case issues which would be caused by arrays being modified while we're
        # iterating over them.
        for code in tuple(guild_entry.invites):
            invite_data = self._invite_entries[code]
            if invite_data.channel_id != channel_id:
                continue

            cached_invites[code] = invite_data
            guild_entry.invites.remove(code)
            del self._invite_entries[code]

            if invite_data.inviter_id is not None:
                cached_users[invite_data.inviter_id] = self._user_entries[invite_data.inviter_id]

            if invite_data.target_user_id is not None:
                cached_users[invite_data.target_user_id] = self._user_entries[invite_data.target_user_id]

        if not guild_entry.channels:  # TODO: test coverage
            guild_entry.channels = None
            self._remove_guild_record_if_empty(guild_id)

        return cache_utility.StatefulCacheMappingView(
            cached_invites, builder=lambda invite_data: self._build_invite(invite_data, cached_users=cached_users)
        )

    def set_invite(self, invite: invites.InviteWithMetadata, /) -> None:
        if invite.inviter is not None:
            self.set_user(invite.inviter)
            if invite.code not in self._invite_entries:
                self._increment_user_ref_count(invite.inviter.id)

        if invite.target_user is not None:
            self.set_user(invite.target_user)
            if invite.code not in self._invite_entries:
                self._increment_user_ref_count(invite.target_user.id)

        self._invite_entries[invite.code] = cache_utility.InviteData.build_from_entity(invite)
        if invite.guild_id:
            guild_entry = self._get_or_create_guild_record(invite.guild_id)

            if guild_entry.invites is None:
                guild_entry.invites = []

            guild_entry.invites.append(invite.code)

    def update_invite(
        self, invite: invites.InviteWithMetadata, /
    ) -> typing.Tuple[typing.Optional[invites.InviteWithMetadata], typing.Optional[invites.InviteWithMetadata]]:
        cached_invite = self.get_invite(invite.code)
        self.set_invite(invite)
        return cached_invite, self.get_invite(invite.code)

    def delete_me(self) -> typing.Optional[users.OwnUser]:
        cached_user = self._me
        self._me = None
        return cached_user

    def get_me(self) -> typing.Optional[users.OwnUser]:
        return copy.copy(self._me)

    def set_me(self, user: users.OwnUser, /) -> None:
        self._me = copy.copy(user)

    def update_me(
        self, user: users.OwnUser, /
    ) -> typing.Tuple[typing.Optional[users.OwnUser], typing.Optional[users.OwnUser]]:
        _LOGGER.debug("setting my user to %s", user)
        cached_user = self.get_me()
        self.set_me(user)
        return cached_user, self._me

    def _build_member(
        self,
        member_data: cache_utility.MemberData,
        cached_users: typing.Optional[
            typing.Mapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]]
        ] = None,
    ) -> guilds.Member:
        if cached_users is None:
            user = copy.copy(self._user_entries[member_data.id].object)
        else:
            user = copy.copy(cached_users[member_data.id].object)

        return member_data.build_entity(guilds.Member, user=user)

    @staticmethod
    def _can_remove_member(member: cache_utility.MemberData, guild_record: cache_utility.GuildRecord) -> bool:
        if member.has_been_deleted is False:
            return False

        return bool(not guild_record.voice_states or member.id not in guild_record.voice_states)

    def _garbage_collect_member(
        self, guild_record: cache_utility.GuildRecord, member: cache_utility.MemberData
    ) -> None:
        if guild_record.members is None or member.id not in guild_record.members:
            return

        if not self._can_remove_member(member, guild_record):
            return

        del guild_record.members[member.id]
        if not guild_record.members:
            guild_record.members = None
            self._remove_guild_record_if_empty(member.guild_id)

    def _chainable_remove_member(
        self, member: cache_utility.MemberData, guild_record: cache_utility.GuildRecord
    ) -> typing.Optional[cache_utility.MemberData]:
        assert guild_record.members is not None
        member.has_been_deleted = True
        if not self._can_remove_member(member, guild_record):
            return None

        self._garbage_collect_user(member.id, decrement=1)
        del guild_record.members[member.id]

        if not guild_record.members:
            guild_record.members = None
            self._remove_guild_record_if_empty(member.guild_id)

        return member

    def clear_members(
        self,
    ) -> cache.CacheView[snowflakes.Snowflake, cache.CacheView[snowflakes.Snowflake, guilds.Member]]:
        views = {}
        cached_users = self._user_entries.freeze()

        def build_member(member: cache_utility.MemberData) -> guilds.Member:
            return self._build_member(member, cached_users=cached_users)

        for guild_id, guild_record in self._guild_entries.freeze().items():
            if not guild_record.members:
                continue

            #  This takes roughly half the time a two-layered for loop where we
            #  assign to the members dict on every inner-iteration takes.
            members_gen = (
                self._chainable_remove_member(m, guild_record) for m in guild_record.members.freeze().values()
            )
            # _chainable_remove_member will only return the member data object if they could be removed, else None.
            cached_members = {member.id: member for member in members_gen if member is not None}
            views[guild_id] = cache_utility.StatefulCacheMappingView(cached_members, builder=build_member)

        return cache_utility.StatefulCacheMappingView(views)

    def clear_members_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return cache_utility.EmptyCacheView()

        cached_members = guild_record.members.freeze()
        members_gen = (self._chainable_remove_member(m, guild_record) for m in cached_members.values())
        # _chainable_remove_member will only return the member data object if they could be removed, else None.
        cached_members = {member.id: member for member in members_gen if member is not None}
        cached_users = {user_id: self._user_entries[user_id] for user_id in cached_members}
        return cache_utility.StatefulCacheMappingView(
            cached_members, builder=lambda member: self._build_member(member, cached_users=cached_users)
        )

    def delete_member(
        self, guild_id: snowflakes.Snowflake, user_id: snowflakes.Snowflake, /
    ) -> typing.Optional[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return None

        member_data = guild_record.members.get(user_id)
        if member_data is None:
            return None

        member = self._build_member(member_data)
        # _chainable_remove_member will only return the member data object if they could be removed, else None.
        return member if self._chainable_remove_member(member_data, guild_record) is not None else None

    def get_member(
        self, guild_id: snowflakes.Snowflake, user_id: snowflakes.Snowflake, /
    ) -> typing.Optional[guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return None

        member = guild_record.members.get(user_id)
        return self._build_member(member) if member is not None else None

    def get_members_view(
        self,
    ) -> cache.CacheView[snowflakes.Snowflake, cache.CacheView[snowflakes.Snowflake, guilds.Member]]:
        cached_users = self._user_entries.freeze()

        def member_builder(member: cache_utility.MemberData) -> guilds.Member:
            return self._build_member(member, cached_users=cached_users)

        return cache_utility.Cache3DMappingView(
            {
                guild_id: cache_utility.StatefulCacheMappingView(view.members, builder=member_builder)
                for guild_id, view in self._guild_entries.freeze().items()
                if view.members
            }
        )

    def get_members_view_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, guilds.Member]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.members is None:
            return cache_utility.EmptyCacheView()

        cached_members = {
            user_id: member for user_id, member in guild_record.members.freeze().items() if not member.has_been_deleted
        }
        cached_users = {user_id: self._user_entries[user_id] for user_id in cached_members}

        return cache_utility.StatefulCacheMappingView(
            cached_members, builder=lambda member: self._build_member(member, cached_users=cached_users)
        )

    def set_member(self, member: guilds.Member, /) -> None:
        guild_record = self._get_or_create_guild_record(member.guild_id)
        self.set_user(member.user)
        member_data = cache_utility.MemberData.build_from_entity(member)

        if guild_record.members is None:  # TODO: test when this is not None
            guild_record.members = mapping.DictionaryCollection()

        if member.user.id not in guild_record.members:
            self._increment_user_ref_count(member.user.id)

        guild_record.members[member_data.id] = member_data

    def update_member(
        self, member: guilds.Member, /
    ) -> typing.Tuple[typing.Optional[guilds.Member], typing.Optional[guilds.Member]]:
        cached_member = self.get_member(member.guild_id, member.user.id)
        self.set_member(member)
        return cached_member, self.get_member(member.guild_id, member.user.id)

    def _build_presence(
        self,
        presence_data: cache_utility.MemberPresenceData,
        cached_emojis: typing.Optional[
            typing.Mapping[
                snowflakes.Snowflake,
                typing.Union[cache_utility.GenericRefWrapper[emojis.CustomEmoji], cache_utility.KnownCustomEmojiData],
            ]
        ] = None,
        cached_users: typing.Optional[
            typing.Mapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]]
        ] = None,
    ) -> presences.MemberPresence:
        presence_kwargs: typing.MutableSequence[typing.Mapping[str, typing.Optional[emojis.Emoji]]] = []
        for activity_data in presence_data.activities:
            identifier = activity_data.emoji_id_or_name
            if identifier is None:
                presence_kwargs.append({"emoji": None})

            elif isinstance(identifier, str):
                presence_kwargs.append({"emoji": emojis.UnicodeEmoji(identifier)})

            elif cached_emojis:
                emoji = cached_emojis[identifier]
                if isinstance(emoji, cache_utility.KnownCustomEmojiData):
                    presence_kwargs.append({"emoji": self._build_emoji(emoji, cached_users=cached_users)})
                else:
                    presence_kwargs.append({"emoji": copy.copy(emoji.object)})

            elif identifier in self._emoji_entries:
                presence_kwargs.append(
                    {"emoji": self._build_emoji(self._emoji_entries[identifier], cached_users=cached_users)}
                )

            else:
                presence_kwargs.append({"emoji": copy.copy(self._unknown_custom_emoji_entries[identifier].object)})

        return presence_data.build_entity(presences.MemberPresence, app=self._app, presence_kwargs=presence_kwargs)

    def _garbage_collect_unknown_custom_emoji(self, emoji_id: snowflakes.Snowflake, decrement: int = 0) -> None:
        emoji = self._unknown_custom_emoji_entries.get(emoji_id)
        if emoji is None:
            return None

        emoji.ref_count -= decrement
        if emoji.ref_count < 1:
            del self._unknown_custom_emoji_entries[emoji_id]

    def _chainable_remove_presence_assets(
        self,
        presence_data: cache_utility.MemberPresenceData,
        cached_emojis: typing.MutableMapping[
            snowflakes.Snowflake,
            typing.Union[cache_utility.KnownCustomEmojiData, cache_utility.GenericRefWrapper[emojis.CustomEmoji]],
        ],
        cached_users: typing.MutableMapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]],
    ) -> None:
        for activity_data in presence_data.activities:
            emoji_identifier = activity_data.emoji_id_or_name
            if emoji_identifier is None or isinstance(emoji_identifier, str):
                continue

            if emoji_identifier in self._emoji_entries:
                if emoji_identifier not in cached_emojis:
                    known_emoji_data = self._emoji_entries[emoji_identifier]

                    if known_emoji_data.user_id is not None and known_emoji_data.user_id not in cached_users:
                        cached_users[known_emoji_data.user_id] = self._user_entries[known_emoji_data.user_id]

                    cached_emojis[emoji_identifier] = known_emoji_data

                self._garbage_collect_emoji(emoji_identifier, decrement=-1)

            else:
                if emoji_identifier not in cached_emojis:
                    cached_emojis[emoji_identifier] = self._unknown_custom_emoji_entries[emoji_identifier]

                self._garbage_collect_unknown_custom_emoji(emoji_identifier, decrement=1)

    def clear_presences(
        self,
    ) -> cache.CacheView[snowflakes.Snowflake, cache.CacheView[snowflakes.Snowflake, presences.MemberPresence]]:
        views = {}
        cached_emojis: typing.MutableMapping[
            snowflakes.Snowflake,
            typing.Union[cache_utility.GenericRefWrapper[emojis.CustomEmoji], cache_utility.KnownCustomEmojiData],
        ] = {}
        cached_users: typing.MutableMapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]] = {}

        def build_presence(presence: cache_utility.MemberPresenceData) -> presences.MemberPresence:
            return self._build_presence(presence, cached_users=cached_users, cached_emojis=cached_emojis)

        for guild_id, guild_record in self._guild_entries.freeze().items():
            if not guild_record.presences:
                continue

            cached_presences: typing.MutableMapping[
                snowflakes.Snowflake, cache_utility.MemberPresenceData
            ] = guild_record.presences
            guild_record.presences = None

            for presence in cached_presences.values():
                self._chainable_remove_presence_assets(presence, cached_emojis, cached_users)

            self._remove_guild_record_if_empty(guild_id)
            views[guild_id] = cache_utility.StatefulCacheMappingView(cached_presences, builder=build_presence)

        return cache_utility.StatefulCacheMappingView(views)

    def clear_presences_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.presences is None:
            return cache_utility.EmptyCacheView()

        cached_emojis: typing.MutableMapping[
            snowflakes.Snowflake,
            typing.Union[cache_utility.GenericRefWrapper[emojis.CustomEmoji], cache_utility.KnownCustomEmojiData],
        ] = {}
        cached_users: typing.MutableMapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]] = {}
        cached_presences: typing.MutableMapping[
            snowflakes.Snowflake, cache_utility.MemberPresenceData
        ] = guild_record.presences
        guild_record.presences = None

        for presence in cached_presences.values():
            self._chainable_remove_presence_assets(presence, cached_emojis, cached_users)

        self._remove_guild_record_if_empty(guild_id)
        return cache_utility.StatefulCacheMappingView(
            cached_presences,
            builder=lambda presence_data_: self._build_presence(
                presence_data_, cached_users=cached_users, cached_emojis=cached_emojis
            ),
        )

    def delete_presence(
        self, guild_id: snowflakes.Snowflake, user_id: snowflakes.Snowflake, /
    ) -> typing.Optional[presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.presences is None:
            return None

        presence_data = guild_record.presences.pop(user_id, None)

        if presence_data is None:
            return None

        presence = self._build_presence(presence_data)
        # _VOID_MAPPING is used here to avoid duplicating logic as we don't actually care about the assets there were
        # removed in this case as we've already built the presence.
        self._chainable_remove_presence_assets(presence_data, _VOID_MAPPING, _VOID_MAPPING)

        if not guild_record.presences:
            guild_record.presences = None
            self._remove_guild_record_if_empty(guild_id)

        return presence

    def get_presence(
        self, guild_id: snowflakes.Snowflake, user_id: snowflakes.Snowflake, /
    ) -> typing.Optional[presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.presences is None:
            return None

        return self._build_presence(guild_record.presences[user_id]) if user_id in guild_record.presences else None

    def _chainable_get_presence_assets(
        self,
        presence_data: cache_utility.MemberPresenceData,
        cached_emojis: typing.MutableMapping[
            snowflakes.Snowflake,
            typing.Union[cache_utility.KnownCustomEmojiData, cache_utility.GenericRefWrapper[emojis.CustomEmoji]],
        ],
        cached_users: typing.MutableMapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]],
    ) -> None:
        for activity_data in presence_data.activities:
            emoji_identifier = activity_data.emoji_id_or_name

            if emoji_identifier is None or isinstance(emoji_identifier, str) or emoji_identifier in cached_emojis:
                continue

            if emoji_identifier in self._emoji_entries:
                emoji_data = self._emoji_entries[emoji_identifier]

                if emoji_data.user_id is not None and emoji_data.user_id not in cached_users:
                    cached_users[emoji_data.user_id] = self._user_entries[emoji_data.user_id]

                cached_emojis[emoji_identifier] = emoji_data

            else:
                cached_emojis[emoji_identifier] = self._unknown_custom_emoji_entries[emoji_identifier]

    def get_presences_view(
        self,
    ) -> cache.CacheView[snowflakes.Snowflake, cache.CacheView[snowflakes.Snowflake, presences.MemberPresence]]:
        views = {}

        cached_emojis: typing.MutableMapping[
            snowflakes.Snowflake,
            typing.Union[cache_utility.GenericRefWrapper[emojis.CustomEmoji], cache_utility.KnownCustomEmojiData],
        ] = self._unknown_custom_emoji_entries.freeze()  # type: ignore[assignment]  # TODO: open mypy issue
        cached_users: typing.MutableMapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]] = {}

        def presence_builder(presence: cache_utility.MemberPresenceData) -> presences.MemberPresence:
            return self._build_presence(presence, cached_users=cached_users, cached_emojis=cached_emojis)

        for guild_id, guild_record in self._guild_entries.freeze().items():
            if not guild_record.presences:
                continue

            cached_presences = guild_record.presences.freeze()

            for presence in cached_presences.values():
                self._chainable_get_presence_assets(presence, cached_emojis, cached_users)

            views[guild_id] = cache_utility.StatefulCacheMappingView(cached_presences, builder=presence_builder)

        return cache_utility.Cache3DMappingView(views)

    def get_presences_view_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, presences.MemberPresence]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.presences is None:
            return cache_utility.EmptyCacheView()

        cached_emojis: typing.MutableMapping[
            snowflakes.Snowflake,
            typing.Union[cache_utility.GenericRefWrapper[emojis.CustomEmoji], cache_utility.KnownCustomEmojiData],
        ] = {}
        cached_users: typing.MutableMapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]] = {}
        cached_presences = guild_record.presences.freeze()

        for presence in cached_presences.values():
            self._chainable_get_presence_assets(presence, cached_emojis, cached_users)

        return cache_utility.StatefulCacheMappingView(
            cached_presences,
            builder=lambda presence_data_: self._build_presence(
                presence_data_, cached_users=cached_users, cached_emojis=cached_emojis
            ),
        )

    def set_presence(self, presence: presences.MemberPresence, /) -> None:
        presence_data = cache_utility.MemberPresenceData.build_from_entity(presence)

        for activity in presence.activities:
            emoji = activity.emoji
            if emoji is None or not isinstance(emoji, emojis.CustomEmoji):
                continue

            if emoji.id in self._emoji_entries:
                self._increment_emoji_ref_count(emoji.id)

            elif emoji.id in self._unknown_custom_emoji_entries:
                self._unknown_custom_emoji_entries[emoji.id].ref_count += 1
                self._unknown_custom_emoji_entries[emoji.id].object = copy.copy(emoji)

            else:
                self._unknown_custom_emoji_entries[emoji.id] = cache_utility.GenericRefWrapper(
                    object=copy.copy(emoji), ref_count=1
                )

        guild_record = self._get_or_create_guild_record(presence.guild_id)
        if guild_record.presences is None:
            guild_record.presences = mapping.DictionaryCollection()

        guild_record.presences[presence.user_id] = presence_data

    def update_presence(
        self, presence: presences.MemberPresence, /
    ) -> typing.Tuple[typing.Optional[presences.MemberPresence], typing.Optional[presences.MemberPresence]]:
        cached_presence = self.get_presence(presence.guild_id, presence.user_id)
        self.set_presence(presence)
        return cached_presence, self.get_presence(presence.guild_id, presence.user_id)

    def clear_roles(self) -> cache.CacheView[snowflakes.Snowflake, guilds.Role]:
        if not self._role_entries:
            return cache_utility.EmptyCacheView()

        roles = self._role_entries
        self._role_entries = mapping.DictionaryCollection()

        for guild_id, guild_record in self._guild_entries.freeze().items():
            if guild_record.roles is not None:  # TODO: test coverage for this
                guild_record.roles = None
                self._remove_guild_record_if_empty(guild_id)

        return cache_utility.StatefulCacheMappingView(roles)

    def clear_roles_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, guilds.Role]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or not guild_record.roles:
            return cache_utility.EmptyCacheView()

        view = cache_utility.StatefulCacheMappingView(
            {role_id: self._role_entries[role_id] for role_id in guild_record.roles}
        )
        guild_record.roles = None
        self._remove_guild_record_if_empty(guild_id)
        return view

    def delete_role(self, role_id: snowflakes.Snowflake, /) -> typing.Optional[guilds.Role]:
        role = self._role_entries.pop(role_id, None)
        if role is None:
            return None

        guild_record = self._guild_entries.get(role.guild_id)
        if guild_record and guild_record.roles is not None:
            guild_record.roles.remove(role_id)

            if not guild_record.roles:  # TODO: should this make assumptions and be flat?
                guild_record.roles = None
                self._remove_guild_record_if_empty(role.guild_id)

        return role

    def get_role(self, role_id: snowflakes.Snowflake, /) -> typing.Optional[guilds.Role]:
        return self._role_entries.get(role_id)

    def get_roles_view(self) -> cache.CacheView[snowflakes.Snowflake, guilds.Role]:
        cached_roles = self._role_entries.freeze()
        return cache_utility.StatefulCacheMappingView(cached_roles)

    def get_roles_view_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, guilds.Role]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.roles is None:
            return cache_utility.EmptyCacheView()

        # Tuple casts like this avoids edge case issues which would be caused by arrays being modified while we're
        # iterating over them.
        return cache_utility.StatefulCacheMappingView(
            {role_id: self._role_entries[role_id] for role_id in tuple(guild_record.roles)}
        )

    def set_role(self, role: guilds.Role, /) -> None:
        self._role_entries[role.id] = role
        guild_record = self._get_or_create_guild_record(role.guild_id)

        if guild_record.roles is None:  # TODO: test when this is not None
            guild_record.roles = cache_utility.IDTable()

        guild_record.roles.add(role.id)

    def update_role(
        self, role: guilds.Role, /
    ) -> typing.Tuple[typing.Optional[guilds.Role], typing.Optional[guilds.Role]]:
        cached_role = self.get_role(role.id)
        self.set_role(role)
        return cached_role, self.get_role(role.id)

    @staticmethod
    def _can_remove_user(user_data: typing.Optional[cache_utility.GenericRefWrapper[users.User]]) -> bool:
        return bool(user_data and user_data.ref_count == 0)

    def _increment_user_ref_count(self, user_id: snowflakes.Snowflake, increment: int = 1) -> None:
        self._user_entries[user_id].ref_count += increment

    def _garbage_collect_user(self, user_id: snowflakes.Snowflake, *, decrement: typing.Optional[int] = None) -> None:
        if decrement is not None and user_id in self._user_entries:
            self._increment_user_ref_count(user_id, -decrement)

        if self._can_remove_user(self._user_entries.get(user_id)):
            del self._user_entries[user_id]

    def clear_users(self) -> cache.CacheView[snowflakes.Snowflake, users.User]:
        if not self._user_entries:
            return cache_utility.EmptyCacheView()

        cached_users = {}

        for user_id, user in self._user_entries.freeze().items():
            if user.ref_count > 0:
                continue

            cached_users[user_id] = user.object
            del self._user_entries[user_id]

        return cache_utility.StatefulCacheMappingView(cached_users) if cached_users else cache_utility.EmptyCacheView()

    def delete_user(self, user_id: snowflakes.Snowflake, /) -> typing.Optional[users.User]:
        if self._can_remove_user(self._user_entries.get(user_id)):
            return self._user_entries.pop(user_id).object

        return None

    def get_user(self, user_id: snowflakes.Snowflake, /) -> typing.Optional[users.User]:
        return copy.copy(self._user_entries[user_id].object) if user_id in self._user_entries else None

    def get_users_view(self) -> cache.CacheView[snowflakes.Snowflake, users.User]:
        if not self._user_entries:
            return cache_utility.EmptyCacheView()

        cached_users = self._user_entries.freeze()
        return cache_utility.StatefulCacheMappingView(cached_users, unpack=True)

    def set_user(self, user: users.User, /) -> None:
        try:
            self._user_entries[user.id].object = copy.copy(user)
        except KeyError:
            self._user_entries[user.id] = cache_utility.GenericRefWrapper(object=copy.copy(user), ref_count=0)

    def update_user(
        self, user: users.User, /
    ) -> typing.Tuple[typing.Optional[users.User], typing.Optional[users.User]]:
        cached_user = self.get_user(user.id)
        self.set_user(user)
        return cached_user, self.get_user(user.id)

    def _build_voice_state(
        self,
        voice_data: cache_utility.VoiceStateData,
        cached_members: typing.Optional[typing.Mapping[snowflakes.Snowflake, cache_utility.MemberData]] = None,
        cached_users: typing.Optional[
            typing.Mapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]]
        ] = None,
    ) -> voices.VoiceState:
        if cached_members:
            member = self._build_member(cached_members[voice_data.user_id], cached_users=cached_users)
        else:
            guild_record = self._guild_entries[voice_data.guild_id]
            assert guild_record.members is not None
            member_data = guild_record.members[voice_data.user_id]
            member = self._build_member(member_data, cached_users=cached_users)

        return voice_data.build_entity(voices.VoiceState, app=self._app, member=member)

    def _chainable_remove_voice_state_assets(
        self,
        voice_state: cache_utility.VoiceStateData,
        guild_record: cache_utility.GuildRecord,
        cached_members: typing.MutableMapping[snowflakes.Snowflake, cache_utility.MemberData],
        cached_users: typing.MutableMapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]],
    ) -> None:
        assert guild_record.members is not None
        member = guild_record.members[voice_state.user_id]
        cached_members[voice_state.user_id] = member

        if voice_state.user_id not in cached_users:
            cached_users[voice_state.user_id] = self._user_entries[voice_state.user_id]

        self._garbage_collect_member(guild_record, member)

    def clear_voice_states(
        self,
    ) -> cache.CacheView[snowflakes.Snowflake, cache.CacheView[snowflakes.Snowflake, voices.VoiceState]]:
        views: typing.MutableMapping[
            snowflakes.Snowflake, cache_utility.StatefulCacheMappingView[snowflakes.Snowflake, voices.VoiceState]
        ] = {}
        cached_users: typing.MutableMapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]] = {}

        def builder_generator(
            cached_members_: typing.MutableMapping[snowflakes.Snowflake, cache_utility.MemberData]
        ) -> typing.Callable[[cache_utility.VoiceStateData], voices.VoiceState]:
            return lambda voice_data: self._build_voice_state(
                voice_data, cached_members=cached_members_, cached_users=cached_users
            )

        for guild_id, guild_record in self._guild_entries.freeze().items():
            if not guild_record.voice_states:
                continue

            assert guild_record.members is not None
            cached_voice_states = guild_record.voice_states
            guild_record.voice_states = None
            cached_members: typing.MutableMapping[snowflakes.Snowflake, cache_utility.MemberData] = {}

            for voice_state in cached_voice_states.values():
                self._chainable_remove_voice_state_assets(voice_state, guild_record, cached_members, cached_users)

            self._remove_guild_record_if_empty(guild_id)
            views[guild_id] = cache_utility.StatefulCacheMappingView(
                cached_voice_states, builder=builder_generator(cached_members)
            )

        return cache_utility.StatefulCacheMappingView(views)

    def clear_voice_states_for_channel(
        self, guild_id: snowflakes.Snowflake, channel_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, voices.VoiceState]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or not guild_record.voice_states:
            return cache_utility.EmptyCacheView()

        assert guild_record.members is not None
        cached_members: typing.MutableMapping[snowflakes.Snowflake, cache_utility.MemberData] = {}
        cached_users: typing.MutableMapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]] = {}
        cached_voice_states = {}

        for user_id, voice_state in guild_record.voice_states.items():
            if voice_state.channel_id == channel_id:
                cached_voice_states[voice_state.user_id] = voice_state
                self._chainable_remove_voice_state_assets(voice_state, guild_record, cached_members, cached_users)

        if not guild_record.voice_states:
            guild_record.voice_states = None
            self._remove_guild_record_if_empty(guild_id)

        return cache_utility.StatefulCacheMappingView(
            cached_voice_states,
            builder=lambda voice_state: self._build_voice_state(
                voice_state, cached_members=cached_members, cached_users=cached_users
            ),
        )

    def clear_voice_states_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, voices.VoiceState]:
        guild_record = self._guild_entries.get(guild_id)

        if guild_record is None or guild_record.voice_states is None:
            return cache_utility.EmptyCacheView()

        assert guild_record.members is not None
        cached_voice_states = guild_record.voice_states
        guild_record.voice_states = None
        cached_members: typing.MutableMapping[snowflakes.Snowflake, cache_utility.MemberData] = {}
        cached_users: typing.MutableMapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]] = {}

        for voice_state in cached_voice_states.values():
            self._chainable_remove_voice_state_assets(voice_state, guild_record, cached_members, cached_users)

        self._remove_guild_record_if_empty(guild_id)
        return cache_utility.StatefulCacheMappingView(
            cached_voice_states,
            builder=lambda voice_data: self._build_voice_state(
                voice_data, cached_members=cached_members, cached_users=cached_users
            ),
        )

    def delete_voice_state(
        self, guild_id: snowflakes.Snowflake, user_id: snowflakes.Snowflake, /
    ) -> typing.Optional[voices.VoiceState]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None:
            return None

        voice_state_data = guild_record.voice_states.pop(user_id, None) if guild_record.voice_states else None
        if voice_state_data is None:
            return None

        if not guild_record.voice_states:
            guild_record.voice_states = None

        voice_state = self._build_voice_state(voice_state_data)
        self._chainable_remove_voice_state_assets(voice_state_data, guild_record, _VOID_MAPPING, _VOID_MAPPING)
        self._remove_guild_record_if_empty(guild_id)
        return voice_state

    def get_voice_state(
        self, guild_id: snowflakes.Snowflake, user_id: snowflakes.Snowflake, /
    ) -> typing.Optional[voices.VoiceState]:
        guild_record = self._guild_entries.get(guild_id)
        voice_data = guild_record.voice_states.get(user_id) if guild_record and guild_record.voice_states else None
        return self._build_voice_state(voice_data) if voice_data else None

    def _chainable_get_voice_states_assets(
        self,
        voice_state: cache_utility.VoiceStateData,
        guild_record: cache_utility.GuildRecord,
        cached_members: typing.MutableMapping[snowflakes.Snowflake, cache_utility.MemberData],
        cached_users: typing.MutableMapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]],
    ) -> None:
        assert guild_record.members is not None
        cached_members[voice_state.user_id] = guild_record.members[voice_state.user_id]

        if voice_state.user_id not in cached_users:
            cached_users[voice_state.user_id] = self._user_entries[voice_state.user_id]

    def get_voice_states_view(
        self,
    ) -> cache.CacheView[snowflakes.Snowflake, cache.CacheView[snowflakes.Snowflake, voices.VoiceState]]:
        views: typing.MutableMapping[
            snowflakes.Snowflake, cache_utility.StatefulCacheMappingView[snowflakes.Snowflake, voices.VoiceState]
        ] = {}
        cached_users: typing.MutableMapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]] = {}
        cached_members: typing.MutableMapping[snowflakes.Snowflake, cache_utility.MemberData]

        def builder_generator(
            cached_members_: typing.MutableMapping[snowflakes.Snowflake, cache_utility.MemberData]
        ) -> typing.Callable[[cache_utility.VoiceStateData], voices.VoiceState]:
            return lambda voice_state_: self._build_voice_state(
                voice_state_, cached_members=cached_members_, cached_users=cached_users
            )

        for guild_id, guild_record in self._guild_entries.freeze().items():
            if not guild_record.voice_states:
                continue

            cached_voice_states = guild_record.voice_states.freeze()
            cached_members = {}

            for voice_state in cached_voice_states.values():
                self._chainable_get_voice_states_assets(voice_state, guild_record, cached_members, cached_users)

            views[guild_id] = cache_utility.StatefulCacheMappingView(
                cached_voice_states, builder=builder_generator(cached_members)
            )

        return cache_utility.Cache3DMappingView(views)

    def get_voice_states_view_for_channel(
        self, guild_id: snowflakes.Snowflake, channel_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, voices.VoiceState]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.voice_states is None:
            return cache_utility.EmptyCacheView()

        cached_members: typing.MutableMapping[snowflakes.Snowflake, cache_utility.MemberData] = {}
        cached_users: typing.MutableMapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]] = {}
        cached_voice_states = guild_record.voice_states.freeze()

        for voice_state in cached_voice_states.values():
            if voice_state.channel_id == channel_id:
                self._chainable_get_voice_states_assets(voice_state, guild_record, cached_members, cached_users)

        return cache_utility.StatefulCacheMappingView(
            cached_voice_states,
            builder=lambda voice_data: self._build_voice_state(
                voice_data, cached_members=cached_members, cached_users=cached_users
            ),
        )

    def get_voice_states_view_for_guild(
        self, guild_id: snowflakes.Snowflake, /
    ) -> cache.CacheView[snowflakes.Snowflake, voices.VoiceState]:
        guild_record = self._guild_entries.get(guild_id)
        if guild_record is None or guild_record.voice_states is None:
            return cache_utility.EmptyCacheView()

        voice_states = guild_record.voice_states.freeze()
        cached_members: typing.MutableMapping[snowflakes.Snowflake, cache_utility.MemberData] = {}
        cached_users: typing.MutableMapping[snowflakes.Snowflake, cache_utility.GenericRefWrapper[users.User]] = {}

        for voice_state in voice_states.values():
            self._chainable_get_voice_states_assets(voice_state, guild_record, cached_members, cached_users)

        return cache_utility.StatefulCacheMappingView(
            voice_states,
            builder=lambda voice_data: self._build_voice_state(
                voice_data, cached_members=cached_members, cached_users=cached_users
            ),
        )

    def set_voice_state(self, voice_state: voices.VoiceState, /) -> None:
        guild_record = self._get_or_create_guild_record(voice_state.guild_id)

        if guild_record.voice_states is None:  # TODO: test when this is not None
            guild_record.voice_states = mapping.DictionaryCollection()

        # TODO: account for this method not setting the member in some cases later on
        self.set_member(voice_state.member)
        assert guild_record.members is not None
        guild_record.members[voice_state.member.id].has_been_deleted = True
        guild_record.voice_states[voice_state.user_id] = cache_utility.VoiceStateData.build_from_entity(voice_state)

    def update_voice_state(
        self, voice_state: voices.VoiceState, /
    ) -> typing.Tuple[typing.Optional[voices.VoiceState], typing.Optional[voices.VoiceState]]:
        cached_voice_state = self.get_voice_state(voice_state.guild_id, voice_state.user_id)
        self.set_voice_state(voice_state)
        return cached_voice_state, self.get_voice_state(voice_state.guild_id, voice_state.user_id)
