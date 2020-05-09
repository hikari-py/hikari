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
# along ith Hikari. If not, see <https://www.gnu.org/licenses/>.
import datetime
import typing

import attr
import mock
import pytest

from hikari import bases
from hikari.clients import components
from hikari.internal import marshaller


class TestHikariEntity:
    @pytest.fixture()
    def stub_entity(self) -> typing.Type["StubEntity"]:
        @marshaller.marshallable()
        @attr.s()
        class StubEntity(bases.HikariEntity, marshaller.Deserializable, marshaller.Serializable):
            ...

        return StubEntity

    def test_deserialize(self, stub_entity):
        mock_components = mock.MagicMock(components.Components)
        entity = stub_entity.deserialize({}, components=mock_components)
        assert entity._components is mock_components

    def test_serialize(self, stub_entity):
        mock_components = mock.MagicMock(components.Components)
        assert stub_entity(components=mock_components).serialize() == {}


class TestSnowflake:
    @pytest.fixture()
    def raw_id(self):
        return 537_340_989_808_050_216

    @pytest.fixture()
    def neko_snowflake(self, raw_id):
        return bases.Snowflake(raw_id)

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
        assert neko_snowflake == bases.Snowflake(raw_id)
        assert str(raw_id) != neko_snowflake

    def test_lt(self, neko_snowflake, raw_id):
        assert neko_snowflake < raw_id + 1

    def test_deserialize(self, neko_snowflake, raw_id):
        assert neko_snowflake == bases.Snowflake(raw_id)

    def test_from_datetime(self):
        result = bases.Snowflake.from_datetime(
            datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000, tzinfo=datetime.timezone.utc)
        )
        assert result == 537340989807788032
        assert isinstance(result, bases.Snowflake)

    def test_from_timestamp(self):
        result = bases.Snowflake.from_timestamp(1548182475.283)
        assert result == 537340989807788032
        assert isinstance(result, bases.Snowflake)

    def test_min(self):
        sf = bases.Snowflake.min()
        assert sf == 0
        assert bases.Snowflake.min() is sf

    def test_max(self):
        sf = bases.Snowflake.max()
        assert sf == (1 << 63) - 1
        assert bases.Snowflake.max() is sf


@marshaller.marshallable()
@attr.s(slots=True)
class StubEntity(bases.UniqueEntity, marshaller.Deserializable, marshaller.Serializable):
    ...


class TestUniqueEntity:
    def test_int(self):
        assert int(bases.UniqueEntity(id=bases.Snowflake("2333333"))) == 2333333

    def test_deserialize(self):
        unique_entity = StubEntity.deserialize({"id": "5445"})
        assert unique_entity.id == bases.Snowflake("5445")
        assert isinstance(unique_entity.id, bases.Snowflake)

    def test_serialize(self):
        assert StubEntity(id=bases.Snowflake(5445)).serialize() == {"id": "5445"}
