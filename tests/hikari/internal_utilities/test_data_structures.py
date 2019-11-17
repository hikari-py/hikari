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

from hikari.internal_utilities import data_structures


class TestObjectProxy:
    def test_ObjectProxy___getattr__(self):
        dop = data_structures.ObjectProxy({"foo": "bar"})
        assert dop["foo"] == dop.foo

    def test_ObjectProxy___setattr__(self):
        dop = data_structures.ObjectProxy({"foo": "bar"})
        dop["foof"] = 123
        assert dop["foof"] == 123

    def test_ObjectProxy___setitem__(self):
        dop = data_structures.ObjectProxy({"foo": "bar"})
        dop.foof = 456
        assert dop.foof == 456

    def test_ObjectProxy___delattr__(self):
        dop = data_structures.ObjectProxy({"foo": "bar"})
        assert "foo" in dop
        del dop["foo"]
        assert "foo" not in dop

    def test_ObjectProxy___delitem__(self):
        dop = data_structures.ObjectProxy({"foo": "bar"})
        assert "foo" in dop
        del dop.foo
        assert "foo" not in dop

    def test_json_module_handles_as_expected_flat(self):
        import json

        d = json.loads('{"foo": "bar"}', object_hook=data_structures.ObjectProxy)
        assert d == {"foo": "bar"}
        assert d.foo == "bar"

    def test_json_module_handles_as_expected_nested_in_object(self):
        import json

        d = json.loads('{"foo": "bar", "baz": [{"id": 1}, {"id": 2}]}', object_hook=data_structures.ObjectProxy)
        assert d == {"foo": "bar", "baz": [{"id": 1}, {"id": 2}]}
        assert d.baz[1].id == 2


class TestLRUDict:
    def test_init_calls_dict_factory(self):
        class SomeDict(dict):
            pass

        c = data_structures.LRUDict(123, dict_factory=SomeDict)
        assert isinstance(c._data, SomeDict)

    def test_init_sets_lru_cache_size(self):
        c = data_structures.LRUDict(123)
        assert c._lru_size == 123

    def test_get_item(self):
        c = data_structures.LRUDict(123)
        c._data["foo"] = "bar"

        assert c["foo"] == "bar"

    def test_set_item_when_lru_has_space(self):
        c = data_structures.LRUDict(123)
        first_size = len(c._data)
        c["foo"] = "bar"
        second_size = len(c._data)
        assert c._data["foo"] == "bar"
        assert second_size == first_size + 1

    def test_set_item_when_lru_is_full(self):
        c = data_structures.LRUDict(4)
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
        c = data_structures.LRUDict(123)
        c._data["foo"] = "bar"
        del c["foo"]
        assert "foo" not in c._data

    def test_len(self):
        c = data_structures.LRUDict(123)
        c._data = {"foo": 1, "bar": 2, "baz": 3}
        assert len(c) == len(c._data) == 3

    def test_iter(self):
        c = data_structures.LRUDict(123)
        c._data = {"foo": 1, "bar": 2, "baz": 3}
        iterable = [*iter(c)]
        assert iterable == ["foo", "bar", "baz"]


class TestDefaultImmutableMapping:
    def test_init(self):
        m = data_structures.DefaultImmutableMapping({"foo": "bar"}, 12)
        assert m._data == {"foo": "bar"}
        assert m._default == 12

    def test_immutability_external(self):
        try:
            m = data_structures.DefaultImmutableMapping({"foo": "bar"}, 12)
            m["bar"] = 13
            assert False, "No error raised"
        except TypeError:
            assert True

    def test_immutability_internal(self):
        try:
            m = data_structures.DefaultImmutableMapping({"foo": "bar"}, 12)
            m._data["bar"] = 13
            assert False, "No error raised"
        except TypeError:
            assert True

    def test___getitem___happy_path(self):
        m = data_structures.DefaultImmutableMapping({"foo": "bar"}, 12)
        assert m["foo"] == "bar"

    def test___getitem___sad_path(self):
        m = data_structures.DefaultImmutableMapping({"foo": "bar"}, 12)
        assert m["baz"] == 12

    def test___len__(self):
        m = data_structures.DefaultImmutableMapping({"foo": "bar", "baz": "bork"}, 12)
        assert len(m) == 2

    def test___iter__(self):
        m = data_structures.DefaultImmutableMapping({"foo": "bar", "baz": "bork"}, 12)
        assert {*iter(m)} == {"foo", "baz"}
