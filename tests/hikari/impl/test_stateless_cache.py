# -*- coding: utf-8 -*-
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

import mock
import pytest

from hikari import users
from hikari.impl import stateless_cache
from tests.hikari import hikari_test_helpers


class TestStatelessCache:
    @pytest.fixture()
    def component(self):
        return stateless_cache.StatelessCacheImpl()

    def test_clear_emojis(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_emojis()

    def test_clear_emojis_for_guild(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_emojis_for_guild(123432)

    def test_delete_emoji(self, component):
        with pytest.raises(NotImplementedError):
            assert component.delete_emoji(34123)

    def test_get_emoji(self, component):
        assert component.get_emoji(532134) is None

    def test_get_emojis_view(self, component):
        assert component.get_emojis_view() == {}

    def test_get_emojis_view_for_guild(self, component):
        assert component.get_emojis_view_for_guild(234123) == {}

    def test_set_emoji(self, component):
        with pytest.raises(NotImplementedError):
            assert component.set_emoji(object())

    def test_update_emoji(self, component):
        with pytest.raises(NotImplementedError):
            assert component.update_emoji(object())

    def test_clear_guilds(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_guilds()

    def test_delete_guild(self, component):
        with pytest.raises(NotImplementedError):
            assert component.delete_guild(123123)

    def test_get_guild(self, component):
        assert component.get_guild(1234123) is None

    def test_get_available_guild(self, component):
        assert component.get_available_guild(1234123) is None

    def test_get_unavailable_guild(self, component):
        assert component.get_unavailable_guild(43123) is None

    def test_get_available_guilds_view(self, component):
        assert component.get_available_guilds_view() == {}

    def test_get_unavailable_guilds_view(self, component):
        assert component.get_unavailable_guilds_view() == {}

    def test_set_guild(self, component):
        with pytest.raises(NotImplementedError):
            assert component.set_guild(object())

    def test_set_guild_availability(self, component):
        with pytest.raises(NotImplementedError):
            assert component.set_guild_availability(123123, True)

    def test_update_guild(self, component):
        with pytest.raises(NotImplementedError):
            assert component.update_guild(object())

    def test_clear_guild_channels(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_guild_channels()

    def test_clear_guild_channels_for_guild(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_guild_channels_for_guild(123123123)

    def test_delete_guild_channel(self, component):
        with pytest.raises(NotImplementedError):
            assert component.delete_guild_channel(652341234)

    def test_get_guild_channel(self, component):
        assert component.get_guild_channel(3234243) is None

    def test_get_guild_channels_view(self, component):
        assert component.get_guild_channels_view() == {}

    def test_get_guild_channels_view_for_guild(self, component):
        assert component.get_guild_channels_view_for_guild(1234123) == {}

    def test_set_guild_channel(self, component):
        with pytest.raises(NotImplementedError):
            assert component.set_guild_channel(object())

    def test_update_guild_channel(self, component):
        with pytest.raises(NotImplementedError):
            assert component.update_guild_channel(object())

    def test_clear_invites(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_invites()

    def test_clear_invites_for_guild(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_invites_for_guild(123123)

    def test_clear_invites_for_channel(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_invites_for_channel(12354234, 753245234)

    def test_delete_invite(self, component):
        with pytest.raises(NotImplementedError):
            assert component.delete_invite("OKOKOKOKLKOK")

    def test_get_invite(self, component):
        assert component.get_invite("Okokok") is None

    def test_get_invites_view(self, component):
        assert component.get_invites_view() == {}

    def test_get_invites_view_for_guild(self, component):
        assert component.get_invites_view_for_guild(1342234123) == {}

    def test_get_invites_view_for_channel(self, component):
        assert component.get_invites_view_for_channel(123123, 542341234) == {}

    def test_set_invite(self, component):
        with pytest.raises(NotImplementedError):
            assert component.set_invite(object())

    def test_update_invite(self, component):
        with pytest.raises(NotImplementedError):
            assert component.update_invite(object())

    def test_delete_me_for_cached_me(self, component):
        me = object()
        component._me = me
        assert component.delete_me() is me
        assert component._me is None

    def test_delete_me_for_uncached_me(self, component):
        assert component.delete_me() is None
        assert component._me is None

    def test_get_me(self, component):
        me = mock.Mock(spec_set=users.OwnUser)
        component._me = me
        assert component.get_me() is me

    def test_set_me(self, component):
        me = mock.Mock(spec_set=users.OwnUser)
        component._me = object()
        component.set_me(me)
        assert component._me is me

    def test_update_me(self):
        old_cached_me = object()
        new_cached_me = object()
        me = object()
        component_ = hikari_test_helpers.mock_class_namespace(
            stateless_cache.StatelessCacheImpl,
            set_me=mock.Mock(),
            get_me=mock.Mock(side_effect=[old_cached_me, new_cached_me]),
        )()
        assert component_.update_me(me) == (old_cached_me, new_cached_me)
        component_.set_me.assert_called_once_with(me)
        component_.get_me.assert_has_calls([mock.call(), mock.call()])

    def test_clear_members(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_members()

    def test_clear_members_for_guild(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_members_for_guild(123123)

    def test_delete_member(self, component):
        with pytest.raises(NotImplementedError):
            assert component.delete_member(45234, 123123132)

    def test_get_member(self, component):
        assert component.get_member(345123, 5632452134) is None

    def test_get_members_view(self, component):
        assert component.get_members_view() == {}

    def test_get_members_view_for_guild(self, component):
        assert component.get_members_view_for_guild(354123) == {}

    def test_set_member(self, component):
        with pytest.raises(NotImplementedError):
            assert component.set_member(object())

    def test_update_member(self, component):
        with pytest.raises(NotImplementedError):
            assert component.update_member(object())

    def test_clear_presences(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_presences()

    def test_clear_presences_for_guild(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_presences_for_guild(1234123)

    def test_delete_presence(self, component):
        with pytest.raises(NotImplementedError):
            assert component.delete_presence(123, 54234)

    def test_get_presence(self, component):
        assert component.get_presence(123, 54234) is None

    def test_get_presences_view(self, component):
        assert component.get_presences_view() == {}

    def test_get_presences_view_for_guild(self, component):
        assert component.get_presences_view_for_guild(34123) == {}

    def test_set_presence(self, component):
        with pytest.raises(NotImplementedError):
            assert component.set_presence(object())

    def test_update_presence(self, component):
        with pytest.raises(NotImplementedError):
            assert component.update_presence(object())

    def test_clear_roles(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_roles() == {}

    def test_clear_roles_for_guild(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_roles_for_guild(43123123)

    def test_delete_role(self, component):
        with pytest.raises(NotImplementedError):
            assert component.delete_role(12353123)

    def test_get_role(self, component):
        assert component.get_role(351234) is None

    def test_get_roles_view(self, component):
        assert component.get_roles_view() == {}

    def test_get_roles_view_for_guild(self, component):
        assert component.get_roles_view_for_guild(43234) == {}

    def test_set_role(self, component):
        with pytest.raises(NotImplementedError):
            assert component.set_role(object())

    def test_update_role(self, component):
        with pytest.raises(NotImplementedError):
            assert component.update_role(object())

    def test_clear_users(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_users()

    def test_delete_user(self, component):
        with pytest.raises(NotImplementedError):
            assert component.delete_user(312312)

    def test_get_user(self, component):
        assert component.get_user(123123) is None

    def test_get_users_view(self, component):
        assert component.get_users_view() == {}

    def test_set_user(self, component):
        with pytest.raises(NotImplementedError):
            assert component.set_user(object())

    def test_update_user(self, component):
        with pytest.raises(NotImplementedError):
            assert component.update_user(object())

    def test_clear_voice_states(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_voice_states()

    def test_clear_voice_states_for_guild(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_voice_states_for_guild(1223123)

    def test_clear_voice_states_for_channel(self, component):
        with pytest.raises(NotImplementedError):
            assert component.clear_voice_states_for_channel(1236543, 43123)

    def test_delete_voice_state(self, component):
        with pytest.raises(NotImplementedError):
            assert component.delete_voice_state(3123, 6542134123)

    def test_get_voice_state(self, component):
        assert component.get_voice_state(123, 6234) is None

    def test_get_voice_states_view(self, component):
        assert component.get_voice_states_view() == {}

    def test_get_voice_states_view_for_channel(self, component):
        assert component.get_voice_states_view_for_channel(2123, 5234) == {}

    def test_get_voice_states_view_for_guild(self, component):
        assert component.get_voice_states_view_for_guild(54231324) == {}

    def test_set_voice_state(self, component):
        with pytest.raises(NotImplementedError):
            assert component.set_voice_state(object())

    def test_update_voice_state(self, component):
        with pytest.raises(NotImplementedError):
            assert component.update_voice_state(object())
