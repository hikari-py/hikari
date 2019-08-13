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

from hikari.core.state import cache


@pytest.mark.state
class TestInMemoryCache:
    @pytest.fixture()
    def mock_cache_init(self):
        class MockedCacheInit(cache.InMemoryCache):
            # noinspection PyMissingConstructor
            def __init__(self, *args, **kwargs):
                pass

        return MockedCacheInit()

    def test_get_user_by_id_calls_get(self):
        c = cache.InMemoryCache()
        c._users = mock.MagicMock(spec_set=dict)

        c.get_user_by_id(123)
        c._users.get.assert_called_once_with(123)

    def test_get_guild_by_id_calls_get(self):
        c = cache.InMemoryCache()
        c._guilds = mock.MagicMock(spec_set=dict)

        c.get_guild_by_id(123)
        c._guilds.get.assert_called_once_with(123)

    def test_get_message_by_id_calls_get(self):
        c = cache.InMemoryCache()
        c._messages = mock.MagicMock()

        c.get_message_by_id(123)
        c._messages.get.assert_called_once_with(123)

    @pytest.mark.xfail
    def test_parse_existing_user(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_new_user(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_existing_guild(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_new_guild(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_existing_member(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_new_member(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_existing_role(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_new_role(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_existing_emoji(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_new_emoji(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_existing_message(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_new_message(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_existing_channel(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_new_channel(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_existing_webhook(self):
        raise NotImplementedError  # TODO

    @pytest.mark.xfail
    def test_parse_new_webhook(self):
        raise NotImplementedError  # TODO
