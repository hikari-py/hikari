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
import contextlib
from unittest import mock

import pytest

from hikari.core.internal import state_registry_impl
from hikari.core.models import emojis, users, channels, guilds, roles
from hikari.core.models import messages
from hikari.core.models import reactions
from tests.hikari.core import _helpers
from tests.hikari.core._helpers import mock_model


@pytest.fixture()
def registry():
    # We cant overwrite methods on a slotted class... subclass it to remove that constraint.
    return _helpers.unslot_class(state_registry_impl.StateRegistryImpl)(999, 999)


# noinspection PyPropertyAccess,PyProtectedMember,PyTypeChecker,PyDunderSlots,PyUnresolvedReferences
@pytest.mark.state
class TestStateRegistryImpl:
    def test_message_cache_property_returns_message_cache(self, registry: state_registry_impl.StateRegistryImpl):
        cache = mock_model(dict)
        registry._message_cache = cache

        assert registry.message_cache is cache

    def test_me_property_returns_bot_user_when_cached(self, registry: state_registry_impl.StateRegistryImpl):
        user = mock_model(users.BotUser)
        registry._user = user

        assert registry.me is user

    def test_me_property_returns_None_when_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        assert registry.me is None

    def test_add_reaction_for_existing_reaction(self, registry: state_registry_impl.StateRegistryImpl):
        message_obj = mock_model(messages.Message)
        emoji_obj = mock_model(emojis.Emoji)
        other_emoji_obj = mock_model(emojis.Emoji)
        reaction_obj = reactions.Reaction(5, emoji_obj, message_obj)
        other_reaction_obj = reactions.Reaction(17, other_emoji_obj, message_obj)
        message_obj.reactions = [other_reaction_obj, reaction_obj]

        new_reaction_obj = registry.add_reaction(message_obj, emoji_obj)

        assert new_reaction_obj is reaction_obj
        assert new_reaction_obj.count == 6
        assert len(message_obj.reactions) == 2

    def test_add_reaction_for_new_reaction(self, registry: state_registry_impl.StateRegistryImpl):
        message_obj = mock_model(messages.Message)
        emoji_obj = mock_model(emojis.Emoji)
        message_obj.reactions = []

        new_reaction_obj = registry.add_reaction(message_obj, emoji_obj)

        assert isinstance(new_reaction_obj, reactions.Reaction)
        assert new_reaction_obj.count == 1

    def test_delete_channel_when_cached_guild_channel(self, registry: state_registry_impl.StateRegistryImpl):
        channel_obj = mock_model(channels.GuildTextChannel, id=5678)
        guild_obj = mock_model(guilds.Guild, id=1234)
        channel_obj.guild = guild_obj
        registry._guilds = {guild_obj.id: guild_obj}
        guild_obj.channels = {channel_obj.id: channel_obj}
        registry._guild_channels = {channel_obj.id: channel_obj}

        registry.delete_channel(channel_obj)

        assert channel_obj.id not in registry._guild_channels
        assert channel_obj.id not in guild_obj.channels

    def test_delete_channel_when_cached_dm_channel(self, registry: state_registry_impl.StateRegistryImpl):
        channel_obj = mock_model(channels.DMChannel, id=5678)
        registry._dm_channels = {channel_obj.id: channel_obj}

        registry.delete_channel(channel_obj)

        assert channel_obj.id not in registry._dm_channels

    def test_delete_channel_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        channel_obj = mock_model(channels.Channel)

        registry.delete_channel(channel_obj)

        assert True, "this should exit silently"

    def test_delete_emoji_cached_deletes_from_global_cache(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = mock_model(emojis.GuildEmoji, id=10987)
        guild_obj = mock_model(guilds.Guild, id=6969)
        guild_obj.emojis = {emoji_obj.id: emoji_obj}
        emoji_obj.guild = guild_obj
        registry._emojis = {emoji_obj.id: emoji_obj}
        registry._guilds = {guild_obj.id: guild_obj}

        registry.delete_emoji(emoji_obj)

        assert emoji_obj.id not in registry._emojis

    def test_delete_emoji_cached_deletes_from_guild(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = mock_model(emojis.GuildEmoji, id=10987)
        guild_obj = mock_model(guilds.Guild, id=6969)
        guild_obj.emojis = {emoji_obj.id: emoji_obj}
        emoji_obj.guild = guild_obj
        registry._emojis = {emoji_obj.id: emoji_obj}
        registry._guilds = {guild_obj.id: guild_obj}

        registry.delete_emoji(emoji_obj)

        assert emoji_obj.id not in guild_obj.emojis

    def test_delete_emoji_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = mock_model(emojis.GuildEmoji, id=10987)
        guild_obj = mock_model(guilds.Guild, id=6969)
        emoji_obj.guild = guild_obj

        registry.delete_emoji(emoji_obj)

        assert True, "this should exit silently"

    def test_delete_guild_cached(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = mock_model(guilds.Guild, id=1234)
        registry._guilds = {guild_obj.id: guild_obj}

        registry.delete_guild(guild_obj)

        assert guild_obj.id not in registry._guilds

    def test_delete_guild_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = mock_model(guilds.Guild, id=1234)
        registry._guilds = {}

        registry.delete_guild(guild_obj)

        assert True, "this should exit silently"

    def test_delete_message_cached(self, registry: state_registry_impl.StateRegistryImpl):
        message_obj = mock_model(messages.Message, id=1234)
        registry._message_cache = {message_obj.id: message_obj}

        registry.delete_message(message_obj)

        assert message_obj not in registry._message_cache

    def test_delete_message_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        message_obj = mock_model(messages.Message, id=1234)

        registry.delete_message(message_obj)

        assert True, "this should exit silently"

    def test_delete_member_cached(self, registry: state_registry_impl.StateRegistryImpl):
        member_obj = mock_model(users.Member, id=1234)
        guild_obj = mock_model(guilds.Guild, id=5689)
        guild_obj.members = {member_obj.id: member_obj}
        member_obj.guild = guild_obj
        registry._guilds = {guild_obj.id: guild_obj}

        registry.delete_member(member_obj)

        assert member_obj.id not in guild_obj.members

    def test_delete_member_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        member_obj = mock_model(users.Member, id=1234)

        registry.delete_member(member_obj)

        assert True, "this should exit silently"

    def test_delete_reaction_cached(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj_to_remove = mock_model(emojis.Emoji)
        emoji_obj_to_keep = mock_model(emojis.Emoji)
        user_obj = mock_model(users.User, id=6789)
        message_obj = mock_model(messages.Message, id=1234)
        message_obj.reactions = [
            reactions.Reaction(7, emoji_obj_to_keep, message_obj),
            reactions.Reaction(5, emoji_obj_to_remove, message_obj),
        ]

        registry.delete_reaction(message_obj, user_obj, emoji_obj_to_remove)

        assert len(message_obj.reactions) == 1

    def test_delete_reaction_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = mock_model(emojis.Emoji)
        user_obj = mock_model(users.User, id=6789)
        message_obj = mock_model(messages.Message, id=1234)

        registry.delete_reaction(message_obj, user_obj, emoji_obj)

        assert True, "this should exit silently"

    def test_delete_role_cached(self, registry: state_registry_impl.StateRegistryImpl):
        role_obj_to_remove = mock_model(roles.Role, id=1234)
        role_obj_to_keep = mock_model(roles.Role, id=1235)
        guild_obj = mock_model(guilds.Guild, id=5678)
        guild_obj.roles = {role_obj_to_remove.id: role_obj_to_remove, role_obj_to_keep.id: role_obj_to_keep}
        role_obj_to_remove.guild = guild_obj
        role_obj_to_keep.guild = guild_obj
        member_obj = mock_model(users.Member, id=9101112)
        member_obj._role_ids = [role_obj_to_keep.id, role_obj_to_remove.id]
        other_member_obj = mock_model(users.Member, id=13141516)
        guild_obj.members = {member_obj.id: member_obj, other_member_obj.id: other_member_obj}
        registry._guilds = {guild_obj.id: guild_obj}
        registry.delete_role(role_obj_to_remove)

        assert len(guild_obj.roles) == 1
        assert len(member_obj._role_ids) == 1

    def test_delete_role_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        role_obj = mock_model(roles.Role, id=1234)
        registry.delete_role(role_obj)

        assert True, "this should exit silently"

    def test_get_channel_by_id_cached_guild_channel(self, registry: state_registry_impl.StateRegistryImpl):
        guild_channel_obj = mock_model(channels.GuildTextChannel, id=1234)
        dm_channel_obj = mock_model(channels.GroupDMChannel, id=1235)
        registry._guild_channels = {guild_channel_obj.id: guild_channel_obj}
        registry._dm_channels = {dm_channel_obj.id: dm_channel_obj}

        assert registry.get_channel_by_id(guild_channel_obj.id) is guild_channel_obj

    def test_get_channel_by_id_cached_dm_channel(self, registry: state_registry_impl.StateRegistryImpl):
        guild_channel_obj = mock_model(channels.GuildTextChannel, id=1234)
        dm_channel_obj = mock_model(channels.GroupDMChannel, id=1235)
        registry._guild_channels = {guild_channel_obj.id: guild_channel_obj}
        registry._dm_channels = {dm_channel_obj.id: dm_channel_obj}

        assert registry.get_channel_by_id(dm_channel_obj.id) is dm_channel_obj

    def test_get_channel_by_id_uncached_returns_None(self, registry: state_registry_impl.StateRegistryImpl):
        guild_channel_obj = mock_model(channels.GuildTextChannel, id=1234)
        dm_channel_obj = mock_model(channels.GroupDMChannel, id=1235)
        registry._guild_channels = {guild_channel_obj.id: guild_channel_obj}
        registry._dm_channels = {dm_channel_obj.id: dm_channel_obj}

        assert registry.get_channel_by_id(1236) is None

    def test_get_emoji_by_id_cached(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = mock_model(emojis.GuildEmoji, id=69)
        registry._emojis = {emoji_obj.id: emoji_obj}

        assert registry.get_emoji_by_id(emoji_obj.id) is emoji_obj

    def test_get_emoji_by_id_uncached_returns_None(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = mock_model(emojis.GuildEmoji, id=69)
        registry._emojis = {emoji_obj.id: emoji_obj}

        assert registry.get_emoji_by_id(70) is None

    def test_get_guild_by_id_cached(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = mock_model(guilds.Guild, id=69)
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_guild_by_id(guild_obj.id) is guild_obj

    def test_get_guild_by_id_uncached_returns_None(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = mock_model(guilds.Guild, id=69)
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_guild_by_id(70) is None

    def test_get_member_by_id_cached_guild_cached_user(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = mock_model(guilds.Guild, id=1)
        member_obj = mock_model(users.Member, id=2, guild=guild_obj)
        guild_obj.members = {member_obj.id: member_obj}
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_member_by_id(member_obj.id, guild_obj.id) is member_obj

    def test_get_member_by_id_cached_guild_uncached_user(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = mock_model(guilds.Guild, id=1)
        guild_obj.members = {}
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_member_by_id(1, guild_obj.id) is None

    def test_get_member_by_id_uncached_guild_uncached_user(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = mock_model(guilds.Guild, id=1)
        member_obj = mock_model(users.Member, id=2, guild=guild_obj)
        guild_obj.members = {member_obj.id: member_obj}
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_member_by_id(3, 4) is None

    def test_get_message_by_id_cached(self, registry: state_registry_impl.StateRegistryImpl):
        message_obj = mock_model(messages.Message, id=69)
        registry._message_cache = {message_obj.id: message_obj}

        assert registry.get_message_by_id(message_obj.id) is message_obj

    def test_get_message_by_id_uncached_returns_None(self, registry: state_registry_impl.StateRegistryImpl):
        message_obj = mock_model(messages.Message, id=69)
        registry._message_cache = {message_obj.id: message_obj}

        assert registry.get_message_by_id(70) is None

    def test_get_role_by_id_cached_guild_cached_role(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = mock_model(guilds.Guild, id=1)
        role_obj = mock_model(roles.Role, id=2, guild=guild_obj)
        guild_obj.roles = {role_obj.id: role_obj}
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_role_by_id(guild_obj.id, role_obj.id) is role_obj

    def test_get_role_by_id_cached_guild_uncached_role(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = mock_model(guilds.Guild, id=1)
        guild_obj.roles = {}
        registry._guilds = {guild_obj.id: guild_obj}

        assert registry.get_role_by_id(guild_obj.id, 2) is None

    def test_get_role_by_id_uncached_guild_uncached_role(self, registry: state_registry_impl.StateRegistryImpl):
        registry._guilds = {}

        assert registry.get_role_by_id(1, 2) is None

    def test_get_user_by_id_cached_bot_user(self, registry: state_registry_impl.StateRegistryImpl):
        user_obj = mock_model(users.BotUser, id=1)
        registry._user = user_obj
        registry._users = {}

        assert registry.get_user_by_id(user_obj.id) is registry._user

    def test_get_user_by_id_cached(self, registry: state_registry_impl.StateRegistryImpl):
        user_obj = mock_model(users.User, id=1)
        registry._user = mock_model(users.BotUser, id=2)
        registry._users = {user_obj.id: user_obj}

        assert registry.get_user_by_id(user_obj.id) is user_obj

    def test_get_user_by_id_uncached_returns_None(self, registry: state_registry_impl.StateRegistryImpl):
        registry._user = None
        registry._users = {}

        assert registry.get_user_by_id(1) is None

    def test_parse_bot_user_given_user_cached(self, registry: state_registry_impl.StateRegistryImpl):
        bot_user = mock.MagicMock(spec_set=users.BotUser)
        registry._user = bot_user
        with mock.patch(_helpers.fqn1(users.BotUser), return_value=bot_user) as BotUser:
            parsed_obj = registry.parse_bot_user({})
            assert parsed_obj is bot_user
            assert parsed_obj is registry.me
            BotUser.assert_not_called()
            bot_user.update_state.assert_called_once_with({})

    def test_parse_bot_user_given_no_previous_user_cached(self, registry: state_registry_impl.StateRegistryImpl):
        bot_user = mock.MagicMock(spec_set=users.BotUser)
        with mock.patch(_helpers.fqn1(users.BotUser), return_value=bot_user) as BotUser:
            parsed_obj = registry.parse_bot_user({})
            assert parsed_obj is bot_user
            assert parsed_obj is registry.me
            BotUser.assert_called_once_with(registry, {})

    def test_parse_channel_sets_guild_id_on_guild_channel_payload_if_guild_id_param_is_not_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"id": "1234"}
        channel_obj = mock_model(channels.GuildTextChannel, id=5678)
        registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        with contextlib.suppress(Exception):
            registry.parse_channel(payload, 1234)

        assert payload["guild_id"] == 1234

    def test_parse_channel_updates_state_if_already_cached(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"id": "1234"}
        channel_obj = mock_model(channels.Channel, id=1234)
        registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        registry.parse_channel(payload)
        channel_obj.update_state.assert_called_once_with(payload)

    def test_parse_channel_returns_existing_channel_if_already_cached(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"id": "1234"}
        channel_obj = mock_model(channels.Channel, id=1234)
        registry.get_channel_by_id = mock.MagicMock(return_value=channel_obj)
        result = registry.parse_channel(payload)
        assert result is channel_obj

    def test_parse_channel_caches_dm_channel_if_uncached_dm_channel(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"id": "1234", "type": -1}
        channel_obj = mock_model(channels.DMChannel, id=1234)
        registry._dm_channels = {}
        registry.get_channel_by_id = mock.MagicMock(return_value=None)
        with mock.patch(_helpers.fqn1(channels.channel_from_dict), return_value=channel_obj):
            with mock.patch(_helpers.fqn1(channels.is_channel_type_dm), return_value=True):
                registry.parse_channel(payload)
                assert channel_obj in registry._dm_channels.values()
                assert channel_obj not in registry._guild_channels.values()

    def test_parse_channel_caches_guild_channel_if_uncached_guild_channel(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        payload = {"id": "1234", "type": -1}
        guild_obj = mock_model(guilds.Guild, id=100, channels={})
        channel_obj = mock_model(channels.GuildChannel, id=1234, guild=guild_obj)
        registry._dm_channels = {}
        registry._guild_channels = {}
        registry.get_channel_by_id = mock.MagicMock(return_value=None)
        with mock.patch(_helpers.fqn1(channels.channel_from_dict), return_value=channel_obj):
            with mock.patch(_helpers.fqn1(channels.is_channel_type_dm), return_value=False):
                registry.parse_channel(payload)
                assert channel_obj not in registry._dm_channels.values()
                assert channel_obj in registry._guild_channels.values()
                assert guild_obj.channels[channel_obj.id] is channel_obj

    def test_parse_channel_returns_new_channel_if_uncached(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"id": "1234", "type": -1}
        channel_obj = mock_model(channels.Channel, id=1234)
        registry.get_channel_by_id = mock.MagicMock(return_value=None)
        with mock.patch(_helpers.fqn1(channels.channel_from_dict), return_value=channel_obj):
            with mock.patch(_helpers.fqn1(channels.is_channel_type_dm), return_value=True):
                result = registry.parse_channel(payload)
                assert result is channel_obj

    def test_parse_unicode_emoji_does_not_change_cache(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        payload = {"id": "1234"}
        registry._emojis = {}
        guild_id = None
        with mock.patch(_helpers.fqn1(emojis.emoji_from_dict), return_value=emoji_obj):
            registry.parse_emoji(payload, guild_id)
            assert registry._emojis == {}

    def test_parse_unicode_emoji_returns_unicode_emoji(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.UnicodeEmoji)
        payload = {"id": "1234"}
        guild_id = None
        with mock.patch(_helpers.fqn1(emojis.emoji_from_dict), return_value=emoji_obj):
            assert registry.parse_emoji(payload, guild_id) is emoji_obj

    def test_parse_unknown_emoji_does_not_change_cache(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.UnknownEmoji)
        payload = {"id": "1234"}
        registry._emojis = {}
        guild_id = None
        with mock.patch(_helpers.fqn1(emojis.emoji_from_dict), return_value=emoji_obj):
            registry.parse_emoji(payload, guild_id)
            assert registry._emojis == {}

    def test_parse_unknown_emoji_returns_unknown_emoji(self, registry: state_registry_impl.StateRegistryImpl):
        emoji_obj = _helpers.mock_model(emojis.UnknownEmoji)
        payload = {"id": "1234"}
        guild_id = None
        with mock.patch(_helpers.fqn1(emojis.emoji_from_dict), return_value=emoji_obj):
            assert registry.parse_emoji(payload, guild_id) is emoji_obj

    def test_parse_guild_emoji_caches_emoji_globally(self, registry: state_registry_impl.StateRegistryImpl):
        guild_obj = _helpers.mock_model(guilds.Guild, id=5678)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, guild=guild_obj)
        payload = {"id": "1234"}
        registry._emojis = {}
        registry._guilds = {guild_obj.id: guild_obj}
        guild_id = guild_obj.id
        with mock.patch(_helpers.fqn1(emojis.emoji_from_dict), return_value=emoji_obj):
            registry.parse_emoji(payload, guild_id)
            assert registry._emojis == {emoji_obj.id: emoji_obj}

    def test_parse_guild_emoji_when_valid_guild_caches_emoji_on_guild(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=5678, emojis={})
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, guild=guild_obj)
        payload = {"id": "1234"}
        registry._guilds = {guild_obj.id: guild_obj}
        guild_id = guild_obj.id
        with mock.patch(_helpers.fqn1(emojis.emoji_from_dict), return_value=emoji_obj):
            registry.parse_emoji(payload, guild_id)
            assert emoji_obj in guild_obj.emojis.values()

    def test_parse_guild_emoji_when_valid_guild_returns_guild_emoji(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        guild_obj = _helpers.mock_model(guilds.Guild, id=5678)
        emoji_obj = _helpers.mock_model(emojis.GuildEmoji, id=1234, guild=guild_obj)
        payload = {"id": "1234"}
        registry._guilds = {guild_obj.id: guild_obj}
        guild_id = guild_obj.id
        with mock.patch(_helpers.fqn1(emojis.emoji_from_dict), return_value=emoji_obj):
            assert registry.parse_emoji(payload, guild_id) is emoji_obj

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
        guild_obj = _helpers.mock_model(guilds.Guild, id=1234, unavailable=False)
        registry._guilds = {guild_obj.id: guild_obj}

        registry.parse_guild(payload)

        guild_obj.update_state.assert_not_called()
        assert guild_obj.unavailable is True

    def test_parse_guild_when_not_cached_caches_new_guild(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"id": "1234", "unavailable": False}
        guild_obj = _helpers.mock_model(guilds.Guild, id=1234, unavailable=False)
        registry._guilds = {}

        with mock.patch(_helpers.fqn1(guilds.Guild), return_value=guild_obj) as Guild:
            registry.parse_guild(payload)
            Guild.assert_called_once_with(registry, payload)
            assert guild_obj in registry._guilds.values()

    def test_parse_guild_when_not_cached_returns_new_guild(self, registry: state_registry_impl.StateRegistryImpl):
        payload = {"id": "1234", "unavailable": False}
        guild_obj = _helpers.mock_model(guilds.Guild, id=1234, unavailable=False)
        registry._guilds = {}

        with mock.patch(_helpers.fqn1(guilds.Guild), return_value=guild_obj):
            assert registry.parse_guild(payload) is guild_obj

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_member_when_existing_member_updates_state(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_member_when_existing_member_returns_existing_member(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_member_when_new_member_caches_new_member_on_guild(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_member_when_new_member_returns_new_member(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_message_when_channel_uncached_returns_None(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_message_when_channel_cached_updates_last_message_timestamp_on_channel(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_message_when_channel_cached_returns_message(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_presence(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_reaction_when_message_is_cached_and_existing_reaction_updates_reaction_count(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_reaction_when_message_is_cached_and_not_existing_reaction_adds_new_reaction(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_reaction_when_message_is_uncached_returns_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_role_when_guild_uncached_returns_None(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_role_when_guild_cached_updates_role_mapping(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_role_when_guild_cached_returns_role(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_user_when_bot_user_calls_parse_bot_user(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_user_when_uncached_user_creates_new_user_and_returns_it(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_user_when_cached_user_updates_state_of_existing_user(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_user_when_cached_returns_cached_user(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_webhook_returns_webhook(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_all_reactions_sets_reaction_counts_to_0(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_all_reactions_removes_all_reactions(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_reaction_when_cached_and_more_than_one_user_on_the_same_reaction_decrements_count_by_1(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_reaction_when_cached_and_one_user_on_reaction_sets_count_to_0(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_reaction_when_cached_and_one_user_on_reaction_removes_reaction_from_message(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_reaction_when_cached_returns_existing_reaction(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_reaction_when_uncached_returns_new_reaction(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_reaction_when_uncached_sets_reaction_count_to_0(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_set_guild_unavailability_for_uncached_guild_exits_silently(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    @pytest.mark.parametrize("unavailability", [True, False])
    def test_set_guild_unavailability_for_cached_guild(self, unavailability):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_set_last_pinned_timestamp_for_cached_channel_id_exits_silently(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_set_last_pinned_timestamp_for_uncached_channel_id_exits_silently(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_set_roles_for_member_replaces_role_list_on_member(self, registry: state_registry_impl.StateRegistryImpl):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_channel_when_existing_channel_does_not_exist_returns_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_channel_when_existing_channel_exists_returns_old_state_copy_and_updated_new_state(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_guild_when_existing_guild_does_not_exist_returns_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_guild_when_existing_guild_exists_returns_old_state_copy_and_updated_new_state(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_member_when_guild_does_not_exist_returns_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_member_when_existing_member_does_not_exist_returns_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_member_when_existing_member_exists_returns_old_state_copy_and_updated_new_state(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_member_presence_when_guild_does_not_exist_returns_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_member_presence_when_existing_member_does_not_exist_returns_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_member_presence_when_existing_member_exists_returns_old_state_copy_and_updated_new_state(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_message_when_existing_message_uncached_returns_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_message_when_existing_message_cached_returns_old_state_copy_and_updated_new_state(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_role_when_existing_role_does_not_exist_returns_None(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_role_when_existing_role_exists_returns_old_state_copy_and_updated_new_state(
        self, registry: state_registry_impl.StateRegistryImpl
    ):
        raise NotImplementedError

    def test_copy_constructor_returns_same_instance(self):
        import copy

        reg = state_registry_impl.StateRegistryImpl(100, 100)
        assert copy.copy(reg) is reg
