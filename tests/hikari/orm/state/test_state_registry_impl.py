#!/usr/bin/env python3
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
import contextlib
import copy
import datetime

import cymock as mock
import pytest

from hikari.orm import fabric
from hikari.orm.http import base_http_adapter
from hikari.orm.models import applications
from hikari.orm.models import audit_logs
from hikari.orm.models import bases
from hikari.orm.models import channels
from hikari.orm.models import connections
from hikari.orm.models import emojis
from hikari.orm.models import gateway_bot
from hikari.orm.models import guilds
from hikari.orm.models import integrations
from hikari.orm.models import invites
from hikari.orm.models import members
from hikari.orm.models import messages
from hikari.orm.models import presences
from hikari.orm.models import reactions
from hikari.orm.models import roles
from hikari.orm.models import users
from hikari.orm.models import voices
from hikari.orm.models import webhooks
from hikari.orm.state import base_registry
from hikari.orm.state import state_registry_impl
from tests.hikari import _helpers


@pytest.fixture
def registry():
    fabric_obj = fabric.Fabric()

    # We cant overwrite methods on a slotted class... subclass it to remove that constraint.
    state_registry_obj = _helpers.unslot_class(state_registry_impl.StateRegistryImpl)(fabric_obj, 999, 999)
    fabric_obj.state_registry = state_registry_obj
    return state_registry_obj


# noinspection PyPropertyAccess,PyProtectedMember,PyTypeChecker,PyDunderSlots
@pytest.mark.orm
class TestStateRegistryImpl:
    def test_prepare_unknown_with_callback(self, registry: state_registry_impl.StateRegistryImpl):
        resolver = mock.AsyncMock()
        callback = mock.MagicMock()

        unknown = registry._prepare_unknown_with_callback(1234, resolver, callback, 1, 2, 3, a="a", b="b", c="c")

        assert unknown._future.func is resolver
        assert unknown._future.args == (1, 2, 3)
        assert unknown._future.keywords == dict(a="a", b="b", c="c")
        assert callback in unknown._callbacks

    def test_message_cache_property_returns_message_cache(self, registry: state_registry_impl.StateRegistryImpl):
        cache = _helpers.mock_model(dict)
        registry._message_cache = cache

        assert registry.message_cache is cache

    def test_me_property_returns_OAuth2_user_when_cached(self, registry: state_registry_impl.StateRegistryImpl):
        user = _helpers.mock_model(users.OAuth2User)
        registry._user = user

        assert registry.me is user

    def test_me_property_returns_None_when_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        assert registry.me is None

    def test_increment_reaction_count_for_existing_reaction_does_not_add_new_reaction(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        message_obj = _helpers.mock_model(messages.Message)
        emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        other_emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        reaction_obj = reactions.Reaction(registry.fabric, 5, emoji_obj, 444, 333)
        other_reaction_obj = reactions.Reaction(registry.fabric, 17, other_emoji_obj, 444, 333)
        message_obj.reactions = [other_reaction_obj, reaction_obj]

        registry.increment_reaction_count(message_obj, emoji_obj)

        assert len(message_obj.reactions) == 2

    def test_increment_reaction_count_for_existing_reaction_returns_existing_reaction(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        message_obj = _helpers.mock_model(messages.Message)
        emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        other_emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        reaction_obj = reactions.Reaction(registry.fabric, 5, emoji_obj, 444, 555)
        other_reaction_obj = reactions.Reaction(registry.fabric, 17, other_emoji_obj, 444, 555)
        message_obj.reactions = [other_reaction_obj, reaction_obj]

        new_reaction_obj = registry.increment_reaction_count(message_obj, emoji_obj)

        assert new_reaction_obj is reaction_obj

    def test_increment_reaction_count_for_new_reaction(self, registry: state_registry_impl.StateRegistryImpl):
        message_obj = _helpers.mock_model(messages.Message)
        emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        message_obj.reactions = []

        new_reaction_obj = registry.increment_reaction_count(message_obj, emoji_obj)

        assert isinstance(new_reaction_obj, reactions.Reaction)
        assert new_reaction_obj.count == 1

    def test_increment_reaction_count_for_existing_reaction_increments_count_by_1(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        message_obj = _helpers.mock_model(messages.Message)
        emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        other_emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        reaction_obj = reactions.Reaction(registry.fabric, 5, emoji_obj, 32, 43)
        other_reaction_obj = reactions.Reaction(registry.fabric, 17, other_emoji_obj, 32, 43)
        message_obj.reactions = [other_reaction_obj, reaction_obj]

        new_reaction_obj = registry.increment_reaction_count(message_obj, emoji_obj)

        assert new_reaction_obj.count == 6

    def test_decrement_reaction_count_for_existing_reaction_does_not_remove_reaction_if_reactions_still_exist(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        message_obj = _helpers.mock_model(messages.Message, id=32)
        emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        other_emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        reaction_obj = reactions.Reaction(registry.fabric, 5, emoji_obj, 32, 44)
        other_reaction_obj = reactions.Reaction(registry.fabric, 17, other_emoji_obj, 32, 44)
        message_obj.reactions = [other_reaction_obj, reaction_obj]

        registry.decrement_reaction_count(message_obj, emoji_obj)

        assert len(message_obj.reactions) == 2

    def test_decrement_reaction_count_for_existing_reaction_removes_reaction_if_reactions_no_longer_exist(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        message_obj = _helpers.mock_model(messages.Message)
        emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        other_emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        reaction_obj = reactions.Reaction(registry.fabric, 1, emoji_obj, 32, 43)
        other_reaction_obj = reactions.Reaction(registry.fabric, 17, other_emoji_obj, 32, 43)
        message_obj.reactions = [other_reaction_obj, reaction_obj]

        registry.decrement_reaction_count(message_obj, emoji_obj)

        assert len(message_obj.reactions) == 1
        assert reaction_obj not in message_obj.reactions

    def test_decrement_reaction_count_for_existing_reaction_returns_existing_reaction(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        message_obj = _helpers.mock_model(messages.Message)
        emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        other_emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        reaction_obj = reactions.Reaction(registry.fabric, 5, emoji_obj, 22, 33)
        other_reaction_obj = reactions.Reaction(registry.fabric, 17, other_emoji_obj, 22, 33)
        message_obj.reactions = [other_reaction_obj, reaction_obj]

        new_reaction_obj = registry.decrement_reaction_count(message_obj, emoji_obj)

        assert new_reaction_obj is reaction_obj

    def test_decrement_reaction_count_for_new_reaction_returns_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        message_obj = _helpers.mock_model(messages.Message)
        emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        message_obj.reactions = []

        new_reaction_obj = registry.decrement_reaction_count(message_obj, emoji_obj)

        assert new_reaction_obj is None

    def test_decrement_reaction_count_for_existing_reaction_decrements_count_by_1(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        message_obj = _helpers.mock_model(messages.Message)
        emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        other_emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        reaction_obj = reactions.Reaction(registry.fabric, 5, emoji_obj, 44, 55)
        other_reaction_obj = reactions.Reaction(registry.fabric, 17, other_emoji_obj, 44, 55)
        message_obj.reactions = [other_reaction_obj, reaction_obj]

        new_reaction_obj = registry.decrement_reaction_count(message_obj, emoji_obj)

        assert new_reaction_obj.count == 4

    def test_delete_channel_when_cached_guild_channel(self, registry: state_registry_impl.StateRegistryImpl):
        channel_obj = _helpers.mock_model(channels.GuildTextChannel, id=5678)
        guild_obj = _helpers.mock_model(guilds.Guild, id=1234)
        channel_obj.guild = guild_obj
        registry._guilds = {guild_obj.id: guild_obj}
        guild_obj.channels = {channel_obj.id: channel_obj}
        registry._guild_channels = {channel_obj.id: channel_obj}

        registry.delete_channel(channel_obj)

        assert channel_obj.id not in registry._guild_channels
        assert channel_obj.id not in guild_obj.channels

    def test_delete_channel_when_cached_dm_channel(self, registry: state_registry_impl.StateRegistryImpl):
        channel_obj = _helpers.mock_model(channels.DMChannel, id=5678)
        registry._dm_channels = {channel_obj.id: channel_obj}

        registry.delete_channel(channel_obj)

        assert channel_obj.id not in registry._dm_channels

    def test_delete_channel_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        channel_obj = _helpers.mock_model(channels.Channel)

        registry.delete_channel(channel_obj)

        assert True, "this should exit silently"

    def test_delete_emoji_cached_deletes_from_global_cache(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=10987)
        guild_obj = _helpers.mock_model(guilds.Guild, id=6969)
        guild_obj.emojis = {emoji_obj.id: emoji_obj}
        emoji_obj.guild = guild_obj
        registry._emojis = {emoji_obj.id: emoji_obj}
        registry._guilds = {guild_obj.id: guild_obj}

        registry.delete_emoji(emoji_obj)

        assert emoji_obj.id not in registry._emojis

    def test_delete_emoji_cached_deletes_from_guild(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=10987)
        guild_obj = _helpers.mock_model(guilds.Guild, id=6969)
        guild_obj.emojis = {emoji_obj.id: emoji_obj}
        emoji_obj.guild = guild_obj
        registry._emojis = {emoji_obj.id: emoji_obj}
        registry._guilds = {guild_obj.id: guild_obj}

        registry.delete_emoji(emoji_obj)

        assert emoji_obj.id not in guild_obj.emojis

    def test_delete_emoji_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=10987)
        guild_obj = _helpers.mock_model(guilds.Guild, id=6969)
        emoji_obj.guild = guild_obj

        registry.delete_emoji(emoji_obj)

        assert True, "this should exit silently"

    def test_delete_guild_cached(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=1234)
        registry._guilds = {guild_obj.id: guild_obj}

        registry.delete_guild(guild_obj)

        assert guild_obj.id not in registry._guilds

    def test_delete_guild_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=1234)
        registry._guilds = _helpers.StrongWeakValuedDict()

        registry.delete_guild(guild_obj)

        assert True, "this should exit silently"

    def test_delete_message_cached(self, registry: state_registry_impl.StateRegistryImpl):
        message_obj = _helpers.mock_model(messages.Message, id=1234)
        registry._message_cache = {message_obj.id: message_obj}

        registry.delete_message(message_obj)

        assert message_obj not in registry._message_cache

    def test_delete_message_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        message_obj = _helpers.mock_model(messages.Message, id=1234)

        registry.delete_message(message_obj)

        assert True, "this should exit silently"

    def test_delete_member_cached(self, registry: state_registry_impl.StateRegistryImpl):
        member_obj = _helpers.mock_model(members.Member, id=1234)
        guild_obj = _helpers.mock_model(guilds.Guild, id=5689)
        guild_obj.members = {member_obj.id: member_obj}
        member_obj.guild = guild_obj
        registry._guilds = {guild_obj.id: guild_obj}

        registry.delete_member(member_obj)

        assert member_obj.id not in guild_obj.members

    def test_delete_member_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        member_obj = _helpers.mock_model(members.Member, id=1234)

        registry.delete_member(member_obj)

        assert True, "this should exit silently"

    def test_delete_reaction_cached(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj_to_remove = _helpers.mock_model(emojis.UnicodeEmoji)
        emoji_obj_to_keep = _helpers.mock_model(emojis.UnicodeEmoji)
        user_obj = _helpers.mock_model(users.User, id=6789)
        message_obj = _helpers.mock_model(messages.Message, id=1234)
        message_obj.reactions = [
            reactions.Reaction(registry.fabric, 7, emoji_obj_to_keep, 1234, 2345),
            reactions.Reaction(registry.fabric, 5, emoji_obj_to_remove, 1234, 2345),
        ]

        registry.delete_reaction(message_obj, user_obj, emoji_obj_to_remove)

        assert len(message_obj.reactions) == 1

    def test_delete_reaction_cached_sets_reaction_count_to_0(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj_to_remove = _helpers.mock_model(emojis.UnicodeEmoji)
        emoji_obj_to_keep = _helpers.mock_model(emojis.UnicodeEmoji)
        user_obj = _helpers.mock_model(users.User, id=6789)
        message_obj = _helpers.mock_model(messages.Message, id=1234)
        reaction_obj_to_delete = reactions.Reaction(registry.fabric, 5, emoji_obj_to_remove, 1234, 44)
        reaction_obj_to_keep = reactions.Reaction(registry.fabric, 7, emoji_obj_to_keep, 1234, 44)
        message_obj.reactions = [reaction_obj_to_keep, reaction_obj_to_delete]

        registry.delete_reaction(message_obj, user_obj, emoji_obj_to_remove)

        assert reaction_obj_to_delete.count == 0
        assert reaction_obj_to_keep.count == 7

    def test_delete_reaction_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        user_obj = _helpers.mock_model(users.User, id=6789)
        message_obj = _helpers.mock_model(messages.Message, id=1234)

        registry.delete_reaction(message_obj, user_obj, emoji_obj)

        assert True, "this should exit silently"

    def test_delete_all_reactions_sets_reaction_counts_to_0(self, registry: state_registry_impl.StateRegistryImpl):
        reaction_objs = [
            _helpers.mock_model(reactions.Reaction, count=5),
            _helpers.mock_model(reactions.Reaction, count=7),
            _helpers.mock_model(reactions.Reaction, count=3),
        ]

        message_obj = _helpers.mock_model(messages.Message, reactions=copy.copy(reaction_objs))

        registry.delete_all_reactions(message_obj)

        for reaction_obj in reaction_objs:
            assert reaction_obj.count == 0

    def test_delete_all_reactions_removes_all_reactions(self, registry: state_registry_impl.StateRegistryImpl):
        reaction_objs = [
            _helpers.mock_model(reactions.Reaction, count=5),
            _helpers.mock_model(reactions.Reaction, count=7),
            _helpers.mock_model(reactions.Reaction, count=3),
        ]

        message_obj = _helpers.mock_model(messages.Message, reactions=copy.copy(reaction_objs))

        registry.delete_all_reactions(message_obj)

        assert len(message_obj.reactions) == 0

    def test_delete_role_cached(self, registry: state_registry_impl.StateRegistryImpl):
        role_obj_to_remove = _helpers.mock_model(roles.Role, id=1234)
        role_obj_to_keep = _helpers.mock_model(roles.Role, id=1235)
        guild_obj = _helpers.mock_model(guilds.Guild, id=5678)
        guild_obj.roles = {role_obj_to_remove.id: role_obj_to_remove, role_obj_to_keep.id: role_obj_to_keep}
        role_obj_to_remove.guild_id = guild_obj.id
        role_obj_to_keep.guild_id = guild_obj.id
        member_obj = _helpers.mock_model(members.Member, id=9101112)
        member_obj.roles = [role_obj_to_keep, role_obj_to_remove]
        other_member_obj = _helpers.mock_model(members.Member, id=13141516)
        guild_obj.members = {member_obj.id: member_obj, other_member_obj.id: other_member_obj}
        registry._guilds = {guild_obj.id: guild_obj}
        registry.delete_role(role_obj_to_remove)

        assert len(guild_obj.roles) == 1
        assert len(member_obj.roles) == 1

    def test_delete_role_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        role_obj = _helpers.mock_model(roles.Role, id=1234)
        registry.delete_role(role_obj)

        assert True, "this should exit silently"

    def test_get_channel_by_id_cached_guild_channel(self, registry: state_registry_impl.StateRegistryImpl):
        guild_channel_obj = _helpers.mock_model(channels.GuildTextChannel, id=1234)
        dm_channel_obj = _helpers.mock_model(channels.GroupDMChannel, id=1235)
        registry._guild_channels = {guild_channel_obj.id: guild_channel_obj}
        registry._dm_channels = {dm_channel_obj.id: dm_channel_obj}

        assert registry.get_channel_by_id(guild_channel_obj.id) is guild_channel_obj

    def test_get_channel_by_id_cached_dm_channel(self, registry: state_registry_impl.StateRegistryImpl):
        guild_channel_obj = _helpers.mock_model(channels.GuildTextChannel, id=1234)
        dm_channel_obj = _helpers.mock_model(channels.GroupDMChannel, id=1235)
        registry._guild_channels = {guild_channel_obj.id: guild_channel_obj}
        registry._dm_channels = {dm_channel_obj.id: dm_channel_obj}

        assert registry.get_channel_by_id(dm_channel_obj.id) is dm_channel_obj

    def test_get_channel_by_id_uncached_returns_None(self, registry: state_registry_impl.StateRegistryImpl):
        guild_channel_obj = _helpers.mock_model(channels.GuildTextChannel, id=1234)
        dm_channel_obj = _helpers.mock_model(channels.GroupDMChannel, id=1235)
        registry._guild_channels = {guild_channel_obj.id: guild_channel_obj}
        registry._dm_channels = {dm_channel_obj.id: dm_channel_obj}

        assert registry.get_channel_by_id(1236) is None

    def test_get_mandatory_channel_by_id_cached_guild_channel(self, registry: state_registry_impl.StateRegistryImpl):
        guild_channel_obj = _helpers.mock_model(channels.GuildTextChannel, id=1234)
        dm_channel_obj = _helpers.mock_model(channels.GroupDMChannel, id=1235)
        registry._guild_channels = {guild_channel_obj.id: guild_channel_obj}
        registry._dm_channels = {dm_channel_obj.id: dm_channel_obj}

        assert registry.get_mandatory_channel_by_id(guild_channel_obj.id) is guild_channel_obj

    def test_get_mandatory_channel_by_id_cached_dm_channel(self, registry: state_registry_impl.StateRegistryImpl):
        guild_channel_obj = _helpers.mock_model(channels.GuildTextChannel, id=1234)
        dm_channel_obj = _helpers.mock_model(channels.GroupDMChannel, id=1235)
        registry._guild_channels = {guild_channel_obj.id: guild_channel_obj}
        registry._dm_channels = {dm_channel_obj.id: dm_channel_obj}

        assert registry.get_mandatory_channel_by_id(dm_channel_obj.id) is dm_channel_obj

    def test_get_mandatory_channel_by_id_uncached_returns_unknown(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        guild_channel_obj = _helpers.mock_model(channels.GuildTextChannel, id=1234)
        dm_channel_obj = _helpers.mock_model(channels.GroupDMChannel, id=1235)
        unknown_obj = _helpers.mock_model(bases.UnknownObject, id=1236)
        callback_obj = mock.MagicMock()
        registry.fabric = _helpers.create_autospec(fabric.Fabric)
        registry.fabric.state_registry = registry
        registry.fabric.http_adapter = _helpers.create_autospec(base_http_adapter.BaseHTTPAdapter)
        registry._guild_channels = {guild_channel_obj.id: guild_channel_obj}
        registry._dm_channels = {dm_channel_obj.id: dm_channel_obj}
        registry._prepare_unknown_with_callback = mock.MagicMock(return_value=unknown_obj)

        result = registry.get_mandatory_channel_by_id(1236, callback_obj)
        assert result is unknown_obj
        registry._prepare_unknown_with_callback.assert_called_with(
            1236, registry.fabric.http_adapter.fetch_channel, callback_obj, 1236
        )

    def test_get_guild_emoji_by_id_cached(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=69)
        registry._emojis = {emoji_obj.id: emoji_obj}

        assert registry.get_guild_emoji_by_id(emoji_obj.id) is emoji_obj

    def test_get_guild_emoji_by_id_uncached_returns_None(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=69)
        registry._emojis = {emoji_obj.id: emoji_obj}

        assert registry.get_guild_emoji_by_id(70) is None

    def test_get_mandatory_guild_emoji_by_id_cached(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=69, _guild_id=70)
        registry._emojis = {emoji_obj.id: emoji_obj}

        assert registry.get_mandatory_guild_emoji_by_id(emoji_obj.id, emoji_obj.guild.id) is emoji_obj

    def test_get_mandatory_guild_emoji_by_id_uncached_returns_unknown(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=69)
        unknown_obj = _helpers.mock_model(bases.UnknownObject, id=70)
        callback_obj = mock.MagicMock()
        registry.fabric = _helpers.create_autospec(fabric.Fabric)
        registry.fabric.http_adapter = _helpers.create_autospec(base_http_adapter.BaseHTTPAdapter)
        registry.fabric.state_registry = registry
        registry._prepare_unknown_with_callback = mock.MagicMock(return_value=unknown_obj)
        registry._emojis = {emoji_obj.id: emoji_obj}

        result = registry.get_mandatory_guild_emoji_by_id(70, 123, callback_obj)
        assert result is unknown_obj
        registry._prepare_unknown_with_callback.assert_called_with(
            70, registry.fabric.http_adapter.fetch_guild_emoji, callback_obj, 70, guild=123
        )

    def test_get_guild_by_id_cached(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=69)
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_guild_by_id(guild_obj.id) is guild_obj

    def test_get_guild_by_id_uncached_returns_None(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=69)
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_guild_by_id(70) is None

    def test_get_mandatory_guild_by_id_cached(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=69)
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_mandatory_guild_by_id(69) is guild_obj

    def test_get_mandatory_guild_by_id_uncached_returns_unknown(self, registry: state_registry_impl.StateRegistryImpl):
        unknown_obj = _helpers.mock_model(bases.UnknownObject, id=70)
        callback_obj = mock.MagicMock()
        registry.fabric = _helpers.create_autospec(fabric.Fabric)
        registry.fabric.http_adapter = _helpers.create_autospec(base_http_adapter.BaseHTTPAdapter)
        registry.fabric.state_registry = registry
        registry._prepare_unknown_with_callback = mock.MagicMock(return_value=unknown_obj)

        registry._guilds = {}

        result = registry.get_mandatory_guild_by_id(70, callback_obj)

        registry._prepare_unknown_with_callback.assert_called_with(
            70, registry.fabric.http_adapter.fetch_guild, callback_obj, 70
        )

        assert result is unknown_obj

    def test_get_message_by_id_cached(self, registry: state_registry_impl.StateRegistryImpl):
        message_obj = _helpers.mock_model(messages.Message, id=69)
        registry._message_cache = {message_obj.id: message_obj}

        assert registry.get_message_by_id(message_obj.id) is message_obj

    def test_get_message_by_id_uncached_returns_None(self, registry: state_registry_impl.StateRegistryImpl):
        message_obj = _helpers.mock_model(messages.Message, id=69)
        registry._message_cache = {message_obj.id: message_obj}

        assert registry.get_message_by_id(70) is None

    def test_get_mandatory_message_by_id_cached(self, registry: state_registry_impl.StateRegistryImpl):
        message_obj = _helpers.mock_model(messages.Message, id=69, channel_id=456)
        registry._message_cache = {message_obj.id: message_obj}

        assert registry.get_mandatory_message_by_id(message_obj.id, message_obj.channel_id) is message_obj

    def test_get_mandatory_message_by_id_uncached_returns_unknown(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        registry._message_cache = {}
        unknown_obj = _helpers.mock_model(bases.UnknownObject, id=70)
        callback_obj = mock.MagicMock()
        registry.fabric = _helpers.create_autospec(fabric.Fabric)
        registry.fabric.state_registry = registry
        registry.fabric.http_adapter = _helpers.create_autospec(base_http_adapter.BaseHTTPAdapter)
        registry._prepare_unknown_with_callback = mock.MagicMock(return_value=unknown_obj)

        result = registry.get_mandatory_message_by_id(70, 420, callback_obj)

        registry._prepare_unknown_with_callback.assert_called_with(
            70, registry.fabric.http_adapter.fetch_message, callback_obj, 70, channel=420
        )

        assert result is unknown_obj

    def test_get_role_by_id_cached_guild_cached_role(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=1)
        role_obj = _helpers.mock_model(roles.Role, id=2, guild_id=guild_obj.id)
        guild_obj.roles = {role_obj.id: role_obj}
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_role_by_id(guild_obj.id, role_obj.id) is role_obj

    def test_get_role_by_id_cached_guild_uncached_role(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=1)
        guild_obj.roles = _helpers.StrongWeakValuedDict()
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_role_by_id(guild_obj.id, 2) is None

    def test_get_role_by_id_uncached_guild_uncached_role(self, registry: state_registry_impl.StateRegistryImpl):
        registry._guilds = _helpers.StrongWeakValuedDict()

        assert registry.get_role_by_id(1, 2) is None

    @pytest.mark.asyncio
    async def test__role_fetcher_when_role_found(self, registry: state_registry_impl.StateRegistryImpl):
        target = _helpers.mock_model(roles.Role, id=125, guild_id=120)
        registry.fabric = fabric.Fabric()
        registry.fabric.http_adapter = _helpers.create_autospec(base_http_adapter.BaseHTTPAdapter)
        registry.fabric.http_adapter.fetch_roles = mock.AsyncMock(
            return_value=[
                _helpers.mock_model(roles.Role, id=123, guild_id=120),
                _helpers.mock_model(roles.Role, id=124, guild_id=120),
                target,
                _helpers.mock_model(roles.Role, id=127, guild_id=120),
            ]
        )

        result = await registry._role_fetcher(120, 125)

        registry.fabric.http_adapter.fetch_roles.assert_called_once_with(120)
        assert result is target

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=ValueError)
    async def test__role_fetcher_when_role_not_found(self, registry: state_registry_impl.StateRegistryImpl):
        target = _helpers.mock_model(roles.Role, id=125, guild_id=120)
        registry.fabric = fabric.Fabric()
        registry.fabric.http_adapter = _helpers.create_autospec(base_http_adapter.BaseHTTPAdapter)
        registry.fabric.http_adapter.fetch_roles = mock.AsyncMock(
            return_value=[
                _helpers.mock_model(roles.Role, id=123, guild_id=120),
                _helpers.mock_model(roles.Role, id=124, guild_id=120),
                target,
                _helpers.mock_model(roles.Role, id=127, guild_id=120),
            ]
        )

        await registry._role_fetcher(120, 126)

    def test_get_mandatory_role_by_id_cached_guild_cached_role(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=1)
        role_obj = _helpers.mock_model(roles.Role, id=2, guild_id=guild_obj.id)
        guild_obj.roles = {role_obj.id: role_obj}
        registry._guilds = {guild_obj.id: guild_obj}
        callback_obj = mock.MagicMock()

        assert registry.get_mandatory_role_by_id(guild_obj.id, role_obj.id, callback_obj) is role_obj

    def test_get_mandatory_role_by_id_cached_guild_uncached_role_returns_unknown(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=1)
        guild_obj.roles = _helpers.StrongWeakValuedDict()
        registry._guilds = {guild_obj.id: guild_obj}
        callback_obj = mock.MagicMock()
        registry._role_fetcher = mock.AsyncMock()
        unknown_obj = _helpers.mock_model(bases.UnknownObject, id=2)
        registry._prepare_unknown_with_callback = mock.MagicMock(return_value=unknown_obj)

        result = registry.get_mandatory_role_by_id(guild_obj.id, 2, callback_obj)
        registry._prepare_unknown_with_callback.assert_called_with(
            2, registry._role_fetcher, callback_obj, guild_obj.id, 2
        )
        assert result is unknown_obj

    def test_get_mandatory_role_by_id_uncached_guild_uncached_role_returns_unknown(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        registry._guilds = _helpers.StrongWeakValuedDict()
        callback_obj = mock.MagicMock()
        registry._role_fetcher = mock.AsyncMock()
        unknown_obj = _helpers.mock_model(bases.UnknownObject, id=2)
        registry._prepare_unknown_with_callback = mock.MagicMock(return_value=unknown_obj)

        result = registry.get_mandatory_role_by_id(1, 2, callback_obj)
        registry._prepare_unknown_with_callback.assert_called_with(2, registry._role_fetcher, callback_obj, 1, 2)
        assert result is unknown_obj

    def test_get_user_by_id_cached_oauth2_user(self, registry: state_registry_impl.StateRegistryImpl):
        user_obj = _helpers.mock_model(users.OAuth2User, id=1)
        registry._user = user_obj
        registry._users = _helpers.StrongWeakValuedDict()

        assert registry.get_user_by_id(user_obj.id) is registry._user

    def test_get_user_by_id_cached(self, registry: state_registry_impl.StateRegistryImpl):
        user_obj = _helpers.mock_model(users.User, id=1)
        registry._user = _helpers.mock_model(users.OAuth2User, id=2)
        registry._users = {user_obj.id: user_obj}

        assert registry.get_user_by_id(user_obj.id) is user_obj

    def test_get_user_by_id_uncached_returns_None(self, registry: state_registry_impl.StateRegistryImpl):
        registry._user = None
        registry._users = _helpers.StrongWeakValuedDict()

        assert registry.get_user_by_id(1) is None

    def test_get_mandatory_user_by_id_cached_oauth2_user(self, registry: state_registry_impl.StateRegistryImpl):
        user_obj = _helpers.mock_model(users.OAuth2User, id=1)
        registry._user = user_obj
        registry._users = _helpers.StrongWeakValuedDict()

        assert registry.get_mandatory_user_by_id(user_obj.id) is registry._user

    def test_get_mandatory_user_by_id_cached(self, registry: state_registry_impl.StateRegistryImpl):
        user_obj = _helpers.mock_model(users.User, id=1)
        registry._user = _helpers.mock_model(users.OAuth2User, id=2)
        registry._users = {user_obj.id: user_obj}

        assert registry.get_mandatory_user_by_id(user_obj.id) is user_obj

    def test_get_mandatory_user_by_id_uncached_returns_unknown(self, registry: state_registry_impl.StateRegistryImpl):
        registry._user = None
        registry._users = _helpers.StrongWeakValuedDict()
        registry.fabric = _helpers.create_autospec(fabric.Fabric)
        registry.fabric.http_adapter = _helpers.create_autospec(base_http_adapter.BaseHTTPAdapter)
        registry.fabric.state_registry = registry
        unknown_obj = _helpers.mock_model(bases.UnknownObject, id=1)
        callback_obj = mock.MagicMock()
        registry._prepare_unknown_with_callback = mock.MagicMock(return_value=unknown_obj)

        result = registry.get_mandatory_user_by_id(1, callback_obj)

        registry._prepare_unknown_with_callback.assert_called_with(
            1, registry.fabric.http_adapter.fetch_user, callback_obj, 1
        )

        assert result is unknown_obj

    def test_get_member_by_id_cached_guild_cached_user(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=1)
        member_obj = _helpers.mock_model(members.Member, id=2, guild=guild_obj)
        guild_obj.members = {member_obj.id: member_obj}
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_member_by_id(member_obj.id, guild_obj.id) is member_obj

    def test_get_member_by_id_cached_guild_uncached_user(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=1)
        guild_obj.members = _helpers.StrongWeakValuedDict()
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_member_by_id(1, guild_obj.id) is None

    def test_get_member_by_id_uncached_guild_uncached_user(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=1)
        member_obj = _helpers.mock_model(members.Member, id=2, guild=guild_obj)
        guild_obj.members = {member_obj.id: member_obj}
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_member_by_id(3, 4) is None

    def test_get_mandatory_member_by_id_cached_guild_cached_user(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=1)
        member_obj = _helpers.mock_model(members.Member, id=2, guild=guild_obj)
        guild_obj.members = {member_obj.id: member_obj}
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_mandatory_member_by_id(member_obj.id, guild_obj.id) is member_obj

    def test_get_mandatory_member_by_id_cached_guild_uncached_user(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=2)
        guild_obj.members = _helpers.StrongWeakValuedDict()
        registry._guilds = {guild_obj.id: guild_obj}
        registry.fabric = _helpers.create_autospec(fabric.Fabric)
        registry.fabric.http_adapter = _helpers.create_autospec(base_http_adapter.BaseHTTPAdapter)
        fabric._state_registry = _helpers.create_autospec(base_registry.BaseRegistry)
        unknown_obj = _helpers.mock_model(bases.UnknownObject, id=1)
        callback_obj = mock.MagicMock()
        registry._prepare_unknown_with_callback = mock.MagicMock(return_value=unknown_obj)

        result = registry.get_mandatory_member_by_id(1, guild_obj.id, callback_obj)

        registry._prepare_unknown_with_callback.assert_called_with(
            1, registry.fabric.http_adapter.fetch_member, callback_obj, 1, guild=2
        )

        assert result is unknown_obj

    def test_get_mandatory_member_by_id_uncached_guild_uncached_user(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=1)
        member_obj = _helpers.mock_model(members.Member, id=2, guild=guild_obj)
        guild_obj.members = {member_obj.id: member_obj}
        registry._guilds = {guild_obj.id: guild_obj}
        registry.fabric = _helpers.create_autospec(fabric.Fabric)
        registry.fabric.http_adapter = _helpers.create_autospec(base_http_adapter.BaseHTTPAdapter)
        registry.fabric.state_registry = registry
        unknown_obj = _helpers.mock_model(bases.UnknownObject, id=1)
        callback_obj = mock.MagicMock()
        registry._prepare_unknown_with_callback = mock.MagicMock(return_value=unknown_obj)

        result = registry.get_mandatory_member_by_id(3, 4, callback_obj)

        registry._prepare_unknown_with_callback.assert_called_with(
            3, registry.fabric.http_adapter.fetch_member, callback_obj, 3, guild=4
        )

        assert result is unknown_obj

    def test_parse_application(self, registry: state_registry_impl.StateRegistryImpl):
        application_obj = _helpers.mock_model(applications.Application)
        with _helpers.mock_patch(applications.Application, return_value=application_obj) as Application:
            parsed_obj = registry.parse_application({})
            assert parsed_obj is application_obj
            Application.assert_called_once_with(registry.fabric, {})

    def test_parse_application_user_given_user_cached(self, registry: state_registry_impl.StateRegistryImpl):
        oa2_user = _helpers.create_autospec(users.OAuth2User)
        registry._user = oa2_user
        with _helpers.mock_patch(users.OAuth2User, return_value=oa2_user) as OAuth2User:
            parsed_obj = registry.parse_application_user({})
            assert parsed_obj is oa2_user
            assert parsed_obj is registry.me
            OAuth2User.assert_not_called()
            oa2_user.update_state.assert_called_once_with({})

    def test_parse_application_user_given_no_previous_user_cached(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        oa2_user = _helpers.create_autospec(users.OAuth2User)
        with _helpers.mock_patch(users.OAuth2User, return_value=oa2_user) as OAuth2User:
            parsed_obj = registry.parse_application_user({})
            assert parsed_obj is oa2_user
            assert parsed_obj is registry.me
            OAuth2User.assert_called_once_with(registry.fabric, {})

    def test_parse_audit_log(self, registry: state_registry_impl.StateRegistryImpl):
        audit_log_obj = _helpers.mock_model(audit_logs.AuditLog)
        with _helpers.mock_patch(audit_logs.AuditLog, return_value=audit_log_obj) as AuditLog:
            parsed_obj = registry.parse_audit_log({})
            assert parsed_obj is audit_log_obj
            AuditLog.assert_called_once_with(registry.fabric, {})

    def test_parse_ban(self, registry: state_registry_impl.StateRegistryImpl):
        ban_obj = _helpers.mock_model(guilds.Ban)
        with _helpers.mock_patch(guilds.Ban, return_value=ban_obj) as GuildBan:
            assert registry.parse_ban({}) is ban_obj
            GuildBan.assert_called_once_with(registry.fabric, {})

    @pytest.mark.parametrize(
        "impl_t",
        [
            channels.GuildAnnouncementChannel,
            channels.GuildVoiceChannel,
            channels.GuildCategory,
            channels.GuildTextChannel,
            channels.GuildStoreChannel,
        ],
    )
    def test_parse_channel_sets_guild_id_on_guild_channel_payload_if_guild_id_param_is_not_None(
        self, registry: state_registry_impl.StateRegistryImpl, impl_t
    ):
        payload = {"id": "1234"}
        guild_obj = _helpers.mock_model(guilds.Guild, id=9873)
        registry._guilds = {guild_obj.id: guild_obj}
        channel_obj = _helpers.mock_model(impl_t, id=5678, guild=guild_obj)
        registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        with contextlib.suppress(Exception):
            registry.parse_channel(payload, guild_obj)

        assert payload["guild_id"] == 9873

    @pytest.mark.parametrize(
        "impl_t",
        [
            channels.GuildAnnouncementChannel,
            channels.GuildVoiceChannel,
            channels.GuildCategory,
            channels.GuildTextChannel,
            channels.GuildStoreChannel,
            channels.DMChannel,
            channels.GroupDMChannel,
        ],
    )
    def test_parse_channel_updates_state_if_already_cached(
        self, registry: state_registry_impl.StateRegistryImpl, impl_t
    ):
        payload = {"id": "1234"}
        channel_obj = _helpers.mock_model(impl_t, id=1234)
        registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        registry.parse_channel(payload)
        channel_obj.update_state.assert_called_once_with(payload)

    @pytest.mark.parametrize(
        "impl_t",
        [
            channels.GuildAnnouncementChannel,
            channels.GuildVoiceChannel,
            channels.GuildCategory,
            channels.GuildTextChannel,
            channels.GuildStoreChannel,
            channels.DMChannel,
            channels.GroupDMChannel,
        ],
    )
    def test_parse_channel_returns_existing_channel_if_already_cached(
        self, registry: state_registry_impl.StateRegistryImpl, impl_t
    ):
        payload = {"id": "1234"}
        channel_obj = _helpers.mock_model(impl_t, id=1234)
        registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        result = registry.parse_channel(payload)
        assert result is channel_obj

    @pytest.mark.parametrize("impl_t", [channels.DMChannel, channels.GroupDMChannel,])
    def test_parse_channel_caches_dm_channel_if_uncached_dm_channel(
        self, registry: state_registry_impl.StateRegistryImpl, impl_t
    ):
        payload = {"id": "1234", "type": -1}
        channel_obj = _helpers.mock_model(impl_t, id=1234)
        registry._dm_channels = _helpers.StrongWeakValuedDict()
        registry.get_channel_by_id = mock.MagicMock(return_value=None)
        with _helpers.mock_patch(channels.parse_channel, return_value=channel_obj):
            with _helpers.mock_patch(channels.is_channel_type_dm, return_value=True):
                registry.parse_channel(payload)
                assert channel_obj in registry._dm_channels.values()
                assert channel_obj not in registry._guild_channels.values()

    @pytest.mark.parametrize(
        "impl_t",
        [
            channels.GuildAnnouncementChannel,
            channels.GuildVoiceChannel,
            channels.GuildCategory,
            channels.GuildTextChannel,
            channels.GuildStoreChannel,
        ],
    )
    def test_parse_channel_caches_guild_channel_if_uncached_guild_channel(
        self, registry: state_registry_impl.StateRegistryImpl, impl_t
    ):
        payload = {"id": "1234", "type": -1}
        guild_obj = _helpers.mock_model(guilds.Guild, id=567, channels={})
        channel_obj = _helpers.mock_model(impl_t, id=1234)
        registry.get_guild_by_id = mock.MagicMock(return_value=guild_obj)
        registry.get_channel_by_id = mock.MagicMock(return_value=None)
        with _helpers.mock_patch(channels.parse_channel, return_value=channel_obj):
            with _helpers.mock_patch(channels.is_channel_type_dm, return_value=False):
                registry.parse_channel(payload)
                assert channel_obj not in registry._dm_channels.values()
                assert channel_obj in registry._guild_channels.values()
                assert guild_obj.channels[1234] == channel_obj

    @pytest.mark.parametrize(
        "impl_t",
        [
            channels.GuildAnnouncementChannel,
            channels.GuildVoiceChannel,
            channels.GuildCategory,
            channels.GuildTextChannel,
            channels.GuildStoreChannel,
            channels.DMChannel,
            channels.GroupDMChannel,
        ],
    )
    def test_parse_channel_returns_new_channel_if_uncached(
        self, registry: state_registry_impl.StateRegistryImpl, impl_t
    ):
        payload = {"id": "1234", "type": -1}
        channel_obj = _helpers.mock_model(impl_t, id=1234)
        registry.get_channel_by_id = mock.MagicMock(return_value=None)
        with _helpers.mock_patch(channels.parse_channel, return_value=channel_obj):
            with _helpers.mock_patch(channels.is_channel_type_dm, return_value=True):
                result = registry.parse_channel(payload)
                assert result is channel_obj

    def test_parse_connection(self, registry: state_registry_impl.StateRegistryImpl):
        connection_obj = _helpers.mock_model(connections.Connection)
        with _helpers.mock_patch(connections.Connection, return_value=connection_obj) as Connection:
            parsed_obj = registry.parse_connection({})
            assert parsed_obj is connection_obj
            Connection.assert_called_once_with(registry.fabric, {})

    def test_parse_unicode_emoji_does_not_change_cache(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        payload = {"id": "1234"}
        registry._emojis = _helpers.StrongWeakValuedDict()
        guild_id = None
        with _helpers.mock_patch(emojis.parse_emoji, return_value=emoji_obj):
            registry.parse_emoji(payload, guild_id)
            assert registry._emojis == _helpers.StrongWeakValuedDict()

    def test_parse_unicode_emoji_returns_unicode_emoji(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        payload = {"id": "1234"}
        guild_id = None
        with _helpers.mock_patch(emojis.parse_emoji, return_value=emoji_obj):
            assert registry.parse_emoji(payload, guild_id) is emoji_obj

    def test_parse_unknown_emoji_does_not_change_cache(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.UnknownEmoji)
        payload = {"id": "1234"}
        registry._emojis = _helpers.StrongWeakValuedDict()
        guild_id = None
        with _helpers.mock_patch(emojis.parse_emoji, return_value=emoji_obj):
            registry.parse_emoji(payload, guild_id)
            assert registry._emojis == _helpers.StrongWeakValuedDict()

    def test_parse_unknown_emoji_returns_unknown_emoji(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.UnknownEmoji)
        payload = {"id": "1234"}
        guild_id = None
        with _helpers.mock_patch(emojis.parse_emoji, return_value=emoji_obj):
            assert registry.parse_emoji(payload, guild_id) is emoji_obj

    def test_parse_guild_emoji_caches_emoji_globally(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=5678)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, guild=guild_obj)
        payload = {"id": "1234"}
        registry._emojis = _helpers.StrongWeakValuedDict()
        registry._guilds = {guild_obj.id: guild_obj}
        with _helpers.mock_patch(emojis.parse_emoji, return_value=emoji_obj):
            registry.parse_emoji(payload, guild_obj)
            assert registry._emojis == {emoji_obj.id: emoji_obj}

    def test_parse_guild_emoji_when_valid_guild_caches_emoji_on_guild(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=5678, emojis={})
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, guild=guild_obj)
        payload = {"id": "1234"}
        registry._guilds = {guild_obj.id: guild_obj}
        with _helpers.mock_patch(emojis.parse_emoji, return_value=emoji_obj):
            registry.parse_emoji(payload, guild_obj)
            assert emoji_obj in guild_obj.emojis.values()

    def test_parse_guild_emoji_when_valid_guild_returns_guild_emoji(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=5678)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, guild=guild_obj)
        payload = {"id": "1234"}
        registry._guilds = {guild_obj.id: guild_obj}
        with _helpers.mock_patch(emojis.parse_emoji, return_value=emoji_obj):
            assert registry.parse_emoji(payload, guild_obj) is emoji_obj

    def test_parse_guild_emoji_when_already_cached_returns_cached_emoji(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=5678)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, guild=guild_obj)
        registry._emojis = {emoji_obj.id: emoji_obj}
        payload = {"id": "1234"}
        registry._guilds = {guild_obj.id: guild_obj}
        guild_id = guild_obj.id

        assert registry.parse_emoji(payload, guild_id) is emoji_obj

    def test_parse_gateway_bot(self, registry: state_registry_impl.StateRegistryImpl):
        gateway_bot_obj = _helpers.mock_model(gateway_bot.GatewayBot)
        with _helpers.mock_patch(gateway_bot.GatewayBot, return_value=gateway_bot_obj) as GatewayBot:
            parsed_obj = registry.parse_gateway_bot({})
            assert parsed_obj is gateway_bot_obj
            GatewayBot.assert_called_once_with({})

    def test_parse_guild_when_already_cached_and_payload_is_available_calls_update_state(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"id": "1234", "unavailable": False}
        guild_obj = _helpers.mock_model(guilds.Guild, id=1234)
        registry._guilds = {guild_obj.id: guild_obj}

        registry.parse_guild(payload)

        guild_obj.update_state.assert_called_with(payload)

    def test_parse_guild_when_already_cached_and_becomes_unavailable_only_sets_unavailability_flag(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"id": "1234", "unavailable": True}
        guild_obj = _helpers.mock_model(guilds.Guild, id=1234, is_unavailable=False)
        registry._guilds = {guild_obj.id: guild_obj}

        registry.parse_guild(payload)

        guild_obj.update_state.assert_not_called()
        assert guild_obj.is_unavailable is True

    def test_parse_guild_when_not_cached_caches_new_guild(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"id": "1234", "unavailable": False}
        guild_obj = _helpers.mock_model(guilds.Guild, id=1234, is_unavailable=False)
        registry._guilds = _helpers.StrongWeakValuedDict()

        with _helpers.mock_patch(guilds.Guild, return_value=guild_obj) as Guild:
            registry.parse_guild(payload)
            Guild.assert_called_once_with(registry.fabric, payload)
            assert guild_obj in registry._guilds.values()

    def test_parse_guild_when_not_cached_returns_new_guild(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"id": "1234", "unavailable": False}
        guild_obj = _helpers.mock_model(guilds.Guild, id=1234, is_unavailable=False)
        registry._guilds = _helpers.StrongWeakValuedDict()

        with _helpers.mock_patch(guilds.Guild, return_value=guild_obj):
            assert registry.parse_guild(payload) is guild_obj

    def test_parse_integration(self, registry: state_registry_impl.StateRegistryImpl):
        integration_obj = _helpers.mock_model(integrations.Integration)
        with _helpers.mock_patch(integrations.Integration, return_value=integration_obj) as Integration:
            assert registry.parse_integration({}) is integration_obj
            Integration.assert_called_once_with(registry.fabric, {})

    @pytest.mark.parametrize(
        ["invite_payload", "expected_type"],
        [
            ({"code": "xacasa"}, invites.Invite),
            ({"code": "xacasa", "created_at": "2019-04-19T04:02:07.038000+00:00"}, invites.InviteWithMetadata),
        ],
    )
    def test_parse_invite(self, registry: state_registry_impl, invite_payload, expected_type):
        mock_invite_obj = mock.MagicMock(expected_type)
        with _helpers.mock_patch(expected_type, return_value=mock_invite_obj, __slots__=expected_type.__slots__):
            assert registry.parse_invite(invite_payload) is mock_invite_obj

    def test_parse_voice_state(self, registry: state_registry_impl.StateRegistryImpl):
        registry._guilds[69] = guild_obj = _helpers.mock_model(guilds.Guild, id=69, voice_states={})
        voice_obj = _helpers.mock_model(voices.VoiceState, session_id="nz2o312")

        with _helpers.mock_patch(voices.VoiceState, return_value=voice_obj):
            registry.parse_voice_state(
                {"session_id": "nz2o312", "channel_id": "115590097143215541", "user_id": "432341", "guild_id": 69},
                guild_obj,
            )
            assert guild_obj.voice_states[432341] == voice_obj

    def test_parse_voice_state_when_existing_voice_state(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {
            "user_id": "4333",
            "session_id": "39ksdjefoi",
            "channel_id": "115590097143215541",
            "guild_id": "777",
            "deaf": True,
            "mute": True,
        }
        voice_state_obj = _helpers.mock_model(voices.VoiceState, user_id=4333)
        registry._guilds[777] = guild_obj = _helpers.mock_model(
            guilds.Guild, id=777, voice_states={4333: voice_state_obj}
        )
        registry.parse_voice_state(payload, guild_obj)
        voice_state_obj.update_state.assert_called_with(payload)

    def test_parse_partial_member_calls_parse_member_correctly_and_returns_result(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        partial_member = {"roles": ["9", "18", "27"], "nick": "Roy Rodgers McFreely"}
        user = {"id": "1234"}
        guild = _helpers.mock_model(guilds.Guild, id=659)
        mock_result = _helpers.mock_model(members.Member, id=1234)
        registry.parse_member = _helpers.create_autospec(registry.parse_member, return_value=mock_result)
        assert registry.parse_partial_member(partial_member, user, guild) is mock_result
        registry.parse_member.assert_called_with(
            {"roles": ["9", "18", "27"], "nick": "Roy Rodgers McFreely", "user": {"id": "1234"}}, guild
        )

    def test_parse_member_when_existing_member_updates_state(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"user": {"id": "1234"}, "roles": ["9", "18", "27"], "nick": "Roy Rodgers McFreely"}

        expected_roles = [
            _helpers.mock_model(roles.Role, id=9),
            _helpers.mock_model(roles.Role, id=18),
            _helpers.mock_model(roles.Role, id=27),
        ]

        roles_map = {
            1: _helpers.mock_model(roles.Role, id=1),
            2: _helpers.mock_model(roles.Role, id=2),
            36: _helpers.mock_model(roles.Role, id=36),
            **{r.id: r for r in expected_roles},
        }

        guild_obj = _helpers.mock_model(guilds.Guild, id=5678, roles=roles_map)
        registry._guilds = {guild_obj.id: guild_obj}

        member_obj = _helpers.mock_model(members.Member, id=1234, roles=[], nick=None, guild=guild_obj)

        guild_obj.members = {member_obj.id: member_obj}

        registry.parse_member(payload, guild_obj)

        member_obj.update_state.assert_called_with(expected_roles, payload)

    def test_parse_member_when_existing_member_returns_existing_member(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"user": {"id": "1234"}, "roles": ["9", "18", "27"], "nick": "Roy Rodgers McFreely"}
        member_obj = _helpers.mock_model(members.Member, id=1234, roles=[], nick=None)
        guild_obj = _helpers.mock_model(guilds.Guild, id=5678, members={member_obj.id: member_obj})
        registry._guilds = {guild_obj.id: guild_obj}
        member_obj.guild = guild_obj

        assert registry.parse_member(payload, guild_obj) is member_obj

    def test_parse_member_when_new_member_caches_new_member_on_guild(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"user": {"id": "1234"}, "roles": ["9", "18", "27"], "nick": "Roy Rodgers McFreely"}
        guild_obj = _helpers.mock_model(guilds.Guild, id=5678, members={})
        registry._guilds = {guild_obj.id: guild_obj}
        member_obj = _helpers.mock_model(members.Member)

        with _helpers.mock_patch(members.Member, return_value=member_obj):
            registry.parse_member(payload, guild_obj)
            assert member_obj in guild_obj.members.values()

    def test_parse_member_when_new_member_returns_new_member(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"user": {"id": "1234"}, "roles": ["9", "18", "27"], "nick": "Roy Rodgers McFreely"}
        guild_obj = _helpers.mock_model(guilds.Guild, id=5678, members={})
        registry._guilds = {guild_obj.id: guild_obj}
        member_obj = _helpers.mock_model(members.Member)

        with _helpers.mock_patch(members.Member, return_value=member_obj):
            parsed_member_obj = registry.parse_member(payload, guild_obj)
            assert parsed_member_obj is member_obj

    def test_parse_message_when_channel_cached_updates_last_message_timestamp_on_channel(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"id": "1234", "channel_id": "4567"}
        channel_obj = _helpers.mock_model(channels.GuildTextChannel, id=4567, last_message_id=9999)
        registry._guild_channels = {channel_obj.id: channel_obj}
        registry._dm_channels = _helpers.StrongWeakValuedDict()
        mock_message = _helpers.mock_model(messages.Message, id=1234, channel=channel_obj)

        with _helpers.mock_patch(messages.Message, return_value=mock_message):
            registry.parse_message(payload)
            assert channel_obj.last_message_id == mock_message.id

    def test_parse_message_when_channel_cached_returns_message(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"id": "1234", "channel_id": "4567"}
        channel_obj = _helpers.mock_model(channels.GuildTextChannel, id=4567, last_message_id=9999)
        registry._guild_channels = {channel_obj.id: channel_obj}
        registry._dm_channels = _helpers.StrongWeakValuedDict()
        mock_message = _helpers.mock_model(messages.Message, id=1234, channel=channel_obj)

        with _helpers.mock_patch(messages.Message, return_value=mock_message):
            parsed_message = registry.parse_message(payload)
            assert parsed_message is mock_message

    def test_parse_presence_updates_member(self, registry: state_registry_impl.StateRegistryImpl):
        member_obj = _helpers.mock_model(members.Member, presence=None)
        presence_obj = _helpers.mock_model(presences.MemberPresence)
        payload = _helpers.StrongWeakValuedDict()

        with _helpers.mock_patch(presences.MemberPresence, return_value=presence_obj):
            registry.parse_presence(member_obj, payload)
            assert member_obj.presence is presence_obj

    def test_parse_presence_returns_presence(self, registry: state_registry_impl.StateRegistryImpl):
        member_obj = _helpers.mock_model(members.Member, presence=None)
        presence_obj = _helpers.mock_model(presences.MemberPresence)
        payload = _helpers.StrongWeakValuedDict()

        with _helpers.mock_patch(presences.MemberPresence, return_value=presence_obj):
            parsed_presence = registry.parse_presence(member_obj, payload)
            assert parsed_presence is presence_obj

    def test_parse_reaction_parses_emoji(self, registry: state_registry_impl.StateRegistryImpl):
        registry.parse_emoji = _helpers.create_autospec(registry.parse_emoji)
        message_obj = _helpers.mock_model(messages.Message, id=42069)
        registry._message_cache = {message_obj.id: message_obj}
        emoji_payload = {"name": "\N{OK HAND SIGN}", "id": None}
        payload = {"message_id": "46029", "count": 12, "emoji": emoji_payload}

        registry.parse_reaction(payload, 33, 44)

        registry.parse_emoji.assert_called_with(emoji_payload, None)

    def test_parse_reaction_when_message_is_cached_and_existing_reaction_updates_reaction_count(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        emoji_payload = {"name": "\N{OK HAND SIGN}", "id": None}
        payload = {"message_id": "1234", "count": 12, "emoji": emoji_payload}
        expected_emoji = emojis.UnicodeEmoji(emoji_payload)
        reaction_obj = _helpers.mock_model(reactions.Reaction, count=10, emoji=expected_emoji)
        message_obj = _helpers.mock_model(messages.Message, id=1234, reactions=[reaction_obj])
        registry._message_cache = {message_obj.id: message_obj}

        registry.parse_reaction(payload, message_obj.id, 44)
        assert message_obj.reactions[0].count == 12

    def test_parse_reaction_when_message_is_cached_and_existing_reaction_returns_existing_reaction(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        emoji_payload = {"name": "\N{OK HAND SIGN}", "id": None}
        payload = {"message_id": "1234", "count": 12, "emoji": emoji_payload}
        expected_emoji = emojis.UnicodeEmoji(emoji_payload)
        reaction_obj = _helpers.mock_model(reactions.Reaction, count=10, emoji=expected_emoji)
        other_reaction_obj = _helpers.mock_model(reactions.Reaction)
        reaction_objs = [other_reaction_obj, reaction_obj]
        message_obj = _helpers.mock_model(messages.Message, id=1234, reactions=reaction_objs)
        registry._message_cache = {message_obj.id: message_obj}

        assert registry.parse_reaction(payload, message_obj.id, 66) is reaction_obj

    def test_parse_reaction_when_message_is_cached_and_not_existing_reaction_adds_new_reaction(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"message_id": "1234", "count": 12, "emoji": {"name": "\N{OK HAND SIGN}", "id": None}}
        message_obj = _helpers.mock_model(messages.Message, id=1234, reactions=[])
        reaction_obj = _helpers.mock_model(reactions.Reaction)
        registry._message_cache = {message_obj.id: message_obj}

        with _helpers.mock_patch(reactions.Reaction, return_value=reaction_obj):
            assert registry.parse_reaction(payload, 1234, 555)
            assert reaction_obj in message_obj.reactions

    def test_parse_reaction_when_message_is_cached_returns_reaction(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"message_id": "1234", "count": 12, "emoji": {"name": "\N{OK HAND SIGN}", "id": None}}
        message_obj = _helpers.mock_model(messages.Message, id=1234, reactions=[])
        reaction_obj = _helpers.mock_model(reactions.Reaction)
        registry._message_cache = {message_obj.id: message_obj}

        with _helpers.mock_patch(reactions.Reaction, return_value=reaction_obj):
            assert registry.parse_reaction(payload, message_obj.id, 777) is reaction_obj

    def test_parse_role_when_role_exists_does_not_update_role_mapping(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"id": "1234"}
        role_obj = _helpers.mock_model(roles.Role, id=1234)
        before_mapping = {role_obj.id: role_obj}
        guild_obj = _helpers.mock_model(guilds.Guild, roles=before_mapping)

        registry.parse_role(payload, guild_obj)

        assert guild_obj.roles is before_mapping

    def test_parse_role_when_role_does_not_exist_adds_to_role_mapping(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"id": "1234"}
        role_obj = _helpers.mock_model(roles.Role, id=1234)
        guild_obj = _helpers.mock_model(guilds.Guild, roles={})

        with _helpers.mock_patch(roles.Role, return_value=role_obj):
            registry.parse_role(payload, guild_obj)

        assert guild_obj.roles == {role_obj.id: role_obj}

    def test_parse_role_when_role_exists_updates_existing_role(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"id": "1234"}
        role_obj = _helpers.mock_model(roles.Role, id=1234)
        guild_obj = _helpers.mock_model(guilds.Guild, roles={role_obj.id: role_obj})

        registry.parse_role(payload, guild_obj)

        role_obj.update_state.assert_called_with(payload)

    def test_parse_role_when_role_exists_returns_existing_role(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"id": "1234"}
        role_obj = _helpers.mock_model(roles.Role, id=1234)
        guild_obj = _helpers.mock_model(guilds.Guild, roles={role_obj.id: role_obj})

        assert registry.parse_role(payload, guild_obj) is role_obj

    def test_parse_role_when_role_does_not_exist_returns_new_role(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"id": "1234"}
        role_obj = _helpers.mock_model(roles.Role, id=1234)
        guild_obj = _helpers.mock_model(guilds.Guild, roles={})

        with _helpers.mock_patch(roles.Role, return_value=role_obj):
            assert registry.parse_role(payload, guild_obj) is role_obj

    def test_parse_user_when_bot_user_calls_parse_application_user(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"id": "1234", "mfa_enabled": False, "verified": True}
        application_user_obj = _helpers.mock_model(users.OAuth2User)
        registry.parse_application_user = mock.MagicMock(return_value=application_user_obj)

        registry.parse_user(payload)

        registry.parse_application_user.assert_called_with(payload)

    def test_parse_user_invokes_users_parse_user(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"id": "1234"}
        user_obj = _helpers.mock_model(users.User, id=1234)
        registry._users = _helpers.StrongWeakValuedDict()

        with _helpers.mock_patch(users.parse_user, return_value=user_obj) as parse_user:
            registry.parse_user(payload)
            parse_user.assert_called_with(registry.fabric, payload)

    def test_parse_user_when_OAuth2_user_returns_OAuth2_user(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"id": "1234", "mfa_enabled": False, "verified": True}
        oa2_user_obj = _helpers.mock_model(users.OAuth2User)
        registry.parse_application_user = mock.MagicMock(return_value=oa2_user_obj)

        assert registry.parse_user(payload) is oa2_user_obj

    def test_parse_user_when_uncached_user_caches_new_user(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"id": "1234"}
        user_obj = _helpers.mock_model(users.User, id=1234)
        registry._users = _helpers.StrongWeakValuedDict()

        with _helpers.mock_patch(users.User, return_value=user_obj):
            registry.parse_user(payload)

        assert user_obj in registry._users.values()

    def test_parse_user_when_uncached_user_returns_new_user(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"id": "1234"}
        user_obj = _helpers.mock_model(users.User, id=1234)
        registry._users = _helpers.StrongWeakValuedDict()

        with _helpers.mock_patch(users.User, return_value=user_obj):
            assert registry.parse_user(payload) is user_obj

    def test_parse_user_when_cached_user_updates_state_of_existing_user(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"id": "1234"}
        user_obj = _helpers.mock_model(users.User, id=1234)
        registry._users = {user_obj.id: user_obj}

        with _helpers.mock_patch(users.User, return_value=user_obj):
            registry.parse_user(payload)

        user_obj.update_state.assert_called_with(payload)

    def test_parse_user_when_cached_returns_cached_user(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"id": "1234"}
        user_obj = _helpers.mock_model(users.User, id=1234)
        registry._users = {user_obj.id: user_obj}

        with _helpers.mock_patch(users.User, return_value=user_obj):
            assert registry.parse_user(payload) is user_obj

    def test_parse_webhook_returns_webhook(self, registry: state_registry_impl.StateRegistryImpl):
        webhook_obj = _helpers.mock_model(webhooks.Webhook)
        with _helpers.mock_patch(webhooks.Webhook, return_value=webhook_obj):
            assert registry.parse_webhook({}) is webhook_obj

    def test_parse_webhook_user_returns_webhook_user(self, registry: state_registry_impl.StateRegistryImpl):
        webhook_user_obj = _helpers.mock_model(webhooks.WebhookUser)
        with _helpers.mock_patch(webhooks.WebhookUser, return_value=webhook_user_obj):
            assert registry.parse_webhook_user({}) is webhook_user_obj

    @pytest.mark.parametrize("initial_unavailability", [True, False])
    @pytest.mark.parametrize("new_unavailability", [True, False])
    def test_set_guild_unavailability(
        self, initial_unavailability, new_unavailability, registry: state_registry_impl.StateRegistryImpl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, is_unavailable=initial_unavailability)
        registry.set_guild_unavailability(guild_obj, new_unavailability)
        assert guild_obj.is_unavailable is new_unavailability

    @pytest.mark.parametrize("timestamp", [datetime.datetime.now(), None])
    def test_set_last_pinned_timestamp_for_cached_channel_id_exits_silently(
        self, registry: state_registry_impl.StateRegistryImpl, timestamp: datetime.datetime
    ):
        channel_obj = _helpers.mock_model(channels.TextChannel)
        registry.set_last_pinned_timestamp(channel_obj, timestamp)
        # We don't store this attribute, so we don't bother doing anything with it.
        assert True, r"¯\_(ツ)_/¯"

    def test_set_roles_for_member_replaces_role_list_on_member(self, registry: state_registry_impl.StateRegistryImpl):
        role_objs = [
            _helpers.mock_model(roles.Role, id=9),
            _helpers.mock_model(roles.Role, id=2),
            _helpers.mock_model(roles.Role, id=33),
        ]
        member_obj = _helpers.mock_model(members.Member, roles=[])

        registry.set_roles_for_member(role_objs, member_obj)

        assert role_objs[0] in member_obj.roles
        assert role_objs[1] in member_obj.roles
        assert role_objs[2] in member_obj.roles

    def test_update_channel_when_existing_channel_does_not_exist_returns_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        registry.get_channel_by_id = mock.MagicMock(return_value=None, spec_set=registry.get_channel_by_id)
        payload = {"id": "1234"}

        diff = registry.update_channel(payload)

        assert diff is None

    def test_update_channel_when_existing_channel_exists_returns_old_state_copy_and_updated_new_state(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123, channels={})
        registry._guilds = {guild_obj.id: guild_obj}
        original_channel_obj = _helpers.mock_model(channels.GuildTextChannel, id=456)
        cloned_channel_obj = _helpers.mock_model(channels.GuildTextChannel, id=456)
        original_channel_obj.copy = mock.MagicMock(spec_set=original_channel_obj.copy, return_value=cloned_channel_obj)
        registry._guild_channels = {original_channel_obj.id: original_channel_obj}
        payload = {"id": "456"}

        old, new = registry.update_channel(payload)

        assert old is not None
        assert new is not None

        assert new is original_channel_obj, "existing channel was not used as target for update!"
        assert old is cloned_channel_obj, "existing channel did not get the old state copied and returned!"

    def test_update_guild_when_existing_guild_does_not_exist_returns_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        registry.get_guild_by_id = mock.MagicMock(return_value=None, spec_set=registry.get_guild_by_id)
        payload = {"id": "1234"}

        diff = registry.update_guild(payload)

        assert diff is None

    def test_update_guild_when_existing_guild_exists_returns_old_state_copy_and_updated_new_state(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        original_guild_obj = _helpers.mock_model(guilds.Guild, id=123)
        cloned_guild_obj = _helpers.mock_model(guilds.Guild, id=123)
        original_guild_obj.copy = mock.MagicMock(spec_set=original_guild_obj.copy, return_value=cloned_guild_obj)
        registry._guilds = {original_guild_obj.id: original_guild_obj}
        payload = {"id": "123"}

        old, new = registry.update_guild(payload)

        assert old is not None
        assert new is not None

        assert new is original_guild_obj, "existing guild was not used as target for update!"
        assert old is cloned_guild_obj, "existing guild did not get the old state copied and returned!"

    def test_update_member_when_existing_member_exists_returns_old_state_copy_and_updated_new_state(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        role_1 = _helpers.mock_model(roles.Role, id=111)
        role_2 = _helpers.mock_model(roles.Role, id=112)
        role_3 = _helpers.mock_model(roles.Role, id=113)

        roles_map = {role_1.id: role_1, role_2.id: role_2, role_3.id: role_3}
        guild_obj = _helpers.mock_model(guilds.Guild, id=124, roles=roles_map)

        registry._guilds = {guild_obj.id: guild_obj}
        original_member_obj = _helpers.mock_model(members.Member, id=123)
        cloned_member_obj = _helpers.mock_model(members.Member, id=123, roles=roles_map)
        original_member_obj.copy = mock.MagicMock(spec_set=original_member_obj.copy, return_value=cloned_member_obj)
        guild_obj.members = {original_member_obj.id: original_member_obj}

        old, new = registry.update_member(original_member_obj, list(roles_map.values()), {"nick": "potatoboi"})

        assert old is not None
        assert new is not None

        assert new is original_member_obj, "existing member was not used as target for update!"
        assert old is cloned_member_obj, "existing member did not get the old state copied and returned!"

        new.update_state.assert_called_with(list(roles_map.values()), {"nick": "potatoboi"})

    def test_update_member_presence_when_existing_member_exists_returns_old_state_copy_and_updated_new_state(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=123)
        registry._guilds = {guild_obj.id: guild_obj}
        presence = _helpers.mock_model(presences.MemberPresence)
        original_member_obj = _helpers.mock_model(members.Member, id=456, presence=presence)
        cloned_member_obj = _helpers.mock_model(members.Member, id=456, presence=presence)
        original_member_obj.copy = mock.MagicMock(spec_set=original_member_obj.copy, return_value=cloned_member_obj)
        guild_obj.members = {original_member_obj.id: original_member_obj}
        payload = {
            "user": {"id": "339767912841871360"},
            "status": "online",
            "game": None,
            "client_status": {"desktop": "online"},
            "activities": [],
        }

        member_obj, old, new = registry.update_member_presence(original_member_obj, payload)

        assert old is not None
        assert new is not None

        assert new is original_member_obj.presence, "existing presence was not used as target for update!"
        assert old is cloned_member_obj.presence, "existing presence did not get the old state copied and returned!"

    def test_update_message_when_existing_message_uncached_returns_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        registry._message_cache = _helpers.StrongWeakValuedDict()
        payload = {"id": "1234"}

        diff = registry.update_message(payload)

        assert diff is None

    def test_update_message_when_existing_message_cached_returns_old_state_copy_and_updated_new_state(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        original_message_obj = _helpers.mock_model(messages.Message, id=123)
        cloned_message_obj = _helpers.mock_model(messages.Message, id=123)
        original_message_obj.copy = mock.MagicMock(spec_set=original_message_obj.copy, return_value=cloned_message_obj)
        registry._message_cache = {original_message_obj.id: original_message_obj}
        payload = {"id": "123"}

        old, new = registry.update_message(payload)

        assert old is not None
        assert new is not None

        assert new is original_message_obj, "existing message was not used as target for update!"
        assert old is cloned_message_obj, "existing message did not get the old state copied and returned!"

    def test_update_role_when_existing_role_does_not_exist_returns_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=5678, roles={})
        registry.get_role_by_id = mock.MagicMock(return_value=None, spec_set=registry.get_role_by_id)
        payload = {"id": "1234"}

        diff = registry.update_role(guild_obj, payload)

        assert diff is None

    def test_update_role_when_existing_role_exists_returns_old_state_copy_and_updated_new_state(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        original_role_obj = _helpers.mock_model(roles.Role, id=123)
        cloned_role_obj = _helpers.mock_model(roles.Role, id=123)
        original_role_obj.copy = mock.MagicMock(spec_set=original_role_obj.copy, return_value=cloned_role_obj)
        guild_obj = _helpers.mock_model(guilds.Guild, id=124, roles={original_role_obj.id: original_role_obj})
        registry._guilds = {guild_obj.id: guild_obj}
        payload = {"id": "123"}

        old, new = registry.update_role(guild_obj, payload)

        assert old is not None
        assert new is not None

        assert new is original_role_obj, "existing role was not used as target for update!"
        assert old is cloned_role_obj, "existing role did not get the old state copied and returned!"

    def test_update_guild_emojis_when_when_existing_guild_exists_returns_old_state_copy_and_updated_new_state(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        guild_id = 9999
        existing_emoji_1 = _helpers.mock_model(emojis.GuildEmoji, id=1234, name="bowsettebaka", is_animated=False)
        existing_emoji_2 = _helpers.mock_model(emojis.GuildEmoji, id=1235, name="bowsettel00d", is_animated=False)
        existing_emoji_3 = _helpers.mock_model(emojis.GuildEmoji, id=1236, name="bowsetteowo", is_animated=True)

        initial_emoji_map = {
            existing_emoji_1.id: existing_emoji_1,
            existing_emoji_2.id: existing_emoji_2,
            existing_emoji_3.id: existing_emoji_3,
        }

        guild_obj = _helpers.mock_model(guilds.Guild, id=guild_id, emojis=dict(initial_emoji_map))
        registry._guilds = {guild_obj.id: guild_obj}

        registry.parse_emoji = mock.MagicMock(side_effect=[existing_emoji_1, existing_emoji_2])

        payload = {
            "emojis": [
                {"id": "1234", "name": "bowsettebaka", "animated": False},
                {"id": "1235", "name": "bowsettel00d", "animated": False},
            ],
            "guild_id": guild_obj.id,
        }

        diff = registry.update_guild_emojis(payload, guild_obj)

        assert diff is not None

        before, after = diff

        assert before == set(initial_emoji_map.values())
        assert after == {existing_emoji_1, existing_emoji_2}
