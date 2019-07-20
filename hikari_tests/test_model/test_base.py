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

import pytest

import asynctest

from hikari import utils
from hikari.model import base


@dataclasses.dataclass()
class DummyModel(base.StatefulModel):
    @classmethod
    def from_dict(cls, payload: utils.DiscordObject, state):
        return super().from_dict(payload, state)


@dataclasses.dataclass()
class DummySnowflake(base.Snowflake):
    @classmethod
    def from_dict(cls, payload: utils.DiscordObject, state):
        return super().from_dict(payload, state)


@pytest.fixture()
def dummy_model():
    return DummyModel(NotImplemented)


@pytest.fixture()
def neko_snowflake():
    return DummySnowflake(NotImplemented, 537340989808050216)


class DummyNamedEnum(base.NamedEnum):
    FOO = 9
    BAR = 18
    BAZ = 27


@pytest.mark.model
class TestModel:
    def test_Model_init_subclass(self, dummy_model):
        assert dummy_model is not None
        assert isinstance(dummy_model, base.StatefulModel)

    def test_Model_from_dict_defaults_to_NotImplemented(self):
        assert DummyModel.from_dict(dict(), object()) is NotImplemented


@pytest.mark.model
class TestSnowflake:
    def test_Snowflake_init_subclass(self):
        instance = DummySnowflake(NotImplemented, id=12345)
        assert instance is not None
        assert isinstance(instance, base.Snowflake)
        assert isinstance(instance, base.StatefulModel)

    def test_Snowflake_from_dict_calls_Model_from_dict(self):
        with asynctest.patch("hikari.model.base.Model.from_dict", asynctest.MagicMock()):
            DummySnowflake.from_dict({}, NotImplemented)
            assert base.StatefulModel.from_dict.called_once_with(NotImplemented)

    def test_Snowflake_comparison(self):
        assert DummySnowflake(NotImplemented, 12345) < DummySnowflake(NotImplemented, 12346)
        assert not (DummySnowflake(NotImplemented, 12345) < DummySnowflake(NotImplemented, 12345))
        assert not (DummySnowflake(NotImplemented, 12345) < DummySnowflake(NotImplemented, 12344))

        assert DummySnowflake(NotImplemented, 12345) <= DummySnowflake(NotImplemented, 12345)
        assert DummySnowflake(NotImplemented, 12345) <= DummySnowflake(NotImplemented, 12346)
        assert not (DummySnowflake(NotImplemented, 12346) <= DummySnowflake(NotImplemented, 12345))

        assert DummySnowflake(NotImplemented, 12347) > DummySnowflake(NotImplemented, 12346)
        assert not (DummySnowflake(NotImplemented, 12344) > DummySnowflake(NotImplemented, 12345))
        assert not (DummySnowflake(NotImplemented, 12345) > DummySnowflake(NotImplemented, 12345))

        assert DummySnowflake(NotImplemented, 12345) >= DummySnowflake(NotImplemented, 12345)
        assert DummySnowflake(NotImplemented, 12347) >= DummySnowflake(NotImplemented, 12346)
        assert not (DummySnowflake(NotImplemented, 12346) >= DummySnowflake(NotImplemented, 12347))

    @pytest.mark.parametrize("operator", [getattr(DummySnowflake, o) for o in ["__lt__", "__gt__", "__le__", "__ge__"]])
    def test_Snowflake_comparison_TypeError_cases(self, operator):
        try:
            operator(DummySnowflake(NotImplemented, 12345), object())
        except TypeError:
            pass
        else:
            assert False, f"No type error raised for bad comparison for {operator.__name__}"

    def test_Snowflake_created_at(self, neko_snowflake):
        assert neko_snowflake.created_at == datetime.datetime(2019, 1, 22, 18, 41, 15, 283_000)

    def test_Snowflake_increment(self, neko_snowflake):
        assert neko_snowflake.increment == 40

    def test_Snowflake_internal_process_id(self, neko_snowflake):
        assert neko_snowflake.internal_process_id == 0

    def test_Snowflake_internal_worker_id(self, neko_snowflake):
        assert neko_snowflake.internal_worker_id == 2


@pytest.mark.model
def test_NamedEnum_from_discord_name():
    assert DummyNamedEnum.from_discord_name("bar") == DummyNamedEnum.BAR


@pytest.mark.model
def test_PartialObject_just_id():
    assert base.PartialObject.from_dict({"id": "123456"}, NotImplemented) is not None


@pytest.mark.model
def test_PartialObject_dynamic_attrs():
    po = base.PartialObject.from_dict({"id": "123456", "foo": 69, "bar": False}, NotImplemented)
    assert po.id == 123456
    assert po.foo == 69
    assert po.bar is False
