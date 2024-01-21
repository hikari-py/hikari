# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import builtins
import operator
import warnings

import mock
import pytest

from hikari.internal import deprecation
from hikari.internal import enums


class TestEnum:
    @mock.patch.object(enums, "_Enum", new=NotImplemented)
    def test_init_first_enum_type_populates_Enum(self):
        class Enum(metaclass=enums._EnumMeta):
            pass

        assert enums._Enum is Enum

    @mock.patch.object(enums, "_Enum", new=NotImplemented)
    def test_init_first_enum_type_with_wrong_name_and_no_bases_raises_TypeError(self):
        with pytest.raises(TypeError):

            class Potato(metaclass=enums._EnumMeta):
                pass

        assert enums._Enum is NotImplemented

    def test_init_second_enum_type_with_no_bases_does_not_change_Enum_attribute_and_raises_TypeError(self):
        expect = enums._Enum

        with pytest.raises(TypeError):

            class Enum(metaclass=enums._EnumMeta):
                pass

        assert enums._Enum is expect

    @pytest.mark.parametrize(
        ("args", "kwargs"),
        [([str], {"metaclass": enums._EnumMeta}), ([enums.Enum], {"metaclass": enums._EnumMeta}), ([enums.Enum], {})],
    )
    def test_init_enum_type_with_one_base_is_TypeError(self, args, kwargs):
        with pytest.raises(TypeError):

            class Enum(*args, **kwargs):
                pass

    @pytest.mark.parametrize(
        ("args", "kwargs"), [([enums.Enum, str], {"metaclass": enums._EnumMeta}), ([enums.Enum, str], {})]
    )
    def test_init_enum_type_with_bases_in_wrong_order_is_TypeError(self, args, kwargs):
        with pytest.raises(TypeError):

            class Enum(*args, **kwargs):
                pass

    def test_init_with_more_than_2_types(self):
        with pytest.raises(TypeError):

            class Enum(enums.Enum, str, int):
                pass

    def test_init_with_less_than_2_types(self):
        with pytest.raises(TypeError):

            class Enum(enums.Enum):
                pass

    def test_init_enum_type_default_docstring_set(self):
        class Enum(str, enums.Enum):
            pass

        assert Enum.__doc__ == "An enumeration."

    def test_init_enum_type_disallows_objects_that_are_not_instances_of_the_first_base(self):
        with pytest.raises(TypeError):

            class Enum(str, enums.Enum):
                foo = 1

    def test_init_enum_type_allows_any_object_if_it_has_a_dunder_name(self):
        class Enum(str, enums.Enum):
            __foo__ = 1
            __bar = 2

        assert Enum is not None

    def test_init_enum_type_allows_any_object_if_it_has_a_sunder_name(self):
        class Enum(str, enums.Enum):
            _foo_ = 1
            _bar = 2

        assert Enum is not None

    def test_init_enum_type_allows_methods(self):
        class Enum(int, enums.Enum):
            def foo(self):
                return "foo"

        assert Enum.foo(12) == "foo"

    def test_init_enum_type_allows_classmethods(self):
        class Enum(int, enums.Enum):
            @classmethod
            def foo(cls):
                assert cls is Enum
                return "foo"

        assert Enum.foo() == "foo"

    def test_init_enum_type_allows_staticmethods(self):
        class Enum(int, enums.Enum):
            @staticmethod
            def foo():
                return "foo"

        assert Enum.foo() == "foo"

    def test_init_enum_type_allows_descriptors(self):
        class Enum(int, enums.Enum):
            @property
            def foo(self):
                return "foo"

        assert isinstance(Enum.foo, property)

    def test_init_enum_type_maps_names_in_members(self):
        class Enum(int, enums.Enum):
            foo = 9
            bar = 18
            baz = 27

            @staticmethod
            def sm():
                pass

            @classmethod
            def cm(cls):
                pass

            def m(self):
                pass

            @property
            def p(self):
                pass

            __dunder__ = "aaa"
            _sunder_ = "bbb"
            __priv = "ccc"
            _prot = "ddd"

        assert Enum.__members__ == {"foo": 9, "bar": 18, "baz": 27}

    def test_init_with_invalid_name(self):
        with pytest.raises(TypeError):

            class Enum(int, enums.Enum):
                mro = 420

    def test_init_with_unhashable_value(self):
        with mock.patch.object(builtins, "hash", side_effect=TypeError):
            with pytest.raises(TypeError):

                class Enum(int, enums.Enum):
                    test = 420

    def test_init_with_duplicate(self):
        with pytest.raises(TypeError):

            class Enum(int, enums.Enum):
                test = 123
                test = 321

    def test_call_when_member(self):
        class Enum(int, enums.Enum):
            foo = 9
            bar = 18
            baz = 27

        returned = Enum(9)
        assert returned == Enum.foo
        assert type(returned) is Enum

    def test_call_when_not_member(self):
        class Enum(int, enums.Enum):
            foo = 9
            bar = 18
            baz = 27

        returned = Enum(69)
        assert returned == 69
        assert type(returned) is not Enum

    def test_getitem(self):
        class Enum(int, enums.Enum):
            foo = 9
            bar = 18
            baz = 27

        returned = Enum["foo"]
        assert returned == Enum.foo
        assert type(returned) is Enum

    def test_contains(self):
        class Enum(int, enums.Enum):
            foo = 9
            bar = 18
            baz = 27

        assert 9 in Enum
        assert 100 not in Enum

    def test_name(self):
        class Enum(int, enums.Enum):
            foo = 9
            bar = 18
            baz = 27

        assert Enum.foo.name == "foo"

    def test_iter(self):
        class Enum(int, enums.Enum):
            foo = 9
            bar = 18
            baz = 27

        a = []
        for i in Enum:
            a.append(i)

        assert a == [Enum.foo, Enum.bar, Enum.baz]

    def test_repr(self):
        class Enum(int, enums.Enum):
            foo = 9
            bar = 18
            baz = 27

        assert repr(Enum) == "<enum Enum>"
        assert repr(Enum.foo) == "<Enum.foo: 9>"

    def test_str(self):
        class Enum(int, enums.Enum):
            foo = 9
            bar = 18
            baz = 27

        assert str(Enum) == "<enum Enum>"
        assert str(Enum.foo) == "foo"

    def test_can_overwrite_method(self):
        class TestEnum1(str, enums.Enum):
            FOO = "foo"

            def __str__(self) -> str:
                return "Ok"

        assert str(TestEnum1.FOO) == "Ok"

    @pytest.mark.parametrize(("type_", "value"), [(int, 42), (str, "ok"), (bytes, b"no"), (float, 4.56), (complex, 3j)])
    def test_inherits_type_dunder_method_behaviour(self, type_, value):
        class TestEnum(type_, enums.Enum):
            BAR = value

        result = type_(TestEnum.BAR)

        assert type(result) is type_
        assert result == value

    def test_allows_overriding_methods(self):
        class TestEnum(int, enums.Enum):
            BAR = 2222

            def __int__(self):
                return 53

        assert int(TestEnum.BAR) == 53


class TestIntFlag:
    @mock.patch.object(enums, "_Flag", new=NotImplemented)
    def test_init_first_flag_type_populates_Flag(self):
        class Flag(metaclass=enums._FlagMeta):
            a = 1

        assert enums._Flag is Flag

    @mock.patch.object(enums, "_Flag", new=NotImplemented)
    def test_init_first_flag_type_with_wrong_name_and_no_bases_raises_TypeError(self):
        with pytest.raises(TypeError):

            class Potato(metaclass=enums._FlagMeta):
                a = 1

        assert enums._Flag is NotImplemented

    def test_init_second_flag_type_with_no_bases_does_not_change_Flag_attribute_and_raises_TypeError(self):
        expect = enums._Flag

        with pytest.raises(TypeError):

            class Flag(metaclass=enums._FlagMeta):
                a = 1

        assert enums._Flag is expect

    def test_init_flag_type_default_docstring_set(self):
        class Flag(enums.Flag):
            a = 1

        assert Flag.__doc__ == "An enumeration."

    def test_init_flag_type_disallows_objects_that_are_not_instances_int(self):
        with pytest.raises(TypeError):

            class Flag(enums.Flag):
                a = 1
                foo = "hi"

    def test_init_flag_type_disallows_other_bases(self):
        with pytest.raises(TypeError):

            class Flag(float, enums.Flag):
                a = 1

    def test_init_flag_type_allows_any_object_if_it_has_a_dunder_name(self):
        class Flag(enums.Flag):
            __foo__ = 1
            __bar = 2
            a = 3

        assert Flag is not None

    def test_init_flag_type_allows_any_object_if_it_has_a_sunder_name(self):
        class Flag(enums.Flag):
            _foo_ = 1
            _bar = 2
            a = 3

        assert Flag is not None

    def test_init_flag_type_allows_methods(self):
        class Flag(enums.Flag):
            A = 0x1

            def foo(self):
                return "foo"

        assert Flag().foo() == "foo"

    def test_init_flag_type_allows_classmethods(self):
        class Flag(enums.Flag):
            A = 0x1

            @classmethod
            def foo(cls):
                assert cls is Flag
                return "foo"

        assert Flag.foo() == "foo"

    def test_init_flag_type_allows_staticmethods(self):
        class Flag(enums.Flag):
            A = 0x1

            @staticmethod
            def foo():
                return "foo"

        assert Flag.foo() == "foo"

    def test_init_flag_type_allows_descriptors(self):
        class Flag(enums.Flag):
            A = 0x1

            @property
            def foo(self):
                return "foo"

        assert isinstance(Flag.foo, property)

    def test_name_to_member_map(self):
        class Flag(enums.Flag):
            foo = 9
            bar = 18
            baz = 27

            @staticmethod
            def sm():
                pass

            @classmethod
            def cm(cls):
                pass

            def m(self):
                pass

            @property
            def p(self):
                pass

        assert Flag._name_to_member_map_["foo"].__class__ is Flag
        assert Flag._name_to_member_map_["foo"] is Flag.foo

        assert Flag._name_to_member_map_["bar"].__class__ is Flag
        assert Flag._name_to_member_map_["bar"] is Flag.bar

        assert Flag._name_to_member_map_["baz"].__class__ is Flag
        assert Flag._name_to_member_map_["baz"] is Flag.baz

        assert len(Flag._name_to_member_map_) == 3

    def test_value_to_member_map(self):
        class Flag(enums.Flag):
            foo = 9
            bar = 18
            baz = 27

            @staticmethod
            def sm():
                pass

            @classmethod
            def cm(cls):
                pass

            def m(self):
                pass

            @property
            def p(self):
                pass

        assert Flag._value_to_member_map_[9].__class__ is Flag
        assert Flag._value_to_member_map_[9] is Flag.foo

        assert Flag._value_to_member_map_[18].__class__ is Flag
        assert Flag._value_to_member_map_[18] is Flag.bar

        assert Flag._value_to_member_map_[27].__class__ is Flag
        assert Flag._value_to_member_map_[27] is Flag.baz

    def test_member_names(self):
        class Flag(enums.Flag):
            foo = 9
            bar = 18
            baz = 27

            @staticmethod
            def sm():
                pass

            @classmethod
            def cm(cls):
                pass

            def m(self):
                pass

            @property
            def p(self):
                pass

        assert Flag._member_names_ == ["foo", "bar", "baz"]

    def test_members(self):
        class Flag(enums.Flag):
            foo = 9
            bar = 18
            baz = 27

            @staticmethod
            def sm():
                pass

            @classmethod
            def cm(cls):
                pass

            def m(self):
                pass

            @property
            def p(self):
                pass

        assert Flag.__members__["foo"].__class__ is int
        assert Flag.__members__["foo"] == 9

        assert Flag.__members__["bar"].__class__ is int
        assert Flag.__members__["bar"] == 18

        assert Flag.__members__["baz"].__class__ is int
        assert Flag.__members__["baz"] == 27

        assert len(Flag.__members__) == 3

    def test_call_on_existing_value(self):
        class Flag(enums.Flag):
            foo = 9
            bar = 18
            baz = 27

        assert Flag(9) is Flag.foo
        assert Flag(Flag.foo) is Flag.foo

    def test_call_on_composite_value(self):
        class Flag(enums.Flag):
            foo = 1
            bar = 2
            baz = 4

        assert Flag(3) is Flag.foo | Flag.bar
        assert Flag(Flag.foo | Flag.bar) is Flag.foo | Flag.bar

    def test_call_on_named_composite_value(self):
        class Flag(enums.Flag):
            foo = 1
            bar = 2
            baz = 3

        assert Flag(3) is Flag.baz
        assert Flag(Flag.foo | Flag.bar) is Flag.baz

    def test_call_on_invalid_value(self):
        class Flag(enums.Flag):
            foo = 1
            bar = 2
            baz = 3

        assert Flag(4) == 4

    def test_cache(self):
        class Flag(enums.Flag):
            foo = 1
            bar = 2
            baz = 4

        assert Flag._temp_members_ == {}
        # Cache something. Remember the dict is evaluated before the equality
        # so this will populate the cache.
        assert Flag._temp_members_ == {3: Flag.foo | Flag.bar}
        assert Flag._temp_members_ == {3: Flag.foo | Flag.bar, 7: Flag.foo | Flag.bar | Flag.baz}

        # Shouldn't mutate for existing items.
        assert Flag._temp_members_ == {3: Flag.foo | Flag.bar, 7: Flag.foo | Flag.bar | Flag.baz}
        assert Flag._temp_members_ == {3: Flag.foo | Flag.bar, 7: Flag.foo | Flag.bar | Flag.baz}

    def test_cache_when_temp_values_over_MAX_CACHED_MEMBERS(self):
        class MockDict:
            def __getitem__(self, key):
                raise KeyError

            def __len__(self):
                return enums._MAX_CACHED_MEMBERS + 1

            def __setitem__(self, k, v):
                pass

            popitem = mock.Mock()

        class Flag(enums.Flag):
            foo = 1
            bar = 2
            baz = 3

        Flag._temp_members_ = MockDict()

        Flag(4)
        Flag._temp_members_.popitem.assert_called_once_with()

    def test_bitwise_name(self):
        class Flag(enums.Flag):
            foo = 1
            bar = 2
            baz = 4

        assert Flag.foo.name == "foo"

    def test_combined_bitwise_name(self):
        class Flag(enums.Flag):
            foo = 1
            bar = 2
            baz = 4

        assert (Flag.foo | Flag.bar).name == "foo|bar"

    def test_combined_known_bitwise_name(self):
        class Flag(enums.Flag):
            foo = 1
            bar = 2
            baz = 3

        assert (Flag.foo | Flag.bar).name == "baz"

    def test_combined_partially_known_name(self):
        class Flag(enums.Flag):
            doo = 1
            laa = 2
            dee = 3

        # This is fine because it is not an identity or exact value.
        assert (Flag.laa | 4 | Flag.doo).name == "doo|laa|0x4"

    def test_combined_partially_known_combined_bitwise_name(self):
        class Flag(enums.Flag):
            foo = 1
            bar = 2
            baz = 3

        # This is fine because it is not an identity or exact value.
        assert (Flag.baz | 4).name == "foo|bar|0x4"

    def test_unknown_name(self):
        class Flag(enums.Flag):
            foo = 1
            bar = 2
            baz = 3

        assert Flag(4).name == "UNKNOWN 0x4"

    def test_value(self):
        class Flag(enums.Flag):
            foo = 1
            bar = 2
            baz = 3

        assert Flag.foo.value.__class__ is int
        assert Flag.foo.value == 1

        assert Flag.bar.value.__class__ is int
        assert Flag.bar.value == 2

        assert Flag.baz.value.__class__ is int
        assert Flag.baz.value == 3

    def test_is_instance_of_declaring_type(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8
            QUXX = QUX | BORK

        assert isinstance(TestFlag.BORK, TestFlag)
        assert isinstance(TestFlag.BORK, int)

        assert isinstance(TestFlag.QUXX, TestFlag)
        assert isinstance(TestFlag.QUXX, int)

    def test_and(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8
            QUXX = QUX | BORK

        assert TestFlag.QUXX & TestFlag.QUX == TestFlag.QUX
        assert TestFlag.QUXX & TestFlag.QUX == 0x8
        assert TestFlag.QUXX & 0x8 == 0x8
        assert isinstance(TestFlag.QUXX & TestFlag.QUX, TestFlag)
        assert isinstance(TestFlag.QUXX & TestFlag.QUX, int)

    def test_rand(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8
            QUXX = QUX | BORK

        assert 0x8 & TestFlag.QUXX == TestFlag.QUX
        assert 0x8 & TestFlag.QUXX == 0x8
        assert isinstance(0x8 & TestFlag.QUXX, TestFlag)
        assert isinstance(0x8 & TestFlag.QUXX, int)

    def test_all_positive_case(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val = TestFlag.BAZ | TestFlag.BORK

        assert val.all(TestFlag.FOO)

        assert val.all(TestFlag.FOO, TestFlag.BAR, TestFlag.BAZ, TestFlag.BORK)

    def test_all_negative_case(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8
            QUXX = 0x10

        val = TestFlag.BAZ | TestFlag.BORK

        assert not val.all(TestFlag.QUX)
        assert not val.all(TestFlag.BAZ, TestFlag.QUX, TestFlag.QUXX)

    def test_any_positive_case(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val = TestFlag.BAZ | TestFlag.BORK

        assert val.any(TestFlag.FOO)
        assert val.any(TestFlag.BAR)
        assert val.any(TestFlag.BAZ)
        assert val.any(TestFlag.BORK)
        # All present
        assert val.any(TestFlag.FOO, TestFlag.BAR, TestFlag.BAZ, TestFlag.BORK)
        # One present, one not
        assert val.any(TestFlag.FOO, TestFlag.QUX)

    def test_any_negative_case(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8
            QUXX = 0x10

        val = TestFlag.BAZ | TestFlag.BORK

        assert not val.any(TestFlag.QUX)

    def test_bool(self):
        class TestFlag(enums.Flag):
            BLEH = 0x0
            FOO = 0x1
            BAR = 0x2

        assert not TestFlag.BLEH
        assert TestFlag.FOO
        assert TestFlag.BAR

    def test_contains(self):
        class TestFlag(enums.Flag):
            BLEH = 0x1
            FOO = 0x2
            BAR = 0x4
            BAZ = 0x8

        f = TestFlag.FOO | TestFlag.BLEH | TestFlag.BAZ
        assert TestFlag.FOO in f
        assert TestFlag.BLEH in f
        assert TestFlag.BAZ in f
        assert TestFlag.BAR not in f

    def test_difference(self):
        class TestFlag(enums.Flag):
            A = 0x1
            B = 0x2
            C = 0x4
            D = 0x8
            E = 0x10
            F = 0x20
            G = 0x40
            H = 0x80

        a = TestFlag.A | TestFlag.B | TestFlag.D | TestFlag.F | TestFlag.G
        b = TestFlag.A | TestFlag.B | TestFlag.E
        c = 0x13
        expect_asubb = TestFlag.D | TestFlag.F | TestFlag.G
        expect_bsuba = TestFlag.E
        expect_asubc = 0x68

        assert a.difference(b) == expect_asubb
        assert b.difference(a) == expect_bsuba
        assert a.difference(c) == expect_asubc

        assert isinstance(a.difference(b), int)
        assert isinstance(a.difference(b), TestFlag)
        assert isinstance(a.difference(c), int)
        assert isinstance(a.difference(c), TestFlag)

    def test_index(self):
        class TestFlag(enums.Flag):
            OK = 0x5
            FOO = 0x312
            BAT = 0x3123

        assert operator.index(TestFlag.OK) == 0x5
        assert operator.index(TestFlag.FOO) == 0x312
        assert operator.index(TestFlag.BAT) == 0x3123

    def test_int(self):
        class TestFlag(enums.Flag):
            BLEH = 0x0
            FOO = 0x1
            BAR = 0x2

        assert int(TestFlag.BLEH) == 0x0
        assert int(TestFlag.FOO) == 0x1
        assert int(TestFlag.BAR) == 0x2

        assert type(int(TestFlag.BAR)) is int

    def test_intersection(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8
            QUXX = QUX | BORK

        assert TestFlag.QUXX.intersection(TestFlag.QUX) == TestFlag.QUX
        assert TestFlag.QUXX.intersection(TestFlag.QUX) == 0x8
        assert TestFlag.QUXX.intersection(0x8) == 0x8
        assert isinstance(TestFlag.QUXX.intersection(TestFlag.QUX), TestFlag)
        assert isinstance(TestFlag.QUXX.intersection(TestFlag.QUX), int)

    def test_invert(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x4

        assert TestFlag.BAR.invert() == TestFlag.FOO | TestFlag.BAZ

    def test_invert_op(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x4

        assert ~TestFlag.BAR == TestFlag.FOO | TestFlag.BAZ

    def test_is_disjoint(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x4
            BORK = 0x8
            QUX = 0x10

        assert (TestFlag.FOO | TestFlag.BAR).is_disjoint(TestFlag.BAZ | TestFlag.BORK)
        assert not (TestFlag.FOO | TestFlag.BAR).is_disjoint(TestFlag.BAR | TestFlag.BORK)
        assert (TestFlag.FOO | TestFlag.BAR).is_disjoint(0xC)
        assert not (TestFlag.FOO | TestFlag.BAR).is_disjoint(0xA)

    def test_isdisjoint(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x4
            BORK = 0x8
            QUX = 0x10

        assert (TestFlag.FOO | TestFlag.BAR).isdisjoint(TestFlag.BAZ | TestFlag.BORK)
        assert not (TestFlag.FOO | TestFlag.BAR).isdisjoint(TestFlag.BAR | TestFlag.BORK)
        assert (TestFlag.FOO | TestFlag.BAR).isdisjoint(0xC)
        assert not (TestFlag.FOO | TestFlag.BAR).isdisjoint(0xA)

    def test_is_subset(self):
        class TestFlag(enums.Flag):
            BLEH = 0x1
            FOO = 0x2
            BAR = 0x4
            BAZ = 0x8
            BORK = 0x10

        f = TestFlag.FOO | TestFlag.BLEH | TestFlag.BAZ
        assert f.is_subset(TestFlag.FOO)
        assert f.is_subset(TestFlag.BLEH)
        assert f.is_subset(TestFlag.BAZ)
        assert not f.is_subset(TestFlag.BAR)
        assert f.is_subset(0x2)
        assert f.is_subset(0x1)
        assert f.is_subset(0x8)
        assert not f.is_subset(0x4)
        assert f.is_subset(TestFlag.FOO | TestFlag.BLEH)
        assert f.is_subset(0x3)
        assert f.is_subset(TestFlag.FOO | TestFlag.BLEH)
        assert not f.is_subset(TestFlag.BAR | TestFlag.BORK)
        assert not f.is_subset(0x14)

    def test_issubset(self):
        class TestFlag(enums.Flag):
            BLEH = 0x1
            FOO = 0x2
            BAR = 0x4
            BAZ = 0x8
            BORK = 0x10

        f = TestFlag.FOO | TestFlag.BLEH | TestFlag.BAZ
        assert f.issubset(TestFlag.FOO)
        assert f.issubset(TestFlag.BLEH)
        assert f.issubset(TestFlag.BAZ)
        assert not f.issubset(TestFlag.BAR)
        assert f.issubset(0x2)
        assert f.issubset(0x1)
        assert f.issubset(0x8)
        assert not f.issubset(0x4)
        assert f.issubset(TestFlag.FOO | TestFlag.BLEH)
        assert f.issubset(0x3)
        assert not f.issubset(TestFlag.BAR | TestFlag.BORK)
        assert not f.issubset(0x14)

    def test_is_superset(self):
        class TestFlag(enums.Flag):
            BLEH = 0x1
            FOO = 0x2
            BAR = 0x4
            BAZ = 0x8
            BORK = 0x10
            QUX = 0x10

        f = TestFlag.FOO | TestFlag.BLEH | TestFlag.BAZ

        assert f.is_superset(TestFlag.BLEH | TestFlag.FOO | TestFlag.BAR | TestFlag.BAZ | TestFlag.BORK)
        assert f.is_superset(0x1F)
        assert not f.is_superset(TestFlag.QUX)
        assert not f.is_superset(0x20)

    def test_issuperset(self):
        class TestFlag(enums.Flag):
            BLEH = 0x1
            FOO = 0x2
            BAR = 0x4
            BAZ = 0x8
            BORK = 0x10
            QUX = 0x10

        f = TestFlag.FOO | TestFlag.BLEH | TestFlag.BAZ

        assert f.issuperset(TestFlag.BLEH | TestFlag.FOO | TestFlag.BAR | TestFlag.BAZ | TestFlag.BORK)
        assert f.issuperset(0x1F)
        assert not f.issuperset(TestFlag.QUX)
        assert not f.issuperset(0x20)

    def test_iter(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val_iter = iter(TestFlag)
        assert next(val_iter) == TestFlag.FOO
        assert next(val_iter) == TestFlag.BAR
        assert next(val_iter) == TestFlag.BAZ
        assert next(val_iter) == TestFlag.BORK
        assert next(val_iter) == TestFlag.QUX
        with pytest.raises(StopIteration):
            next(val_iter)

    def test_flag_iter(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val = TestFlag.BAZ | TestFlag.BORK
        val_iter = iter(val)
        assert next(val_iter) == TestFlag.BAR
        assert next(val_iter) == TestFlag.BORK
        assert next(val_iter) == TestFlag.FOO
        with pytest.raises(StopIteration):
            next(val_iter)

    def test_len(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val0 = TestFlag(0)
        val1 = TestFlag.FOO
        val2 = TestFlag.FOO | TestFlag.BORK
        val3 = TestFlag.FOO | TestFlag.BAR | TestFlag.BORK
        val3_comb = TestFlag.BAZ | TestFlag.BORK

        assert len(val0) == 0
        assert len(val1) == 1
        assert len(val2) == 2
        assert len(val3) == 3
        assert len(val3_comb) == 3

    def test_or(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x4
            BORK = 0x8
            QUX = 0x10

        assert isinstance(TestFlag.FOO | TestFlag.BAR, int)
        assert isinstance(TestFlag.FOO | TestFlag.BAR, TestFlag)
        assert isinstance(TestFlag.FOO | 0x2, int)
        assert isinstance(TestFlag.FOO | 0x2, TestFlag)

        assert TestFlag.FOO | TestFlag.BAR == 0x3
        assert TestFlag.FOO | TestFlag.BAR == TestFlag(0x3)
        assert TestFlag.FOO | 0x2 == 0x3
        assert TestFlag.FOO | 0x2 == TestFlag(0x3)

    def test_ror(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x4
            BORK = 0x8
            QUX = 0x10

        assert isinstance(0x2 | TestFlag.FOO, int)
        assert isinstance(0x2 | TestFlag.FOO, TestFlag)

        assert 0x2 | TestFlag.FOO == 0x3
        assert 0x2 | TestFlag.FOO == TestFlag(0x3)

    def test_none_positive_case(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8
            QUXX = 0x10

        val = TestFlag.BAZ | TestFlag.BORK

        assert val.none(TestFlag.QUX)

    def test_none_negative_case(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val = TestFlag.BAZ | TestFlag.BORK

        assert not val.none(TestFlag.FOO)
        assert not val.none(TestFlag.BAR)
        assert not val.none(TestFlag.BAZ)
        assert not val.none(TestFlag.BORK)
        # All present
        assert not val.none(TestFlag.FOO, TestFlag.BAR, TestFlag.BAZ, TestFlag.BORK)
        # One present, one not
        assert not val.none(TestFlag.FOO, TestFlag.QUX)

    def test_split(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val = TestFlag.BAZ | TestFlag.BORK

        # Baz is a combined field technically, so we don't expect it to be output here
        assert val.split() == [TestFlag.BAR, TestFlag.BORK, TestFlag.FOO]

    def test_str_operator(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x3
            BORK = 0x4
            QUX = 0x8

        val = TestFlag.BAZ | TestFlag.BORK

        assert str(val) == "FOO|BAR|BORK"

    def test_symmetric_difference(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x4
            BORK = 0x8
            QUX = 0x10

        a = TestFlag.FOO | TestFlag.BAR | TestFlag.BAZ
        b = TestFlag.BAZ | TestFlag.BORK | TestFlag.QUX

        assert isinstance(a.symmetric_difference(b), int)
        assert isinstance(a.symmetric_difference(b), TestFlag)
        assert isinstance(a.symmetric_difference(0x1C), int)
        assert isinstance(a.symmetric_difference(0x1C), TestFlag)

        assert a.symmetric_difference(b) == b.symmetric_difference(a)
        assert a.symmetric_difference(a) == 0
        assert b.symmetric_difference(b) == 0

        assert a.symmetric_difference(b) == TestFlag.FOO | TestFlag.BAR | TestFlag.BORK | TestFlag.QUX
        assert a.symmetric_difference(b) == 0x1B

    def test_sub(self):
        class TestFlag(enums.Flag):
            A = 0x1
            B = 0x2
            C = 0x4
            D = 0x8
            E = 0x10
            F = 0x20
            G = 0x40
            H = 0x80

        a = TestFlag.A | TestFlag.B | TestFlag.D | TestFlag.F | TestFlag.G
        b = TestFlag.A | TestFlag.B | TestFlag.E
        c = 0x13
        expect_asubb = TestFlag.D | TestFlag.F | TestFlag.G
        expect_bsuba = TestFlag.E
        expect_asubc = 0x68

        assert a - b == expect_asubb
        assert b - a == expect_bsuba
        assert a - c == expect_asubc

        assert isinstance(a - b, int)
        assert isinstance(a - b, TestFlag)
        assert isinstance(a - c, int)
        assert isinstance(a - c, TestFlag)

    def test_rsub(self):
        class TestFlag(enums.Flag):
            A = 0x1
            B = 0x2
            C = 0x4
            D = 0x8
            E = 0x10
            F = 0x20
            G = 0x40
            H = 0x80

        a = TestFlag.A | TestFlag.B | TestFlag.D | TestFlag.F | TestFlag.G
        c = 0x13
        expect_csuba = 0x10

        assert c - a == expect_csuba

        assert isinstance(c - a, int)
        assert isinstance(c - a, TestFlag)

    def test_union(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x4
            BORK = 0x8
            QUX = 0x10

        assert isinstance(TestFlag.FOO.union(TestFlag.BAR), int)
        assert isinstance(TestFlag.FOO.union(TestFlag.BAR), TestFlag)
        assert isinstance(TestFlag.FOO.union(TestFlag.BAR).union(TestFlag.BAZ), int)
        assert isinstance(TestFlag.FOO.union(TestFlag.BAR).union(TestFlag.BAZ), TestFlag)
        assert isinstance(TestFlag.FOO.union(0x2).union(TestFlag.BAZ), int)
        assert isinstance(TestFlag.FOO.union(0x2).union(TestFlag.BAZ), TestFlag)
        assert isinstance(TestFlag.FOO.union(0x2), int)
        assert isinstance(TestFlag.FOO.union(0x2), TestFlag)

        assert TestFlag.FOO.union(TestFlag.BAR) == 0x3
        assert TestFlag.FOO.union(TestFlag.BAR) == TestFlag(0x3)
        assert TestFlag.FOO.union(0x2) == 0x3
        assert TestFlag.FOO.union(0x2) == TestFlag(0x3)

    def test_xor(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x4
            BORK = 0x8
            QUX = 0x10

        a = TestFlag.FOO | TestFlag.BAR | TestFlag.BAZ
        b = TestFlag.BAZ | TestFlag.BORK | TestFlag.QUX

        assert isinstance(a ^ b, int)
        assert isinstance(a ^ b, TestFlag)
        assert isinstance(a ^ 0x1C, int)
        assert isinstance(a ^ 0x1C, TestFlag)

        assert a ^ b == b ^ a
        assert a ^ a == 0
        assert b ^ b == 0

        assert a ^ b == TestFlag.FOO | TestFlag.BAR | TestFlag.BORK | TestFlag.QUX
        assert a ^ b == 0x1B
        assert a ^ 0x1C == TestFlag.FOO | TestFlag.BAR | TestFlag.BORK | TestFlag.QUX
        assert a ^ 0x1C == 0x1B

    def test_rxor(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x4
            BORK = 0x8
            QUX = 0x10

        a = TestFlag.FOO | TestFlag.BAR | TestFlag.BAZ

        assert isinstance(0x1C ^ a, int)
        assert isinstance(0x1C ^ a, TestFlag)
        assert 0x1C ^ a == TestFlag.FOO | TestFlag.BAR | TestFlag.BORK | TestFlag.QUX
        assert 0x1C ^ a == 0x1B

    def test_getitem(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x4
            BORK = 0x8
            QUX = 0x10

        returned = TestFlag["FOO"]
        assert returned == TestFlag.FOO
        assert type(returned) is TestFlag

    def test_repr(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x4
            BORK = 0x8
            QUX = 0x10

        assert repr(TestFlag) == "<enum TestFlag>"
        assert repr(TestFlag.FOO) == "<TestFlag.FOO: 1>"

    def test_allows_overriding_methods(self):
        class TestFlag(enums.Flag):
            FOO = 0x1
            BAR = 0x2
            BAZ = 0x4
            BORK = 0x8
            QUX = 0x10

            def __int__(self):
                return 855555

        assert int(TestFlag.FOO | TestFlag.BAR) == 855555


def test_deprecated():
    with mock.patch.object(deprecation, "check_if_past_removal"):

        class Enum(int, enums.Enum):
            OK_VALUE = 1
            DEPRECATED = enums.deprecated(OK_VALUE, removal_version="4.0.0")

        with mock.patch.object(warnings, "warn") as warn:
            assert Enum.DEPRECATED == Enum.OK_VALUE
            warn.assert_called_once()
            warn.reset_mock()

            assert Enum["DEPRECATED"] == Enum.OK_VALUE
            warn.assert_called_once()
            warn.reset_mock()

            assert Enum.DEPRECATED.value == Enum.OK_VALUE.value
            warn.assert_called_once()
            warn.reset_mock()

            # Ensure we didn't break any other attributes
            assert Enum(1) == Enum.OK_VALUE
            warn.assert_not_called()

            Enum.OK_VALUE
            warn.assert_not_called()
