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
import typing

import attr
import mock
import multidict
import pytest

from hikari.utilities import data_binding
from hikari.utilities import snowflake
from hikari.utilities import undefined


@attr.s(slots=True)
class MyUnique(snowflake.Unique):
    id: snowflake.Snowflake = attr.ib(converter=snowflake.Snowflake)


class TestStringMapBuilder:
    def test_is_mapping(self):
        assert isinstance(data_binding.StringMapBuilder(), typing.Mapping)

    def test_is_multidict(self):
        assert isinstance(data_binding.StringMapBuilder(), multidict.MultiDict)

    def test_starts_empty(self):
        mapping = data_binding.StringMapBuilder()
        assert mapping == {}

    def test_put_undefined(self):
        mapping = data_binding.StringMapBuilder()
        mapping.put("foo", undefined.UNDEFINED)
        assert dict(mapping) == {}

    def test_put_general_value_casts_to_str(self):
        m = mock.MagicMock()
        mapping = data_binding.StringMapBuilder()
        mapping.put("foo", m)
        assert dict(mapping) == {"foo": m.__str__()}

    def test_duplicate_puts_stores_values_as_sequence(self):
        m1 = mock.MagicMock()
        m2 = mock.MagicMock()
        mapping = data_binding.StringMapBuilder()
        mapping.put("foo", m1)
        mapping.put("foo", m2)
        assert mapping.getall("foo") == [m1.__str__(), m2.__str__()]
        assert list(mapping.keys()) == ["foo", "foo"]

    def test_put_Unique(self):
        mapping = data_binding.StringMapBuilder()

        mapping.put("myunique", MyUnique(123))
        assert dict(mapping) == {"myunique": "123"}

    def test_put_int(self):
        mapping = data_binding.StringMapBuilder()
        mapping.put("yeet", 420_69)
        assert dict(mapping) == {"yeet": "42069"}

    @pytest.mark.parametrize(
        ["name", "input_val", "expect"], [("a", True, "true"), ("b", False, "false"), ("c", None, "null")]
    )
    def test_put_py_singleton(self, name, input_val, expect):
        mapping = data_binding.StringMapBuilder()
        mapping.put(name, input_val)
        assert dict(mapping) == {name: expect}

    def test_put_with_conversion_uses_return_value(self):
        def convert(_):
            return "yeah, i got called"

        mapping = data_binding.StringMapBuilder()
        mapping.put("blep", "meow", conversion=convert)
        assert dict(mapping) == {"blep": "yeah, i got called"}

    def test_put_with_conversion_passes_raw_input_to_converter(self):
        mapping = data_binding.StringMapBuilder()
        convert = mock.MagicMock()

        expect = object()
        mapping.put("yaskjgakljglak", expect, conversion=convert)
        convert.assert_called_once_with(expect)

    def test_put_py_singleton_conversion_runs_before_check(self):
        def convert(_):
            return True

        mapping = data_binding.StringMapBuilder()
        mapping.put("im hungry", "yo", conversion=convert)
        assert dict(mapping) == {"im hungry": "true"}


class TestJSONObjectBuilder:
    def test_is_mapping(self):
        assert isinstance(data_binding.JSONObjectBuilder(), typing.Mapping)

    def test_starts_empty(self):
        assert data_binding.JSONObjectBuilder() == {}

    def test_put_undefined(self):
        builder = data_binding.JSONObjectBuilder()
        builder.put("foo", undefined.UNDEFINED)
        assert builder == {}

    def test_put_defined(self):
        m = mock.MagicMock()
        builder = data_binding.JSONObjectBuilder()
        builder.put("bar", m)
        assert builder == {"bar": m}

    def test_put_with_conversion_uses_conversion_result(self):
        m = mock.MagicMock()
        convert = mock.MagicMock()
        builder = data_binding.JSONObjectBuilder()
        builder.put("rawr", m, conversion=convert)
        assert builder == {"rawr": convert()}

    def test_put_with_conversion_passes_raw_input_to_converter(self):
        m = mock.MagicMock()
        convert = mock.MagicMock()
        builder = data_binding.JSONObjectBuilder()
        builder.put("bar", m, conversion=convert)
        convert.assert_called_once_with(m)

    def test_put_array_undefined(self):
        builder = data_binding.JSONObjectBuilder()
        builder.put_array("dd", undefined.UNDEFINED)
        assert builder == {}

    def test__put_array_defined(self):
        m1 = mock.MagicMock()
        m2 = mock.MagicMock()
        m3 = mock.MagicMock()
        builder = data_binding.JSONObjectBuilder()
        builder.put_array("ttt", [m1, m2, m3])
        assert builder == {"ttt": [m1, m2, m3]}

    def test_put_array_with_conversion_uses_conversion_result(self):
        r1 = mock.MagicMock()
        r2 = mock.MagicMock()
        r3 = mock.MagicMock()

        convert = mock.MagicMock(side_effect=[r1, r2, r3])
        builder = data_binding.JSONObjectBuilder()
        builder.put_array("www", [object(), object(), object()], conversion=convert)
        assert builder == {"www": [r1, r2, r3]}

    def test_put_array_with_conversion_passes_raw_input_to_converter(self):
        m1 = mock.MagicMock()
        m2 = mock.MagicMock()
        m3 = mock.MagicMock()

        convert = mock.MagicMock()
        builder = data_binding.JSONObjectBuilder()
        builder.put_array("xxx", [m1, m2, m3], conversion=convert)
        assert convert.call_args_list[0] == mock.call(m1)
        assert convert.call_args_list[1] == mock.call(m2)
        assert convert.call_args_list[2] == mock.call(m3)

    def test_put_snowflake_undefined(self):
        builder = data_binding.JSONObjectBuilder()
        builder.put_snowflake("nya!", undefined.UNDEFINED)
        assert builder == {}

    @pytest.mark.parametrize(
        ("input_value", "expected_str"),
        [
            (100123, "100123"),
            ("100124", "100124"),
            (MyUnique(100127), "100127"),
            (MyUnique("100129"), "100129"),
            (snowflake.Snowflake(100125), "100125"),
            (snowflake.Snowflake("100126"), "100126"),
        ],
    )
    def test_put_snowflake(self, input_value, expected_str):
        builder = data_binding.JSONObjectBuilder()
        builder.put_snowflake("WAWAWA!", input_value)
        assert builder == {"WAWAWA!": expected_str}

    @pytest.mark.parametrize(
        ("input_value", "expected_str"),
        [
            (100123, "100123"),
            ("100124", "100124"),
            (MyUnique(100127), "100127"),
            (MyUnique("100129"), "100129"),
            (snowflake.Snowflake(100125), "100125"),
            (snowflake.Snowflake("100126"), "100126"),
        ],
    )
    def test_put_snowflake_array_conversions(self, input_value, expected_str):
        builder = data_binding.JSONObjectBuilder()
        builder.put_snowflake_array("WAWAWAH!", [input_value] * 5)
        assert builder == {"WAWAWAH!": [expected_str] * 5}

    def test_put_snowflake_array(self):
        builder = data_binding.JSONObjectBuilder()
        builder.put_snowflake_array("DESU!", [123, 456, 987, 115])
        assert builder == {"DESU!": ["123", "456", "987", "115"]}

    def test_put_snowflake_array_undefined(self):
        builder = data_binding.JSONObjectBuilder()
        builder.put_snowflake_array("test", undefined.UNDEFINED)
        assert builder == {}


class TestCastJSONArray:
    def test_cast_is_invoked_with_each_item(self):
        cast = mock.MagicMock()
        arr = ["foo", "bar", "baz"]

        data_binding.cast_json_array(arr, cast)

        assert cast.call_args_list[0] == mock.call("foo")
        assert cast.call_args_list[1] == mock.call("bar")
        assert cast.call_args_list[2] == mock.call("baz")

    def test_cast_result_is_used_for_each_item(self):
        r1 = mock.MagicMock()
        r2 = mock.MagicMock()
        r3 = mock.MagicMock()
        cast = mock.MagicMock(side_effect=[r1, r2, r3])

        arr = ["foo", "bar", "baz"]

        assert data_binding.cast_json_array(arr, cast) == [r1, r2, r3]
