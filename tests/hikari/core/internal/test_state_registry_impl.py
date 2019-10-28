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
from unittest import mock

import pytest
import typing

from hikari.core.internal import state_registry_impl
from hikari.core.models import emojis, users
from hikari.core.models import messages
from hikari.core.models import reactions


T = typing.TypeVar("T")


def mock_model(spec_set: typing.Type[T]) -> T:
    # Enables type hinting for my own reference.
    return mock.MagicMock(spec_set=spec_set)


@pytest.fixture()
def state_registry_obj():
    return state_registry_impl.StateRegistryImpl(999, 999)


@pytest.mark.state
class TestStateRegistryImpl:
    def test_message_cache_property_returns_message_cache(self, state_registry_obj):
        cache = mock_model(dict)
        state_registry_obj._message_cache = cache
        assert state_registry_obj.message_cache is cache

    def test_me_property_returns_bot_user_when_cached(self, state_registry_obj):
        user = mock_model(users.BotUser)
        state_registry_obj._user = user
        assert state_registry_obj.me is user

    def test_me_property_returns_None_when_uncached(self, state_registry_obj):
        assert state_registry_obj.me is None

    def test_add_reaction_for_existing_reaction(self, state_registry_obj):
        message_obj = mock_model(messages.Message)
        emoji_obj = mock_model(emojis.Emoji)
        reaction_obj = reactions.Reaction(5, emoji_obj, message_obj)
        message_obj.reactions = [reaction_obj]
        new_reaction_obj = state_registry_obj.add_reaction(message_obj, emoji_obj)
        assert new_reaction_obj is reaction_obj
        assert new_reaction_obj.count == 6

    def test_add_reaction_for_new_reaction(self, state_registry_obj):
        message_obj = mock_model(messages.Message)
        emoji_obj = mock_model(emojis.Emoji)
        message_obj.reactions = []
        new_reaction_obj = state_registry_obj.add_reaction(message_obj, emoji_obj)
        assert isinstance(new_reaction_obj, reactions.Reaction)
        assert new_reaction_obj.count == 1

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_channel_when_cached_guild_channel(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_channel_when_cached_dm_channel(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_channel_uncached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_emoji_cached_deletes_from_global_cache(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_emoji_cached_deletes_from_guild(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_emoji_uncached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_guild_cached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_guild_uncached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_message_cached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_message_uncached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_member_cached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_member_uncached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_reaction_cached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_reaction_uncached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_role_cached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_delete_role_uncached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_channel_by_id_cached_guild_channel(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_channel_by_id_cached_dm_channel(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_channel_by_id_uncached_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_emoji_by_id_cached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_emoji_by_id_uncached_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_guild_by_id_cached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_guild_by_id_uncached_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_member_by_id_cached_guild_cached_user(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_member_by_id_cached_guild_uncached_user(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_member_by_id_uncached_guild_cached_user(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_member_by_id_uncached_guild_uncached_user(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_message_by_id_cached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_message_by_id_uncached_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_role_by_id_cached_guild_cached_role(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_role_by_id_cached_guild_uncached_role(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_role_by_id_uncached_guild_uncached_role(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_user_by_id_cached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_get_user_by_id_uncached_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_channel_sets_guild_id_on_guild_channel_payload_if_not_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_channel_updates_state_if_already_cached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_channel_returns_existing_channel_if_already_cached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_channel_caches_dm_channel_if_uncached_dm_channel(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_channel_caches_guild_channel_if_uncached_guild_channel(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_channel_returns_new_channel_if_uncached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_unicode_emoji_does_not_change_cache(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_unicode_emoji_returns_unicode_emoji(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_unknown_emoji_does_not_change_cache(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_unknown_emoji_returns_unknown_emoji(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_guild_emoji_caches_emoji_globally(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_guild_emoji_when_valid_guild_caches_emoji_on_guild(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_guild_emoji_when_valid_guild_returns_guild_emoji(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_guild_emoji_when_invalid_guild_returns_guild_emoji(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_guild_when_already_cached_and_is_available(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_guild_when_already_cached_and_is_unavailable(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_guild_when_not_cached(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_guild_returns_guild(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_member_when_existing_member_updates_state(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_member_when_existing_member_returns_existing_member(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_member_when_new_member_caches_new_member_on_guild(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_member_when_new_member_returns_new_member(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_message_when_channel_uncached_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_message_when_channel_cached_updates_last_message_timestamp_on_channel(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_message_when_channel_cached_returns_message(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_presence(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_reaction_when_message_is_cached_and_existing_reaction_updates_reaction_count(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_reaction_when_message_is_cached_and_not_existing_reaction_adds_new_reaction(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_reaction_when_message_is_uncached_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_role_when_guild_uncached_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_role_when_guild_cached_updates_role_mapping(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_role_when_guild_cached_returns_role(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_user_when_bot_user_calls_parse_bot_user(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_user_when_uncached_user_creates_new_user_and_returns_it(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_user_when_cached_user_updates_state_of_existing_user(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_user_when_cached_returns_cached_user(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_parse_webhook_returns_webhook(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_all_reactions_sets_reaction_counts_to_0(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_all_reactions_removes_all_reactions(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_reaction_when_cached_and_more_than_one_user_on_the_same_reaction_decrements_count_by_1(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_reaction_when_cached_and_one_user_on_reaction_sets_count_to_0(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_reaction_when_cached_and_one_user_on_reaction_removes_reaction_from_message(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_reaction_when_cached_returns_existing_reaction(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_reaction_when_uncached_returns_new_reaction(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_remove_reaction_when_uncached_sets_reaction_count_to_0(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_set_guild_unavailability_for_uncached_guild_exits_silently(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    @pytest.mark.parametrize("unavailability", [True, False])
    def test_set_guild_unavailability_for_cached_guild(self, unavailability):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_set_last_pinned_timestamp_for_cached_channel_id_exits_silently(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_set_last_pinned_timestamp_for_uncached_channel_id_exits_silently(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_set_roles_for_member_replaces_role_list_on_member(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_channel_when_existing_channel_does_not_exist_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_channel_when_existing_channel_exists_returns_old_state_copy_and_updated_new_state(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_guild_when_existing_guild_does_not_exist_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_guild_when_existing_guild_exists_returns_old_state_copy_and_updated_new_state(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_member_when_guild_does_not_exist_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_member_when_existing_member_does_not_exist_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_member_when_existing_member_exists_returns_old_state_copy_and_updated_new_state(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_member_presence_when_guild_does_not_exist_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_member_presence_when_existing_member_does_not_exist_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_member_presence_when_existing_member_exists_returns_old_state_copy_and_updated_new_state(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_message_when_existing_message_uncached_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_message_when_existing_message_cached_returns_old_state_copy_and_updated_new_state(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_role_when_existing_role_does_not_exist_returns_None(self):
        raise NotImplementedError

    @pytest.mark.xfail(reason="Not yet implemented")
    def test_update_role_when_existing_role_exists_returns_old_state_copy_and_updated_new_state(self):
        raise NotImplementedError

    def test_copy_constructor_returns_same_instance(self):
        import copy

        reg = state_registry_impl.StateRegistryImpl(100, 100)
        assert copy.copy(reg) is reg
