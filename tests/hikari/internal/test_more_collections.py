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

from hikari.internal import more_collections


class TestWeakKeyDictionary:
    def test_is_weak(self):
        class Key:
            pass

        class Value:
            pass

        d: more_collections.WeakKeyDictionary[Key, Value] = more_collections.WeakKeyDictionary()

        key1 = Key()
        key2 = Key()
        value1 = Value()
        value2 = Value()

        d[key1] = value1
        d[key2] = value2

        assert key1 in d
        assert key2 in d
        assert value1 in d.values()
        assert value2 in d.values()
        del key2
        assert len([*d.keys()]) == 1
        assert value1 in d.values()
        assert value2 not in d.values()


class TestWeakValueDictionary:
    def test_is_weak(self):
        class Key:
            pass

        class Value:
            pass

        d: more_collections.WeakValueDictionary[Key, Value] = more_collections.WeakValueDictionary()

        key1 = Key()
        key2 = Key()
        value1 = Value()
        value2 = Value()

        d[key1] = value1
        d[key2] = value2

        assert key1 in d
        assert key2 in d
        del value2
        assert len([*d.keys()]) == 1
        assert key1 in d
        assert key2 not in d
