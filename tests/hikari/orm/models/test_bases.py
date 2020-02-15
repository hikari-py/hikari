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
import asyncio
import dataclasses
import datetime
import enum
import functools
import typing
import weakref

import pytest

import hikari.internal_utilities.type_hints
from hikari.internal_utilities import delegate
from hikari.internal_utilities import type_hints
from hikari.orm.models import bases
from tests.hikari import _helpers


@dataclasses.dataclass()
class DummySnowflake(bases.BaseModel, bases.SnowflakeMixin):
    __slots__ = ("id",)
    id: int


@pytest.fixture
def neko_snowflake():
    return DummySnowflake(537_340_989_808_050_216)


class DummyNamedEnum(bases.NamedEnumMixin, enum.IntEnum):
    FOO = 9
    BAR = 18
    BAZ = 27


class DummyBestEffortEnum(bases.BestEffortEnumMixin, enum.IntEnum):
    FOO = 9
    BAR = 18
    BAZ = 27


class DummyBestEffortEnumStringBased(bases.BestEffortEnumMixin, enum.Enum):
    FOO = "bar"
    BAR = "baz"
    BAZ = "foo"


@pytest.mark.model
class TestSnowflake:
    def test_Snowflake_init_subclass(self):
        instance = DummySnowflake(12345)
        assert instance is not None
        assert isinstance(instance, bases.SnowflakeMixin)

    def test_Snowflake_is_resolved(self):
        assert DummySnowflake(12345).is_resolved is True

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
        class SnowflakeImpl(bases.BaseModel, bases.SnowflakeMixin):
            __slots__ = ("id",)

            def __init__(self):
                self.id = 1

        assert SnowflakeImpl() == SnowflakeImpl()

    def test___eq___when_matching_type_but_no_matching_id(self):
        class SnowflakeImpl(bases.BaseModel, bases.SnowflakeMixin):
            __slots__ = ("id",)

            def __init__(self, id_):
                self.id = id_

        assert SnowflakeImpl(1) != SnowflakeImpl(2)

    def test___eq___when_no_matching_type_but_matching_id(self):
        class SnowflakeImpl1(bases.BaseModel, bases.SnowflakeMixin):
            __slots__ = ("id",)

            def __init__(self, id_):
                self.id = id_

        class SnowflakeImpl2(bases.BaseModel, bases.SnowflakeMixin):
            __slots__ = ("id",)

            def __init__(self, id_):
                self.id = id_

        assert SnowflakeImpl1(1) != SnowflakeImpl2(1)

    def test___eq___when_no_matching_type_and_no_matching_id(self):
        class SnowflakeImpl1(bases.BaseModel, bases.SnowflakeMixin):
            __slots__ = ("id",)

            def __init__(self, id_):
                self.id = id_

        class SnowflakeImpl2(bases.BaseModel, bases.SnowflakeMixin):
            __slots__ = ("id",)

            def __init__(self, id_):
                self.id = id_

        assert SnowflakeImpl1(1) != SnowflakeImpl2(2)

    def test_cast_snowflake_to_int(self):
        class SnowflakeImpl(bases.BaseModel, bases.SnowflakeMixin):
            __slots__ = ("id",)

            def __init__(self, id_):
                self.id = id_

        assert int(SnowflakeImpl(9182736)) == 9182736


@pytest.mark.model
class TestNamedEnumMixin:
    def test_from_discord_name(self):
        assert DummyNamedEnum.from_discord_name("bar") is DummyNamedEnum.BAR

    def test_str(self):
        assert str(DummyNamedEnum.BAZ) == "baz"


@pytest.mark.model
class TestBestEffortEnumMixin:
    def test_get_best_effort_from_name_happy_path(self):
        assert DummyBestEffortEnum.get_best_effort_from_name("BAR") is DummyBestEffortEnum.BAR

    def test_get_best_effort_from_name_sad_path(self):
        assert DummyBestEffortEnum.get_best_effort_from_name("BARr") == "BARr"

    def test_get_best_effort_from_value_happy_path(self):
        assert DummyBestEffortEnum.get_best_effort_from_value(18) is DummyBestEffortEnum.BAR

    def test_get_best_effort_from_value_sad_path(self):
        assert DummyBestEffortEnum.get_best_effort_from_value("BARr") == "BARr"

    def test_str_and_repr(self):
        assert str(DummyBestEffortEnum.BAZ) == "baz"

    def test_str_with_non_int_based_enum(self):
        assert str(DummyBestEffortEnumStringBased.BAZ) == "foo"


@pytest.mark.model
class TestIModel:
    def test_injects_dummy_init_if_interface(self):
        class Test(bases.BaseModel, interface=True):
            __slots__ = ()

        try:
            Test()
            assert False, "Expected TypeError"
        except TypeError:
            assert True

    def test_does_not_inject_dummy_init_if_not_interface(self):
        class Test(bases.BaseModel, interface=False):
            __slots__ = ()

        assert Test()  # *shrug emoji*

    def test_copy(self):
        @dataclasses.dataclass()
        class Test(bases.BaseModel):
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

    def test_does_not_clone_fields_in___copy_by_ref__(self):
        @dataclasses.dataclass()
        class Test(bases.BaseModel):
            __copy_by_ref__ = ("data",)
            __slots__ = ("data",)
            data: typing.List[int]

        data = [1, 2, 3]
        test = Test(data)

        assert test.copy() is not test
        assert test.copy().data is data

    def test_does_not_write_fields_in___do_not_copy__(self):
        @dataclasses.dataclass()
        class Test(bases.BaseModel):
            __do_not_copy__ = ("data",)
            __slots__ = ("data",)
            data: typing.List[int]

        data = [1, 2, 3]
        test = Test(data)

        assert test.copy() is not test
        try:
            test.copy().data
            assert False, "this should have raised an AttributeError."
        except AttributeError:
            pass

    def test_does_not_clone_state_by_default_fields(self):
        @dataclasses.dataclass()
        class Test(bases.BaseModel):
            __copy_by_ref__ = ("foo",)
            __slots__ = ("foo", "_fabric")
            _fabric: typing.List[int]
            foo: int

        fabric = [1, 2, 3]
        foo = 12
        test = Test(fabric, foo)

        assert test.copy() is not test
        assert test.copy()._fabric is fabric

    def test_clone_with_weakrefs_does_not_copy_them(self):
        class WeakReffedModel(bases.BaseModel):
            __slots__ = ("foo", "bar", "__weakref__")

            def __init__(self, foo, bar):
                self.foo = foo
                self.bar = bar

        obj = WeakReffedModel(9, 18)
        # noinspection PyUnusedLocal
        obj_wr1 = weakref.proxy(obj)
        # noinspection PyUnusedLocal
        obj_wr2 = weakref.proxy(obj)
        # noinspection PyUnusedLocal
        obj_wr3 = weakref.proxy(obj)

        obj_copy = obj.copy()
        assert obj_copy.__weakref__ is not obj.__weakref__

    def test_clone_with_delegated_attributes_does_not_copy_them(self):
        @dataclasses.dataclass()
        class Base(bases.BaseModel):
            __slots__ = ("foo", "bar")
            foo: int
            bar: dict

        @delegate.delegate_to(Base, "_base")
        class Delegated(Base):
            __slots__ = ("_base", "baz")
            __copy_by_ref__ = ("_base",)

            def __init__(self, _base, baz):
                self._base = _base
                self.baz = baz

            _base: Base
            baz: list

        b = Base(1, {})
        d = Delegated(b, [])

        assert d.copy()._base is b
        assert d.copy().baz is not d.baz
        assert d.copy().foo is d.foo
        assert d.copy().bar is d.bar

    def test___copy_by_ref___is_inherited(self):
        class Base1(bases.BaseModel):
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
        class Base1(bases.BaseModel):
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

            class BadClass(bases.BaseModel):
                # look ma, no slots.
                pass

        except TypeError:
            assert True

    def test_slotted_IModel_can_initialize(self):
        try:

            class GoodClass(bases.BaseModel):
                __slots__ = ()

        except TypeError as ex:
            raise AssertionError from ex


@pytest.mark.model
class TestFabricatedMixin:
    def test_interface_FabricatedMixin_does_not_need_fabric(self):
        class Interface(bases.BaseModelWithFabric, interface=True):
            __slots__ = ()

    def test_delegate_fabricated_FabricatedMixin_does_not_need_fabric(self):
        class Delegated(bases.BaseModelWithFabric, delegate_fabricated=True):
            __slots__ = ()

    def test_regular_FabricatedMixin_fails_to_initialize_without_fabric_slot(self):
        try:

            class Regular(bases.BaseModelWithFabric):
                __slots__ = ()

            assert False, "No TypeError was raised."
        except TypeError:
            assert True, "passed"

    def test_regular_FabricatedMixin_can_initialize_with_fabric_slot(self):
        class Regular(bases.BaseModelWithFabric):
            __slots__ = ("_fabric",)


@pytest.mark.model
class TestUnknownObject:
    def test_is_resolved_is_False(self):
        assert bases.UnknownObject(1234, ...).is_resolved is False

    @pytest.mark.asyncio
    async def test_await_creates_future(self):
        async def coro(a, b, c):
            return a + b + c

        obj = bases.UnknownObject(1234, functools.partial(coro, 1, 2, 3))

        await obj

        assert isinstance(obj._future, asyncio.Future)

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=NotImplementedError)
    async def test_await_on_unawaitable_UnknownObject_errors(self):
        obj = bases.UnknownObject(1234)
        await obj

    @pytest.mark.asyncio
    async def test_await_yields_result(self):
        call_count = 0

        async def coro(a, b, c):
            nonlocal call_count
            call_count += 1
            return a + b + c

        obj = bases.UnknownObject(1234, functools.partial(coro, 1, 2, 3))

        for i in range(3):
            assert await obj == 6

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_callback_is_invoked(self):
        call_count = 0
        received_result = ...

        async def coro(a, b, c):
            return a + b + c

        def callback(result):
            nonlocal received_result, call_count
            call_count += 1
            received_result = result

        obj = bases.UnknownObject(1234, functools.partial(coro, 1, 2, 3))
        obj.add_done_callback(callback)

        for i in range(3):
            await obj

        assert call_count == 1
        assert received_result == 6

    @pytest.mark.asyncio
    async def test_callback_is_invoked_after_finished_asap(self):
        call_count = 0
        received_result = ...

        async def coro(a, b, c):
            return a + b + c

        def callback(result):
            nonlocal received_result, call_count
            call_count += 1
            received_result = result

        obj = bases.UnknownObject(1234, functools.partial(coro, 1, 2, 3))

        for i in range(3):
            await obj

        obj.add_done_callback(callback)

        await asyncio.sleep(0.1)

        assert call_count == 1
        assert received_result == 6


@dataclasses.dataclass()
class DummyModel(bases.MarshalMixin):
    __slots__ = ("is_a_dummy",)

    is_a_dummy: bool

    def __init__(self, is_a_dummy: bool):
        self.is_a_dummy = is_a_dummy


class DummyEnum(enum.Enum):
    NYAA = "nyaa"
    NEKOS = "neko"


@pytest.mark.model
def test_dict_factory_impl():
    mock_dict = bases.dict_factory_impl(
        (("name", DummyNamedEnum(9)), ("model", DummyModel(is_a_dummy=True))),
        ok="Test",
        neko=18,
        enumerated=DummyEnum("nyaa"),
        named_enumerated=DummyNamedEnum.from_discord_name("bar"),
    )

    assert mock_dict == {
        "name": 9,
        "model": {"is_a_dummy": True},
        "ok": "Test",
        "neko": 18,
        "enumerated": "nyaa",
        "named_enumerated": 18,
    }


@dataclasses.dataclass()
class DummyModel2(bases.MarshalMixin):
    __slots__ = ("id", "name", "nekos", "model", "optional")
    id: int
    name: str
    nekos: typing.List[int]
    model: DummyModel
    optional: type_hints.Nullable[str]

    def __init__(
        self,
        id: int,
        name: str,
        nekos: typing.List[int],
        model: hikari.internal_utilities.type_hints.JSONObject,
        optional=None,
    ):
        self.id = id
        self.name = name
        self.nekos = nekos
        self.model = DummyModel.from_dict(model)
        self.optional = optional


@pytest.mark.model
def test_MarshalMixin_from_dict():
    mock_object = DummyModel2.from_dict(
        {"id": 23123, "name": "Nyaa!", "nekos": [2, 6, 3], "model": {"is_a_dummy": True}}
    )
    assert mock_object.id == 23123
    assert mock_object.name == "Nyaa!"
    assert mock_object.nekos == [2, 6, 3]
    assert mock_object.optional is None
    assert isinstance(mock_object, DummyModel2)


@pytest.mark.model
def test_MarshalMixin_to_dict():
    mock_object = DummyModel2(1231, "boo", [2, 6, 3], {"is_a_dummy": True})
    assert mock_object.to_dict() == {"id": 1231, "name": "boo", "nekos": [2, 6, 3], "model": {"is_a_dummy": True}}
