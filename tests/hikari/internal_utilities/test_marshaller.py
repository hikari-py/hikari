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
import cymock as mock
import pytest

from hikari.internal_utilities import marshaller
from tests.hikari import _helpers


class TestAttrib:
    def test_invokes_attrs(self):
        deserializer = lambda _: _
        serializer = lambda _: _

        mock_default_factory_1 = mock.MagicMock
        mock_default_factory_2 = mock.MagicMock

        with mock.patch("attr.ib") as attrib:
            marshaller.attrib(
                deserializer=deserializer,
                raw_name="foo",
                if_none=mock_default_factory_1,
                if_undefined=mock_default_factory_2,
                transient=False,
                serializer=serializer,
                foo=12,
                bar="hello, world",
            )

            attrib.assert_called_once_with(
                foo=12,
                bar="hello, world",
                metadata={
                    marshaller._RAW_NAME_ATTR: "foo",
                    marshaller._SERIALIZER_ATTR: serializer,
                    marshaller._DESERIALIZER_ATTR: deserializer,
                    marshaller._TRANSIENT_ATTR: False,
                    marshaller._IF_UNDEFINED: mock_default_factory_2,
                    marshaller._IF_NONE: mock_default_factory_1,
                },
            )


class TestAttrs:
    def test_invokes_attrs(self):
        marshaller_mock = mock.create_autospec(marshaller.HikariEntityMarshaller, spec_set=True)

        kwargs = {"foo": 9, "bar": "lol", "marshaller": marshaller_mock}

        marshaller_mock.register = mock.MagicMock(wraps=lambda c: c)

        with mock.patch("attr.s", return_value=lambda c: c) as attrs:

            @marshaller.attrs(**kwargs)
            class Foo:
                bar = 69

            assert Foo is not None
            assert Foo.bar == 69

            attrs.assert_called_once_with(foo=9, bar="lol", auto_attribs=False)
            marshaller_mock.register.assert_called_once_with(Foo)


class TestMarshaller:
    @pytest.fixture()
    def marshaller_impl(self):
        return marshaller.HikariEntityMarshaller()

    def test_deserialize(self, marshaller_impl):
        deserialized_id = mock.MagicMock()
        id_deserializer = mock.MagicMock(return_value=deserialized_id)

        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(deserializer=id_deserializer)
            some_list: list = marshaller.attrib(deserializer=lambda items: [str(i) for i in items])

        result = marshaller_impl.deserialize({"id": "12345", "some_list": [True, False, "foo", 12, 3.4]}, User)

        assert isinstance(result, User)
        assert result.id == deserialized_id
        assert result.some_list == ["True", "False", "foo", "12", "3.4"]

    def test_deserialize_not_required_success_if_specified(self, marshaller_impl):
        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(if_undefined=None, deserializer=str)

        result = marshaller_impl.deserialize({"id": 12345}, User)

        assert isinstance(result, User)
        assert result.id == "12345"

    def test_deserialize_not_required_success_if_not_specified(self, marshaller_impl):
        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(if_undefined=None, deserializer=str)

        result = marshaller_impl.deserialize({}, User)

        assert isinstance(result, User)
        assert result.id is None

    def test_deserialize_calls_if_undefined_if_not_none_and_field_not_present(self, marshaller_impl):
        mock_result = mock.MagicMock()
        mock_callable = mock.MagicMock(return_value=mock_result)

        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(if_undefined=mock_callable, deserializer=str)

        result = marshaller_impl.deserialize({}, User)

        assert isinstance(result, User)
        assert result.id is mock_result
        mock_callable.assert_called_once()

    @_helpers.assert_raises(type_=AttributeError)
    def test_deserialize_fail_on_unspecified_if_required(self, marshaller_impl):
        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(deserializer=str)

        marshaller_impl.deserialize({}, User)

    def test_deserialize_nullable_success_if_not_null(self, marshaller_impl):
        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(if_none=None, deserializer=str)

        result = marshaller_impl.deserialize({"id": 12345}, User)

        assert isinstance(result, User)
        assert result.id == "12345"

    def test_deserialize_nullable_success_if_null(self, marshaller_impl):
        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(if_none=None, deserializer=str)

        result = marshaller_impl.deserialize({"id": None}, User)

        assert isinstance(result, User)
        assert result.id is None

    def test_deserialize_calls_if_none_if_not_none_and_data_is_none(self, marshaller_impl):
        mock_result = mock.MagicMock()
        mock_callable = mock.MagicMock(return_value=mock_result)

        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(if_none=mock_callable, deserializer=str)

        result = marshaller_impl.deserialize({"id": None}, User)

        assert isinstance(result, User)
        assert result.id is mock_result
        mock_callable.assert_called_once()

    @_helpers.assert_raises(type_=AttributeError)
    def test_deserialize_fail_on_None_if_not_nullable(self, marshaller_impl):
        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(deserializer=str)

        marshaller_impl.deserialize({"id": None}, User)

    @_helpers.assert_raises(type_=TypeError)
    def test_deserialize_fail_on_Error(self, marshaller_impl):
        die = mock.MagicMock(side_effect=RuntimeError)

        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(deserializer=die)

        marshaller_impl.deserialize({"id": 123,}, User)

    def test_serialize(self, marshaller_impl):
        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(deserializer=..., serializer=str)
            some_list: list = marshaller.attrib(deserializer=..., serializer=lambda i: list(map(int, i)))

        u = User(12, ["9", "18", "27", "36"])

        assert marshaller_impl.serialize(u) == {"id": "12", "some_list": [9, 18, 27, 36]}

    def test_serialize_transient(self, marshaller_impl):
        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(deserializer=..., serializer=str)
            some_list: list = marshaller.attrib(
                deserializer=..., transient=True,
            )

        u = User(12, ["9", "18", "27", "36"])

        assert marshaller_impl.serialize(u) == {
            "id": "12",
        }

    @_helpers.assert_raises(type_=LookupError)
    def test_deserialize_on_unregistered_class_raises_LookupError(self, marshaller_impl):
        class Foo:
            pass

        marshaller_impl.deserialize({}, Foo)

    @_helpers.assert_raises(type_=LookupError)
    def test_serialize_on_unregistered_class_raises_LookupError(self, marshaller_impl):
        class Foo:
            pass

        f = Foo()

        marshaller_impl.serialize(f)

    def test_handling_underscores_correctly_during_deserialization(self, marshaller_impl):
        @marshaller.attrs(marshaller=marshaller_impl)
        class ClassWithUnderscores:
            _foo = marshaller.attrib(deserializer=str)

        impl = marshaller_impl.deserialize({"_foo": 1234}, ClassWithUnderscores)

        assert impl._foo == "1234"

    def test_handling_underscores_correctly_during_serialization(self, marshaller_impl):
        @marshaller.attrs(marshaller=marshaller_impl)
        class ClassWithUnderscores:
            _foo = marshaller.attrib(serializer=int)

        impl = ClassWithUnderscores(foo="1234")

        assert marshaller_impl.serialize(impl) == {"_foo": 1234}
