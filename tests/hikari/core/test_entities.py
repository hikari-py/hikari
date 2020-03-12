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
import datetime

import attr
import cymock
import pytest

from hikari.core import entities


class TestEntity:
    def test_init_subclass_invokes_init_class(self):
        class SubEntity(entities.Entity):
            __init_class__ = cymock.MagicMock()

        SubEntity.__init_class__.assert_called_once_with(entities.Entity._converter)

    def test_serialize_unstructures_instance(self):
        @attr.s(slots=True)
        class SubEntity(entities.Entity):
            a_number: int = attr.ib()
            a_string: str = attr.ib()

        instance = SubEntity(9, "18")
        assert instance.serialize() == {"a_number": 9, "a_string": "18"}

    def test_deserialize_structures_new_instance(self):
        @attr.s(slots=True)
        class SubEntity(entities.Entity):
            a_number: int = attr.ib()
            a_string: str = attr.ib()

        assert SubEntity.deserialize({"a_number": 9, "a_string": "18"}) == SubEntity(9, "18")


class TestSnowflake:
    @pytest.fixture()
    def raw_id(self):
        return 537_340_989_808_050_216

    @pytest.fixture()
    def neko_snowflake(self, raw_id):
        return entities.Snowflake(raw_id)

    def test_created_at(self, neko_snowflake):
        assert neko_snowflake.created_at == datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000).replace(
            tzinfo=datetime.timezone.utc
        )

    def test_increment(self, neko_snowflake):
        assert neko_snowflake.increment == 40

    def test_internal_process_id(self, neko_snowflake):
        assert neko_snowflake.internal_process_id == 0

    def test_internal_worker_id(self, neko_snowflake):
        assert neko_snowflake.internal_worker_id == 2

    def test_int_cast(self, neko_snowflake, raw_id):
        assert int(neko_snowflake) == raw_id

    def test_str_cast(self, neko_snowflake, raw_id):
        assert str(neko_snowflake) == str(raw_id)

    def test_repr_cast(self, neko_snowflake, raw_id):
        assert repr(neko_snowflake) == repr(raw_id)

    def test_eq(self, neko_snowflake, raw_id):
        assert neko_snowflake == raw_id
        assert neko_snowflake == entities.Snowflake(raw_id)
        assert str(raw_id) != neko_snowflake

    def test_lt(self, neko_snowflake, raw_id):
        assert neko_snowflake < raw_id + 1


class TestHashable:
    def test_hashable_serializes_id_to_int(self):
        assert entities.Hashable(entities.Snowflake(12)).serialize() == {"id": "12"}

    def test_hashable_deserializes_id_to_int(self):
        assert entities.Hashable.deserialize({"id": "12"}) == entities.Hashable(entities.Snowflake(12))
