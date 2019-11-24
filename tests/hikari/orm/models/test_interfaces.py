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
import traceback
import typing

import pytest

from hikari.orm.models import interfaces


@dataclasses.dataclass()
class DummySnowflake(interfaces.ISnowflake):
    __slots__ = ("id",)
    id: int


@pytest.fixture()
def neko_snowflake():
    return DummySnowflake(537_340_989_808_050_216)


class DummyNamedEnum(interfaces.INamedEnum, enum.IntEnum):
    FOO = 9
    BAR = 18
    BAZ = 27


class DummyBestEffortEnum(interfaces.BestEffortEnumMixin, enum.IntEnum):
    FOO = 9
    BAR = 18
    BAZ = 27


@pytest.mark.model
class TestSnowflake:
    def test_Snowflake_init_subclass(self):
        instance = DummySnowflake(12345)
        assert instance is not None
        assert isinstance(instance, interfaces.ISnowflake)

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

    def test___eq___when_matching_type_and_matching_id(self):
        class SnowflakeImpl(interfaces.ISnowflake):
            __slots__ = ("id",)

            def __init__(self):
                self.id = 1

        assert SnowflakeImpl() == SnowflakeImpl()

    def test___eq___when_matching_type_but_no_matching_id(self):
        class SnowflakeImpl(interfaces.ISnowflake):
            __slots__ = ("id",)

            def __init__(self, id_):
                self.id = id_

        assert SnowflakeImpl(1) != SnowflakeImpl(2)

    def test___eq___when_no_matching_type_but_matching_id(self):
        class SnowflakeImpl1(interfaces.ISnowflake):
            __slots__ = ("id",)

            def __init__(self, id_):
                self.id = id_

        class SnowflakeImpl2(interfaces.ISnowflake):
            __slots__ = ("id",)

            def __init__(self, id_):
                self.id = id_

        assert SnowflakeImpl1(1) != SnowflakeImpl2(1)

    def test___eq___when_no_matching_type_and_no_matching_id(self):
        class SnowflakeImpl1(interfaces.ISnowflake):
            __slots__ = ("id",)

            def __init__(self, id_):
                self.id = id_

        class SnowflakeImpl2(interfaces.ISnowflake):
            __slots__ = ("id",)

            def __init__(self, id_):
                self.id = id_

        assert SnowflakeImpl1(1) != SnowflakeImpl2(2)


@pytest.mark.model
class TestNamedEnumMixin:
    def test_from_discord_name(self):
        assert DummyNamedEnum.from_discord_name("bar") == DummyNamedEnum.BAR

    @pytest.mark.parametrize("cast", [str, repr], ids=lambda it: it.__qualname__)
    def test_str_and_repr(self, cast):
        assert cast(DummyNamedEnum.BAZ) == "BAZ"


@pytest.mark.model
class TestBestEffortEnumMixin:
    def test_get_best_effort_from_name_happy_path(self):
        assert DummyBestEffortEnum.get_best_effort_from_name("BAR") == DummyBestEffortEnum.BAR

    def test_get_best_effort_from_name_sad_path(self):
        assert DummyBestEffortEnum.get_best_effort_from_name("BARr") == "BARr"

    def test_get_best_effort_from_value_happy_path(self):
        assert DummyBestEffortEnum.get_best_effort_from_value(18) == DummyBestEffortEnum.BAR

    def test_get_best_effort_from_value_sad_path(self):
        assert DummyBestEffortEnum.get_best_effort_from_value("BARr") == "BARr"

    @pytest.mark.parametrize("cast", [str, repr], ids=lambda it: it.__qualname__)
    def test_str_and_repr(self, cast):
        assert cast(DummyBestEffortEnum.BAZ) == "BAZ"


@pytest.mark.model
class TestIModel:
    def test_injects_dummy_init_if_interface(self):
        class Test(interfaces.IModel, interface=True):
            __slots__ = ()

        try:
            Test()
            assert False, "Expected TypeError"
        except TypeError:
            traceback.print_exc()
            assert True

    def test_does_not_inject_dummy_init_if_not_interface(self):
        class Test(interfaces.IModel, interface=False):
            __slots__ = ()

        assert Test()  # *shrug emoji*

    def test_copy(self):
        @dataclasses.dataclass()
        class Test(interfaces.IModel):
            __slots__ = ("data", "whatever")
            data: typing.List[int]
            whatever: object

            def __eq__(self, other):
                return self.data == other.data

        data = [1, 2, 3, object(), object()]
        whatever = object()
        test = Test(data, whatever)

        assert test.copy() is not test
        assert test.copy() == test
        assert test.copy().data is not data
        assert test.copy().data == data

        assert test.copy().whatever is not whatever

    def test_does_not_clone_fields_in___copy_by_ref___(self):
        @dataclasses.dataclass()
        class Test(interfaces.IModel):
            __copy_by_ref__ = ("data",)
            __slots__ = ("data",)
            data: typing.List[int]

        data = [1, 2, 3]
        test = Test(data)

        assert test.copy() is not test
        assert test.copy().data is data

    def test_does_not_clone_state_by_default_fields(self):
        @dataclasses.dataclass()
        class Test(interfaces.IModel):
            __copy_by_ref__ = ("foo",)
            __slots__ = ("foo", "_fabric")
            _fabric: typing.List[int]
            foo: int

        fabric = [1, 2, 3]
        foo = 12
        test = Test(fabric, foo)

        assert test.copy() is not test
        assert test.copy()._fabric is fabric

    def test___copy_by_ref___is_inherited(self):
        class Base1(interfaces.IModel):
            __copy_by_ref__ = ["a", "b", "c"]
            __slots__ = ("a", "b", "c")

        class Base2(Base1):
            __copy_by_ref__ = ["d", "e", "f"]
            __slots__ = ("d", "e", "f")

        class Base3(Base2):
            __copy_by_ref__ = ["g", "h", "i"]
            __slots__ = ("g", "h", "i")

        for letter in "abcdefghi":
            assert letter in Base3.__copy_by_ref__, f"{letter!r} was not inherited into __copy_by_ref__"

    def test___all_slots___is_inherited(self):
        class Base1(interfaces.IModel):
            __copy_by_ref__ = ["a", "b", "c"]
            __slots__ = ("a", "b", "c")

        class Base2(Base1):
            __copy_by_ref__ = ["d", "e", "f"]
            __slots__ = ("d", "e", "f")

        class Base3(Base2):
            __copy_by_ref__ = ["g", "h", "i"]
            __slots__ = ("g", "h", "i")

        for letter in "abcdefghi":
            assert letter in Base3.__all_slots__, f"{letter!r} was not inherited into __all_slots__"

    def test_non_slotted_IModel_refuses_to_initialize(self):
        try:

            class BadClass(interfaces.IModel):
                # look ma, no slots.
                pass

        except TypeError:
            assert True

    def test_slotted_IModel_can_initialize(self):
        try:

            class GoodClass(interfaces.IModel):
                __slots__ = ()

        except TypeError as ex:
            raise AssertionError from ex


@pytest.mark.model
class TestFabricatedMixin:
    def test_interface_FabricatedMixin_does_not_need_fabric(self):
        class Interface(interfaces.IStatefulModel, interface=True):
            __slots__ = ()

    def test_delegate_fabricated_FabricatedMixin_does_not_need_fabric(self):
        class Delegated(interfaces.IStatefulModel, delegate_fabricated=True):
            __slots__ = ()

    def test_regular_FabricatedMixin_fails_to_initialize_without_fabric_slot(self):
        try:

            class Regular(interfaces.IStatefulModel):
                __slots__ = ()

            assert False, "No TypeError was raised."
        except TypeError:
            assert True, "passed"

    def test_regular_FabricatedMixin_can_initialize_with_fabric_slot(self):
        class Regular(interfaces.IStatefulModel):
            __slots__ = ("_fabric",)
