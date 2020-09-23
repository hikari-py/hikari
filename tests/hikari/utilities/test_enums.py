# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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
import mock
import pytest

from hikari.utilities import enums


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
        ("args", "kwargs"),
        [
            ([enums.Enum, str], {"metaclass": enums._EnumMeta}),
            ([enums.Enum, str], {}),
        ],
    )
    def test_init_enum_type_with_bases_in_wrong_order_is_TypeError(self, args, kwargs):
        with pytest.raises(TypeError):

            class Enum(*args, **kwargs):
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

    def test_init_enum_type_maps_names_in___members__(self):
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

    def test___call___when_member(self):
        class Enum(int, enums.Enum):
            foo = 9
            bar = 18
            baz = 27

        returned = Enum(9)
        assert returned == Enum.foo
        assert type(returned) == Enum

    def test___call___when_not_member(self):
        class Enum(int, enums.Enum):
            foo = 9
            bar = 18
            baz = 27

        returned = Enum(69)
        assert returned == 69
        assert type(returned) != Enum

    def test___getitem__(self):
        class Enum(int, enums.Enum):
            foo = 9
            bar = 18
            baz = 27

        returned = Enum["foo"]
        assert returned == Enum.foo
        assert type(returned) == Enum
