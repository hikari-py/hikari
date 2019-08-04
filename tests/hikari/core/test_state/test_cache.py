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
import pytest

from hikari.core.state import cache


@pytest.mark.state
class TestLRUDict:
    def test_init_calls_dict_factory(self):
        class SomeDict(dict):
            pass

        c = cache.LRUDict(123, dict_factory=SomeDict)
        assert isinstance(c._data, SomeDict)

    def test_init_sets_lru_cache_size(self):
        c = cache.LRUDict(123)
        assert c._lru_size == 123

    def test_get_item(self):
        c = cache.LRUDict(123)
        c._data["foo"] = "bar"

        assert c["foo"] == "bar"

    def test_set_item_when_lru_has_space(self):
        c = cache.LRUDict(123)
        first_size = len(c._data)
        c["foo"] = "bar"
        second_size = len(c._data)
        assert c._data["foo"] == "bar"
        assert second_size == first_size + 1

    def test_set_item_when_lru_is_full(self):
        c = cache.LRUDict(4)
        data = c._data
        data["foo"] = 1
        data["bar"] = 2
        data["baz"] = 3
        data["bork"] = 4
        first_size = len(data)
        c["qux"] = 5
        second_size = len(data)
        assert first_size == second_size
        assert data["qux"] == 5
        assert "foo" not in "data"

    def test_del_item(self):
        c = cache.LRUDict(123)
        c._data["foo"] = "bar"
        del c["foo"]
        assert "foo" not in c._data

    def test_len(self):
        c = cache.LRUDict(123)
        c._data = {"foo": 1, "bar": 2, "baz": 3}
        assert len(c) == len(c._data) == 3

    def test_iter(self):
        c = cache.LRUDict(123)
        c._data = {"foo": 1, "bar": 2, "baz": 3}
        iterable = [*iter(c)]
        assert iterable == ["foo", "bar", "baz"]


@pytest.mark.state
class TestCache:
    @pytest.fixture()
    def mock_cache_init(self):
        class MockedCacheInit(cache.Cache):
            def __init__(self, *args, **kwargs):
                pass
        return MockedCacheInit()

    def test_init_can_run_successfully(self):
        assert cache.Cache() is not None
