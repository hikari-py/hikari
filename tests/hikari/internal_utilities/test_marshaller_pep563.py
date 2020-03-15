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
"""
Same as the marshaller tests, but with PEP 563 POSTPONED TYPE ANNOTATIONS
future support enabled, to prove type hints do not interfere with this
mechanism if they are postponed and evaluated as string literals.
"""
from __future__ import annotations

import cymock as mock
import pytest

from hikari.internal_utilities import marshaller
from tests.hikari import _helpers


class TestAttribPep563:
    def test_invokes_attrs(self):
        deserializer = lambda _: _
        serializer = lambda _: _

        with mock.patch("attr.ib") as attrib:
            marshaller.attrib(
                deserializer=deserializer,
                raw_name="foo",
                transient=False,
                optional=True,
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
                    marshaller._OPTIONAL_ATTR: True,
                },
            )


class TestAttrsPep563:
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


class TestMarshallerPep563:
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

    def test_deserialize_optional_success_if_specified(self, marshaller_impl):
        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(optional=True, deserializer=str)

        result = marshaller_impl.deserialize({"id": 12345,}, User)

        assert isinstance(result, User)
        assert result.id == "12345"

    def test_deserialize_optional_success_if_not_specified(self, marshaller_impl):
        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(optional=True, deserializer=str)

        result = marshaller_impl.deserialize({"id": None,}, User)

        assert isinstance(result, User)
        assert result.id is None

    @_helpers.assert_raises(type_=AttributeError)
    def test_deserialize_fail_on_None_if_not_optional(self, marshaller_impl):
        @marshaller.attrs(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(optional=False, deserializer=str)

        marshaller_impl.deserialize({"id": None,}, User)

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
