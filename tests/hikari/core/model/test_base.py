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
import dataclasses
import datetime
import enum

import pytest

from hikari.core.model import base


@dataclasses.dataclass()
class DummySnowflake(base.Snowflake):
    id: int


@pytest.fixture()
def neko_snowflake():
    return DummySnowflake(537340989808050216)


class DummyNamedEnum(base.NamedEnum, enum.IntEnum):
    FOO = 9
    BAR = 18
    BAZ = 27


@pytest.mark.model
class TestSnowflake:
    def test_Snowflake_init_subclass(self):
        instance = DummySnowflake(12345)
        assert instance is not None
        assert isinstance(instance, base.Snowflake)

    def test_Snowflake_comparison(self):
        assert DummySnowflake(12345) < DummySnowflake(12346)
        assert not (DummySnowflake(12345) < DummySnowflake(12345))
        assert not (DummySnowflake(12345) < DummySnowflake(12344))

        assert DummySnowflake(12345) <= DummySnowflake(12345)
        assert DummySnowflake(12345) <= DummySnowflake(12346)
        assert not (DummySnowflake(12346) <= DummySnowflake(12345))

        assert DummySnowflake(12347) > DummySnowflake(12346)
        assert not (DummySnowflake(12344) > DummySnowflake(12345))
        assert not (DummySnowflake(12345) > DummySnowflake(12345))

        assert DummySnowflake(12345) >= DummySnowflake(12345)
        assert DummySnowflake(12347) >= DummySnowflake(12346)
        assert not (DummySnowflake(12346) >= DummySnowflake(12347))

    @pytest.mark.parametrize("operator", [getattr(DummySnowflake, o) for o in ["__lt__", "__gt__", "__le__", "__ge__"]])
    def test_Snowflake_comparison_TypeError_cases(self, operator):
        try:
            operator(DummySnowflake(12345), object())
        except TypeError:
            pass
        else:
            assert False, f"No type error raised for bad comparison for {operator.__name__}"

    def test_Snowflake_created_at(self, neko_snowflake):
        assert neko_snowflake.created_at == datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000).replace(
            tzinfo=datetime.timezone.utc
        )

    def test_Snowflake_increment(self, neko_snowflake):
        assert neko_snowflake.increment == 40

    def test_Snowflake_internal_process_id(self, neko_snowflake):
        assert neko_snowflake.internal_process_id == 0

    def test_Snowflake_internal_worker_id(self, neko_snowflake):
        assert neko_snowflake.internal_worker_id == 2


@pytest.mark.model
def test_NamedEnumMixin_from_discord_name():
    assert DummyNamedEnum.from_discord_name("bar") == DummyNamedEnum.BAR


@pytest.mark.model
@pytest.mark.parametrize("cast", [str, repr], ids=lambda it: it.__qualname__)
def test_NamedEnumMixin_str_and_repr(cast):
    assert cast(DummyNamedEnum.BAZ) == "BAZ"


@pytest.mark.model
def test_no_hash_is_applied_to_dataclass_without_id():
    @base.dataclass()
    class NonIDDataClass:
        foo: int
        bar: float
        baz: str
        bork: object

    first = NonIDDataClass(10, 10.5, "11.0", object())
    second = NonIDDataClass(10, 10.9, "11.5", object())

    try:
        assert hash(first) != hash(second)
        assert False
    except TypeError as ex:
        assert "unhashable type" in str(ex)


@pytest.mark.model
def test_hash_is_applied_to_dataclass_with_id():
    @base.dataclass()
    class IDDataClass:
        id: int
        bar: float
        baz: str
        bork: object

    first = IDDataClass(10, 10.5, "11.0", object())
    second = IDDataClass(10, 10.9, "11.5", object())
    assert hash(first) == hash(second)
