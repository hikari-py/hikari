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
import pytest

from hikari import entities
from hikari import snowflakes
from hikari.internal import marshaller


class TestSnowflake:
    @pytest.fixture()
    def raw_id(self):
        return 537_340_989_808_050_216

    @pytest.fixture()
    def neko_snowflake(self, raw_id):
        return snowflakes.Snowflake.deserialize(raw_id)

    def test_created_at(self, neko_snowflake):
        assert neko_snowflake.created_at == datetime.datetime(
            2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc
        )

    def test_increment(self, neko_snowflake):
        assert neko_snowflake.increment == 40

    def test_internal_process_id(self, neko_snowflake):
        assert neko_snowflake.internal_process_id == 0

    def test_internal_worker_id(self, neko_snowflake):
        assert neko_snowflake.internal_worker_id == 2

    def test_hash(self, neko_snowflake, raw_id):
        assert hash(neko_snowflake) == raw_id

    def test_int_cast(self, neko_snowflake, raw_id):
        assert int(neko_snowflake) == raw_id

    def test_str_cast(self, neko_snowflake, raw_id):
        assert str(neko_snowflake) == str(raw_id)

    def test_repr_cast(self, neko_snowflake, raw_id):
        assert repr(neko_snowflake) == repr(raw_id)

    def test_eq(self, neko_snowflake, raw_id):
        assert neko_snowflake == raw_id
        assert neko_snowflake == snowflakes.Snowflake.deserialize(raw_id)
        assert str(raw_id) != neko_snowflake

    def test_lt(self, neko_snowflake, raw_id):
        assert neko_snowflake < raw_id + 1

    def test_deserialize(self, neko_snowflake, raw_id):
        assert neko_snowflake == snowflakes.Snowflake.deserialize(raw_id)

    def test_from_datetime(self):
        result = snowflakes.Snowflake.from_datetime(
            datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        )
        assert result == 537340988620800000
        assert isinstance(result, snowflakes.Snowflake)

    def test_from_timestamp(self):
        result = snowflakes.Snowflake.from_timestamp(1548182475.283)
        assert result == 537340988620800000
        assert isinstance(result, snowflakes.Snowflake)


class TestUniqueEntity:
    def test_int(self):
        assert int(snowflakes.UniqueEntity(id=snowflakes.Snowflake.deserialize("2333333"))) == 2333333

    @pytest.fixture()
    def stud_marshal_entity(self):
        @marshaller.marshallable()
        @attr.s(slots=True)
        class StudEntity(snowflakes.UniqueEntity, entities.Deserializable, entities.Serializable):
            ...

        return StudEntity

    def test_deserialize(self, stud_marshal_entity):
        unique_entity = stud_marshal_entity.deserialize({"id": "5445"})
        assert unique_entity.id == snowflakes.Snowflake("5445")
        assert isinstance(unique_entity.id, snowflakes.Snowflake)

    def test_serialize(self, stud_marshal_entity):
        assert stud_marshal_entity(id=snowflakes.Snowflake(5445)).serialize() == {"id": "5445"}
